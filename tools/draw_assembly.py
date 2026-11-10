#!/usr/bin/env python3
"""Draw the standoff and switch-pad assembly figures from the board and case_geometry.py:

assets/assembly-standoffs.svg     how a shim, standoff and screw go on at a mounting hole, and the
                                  fitted section under the plate, to scale
assets/assembly-switch-pads.svg   peeling a Poron ring off its sheet, where it goes round a switch
                                  (from a real key, with a diode's joints under it and a standoff
                                  beside another), and the section through the plate-to-PCB gap

The sizes and counts come from case_geometry.py and the PCB, so the figures follow the design.

    python3 tools/draw_assembly.py
"""
import math, sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
LED_WINDOW = (3.4, 3.0)          # the LED's window through the PCB (fab/ORDER.md)
BUTTON_HEAD = (3.5, 1.1)         # ISO 7380 M2 head: diameter, height (gen_case.py)
STANDOFF_HOLE = 2.2              # the plate's hole over each standoff
FOAM_STANDOFF_HOLE = C.STANDOFF_D + 2 * C.FOAM_HOLE_CLEAR + 1.0   # the plate foam's, and the ring's snipped corner

STYLE = """
  <style>
    text { font-family: DejaVu Sans, Arial, sans-serif; fill: #182234; }
    .title { font-size: 27px; font-weight: 700; }
    .head { font-size: 19px; font-weight: 700; }
    .lab { font-size: 16px; }
    .small { font-size: 14px; }
    .num { font-size: 17px; font-weight: 700; fill: #fff; }
    .white { fill: #fff; }
    .plate { fill: #acd6e5; stroke: #315b73; stroke-width: 2; }
    .ghost { fill: #acd6e5; fill-opacity: 0.35; stroke: #315b73; stroke-width: 1.5; stroke-dasharray: 6 4; }
    .pcb { fill: #397765; stroke: #174a3c; stroke-width: 2; }
    .copper { fill: #c98a3c; }
    .bare { fill: #5f9a87; }
    .eva { fill: #626a76; stroke: #454c57; stroke-width: 1.5; }
    .ring { fill: #4b505b; stroke: #2b2f36; stroke-width: 1.5; }
    .liner { fill: #39b8d8; stroke: #1f7f99; stroke-width: 1.5; }
    .brass { fill: #d9a143; stroke: #8a5c16; stroke-width: 2; }
    .screw { fill: #8592a6; stroke: #344054; stroke-width: 2; }
    .switch { fill: #bd9ecb; stroke: #6a4879; stroke-width: 2; }
    .hole { fill: #f8fafc; stroke: #174a3c; stroke-width: 1.5; }
    .joint { fill: #c8ccd2; stroke: #6b7280; stroke-width: 1.5; }
    .led { fill: #f8fafc; stroke: #174a3c; stroke-width: 1.5; }
    .outline { fill: none; stroke: #6a4879; stroke-width: 1.5; stroke-dasharray: 6 4; }
    .axis { stroke: #a0acba; stroke-width: 1.5; stroke-dasharray: 5 5; fill: none; }
    .dim { stroke: #182234; stroke-width: 1.2; fill: none; }
    .lead { stroke: #182234; stroke-width: 1.2; fill: none; }
    .arrow { stroke: #c2410c; stroke-width: 3; fill: none; marker-end: url(#tip); }
    .cut { stroke: #c2410c; stroke-width: 2.5; fill: none; }
    .tool { fill: #b8c0cc; stroke: #4b5563; stroke-width: 1.5; }
    .badge { fill: #c2410c; }
    .note { fill: #e7eef6; }
    .no { stroke: #b91c1c; stroke-width: 4; fill: none; }
  </style>
  <defs>
    <marker id="tip" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 Z" fill="#c2410c"/>
    </marker>
  </defs>"""


def svg(w, h, title, desc, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">\n'
            f'  <title id="title">{title}</title>\n  <desc id="desc">{desc}</desc>{STYLE}\n'
            f'  <rect width="{w}" height="{h}" fill="#f8fafc"/>\n' + "\n".join("  " + b for b in body) + "\n</svg>\n")


