#!/usr/bin/env python3
"""Write the OLED screens' pixel fonts and icons, drawn below as text, into the firmware as C.

The screens (firmware/module/src/ui/) are 1-bit, 128 x 64, and draw everything themselves: two
pixel fonts (5 x 7 for text, 3 x 5 for small labels) and the icons. Each glyph or icon is a block of
rows, '#' lit and '.' dark. The fonts cover space to '_' in ASCII; lower case draws as upper case.

    python3 tools/gen_oled_assets.py   # firmware/module/src/ui/kg_assets.{c,h}
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "firmware/module/src/ui"

# 5 x 7, one space between glyphs. Digits are all 5 wide so numbers keep their width.
FONT5 = """
' ' ... ... ... ... ... ... ...
'!' # # # # # . #
'"' #.# #.# ... ... ... ... ...
'#' .#.#. ##### .#.#. .#.#. .#.#. ##### .#.#.
'%' ##..# ##..# ...#. ..#.. .#... #..## #..##
'\\'' # # . . . . .
'(' ..# .#. #.. #.. #.. .#. ..#
')' #.. .#. ..# ..# ..# .#. #..
'*' ..... #.#.# .###. ##### .###. #.#.# .....
'+' ..... ..#.. ..#.. ##### ..#.. ..#.. .....
',' .. .. .. .. .. .# #.
'-' .... .... .... #### .... .... ....
'.' . . . . . . #
'/' ....# ...#. ...#. ..#.. .#... .#... #....
'0' .###. #...# #..## #.#.# ##..# #...# .###.
'1' ..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.
'2' .###. #...# ....# ...#. ..#.. .#... #####
'3' ##### ...#. ..#.. ...#. ....# #...# .###.
'4' ...#. ..##. .#.#. #..#. ##### ...#. ...#.
'5' ##### #.... ####. ....# ....# #...# .###.
'6' ..##. .#... #.... ####. #...# #...# .###.
'7' ##### ....# ...#. ..#.. .#... .#... .#...
'8' .###. #...# #...# .###. #...# #...# .###.
'9' .###. #...# #...# .#### ....# ...#. .##..
':' . # . . . # .
';' .. .# .. .. .. .# #.
'<' ...# ..#. .#.. #... .#.. ..#. ...#
'=' .... .... #### .... #### .... ....
'>' #... .#.. ..#. ...# ..#. .#.. #...
'?' .###. #...# ....# ...#. ..#.. ..... ..#..
'@' .#. #.# .#. ... ... ... ...
'A' .###. #...# #...# ##### #...# #...# #...#
'B' ####. #...# #...# ####. #...# #...# ####.
'C' .###. #...# #.... #.... #.... #...# .###.
'D' ####. #...# #...# #...# #...# #...# ####.
'E' ##### #.... #.... ####. #.... #.... #####
'F' ##### #.... #.... ####. #.... #.... #....
'G' .###. #...# #.... #.### #...# #...# .####
'H' #...# #...# #...# ##### #...# #...# #...#
'I' ### .#. .#. .#. .#. .#. ###
'J' ..### ...#. ...#. ...#. #..#. #..#. .##..
'K' #...# #..#. #.#.. ##... #.#.. #..#. #...#
'L' #.... #.... #.... #.... #.... #.... #####
'M' #...# ##.## #.#.# #.#.# #...# #...# #...#
'N' #...# #...# ##..# #.#.# #..## #...# #...#
'O' .###. #...# #...# #...# #...# #...# .###.
'P' ####. #...# #...# ####. #.... #.... #....
'Q' .###. #...# #...# #...# #.#.# #..#. .##.#
'R' ####. #...# #...# ####. #.#.. #..#. #...#
'S' .#### #.... #.... .###. ....# ....# ####.
'T' ##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..
'U' #...# #...# #...# #...# #...# #...# .###.
'V' #...# #...# #...# #...# #...# .#.#. ..#..
'W' #...# #...# #...# #.#.# #.#.# #.#.# .#.#.
'X' #...# #...# .#.#. ..#.. .#.#. #...# #...#
'Y' #...# #...# .#.#. ..#.. ..#.. ..#.. ..#..
'Z' ##### ....# ...#. ..#.. .#... #.... #####
'[' ### #.. #.. #.. #.. #.. ###
']' ### ..# ..# ..# ..# ..# ###
'_' ..... ..... ..... ..... ..... ..... #####
"""

# 3 x 5, one space between glyphs
FONT3 = """
' ' .. .. .. .. ..
'%' #.# ..# .#. #.. #.#
'+' ... .#. ### .#. ...
'-' ... ... ### ... ...
'.' . . . . #
'/' ..# ..# .#. #.. #..
'0' ### #.# #.# #.# ###
'1' .#. ##. .#. .#. ###
'2' ##. ..# .#. #.. ###
'3' ##. ..# .#. ..# ##.
'4' #.# #.# ### ..# ..#
'5' ### #.. ##. ..# ##.
'6' .## #.. ### #.# ###
'7' ### ..# .#. .#. .#.
'8' ### #.# ### #.# ###
'9' ### #.# ### ..# ##.
':' . # . # .
'<' ..# .#. #.. .#. ..#
'>' #.. .#. ..# .#. #..
'@' .#. #.# .#. ... ...
'A' .#. #.# ### #.# #.#
'B' ##. #.# ##. #.# ##.
'C' .## #.. #.. #.. .##
'D' ##. #.# #.# #.# ##.
'E' ### #.. ##. #.. ###
'F' ### #.. ##. #.. #..
'G' .## #.. #.# #.# .##
'H' #.# #.# ### #.# #.#
'I' ### .#. .#. .#. ###
'J' ..# ..# ..# #.# .#.
'K' #.# #.# ##. #.# #.#
'L' #.. #.. #.. #.. ###
'M' #.# ### ### #.# #.#
'N' ##. #.# #.# #.# #.#
'O' .#. #.# #.# #.# .#.
'P' ##. #.# ##. #.. #..
'Q' .#. #.# #.# ##. .##
'R' ##. #.# ##. #.# #.#
'S' .## #.. .#. ..# ##.
'T' ### .#. .#. .#. .#.
'U' #.# #.# #.# #.# ###
'V' #.# #.# #.# #.# .#.
'W' #.# #.# ### ### #.#
'X' #.# #.# .#. #.# #.#
'Y' #.# #.# .#. .#. .#.
'Z' ### ..# .#. #.. ###
"""

ICONS = {
    # the Bluetooth rune
    "bt": """
        ..#..
        ..##.
        #.#.#
        .###.
        ..#..
        .###.
        #.#.#
        ..##.
        ..#..
    """,
    "check": """
        ......#
        .....##
        #...##.
        ##.##..
        .###...
        ..#....
    """,
    "cross": """
        #...#
        .#.#.
        ..#..
        .#.#.
        #...#
    """,
    "bolt": """
        ...##
        ..##.
        .##..
        #####
        ..##.
        .##..
        ##...
    """,
    # the link between the halves: two arrows
    "link": """
        ......#..
        .......#.
        #########
        .........
        #########
        .#.......
        ..#......
    """,
    "shift": """
        ...#...
        ..#.#..
        .#...#.
        ##...##
        .#...#.
        .#...#.
        .#####.
    """,
    "ctrl": """
        .......
        ...#...
        ..###..
        .##.##.
        ##...##
        #.....#
        .......
    """,
    "alt": """
        .......
        ##..###
        ..#....
        ...#...
        ....#..
        .....##
        .......
    """,
    "super": """
        ###.###
        ###.###
        ###.###
        .......
        ###.###
        ###.###
        ###.###
    """,
    "left": """
        ..#
        .##
        ###
        .##
        ..#
    """,
    "right": """
        #..
        ##.
        ###
        ##.
        #..
    """,
}


# the boot animation's logo, drawn in outline: these letters, 1 apart, at 2x
LOGO = "KEYGEN"
LOGO_LETTERS = {
    "K": "##....## ##...##. ##..##.. ##.##... ####.... ####.... ##.##... ##..##.. ##...##. ##....##",
    "E": ".####### ######## ##...... ##...... ######.. ######.. ##...... ##...... ######## .#######",
    "Y": "##....## ##....## .##..##. ..####.. ...##... ...##... ...##... ...##... ...##... ...##...",
    "G": ".######. ######## ##...... ##...... ##..#### ##..#### ##....## ##....## ######## .######.",
    "N": "##....## ###...## ####..## ####..## ##.##.## ##.##.## ##..#### ##..#### ##...### ##....##",
}


def logo_rows():
    letters = [LOGO_LETTERS[c].split() for c in LOGO]
    rows = [".".join(l[j] for l in letters) for j in range(len(letters[0]))]
    return ["".join(c * 2 for c in r) for r in rows for _ in range(2)]


def rows_of(text):
    return [r.strip() for r in text.strip().splitlines() if r.strip()]


def pack(rows):
    """Rows of '#'/'.' as bytes, MSB first, ceil(width / 8) bytes a row."""
    out = []
    for r in rows:
        for i in range(0, len(r), 8):
            chunk = r[i:i + 8].ljust(8, ".")
            out.append(sum(1 << (7 - j) for j, c in enumerate(chunk) if c == "#"))
    return out


def font(name, table, height):
    glyphs = {}
    for line in table.strip().splitlines():
        ch, rest = line[1:].split("' ", 1) if not line.startswith("'\\''") else ("'", line[5:])
        ch = ch.replace("\\\\", "\\")
        rows = rest.split()
        if len(rows) != height or len({len(r) for r in rows}) != 1:
            raise SystemExit(f"gen_oled_assets: {name} {ch!r}: {len(rows)} rows of {[len(r) for r in rows]}")
        glyphs[ch] = rows
    first, last = 32, 95
    widths, bits = [], []
    for code in range(first, last + 1):
        rows = glyphs.get(chr(code))
        if rows is None:                         # missing glyphs draw as a box
            rows = ["#" * 3] + ["#.#"] * (height - 2) + ["#" * 3]
        widths.append(len(rows[0]))
        bits += pack(rows)
    return (f"static const uint8_t {name}_widths[] = {{{', '.join(map(str, widths))}}};\n"
            f"static const uint8_t {name}_rows[] = {{\n{c_bytes(bits)}\n}};\n"
            f"const struct kg_font kg_{name} = {{.height = {height}, .first = {first}, .count = {last - first + 1}, "
            f".widths = {name}_widths, .rows = {name}_rows}};\n")


def c_bytes(values, per_line=16):
    return "\n".join("    " + ", ".join(f"0x{v:02x}" for v in values[i:i + per_line]) + ","
                     for i in range(0, len(values), per_line))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    head = "/* Generated by tools/gen_oled_assets.py; edit the drawings there. */\n"
    c = [head, '#include "kg_assets.h"\n\n', font("font5", FONT5, 7), "\n", font("font3", FONT3, 5), "\n"]
    h = [head, "#pragma once\n\n#include \"kg_gfx.h\"\n\n",
         "extern const struct kg_font kg_font5, kg_font3;\n"]
    for name, art in [*ICONS.items(), ("logo", "\n".join(logo_rows()))]:
        rows = rows_of(art)
        if len({len(r) for r in rows}) != 1:
            raise SystemExit(f"gen_oled_assets: icon {name}: uneven rows")
        c.append(f"static const uint8_t icon_{name}_rows[] = {{\n{c_bytes(pack(rows))}\n}};\n"
                 f"const struct kg_bitmap kg_icon_{name} = {{.w = {len(rows[0])}, .h = {len(rows)}, "
                 f".rows = icon_{name}_rows}};\n")
        h.append(f"extern const struct kg_bitmap kg_icon_{name};\n")
    (OUT / "kg_assets.c").write_text("".join(c))
    (OUT / "kg_assets.h").write_text("".join(h))
    print(f"wrote {(OUT / 'kg_assets.c').relative_to(ROOT)}, kg_assets.h")


if __name__ == "__main__":
    main()
