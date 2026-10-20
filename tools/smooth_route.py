#!/usr/bin/env python3
"""Straighten routed tracks into clean 0/45/90 degree runs.

The grid maze router (finish_route.py) steps on a 0.2 mm grid, so its paths come out as
staircases of tiny orthogonal and diagonal segments, and Freerouting leaves bends it never
optimised away. This pass walks every chain of tracks (one net, one layer, one width, between
pads, vias and junctions) and string-pulls it: from each point it jumps to the farthest later
point that one straight segment, or one straight plus one 45 degree segment, can reach without
breaking clearance to other nets' copper, holes or the board edge. A chain is only replaced if
the new path still touches every pad, via and track the old one touched.

Edits are made on the file text (removing items through the Python API corrupts the board in
KiCad 10), then the zones are refilled and any ground fill
piece a moved track cut off is stitched back with a via. KiCad's DRC is the judge of the result.
"""
import math, sys, uuid
from collections import defaultdict
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
from sexp import parse, dump, first, Sym
import route_pcb

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
mm, ToMM = pcbnew.FromMM, pcbnew.ToMM
CLR, HOLE_CLR, EDGE_CLR = mm(0.21), mm(0.26), mm(0.25)   # project rules (0.2/0.25/0.2) plus margin
BUCKET = mm(2.0)
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
V = pcbnew.VECTOR2I


