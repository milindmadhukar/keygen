---
created: 2026-03-09
updated: 2026-10-22T17:00
name: 05 - pcb design
---

> [!success] Decision (2026-10-19)
> KiCad 10, **one project** (`pcb/keygen.kicad_pro`) with left and right sheets, and both halves in one board file as **two separate outlines**, each ordered on its own. Key geometry comes from **Redox rev1**; the copper is drawn new. Kailh MX hotswap sockets, 1N4148 through-hole diodes, SK6812MINI-E per-key LEDs on the battery through a MOSFET LED power switch, an EC11 encoder and an SSD1306 OLED module on each half, and a LiPo with a slide switch driving a P-MOSFET battery switch. The nice!nano mounts socketed on the underside and provides USB-C. Ground fill stays off each controller's antenna end. Lion Circuits (Bengaluru), HASL, black mask with white silkscreen, 5 + 5 boards. Status 2026-10-20: schematic generated and ERC clean; **PCB fully routed, DRC clean with schematic parity**. See [[12 - final design#Schematic]] and [[12 - final design#Controller pin map]].

## Board at a glance

| | |
|---|---|
| Tool | KiCad 10, with its `pcbnew` Python module and `kicad-cli` |
| Project | `pcb/keygen.kicad_pro`: top sheet plus `left` (refs 1xx) and `right` (refs 2xx) sub-sheets |
| Outline | One half is 160.2 × 126.0 mm. The bottom edge runs along the bottom row, flat, then along the thumb keys at 30° |
| Stackup | 2 layers, FR-4 1.6 mm, 1 oz copper, HASL, black soldermask, white silkscreen |
| Footprints | marbastlib (MX hotswap, EC11, nice!nano) and Keebio-Parts, as git submodules in `lib/` |
| Mounting | 5 M2 holes per half, placed where nothing else is |
| Rules | 0.25 mm signal, 0.4 mm power, 0.2 mm clearance, 0.15 mm minimum track, 0.2 mm copper-to-edge |

## Key matrix

Each half is **5 rows × 7 columns, COL2ROW**: each switch connects to its column, and its diode's cathode connects to its row. The controller drives one column at a time and reads which rows see it. The diode per key stops current flowing backwards through other pressed keys, so any combination of keys reads correctly.

- 33 keys per half. Each half's encoder push switch sits in its matrix at row 0 / column 6, so each half has 34 diodes. The left switches and diodes are SW101–SW106 / D101–D106 and SW108–SW134 / D108–D134.
- Rows run on the front copper and columns on the back.

