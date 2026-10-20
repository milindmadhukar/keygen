#!/usr/bin/env python3
"""Square off each half's bottom edge under the bottom row and thumb cluster.

gen_pcb.py draws each half as the convex hull of its keys, so the bottom edge runs straight
from the outer bottom key to the thumb-cluster tip and leaves a wedge of bare board under the
bottom row, right where the wrists come in. This swaps that one hull edge for two: a flat line
along the bottom of the outer bottom key, then a straight run down to the thumb tip, as steep
as the thumb keys (cells grown 0.6 mm, as gen_pcb's hull), pads (0.5 mm) and
mounting holes (2.9 mm) below the flat allow. Both halves get the same, mirrored, edge. Vias
and tracks left outside or on the new edge are dropped and the zones refilled; reroute what
that cut with finish_route.py.

    python3 tools/trim_outline.py [--out other.kicad_pcb]
"""
import argparse, math, sys, uuid
from collections import Counter
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
from sexp import parse, dump, first, Sym
import gen_pcb as G

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
ToMM = pcbnew.ToMM

CELL_GROW = 0.6       # mm outside each key's 19.05 mm cell, as gen_pcb's hull
PAD_CLR = 0.5         # mm from any pad to the edge
HOLE_EDGE = 2.9       # mm from a mounting hole's centre to the edge: H104/H203 sit 3.0 mm inside
                      # the thumb keys' line (gen_pcb kept 4.0 from the old hull)
TRACK_CLR = 0.25      # mm from via or track copper to the edge (project copper-to-edge rule + margin)


def ends(node):
    (x1, y1), (x2, y2) = [tuple(map(float, first(node, k)[1:3])) for k in ("start", "end")]
    return ((x1, y1), (x2, y2)) if x1 < x2 else ((x2, y2), (x1, y1))


def bottom_edges(tree):
    """{side: gr_line node} for the lowest long Edge.Cuts line of each half."""
    best = {}
    for n in tree:
        if not (isinstance(n, list) and n and n[0] == "gr_line" and first(n, "layer")[1] == "Edge.Cuts"): continue
        (x1, y1), (x2, y2) = ends(n)
        if math.hypot(x2 - x1, y2 - y1) < 50: continue
        side = "left" if x1 + x2 < 2 * (G.OFF[0] + G.MIRROR_X / 2) else "right"
        if side not in best or y1 + y2 > best[side][1]:
            best[side] = (n, y1 + y2)
    return {s: v[0] for s, v in best.items()}


