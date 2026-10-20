# Keygen firmware

Keygen runs [ZMK](https://zmk.dev). The firmware has not been written yet; this directory is
where the ZMK user config will live once the boards are in hand.

## Planned layout

```
firmware/
├── build.yaml                       GitHub Actions build matrix (left, right, settings reset)
├── config/
│   ├── west.yml                     ZMK version plus the zmk-rgb-matrix module
│   ├── keygen.conf                  Bluetooth, sleep, external power and RGB settings
│   └── keygen.keymap                base, Fn and adjust layers; encoder bindings
└── boards/shields/keygen/
    ├── Kconfig.shield
    ├── Kconfig.defconfig            split roles: left is the central
    ├── keygen.dtsi                  5 × 7 matrix (COL2ROW), encoder, LED strip, physical layout
    ├── keygen_left.overlay
    ├── keygen_right.overlay         encoder on P0.20 / P0.09 (nfct-pins-as-gpios)
    └── keygen.zmk.yml
```

Each half is built for the `nice_nano_v2` board, one Bluetooth-split build per half. There is no
wired split: the board has no cable between the halves.

## What the firmware has to do

- **Matrix:** 5 rows × 7 columns per half, COL2ROW. The controller pin map is in
  [the build plan](../plan/index.html) and in `tools/gen_schematic.py`.
- **Encoder:** volume on the right half, press to mute. Its push switch sits in the matrix at
  row 0 / column 6.
- **Per-key RGB as the status display**, through
  [zmk-rgb-matrix](https://github.com/dima-m711/zmk-rgb-matrix): caps lock, active layer,
  Bluetooth profile, and battery level while Fn is held. The LEDs run from the controller's switched
  VCC (P0.13), so turn on ZMK's external power control and cap the brightness. Even dim, 33 LEDs
  empty a 1000 mAh cell in about a day, so on battery they light only for status flashes; full
  effects only while USB is plugged in.
- **Connectivity:** USB-C on the left half plus 5 Bluetooth profiles to the host; plugging USB in
  makes it the output. The halves talk over Bluetooth only.
- **Power:** each half charges from its own USB-C. Bridge the nice!nano's BOOST jumper (500 mA,
  safe for cells over 500 mAh) before fitting the 1000–1500 mAh batteries.
- **ZMK Studio** for live remapping.

## References

- [ZMK split keyboards](https://zmk.dev/docs/features/split-keyboards)
- [ZMK encoders](https://zmk.dev/docs/features/encoders)
- [ZMK lighting](https://zmk.dev/docs/features/lighting)
- [ZMK Studio](https://zmk.dev/docs/features/studio)
