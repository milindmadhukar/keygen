#!/usr/bin/env python3
"""Render the case and the switch plate into assets/:

render-case.png           the board in its case
render-case-top.png       the same from straight above, to judge the deck round the keycaps
render-case-exploded.png  bottom shell, case foam, PCB, switch pads, plate foam, lower gaskets,
                          plate, upper gaskets and top frame lifted apart (no switches or keycaps)
render-case-parts.png     the printed parts alone: each bottom shell with its top frame above it
render-case-bottom.png    the case from below: floor, case screw counterbores, reset pinholes, USB-C and
                          switch openings
render-case-wedge.png     the keyboard tented on its wedges, from the front: each half turned to the wedge's
                          angle, so the desk runs level under both
render-case-wedge-parts.png   the wedges alone: the foot recesses and the magnet pockets in their top faces
render-plate.png          the switch plates, top view

The case views attach the parts from case/*/step/ (run gen_case.py first) to a copy of the board as 3D
models, with the same opaque black mask as render_board.py; the plate view gives the plate board a pale
tinted mask for its clear polycarbonate. KiCad only renders a board, so the
case-only views use a scratch board made of 1 mm squares hidden inside the case walls. KiCad cannot
tilt the board either, so the tented view renders it level and turns each half's image.

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
EXPLODE = {"bottom": -50.0, "foam/case": -25.0, "pads": 10.0, "foam/plate": 22.0, "gaskets/lower": 28.0,
           "plate": 36.0, "gaskets/upper": 46.0, "top": 64.0}                                   # mm, for the exploded view
PARTS_LIFT = 30.0                                         # top frame above its shell, parts view
SWITCHES_AND_CAPS = re.compile(r'\t\t\(model "[^"]*(?:SW_Cherry_MX_PCB|Keycap_)[^"]*"\n(?:\t\t\t[^\n]*\n)*\t\t\)\n')
OPAQUE_MASK = (r'(\(type "(?:Top|Bottom) Solder Mask"\)\s*\(color )"Black"', r'\1"#0E0E10F5"')
# the plate is clear polycarbonate: KiCad renders a board body opaque, so a pale tinted sheet stands in
CLEAR_PLATE = [(r'(\(type "(?:Top|Bottom) Solder Mask"\)\s*\(color )"Black"', r'\1"#A9BCC6B0"'),
               (r'\(color "FR4 natural"\)', '(color "#D5E0E4")')]
BOARD_VIEWS = {
    "case": ["-w", "5600", "-h", "2800", "--quality", "basic", "--floor", "--perspective",
             "--rotate", "-38,0,0", "--zoom", "1.75"],
    "case-top": ["-w", "8800", "-h", "4000", "--quality", "basic", "--side", "top", "--zoom", "1.7"],
    "case-exploded": ["-w", "5600", "-h", "3600", "--quality", "basic", "--perspective",
                      "--rotate", "-60,0,0", "--zoom", "1.2"],
}
CASE_VIEWS = {
    "case-parts": ["-w", "5600", "-h", "3200", "--quality", "basic", "--perspective",
                   "--rotate", "-45,0,0", "--zoom", "1.4"],
    "case-bottom": ["-w", "5600", "-h", "2600", "--quality", "basic", "--side", "bottom", "--zoom", "2.1"],
}
WEDGE_VIEW = ["-w", "5600", "-h", "3000", "--quality", "basic", "--perspective", "--rotate", "-82,0,0", "--zoom", "1.5"]
WEDGE_PARTS_VIEW = ["-w", "5600", "-h", "3200", "--quality", "basic", "--perspective", "--rotate", "-42,0,0", "--zoom", "0.42"]
WEDGE_PARTS_LIFT = 36.0                                   # wedges raised round the scratch board's squares


def case_footprint(lifts, parts=("bottom", "plate", "top")):
    """A footprint carrying the case parts as 3D models; a part is "bottom", "plate", "top",
    "foam/<layer>", "pads" (the switch pads) or "gaskets/<lower|upper>"."""
    models = []
    for side in ("left", "right"):
        for part in parts:
            d, _, name = part.rpartition("/")
            if part == "pads":
                path = CASE / "foam/step" / f"keygen-{side}-switch-pads.step"
            elif d == "gaskets":
                path = CASE / "foam/step" / f"keygen-{side}-{name}-gaskets.step"
            else:
                path = CASE / (d or part) / "step" / f"keygen-{side}-{name}{'-foam' if d else ''}.step"
            models.append(f'(model "{path}" (offset (xyz 0 0 {lifts.get(part, 0.0)})) '
                          f'(scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    return (f'(footprint "keygen:case" (layer "F.Cu") (uuid "{uuid.uuid4()}") (at 0 0)\n'
            f'(property "Reference" "CASE1" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{uuid.uuid4()}") '
            f'(effects (font (size 1 1) (thickness 0.15))))\n'
            f'(attr board_only exclude_from_pos_files exclude_from_bom)\n' + "\n".join(models) + ")\n")


def render(board, name, args, finish=None):
    raw = ROOT / f"assets/_{name}.png"; out = ROOT / f"assets/render-{name}.png"
    subprocess.run(["kicad-cli", "pcb", "render", "-o", str(raw), *args, "--background", "transparent",
                    "--use-board-stackup-colors", str(board)], check=True, capture_output=True)
    if finish:
        finish(raw, out)
    else:
        subprocess.run(["magick", str(raw), "-trim", "+repage", "-bordercolor", "none", "-border", "20",
                        "-resize", "3840x", "-strip", str(out)], check=True)
    raw.unlink()
    print(f"wrote {out.relative_to(ROOT)}")


def squares_board(points):
    """Board text whose outline is a 1 mm square at each point."""
    b = pcbnew.BOARD()
    for x, y in points:
        corners = [(x - .5, y - .5), (x + .5, y - .5), (x + .5, y + .5), (x - .5, y + .5)]
        for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
            sh = pcbnew.PCB_SHAPE(b); sh.SetShape(pcbnew.SHAPE_T_SEGMENT); sh.SetLayer(pcbnew.Edge_Cuts)
            sh.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(ax), pcbnew.FromMM(ay)))
            sh.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by))); b.Add(sh)
    pcbnew.SaveBoard(str(TMP), b)
    return TMP.read_text().rstrip()


def hidden_board():
    """Squares in the middle of each case wall (bar the thin wall by the ports), each as far as it
    can get from the tab pockets and screw holes. They stay out of sight but span the case, so KiCad
    frames the view on the whole case."""
    points = []
    for h in C.halves().values():
        tabs = C.tabs(h)
        taken = [t["centre"] for t in tabs] + C.case_screws(h, tabs)
        for e in h["edges"]:
            if e is h["port_edge"] or e.len < 12: continue
            s = max(range(5, int(e.len) - 5), key=lambda s: min(math.dist(e.at(s), p) for p in taken))
            points.append(e.at(s, C.screw_offset()))
    return squares_board(points)


def wedge_board():
    """Squares inside the wedges' thick inner parts, once they are lifted WEDGE_PARTS_LIFT."""
    points = []
    for h in C.halves().values():
        xs, ys = zip(*h["outline"])
        x = max(xs) - 30.0 if h["side"] == "left" else min(xs) + 30.0
        points += [(x, min(ys) + 30.0), (x, max(ys) - 40.0)]
    return squares_board(points)


