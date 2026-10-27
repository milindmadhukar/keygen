#!/usr/bin/env python3
"""Draw each half's OLED screens, pixel for pixel, by running the firmware's own screen code.

The screens are plain C on a 128 x 64, 1-bit framebuffer (firmware/module/src/ui). This builds them
with the PC's C compiler into firmware/module/sim/kg_sim.c, which plays scripted scenes through
them, and turns the frames into:

    assets/oled-left.svg, oled-right.svg   the state in the renders: both halves on USB power, the
                                           left connected to Bluetooth profile 1, on the Base layer
                                           (tools/gen_blend.py reads them for the Blender scene)
    assets/oled-boot-left.gif, oled-boot-right.gif   the boot animation on each half
    assets/oled-left.gif, oled-right.gif   the status screens through layers, modifiers, caps lock,
                                           a profile change, USB and a lost link
    assets/oled-light-menu.gif             the lighting menu on the right half

    python3 tools/render_oled.py
"""
import re, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "firmware/module/src/ui"
SIM = ROOT / "firmware/module/sim/kg_sim.c"
W, H = 128, 64
PIXEL = "#F2F4F6"                        # a white OLED
GLASS = "#050506"
# The panel: 128 x 64 over a 21.7 x 10.9 mm active area, square pixels on a 0.17 mm pitch, each lit
# over about 90 % of it. The GIFs draw a pixel as 9 of every 10 GIF pixels, unlit ones as the glass.
SCALE, LIT, BORDER = 10, 9, 4            # GIF pixels per OLED pixel, lit of them, OLED pixels of glass
GIFS = ["boot-left", "boot-right", "left", "right", "light-menu"]


def frames(path):
    """[(ms, 64 rows of 128 pixels, 1 lit)] from a kg_sim .frames file."""
    data, out = path.read_bytes(), []
    for i in range(0, len(data), 2 + W * H // 8):
        ms = data[i] | data[i + 1] << 8
        fb = data[i + 2:i + 2 + W * H // 8]
        out.append((ms, [[fb[y * W // 8 + x // 8] >> (7 - x % 8) & 1 for x in range(W)] for y in range(H)]))
    return out


def svg(px):
    """The lit pixels as one rect per horizontal run, on the black glass."""
    rects = []
    for y, row in enumerate(px):
        x = 0
        while x < W:
            if row[x]:
                e = x
                while e < W and row[e]: e += 1
                rects.append(f'<rect x="{x}" y="{y}" width="{e - x}" height="1"/>')
                x = e
            else:
                x += 1
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 -4 {W + 8} {H + 8}" width="{(W + 8) * 4}" '
            f'height="{(H + 8) * 4}" shape-rendering="crispEdges">\n'
            f'<rect x="-4" y="-4" width="{W + 8}" height="{H + 8}" rx="2" fill="{GLASS}"/>\n'
            f'<g fill="{PIXEL}">\n' + "\n".join(rects) + "\n</g>\n</svg>\n")


def read_svg(path):
    """The pixels back from an SVG written by svg(): 64 rows of 128, 1 lit."""
    px = [[0] * W for _ in range(H)]
    for x, y, w in re.findall(r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="1"/>', path.read_text()):
        for i in range(int(x), int(x) + int(w)):
            px[int(y)][i] = 1
    return px


def gif(scene, path):
    """The scene as an animated GIF at the panel's 2:1, each lit pixel a square with the panel's gap."""
    from PIL import Image
    hexrgb = lambda c: tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    palette = [*hexrgb(GLASS), *hexrgb(PIXEL)]
    cell, lit = SCALE, LIT
    size = ((W + 2 * BORDER) * cell, (H + 2 * BORDER) * cell)
    images, durations = [], []
    for ms, px in scene:
        if images and px == images[-1][0]:
            durations[-1] += ms
            continue
        img = Image.new("P", size, 0)
        img.putpalette(palette)
        for y, row in enumerate(px):
            for x, on in enumerate(row):
                if on:
                    x0, y0 = (x + BORDER) * cell, (y + BORDER) * cell
                    img.paste(1, (x0, y0, x0 + lit, y0 + lit))
        images.append((px, img))
        durations.append(ms)
    first, *rest = [img for _, img in images]
    first.save(path, save_all=True, append_images=rest, duration=durations, loop=0, optimize=False,
               disposal=1)


def main():
    with tempfile.TemporaryDirectory(prefix="kg-oled-") as tmp:
        exe = Path(tmp) / "kg_sim"
        sources = [SIM, *sorted(UI.glob("kg_*.c"))]
        subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", f"-I{UI}", "-o", exe,
                        *sources, "-lm"], check=True)
        subprocess.run([exe, tmp], check=True)
        for side in ("left", "right"):
            out = ROOT / f"assets/oled-{side}.svg"
            out.write_text(svg(frames(Path(tmp) / f"still-{side}.frames")[-1][1]))
            print(f"wrote {out.relative_to(ROOT)}")
        for name in GIFS:
            out = ROOT / f"assets/oled-{name}.gif"
            gif(frames(Path(tmp) / f"{name}.frames"), out)
            print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
