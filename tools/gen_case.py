#!/usr/bin/env python3
"""The 3D-printed case: a bottom shell and a top frame per half, gasket-mounted.

case/bottom/{stl,step}/keygen-{left,right}-bottom.*   floor, battery bay, walls, gasket ledges, counterbored
                                                      screw holes
case/top/{stl,step}/keygen-{left,right}-top.*         frame round the plate and a deck over it, gasket
                                                      pockets, insert holes
case/plate/{stl,step}/keygen-{left,right}-plate.*     the plate, for the fit check and the Blender scene (it is
                                                      made from the Gerbers)
case/foam/{dxf,svg}/keygen-{left,right}-{plate,case}-foam.*   the two foam layers, to cut
case/foam/step/keygen-{left,right}-*-foam.step        the same layers as solids, in place
case/foam/step/keygen-{left,right}-switch-pads.step   the switch pads, one ring per switch, in place
case/foam/step/keygen-{left,right}-{lower,upper}-gaskets.step   the gasket strips under and over the
                                                      plate tabs, in place and squeezed as when closed
case/keygen-case.step                                 all six parts in place

The plate and PCB, held together by the switches and spaced by standoffs, float on the plate's
gasket tabs. Each tab sits
between two Poron strips: one on a ledge in the bottom shell, one under the top frame. The two
parts are screwed together from below, up through the walls (M2 x 16 into M2 heat-set inserts in
blind holes in the top frame's underside), so the top has no holes and the screw heads sit in
counterbores, below the flat underside. The bottom shell
has a rounded USB-C port, sized for a cable's plug wherever the floating stack carries it, in front of a
pocket inside the wall for the controller's end; a slot for the power switch lever (the wall thinned
outside both); and a guided pinhole under the reset button. The LiPo lies in a bay sunk into the
floor, clear of the solder joints above it. The underside is flat.

The top frame's deck is level with its rim and covers the plate everywhere but the keycaps, the
OLED and the encoder (a hole round its bushing, under the knob). The OLED module is held in the top
frame and plugs into the PCB: its glass sits in a pocket under a thin lip round the window, which
opens towards the thumbs, and its board on a boss that thickens the deck down to it, with four pegs
through its corner holes to melt or glue over. Where keycap windows leave a narrow notch of deck
between them it is cut away, and every edge of the deck is straight.

The foam, from the top: EVA plate foam taped to the plate's underside, cut round the switches
(notched for their latches), the encoder, the OLED and the standoffs, 1 mm above the Poron ring
switch pads stuck on the PCB round each switch (the 0.5 mm PE_Z layer: a square ring round each switch, its corner clipped where it meets a
standoff; they come ready-made, so they have a STEP but no cut file); and EVA case foam on the floor
round the battery bay, the controller, the tall parts under the PCB and the reset tube. They are
written as 1:1 DXF and SVG, seen from above.

Geometry and the stack come from case_geometry.py, so rerun this after any PCB change. Needs
build123d next to KiCad's pcbnew; see the README:

    ~/.venvs/keygen-cad/bin/python tools/gen_case.py
"""
import math, sys
from pathlib import Path

from build123d import (Align, Axis, Box, Circle, Color, Compound, Cone, Cylinder, ExportDXF, ExportSVG, Face, Kind, Polygon, Pos,
                       Rectangle, RectangleRounded, Rot, Unit, Wire, export_step, export_stl, extrude, fillet, loft, offset)

from shapely import Point, Polygon as SPoly, box, unary_union
from shapely.affinity import rotate

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C
from gen_plate import outline_with_tabs

OUT = C.ROOT / "case"


def out_path(part, ext, side, name=None):
    """case/<part>/<ext>/keygen-<side>-<name or part>.<ext>, its folder made."""
    p = OUT / part / ext / f"keygen-{side}-{name or part}.{ext}"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
INSERT_D, INSERT_L = 3.2, 3.0          # M2 x 3 heat-set insert and its hole, in the top frame's underside
INSERT_DEPTH = INSERT_L + 0.8          # blind, with room for the melt; the rest of the frame stays solid above it
SCREW_D = 2.4                          # M2 clearance
SCREW_L = 16.0                         # M2 x 16 socket head (ISO 4762), from below
CBORE_D, HEAD_H = 4.4, 2.0             # its counterbore in the floor, and its head height
CBORE_CHAMFER = 0.6
CBORE_TOP = C.SPLIT_Z + INSERT_L - SCREW_L   # the head's seat: the screw ends level with the insert's top
NANO_POCKET_W = C.NANO_W + 2.0         # the controller's end, which overhangs the slanted edge, floating sideways
LEVER_SLOT_W, LEVER_SLOT_H = 9.0, 3.4
RESET_HOLE_D, RESET_TUBE_D = 2.0, 5.0  # paperclip hole, and the guide tube round it
RESET_BUTTON_H = 5.0                   # 6 mm tact switch, 5 mm tall, on the PCB underside
EPS = 0.01
NOTCH_FILL = 8.0                       # deck notches between keycap windows narrower than this are cut away
CASE_COLOUR = Color(0x2E2E33)
PLATE_COLOUR = Color(0xC8D6DC, alpha=0x60)   # clear polycarbonate, see-through
FOAM_COLOURS = {"plate": Color(0x3A3B40), "case": Color(0x4A4C52)}   # both black EVA, two greys to tell them apart
PAD_COLOUR = Color(0x6A6C73)                                          # black Poron rings, lighter to show on the PCB

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


