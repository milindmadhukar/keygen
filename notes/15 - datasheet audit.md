---
created: 2026-10-20
name: 15 - datasheet audit
tags:
  - keyboards
  - pcb
updated: 2026-10-22T15:00
---
# Datasheet Audit

> [!success] Result (2026-10-20): no wiring mistakes
> `tools/check_datasheets.py` in the repo checks the routed PCB against each part's datasheet: **85 pass, 0 fail, 8 warnings** (2026-10-20). Re-run it after any PCB change, with `-v` to list the passes too. The datasheets themselves, with sources and page references, are in `docs/datasheets/`. Design: [[12 - final design]]. Assembly: [[10 - assembly & build guide]].

## How the checking fits together

There are three checks, each covering a different gap:

1. `tools/check_schematic.py`: the schematic matches the design tables in `gen_schematic.py` (plus KiCad's electrical rules check).
2. `kicad-cli pcb drc --schematic-parity`: the PCB matches the schematic.
3. `tools/check_datasheets.py`: the design tables are **right for the parts**. Nothing else checked this.

The audit reads the `.kicad_pcb` file, the thing that gets fabricated. It checks **physical pad positions**, not just pin numbers, because footprint numbering can disagree with the datasheet.

To prove the test catches real mistakes, I fed it deliberately broken copies of the board, and it flagged every one. They included a mirrored controller pinout, a mirrored LED footprint, a reversed diode, LED data on a low-frequency pin, and the battery bypassing the switch.

## Learnings

### nRF52840 pins
- **No bootstrapping pins.** Unlike the ESP32, every nRF52840 GPIO resets to a disconnected input, and nothing on the GPIOs decides how the chip boots. P0.18 is reset; P0.00/P0.01 are the 32 kHz crystal; SWD has dedicated pins.
- **Bootloader:** the nice!nano's Adafruit bootloader 0.6.0 defines DFU = P0.18 (reset) and FRESET = P0.19 (not connected), and current master says "no buttons". **No edge pad is read at power-up**, so a held key can't push the board into DFU. Double-tapping RST within 500 ms enters the bootloader.
- **"Low frequency" pins (≤ 10 kHz)** come from the *Recommended usage* column of Table 142 in the nRF52840 spec (aQFN73 ball assignments, p. 578). The nRF52840 has no "GPIO near the radio" section; that is the nRF52832's document. The restricted pins on the edge pads are P0.02, P0.09, P0.10, P0.29, P0.31, P1.04, P1.06, P1.11, P1.13 and P1.15, plus the inner pads P1.01, P1.02 and P1.07. The nice!nano pinout image colours exactly these purple. Running faster signals on them can upset the radio.
  - LED data (SPI at 4 MHz) is on **P0.06**, unrestricted. **P0.08** drives the LED power switch (a slow output). The OLED's I2C is on **P0.17** (SDA) and **P0.20** (SCL), both full-speed pins.
  - The encoder's A and B lines (P0.10, P0.09) are slow inputs, so the low-frequency NFC pins suit them.
  - The matrix columns and ROW4 *are* on low-frequency pins. That's fine: ZMK scans about once per millisecond (~1 kHz).
- **NFC pins P0.09/P0.10** stay NFC antenna pads until UICR.NFCPINS is cleared. With ZMK's Zephyr 4.1, the old `CONFIG_NFCT_PINS_AS_GPIOS` is gone; use devicetree `&uicr { nfct-pins-as-gpios; };`. Once written, the setting sticks until UICR is erased. When driven to different levels, the two pins leak 1–10 µA between each other.
- **Absolute maximum on any I/O is VDD + 0.3 V.** Every signal on a pin comes from inside the half, at 3.3 V.

### nice!nano v2
- Pinout verified pad by pad against the official image. **Mounted on the underside, the component side (chip, USB-C) must face away from the PCB.** That's what the footprint assumes. Soldered the other way, the columns swap and battery + lands on a GPIO.
- P0.13 *low* cuts VCC on the v2. The "high" wording in the docs is for v1. VCC (pad 16) powers the OLED, so the firmware holds P0.13 high with a gpio-hog. Battery voltage is read internally (VDDH), so it uses no pin.
- Charging is **100 mA** by default; bridging the BOOST jumper gives 500 mA, only for batteries over 500 mAh. The charger is a BQ24075.
- No VCC current limit is published, and no antenna position or keep-out. The renders show bare board at the end away from USB-C, so the audit keeps the last 6 mm clear.

### Parts
- **SK6812MINI-E:** the datasheet numbers the pins 1 VDD, 2 DOUT, 3 GND, 4 DIN. KiCad's symbol uses 1 VSS, 2 DIN, 3 VDD, 4 DOUT. They still line up physically: the reverse-mount footprint is the datasheet's lens-side view mirrored, which is correct because the lens faces the board. The chamfered corner is GND. When ordering assembly, check the fab's placement preview against that.
  - VDD is rated 3.7–5.5 V. The LEDs get the battery's 3.0–4.2 V through the LED power switch, inside spec until the cell runs low. VIH = 0.7 × VDD: 2.94 V at a full cell, against the nRF52840's VOH ≥ VDD − 0.4 V = 2.9 V at 0.5 mA (p. 157). The LED input draws microamps, so P0.06 sits near 3.3 V, but the datasheet margin is thin.
  - 12 mA per colour, so 33 LEDs at full white ≈ 1.2 A per half. Each LED also draws 1 mA even when dark (≈ 33 mA per half), which is why the LEDs sit behind their own power switch.
- **MSK12C02-HB power switch:** pin ② is common, and the pins are *not* evenly spaced (③ 1.5 mm ② 3 mm ①). Rated **50 mA at 12 V DC**. So it only drives the gate of an AO3401A P-MOSFET, which carries the battery current, including 500 mA BOOST charging.
- **EC11:** A C B in a row with C (common) in the middle, and the push switch on the other side. Swapping A and B only reverses the rotation direction, which firmware can fix.
- **AO3401A:** SOT-23 pins 1 G, 2 S, 3 D, matching KiCad's symbol. RDS(on) < 85 mΩ at VGS = −2.5 V, so the battery's −3.0 to −4.2 V gate drive turns it fully on (about 43 mV drop at 500 mA). Its body diode runs drain to source: with the source on the battery and the drain on B+, it blocks the battery when the switch is off. With the switch off and USB in, the charger still fills the cell through that diode, about 0.35 W.
- **AO3400A:** SOT-23 pins 1 G, 2 S, 3 D, like the AO3401A. VGS(th) 0.65–1.45 V, so P0.08's 3.3 V turns it fully on (RDS(on) < 48 mΩ at VGS = 2.5 V). It pulls the LED switch's gate low, so that AO3401A sees −3.0 to −4.2 V, as the battery switch does.
- **JST PH:** JST defines no battery polarity, and LiPo packs come wired both ways round.

## Open warnings

> [!success] Fixed 2026-10-20
> - **Antenna keep-out.** `load_without_zones()` now keeps rule areas and `ground_pours()` adds back any missing antenna keep-out, so re-pours can't put ground under the antenna. Both keep-outs are on the board. About 20 signal tracks per half still cross the antenna end; that matters much less than solid ground.
> - **Battery polarity.** A "+" is printed beside pad 1 of BT101/BT201. Still check each battery's red wire before plugging it in: a reversed pack destroys the charger.

> [!note] Firmware (ZMK)
> - Both halves: `&uicr { nfct-pins-as-gpios; };`, or the encoder lines (A on P0.10, B on P0.09) read dead.
> - Hold P0.13 high (gpio-hog) so the OLED keeps its 3.3 V supply.
> - Cap the LED brightness, and keep ext-power control on so the LED power switch (P0.08) cuts the LEDs when they are off.
> - Matrix: `diode-direction = "col2row"` (cathodes are on the rows).

> [!note] Accepted, but outside datasheet limits
> - LEDs below their 3.7 V minimum once the cell runs under 3.7 V; LED data has a thin datasheet margin at a full cell (VIH 2.94 V against VOH ≥ 2.9 V).
> - Switch off with USB plugged in: the cell still charges through the AO3401A's body diode, about 0.35 W (+44 °C on the SOT-23). Leave the switch on while charging.

## Datasheets

All in `docs/datasheets/` in the repo. Its `README.md` lists each source and the page every fact comes from, and has English translations of the Chinese notes on the MSK12C02 drawing. The nRF52840 spec is v1.1 (Nordic blocks scripted downloads); its pin table matches the current online spec.