**Reference:** [GOLEM Keyboard Matrix Guide](https://golem.hu/guide/keyboard-matrix/)

## Parts on the board

### Diodes
**1N4148, through-hole (DO-35)**, on the back, standing beside each switch. The band (cathode) goes toward the square pad, which is the row side. Through-hole is quick to hand-solder.

### Hotswap sockets
**Kailh MX hotswap (CPG151101S11)** on the back. Switches press in and pull out without soldering. One per key: 66 in total.

### Per-key RGB: SK6812MINI-E
- Reverse-mount on the back, shining up through a window under each switch. Each half has 33 windows (about 3.5 × 3.2 mm) that the fab mills; the LED pads sit about 0.25 mm from them.
- One daisy chain per half: data runs from the controller (P0.06, a full-speed pin) through every LED in turn.
- **Power:** the LED rail runs from the battery (B+) through an AO3401A P-MOSFET switch, turned on from P0.08 through an AO3400A N-MOSFET. A 10 µF and a 100 nF capacitor sit at the switch's output, next to it on the back between the battery connector and the board edge.
- **Current:** 12 mA per colour, so 36 mA per LED at full white, about 1.2 A for 33 LEDs. Brightness is capped in firmware. Each LED draws about 1 mA even when dark, which the LED power switch removes.
- The datasheet's VDD range is 3.7–5.5 V; the cell supplies 3.0–4.2 V and sits near 4.2 V on USB power, when the LEDs light. See [[12 - final design#Schematic]].

### Rotary encoders
**EC11** with a push switch and a 20 mm D shaft on each half, through-hole on the front, below the controller, mirrored: shafts at (167.0, 134.5) left and (256.5, 134.5) right, in board coordinates. Each takes a 17 × 13 mm knurled aluminium knob, whose edge sits 10 mm below the OLED, 5.7 mm from the thumb cluster's top key and 9.1 mm from the G/H column. On both halves A is on P0.10 (pad 23) and B on P0.09 (pad 24), both NFC pins used as GPIO. Each push switch is in its half's matrix at row 0 / column 6, with its own 1N4148 (D107, D207) on the back beside the encoder.

### OLED
A generic **0.96 in. 128×64 SSD1306 I2C module** per half (J101 / J201), on a 1×4 2.54 mm header footprint, pin order GND, VCC, SCL, SDA. SDA is on P0.17 (pad 5), SCL on P0.20 (pad 6), and power on the controller's switched 3.3 V VCC (pad 16). The module's own header pins solder straight into the board on their 2.5 mm spacer, over the lower (antenna) end of the controller, above the knob: right x 242–269.5, y 88–116; left x 154–181.5, y 88–116. Its nearest keycap gap is 4.6 mm on either half. Details: [[12 - final design#OLED]].

### Power
- **Battery:** JST-PH 2-pin side-entry connector (BT101/BT201) on the back. A "+" on the silkscreen marks the + pad.
- **Battery switch:** the MSK12C02 slide switch (top edge, lever out) drives the gate of an **AO3401A P-MOSFET** (source on the battery, drain on B+), with a 1 MΩ resistor holding the gate off between positions.
- **Reset:** a 6 mm button on the back, labelled GENERATE, mirrored between the halves. Double-tap enters the bootloader.

## Routing

The board is generated and routed by the scripts in `tools/` of the repo, so every step reruns:

1. `gen_pcb.py` places every footprint from the schematic using Redox's KLE positions, draws the outline and picks the mounting holes.
2. `trim_outline.py` runs the bottom edge along the bottom row and the thumb keys.
3. `route_pcb.py` routes signals with **Freerouting** (about 85%), leaving ground to the fill.
4. `finish_route.py`, a custom grid maze router, finishes what Freerouting leaves.
5. `smooth_route.py` straightens tracks into 0/45/90° runs.
6. `stitch_gnd.py` adds ground stitching vias (about 280); `cleanup_pcb.py` removes dangling copper.
7. `sync_pcb.py` relinks footprints to the schematic.
8. `silkscreen_art.py` writes the black-mask stackup and the silkscreen artwork.

Ground is a fill on both layers of each half, kept out from under each controller's antenna end by keep-out areas that survive every re-pour.

## Checks

- `kicad-cli pcb drc --schematic-parity`: 0 errors, 0 unconnected, 0 parity issues. Only cosmetic silkscreen warnings remain.
- `tools/check_schematic.py`: KiCad ERC plus a netlist comparison against the design tables.
- `tools/check_datasheets.py`: the routed board against each part's datasheet. See [[15 - datasheet audit]].

## Fabrication

- **Lion Circuits** (Bengaluru): 5–6 days, no customs, 6/6 mil capability on 1 oz copper.
- Order [`keygen-left-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-left-gerbers.zip) and [`keygen-right-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-right-gerbers.zip) (the [build release](https://github.com/milindmadhukar/keygen/releases/tag/build)) as **two orders of 5**: bare boards, 2 layers, 1.6 mm, HASL lead-free. Everything is hand-soldered.
- Raise with the fab: the LED windows must be milled, and the LED pads sit close to them. Settings: `fab/ORDER.md`. Assembly BOM: `fab/BOM.md`.

## Related Notes
- [[02 - layout design]] for key positions
- [[03 - microcontroller selection]] for the controller and its pins
- [[04 - firmware options]] for ZMK
- [[06 - split architecture]] for how the halves connect
- [[08 - electronics & components]] for the full component list
- [[10 - assembly & build guide]] for soldering order

## Resources

- [Keyboard PCB Guide by Ruiqi Mao](https://github.com/ruiqimao/keyboard-pcb-guide)
- [ai03 PCB Designer Guide](https://wiki.ai03.me/books/pcb-design/chapter/pcb-designer-guide)
- [GOLEM PCB Design Guide](https://golem.hu/article/make-keyboard-pcb/)
- [How to Build a Custom Keyboard From Scratch | Part 1](https://www.youtube.com/watch?v=IJxuzyO9b8M) and [Part 2, KiCad](https://www.youtube.com/watch?v=fYNxG8RwpaE)

### Video Notes
- [[Designing Keyboard PCBs with KiCad]] — the KiCad workflow: schematic, footprints, matrix, layout, routing, edge cuts, Gerbers, order
- [[I Built My DREAM Keyboard from Scratch - Modular]] — KiCad with KB Placer and a KLE import, and choosing controller pins by function
