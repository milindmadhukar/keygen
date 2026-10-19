#!/usr/bin/env python3
"""Build pcb/keygen.kicad_pcb: place every footprint from the schematic's netlist, assign nets,
and draw each half's outline. Routing is not done here.

Key positions come from Redox's KLE layout (19.05 mm per unit). Per-key parts are placed
relative to each switch:  switch + socket (back), SK6812MINI-E under the switch's LED window
(back, south), 1N4148 standing east of the switch (back). Everything else is placed by hand
below. Footprints keep their schematic link (path) so KiCad's "Update PCB from schematic"
still works after this script.
"""
import math, re, subprocess, sys, tempfile
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
from sexp import find, first, parse
import gen_schematic as g

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb"
U = 19.05
OFF = (15.0, 15.0)            # shift the whole design into positive coordinates (mm)
MIRROR_X = 19.5 * U           # left x  <->  right x  (Redox is mirror-symmetric about 9.75u)

FP_DIRS = {
    "keygen": ROOT / "pcb/lib/keygen.pretty",
    "marbastlib-mx": ROOT / "lib/marbastlib/footprints/marbastlib-mx.pretty",
    "marbastlib-various": ROOT / "lib/marbastlib/footprints/marbastlib-various.pretty",
    "marbastlib-xp-promicroish": ROOT / "lib/marbastlib/footprints/marbastlib-xp-promicroish.pretty",
    "Keebio-Parts": ROOT / "lib/Keebio-Parts.pretty",
}

# --------------------------------------------------------------------------------------
# Redox KLE (img/redox-layout.json from mattdibi/redox-keyboard, MIT), legends stripped
# --------------------------------------------------------------------------------------
KLE = [[{"x":3.5},"",{"x":10.5},""],[{"y":-0.875,"x":2.5},"",{"x":1},"",{"x":8.5},"",{"x":1},""],[{"y":-0.875,"x":5.5},"",{"x":6.5},""],[{"y":-0.875,"x":0.25,"w":1.25},"","",{"x":14.5},"",{"w":1.25},""],[{"y":-0.625,"x":6.5},"",{"x":4.5},""],[{"y":-0.75,"x":3.5},"",{"x":10.5},""],[{"y":-0.875,"x":2.5},"",{"x":1},"",{"x":8.5},"",{"x":1},""],[{"y":-0.875,"x":5.5},"",{"x":6.5},""],[{"y":-0.875,"x":0.25,"w":1.25},"","",{"x":14.5},"",{"w":1.25},""],[{"y":-0.625,"x":6.5,"h":1.5},"",{"x":4.5,"h":1.5},""],[{"y":-0.75,"x":3.5},"",{"x":10.5},""],[{"y":-0.875,"x":2.5},"",{"x":1},"",{"x":8.5},"",{"x":1},""],[{"y":-0.875,"x":5.5},"",{"x":6.5},""],[{"y":-0.875,"x":0.25,"w":1.25},"","",{"x":14.5},"",{"w":1.25},""],[{"y":-0.375,"x":3.5},"",{"x":10.5},""],[{"y":-0.875,"x":2.5},"",{"x":1},"",{"x":8.5},"",{"x":1},""],[{"y":-0.875,"x":5.5},"",{"x":6.5},""],[{"y":-0.875,"x":0.25,"w":1.25},"","",{"x":14.5},"",{"w":1.25},""],[{"y":-0.375,"x":3.5},"",{"x":10.5},""],[{"y":-0.875,"x":2.5},"",{"x":12.5},""],[{"y":-0.75,"x":0.5},"","",{"x":14.5},"",""],[{"r":15,"y":-2.625,"x":5.75,"w":1.25},""],[{"r":30,"rx":6.5,"ry":4.25,"y":-1},"",""],[{"h":1.5},"",{"h":1.5},""],[{"r":-30,"rx":13,"y":-1,"x":-2},"",""],[{"x":-2,"h":1.5},"",{"h":1.5},""],[{"r":-15,"rx":0,"ry":0,"y":7.75,"x":11.75,"w":1.25},""]]

