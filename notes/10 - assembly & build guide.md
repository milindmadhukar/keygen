---
created: 2026-03-09
updated: 2026-10-22T17:53
name: 10 - assembly & build guide
---

> [!success] Assembly
> Bare boards from JLCPCB, everything hand-soldered. All parts sit on the **back** of the PCB except the switches, the encoder and the OLED module. The controller is **socketed** on low-profile machined pins. Firmware is **ZMK**, flashed as a UF2 per half by drag-and-drop. The LED chain is soldered and tested **one column at a time**. Per-part references and soldering notes: `fab/BOM.md` in the repo. Build order and checklist: [[12 - final design#Build order]]. The numbered build steps are `INSTRUCTIONS.md` in the repo.

## Tools

- Temperature-controlled soldering iron (300–350 °C, 320 °C for the LEDs), fine tip
- Solder, flux, desoldering wick
- Flush cutters, fine tweezers
- Multimeter (continuity, polarity, battery voltage)
- Kapton tape and sheet
- Isopropyl alcohol (90 %+) for flux residue
- Magnifier for the LED and SOT-23 joints
- USB-C cable; a 1-to-2 USB-C cable for charging both halves
- 1.3 mm hex key for the M2 button-head screws, 1.5 mm for the case screws; iron tip or heat-set tool for the inserts

[GOLEM tools guide](https://golem.hu/guide/tools/)

## Parts per half

From `fab/BOM.md` (left 1xx, right 2xx):

| Part | Qty | Side | Notes |
|---|---|---|---|
| AO3401A P-MOSFET (SOT-23), Q101/Q201 | 1 | back | between the controller and the power switch |
| 1 MΩ resistor (1206), R101/R201 | 1 | back | below the MOSFET |
| AO3401A P-MOSFET + AO3400A N-MOSFET (SOT-23), Q1x2/Q1x3 | 1 + 1 | back | LED power switch, between the battery connector and the board edge |
| 100 kΩ resistors (1206), R1x2/R1x3 | 2 | back | LED power switch, below each MOSFET |
| 10 µF + 100 nF capacitors (1206), C1x1/C1x2 | 1 + 1 | back | beside the LED power switch |
| MSK12C02 power slide switch, SW190/SW290 | 1 | back | top edge, lever out |
| JST-PH 2-pin side-entry, BT101/BT201 | 1 | back | battery connector; + marked on the silkscreen |
| 6 mm reset button, SW191/SW291 | 1 | back | labelled GENERATE |
| nRF52840 SuperMini, U101/U201 | 1 | back | socketed; check B+, GND and VCC first |
| SK6812MINI-E LED | 33 | back | reverse-mount through the board cut-out |
| 1N4148 diode (DO-35) | 34 | back | band (cathode) toward the square pad; D107/D207 is the encoder's, beside it |
| Kailh MX hotswap socket | 33 | back | |
| EC11 encoder, ENC101/ENC201 | 1 | front | 17 mm knob on the D shaft |
| MX switch + keycap | 33 | front | tall 1.25u thumb switches turned 90° |
| 0.96 in. SSD1306 I2C OLED module, J101/J201 | 1 | front | a 1×4 right-angle header; the module goes in the top frame and plugs in |

## Build sequence (per half)

### 1. Inspect the board
- Check the LED cut-outs are milled cleanly and nothing is bridged.
- Continuity: no short between B+, the LED rail and GND.

### 2. Power parts
- AO3401A and its 1 MΩ gate resistor, then the MSK12C02 slide switch at the top edge.
- The 10 µF and 100 nF LED-rail capacitors next to the first LED.
- JST-PH connector and the reset button.
- These are the small SMD parts; doing them first keeps the board flat on the mat.

### 3. Controller
- Before soldering, check the SuperMini with a multimeter: B+ (pad 13), GND and VCC (pad 16).
- Solder the low-profile machined socket strips to the PCB, and the matching round pins to the controller.
- Seat the controller with its **chip and USB-C facing away from the PCB**. The footprint assumes this. Seated the other way, the pinout is mirrored and battery + lands on a GPIO ([[15 - datasheet audit]]).
- Check the USB-C end lines up with the board's top edge.

### 4. Bring-up
- Flash the firmware (see [[#Flashing]]) and check the half enumerates over USB.
- **Battery polarity:** JST-PH packs come wired both ways round. With a multimeter, confirm the red wire lands on the PCB's **+** pad before plugging in. Swap the crimps if it doesn't.
- **Protection board:** check the cell has one; the controller has no over-discharge cut-off. Add a DW01A module to a cell without one.
- Plug the battery in, then check the slide switch turns the half on and off. Leave the switch **on** while charging.
- **Charge current:** with the multimeter in series with the battery, confirm about 100 mA on USB. An empty cell takes roughly a day.

### 5. LEDs, one column at a time
- SK6812MINI-E, reverse-mount on the back, lit side through the cut-out. **Mind the corner mark**.
- Solder in chain order, one column, then light that column from the firmware before starting the next. Data passes LED to LED, so one bad joint darkens everything after it; testing per column finds it straight away.
- Iron at 320 °C, plenty of flux, 2–3 seconds per pad.

### 6. Diodes
- 1N4148 through-hole, body on the back, **band toward the square pad** (cathode to the row, COL2ROW).
- Include the encoder's diode (D107 left, D207 right) on the back beside the encoder.
- Trim the legs flush so nothing touches a switch.

### 7. Hotswap sockets
- Kailh sockets on the back. Tack one pad while holding the socket flat, solder the other fully, then finish the first. Both joints should be concave.

### 8. Encoder
- EC11 on the front of each half: solder all five pins and the mounting tabs.

### 9. Matrix test
- Short each socket's two contacts with tweezers and check the key registers (an online key tester, or ZMK Studio on the left half).
- Turn and press the encoder: on the left, scroll and middle click; on the right, volume and mute.

### 10. Battery
- Tape the pouch into the battery bay in the bottom shell's floor with double-sided tape, its lead end towards the battery connector. The bay keeps it at least 15 mm from the controller's antenna end and 1.0 mm from assumed 2 mm underside parts at full gasket travel, with a 6.1 mm installed battery stack. Placement: [[14 - case & plate requirements#Inside the case (under the PCB)]].
- The lead end sits about 40 mm from the connector, so a lead of 60 mm or more reaches it.
- Never press, fold or puncture the pouch.

### Case assembly
The case is gasket-mounted: the plate and PCB become one unit that floats on Poron strips. Design: [[09 - case design]].
- Lay the top frame deck-down and press the 8 M2 heat-set inserts into the holes in its underside (about 200–230 °C), flush and no deeper, and let them cool. 1.7 mm of frame covers each hole. [Heat-set insert guide](https://www.youtube.com/watch?v=cyof7fYFcuQ)
- Put a 0.5 mm shim on the PCB over each mounting hole, stand an M2 × 3 mm standoff on it and screw it on from below with an M2 × 5 button head, at all ten holes.
- Cut the foam from the files in `case/foam/dxf/` or `case/foam/svg/` (DXF for a laser, SVG printed at 100 % as a template): per half a 2 mm EVA plate foam and a 5 mm EVA case foam, each the right way up as drawn.
- Stick a 0.5 mm Poron ring switch pad on the PCB round each switch, its notches towards the switch clips and its open middle round the pins and the LED window, then tape the plate foam to the plate's underside, its cut-outs over the plate's and its notches clear for the switch latches. Seven rings per half have a corner snipped off where they meet a standoff.
- Plate onto the standoffs, foam side down. It is not screwed: the standoffs bear on it and the switches clip it to the PCB.
- **OLED module (J101/J201):** check its printed pin order matches the footprint's GND, VCC, SCL, SDA (some modules swap GND and VCC). Solder a right-angle header into the board, pins pointing away from the thumbs. Remove the module's header if it has one and solder a 45 mm lead of four jumper wires (their plugs glued into one 4-pin plug) into its holes from the back, matching the header's pin order. Plug it in, power the half and check the status screen appears. When closing the case, seat the module on the top frame's four pegs, melt or glue the peg tips, and plug it in.

### 11. Switches, then into the case
- Check each switch's pins are straight, then press it through the plate into its socket, with a hand under the PCB behind the socket. The tall 1.25u thumb switches are turned 90°.
- Case foam onto the floor of the bottom shell, round the battery in its bay.
- Poron strips (12 × 4 × 3 mm, cut from 80 × 4 × 3 mm strips) on the 8 ledges, then the plate-and-PCB unit onto them with the controller's end down into its pocket behind the USB-C port, then a strip on top of each tab.
- Top frame on. Holding the two parts together, turn the half over onto a soft cloth and drive the 8 M2 × 16 screws up through the floor evenly: snug, not tight, so the gaskets stay soft.
- Fit the keycaps (52 × 1u, 14 × 1.25u) and push a knob onto each encoder shaft.
- Final test: every key on every layer, both encoders, both OLEDs, the LEDs on USB, and Bluetooth between the halves on battery.

## Flashing

The firmware lives in `firmware/` in the repo. GitHub Actions (`build.yaml`) or `firmware/build.sh` produce three UF2 files: `keygen_left` (with ZMK Studio), `keygen_right` and `settings_reset`.

1. Plug the half into USB.
2. **Double-tap the reset button** (GENERATE). The controller mounts as a USB drive.
3. Copy the matching UF2 onto it: `keygen_left` to the left half, `keygen_right` to the right. It reboots by itself.
4. If the halves won't pair, flash `settings_reset` to both, then the normal UF2s again.

Key testers: [keyboard-test.space](https://keyboard-test.space), [keyboardchecker.com](https://keyboardchecker.com).

## Soldering technique

**Through-hole diodes:** bend the leads 90° to the footprint spacing, insert, splay the legs to hold the diode, solder, trim flush. Angle the cutters away so legs don't fly.

**Hotswap sockets:** tack, hold flat, solder the other pad fully, reflow the tack. Use plenty of solder; it's a mechanical joint.

**SK6812MINI-E (reverse-mount):** pre-tin one pad, flux, place the LED in its cut-out with tweezers and reflow the tinned pad, then solder the other three. Work quickly; the LEDs are heat-sensitive. If one doesn't light, check its orientation first.

**1206 and SOT-23:** pre-tin one pad, place with tweezers while reflowing it, solder the rest, then touch up the first.

**Controller sockets:** solder the socket strips with the controller seated in them, so the pins line up, then lift it out to check every joint. [Mill-Max socket guide](https://golem.hu/guide/mill-max/)

## Troubleshooting

### Half not detected over USB
- Try another cable and port.
- Controller seated the right way round and fully in its sockets.
- No short between the LED rail and GND.
- Double-tap reset to check the bootloader still appears.

### Half won't run on battery
- Red wire on the + pad; battery charged (above 3.0 V).
- Slide switch on; AO3401A and its 1 MΩ resistor soldered.

### Key not working
- Switch fully seated, pins straight.
- Diode present and the right way round.
- Socket joints; trace continuity from socket to controller pin.

### Several keys register at once
- A diode missing or reversed, or a short between a row and a column.

### LEDs dark from one point on
- The first dark LED, or the one before it, has a bad joint or is turned the wrong way.
- Data from P0.06 reaching the first LED.
- The LED rail (Q2's drain) at battery voltage while the LEDs are on; if not, check the LED power switch (Q2, Q3, R2, R3) and P0.08.
- LED power comes through the LED power switch (P0.08), so it is off whenever the firmware has the LEDs off. On battery they only light for status.

### OLED blank
- Module pin order against the footprint (GND, VCC, SCL, SDA); a module with GND and VCC swapped gets reverse power.
- 3.3 V on VCC (pad 16), which the firmware turns on through P0.13.
- SDA on P0.17 and SCL on P0.20; the module's I2C address is 0x3C.
- The screen blanks when the keyboard goes idle; press a key.

### Halves don't connect
- Both halves on and charged; flash `settings_reset` to both, then the normal firmware.

## Common mistakes
1. Diode backwards: check the band before soldering.
2. Battery plugged in reversed: check polarity first, every pack.
3. Controller seated upside down: chip and USB-C away from the PCB.
4. Bent switch pins: inspect before pressing in.
5. Cold joints: reheat any dull or grainy joint.
6. Overtightened screws: they crack the PCB or the bosses.

Budget several evenings per half and test after each step.

## Related notes
- [[12 - final design]]: the design and the pre-order checklist
- [[13 - bill of materials]]: parts to buy
- [[14 - case & plate requirements]]: battery placement and case openings
- [[15 - datasheet audit]]: orientation and polarity checks
- [[04 - firmware options]]: ZMK
- [[09 - case design]]: the case

## Resources
- [GOLEM keyboard guides](https://golem.hu/guide/)
- [Mill-Max socket guide](https://golem.hu/guide/mill-max/)

### Video notes
- [[How To Build A Corne Keyboard - Beginners Guide]]: per-side component order, LED-chain technique, key testing with tweezers
- [[I Built My DREAM Keyboard from Scratch - Modular]]: build order from test plates to case, and mistakes to avoid
