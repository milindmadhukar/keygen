---
created: 2026-10-22
name: 16 - hardware reference
tags:
  - keyboards
  - pcb
  - case
updated: 2026-10-22T19:00
---
# Hardware Reference

> [!info] Reference
> The electronics, the PCB, the switch plate, the case and the silkscreen artwork, in detail. The design as a whole is [[12 - final design]]; the assembly steps are `INSTRUCTIONS.md` in the repo. Renders of the board, case and plate are in the repo's `assets/`.

## Electronics

- **Matrix:** 5 rows × 7 columns per half, COL2ROW, with a 1N4148 diode per key. Each half's
  encoder push switch sits in its matrix at row 0 / column 6.
- **Controller pins:** both halves use the same pin map, with every edge pin in use. LED data is on
  P0.06 and the LED power switch on P0.08. The OLED's I2C is on P0.17 (SDA) and P0.20 (SCL), both
  full-speed pins. The encoder is on P0.10 and P0.09, the NFC pins, set up as GPIOs in firmware.
  The full pin table is in the build plan (`plan/index.html`).
- **OLED:** a generic 0.96 in. SSD1306 module per half, its own header pins soldered into the board
  (pin order GND, VCC, SCL, SDA), standing in a window in the plate. It sits over the controller's
  lower end with its header along its bottom edge, and the firmware turns the image 180°. It runs
  from the controller's switched 3.3 V output (VCC), which the firmware keeps on through P0.13.
- **Power and charging:** each half has its own LiPo and charges through its own controller's
  USB-C at about 100 mA, roughly a day for an empty cell; a 1-to-2 USB-C cable charges both from
  one charger.
- **Battery switch:** the MSK12C02 slide switch drives the gate of an AO3401A P-MOSFET, which
  carries the battery current: source on the battery, drain on B+. A 1 MΩ resistor holds the gate
  off between positions. Leave the switch on while charging.
- **Battery:** a 505080 LiPo pouch (5 × 50 × 80 mm, about 2500 mAh) with a protection board, as
  the controller has no over-discharge cut-off. It lies in a bay sunk 1 mm into the case floor,
  which takes up to a 60 × 88 mm cell with a 6.1 mm installed height envelope, under the outer
  and middle key columns, its lead end towards
  the battery connector. With a 6.1 mm installed battery stack, it clears assumed 2 mm underside
  parts by 2.9 mm at rest and 1.4 mm at full gasket travel, and stays at least 15 mm from the
  controller's antenna end.
- **LED power:** the LEDs run from the battery (B+) through an AO3401A P-MOSFET, whose gate an
  AO3400A N-MOSFET on P0.08 pulls low to turn them on. 100 kΩ resistors hold both MOSFETs off, and
  a 10 µF + 100 nF pair sits at the switch's output.
- **Antenna:** each controller's antenna end is kept clear of the ground fill, and the case is
  plastic.

## Parts per half

References and soldering notes for every part are in `fab/BOM.md`.

| Part | Left | Right |
|---|---|---|
| nRF52840 controller (socketed, underside) | 1 | 1 |
| Akko V3 Lavender Purple Pro switch + Kailh hotswap socket | 33 | 33 |
| 1N4148 diode (DO-35) | 34 | 34 |
| SK6812MINI-E RGB LED | 33 | 33 |
| 10 µF + 100 nF capacitors, 1206 (LED rail) | 1 + 1 | 1 + 1 |
| 505080 LiPo battery + JST-PH connector | 1 | 1 |
| MSK12C02 power slide switch | 1 | 1 |
| AO3401A P-MOSFET + 1 MΩ gate resistor, 1206 (battery switch) | 1 + 1 | 1 + 1 |
| AO3401A P-MOSFET, AO3400A N-MOSFET, 2 × 100 kΩ, 1206 (LED power switch) | 1 + 1 + 2 | 1 + 1 + 2 |
| 6 mm reset button | 1 | 1 |
| EC11 encoder (20 mm D shaft) + knob | 1 | 1 |
| 0.96 in. SSD1306 OLED module, I2C | 1 | 1 |

## PCB

- **Routed and DRC clean.** DRC with schematic parity shows 0 errors, 0 warnings, 0 unconnected
  items and 0 parity issues.
- **Rules:** 0.25 mm signal and 0.4 mm power traces, 0.2 mm clearance, 0.15 mm minimum track,
  0.2 mm copper-to-edge. That is within Lion Circuits' 6/6 mil capability.
