#!/usr/bin/env python3
"""The case-mounted EC11 in local coordinates around one shaft: a section drawing, a STEP
assembly, and a printable 30 mm coupon of the frame's boss for checking the delivered encoder.

The dimensions are in docs/encoder-mount.md; the production parts come from gen_case.py.

    ~/.venvs/keygen-cad/bin/python tools/mock_encoder_mount.py
"""
from pathlib import Path

from build123d import Align, Box, Color, Compound, Cylinder, Pos, RegularPolygon, extrude, export_step, export_stl

import gen_models


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "case/mockup/encoder-mount-assembled.step"
PANEL_STL = ROOT / "case/mockup/encoder-panel-test.stl"
SVG = ROOT / "assets/encoder-mount-mockup.svg"
Z = (Align.CENTER, Align.CENTER, Align.MIN)


def part(shape, name, rgb):
    shape.label = name
    shape.color = Color(rgb)
    return shape


def write_svg():
    """Draw the same nominal z stack as a readable section and plan view."""
    S = 10.5
    def x(v): return 330 + v * S
    def z(v): return 470 - v * S
    def rect(x0, x1, z0, z1, fill, stroke="none", extra=""):
        return (f'<rect x="{x(x0):.1f}" y="{z(z1):.1f}" width="{(x1-x0)*S:.1f}" '
                f'height="{(z1-z0)*S:.1f}" fill="{fill}" stroke="{stroke}" {extra}/>')

    a = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="650" viewBox="0 0 1200 650">',
         '<style>text{font-family:DejaVu Sans,Arial,sans-serif;fill:#e9eef2} .sub{fill:#aab6c2;font-size:16px} '
         '.label{font-size:17px} .small{font-size:14px} .hair{stroke:#aab6c2;stroke-width:1.5;fill:none} </style>',
         '<rect width="1200" height="650" fill="#101820"/>',
         '<text x="42" y="49" font-size="27" font-weight="bold">Case-mounted EC11</text>',
         '<text x="42" y="76" class="sub">Nominal section through the shaft · dimensions in mm · fixed parts blue, floating parts green</text>',
         '<text x="30" y="115" class="label">SIDE SECTION</text>']
    # Fixed deck, its downward boss relieved only for the M7 bushing, and the cheeks beside the body.
    for lo, hi in ((-15, -3.65), (3.65, 15)):
        a.append(rect(lo, hi, 7, 9, "#49718e"))
    for lo, hi in ((-7.5, -3.65), (3.65, 7.5)):
        a.append(rect(lo, hi, 6.5, 7, "#49718e"))
    for lo, hi in ((-7.45, -6.25), (6.25, 7.45)):
        a.append(rect(lo, hi, 4.5, 6.5, "#49718e"))
    # Floating plate and PCB; their openings are larger than the case-mounted body and pins.
    for lo, hi in ((-15, -9), (9, 15)):
        a.append(rect(lo, hi, 3.5, 5, "#5ea7a1"))
    for lo, hi in ((-15, -9), (9, 15)):
        a.append(rect(lo, hi, -1.6, 0, "#317d63"))
    a.append(rect(-6, 6, 0, 6.5, "#777e85", "#c4cbd0"))
    a.append(rect(-3.5, 3.5, 6.5, 13.5, "#a3aab0"))
    a.append(rect(-3, 3, 13.5, 25.5, "#c2c8cc"))
    for cx in (-5, -2.5, 0, 2.5, 5):
        a.append(rect(cx-.45, cx+.45, -3.5, 0, "#c69e61"))
    a.append(rect(-5.75, 5.75, 9, 9.3, "#d8dcdd"))
    a.append(rect(-5, 5, 9.3, 11.3, "#d0d3d4"))
    # The aluminium knob is translucent in section so the shortened shaft can be seen.
    a.append(rect(-8.5, 8.5, 14.5, 27.5, "#d9e0e3", "#f5f7f8", 'opacity="0.58"'))
    a.append(f'<line x1="{x(-15)}" y1="{z(9)}" x2="{x(15)}" y2="{z(9)}" stroke="#b7c8d2" stroke-width="2"/>')
    # Each label sits level with its part, joined to it by a short leader.
    for pz, px, label in ((22, -8.5, "17 mm knob"), (10.3, -5, "M7 nut, washer"), (8, -15, "2.5 mm boss"),
                          (4.25, -15, "18 × 18 plate"), (-.8, -15, "18 × 20 PCB")):
        y = z(pz)
        a.append(f'<path class="hair" d="M {34 + len(label) * 8} {y:.1f} L {x(px):.1f} {y:.1f}"/>')
        a.append(f'<text x="30" y="{y + 5:.1f}" class="small">{label}</text>')
    for pz, px, lines in ((22, 8.5, ("Hub on the shaft's D flat",)),
                          (13.7, 8.5, ("2.4 mm gap to the nut", "when pushed 0.8 mm")),
                          (5.5, 7.45, ("Cheeks stop the body", "turning with the knob")),
                          (2, 6, ("Body clear of the plate", "and PCB as they float")),
                          (-2.5, 5.45, ("Five leads, to the header", "under the PCB"))):
        y = z(pz)
        a.append(f'<path class="hair" d="M {x(px):.1f} {y:.1f} L 492 {y:.1f}"/>')
        a += [f'<text x="498" y="{y + 5 + i * 18:.1f}" class="small">{line}</text>' for i, line in enumerate(lines)]
    a += [
          '<line x1="705" y1="114" x2="705" y2="550" stroke="#34434d" stroke-width="2"/>',
          '<text x="747" y="115" class="label">TOP VIEW AT SHAFT</text>',
          '<rect x="785" y="148" width="190" height="190" rx="3" fill="none" stroke="#5ea7a1" stroke-width="4"/>',
          '<rect x="790" y="143" width="180" height="200" rx="3" fill="none" stroke="#317d63" stroke-width="3" stroke-dasharray="9 6"/>',
          '<circle cx="880" cy="243" r="75" fill="#49718e" opacity=".6"/>',
          '<rect x="820" y="184.5" width="120" height="117" rx="5" fill="#777e85" stroke="#c4cbd0" stroke-width="2"/>',
          '<circle cx="880" cy="243" r="35" fill="#a3aab0"/>',
          '<circle cx="880" cy="243" r="57.5" fill="none" stroke="#e3e7e8" stroke-width="3"/>',
          '<text x="995" y="176" class="small">plate 18 × 18</text>',
          '<text x="995" y="204" class="small">PCB 18 × 20</text>',
          '<text x="995" y="232" class="small">boss Ø15</text>',
          '<text x="995" y="260" class="small">body 12 × 11.7</text>',
          '<text x="747" y="391" class="label">FIVE-WIRE CONNECTION</text>',
          '<rect x="745" y="414" width="205" height="111" rx="10" fill="#2e3942" stroke="#6f8797"/>',
          '<text x="764" y="448" class="small">EC11 A · C · B</text>',
          '<text x="764" y="476" class="small">push S1 · S2</text>',
          '<text x="764" y="505" class="small">case fixed</text>',
          '<path d="M 950 464 C 984 402, 1006 547, 1040 467" fill="none" stroke="#f0b65e" stroke-width="5"/>',
          '<rect x="1040" y="433" width="120" height="85" rx="10" fill="#245a48" stroke="#6bc3a2"/>',
          '<text x="1052" y="463" class="small">1×5 header</text>',
          '<text x="1052" y="490" class="small">PCB floats</text>',
          '<text x="42" y="607" class="sub">The encoder is fixed to the top frame; the plate and PCB float round it. Its lead plugs into J102 / J202 on the back of the PCB.</text>',
          '</svg>']
    SVG.write_text("\n".join(a) + "\n")
    print(f"wrote {SVG.relative_to(ROOT)}")