def text(x, y, s, cls="lab", anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}"{a}>{s}</text>'


def lines(x, y, rows, cls="lab", step=21):
    return [text(x, y + i * step, r, cls) for i, r in enumerate(rows)]


def rect(x0, y0, x1, y1, cls, rx=0):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
    r = f' rx="{rx}"' if rx else ""
    return f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" class="{cls}"{r}/>'


def badge(x, y, n):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" class="badge"/>' + text(x, y + 6, str(n), "num", "middle")


def path(d, cls):
    return f'<path d="{d}" class="{cls}"/>'


def vdim(x, y0, y1, label, side=1):
    """A vertical dimension line from y0 to y1 at x, its label beside it."""
    t = 6
    return [path(f"M{x - t} {y0:.1f} H{x + t} M{x - t} {y1:.1f} H{x + t} M{x} {y0:.1f} V{y1:.1f}", "dim"),
            text(x + 10 * side, (y0 + y1) / 2 + 5, label, "small", None if side > 0 else "end")]


# ---------------------------------------------------------------- the board


def board_data():
    """For each switch of the left half (the right is its mirror): the diode joints near it, those
    under its ring's band, and the standoffs its ring meets, in the switch's own frame seen from the
    front (LED window down)."""
    b = pcbnew.LoadBoard(str(ROOT / "pcb/keygen.kicad_pcb"))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    mm = lambda v: (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y))
    holes = [mm(f.GetPosition()) for r, f in fps.items() if r.startswith("H1")]
    diode_pads = [(mm(p.GetPosition()), pcbnew.ToMM(p.GetSizeX())) for r, f in fps.items()
                  if r.startswith("D1") for p in f.Pads()]
    half, band = C.SWITCH_PAD / 2, C.SWITCH_PAD_BAND
    keys = []
    for ref in sorted(r for r in fps if r.startswith("SW1") and "SW_MX" in fps[r].GetFPIDAsString()):
        f = fps[ref]; cx, cy = mm(f.GetPosition())
        a = math.radians(f.GetOrientationDegrees() - 180.0)

        def local(p):
            dx, dy = p[0] - cx, p[1] - cy
            return (dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))

        joints = [(local(q), d) for q, d in diode_pads]
        joints = [j for j in joints if max(abs(c) for c in j[0]) < half + 3]
        under = [j for j in joints if max(abs(j[0][0]), abs(j[0][1])) < half + j[1] / 2
                 and max(abs(j[0][0]), abs(j[0][1])) > half - band - j[1] / 2]
        near = [local(q) for q in holes if max(abs(c) for c in local(q)) < half + FOAM_STANDOFF_HOLE / 2]
        keys.append(dict(ref=ref, joints=joints, under=under, standoffs=near))
    return keys




# ---------------------------------------------------------------- standoffs


