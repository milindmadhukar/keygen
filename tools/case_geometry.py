#!/usr/bin/env python3
"""Shared geometry for the switch plate (gen_plate.py) and the case (gen_case.py).

Everything is read from pcb/keygen.kicad_pcb and the key tables, so the plate and the case follow
the PCB. Coordinates are KiCad board mm (x right, y down); z is mm above the PCB's top surface.

The stack, bottom to top:

  case floor        BOTTOM_Z .. CAVITY_Z, with the battery bay sunk BAY_DEPTH into it
  cavity            the socketed controller hangs CONTROLLER_DEPTH below the PCB; the LiPo lies
                    in its bay on the floor, clear of the solder joints above it
  PCB               -PCB_T .. 0
  plate             PLATE_BOT .. PLATE_TOP (MX: plate top 5 mm above the PCB)
  gasket tabs       on the plate edge, between two Poron strips: the lower one on the bottom
                    shell's ledge (LEDGE_Z), the upper one under the top frame (CEIL_Z)
  top frame         SPLIT_Z .. TOP_Z round the edge; inside it a deck, CEIL_Z .. TOP_Z, covers the
                    plate everywhere but the keycaps, the OLED and the encoder

The foam: Poron ring switch pads on the PCB round the switches, EVA plate foam taped to the
plate's underside, and EVA case foam on the floor round the battery bay (PE_Z, PLATE_FOAM_Z,
CASE_FOAM_Z).

The plate rests on M2 standoffs, each screwed to the PCB from below; the switches, clipped into
the plate and plugged into the PCB's sockets, hold the two together, and they float on the tabs.
Nothing screws the plate to the standoffs, or the PCB to the case. The bottom shell and the top frame are screwed together from below, up through
the walls into heat-set inserts in the top frame.

    python3 tools/case_geometry.py      # print the tabs, case screws and plate standoffs
"""
import functools, math, sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import gen_pcb as G
import gen_schematic as g

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
MM = pcbnew.ToMM

# ---------------------------------------------------------------- stack (mm)
PCB_T = 1.6
PLATE_T = 1.5                  # clear polycarbonate sheet, CNC-routed; the MX clips are made for 1.5 mm
PLATE_TOP = 5.0
PLATE_BOT = PLATE_TOP - PLATE_T
CAP_SKIRT = 6.7                # keycap skirt bottom above the plate at rest: the MX slider's shoulder, where
                               # a DSA cap's flush stem seats (SW_Cherry_MX_PCB.stp: 11.74 mm above the PCB)
CAP_H = 7.67                   # DSA 1u cap, skirt to top (Keycap_DSA_1u.stl)
CAP_STEM_RECESS = 1.0          # a cap whose stem is recessed into it sits up to this much lower
KEY_TRAVEL = 4.0               # MX total travel; the Akko V3 is 3.8
GASKET_T = 3.0                 # Poron strip, uncompressed
GASKET_SQUEEZE = 1.0           # how much each strip is compressed when the case is closed: a third, so
                               # a printed part ±0.2 mm off still leaves every strip 27-40 % squeezed
GASKET_L, GASKET_W = 12.0, 4.0 # each strip: along the tab's edge, and outward across it
LEDGE_Z = PLATE_BOT - (GASKET_T - GASKET_SQUEEZE)
CEIL_Z = PLATE_TOP + (GASKET_T - GASKET_SQUEEZE)
SPLIT_Z = PLATE_BOT            # bottom shell / top frame joint
TOP_Z = CEIL_Z + 2.0
CONTROLLER_DEPTH = g.CONTROLLER_H + g.NANO_T + 2.9   # socketed-controller envelope below the PCB's underside: its
                               # parts and trimmed pin tails (about 1.5 mm) under the board, and 1.4 mm to spare
FLOAT_GAP = 1.5                # under the controller, so the floating stack can travel
CAVITY_Z = -PCB_T - CONTROLLER_DEPTH - FLOAT_GAP
FLOOR_T = 3.0
BOTTOM_Z = CAVITY_Z - FLOOR_T

