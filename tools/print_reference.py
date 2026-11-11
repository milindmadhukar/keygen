#!/usr/bin/env python3
"""Write docs/keygen-reference.pdf: one printable A4 reference for building and using Keygen, in
black and white.

    cover                 contents, the scale check, both halves at 1:2
    key layout 1:1        each half: every keycap with its legend on each layer and its switch
    back 1:1              each half turned over: where every part goes, by reference
    power parts           the small parts beside each controller, enlarged
    parts close up        one part of each type, with its orientation marks and how it goes in
    keymap                every layer across both halves
    key matrix            each key's row, column, switch and diode, and the controller's pads
    parts list            each half's assembly BOM, with a box to tick per line

Positions come from pcb/keygen.kicad_pcb, legends from the keymap pictures (assets/keymap-*.svg),
the parts lists from fab/BOM.md. Print at 100 % ("Actual size", not "Fit to page") and measure the
100 mm ruler on a 1:1 page.

    python3 tools/print_reference.py
"""
import html, math, re, subprocess, sys, tempfile
from pathlib import Path

import cairo
import gi
import pcbnew

gi.require_version("Rsvg", "2.0")
gi.require_foreign("cairo")
from gi.repository import Rsvg

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C
import gen_pcb as G
import gen_zmk_layout as Z
import plate_print as P
import render_assembly as A

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/keygen-reference.pdf"
A.TMP = ROOT / "pcb/_reference.kicad_pcb"        # render_assembly's board copy, under our own name
PT = 72 / 25.4
W, H = 297.0, 210.0                              # A4 landscape, mm
M = 12.0                                         # page margin
TOP, BOTTOM = 24.0, H - 17.0                     # the drawing area between the header and the ruler
FONT = "DejaVu Sans"
KNOB_D, CAP_GAP = 19.0, 0.95
LAYERS = ("base", "nav", "fn", "system")
GREY = 0.45
POWER_NEAR = 40.0                                # mm from the battery connector: the power parts


# ---------------------------------------------------------------------------------------------
# drawing helpers (all lengths in mm)

def font(cr, size, bold=False, italic=False):
    cr.select_font_face(FONT, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size)


def text(cr, s, x, y, size, bold=False, align="left", grey=0.0, italic=False):
    """Draw s with its baseline at y; align is left, centre or right of x. Returns its width."""
    font(cr, size, bold, italic)
    e = cr.text_extents(s)
    dx = {"left": 0, "centre": -e.x_advance / 2, "right": -e.x_advance}[align]
    cr.set_source_rgb(grey, grey, grey)
    cr.move_to(x + dx, y); cr.show_text(s)
    cr.set_source_rgb(0, 0, 0)
    return e.x_advance


def width(cr, s, size, bold=False):
    font(cr, size, bold)
    return cr.text_extents(s).x_advance


def wrap(cr, s, size, maxw, bold=False):
    lines, cur = [], ""
    for word in s.split():
        if cur and width(cr, cur + " " + word, size, bold) > maxw:
            lines.append(cur); cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + ([cur] if cur else [])


def paragraph(cr, s, x, y, size, maxw, lead=1.35, **kw):
    """Draw s wrapped to maxw from the baseline y down. Returns the y below it."""
    for line in wrap(cr, s, size, maxw, kw.get("bold", False)):
        text(cr, line, x, y, size, **kw); y += size * lead
    return y


def fit(cr, lines, size, maxw, bold=False, smallest=0.9):
    """The largest size up to `size` at which every line fits maxw (not below `smallest`)."""
    while size > smallest and max(width(cr, l, size, bold) for l in lines) > maxw:
        size *= 0.93
    return size


def ruler(cr, x, y):
    """A 100 mm scale bar, to check the print's scale."""
    cr.set_line_width(0.25)
    cr.move_to(x, y); cr.line_to(x + 100, y); cr.stroke()
    for i in range(0, 101, 5):
        cr.move_to(x + i, y); cr.line_to(x + i, y - (3 if i % 10 == 0 else 1.5)); cr.stroke()
        if i % 50 == 0: text(cr, f"{i}", x + i, y - 4, 2.4, align="centre")
    text(cr, "100 mm. If it measures anything else, reprint at 100 % (Actual size).", x + 104, y, 2.5)


