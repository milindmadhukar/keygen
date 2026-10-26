#!/usr/bin/env python3
"""Render the board into assets/:

render-hero.png         assembled, at an angle, with switches and keycaps
render-top.png          assembled, from above
render-bottom.png       assembled, from below: the controllers and the back-side parts
render-bare.png         the bare PCB at an angle: soldermask, silkscreen artwork and pads only
render-bare-top.png     the bare PCB from above
render-bare-bottom.png  the bare PCB from below

KiCad's named "Black" soldermask (what the stackup says, so the Gerber job file and fab read
"Black") renders see-through brown, so the renders use a copy of the board with an opaque
near-black mask instead. The bare views use a copy with every 3D model taken out.

    python3 tools/render_board.py
"""
import re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
TMP = ROOT / "pcb/_render.kicad_pcb"          # beside the real board so ${KIPRJMOD} models resolve
OPAQUE_MASK = (r'(\(type "(?:Top|Bottom) Solder Mask"\)\s*\(color )"Black"', r'\1"#0E0E10F5"')
MODELS = re.compile(r'\n\t\t\(model "[^"]*"\n(?:\t\t\t[^\n]*\n)*\t\t\)')
FLAT = ["-w", "5600", "-h", "2200", "--zoom", "2.5"]
VIEWS = {   # name: (bare board, kicad-cli render options)
    "hero": (False, ["-w", "5600", "-h", "2600", "--quality", "high", "--floor", "--perspective",
                     "--rotate", "-38,0,0", "--zoom", "1.85"]),
    "top": (False, [*FLAT, "--quality", "basic", "--side", "top"]),
    "bottom": (False, [*FLAT, "--quality", "basic", "--side", "bottom"]),
    "bare": (True, ["-w", "5600", "-h", "2800", "--quality", "high", "--floor", "--perspective",
                    "--rotate", "-45,0,0", "--zoom", "1.9"]),
    "bare-top": (True, [*FLAT, "--quality", "high", "--side", "top"]),
    "bare-bottom": (True, [*FLAT, "--quality", "high", "--side", "bottom"]),
}


def main():
    board = re.sub(*OPAQUE_MASK, PCB.read_text())
    try:
        for name, (bare, args) in VIEWS.items():
            TMP.write_text(MODELS.sub("", board) if bare else board)
            raw = ROOT / f"assets/_{name}.png"; out = ROOT / f"assets/render-{name}.png"
            subprocess.run(["kicad-cli", "pcb", "render", "-o", str(raw), *args, "--background", "transparent",
                            "--use-board-stackup-colors", str(TMP)], check=True, capture_output=True)
            subprocess.run(["magick", str(raw), "-trim", "+repage", "-bordercolor", "none", "-border", "20",
                            "-resize", "3840x", "-strip", str(out)], check=True)
            raw.unlink()
            print(f"wrote {out.relative_to(ROOT)}")
    finally:
        for p in (TMP, TMP.with_suffix(".kicad_prl")): p.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