def parse_kle(rows):
    keys, c, cl = [], dict(x=0, y=0, w=1, h=1, r=0, rx=0, ry=0), dict(x=0, y=0)
    for row in rows:
        for it in row:
            if isinstance(it, dict):
                if "r" in it: c["r"] = it["r"]
                if "rx" in it: c["rx"] = cl["x"] = it["rx"]; c["x"], c["y"] = cl["x"], cl["y"]
                if "ry" in it: c["ry"] = cl["y"] = it["ry"]; c["x"], c["y"] = cl["x"], cl["y"]
                c["x"] += it.get("x", 0); c["y"] += it.get("y", 0)
                if "w" in it: c["w"] = it["w"]
                if "h" in it: c["h"] = it["h"]
            else:
                keys.append(dict(c)); c["x"] += c["w"]; c["w"] = c["h"] = 1
        c["y"] += 1; c["x"] = c["rx"]
    return keys

# KLE index -> (side, row, col) of the matrix in gen_schematic.KEYS. Indices 12, 13, 26, 27 are
# Redox's inner column, removed in Keygen.
KLE_MAP = {
    8: ("left", 0, 0), 9: ("left", 0, 1), 2: ("left", 0, 2), 0: ("left", 0, 3), 3: ("left", 0, 4), 6: ("left", 0, 5),
    22: ("left", 1, 0), 23: ("left", 1, 1), 16: ("left", 1, 2), 14: ("left", 1, 3), 17: ("left", 1, 4), 20: ("left", 1, 5),
    36: ("left", 2, 0), 37: ("left", 2, 1), 30: ("left", 2, 2), 28: ("left", 2, 3), 31: ("left", 2, 4), 34: ("left", 2, 5),
    48: ("left", 3, 0), 49: ("left", 3, 1), 42: ("left", 3, 2), 40: ("left", 3, 3), 43: ("left", 3, 4), 46: ("left", 3, 5),
    56: ("left", 4, 0), 57: ("left", 4, 1), 54: ("left", 4, 2), 52: ("left", 4, 3), 60: ("left", 4, 4),
    63: ("left", 4, 5), 64: ("left", 4, 6), 61: ("left", 3, 6), 62: ("left", 2, 6),
    11: ("right", 0, 0), 10: ("right", 0, 1), 5: ("right", 0, 2), 1: ("right", 0, 3), 4: ("right", 0, 4), 7: ("right", 0, 5),
    25: ("right", 1, 0), 24: ("right", 1, 1), 19: ("right", 1, 2), 15: ("right", 1, 3), 18: ("right", 1, 4), 21: ("right", 1, 5),
    39: ("right", 2, 0), 38: ("right", 2, 1), 33: ("right", 2, 2), 29: ("right", 2, 3), 32: ("right", 2, 4), 35: ("right", 2, 5),
    51: ("right", 3, 0), 50: ("right", 3, 1), 45: ("right", 3, 2), 41: ("right", 3, 3), 44: ("right", 3, 4), 47: ("right", 3, 5),
    59: ("right", 4, 0), 58: ("right", 4, 1), 55: ("right", 4, 2), 53: ("right", 4, 3), 69: ("right", 4, 4),
    68: ("right", 4, 5), 67: ("right", 4, 6), 66: ("right", 3, 6), 65: ("right", 2, 6),
}

