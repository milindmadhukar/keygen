#!/usr/bin/env python3
"""Make a 1:1 portrait A4 paper footprint for each assembled case half.

Run with ~/.venvs/keygen-cad/bin/python tools/case_footprint_print.py. The black
outside line is the case edge; cut it out to try both halves on a desk. Print at
actual size and check the 100 mm ruler before using the paper as a template.
"""

import math
from pathlib import Path

import cairo
from shapely.geometry import Polygon

import case_geometry as C
import gen_pcb as G


OUT = C.ROOT / "case/plate/pdf/keygen-case-footprint-portrait.pdf"
PT = 72 / 25.4
PAGE = (210.0, 297.0)  # A4 portrait, mm


def label(cr, message, x, y, size=3.0, bold=False):
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size)
    cr.move_to(x, y)
    cr.show_text(message)


def polygon(cr, points):
    cr.move_to(*points[0])
    for point in points[1:]:
        cr.line_to(*point)
    cr.close_path()


def rectangle(cr, bounds):
    x0, y0, x1, y1 = bounds
    cr.rectangle(x0, y0, x1 - x0, y1 - y0)


def ruler(cr):
    x, y = 20.0, 270.0
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.25)
    cr.move_to(x, y)
    cr.line_to(x + 100, y)
    cr.stroke()
    for i in range(21):
        xx = x + 5 * i
        cr.move_to(xx, y)
        cr.line_to(xx, y - (3 if i % 2 == 0 else 1.5))
    cr.stroke()
    label(cr, "0", x - 1, y - 5, 2.5)
    label(cr, "50", x + 47, y - 5, 2.5)
    label(cr, "100", x + 96, y - 5, 2.5)
    label(cr, "Measure this ruler: 100 mm", 20, 281, 3.0)


def page(cr, side, h):
    # This is the same offset used for the outer shell in gen_case.py.
    outer = Polygon(h["outline"]).buffer(C.WALL_OUT, join_style="mitre", mitre_limit=10)
    x0, y0, x1, y1 = outer.bounds
    width, height = x1 - x0, y1 - y0
    ox = (PAGE[0] - width) / 2 - x0
    oy = 46 + (height - (y1 - y0)) / 2 - y0

    label(cr, f"KEYGEN  /  {side.upper()} CASE HALF  /  1:1", 16, 18, 5.0, bold=True)
    label(cr, f"Top view  |  outside footprint {width:.1f} x {height:.1f} mm", 16, 25, 3.2)
    label(cr, "Cut along the solid outer line to try the case positions on your desk.", 16, 32, 2.8)

    cr.save()
    cr.translate(ox, oy)

    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.45)
    polygon(cr, list(outer.exterior.coords))
    cr.stroke()

    cr.set_source_rgb(0.40, 0.40, 0.40)
    cr.set_dash([1.8, 1.2])
    cr.set_line_width(0.22)
    polygon(cr, h["outline"])
    cr.stroke()
    cr.set_dash([])

    # Keycap footprints make the paper silhouette useful with real keycaps.
    cr.set_source_rgb(0.66, 0.66, 0.66)
    cr.set_line_width(0.18)
    for key in h["keys"]:
        cr.save()
        cr.translate(key["x"], key["y"])
        cr.rotate(math.radians(key["rot"]))
        w = key["w"] * G.U - C.CAP_GAP
        height_key = key["h"] * G.U - C.CAP_GAP
        cr.rectangle(-w / 2, -height_key / 2, w, height_key)
        cr.stroke()
        cr.restore()

    # The largest supported battery lies below the PCB; keep its line distinct.
    cr.set_source_rgb(0.25, 0.25, 0.25)
    cr.set_dash([2.0, 1.0])
    cr.set_line_width(0.26)
    rectangle(cr, C.battery(h)["cell"])
    cr.stroke()
    cr.set_dash([])

    for ex, ey in h["enc"]:
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.set_line_width(0.28)
        cr.arc(ex, ey, C.KNOB_D / 2, 0, 2 * math.pi)
        cr.stroke()
    cr.set_source_rgb(0.1, 0.1, 0.1)
    cr.set_line_width(0.25)
    rectangle(cr, h["oled"])
    cr.stroke()

    cr.restore()

    label(cr, "Solid black: case edge   Gray dashed: PCB edge   Light gray: keycaps", 16, 212, 2.8)
    label(cr, "Black dashed: 88 x 60 mm maximum battery below PCB", 16, 218, 2.8)
    label(cr, "Circle: encoder knob   Rectangle: OLED module", 16, 224, 2.8)
    label(cr, "The assembled case has thickness; paper shows its plan footprint only.", 16, 234, 2.8)
    ruler(cr)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    surface = cairo.PDFSurface(str(OUT), PAGE[0] * PT, PAGE[1] * PT)
    cr = cairo.Context(surface)
    cr.scale(PT, PT)
    halves = C.halves()
    for side in ("left", "right"):
        page(cr, side, halves[side])
        cr.show_page()
    surface.finish()
    print(f"wrote {OUT.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