def scale_bar(cr, x, y, scale, mm=10):
    """A bar `mm` long on the board at `scale`."""
    cr.set_line_width(0.3)
    cr.move_to(x, y); cr.line_to(x + mm * scale, y); cr.stroke()
    for t in (0, mm * scale):
        cr.move_to(x + t, y - 1.5); cr.line_to(x + t, y + 0.5); cr.stroke()
    text(cr, f"{mm} mm", x + mm * scale + 2, y + 0.8, 2.4)


def svg(cr, data, x, y, w, h):
    """Draw SVG text into the box (x, y, w, h), in mm on the page, keeping its aspect ratio."""
    handle = Rsvg.Handle.new_from_data(data.encode())
    vp = Rsvg.Rectangle(); vp.x, vp.y, vp.width, vp.height = x, y, w, h
    cr.save(); cr.rectangle(x, y, w, h); cr.clip()                 # rsvg draws past its viewBox
    handle.render_document(cr, vp)
    cr.restore()


def outline_path(cr, pts):
    cr.move_to(*pts[0])
    for p in pts[1:]: cr.line_to(*p)
    cr.close_path()


# ---------------------------------------------------------------------------------------------
# board data

def board():
    b = pcbnew.LoadBoard(str(A.PCB))
    mm = pcbnew.ToMM
    polys = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(polys, False)
    mid = mm(b.GetBoardEdgesBoundingBox().GetCenter().x)
    halves = {}
    for i in range(polys.OutlineCount()):
        o = polys.Outline(i)
        pts = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
        side = "left" if sum(p[0] for p in pts) / len(pts) < mid else "right"
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        halves[side] = dict(outline=pts, box=(min(xs), min(ys), max(xs), max(ys)), holes=[], enc=[], sw={})
    for fp in b.GetFootprints():
        ref, p = fp.GetReference(), fp.GetPosition()
        x, y = mm(p.x), mm(p.y)
        side = halves["left" if x < mid else "right"]
        if ref.startswith("H"): side["holes"].append((x, y))
        elif ref.startswith("ENC"): side["enc"].append((x, y))
        elif re.fullmatch(r"SW\d+", ref) and int(ref[2:]) % 100 < 90: side["sw"][ref] = (x, y)
    for side, h in halves.items():
        h["oled"] = C.halves()[side]["oled"]
    return b, halves


def legends():
    """{key position: {layer: {"tap": [lines], "hold": [...], "shifted": [...]}}} from the keymap
    pictures."""
    out = {}
    for layer in LAYERS:
        s = (ROOT / f"assets/keymap-{layer}.svg").read_text()
        for pos, body in re.findall(r'class="key[^"]* keypos-(\d+)">(.*?)</g>', s, re.S):
            for cls, t in re.findall(r'<text[^>]*class="key ([^"]*)"[^>]*>(.*?)</text>', body, re.S):
                lines = [html.unescape(l).lstrip("&") for l in re.findall(r">([^<]+)<", f">{t}<") if l.strip()]
                if lines:
                    kind = cls.split()[-1] if cls.split()[-1] in ("hold", "shifted") else "tap"
                    out.setdefault(int(pos), {}).setdefault(layer, {})[kind] = lines
    return out


def key_table(halves):
    """[(side, pos, cx, cy, rot, w_u, h_u, switch ref)] for every key, and the encoder presses
    as (side, pos, x, y) ."""
    flat = [k for row in Z.ORDER for k in row]
    pos_of = {k: i for i, k in enumerate(flat)}
    keys = []
    for side in ("left", "right"):
        rows = [(r, c) for r, c, *_ in P.g.KEYS[side]]
        for (r, c), (lab, cx, cy, rr, w, h) in zip(rows, P.keys(side)):
            sw = min(halves[side]["sw"], key=lambda ref: math.dist(halves[side]["sw"][ref], (cx, cy)))
            keys.append((side, pos_of[(side, r, c)], cx, cy, rr, w, h, sw))
    knobs = [(side, pos_of[(side, *P.g.ENCODER_POS[side])], *halves[side]["enc"][0]) for side in ("left", "right")]
    return keys, knobs


# ---------------------------------------------------------------------------------------------
# key layout

CORNERS = {"nav": "tl", "fn": "tr", "system": "bl"}      # base sits in the middle, its hold at br