def standoffs_svg():
    W, H = 1200, 790
    body = [text(35, 45, "Standoffs: a shim, a standoff and a screw at each mounting hole", "title"),
            text(35, 75, "H101–H105 and H201–H205, all ten the same. Fit them once the board is soldered and tested, "
                         "before the switch pads.", "lab"),
            text(40, 130, "Fit it", "head"), text(640, 130, "Fitted, to scale (30 px per mm)", "head")]

    # left: the three parts, exploded along the screw's axis
    cx, s = 400, 22                                                   # the axis, px per mm (widths only)
    pt, pb = 430, 466                                                 # the PCB's top and bottom
    bare = 1.1 + 3.0                                                  # copper-free round each hole
    body.append(path(f"M{cx} 160 V700", "axis"))
    body += [rect(cx - 7 * s, pt, cx + 7 * s, pb, "pcb", 3)]
    for y in (pt - 4, pb):
        body += [rect(cx - 7 * s, y, cx - bare * s, y + 4, "copper"), rect(cx + bare * s, y, cx + 7 * s, y + 4, "copper"),
                 rect(cx - bare * s, y, cx + bare * s, y + 4, "bare")]
    body += [rect(cx - 1.1 * s, pt - 4, cx + 1.1 * s, pb + 4, "hole"),
             text(cx - 7 * s + 8, pt + 24, "PCB, front up", "lab white"),
             *lines(cx - 7 * s, pb + 30, ["no copper round the hole,", "on both faces"], "small", 18)]
    ty0, ty1 = 180, 270                                               # the standoff
    body += [rect(cx - C.STANDOFF_D / 2 * s, ty0, cx + C.STANDOFF_D / 2 * s, ty1, "brass", 3),
             path(f"M{cx - 1.0 * s} {ty0 + 6} V{ty1 - 6} M{cx + 1.0 * s} {ty0 + 6} V{ty1 - 6}", "axis"),
             path(f"M{cx + 80} {ty1 + 10} V{345}", "arrow"),
             badge(60, ty0 + 10, 2),
             *lines(85, ty0 + 16, [f"M2 × {C.STANDOFF_L:g} mm standoff", "on the shim; hold it", "with your fingers"], "small", 18)]
    sy = 360                                                          # the shim
    body += [rect(cx - C.SHIM_D / 2 * s, sy, cx + C.SHIM_D / 2 * s, sy + 10, "brass", 2),
             rect(cx - 1.1 * s, sy - 1, cx + 1.1 * s, sy + 11, "hole"),
             path(f"M{cx + 80} {sy + 18} V{pt - 12}", "arrow"),
             badge(60, sy + 5, 1),
             *lines(85, sy + 11, [f"{C.SHIM_T:g} mm shim on the", "front, centred on", "the hole"], "small", 18)]
    hy = 640                                                          # the screw's head
    body += [rect(cx - 1.0 * s, hy - 100, cx + 1.0 * s, hy, "screw"),
             rect(cx - BUTTON_HEAD[0] / 2 * s, hy, cx + BUTTON_HEAD[0] / 2 * s, hy + 26, "screw", 10),
             path(f"M{cx + 80} {hy + 10} V{pb + 14}", "arrow"),
             badge(60, hy - 10, 3),
             *lines(85, hy - 4, [f"M2 × {C.SCREW_L:g} button head,", "up from the back with", "the 1.3 mm hex key:",
                                 "snug, not hard"], "small", 18)]
    body += lines(40, 735, ["Done when the shim doesn't spin and the standoff doesn't rock.",
                            "Nothing screws into the standoffs from above."], "small", 19)

    # right: the fitted section, to scale
    s, ax, y0 = 30, 820, 500                                          # px per mm, the axis, the PCB's top
    Y = lambda z: round(y0 - z * s, 1)
    X = lambda x: round(ax + x * s, 1)
    xl, xr = X(-5.5), X(6.0)
    pb_ = C.PLATE_BOT
    into = min(C.SCREW_L - C.PCB_T - C.SHIM_T, C.STANDOFF_L)
    tip = C.STANDOFF_L - into
    fh = FOAM_STANDOFF_HOLE / 2
    body += [path(f"M{xl} {Y(0)} H{xr} M{xl} {Y(pb_)} H{xr}", "axis"),
             rect(xl, Y(0), xr, Y(-C.PCB_T), "pcb", 2),
             rect(X(-STANDOFF_HOLE / 2), Y(0), X(STANDOFF_HOLE / 2), Y(-C.PCB_T), "hole"),
             rect(xl, Y(C.PLATE_FOAM_Z[0]), X(-fh), Y(C.PLATE_FOAM_Z[1]), "eva"),
             rect(X(fh), Y(C.PLATE_FOAM_Z[0]), xr, Y(C.PLATE_FOAM_Z[1]), "eva"),
             rect(xl, Y(pb_), X(-STANDOFF_HOLE / 2), Y(pb_ + C.PLATE_T), "plate", 2),
             rect(X(STANDOFF_HOLE / 2), Y(pb_), xr, Y(pb_ + C.PLATE_T), "plate", 2),
             rect(X(-C.SHIM_D / 2), Y(0), X(C.SHIM_D / 2), Y(C.SHIM_T), "brass", 2),
             rect(X(-C.STANDOFF_D / 2), Y(C.SHIM_T), X(C.STANDOFF_D / 2), Y(C.SHIM_T + C.STANDOFF_L), "brass", 3),
             rect(X(-1.0), Y(-C.PCB_T), X(1.0), Y(C.SHIM_T + into), "screw"),
             rect(X(-BUTTON_HEAD[0] / 2), Y(-C.PCB_T), X(BUTTON_HEAD[0] / 2), Y(-C.PCB_T - BUTTON_HEAD[1]), "screw", 8),
             text(xl + 8, Y(-C.PCB_T) - 15, f"PCB, {C.PCB_T:g} mm", "lab white"),
             text(xr + 12, Y(pb_ + C.PLATE_T / 2) + 5, f"plate, {C.PLATE_T:g} mm (later)", "small"),
             text(xr + 12, Y(sum(C.PLATE_FOAM_Z) / 2) + 5, "plate foam (later)", "small"),
             path(f"M{X(C.STANDOFF_D / 2)} {Y(1.1)} H{xr + 8}", "lead"),
             text(xr + 12, Y(1.1) + 5, f"{C.STANDOFF_L:g} mm standoff", "small"),
             path(f"M{X(C.SHIM_D / 2)} {Y(C.SHIM_T / 2)} H{xr + 8}", "lead"),
             text(xr + 12, Y(C.SHIM_T / 2) + 5, f"{C.SHIM_T:g} mm shim", "small"),
             path(f"M{X(BUTTON_HEAD[0] / 2)} {Y(-C.PCB_T - BUTTON_HEAD[1] / 2)} H{xr + 8}", "lead"),
             text(xr + 12, Y(-C.PCB_T - BUTTON_HEAD[1] / 2) + 5, f"M2 × {C.SCREW_L:g} button head", "small"),
             *vdim(X(-6.2), Y(0), Y(pb_), f"{pb_:g} mm", -1)]
    body += lines(640, 640, [f"The screw fills {into:.1f} mm of the standoff's {C.STANDOFF_L:g} mm thread and stops",
                             f"{tip:.1f} mm under its top. The plate goes on later: it only rests on",
                             "the standoffs, and the switches hold it to the PCB."], "small", 19)
    desc = (f"How to fit each of the ten mounting-hole stacks: a {C.SHIM_T:g} millimetre shim on the PCB's front over the "
            f"hole, an M2 by {C.STANDOFF_L:g} standoff on it, and an M2 by {C.SCREW_L:g} button-head screw driven up "
            f"from the back into the standoff. The section shows the {pb_:g} millimetre gap they make under the plate.")
    return svg(W, H, "Fitting the standoffs at the mounting holes", desc, body)


