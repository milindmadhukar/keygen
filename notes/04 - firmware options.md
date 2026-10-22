---
created: 2026-03-09
updated: 2026-10-22T15:00
name: 04 - firmware options
---

> [!success] Firmware
> **ZMK**, with ZMK Studio for live remapping. It runs the Bluetooth split, USB plus 5 Bluetooth profiles to the host, an encoder and an OLED status screen on each half, and power control for the LEDs. See [[12 - final design#Firmware: ZMK]].

## ZMK (Zephyr Mechanical Keyboard)

**Website:** [https://zmk.dev/](https://zmk.dev/)
**Documentation:** [https://zmk.dev/docs](https://zmk.dev/docs)
**Language:** C on Zephyr RTOS
**License:** MIT

### What Keygen uses
- **Bluetooth split**: the left half is the central, the right half the peripheral. One firmware build per half.
- **Host connection**: USB-C on the left half, or Bluetooth with up to 5 paired hosts. Plugging USB in makes it the output.
- **Power management**: deep sleep and low-power BLE, which give weeks to months per charge with the LEDs off.
- **External power control**: drives only the board's LED power switch (P0.08), turning it and the LED rail off when the LEDs are off.
- **Encoders on both halves**: both defined in the shared `.dtsi`, the right one running on the peripheral. The left knob scrolls through ZMK's mouse emulation (`CONFIG_ZMK_POINTING`); the right one sends volume, page and brightness keys. Mapping: [[12 - final design#Knobs]].
- **Displays**: ZMK's status screen on each half's SSD1306 OLED (`CONFIG_ZMK_DISPLAY`). The left shows output, Bluetooth profile, layer and battery; the right its own battery and link. It blanks when the keyboard goes idle (`CONFIG_ZMK_DISPLAY_BLANK_ON_IDLE`). A gpio-hog holds P0.13 high so the OLED keeps its 3.3 V supply.
- **ZMK Studio**: live keymap changes over USB or Bluetooth, no reflash needed.

### Configuration workflow
- The config lives in `firmware/` of the hardware repo: keymap, `.conf`, and the shield under `firmware/boards/`.
- Pushing to GitHub runs ZMK's GitHub Actions build, which produces a UF2 per half.
- Flash by double-tapping reset (the GENERATE button) and copying the UF2 to the drive that appears.
- Build details (ZMK version, Zephyr 4.1 changes, the physical layout for Studio): [[12 - final design#Firmware as built (2026-10-20)]].

### RGB
- The 33 LEDs per half are driven over SPI (`ws2812-spi`) from P0.06.
- Per-key status (caps lock, layer, Bluetooth profile, battery level) uses a community per-key RGB module such as `zmk-rgb-matrix`. See [[12 - final design#Status display]] for its current state.
- On battery the LEDs light only for status; full effects run while USB is plugged in. Brightness is capped in firmware.

### Several computers
- **Bluetooth profiles**: up to 5 hosts, selected from the System layer.
- **Layers and macros** cover host-specific shortcuts.

## Related notes
- [[03 - microcontroller selection]] — the nRF52840 SuperMini
- [[06 - split architecture]] — how the halves connect
- [[10 - assembly & build guide]] — flashing during the build

## Resources
- [ZMK documentation](https://zmk.dev/docs)
- [ZMK split keyboards](https://zmk.dev/docs/features/split-keyboards)
- [ZMK hardware support](https://zmk.dev/docs/hardware)
- [ZMK power profiler](https://zmk.dev/power-profiler)
- [ZMK Discord](https://zmk.dev/community/discord/invite)
- [r/ErgoMechKeyboards](https://www.reddit.com/r/ErgoMechKeyboards/)