def key_geometry():
    """(side, row, col) -> (cx_mm, cy_mm, rot_cw_deg, w_u, h_u, corners_mm)"""
    out = {}
    for i, k in enumerate(parse_kle(KLE)):
        if i not in KLE_MAP: continue
        a = math.radians(k["r"])
        def tf(x, y):
            dx, dy = x - k["rx"], y - k["ry"]
            return ((k["rx"] + dx * math.cos(a) - dy * math.sin(a)) * U, (k["ry"] + dx * math.sin(a) + dy * math.cos(a)) * U)
        cx, cy = tf(k["x"] + k["w"] / 2, k["y"] + k["h"] / 2)
        corners = [tf(k["x"], k["y"]), tf(k["x"] + k["w"], k["y"]), tf(k["x"] + k["w"], k["y"] + k["h"]), tf(k["x"], k["y"] + k["h"])]
        out[KLE_MAP[i]] = (cx, cy, k["r"], k["w"], k["h"], corners)
    return out

def rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))

# --------------------------------------------------------------------------------------
# Netlist from the schematic
# --------------------------------------------------------------------------------------
def read_netlist():
    sch = PCB / "keygen.kicad_sch"
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "n.net"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(out), str(sch)],
                       check=True, capture_output=True)
        tree = parse(out.read_text())
    comps = {}
    for c in find(first(tree, "components"), "comp"):
        ref = first(c, "ref")[1]
        sp = first(c, "sheetpath")
        comps[ref] = dict(value=first(c, "value")[1], footprint=first(c, "footprint")[1],
                          path=first(sp, "tstamps")[1] + first(c, "tstamps")[1], pins={})
    for n in find(first(tree, "nets"), "net"):
        name = first(n, "name")[1]
        for node in find(n, "node"):
            ref, pin = first(node, "ref")[1], first(node, "pin")[1]
            if ref in comps: comps[ref]["pins"][pin] = name
    return comps

# --------------------------------------------------------------------------------------
# Board building
# --------------------------------------------------------------------------------------
def mm(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(x + OFF[0]), pcbnew.FromMM(y + OFF[1]))

