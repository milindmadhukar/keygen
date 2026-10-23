#!/usr/bin/env python3
"""Write a 1:1 switch plate PDF on A4, one half per page, for printing
on paper to get a feel for the layout. Each page shows the plate outline (= PCB outline), the
14 x 14 mm switch cut-outs, keycap footprints with legends, M2 holes, the encoder cut-out and
knob, and the OLED window. Positions come from pcb/keygen.kicad_pcb and the key tables, so re-run
it after any PCB change. Print at 100 % ("Actual size", not "Fit to page") and check the 100 mm
ruler on the sheet. Use --portrait for printers that shrink landscape PDF pages."""
import argparse
import math, sys
from pathlib import Path

import cairo
import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C
import gen_pcb as G
import gen_schematic as g

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "case/plate/pdf/keygen-plate-print.pdf"
PORTRAIT_OUT = ROOT / "case/plate/pdf/keygen-plate-print-portrait.pdf"
PT = 72 / 25.4                     # points per mm
A4 = (297.0, 210.0)                # landscape, mm
CUTOUT = 14.0                      # MX plate cut-out
CAP_GAP = 0.95                     # keycap bottom = n * 19.05 - this
ENC_CUTOUT = 13.0                  # square cut-out around the EC11 body
KNOB_D = 19.0
HOLE_D = 2.2


def board_data():
    b = pcbnew.LoadBoard(str(ROOT / "pcb/keygen.kicad_pcb"))
    mm = pcbnew.ToMM
    polys = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(polys, False)
    outlines = []
    for i in range(polys.OutlineCount()):
        o = polys.Outline(i)
        outlines.append([(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())])
    holes, enc = [], []
    for fp in b.GetFootprints():
        p = fp.GetPosition(); x, y = mm(p.x), mm(p.y)
        if fp.GetReference().startswith("H"): holes.append((x, y))
        if fp.GetReference().startswith("ENC"): enc.append((x, y))
    return outlines, holes, enc


def keys(side):
    """[(label, cx, cy, rot_cw_deg, w_u, h_u)] in PCB mm."""
    geo = G.key_geometry()
    out = []
    for r, c, lab, _ in g.KEYS[side]:
        cx, cy, rr, w, h, _ = geo[(side, r, c)]
        out.append((lab, cx + G.OFF[0], cy + G.OFF[1], rr, w, h))
    return out


def rrect(cr, w, h, r):
    x, y = -w / 2, -h / 2
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def text(cr, s, x, y, size, centre=True, bold=False):
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size)
    e = cr.text_extents(s)
    if centre: cr.move_to(x - e.x_bearing - e.width / 2, y - e.y_bearing - e.height / 2)
    else: cr.move_to(x, y)
    cr.show_text(s)


def ruler(cr, x, y):
    """100 mm scale bar with 10 mm ticks, so the print scale can be checked."""
    cr.set_source_rgb(0, 0, 0); cr.set_line_width(0.25)
    cr.move_to(x, y); cr.line_to(x + 100, y); cr.stroke()
    for i in range(0, 101, 5):
        cr.move_to(x + i, y); cr.line_to(x + i, y - (3 if i % 10 == 0 else 1.5)); cr.stroke()
        if i % 50 == 0: text(cr, f"{i}", x + i, y - 5, 2.5)
    text(cr, "100 mm: measure this; if it isn't exactly 100 mm, reprint at 100 % / Actual size", x + 104, y - 0.5, 2.6, centre=False)


