#!/usr/bin/env python3
"""The switch plate: clear polycarbonate, CNC-routed from 1.5 mm sheet with the DXFs, or the same
plate in FR-4, made by a PCB fab as a 1.6 mm board with no copper from the Gerbers.

pcb/plate/keygen-plate.kicad_pcb     both halves (KiCad 10), black mask
case/plate/gerber/keygen-plate-left-gerbers.zip    } one order per half, like the PCB
case/plate/gerber/keygen-plate-right-gerbers.zip   }
case/plate/PLATE.md                                how to cut the sheet, and the fab's order form

Each half follows its PCB outline, plus the gasket tabs that sit between Poron strips in the case.
It has a 14 x 14 mm cut-out per switch (rotated with the key), a cut-out for each encoder, a window
for each OLED module, and the PCB's M2 holes for the plate-to-PCB standoffs. Geometry comes from
case_geometry.py, so rerun this after any PCB change.
"""
import math, subprocess, sys, tempfile
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C
from export_fab import gerbers
from sexp import parse, dump, first
from silkscreen_art import STACKUP

ROOT = C.ROOT
OUT = ROOT / "pcb/plate/keygen-plate.kicad_pcb"
PLATE_DIR = ROOT / "case/plate"
GERBERS = PLATE_DIR / "gerber"
DXF = PLATE_DIR / "dxf"
FAB_T = 1.6                    # the PCB fab's standard thickness; the case takes it too
BIT_D = 3.175                  # largest router bit the DXF dogbones fit (1/8 in.); any smaller bit works
HOLE_D = 2.2                   # M2 clearance, drilled
N = pcbnew.FromMM
V = lambda p: pcbnew.VECTOR2I(N(p[0]), N(p[1]))


def outline_with_tabs(h, tab_list):
    pts = []
    for e in h["edges"]:
        pts.append(e.a)
        for t in sorted((t for t in tab_list if t["edge"] is e), key=lambda t: t["s"]):
            s0, s1 = t["s"] - C.TAB_W / 2, t["s"] + C.TAB_W / 2
            pts += [e.at(s0), e.at(s0, C.TAB_D), e.at(s1, C.TAB_D), e.at(s1)]
    return pts


def rounded_rect(cx, cy, w, h, r):
    """An axis-aligned w x h rectangle with corner radius r, as lines and arcs."""
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    m = r * (1 - 1 / 2 ** 0.5)
    return [("line", (x0 + r, y0), (x1 - r, y0)), ("arc", (x1 - r, y0), (x1 - m, y0 + m), (x1, y0 + r)),
            ("line", (x1, y0 + r), (x1, y1 - r)), ("arc", (x1, y1 - r), (x1 - m, y1 - m), (x1 - r, y1)),
            ("line", (x1 - r, y1), (x0 + r, y1)), ("arc", (x0 + r, y1), (x0 + m, y1 - m), (x0, y1 - r)),
            ("line", (x0, y1 - r), (x0, y0 + r)), ("arc", (x0, y0 + r), (x0 + m, y0 + m), (x0 + r, y0))]


def rounded_square(cx, cy, rot, size, r):
    """[('line', a, b) | ('arc', start, mid, end)] for a square of side `size` rotated `rot` degrees."""
    a = math.radians(rot)
    w = lambda lx, ly: (cx + lx * math.cos(a) - ly * math.sin(a), cy + lx * math.sin(a) + ly * math.cos(a))
    h, k = size / 2, size / 2 - r
    out = []
    for i in range(4):
        # each side, then the corner after it; sides go round counter-clockwise in the key frame
        ang = math.pi / 2 * i
        rx = lambda lx, ly: (lx * math.cos(ang) - ly * math.sin(ang), lx * math.sin(ang) + ly * math.cos(ang))
        out.append(("line", w(*rx(h, -k)), w(*rx(h, k))))
        m = r * (1 - 1 / math.sqrt(2))
        out.append(("arc", w(*rx(h, k)), w(*rx(h - m, h - m)), w(*rx(k, h))))
    return out


