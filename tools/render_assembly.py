#!/usr/bin/env python3
"""Render the assembly maps into assets/: every part's reference where it sits on the board, for
INSTRUCTIONS.md. The board's silkscreen is artwork and hides most references, so these drawings
are how a builder finds Q101 or H102.

assembly-{left,right}-back.png    one half seen from the back, as it lies when turned over
assembly-{left,right}-front.png   one half seen from the front (the switch side)
assembly-power.png                the power parts beside each controller, from the back, enlarged
assembly-overview.png             the left half from the front and the back, each part coloured by
                                  type, so a builder sees at a glance what goes on which side
assembly-part-<name>.png          one part of each type close up, with its orientation marks and
                                  pad numbers, and a line saying how it goes in

Drawn by kicad-cli from the fabrication layers of a temporary copy of the board, with each part's
value hidden and its reference shown at one readable size.

    python3 tools/render_assembly.py
"""
import math, re, subprocess, sys, tempfile
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
TMP = ROOT / "pcb/_assembly.kicad_pcb"
WIDTH = 3840                  # px, one half
REF_H, REF_W = 1.2, 0.18      # mm, reference text height and stroke
POWER = re.compile(r"^(Q|R|C|BT)\d+$|^SW[12]9[01]$")   # the parts in the enlarged view
MARGIN = 3.0                  # mm round a half, or round the power parts


def mm(v):
    return pcbnew.FromMM(v)


# name, reference, side seen from, title, caption (the close-ups, in soldering order)
PARTS = [
    ("mosfet", "Q101", "back", "MOSFET (SOT-23), from the back",
     "One leg on one side, two on the other: it fits its pads one way only."),
    ("resistor", "R101", "back", "Resistor or capacitor (1206), from the back",
     "Either way round. Tin one pad, place it, reheat, then solder the other."),
    ("slide-switch", "SW190", "back", "Power switch (MSK12C02), from the back",
     "Its lever points out over the top edge. Pins 1-3 and the four MP tabs all get solder."),
    ("battery", "BT101", "back", "Battery connector (JST-PH), from the back",
     "Side entry: the plug goes in flat along the board. The triangle marks pad 1, battery +."),
    ("reset", "SW191", "back", "Reset button, from the back",
     "Through-hole: place it on the back, solder its four legs on the front."),
    ("led", "LED101", "back", "LED (SK6812MINI-E), from the back",
     "Lit side down into the cut-out. Its cut corner goes on pad 1, GND."),
    ("diode", "D101", "back", "Diode (1N4148), from the back",
     "Body on the back, band towards the square pad marked K."),
    ("socket", "SW101", "back", "Hotswap socket, from the back",
     "It fits its two pads one way. Plenty of solder: it takes every switch insertion."),
    ("encoder", "ENC101", "front", "Encoder (EC11), from the front",
     "On the front. Solder its five pins and both mounting tabs on the back."),
    ("oled", "J101", "front", "OLED header, from the front",
     "The square pad is pin 1, GND: the module's pins must read GND, VCC, SCL, SDA."),
]
PART_W = 900                  # px, each close-up
PART_SPAN = 16.0              # mm, the square each close-up shows (more for the larger parts)

# the overview's part groups: name, colour, which side they sit on, references
GROUPS = [
    ("Switches (from the front)", "#4C78A8", "front", re.compile(r"^SW\d+$"), lambda r: int(r[2:]) % 100 < 90),
    ("Encoder and OLED", "#F58518", "front", re.compile(r"^(ENC|J)\d+$"), None),
    ("Hotswap sockets", "#4C78A8", "back", re.compile(r"^SW\d+$"), lambda r: int(r[2:]) % 100 < 90),
    ("LEDs", "#E45756", "back", re.compile(r"^LED\d+$"), None),
    ("Diodes", "#54A24B", "back", re.compile(r"^D\d+$"), None),
    ("Power parts: MOSFETs, resistors, capacitors", "#B279A2", "back", re.compile(r"^(Q|R|C)\d+$"), None),
    ("Battery connector, power switch, reset", "#9D755D", "back", re.compile(r"^(BT\d+|SW[12]9[01])$"), None),
    ("Controller (socketed)", "#72B7B2", "back", re.compile(r"^U\d+$"), None),
]