def page(cr, side, outline, holes, enc, oled):
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    ox = (A4[0] - (max(xs) - min(xs))) / 2 - min(xs)
    oy = (A4[1] - 14 - (max(ys) - min(ys))) / 2 - min(ys)   # leave the bottom strip for the ruler
    cr.save(); cr.translate(ox, oy)

    # plate outline
    cr.set_source_rgb(0, 0, 0); cr.set_line_width(0.35)
    cr.move_to(*outline[0])
    for p in outline[1:]: cr.line_to(*p)
    cr.close_path(); cr.stroke()

    for lab, cx, cy, rr, w, h in keys(side):
        cr.save(); cr.translate(cx, cy); cr.rotate(math.radians(rr))
        # keycap footprint (grey, filled lightly)
        rrect(cr, w * G.U - CAP_GAP, h * G.U - CAP_GAP, 1.0)
        cr.set_source_rgb(0.93, 0.93, 0.93); cr.fill_preserve()
        cr.set_source_rgb(0.55, 0.55, 0.55); cr.set_line_width(0.2); cr.stroke()
        # switch cut-out
        cr.rectangle(-CUTOUT / 2, -CUTOUT / 2, CUTOUT, CUTOUT)
        cr.set_source_rgb(1, 1, 1); cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0); cr.set_line_width(0.3); cr.stroke()
        cr.set_source_rgb(0.15, 0.15, 0.15)
        text(cr, lab, 0, -1.0, 3.2 if len(lab) <= 2 else 2.4, bold=True)
        size = f"{max(w, h):g}u"
        if size != "1u": text(cr, size, 0, 3.6, 1.8)
        cr.restore()

    for x, y in holes:
        cr.new_path(); cr.arc(x, y, HOLE_D / 2, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0); cr.set_line_width(0.25); cr.stroke()
        cr.move_to(x - 2, y); cr.line_to(x + 2, y); cr.move_to(x, y - 2); cr.line_to(x, y + 2)
        cr.set_line_width(0.1); cr.stroke()

    x0, y0, x1, y1 = oled                   # OLED module (dashed) and its plate window
    cr.rectangle(x0 - C.OLED_CLEAR, y0 - C.OLED_CLEAR, x1 - x0 + 2 * C.OLED_CLEAR, y1 - y0 + 2 * C.OLED_CLEAR)
    cr.set_source_rgb(0, 0, 0); cr.set_line_width(0.3); cr.stroke()
    cr.rectangle(x0, y0, x1 - x0, y1 - y0)
    cr.set_dash([1.2, 0.8]); cr.set_source_rgb(0.2, 0.3, 0.8); cr.set_line_width(0.3); cr.stroke(); cr.set_dash([])
    cr.set_source_rgb(0.2, 0.3, 0.8); text(cr, "OLED", (x0 + x1) / 2, (y0 + y1) / 2, 2.6)

    for x, y in enc:
        cr.rectangle(x - ENC_CUTOUT / 2, y - ENC_CUTOUT / 2, ENC_CUTOUT, ENC_CUTOUT)
        cr.set_source_rgb(0, 0, 0); cr.set_line_width(0.3); cr.stroke()
        cr.new_path(); cr.arc(x, y, KNOB_D / 2, 0, 2 * math.pi)
        cr.set_dash([1.2, 0.8]); cr.set_source_rgb(0.2, 0.3, 0.8); cr.set_line_width(0.3); cr.stroke(); cr.set_dash([])
        cr.set_source_rgb(0.2, 0.3, 0.8); text(cr, f"knob Ø{KNOB_D:g}", x, y, 2.2)
    cr.restore()

    cr.set_source_rgb(0, 0, 0)
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    text(cr, f"Keygen switch plate, {side} half, top view, 1:1  ({w:.1f} × {h:.1f} mm)", 12, 12, 4, centre=False, bold=True)
    text(cr, "Black squares: 14 × 14 mm switch cut-outs.  Grey: keycap footprints.  Crosses: M2 holes."
         + ("  Blue dashed: encoder knob and OLED module; black: their plate cut-outs." if enc else ""), 12, 17, 2.6, centre=False)
    ruler(cr, 12, A4[1] - 10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portrait", action="store_true", help="rotate the full-size drawing onto portrait A4")
    args = parser.parse_args()
    outlines, holes, enc = board_data()
    halves = {}
    for o in outlines:
        mid = sum(p[0] for p in o) / len(o)
        halves["left" if mid < 200 else "right"] = o
    inside = lambda pt, o: min(p[0] for p in o) <= pt[0] <= max(p[0] for p in o) and min(p[1] for p in o) <= pt[1] <= max(p[1] for p in o)
    out = PORTRAIT_OUT if args.portrait else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    size = (A4[1], A4[0]) if args.portrait else A4
    surf = cairo.PDFSurface(str(out), size[0] * PT, size[1] * PT)
    cr = cairo.Context(surf); cr.scale(PT, PT)
    for side in ("left", "right"):
        o = halves[side]
        if args.portrait:
            cr.save()
            cr.translate(0, A4[0])
            cr.rotate(-math.pi / 2)
        page(cr, side, o, [h for h in holes if inside(h, o)], [e for e in enc if inside(e, o)], C.halves()[side]["oled"])
        if args.portrait:
            cr.restore()
        cr.show_page()
    surf.finish()
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
