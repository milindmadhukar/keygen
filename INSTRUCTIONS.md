# Assembling Keygen

Step-by-step instructions for building Keygen from nothing: what to order and when, then soldering,
flashing and closing the case. Every part is hand-soldered. Read [Before you start](#before-you-start)
and [the plan](#1-the-plan-what-to-get-and-when) first: some parts are made to fit others, so the
order of things matters.

## Contents

0. [Before you start](#before-you-start)
1. [The plan: what to get, and when](#1-the-plan-what-to-get-and-when)
2. [Order and make the parts](#2-order-and-make-the-parts)
3. [Tools](#3-tools)
4. [Solder the board](#4-solder-the-board) (steps 1–10)
5. [Plate, OLED and switches](#5-plate-oled-and-switches) (steps 11–14)
6. [Close the case](#6-close-the-case) (steps 15–21)
7. [Flashing](#flashing)
8. [Troubleshooting](#troubleshooting)

## Before you start

### What you are building

Two halves, built the same way. Each is a stack, from the bottom: a 3D-printed bottom shell with
the battery and a foam layer in it; the PCB, with most parts on its underside; foam pads and a foam
sheet; a clear polycarbonate switch plate on five standoffs, holding the switches; and a 3D-printed top frame
over it all, screwed to the bottom shell. The plate-and-PCB unit rests on small foam strips (gaskets)
between the shell and the frame, so it floats.

![The case layers, exploded: bottom shell, case foam, PCB, switch pads, plate foam, gasket strips, plate and top frame](https://github.com/milindmadhukar/keygen/releases/download/media/render-case-exploded.png)

### What you need to be able to do

- Solder through-hole parts: diodes, sockets, an encoder, header pins.
- Solder small surface-mount parts by hand: three-legged SOT-23 transistors, 1206 resistors and
  capacitors, and 66 SK6812MINI-E LEDs (3.2 × 2.8 mm). The LEDs are the hard part. If you have not
  soldered surface-mount parts before, practise on spares first (the parts list includes plenty), or
  have the PCB fab fit the LEDs (an option on the parts list).
- Measure to 0.1 mm with calipers, twice, before parts are made (see [the plan](#1-the-plan-what-to-get-and-when)).

### Words used here

- **Front** is the switch side of the PCB. **Back** is the other side: it has two large pads per key
  for the hotswap sockets. Everything sits on the back except the switches, the encoder and the OLED.
- **Left and right.** The left half's parts are numbered 1xx and the right half's 2xx: Q101 on the
  left is Q201 on the right. In the steps below the left reference comes first. To tell the bare
  boards apart, lay them front up: the left half has its encoder and OLED holes along its right-hand
  (inner) edge, the right half along its left-hand edge. [`fab/BOM.md`](fab/BOM.md) lists every
  reference per half.
- **Through-hole** parts have legs that go through the board; you solder them on the opposite side
  and trim the legs. **Surface-mount (SMD)** parts sit on pads on one side.
- **References** (Q101, D107, H102) name each part's place on the board. The silkscreen prints only
  a few of them; the assembly maps below show all of them.

### Assembly maps

Each map shows one side of one half with every part's reference and pad numbers. The back maps
are drawn as the board lies when you turn it over, so they match what you see.

| Half | Back | Front |
|---|---|---|
| Left | [`assembly-left-back.png`](https://github.com/milindmadhukar/keygen/releases/download/media/assembly-left-back.png) | [`assembly-left-front.png`](https://github.com/milindmadhukar/keygen/releases/download/media/assembly-left-front.png) |
| Right | [`assembly-right-back.png`](https://github.com/milindmadhukar/keygen/releases/download/media/assembly-right-back.png) | [`assembly-right-front.png`](https://github.com/milindmadhukar/keygen/releases/download/media/assembly-right-front.png) |

The power parts beside each controller, enlarged:

![The power parts of both halves seen from the back, with their references](https://github.com/milindmadhukar/keygen/releases/download/media/assembly-power.png)

## 1. The plan: what to get, and when

Most things can be ordered on day one. Two parts are made to fit parts you buy, so they wait until
those have arrived and been measured: the switch plate (with its foam) waits for the OLED modules,
and the case (with its foam) for the controller sockets. Soldering does not need either, so the
boards can be built and tested while the plate and the case are being made.

| When | Do | Waiting for |
|---|---|---|
| Day one | Print the fit test ([2.1](#21-fit-test)). Then order the PCBs ([2.2](#22-pcbs)) and every part on the parts list ([2.3](#23-parts)), including the polycarbonate sheet for the plates and the EVA foam sheets | Nothing. The parts shipped from abroad and the PCBs take longest: order them first |
| The OLED modules have arrived | Measure one ([2.4](#24-switch-plates)). Then have the switch plates cut, and cut the plate foam ([2.5](#25-foam)) | The plate's OLED window, and the plate foam round it, are sized for a 27.5 × 28 mm module with 1 mm to spare on each side |
| The controller sockets have arrived | Measure one ([2.6](#26-case)). Then print the case, and cut the case foam ([2.5](#25-foam)) | The case's USB-C opening is placed from the socket height |
| The PCBs and the electronics have arrived | Solder and test both boards: steps 1–10 | Nothing more |
| The plates and the plate foam are ready | Steps 11–14 | |
| The case and the case foam are ready | Steps 15–21 | |

Every file to order, print or cut is in the [build release](https://github.com/milindmadhukar/keygen/releases/tag/build).
Cut and print everything from the same release, so the plate, the foam and the case match.

## 2. Order and make the parts

### 2.1 Fit test

Print [`keygen-plate-print.pdf`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-print.pdf)
at 100 % ("actual size") on A4 and measure the 100 mm ruler on it: if it is not exactly 100 mm,
reprint. Rest your hands on it and check the thumb cluster and the knob positions.

### 2.2 PCBs

Two orders of 5, one per half: [`keygen-left-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-left-gerbers.zip) and
[`keygen-right-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-right-gerbers.zip), bare boards, black mask. The
order-form settings and what to check in the fab's design check (DFM) report are in
[`fab/ORDER.md`](fab/ORDER.md).

### 2.3 Parts

Everything else, with quantities, spares and sources, is in the [parts list](plan/bom.html)
([`bom/bom.csv`](bom/bom.csv)). When they arrive, check:

- **OLED modules:** the pin order printed on the module is GND, VCC, SCL, SDA. Some modules swap
  GND and VCC; don't use those.
- **Batteries:** each cell has a protection board (a small circuit board under the tape at the lead
  end). The controller has no over-discharge cut-off; fit a DW01A module to a cell without one.
- **Battery connectors:** the side-entry type (S2B-PH-K-S), whose opening faces sideways, not up.
- **Encoders:** a D-shaped (half-round) shaft, to match the knob.

Fasteners per half:

| Part | Qty | Where |
|---|---|---|
| M2 × 3 mm female-female standoff | 5 | Between the PCB and the plate |
| M2 shim, 2 × 5 × 0.5 mm (DIN 988) | 5 | Under each standoff, on the PCB |
| M2 × 4 mm button-head screw | 2 (left), 3 (right) | Standoffs with no plate screw, from below |
| M2 × 3 mm button-head screw | 3 + 3 (left), 2 + 2 (right) | Standoffs with a plate screw, from below; plate from above |
| M2 × 3 mm brass heat-set insert | 8 | Top frame underside |
| M2 × 16 mm socket-head screw | 8 | Bottom shell to top frame, from below |
| Poron strip, 12 × 4 × 3 mm, cut from 80 × 4 × 3 mm strips | 16 | Two per plate tab |

### 2.4 Switch plates

**When:** once the OLED modules have arrived. Measure one module's board with calipers: it must be
no larger than 27.5 × 28 mm. If it is larger, the plate and the plate foam have to be redrawn first:
set `OLED_W` and `OLED_H` in [`tools/case_geometry.py`](tools/case_geometry.py) and run
`tools/regen.py` (the tools are listed in [Building from source](notes/17%20-%20building%20from%20source.md)).

Then have both halves CNC-routed (not laser-cut) from the 1.5 mm clear polycarbonate sheet with
[`keygen-plate-left.dxf`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-left.dxf) and
[`keygen-plate-right.dxf`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-right.dxf), as
[`PLATE.md`](case/plate/PLATE.md#routing-the-plates-from-polycarbonate-sheet) describes. Or
order the same plate in FR-4 from a PCB fab: [`keygen-plate-left-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-left-gerbers.zip) and
[`keygen-plate-right-gerbers.zip`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-right-gerbers.zip), with the
settings in [`case/plate/PLATE.md`](case/plate/PLATE.md).

### 2.5 Foam

**When:** the plate foam with the plates, from the same release; the case foam with the case. Both
are needed only at steps 12 and 17, so they can be cut while the boards are being soldered.

Each half has two foam layers, cut from the 1:1 `keygen-{left,right}-{plate,case}-foam` files in
the [build release](https://github.com/milindmadhukar/keygen/releases/tag/build): a 2 mm EVA plate
foam and a 5 mm EVA case foam. Use the DXF files for a laser cutter. To cut by hand, print the SVG
at 100 % ("actual size") as for the fit test, tape it to the sheet and cut along the lines with
a sharp craft knife and a steel ruler. Keep each piece the right way up as drawn: they are seen from
above and are not symmetrical. The Poron switch pads and gasket strips come ready-made.

### 2.6 Case

**When:** once the controller sockets have arrived. Measure the height of a female socket strip's
plastic body with calipers. If it is not 3.0 mm, set `SOCKET_H` in
[`tools/gen_schematic.py`](tools/gen_schematic.py) and run `tools/regen.py` before printing.

Print the four STLs, [`keygen-left-bottom.stl`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-left-bottom.stl),
[`keygen-right-bottom.stl`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-right-bottom.stl), [`keygen-left-top.stl`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-left-top.stl)
and [`keygen-right-top.stl`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-right-top.stl), in PETG at 0.2 mm layers and 90 % infill, dense for weight and a deeper sound: the bottom
shells floor-down and the top frames deck-down, without supports (the 40 mm pocket for the steel
disc in each floor is bridged). A printing service can do this
from the same settings. The fits are close (1.0 mm from the plate edge to the wall, 0.5 mm round
each gasket tab), so calibrate the printer's flow and dimensions first, and try the plate in each
bottom shell before setting the inserts: sand a tight wall or pocket, don't force the plate.

## 3. Tools

- Temperature-controlled soldering iron with a fine tip (300–350 °C; 320 °C for the LEDs)
- Solder, no-clean flux (a syringe of 559 flux paste), desoldering wick
- Flush cutters, fine tweezers
- Multimeter (continuity, polarity, battery voltage, and current for the charge check)
- Calipers, for the OLED module and the controller sockets
- Kapton tape
- Isopropyl alcohol (90 % or more) for flux residue
- A magnifier for the LED and SOT-23 joints
- A USB-C cable and a computer, to flash and test
- A 1.3 mm hex key for the M2 button-head screws, a 1.5 mm hex key for the case screws, and an iron tip or heat-set tool for the inserts
- Thin double-sided tape for the battery (tissue tape, 0.3 mm or less, not foam tape)
- A keycap and switch puller
- A craft knife and a steel ruler, to cut the foam by hand

## 4. Solder the board

Keep the battery unplugged whenever you solder. Clean off flux with isopropyl alcohol as you go.
Find each part on the [assembly maps](#assembly-maps) before you solder it.

### Step 1: Inspect the board

- Tell the front from the back and the left half from the right ([Words used here](#words-used-here)).
- Check that the 33 LED cut-outs are milled cleanly and nothing is bridged.
- With the multimeter, check there is no short between B+, the LED rail and GND.

### Step 2: Battery switch

On the back, beside the controller's footprint (the enlarged map above):

- AO3401A P-MOSFET **Q101 / Q201** (SOT-23), between the controller and the power switch. A SOT-23
  part fits its three pads only one way round.
- 1 MΩ resistor **R101 / R201** (1206), below it. Resistors and capacitors can go either way round.
- MSK12C02 slide switch **SW190 / SW290** at the top edge, lever pointing out over the edge.

For each small SMD part: tin one pad, hold the part in place with tweezers while you reflow that
pad, solder the other pads, then touch up the first.

### Step 3: LED power switch

- AO3401A P-MOSFET **Q102 / Q202** and AO3400A N-MOSFET **Q103 / Q203** (SOT-23), between the
  battery connector and the board edge. They look alike: keep the two types apart until soldered.
- 100 kΩ resistors **R102, R103 / R202, R203** (1206), below each MOSFET.
- 10 µF capacitor **C101 / C201** and 100 nF capacitor **C102 / C202** (1206), beside the switch.
  Ceramic capacitors carry no marking, so take each from its labelled bag only as you place it.

### Step 4: Battery connector and reset button

These are through-hole: place them on the back and solder them on the front.

- JST-PH side-entry connector **BT101 / BT201**, turned to match its outline on the map. The
  silkscreen marks its **+** pad.
- 6 mm reset button **SW191 / SW291**, the one labelled GENERATE.

### Step 5: Controller

The controller (U101 / U201) plugs into sockets on the back, so it can be swapped. It sits upside
down compared with most keyboards: chip and USB-C away from the PCB.

1. Before soldering, check the SuperMini with the multimeter: **B+** (pad 13), **GND** and **VCC**
   (pad 16).
2. Cut two 12-pin lengths of the female socket strip and two of the round male pins. Push the
   socket strips into the footprint **U101 / U201** from the back, push the male pins into the
   sockets, and lay the controller on the pins.
3. Seat the controller with its **chip and USB-C facing away from the PCB**, the USB-C end at the
   board's top edge (the map marks it USB). Seated the other way, the pinout is mirrored and the
   battery lands on a GPIO.
4. Solder the pins to the controller, then turn the board over and solder the socket strips on the
   front. Soldering everything in place keeps the pins lined up. Lift the controller out and check
   every joint.
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
6. **Lead length.** Measure the battery lead from the pouch to the end of the plug. It runs about
   50 mm in the case, from the bay to **BT101 / BT201**; with less than about 80 mm, plug it in
   before taping the cell down (step 16).

### Step 7: LEDs, a few at a time

- SK6812MINI-E **LED101–LED133 / LED201–LED233**, reverse-mount: placed on the back, upside down,
  with the lit side down through the cut-out so it shines out of the front.
- **Orientation.** The LED's cut corner marks its GND pin. Turn it so that corner sits on the
  footprint's GND pad, the one numbered 1 on the maps.
- Iron at 320 °C, plenty of flux, 2–3 seconds per pad. Tin one pad, place the LED in its cut-out,
  reflow the tinned pad, then solder the other three. Kapton tape keeps the neighbouring pads clean.
- Data passes from LED to LED in number order, LED101 first, so one bad joint darkens every LED
  after it. Solder them in number order, six or so at a time, then plug in USB and check they light
  before going on. The LEDs light while the half has USB power; SYS + `A` toggles them.

### Step 8: Diodes

- 1N4148 **D101–D134 / D201–D234** (DO-35), body on the back, **band towards the square pad** (the
  pad marked K on the maps).
- **D107 / D207** is the encoder's, beside it.
- Bend the leads to the footprint spacing, insert, splay the legs, solder on the front, and trim the
  legs flush so nothing touches a switch. Keep the joints on the front low: the switch pads stick
  down over them.

### Step 9: Hotswap sockets

- Kailh sockets on the back, one per switch position (33). Each fits its two pads only one way.
- Tack one pad while holding the socket flat, solder the other pad fully, then finish the first.
  Use plenty of solder: both joints should be concave, as the socket takes the force of every
  switch insertion.

### Step 10: Encoder and matrix test

1. EC11 encoder **ENC101 / ENC201** on the **front**: solder all five pins and both mounting tabs on
   the back.
2. Short each socket's two contacts with tweezers and check that the key registers (ZMK Studio on
   the left half, or a key tester such as [keyboard-test.space](https://keyboard-test.space)).
3. Turn and press the encoder. Left: scroll and middle click. Right: volume and mute.

The board is done. The rest waits for the plates, the foam and the case.

## 5. Plate, OLED and switches

### Step 11: Standoffs

The five mounting holes, **H101–H105 / H201–H205**, are on the front maps. Put a 0.5 mm shim on the
front of the PCB over each hole, stand an M2 × 3 mm standoff on it and screw it on from the back:
M2 × 3 button-head screws at **H102, H103 and H105** (left) and **H202 and H204** (right), M2 × 4
at the others. The shorter screws leave room for the plate screws that go into the same standoffs
from above.

### Step 12: Switch pads and plate foam

1. Stick a 0.5 mm Poron ring switch pad on the front of the PCB round each switch position (33), its
   notches facing the switch's clips (top and bottom) and its open middle round the pins and the
   LED window. Where a ring's corner meets a standoff (7 rings per half), snip that corner off
   first. Where a ring crosses a diode's two joints, snip a notch in it so it lies flat on the board.
2. Lay the 2 mm EVA plate foam over them.

### Step 13: Plate and OLED

1. Set the plate on the standoffs and screw it down with M2 × 3 button-head screws at
   **H102, H103 and H105** (left) and **H202 and H204** (right). H101, H104, H201, H203 and H205
   get no screw on top; the standoffs bear against the plate there.
2. **OLED J101 / J201.** Check that the pin order printed on the module is GND, VCC, SCL, SDA, the
   same as the footprint; some modules swap GND and VCC. Pass its header pins down through the
   plate's OLED window into the board, with the module resting on its plastic spacer, and solder
   them from the back. Trim the pins flush on the back: the battery lead runs under them.
3. Power the half and check the status screen appears.

### Step 14: Switches

- Check each switch's pins are straight, then press it through the plate into its socket while
  supporting the PCB behind the socket with your other hand.
- The two tall 1.25u thumb switches per half are turned 90°.

## 6. Close the case

### Step 15: Heat-set inserts

Lay the top frame deck-down and press the 8 M2 heat-set inserts into the blind holes in its
underside at about 200–230 °C, flush with the surface and no deeper (1.7 mm of frame covers each
hole), and let them cool.

### Step 16: Battery

- Tape the pouch into the bay in the bottom shell's floor with thin double-sided tape, its lead
  end towards the battery connector. With a short lead (step 6), plug it into **BT101 / BT201**
  first, holding the plate-and-PCB unit on its edge beside the shell, then lay the cell in its bay.
- Check the installed cell, protection board and tape thickness before closing: the modeled 1.0 mm
  gap at full gasket travel includes a 6.1 mm battery stack (5.0 mm cell, 0.3 mm thickness tolerance,
  0.5 mm swelling allowance and 0.3 mm tape) and underside parts no taller than 2.0 mm. Excess
  solder or a thicker battery stack uses that gap.
- Never press, fold or puncture the pouch.

### Step 17: Case foam

Lay the 5 mm EVA case foam on the floor of the bottom shell, round the battery in its bay.

### Step 18: Plate-and-PCB unit

1. Cut the Poron strips into 12 mm pieces and put one on each of the 8 gasket ledges, pushed to
   the ledge's outer end.
2. Plug the battery lead into **BT101 / BT201**, leaving it a loose loop: the unit floats, and a
   tight lead holds it down on one side.
3. Lower the plate-and-PCB unit onto the strips, with the controller's end down into its pocket
   behind the USB-C port and the slide switch in its opening. Hold the unit away from the top
   edge as it goes down: the switch lever clears that wall by only 0.2 mm.
4. Press the plate down near each tab: it should sink evenly on the strips and spring back, with
   nothing under it (the lead, a strip off its ledge) pressing on it or holding it.
5. Put a second piece on top of each plate tab.

### Step 19: Top frame

Fit the top frame. Holding the two parts together, turn the half over onto a soft cloth and drive
the 8 M2 × 16 screws up through the floor's counterbores evenly, a little at a time: snug, not
tight, so the gaskets stay soft. The closed half should not rattle when shaken, and the plate
should give a little when pressed in the middle; if it rattles, a strip has fallen off its ledge.

### Step 20: Keycaps, knob and final test

1. Fit the keycaps: per half, 26 × 1u and 7 × 1.25u (the two tall thumb caps turned 90°).
2. Push a knob onto each encoder shaft, stopping at least 2.5 mm above the deck so it clears the
   deck when the plate is pressed down.
3. Turn both halves on together so they pair with each other, then pair the host to Bluetooth
   profile 1 (SYS + `1`: hold both 1.25u thumb keys and press `1`).
4. Test every key on every layer, both encoders, both OLEDs, the LEDs on USB, and the link between
   the halves on battery. The keymap is in [`firmware/README.md`](firmware/README.md#keymap).

### Step 21: Feet and tenting

1. **Rubber feet.** Stick four 8 mm silicone bumpers on the floor, centred about 7 mm in from the
   edges: at the outer bottom corner and the tip under the thumb cluster, and at the outer and
   inner top corners with their centres 17 mm below the top edge. Lower than that, the outer top
   foot covers a screw counterbore, and the inner one the USB-C opening. Keep each one clear of the
   counterbores and the reset pinhole.
2. **Steel disc.** Press a 40 mm round steel plate, adhesive side down, into the round pocket in
   the floor. It sits flush, like the screw heads.
3. **Stand.** The tenting stand's magnetic puck holds to the disc, and the half tilts on its two
   outer feet. Pull the stand off to lay the half flat on its feet.

## Flashing

The firmware is three UF2 files: `keygen_left`, `keygen_right` and `settings_reset`. To get them,
open the [Firmware workflow](https://github.com/milindmadhukar/keygen/actions/workflows/firmware.yml)
on GitHub, pick the latest successful run, and download its `keygen-firmware` artifact (this needs
a GitHub account); unzip it. Artifacts expire after 90 days. Or build them yourself with `firmware/build.sh`
([`firmware/README.md`](firmware/README.md#building)).

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
