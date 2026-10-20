#!/usr/bin/env python3
"""Route the connections Freerouting left open (grid A* maze router, two layers + vias).

Reads the board, asks KiCad's DRC which connections are still open (ground excluded: the pour
handles it), builds a 0.2 mm occupancy grid of existing copper per layer, and routes each open
connection on that grid. Then pours ground, stitches isolated ground pads and saves.
KiCad's DRC is the judge of the result; this script only proposes copper.
"""
import heapq, json, math, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import route_pcb

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
G = 0.2                      # grid pitch, mm
W = 0.25                     # new track width, mm
CLR = 0.2                    # copper clearance, mm
SNAP = 0.12                  # slack for grid snapping, mm
EDGE = 0.3                   # copper to board edge / cut-outs, mm
HOLE = 0.3                   # copper to holes, mm
VIA_D, VIA_DRILL = 0.6, 0.3
VIA_COST, STEP, DIAG = 25.0, 1.0, 1.414
FREE, BLOCK = -1, -2
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
toMM = pcbnew.ToMM


class Grid:
    def __init__(self, b):
        bb = b.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = toMM(bb.GetLeft()) - 1, toMM(bb.GetTop()) - 1
        self.nx = int((toMM(bb.GetRight()) + 1 - self.x0) / G) + 1
        self.ny = int((toMM(bb.GetBottom()) + 1 - self.y0) / G) + 1
        self.own = np.full((2, self.ny, self.nx), FREE, dtype=np.int32)
        xs = self.x0 + np.arange(self.nx) * G
        ys = self.y0 + np.arange(self.ny) * G
        self.X, self.Y = np.meshgrid(xs, ys)

    def cell(self, x, y):
        return int(round((y - self.y0) / G)), int(round((x - self.x0) / G))

    def xy(self, iy, ix):
        return self.x0 + ix * G, self.y0 + iy * G

    def window(self, x0, y0, x1, y1):
        i0, j0 = max(0, int((y0 - self.y0) / G) - 1), max(0, int((x0 - self.x0) / G) - 1)
        i1, j1 = min(self.ny, int((y1 - self.y0) / G) + 2), min(self.nx, int((x1 - self.x0) / G) + 2)
        return slice(i0, i1), slice(j0, j1)

    def mark(self, layers, mask_fn, bbox, net):
        sy, sx = self.window(*bbox)
        X, Y = self.X[sy, sx], self.Y[sy, sx]
        m = mask_fn(X, Y)
        for li in layers:
            sub = self.own[li][sy, sx]
            if net == BLOCK:
                sub[m] = BLOCK
            else:
                free = m & (sub == FREE)
                clash = m & (sub != FREE) & (sub != net)
                sub[free] = net
                sub[clash] = BLOCK


def seg_dist(X, Y, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1) if L2 > 0 else 0
    return np.hypot(X - ax - t * vx, Y - ay - t * vy)