def keycap(cr, leg, w, h, sw, detail=True):
    """One keycap centred on the origin, w x h mm, with its legends."""
    P.rrect(cr, w, h, 1.2)
    cr.set_source_rgb(1, 1, 1); cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0); cr.set_line_width(0.3); cr.stroke()
    base = leg.get("base", {})
    tap = base.get("tap", [])
    if tap:
        size = fit(cr, tap, 3.6 if len("".join(tap)) <= 2 else 2.6, w - 3, bold=True)
        y0 = -0.6 - (len(tap) - 1) * size * 0.6 + size * 0.35
        for i, l in enumerate(tap):
            text(cr, l, 0, y0 + i * size * 1.15, size, bold=True, align="centre")
    if not detail:
        return
    cw, pad, sz = w / 2 - 2.0, 1.1, 1.5
    spots = dict(CORNERS)
    for layer, corner in spots.items():
        lines = leg.get(layer, {}).get("tap", [])
        if lines:
            corner_text(cr, lines, corner, w, h, cw, pad, sz)
    if (hold := base.get("hold")):
        corner_text(cr, hold, "br", w, h, cw, pad, sz, italic=True)
    if sw:
        text(cr, sw, 0, h / 2 - pad - 3.2, 1.05, align="centre", grey=GREY)


def corner_text(cr, lines, corner, w, h, cw, pad, size, italic=False):
    size = fit(cr, lines, size, cw)
    lead = size * 1.15
    x = -w / 2 + pad if corner[1] == "l" else w / 2 - pad
    if corner[0] == "t":
        ys = [-h / 2 + pad + size * 0.8 + i * lead for i in range(len(lines))]
    else:
        ys = [h / 2 - pad - (len(lines) - 1 - i) * lead for i in range(len(lines))]
    for l, y in zip(lines, ys):
        text(cr, l, x, y, size, align="left" if corner[1] == "l" else "right", italic=italic)


def knob(cr, leg):
    """The encoder: the knob's circle, its press and what turning it does, on each layer."""
    cr.new_path(); cr.arc(0, 0, KNOB_D / 2, 0, 2 * math.pi)
    cr.set_dash([1.0, 0.7]); cr.set_line_width(0.3); cr.stroke(); cr.set_dash([])
    rows = []
    for layer in LAYERS:
        l = leg.get(layer, {})
        press, turn = " ".join(l.get("tap", [])), " ".join(l.get("shifted", [])).replace("↻", "").strip()
        if press or turn:
            rows.append((layer, press, turn))
    text(cr, "knob: press / ↻ turn", 0, -KNOB_D / 2 - 1.2, 1.5, align="centre", grey=GREY)
    y = -2.0 * (len(rows) - 1) - 0.4
    for layer, press, turn in rows:
        base = layer == "base"
        s = " / ".join(filter(None, [press, f"↻ {turn}" if turn else ""]))
        size = fit(cr, [s], 2.0 if base else 1.5, KNOB_D - 4 if base else KNOB_D - 6, bold=base)
        if not base:
            s = f"{layer.capitalize()}: {s}"
        text(cr, s, 0, y, size, bold=base, align="centre")
        y += 4.0


def layout(cr, half, keys, knobs, leg, ox, oy, scale=1.0, detail=True):
    """One half's outline, keycaps, holes, OLED and knob, with the half's top-left at (ox, oy)."""
    x0, y0 = half["box"][:2]
    cr.save(); cr.translate(ox, oy); cr.scale(scale, scale); cr.translate(-x0, -y0)
    outline_path(cr, half["outline"]); cr.set_line_width(0.4 / scale); cr.stroke()
    for x, y in half["holes"]:
        cr.new_path(); cr.arc(x, y, 1.1, 0, 2 * math.pi); cr.set_line_width(0.25); cr.stroke()
    ox0, oy0, ox1, oy1 = half["oled"]
    cr.rectangle(ox0, oy0, ox1 - ox0, oy1 - oy0); cr.set_dash([1.0, 0.7]); cr.set_line_width(0.3); cr.stroke(); cr.set_dash([])
    if detail: text(cr, "OLED", (ox0 + ox1) / 2, (oy0 + oy1) / 2 + 1, 2.6, align="centre", grey=GREY)
    for _, pos, cx, cy, rr, w, h, sw in keys:
        cr.save(); cr.translate(cx, cy); cr.rotate(math.radians(rr))
        keycap(cr, leg.get(pos, {}), w * G.U - CAP_GAP, h * G.U - CAP_GAP, sw, detail)
        cr.restore()
    for _, pos, x, y in knobs:
        cr.save(); cr.translate(x, y)
        if detail: knob(cr, leg.get(pos, {}))
        else:
            cr.new_path(); cr.arc(0, 0, KNOB_D / 2, 0, 2 * math.pi); cr.set_line_width(0.3); cr.stroke()
        cr.restore()
    cr.restore()


