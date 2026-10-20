# Keygen

A one-off wireless split keyboard built on the [Redox](https://github.com/mattdibi/redox-keyboard)
layout: 66 QWERTY keys (Redox minus its inner column), a 2×2 + 1.25u thumb cluster per hand,
one rotary encoder on the right, per-key RGB + underglow and no screen. Two nRF52840
controllers (nice!nano v2) are hidden on the PCB underside and run ZMK, connecting over
Bluetooth or USB-C to the host and over Bluetooth or a TRRS cable between halves.

![Keygen, top](docs/render-top.png)
![Keygen, underside](docs/render-bottom.png)

- `plan/index.html` — the build plan: layout drawing, connectivity, parts, pin budget,
  firmware notes, build steps, checklist, references. Open it in a browser.
- `pcb/keygen.kicad_pro` — the KiCad 10 project. One schematic (top sheet with `left` and `right`
  sub-sheets; refs 1xx / 2xx) and, later, one PCB carrying both halves joined by snap-off tabs. The
  schematics are generated: edit the tables in `tools/gen_schematic.py`, run it, then run
  `tools/check_schematic.py` (KiCad ERC + a netlist check that every connection matches the tables).
  `pcb/keygen-schematic.pdf` is the printable version.
- PCB pipeline (each step is a script in `tools/`, run in this order):
  `gen_pcb.py` (place footprints, outline, holes) → `route_pcb.py` (Freerouting, ground left to the
  pour) → `finish_route.py` (grid maze router for whatever Freerouting leaves; `--include-gnd`,
  `--pads-to-ground REF.PAD`) → `stitch_gnd.py` / `cleanup_pcb.py` (ground stitching, dangling copper)
  → `sync_pcb.py` (relink to the schematic). `kicad-cli pcb drc --schematic-parity` is the judge.
- `lib/` — git submodules: marbastlib (MX hotswap, nice!nano, MSK12C02 footprints) and
  Keebio-Parts (PJ-320A). Clone with `git clone --recursive`.
- `bom/bom.csv` — bill of materials with Indian and import sources. Edit it, then run
  `tools/render_bom.py` to regenerate `plan/bom.html` and the vault note `13 - bill of materials.md`.
- `notes/` — symlink to the project notes in the Obsidian vault
  (`~/Documents/Obsidian Vault/01 - Projects/Hardware & Electronics/Keygen Custom Keyboard`).
  `notes/12 - final design.md` is the source of truth. The link only resolves on this machine.

Redox is © 2018 Mattia Dal Ben, MIT licensed.