# ---------------------------------------------------------------- plan view (mm)
CUTOUT = 14.0                  # MX switch cut-out
CUTOUT_R = 0.5                 # its corner radius (the fab's router bit)
SWITCH_FLANGE = 15.6           # MX top housing, resting on the plate
CAP_GAP = 0.95                 # keycap = n * 19.05 - this
CAP_SIZE_TOL = 0.15            # real DSA skirts are up to 18.4 mm (KeyV2 18.24): this much wider each side
ENC_CUTOUT = 15.0              # square plate cut-out around the selected HongYan EC11H body
OLED_W, OLED_H = 27.5, 27.8    # 0.96 in. OLED module (GME12864-11 drawing), held in the top frame over a plate window
OLED_HDR_IN = 1.5              # its pin row from its pin edge, over the PCB's 1x4 footprint it plugs into
OLED_CLEAR = 1.0               # module to plate window, each side
HOLE_D = 2.2
TAB_W, TAB_D = 12.0, 5.0       # gasket tab: width along the edge, depth beyond the outline
TABS_PER_HALF = 8
POCKET_CLEAR = 0.5             # tab to pocket, each side, so the tab floats
WALL_IN = 1.0                  # PCB/plate edge to the case's inner wall
WALL_OUT = 7.5                 # PCB/plate edge to the case's outer wall
PORT_WALL = 1.5                # wall in front of the controller's pocket, and round the switch lever
PORT_KEEP = 22.0               # no tab this close to the USB-C or switch lever
PORT_KEEP_SCREW = 16.0         # no case screw this close to them
NANO_W, NANO_L = 18.0, 33.5    # nice!nano v2 board
USB_OVERHANG = 1.0             # its USB-C end reaches this far past the PCB edge
CONTROLLER_H, NANO_T = g.CONTROLLER_H, g.NANO_T   # the controller's sockets, pin carriers and board (set as measured in gen_schematic.py)
USB_Z = -PCB_T - CONTROLLER_H - NANO_T / 2   # the USB-C receptacle's centre, on the board's mid-plane (mid-mount)
PLUG_W, PLUG_H = 12.35, 6.5    # USB-C cable overmould: the largest the USB-C spec recommends
FLOAT_UP = 1.0                 # the floating stack lifting, the upper gasket strips squeezed further
PORT_CLEAR = 0.4               # plug to port at the end of its float, each side: print error
PORT_R = 2.0                   # port corner radius; overmoulds are rounded at least this much
NANO_POCKET_CLEAR = 0.3        # controller end to its pocket in the wall, past the stack's float
ANTENNA_LEN = 12.0             # chip antenna end of the nice!nano
ANTENNA_KEEP = 15.0            # no metal (inserts, screws) this close to it
BATTERY_W, BATTERY_L, BATTERY_T = 60.0, 88.0, 5.0   # the largest cell bom.csv allows, protection board included
BATTERY_SIZE_TOL = 0.3         # delivered cell thickness above its nominal rating
BATTERY_GROWTH = 0.5           # pouch swelling with age
BATTERY_TAPE = 0.3             # double-sided mounting tape
BATTERY_STACK_T = BATTERY_T + BATTERY_SIZE_TOL + BATTERY_GROWTH + BATTERY_TAPE
BATTERY_CLEAR = 1.5            # cell to the bay wall, each side
BAY_DEPTH = 1.6                # the bay is sunk this far into the floor, leaving 1.4 mm under the cell
STEEL_D, STEEL_T = 40.0, 0.6   # round steel plate the tenting wedge's magnets hold to (LIRAMARK)
STEEL_POCKET_D = STEEL_D + 0.6 # its pocket in the floor's underside, 0.3 mm round the plate,
STEEL_POCKET_DEPTH = 1.0       # deep enough for the plate and its tape (about 0.75 mm) with the pocket's
                               # bridged ceiling sagging a little, so the plate sits flush, like the screws
STEEL_KEEP = 2.0               # pocket to the battery bay, the screw counterbores and the reset pinhole
STEEL_EDGE_KEEP = 12.0         # pocket to the floor's edge, which keeps it clear of the feet
FOOT_D, FOOT_H = 8.0, 3.0      # silicone bumper, stuck on the floor by hand
FOOT_IN, FOOT_TOP_IN = 7.0, 17.0   # foot centres from the floor's edges, and the top two from its top edge
WEDGE_ANGLE = 13.0             # the optional tenting wedge lifts the inner edge by this much
WEDGE_EDGE = 4.0               # its thickness along the outer edge
WEDGE_GAP = 0.3                # its top face under the floor: the half stands on its feet, in the recesses
FOOT_RECESS_D = 12.0           # recess round each foot, which takes a foot stuck 2 mm off its mark
MAGNET_D, MAGNET_T = 10.0, 3.0 # N35 disc magnet, four per wedge, superglued in under the steel disc
MAGNET_POCKET_D = 10.3         # its pocket in the wedge's top face, with room for the glue
MAGNET_RECESS = 0.1            # magnet top under the wedge's top face
MAGNET_R = 13.0                # the magnets' circle round the steel disc's centre: all four under the disc
CBORE_MOUTH_R = 2.8            # a case screw's counterbore with its chamfered mouth (gen_case.py)
RESET_MOUTH_R = 2.0            # the reset pinhole's chamfered mouth (gen_case.py)
UNDERSIDE_H = 2.0             # hotswap sockets (1.85 mm) and DO-35 diodes (1.75 mm body) under the PCB
TALL_CLEAR = 3.0               # cell to the controller, battery connector, buttons, encoder and OLED pins
TALL_REFS = ("U", "BT", "ENC", "J")   # and the slide switch and reset button (SWx90, SWx91)

# ---------------------------------------------------------------- top frame deck (mm)
CAP_CLEAR = 1.2                # keycap to its window in the deck, each side: covers CAP_SIZE_TOL, the plate
                               # floating POCKET_CLEAR in its gasket pockets, and cap wobble and print error
CAP_CHAMFER = 0.4              # 45 degree chamfer round each keycap window at the deck top, the face printed
                               # on the bed, so first-layer squish does not narrow the window where caps enter
DECK_MIN_WEB = 4.0             # narrowest web or finger of deck between the windows; anything thinner
                               # is trimmed back to a rounded end, so no point of the printed deck snaps off
