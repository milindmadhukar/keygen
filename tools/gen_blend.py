#!/usr/bin/env python3
"""Build the Blender scene, blender/keygen-parts.blend, from the board and the case:

1. read the switches and LEDs from pcb/keygen.kicad_pcb (pcbnew) into scene.json;
2. export the board, its parts and their models to GLB with kicad-cli, the keycaps left out;
3. run tools/blend_scene.py in Blender, which imports the GLB, the case, plate and keycap STLs,
   places the caps and the LEDs, sets the materials and saves the parts file. It also writes the
   studio file, blender/keygen.blend, if there is none yet.

keygen-parts.blend is gitignored and rebuilt by tools/regen.py whenever its sources change.
keygen.blend links its "Keygen" collection, so it always shows the current design; its camera,
lights and render settings are kept by hand.

    python3 tools/gen_blend.py                  build the parts file
    python3 tools/gen_blend.py --reset-studio   also rewrite blender/keygen.blend from scratch

Uses $KEYGEN_BLENDER as the Blender binary if set, else `blender`.
"""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
TMP = ROOT / "pcb/_blend.kicad_pcb"           # beside the real board so ${KIPRJMOD} models resolve
KEYCAPS = re.compile(r'\t\t\(model "[^"]*Keycap_[^"]*"\n(?:\t\t\t[^\n]*\n)*\t\t\)\n')
SCENE = ROOT / "tools/blend_scene.py"


def mm(v):
    return round(pcbnew.ToMM(v), 4)


def board_data():
    b = pcbnew.LoadBoard(str(PCB))
    keys, leds = [], []
    for f in b.GetFootprints():
        ref, name = f.GetReference(), str(f.GetFPID().GetLibItemName())
        p = f.GetPosition()
        at = dict(ref=ref, x=mm(p.x), y=mm(p.y), rot=f.GetOrientationDegrees(), back=f.IsFlipped(),
                  side="left" if ref[-3] == "1" else "right")
        if m := re.match(r"SW_MX_HS_\w+_([\d.]+)u$", name):
            keys.append(dict(at, size=m.group(1)))
        elif ref.startswith("LED"):
            leds.append(at)
    return dict(keys=keys, leds=leds, pcb_t=C.PCB_T, plate_top=C.PLATE_TOP, cap_skirt=C.CAP_SKIRT)


def main():
    reset = "--reset-studio" in sys.argv[1:]
    blender = os.environ.get("KEYGEN_BLENDER", "blender")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "scene.json").write_text(json.dumps(board_data(), indent=1))
        TMP.write_text(KEYCAPS.sub("", PCB.read_text()))
        try:
            subprocess.run(["kicad-cli", "pcb", "export", "glb", "-f", "-o", str(tmp / "board.glb"),
                            "--user-origin", "0x0mm", "--subst-models", "--include-tracks", "--include-pads",
                            "--include-silkscreen", "--include-soldermask", str(TMP)],
                           check=True, capture_output=True, text=True)
        finally:
            for p in (TMP, TMP.with_suffix(".kicad_prl")): p.unlink(missing_ok=True)
        (ROOT / "blender").mkdir(exist_ok=True)
        p = subprocess.run([blender, "-b", "--factory-startup", "--python-exit-code", "1", "--python", str(SCENE),
                            "--", str(tmp), str(ROOT), *(["--reset-studio"] if reset else [])],
                           capture_output=True, text=True)
        out = "\n".join(l for l in (p.stdout + p.stderr).splitlines() if l.startswith(("keygen:", "Traceback", "  ", "Error"))
                        or "Error" in l)
        print(out)
        if p.returncode:
            sys.exit(f"blender failed ({p.returncode}):\n{(p.stdout + p.stderr)[-3000:]}")


if __name__ == "__main__":
    main()