# ---------------------------------------------------------------- switch pads


def ring_path(X, Y):
    """The ring seen from the front, as one evenodd path: a rounded square outside, a square inside
    with a notch on each clip side (top and bottom)."""
    o, b, r = C.SWITCH_PAD / 2, C.SWITCH_PAD_BAND, C.SWITCH_PAD_R
    i = o - b; nw, nd = C.SWITCH_PAD_NOTCH
    outer = (f"M{X(-o + r)} {Y(-o)} H{X(o - r)} Q{X(o)} {Y(-o)} {X(o)} {Y(-o + r)} V{Y(o - r)} "
             f"Q{X(o)} {Y(o)} {X(o - r)} {Y(o)} H{X(-o + r)} Q{X(-o)} {Y(o)} {X(-o)} {Y(o - r)} V{Y(-o + r)} "
             f"Q{X(-o)} {Y(-o)} {X(-o + r)} {Y(-o)} Z")
    inner = (f"M{X(-i)} {Y(-i)} H{X(-nw / 2)} V{Y(-i - nd)} H{X(nw / 2)} V{Y(-i)} H{X(i)} V{Y(i)} "
             f"H{X(nw / 2)} V{Y(i + nd)} H{X(-nw / 2)} V{Y(i)} H{X(-i)} Z")
    return f'<path d="{outer} {inner}" fill-rule="evenodd" class="ring"/>'


