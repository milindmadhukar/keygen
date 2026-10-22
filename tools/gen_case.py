#!/usr/bin/env python3
"""The 3D-printed case: a bottom shell and a top frame per half, gasket-mounted.

case/bottom/{stl,step}/keygen-{left,right}-bottom.*   floor, battery bay, walls, gasket ledges, insert holes
case/top/{stl,step}/keygen-{left,right}-top.*         frame round the plate and a deck over it, gasket
                                                      pockets, screw holes
case/plate/step/keygen-{left,right}-plate.step        the plate, for the fit check (it is made from the Gerbers)
case/foam/{dxf,svg}/keygen-{left,right}-{plate,case}-foam.*   the two foam layers, to cut
case/foam/step/keygen-{left,right}-*-foam.step        the same layers as solids, in place
case/keygen-case.step                                 all six parts in place

The plate and PCB, tied together by standoffs, float on the plate's gasket tabs. Each tab sits
between two Poron strips: one on a ledge in the bottom shell, one under the top frame. The two
parts are screwed together through the walls (M2 x 6 into M2 heat-set inserts). The bottom shell
has an open slot under the USB-C, a slot for the power switch lever (with the wall thinned in
front of both), and a guided pinhole under the reset button. The LiPo lies in a bay sunk into the
floor, clear of the solder joints above it. The underside is flat.

The top frame's deck is level with its rim and covers the plate everywhere but the keycaps, the
OLED (a window that opens towards the thumbs) and the encoder (a hole round its bushing, under the
knob).

The foam, from the top: EVA plate foam under the plate, cut round the switches, the encoder, the
OLED and the standoffs, resting on the Poron ring switch pads stuck on the PCB under each switch
(the 0.5 mm PE_Z layer; they come ready-made, so it has no file); and EVA case foam on the floor
round the battery bay, the controller, the tall parts under the PCB and the reset tube. They are
written as 1:1 DXF and SVG, seen from above.

Geometry and the stack come from case_geometry.py, so rerun this after any PCB change. Needs
build123d next to KiCad's pcbnew; see the README:

    ~/.venvs/keygen-cad/bin/python tools/gen_case.py
"""
import math, sys
from pathlib import Path

from build123d import (Align, Box, Circle, Color, Compound, Cone, Cylinder, ExportDXF, ExportSVG, Face, Kind, Polygon, Pos,
                       Rectangle, Rot, Unit, Wire, export_step, export_stl, extrude, loft, offset)

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
INSERT_D, INSERT_DEPTH = 3.2, 5.0      # hole for an M2 x 3 heat-set insert, with room for the melt
SCREW_D = 2.4                          # M2 clearance
CBORE_D, CBORE_DEPTH = 4.4, 2.2        # M2 x 6 socket head, flush with the top
USB_SLOT_W = C.NANO_W + 2.0            # the whole nice!nano end, which overhangs the slanted edge
LEVER_SLOT_W, LEVER_SLOT_H = 9.0, 3.4
RESET_HOLE_D, RESET_TUBE_D = 2.0, 5.0  # paperclip hole, and the guide tube round it
RESET_BUTTON_H = 5.0                   # 6 mm tact switch, 5 mm tall, on the PCB underside
EPS = 0.01
CASE_COLOUR, PLATE_COLOUR = Color(0x2E2E33), Color(0x111113)
FOAM_COLOURS = {"plate": Color(0x8C6E7A), "case": Color(0x6B7078)}

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

    # top frame: the ring round the plate from the split up to the gasket ceiling, then the deck over
    # the plate, level with the rim, with windows for the keycaps and the OLED and a hole for the encoder
    top = Pos(0, 0, C.SPLIT_Z) * extrude(outer - inner, C.CEIL_Z - C.SPLIT_Z, dir=UP)
    top += Pos(0, 0, C.CEIL_Z) * extrude(deck(h), C.TOP_Z - C.CEIL_Z, dir=UP)
    z0, z1 = C.CEIL_Z - 0.1, C.TOP_Z + 0.1
    top -= loft([Pos(0, 0, z0) * rect(C.oled_window(h, z0)), Pos(0, 0, z1) * rect(C.oled_window(h, z1))], ruled=True)
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