def rasterize(b, g):
    infl = CLR + W / 2 + SNAP
    li_of = lambda layer: 0 if layer == pcbnew.F_Cu else 1
    # board outline: outside blocked, near edges blocked (includes LED cut-outs as holes)
    polys = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(polys, False)
    inside = np.zeros((g.ny, g.nx), bool)
    def poly_pts(chain): return [(toMM(chain.CPoint(k).x), toMM(chain.CPoint(k).y)) for k in range(chain.PointCount())]
    def pip(pts):
        res = np.zeros_like(inside); n = len(pts)
        for k in range(n):
            (ax, ay), (bx, by) = pts[k], pts[(k + 1) % n]
            cond = ((ay > g.Y) != (by > g.Y))
            xint = ax + (g.Y - ay) * (bx - ax) / ((by - ay) if by != ay else 1e-12)
            res ^= cond & (g.X < xint)
        return res
    edges = []
    for i in range(polys.OutlineCount()):
        pts = poly_pts(polys.Outline(i)); inside |= pip(pts); edges.append(pts)
        for h in range(polys.HoleCount(i)):
            hp = poly_pts(polys.Hole(i, h)); inside &= ~pip(hp); edges.append(hp)
    for li in (0, 1): g.own[li][~inside] = BLOCK
    e = EDGE + W / 2 + SNAP
    for pts in edges:
        for k in range(len(pts)):
            (ax, ay), (bx, by) = pts[k], pts[(k + 1) % len(pts)]
            g.mark((0, 1), lambda X, Y: seg_dist(X, Y, ax, ay, bx, by) <= e,
                   (min(ax, bx) - e, min(ay, by) - e, max(ax, bx) + e, max(ay, by) + e), BLOCK)
    # pads and holes
    HOLES.clear()
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition(); HOLES.append((toMM(c.x), toMM(c.y), toMM(t.GetDrillValue()) / 2))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                c = p.GetPosition(); HOLES.append((toMM(c.x), toMM(c.y), toMM(p.GetDrillSize().x) / 2))
            net = p.GetNetCode() if p.GetNetCode() > 0 else BLOCK
            bb = p.GetBoundingBox()
            l, t, r, bt = toMM(bb.GetLeft()), toMM(bb.GetTop()), toMM(bb.GetRight()), toMM(bb.GetBottom())
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                c = p.GetPosition(); cx, cy = toMM(c.x), toMM(c.y); rad = toMM(p.GetDrillSize().x) / 2 + HOLE + W / 2 + SNAP
                g.mark((0, 1), lambda X, Y: np.hypot(X - cx, Y - cy) <= rad, (cx - rad, cy - rad, cx + rad, cy + rad), BLOCK)
                continue
            layers = [li_of(L) for L in LAYERS if p.IsOnLayer(L)]
            if p.GetShape(pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
                c = p.GetPosition(); cx, cy = toMM(c.x), toMM(c.y); rad = (r - l) / 2 + infl
                g.mark(layers, lambda X, Y: np.hypot(X - cx, Y - cy) <= rad, (cx - rad, cy - rad, cx + rad, cy + rad), net)
            else:
                g.mark(layers, lambda X, Y: (X >= l - infl) & (X <= r + infl) & (Y >= t - infl) & (Y <= bt + infl),
                       (l - infl, t - infl, r + infl, bt + infl), net)
    # existing tracks and vias
    for t in b.GetTracks():
        net = t.GetNetCode()
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition(); cx, cy = toMM(c.x), toMM(c.y)
            try: d = toMM(t.GetWidth(pcbnew.F_Cu))
            except TypeError: d = toMM(t.GetWidth())
            rad = d / 2 + infl
            g.mark((0, 1), lambda X, Y: np.hypot(X - cx, Y - cy) <= rad, (cx - rad, cy - rad, cx + rad, cy + rad), net)
        else:
            if t.GetLayer() not in LAYERS: continue
            a, c = t.GetStart(), t.GetEnd(); ax, ay, bx, by = toMM(a.x), toMM(a.y), toMM(c.x), toMM(c.y)
            rad = toMM(t.GetWidth()) / 2 + infl
            g.mark((li_of(t.GetLayer()),), lambda X, Y: seg_dist(X, Y, ax, ay, bx, by) <= rad,
                   (min(ax, bx) - rad, min(ay, by) - rad, max(ax, bx) + rad, max(ay, by) + rad), net)


HOLES = []          # (x, y, radius) of every drilled hole, filled by rasterize()
H2H = 0.25          # Lion Circuits-safe drill-to-drill spacing, mm

def via_ok(g, iy, ix, net, cache):
    k = (iy, ix)
    if k in cache: return cache[k]
    x, y = g.xy(iy, ix)
    if any(math.hypot(x - hx, y - hy) < hr + VIA_DRILL / 2 + H2H for hx, hy, hr in HOLES):
        cache[k] = False; return False
    r = int(math.ceil((VIA_D / 2 - W / 2) / G))
    sy, sx = slice(max(0, iy - r), iy + r + 1), slice(max(0, ix - r), ix + r + 1)
    ok = True
    for li in (0, 1):
        sub = g.own[li][sy, sx]
        yy, xx = np.ogrid[sy, sx]
        m = (yy - iy) ** 2 + (xx - ix) ** 2 <= r * r
        if np.any(m & (sub != FREE) & (sub != net)): ok = False; break
    cache[k] = ok
    return ok


def astar(g, net, starts, goals, max_expand=3_000_000):
    """starts/goals: lists of (layer_index, iy, ix). Returns list of (li, iy, ix) or None."""
    own = g.own
    goalset = set(goals)
    gy = np.mean([q[1] for q in goals]); gx = np.mean([q[2] for q in goals])
    h = lambda iy, ix: math.hypot(iy - gy, ix - gx) * STEP
    openh, came, cost = [], {}, {}
    for s in starts:
        cost[s] = 0.0; heapq.heappush(openh, (h(s[1], s[2]), 0.0, s))
    nb = [(-1, 0, STEP), (1, 0, STEP), (0, -1, STEP), (0, 1, STEP), (-1, -1, DIAG), (-1, 1, DIAG), (1, -1, DIAG), (1, 1, DIAG)]
    vcache, n = {}, 0
    while openh:
        f, c, s = heapq.heappop(openh)
        if c > cost.get(s, 1e18): continue
        if s in goalset:
            path = [s]
            while s in came: s = came[s]; path.append(s)
            return path[::-1]
        n += 1
        if n > max_expand: return None
        li, iy, ix = s
        for dy, dx, sc in nb:
            y2, x2 = iy + dy, ix + dx
            if not (0 <= y2 < g.ny and 0 <= x2 < g.nx): continue
            o = own[li, y2, x2]
            if o != FREE and o != net: continue
            if dy and dx and ((own[li, iy, x2] not in (FREE, net)) or (own[li, y2, ix] not in (FREE, net))): continue
            t = (li, y2, x2); nc = c + sc
            if nc < cost.get(t, 1e18):
                cost[t] = nc; came[t] = s; heapq.heappush(openh, (nc + h(y2, x2), nc, t))
        t = (1 - li, iy, ix)
        if own[1 - li, iy, ix] in (FREE, net) and via_ok(g, iy, ix, net, vcache):
            nc = c + VIA_COST
            if nc < cost.get(t, 1e18):
                cost[t] = nc; came[t] = s; heapq.heappush(openh, (nc + h(iy, ix), nc, t))
    return None


def endpoints(b, g, item_pos, net):
    """Grid cells (both feasible layers) for the copper item at item_pos on net."""
    x, y = item_pos
    v = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
    layers = set()
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == net and p.HitTest(v, pcbnew.FromMM(0.05)):
                layers |= {i for i, L in enumerate(LAYERS) if p.IsOnLayer(L)}
    for t in b.GetTracks():
        if t.GetNetCode() == net and t.HitTest(v, pcbnew.FromMM(0.05)):
            layers |= {0, 1} if isinstance(t, pcbnew.PCB_VIA) else {0 if t.GetLayer() == pcbnew.F_Cu else 1}
    iy, ix = g.cell(x, y)
    return [(li, iy, ix) for li in (layers or {0, 1})]


def to_tracks(b, g, path, netinfo, a_xy, b_xy):
    pts = [(li, *g.xy(iy, ix)) for li, iy, ix in path]
    pts[0] = (pts[0][0], *a_xy); pts[-1] = (pts[-1][0], *b_xy)
    # split into runs on one layer, simplify collinear points
    runs, cur, created = [], [pts[0]], []
    for p in pts[1:]:
        if p[0] != cur[-1][0]:
            runs.append(cur); via = p[1:]
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(via[0]), pcbnew.FromMM(via[1])))
            v.SetWidth(pcbnew.FromMM(VIA_D)); v.SetDrill(pcbnew.FromMM(VIA_DRILL)); v.SetNet(netinfo); b.Add(v)
            created.append(v)
            cur = [p]
        else:
            cur.append(p)
    runs.append(cur)
    for run in runs:
        simp = [run[0]]
        for k in range(1, len(run) - 1):
            (_, x0, y0), (_, x1, y1), (_, x2, y2) = simp[-1], run[k], run[k + 1]
            if abs((x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)) > 1e-6: simp.append(run[k])
        if len(run) > 1: simp.append(run[-1])
        for (li, ax, ay), (_, bx, by) in zip(simp, simp[1:]):
            if math.hypot(bx - ax, by - ay) < 1e-6: continue
            tr = pcbnew.PCB_TRACK(b); tr.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(ax), pcbnew.FromMM(ay)))
            tr.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by))); tr.SetWidth(pcbnew.FromMM(W))
            tr.SetLayer(LAYERS[li]); tr.SetNet(netinfo); b.Add(tr); created.append(tr)
    return created


