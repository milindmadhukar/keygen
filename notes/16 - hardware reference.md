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
  P0.06 and the LED boost's enable on P0.08. The OLED's I2C is on P0.17 (SDA) and P0.20 (SCL), both
  full-speed pins. The encoder is on P0.10 and P0.09, the NFC pins, set up as GPIOs in firmware.
  The full pin table is in the build plan (`plan/index.html`).
- **OLED:** a generic 0.96 in. SSD1306 module per half, held in the top frame on four pegs and
  plugged into a right-angle header in the board's 1×4 footprint (pin order GND, VCC, SCL, SDA),
  over a window in the plate. It sits over the controller's
  lower end with its header along its bottom edge, and the firmware turns the image 180°. It runs
  from the controller's switched 3.3 V output (VCC), which the firmware keeps on through P0.13.
- **Power and charging:** each half has its own LiPo and charges through its own controller's
  USB-C at about 300 mA (TP4054, with the controller's BOOST link bridged), about ten hours for an
  empty cell; a 1-to-2 USB-C cable charges both from one charger. On USB the controller and the
  OLED run from USB through the module's diode and P-MOSFET; the LED boost runs from B+, so bright
  white lighting can still draw more from the cell than the charger replaces. The battery level
  reads full while plugged in. With no battery fitted, the keys, OLED and Bluetooth run from USB
  and the lighting has no supply. Battery life has not been measured (see
  [`docs/logic-audit.md`](../docs/logic-audit.md)).
- **Battery switch:** the SK12D07VG5 right-angle slide switch drives the gate of an AO3401A
  P-MOSFET, which carries the battery current: source on the battery, drain on B+. A 1 MΩ resistor
  holds the gate at the source when the switch is off; the switch's pin 3 is unconnected. Leave the
  switch on while charging.
- **Battery:** a KP-355085 LiPo pouch (3.5 × 50 × 85 mm, listed 3000 mAh) with a protection board, as
  the controller has no over-discharge cut-off. It lies in a bay sunk 1.6 mm into the case floor,
  which takes up to a 60 × 88 mm cell with a 6.1 mm installed height envelope, under the outer
  and middle key columns, its lead end towards
  the battery connector. With a 6.1 mm installed battery stack, it clears assumed 2 mm underside
  parts by 4.4 mm at rest and 2.9 mm at full gasket travel, and stays at least 15 mm from the
  controller's antenna end.
- **LED power:** a TI TPS61023 synchronous boost (SOT-563, on pads 0.4 mm longer than KiCad's for
  hand soldering) turns B+ into a 4.95 V LED rail
  (LED_VDD), inside the SK6812MINI-E's 3.7–5.5 V over the whole charge. P0.08 drives its enable
  directly (ZMK's ext-power), and a 100 kΩ resistor holds it off while the controller boots or
  sleeps; shut down, the converter disconnects its output, so the rail sits at 0 V. A 1 µH, 1210
  inductor (TDK TMS322512ALM-1R0MTAA), 2 × 22 µF at the output, 10 µF at the input and a 732 kΩ /
  100 kΩ feedback divider complete it, laid out as the datasheet's example. Its switch limit is
  2.7–3.7 A.
- **LED data:** P0.06 drives an SN74LV1T125 single buffer beside the first LED, powered from the
  LED rail; its input threshold is 2.03 V at 5 V, so the controller's 3.3 V data drives the chain
  at 5 V, through a 330 Ω resistor into the first LED's DIN. Its inputs take 5.5 V with no supply,
  so the controller can't back-power the dark rail.
- **LED decoupling:** every LED has a 0805 100 nF footprint beside it; every fourth is fitted
  (LEDs 4, 8, … 32), the others are optional. A 10 µF capacitor sits beside the last LED.
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
| TPS61023 boost (SOT-563), 1 µH inductor (1210) | 1 + 1 | 1 + 1 |
| 22 µF capacitors, 1206 (boost output) | 2 | 2 |
| 10 µF capacitors, 1206 (boost input, last LED) | 2 | 2 |
| 732 kΩ + 2 × 100 kΩ resistors, 1206 (feedback, enable) | 1 + 2 | 1 + 2 |
| SN74LV1T125 buffer (SOT-23-5), 330 Ω resistor (0805) | 1 + 1 | 1 + 1 |
| 100 nF capacitors, 0805 (buffer, every fourth LED; 25 optional) | 9 | 9 |
| KP-355085 LiPo battery + JST-PH connector | 1 | 1 |
| SK12D07VG5 power slide switch | 1 | 1 |
| AO3401A P-MOSFET + 1 MΩ gate resistor, 1206 (battery switch) | 1 + 1 | 1 + 1 |
| 6 mm reset button | 1 | 1 |
| EC11 encoder (20 mm D shaft) + knob | 1 | 1 |
| 0.96 in. SSD1306 OLED module, I2C | 1 | 1 |

## PCB

- **Routed and DRC clean.** DRC with schematic parity shows 0 errors, 0 unconnected items and 0
  parity issues, with 3 silkscreen warnings.
- **Rules:** 0.25 mm signal and 0.4 mm power traces, 0.2 mm clearance (0.15 mm at the LED boost's
  0.5 mm-pitch pins), 0.15 mm minimum track, 0.2 mm copper-to-edge. That is within JLCPCB's
  2-layer capability.
- **Routing:** Freerouting does most of the signal routing, then a custom grid maze router
  finishes the rest. All tracks are then straightened into 0/45/90° runs. Ground is a fill on both
  layers, joined to every pad through thermal spokes so a hand iron heats the pad rather than the
  plane. Two spokes per pad at least, one on the LED, buffer and capacitor ground pads with room
  for only one (`pcb/keygen.kicad_dru`). [`pcb-routing.png`](https://github.com/milindmadhukar/keygen/releases/download/media/pcb-routing.png) shows both copper layers.
- **Datasheet audit:** `tools/check_datasheets.py` checks the routed
  board against each part's datasheet: pinouts, orientations, nRF52840 pin restrictions, the battery
  path, antenna clearance and the current budget. The datasheets are in
  `docs/datasheets/`.

## Plate and case

- **Gasket mount:** the plate and PCB are held together by the switches, spaced by M2 × 3 mm standoffs on
  0.5 mm shims, and touch the case only through Poron strips (12 × 4 × 3 mm, cut from 80 × 4 × 3 mm strips), one above and
  one below each of the plate's 8 tabs per half. Closing the case squeezes each strip by 1.0 mm, a third of it.
- **Plate:** clear polycarbonate, 1.5 mm, CNC-routed from sheet. 14 × 14 mm cut-outs following each key's
  rotation, an 18 × 18 mm encoder cut-out and a 29.5 × 29.8 mm OLED window per half, and the PCB's M2
  holes. Each standoff is screwed to the PCB from below with an M2 × 5 button head; nothing
  screws into it from above, and its top bears on the plate.
- **Case:** the bottom shell and top frame are screwed together from below with 8 M2 × 16 screws
  per half, up through the walls into heat-set inserts in blind holes in the top frame's underside,
  none within 15 mm of the controller's antenna end. The heads sit 4 mm up in counterbores in the
  floor; the top frame has no holes on top. The PCB top sits 15.5 mm
  above the desk and the plate top 20.5 mm.
- **Top frame deck:** level with the frame's rim, 4.0 mm above the plate top, covering the plate
  everywhere but the keycaps (1.2 mm clear of each, the windows chamfered 0.4 mm at the deck top),
  the OLED window and the encoder. The OLED window opens out towards the thumbs; the glass sits
  1.0 mm below the deck top, in a pocket under a 1.0 mm lip; the module sits on a boss under the
  deck, on four pegs through its holes, 0.5 mm clear of the floating plate's window. The encoder is fixed to the frame: its bushing passes through a
  7.3 mm hole in a Ø15 mm boss, 2.5 mm thick, two cheeks hold its body square, and its washer and M7
  nut clamp it from above. The shaft is cut 1.0 mm short so the knob's underside sits 5.5 mm above
  the deck, 2.4 mm over the nut when pushed, and its top 8.1 mm above the keycap tops.
- **Foam:** per half, the switch pads and two foam layers, the layers cut from the files in
  `case/foam/` (DXF or SVG).
  - Poron ring switch pads, 0.5 mm, ready-made: a square ring about 18 mm across with a 14.2 mm
    open middle, notched on the clip sides, one stuck on the PCB round each switch. Seven rings
    per half have a corner snipped off round a standoff.
  - EVA plate foam, 2 mm, taped to the plate's underside, 1.0 mm above the switch pads, with the
    plate's switch, encoder and OLED cut-outs (switches 14.4 mm, notched for the switch latches)
    and holes for the pads and standoffs. Up to 3.0 mm fits.
  - EVA case foam, 5 mm, on the case floor round the battery bay, the controller, the
    battery connector, the slide switch, the reset tube, the OLED pins and a bay for the encoder's terminals, lead and header. It sits
    3.0 mm below the parts under the PCB at rest and 1.5 mm below at full gasket travel.
- **Openings:** a 14.2 × 9.8 mm rounded USB-C port, in front of a pocket inside the wall for the
  controller's end, and a 9 × 5.3 mm slot on the top edge for the power switch's knob, closed above
  the knob by a tongue on the top frame, with the wall thinned outside them, and a 2 mm reset pinhole in the floor with a guide
  tube up to the button.
- **Fit check:** `tools/gen_case.py` checks every case part against the PCB, the plate, the
  controller, the reset button, the battery, the OLED, the encoder, the knob
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
| Underside, both halves | Under each reset button, beside the encoder opening: an STMPD emblem over a GENERATE button and "press twice to flash". Double-tapping reset enters the bootloader |
| Underside, left half, bottom edge | The KEYGEN logo over `github.com/milindmadhukar/keygen` |
| Underside, right half, bottom edge | KEYGEN REV 0.1 over DESIGNED BY MILIND MADHUKAR |
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
