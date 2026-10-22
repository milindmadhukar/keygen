#!/usr/bin/env python3
"""Render the case and the switch plate into assets/:

render-case.png           the board in its case
render-case-exploded.png  bottom shell, case foam, PCB, switch foam, plate foam, plate and top frame lifted
                          apart (no switches or keycaps)
render-case-parts.png     the printed parts alone: each bottom shell with its top frame above it
render-case-bottom.png    the case from below: floor, reset pinholes, USB-C and switch openings
render-plate.png          the FR-4 switch plates, top view

The case views attach the parts from case/*/step/ (run gen_case.py first) to a copy of the board as 3D
models, with the same opaque black mask as render_board.py. KiCad only renders a board, so the
case-only views use a scratch board made of 1 mm squares hidden inside the case walls.

    python3 tools/render_case.py
"""
import math, re, subprocess, sys, uuid
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
PLATE = ROOT / "pcb/plate/keygen-plate.kicad_pcb"
TMP = ROOT / "pcb/_render_case.kicad_pcb"      # beside the real board so ${KIPRJMOD} models resolve
CASE = ROOT / "case"
EXPLODE = {"bottom": -45.0, "foam/case": -22.0, "foam/switch": 9.0, "foam/plate": 18.0, "plate": 30.0,
           "top": 55.0}                                   # mm, for the exploded view
PARTS_LIFT = 30.0                                         # top frame above its shell, parts view
SWITCHES_AND_CAPS = re.compile(r'\t\t\(model "[^"]*(?:SW_Cherry_MX_PCB|Keycap_)[^"]*"\n(?:\t\t\t[^\n]*\n)*\t\t\)\n')
OPAQUE_MASK = (r'(\(type "(?:Top|Bottom) Solder Mask"\)\s*\(color )"Black"', r'\1"#0E0E10F5"')
BOARD_VIEWS = {
    "case": ["-w", "2800", "-h", "1400", "--quality", "basic", "--floor", "--perspective",
             "--rotate", "-38,0,0", "--zoom", "1.75"],
    "case-exploded": ["-w", "2800", "-h", "1800", "--quality", "basic", "--perspective",
                      "--rotate", "-50,0,0", "--zoom", "1.3"],
}
CASE_VIEWS = {
    "case-parts": ["-w", "2800", "-h", "1600", "--quality", "basic", "--perspective",
                   "--rotate", "-45,0,0", "--zoom", "1.4"],
    "case-bottom": ["-w", "2800", "-h", "1300", "--quality", "basic", "--side", "bottom", "--zoom", "2.3"],
}


def case_footprint(lifts, parts=("bottom", "plate", "top")):
    """A footprint carrying the case parts as 3D models; a part is "bottom", "plate", "top" or
    "foam/<layer>"."""
    models = []
    for side in ("left", "right"):
        for part in parts:
            d, _, name = part.rpartition("/")
            path = CASE / (d or part) / "step" / f"keygen-{side}-{name}{'-foam' if d else ''}.step"
            models.append(f'(model "{path}" (offset (xyz 0 0 {lifts.get(part, 0.0)})) '
                          f'(scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    return (f'(footprint "keygen:case" (layer "F.Cu") (uuid "{uuid.uuid4()}") (at 0 0)\n'
            f'(property "Reference" "CASE1" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{uuid.uuid4()}") '
            f'(effects (font (size 1 1) (thickness 0.15))))\n'
            f'(attr board_only exclude_from_pos_files exclude_from_bom)\n' + "\n".join(models) + ")\n")


def render(board, name, args):
    raw = ROOT / f"assets/_{name}.png"; out = ROOT / f"assets/render-{name}.png"
    subprocess.run(["kicad-cli", "pcb", "render", "-o", str(raw), *args, "--background", "transparent",
                    "--use-board-stackup-colors", str(board)], check=True, capture_output=True)
    subprocess.run(["magick", str(raw), "-trim", "+repage", "-bordercolor", "none", "-border", "20",
                    "-resize", "2000x", "-strip", str(out)], check=True)
    raw.unlink()
    print(f"wrote {out.relative_to(ROOT)}")


def hidden_board():
    """Board text whose outline is a set of 1 mm squares, one in the middle of each case wall (bar the
    thin wall by the ports), each as far as it can get from the tab pockets and screw holes. They
    stay out of sight but span the case, so KiCad frames the view on the whole case."""
    b = pcbnew.BOARD()
    for h in C.halves().values():
        tabs = C.tabs(h)
        taken = [t["centre"] for t in tabs] + C.case_screws(h, tabs)
        for e in h["edges"]:
            if e is h["port_edge"] or e.len < 12: continue
            s = max(range(5, int(e.len) - 5), key=lambda s: min(math.dist(e.at(s), p) for p in taken))
            x, y = e.at(s, C.screw_offset())
            corners = [(x - .5, y - .5), (x + .5, y - .5), (x + .5, y + .5), (x - .5, y + .5)]
            for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
                sh = pcbnew.PCB_SHAPE(b); sh.SetShape(pcbnew.SHAPE_T_SEGMENT); sh.SetLayer(pcbnew.Edge_Cuts)
                sh.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(ax), pcbnew.FromMM(ay)))
                sh.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by))); b.Add(sh)
    pcbnew.SaveBoard(str(TMP), b)
    return TMP.read_text().rstrip()


def main():
    base = re.sub(*OPAQUE_MASK, PCB.read_text()).rstrip()
    try:
        for name, args in BOARD_VIEWS.items():
            exploded = name.endswith("exploded")
            board = SWITCHES_AND_CAPS.sub("", base) if exploded else base
            parts = list(EXPLODE) if exploded else ["bottom", "plate", "top"]
            TMP.write_text(board[:-1] + case_footprint(EXPLODE if exploded else {}, parts) + ")\n")
            render(TMP, name, args)
        empty = hidden_board()
        for name, args in CASE_VIEWS.items():
            lifts = {"top": PARTS_LIFT} if name == "case-parts" else {}
            TMP.write_text(empty[:-1] + case_footprint(lifts, ("bottom", "top")) + ")\n")
            render(TMP, name, args)
        plate = PLATE.with_name("_render.kicad_pcb")
        plate.write_text(re.sub(*OPAQUE_MASK, PLATE.read_text()))
        try:
            render(plate, "plate", ["-w", "2800", "-h", "1100", "--quality", "basic", "--side", "top", "--zoom", "2.5"])
        finally:
            for p in (plate, plate.with_suffix(".kicad_prl")): p.unlink(missing_ok=True)
    finally:
        for p in (TMP, TMP.with_suffix(".kicad_prl"), TMP.with_suffix(".kicad_pro")): p.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