def key_legend(cr, x, y):
    """The sample keycap that says which legend is which."""
    text(cr, "Reading a key", x, y, 3.2, bold=True)
    s = 3.0
    cr.save(); cr.translate(x + 30, y + 34); cr.scale(s, s)
    w = G.U - CAP_GAP
    P.rrect(cr, w, w, 1.2); cr.set_line_width(0.3 / s); cr.stroke()
    text(cr, "Base", 0, 0.6, 3.2, bold=True, align="centre")
    for lab, corner in (("Nav", "tl"), ("Fn", "tr"), ("System", "bl"), ("hold", "br")):
        corner_text(cr, [lab], corner, w, w, w / 2 - 2.0, 1.1, 1.5, italic=lab == "hold")
    text(cr, "SW1xx", 0, w / 2 - 1.1 - 3.2, 1.05, align="centre", grey=GREY)
    cr.restore()
    notes = [
        "Middle: the key on the base layer, bold.",
        "Top left: the Nav layer (hold Nav).",
        "Top right: the Fn layer (hold Fn).",
        "Bottom left: the System layer (Nav and Fn together).",
        "Bottom right, italic: what the key does when held.",
        "Grey: the switch's reference on the board.",
        "Dashed circle: the encoder knob; it lists its press and its turn per layer.",
        "Dashed box: the OLED.  Circles: the M2 standoff holes.",
    ]
    yy = y + 66
    for n in notes:
        yy = paragraph(cr, n, x, yy, 2.5, 84) + 0.8


# ---------------------------------------------------------------------------------------------
# component maps (kicad-cli SVG of the fabrication layers)

def board_svgs(tmp):
    """The back's fab layer as SVG, each part with its reference, without the unfitted parts and
    without the switches' holes ("back"); and both sides' with no references but every hole, for
    the close-ups ("back-bare", "front-bare"). Returns ({name: svg path}, page mapping)."""
    out = {}
    for refs in (True, False):
        b = A.prepare(refs=refs)
        for fp in b.GetFootprints():
            ref = fp.GetReference()
            switch = re.fullmatch(r"SW\d+", ref) and int(ref[2:]) % 100 < 90
            for pad in fp.Pads():                    # on no layer, so never drawn
                if fp.IsDNP() or (refs and switch and pad.HasHole()):
                    pad.SetLayerSet(pcbnew.LSET())
        b.Save(str(A.TMP))
        for side in ("back",) if refs else ("back", "front"):
            f = tmp / f"{side}{'' if refs else '-bare'}.svg"
            layers = "Edge.Cuts,B.Fab" if side == "back" else "Edge.Cuts,F.Fab"
            subprocess.run(["kicad-cli", "pcb", "export", "svg", "--mode-single", "-o", str(f), "-l", layers,
                            "--sketch-pads-on-fab-layers", "--hide-DNP-footprints-on-fab-layers",
                            "--exclude-drawing-sheet", "--page-size-mode", "2", "--black-and-white",
                            "--drill-shape-opt", "0", *(["--mirror"] if side == "back" else []), str(A.TMP)],
                           check=True, capture_output=True)
            out[f.stem] = f
    edge = b.GetBoardEdgesBoundingBox()
    bx0, by0, bx1 = (pcbnew.ToMM(v) for v in (edge.GetLeft(), edge.GetTop(), edge.GetRight()))
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', out["back"].read_text()).group(1).split()]
    pad = (vb[2] - (bx1 - bx0)) / 2

    def page(side, x0, y0, x1, y1):
        """A board box (mm) as a box on that side's SVG page (mirrored on the back)."""
        if side == "back":
            x0, x1 = bx1 - x1 + bx0, bx1 - x0 + bx0
        return (x0 - bx0 + pad, y0 - by0 + pad, x1 - bx0 + pad, y1 - by0 + pad)
    return out, page


def crop(path, box):
    x0, y0, x1, y1 = box
    return re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
                  f'width="{x1 - x0:.4f}mm" height="{y1 - y0:.4f}mm" viewBox="{x0:.4f} {y0:.4f} {x1 - x0:.4f} {y1 - y0:.4f}"',
                  path.read_text(), count=1)


