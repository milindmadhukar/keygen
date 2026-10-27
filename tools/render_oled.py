#!/usr/bin/env python3
"""Draw each half's OLED status screen into assets/oled-<left|right>.svg, pixel for pixel.

The firmware runs ZMK's built-in status screen (CONFIG_ZMK_DISPLAY) on a 128 x 64 SSD1306. The
labels are laid out as zmk/app/src/display/status_screen.c does: the output (or, on the right half,
the link to the left) top left, the battery top right, and on the left half the active layer
bottom left in the small font. The glyphs come from LVGL's own Montserrat 16 and 12 fonts in the
ZMK west workspace (firmware/build.sh fetches it into $KEYGEN_ZMK_WS, default ~/.cache/keygen-zmk),
placed as LVGL places them, kerning included, and lit where a glyph's 4-bit coverage is half or
more, as the 1-bit display does.

The state shown is the one in the renders: both halves on USB power (so the LEDs are lit and the
battery shows charging), the left half connected to Bluetooth profile 1, on the first layer. The
SVGs are the source for the OLEDs in the Blender scene (tools/gen_blend.py reads them).

    python3 tools/render_oled.py
"""
import os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WS = Path(os.environ.get("KEYGEN_ZMK_WS", Path.home() / ".cache/keygen-zmk"))
FONTS = WS / "modules/lib/gui/lvgl/src/font"
KEYMAP = ROOT / "firmware/keygen.keymap"
W, H = 128, 64
PIXEL = "#F2F4F6"                        # a white OLED

# LV_SYMBOL_* (lvgl/src/font/lv_symbol_def.h)
WIFI, USB, OK, CLOSE, CHARGE, KEYBOARD, BATTERY_FULL = (chr(c) for c in (
    0xF1EB, 0xF287, 0xF00C, 0xF00D, 0xF0E7, 0xF11C, 0xF240))


class Font:
    """An LVGL font in lv_font_conv's C format (plain 4 bpp bitmaps, tiny cmaps, kerning classes)."""

    def __init__(self, size):
        src = re.sub(r"/\*.*?\*/", "", (FONTS / f"lv_font_montserrat_{size}.c").read_text(), flags=re.S)
        array = lambda name: [int(v, 0) for v in re.search(rf"{name}\[\] = \{{(.*?)\}};", src, re.S)
                              .group(1).replace("\n", " ").split(",") if v.strip()]
        field = lambda name: int(re.search(rf"\.{name}\s*=\s*(-?\d+)", src).group(1))
        self.bitmap = array("glyph_bitmap")
        self.glyphs = [tuple(int(v) for v in m) for m in re.findall(
            r"\.bitmap_index = (\d+), \.adv_w = (\d+), \.box_w = (\d+), \.box_h = (\d+), "
            r"\.ofs_x = (-?\d+), \.ofs_y = (-?\d+)", src)]
        self.cmaps = []
        for m in re.finditer(r"\.range_start = (\d+), \.range_length = (\d+), \.glyph_id_start = (\d+),\s*"
                             r"\.unicode_list = (\w+)", src):
            start, length, gid = (int(v) for v in m.groups()[:3])
            lst = None if m.group(4) == "NULL" else array(m.group(4))
            self.cmaps.append((start, length, gid, lst))
        self.left, self.right = array("kern_left_class_mapping"), array("kern_right_class_mapping")
        self.pairs = [v - 256 if v > 127 else v for v in array("kern_class_values")]
        self.right_cnt, self.kern_scale = field("right_class_cnt"), field("kern_scale")
        self.line_height, self.base_line = field("line_height"), field("base_line")

    def gid(self, ch):
        cp = ord(ch)
        for start, length, gid, lst in self.cmaps:
            if start <= cp < start + length:
                if lst is None:
                    return gid + cp - start
                if cp - start in lst:
                    return gid + lst.index(cp - start)
        raise SystemExit(f"render_oled: {ch!r} (U+{cp:04X}) is not in the font")

    def advance(self, ch, nxt):
        """The glyph's advance in whole pixels, with the kerning to the next glyph (lv_font_fmt_txt.c)."""
        g = self.gid(ch)
        adv = self.glyphs[g][1]
        if nxt != "\0":
            l, r = self.left[g], self.right[self.gid(nxt)]
            if l and r:
                adv += (self.pairs[(l - 1) * self.right_cnt + r - 1] * self.kern_scale) >> 4
        return (adv + 8) >> 4

    def width(self, text):
        return sum(self.advance(c, n) for c, n in zip(text, text[1:] + "\0"))

    def draw(self, px, text, x, y):
        """Draw a label whose top left corner is at (x, y), as lv_draw_label does."""
        for c, n in zip(text, text[1:] + "\0"):
            index, _, bw, bh, ox, oy = self.glyphs[self.gid(c)]
            gx, gy = x + ox, y + (self.line_height - self.base_line) - bh - oy
            for i in range(bw * bh):              # 4 bpp, packed across rows, high nibble first
                byte = self.bitmap[index + i // 2]
                if (byte >> 4 if i % 2 == 0 else byte & 0xF) >= 8:
                    px[gy + i // bw][gx + i % bw] = 1
            x += self.advance(c, n)


def first_layer():
    return re.search(r'display-name = "([^"]+)"', KEYMAP.read_text()).group(1)


def screens():
    """{side: 64 rows of 128 pixels, 1 lit}."""
    if not FONTS.is_dir():
        raise SystemExit(f"render_oled: no LVGL fonts in {FONTS}; run firmware/build.sh to fetch ZMK")
    big, small = Font(16), Font(12)
    battery = f"{CHARGE} {BATTERY_FULL}"                                  # battery_status.c, on USB power
    labels = {
        "left": [(big, f"{WIFI} 1 {OK}", "top_left"),                  # output_status.c: BLE profile 1, connected
                 (big, battery, "top_right"),
                 (small, f"{KEYBOARD} {first_layer()}", "bottom_left")],  # layer_status.c
        "right": [(big, f"{WIFI} {OK}", "top_left"),                   # peripheral_status.c: linked to the left
                  (big, battery, "top_right")],
    }
    out = {}
    for side, items in labels.items():
        px = [[0] * W for _ in range(H)]
        for font, text, align in items:
            x = W - font.width(text) if align.endswith("right") else 0
            y = H - font.line_height if align.startswith("bottom") else 0
            font.draw(px, text, x, y)
        out[side] = px
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
            f'<rect x="-4" y="-4" width="{W + 8}" height="{H + 8}" rx="2" fill="#050506"/>\n'
            f'<g fill="{PIXEL}">\n' + "\n".join(rects) + "\n</g>\n</svg>\n")


def read_svg(path):
    """The pixels back from an SVG written by svg(): 64 rows of 128, 1 lit."""
    px = [[0] * W for _ in range(H)]
    for x, y, w in re.findall(r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="1"/>', path.read_text()):
        for i in range(int(x), int(x) + int(w)):
            px[int(y)][i] = 1
    return px


def main():
    for side, px in screens().items():
        out = ROOT / f"assets/oled-{side}.svg"
        out.write_text(svg(px))
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
