---
created: 2026-03-09
updated: 2026-10-22T17:00
name: 08 - electronics & components
---

> [!success] Decision (2026-10-19)
> Each half carries an nRF52840 SuperMini (a nice!nano v2 clone), 33 MX switches in Kailh hotswap sockets, 1N4148 through-hole diodes, 33 per-key **SK6812MINI-E** LEDs, a LiPo on a JST-PH connector, an MSK12C02 slide switch driving an AO3401A P-MOSFET battery switch, a reset button, an EC11 encoder (D shaft) with a 17 mm knob, and a 0.96 in. SSD1306 I2C OLED module. USB-C comes from the controller module, and the LEDs run from the battery through an AO3401A/AO3400A MOSFET power switch. The per-half table is in [[12 - final design#Parts per half]]; the shopping list is [[13 - bill of materials]].

## Parts per half

| Part | Left | Right | References | Notes |
|---|---|---|---|---|
| nRF52840 SuperMini (nice!nano v2 clone) | 1 | 1 | U101 / U201 | Underside, socketed on low-profile machined pins |
| MX switch + Kailh MX hotswap socket (CPG151101S11) | 33 | 33 | SW1xx / SW2xx | Sockets on the back; SW101–SW106 and SW108–SW134, the same numbers in 2xx on the right |
| 1N4148 diode, DO-35 | 34 | 34 | D1xx / D2xx | Through-hole, back side; left D101–D134, right D201–D234 |
| SK6812MINI-E RGB LED | 33 | 33 | LED1xx / LED2xx | Reverse-mount on the back, shining through a PCB cut-out |
| 10 µF + 100 nF capacitors, 1206 | 1 + 1 | 1 + 1 | C101–C102 / C201–C202 | LED rail, at the LED power switch's output |
| 505080 LiPo pouch + JST-PH 2-pin side-entry connector (S2B-PH-K-S) | 1 | 1 | BT101 / BT201 | Connector on the back |
| MSK12C02 slide switch | 1 | 1 | SW190 / SW290 | Back side at the top edge, lever out |
| AO3401A P-MOSFET, SOT-23 + 1 MΩ resistor, 1206 | 1 + 1 | 1 + 1 | Q101, R101 / Q201, R201 | Battery switch |
| AO3401A P-MOSFET + AO3400A N-MOSFET, SOT-23, + 2 × 100 kΩ, 1206 | 1 + 1 + 2 | 1 + 1 + 2 | Q102, Q103, R102, R103 / Q202, Q203, R202, R203 | LED power switch, back side beside the battery connector |
| 6 mm reset button | 1 | 1 | SW191 / SW291 | Through-hole, back side; double-tap for the bootloader |
| EC11 rotary encoder (push switch, 20 mm D shaft) + 17 mm knurled aluminium knob | 1 | 1 | ENC101 / ENC201 | Through-hole, front side; push switch diode D107 / D207 |
| 0.96 in. 128×64 SSD1306 I2C OLED module | 1 | 1 | J101 / J201 | The module's own header pins, soldered into a 1×4 2.54 mm footprint |

Each half has 34 diodes: 33 for the keys and one for its encoder's push switch, which sits in the key matrix. The generated assembly BOM with every reference and solder note is `fab/BOM.md` in the repo.

## Controller

- **nRF52840 SuperMini**, one per half: a nice!nano v2 clone with the same 24-pin Pro Micro header and pinout, built in ZMK as the nice!nano v2. It provides the nRF52840, the USB-C port and the LiPo charger.
- **Charging** at about 100 mA; the board has no BOOST jumper.
- **Check before soldering:** B+ (pad 13), GND and VCC (pad 16) with a multimeter, and the charge current.
- **Socketed** on the PCB underside with USB-C facing the top edge, so a controller can be swapped.
- Pin map and pin budget: [[12 - final design#Controller pin map]]. Pin restrictions were checked in [[15 - datasheet audit]].

## Matrix

- 5 rows × 7 columns per half, COL2ROW: each switch connects to its column, and each diode's cathode (the band) faces its row.
- 1N4148 through-hole diodes on the back; the band goes toward the square pad.
- Each encoder's push switch sits at row 0 / column 6 in its half's matrix.

## Per-key RGB

- **SK6812MINI-E**, reverse-mount: the LED sits on the back and shines up through a cut-out under each switch, which suits the translucent caps ([[07 - switch & keycap selection]]).
- One data chain per half from P0.06 (full-speed pin), driven by ZMK's SPI WS2812 driver at 4 MHz.
- **Current:** 12 mA per colour, about 36 mA per LED at full white, so 33 LEDs reach about 1.2 A per half at full white. Brightness is capped in firmware.
- **Idle drain:** about 1 mA per LED even when dark. The LED rail runs from the battery through the LED power switch, and ZMK's external power control (P0.08) cuts it when the LEDs are off.
- On battery the LEDs light for status; full effects run while USB is plugged in.
- **Supply voltage:** the datasheet asks for VDD 3.7–5.5 V; the LEDs get the cell's 3.0–4.2 V, near 4.2 V on USB power when they light. See [[12 - final design#Schematic]].
- **Soldering:** mind the corner mark on each LED, and test the chain one column at a time, since one bad joint stops every LED after it.

## OLED

- **Module:** a generic 0.96 in. 128×64 SSD1306 I2C module (address 0x3C), 27.5 × 28 mm, using its own pull-ups and regulator. The controller's internal pull-ups are on as well, so the bus still works on a module without them.
- **Pins:** footprint order GND, VCC, SCL, SDA. Check the module's printed order; some swap GND and VCC.
- **Wiring:** SDA on P0.17 (pad 5), SCL on P0.20 (pad 6), power from the controller's switched 3.3 V VCC (pad 16), which the firmware keeps on by holding P0.13 high.
- **Mounting:** its header pins solder straight into the board on their 2.5 mm spacer, so the glass sits about level with the plate top, in the plate's OLED window. Position: [[12 - final design#OLED]].

## Power

- **Battery:** 3.7 V 505080 LiPo pouch (5 × 50 × 80 mm, about 2500 mAh), on a JST-PH 2.0 lead, at most 60 × 88 mm including its protection board. The controller has no over-discharge cut-off, so the cell needs a protection board: a cell sold without one gets a DW01A module. It lies in a bay sunk 1 mm into the case floor. With a 6.1 mm installed battery stack and assumed 2 mm underside parts, clearance is 2.9 mm at rest and 1.4 mm at full gasket travel; it stays at least 15 mm from the antenna end. Placement: [[12 - final design#Power]] and [[14 - case & plate requirements]].
- **Polarity:** LiPo packs come wired both ways. Check that the red wire lands on the + pad marked on the silkscreen before plugging in.
- **Battery switch:** the MSK12C02 (rated 50 mA) only drives the gate of the AO3401A, which carries the battery current, so charging and LED current never pass through the switch contacts. Source to the battery, drain to B+; the 1 MΩ resistor holds the gate off between positions. Leave the switch on while charging.
- **Charging:** through each half's own USB-C, at about 100 mA: roughly a day for a 2500 mAh cell from empty. A 1-to-2 USB-C cable charges both halves from one charger.

## Mounting and case hardware

- M2 screws and standoffs for the 10 mounting holes, with M2 heat-set inserts in the 3D-printed case. Case details: [[09 - case design]], [[14 - case & plate requirements]].

## Status

- Schematic generated and ERC clean; PCB routed and DRC clean with schematic parity.
- Datasheet audit: 0 failures ([[15 - datasheet audit]]).
- Assembly BOM generated from the schematic (`fab/BOM.md`); shopping list in [[13 - bill of materials]].
- Parts not yet ordered.

## Related Notes
- [[12 - final design]] for the full design
- [[05 - pcb design]] for the board
- [[06 - split architecture]] for how the halves connect
- [[07 - switch & keycap selection]] for switches and keycaps
- [[10 - assembly & build guide]] for assembly order

### Video Notes
- [[How To Build A Corne Keyboard - Beginners Guide]]: a per-side parts list with Kailh MX sockets and SK6812-style RGB, and hand-soldering technique
- [[Designing Keyboard PCBs with KiCad]]: placing the physical parts the PCB carries (diodes, switch footprints, encoder)
- [[I Built My DREAM Keyboard from Scratch - Modular]]: MCU pin suitability for LEDs, and SMD soldering tools
