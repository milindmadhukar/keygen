#!/usr/bin/env python3
"""Write assets/render-hero.png, assets/render-top.png and assets/render-bottom.png from the board.

KiCad's named "Black" soldermask (what the stackup says, so the Gerber job file and fab read
"Black") renders see-through brown, so the renders use a copy of the board with an opaque
near-black mask instead.

    python3 tools/render_board.py
"""
import re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
TMP = ROOT / "pcb/_render.kicad_pcb"          # beside the real board so ${KIPRJMOD} models resolve
VIEWS = {
    "hero": ["-w", "2800", "-h", "1300", "--quality", "high", "--floor", "--perspective",
             "--rotate", "-38,0,0", "--zoom", "1.85"],
    "top": ["-w", "2800", "-h", "1100", "--quality", "basic", "--side", "top", "--zoom", "2.5"],
    "bottom": ["-w", "2800", "-h", "1100", "--quality", "basic", "--side", "bottom", "--zoom", "2.5"],
}

def main():
    text = re.sub(r'(\(type "(?:Top|Bottom) Solder Mask"\)\s*\(color )"Black"', r'\1"#0E0E10F5"', PCB.read_text())
    TMP.write_text(text)
    try:
        for name, args in VIEWS.items():
            raw = ROOT / f"assets/_{name}.png"; out = ROOT / f"assets/render-{name}.png"
            subprocess.run(["kicad-cli", "pcb", "render", "-o", str(raw), *args, "--background", "transparent",
                            "--use-board-stackup-colors", str(TMP)], check=True, capture_output=True)
            subprocess.run(["magick", str(raw), "-trim", "+repage", "-bordercolor", "none", "-border", "20",
                            "-resize", "2000x", "-strip", str(out)], check=True)
            raw.unlink()
            print(f"wrote {out.relative_to(ROOT)}")
    finally:
        for p in (TMP, TMP.with_suffix(".kicad_prl")): p.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
