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
  top frame         SPLIT_Z .. TOP_Z

The plate and PCB are tied together by M2 standoffs and float on the tabs; nothing screws the
PCB to the case. The bottom shell and the top frame are screwed together through the walls,
into heat-set inserts.

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
PLATE_T = 1.6                  # FR-4 plate; MX clips are made for 1.5 mm and take 1.6
PLATE_TOP = 5.0
PLATE_BOT = PLATE_TOP - PLATE_T
GASKET_T = 2.0                 # Poron strip, uncompressed
GASKET_SQUEEZE = 0.4           # how much each strip is compressed when the case is closed
LEDGE_Z = PLATE_BOT - (GASKET_T - GASKET_SQUEEZE)
CEIL_Z = PLATE_TOP + (GASKET_T - GASKET_SQUEEZE)
SPLIT_Z = PLATE_BOT            # bottom shell / top frame joint
TOP_Z = CEIL_Z + 2.0
CONTROLLER_DEPTH = 7.5         # socketed nice!nano below the PCB's underside
FLOAT_GAP = 1.5                # under the controller, so the floating stack can travel
CAVITY_Z = -PCB_T - CONTROLLER_DEPTH - FLOAT_GAP
FLOOR_T = 3.0
BOTTOM_Z = CAVITY_Z - FLOOR_T

# ---------------------------------------------------------------- plan view (mm)
CUTOUT = 14.0                  # MX switch cut-out
CUTOUT_R = 0.5                 # its corner radius (the fab's router bit)
SWITCH_FLANGE = 15.6           # MX top housing, resting on the plate
CAP_GAP = 0.95                 # keycap = n * 19.05 - this
ENC_CUTOUT = 13.0              # square plate cut-out around the EC11 body
OLED_W, OLED_H = 27.5, 28.0    # 0.96 in. OLED module, standing in a plate window
OLED_HDR_IN = 1.3              # its header row from its bottom edge (the module sits above the pins)
OLED_Z = (2.5, 5.1)            # module bottom and glass top above the PCB (on the header's spacer)
OLED_CLEAR = 0.5               # module to plate window, each side
HOLE_D = 2.2
TAB_W, TAB_D = 12.0, 5.0       # gasket tab: width along the edge, depth beyond the outline
TABS_PER_HALF = 8
POCKET_CLEAR = 0.5             # tab to pocket, each side, so the tab floats
WALL_IN = 1.0                  # PCB/plate edge to the case's inner wall
WALL_OUT = 7.5                 # PCB/plate edge to the case's outer wall
PORT_WALL = 1.5                # wall thickness in front of the USB-C and power switch
PORT_KEEP = 22.0               # no tab this close to the USB-C or switch lever
PORT_KEEP_SCREW = 16.0         # no case screw this close to them
NANO_W, NANO_L = 18.0, 33.5    # nice!nano v2 board
USB_OVERHANG = 1.0             # its USB-C end reaches this far past the PCB edge
ANTENNA_LEN = 12.0             # chip antenna end of the nice!nano
ANTENNA_KEEP = 15.0            # no metal (inserts, screws) this close to it
SCREW_HEAD_D = 3.5             # M2 button head (ISO 7380) on top of the plate
HEAD_CLEAR = 0.3               # head to switch top housing
BATTERY_W, BATTERY_L, BATTERY_T = 60.0, 88.0, 5.0   # the largest cell bom.csv allows, protection board included
BATTERY_GROWTH = 0.5           # pouch thickness tolerance and swelling with age
BATTERY_CLEAR = 1.5            # cell to the bay wall, each side
BAY_DEPTH = 1.0                # the bay is sunk this far into the floor
UNDERSIDE_H = 2.0              # hotswap sockets (1.85 mm) and DO-35 diodes (1.75 mm body) under the PCB
TALL_CLEAR = 3.0               # cell to the controller, battery connector, buttons, encoder and OLED pins
TALL_REFS = ("U", "BT", "ENC", "J")   # and the slide switch and reset button (SWx90, SWx91)


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
    """{'left'|'right': dict(side, outline, edges, keys, holes, enc, oled, usb, lever, reset, antenna,
    battery_jack, tall)}"""
    b = pcbnew.LoadBoard(str(PCB))
    polys = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(polys, False)
    out = {}
    for i in range(polys.OutlineCount()):
        o = polys.Outline(i)
        poly = [(MM(o.CPoint(j).x), MM(o.CPoint(j).y)) for j in range(o.PointCount())]
        side = "left" if sum(p[0] for p in poly) / len(poly) < 211 else "right"
        out[side] = dict(side=side, outline=poly, edges=[Edge(poly[k], poly[(k + 1) % len(poly)], poly) for k in range(len(poly))],
                         holes={}, enc=[], tall=[])
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
        if ref.startswith("H"): h["holes"][ref] = (x, y)
        elif ref.startswith("ENC"): h["enc"].append((x, y))
        elif ref[0] == "J":                     # OLED header: the module stands above its pins
            pins = [(MM(p.GetPosition().x), MM(p.GetPosition().y)) for p in fp.Pads()]
            cx = sum(q[0] for q in pins) / len(pins); py = pins[0][1]
            h["oled"] = (cx - OLED_W / 2, py + OLED_HDR_IN - OLED_H, cx + OLED_W / 2, py + OLED_HDR_IN)
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


