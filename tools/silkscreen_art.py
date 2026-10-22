#!/usr/bin/env python3
"""Black soldermask, white silkscreen, and the Keygen artwork.

The board is named after Martin Garrix's track "Keygen" (STMPD RCRDS). Its cover is a fake
keygen.exe window: a "MARTIN GARRIX" title bar, an outlined KEYGEN logo in a starfield beside a
crescent moon, a serial-number field, and a GENERATE button between two STMPD emblems. This
script draws those pieces on the free board between each controller and its thumb cluster:

  top, left half       the window: title bar, KEYGEN logo, stars, serial, stacked frames
  top, right half      crescent moon, STMPD emblem and stars beside the encoder
  bottom, both halves  [emblem] GENERATE [emblem] under the reset button (double-tap: bootloader)
  bottom, left half    credits
  bottom, right half   a small keygen.exe window with the flashing hint
  everywhere else      stars, on both faces, wherever the board is free

It also writes a board stackup with black mask, white silkscreen and HASL, which is what
kicad-cli's renders and the Gerber job file pick up. Before drawing, it moves any footprint label
(a reference, a diode's K) that crosses the edge, a pad or other silkscreen to the nearest clear spot.

    python3 tools/silkscreen_art.py [board.kicad_pcb]

Rerunnable: the previous artwork (the "keygen-art" group) is removed first. Everything is
clipped 0.25 mm clear of pads and holes, 0.2 mm clear of the footprints' own silkscreen and
0.5 mm inside the board edge, and the script reports how much it had to clip.
"""
import math, random, re, sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
from sexp import parse, dump, first, find

ROOT = Path(__file__).resolve().parent.parent
PCB = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "pcb/keygen.kicad_pcb"
GROUP = "keygen-art"
SERIAL = "5233-5131-4927-406"            # the serial on the cover
PAD_CLEAR, EDGE_CLEAR = 0.25, 0.5         # mm
SKY = {"F": (0.05, 7), "B": (0.035, 5)}    # board-wide stars per mm^2, and how many nebulae
N = pcbnew.FromMM


# ---------------------------------------------------------------- polygon helpers (mm in, nm out)

def poly(pts):
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in pts: ch.Append(N(x), N(y))
    ch.SetClosed(True)
    ps = pcbnew.SHAPE_POLY_SET(); ps.AddOutline(ch)
    return ps

def empty(): return pcbnew.SHAPE_POLY_SET()

def copy(ps): return pcbnew.SHAPE_POLY_SET(ps)

def union(parts):
    out = empty()
    for p in parts: out.BooleanAdd(p)
    return out

def minus(a, b):
    a = copy(a); a.BooleanSubtract(b); return a

def grow(ps, d):
    ps = copy(ps); ps.Inflate(N(d), pcbnew.CORNER_STRATEGY_CHAMFER_ACUTE_CORNERS, N(0.005)); return ps

def area(ps): return ps.Area() / 1e12 if ps.OutlineCount() else 0.0      # mm^2

def hits(a, b):
    a = copy(a); a.BooleanIntersection(b); return area(a) > 1e-6

def circle(cx, cy, r, n=48):
    return poly([(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)])

def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]
    return half(pts) + half(pts[::-1])

