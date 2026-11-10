#!/usr/bin/env python3
"""Widen the battery and LED supply tracks (BAT_RAW, VBAT, LED_VDD) wherever clearance allows.

The routers lay most tracks at 0.25 mm. These nets carry the LED boost's input current (about
0.75 A at the 40 % cap, more on a low cell) and the LED rail, so each of their segments narrower
than 0.6 mm is widened to the first of 0.6, 0.5 or 0.4 mm that keeps 0.21 mm from other nets'
copper, 0.26 mm from other nets' holes, 0.25 mm from the board edge and out of the keep-out
areas. Run it after smooth_route.py (which joins only runs of one width), then refill the zones
(cleanup_pcb.py does). Edits are made on the file text. Needs shapely: run it with the keygen-cad
venv's python (notes/17).
"""
import collections, re, sys
from pathlib import Path

import pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).parent))
from sexp import parse, dump, first

PCB = Path(__file__).resolve().parent.parent / "pcb/keygen.kicad_pcb"
POWER = re.compile(r"/(left|right)/(BAT_RAW|VBAT|LED_VDD)$")
WIDTHS = (0.6, 0.5, 0.4)
CLR, HOLE_CLR, EDGE_CLR = 0.21, 0.26, 0.25
T = pcbnew.ToMM
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


def spoly(ps):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(T(o.CPoint(j).x), T(o.CPoint(j).y)) for j in range(o.PointCount())]
        if len(pts) >= 3:
            holes = [[(T(ps.Hole(i, h).CPoint(j).x), T(ps.Hole(i, h).CPoint(j).y))
                      for j in range(ps.Hole(i, h).PointCount())] for h in range(ps.HoleCount(i))]
            out.append(Polygon(pts, holes).buffer(0))
    return unary_union(out) if out else Polygon()


def shape(item, layer):
    s = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(s, layer, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
    return spoly(s)


def main():
    b = pcbnew.LoadBoard(str(PCB))
    copper = {L: [] for L in LAYERS}          # [geometry, net, uuid or None]
    holes = []                                # (geometry, net)
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            q = t.GetPosition(); c = Point(T(q.x), T(q.y))
            for L in LAYERS: copper[L].append([c.buffer(T(t.GetWidth(pcbnew.F_Cu)) / 2, 16), t.GetNetname(), None])
            holes.append((c.buffer(T(t.GetDrillValue()) / 2, 16), t.GetNetname()))
        elif t.GetLayer() in LAYERS:
            copper[t.GetLayer()].append([shape(t, t.GetLayer()), t.GetNetname(), t.m_Uuid.AsString()])
    for fp in b.GetFootprints():
        for p in fp.Pads():
            for L in LAYERS:
                if p.IsOnLayer(L) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    copper[L].append([shape(p, L), p.GetNetname(), None])
            if p.GetDrillSize().x > 0:
                q = p.GetPosition()
                holes.append((Point(T(q.x), T(q.y)).buffer(T(p.GetDrillSize().x) / 2, 16), p.GetNetname()))
    keepouts = [spoly(z.Outline()) for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]
    outline = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(outline, False)
    inside = spoly(outline).buffer(-EDGE_CLR)
    hole_tree = STRtree([g for g, _ in holes])

    wider = {}
    for L in LAYERS:
        where = {item[2]: i for i, item in enumerate(copper[L]) if item[2]}
        tree = STRtree([g for g, _, _ in copper[L]])
        for t in b.GetTracks():
            if t.GetClass() != "PCB_TRACK" or t.GetLayer() != L or not POWER.search(t.GetNetname()): continue
            if T(t.GetWidth()) >= WIDTHS[0] - 1e-6: continue
            a, e = t.GetStart(), t.GetEnd()
            line = LineString([(T(a.x), T(a.y)), (T(e.x), T(e.y))]) if a != e else Point(T(a.x), T(a.y))
            net, uid = t.GetNetname(), t.m_Uuid.AsString()
            for w in WIDTHS:
                if w <= T(t.GetWidth()) + 1e-6: break
                g = line.buffer(w / 2, 16)
                if not inside.contains(g) or any(g.intersects(k) for k in keepouts): continue
                if any(copper[L][i][1] != net and g.distance(copper[L][i][0]) < CLR for i in tree.query(g.buffer(CLR))):
                    continue
                if any((holes[i][1] != net or not net) and g.distance(holes[i][0]) < HOLE_CLR
                       for i in hole_tree.query(g.buffer(HOLE_CLR))):
                    continue
                wider[uid] = w
                copper[L][where[uid]][0] = g
                tree = STRtree([gg for gg, _, _ in copper[L]])
                break
    del b
    tree = parse(PCB.read_text())
    for n in tree:
        if isinstance(n, list) and n and n[0] == "segment" and first(n, "uuid")[1] in wider:
            first(n, "width")[1] = wider[first(n, "uuid")[1]]
    PCB.write_text(dump(tree) + "\n")
    print(f"widened {len(wider)} supply segments: {dict(sorted(collections.Counter(wider.values()).items()))}")


if __name__ == "__main__":
    main()
