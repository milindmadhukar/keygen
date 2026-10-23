# Assembling Keygen

Step-by-step instructions for building Keygen from bare boards: ordering, soldering, flashing and
closing the case. Every part is hand-soldered.

The two halves are built the same way, so follow the steps once per half. The left half's parts are
numbered 1xx and the right half's 2xx: Q101 on the left is Q201 on the right. In the steps below
the left reference comes first. [`fab/BOM.md`](fab/BOM.md) lists every reference per half.

Everything sits on the **back** of the PCB except the switches, the encoder and the OLED.

## Contents

1. [Order the parts](#1-order-the-parts)
2. [Tools](#2-tools)
3. [Solder the board](#3-solder-the-board) (steps 1–10)
4. [Plate, OLED and switches](#4-plate-oled-and-switches) (steps 11–14)
5. [Close the case](#5-close-the-case) (steps 15–20)
6. [Flashing](#flashing)
7. [Troubleshooting](#troubleshooting)

## 1. Order the parts

1. **Fit test.** Print [`case/plate/pdf/keygen-plate-print.pdf`](case/plate/pdf/keygen-plate-print.pdf)
   at 100 % on A4 and check the thumb cluster and the knob positions against your hand.
2. **PCBs.** Two orders of 5: [`fab/keygen-left-gerbers.zip`](fab/keygen-left-gerbers.zip) and
   [`fab/keygen-right-gerbers.zip`](fab/keygen-right-gerbers.zip), bare boards, black mask. The
   order-form settings and what to check in the DFM report are in [`fab/ORDER.md`](fab/ORDER.md).
3. **Switch plates.** The two zips in [`case/plate/gerber/`](case/plate/gerber/), with the settings
   in [`case/plate/PLATE.md`](case/plate/PLATE.md). Or have them CNC- or laser-cut from 1.5–1.6 mm
   sheet with the DXFs in [`case/plate/dxf/`](case/plate/dxf/), as
   [`PLATE.md`](case/plate/PLATE.md#cutting-the-plates-from-sheet-cnc-router-or-laser) describes.
4. **Case.** The four STLs in [`case/bottom/stl/`](case/bottom/stl/) and
   [`case/top/stl/`](case/top/stl/), printed in PETG.
5. **Foam.** Cut per half from the 1:1 files in [`case/foam/dxf/`](case/foam/dxf/) (laser) or
   [`case/foam/svg/`](case/foam/svg/) (printed at 100 % as a template): a 2 mm EVA plate foam and a
   5 mm EVA case foam, each the right way up as drawn. The Poron switch pads come ready to stick.
6. **Parts.** Everything else, with quantities, spares and sources, is in the
   [parts list](plan/bom.html) ([`bom/bom.csv`](bom/bom.csv)).

Fasteners per half:

| Part | Qty | Where |
|---|---|---|
| M2 × 3.5 mm female-female standoff | 5 | Between the PCB and the plate |
| M2 × 4 mm button-head screw | 5 + 4 (left), 5 + 3 (right) | Standoffs from below; plate from above |
| M2 × 3 mm brass heat-set insert | 8 | Top frame underside |
| M2 × 16 mm socket-head screw | 8 | Bottom shell to top frame, from below |
| Poron strip, 12 × 4 × 2 mm, cut from 80 × 4 × 2 mm strips | 16 | Two per plate tab |

## 2. Tools

- Temperature-controlled soldering iron with a fine tip (300–350 °C; 320 °C for the LEDs)
- Solder, flux, desoldering wick
- Flush cutters, fine tweezers
- Multimeter (continuity, polarity, battery voltage)
- Kapton tape
- Isopropyl alcohol (90 % or more) for flux residue
- A magnifier for the LED and SOT-23 joints
- A USB-C cable
- A Phillips screwdriver for the M2 screws, a 1.5 mm hex key for the case screws, and an iron tip or heat-set tool for the inserts
- Double-sided tape for the battery

## 3. Solder the board

Keep the battery unplugged whenever you solder. Clean off flux with isopropyl alcohol as you go.

### Step 1: Inspect the board

- Check that the 33 LED cut-outs are milled cleanly and nothing is bridged.
- With the multimeter, check there is no short between B+, the LED rail and GND.

### Step 2: Battery switch

- AO3401A P-MOSFET **Q101 / Q201** (SOT-23), between the controller and the power switch.
- 1 MΩ resistor **R101 / R201** (1206), below it.
- MSK12C02 slide switch **SW190 / SW290** at the top edge, lever pointing out.

For each small SMD part: tin one pad, hold the part in place with tweezers while you reflow that
pad, solder the other pads, then touch up the first.

### Step 3: LED power switch

- AO3401A P-MOSFET **Q102 / Q202** and AO3400A N-MOSFET **Q103 / Q203** (SOT-23), between the
  battery connector and the board edge.
- 100 kΩ resistors **R102, R103 / R202, R203** (1206), below each MOSFET.
- 10 µF capacitor **C101 / C201** and 100 nF capacitor **C102 / C202** (1206), beside the switch.

### Step 4: Battery connector and reset button

- JST-PH side-entry connector **BT101 / BT201**. The silkscreen marks its **+** pad.
- 6 mm reset button **SW191 / SW291**, the one labelled GENERATE.

### Step 5: Controller

1. Before soldering, check the SuperMini with the multimeter: **B+** (pad 13), **GND** and **VCC**
   (pad 16).
2. Fit the low-profile machined socket strips to the PCB footprint **U101 / U201** and the matching
   round pins to the controller.
3. Seat the controller with its **chip and USB-C facing away from the PCB**. Seated the other way,
   the pinout is mirrored and the battery lands on a GPIO.
4. Solder the socket strips with the controller seated in them, so the pins line up, then lift it
   out and check every joint.
5. Check that the USB-C end lines up with the board's top edge, overhanging it by 1 mm.

### Step 6: Bring-up

1. Flash the firmware (see [Flashing](#flashing)) and check that the half shows up over USB.
2. **Protection board.** Check the cell has one: the controller has no over-discharge cut-off. Fit
   a DW01A module to a cell without one.
3. **Battery polarity.** JST-PH packs come wired both ways round. With the multimeter, confirm the
   red wire lands on the PCB's **+** pad before plugging in. Swap the crimps if it does not.
4. Plug the battery in and check that the slide switch turns the half on and off. Leave the switch
   on while charging.
5. **Charge current.** With the multimeter in series with the battery and USB plugged in, confirm
   about 100 mA. An empty 2500 mAh cell takes roughly a day. Unplug the battery again before the
   next step.

### Step 7: LEDs, one column at a time

- SK6812MINI-E **LED101–LED133 / LED201–LED233**, reverse-mount on the back with the lit side
  through the cut-out. **Match the corner mark** to the footprint.
- Iron at 320 °C, plenty of flux, 2–3 seconds per pad. Tin one pad, place the LED in its cut-out,
  reflow the tinned pad, then solder the other three.
- Solder one column in chain order, then plug in USB and check the column lights before starting
  the next. The LEDs light while the half has USB power; SYS + `A` toggles them. Data passes from
  LED to LED, so one bad joint darkens every LED after it.

### Step 8: Diodes

- 1N4148 **D101–D134 / D201–D234** (DO-35), body on the back, **band towards the square pad**.
- **D107 / D207** is the encoder's, beside it.
- Bend the leads to the footprint spacing, insert, splay the legs, solder, and trim the legs flush
  so nothing touches a switch.

### Step 9: Hotswap sockets

- Kailh sockets on the back, one per switch position (33).
- Tack one pad while holding the socket flat, solder the other pad fully, then finish the first.
  Use plenty of solder: both joints should be concave, as the socket takes the force of every
  switch insertion.

### Step 10: Encoder and matrix test

1. EC11 encoder **ENC101 / ENC201** on the **front**: solder all five pins and both mounting tabs.
2. Short each socket's two contacts with tweezers and check that the key registers (ZMK Studio on
   the left half, or a key tester such as [keyboard-test.space](https://keyboard-test.space)).
3. Turn and press the encoder. Left: scroll and middle click. Right: volume and mute.

## 4. Plate, OLED and switches

### Step 11: Standoffs

Screw the five M2 × 3.5 mm standoffs onto the PCB at **H101–H105 / H201–H205**, with M2 × 4
button-head screws from below.

### Step 12: Switch pads and plate foam

1. Stick a 0.5 mm Poron ring switch pad on the PCB under each switch position (33), its open middle
   over the LED window.
2. Lay the 2 mm EVA plate foam over them.

### Step 13: Plate and OLED

1. Set the plate on the standoffs and screw it down with M2 × 4 button-head screws at
   **H102–H105** (left) and **H202–H204** (right). H101, H201 and H205 get no screw on top.
2. **OLED J101 / J201.** Check that the pin order printed on the module is GND, VCC, SCL, SDA, the
   same as the footprint; some modules swap GND and VCC. Pass its header pins down through the
   plate's OLED window into the board, with the module resting on its plastic spacer, and solder
   them from the back.
3. Power the half and check the status screen appears.

### Step 14: Switches

- Check each switch's pins are straight, then press it through the plate into its socket while
  supporting the PCB behind the socket with your other hand.
- The two 1.5u thumb switches per half are turned 90°.

## 5. Close the case

### Step 15: Heat-set inserts

Lay the top frame deck-down and press the 8 M2 heat-set inserts into the blind holes in its
underside at about 200–230 °C, flush with the surface and no deeper (1.4 mm of frame covers each
hole), and let them cool.

### Step 16: Battery

- Tape the pouch into the bay in the bottom shell's floor with double-sided tape, its lead end
  towards the battery connector.
- Never press, fold or puncture the pouch.

### Step 17: Case foam

Lay the 5 mm EVA case foam on the floor of the bottom shell, round the battery in its bay.

### Step 18: Plate-and-PCB unit

1. Cut the Poron strips into 12 mm pieces and put one on each of the 8 gasket ledges.
2. Plug the battery lead into **BT101 / BT201**.
3. Lower the plate-and-PCB unit onto the strips, with the USB-C over its slot and the slide switch
   in its opening.
4. Put a second piece on top of each plate tab.

### Step 19: Top frame

Fit the top frame. Holding the two parts together, turn the half over onto a soft cloth and drive
the 8 M2 × 16 screws up through the floor's counterbores evenly, a little at a time: snug, not
tight, so the gaskets stay soft.

### Step 20: Keycaps, knob and final test

1. Fit the keycaps: per half, 26 × 1u, 5 × 1.25u and 2 × 1.5u.
2. Push a knob onto each encoder shaft.
3. Turn both halves on together so they pair with each other, then pair the host to Bluetooth
   profile 1 (SYS + `1`).
4. Test every key on every layer, both encoders, both OLEDs, the LEDs on USB, and the link between
   the halves on battery. The keymap is in [`firmware/README.md`](firmware/README.md#keymap).

## Flashing

Build the firmware with GitHub Actions or `firmware/build.sh`
([`firmware/README.md`](firmware/README.md#building)). It produces `keygen_left`, `keygen_right`
and `settings_reset` UF2 files.

1. Plug the half in over USB-C.
2. **Double-press the reset button** (GENERATE). In the case, press it through the pinhole in the
   floor. A drive called `NICENANO` appears.
3. Copy `keygen_left-nice_nano.uf2` to the left half, or `keygen_right-nice_nano.uf2` to the right.
   The drive disconnects when it is done.

Once the firmware is running, SYS + `B` (left) or SYS + `N` (right) also enters the bootloader.
If the halves do not pair, flash `settings_reset-nice_nano.uf2` to both, then the normal firmware
again.

## Troubleshooting

| Symptom | Check |
|---|---|
| Half not detected over USB | Another cable and port. Controller seated chip-out and fully in its sockets. No short between the LED rail and GND. A double-press of reset still brings up the bootloader |
| Half does not run on battery | Red wire on the **+** pad. Battery above 3.0 V. Slide switch on. Q101 / Q201 and R101 / R201 soldered |
| One key does not work | Switch fully seated, pins straight. Diode present and the right way round. Socket joints. Continuity from the socket to the controller pin |
| Several keys register at once | A diode missing or reversed, or a short between a row and a column |
| LEDs dark from one point on | The first dark LED or the one before it: a bad joint, or turned the wrong way. Data from P0.06 reaching the first LED. The LED rail at battery voltage while the LEDs are on; if not, the LED power switch (Q102/Q103, R102/R103) and P0.08. The LEDs only light on USB power |
| OLED blank | Module pin order against the footprint (GND, VCC, SCL, SDA). 3.3 V on VCC, switched on through P0.13. SDA on P0.17, SCL on P0.20, address 0x3C. The screen blanks when idle: press a key |
| Halves do not connect | Both halves on and charged. Flash `settings_reset` to both, then the normal firmware |

Common mistakes: a diode backwards, a battery plugged in reversed, the controller seated upside
down, bent switch pins, cold (dull or grainy) joints, and overtightened screws, which crack the
PCB or the screw bosses.