ENC_BODY, ENC_BODY_H = 12.5, 6.8         # HongYan EC11H: 12 x 11.7 plan, 6.5 tall; include drawing tolerances
ENC_BUSHING_D, ENC_BUSHING_TOP = 7.0, 14.1   # HongYan bushing: 6.5 + 7 mm nominal, plus both tolerances
ENC_HOLE_D = 9.0               # deck hole round the bushing; the knob hides it
ENC_RECESS_TOP = 7.4           # local underside relief: 0.6 mm above the tallest encoder body
ENC_SHAFT_TOP = 6.5 + 20.0     # HongYan EC11H-...ZD20F10: the 20 mm shaft is measured from the 6.5 mm body's top
ENC_FLAT_FROM = ENC_SHAFT_TOP - 10.0   # its D flat, the top 10 mm
ENC_PUSH = 0.7                 # push switch travel, 0.5 +0.2
KNOB_D, KNOB_H = 17.0, 13.0    # knob: an aluminium cup round a plastic hub with a blind D hole (gen_models.py)
KNOB_DEPTH = 11.0              # from its bottom edge up to where the shaft stops inside it (measure)
KNOB_HUB_UP = 2.0              # its hub's bottom face, this far up inside from its bottom edge (measure)
KNOB_GAP = max(3.0, ENC_BUSHING_TOP + ENC_PUSH + 0.3 - KNOB_HUB_UP - TOP_Z)   # knob above the deck top: clear of
                               # the deck with the stack pressed down and the knob pushed, and its hub clear of the
                               # bushing while pushed
KNOB_Z = TOP_Z + KNOB_GAP      # the knob's underside (gen_schematic.KNOB_MODEL_Z, for the 3D model, matches)
ENC_SHAFT_CUT = ENC_SHAFT_TOP - (KNOB_Z + KNOB_DEPTH)   # cut this much off the shaft so the knob sits at KNOB_Z
OLED_GLASS = (26.7, 19.26, 1.6)   # glass with its tape (the drawing allows up to 2.3), centred across the module
OLED_GLASS_IN = 4.27           # glass from the pin edge (and from the far edge)
OLED_ACTIVE = (21.744, 10.864) # active area, centred across the module,
OLED_ACTIVE_IN = 6.37          # this far from the pin edge
OLED_BOARD_T = 1.2             # the module's PCB
OLED_BACK_H = 1.2              # parts on the module's back (its regulator, SOT-23)
OLED_HOLE_D, OLED_HOLE_IN = 2.0, 2.0   # its four mounting holes, centred this far in from each edge
OLED_FPC_W = 16.0              # the glass's flex cable wraps round the far edge, in a 14 mm notch in the board
OLED_PEG_D = 1.7               # pegs on the boss through the module's holes, located and held by melting
OLED_PEG_PROUD = 1.0           # their tips (or hot glue) this far past the module's back
OLED_PLUG = (19.0, 10.8, 2.8)  # 1x4 right-angle header in J101/J201 and a Dupont plug on it, pointing under the
                               # module: length from the pin row, width, height above the PCB
OLED_LIP = 1.0                 # deck over the glass, round the window: the glass sits this far below the top
OLED_Z = (TOP_Z - OLED_LIP - OLED_GLASS[2] - OLED_BOARD_T, TOP_Z - OLED_LIP)   # module bottom, glass top
OLED_BOSS = 1.5                # the deck thickens down to the module's top, this far round it: the module is
                               # taped to it, its glass in a pocket under the lip
OLED_POCKET_CLEAR = 0.15       # glass to its pocket, each side
OLED_JOINT_RELIEF = (1.0, 1.5) # over the module's four solder joints: past their pads each side, and deep
OLED_MARGIN = 1.0              # lip window past the active area at the lip's underside
OLED_VIEW = 50.0               # degrees from vertical, from the thumb side: the window shows all of
                               # the active area at this angle
STANDOFF_D = 4.0               # M2 hex standoff, across the corners
STANDOFF_L = 3.0               # M2 x 3 female-female; 3.5 mm is not a stock length
SHIM_T, SHIM_D = 0.5, 5.0      # DIN 988 shim (2 x 5 x 0.5) under each standoff, on the PCB, so
                               # standoff and shim fill the plate gap
SCREW_L = 5.0                  # M2 button head (ISO 7380), up through the PCB and shim into each standoff:
                               # nearly its whole thread. Its tip ends 0.1 mm under the standoff's top, and
                               # a long screw's tip goes on up into the plate's 2.2 mm hole
SCREW_L_TOL = 0.25             # ISO 4762/7380 length tolerance (js15) for a 3-6 mm screw

# ---------------------------------------------------------------- foam (mm)
PE_T = 0.5                     # Poron ring switch pads on the PCB, one per switch
PLATE_FOAM_T = 2.0             # EVA plate foam taped to the plate's underside (3.0 at most, to the switch pads)
CASE_FOAM_T = 5.0              # EVA case foam on the floor
PE_Z = (0.0, PE_T)
PLATE_FOAM_Z = (PLATE_BOT - PLATE_FOAM_T, PLATE_BOT)
SWITCH_PAD = 18.0              # Poron ring switch pad: a square ring this wide outside,
SWITCH_PAD_BAND = 1.9          # this wide all round (14.2 mm open middle),
SWITCH_PAD_R = 1.0             # its outer corners rounded,
SWITCH_PAD_NOTCH = (4.5, 1.0)  # and a notch this wide and deep in the inner edge on the clip sides
FOAM_SWITCH_CUT = 14.4         # plate foam cut-out per switch, notched like the switch pads (SWITCH_PAD_NOTCH)
                               # on the clip sides, where the switch's latches spring out under the plate