def open_connections(include_gnd=False):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "drc.json"
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--units", "mm", "-o", str(out), str(PCB)], capture_output=True)
        data = json.loads(out.read_text())
    conns = []
    for x in data["unconnected_items"]:
        a, c = x["items"]
        if a["description"].startswith("Zone") or c["description"].startswith("Zone"):
            continue                          # zone-to-zone: DRC gives an anchor point, not real copper
        m = re.search(r"\[([^\]]+)\]", a["description"])
        if not m or (m.group(1).endswith("/GND") and not include_gnd): continue
        conns.append((m.group(1), (a["pos"]["x"], a["pos"]["y"]), (c["pos"]["x"], c["pos"]["y"])))
    return conns


def main(include_gnd=False):
    todo = open_connections(include_gnd)
    print(f"{len(todo)} open signal connections")
    if not todo: return
    b = route_pcb.load_without_zones()
    g = Grid(b); rasterize(b, g)
    print(f"grid {g.nx} x {g.ny} x 2, blocked {np.mean(g.own == BLOCK):.0%}")
    nets = b.GetNetsByName()
    done, failed = 0, []
    for name, pa, pb in sorted(todo, key=lambda c: math.dist(c[1], c[2])):
        ni = nets[name]; code = ni.GetNetCode()
        S, T = endpoints(b, g, pa, code), endpoints(b, g, pb, code)
        for li, iy, ix in S + T:             # endpoint cells belong to this net
            if g.own[li, iy, ix] == FREE: g.own[li, iy, ix] = code
        path = astar(g, code, S, T)
        if not path:
            failed.append(name); continue
        new = to_tracks(b, g, path, ni, pa, pb)
        for t2 in new:
            if isinstance(t2, pcbnew.PCB_VIA):
                c = t2.GetPosition(); HOLES.append((toMM(c.x), toMM(c.y), VIA_DRILL / 2))
        for t in new:                        # later routes must keep clear of this one
            infl = CLR + W / 2 + SNAP
            if isinstance(t, pcbnew.PCB_VIA):
                c = t.GetPosition(); cx, cy = toMM(c.x), toMM(c.y); rad = VIA_D / 2 + infl
                g.mark((0, 1), lambda X, Y: np.hypot(X - cx, Y - cy) <= rad, (cx - rad, cy - rad, cx + rad, cy + rad), code)
            else:
                a, c = t.GetStart(), t.GetEnd(); ax, ay, bx, by = toMM(a.x), toMM(a.y), toMM(c.x), toMM(c.y); rad = W / 2 + infl
                g.mark((0 if t.GetLayer() == pcbnew.F_Cu else 1,), lambda X, Y: seg_dist(X, Y, ax, ay, bx, by) <= rad,
                       (min(ax, bx) - rad, min(ay, by) - rad, max(ax, bx) + rad, max(ay, by) + rad), code)
        done += 1
    print(f"routed {done}, failed {len(failed)}: {sorted(set(failed))[:20]}")
    route_pcb.ground_pours(b)
    pcbnew.SaveBoard(str(PCB), b)