def add_shape(board, item):
    s = pcbnew.PCB_SHAPE(board)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(N(0.05))
    if item[0] == "line":
        s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(item[1])); s.SetEnd(V(item[2]))
    else:
        s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(V(item[1]), V(item[2]), V(item[3]))
    board.Add(s)


def build(sides, path):
    hs = C.halves()
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(N(FAB_T))
    for side in sides:
        h = hs[side]
        pts = outline_with_tabs(h, C.tabs(h))
        for i, p in enumerate(pts):
            add_shape(board, ("line", p, pts[(i + 1) % len(pts)]))
        for k in h["keys"]:
            for item in rounded_square(k["x"], k["y"], k["rot"], C.CUTOUT, C.CUTOUT_R):
                add_shape(board, item)
        for x, y in h["enc"]:
            for item in rounded_square(x, y, 0, C.ENC_CUTOUT, C.CUTOUT_R):
                add_shape(board, item)
        x0, y0, x1, y1 = h["oled"]
        for item in rounded_rect((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0 + 2 * C.OLED_CLEAR, y1 - y0 + 2 * C.OLED_CLEAR, C.CUTOUT_R):
            add_shape(board, item)
        for ref, (x, y) in sorted(h["holes"].items()):
            fp = pcbnew.FootprintLoad("/usr/share/kicad/footprints/MountingHole.pretty", "MountingHole_2.2mm_M2")
            fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_2.2mm_M2"))
            fp.SetReference(ref); fp.Reference().SetVisible(False)
            fp.SetPosition(V((x, y))); board.Add(fp)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(path), board)
    # black mask on both faces, like the PCB (the Gerber job file carries the colour)
    tree = parse(path.read_text())
    setup = first(tree, "setup")
    setup[:] = [n for n in setup if not (isinstance(n, list) and n and n[0] == "stackup")]
    setup.insert(1, parse(STACKUP))
    path.write_text(dump(tree) + "\n")
    return path


def dogbone_rect(cx, cy, w, h, rot):
    """Closed polyline [(x, y, bulge)] of a w x h rectangle rotated `rot` degrees, each corner relieved
    by a dogbone: a half circle of radius BIT_D / 2 through the corner, so a router bit of BIT_D or less
    cuts it square."""
    a, r = math.radians(rot), BIT_D / 2
    w_ = lambda lx, ly: (cx + lx * math.cos(a) - ly * math.sin(a), cy + lx * math.sin(a) + ly * math.cos(a))
    corners = [(w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2), (-w / 2, -h / 2)]
    d = r * math.sqrt(2)                        # where the half circle meets each side
    out = []
    for i, (x, y) in enumerate(corners):
        px, py = corners[i - 1]
        nx, ny = corners[(i + 1) % 4]
        ux, uy = (x - px) / math.hypot(x - px, y - py), (y - py) / math.hypot(x - px, y - py)
        vx, vy = (nx - x) / math.hypot(nx - x, ny - y), (ny - y) / math.hypot(nx - x, ny - y)
        out.append(("arc", w_(x - ux * d, y - uy * d), w_(x, y), w_(x + vx * d, y + vy * d)))
    return out


def polyline(items):
    """[('arc', start, mid, end)] joined by straight sides -> [(x, y, bulge)] in DXF axes (y up)."""
    verts = []
    for _, s, m, e in items:
        s, m, e = (s[0], -s[1]), (m[0], -m[1]), (e[0], -e[1])
        half = math.dist(s, e) / 2
        sag = math.dist(m, ((s[0] + e[0]) / 2, (s[1] + e[1]) / 2))
        turn = (m[0] - s[0]) * (e[1] - s[1]) - (m[1] - s[1]) * (e[0] - s[0])
        verts += [(*s, -math.copysign(sag / half, turn)), (*e, 0.0)]
    return verts


