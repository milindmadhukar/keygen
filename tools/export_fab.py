#!/usr/bin/env python3
"""Manufacturing files for a bare-board order (you solder everything yourself).

fab/keygen-gerbers.zip         both halves in one file (two separate board outlines)
fab/keygen-left-gerbers.zip    left half only  } fallback if the fab won't take two outlines
fab/keygen-right-gerbers.zip   right half only } in one design
fab/ORDER.md                   what to enter in the fab's order form

Each zip holds Gerbers (copper, soldermask, silkscreen, outline) and Excellon drill files.
"""
import re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from sexp import parse, dump, first, find

PCB = ROOT / "pcb/keygen.kicad_pcb"
OUT = ROOT / "fab"
LAYERS = "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts"
SPLIT_X = 210.0          # sheet x (mm) between the two halves


def gerbers(board, out_zip):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask",
                        "--no-x2", "-o", str(d) + "/", str(board)], check=True, capture_output=True)
        subprocess.run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th",
                        "--generate-map", "--map-format", "gerberx2", "-o", str(d) + "/", str(board)],
                       check=True, capture_output=True)
        files = sorted(p for p in d.iterdir() if p.is_file())
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for p in files:
                z.write(p, p.name)
        return [p.name for p in files]


def x_of(node):
    """A representative x (mm) for a top-level board item, or None if it has none."""
    for key in ("at", "start", "center"):
        n = first(node, key)
        if n: return float(n[1])
    pts = first(node, "pts") or first(first(node, "polygon") or [], "pts") if node[0] == "zone" else first(node, "pts")
    if pts:
        xy = find(pts, "xy")
        if xy: return sum(float(p[1]) for p in xy) / len(xy)
    return None


def one_half(side, dest):
    """Copy of the board with the other half's items removed (outline, parts, copper, zones)."""
    tree = parse(PCB.read_text())
    keep = []
    for n in tree:
        if isinstance(n, list) and n and n[0] in ("footprint", "segment", "arc", "via", "zone", "gr_line",
                                                   "gr_arc", "gr_rect", "gr_poly", "gr_circle", "gr_text"):
            x = x_of(n)
            if x is not None and ((x < SPLIT_X) != (side == "left")):
                continue
        keep.append(n)
    tree[:] = keep
    dest.write_text(dump(tree) + "\n")
    shutil.copy(PCB.with_suffix(".kicad_pro"), dest.with_suffix(".kicad_pro"))


def led_windows(board):
    """Reverse-mount LEDs on one half: each sits in its own Edge.Cuts light cut-out."""
    import pcbnew
    return sum(1 for fp in pcbnew.LoadBoard(str(board)).GetFootprints() if re.match(r"LED1\d\d$", fp.GetReference()))


def outline_size(board):
    import pcbnew
    b = pcbnew.LoadBoard(str(board))
    bb = b.GetBoardEdgesBoundingBox()
    return pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())


def main():
    OUT.mkdir(exist_ok=True)
    sizes = {}
    files = gerbers(PCB, OUT / "keygen-gerbers.zip")
    sizes["both"] = outline_size(PCB)
    for side in ("left", "right"):
        with tempfile.TemporaryDirectory(dir=ROOT / "pcb") as d:
            half = Path(d) / f"keygen-{side}.kicad_pcb"
            one_half(side, half)
            gerbers(half, OUT / f"keygen-{side}-gerbers.zip")
            sizes[side] = outline_size(half)
    w, h = sizes["left"]
    leds = led_windows(PCB)
    W, H = sizes["both"]
    (OUT / "ORDER.md").write_text(f"""# Ordering the Keygen PCBs (bare boards, self-assembly)

Place **two orders**: [`keygen-left-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-left-gerbers.zip) and
[`keygen-right-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-right-gerbers.zip), 5 of each, from the build release.
Per half came out cheaper at Lion Circuits than the combined file (checked 2026-10-20).
[`keygen-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-gerbers.zip) (both halves in one design) is kept for fabs that price it better.

| Setting | Value |
|---|---|
| Layers | 2 |
| Material | FR-4, 1.6 mm |
| Copper | 1 oz (35 µm) |
| Board size | both halves: {W:.1f} × {H:.1f} mm · one half: {w:.1f} × {h:.1f} mm |
| Quantity | 5 left + 5 right (two orders) |
| Surface finish | HASL lead-free (cheapest; fine for hand soldering) |
| Soldermask / silkscreen | **black / white** (the silkscreen artwork is drawn for it; set in the board stackup) |
| Min track / clearance | 0.15 mm / 0.2 mm (6/8 mil) |
| Min hole | 0.3 mm (vias); no blind/buried vias |
| Assembly | none (bare boards) |
| Stencil | not needed |

**Things to tell the fab or check in their DFM report**
- Each half has {leds} small internal rectangular cut-outs (reverse-mount LED windows, about
  3.5 × 3.2 mm, with corner reliefs). They are on the Edge.Cuts layer and must be routed (milled).
- LED pads sit about 0.25 mm from those cut-outs (copper-to-edge 0.2 mm).
- The USB-C end of each controller overhangs the board edge by 1 mm on purpose (no copper there).

Generated by `tools/export_fab.py` from `pcb/keygen.kicad_pcb`.
Files in each zip, named keygen-left-… and keygen-right-… in the half zips: {", ".join(files)}
""")
    for z in sorted(OUT.glob("*.zip")):
        print(f"{z.name}: {z.stat().st_size // 1024} KB")
    print(f"sizes: both {W:.1f}x{H:.1f} mm, half {w:.1f}x{h:.1f} mm")


if __name__ == "__main__":
    main()