def deck(h):
    """The top frame in plan at deck level: the case outline less a window per keycap, the OLED
    window and the encoder hole. Webs under 1 mm wide, and any islands they leave, are dropped."""
    outer = SPoly(h["outline"]).buffer(C.WALL_OUT, join_style="mitre", mitre_limit=10)
    holes = [sq((k["x"], k["y"]), k["h"] * 19.05 - C.CAP_GAP + 2 * C.CAP_CLEAR, k["rot"],
                k["w"] * 19.05 - C.CAP_GAP + 2 * C.CAP_CLEAR) for k in h["keys"]]
    holes += [circ(p, C.ENC_HOLE_D) for p in h["enc"]]
    holes.append(box(*C.oled_window(h, C.CEIL_Z)))
    return to_face(opened(outer.difference(unary_union(holes)), 0.5))


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

    # plate foam, on the switch pads under the plate: the plate's cut-outs, a little larger, and the
    # drilled pads
    plate_foam = board_less(board, [cut_square((k["x"], k["y"]), C.FOAM_SWITCH_CUT, k["rot"]) for k in h["keys"]]
                            + pads + standoffs + encoders + [cut_rect(grown(h["oled"], C.OLED_CLEAR + clear))])

    # case foam, on the floor: the cavity less the battery bay and everything that hangs below the PCB
    g = C.WALL_IN - C.FOAM_WALL_CLEAR
    cavity = (board[0].buffer(g, join_style="mitre", mitre_limit=10), offset(board[1], g, kind=Kind.INTERSECTION))
    under = [cut_rect(C.battery(h)["bay"]), cut_rect(grown(h["controller"], C.FOAM_PART_CLEAR)),
             cut_circle(h["reset"], RESET_TUBE_D + 2 * C.FOAM_PART_CLEAR)]
    under += [cut_rect(grown(t, C.FOAM_PART_CLEAR)) for t in h["tall"]]
    case_foam = board_less(cavity, under)
    return {"plate": plate_foam, "case": case_foam}


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


KEY_TRAVEL = 4.0
CAP_SKIRT = 7.5                        # keycap skirt bottom above the plate at rest (DSA on MX, about)


