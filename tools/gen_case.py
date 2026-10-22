#!/usr/bin/env python3
"""The 3D-printed case: a bottom shell and a top frame per half, gasket-mounted.

case/keygen-{left,right}-bottom.{step,stl}   floor, battery bay, walls, gasket ledges, heat-set insert holes
case/keygen-{left,right}-top.{step,stl}      frame round the plate, gasket pockets, screw holes
case/keygen-{left,right}-plate.step          the plate, for the fit check (it is made from the Gerbers)
case/keygen-case.step                        all six parts in place

The plate and PCB, tied together by standoffs, float on the plate's gasket tabs. Each tab sits
between two Poron strips: one on a ledge in the bottom shell, one under the top frame. The two
parts are screwed together through the walls (M2 x 6 into M2 heat-set inserts). The bottom shell
has an open slot under the USB-C, a slot for the power switch lever (with the wall thinned in
front of both), and a guided pinhole under the reset button. The LiPo lies in a bay sunk into the
floor, clear of the solder joints above it. The underside is flat.

Geometry and the stack come from case_geometry.py, so rerun this after any PCB change. Needs
build123d next to KiCad's pcbnew; see the README:

    ~/.venvs/keygen-cad/bin/python tools/gen_case.py
"""
import math, sys
from pathlib import Path

from build123d import (Align, Box, Color, Compound, Cone, Cylinder, Kind, Polygon, Pos, Rot, export_step,
                       export_stl, extrude, offset)

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C
from gen_plate import outline_with_tabs

OUT = C.ROOT / "case"
INSERT_D, INSERT_DEPTH = 3.2, 5.0      # hole for an M2 x 3 heat-set insert, with room for the melt
SCREW_D = 2.4                          # M2 clearance
CBORE_D, CBORE_DEPTH = 4.4, 2.2        # M2 x 6 socket head, flush with the top
USB_SLOT_W = C.NANO_W + 2.0            # the whole nice!nano end, which overhangs the slanted edge
LEVER_SLOT_W, LEVER_SLOT_H = 9.0, 3.4
RESET_HOLE_D, RESET_TUBE_D = 2.0, 5.0  # paperclip hole, and the guide tube round it
RESET_BUTTON_H = 5.0                   # 6 mm tact switch, 5 mm tall, on the PCB underside
EPS = 0.01
CASE_COLOUR, PLATE_COLOUR = Color(0x2E2E33), Color(0x111113)

xy = lambda p: (p[0], -p[1])           # KiCad y points down; the CAD model's y points up
Z = (Align.CENTER, Align.CENTER, Align.MIN)
UP = (0, 0, 1)                         # the outline winds clockwise once y is flipped, so say which way


def face(pts):
    return Polygon(*[xy(p) for p in pts], align=None)


def edge_box(e, s0, s1, out0, out1, z0, z1):
    """A box on edge e: from s0 to s1 along it, out0 to out1 mm outward, z0 to z1."""
    s, o = (s0 + s1) / 2, (out0 + out1) / 2
    cx, cy = xy(e.at(s, o))
    ang = math.degrees(math.atan2(-e.d[1], e.d[0]))
    return Pos(cx, cy, z0) * Rot(0, 0, ang) * Box(s1 - s0, out1 - out0, z1 - z0, align=Z)


def dir_box(p, u, along0, along1, width, z0, z1):
    """A box from along0 to along1 mm along the unit direction u from p, `width` wide."""
    a = (along0 + along1) / 2
    cx, cy = xy((p[0] + u[0] * a, p[1] + u[1] * a))
    ang = math.degrees(math.atan2(-u[1], u[0]))
    return Pos(cx, cy, z0) * Rot(0, 0, ang) * Box(along1 - along0, width, z1 - z0, align=Z)


def cylinder(p, d, z0, z1):
    x, y = xy(p)
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=Z)


def port_cuts(h):
    """The thinned wall in front of the USB-C and the switch lever, as edge-aligned spans."""
    e = h["port_edge"]
    s_usb, s_lev = e.s_of(h["usb"]), e.s_of(h["lever"])
    lo, hi = min(s_usb, s_lev) - 10.0, max(s_usb, s_lev) + 8.0
    if lo < 10.0: lo = -(C.WALL_OUT + 2.0)          # run the notch off the corner
    if hi > e.len - 10.0: hi = e.len + C.WALL_OUT + 2.0
    return e, lo, hi, s_lev


