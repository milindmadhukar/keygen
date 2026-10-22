#!/usr/bin/env python3
"""The switch plate: a 1.6 mm FR-4 board with no copper, made by the PCB fab.

pcb/plate/keygen-plate.kicad_pcb     both halves (KiCad 10), black mask
case/plate/gerber/keygen-plate-left-gerbers.zip    } one order per half, like the PCB
case/plate/gerber/keygen-plate-right-gerbers.zip   }
case/plate/PLATE.md                                what to enter in the fab's order form

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
    board.GetDesignSettings().SetBoardThickness(N(C.PLATE_T))
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
    cut = sum(len(h["keys"]) for h in hs.values())
    w, hh = sizes["left"]
    (PLATE_DIR / "PLATE.md").write_text(f"""# Ordering the Keygen switch plates

The plate is a plain FR-4 board with no copper. Place **two orders**, like the PCB:
`gerber/keygen-plate-left-gerbers.zip` and `gerber/keygen-plate-right-gerbers.zip`, 5 of each.

| Setting | Value |
|---|---|
| Layers | 2 (both copper layers are empty) |
| Material | FR-4, 1.6 mm |
| Board size | one half: {w:.1f} × {hh:.1f} mm |
| Quantity | 5 left + 5 right (two orders) |
| Surface finish | HASL lead-free (no copper is exposed) |
| Soldermask / silkscreen | **black** both sides / none |
| Assembly | none |

**Things to tell the fab or check in their DFM report**
- It is a keyboard switch plate: **no copper** on either layer. Empty copper Gerbers are on purpose.
- {cut} square switch cut-outs ({cut // 2} per half), 14.0 × 14.0 mm with 0.5 mm corner radii, plus
  a 13 × 13 mm encoder cut-out and a {C.OLED_W + 2 * C.OLED_CLEAR:g} × {C.OLED_H + 2 * C.OLED_CLEAR:g} mm OLED window per half. All are internal Edge.Cuts outlines to be
  routed (milled) with a bit of 1.0 mm or less, so the corners stay at 0.5 mm.
- The outline has rectangular tabs ({C.TAB_W:g} × {C.TAB_D:g} mm) on its edges. They are part of the board.
- Five 2.2 mm non-plated holes per half (M2).

Generated by `tools/gen_plate.py` from `pcb/keygen.kicad_pcb`.
Files in each zip: {", ".join(files)}
""")
    print("wrote case/plate/PLATE.md")


if __name__ == "__main__":
    main()