def obstacles(b, side, x0, x1):
    """Points the edge must keep below: the outline of each grown key cell, and circles (as
    polygons drawn just outside them) around pads and mounting holes. Board mm. Tracks don't
    count: any left outside are dropped and rerouted."""
    pts, circles = [], []
    for (s, r, c), (cx, cy, rr, w, h, corners) in G.key_geometry().items():
        if s != side: continue
        cell = [(x + G.OFF[0], y + G.OFF[1]) for x, y in G.grow(corners, cx, cy, CELL_GROW)]
        for (ax, ay), (bx, by) in zip(cell, cell[1:] + cell[:1]):     # along the sides too, so a
            n = max(1, int(math.hypot(bx - ax, by - ay) / 0.2))        # split mid-key sees the key
            pts += [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(n)]
    near = lambda x: x0 - 25 < x < x1 + 25
    for fp in b.GetFootprints():
        p = fp.GetPosition()
        if not near(ToMM(p.x)): continue
        if fp.GetReference().startswith("H"):
            circles.append((ToMM(p.x), ToMM(p.y), HOLE_EDGE))
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            circles.append((ToMM(bb.Centre().x), ToMM(bb.Centre().y),
                            math.hypot(ToMM(bb.GetWidth()), ToMM(bb.GetHeight())) / 2 + PAD_CLR))
    for cx, cy, r in circles:
        n = max(16, math.ceil(2 * math.pi * r / 0.2)); k = r / math.cos(math.pi / n)
        pts += [(cx + k * math.cos(2 * math.pi * i / n), cy + k * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return pts


def trim(pts, xa, ya, xb, yb):
    """Two lines in place of the hull edge (xa, ya)-(xb, yb): flat along the bottom of the outer
    bottom key, then straight down to the thumb tip, as steep as the parts below the flat allow.
    Returns (area cut, corners)."""
    xt, yt = xb, yb
    m = min((yt - y) / (xt - x) for x, y in pts if y > ya + 0.01 and x < xt - 0.01)
    corner = (xt - (yt - ya) / m, ya)
    if not xa < corner[0] < xt: raise SystemExit(f"no room for the flat: corner at {corner}")
    line = lambda x: ya + (yb - ya) * (x - xa) / (xb - xa)
    cut = (line(corner[0]) - ya) * (xt - xa) / 2           # triangle under the old edge
    return cut, [(xa, ya), corner, (xt, yt)]


def mirror(pts):
    """Same points on the other half (the halves mirror about the gap between them)."""
    return [(2 * (G.OFF[0] + G.MIRROR_X / 2) - x, y) for x, y in pts]


def gr_line(a, b):
    return [Sym("gr_line"), [Sym("start"), round(a[0], 4), round(a[1], 4)], [Sym("end"), round(b[0], 4), round(b[1], 4)],
            [Sym("stroke"), [Sym("width"), 0.1], [Sym("type"), Sym("default")]], [Sym("layer"), "Edge.Cuts"],
            [Sym("uuid"), str(uuid.uuid4())]]


def below(edge, x, y, r):
    """A circle (x, y, r) reaches past the edge polyline."""
    for (ax, ay), (bx, by) in zip(edge, edge[1:]):
        vx, vy = bx - ax, by - ay; L = math.hypot(vx, vy)
        t = max(0, min(1, ((x - ax) * vx + (y - ay) * vy) / (L * L)))
        if math.hypot(x - ax - t * vx, y - ay - t * vy) < r: return True
        if ax <= x <= bx and y > ay + vy * (x - ax) / vx: return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=PCB)
    args = ap.parse_args()
    b = pcbnew.LoadBoard(str(PCB))
    tree = parse(PCB.read_text())
    edges = bottom_edges(tree)
    (xa, ya), (xb, yb) = ends(edges["left"])
    if not all(math.dist(p, q) < 1e-3 for p, q in zip(mirror(ends(edges["left"])), ends(edges["right"])[::-1])):
        raise SystemExit("the halves' bottom edges are not mirror images")
    # one edge for both halves (the right one mirrored), cut around either half's parts
    pts = obstacles(b, "left", xa, xb) + mirror(obstacles(b, "right", 2 * (G.OFF[0] + G.MIRROR_X / 2) - xb,
                                                          2 * (G.OFF[0] + G.MIRROR_X / 2) - xa))
    cut, edge = trim(pts, xa, ya, xb, yb)
    new_edges = [edge, mirror(edge)[::-1]]
    new_lines = [gr_line(p, q) for e in new_edges for p, q in zip(e, e[1:])]
    print(f"bottom edge ({xa:.2f},{ya:.2f})-({xb:.2f},{yb:.2f}) on the left, mirrored on the right, now: "
          + " ".join(f"({x:.2f},{y:.2f})" for x, y in edge) + f"; {cut / 100:.1f} cm² cut per half")
    def crosses(n):
        """A via or segment whose copper reaches the new edge or lies past it."""
        if n[0] == "via":
            x, y = map(float, first(n, "at")[1:3])
            return any(below(e, x, y, float(first(n, "size")[1]) / 2 + TRACK_CLR) for e in new_edges)
        (ax, ay), (bx, by) = [tuple(map(float, first(n, k)[1:3])) for k in ("start", "end")]
        r, k = float(first(n, "width")[1]) / 2 + TRACK_CLR, max(1, int(math.hypot(bx - ax, by - ay) / 0.1))
        return any(below(e, ax + (bx - ax) * i / k, ay + (by - ay) * i / k, r) for e in new_edges for i in range(k + 1))
    gone, keep, dropped = {id(n) for n in edges.values()}, [], Counter()
    for n in tree:
        if isinstance(n, list) and n and n[0] in ("via", "segment") and crosses(n):
            dropped[(n[0], first(n, "net")[1])] += 1; continue
        if id(n) not in gone: keep.append(n)
    tree[:] = keep + new_lines
    args.out.write_text(dump(tree) + "\n")
    for (kind, net), k in sorted(dropped.items()):
        print(f"dropped {k} {kind}{'s' * (k > 1)} on {net}")
    if any(kind == "segment" for kind, net in dropped):
        print("tracks were cut: run tools/finish_route.py, cleanup_pcb.py and sync_pcb.py, then DRC")
    b = pcbnew.LoadBoard(str(args.out))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(args.out), b)


if __name__ == "__main__":
    main()