def build(h):
    outline = face(h["outline"])
    inner = offset(outline, C.WALL_IN, kind=Kind.INTERSECTION)
    outer = offset(outline, C.WALL_OUT, kind=Kind.INTERSECTION)
    tab_list = C.tabs(h)
    screws = C.case_screws(h, tab_list)
    e, lo, hi, s_lev = port_cuts(h)
    notch = edge_box(e, lo, hi, C.WALL_IN + C.PORT_WALL, C.WALL_OUT + 3.0, C.BOTTOM_Z - 1, C.TOP_Z + 1)

    # bottom shell: floor + walls up to the split
    bottom = Pos(0, 0, C.BOTTOM_Z) * extrude(outer, C.SPLIT_Z - C.BOTTOM_Z, dir=UP)
    bottom -= Pos(0, 0, C.CAVITY_Z) * extrude(inner, C.SPLIT_Z - C.CAVITY_Z + 1, dir=UP)
    cuts = [notch]
    for t in tab_list:                               # ledge for the lower gasket strip
        cuts.append(edge_box(t["edge"], t["s"] - C.TAB_W / 2 - C.POCKET_CLEAR, t["s"] + C.TAB_W / 2 + C.POCKET_CLEAR,
                             -2.0, C.TAB_D + C.POCKET_CLEAR, C.LEDGE_Z, C.SPLIT_Z + 1))
    for p in screws:
        cuts.append(cylinder(p, INSERT_D, C.SPLIT_Z - INSERT_DEPTH, C.SPLIT_Z + 1))
    # USB-C: open slot down through the floor edge, along the controller's USB direction
    ax0, ay0, ax1, ay1 = h["antenna"]
    u = (h["usb"][0] - (ax0 + ax1) / 2, h["usb"][1] - (ay0 + ay1) / 2)
    n = math.hypot(*u); u = (u[0] / n, u[1] / n)
    cuts.append(dir_box(h["usb"], u, -3.0, C.WALL_OUT + 5.0, USB_SLOT_W, C.BOTTOM_Z - 1, -C.PCB_T))
    # power switch lever
    cuts.append(edge_box(e, s_lev - LEVER_SLOT_W / 2, s_lev + LEVER_SLOT_W / 2, -2.0, C.WALL_OUT + 3.0,
                         -C.PCB_T - LEVER_SLOT_H, -C.PCB_T))
    bx0, by0, bx1, by1 = C.battery(h)["bay"]          # battery bay, sunk into the floor
    (bcx, bcy) = xy(((bx0 + bx1) / 2, (by0 + by1) / 2))
    cuts.append(Pos(bcx, bcy, C.CAVITY_Z - C.BAY_DEPTH) * Box(bx1 - bx0, by1 - by0, C.BAY_DEPTH + 1, align=Z))
    for c in cuts:
        bottom -= c
    # reset: a guide tube from the floor up to just under the button, and the pinhole through both
    tube_top = -C.PCB_T - RESET_BUTTON_H - 1.0
    bottom += cylinder(h["reset"], RESET_TUBE_D, C.CAVITY_Z - EPS, tube_top)
    bottom -= cylinder(h["reset"], RESET_HOLE_D, C.BOTTOM_Z - 1, tube_top + 1)
    rx, ry = xy(h["reset"])
    bottom -= Pos(rx, ry, C.BOTTOM_Z - EPS) * Cone(RESET_HOLE_D, RESET_HOLE_D / 2, 1.0, align=Z)

    # top frame: the ring round the plate, from the split to the top
    top = Pos(0, 0, C.SPLIT_Z) * extrude(outer - inner, C.TOP_Z - C.SPLIT_Z, dir=UP)
    cuts = [notch]
    for t in tab_list:                               # pocket for the tab and the upper gasket strip
        cuts.append(edge_box(t["edge"], t["s"] - C.TAB_W / 2 - C.POCKET_CLEAR, t["s"] + C.TAB_W / 2 + C.POCKET_CLEAR,
                             -2.0, C.TAB_D + C.POCKET_CLEAR, C.SPLIT_Z - 1, C.CEIL_Z))
    for p in screws:
        cuts.append(cylinder(p, SCREW_D, C.SPLIT_Z - 1, C.TOP_Z + 1))
        cuts.append(cylinder(p, CBORE_D, C.TOP_Z - CBORE_DEPTH, C.TOP_Z + 1))
    for c in cuts:
        top -= c
    return bottom, top, plate(h, tab_list), len(tab_list), len(screws)


def plate(h, tab_list):
    p = Pos(0, 0, C.PLATE_BOT) * extrude(face(outline_with_tabs(h, tab_list)), C.PLATE_T, dir=UP)
    for k in h["keys"]:
        x, y = xy((k["x"], k["y"]))
        p -= Pos(x, y, C.PLATE_BOT - 1) * Rot(0, 0, -k["rot"]) * Box(C.CUTOUT, C.CUTOUT, C.PLATE_T + 2, align=Z)
    for x, y in h["enc"]:
        x, y = xy((x, y))
        p -= Pos(x, y, C.PLATE_BOT - 1) * Box(C.ENC_CUTOUT, C.ENC_CUTOUT, C.PLATE_T + 2, align=Z)
    for q in h["holes"].values():
        p -= cylinder(q, C.HOLE_D, C.PLATE_BOT - 1, C.PLATE_TOP + 1)
    x0, y0, x1, y1 = h["oled"]
    (cx, cy) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    p -= Pos(cx, cy, C.PLATE_BOT - 1) * Box(x1 - x0 + 2 * C.OLED_CLEAR, y1 - y0 + 2 * C.OLED_CLEAR, C.PLATE_T + 2, align=Z)
    return p