def fit_check(h, bottom, top, plt, foam):
    """Volumes (mm3) where a case part or a foam layer overlaps the board, the plate, the parts on
    and under the PCB, the battery, the knob or a keycap at the bottom of its travel, and where the
    battery or the case foam meets the solder joints under the PCB with the stack pressed down. All
    should be 0."""
    pcb = Pos(0, 0, -C.PCB_T) * extrude(face(h["outline"]), C.PCB_T, dir=UP)
    x0, y0, x1, y1 = h["controller"]
    (cx, cy) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    controller = Pos(cx, cy, -C.PCB_T - C.CONTROLLER_DEPTH) * Box(x1 - x0, y1 - y0, C.CONTROLLER_DEPTH, align=Z)
    rx, ry = xy(h["reset"])
    button = Pos(rx, ry, -C.PCB_T - RESET_BUTTON_H) * Box(6.2, 6.2, RESET_BUTTON_H, align=Z)
    caps = switches = None
    for k in h["keys"]:
        x, y = xy((k["x"], k["y"]))
        cap = Pos(x, y, C.PLATE_TOP + CAP_SKIRT - KEY_TRAVEL) * Rot(0, 0, -k["rot"]) * Box(
            k["w"] * 19.05 - C.CAP_GAP, k["h"] * 19.05 - C.CAP_GAP, 10, align=Z)
        sw = Pos(x, y, 0) * Rot(0, 0, -k["rot"]) * Box(C.CUTOUT, C.CUTOUT, C.PLATE_BOT, align=Z)
        caps = cap if caps is None else caps + cap
        switches = sw if switches is None else switches + sw
    x0, y0, x1, y1 = h["oled"]
    (ox, oy) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    oled = Pos(ox, oy, C.OLED_Z[0]) * Box(x1 - x0, y1 - y0, C.OLED_Z[1] - C.OLED_Z[0], align=Z)
    x0, y0, x1, y1 = h["header"]
    (hx, hy) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    header = Pos(hx, hy, 0) * Box(x1 - x0, y1 - y0, C.OLED_Z[0], align=Z)
    encoder = knob = None
    for p in h["enc"]:
        x, y = xy(p)
        e = Pos(x, y, 0) * Box(C.ENC_BODY, C.ENC_BODY, C.ENC_BODY_H, align=Z) + cylinder(p, C.ENC_BUSHING_D, 0, C.ENC_BUSHING_TOP)
        kn = cylinder(p, C.KNOB_D, C.ENC_BUSHING_TOP, C.ENC_BUSHING_TOP + C.KNOB_H)
        encoder = e if encoder is None else encoder + e
        knob = kn if knob is None else knob + kn
    kinds = C.standoffs(h)
    standoffs = heads = None
    for ref, p in h["holes"].items():
        so = cylinder(p, C.STANDOFF_D, 0, C.PLATE_BOT)
        standoffs = so if standoffs is None else standoffs + so
        if kinds[ref][0] == "screwed":
            hd = cylinder(p, C.SCREW_HEAD_D, C.PLATE_TOP, C.PLATE_TOP + C.SCREW_HEAD_H)
            heads = hd if heads is None else heads + hd
    x0, y0, x1, y1 = C.battery(h)["cell"]
    (bx, by) = xy(((x0 + x1) / 2, (y0 + y1) / 2))
    cell = lambda lift: Pos(bx, by, C.CAVITY_Z - C.BAY_DEPTH + lift) * Box(
        x1 - x0, y1 - y0, C.BATTERY_T + C.BATTERY_GROWTH, align=Z)
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
                           ("keycaps", caps), ("oled", oled), ("battery", battery), ("encoder", encoder),
                           ("knob", knob), ("plate screw heads", heads)))
    check("plate foam", foam["plate"], (("switches", switches), ("encoder", encoder), ("oled", oled),
                                        ("oled header", header), ("standoffs", standoffs), ("plate", plt)))
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
    OUT.mkdir(exist_ok=True)
    parts = []
    for side, h in C.halves().items():
        bottom, top, plt, n_tabs, n_screws = build(h)
        for name, part in (("bottom", bottom), ("top", top), ("plate", plt)):
            part.color = PLATE_COLOUR if name == "plate" else CASE_COLOUR
            export_step(part, str(out_path(name, "step", side)))
            if name != "plate":
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
        print(f"{side}: {n_tabs} gasket tabs, {n_screws} case screws")
        for k, v in C.deck_clearances(h).items():
            print(f"{side} deck: {k} {v:.1f} mm")
        top_z, gap, pressed = C.battery_heights()
        print(f"{side} battery: {C.BATTERY_L:g} x {C.BATTERY_W:g} x {C.BATTERY_T:g} mm (+{C.BATTERY_GROWTH:g}) in the "
              f"floor bay, {gap:.1f} mm under the solder joints, {pressed:.1f} mm with the stack pressed down")
        clash = fit_check(h, bottom, top, plt, foam)
        print(f"{side} fit check: " + (", ".join(f"{k} {v:.2f} mm3" for k, v in clash.items()) or "no overlaps"))
    export_step(Compound(children=parts), str(OUT / "keygen-case.step"))
    print(f"wrote {OUT.relative_to(C.ROOT)}/")


if __name__ == "__main__":
    main()