def tented(raw, out):
    """Turn each half of the level render to the wedge's angle, inner edge up, and stand them side by side."""
    half = lambda crop, angle: ["(", str(raw), "-crop", crop, "+repage", "-trim", "+repage", "-background", "none",
                                "-rotate", f"{angle:g}", "+repage", "-trim", "+repage", ")"]
    subprocess.run(["magick", *half("50%x100%+0+0", -C.WEDGE_ANGLE), *half(f"50%x100%+{int(WEDGE_VIEW[1]) // 2}+0", C.WEDGE_ANGLE),
                    "-background", "none", "-gravity", "south", "+append", "-bordercolor", "none", "-border", "20",
                    "-resize", "3840x", "-strip", str(out)], check=True)


def main():
    base = re.sub(*OPAQUE_MASK, PCB.read_text()).rstrip()
    try:
        for name, args in BOARD_VIEWS.items():
            exploded = name.endswith("exploded")
            board = SWITCHES_AND_CAPS.sub("", base) if exploded else base
            parts = list(EXPLODE) if exploded else ["bottom", "plate", "top"]
            TMP.write_text(board[:-1] + case_footprint(EXPLODE if exploded else {}, parts) + ")\n")
            render(TMP, name, args)
        TMP.write_text(base[:-1] + case_footprint({}, ["bottom", "plate", "top", "wedge"]) + ")\n")
        render(TMP, "case-wedge", WEDGE_VIEW, tented)
        wedges = wedge_board()
        TMP.write_text(wedges[:-1] + case_footprint({"wedge": WEDGE_PARTS_LIFT}, ("wedge",)) + ")\n")
        render(TMP, "case-wedge-parts", WEDGE_PARTS_VIEW)
        empty = hidden_board()
        for name, args in CASE_VIEWS.items():
            lifts = {"top": PARTS_LIFT} if name == "case-parts" else {}
            TMP.write_text(empty[:-1] + case_footprint(lifts, ("bottom", "top")) + ")\n")
            render(TMP, name, args)
        plate = PLATE.with_name("_render.kicad_pcb")
        text = PLATE.read_text()
        for pat, rep in CLEAR_PLATE:
            text = re.sub(pat, rep, text)
        plate.write_text(text)
        try:
            render(plate, "plate", ["-w", "5600", "-h", "2200", "--quality", "basic", "--side", "top", "--zoom", "2.5"])
        finally:
            for p in (plate, plate.with_suffix(".kicad_prl")): p.unlink(missing_ok=True)
    finally:
        for p in (TMP, TMP.with_suffix(".kicad_prl"), TMP.with_suffix(".kicad_pro")): p.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