class Obstacles:
    """Copper, holes and board edges per layer, in a spatial hash of 2 mm buckets."""
    def __init__(self):
        self.items, self.cells = {}, defaultdict(set)

    def _keys(self, li, bb):
        x0, y0, x1, y1 = bb
        for i in range(x0 // BUCKET, x1 // BUCKET + 1):
            for j in range(y0 // BUCKET, y1 // BUCKET + 1):
                yield li, i, j

    def add(self, key, li, net, shape, clr):
        bb = shape.BBox()
        bb = (bb.GetLeft() - clr, bb.GetTop() - clr, bb.GetRight() + clr, bb.GetBottom() + clr)
        self.items[key] = (li, net, shape, clr, bb)
        for k in self._keys(li, bb): self.cells[k].add(key)

    def remove(self, key):
        li, _, _, _, bb = self.items.pop(key)
        for k in self._keys(li, bb): self.cells[k].discard(key)

    def near(self, li, a, b, w):
        bb = (min(a.x, b.x) - w, min(a.y, b.y) - w, max(a.x, b.x) + w, max(a.y, b.y) + w)
        keys = set()
        for k in self._keys(li, bb): keys |= self.cells.get(k, set())
        return [(k, self.items[k]) for k in keys]

    def clear(self, li, net, a, b, w):
        a, b = V(*a), V(*b)
        seg = pcbnew.SHAPE_SEGMENT(a, b, w)
        for _, (_, n, shape, clr, _) in self.near(li, a, b, w):
            if (n != net or n <= 0) and shape.Collide(seg, clr): return False
        return True

    def touched(self, li, net, segs, w):
        """Keys of same-net items that the chain of segments touches."""
        out = set()
        for a, b in segs:
            a, b = V(*a), V(*b)
            seg = pcbnew.SHAPE_SEGMENT(a, b, w)
            for k, (_, n, shape, _, _) in self.near(li, a, b, w):
                if n == net and n > 0 and shape.Collide(seg, 0): out.add(k)
        return out


def build(b):
    obs = Obstacles()
    for t in b.GetTracks():
        net = t.GetNetCode()
        if isinstance(t, pcbnew.PCB_VIA):
            for li, L in enumerate(LAYERS):
                obs.add(("via", t.m_Uuid.AsString(), li), li, net, t.GetEffectiveShape(L), CLR)
                obs.add(("vhole", t.m_Uuid.AsString(), li), li, net, t.GetEffectiveHoleShape(), HOLE_CLR)
        elif t.GetLayer() in LAYERS:
            li = LAYERS.index(t.GetLayer())
            obs.add(("trk", t.m_Uuid.AsString()), li, net, pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth()), CLR)
    for fp in b.GetFootprints():
        for k, p in enumerate(fp.Pads()):
            net = p.GetNetCode()
            npth = p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
            for li, L in enumerate(LAYERS):
                if p.IsOnLayer(L) and not npth:
                    obs.add(("pad", fp.GetReference(), k, li), li, net, p.GetEffectiveShape(L), CLR)
                if p.GetDrillSize().x > 0:
                    obs.add(("phole", fp.GetReference(), k, li), li, -1 if npth else net, p.GetEffectiveHoleShape(), HOLE_CLR)
    polys = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(polys, False)
    chains = []
    for i in range(polys.OutlineCount()):
        chains.append(polys.Outline(i))
        chains += [polys.Hole(i, h) for h in range(polys.HoleCount(i))]
    for ci, ch in enumerate(chains):
        n = ch.PointCount()
        for k in range(n):
            s = pcbnew.SHAPE_SEGMENT(ch.CPoint(k), ch.CPoint((k + 1) % n), 0)
            for li in (0, 1): obs.add(("edge", ci, k, li), li, -1, s, EDGE_CLR)
    return obs


def chains(b):
    """Yield (net, layer index, width, [points], [track uuids]) for each run of tracks between
    anchors: pads, vias, junctions, dead ends and width changes."""
    segs = defaultdict(list)            # (net, li) -> tracks
    vias = set()
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            vias.add((t.GetPosition().x, t.GetPosition().y))
        elif t.GetLayer() in LAYERS:
            segs[(t.GetNetCode(), LAYERS.index(t.GetLayer()))].append(t)
    pads = defaultdict(list)
    for fp in b.GetFootprints():
        for p in fp.Pads(): pads[p.GetNetCode()].append(p)
    for (net, li), ts in segs.items():
        adj = defaultdict(list)
        for t in ts:
            a, c = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            if a == c: continue
            adj[a].append((t, c)); adj[c].append((t, a))
        def anchor(p):
            if len(adj[p]) != 2 or p in vias: return True
            if adj[p][0][0].GetWidth() != adj[p][1][0].GetWidth(): return True
            return any(pd.IsOnLayer(LAYERS[li]) and pd.HitTest(V(*p)) for pd in pads[net])
        seen = set()
        for start in [p for p in adj if anchor(p)]:
            for t, nxt in adj[start]:
                if t.m_Uuid.AsString() in seen: continue
                pts, ids, cur = [start], [], start
                while True:
                    seen.add(t.m_Uuid.AsString()); ids.append(t.m_Uuid.AsString()); pts.append(nxt)
                    if anchor(nxt): break
                    t, nxt2 = next((u, q) for u, q in adj[nxt] if u.m_Uuid.AsString() not in seen)
                    cur, nxt = nxt, nxt2
                yield net, li, t.GetWidth(), pts, ids


def connectors(a, b):
    """Octilinear paths from a to b: one segment if a-b is already at 0/45/90, else the two ways
    of splitting it into a 45 degree leg and a straight leg."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == 0 or dy == 0 or abs(dx) == abs(dy): return [[a, b]]
    sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
    d = min(abs(dx), abs(dy))
    diag = (a[0] + sx * d, a[1] + sy * d)
    straight = (b[0] - sx * d, b[1] - sy * d)
    return [[a, diag, b], [a, straight, b]]


def simplify(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if p == out[-1]: continue
        if len(out) >= 2:
            (x0, y0), (x1, y1) = out[-2], out[-1]
            if (x1 - x0) * (p[1] - y1) - (y1 - y0) * (p[0] - x1) == 0 and (x1 - x0) * (p[0] - x1) + (y1 - y0) * (p[1] - y1) >= 0:
                out[-1] = p; continue
        out.append(p)
    return out


def pull(obs, net, li, w, pts):
    out, i, n = [pts[0]], 0, len(pts) - 1
    while i < n:
        for j in range(n, i, -1):
            path = next((c for c in connectors(pts[i], pts[j])
                         if all(obs.clear(li, net, p, q, w) for p, q in zip(c, c[1:]))), None)
            if path: break
        else:
            j, path = i + 1, [pts[i], pts[i + 1]]         # keep the original segment
        out += path[1:]; i = j
    return simplify(out)


def smooth_once(b):
    obs = build(b)
    removed, added = set(), []
    for net, li, w, pts, ids in list(chains(b)):
        if len(pts) == 2 and len(connectors(*pts)) == 1: continue      # already one straight run
        own = [("trk", u) for u in ids]
        old = obs.touched(li, net, list(zip(pts, pts[1:])), w) - set(own)
        for k in own: obs.remove(k)
        new = pull(obs, net, li, w, pts)
        if new != simplify(pts):
            segs = list(zip(new, new[1:]))
            if obs.touched(li, net, segs, w) >= old:
                for p, q in segs:
                    u = str(uuid.uuid4())
                    obs.add(("trk", u), li, net, pcbnew.SHAPE_SEGMENT(V(*p), V(*q), w), CLR)
                    added.append((p, q, w, li, net, u))
                removed |= set(ids)
                continue
        for k, (p, q) in zip(own, zip(pts, pts[1:])):     # unchanged: put the chain back
            obs.add(k, li, net, pcbnew.SHAPE_SEGMENT(V(*p), V(*q), w), CLR)
    return removed, added


def write(b, removed, added):
    names = {n.GetNetCode(): n.GetNetname() for n in b.GetNetsByName().values()}
    tree = parse(PCB.read_text())
    keep = [n for n in tree if not (isinstance(n, list) and n and n[0] == "segment" and first(n, "uuid")[1] in removed)]
    f = lambda v: round(ToMM(v), 6)
    for p, q, w, li, net, u in added:
        keep.append([Sym("segment"), [Sym("start"), f(p[0]), f(p[1])], [Sym("end"), f(q[0]), f(q[1])],
                     [Sym("width"), f(w)], [Sym("layer"), "F.Cu" if li == 0 else "B.Cu"], [Sym("net"), names[net]],
                     [Sym("uuid"), u]])
    tree[:] = keep
    PCB.write_text(dump(tree) + "\n")


def count():
    b = pcbnew.LoadBoard(str(PCB))
    return sum(1 for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))


def main(passes=4):
    print(f"segments before: {count()}")
    for k in range(passes):
        b = pcbnew.LoadBoard(str(PCB))
        removed, added = smooth_once(b)
        print(f"pass {k + 1}: replaced {len(removed)} segments with {len(added)}")
        if not removed: break
        write(b, removed, added)
    b = pcbnew.LoadBoard(str(PCB))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    if route_pcb.stitch_fragments(b):              # moved tracks can split a ground fill in two
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB), b)
    print(f"segments after: {count()}")


if __name__ == "__main__":
    main()