class Board:
    def __init__(self, comps):
        self.b = pcbnew.CreateEmptyBoard()
        self.comps, self.nets, self.placed = comps, {}, set()
        ds = self.b.GetDesignSettings()
        ds.m_TrackMinWidth = pcbnew.FromMM(0.2)
        ds.m_MinClearance = pcbnew.FromMM(0.2)
        ds.m_ViasMinSize = pcbnew.FromMM(0.6)
        ds.m_MinThroughDrill = pcbnew.FromMM(0.3)
        # Reverse-mount SK6812MINI-E pads sit ~0.29 mm from their own light cut-out.
        ds.m_CopperEdgeClearance = pcbnew.FromMM(0.25)

    def net(self, name):
        if name not in self.nets:
            ni = pcbnew.NETINFO_ITEM(self.b, name); self.b.Add(ni); self.nets[name] = ni
        return self.nets[name]

    def place(self, ref, x, y, rot_cw=0.0, back=False, extra=0.0):
        """Put ref's footprint with its origin at (x, y) mm. rot_cw: clockwise degrees (KLE sense).
        extra: additional rotation for parts whose own drawing needs turning."""
        c = self.comps[ref]
        lib, name = c["footprint"].split(":", 1)
        d = FP_DIRS.get(lib, Path(f"/usr/share/kicad/footprints/{lib}.pretty"))
        fp = pcbnew.FootprintLoad(str(d), name)
        if fp is None: raise RuntimeError(f"{ref}: footprint {c['footprint']} not found")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref); fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        self.b.Add(fp)
        pos = mm(x, y)
        fp.SetPosition(pos)
        if back:
            fp.SetOrientationDegrees(rot_cw + extra)
            fp.Flip(pos, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        else:
            fp.SetOrientationDegrees(-(rot_cw + extra))
        for p in fp.Pads():
            n = c["pins"].get(p.GetNumber())
            if n: p.SetNet(self.net(n))
        if re.match(r"(SW|D|LED)\d+$", ref) and not ref.startswith(("SW19", "SW29")):
            fp.Reference().SetVisible(False)      # 200+ labels would only clutter the silkscreen
        self.placed.add(ref)
        return fp

    def outline(self, pts):
        hull = convex_hull(pts)
        for a, b in zip(hull, hull[1:] + hull[:1]):
            s = pcbnew.PCB_SHAPE(self.b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(mm(*a)); s.SetEnd(mm(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1))
            self.b.Add(s)

HOLES_PER_HALF = 5
HOLE_KEEPOUT = 3.5      # mm from hole centre to any pad, hole or LED cut-out
EDGE_KEEPOUT = 4.0      # mm from hole centre to the board edge

def _mounting_holes(self, hull, side):
    """Pick M2 hole spots where nothing else is, spread across the half (farthest-point)."""
    obst, switches, boxes = [], [], []
    for fp in self.b.GetFootprints():
        ref = fp.GetReference()
        for p in fp.Pads():
            q = p.GetPosition(); s = p.GetSize()
            obst.append((pcbnew.ToMM(q.x) - OFF[0], pcbnew.ToMM(q.y) - OFF[1], max(pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)) / 2))
        if ref.startswith("LED"):          # light cut-out
            q = fp.GetPosition(); obst.append((pcbnew.ToMM(q.x) - OFF[0], pcbnew.ToMM(q.y) - OFF[1], 2.0))
        if re.match(r"SW\d+$", ref) and int(ref[2:]) % 100 < 90:   # key switches: 14 mm body + screw head
            q = fp.GetPosition()
            switches.append((pcbnew.ToMM(q.x) - OFF[0], pcbnew.ToMM(q.y) - OFF[1], fp.GetOrientationDegrees()))
        elif not re.match(r"(D|LED|H)\d+$", ref):                    # controller, jack, encoder, ...
            bb = fp.GetBoundingBox(False)
            boxes.append((pcbnew.ToMM(bb.GetLeft()) - OFF[0], pcbnew.ToMM(bb.GetTop()) - OFF[1],
                          pcbnew.ToMM(bb.GetRight()) - OFF[0], pcbnew.ToMM(bb.GetBottom()) - OFF[1]))
    def clear_of_switches(x, y):
        for sx, sy, o in switches:
            dx, dy = rot((x - sx, y - sy), o)      # into the switch's own frame (either sign works: square)
            if max(abs(dx), abs(dy)) < 9.4: return False
        return True
    def clear_of_boxes(x, y):
        return all(not (l - 2.5 < x < r + 2.5 and t - 2.5 < y < b + 2.5) for l, t, r, b in boxes)
    def edge_dist(x, y):
        best = 1e9
        for (ax, ay), (bx, by) in zip(hull, hull[1:] + hull[:1]):
            vx, vy = bx - ax, by - ay; t = max(0, min(1, ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy)))
            best = min(best, math.hypot(x - ax - t * vx, y - ay - t * vy))
        return best
    def inside(x, y):
        return all((bx - ax) * (y - ay) - (by - ay) * (x - ax) >= 0 for (ax, ay), (bx, by) in zip(hull, hull[1:] + hull[:1]))
    xs = [p[0] for p in hull]; ys = [p[1] for p in hull]
    cands = []
    y = min(ys)
    while y < max(ys):
        x = min(xs)
        while x < max(xs):
            if inside(x, y) and edge_dist(x, y) >= EDGE_KEEPOUT and \
               all(math.hypot(x - ox, y - oy) >= HOLE_KEEPOUT + r for ox, oy, r in obst) and \
               clear_of_switches(x, y) and clear_of_boxes(x, y):
                cands.append((x, y))
            x += 0.5
        y += 0.5
    if not cands: raise RuntimeError(f"{side}: no room for mounting holes")
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    chosen = [min(cands, key=lambda p: math.hypot(p[0] - cx, p[1] - cy))]
    while len(chosen) < HOLES_PER_HALF:
        chosen.append(max(cands, key=lambda p: min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in chosen)))
    for i, (x, y) in enumerate(chosen, 1):
        fp = pcbnew.FootprintLoad("/usr/share/kicad/footprints/MountingHole.pretty", "MountingHole_2.2mm_M2")
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_2.2mm_M2"))
        fp.SetReference(f"H{(100 if side == 'left' else 200) + i}"); fp.SetValue("M2")
        fp.SetPosition(mm(x, y)); self.b.Add(fp)
    print(f"{side}: mounting holes at " + ", ".join(f"({x:.1f},{y:.1f})" for x, y in chosen))