KEY_TRAVEL = 4.0
CAP_SKIRT = 7.5                        # keycap skirt bottom above the plate at rest (DSA on MX, about)


def fit_check(h, bottom, top, plt):
    """Volumes (mm3) where a case part overlaps the board, the plate, the parts under the PCB, the
    battery or a keycap at the bottom of its travel, and where the battery meets the solder joints
    under the PCB with the stack pressed down. All should be 0."""
    pcb = Pos(0, 0, -C.PCB_T) * extrude(face(h["outline"]), C.PCB_T, dir=UP)
    x0, y0, x1, y1 = h["controller"]
    (cx, cy) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    controller = Pos(cx, cy, -C.PCB_T - C.CONTROLLER_DEPTH) * Box(x1 - x0, y1 - y0, C.CONTROLLER_DEPTH, align=Z)
    rx, ry = xy(h["reset"])
    button = Pos(rx, ry, -C.PCB_T - RESET_BUTTON_H) * Box(6.2, 6.2, RESET_BUTTON_H, align=Z)
    caps = None
    for k in h["keys"]:
        x, y = xy((k["x"], k["y"]))
        cap = Pos(x, y, C.PLATE_TOP + CAP_SKIRT - KEY_TRAVEL) * Rot(0, 0, -k["rot"]) * Box(
            k["w"] * 19.05 - C.CAP_GAP, k["h"] * 19.05 - C.CAP_GAP, 10, align=Z)
        caps = cap if caps is None else caps + cap
    x0, y0, x1, y1 = h["oled"]
    (ox, oy) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    oled = Pos(ox, oy, C.OLED_Z[0]) * Box(x1 - x0, y1 - y0, C.OLED_Z[1] - C.OLED_Z[0], align=Z)
    x0, y0, x1, y1 = C.battery(h)["cell"]
    (bx, by) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    cell = lambda lift: Pos(bx, by, C.CAVITY_Z - C.BAY_DEPTH + lift) * Box(
        x1 - x0, y1 - y0, C.BATTERY_T + C.BATTERY_GROWTH, align=Z)
    battery = cell(0.0)
    out = {}
    for name, part in (("bottom", bottom), ("top", top)):
        for what, solid in (("pcb", pcb), ("plate", plt), ("controller", controller), ("reset button", button),
                            ("keycaps", caps), ("oled", oled), ("battery", battery)):
            v = (part & solid).volume
            if v > 1e-3: out[f"{name} x {what}"] = v
    # the battery against the sockets, diodes and the tall parts under the PCB, the stack pressed down
    underside = Pos(0, 0, -C.PCB_T - C.UNDERSIDE_H) * extrude(face(h["outline"]), C.UNDERSIDE_H, dir=UP)
    pressed = cell(C.FLOAT_GAP)
    for what, solid in (("parts under the pcb", underside), ("controller", controller), ("reset button", button)):
        v = (pressed & solid).volume
        if v > 1e-3: out[f"battery x {what}"] = v
    return out


def main():
    OUT.mkdir(exist_ok=True)
    parts = []
    for side, h in C.halves().items():
        bottom, top, plt, n_tabs, n_screws = build(h)
        for name, part in (("bottom", bottom), ("top", top), ("plate", plt)):
            stem = OUT / f"keygen-{side}-{name}"
            part.color = PLATE_COLOUR if name == "plate" else CASE_COLOUR
            export_step(part, str(stem.with_suffix(".step")))
            if name != "plate":
                export_stl(part, str(stem.with_suffix(".stl")), tolerance=0.02, angular_tolerance=0.2)
            bb = part.bounding_box()
            print(f"{stem.name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
                  f"{part.volume / 1000:.1f} cm3, valid {part.is_valid}")
            part.label = f"{side} {name}"
            parts.append(part)
        print(f"{side}: {n_tabs} gasket tabs, {n_screws} case screws")
        top_z, gap, pressed = C.battery_heights()
        print(f"{side} battery: {C.BATTERY_L:g} x {C.BATTERY_W:g} x {C.BATTERY_T:g} mm (+{C.BATTERY_GROWTH:g}) in the "
              f"floor bay, {gap:.1f} mm under the solder joints, {pressed:.1f} mm with the stack pressed down")
        clash = fit_check(h, bottom, top, plt)
        print(f"{side} fit check: " + (", ".join(f"{k} {v:.2f} mm3" for k, v in clash.items()) or "no overlaps"))
    export_step(Compound(children=parts), str(OUT / "keygen-case.step"))
    print(f"wrote {OUT.relative_to(C.ROOT)}/")


if __name__ == "__main__":
    main()
