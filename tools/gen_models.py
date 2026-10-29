#!/usr/bin/env python3
"""Write the 3D models KiCad's 3D view and the renders use for parts without a stock model:

pcb/lib/keygen.3dshapes/Knob_17mm.step     the encoder knob
pcb/lib/keygen.3dshapes/OLED_096_I2C.step  the 0.96 in. 128x64 OLED module

Shapes for the 3D view, not manufacturing data. Needs build123d (see the README):

    ~/.venvs/keygen-cad/bin/python tools/gen_models.py
"""
from pathlib import Path

from build123d import Align, Axis, Box, Color, Cylinder, Pos, Rot, chamfer, export_step

ROOT = Path(__file__).resolve().parent.parent
SHAPES = ROOT / "pcb/lib/keygen.3dshapes"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)

# ---------------------------------------------------------------- knob
# An aluminium knob, 17 mm across and 13 mm tall (a "D halfshaft 17x13" amplifier knob), knurled
# round its lower part, with an indicator groove on top and a blind bore for the EC11's 6 mm D-shaft.
# Origin: shaft centre at the bottom face; the encoder footprint lifts it to where it sits on the cut
# shaft (case_geometry.KNOB_Z).
D, H = 17.0, 13.0
KNURL_N, KNURL_H, KNURL_R = 36, 9.0, 0.45      # grooves round the side, from the bottom up
BORE_D, BORE_DEPTH, FLAT = 6.0, 11.0, 4.5      # EC11 D-shaft: 6 mm, 4.5 mm across the flat; case_geometry.KNOB_DEPTH


def knob():
    k = Cylinder(D / 2, H, align=BOTTOM)
    k = chamfer(k.edges().group_by(Axis.Z)[-1], 1.0)          # top edge
    k = chamfer(k.edges().group_by(Axis.Z)[0], 0.4)           # bottom edge
    for i in range(KNURL_N):
        a = 360 * i / KNURL_N
        k -= Rot(0, 0, a) * Pos(D / 2, 0, -0.1) * Cylinder(KNURL_R, KNURL_H + 0.1, align=BOTTOM)
    k -= Pos(0, 0, H - 0.5) * Cylinder(D / 2 - 2.0, 1.0, align=BOTTOM)        # shallow dish on top
    k -= Pos(D / 4 - 0.5, 0, H - 1.0) * Box(D / 2 - 3.0, 0.9, 2.0, align=BOTTOM)   # indicator groove
    bore = Cylinder(BORE_D / 2, BORE_DEPTH, align=BOTTOM) & Pos(BORE_D / 2 - FLAT, 0, 0) * Box(
        BORE_D, BORE_D, BORE_DEPTH, align=(Align.MIN, Align.CENTER, Align.MIN))
    return k - bore


# ---------------------------------------------------------------- OLED module
# A generic 0.96 in. 128x64 SSD1306 module, 27.5 x 28 mm, its 4-pin row along one edge. It is
# drawn in the board's top view (x right, y up) relative to pin 1, with the module above the pins
# (the pin row along its bottom edge, as on Keygen) and pins 2-4 toward -x, then turned to the 1x4
# footprint's own frame. It sits in the top frame, plugged into the footprint, LIFT above the PCB with
# the case closed (case_geometry.OLED_Z; gen_case.py checks they agree).
MOD_W, MOD_H, MOD_T, HDR_IN, LIFT = 27.5, 27.8, 1.2, 1.5, 5.2
GLASS, GLASS_IN = (26.7, 19.26, 1.6), 4.27     # centred across the module, this far from the pin edge
ACTIVE, ACTIVE_IN = (21.744, 10.864), 6.37    # likewise


def oled():
    cx, cy = -3 * 2.54 / 2, MOD_H / 2 - HDR_IN                 # module centre from pin 1
    board = Pos(cx, cy, LIFT) * Box(MOD_W, MOD_H, MOD_T, align=BOTTOM)
    gy = -HDR_IN + GLASS_IN + GLASS[1] / 2                      # from the pin edge
    ay = -HDR_IN + ACTIVE_IN + ACTIVE[1] / 2
    glass = Pos(cx, gy, LIFT + MOD_T) * Box(*GLASS, align=BOTTOM)
    active = Pos(cx, ay, LIFT + MOD_T + GLASS[2]) * Box(*ACTIVE, 0.02, align=BOTTOM)
    parts = [(board, 0x15161A), (glass, 0x2A2C31), (active, 0x050506)]
    out = []
    for shape, colour in parts:
        s = Rot(0, 0, 90) * shape          # board top view -> the header footprint's frame (turned 90 deg)
        s.color = Color(colour)
        out.append(s)
    return out


def main():
    k = knob(); k.color = Color(0xB9BDC4); k.label = "knob"
    export_step(k, str(SHAPES / "Knob_17mm.step"))
    from build123d import Compound
    o = Compound(children=oled()); o.label = "oled"
    export_step(o, str(SHAPES / "OLED_096_I2C.step"))
    for name, s in (("Knob_17mm", k), ("OLED_096_I2C", o)):
        bb = s.bounding_box()
        print(f"wrote pcb/lib/keygen.3dshapes/{name}.step: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")


if __name__ == "__main__":
    main()