Board.mounting_holes = _mounting_holes

def convex_hull(pts):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def grow(corners, cx, cy, d):
    """Push polygon corners outward from (cx, cy) by d mm."""
    out = []
    for x, y in corners:
        vx, vy = x - cx, y - cy; L = math.hypot(vx, vy)
        out.append((x + vx / L * d, y + vy / L * d))
    return out

# --------------------------------------------------------------------------------------
# Placement
# --------------------------------------------------------------------------------------
LED_OFFSET = (0.0, 5.08)          # SK6812MINI-E under the MX LED window (south of centre)
DIODE_PAD1 = (8.3, 6.6)           # 1N4148 cathode; anode 7.62 mm north of it
UNDERGLOW_GAPS = [((0, 1), 1), ((0, 1), 4), ((1, 2), 3), ((2, 3), 1), ((2, 3), 4), ((3, 4), 2)]

# Non-key parts on the LEFT half (mm, KLE frame). The right half mirrors these about MIRROR_X.
TOP_EDGE = 0.25 * U               # top of the number-row key next to the controller ("5")
MCU_X = 7.0 * U                   # centre of Redox's removed inner column
LEFT_PARTS = {
    "U":  dict(x=MCU_X, y=TOP_EDGE + 16.65 - 1.0, back=True),     # USB-C overhangs the edge by 1 mm
    "J":  dict(x=MCU_X + 9.0 + 1.2 + 3.05, y=TOP_EDGE + 2.0, back=True),   # TRRS, opening up
    "SW90": dict(x=MCU_X + 9.0 + 1.2 + 6.1 + 1.5 + 3.7, y=TOP_EDGE + 1.8, back=True),  # power slide, lever up
    "BT": dict(x=MCU_X + 9.0 + 5.5, y=TOP_EDGE + 23.0, back=True),          # JST-PH battery
    # reset: origin is pad 1; on the back the 6.5 mm body mirrors toward -x, so offset by its width
    "SW91": dict(x=MCU_X + 9.0 + 1.5 + 6.5, y=TOP_EDGE + 36.0, back=True),
}
CAP_NEAR_LED1 = [(-6.5, 4.6), (-3.0, 4.6)]   # C1/C2 relative to the first LED, back side
ENCODER_SHAFT = (12.5 * U, TOP_EDGE + 16.65 * 2 + 15.0)   # right half, front, below the controller
ENC_ORIGIN_TO_SHAFT = (7.5, 2.5)                          # EC11 footprint origin is pin A