FOAM_HOLE_CLEAR = 0.3          # foam to pins, pads, LED windows and standoffs, each side
FOAM_PART_CLEAR = 1.0          # case foam to the parts under the PCB and the reset tube, each side
FOAM_WALL_CLEAR = 0.5          # case foam to the case wall


# ---------------------------------------------------------------- 2D helpers
def inside(p, poly):
    x, y = p; c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c


def seg_dist(p, a, b):
    (ax, ay), (bx, by), (px, py) = a, b, p
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def poly_dist(p, poly):
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def rect_dist(p, x0, y0, x1, y1):
    return math.hypot(max(x0 - p[0], 0, p[0] - x1), max(y0 - p[1], 0, p[1] - y1))


def local(p, cx, cy, rot):
    """p in the frame of a key at (cx, cy) rotated rot degrees clockwise."""
    a = math.radians(rot); dx, dy = p[0] - cx, p[1] - cy
    return dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)


def rects_dist(a, b):
    """Gap between two axis-aligned rectangles (x0, y0, x1, y1); 0 if they touch or overlap."""
    return math.hypot(max(b[0] - a[2], a[0] - b[2], 0), max(b[1] - a[3], a[1] - b[3], 0))


def square_dist(p, key, size):
    """Distance from p to a key-aligned square of side `size` (0 inside)."""
    lx, ly = local(p, key["x"], key["y"], key["rot"])
    return math.hypot(max(abs(lx) - size / 2, 0), max(abs(ly) - size / 2, 0))


# ---------------------------------------------------------------- the board
class Edge:
    """One outline segment, with its outward normal."""
    def __init__(self, a, b, poly):
        self.a, self.b = a, b
        self.len = math.dist(a, b)
        self.d = ((b[0] - a[0]) / self.len, (b[1] - a[1]) / self.len)
        n = (self.d[1], -self.d[0])
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        self.n = n if not inside((mid[0] + n[0] * 0.5, mid[1] + n[1] * 0.5), poly) else (-n[0], -n[1])

    def at(self, s, out=0.0):
        return (self.a[0] + self.d[0] * s + self.n[0] * out, self.a[1] + self.d[1] * s + self.n[1] * out)

    def s_of(self, p):
        return (p[0] - self.a[0]) * self.d[0] + (p[1] - self.a[1]) * self.d[1]


def _pads_centre(fp):
    pts = [(MM(p.GetPosition().x), MM(p.GetPosition().y)) for p in fp.Pads()]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


@functools.lru_cache(maxsize=None)
def halves():
    """{'left'|'right': dict(side, outline, edges, windows, keys, holes, drills, enc, oled, header, usb,
    lever, reset, antenna, battery_jack, tall)}. windows are the board's internal cut-outs (the LED
    windows); drills are the drilled pads as (x, y, w, h, round)."""
    b = pcbnew.LoadBoard(str(PCB))
    polys = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(polys, False)
    out = {}
    for i in range(polys.OutlineCount()):
        o = polys.Outline(i)
        poly = [(MM(o.CPoint(j).x), MM(o.CPoint(j).y)) for j in range(o.PointCount())]
        side = "left" if sum(p[0] for p in poly) / len(poly) < 211 else "right"
        out[side] = dict(side=side, outline=poly, edges=[Edge(poly[k], poly[(k + 1) % len(poly)], poly) for k in range(len(poly))],
                         holes={}, enc=[], tall=[], drills=[],
                         windows=[[(MM(polys.Hole(i, j).CPoint(k).x), MM(polys.Hole(i, j).CPoint(k).y))
                                   for k in range(polys.Hole(i, j).PointCount())] for j in range(polys.HoleCount(i))])
    geo = G.key_geometry()
    for side, h in out.items():
        h["keys"] = []
        for r, c, lab, _ in g.KEYS[side]:
            cx, cy, rr, w, hh, _ = geo[(side, r, c)]
            h["keys"].append(dict(label=lab, x=cx + G.OFF[0], y=cy + G.OFF[1], rot=rr, w=w, h=hh))
    for fp in b.GetFootprints():
        ref = fp.GetReference(); p = fp.GetPosition(); x, y = MM(p.x), MM(p.y)
        h = next((h for h in out.values() if inside((x, y), h["outline"])), None)
        if h is None: continue
        if ref.rstrip("0123456789") in TALL_REFS or ref.startswith("SW") and ref[-2:] in ("90", "91"):
            bb = fp.GetBoundingBox(False)
            h["tall"].append((MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())))
        if ref.startswith("BT"): h["battery_jack"] = _pads_centre(fp)
        for pad in fp.Pads():                   # every drilled pad: (x, y, w, h, round), what the foam clears
            if pad.GetDrillSize().x > 0:
                bb = pad.GetBoundingBox(); q = pad.GetPosition()
                w, hh = max(MM(bb.GetWidth()), MM(pad.GetDrillSize().x)), max(MM(bb.GetHeight()), MM(pad.GetDrillSize().y))
                h["drills"].append((MM(q.x), MM(q.y), w, hh, pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE))
        if ref.startswith("H"): h["holes"][ref] = (x, y)
        elif ref.startswith("ENC"): h["enc"].append((x, y))
        elif ref[0] == "J":                     # OLED header: the module stands above its pins
            pins = [(MM(p.GetPosition().x), MM(p.GetPosition().y)) for p in fp.Pads()]
            cx = sum(q[0] for q in pins) / len(pins); py = pins[0][1]
            h["oled"] = (cx - OLED_W / 2, py + OLED_HDR_IN - OLED_H, cx + OLED_W / 2, py + OLED_HDR_IN)
            bb = fp.GetBoundingBox(False)
            h["header"] = (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))
        elif ref[0] == "U":
            bb = fp.GetBoundingBox(False)
            x0, y0, x1, y1 = MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())
            cx = MM(p.x)
            ends = [(cx, y0), (cx, y1)]
            ends.sort(key=lambda e: poly_dist(e, h["outline"]))
            way = 1 if ends[1][1] > ends[0][1] else -1          # from the USB-C end towards the antenna
            edge = min(h["edges"], key=lambda e: seg_dist(ends[0], e.a, e.b))
            y_edge = edge.a[1] + (cx - edge.a[0]) * edge.d[1] / edge.d[0]
            usb_y = y_edge - way * USB_OVERHANG
            far = usb_y + way * NANO_L
            h["usb"] = (cx, usb_y)
            h["controller"] = (cx - NANO_W / 2, min(usb_y, far), cx + NANO_W / 2, max(usb_y, far))
            h["antenna"] = (cx - NANO_W / 2, min(far, far - way * ANTENNA_LEN), cx + NANO_W / 2, max(far, far - way * ANTENNA_LEN))
        elif ref.startswith("SW") and ref[-2:] == "90":
            bb = fp.GetBoundingBox(False)
            c = (MM(bb.GetCenter().x), MM(bb.GetCenter().y))
            h["lever"] = c
        elif ref.startswith("SW") and ref[-2:] == "91":
            h["reset"] = _pads_centre(fp)
    for h in out.values():
        h["port_edge"] = min(h["edges"], key=lambda e: seg_dist(h["usb"], e.a, e.b))
    # the halves mirror each other about this x; the right half's tabs and screws are the left's, mirrored
    mirror_x = (max(p[0] for p in out["left"]["outline"]) + min(p[0] for p in out["right"]["outline"])) / 2
    for h in out.values(): h["mirror_x"] = mirror_x
    return out


