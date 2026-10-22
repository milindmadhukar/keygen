---
created: 2026-03-09
updated: 2026-10-22T15:00
name: 06 - split architecture
---

> [!success] Decision (2026-10-19, reconfirmed 2026-10-22)
> **Two separate halves, one nRF52840 controller and one LiPo each, linked over Bluetooth.** The left half is the ZMK central and the right half its peripheral. The host connection is Bluetooth (5 profiles) or USB-C on the left half. See [[12 - final design#Connectivity]].

## Why a wireless two-piece split

- **Ergonomics:** each half sits where its hand wants it, at shoulder width, and tents on its own.
- **Anywhere use:** with no cable between the halves or to the computer, the keyboard works away from the desk, such as on the bed beyond the laptop cable's reach.
- **Portability:** each half packs separately.

## How the halves work

| Half | Role | Does |
|---|---|---|
| Left | ZMK central | Scans its own keys and encoder, receives the right half's events over Bluetooth, talks to the host, and shows output, profile, layer and battery on its OLED |
| Right | ZMK peripheral | Scans its keys and encoder, sends events to the left half, and shows its own battery and link on its OLED |

- **One firmware build per half**, flashed by double-tapping that half's reset button (GENERATE) and copying its UF2.
- **Host link:** Bluetooth with 5 profiles, or USB-C into the left half. Plugging USB in makes it the output. Profiles and output switching sit on the System layer.
- **Pairing:** the halves bond to each other on first boot. A settings-reset build clears the bond if they lose each other.
- **Latency:** the Bluetooth split adds a few milliseconds, well below what typing notices.

## Power per half

- **LiPo pouch** with a protection circuit, a JST-PH connector, and a slide switch driving a P-MOSFET. Capacity, size and placement: [[12 - final design#Power]].
- **Charging:** each half charges from its own USB-C through the nice!nano's charger (500 mA with BOOST bridged). A **1-to-2 USB-C cable** charges both from one charger.
- **Drain:** the right half (peripheral) uses far less than the left (central), so it charges less often.

### RGB and the battery

The per-key LEDs are the biggest load. Per-key RGB empties a cell in about a day even when dim, so:

- **On battery:** the LEDs light only for status flashes (caps lock, layer, Bluetooth profile, battery level while Fn is held) and are otherwise switched fully off.
- **On USB:** full effects. At the desk, the 1-to-2 cable from the laptop lights and charges both halves at once.

The ZMK [power profiler](https://zmk.dev/power-profiler) estimates battery life for a given setup.

## ZMK configuration

The config is in the repo's `firmware/`. Details: [[12 - final design#Firmware as built (2026-10-20)]].

- Split enabled, left as central, right as peripheral.
- External power control on, driving only the LED power switch (P0.08), so it cuts the LED rail when the LEDs are off. A gpio-hog holds P0.13 high so each OLED keeps its 3.3 V supply.
- Sleep after inactivity; any key wakes the half.
- Both encoders are defined in the shared `.dtsi`; the right one runs on the peripheral.
- Each half runs ZMK's status screen on its OLED, blanked when the keyboard goes idle.

See [[04 - firmware options]].

## Related Notes
- [[01 - overview]] for the project goals
- [[03 - microcontroller selection]] for the nRF52840 controller
- [[04 - firmware options]] for ZMK
- [[05 - pcb design]] for the per-half PCB
- [[08 - electronics & components]] for the per-half parts

## Resources

- [ZMK Split Keyboards](https://zmk.dev/docs/features/split-keyboards)
- [ZMK Power Profiler](https://zmk.dev/power-profiler)
- [Split Keyboard Database](https://yal-tools.github.io/ergo-keyboards)
- r/ErgoMechKeyboards

### Video Notes
- [[How Im Designing My Dream Keyboard - Dungeon Delver]] — each half as an independent unit
- [[How To Build A Corne Keyboard - Beginners Guide]] — per-side PCBs and per-side flashing
