#!/usr/bin/env python3
"""Write assets/pcb-routing.png: both halves' copper on a dark board, front tracks red, back tracks
blue, pads gold, vias white. Zone fills are left out so the routing shows.

    python3 tools/render_routing.py [board.kicad_pcb] [out.png]
"""
import subprocess, sys
from pathlib import Path

import cairo
import pcbnew

ROOT = Path(__file__).resolve().parent.parent
board = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "pcb/keygen.kicad_pcb")
out = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "assets/pcb-routing.png")
b = pcbnew.LoadBoard(board)
mm = pcbnew.ToMM
poly = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(poly, False)
bb = b.GetBoardEdgesBoundingBox(); X0, Y0 = mm(bb.GetLeft()) - 4, mm(bb.GetTop()) - 4
W, H = mm(bb.GetWidth()) + 8, mm(bb.GetHeight()) + 8; S = 7
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * S), int(H * S)); c = cairo.Context(surf)
c.scale(S, S); c.translate(-X0, -Y0)
def outline(o):
    c.move_to(mm(o.CPoint(0).x), mm(o.CPoint(0).y))
    for j in range(1, o.PointCount()): c.line_to(mm(o.CPoint(j).x), mm(o.CPoint(j).y))
    c.close_path()
c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
for i in range(poly.OutlineCount()):
    outline(poly.Outline(i))
    for h in range(poly.HoleCount(i)): outline(poly.Hole(i, h))
c.set_source_rgb(0.07, 0.09, 0.11); c.fill_preserve(); c.set_source_rgb(0.75, 0.78, 0.8); c.set_line_width(0.35); c.stroke()
c.set_line_cap(cairo.LINE_CAP_ROUND)
cols = {pcbnew.B_Cu: (0.30, 0.55, 0.95, 0.85), pcbnew.F_Cu: (0.93, 0.33, 0.30, 0.85)}
for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
    c.set_source_rgba(*cols[layer])
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != layer: continue
        c.set_line_width(mm(t.GetWidth())); c.move_to(mm(t.GetStart().x), mm(t.GetStart().y)); c.line_to(mm(t.GetEnd().x), mm(t.GetEnd().y)); c.stroke()
c.set_source_rgba(0.85, 0.72, 0.35, 0.9)
for fp in b.GetFootprints():
    for p in fp.Pads():
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not p.IsOnLayer(layer): continue
            sp = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(sp, layer, 0, pcbnew.FromMM(0.01), pcbnew.ERROR_INSIDE)
            for i in range(sp.OutlineCount()): outline(sp.Outline(i))
            c.fill(); break
        if p.GetDrillSizeX() > 0:
            q = p.GetPosition(); c.save(); c.set_source_rgb(0.07, 0.09, 0.11)
            c.arc(mm(q.x), mm(q.y), mm(p.GetDrillSizeX()) / 2, 0, 6.2832); c.fill(); c.restore()
c.set_source_rgba(0.9, 0.9, 0.9, 0.9)
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        c.arc(mm(t.GetPosition().x), mm(t.GetPosition().y), mm(t.GetWidth(pcbnew.F_Cu)) / 2, 0, 6.2832); c.fill()
surf.write_to_png(out)
subprocess.run(["magick", out, "-trim", "+repage", "-bordercolor", "none", "-border", "20",
                "-resize", "2000x", "-strip", out], check=True)
print(f"wrote {out}")
