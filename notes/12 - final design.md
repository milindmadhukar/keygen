---
created: 2026-10-19
name: 12 - final design
tags:
  - keyboards
  - decision
updated: 2026-10-22T17:53
---
# Final Design

> [!success] Locked in on 2026-10-19
> This note is the source of truth for what Keygen *is*. The topical notes ([[01 - overview]] through [[11 - learning resources & references]]) go into more detail on each part; where they disagree with this note, this note wins.
>
> Visual build plan (layout drawing, tables, links): `~/Code/keygen/plan/index.html` in the private repo [milindmadhukar/keygen](https://github.com/milindmadhukar/keygen).

## Summary

A one-off, **flat, wireless split keyboard** built on the **Redox** key layout, with:

- **66 keys**, QWERTY, on Redox key positions, six columns per hand
- **Redox thumb cluster**: a 2×2 block (two 1u over two 1.25u, rotated 30°) plus one 1.25u key per hand
- **Two rotary encoders (knobs)**, one on each half's inner edge, mirrored
- **An OLED status screen on each half** (0.96 in., 128×64), plus **per-key RGB** that also shows status
- **Two nRF52840 controllers**, hidden under the PCB, USB-C through the case
- **Bluetooth or USB-C** to the computer, **Bluetooth** between halves
- **ZMK** firmware
- **Custom PCB** designed in KiCad 10 (the PCB-learning goal), 3D-printed closed case, tented with a printed wedge

No v2 is planned. At most two complete keyboards get built.

## Layout

Based on [mattdibi/redox-keyboard](https://github.com/mattdibi/redox-keyboard) (MIT, © 2018 Mattia Dal Ben). Key coordinates come from its `img/redox-layout.json`.

Keygen uses Redox's six main columns per hand. The space beside T/G and Y/H holds a knob on each half, with an OLED above it.

### Base layer

| Row | Left half | Right half |
|---|---|---|
| Number | `=` `1` `2` `3` `4` `5` | `6` `7` `8` `9` `0` `-` |
| Top | `Tab` `Q` `W` `E` `R` `T` | `Y` `U` `I` `O` `P` `\` |
| Home | `Esc`/`Ctrl` `A` `S` `D` `F` `G` | `H` `J` `K` `L` `;` `'` |
| Bottom | `Shift` `Z` `X` `C` `V` `B` | `N` `M` `,` `.` `/` `_` |
| Extra | `` ` `` `CapsWord` `(` `)` | `[` `]` `{` `}` |

The outer columns are 1.25u. The extra bottom row follows the Kinesis Advantage. In the keymap the number row has 14 positions, with the two knob presses in the middle (position 6 = left knob, 7 = right knob), so the keymap has 68 positions in all.

> [!success] Keymap decided (2026-10-20), for a Vim + Hyprland user with small hands
> - **Blank keycaps**, so only the letters are fixed (QWERTY); everything else is free to move.
> - **Esc key = tap Esc, hold Ctrl** (balanced hold-tap, 200 ms): Esc and Ctrl-w/d/u/r on the home row for Vim.
> - **Extra row = brackets**: every bracket pair without Shift. Arrows are on HJKL in the Nav layer.
> - **Caps = Caps Word** (types ONE_WORD in capitals, then stops); Caps Lock is on Fn.
> - **Number row kept**: Hyprland's Super+1…0 workspaces need it. A numpad sits on the Fn layer for long number entry.
> - Config: `firmware/keygen.keymap` in the repo.

### Thumbs

| Key | Left | Right |
|---|---|---|
| 1.25u, hand side (rest) | `Backspace` | `Space` |
| 1.25u, centre side | `Super` | `Enter` |
| 1u, over the rest key | `Ctrl` | `:` |
| 1u, over the centre key | `Alt` | Dictate (`Ctrl`+`Alt`+`Space`) |
| 1.25u, toward the palm | hold `Nav` | hold `Fn` |

**Super** sits one step from the resting thumb because Hyprland uses it constantly: Super + number row for workspaces, Super + HJKL for focus, Super + Enter/Space across both thumbs. Shift, Ctrl and Alt live on the left half only, so the right half's keys each do something of their own: `:` opens Vim's command line in one press, and Dictate sends `Ctrl`+`Alt`+`Space`, OpenWhispr's dictation toggle in Hyprland. Del is Fn + Bksp. Both 1.25u keys are layer keys; holding both gives the System layer.

Every 2×2 key is at most one step from where the thumb rests. That keeps the whole cluster in reach for small hands.
The upper two keys stay 1u: with 1.25u lower caps, they can sit 4.76 mm closer to the resting thumb than before. Making the upper caps 1.25u too would push their switch centres 2.38 mm back to preserve cap clearance.

### Nav, Fn and System layers

- **Nav** (hold left 1.25u): **arrows on `H` `J` `K` `L`** (← ↓ ↑ →), vim-style; `Y` `U` `I` `O` = Home, PgDn, PgUp, End; `A` `S` `D` `F` = plain Super, Alt, Ctrl, Shift so modified arrows need one hand. Nav is on the opposite thumb to HJKL so Shift + arrow selection is comfortable.
- **Fn** (hold right 1.25u): F1–F12 on the number row; numpad `7 8 9 / 4 5 6 / 1 2 3` on `U I O / J K L / M , .`, with `0` and `.` on `[` `]`; Del on Bksp, Caps Lock, PrtSc, Ins, media keys.
- **System** (hold both): Bluetooth profiles 1–5 on the number keys, USB/Bluetooth output, LED controls, ZMK Studio unlock, reset and bootloader per half.

### Knobs

Each half has an EC11 encoder (push switch, 20 mm D shaft) with a 17 × 13 mm knurled aluminium knob (a "D halfshaft 17x13" amplifier knob) on its inner edge, mirrored: the right shaft is at (256.5, 134.5) and the left at (167.0, 134.5) in board coordinates (KiCad mm). On both halves the knob's edge sits 10 mm below the OLED, 5.7 mm from the thumb cluster's top key and 9.1 mm from the G/H column, close enough to reach with the thumb.

| Layer | Left knob | Right knob |
|---|---|---|
| Base | scroll wheel; press: middle click | volume; press: mute |
| Nav | scroll wheel | Page Down / Page Up |
| Fn | scroll wheel | screen brightness; press: play/pause |

- **Left knob:** a scroll wheel on every layer, through ZMK's mouse emulation (`CONFIG_ZMK_POINTING`). With Super held it walks Hyprland's workspaces through the existing Super + mouse-wheel bind (`workspace e+1 / e-1`).
- Both encoders are defined in the shared `.dtsi`, each enabled in its half's overlay. ZMK has supported encoders on the peripheral half since PR #1841 (Oct 2023).

## Status display

Each half has a 0.96 in. OLED running ZMK's status screen, which is the main status display:

- **Left (central):** output (USB/BLE), Bluetooth profile, layer and battery
- **Right:** its own battery and link
- It blanks when the keyboard goes idle (`CONFIG_ZMK_DISPLAY_BLANK_ON_IDLE`).

The per-key LEDs also show status:

- caps lock lit
- layer shown by colour
- active Bluetooth profile on the number keys
- battery level while Fn is held

Per-key indicators need the community module [zmk-rgb-matrix](https://github.com/dima-m711/zmk-rgb-matrix). Stock ZMK drives all the LEDs as one strip.

> [!warning] Per-key status comes later (2026-10-20)
> The first firmware drives the 33 per-key RGB backlights per half as one ZMK lighting strip; there is no case underglow. ZMK's addressable RGB driver is named `RGB_UNDERGLOW` even for per-key lights. Its power-off behavior needs the battery-only measurement in [`docs/logic-audit.md`](../docs/logic-audit.md): 33 dark but powered SK6812s draw about 33 mA per half. The per-key module is [gudzpoz/zmk-rgb-matrix](https://github.com/gudzpoz/zmk-rgb-matrix) (the `dima-m711` repo is a fork); per-key indicators remain future firmware work.

## Electronics

### Controllers

- **One per half: an nRF52840 SuperMini** (decided 2026-10-23), a nice!nano v2 clone with the same 24-pin Pro Micro header and pinout, built in ZMK as the nice!nano v2. It charges at about 100 mA (TP4054): roughly a day for an empty 2500 mAh cell with lighting off. Its BOOST jumper (about 300 mA) stays open. On USB the controller runs from USB; the LEDs still draw from the cell rail when lit. Before soldering, check B+ (pad 13), GND and VCC (pad 16) with a multimeter, and confirm the charge current.
- **Hidden:** mounted on the PCB underside near the inner edge, socketed with low-profile Mill-Max pins (adds about 3–4 mm of case depth). USB-C faces the top edge and reaches out through a slot in the case.
- **Why two:** each half runs on its own battery and radio. More on the controller: [[03 - microcontroller selection]].

### Controller pin map

Identical on both halves. Every one of the 18 edge pins is used. The pad numbers follow marbastlib's `nice_nano_H_USBup` footprint: pads 1–12 run down the left edge and 13–24 down the right, with USB at the top.

| Pad | Pin | Left | Right |
|---|---|---|---|
| 1 | P0.06 | LED data | LED data |
| 2 | P0.08 | LED power switch | LED power switch |
| 5 | P0.17 | OLED SDA (full speed) | OLED SDA (full speed) |
| 6 | P0.20 | OLED SCL (full speed) | OLED SCL (full speed) |
| 7–11 | P0.22, P0.24, P1.00, P0.11, P1.04 | ROW0–ROW4 | ROW0–ROW4 |
| 12, 22, 21, 20, 19, 18, 17 | P1.06, P1.11, P1.13, P1.15, P0.02, P0.29, P0.31 | COL0–COL6 | COL0–COL6 |
| 23 | P0.10 (NFC) | encoder A (`nfct-pins-as-gpios`) | encoder A (`nfct-pins-as-gpios`) |
| 24 | P0.09 (NFC) | encoder B (`nfct-pins-as-gpios`) | encoder B (`nfct-pins-as-gpios`) |
| 13 / 14 / 15 / 16 | B+ / GND / RST / VCC | battery via switch, LED power switch / GND / reset button / OLED power (switched 3.3 V, on via P0.13) | same |

The three inner pads (P1.01, P1.02, P1.07) are unused.

### Matrix

The matrix is COL2ROW: each switch connects to its column, and the diode cathode connects to its row. There are 5 rows and 7 columns (column 0 is the outer edge on both halves).

- **Column 6** holds Alt (row 2), Ctrl (row 3) and the 1.25u centre-side thumb key (row 4).
- **Row 4** holds the extra bottom row and the thumbs.
- **Both halves:** each encoder's push switch sits at row 0 / column 6, with its own 1N4148 (D107 left, D207 right, on the back beside the encoder).
- **Left references:** the left keys are SW101–SW106 and SW108–SW134, with diodes D101–D106 and D108–D134.

### OLED

- **Module:** a generic 0.96 in. 128×64 **SSD1306 I2C** module per half (address 0x3C), J101 / J201. Its own pull-ups and regulator are used, with the controller's internal pull-ups on as well. The firmware gives the I2C (TWIM) driver a 1025-byte buffer so a whole 1024-byte frame goes out in one transfer, as the SSD1306 needs.
- **Footprint:** a 1×4 2.54 mm header footprint, pin order **GND, VCC, SCL, SDA**, with a right-angle header the module's lead plugs onto. Check the module's printed order before soldering; some swap GND and VCC.
- **Wiring:** SDA on P0.17 (pad 5), SCL on P0.20 (pad 6), both full-speed pins. Power comes from the controller's VCC (pad 16), its switched 3.3 V output, which P0.13 turns on. The firmware holds P0.13 high with a gpio-hog, so the OLED stays powered on battery.
- **Mounting:** the module (27.5 × 27.8 mm) sits in the top frame on four pegs through its Ø 2 mm corner holes, their tips melted over (or glued) on its back. Its glass sits in a pocket under a 1.0 mm lip, 1.0 mm below the top surface, and its board on a boss that thickens the deck down to it, relieved over its solder joints and the glass's flex cable. A 45 mm lead of four jumper wires soldered to it, their plugs glued into one 4-pin plug, plugs onto a right-angle header in J101/J201, lying flat under the module (2.8 mm tall) in the plate's 29.5 × 29.8 mm OLED window, which clears the module by 0.5 mm all round with the plate floated sideways. The module stays with the case while the plate and PCB float, and the top frame comes off by unplugging it.
- **Position:** over the lower (antenna) end of each controller, in the free area above the knob. Right module x 242–269.5, y 88–116; left x 154–181.5, y 88–116 (board coordinates). The module is 4.6 mm from the nearest keycaps on either half; the nearby M2 holes sit below the reset switches. The header runs along the module's bottom edge, so the firmware draws the text turned 180°. Sitting over the antenna end costs some Bluetooth range, as with a display over a nice!nano on a Corne.

### Schematic

Everything lives in **one KiCad project**, `pcb/keygen.kicad_pro`:

- **Schematic:** a top sheet with `left` and `right` sub-sheets. References are 1xx on the left and 2xx on the right, and each half keeps its own nets.
- **PCB:** both halves in one board file as two separate outlines, exported and ordered as two designs, 5 of each.
- **Generated:** the schematics are generated by `tools/gen_schematic.py`, so edit its tables rather than the files.
- **Checked:** `tools/check_schematic.py` runs KiCad's electrical rules check (ERC) and compares KiCad's netlist with the tables. Both halves pass with zero violations as of 2026-10-20.
- **PDF:** [`keygen-schematic.pdf`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-schematic.pdf).
- **Datasheet audit:** `tools/check_datasheets.py` checks the routed PCB against each part's datasheet (`docs/datasheets/`): 109 pass, 15 warnings, 0 fail as of 2026-10-28. Operating limits: [`docs/logic-audit.md`](../docs/logic-audit.md). Findings and learnings: [[15 - datasheet audit]].

> [!note] LED supply
> The LEDs run from the battery (B+, 3.0–4.2 V) through a high-side **AO3401A P-MOSFET** (Q2). An **AO3400A N-MOSFET** (Q3), driven from P0.08, pulls Q2's gate low to turn them on. A 100 kΩ resistor from Q2's gate to its source (R2) and one from Q3's gate to GND (R3) hold both off before firmware configures the output. The SK6812MINI-E is rated for **VDD 3.7–5.5 V**, so this raw battery rail cannot keep it in specification over the full discharge range. The 10 µF + 100 nF capacitors sit at Q2's output, rather than one bypass capacitor per LED as in the manufacturer's example. The controller's switched 3.3 V VCC output powers only the OLED. All the resistors and capacitors are 1206, for hand soldering.

### Connectivity

| Link | Connection | Switching |
|---|---|---|
| Keyboard ↔ computer | Bluetooth (5 profiles) or USB-C on the left half | Live: one key, and USB takes priority when plugged in |
| Left ↔ right | Bluetooth split | One firmware build per half |

The left half is the ZMK central. Plugging USB-C into it is the wired mode, and it charges that half while the halves stay on Bluetooth. Both halves run on battery, so the keyboard works away from the desk too; at the desk a 1-to-2 USB-C cable to the computer lights and charges both halves.


### Power

- **LiPo pouch per half: 505080 (5 × 50 × 80 mm), about 2500 mAh**, on a JST-PH 2.0 lead, with a protection board (decided 2026-10-23). It is listed as 3000 mAh; a 505080 holds about 2500. The controller has no over-discharge cut-off, so a cell sold without a protection board gets a DW01A module. The bay takes a cell up to 5 mm thick and 60 × 88 mm including the protection board; a thicker cell would raise the case.
  - **Where:** in a bay sunk 1.6 mm into the case floor, under the outer and middle key columns (1–4, Q–R, A–F on the left; mirrored on the right), long side across the board, held with double-sided tape. Its lead end faces the JST-PH connector, about 40 mm away. The cell keeps at least 15 mm from the controller's antenna end and 10 mm from the controller, connector, buttons, encoder and OLED pins. `tools/case_geometry.py` places it and `tools/gen_case.py` checks it. Positions: [[14 - case & plate requirements]].
  - **Height:** the case reserves 7.5 mm below the PCB for the socketed controller plus 1.5 mm of float travel, so the case floor is 9.0 mm below the PCB's underside and the bay 10.6 mm. A 5 mm nominal cell, plus 0.3 mm size tolerance, 0.5 mm swelling and 0.3 mm mounting tape, leaves 2.5 mm to the sockets and diodes above it, and 1.0 mm with the floating stack pressed 1.5 mm down. In the case: PCB top 13.6 mm above the desk, plate top 18.6 mm, keycap tops about 33 mm before tenting.
- **Charging:** each half charges from its own USB-C at about 100 mA, roughly a day from empty with lighting off; a 1-to-2 USB-C cable supplies both from one USB source. Battery life has not been measured. On USB the controller and OLED run from USB, while the LEDs on B+ can draw more from the cell than the charger replaces. Confirm LED_VDD is off on battery before estimating runtime (see [`docs/logic-audit.md`](../docs/logic-audit.md)).
- **Battery switch** (decided 2026-10-20): the MSK12C02 slide switch (rated 50 mA) only drives the gate of an **AO3401A P-MOSFET** that carries the battery current, so charging and LED current never pass through its contacts. Source on the battery, drain on B+, so the body diode blocks the battery when off. A 1 MΩ resistor holds the gate off between positions. Leave the switch on while charging: switched off with USB in, charge current can cross the body diode and the MOSFET warms (~0.07 W at 100 mA), but full-charge termination is not assured. The controller has a charger but no switch.
- **LEDs powered from the battery through the LED power switch** (Q2/Q3, P0.08; see [[#Schematic]]). Each SK6812 draws about 1 mA even when dark, about 33 mA per half. The pinned ZMK driver enables ext-power at startup, so confirm the rail actually turns off in each battery state. Brightness is capped at 40%, still about 508 mA per half at the datasheet's typical full-white current reference; this can exceed the 100 mA charge rate while USB is connected. See [`docs/logic-audit.md`](../docs/logic-audit.md).
- Per-key status flashes on battery are planned firmware work. The first ZMK build has whole-strip effects only, requested for USB operation; battery-only rail-off behavior needs the measurement in [`docs/logic-audit.md`](../docs/logic-audit.md).

### Parts per half

| Part | Left | Right | Mount |
|---|---|---|---|
| nRF52840 module (socketed, underside) | 1 | 1 | header |
| MX switch + Kailh MX hotswap socket | 33 | 33 | hand-solder |
| 1N4148 diode (DO-35) | 34 | 34 | TH |
| SK6812MINI-E (per-key) | 33 | 33 | SMD (hand-solder or JLC assembly) |
| 10 µF + 100 nF capacitors, 1206 (LED rail) | 1 + 1 | 1 + 1 | SMD |
| 505080 LiPo + JST-PH 2-pin | 1 | 1 | TH |
| MSK12C02 slide switch | 1 | 1 | SMD |
| AO3401A P-MOSFET + 1 MΩ resistor, 1206 (battery switch) | 1 + 1 | 1 + 1 | SMD |
| AO3401A P-MOSFET, AO3400A N-MOSFET, 2 × 100 kΩ, 1206 (LED power switch) | 1 + 1 + 2 | 1 + 1 + 2 | SMD |
| 6 mm reset button (pinhole in case) | 1 | 1 | TH |
| EC11 encoder (D shaft) + 17 mm knob | 1 | 1 | TH |
| 0.96 in. SSD1306 I2C OLED module, 128×64 (J101 / J201) | 1 | 1 | TH (right-angle header; the module plugs in) |

Each half has 34 diodes: 33 for the keys and one for its encoder's push switch, which sits in the key matrix. 3D models of the knob and the OLED module (`pcb/lib/keygen.3dshapes/Knob_17mm.step`, `OLED_096_I2C.step`) are made by `tools/gen_models.py`. Keygen is a single build. JLCPCB's minimum is 5 per design, so order **5 left + 5 right** boards and keep the rest as spares. Full shopping list: [[13 - bill of materials]].

### Keycaps

**14 × 1.25u** (8 outer column, 2 thumb, 4 tall thumb), **52 × 1u**. Nothing is wider than 1.25u, so **no stabilizers** are needed. Uniform-profile caps are easiest because the thumb keys are rotated.

- **Keycaps** (decided 2026-10-20): blank **DSA PBT in smoke translucent**, so the per-key status LEDs show through. All sizes from one AliExpress seller (SZElectronic Store) in its translucent black, every key the same.
- **Switches** (decided 2026-10-20): **Akko V3 Lavender Purple Pro**, a light tactile with a clear top.
- Sources and reasons: [[07 - switch & keycap selection]], [[13 - bill of materials]].

### Pin budget (nRF52840, 21 usable)

| Function | Left | Right |
|---|---|---|
| Matrix (5 rows × 7 cols) | 12 | 12 |
| Encoder A/B | 2 | 2 |
| RGB data | 1 | 1 |
| LED power switch | 1 | 1 |
| OLED SDA/SCL | 2 | 2 |
| **Total** | **18** | **18** |

These use all 18 GPIO along the standard Pro Micro edge pads on both halves: 12 matrix, LED data (P0.06), LED power switch (P0.08), OLED (P0.17, P0.20) and encoder (P0.10, P0.09). The encoder lines are on the two NFC pins, which work as GPIO once `nfct-pins-as-gpios` is set on both halves; they are slow inputs. The three inner pads (P1.01, P1.02, P1.07) stay unused. They're "low-frequency" pins, fine for matrix lines but not for LED data or UART.

## Firmware: ZMK

ZMK brings:

- Bluetooth split
- USB plus 5 Bluetooth profiles
- Encoders on both halves, including the peripheral
- A status screen on each half's OLED
- Mouse emulation, for the left knob's scroll
- ZMK Studio for live remapping, which the [Dactyl CC](https://www.reddit.com/r/ErgoMechKeyboards/comments/1tp0r9s/) builder calls a must-have
- External power control for the LED power switch

The one community module needed is `zmk-rgb-matrix` for per-key RGB and indicators. See [[04 - firmware options]].

### Firmware as built (2026-10-20)

- **ZMK `main`** at `4dd95d78` (Zephyr 4.1). v0.3 is the last release but uses Zephyr 3.5; v0.4 is in PR #3024. The board is now named `nice_nano//zmk`, not `nice_nano_v2`.
- Zephyr 4.1 changes that mattered: NFC pins as GPIO is `&uicr { nfct-pins-as-gpios; };` (the Kconfig option is gone), EC11 needs `CONFIG_EC11_TRIGGER_GLOBAL_THREAD=y`.
- The config lives in `firmware/` of the hardware repo. ZMK's reusable workflow can't handle a nested config path (issue #3006), so `config_path: firmware` with the shield under `firmware/boards/`; that board root is deprecated but works.
- The physical layout for ZMK Studio is generated from the PCB's KLE by `tools/gen_zmk_layout.py`.
- Both halves set `&uicr { nfct-pins-as-gpios; };` for the encoder lines. ZMK's ext-power drives only the LED power switch (P0.08); a gpio-hog holds P0.13 high so the OLED keeps its power. `CONFIG_ZMK_DISPLAY` runs the status screen, and `CONFIG_ZMK_POINTING` the left knob's scroll.

## PCB

- **Redox geometry, Keygen's own copper.** Key positions come from Redox; the schematic, placement and most of the routing are generated in KiCad 10 by the scripts in the repo's `tools/`, with footprints from marbastlib and Keebio-Parts.
- **Separate left and right layouts** (decided 2026-10-20), each with every part on its own side. Both sit in one PCB file as two outlines.
- Keep **ground pour away from the controller's antenna end**.
- Fabricate at **JLCPCB** with a lead-free **HASL** finish and no order-number mark.

See [[05 - pcb design]].


### PCB status (2026-10-20)

**Fully routed.** KiCad DRC shows 0 unconnected, 0 errors and 0 schematic-parity issues. The only remaining warnings are cosmetic silkscreen ones.

- **Placement:**
  - Generated from Redox's KLE.
  - The tall 1.25u thumb keys are turned 90°.
  - Both halves sit on one A3 sheet in one KiCad project.
  - The bottom edge runs flat along the bottom row, then along the thumb keys at 30° (`tools/trim_outline.py`).
- **Look:** black soldermask with white silkscreen artwork from the *Keygen* cover (`tools/silkscreen_art.py`): the keygen.exe window on the left half, moon and STMPD emblem by the right half's encoder, GENERATE under each reset button, stars on free board area.
- **Routing:**
  - **Freerouting** did about 85% of the signal routing, with ground left to the fill.
  - A **custom grid maze router** (`tools/finish_route.py`) finished the rest.
  - Ground is a fill on both layers per half. About 280 stitching vias plus a few targeted ones join the front and back fill pieces.
  - The ground fill is kept out from under each controller's antenna end.
- **Rules:**
  - Signal 0.25 mm, power 0.4 mm, 0.2 mm clearance.
  - Minimum track 0.15 mm and hole-to-hole 0.25 mm, within JLCPCB's 2-layer capability.
  - Copper-to-edge 0.2 mm, because the reverse-mount LED pads sit 0.25 mm from their light cut-out; check this in JLCPCB's DFM.
- **Fabrication files:** made by `tools/export_fab.py` into `fab/`; the Gerber zips are downloaded from the [build release](https://github.com/milindmadhukar/keygen/releases/tag/build):
  - **`keygen-left-gerbers.zip` and `keygen-right-gerbers.zip`: order these, as two orders of 5.** Per half is how they are ordered.
  - `keygen-gerbers.zip`: both halves in one design, kept in case another fab prices that better.
  - `BOM.md`, `BOM-left.csv`, `BOM-right.csv`: the **assembly BOM** from the schematic, giving every part's references per half, quantities for 1 and 2 keyboards, and soldering notes. Made by `tools/export_bom.py`.
  - `ORDER.md`: the order-form settings. Bare boards, 2 layers, 1.6 mm, HASL lead-free, no assembly, no stencil. You solder everything yourself.

## Case

- **3D-printed PETG, closed, gasket-mounted**: a bottom shell and a top frame per half, 175.4 × 143.7 × 22.6 mm. The top frame's deck, level with its rim, covers the plate everywhere but the keycaps, the OLED and the knob. Plastic all round keeps the Bluetooth antenna clear.
- **Switch plate: 1.5 mm clear polycarbonate**, CNC-routed from solid sheet, three halves per 6 × 24 in. (152 × 610 mm) strip. It rests on M2 × 3 mm standoffs on 0.5 mm shims, screwed to the PCB from below, and the switches hold it to the PCB; and its 8 tabs per half float between Poron strips clamped by the case. Each half's plate has a 15 × 15 mm encoder cut-out and a 29.5 × 30 mm OLED window.
- A rounded **USB-C port**, sized for a plug carried by the floating stack, and a **power switch slot** on the top edge, with the wall thinned outside them, and a guided **reset pinhole** in the floor. The reset buttons mirror between the halves (left origin at x 182.85), and so do the pinholes.
- 7.5 mm under the PCB for the socketed controller, plus 1.5 mm to float; the ≤ 5 mm nominal battery fits with thickness and tape allowances.
- Foam for a thocky sound: a 0.5 mm Poron ring switch pad under each switch, 2 mm EVA plate foam taped under the plate and 5 mm EVA case foam.
- **Tenting** with an optional printed 13° wedge per half, held by four magnets to a steel plate on the floor; four rubber feet for flat use.

The case and plate are generated from the PCB by `tools/gen_case.py` and `tools/gen_plate.py`. See [[09 - case design]].

## Build order

1. **Fit test:** print [`keygen-plate-print.pdf`](https://github.com/milindmadhukar/keygen/releases/download/build/keygen-plate-print.pdf) at 1:1 and check the 2×2 thumbs and the knob spots with your real hand.
2. Schematic per half, generated and ERC clean. **Done.**
3. Place and route, DRC clean. **Done.**
4. **Optional bring-up board:** 4 keys, encoder, OLED, 4 LEDs and an underside controller, to prove every circuit cheaply.
5. JLCPCB order (5 left + 5 right), assembly, flash the ZMK left/right UF2s.
6. Case, foam, weight, tenting.

## Pre-order checklist

- [ ] Controller footprint includes the 3 inner pads
- [x] Pin functions checked (Modular-build lesson: "not all pins are created equal"). Done 2026-10-20 in [[15 - datasheet audit]]: LED data on a full-speed pin, only slow signals on low-frequency pins, no bootloader-sampled pins
- [x] LEDs behind their own power switch (P0.08), off with the LEDs; brightness capped in firmware
- [x] Each half is self-contained on its own battery; nothing is wired between the halves
- [x] USB-C lines up with the case slot: `tools/gen_case.py` checks the case against the controller, and [`render-case.png`](https://github.com/milindmadhukar/keygen/releases/download/media/render-case.png) shows it (2026-10-22)
- [x] Antenna end clear of ground pour; plastic case. Keep-out rule areas restored on the board 2026-10-20, and the PCB scripts now keep them through every re-pour
- [x] "+" marked on the silkscreen next to the battery connector's + pad (2026-10-20, beside pad 1 of BT101/BT201; still check each battery's red wire)
- [ ] LED chain tested one column at a time (one bad joint kills the rest)
- [ ] Controller socketed
- [ ] Weight planned into the case

## Sources

- Thread: [[02 - layout design]] → [[06 - split architecture]] → this note
- Builds: [[video notes]] (Corne guide, KiCad PCB, Dungeon Delver, Modular, Dactyl)
- Reddit (r/ErgoMechKeyboards):
  - [Third Redox, First Wireless](https://www.reddit.com/r/ErgoMechKeyboards/comments/1fpv3d7/)
  - [DIY Wireless Redox using nice!nano](https://www.reddit.com/r/ErgoMechKeyboards/comments/wafgyf/)
  - [The Wolf](https://www.reddit.com/r/ErgoMechKeyboards/comments/1x8d8sb/)
  - [Dactyl CC](https://www.reddit.com/r/ErgoMechKeyboards/comments/1tp0r9s/)
  - [Elora Hyper Case](https://www.reddit.com/r/ErgoMechKeyboards/comments/1ls6857/) (small hands + aggressive stagger)
  - [Harite](https://github.com/dlip/harite) (BLE + USB, open source)
- ZMK:
  - [split keyboards](https://zmk.dev/docs/features/split-keyboards)
  - [peripheral encoders](https://zmk.dev/blog/2023/10/05/zmk-sotf-6)
  - [displays](https://zmk.dev/docs/features/displays)
  - [lighting](https://zmk.dev/docs/features/lighting)