def dir_port(p, u, along0, along1, width, z0, z1, r):
    """dir_box with its four edges along u rounded to r: a port through a wall."""
    a = (along0 + along1) / 2
    cx, cy = xy((p[0] + u[0] * a, p[1] + u[1] * a))
    ang = math.degrees(math.atan2(-u[1], u[0]))
    b = Box(along1 - along0, width, z1 - z0)
    return Pos(cx, cy, (z0 + z1) / 2) * Rot(0, 0, ang) * fillet(b.edges().filter_by(Axis.X), r)


def rect(r):
    x0, y0, x1, y1 = r
    return face([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


# ---------------------------------------------------------------- plan view, in shapely (board mm, y down)
def sq(p, size, rot=0.0, w=None):
    """A size x size square (or w x size), turned rot degrees clockwise like a key, centred on p."""
    return rotate(box(p[0] - (w or size) / 2, p[1] - size / 2, p[0] + (w or size) / 2, p[1] + size / 2), rot, origin=p)


def circ(p, d):
    return Point(p).buffer(d / 2, quad_segs=16)


def opened(g, r):
    """The piece of g that holds its outer edge, less any part narrower than 2r."""
    g = g.buffer(-r, join_style="mitre").buffer(r, join_style="mitre")
    return max(getattr(g, "geoms", [g]), key=lambda p: p.area)


def to_face(g):
    """A shapely polygon as a build123d face, y flipped like xy()."""
    ring = lambda c: Wire.make_polygon([(x, -y) for x, y in list(c.coords)[:-1]], close=True)
    f = Face(ring(g.exterior), [ring(i) for i in g.interiors])
    return f if f.normal_at().Z > 0 else -f


def cylinder(p, d, z0, z1):
    x, y = xy(p)
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=Z)


def usb_axis(h):
    """The unit direction the controller's USB-C faces, from its antenna end."""
    ax0, ay0, ax1, ay1 = h["antenna"]
    u = (h["usb"][0] - (ax0 + ax1) / 2, h["usb"][1] - (ay0 + ay1) / 2)
    n = math.hypot(*u)
    return u[0] / n, u[1] / n


def nano_pocket(h):
    """The pocket inside the wall that the controller's end sits in, as (along0, along1, width) on
    usb_axis from the USB-C end, and the four corners of its outer face, in board mm."""
    u = usb_axis(h)
    along1 = C.POCKET_CLEAR + C.NANO_POCKET_CLEAR
    c = (h["usb"][0] + u[0] * along1, h["usb"][1] + u[1] * along1)
    side = (-u[1] * NANO_POCKET_W / 2, u[0] * NANO_POCKET_W / 2)
    return (-3.0, along1, NANO_POCKET_W), [(c[0] + side[0], c[1] + side[1]), (c[0] - side[0], c[1] - side[1])]


def port_cuts(h):
    """The thinned wall outside the USB-C and the switch lever, as edge-aligned boxes: PORT_WALL in
    front of the controller's pocket, and PORT_WALL past the inner wall round the lever."""
    e = h["port_edge"]
    s_usb, s_lev = e.s_of(h["usb"]), e.s_of(h["lever"])
    lo, hi = min(s_usb, s_lev) - 10.0, max(s_usb, s_lev) + 8.0
    if lo < 10.0: lo = -(C.WALL_OUT + 2.0)          # run the notch off the corner
    if hi > e.len - 10.0: hi = e.len + C.WALL_OUT + 2.0
    _, corners = nano_pocket(h)
    out = lambda p: (p[0] - e.a[0]) * e.n[0] + (p[1] - e.a[1]) * e.n[1]
    deep = max(out(p) for p in corners) + C.PORT_WALL
    ps = sorted(e.s_of(p) for p in corners)
    z = (C.BOTTOM_Z - 1, C.TOP_Z + 1)
    if s_lev > s_usb:
        boxes = [(lo, ps[1] + C.PORT_WALL, deep), (ps[1] + C.PORT_WALL, hi, C.WALL_IN + C.PORT_WALL)]
    else:
        boxes = [(lo, ps[0] - C.PORT_WALL, C.WALL_IN + C.PORT_WALL), (ps[0] - C.PORT_WALL, hi, deep)]
    notch = [edge_box(e, s0, s1, out0, C.WALL_OUT + 3.0, *z) for s0, s1, out0 in boxes]
    return e, notch[0] + notch[1], s_lev, deep


def build(h):
    outline = face(h["outline"])
    inner = offset(outline, C.WALL_IN, kind=Kind.INTERSECTION)
    outer = offset(outline, C.WALL_OUT, kind=Kind.INTERSECTION)
    tab_list = C.tabs(h)
    screws = C.case_screws(h, tab_list)
    e, notch, s_lev, _ = port_cuts(h)

    # bottom shell: floor + walls up to the split
    bottom = Pos(0, 0, C.BOTTOM_Z) * extrude(outer, C.SPLIT_Z - C.BOTTOM_Z, dir=UP)
    bottom -= Pos(0, 0, C.CAVITY_Z) * extrude(inner, C.SPLIT_Z - C.CAVITY_Z + 1, dir=UP)
    cuts = [notch]
    for t in tab_list:                               # ledge for the lower gasket strip
        cuts.append(edge_box(t["edge"], t["s"] - C.TAB_W / 2 - C.POCKET_CLEAR, t["s"] + C.TAB_W / 2 + C.POCKET_CLEAR,
                             -2.0, C.TAB_D + C.POCKET_CLEAR, C.LEDGE_Z, C.SPLIT_Z + 1))
    for p in screws:
        cuts.append(cylinder(p, SCREW_D, C.BOTTOM_Z - 1, C.SPLIT_Z + 1))
        cuts.append(cylinder(p, CBORE_D, C.BOTTOM_Z - 1, CBORE_TOP))
    # USB-C: the controller's end in a pocket inside the wall, open at the top so the stack drops in
    # straight, and a rounded port through the wall in front of it
    u = usb_axis(h)
    (a0, a1, w), _ = nano_pocket(h)
    cuts.append(dir_box(h["usb"], u, a0, a1, w, C.CAVITY_Z, C.SPLIT_Z + 1))
    pw, pz0, pz1 = C.usb_port()
    cuts.append(dir_port(h["usb"], u, -3.0, C.WALL_OUT + 5.0, pw, pz0, pz1, C.PORT_R))
    # power switch lever
    cuts.append(edge_box(e, s_lev - LEVER_SLOT_W / 2, s_lev + LEVER_SLOT_W / 2, -2.0, C.WALL_OUT + 3.0,
                         -C.PCB_T - LEVER_SLOT_H, -C.PCB_T))
    bx0, by0, bx1, by1 = C.battery(h)["bay"]          # battery bay, sunk into the floor
    (bcx, bcy) = xy(((bx0 + bx1) / 2, (by0 + by1) / 2))
    cuts.append(Pos(bcx, bcy, C.CAVITY_Z - C.BAY_DEPTH) * Box(bx1 - bx0, by1 - by0, C.BAY_DEPTH + 1, align=Z))
    for c in cuts:
        bottom -= c
    for p in screws:                                 # chamfer the counterbores' mouths, like the reset pinhole's
        x, y = xy(p)
        bottom -= Pos(x, y, C.BOTTOM_Z - EPS) * Cone(CBORE_D / 2 + CBORE_CHAMFER, CBORE_D / 2, CBORE_CHAMFER + EPS, align=Z)
    # reset: a guide tube from the floor up to just under the button, and the pinhole through both
    tube_top = -C.PCB_T - RESET_BUTTON_H - C.FLOAT_GAP - 0.5   # clear of the button with the stack pressed down
    bottom += cylinder(h["reset"], RESET_TUBE_D, C.CAVITY_Z - EPS, tube_top)
    bottom -= cylinder(h["reset"], RESET_HOLE_D, C.BOTTOM_Z - 1, tube_top + 1)
    rx, ry = xy(h["reset"])
    bottom -= Pos(rx, ry, C.BOTTOM_Z - EPS) * Cone(RESET_HOLE_D, RESET_HOLE_D / 2, 1.0, align=Z)
    # the tenting stand's steel disc, flush in the floor's underside like the screw heads
    bottom -= cylinder(C.steel_disc(h), C.STEEL_POCKET_D, C.BOTTOM_Z - 1, C.BOTTOM_Z + C.STEEL_POCKET_DEPTH)

    # top frame: the ring round the plate from the split up to the gasket ceiling, then the deck over
    # the plate, level with the rim, with windows for the keycaps and the OLED and a hole for the encoder
    top = Pos(0, 0, C.SPLIT_Z) * extrude(outer - inner, C.CEIL_Z - C.SPLIT_Z, dir=UP)
    top += Pos(0, 0, C.CEIL_Z) * extrude(deck(h), C.TOP_Z - C.CEIL_Z, dir=UP)
    # The selected HongYan encoder body can reach 6.8 mm above the PCB; relieve the underside
    # locally while keeping the smaller bushing opening on the visible face of the deck.
    for p in h["enc"]:
        x, y = xy(p)
        top -= Pos(x, y, C.CEIL_Z - EPS) * Box(
            C.ENC_CUTOUT, C.ENC_CUTOUT, C.ENC_RECESS_TOP - C.CEIL_Z + EPS, align=Z)
    top += oled_mount(h)
    top -= oled_pockets(h)
    z0, z1 = C.OLED_Z[1] - 0.1, C.TOP_Z + 0.1
    top -= loft([Pos(0, 0, z0) * rect(C.oled_window(h, z0)), Pos(0, 0, z1) * rect(C.oled_window(h, z1))], ruled=True)
    # chamfer each keycap window's mouth on the deck top, the face printed on the bed
    z0, z1 = C.TOP_Z - C.CAP_CHAMFER, C.TOP_Z + 0.1
    for k in h["keys"]:
        top -= loft([Pos(0, 0, z0) * to_face(key_window(k)), Pos(0, 0, z1) * to_face(key_window(k, z1 - z0))], ruled=True)
    cuts = [notch]
    for t in tab_list:                               # pocket for the tab and the upper gasket strip
        cuts.append(edge_box(t["edge"], t["s"] - C.TAB_W / 2 - C.POCKET_CLEAR, t["s"] + C.TAB_W / 2 + C.POCKET_CLEAR,
                             -2.0, C.TAB_D + C.POCKET_CLEAR, C.SPLIT_Z - 1, C.CEIL_Z))
    for p in screws:
        cuts.append(cylinder(p, INSERT_D, C.SPLIT_Z - 1, C.SPLIT_Z + INSERT_DEPTH))
    for c in cuts:
        top -= c
    return bottom, top, plate(h, tab_list), tab_list, screws


def oled_mount(h):
    """The boss that thickens the deck down to the OLED module's top, OLED_BOSS round the module,
    clear of the keycap windows and the encoder, and four pegs from it through the module's holes,
    long enough to melt over (or glue) on its back."""
    x0, y0, x1, y1 = h["oled"]
    b = C.OLED_BOSS
    plan = box(x0 - b, y0 - b, x1 + b, y1 + b).difference(
        unary_union([key_window(k) for k in h["keys"]] + [circ(p, C.ENC_CUTOUT * 1.5) for p in h["enc"]]))
    z0 = C.OLED_Z[0] + C.OLED_BOARD_T
    mount = Pos(0, 0, z0) * extrude(to_face(opened(plan, 0.5)), C.CEIL_Z - z0 + EPS, dir=UP)
    for p in C.oled_holes(h):
        mount += cylinder(p, C.OLED_PEG_D, C.OLED_Z[0] - C.OLED_PEG_PROUD, z0 + EPS)
    return mount


def oled_pockets(h):
    """Cut up into the boss and deck: the glass's pocket under the lip, a relief over the module's
    four solder joints, and one over its far edge where the glass's flex cable wraps round it."""
    (gx0, gy0, gx1, gy1), _ = C.oled_glass(h)
    c, z0 = C.OLED_POCKET_CLEAR, C.OLED_Z[0] + C.OLED_BOARD_T - EPS
    pocket = Pos(0, 0, z0) * extrude(rect((gx0 - c, gy0 - c, gx1 + c, gy1 + c)), C.OLED_Z[1] - z0, dir=UP)
    hx0, hy0, hx1, hy1 = h["header"]
    g, d = C.OLED_JOINT_RELIEF
    pocket += Pos(0, 0, z0) * extrude(rect((hx0 - g, hy0 - g, hx1 + g, hy1 + g)), d + EPS, dir=UP)
    x0, y0, x1, y1 = h["oled"]
    cx, w = (x0 + x1) / 2, C.OLED_FPC_W
    pocket += Pos(0, 0, z0) * extrude(rect((cx - w / 2, y0 - 1.0, cx + w / 2, gy0)), d + EPS, dir=UP)
    return pocket


def key_window(k, grow=0.0):
    """The deck's window round keycap k, CAP_CLEAR all round, grown by `grow` on each side."""
    m = 2 * (C.CAP_CLEAR + grow)
    return sq((k["x"], k["y"]), k["h"] * 19.05 - C.CAP_GAP + m, k["rot"], k["w"] * 19.05 - C.CAP_GAP + m)


def deck_plan(h):
    """The top frame in plan at deck level, as a shapely polygon: the case outline less the keycap
    windows, the OLED window and the encoder hole. Where neighbouring keycap windows leave a notch of
    deck between them narrower than NOTCH_FILL, the notch is cut away along a straight line, and inside
    the walls every web or point of deck narrower than DECK_MIN_WEB is cut back square; any island
    that leaves is dropped. Every edge is straight; the rim over the walls keeps its corners."""
    outline = SPoly(h["outline"])
    outer = outline.buffer(C.WALL_OUT, join_style="mitre", mitre_limit=10)
    keys = unary_union([key_window(k) for k in h["keys"]])
    notches = keys.buffer(NOTCH_FILL / 2).buffer(-NOTCH_FILL / 2).difference(keys)
    keys = unary_union([keys] + [g.convex_hull for g in getattr(notches, "geoms", [notches]) if g.area > 5.0])
    holes = [keys] + [circ(p, C.ENC_HOLE_D) for p in h["enc"]] + [box(*C.oled_window(h, C.OLED_Z[1]))]
    raw = outer.difference(unary_union(holes))
    raw = raw.buffer(0.6, join_style="mitre").buffer(-0.6, join_style="mitre").intersection(raw.buffer(0.6))
    r = C.DECK_MIN_WEB / 2
    rim = raw.difference(outline.buffer(C.WALL_IN, join_style="mitre", mitre_limit=10))
    inside = raw.buffer(-r, join_style="mitre").buffer(r, join_style="mitre", mitre_limit=1.5).intersection(raw)
    return opened(unary_union([inside, rim]), 0.05)


def deck(h):
    """The deck plan (deck_plan) as a build123d face."""
    return to_face(deck_plan(h))


def foams(h):
    """The two foam layers in plan: {'plate' | 'case': face}."""
    clear = C.FOAM_HOLE_CLEAR
    grown = lambda r, g: (r[0] - g, r[1] - g, r[2] + g, r[3] + g)
    pads = [cut_circle((x, y), max(w, hh) + 2 * clear) if rnd else cut_rect((x - w / 2 - clear, y - hh / 2 - clear,
                                                                            x + w / 2 + clear, y + hh / 2 + clear))
            for x, y, w, hh, rnd in h["drills"]]
    standoffs = [cut_circle(p, C.STANDOFF_D + 2 * clear + 1.0) for p in h["holes"].values()]
    encoders = [cut_square(p, C.ENC_CUTOUT + 2 * clear) for p in h["enc"]]
    board = (SPoly(h["outline"]), face(h["outline"]))

    # plate foam, taped under the plate: the plate's cut-outs, a little larger and notched for the
    # switch latches, and the drilled pads
    plate_foam = board_less(board, [cut_switch(k, C.FOAM_SWITCH_CUT, C.SWITCH_PAD_NOTCH) for k in h["keys"]]
                            + pads + standoffs + encoders + [cut_rect(grown(h["oled"], C.OLED_CLEAR + clear))])

    # case foam, on the floor: the cavity less the battery bay and everything that hangs below the PCB
    g = C.WALL_IN - C.FOAM_WALL_CLEAR
    cavity = (board[0].buffer(g, join_style="mitre", mitre_limit=10), offset(board[1], g, kind=Kind.INTERSECTION))
    under = [cut_rect(C.battery(h)["bay"]), cut_rect(grown(h["controller"], C.FOAM_PART_CLEAR)),
             cut_circle(h["reset"], RESET_TUBE_D + 2 * C.FOAM_PART_CLEAR)]
    under += [cut_rect(grown(t, C.FOAM_PART_CLEAR)) for t in h["tall"]]
    case_foam = board_less(cavity, under)
    return {"plate": plate_foam, "case": case_foam}


def switch_pads(h):
    """The Poron ring switch pads, one per switch on the PCB, as solids in place, and the number
    whose corner is clipped round a standoff (by the plate foam's standoff hole)."""
    s, b = C.SWITCH_PAD, C.SWITCH_PAD_BAND
    ring = RectangleRounded(s, s, C.SWITCH_PAD_R) - Rectangle(s - 2 * b, s - 2 * b)
    nw, nd = C.SWITCH_PAD_NOTCH
    for sign in (1, -1):
        ring -= Pos(0, sign * (s / 2 - b)) * Rectangle(nw, 2 * nd)
    hole = C.STANDOFF_D + 2 * C.FOAM_HOLE_CLEAR + 1.0
    pads, clipped = [], 0
    for k in h["keys"]:
        x, y = xy((k["x"], k["y"]))
        f = Pos(x, y) * Rot(0, 0, -k["rot"]) * ring
        near = [q for q in h["holes"].values() if sq((k["x"], k["y"]), s, k["rot"]).intersects(circ(q, hole))]
        for q in near:
            f -= Pos(*xy(q)) * Circle(hole / 2)
        clipped += bool(near)
        pads.append(Pos(0, 0, C.PE_Z[0]) * extrude(f, C.PE_Z[1] - C.PE_Z[0], dir=UP))
    return Compound(children=pads), clipped


def gaskets(tab_list):
    """The Poron gasket strips, squeezed as when the case is closed: {'lower': on the ledges under
    the plate tabs, 'upper': on the tabs under the top frame}, each a compound of strips."""
    out0 = (C.TAB_D - C.GASKET_W) / 2
    strip = lambda t, z0, z1: edge_box(t["edge"], t["s"] - C.GASKET_L / 2, t["s"] + C.GASKET_L / 2,
                                       out0, out0 + C.GASKET_W, z0, z1)
    return {"lower": Compound(children=[strip(t, C.LEDGE_Z, C.PLATE_BOT) for t in tab_list]),
            "upper": Compound(children=[strip(t, C.PLATE_TOP, C.CEIL_Z) for t in tab_list])}


# A cut is (shapely polygon, build123d face) of the same shape: shapely finds the strips to drop, and
# build123d makes the layer with true circles, which keeps the cut files and STEP small.
def cut_circle(p, d):
    x, y = xy(p)
    return circ(p, d), Pos(x, y) * Circle(d / 2)


def cut_rect(r):
    return box(*r), rect(r)


def cut_square(p, size, rot=0.0):
    x, y = xy(p)
    return sq(p, size, rot), Pos(x, y) * Rot(0, 0, -rot) * Rectangle(size, size)


def cut_switch(k, size, notch):
    """A key's size x size cut-out, turned like the key, with a notch (width, depth) in the middle
    of each clip side."""
    (x, y), nw, nd = xy((k["x"], k["y"])), *notch
    p, d = (k["x"], k["y"]), size / 2
    g = unary_union([sq(p, size)] + [box(p[0] - nw / 2, p[1] + s * d - nd, p[0] + nw / 2, p[1] + s * d + nd)
                                     for s in (1, -1)])
    f = Rectangle(size, size)
    for s in (1, -1):
        f += Pos(0, s * d) * Rectangle(nw, 2 * nd)
    return rotate(g, k["rot"], origin=p), Pos(x, y) * Rot(0, 0, -k["rot"]) * f


def cut_poly(g):
    return g, to_face(g.simplify(0.02))


def board_less(base, cuts, strip=1.5):
    """base less the cuts, less any strip narrower than `strip` mm (it tears) and any island that leaves."""
    raw = base[0].difference(unary_union([c[0] for c in cuts]))
    drop = raw.difference(opened(raw, strip / 2))
    f = base[1]
    for c in cuts:
        f -= c[1]
    for d in getattr(drop, "geoms", [drop]):
        if d.area > 0.05:
            f -= to_face(d.buffer(0.02, join_style="mitre").simplify(0.01))
    return max(f.faces(), key=lambda x: x.area)


FOAM_Z = {"plate": C.PLATE_FOAM_Z, "case": (C.CAVITY_Z, C.CAVITY_Z + C.CASE_FOAM_T)}
FOAM_NAMES = {"plate": f"EVA plate foam, {C.PLATE_FOAM_T:g} mm", "case": f"EVA case foam, {C.CASE_FOAM_T:g} mm"}


def foam_solids(h):
    return {k: Pos(0, 0, FOAM_Z[k][0]) * extrude(f, FOAM_Z[k][1] - FOAM_Z[k][0], dir=UP) for k, f in foams(h).items()}


def write_foam(side, name, f):
    """The layer as a 1:1 cut file, seen from above, its corner at the origin."""
    bb = f.bounding_box()
    f = Pos(-bb.min.X, -bb.min.Y) * f
    dxf = ExportDXF(unit=Unit.MM); dxf.add_layer("cut"); dxf.add_shape(f.edges(), layer="cut")
    dxf.write(str(out_path("foam", "dxf", side, f"{name}-foam")))
    svg = ExportSVG(unit=Unit.MM, margin=5); svg.add_layer("cut", line_color=(0, 0, 0), line_weight=0.1)
    svg.add_shape(f.edges(), layer="cut"); svg.write(str(out_path("foam", "svg", side, f"{name}-foam")))
    return bb.size.X, bb.size.Y


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


def screw_walls(bottom, top, screws):
    """The case screws whose holes break out of the walls: a 0.8 mm skin round each counterbore (above its chamfer),
    clearance hole and insert hole, and over each insert hole up to the deck top, should be solid."""
    out = []
    for i, p in enumerate(screws):
        skin = [(bottom, cylinder(p, CBORE_D + 1.6, C.BOTTOM_Z + CBORE_CHAMFER, CBORE_TOP + 0.8) - cylinder(p, CBORE_D, C.BOTTOM_Z, CBORE_TOP)
                 - cylinder(p, SCREW_D, CBORE_TOP, C.SPLIT_Z)),
                (bottom, cylinder(p, SCREW_D + 1.6, CBORE_TOP, C.SPLIT_Z) - cylinder(p, SCREW_D, CBORE_TOP, C.SPLIT_Z)),
                (top, cylinder(p, INSERT_D + 1.6, C.SPLIT_Z, C.TOP_Z) - cylinder(p, INSERT_D, C.SPLIT_Z, C.SPLIT_Z + INSERT_DEPTH))]
        if any(abs((part & s).volume - s.volume) > 1e-3 for part, s in skin):
            out.append(i)
    return out


def fit_check(h, bottom, top, plt, foam):
    """Volumes (mm3) where a case part or a foam layer overlaps the board, the plate, the parts on
    and under the PCB, the battery, the knob or a keycap at the bottom of its travel, and where the
    battery or the case foam meets the solder joints under the PCB with the stack pressed down. All
    should be 0. The keycaps are taken at their largest (CAP_SIZE_TOL) and lowest (a recessed stem),
    and grown by the plate's float in its gasket pockets, so the deck clears them wherever it settles."""
    pcb = Pos(0, 0, -C.PCB_T) * extrude(face(h["outline"]), C.PCB_T, dir=UP)
    x0, y0, x1, y1 = h["controller"]
    (cx, cy) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    controller = Pos(cx, cy, -C.PCB_T - C.CONTROLLER_DEPTH) * Box(x1 - x0, y1 - y0, C.CONTROLLER_DEPTH, align=Z)
    rx, ry = xy(h["reset"])
    button = Pos(rx, ry, -C.PCB_T - RESET_BUTTON_H) * Box(6.2, 6.2, RESET_BUTTON_H, align=Z)
    caps = switches = None
    for k in h["keys"]:
        x, y = xy((k["x"], k["y"]))
        grow = 2 * (C.CAP_SIZE_TOL + C.POCKET_CLEAR)
        cap = Pos(x, y, C.PLATE_TOP + C.CAP_SKIRT - C.CAP_STEM_RECESS - C.KEY_TRAVEL) * Rot(0, 0, -k["rot"]) * Box(
            k["w"] * 19.05 - C.CAP_GAP + grow, k["h"] * 19.05 - C.CAP_GAP + grow, 10, align=Z)
        sw = Pos(x, y, 0) * Rot(0, 0, -k["rot"]) * Box(C.CUTOUT, C.CUTOUT, C.PLATE_BOT, align=Z)
        caps = cap if caps is None else caps + cap
        switches = sw if switches is None else switches + sw
    # the OLED module in the top frame: the parts on its back, its board with its four holes, and the
    # glass on it; and the plug in its footprint on the PCB, under it
    glass_z = C.OLED_Z[0] + C.OLED_BOARD_T
    (gx0, gy0, gx1, gy1), _ = C.oled_glass(h)
    oled = (Pos(0, 0, C.OLED_Z[0] - C.OLED_BACK_H) * extrude(rect(h["oled"]), C.OLED_BACK_H + C.OLED_BOARD_T, dir=UP)
            + Pos(0, 0, glass_z) * extrude(rect((gx0, gy0, gx1, gy1)), C.OLED_Z[1] - glass_z, dir=UP))
    for p in C.oled_holes(h):
        oled -= cylinder(p, C.OLED_HOLE_D, C.OLED_Z[0] - C.OLED_BACK_H - 1, glass_z + EPS)
    plug = Pos(0, 0, 0) * extrude(rect(C.oled_plug(h)), C.OLED_PLUG[2], dir=UP)
    encoder = knob = None
    for p in h["enc"]:
        x, y = xy(p)
        e = Pos(x, y, 0) * Box(C.ENC_BODY, C.ENC_BODY, C.ENC_BODY_H, align=Z) + cylinder(p, C.ENC_BUSHING_D, 0, C.ENC_BUSHING_TOP)
        kn = cylinder(p, C.KNOB_D, C.KNOB_Z, C.KNOB_Z + C.KNOB_H)
        encoder = e if encoder is None else encoder + e
        knob = kn if knob is None else knob + kn
    standoffs = None
    for p in h["holes"].values():
        so = cylinder(p, C.SHIM_D, 0, C.SHIM_T) + cylinder(p, C.STANDOFF_D, C.SHIM_T, C.PLATE_BOT)
        standoffs = so if standoffs is None else standoffs + so
    x0, y0, x1, y1 = C.battery(h)["cell"]
    (bx, by) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    cell = lambda lift: Pos(bx, by, C.CAVITY_Z - C.BAY_DEPTH + lift) * Box(
        x1 - x0, y1 - y0, C.BATTERY_STACK_T, align=Z)
    battery = cell(0.0)
    tall = None
    for t in h["tall"]:
        (tx, ty) = xy(((t[0] + t[2]) / 2, (t[1] + t[3]) / 2))
        b = Pos(tx, ty, C.CAVITY_Z + C.CASE_FOAM_T - 1.0) * Box(t[2] - t[0], t[3] - t[1], -C.PCB_T - C.CAVITY_Z - C.CASE_FOAM_T + 1.0, align=Z)
        tall = b if tall is None else tall + b
    out = {}

    def check(name, part, solids):
        for what, solid in solids:
            if solid is None: continue
            v = (part & solid).volume
            if v > 1e-3: out[f"{name} x {what}"] = v

    for name, part in (("bottom", bottom), ("top", top)):
        check(name, part, (("pcb", pcb), ("plate", plt), ("controller", controller), ("reset button", button),
                           ("reset button, stack pressed down", Pos(0, 0, -C.FLOAT_GAP) * button),
                           ("keycaps", caps), ("oled", oled), ("battery", battery), ("encoder", encoder),
                           ("knob", knob), ("knob, stack pressed down and knob pushed", Pos(0, 0, -C.FLOAT_GAP - C.ENC_PUSH) * knob)))
    check("plate foam", foam["plate"], (("switches", switches), ("encoder", encoder), ("oled", oled),
                                        ("standoffs", standoffs), ("plate", plt)))
    # the OLED stays with the top frame while the plate floats in its gasket pockets
    for dx, dy, dz in ((C.POCKET_CLEAR, 0, C.FLOAT_UP), (-C.POCKET_CLEAR, 0, C.FLOAT_UP),
                       (0, C.POCKET_CLEAR, C.FLOAT_UP), (0, -C.POCKET_CLEAR, C.FLOAT_UP)):
        check("oled", oled, ((f"plate floated ({dx:g}, {dy:g}, {dz:g})", Pos(dx, dy, dz) * plt),
                             (f"plug floated ({dx:g}, {dy:g}, {dz:g})", Pos(dx, dy, dz) * plug)))
    check("oled plug", plug, (("plate", plt), ("plate foam", foam["plate"]), ("switches", switches), ("encoder", encoder)))
    check("switch pads", foam["pads"], (("switches", switches), ("encoder", encoder),
                                         ("standoffs", standoffs), ("plate foam", foam["plate"])))
    for g in ("lower gaskets", "upper gaskets"):
        check(g, foam[g], (("bottom", bottom), ("top", top), ("plate", plt), ("pcb", pcb)))
    check("case foam", foam["case"], (("bottom", bottom), ("controller", controller), ("reset button", button),
                                      ("battery", battery), ("tall parts under the pcb", tall)))
    # the battery and the case foam against the sockets, diodes and the tall parts under the PCB, the stack pressed down
    underside = Pos(0, 0, -C.PCB_T - C.UNDERSIDE_H) * extrude(face(h["outline"]), C.UNDERSIDE_H, dir=UP)
    lowered = lambda s: Pos(0, 0, C.FLOAT_GAP) * s
    check("battery (stack pressed down)", cell(C.FLOAT_GAP), (("parts under the pcb", underside), ("controller", controller),
                                                              ("reset button", button)))
    check("case foam (stack pressed down)", lowered(foam["case"]), (("parts under the pcb", underside),))
    return out


def main():
    import gen_models
    if abs(gen_models.LIFT - C.OLED_Z[0]) > 1e-6:
        sys.exit(f"gen_models.LIFT {gen_models.LIFT} is not case_geometry.OLED_Z[0] {C.OLED_Z[0]:.2f}")
    OUT.mkdir(exist_ok=True)
    parts = []
    for side, h in C.halves().items():
        bottom, top, plt, tab_list, screws = build(h)
        for name, part in (("bottom", bottom), ("top", top), ("plate", plt)):
            part.color = PLATE_COLOUR if name == "plate" else CASE_COLOUR
            export_step(part, str(out_path(name, "step", side)))
            export_stl(part, str(out_path(name, "stl", side)), tolerance=0.02, angular_tolerance=0.2)
            bb = part.bounding_box()
            print(f"keygen-{side}-{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
                  f"{part.volume / 1000:.1f} cm3, valid {part.is_valid}")
            part.label = f"{side} {name}"
            parts.append(part)
        foam = foam_solids(h)
        for name, f in foams(h).items():
            w, l = write_foam(side, name, f)
            print(f"keygen-{side}-{name}-foam: {FOAM_NAMES[name]}, {w:.1f} x {l:.1f} mm, z {FOAM_Z[name][0]:.1f}..{FOAM_Z[name][1]:.1f}")
        for name, f in foam.items():
            f.color = FOAM_COLOURS[name]; f.label = f"{side} {name} foam"
            export_step(f, str(out_path("foam", "step", side, f"{name}-foam")))
        pads, clipped = switch_pads(h)
        pads.color = PAD_COLOUR; pads.label = f"{side} switch pads"
        export_step(pads, str(out_path("foam", "step", side, "switch-pads")))
        print(f"keygen-{side}-switch-pads: {len(h['keys'])} Poron rings, {C.SWITCH_PAD:g} mm, "
              f"{clipped} clipped round a standoff, z {C.PE_Z[0]:.1f}..{C.PE_Z[1]:.1f}")
        foam["pads"] = pads
        for name, g in gaskets(tab_list).items():
            g.color = PAD_COLOUR; g.label = f"{side} {name} gaskets"
            export_step(g, str(out_path("foam", "step", side, f"{name}-gaskets")))
            foam[f"{name} gaskets"] = g
        print(f"keygen-{side}-gaskets: {len(tab_list)} Poron strips {C.GASKET_L:g} x {C.GASKET_W:g} x {C.GASKET_T:g} mm "
              f"under the tabs and {len(tab_list)} over them, squeezed to {C.GASKET_T - C.GASKET_SQUEEZE:g} mm")
        print(f"{side}: {len(tab_list)} gasket tabs, {len(screws)} case screws (M2 x {SCREW_L:g} from below, heads "
              f"{CBORE_TOP - HEAD_H - C.BOTTOM_Z:.1f} mm up in the floor, {C.TOP_Z - C.SPLIT_Z - INSERT_DEPTH:.1f} mm "
              f"of frame over the inserts)")
        broken = screw_walls(bottom, top, screws)
        print(f"{side} screw walls: " + (f"thin round screws {broken}" if broken else "solid round every screw"))
        for k, v in C.deck_clearances(h).items():
            print(f"{side} deck: {k} {v:.1f} mm")
        for k, v in C.standoff_threads().items():
            print(f"{side} standoffs: {k} {v:.1f} mm")
        top_z, gap, pressed = C.battery_heights()
        print(f"{side} battery: {C.BATTERY_L:g} x {C.BATTERY_W:g} x {C.BATTERY_STACK_T:g} mm installed envelope in the "
              f"floor bay, {gap:.1f} mm under the solder joints, {pressed:.1f} mm with the stack pressed down")
        clash = fit_check(h, bottom, top, plt, foam)
        print(f"{side} fit check: " + (", ".join(f"{k} {v:.2f} mm3" for k, v in clash.items()) or "no overlaps"))
    export_step(Compound(children=parts), str(OUT / "keygen-case.step"))
    print(f"wrote {OUT.relative_to(C.ROOT)}/")


if __name__ == "__main__":
    main()
