#!/usr/bin/env python3
"""Run each half's bottom edge along the bottom row and the thumb keys.

gen_pcb.py draws each half as the convex hull of its keys, so the bottom edge runs straight
from the outer bottom key to the thumb-cluster tip and leaves a wedge of bare board under the
bottom row, right where the wrists come in. This swaps the bottom of the outline, from the outer
bottom key round to the thumb tip, for lines that follow the keys: flat along the bottom of the
bottom row, along the bottom of the 1.25u thumb key (15°) if it reaches below the other two, and
along the bottom of the 2x2 thumb block (30°) to its tip. Each line runs along its keys' cells grown 0.6 mm, as
gen_pcb's hull, and moves out, still parallel, past any pad (0.5 mm) or mounting hole (2.9 mm)
that would cross it. Both halves get the same, mirrored, edge. Vias and tracks left outside or
on the new edge are dropped and the zones refilled; reroute what that cut with finish_route.py.
Rerunnable: it replaces whatever bottom edge the board has.

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


def edge_lines(tree, side):
    """The Edge.Cuts gr_lines of one half."""
    mid = G.OFF[0] + G.MIRROR_X / 2
    return [n for n in tree if isinstance(n, list) and n and n[0] == "gr_line" and first(n, "layer")[1] == "Edge.Cuts"
            and ((ends(n)[0][0] + ends(n)[1][0]) < 2 * mid) == (side == "left")]


def bottom_chain(tree, side, start):
    """The gr_lines from `start` (the outer bottom key's corner) along the bottom of the half to
    its lowest point, the thumb tip, and that tip."""
    lines = edge_lines(tree, side)
    pts = [p for n in lines for p in ends(n)]
    tip = max(pts, key=lambda p: p[1])
    cur, chain, step = min(pts, key=lambda p: math.dist(p, start)), [], 1 if side == "left" else -1
    if math.dist(cur, start) > 0.05: raise SystemExit(f"{side}: no outline corner at {start}")
    while math.dist(cur, tip) > 1e-6:
        nxt = [n for n in lines if n not in chain and any(math.dist(cur, q) < 1e-6 for q in ends(n))]
        nxt = [n for n in nxt if step * (sum(q[0] for q in ends(n)) / 2 - cur[0]) > 0]
        if len(nxt) != 1: raise SystemExit(f"{side}: can't follow the bottom edge from {cur}")
        chain.append(nxt[0]); cur = next(q for q in ends(nxt[0]) if math.dist(cur, q) > 1e-6)
    return chain, tip


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


def cell(side, key):
    """A key's cell grown CELL_GROW, board mm: corners top-left, top-right, bottom-right, bottom-left
    in the key's own frame."""
    cx, cy, rr, w, h, corners = G.key_geometry()[(side, *key)]
    return [(x + G.OFF[0], y + G.OFF[1]) for x, y in G.grow(corners, cx, cy, CELL_GROW)]


def meet(l1, l2):
    """Intersection of two lines, each (point, direction)."""
    (p, d), (q, e) = l1, l2
    den = d[0] * e[1] - d[1] * e[0]
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (p[0] + t * d[0], p[1] + t * d[1])


def trim(pts):
    """The left half's new bottom edge, outer bottom key corner to thumb tip: along the bottom
    row, the 1.25u thumb key and the 2x2 thumb block, each line pushed out (parallel) past any
    obstacle point below it."""
    row, one25, block = cell("left", (4, 0)), cell("left", (4, 4)), (cell("left", (4, 5)), cell("left", (4, 6)))
    lines = [(row[3], (1.0, 0.0)), (one25[3], (one25[2][0] - one25[3][0], one25[2][1] - one25[3][1])),
             (block[0][3], (block[1][2][0] - block[0][3][0], block[1][2][1] - block[0][3][1]))]
    start, tip = row[3], block[1][2]
    y_at = lambda l, x: l[0][1] + l[1][1] / l[1][0] * (x - l[0][0])
    for _ in range(20):
        # the lowest of the lines at each x (lines in order of steepness): skip a line that
        # never comes out lowest between its neighbours
        use = [0, 1, 2] if meet(lines[0], lines[1])[0] < meet(lines[1], lines[2])[0] else [0, 2]
        edge = [start] + [meet(lines[i], lines[j]) for i, j in zip(use, use[1:])] + [tip]
        if not all(a[0] < b[0] for a, b in zip(edge, edge[1:])): raise SystemExit(f"bottom edge folds back: {edge}")
        worst = {}
        for x, y in pts:
            for i, (a, b) in zip(use, zip(edge, edge[1:])):
                if not a[0] <= x <= b[0]: continue
                d = (b[0] - a[0], b[1] - a[1]); L = math.hypot(*d)
                out = ((x - a[0]) * -d[1] + (y - a[1]) * d[0]) / L      # distance past the line, outward
                if out > 1e-3: worst[i] = max(worst.get(i, 0), out)
        if not worst: return edge
        for i, o in worst.items():
            (px, py), d = lines[i]; L = math.hypot(*d)
            lines[i] = ((px - d[1] / L * o, py + d[0] / L * o), d)
            if i == 2: tip = meet(lines[2], (tip, (d[1], -d[0])))   # the tip slides out with its line
    raise SystemExit("bottom edge: obstacles keep crossing it")


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
    mid2 = 2 * (G.OFF[0] + G.MIRROR_X / 2)
    # one edge for both halves (the right one mirrored), cut around either half's parts
    pts = obstacles(b, "left", 30, 200) + mirror(obstacles(b, "right", mid2 - 200, mid2 - 30))
    edge = trim(pts)
    chains = {"left": bottom_chain(tree, "left", edge[0]), "right": bottom_chain(tree, "right", mirror([edge[0]])[0])}
    new_edges = [edge, mirror(edge)[::-1]]
    new_lines = [gr_line(p, q) for e in new_edges for p, q in zip(e, e[1:])]
    print("bottom edge on the left, mirrored on the right: " + " ".join(f"({x:.2f},{y:.2f})" for x, y in edge))
    # the outline's other line into the old tip now ends at the new one
    for side, (chain, old_tip) in chains.items():
        new_tip = edge[-1] if side == "left" else mirror([edge[-1]])[0]
        for n in edge_lines(tree, side):
            if n in chain: continue
            for k in ("start", "end"):
                node = first(n, k)
                if math.dist((float(node[1]), float(node[2])), old_tip) < 1e-6:
                    node[1], node[2] = round(new_tip[0], 4), round(new_tip[1], 4)
    def crosses(n):
        """A via or segment whose copper reaches the new edge or lies past it."""
        if n[0] == "via":
            x, y = map(float, first(n, "at")[1:3])
            return any(below(e, x, y, float(first(n, "size")[1]) / 2 + TRACK_CLR) for e in new_edges)
        (ax, ay), (bx, by) = [tuple(map(float, first(n, k)[1:3])) for k in ("start", "end")]
        r, k = float(first(n, "width")[1]) / 2 + TRACK_CLR, max(1, int(math.hypot(bx - ax, by - ay) / 0.1))
        return any(below(e, ax + (bx - ax) * i / k, ay + (by - ay) * i / k, r) for e in new_edges for i in range(k + 1))
    gone, keep, dropped = {id(n) for chain, tip in chains.values() for n in chain}, [], Counter()
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