def battery_heights():
    """(cell top above the bay floor's z, gap to the parts under the PCB, gap with the stack pressed
    down by FLOAT_GAP), all for a cell grown by BATTERY_GROWTH."""
    top = CAVITY_Z - BAY_DEPTH + BATTERY_T + BATTERY_GROWTH
    gap = -PCB_T - UNDERSIDE_H - top
    return top, gap, gap - FLOAT_GAP


def standoffs(h):
    """{hole ref: 'screwed' | 'post'}. A plate screw goes in only where its head clears the switch
    top housings and the encoder; elsewhere the standoff is screwed from below and its top bears on
    the plate."""
    out = {}
    for ref, p in h["holes"].items():
        room = min(square_dist(p, k, SWITCH_FLANGE) for k in h["keys"])
        for ex, ey in h["enc"]:
            room = min(room, math.hypot(max(abs(p[0] - ex) - ENC_CUTOUT / 2, 0), max(abs(p[1] - ey) - ENC_CUTOUT / 2, 0)))
        out[ref] = ("screwed" if room >= SCREW_HEAD_D / 2 + HEAD_CLEAR else "post", room)
    return out


if __name__ == "__main__":
    for side, h in halves().items():
        t = tabs(h)
        print(f"{side}: usb {h['usb']}, lever {h['lever']}, reset {h['reset']}, antenna {h['antenna']}")
        print(f"  tabs: " + ", ".join(f"({c['centre'][0]:.1f},{c['centre'][1]:.1f})" for c in t))
        print(f"  case screws: " + ", ".join(f"({x:.1f},{y:.1f})" for x, y in case_screws(h, t)))
        print(f"  standoffs: " + ", ".join(f"{r} {k} ({room:.2f} mm)" for r, (k, room) in sorted(standoffs(h).items())))
        bt = battery(h); x0, y0, x1, y1 = bt["cell"]
        print(f"  battery: {x1 - x0:g} x {y1 - y0:g} mm cell at ({x0:.1f},{y0:.1f})..({x1:.1f},{y1:.1f}), "
              f"lead end {math.dist(bt['lead_end'], h['battery_jack']):.1f} mm from the connector, "
              f"{rects_dist(bt['cell'], h['antenna']):.1f} mm from the antenna end, "
              f"{min(rects_dist(bt['cell'], t) for t in h['tall']):.1f} mm from the nearest tall part")
    print(f"stack: floor {BOTTOM_Z:.1f}, cavity {CAVITY_Z:.1f}, ledge {LEDGE_Z:.1f}, split {SPLIT_Z:.1f}, "
          f"plate {PLATE_BOT:.1f}..{PLATE_TOP:.1f}, ceiling {CEIL_Z:.1f}, top {TOP_Z:.1f}")
    top, gap, pressed = battery_heights()
    print(f"battery: bay floor {CAVITY_Z - BAY_DEPTH:.1f}, cell top {top:.1f} ({BATTERY_T:g} + {BATTERY_GROWTH:g} mm), "
          f"{gap:.1f} mm under the solder joints, {pressed:.1f} mm with the stack pressed down {FLOAT_GAP:g} mm")