- **Routing:** Freerouting does most of the signal routing, then a custom grid maze router
  finishes the rest. All tracks are then straightened into 0/45/90° runs. Ground is a fill on both
  layers. [`pcb-routing.png`](https://github.com/milindmadhukar/keygen/releases/download/media/pcb-routing.png) shows both copper layers.
- **Datasheet audit:** `tools/check_datasheets.py` checks the routed
  board against each part's datasheet: pinouts, orientations, nRF52840 pin restrictions, the battery
  path, antenna clearance and the current budget. The datasheets are in
  `docs/datasheets/`.

## Plate and case

- **Gasket mount:** the plate and PCB are tied together by M2 × 3 mm standoffs on 0.5 mm shims and touch the
  case only through Poron strips (12 × 4 × 3 mm, cut from 80 × 4 × 3 mm strips), one above and
  one below each of the plate's 8 tabs per half. Closing the case squeezes each strip by 1.0 mm, a third of it.
- **Plate:** black FR-4, 1.5 mm, CNC-routed from sheet. 14 × 14 mm cut-outs following each key's
  rotation, a 15 × 15 mm encoder cut-out and a 29.5 × 30 mm OLED window per half, and the PCB's M2
  holes. Plate screws go in at H102, H103, H105, H202 and H204; the other five standoffs are
  screwed from below only.
- **Case:** the bottom shell and top frame are screwed together from below with 8 M2 × 16 screws
  per half, up through the walls into heat-set inserts in blind holes in the top frame's underside,
  none within 15 mm of the controller's antenna end. The heads sit 3 mm up in counterbores in the
  floor; the top frame has no holes on top. The PCB top sits 14.6 mm
  above the desk and the plate top 19.6 mm.
- **Top frame deck:** level with the frame's rim, 4.0 mm above the plate top, covering the plate
  everywhere but the keycaps (1.2 mm clear of each, the windows chamfered 0.4 mm at the deck top),
  the OLED window and the encoder. The OLED window opens out towards the thumbs; the glass sits
  3.9 mm below the deck top. The encoder bushing passes through a 9 mm hole under the knob; a 15 mm
  square recess above the encoder body provides 0.6 mm nominal headroom at the tallest published
  body height. The knob underside is 5.1 mm above the deck at the tallest published bushing height.
- **Foam:** per half, the switch pads and two foam layers, the layers cut from the files in
  `case/foam/` (DXF or SVG).
  - Poron ring switch pads, 0.5 mm, ready-made: a square ring about 18 mm across with a 14.2 mm
    open middle, notched on the clip sides, one stuck on the PCB round each switch. Seven rings
    per half have a corner snipped off round a standoff.
  - EVA plate foam, 2 mm, on the switch pads under the plate, with the plate's switch, encoder and
    OLED cut-outs (switches 14.4 mm) and holes for the pads and standoffs. Up to 2.8 mm fits.
  - EVA case foam, 5 mm, on the case floor round the battery bay, the controller, the
    battery connector, the slide switch, the reset tube and the encoder and OLED pins. It sits
    3.0 mm below the parts under the PCB at rest and 1.5 mm below at full gasket travel.
- **Openings:** an open 20 mm USB-C slot and a 9 × 3.4 mm power switch slot on the top edge, with
  the wall thinned to 1.5 mm in front of them, and a 2 mm reset pinhole in the floor with a guide
  tube up to the button.
- **Fit check:** `tools/gen_case.py` checks every case part against the PCB, the plate, the
  controller, the reset button, the battery, the OLED, the encoder, the knob, the plate screw heads
  and the keycaps at the bottom of their travel (an 18.4 mm skirt, a recessed stem and the plate
  shifted 0.5 mm in its pockets); each foam layer against the parts beside it; and a 5.5 mm cell and
  the case foam against the parts under the PCB with the stack pressed 1.5 mm down onto its gaskets.
  It finds no overlaps.

- **Printed parts:** the bottom shells have the battery bays, the gasket ledges, the counterbored
  screw holes, the USB-C and power switch openings and the reset guide tube; the top frames have the
  matching gasket pockets, blind heat-set insert holes in their underside, and a deck round the
  keycaps with an OLED window and a hole for the encoder. The floor is flat, with the reset pinhole
  and the screw counterbores.

## Silkscreen artwork

Keygen is named after *Keygen* by Martin Garrix, released on his label STMPD RCRDS. The cover
shows a keygen.exe window: a "MARTIN GARRIX" title bar, an outlined KEYGEN logo in a starfield
beside a crescent moon, a serial number, and a GENERATE button between two STMPD emblems. The
silkscreen reuses those pieces:

| Where | What |
|---|---|
| Top, left half | The window, upright beside the controller: title bar, the KEYGEN logo as KEY over GEN in a star cloud, moon, the cover's serial `5233-5131-4927-406`, a stacked frame behind |
| Top, right half | A crescent moon and the STMPD emblem beside the right encoder |
| Underside, both halves | GENERATE between two STMPD emblems under each reset button. Double-tapping reset enters the bootloader |
| Underside, left half | The KEYGEN logo, `github.com/milindmadhukar/keygen` and the revision, in a column under GENERATE |
| Underside, right half, bottom edge | KEYGEN REV 0.1 over DESIGNED BY MILIND MADHUKAR |
| Underside, right half | A small keygen.exe window: "press GENERATE twice to flash firmware" |
| Everywhere else, both faces | Stars, on any free board area, with a few denser clouds |

![The bare PCB from above](https://github.com/milindmadhukar/keygen/releases/download/media/render-bare-top.png)

![The bare PCB from below](https://github.com/milindmadhukar/keygen/releases/download/media/render-bare-bottom.png)

`tools/silkscreen_art.py` draws all of it, keeping it 0.25 mm clear
of pads and holes and 0.5 mm inside the board edge, and writes the board stackup (black mask,
white silkscreen, HASL). The letters use a small stroke font defined in the script. The STMPD
emblem is the label's own vector artwork, included as a fan's nod on a one-off board; it remains
the label's mark.

## Related notes

- [[12 - final design]]: the design as a whole
- [[05 - pcb design]]: the PCB
- [[09 - case design]]: the case
- [[14 - case & plate requirements]]: what the case and plate must fit
- [[15 - datasheet audit]]: the PCB checked against each datasheet
- [[17 - building from source]]: the scripts that generate all of it