def prepare(refs=True):
    """A copy of the board with values hidden and every reference on its side's fab layer (or no
    references at all, for the close-ups)."""
    b = pcbnew.LoadBoard(str(PCB))
    for fp in b.GetFootprints():
        fp.Value().SetVisible(False)
        if not refs:
            fp.Reference().SetVisible(False)
            for t in fp.GraphicalItems():
                if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() == "${REFERENCE}": t.SetText("")
            continue
        fab = pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab
        refs = [t for t in fp.GraphicalItems()
                if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() == "${REFERENCE}" and t.GetLayer() == fab]
        if not refs:
            ref = fp.Reference(); ref.SetLayer(fab); ref.SetVisible(True); refs = [ref]
        else:
            fp.Reference().SetVisible(False)
        for t in refs:
            t.SetTextSize(pcbnew.VECTOR2I(mm(REF_H), mm(REF_H))); t.SetTextThickness(mm(REF_W))
            if fp.GetReference().startswith("H"):    # a mounting hole: the reference above it, not on it
                t.SetPosition(fp.GetPosition() + pcbnew.VECTOR2I(0, -mm(2.8)))
    b.Save(str(TMP))
    return b


def export(side, out):
    layers = "Edge.Cuts,B.Fab" if side == "back" else "Edge.Cuts,F.Fab"
    subprocess.run(["kicad-cli", "pcb", "export", "svg", "--mode-single", "-o", str(out), "-l", layers,
                    "--sketch-pads-on-fab-layers", "--exclude-drawing-sheet", "--page-size-mode", "2",
                    "--black-and-white", *(["--mirror"] if side == "back" else []), str(TMP)],
                   check=True, capture_output=True)


def render(svg, box, out, width, label, caption=None):
    """The part of svg inside box = (x0, y0, x1, y1), in its own mm coordinates, as a white PNG
    `width` px wide with `label` above it and `caption`, if any, below."""
    x0, y0, x1, y1 = box
    s = re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
               f'width="{x1 - x0:.4f}mm" height="{y1 - y0:.4f}mm" viewBox="{x0:.4f} {y0:.4f} {x1 - x0:.4f} {y1 - y0:.4f}"',
               svg.read_text(), count=1)
    cropped = svg.with_name(out.stem + ".svg"); cropped.write_text(s)
    subprocess.run(["magick", "-density", "600", str(cropped), "-background", "white", "-flatten",
                    "-resize", f"{width}x", "-density", "72", "-gravity", "North", "-splice", "0x110",
                    "-font", "DejaVu-Sans-Bold", "-pointsize", "64" if width > 2000 else "34", "-annotate",
                    "+0+25", label,
                    *(["-gravity", "South", "-splice", "0x120", "-font", "DejaVu-Sans", "-pointsize", "28",
                       "-size", f"{width - 60}x", "caption:" + caption, "-gravity", "South", "-geometry", "+0+20",
                       "-composite"] if caption else []),
                    "-depth", "8", "-strip", str(out)], check=True)


def side_of(fp):
    return "back" if fp.IsFlipped() else "front"


