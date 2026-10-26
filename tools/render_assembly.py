#!/usr/bin/env python3
"""Render the assembly maps into assets/: every part's reference where it sits on the board, for
INSTRUCTIONS.md. The board's silkscreen is artwork and hides most references, so these drawings
are how a builder finds Q101 or H102.

assembly-{left,right}-back.png    one half seen from the back, as it lies when turned over
assembly-{left,right}-front.png   one half seen from the front (the switch side)
assembly-power.png                the power parts beside each controller, from the back, enlarged

Drawn by kicad-cli from the fabrication layers of a temporary copy of the board, with each part's
value hidden and its reference shown at one readable size.

    python3 tools/render_assembly.py
"""
import re, subprocess, tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
TMP = ROOT / "pcb/_assembly.kicad_pcb"
WIDTH = 3840                  # px, one half
REF_H, REF_W = 1.2, 0.18      # mm, reference text height and stroke
POWER = re.compile(r"^(Q|R|C|BT)\d+$|^SW[12]9[01]$")   # the parts in the enlarged view
MARGIN = 3.0                  # mm round a half, or round the power parts


def mm(v):
    return pcbnew.FromMM(v)


def prepare():
    """A copy of the board with values hidden and every reference on its side's fab layer."""
    b = pcbnew.LoadBoard(str(PCB))
    for fp in b.GetFootprints():
        fp.Value().SetVisible(False)
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


def render(svg, box, out, width, label):
    """The part of svg inside box = (x0, y0, x1, y1), in its own mm coordinates, as a white PNG
    `width` px wide with `label` above it."""
    x0, y0, x1, y1 = box
    s = re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
               f'width="{x1 - x0:.4f}mm" height="{y1 - y0:.4f}mm" viewBox="{x0:.4f} {y0:.4f} {x1 - x0:.4f} {y1 - y0:.4f}"',
               svg.read_text(), count=1)
    cropped = svg.with_name(out.stem + ".svg"); cropped.write_text(s)
    subprocess.run(["magick", "-density", "600", str(cropped), "-background", "white", "-flatten",
                    "-resize", f"{width}x", "-density", "72", "-gravity", "North", "-splice", "0x110",
                    "-font", "DejaVu-Sans-Bold", "-pointsize", "64", "-annotate", "+0+25", label,
                    "-depth", "8", "-strip", str(out)], check=True)


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
        for out in names:
            print(f"wrote {out.relative_to(ROOT)}")
    finally:
        for p in (TMP, TMP.with_suffix(".kicad_prl"), TMP.with_suffix(".kicad_pro")): p.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