def _mirror(h, p):
    return (2 * h["mirror_x"] - p[0], p[1])


# ---------------------------------------------------------------- gasket tabs, case screws, standoffs
def _perimeter(h):
    """[(arc_length_start, edge)] and the total length."""
    acc, out = 0.0, []
    for e in h["edges"]:
        out.append((acc, e)); acc += e.len
    return out, acc


def _near_port(h, p, keep=PORT_KEEP):
    return min(math.dist(p, h["usb"]), math.dist(p, h["lever"])) < keep


def _clear_of_other_edges(h, e, s, out):
    """The point `out` mm outside edge e at s is nearest to e itself (no concave corner close by)."""
    p = e.at(s, out)
    return poly_dist(p, h["outline"]) >= out * 0.99 and not inside(p, h["outline"])


def _spread(cands, total, n):
    """Pick n of the (arc, ...) candidates as evenly spread around the perimeter as possible."""
    best = None
    for off in range(0, int(total / n)):
        picks = []
        for k in range(n):
            t = off + k * total / n
            c = min(cands, key=lambda c: min(abs(c[0] - t), total - abs(c[0] - t)))
            picks.append(c)
        if len({c[0] for c in picks}) < n: continue
        err = max(min(abs(c[0] - (off + k * total / n)), total - abs(c[0] - (off + k * total / n))) for k, c in enumerate(picks))
        if best is None or err < best[0]: best = (err, picks)
    return sorted(best[1], key=lambda c: c[0])


def tabs(h):
    """Gasket tabs: [dict(edge, s, arc, centre)], centre on the outline, TABS_PER_HALF per half."""
    per, total = _perimeter(h)
    if h["side"] == "right":
        out = []
        for t in tabs(halves()["left"]):
            p = _mirror(h, t["centre"])
            a0, e = min(per, key=lambda ae: seg_dist(p, ae[1].a, ae[1].b))
            out.append(dict(edge=e, s=e.s_of(p), arc=a0 + e.s_of(p), centre=p))
        return sorted(out, key=lambda t: t["arc"])
    cands = []
    for a0, e in per:
        margin = TAB_W / 2 + 8.0
        s = margin
        while s <= e.len - margin:
            ok = all(_clear_of_other_edges(h, e, s + ds, TAB_D + POCKET_CLEAR + 2) for ds in (-TAB_W / 2, TAB_W / 2))
            if ok and not _near_port(h, e.at(s)):
                cands.append((a0 + s, e, s))
            s += 1.0
    return [dict(edge=e, s=s, arc=a, centre=e.at(s)) for a, e, s in _spread(cands, total, TABS_PER_HALF)]


def screw_offset():
    return (WALL_IN + WALL_OUT) / 2