def write_dxf(path, polys, circles):
    """A plain R12 DXF in mm: closed polylines {layer: [[(x, y, bulge)]]} in DXF axes and circles
    [(layer, x, y, r)] in board axes (y down), moved so the drawing's lower-left corner is at the origin."""
    xs = [v[0] for ps in polys.values() for p in ps for v in p]
    ys = [v[1] for ps in polys.values() for p in ps for v in p]
    x0, y0 = min(xs), min(ys)
    g = lambda *pairs: "".join(f"{c}\n{v}\n" for c, v in pairs)
    layers = list(polys) + sorted({c[0] for c in circles} - set(polys))
    s = g((0, "SECTION"), (2, "HEADER"), (9, "$ACADVER"), (1, "AC1009"), (9, "$INSUNITS"), (70, 4), (0, "ENDSEC"))
    s += g((0, "SECTION"), (2, "TABLES"), (0, "TABLE"), (2, "LAYER"), (70, len(layers)))
    s += "".join(g((0, "LAYER"), (2, l), (70, 0), (62, 7), (6, "CONTINUOUS")) for l in layers)
    s += g((0, "ENDTAB"), (0, "ENDSEC"), (0, "SECTION"), (2, "ENTITIES"))
    for layer, ps in polys.items():
        for p in ps:
            s += g((0, "POLYLINE"), (8, layer), (66, 1), (70, 1), (10, 0.0), (20, 0.0), (30, 0.0))
            for x, y, b in p:
                s += g((0, "VERTEX"), (8, layer), (10, f"{x - x0:.4f}"), (20, f"{y - y0:.4f}"), (30, 0.0), (42, f"{b:.6f}"))
            s += g((0, "SEQEND"), (8, layer))
    for layer, x, y, r in circles:
        s += g((0, "CIRCLE"), (8, layer), (10, f"{x - x0:.4f}"), (20, f"{-y - y0:.4f}"), (30, 0.0), (40, f"{r:.4f}"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s + g((0, "ENDSEC"), (0, "EOF")))


def plate_dxf(h, path):
    pts = outline_with_tabs(h, C.tabs(h))
    cuts = [dogbone_rect(k["x"], k["y"], C.CUTOUT, C.CUTOUT, k["rot"]) for k in h["keys"]]
    cuts += [dogbone_rect(x, y, C.ENC_CUTOUT, C.ENC_CUTOUT, 0) for x, y in h["enc"]]
    x0, y0, x1, y1 = h["oled"]
    cuts.append(dogbone_rect((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0 + 2 * C.OLED_CLEAR, y1 - y0 + 2 * C.OLED_CLEAR, 0))
    write_dxf(path, {"CUTOUTS": [polyline(c) for c in cuts], "OUTLINE": [[(x, -y, 0.0) for x, y in pts]]},
              [("DRILL", x, y, HOLE_D / 2) for x, y in h["holes"].values()])


def drc(path):
    r = subprocess.run(["kicad-cli", "pcb", "drc", "--units", "mm", "--severity-error", "-o", "/dev/stdout",
                        str(path.resolve())], capture_output=True, text=True)
    return r.stdout


def main():
    build(("left", "right"), OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")
    report = drc(OUT)
    errors = [l for l in report.splitlines() if l.startswith("Found") or l.startswith("[")]
    print("DRC: " + "; ".join(l for l in errors if l.startswith("Found")))
    sizes = {}
    for side in ("left", "right"):
        with tempfile.TemporaryDirectory() as d:
            half = build((side,), Path(d) / f"keygen-plate-{side}.kicad_pcb")
            GERBERS.mkdir(parents=True, exist_ok=True)
            files = gerbers(half, GERBERS / f"keygen-plate-{side}-gerbers.zip")
            bb = pcbnew.LoadBoard(str(half)).GetBoardEdgesBoundingBox()
            sizes[side] = (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()))
        print(f"wrote case/plate/gerber/keygen-plate-{side}-gerbers.zip ({sizes[side][0]:.1f} x {sizes[side][1]:.1f} mm)")
    hs = C.halves()
    for side in ("left", "right"):
        plate_dxf(hs[side], DXF / f"keygen-plate-{side}.dxf")
    print("wrote case/plate/dxf/")
    cut = sum(len(h["keys"]) for h in hs.values())
    w, hh = sizes["left"]
    (PLATE_DIR / "PLATE.md").write_text(f"""# Making the Keygen switch plates

The plate is clear polycarbonate, {C.PLATE_T:g} mm (the MX clips are made for it), CNC-routed from
solid sheet.

## Routing the plates from polycarbonate sheet

[`keygen-plate-left.dxf`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-left.dxf) and [`keygen-plate-right.dxf`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-right.dxf) are the plates as 1:1 DXFs in mm,
seen from above, one closed outline per contour, on three layers:

| Layer | Cut |
|---|---|
| `CUTOUTS` | inside the line (pockets through): switch, encoder and OLED cut-outs |
| `OUTLINE` | outside the line: the plate edge with its gasket tabs |
| `DRILL` | {HOLE_D:g} mm holes, drilled (smaller than a router bit) |

- Sheet: solid clear polycarbonate, {C.PLATE_T:g} mm, at least {w + 8:.0f} × {hh + 8:.0f} mm per half. A
  6 × 24 in. (152 × 610 mm) strip holds three halves, the {hh + 8:.0f} mm side across the strip.
- Route it, don't laser it: a laser browns and chars polycarbonate edges. A sharp single-flute
  (O-flute) bit for plastics, at a feed fast enough that the chips come off cold and the cut doesn't melt
  shut; hold the sheet down with tape or vacuum so the thin strips between cut-outs don't chatter.
- Each cut-out corner has a dogbone (a half circle through the corner) for a router bit of
  {BIT_D:g} mm (1/8 in.) or smaller, so the switches sit square.
- {cut} square switch cut-outs ({cut // 2} per half), 14.0 × 14.0 mm, plus a {C.ENC_CUTOUT:g} × {C.ENC_CUTOUT:g} mm encoder cut-out
  and a {C.OLED_W + 2 * C.OLED_CLEAR:g} × {C.OLED_H + 2 * C.OLED_CLEAR:g} mm OLED window per half. Five {HOLE_D:g} mm holes per half (M2).
- Leave the protective film on while cutting; peel it after deburring the edges.

## The same plate in FR-4 from a PCB fab

The Gerbers make the plate as a plain {FAB_T:g} mm FR-4 board with no copper; the case takes it too.
Place **two orders**, like the PCB:
[`keygen-plate-left-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-left-gerbers.zip) and
[`keygen-plate-right-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-right-gerbers.zip) from the build release, 5 of each.

| Setting | Value |
|---|---|
| Layers | 2 (both copper layers are empty) |
| Material | FR-4, {FAB_T:g} mm |
| Board size | one half: {w:.1f} × {hh:.1f} mm |
| Quantity | 5 left + 5 right (two orders) |
| Surface finish | HASL lead-free (no copper is exposed) |
| Soldermask / silkscreen | **black** both sides / none |
| Assembly | none |

**Things to tell the fab or check in their DFM report**
- It is a keyboard switch plate: **no copper** on either layer. Empty copper Gerbers are on purpose.
- The switch, encoder and OLED cut-outs are internal Edge.Cuts outlines with 0.5 mm corner radii, to be
  routed (milled) with a bit of 1.0 mm or less, so the corners stay at 0.5 mm.
- The outline has rectangular tabs ({C.TAB_W:g} × {C.TAB_D:g} mm) on its edges. They are part of the board.
- Five 2.2 mm non-plated holes per half (M2).

Files in each zip: {", ".join(files)}

Generated by `tools/gen_plate.py` from `pcb/keygen.kicad_pcb`.
""")
    print("wrote case/plate/PLATE.md")


if __name__ == "__main__":
    main()