def footprint(X, Y, s):
    """The switch's five holes and the LED window, seen from the front."""
    out = [f'<circle cx="{X(0)}" cy="{Y(0)}" r="{3.99 / 2 * s:.1f}" class="hole"/>']
    out += [f'<circle cx="{X(x)}" cy="{Y(0)}" r="{1.75 / 2 * s:.1f}" class="hole"/>' for x in (-5.08, 5.08)]
    out += [f'<circle cx="{X(x)}" cy="{Y(y)}" r="{3.0 / 2 * s:.1f}" class="hole"/>' for x, y in ((-3.81, -2.54), (2.54, -5.08))]
    w, h = LED_WINDOW
    out.append(rect(X(-w / 2), Y(5.08 - h / 2), X(w / 2), Y(5.08 + h / 2), "led"))
    return out


def key_view(k, ox, oy, s, reach, ring=True, clip=None):
    """A switch position on the PCB's front: board, holes, the diode joints, the ring."""
    X = lambda x: round(ox + x * s, 1); Y = lambda y: round(oy + y * s, 1)
    out = [rect(X(-reach), Y(-reach), X(reach), Y(reach), "pcb", 4), *footprint(X, Y, s)]
    out.append(rect(X(-7), Y(-7), X(7), Y(7), "outline"))
    if ring:
        r = ring_path(X, Y)
        out.append(f'<g clip-path="url(#{clip})">{r}</g>' if clip else r)
    # the diode joints on top, see-through where the ring lies over them
    out += [f'<circle cx="{X(x)}" cy="{Y(y)}" r="{d / 2 * s:.1f}" class="joint" fill-opacity="0.75" stroke-dasharray="4 3"/>'
            for (x, y), d in k["joints"] if abs(x) < reach - d / 2 and abs(y) < reach - d / 2]
    return out, X, Y