def case_screws(h, tab_list):
    """Shell-to-frame screws, one between each pair of neighbouring tabs: [(x, y)]."""
    if h["side"] == "right":
        left = halves()["left"]
        return [_mirror(h, p) for p in case_screws(left, tabs(left))]
    per, total = _perimeter(h)
    off = screw_offset()
    cands = []
    for a0, e in per:
        s = 4.0
        while s <= e.len - 4.0:
            p = e.at(s, off)
            far_from_tabs = all(min(abs(a0 + s - t["arc"]), total - abs(a0 + s - t["arc"])) >= TAB_W / 2 + POCKET_CLEAR + 4.0
                                for t in tab_list)
            if (far_from_tabs and not _near_port(h, e.at(s), PORT_KEEP_SCREW) and _clear_of_other_edges(h, e, s, off)
                    and rect_dist(p, *h["antenna"]) >= ANTENNA_KEEP):
                cands.append((a0 + s, p))
            s += 1.0
    out = []
    arcs = [t["arc"] for t in tab_list]
    for i, a in enumerate(arcs):
        b = arcs[(i + 1) % len(arcs)] + (total if i == len(arcs) - 1 else 0)
        mid = ((a + b) / 2) % total
        span = [c for c in cands if (a < c[0] < b) or (a < c[0] + total < b)]
        if span:
            out.append(min(span, key=lambda c: min(abs(c[0] - mid), total - abs(c[0] - mid)))[1])
    return out


def _rect_in_cavity(h, r):
    """The rectangle lies inside the bottom shell's cavity (the outline grown by WALL_IN)."""
    x0, y0, x1, y1 = r
    pts = [(x, y) for x in _steps(x0, x1) for y in (y0, y1)] + [(x, y) for y in _steps(y0, y1) for x in (x0, x1)]
    if any(not inside(p, h["outline"]) and poly_dist(p, h["outline"]) > WALL_IN for p in pts):
        return False
    return not any(x0 + WALL_IN < x < x1 - WALL_IN and y0 + WALL_IN < y < y1 - WALL_IN for x, y in h["outline"])


def _steps(a, b, step=2.0):
    n = max(1, math.ceil((b - a) / step))
    return [a + (b - a) * i / n for i in range(n + 1)]


def _bay_if_fits(h, cell):
    """The bay round the cell, if the cell keeps clear of the antenna end and the tall parts and the
    bay fits the cavity; else None."""
    if rects_dist(cell, h["antenna"]) < ANTENNA_KEEP or any(rects_dist(cell, t) < TALL_CLEAR for t in h["tall"]):
        return None
    bay = (cell[0] - BATTERY_CLEAR, cell[1] - BATTERY_CLEAR, cell[2] + BATTERY_CLEAR, cell[3] + BATTERY_CLEAR)
    return bay if _rect_in_cavity(h, bay) else None


@functools.lru_cache(maxsize=None)
def _battery(side):
    h = halves()[side]
    if side == "right":
        left = _battery("left")
        x0, y0, x1, y1 = left["cell"]
        cell = (2 * h["mirror_x"] - x1, y0, 2 * h["mirror_x"] - x0, y1)
        bay = _bay_if_fits(h, cell)
        if bay is None: raise SystemExit("right: the left half's battery place, mirrored, does not fit")
        return dict(cell=cell, bay=bay, lead_end=_mirror(h, left["lead_end"]))
    xs = [p[0] for p in h["outline"]]; ys = [p[1] for p in h["outline"]]
    jack = h["battery_jack"]
    cands = []
    for w, l in ((BATTERY_L, BATTERY_W), (BATTERY_W, BATTERY_L)):       # long side along x, then along y
        for x0 in range(int(min(xs)), int(max(xs) - w) + 1):
            for y0 in range(int(min(ys)), int(max(ys) - l) + 1):
                cell = (x0, y0, x0 + w, y0 + l)
                # the protection board and lead are on one short end; put the end nearest the connector there
                ends = ([(x0, y0 + l / 2), (x0 + w, y0 + l / 2)] if w > l else [(x0 + w / 2, y0), (x0 + w / 2, y0 + l)])
                end = min(ends, key=lambda e: math.dist(e, jack))
                cands.append((math.dist(end, jack), cell, end))
    for _, cell, end in sorted(cands, key=lambda c: c[0]):
        bay = _bay_if_fits(h, cell)
        if bay is not None:
            return dict(cell=cell, bay=bay, lead_end=end)
    raise SystemExit(f"{side}: no room for a {BATTERY_W:g} x {BATTERY_L:g} mm battery")


def battery(h):
    """The LiPo's place on the floor: dict(cell, bay, lead_end), rectangles as (x0, y0, x1, y1). It goes
    as near the battery connector as it can while keeping ANTENNA_KEEP from the antenna end and
    TALL_CLEAR from the tall parts under the PCB; the right half's is the left's, mirrored."""
    return _battery(h["side"])