def map_page(cr, svgs, page, side, half_name, half, scale=1.0, at=None):
    x0, y0, x1, y1 = half["box"]
    m = 1.0
    box = (x0 - m, y0 - m, x1 + m, y1 + m)
    w, h = (box[2] - box[0]) * scale, (box[3] - box[1]) * scale
    ox, oy = at or (M, TOP + (BOTTOM - TOP - h) / 2)
    svg(cr, crop(svgs[side], page(side, *box)), ox, oy, w, h)
    return ox, oy, w, h


# ---------------------------------------------------------------------------------------------
# pages

class Doc:
    def __init__(self, path):
        self.surf = cairo.PDFSurface(str(path), W * PT, H * PT)
        self.surf.set_metadata(cairo.PDFMetadata.TITLE, "Keygen printed reference")
        self.cr = cairo.Context(self.surf); self.cr.scale(PT, PT)
        self.n = 0

    def page(self, title, sub=None, total=None):
        self.n += 1
        cr = self.cr
        text(cr, title, M, 13, 5, bold=True)
        if sub: text(cr, sub, M, 18.5, 2.8, grey=0.25)
        cr.set_line_width(0.2); cr.move_to(M, 21); cr.line_to(W - M, 21); cr.stroke()
        text(cr, f"Keygen reference   {self.n} / {total}", W - M, H - 6, 2.4, align="right", grey=GREY)
        return cr

    def next(self):
        self.cr.show_page()


def bom_tables():
    """{"Left half": [[part, qty, refs, notes], ...], "Right half": ...} from fab/BOM.md."""
    out, cur = {}, None
    for line in (ROOT / "fab/BOM.md").read_text().splitlines():
        if line.startswith("## "):
            cur = out.setdefault(line[3:].strip(), []) if line.endswith(" half") else None
        elif cur is not None and line.startswith("|") and not line.startswith("|---") and not line.startswith("| Part"):
            cur.append([c.strip() for c in line.strip("|").split("|")])
    return out


def bom_rows(cr, rows, cols):
    """Lay out table rows: [(row cells wrapped into lines, height)]."""
    out = []
    for r in rows:
        cells = [wrap(cr, c, 2.3, cw - 2) or [""] for c, (_, cw) in zip(r, cols[1:])]
        out.append((cells, max(len(c) for c in cells) * 3.0 + 1.6))
    return out