def build():
    comps = read_netlist()
    B = Board(comps)
    geo = key_geometry()
    for side in ("left", "right"):
        base = g.BASE[side]
        keys = g.KEYS[side]
        enc = g.ENCODER_POS.get(side)
        cells = sorted([(r, c, lab, w) for r, c, lab, w in keys] + ([(enc[0], enc[1], "enc", None)] if enc else []))
        num = {(r, c): n for n, (r, c, lab, w) in enumerate(cells, 1)}
        outline_pts = []
        for (r, c) in [(r, c) for r, c, *_ in keys]:
            cx, cy, rr, w, h, corners = geo[(side, r, c)]
            n = num[(r, c)]
            B.place(f"SW{base+n}", cx, cy, rr, back=True)
            lx, ly = rot(LED_OFFSET, rr)
            li = [i for i, k in enumerate(keys) if (k[0], k[1]) == (r, c)][0]
            B.place(f"LED{base+li+1}", cx + lx, cy + ly, rr, back=True)
            east = (w * U / 2 - 1.225, DIODE_PAD1[1]) if w > 1 else DIODE_PAD1
            dx, dy = rot(east, rr)
            B.place(f"D{base+n}", cx + dx, cy + dy, rr, back=True, extra=90)
            outline_pts += grow(corners, cx, cy, 0.6)
        if enc:
            # encoder diode: next to the encoder's switch pins
            n = num[enc]
            sx, sy = ENCODER_SHAFT
            B.place(f"D{base+n}", sx + 4.0, sy + 10.5, 0, back=True, extra=0)
        # underglow LEDs: front side, in the gap between two keys of one column
        for j, ((r1, r2), c) in enumerate(UNDERGLOW_GAPS):
            a, b2 = geo[(side, r1, c)], geo[(side, r2, c)]
            x, y = (a[0] + b2[0]) / 2, (a[1] + b2[1]) / 2
            B.place(f"LED{base+len(keys)+j+1}", x, y, 0, back=False)
        # controller and friends
        mir = (lambda x: MIRROR_X - x) if side == "right" else (lambda x: x)
        for key, p in LEFT_PARTS.items():
            ref = f"{key}{base+1}" if key in ("U", "J", "BT") else f"SW{base+int(key[2:])}"
            x = mir(p["x"])
            B.place(ref, x, p["y"], 0, back=p["back"])
        # decoupling caps next to the first LED of the chain
        k0 = keys[0]
        cx, cy, rr, *_ = geo[(side, k0[0], k0[1])]
        for i, (dx, dy) in enumerate(CAP_NEAR_LED1):
            ox, oy = rot((LED_OFFSET[0] + dx, LED_OFFSET[1] + dy), rr)
            B.place(f"C{base+i+1}", cx + ox, cy + oy, rr, back=True)
        if enc:
            sx, sy = ENCODER_SHAFT
            B.place(f"ENC{base+1}", sx - ENC_ORIGIN_TO_SHAFT[0], sy - ENC_ORIGIN_TO_SHAFT[1], 0, back=False)
        # outline: keys + controller ear
        ear_x0, ear_x1 = mir(MCU_X - 9.5), mir(MCU_X + 9.0 + 1.2 + 6.1 + 1.5 + 7.4 + 1.0)
        ear_y1 = TOP_EDGE + 16.65 * 2 + 15.0
        outline_pts += [(ear_x0, TOP_EDGE), (ear_x1, TOP_EDGE), (ear_x1, ear_y1), (ear_x0, ear_y1)]
        if enc:
            sx, sy = ENCODER_SHAFT
            outline_pts += [(sx - 10, sy + 9), (sx + 10, sy + 9)]
        B.outline(outline_pts)
        B.mounting_holes(convex_hull(outline_pts), side)

    missing = set(comps) - B.placed - {r for r in comps if r.startswith("#")}
    if missing: raise RuntimeError(f"not placed: {sorted(missing)}")
    path = PCB / "keygen.kicad_pcb"
    B.b.SetFileName(str(path))
    pcbnew.SaveBoard(str(path), B.b)
    set_project_rules()
    print(f"placed {len(B.placed)} footprints, {len(B.nets)} nets -> {path.relative_to(ROOT)}")


RULES = {                       # Lion Circuits: 6/6 mil on 1 oz copper; we keep some margin
    "min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.6, "min_via_annular_width": 0.13,
    "min_through_hole_diameter": 0.3, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
    "min_copper_edge_clearance": 0.2,    # reverse-mount LED pads sit 0.247 mm from their own cut-out corners
    "min_silk_clearance": 0.0,
}

def set_project_rules():
    import json
    pro = PCB / "keygen.kicad_pro"
    d = json.loads(pro.read_text())
    d.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {}).update(RULES)
    pro.write_text(json.dumps(d, indent=2) + "\n")


if __name__ == "__main__":
    build()