@functools.lru_cache(maxsize=None)
def _steel_disc(side):
    h = halves()[side]
    if side == "right":
        return _mirror(h, _steel_disc("left"))
    from shapely.geometry import Point, Polygon, box
    floor = Polygon(h["outline"]).buffer(WALL_OUT, join_style=2)
    r = STEEL_POCKET_D / 2
    keep = ([box(*battery(h)["bay"])]
            + [Point(p).buffer(CBORE_MOUTH_R) for p in case_screws(h, tabs(h))]
            + [Point(h["reset"]).buffer(RESET_MOUTH_R)])
    antenna = box(*h["antenna"])
    inner_x = (floor.bounds[0] + floor.bounds[2]) / 2
    best = None
    x0, y0, x1, y1 = floor.bounds
    for x in _steps(x0, x1, 0.5):
        if x < inner_x: continue                      # the inner half, where the wedge is thick
        for y in _steps(y0, y1, 0.5):
            c = Point(x, y)
            edge = floor.exterior.distance(c) - r
            if not floor.contains(c) or edge < STEEL_EDGE_KEEP: continue
            if antenna.distance(c) - r < ANTENNA_KEEP: continue
            room = min(k.distance(c) - r for k in keep)
            if room < STEEL_KEEP: continue
            if best is None or min(room, edge - STEEL_EDGE_KEEP + STEEL_KEEP) > best[0]:
                best = (min(room, edge - STEEL_EDGE_KEEP + STEEL_KEEP), (x, y))
    if best is None: raise SystemExit(f"{side}: no room for the {STEEL_D:g} mm steel disc in the floor")
    return best[1]


def steel_disc(h):
    """The centre (x, y) of the steel disc the tenting wedge's magnets hold to, set flush into a pocket in the floor's
    underside: on the inner half, ANTENNA_KEEP from the antenna end, STEEL_EDGE_KEEP in from the
    floor's edge (clear of the feet) and STEEL_KEEP off the battery bay, whose floor is thinner, and
    off the screw counterbores and the reset pinhole, as far from all of them as it can be. The right
    half's is the left's, mirrored."""
    return _steel_disc(h["side"])


def floor_outline(h):
    """The case floor's outline, [(x, y)]: the PCB outline grown by WALL_OUT, with sharp corners."""
    from shapely.geometry import Polygon
    return list(Polygon(h["outline"]).buffer(WALL_OUT, join_style=2).exterior.coords)[:-1]


def outer_x(h):
    """The floor's x at its outer edge, the one that stays on the desk."""
    xs = [p[0] for p in floor_outline(h)]
    return min(xs) if h["side"] == "left" else max(xs)


@functools.lru_cache(maxsize=None)
def _feet(side):
    h = halves()[side]
    if side == "right":
        return [_mirror(h, p) for p in _feet("left")]
    from shapely.geometry import LineString, Polygon
    floor = Polygon(floor_outline(h))
    inset = floor.buffer(-FOOT_IN, join_style=2)
    corners = list(inset.exterior.coords)[:-1]
    mid = (floor.bounds[0] + floor.bounds[2]) / 2
    outer_bottom = max((p for p in corners if p[0] < mid), key=lambda p: p[1])
    thumb_tip = max(corners, key=lambda p: p[1])
    def across_top(pick):
        """The point FOOT_IN in from the side, FOOT_TOP_IN below the top edge."""
        x = pick(p[0] for p in corners)
        top = LineString([(x, floor.bounds[1] - 1), (x, floor.bounds[3] + 1)]).intersection(floor).bounds[1]
        y = top + FOOT_TOP_IN
        return pick(LineString([(floor.bounds[0], y), (floor.bounds[2], y)]).intersection(inset).bounds[i] for i in (0, 2)), y
    return [outer_bottom, thumb_tip, across_top(min), across_top(max)]


def feet(h):
    """The four rubber feet, [(x, y)]: at the outer bottom corner and the tip under the thumbs, FOOT_IN
    in from the edges, and at the outer and inner top, FOOT_IN from the side and FOOT_TOP_IN below the
    top edge. The right half's are the left's, mirrored."""
    return _feet(h["side"])


def magnets(h):
    """The tenting wedge's four magnets, [(x, y)], in a square under the steel disc."""
    cx, cy = steel_disc(h)
    return [(cx + MAGNET_R * dx, cy + MAGNET_R * dy) for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1))]


def wedge_thickness(h, p):
    """The tenting wedge's thickness at p, measured square to its top face."""
    return WEDGE_EDGE + abs(p[0] - outer_x(h)) * math.tan(math.radians(WEDGE_ANGLE))


def usb_port():
    """(width, z0, z1) of the USB-C port through the wall: the largest plug overmould round the
    receptacle, carried by the floating stack (POCKET_CLEAR sideways, FLOAT_GAP down, FLOAT_UP up),
    with PORT_CLEAR all round, so a plugged cable never touches the case."""
    w = PLUG_W + 2 * (POCKET_CLEAR + PORT_CLEAR)
    return w, USB_Z - PLUG_H / 2 - FLOAT_GAP - PORT_CLEAR, USB_Z + PLUG_H / 2 + FLOAT_UP + PORT_CLEAR


def battery_heights():
    """(cell top, gap to underside parts, gap at full travel), including tape, size tolerance and swelling."""
    top = CAVITY_Z - BAY_DEPTH + BATTERY_STACK_T
    gap = -PCB_T - UNDERSIDE_H - top
    return top, gap, gap - FLOAT_GAP


def oled_glass(h):
    """The OLED's glass and its active area, as (x0, y0, x1, y1) in board mm. The module's pin row
    runs along its bottom (larger y) edge."""
    x0, y0, x1, y1 = h["oled"]
    cx, (gw, gh), (aw, ah) = (x0 + x1) / 2, OLED_GLASS[:2], OLED_ACTIVE
    return ((cx - gw / 2, y1 - OLED_GLASS_IN - gh, cx + gw / 2, y1 - OLED_GLASS_IN),
            (cx - aw / 2, y1 - OLED_ACTIVE_IN - ah, cx + aw / 2, y1 - OLED_ACTIVE_IN))