def matrix_page(cr, b, keys, knobs, leg):
    """Each half's matrix as a grid (rows down, columns across, each key with its switch and diode),
    and the controller's pads with their nets."""
    nets = {}                                  # (side, row, col) -> {"sw": ref, "d": ref}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            m = re.fullmatch(r"/(left|right)/K(\d)(\d)", pad.GetNetname())
            if m:
                kind = "d" if ref.startswith("D") else "sw" if ref.startswith(("SW", "J")) else None
                if kind and not (kind == "sw" and ref.startswith("J") and pad.GetNumber() != "5"):
                    nets.setdefault((m[1], int(m[2]), int(m[3])), {})[kind] = ref
    pos = {k: i for i, k in enumerate(k for row in Z.ORDER for k in row)}
    pin = {net: (pad, P.g.MCU_PINS[pad]) for pad, net in P.g.MCU_NETS.items()}
    cw, rh, lw = 25.0, 10.0, 26.0
    y = TOP + 4
    for side in ("left", "right"):
        text(cr, f"{side} half", M, y + 3, 3.2, bold=True)
        y += 6
        for c in range(7):
            x = M + lw + c * cw
            text(cr, f"COL{c}", x + cw / 2, y + 2.6, 2.4, bold=True, align="centre")
            pad, name = pin[f"COL{c}"]
            text(cr, f"{name}, pad {pad}", x + cw / 2, y + 5.4, 1.8, align="centre", grey=GREY)
        y += 7
        for r in range(5):
            pad, name = pin[f"ROW{r}"]
            text(cr, f"ROW{r}", M, y + 4.2, 2.4, bold=True)
            text(cr, f"{name}, pad {pad}", M, y + 7.2, 1.8, grey=GREY)
            for c in range(7):
                x = M + lw + c * cw
                cr.rectangle(x, y, cw, rh); cr.set_line_width(0.2); cr.stroke()
                parts = nets.get((side, r, c))
                if not parts:
                    continue
                tap = leg.get(pos[(side, r, c)], {}).get("base", {}).get("tap", [])
                label = " ".join(tap) if (side, r, c) != (side, *P.g.ENCODER_POS[side]) else "knob press"
                text(cr, label, x + cw / 2, y + 4.2, fit(cr, [label], 2.6, cw - 2, bold=True), bold=True, align="centre")
                sw = parts.get("sw", "")
                sw = f"{sw} pin 5" if sw.startswith("J") else sw
                text(cr, f"{sw}  {parts.get('d', '')}", x + cw / 2, y + 7.6, 1.8, align="centre", grey=0.3)
            y += rh
        y += 6
    x0 = M + lw + 7 * cw + 14
    text(cr, "Controller pads", x0, TOP + 7, 3.2, bold=True)
    yy = paragraph(cr, "nRF52840 SuperMini, U101 and U201. Pad numbers as on the back map beside U101; "
                   "pads 1 to 12 down one edge, 13 to 24 down the other, USB-C at the top.",
                   x0, TOP + 12, 2.3, W - M - x0)
    yy += 2
    for head, dx in (("Pad", 0), ("Pin", 9), ("Net", 22)):
        text(cr, head, x0 + dx, yy, 2.3, bold=True)
    yy += 1.2
    cr.set_line_width(0.25); cr.move_to(x0, yy); cr.line_to(W - M, yy); cr.stroke()
    yy += 3.6
    for pad in range(1, 25):
        text(cr, str(pad), x0, yy, 2.3)
        text(cr, P.g.MCU_PINS[pad], x0 + 9, yy, 2.3)
        text(cr, P.g.MCU_NETS.get(pad, "not connected"), x0 + 22, yy, 2.3, grey=0 if pad in P.g.MCU_NETS else GREY)
        yy += 3.75
    paragraph(cr, "Diodes: cathode (band) to the row. A key whose switch and diode both test good but that "
              "never registers: check its row and column back to these pads.", x0, yy + 2, 2.3, W - M - x0)