def octagon(x, y, w):
    """Regular octagon with flats w apart: strokes made of these have 45-degree chamfered corners."""
    r = w / 2 / math.cos(math.pi / 8)
    return [(x + r * math.cos(math.pi / 8 + i * math.pi / 4), y + r * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]

def strokes(lines, w):
    """Union of polylines drawn with an octagonal pen of width w."""
    parts = []
    for line in lines:
        if len(line) == 1: line = [line[0], line[0]]
        for a, b in zip(line, line[1:]):
            parts.append(poly(hull(octagon(*a, w) + octagon(*b, w))))
    return union(parts)

def rect(x0, y0, x1, y1, w):
    return strokes([[(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]], w)

def ring(ps, w):
    """Outline of ps as a line of width w centred on its edge."""
    return minus(grow(ps, w / 2), grow(ps, -w / 2))


# ---------------------------------------------------------------- a squared stroke font, 6 units tall

GLYPHS = {
    "A": (4, [[(0, 6), (0, 1), (1, 0), (3, 0), (4, 1), (4, 6)], [(0, 3.5), (4, 3.5)]]),
    "B": (4, [[(0, 3), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3)]]),
    "C": (4, [[(4, 0), (1, 0), (0, 1), (0, 5), (1, 6), (4, 6)]]),
    "D": (4, [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 1), (3, 0), (0, 0)]]),
    "E": (4, [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]]),
    "F": (4, [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]]),
    "G": (4, [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3), (2, 3)]]),
    "H": (4, [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]]),
    "I": (0, [[(0, 0), (0, 6)]]),
    "K": (4, [[(0, 0), (0, 6)], [(4, 0), (1, 3), (0, 3)], [(1, 3), (4, 6)]]),
    "L": (3.5, [[(0, 0), (0, 6), (3.5, 6)]]),
    "M": (5, [[(0, 6), (0, 0), (2.5, 3), (5, 0), (5, 6)]]),
    "N": (4, [[(0, 6), (0, 0), (4, 6), (4, 0)]]),
    "O": (4, [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]]),
    "P": (4, [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]]),
    "R": (4, [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]]),
    "S": (4, [[(4, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]]),
    "T": (4, [[(0, 0), (4, 0)], [(2, 0), (2, 6)]]),
    "U": (4, [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]]),
    "V": (4, [[(0, 0), (2, 6), (4, 0)]]),
    "W": (5, [[(0, 0), (1, 6), (2.5, 3), (4, 6), (5, 0)]]),
    "X": (4, [[(0, 0), (4, 6)], [(4, 0), (0, 6)]]),
    "Y": (4, [[(0, 0), (0, 2), (1, 3), (3, 3), (4, 2), (4, 0)], [(2, 3), (2, 6)]]),
    "0": (4, [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)], [(3, 1.5), (1, 4.5)]]),
    "1": (2, [[(0, 1), (1.5, 0), (1.5, 6)]]),
    "2": (4, [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 6), (4, 6)]]),
    "3": (4, [[(0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3)], [(3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]]),
    "4": (4, [[(3, 6), (3, 0), (0, 4), (4, 4)]]),
    "5": (4, [[(4, 0), (0, 0), (0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]]),
    "6": (4, [[(4, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]]),
    "7": (4, [[(0, 0), (4, 0), (4, 1), (1.5, 6)]]),
    "8": (4, [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6),
               (3, 6), (4, 5), (4, 4), (3, 3)]]),
    "9": (4, [[(4, 3), (1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (0, 6)]]),
    "-": (2.5, [[(0, 3), (2.5, 3)]]),
    ":": (0, [[(0, 2)], [(0, 5)]]),
    ".": (0, [[(0, 6)]]),
    "/": (3, [[(0, 6), (3, 0)]]),
    "=": (3, [[(0, 2), (3, 2)], [(0, 4), (3, 4)]]),
    " ": (2, []),
}

def text_lines(s, h, sx=1.0, gap=1.6):
    """Skeleton polylines for s, cap height h (mm), starting at x=0, top at y=0. Returns (lines, width)."""
    u, x, out = h / 6, 0.0, []
    for ch in s:
        w, lines = GLYPHS[ch]
        out += [[(x + px * u * sx, py * u) for px, py in line] for line in lines]
        x += (w * sx + gap) * u
    return out, x - gap * u

def text(s, cx, cy, h, w=None, sx=1.0, gap=1.6):
    """Text centred on (cx, cy); w is the pen width (default h/6)."""
    lines, width = text_lines(s, h, sx, gap)
    return strokes([[(cx - width / 2 + x, cy - h / 2 + y) for x, y in l] for l in lines], w or h / 6)

def text_width(s, h, sx=1.0, gap=1.6): return text_lines(s, h, sx, gap)[1]


# ---------------------------------------------------------------- the pieces, in local mm, (0, 0) centred

def logo(h, w, line, sx=1.15, gap=1.2):
    """Outlined KEYGEN, h tall: letters drawn with a fat pen of width w, then only their outline kept.
    Returns (outline, filled letters)."""
    fat = text("KEYGEN", 0, 0, h - w, w=w, sx=sx, gap=gap + 6 * w / (h - w))
    return ring(fat, line), fat

# The STMPD RCRDS emblem, a geometric lion's face in a hexagon: the label's own vector (the
# favicon at stmpdrcrds.com, a 720-unit viewBox). The first subpath is the hexagon, every other
# one a cell cut out of it, so the lines are what is left. The emblem is the label's mark; it is
# here as a fan's nod on a one-off board.
STMPD_PATH = (
    "M360.11,14.89L60.39,187.38l-.39.22,45.44,350.72,254.67,166.78,254.45-166.78,45.44-350.72L360"
    ".11,14.89ZM71.48,201.99l105.41,91.88,20.19,127.28-83.88,102.79-41.72-321.95ZM211,301.19l9.32"
    ",32.25-25.75,11.1-7.51-47.33,23.94,3.98ZM189.75,287.99l58.49-79.67,32.58,17.95,15.52,79.44-1"
    "06.59-17.73ZM196.11,354.27l29.75-12.82,86.73,45.83,6.19,30.47h-112.59l-10.07-63.48ZM247.2,46"
    "8.67l-120.88,54.26,76.35-93.57,44.53,39.31ZM119.79,536.32l134.13-60.21,40.49,70.47-66.31,60."
    "68-108.31-70.94ZM236.33,612.65l62.21-56.93,51.66,131.51-113.87-74.58ZM355.34,674.24l-46.67-1"
    "18.81,46.67,16.27v102.54ZM355.34,498.39l-57.53-25.4,13.09,34.41.24.63,8.91-3.39-5.21-13.7,40"
    ".5,17.88v13.65l-46.42,5.4-.67.08,1.1,9.47,45.99-5.34v29.54l-51.72-18.03-43.93-76.54-.02-.03-"
    "44.97-39.73h115.29l-8.7-45.88-.05-.33-91.16-48.16-8.66-29.97,86.95,14.46,1.01.17-6.85-33.35h"
    "52.8v214.19ZM355.34,274.67h-54.75l-8.68-42.29,63.44,34.95v7.33ZM355.34,256.45l-109.84-60.53-"
    "64.96,88.48-107.23-93.46,122.33-70.4,159.71,92.09v43.82ZM355.34,201.63l-150.15-86.58L355.34,"
    "28.63v172.99ZM364.87,28.64l149.98,86.38-149.98,86.49V28.64ZM364.87,212.51l159.54-91.99,122.2"
    "9,70.43-82.43,71.85,26.22-56.53-38.81-53.2-62.39,34.72,62.69,85.74-12.51,10.9-64.96-88.49-10"
    "9.63,60.52v-43.93ZM554.87,261.34l-51.52-70.49,45.6-25.37,30.43,41.73-24.51,54.13ZM513.81,417"
    ".74h-112.2l5.99-30.46,86.54-45.84,29.75,12.75-10.08,63.56ZM517.33,429.37l76.33,93.55-120.67-"
    "54.25,44.34-39.29ZM498.5,303.17l-8.58,29.73-79.95,42.34,11.57-58.82,76.96-13.25ZM423.51,306."
    "4l15.76-80.14,32.51-17.95,58.51,79.7-106.77,18.38ZM499.68,333.44l9.26-32.07,24-4.13-7.5,47.2"
    "4-25.76-11.04ZM364.87,267.33l63.49-35.05-8.33,42.39h-55.16v-7.34ZM364.87,532.07l45.31,5.26.6"
    "7.08,1.1-9.47-47.08-5.47v-13.66l40.28-17.86-5.21,13.68,8.91,3.39,13.16-34.58.18-.47-57.33,25"
    ".4v-214.18h53.28l-27.97,142.27-.16.8h115.3l-44.67,39.59-.03.02-44.3,76.71-51.45,18v-29.52ZM3"
    "64.87,571.7l46.47-16.26-46.47,118.71v-102.46ZM369.99,687.23l51.47-131.51,62.25,56.97-113.72,"
    "74.54ZM491.94,607.29l-66.34-60.71,40.68-70.48,133.94,60.22-108.28,70.98ZM606.81,523.95l-83.8"
    "8-102.8,20.2-127.28,105.4-91.87-41.72,321.95Z"
)

def svg_subpaths(d):
    """Polygons of an SVG path made only of M/L/H/V/Z commands (absolute or relative)."""
    toks = re.findall(r"[MLHVZmlhvz]|-?(?:\d+\.?\d*|\.\d+)", d)
    paths, cur, x, y, cmd, i = [], [], 0.0, 0.0, None, 0
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t; i += 1
            if cmd in "Zz":
                paths.append(cur); x, y = cur[0]; cur = []
            continue
        if cmd in "MLml":
            dx, dy = float(toks[i]), float(toks[i + 1]); i += 2
            x, y = (x + dx, y + dy) if cmd.islower() else (dx, dy)
            if cmd in "Mm": cur = [(x, y)]; cmd = "l" if cmd == "m" else "L"
            else: cur.append((x, y))
        else:
            v = float(toks[i]); i += 1
            if cmd in "Hh": x = x + v if cmd == "h" else v
            else: y = y + v if cmd == "v" else v
            cur.append((x, y))
    return paths

def stmpd(h, w):
    """The STMPD emblem, h tall, with its lines thickened to at least w where the original's are thinner."""
    outer, *cells = svg_subpaths("".join(STMPD_PATH))
    k = h / 690.2                                    # hexagon height in SVG units
    tf = lambda pts: [((px - 360) * k, (py - 360) * k) for px, py in pts]
    holes = union([poly(tf(c)) for c in cells])
    thicken = max(0.0, (w - 9.6 * k) / 2)            # the original lines are about 9.6 units wide
    return minus(poly(tf(outer)), grow(holes, -thicken) if thicken else holes)

def moon(r, craters):
    """Crescent lit on the left, with a few craters punched out."""
    m = minus(circle(0, 0, r), circle(r * 0.42, -r * 0.18, r * 0.86))
    for x, y, cr in craters: m = minus(m, circle(x * r, y * r, cr * r, 24))
    return m

def window(w, h, title, line=0.25, bar=3.0, stacked=2, offset=1.3):
    """Frame, title bar with [X], and `stacked` frames peeking out behind to the lower right."""
    x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    parts = [rect(x0, y0, x1, y1, line)]
    xb = x1 - 0.8 - bar + 0.6                      # [X] box
    parts.append(rect(x0 + 0.8, y0 + 0.8, xb - 0.7, y0 + 0.8 + bar - 0.6, line))
    parts.append(rect(xb, y0 + 0.8, x1 - 0.8, y0 + 0.8 + bar - 0.6, line))
    s, xc, yc = bar - 0.6 - 1.0, (xb + x1 - 0.8) / 2, y0 + 0.8 + (bar - 0.6) / 2
    parts.append(strokes([[(xc - s / 2, yc - s / 2), (xc + s / 2, yc + s / 2)], [(xc + s / 2, yc - s / 2), (xc - s / 2, yc + s / 2)]], line))
    if title:
        parts.append(text(title, (x0 + 0.8 + xb - 0.7) / 2, yc, 1.2, w=0.2, gap=2.2))
    for i in range(1, stacked + 1):
        d = offset * i
        parts.append(minus(rect(x0 + d, y0 + d, x1 + d, y1 + d, line), grow(poly([(x0 + d - offset, y0 + d - offset),
                     (x1 + d - offset, y0 + d - offset), (x1 + d - offset, y1 + d - offset), (x0 + d - offset, y1 + d - offset)]), 0.5)))
    return union(parts), (x0 + 0.6, y0 + 0.8 + bar, x1 - 0.6, y1 - 0.6)

def button(label, h=1.3, pad=(1.6, 1.1), line=0.25):
    tw = text_width(label, h, gap=2.0)
    w, hh = tw + 2 * pad[0], h + 2 * pad[1]
    return union([rect(-w / 2, -hh / 2, w / 2, hh / 2, line), text(label, 0, 0, h, w=0.22, gap=2.0)]), w

def generate_row(h=5.6):
    b, w = button("GENERATE", h=1.1)
    c = w / 2 + 0.7 + h * 573 / 658 / 2
    return union([b, place(stmpd(h, 0.15), -c, 0), place(stmpd(h, 0.15), c, 0)])

def sparkle(R):
    pts = []
    for i in range(8):
        rr = R if i % 2 == 0 else R * 0.2
        a = math.pi / 4 * i - math.pi / 2
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return poly(pts)


# ---------------------------------------------------------------- placement

def place(ps, x, y, mirror=False, rot=0.0):
    """Move a local shape to board (x, y). mirror=True for bottom-side art, so it reads from below."""
    ps = copy(ps)
    if rot: ps.Rotate(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T), pcbnew.VECTOR2I(0, 0))
    if mirror: ps.Mirror(pcbnew.VECTOR2I(0, 0), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    ps.Move(pcbnew.VECTOR2I(N(x), N(y)))
    return ps

def obstacles(b, side):
    """Pads on this side's copper, and every hole, grown by PAD_CLEAR; and the footprints' own silkscreen."""
    cu = pcbnew.F_Cu if side == "F" else pcbnew.B_Cu
    silk = pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS
    pads, fsilk = empty(), empty()
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(cu):
                p.TransformShapeToPolygon(pads, cu, N(PAD_CLEAR), N(0.005), pcbnew.ERROR_OUTSIDE)
            if p.GetDrillSizeX() > 0:
                p.TransformHoleToPolygon(pads, N(PAD_CLEAR), N(0.005), pcbnew.ERROR_OUTSIDE)
        for it in list(fp.GraphicalItems()) + [fp.Reference(), fp.Value()]:
            if it.GetLayer() == silk and (not hasattr(it, "IsVisible") or it.IsVisible()):
                it.TransformShapeToPolygon(fsilk, silk, N(0.2), N(0.005), pcbnew.ERROR_OUTSIDE)
    for d in b.GetDrawings():
        if d.GetLayer() == silk:
            d.TransformShapeToPolygon(fsilk, silk, N(0.2), N(0.005), pcbnew.ERROR_OUTSIDE)
    pads.Simplify(); fsilk.Simplify()
    return pads, fsilk

def starfield(region, avoid, rng, n, big=0.06, nebula=None):
    """Scatter n stars (dots, a few four-point sparkles) inside region, each clear of avoid.
    nebula=(x, y, sx, sy) packs most of them into a Gaussian cloud there, as on the cover."""
    stars, taken = [], copy(avoid)
    bb = region.BBox()
    x0, y0, x1, y1 = bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6
    tries = 0
    while len(stars) < n and tries < n * 60:
        tries += 1
        if nebula and rng.random() < 0.7:
            x, y = rng.gauss(nebula[0], nebula[2]), rng.gauss(nebula[1], nebula[3])
        else:
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        k = rng.random()
        if k < big:
            s = place(sparkle(rng.uniform(0.9, 1.4)), x, y)
        else:
            s = circle(x, y, 0.15 + 0.22 * rng.random() ** 2.5, 12)
        if minus(s, region).OutlineCount() and area(minus(s, region)) > 1e-6: continue
        if hits(grow(s, 0.3), taken): continue
        stars.append(s); taken.BooleanAdd(grow(s, 0.3))
    return union(stars)

def sky(free, rng, density, clusters, grid=0.1):
    """Stars over every free spot of the board. free is the area they may use; it is rasterised
    on a 0.1 mm grid so thousands of candidates can be tested quickly. density is stars per mm^2
    spread evenly; clusters is a list of (x, y, sigma, n) Gaussian nebulae on top of that."""
    import cairo, numpy as np
    bb = free.BBox()
    X0, Y0 = bb.GetLeft() / 1e6, bb.GetTop() / 1e6
    W, H = int(bb.GetWidth() / 1e6 / grid) + 2, int(bb.GetHeight() / 1e6 / grid) + 2
    surf = cairo.ImageSurface(cairo.FORMAT_A8, W, H); c = cairo.Context(surf)
    c.scale(1 / grid, 1 / grid); c.translate(-X0, -Y0); c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    def path(ch):
        c.move_to(ch.CPoint(0).x / 1e6, ch.CPoint(0).y / 1e6)
        for j in range(1, ch.PointCount()): c.line_to(ch.CPoint(j).x / 1e6, ch.CPoint(j).y / 1e6)
        c.close_path()
    for i in range(free.OutlineCount()):
        path(free.Outline(i))
        for h in range(free.HoleCount(i)): path(free.Hole(i, h))
    c.fill(); surf.flush()
    ok = np.ndarray((H, surf.get_stride()), np.uint8, surf.get_data())[:, :W] > 250
    ok = ok.copy()
    yy, xx = np.mgrid[-30:31, -30:31] * grid
    def disk(x, y, r):
        i, j = int((y - Y0) / grid), int((x - X0) / grid); k = int(r / grid) + 1
        if i - k < 0 or j - k < 0 or i + k >= H or j + k >= W: return None
        m = (xx[30 - k:31 + k, 30 - k:31 + k] ** 2 + yy[30 - k:31 + k, 30 - k:31 + k] ** 2) <= r * r
        return (slice(i - k, i + k + 1), slice(j - k, j + k + 1)), m
    spots = [(rng.uniform(X0, X0 + W * grid), rng.uniform(Y0, Y0 + H * grid))
             for _ in range(int(area(free) * density * 3))]
    for x, y, sig, n in clusters:
        spots += [(rng.gauss(x, sig), rng.gauss(y, sig * 0.6)) for _ in range(n)]
    rng.shuffle(spots)
    out = empty()
    for x, y in spots:
        big = rng.random() < 0.015
        r = rng.uniform(0.9, 1.4) if big else 0.15 + 0.22 * rng.random() ** 2.5
        d = disk(x, y, (r * 0.45 if big else r) + 0.3)
        if d is None: continue
        (si, sj), m = d
        if not ok[si, sj][m].all(): continue
        ok[si, sj][m] = False
        star = place(sparkle(r), x, y) if big else circle(x, y, r, 8 if r < 0.25 else 12)
        out.AddOutline(star.Outline(0))
    return out


# ---------------------------------------------------------------- the artwork

def artwork(b):
    rng = random.Random(5233)
    art = {"F": [], "B": []}
    obs = {s: obstacles(b, s) for s in "FB"}

    board = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(board, False)
    inside = grow(board, -EDGE_CLEAR - 0.1)

    # top, left half: the keygen window
    WX, WY, WW, WH = 168.0, 133.2, 36.0, 20.0
    frame, (bx0, by0, bx1, by1) = window(WW, WH, "MARTIN GARRIX")
    lg_line, lg_fat = logo(5.6, 1.0, 0.22)
    lg_fat = grow(lg_fat, 0.11)                     # the outline's outer edge
    lw, sw = text_width("SERIAL:", 1.1), text_width(SERIAL, 1.2, gap=1.9) + 2.0
    sy, sx0 = WH / 2 - 2.4, -(text_width("SERIAL:", 1.1) + 1.0 + sw) / 2
    serial = union([text("SERIAL:", sx0 + lw / 2, sy, 1.1, w=0.19),
                    rect(sx0 + lw + 1.0, sy - 1.25, sx0 + lw + 1.0 + sw, sy + 1.25, 0.22),
                    text(SERIAL, sx0 + lw + 1.0 + sw / 2, sy, 1.2, w=0.2, gap=1.9)])
    moon_w = minus(place(moon(2.6, [(-0.55, 0.2, 0.14), (-0.4, -0.45, 0.1)]), bx1 - 2.8, by0 + 2.7, mirror=True),
                   grow(lg_fat, 0.35))
    win = union([frame, lg_line, serial, moon_w])
    sky = minus(poly([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]), grow(moon_w, 0.2))
    avoid = union([grow(win, 0.15), grow(lg_fat, 0.15), place(obs["F"][0], -WX, -WY), place(obs["F"][1], -WX, -WY)])
    stars = starfield(sky, avoid, rng, 170, big=0.03, nebula=(0.0, -0.5, 8.0, 3.5))
    art["F"].append(place(union([win, stars]), WX, WY))

    # top, left half: stars between the controller's header rows
    strip = poly([(152.3, 82.5), (166.0, 82.5), (166.0, 110.0), (152.3, 110.0)])
    art["F"].append(starfield(strip, union(list(obs["F"])), rng, 28))

    # top, right half: moon, STMPD emblem, stars
    m = place(moon(5.4, [(-0.6, 0.1, 0.12), (-0.38, -0.5, 0.08), (-0.5, 0.52, 0.1), (-0.78, -0.25, 0.05)]), 243.3, 106.0)
    c = place(stmpd(11.0, 0.2), 242.4, 133.4)
    lbl = text("STMPD RCRDS", 242.4, 141.9, 1.0, w=0.18, gap=2.0)
    tr = union([m, c, lbl])
    sky_r = union([poly([(228.0, 86.0), (256.0, 86.0), (256.0, 124.0), (228.0, 124.0)]),
                   poly([(226.0, 124.0), (255.0, 124.0), (255.0, 146.0), (226.0, 146.0)]),
                   poly([(258.0, 82.5), (270.0, 82.5), (270.0, 110.0), (258.0, 110.0)])])
    sky_r.BooleanIntersection(inside)
    art["F"].append(union([tr, starfield(sky_r, union([grow(tr, 0.35)] + list(obs["F"])), rng, 85)]))

    # bottom, both halves: GENERATE under the reset button
    art["B"].append(place(generate_row(), 173.05, 128.2, mirror=True))
    art["B"].append(place(generate_row(), 245.4, 128.2, mirror=True))

    # bottom, left half: credits
    lg_line_s, _ = logo(4.2, 0.75, 0.18)
    credits = union([
        place(lg_line_s, 0, -5.6),
        text("A WIRELESS SPLIT KEYBOARD", 0, -1.2, 1.0, w=0.18),
        text("NAMED FOR KEYGEN BY MARTIN GARRIX", 0, 1.0, 1.0, w=0.18),
        text("GITHUB.COM/MILINDMADHUKAR/KEYGEN", 0, 3.6, 1.0, w=0.18),
        text("REV 0.1", 0, 5.8, 1.0, w=0.18),
    ])
    art["B"].append(place(credits, 171.0, 140.0, mirror=True))

    # bottom, right half: keygen.exe window with the flashing hint
    w2, _ = window(22.0, 13.0, "KEYGEN.EXE", stacked=1)
    hint = union([w2, text("PRESS GENERATE TWICE", 0, 0.9, 1.0, w=0.18),
                  text("TO FLASH FIRMWARE", 0, 3.3, 1.0, w=0.18)])
    art["B"].append(place(hint, 245.8, 140.3, mirror=True))
    return art


# ---------------------------------------------------------------- the footprints' own silkscreen

SILK_EDGE, LABEL_CLEAR = 0.25, 0.15       # mm: a moved label's margin to the edge, and to pads and silk
SLIVER = 0.001                            # mm^2: less overlap than this is rounding, as DRC sees it

def shape_poly(it, d=0.0):
    ps = empty(); it.TransformShapeToPolygon(ps, it.GetLayer(), N(d), N(0.005), pcbnew.ERROR_OUTSIDE); return ps

def label_clear(t, board, edge=0.0, clear=0.0):
    """True if text t sits edge mm inside the board and clear mm off every solder mask opening and
    hole on its side, and off all other silkscreen: footprints' (its own included) and the board's."""
    silk = t.GetLayer()
    mask = pcbnew.F_Mask if silk == pcbnew.F_SilkS else pcbnew.B_Mask
    me = shape_poly(t)
    def over(ps):
        x = copy(me); x.BooleanIntersection(ps); return area(x) > SLIVER
    if area(minus(me, grow(board, -edge))) > SLIVER: return False
    box = t.GetBoundingBox(); box.Inflate(N(10))
    mine = t.m_Uuid.AsString()
    for fp in t.GetBoard().GetFootprints():
        if not box.Intersects(fp.GetBoundingBox()): continue
        for p in fp.Pads():
            ps = empty()
            if p.IsOnLayer(mask): p.TransformShapeToPolygon(ps, mask, N(clear), N(0.005), pcbnew.ERROR_OUTSIDE)
            if p.GetDrillSizeX() > 0: p.TransformHoleToPolygon(ps, N(clear), N(0.005), pcbnew.ERROR_OUTSIDE)
            if ps.OutlineCount() and over(ps): return False
        for it in list(fp.GraphicalItems()) + [fp.Reference(), fp.Value()]:
            if it.GetLayer() == silk and it.m_Uuid.AsString() != mine and (not hasattr(it, "IsVisible") or it.IsVisible()):
                if over(shape_poly(it, clear)): return False
    return not any(d.GetLayer() == silk and over(shape_poly(d, clear)) for d in t.GetBoard().GetDrawings())

def label_spots(t, fp):
    """Where a misplaced label may go, nearest its old spot first: mirrored through its nearest pad
    (a diode's K swaps to the band's other side) or beside its footprint on any side, either way
    round; failing those, anywhere on a 0.25 mm grid within 5 mm of the footprint, nearest it first."""
    pos0, ang0 = t.GetPosition(), t.GetTextAngleDegrees()
    dist = lambda c: math.hypot(c[0].x - pos0.x, c[0].y - pos0.y)
    pad = min((p.GetPosition() for p in fp.Pads()), key=lambda v: dist((v,)))
    near = [(pcbnew.VECTOR2I(2 * pad.x - pos0.x, 2 * pad.y - pos0.y), ang0)]
    fb, gap = fp.GetBoundingBox(False), N(0.4)
    cx, cy = fb.GetCenter().x, fb.GetCenter().y
    for ang in (ang0, ang0 + 90):
        t.SetTextAngleDegrees(ang)
        w, h = t.GetBoundingBox().GetWidth(), t.GetBoundingBox().GetHeight()
        near += [(pcbnew.VECTOR2I(cx, fb.GetTop() - gap - h // 2), ang),
                 (pcbnew.VECTOR2I(cx, fb.GetBottom() + gap + h // 2), ang),
                 (pcbnew.VECTOR2I(fb.GetLeft() - gap - w // 2, cy), ang),
                 (pcbnew.VECTOR2I(fb.GetRight() + gap + w // 2, cy), ang)]
    grid = [(pcbnew.VECTOR2I(cx + N(i / 4), cy + N(j / 4)), ang)
            for i in range(-20, 21) for j in range(-20, 21) for ang in (ang0, ang0 + 90)]
    t.SetTextAngleDegrees(ang0)
    return sorted(near, key=dist) + sorted(grid, key=lambda c: math.hypot(c[0].x - cx, c[0].y - cy))

def place_labels(b, board):
    """Move each visible footprint text that crosses the edge, a mask opening or other silkscreen
    to the first spot from label_spots that is SILK_EDGE inside the edge and LABEL_CLEAR off the rest."""
    moved, stuck = [], []
    for fp in b.GetFootprints():
        for t in [fp.Reference()] + [g for g in fp.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT)]:
            if t.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS) or not t.IsVisible() or label_clear(t, board):
                continue
            pos0, ang0 = t.GetPosition(), t.GetTextAngleDegrees()
            for pos, ang in label_spots(t, fp):
                t.SetTextAngleDegrees(ang); t.SetPosition(pos)
                if label_clear(t, board, SILK_EDGE, LABEL_CLEAR):
                    moved.append(f"{fp.GetReference()} {t.GetText()}"); break
            else:
                t.SetTextAngleDegrees(ang0); t.SetPosition(pos0)
                stuck.append(f"{fp.GetReference()} {t.GetText()}")
    return moved, stuck


# ---------------------------------------------------------------- board I/O

STACKUP = """(stackup
  (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
  (layer "F.Paste" (type "Top Solder Paste"))
  (layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))
  (layer "F.Cu" (type "copper") (thickness 0.035))
  (layer "dielectric 1" (type "core") (color "FR4 natural") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
  (layer "B.Cu" (type "copper") (thickness 0.035))
  (layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))
  (layer "B.Paste" (type "Bottom Solder Paste"))
  (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
  (copper_finish "HAL lead-free")
  (dielectric_constraints no))"""

def strip_old_and_set_stackup():
    """On the file text: drop the old art group and its members, (re)write the stackup."""
    tree = parse(PCB.read_text())
    members = set()
    for g in find(tree, "group"):
        if len(g) > 1 and g[1] == GROUP:
            members |= set(first(g, "members")[1:])
    tree[:] = [n for n in tree if not (isinstance(n, list) and n and (
        (n[0] == "group" and len(n) > 1 and n[1] == GROUP) or
        (first(n, "uuid") and first(n, "uuid")[1] in members)))]
    setup = first(tree, "setup")
    setup[:] = [n for n in setup if not (isinstance(n, list) and n and n[0] == "stackup")]
    setup.insert(1, parse(STACKUP))
    PCB.write_text(dump(tree) + "\n")
    return len(members)

def main():
    removed = strip_old_and_set_stackup()
    b = pcbnew.LoadBoard(str(PCB))
    board = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(board, False)
    edge = empty()                         # the outer edge only: the LED cut-outs are holes in board
    for i in range(board.OutlineCount()): edge.AddOutline(board.Outline(i))
    moved, stuck = place_labels(b, edge)
    print(f"footprint labels: moved {len(moved)}" + (f" ({', '.join(moved)})" if moved else ""))
    if stuck: print(f"no clear spot for: {', '.join(stuck)}")
    inside = grow(board, -EDGE_CLEAR)
    group = pcbnew.PCB_GROUP(b); group.SetName(GROUP); b.Add(group)
    count = 0
    for side, pieces in artwork(b).items():
        layer = pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS
        pads, fsilk = obstacles(b, side)
        art = union(pieces)
        free = minus(minus(minus(inside, pads), fsilk), grow(art, 0.4))
        bb = board.BBox()
        rng = random.Random(406 if side == "F" else 4927)
        clusters = [(rng.uniform(bb.GetLeft() / 1e6, bb.GetRight() / 1e6), rng.uniform(bb.GetTop() / 1e6, bb.GetBottom() / 1e6),
                     rng.uniform(5, 10), 400) for _ in range(SKY[side][1])]
        art.BooleanAdd(sky(free, rng, SKY[side][0], clusters))
        want = area(art)
        art.BooleanIntersection(inside); art.BooleanSubtract(pads); art.BooleanSubtract(fsilk)
        clipped = want - area(art)
        if clipped > 0.01: print(f"{side}.SilkS: clipped {clipped:.2f} mm^2 of artwork at pads, holes, "
                                  f"footprint silkscreen or the edge")
        art.Fracture()
        for i in range(art.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(art.Outline(i))
            s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_POLY)
            s.SetPolyShape(one); s.SetFilled(True); s.SetWidth(0); s.SetLayer(layer)
            b.Add(s); group.AddItem(s); count += 1
    pcbnew.SaveBoard(str(PCB), b)
    print(f"removed {removed} old art shapes, added {count}; stackup: black mask, white silkscreen, HASL")


if __name__ == "__main__":
    main()