def switch_pads_svg(keys):
    W, H = 1200, 1010
    joints = [k for k in keys if k["under"]]
    standoff = [k for k in keys if k["standoffs"]]
    mid = C.SWITCH_PAD / 2 - C.SWITCH_PAD_BAND / 2                   # the middle of the band
    on_band = lambda k: min(abs(max(abs(c) for c in j[0]) - mid) for j in k["under"])
    snipped = lambda k: max(abs(c) for c in k["standoffs"][0])         # nearer: more of the corner snipped
    body = [text(35, 45, "Switch pads: a Poron ring round each switch, stuck on the PCB", "title"),
            text(35, 75, f"{len(keys)} per half on the front of the PCB, after the standoffs and before the plate. "
                         "Never on the plate.", "lab")]

    # 1: peel
    body += [badge(55, 120, 1), text(80, 126, "Peel", "head")]
    lx, ly, s = 50, 165, 4.2
    body.append(rect(lx, ly, lx + 300, ly + 205, "liner", 6))
    for r in range(2):
        for c in range(3):
            if (r, c) != (0, 2):
                cx, cy = lx + 55 + c * 95, ly + 55 + r * 95
                body.append(ring_path(lambda x, cx=cx: round(cx + x * s, 1), lambda y, cy=cy: round(cy + y * s, 1)))
    cx, cy = lx + 250, ly + 45                                        # the one being lifted, and the tweezers
    body.append(f'<g transform="rotate(-18 {cx} {cy})">'
                + ring_path(lambda x: round(cx + x * s, 1), lambda y: round(cy + y * s, 1)) + "</g>")
    body += [path(f"M{cx + 30} {cy - 32} L{cx + 105} {cy - 88} L{cx + 112} {cy - 80} L{cx + 38} {cy - 24} Z", "tool"),
             path(f"M{cx + 35} {cy - 23} L{cx + 112} {cy - 66} L{cx + 116} {cy - 57} L{cx + 41} {cy - 15} Z", "tool")]
    body += lines(45, 405, ["Lift each ring off the blue backing", "sheet with tweezers, by its outer edge.",
                            "The side that was on the sheet goes", "down on the PCB. Don't stretch it."], "small", 19)

    # 2: place, on a key with a diode's joints under the band
    k = min(joints, key=on_band)
    body += [badge(435, 120, 2), text(460, 126, "Place", "head")]
    view, X, Y = key_view(k, 590, 320, 12, 11.0)
    body += view
    i = C.SWITCH_PAD / 2 - C.SWITCH_PAD_BAND; nd = C.SWITCH_PAD_NOTCH[1]
    (jx, jy), jd = max(k["under"], key=lambda j: j[0][0])
    body += [path(f"M{X(0)} {Y(-i - nd / 2)} L{X(2.5)} {Y(-11.8)} H750", "lead"),
             text(760, Y(-11.8) + 5, "notch: on a clip side of the switch", "small"),
             path(f"M{X(4.2)} {Y(1.8)} L750 {Y(-2.2)}", "lead"),
             *lines(760, Y(-2.2) + 5, ["open middle: round the pins", "and the LED window"], "small", 18),
             path(f"M{X(jx) + jd / 2 * 12} {Y(jy)} L750 {Y(jy)}", "lead"),
             *lines(760, Y(jy) + 5, ["diode joints: trim them flush;", "the ring sits over them"], "small", 18),
             path(f"M{X(0)} {Y(i + nd / 2)} L{X(2.5)} {Y(11.8)} H750", "lead"),
             text(760, Y(11.8) + 5, "notch: the other clip side", "small")]
    body += lines(435, 495, [f"Shown: {k['ref']}, from the front. Dashed: where the switch's housing goes. Press the ring",
                             f"down all round. {len(joints)} of the {len(keys)} rings per half lie over a diode's joints."],
                  "small", 19)

    # 3: next to a standoff
    k2 = min(standoff, key=snipped); q = k2["standoffs"][0]
    body += [badge(55, 580, 3), text(80, 586, "Next to a standoff", "head")]
    s, fh = 20, FOAM_STANDOFF_HOLE / 2                               # zoomed in on the standoff
    win = (60, 625, 310, 985)
    ox = (win[0] + win[2]) / 2 - (q[0] + 2.5) * s; oy = (win[1] + win[3]) / 2 - (q[1] + 3.5) * s
    cut = lambda X, Y: (f"M{X(q[0]) + fh * s} {Y(q[1])} a{fh * s} {fh * s} 0 1 0 {-2 * fh * s} 0 "
                        f"a{fh * s} {fh * s} 0 1 0 {2 * fh * s} 0 Z")
    Xs = lambda x: round(ox + x * s, 1); Ys = lambda y: round(oy + y * s, 1)
    body.append(f'<clipPath id="snip"><path d="M0 0 H{W} V{H} H0 Z {cut(Xs, Ys)}" clip-rule="evenodd"/></clipPath>')
    body.append(f'<clipPath id="win">{rect(*win, "pcb", 6)}</clipPath>')
    view, X, Y = key_view(k2, ox, oy, s, 16, clip="snip")
    body.append('<g clip-path="url(#win)">' + "".join(view)
                + f'<clipPath id="bite"><path d="{cut(X, Y)}"/></clipPath><g clip-path="url(#bite)">'
                + ring_path(X, Y).replace('class="ring"', 'class="ring" fill-opacity="0.35" stroke-dasharray="3 3"') + '</g>'
                + f'<circle cx="{X(q[0])}" cy="{Y(q[1])}" r="{C.SHIM_D / 2 * s:.1f}" class="brass" fill-opacity="0.55"/>'
                + f'<circle cx="{X(q[0])}" cy="{Y(q[1])}" r="{C.STANDOFF_D / 2 * s:.1f}" class="brass" fill-opacity="0.55"/>'
                + f'<path d="{cut(X, Y)}" class="cut" stroke-dasharray="6 4"/></g>')
    body.append(rect(*win, "outline", 6).replace('class="outline"', 'class="dim"'))
    body += lines(330, 660, [f"Shown: part of {k2['ref']}. {len(standoff)} rings", "per half meet a standoff. Before",
                             "you peel one, snip the bite out", "along the dashed line, so it lies",
                             "flat beside the shim and clear of", "the plate foam's hole round the", "standoff."], "small", 19)

    # 4: the section through the gap
    body += [badge(615, 580, 4), text(640, 586, "In the gap, once the plate is on", "head")]
    s, cx, y0 = 20, 860, 860
    Y = lambda z: round(y0 - z * s, 1); X = lambda x: round(cx + x * s, 1)
    pb_ = C.PLATE_BOT; i = C.SWITCH_PAD / 2 - C.SWITCH_PAD_BAND; o = C.SWITCH_PAD / 2; fc = C.FOAM_SWITCH_CUT / 2
    xl, xr = X(-11.5), X(11.5)
    body += [path(f"M{xl} {Y(0)} H{xr} M{xl} {Y(pb_)} H{xr}", "axis"),
             rect(xl, Y(0), xr, Y(-C.PCB_T), "pcb", 3),
             rect(xl, Y(C.PLATE_FOAM_Z[0]), X(-fc), Y(C.PLATE_FOAM_Z[1]), "eva"),
             rect(X(fc), Y(C.PLATE_FOAM_Z[0]), xr, Y(C.PLATE_FOAM_Z[1]), "eva"),
             rect(xl, Y(pb_), X(-7), Y(pb_ + C.PLATE_T), "plate", 3), rect(X(7), Y(pb_), xr, Y(pb_ + C.PLATE_T), "plate", 3),
             rect(X(-6.4), Y(pb_ + C.PLATE_T + 1.3), X(6.4), Y(pb_ + C.PLATE_T), "switch", 4),
             rect(X(-7.8), Y(pb_ + C.PLATE_T), X(7.8), Y(pb_), "switch", 3),
             rect(X(-7), Y(pb_), X(7), Y(0), "switch", 4),
             path(f"M{X(-7)} {Y(pb_)} L{X(-7.6)} {Y(pb_ - 0.7)} L{X(-7)} {Y(pb_ - 1.0)} Z", "switch"),
             path(f"M{X(7)} {Y(pb_)} L{X(7.6)} {Y(pb_ - 0.7)} L{X(7)} {Y(pb_ - 1.0)} Z", "switch"),
             rect(X(-o), Y(0), X(-i), Y(C.PE_T), "ring"), rect(X(i), Y(0), X(o), Y(C.PE_T), "ring"),
             text(xl + 8, Y(-C.PCB_T) - 12, f"PCB, {C.PCB_T:g} mm", "lab white"),
             text(xl + 8, Y(pb_ + C.PLATE_T) + 26, "plate", "small"),
             text(xl + 8, Y(C.PLATE_FOAM_Z[1]) + 28, "plate foam", "small white"),
             text(X(0), Y(1.6), "switch", "lab", "middle"),
             path(f"M{X(o)} {Y(C.PE_T / 2)} H{xr + 8}", "lead"),
             text(xr + 12, Y(C.PE_T / 2) + 5, f"{C.PE_T:g} mm ring", "small"),
             *vdim(X(-10.6), Y(C.PE_T), Y(C.PLATE_FOAM_Z[0]), f"{C.PLATE_FOAM_Z[0] - C.PE_T:g} mm", 1)]
    nx, ny = X(9.0), Y(pb_ + C.PLATE_T)                               # not on the plate
    body += [rect(nx, ny - C.PE_T * s, nx + 40, ny, "ring"),
             path(f"M{nx - 6} {ny - 28} L{nx + 46} {ny + 6} M{nx + 46} {ny - 28} L{nx - 6} {ny + 6}", "no"),
             text(xr + 12, ny - 8, "not here", "small")]
    body += lines(615, 920, ["The ring lies on the PCB round the switch's housing, not under it,",
                             f"{C.PLATE_FOAM_Z[0] - C.PE_T:g} mm below the plate foam, so nothing presses the plate and PCB",
                             "apart. On the plate it would hold the switch's clips off the plate."], "small", 19)
    desc = (f"Four steps: peel each Poron ring off its blue backing sheet with tweezers; stick it on the PCB's front "
            f"round a switch's footprint, its notches on the switch's clip sides, over the diode joints; snip the "
            f"corner off a ring that meets a standoff; and a section with the {C.PE_T:g} millimetre ring on the PCB, "
            f"{C.PLATE_FOAM_Z[0] - C.PE_T:g} millimetre of air, and the plate foam under the plate.")
    return svg(W, H, "Sticking the switch pads on the PCB", desc, body)


def main():
    keys = board_data()
    for name, s in (("assembly-standoffs.svg", standoffs_svg()), ("assembly-switch-pads.svg", switch_pads_svg(keys))):
        (ASSETS / name).write_text(s)
        print(f"wrote assets/{name}")


if __name__ == "__main__":
    main()