def main():
    b, halves = board()
    leg = legends()
    keys, knobs = key_table(halves)
    by_side = lambda seq, s: [k for k in seq if k[0] == s]
    boms = bom_tables()
    cols = [("", 7), ("Part", 70), ("Qty", 10), ("References", 58), ("Solder notes", W - 2 * M - 145)]

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        try:
            svgs, page = board_svgs(tmp)
        finally:
            for p in (A.TMP, A.TMP.with_suffix(".kicad_prl"), A.TMP.with_suffix(".kicad_pro")): p.unlink(missing_ok=True)

        # plan the BOM pages: each half's table, split where a page fills
        probe = cairo.Context(cairo.PDFSurface(None, 10, 10)); probe.scale(PT, PT)
        bom_pages = []
        for name, rows in boms.items():
            laid, chunk, y = bom_rows(probe, rows, cols), [], 0
            for row in laid:
                if y + row[1] > BOTTOM - TOP - 8 and chunk:
                    bom_pages.append((name, chunk)); chunk, y = [], 0
                chunk.append(row); y += row[1]
            bom_pages.append((name, chunk))

        contents = [("Key layout, left half", "1:1"), ("Key layout, right half", "1:1"),
                    ("Back of the left half: where each part goes", "1:1"),
                    ("Back of the right half: where each part goes", "1:1"),
                    ("Power parts beside each controller", "enlarged"), ("Parts close up: how each type goes in", "enlarged"),
                    ("Keymap: Base and Nav layers", ""), ("Keymap: Fn and System layers", ""),
                    ("Key matrix and controller pins", "")]
        contents += [(f"Parts list, {name.lower()}" + (" (cont.)" if i and bom_pages[i - 1][0] == name else ""), "")
                     for i, (name, _) in enumerate(bom_pages)]
        total = 1 + len(contents)

        doc = Doc(OUT)

        # cover
        cr = doc.page("Keygen: printed reference", "Split, wireless, 33 keys and an encoder per half. "
                      "Everything needed at the bench, in black and white.", total)
        y = 32
        text(cr, "Contents", M, y, 3.6, bold=True); y += 6
        for i, (name, scale) in enumerate(contents):
            text(cr, f"{i + 2}", M + 6, y, 2.8, align="right")
            text(cr, name, M + 10, y, 2.8)
            if scale: text(cr, scale, M + 95, y, 2.8, grey=GREY)
            y += 4.4
        px, y = 160, 32
        text(cr, "Printing", px, y, 3.6, bold=True); y += 6
        for s in ("A4, landscape, black and white, at 100 % (\"Actual size\"; never \"Fit to page\").",
                  "The pages marked 1:1 are full size: lay a keycap, a switch or the bare board on them.",
                  "Measure the ruler at the foot of this page: it must be exactly 100 mm."):
            y = paragraph(cr, s, px, y, 2.8, W - M - px) + 0.8
        lw = halves["left"]["box"][2] - halves["left"]["box"][0]
        lx, ly = (W - lw - 8) / 2, 112
        for i, side in enumerate(("left", "right")):
            text(cr, f"{side} half", lx + i * (lw / 2 + 8) + lw / 4, ly, 2.6, align="centre", grey=GREY)
            layout(cr, halves[side], by_side(keys, side), by_side(knobs, side), leg,
                   lx + i * (lw / 2 + 8), ly + 3, scale=0.5, detail=False)
        text(cr, "Both halves at 1:2, base layer.", W / 2, ly + 72, 2.4, align="centre", grey=GREY)
        ruler(cr, M, BOTTOM + 6)
        doc.next()

        # key layout, 1:1
        for side in ("left", "right"):
            h = halves[side]
            bw, bh = h["box"][2] - h["box"][0], h["box"][3] - h["box"][1]
            cr = doc.page(f"Key layout, {side} half, 1:1",
                          f"From above, as you type on it. Board {bw:.1f} × {bh:.1f} mm; USB-C at the top.", total)
            layout(cr, h, by_side(keys, side), by_side(knobs, side), leg, M, TOP + (BOTTOM - TOP - bh) / 2)
            key_legend(cr, M + bw + 14, TOP + 6)
            ruler(cr, M, BOTTOM + 6)
            doc.next()

        # component maps, 1:1
        notes = {
            "back": ["Seen from the back, with the board turned over, so left and right are swapped: the "
                     "left half's controller sits at top left, the right half's at top right.",
                     "Every part except the switches, the OLED and the encoder goes on this side.",
                     "Diodes: band toward pad 1. LEDs: lit side down into the cut-out, cut corner on pad 1.",
                     "Unfitted parts (the optional 100 nF capacitor beside each LED) are not shown.",
                     "Switch footprints show only their hotswap socket pads.",
                     "The next two pages enlarge the power parts and show each type of part close up."],
        }
        for side in ("back",):
            for name in ("left", "right"):
                h = halves[name]
                cr = doc.page(f"{side.capitalize()} of the {name} half, 1:1",
                              "Fabrication drawing: part outlines, pads and references.", total)
                ox, oy, w, hh = map_page(cr, svgs, page, side, name, h)
                y = TOP + 8
                for s in notes[side]:
                    y = paragraph(cr, s, ox + w + 10, y, 2.6, W - M - (ox + w + 10)) + 1.5
                ruler(cr, M, BOTTOM + 6)
                doc.next()

        # power parts, enlarged
        cr = doc.page("Power parts beside each controller, from the back",
                      "The boost converter, battery switch, LED buffer and their resistors and capacitors.", total)
        boxes = []
        for name, digit in (("left", "1"), ("right", "2")):
            bat = b.FindFootprintByReference(f"BT{digit}01").GetPosition()     # the parts round it, not C5 at the last LED
            rects = [fp.GetBoundingBox(False) for fp in b.GetFootprints()
                     if A.POWER.match(fp.GetReference()) and not fp.IsDNP()
                     and re.search(r"\d", fp.GetReference()).group() == digit
                     and pcbnew.ToMM((fp.GetPosition() - bat).EuclideanNorm()) < POWER_NEAR]
            boxes.append((name, (min(pcbnew.ToMM(r.GetLeft()) for r in rects) - A.MARGIN,
                                 min(pcbnew.ToMM(r.GetTop()) for r in rects) - A.MARGIN,
                                 max(pcbnew.ToMM(r.GetRight()) for r in rects) + A.MARGIN,
                                 max(pcbnew.ToMM(r.GetBottom()) for r in rects) + A.MARGIN)))
        gap = 12
        bw = sum(bx[2] - bx[0] for _, bx in boxes)
        bh = max(bx[3] - bx[1] for _, bx in boxes)
        scale = math.floor(min((W - 2 * M - gap) / bw, (BOTTOM - TOP - 14) / bh) * 2) / 2
        x = (W - bw * scale - gap) / 2
        for name, bx in boxes:
            w, hh = (bx[2] - bx[0]) * scale, (bx[3] - bx[1]) * scale
            text(cr, f"{name} half", x + w / 2, TOP + 7, 3.2, bold=True, align="centre")
            svg(cr, crop(svgs["back"], page("back", *bx)), x, TOP + 10, w, hh)
            cr.set_line_width(0.2); cr.rectangle(x, TOP + 10, w, hh); cr.stroke()
            x += w + gap
        text(cr, f"Scale {scale:g}:1", M, BOTTOM + 6, 2.6, bold=True)
        scale_bar(cr, M + 22, BOTTOM + 5.2, scale, 5)
        doc.next()

        # parts close up
        cr = doc.page("Parts close up: how each type goes in",
                      "Pads and orientation marks, enlarged. In the order they are soldered.", total)
        cols_n, cw, ch = 4, (W - 2 * M) / 4, (BOTTOM - TOP + 8) / 3
        for i, (name, ref, side, title, caption) in enumerate(A.PARTS):
            cx, cy = M + (i % cols_n) * cw, TOP + 2 + (i // cols_n) * ch
            fp = b.FindFootprintByReference(ref)
            r = fp.GetBoundingBox(False)
            mx, my = pcbnew.ToMM(r.GetCenter().x), pcbnew.ToMM(r.GetCenter().y)
            span = max(A.PART_SPAN, pcbnew.ToMM(max(r.GetWidth(), r.GetHeight())) + 4.0)
            s = math.floor(min(2.5, 38 / span) * 4) / 4
            text(cr, title, cx, cy + 3, fit(cr, [title], 2.5, cw - 4, bold=True), bold=True)
            svg(cr, crop(svgs[f"{side}-bare"], page(side, mx - span / 2, my - span / 2, mx + span / 2, my + span / 2)),
                cx + (cw - 4 - span * s) / 2, cy + 5, span * s, span * s)
            text(cr, f"{s:g}:1", cx + cw - 5, cy + 5 + span * s, 2.0, align="right", grey=GREY)
            paragraph(cr, caption, cx, cy + 9 + span * s, 2.2, cw - 5)
        doc.next()

        # keymap
        for pair in (("base", "nav"), ("fn", "system")):
            cr = doc.page(f"Keymap: {pair[0].capitalize()} and {pair[1].capitalize()} layers",
                          "Both halves. Held keys are shaded; blank keys fall through to the layer below.", total)
            for i, layer in enumerate(pair):
                data = (ROOT / f"assets/keymap-{layer}.svg").read_text()
                vw, vh = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', data).groups())
                ah = (BOTTOM - TOP) / 2
                s = min((W - 2 * M) / vw, ah / vh)
                svg(cr, data, (W - vw * s) / 2, TOP + 2 + i * (ah + 4), vw * s, vh * s)
            doc.next()

        # matrix and controller pins
        cr = doc.page("Key matrix and controller pins",
                      "Which row and column each key is on, for checking a dead key with a multimeter. "
                      "Both halves are wired alike.", total)
        matrix_page(cr, b, keys, knobs, leg)
        doc.next()

        # parts list
        for name, rows in bom_pages:
            cr = doc.page(f"Parts list, {name.lower()}", "From fab/BOM.md. Tick each line as it is soldered.", total)
            x, y = M, TOP + 6
            for (head, cw) in cols:
                text(cr, head, x + 1, y, 2.5, bold=True); x += cw
            y += 1.8
            cr.set_line_width(0.3); cr.move_to(M, y); cr.line_to(W - M, y); cr.stroke()
            for cells, rh in rows:
                cr.rectangle(M + 1.2, y + 1.3, 3.2, 3.2); cr.set_line_width(0.25); cr.stroke()
                x = M + cols[0][1]
                for lines, (_, cw) in zip(cells, cols[1:]):
                    for k, l in enumerate(lines):
                        text(cr, l, x + 1, y + 3.8 + k * 3.0, 2.3)
                    x += cw
                y += rh
                cr.set_line_width(0.1); cr.move_to(M, y); cr.line_to(W - M, y); cr.stroke()
            doc.next()

        doc.surf.finish()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({total} pages)")


if __name__ == "__main__":
    main()