def pads_to_ground(pads, radius=30.0):
    """Route each (ref, pad) on a GND net to the nearest GND via (vias tie both pour layers
    together, so this reconnects a pad stranded in a small pocket of fill)."""
    b = route_pcb.load_without_zones()
    g = Grid(b); rasterize(b, g)
    done = []
    for ref, num in pads:
        pad = next(p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num)
        code, ni = pad.GetNetCode(), pad.GetNet()
        c = pad.GetPosition(); px, py = toMM(c.x), toMM(c.y)
        S = endpoints(b, g, (px, py), code)
        for li, iy, ix in S:
            if g.own[li, iy, ix] == FREE: g.own[li, iy, ix] = code
        T = []
        for v in b.GetTracks():
            if isinstance(v, pcbnew.PCB_VIA) and v.GetNetCode() == code:
                q = v.GetPosition(); vx, vy = toMM(q.x), toMM(q.y)
                if 0.8 < math.hypot(vx - px, vy - py) < radius:
                    iy, ix = g.cell(vx, vy); T += [(0, iy, ix), (1, iy, ix)]
        path = astar(g, code, S, T) if T else None
        if not path:
            print(f"  {ref}.{num}: no path"); continue
        li, iy, ix = path[-1]
        to_tracks(b, g, path, ni, (px, py), g.xy(iy, ix))
        done.append(f"{ref}.{num}")
    route_pcb.ground_pours(b)
    pcbnew.SaveBoard(str(PCB), b)
    print(f"tied to ground: {done}")


if __name__ == "__main__":
    if "--pads-to-ground" in sys.argv:
        pads_to_ground([tuple(a.split(".")) for a in sys.argv[sys.argv.index("--pads-to-ground") + 1:]])
        sys.exit()
    main(include_gnd="--include-gnd" in sys.argv)