def oled_holes(h):
    """The OLED module's four mounting holes, [(x, y)]."""
    x0, y0, x1, y1 = h["oled"]
    i = OLED_HOLE_IN
    return [(x0 + i, y0 + i), (x1 - i, y0 + i), (x0 + i, y1 - i), (x1 - i, y1 - i)]


def oled_plug(h):
    """The right-angle header in the OLED footprint and the plug on it, (x0, y0, x1, y1) in plan:
    from the footprint's pads toward the module's far edge, under the module."""
    hx0, hy0, hx1, hy1 = h["header"]
    cx, cy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
    length, width, _ = OLED_PLUG
    return (cx - width / 2, cy - length, cx + width / 2, hy1)


def oled_window(h, z):
    """The deck's OLED window at height z, (x0, y0, x1, y1): the active area plus OLED_MARGIN at the
    lip's underside (the glass top), opening at 45 degrees on three sides and on the thumb side far enough that a
    line of sight OLED_VIEW degrees from vertical reaches the whole active area."""
    _, (x0, y0, x1, y1) = oled_glass(h)
    glass_top = OLED_Z[1]
    side = OLED_MARGIN + (z - glass_top)
    south = max(OLED_MARGIN, (z - glass_top) * math.tan(math.radians(OLED_VIEW)) + 0.5)
    return (x0 - side, y0 - side, x1 + side, y1 + south)


def deck_clearances(h):
    """{what: mm} for the deck: glass below its top, the module's room in the floating plate's window,
    and the knob above the deck."""
    return {"OLED glass below the deck top": TOP_Z - OLED_Z[1],
            "OLED module to the plate window, plate floated sideways": OLED_CLEAR - POCKET_CLEAR,
            "knob above the deck top": KNOB_GAP,
            "knob top above the keycap tops": KNOB_Z + KNOB_H - (PLATE_TOP + CAP_SKIRT + CAP_H),
            "shaft to cut off": ENC_SHAFT_CUT,
            "D flat left inside the knob": ENC_SHAFT_TOP - ENC_SHAFT_CUT - max(ENC_FLAT_FROM, KNOB_Z + KNOB_HUB_UP)}


def standoff_threads():
    """{what: mm} for the standoffs: the gap the standoff and shim leave under the plate, how far the
    screw from below reaches into its standoff, and where its tip ends against the standoff's top
    (negative: below it) at its shortest and longest."""
    into = SCREW_L - PCB_T - SHIM_T
    return {"standoff and shim short of the plate": PLATE_BOT - STANDOFF_L - SHIM_T,
            f"M2 x {SCREW_L:g} from below, into the standoff": min(into, STANDOFF_L),
            "screw tip past the standoff top, shortest": into - SCREW_L_TOL - STANDOFF_L,
            "screw tip past the standoff top, longest": into + SCREW_L_TOL - STANDOFF_L}


if __name__ == "__main__":
    for side, h in halves().items():
        t = tabs(h)
        print(f"{side}: usb {h['usb']}, lever {h['lever']}, reset {h['reset']}, antenna {h['antenna']}")
        print(f"  tabs: " + ", ".join(f"({c['centre'][0]:.1f},{c['centre'][1]:.1f})" for c in t))
        print(f"  case screws: " + ", ".join(f"({x:.1f},{y:.1f})" for x, y in case_screws(h, t)))
        print(f"  standoffs: " + ", ".join(f"{r} ({x:.1f},{y:.1f})" for r, (x, y) in sorted(h["holes"].items())))
        bt = battery(h); x0, y0, x1, y1 = bt["cell"]
        print(f"  battery: {x1 - x0:g} x {y1 - y0:g} mm cell at ({x0:.1f},{y0:.1f})..({x1:.1f},{y1:.1f}), "
              f"lead end {math.dist(bt['lead_end'], h['battery_jack']):.1f} mm from the connector, "
              f"{rects_dist(bt['cell'], h['antenna']):.1f} mm from the antenna end, "
              f"{min(rects_dist(bt['cell'], t) for t in h['tall']):.1f} mm from the nearest tall part")
    print(f"stack: floor {BOTTOM_Z:.1f}, cavity {CAVITY_Z:.1f}, ledge {LEDGE_Z:.1f}, split {SPLIT_Z:.1f}, "
          f"plate {PLATE_BOT:.1f}..{PLATE_TOP:.1f}, ceiling {CEIL_Z:.1f}, top {TOP_Z:.1f}")
    for k, v in deck_clearances(halves()["left"]).items(): print(f"deck: {k} {v:.1f} mm")
    for k, v in standoff_threads().items(): print(f"standoffs: {k} {v:.1f} mm")
    top, gap, pressed = battery_heights()
    print(f"battery: bay floor {CAVITY_Z - BAY_DEPTH:.1f}, cell top {top:.1f} ({BATTERY_STACK_T:g} mm installed), "
          f"{gap:.1f} mm under the solder joints, {pressed:.1f} mm with the stack pressed down {FLOAT_GAP:g} mm")