def main():
    # Heights use the production PCB top as z=0. The body remains at its current height.
    deck = Pos(0, 0, 7.0) * Box(30, 30, 2.0, align=Z)
    boss = Pos(0, 0, 6.5) * Cylinder(7.5, 2.5, align=Z)
    cheeks = Pos(-6.85, 0, 4.5) * Box(1.2, 9, 2.6, align=Z) + Pos(6.85, 0, 4.5) * Box(1.2, 9, 2.6, align=Z)
    panel = (deck + boss + cheeks) - Pos(0, 0, 6.4) * Cylinder(3.65, 2.7, align=Z)

    plate = Pos(0, 0, 3.5) * Box(30, 30, 1.5, align=Z)
    plate -= Pos(0, 0, 3.4) * Box(18, 18, 1.7, align=Z)
    pcb = Pos(0, 0, -1.6) * Box(30, 30, 1.6, align=Z)
    pcb -= Pos(0, 0, -1.7) * Box(18, 20, 1.8, align=Z)

    body = Pos(0, 0, 0) * Box(12, 11.7, 6.5, align=Z)
    bushing = Pos(0, 0, 6.5) * Cylinder(3.5, 7.0, align=Z)
    # The selected shaft's D flat begins at z=16.5. The assumed knob hub begins 2 mm
    # above its skirt, so the skirt starts at z=14.5 to put the bore on the flat.
    shaft_round = Pos(0, 0, 13.5) * Cylinder(3, 3.0, align=Z)
    shaft_flat = Pos(0, 0, 16.5) * Cylinder(3, 9.0, align=Z)
    shaft_flat &= Pos(-1.5, 0, 16.5) * Box(6, 6, 9, align=(Align.MIN, Align.CENTER, Align.MIN))
    shaft = shaft_round + shaft_flat
    encoder = body + bushing + shaft
    # Approximate solder tails; exact lead shape and harness clearance need a physical fit test.
    tails = []
    for x in (-2.5, 0, 2.5):
        tails.append(Pos(x, -7.5, -3.5) * Box(1, 1, 3.5, align=Z))
    for x in (-2.5, 2.5):
        tails.append(Pos(x, 7.0, -3.5) * Box(1, 1, 3.5, align=Z))

    washer = Pos(0, 0, 9.0) * Cylinder(5.75, 0.3, align=Z)
    washer -= Pos(0, 0, 8.9) * Cylinder(3.55, 0.5, align=Z)
    nut = Pos(0, 0, 9.3) * extrude(RegularPolygon(10 / 3**0.5, 6), 2.0)
    nut -= Pos(0, 0, 9.2) * Cylinder(3.5, 2.2, align=Z)
    knob = gen_models.knob() - Cylinder(3.75, 2.0, align=Z)
    knob = Pos(0, 0, 14.5) * knob

    shapes = [part(panel, "fixed top deck with M7 boss", 0x39434E),
              part(plate, "floating switch plate with 18 mm opening", 0xAABFC6),
              part(pcb, "floating PCB with 18 x 20 mm opening", 0x267560),
              part(encoder, "EC11 body bushing and shortened shaft", 0x676D75),
              part(washer, "supplied washer", 0xD2D5D8),
              part(nut, "supplied M7 nut", 0xBBC0C4),
              part(knob, "17 mm knob", 0xB7BCC3)]
    shapes.extend(part(t, f"lead {i}", 0xC6A26B) for i, t in enumerate(tails, 1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    export_step(Compound(children=shapes), str(OUT))
    export_stl(panel, str(PANEL_STL), tolerance=0.02, angular_tolerance=0.2)
    write_svg()
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"wrote {PANEL_STL.relative_to(ROOT)}")
    print("pushed-knob to nut clearance, nominal: 2.4 mm")
    print("shaft cut with 11 mm blind bore and 2 mm recessed hub, nominal: 1.0 mm")
    print("body bottom z=0; moving PCB is relieved around its body and pins")


if __name__ == "__main__":
    main()