def outline_of(fp):
    """A footprint's outline for the overview, as [(x, y)] in mm: its courtyard, or for a switch
    on the back only its hotswap socket (the pads and the two locating holes)."""
    ref = fp.GetReference()
    if ref.startswith("SW") and int(ref[2:]) % 100 < 90 and fp.IsFlipped():
        pads = [p for p in fp.Pads() if p.GetNumber() in ("1", "2") or abs(pcbnew.ToMM(p.GetDrillSize().x) - 3.0) < 0.05]
        bb = pads[0].GetBoundingBox()
        for q in pads[1:]: bb.Merge(q.GetBoundingBox())
        x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    if cy.OutlineCount():
        o = cy.Outline(0)
        return [(pcbnew.ToMM(o.CPoint(i).x), pcbnew.ToMM(o.CPoint(i).y)) for i in range(o.PointCount())]
    bb = fp.GetBoundingBox(False)
    x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def overview(b, tmp, out):
    """The left half from the front and from the back (turned over), each part filled in its
    group's colour, with a legend: which part goes on which side."""
    polys = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(polys, False)
    mid = pcbnew.ToMM(b.GetBoardEdgesBoundingBox().GetCenter().x)
    i = next(i for i in range(polys.OutlineCount())
             if sum(pcbnew.ToMM(polys.Outline(i).CPoint(k).x) for k in range(polys.Outline(i).PointCount()))
             / polys.Outline(i).PointCount() < mid)
    pts = lambda c: [(pcbnew.ToMM(c.CPoint(k).x), pcbnew.ToMM(c.CPoint(k).y)) for k in range(c.PointCount())]
    edge, holes = pts(polys.Outline(i)), [pts(polys.Hole(i, j)) for j in range(polys.HoleCount(i))]
    x0, x1 = min(p[0] for p in edge), max(p[0] for p in edge)
    y0, y1 = min(p[1] for p in edge), max(p[1] for p in edge)
    w, h, gap, top = x1 - x0, y1 - y0, 14.0, 12.0
    fps = [fp for fp in b.GetFootprints() if pcbnew.ToMM(fp.GetPosition().x) < mid]

    def path(ps, dx, mirror):
        q = [((x1 - x + x0) if mirror else x) - x0 + dx for x, _ in ps]
        return "M" + " L".join(f"{a:.3f},{y - y0 + top:.3f}" for a, (_, y) in zip(q, ps)) + " Z"

    svg = []
    for k, (side, mirror) in enumerate((("front", False), ("back", True))):
        dx = k * (w + gap)
        title = "FRONT (switch side)" if side == "front" else "BACK (board turned over)"
        svg.append(f'<text x="{dx + w / 2:.1f}" y="7" font-size="5" font-weight="bold" text-anchor="middle">{title}</text>')
        d = path(edge, dx, mirror) + " " + " ".join(path(hh, dx, mirror) for hh in holes)
        svg.append(f'<path d="{d}" fill="#f4f4f4" fill-rule="evenodd" stroke="#222" stroke-width="0.4"/>')
        for name, colour, gside, pat, keep in GROUPS:
            if gside != side: continue
            for fp in fps:
                ref = fp.GetReference()
                if not pat.match(ref) or (keep and not keep(ref)): continue
                if side == "front" and ref.startswith("SW"):      # a switch: its 14 mm plate cut-out
                    c = fp.GetPosition(); cx, cy = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
                    rot = fp.GetOrientationDegrees()
                    ca, sa = math.cos(math.radians(-rot)), math.sin(math.radians(-rot))
                    poly = [(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in ((-7, -7), (7, -7), (7, 7), (-7, 7))]
                elif ref.startswith("J"):                         # the OLED: its module, not just the header
                    ox0, oy0, ox1, oy1 = C.halves()["left"]["oled"]
                    poly = [(ox0, oy0), (ox1, oy0), (ox1, oy1), (ox0, oy1)]
                elif side == "front" or side_of(fp) == side:
                    poly = outline_of(fp)
                else:
                    continue
                svg.append(f'<path d="{path(poly, dx, mirror)}" fill="{colour}" fill-opacity="0.85" stroke="#222" stroke-width="0.15"/>')
        svg.append(f'<text x="{dx + w / 2:.1f}" y="{top - 1.5:.1f}" font-size="3" text-anchor="middle" fill="#555">top edge: USB-C and power switch</text>')
    ly = top + h + 9
    seen = []
    for name, colour, _, _, _ in GROUPS:
        if name in seen or name == "Hotswap sockets": continue
        seen.append(name)
    seen.insert(1, "Hotswap sockets")
    colours = {g[0]: g[1] for g in GROUPS}
    for n, name in enumerate(seen):
        cx, cy = (n % 2) * (w + gap), ly + (n // 2) * 7
        svg.append(f'<rect x="{cx:.1f}" y="{cy - 3.6:.1f}" width="5" height="4.5" fill="{colours[name]}" stroke="#222" stroke-width="0.15"/>')
        svg.append(f'<text x="{cx + 7:.1f}" y="{cy:.1f}" font-size="4">{name}</text>')
    W, H = 2 * w + gap, ly + ((len(seen) + 1) // 2) * 7 + 2
    f = tmp / "overview.svg"
    f.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" viewBox="0 0 {W:.2f} {H:.2f}" '
                 f'font-family="DejaVu Sans">' + "".join(svg) + "</svg>")
    subprocess.run(["magick", "-density", "500", str(f), "-background", "white", "-flatten", "-resize", f"{WIDTH}x",
                    "-bordercolor", "white", "-border", "40", "-depth", "8", "-strip", str(out)], check=True)


def main():
    b = prepare()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            svgs = {}
            for side in ("back", "front"):
                svgs[side] = tmp / f"{side}.svg"; export(side, svgs[side])
            # each SVG's page is the board's outline box, mirrored left to right on the back
            edge = b.GetBoardEdgesBoundingBox()
            bx0, by0, bx1 = (pcbnew.ToMM(v) for v in (edge.GetLeft(), edge.GetTop(), edge.GetRight()))
            vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svgs["back"].read_text()).group(1).split()]
            pad = (vb[2] - (bx1 - bx0)) / 2

            def page(side, x0, y0, x1, y1):
                """A board-coordinate box (mm) on the side's SVG page."""
                if side == "back":
                    x0, x1 = bx1 - x1 + bx0, bx1 - x0 + bx0
                return (x0 - bx0 + pad, y0 - by0 + pad, x1 - bx0 + pad, y1 - by0 + pad)

            def bounds(rects):
                return (min(pcbnew.ToMM(r.GetLeft()) for r in rects) - MARGIN,
                        min(pcbnew.ToMM(r.GetTop()) for r in rects) - MARGIN,
                        max(pcbnew.ToMM(r.GetRight()) for r in rects) + MARGIN,
                        max(pcbnew.ToMM(r.GetBottom()) for r in rects) + MARGIN)

            mid = pcbnew.ToMM(edge.GetCenter().x)
            edges = [d.GetBoundingBox() for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
            half = {"left": lambda r: pcbnew.ToMM(r.GetCenter().x) < mid,
                    "right": lambda r: pcbnew.ToMM(r.GetCenter().x) >= mid}
            names = []
            for name, inside in half.items():
                box = bounds([r for r in edges if inside(r)])
                for side in ("back", "front"):
                    out = ROOT / f"assets/assembly-{name}-{side}.png"
                    render(svgs[side], page(side, *box), out, WIDTH, f"{name.upper()} HALF, {side}")
                    names.append(out)

            power = []
            for name, digit in (("left", "1"), ("right", "2")):
                rects = [fp.GetBoundingBox(False) for fp in b.GetFootprints()
                         if POWER.match(fp.GetReference()) and re.search(r"\d", fp.GetReference()).group() == digit]
                out = tmp / f"power-{name}.png"
                render(svgs["back"], page("back", *bounds(rects)), out, WIDTH // 2 - 40, f"{name.upper()} HALF, back")
                power.append(out)
            out = ROOT / "assets/assembly-power.png"
            subprocess.run(["magick", *map(str, power), "-bordercolor", "white", "-border", "20", "+append",
                            "-depth", "8", "-strip", str(out)], check=True)
            names.append(out)

            out = ROOT / "assets/assembly-overview.png"
            overview(b, tmp, out); names.append(out)

            c = prepare(refs=False)                      # the close-ups: pads and marks, no references
            for side in ("back", "front"):
                svgs[side] = tmp / f"{side}-bare.svg"; export(side, svgs[side])
            for name, ref, side, title, caption in PARTS:
                r = c.FindFootprintByReference(ref).GetBoundingBox(False)
                cx, cy = pcbnew.ToMM(r.GetCenter().x), pcbnew.ToMM(r.GetCenter().y)
                span = max(PART_SPAN, pcbnew.ToMM(max(r.GetWidth(), r.GetHeight())) + 4.0)
                out = ROOT / f"assets/assembly-part-{name}.png"
                render(svgs[side], page(side, cx - span / 2, cy - span / 2, cx + span / 2, cy + span / 2), out,
                       PART_W, title, caption)
                names.append(out)
        for out in names:
            print(f"wrote {out.relative_to(ROOT)}")
    finally:
        for p in (TMP, TMP.with_suffix(".kicad_prl"), TMP.with_suffix(".kicad_pro")): p.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
