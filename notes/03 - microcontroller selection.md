---
created: 2026-03-09
updated: 2026-10-22T15:00
name: 03 - microcontroller selection
---

> [!success] Controller
> **nice!nano v2** (genuine), one per half, socketed on the PCB **underside** and hidden, with USB-C out through the top edge of the case. It runs ZMK. See [[12 - final design#Controllers]].

## nice!nano v2

- **MCU:** nRF52840 (ARM Cortex-M4F, 64 MHz), 1 MB flash, 256 KB RAM
- **Radio:** Bluetooth Low Energy, used for the host link and the link between the halves
- **USB:** USB-C on the module, which is the keyboard's USB port
- **Format:** Pro Micro footprint (marbastlib's `nice_nano_H_USBup`), with USB facing the top edge
- **Firmware:** ZMK target `nice_nano//zmk`; flashing is drag-and-drop UF2 after a double-tap of reset
- **Charger:** on-board LiPo charger, 100 mA by default and 500 mA with the **BOOST** jumper bridged. Keygen bridges it.
- **Switched VCC:** an on-board MOSFET on P0.13 cuts the 3.3 V VCC rail. Keygen's VCC (pad 16) powers only the OLED, and the firmware holds P0.13 high with a gpio-hog so it stays on. The LEDs run from the battery through their own power switch on P0.08.
- **Mounting:** socketed with low-profile machined round-pin headers, so a controller can be swapped. It sits about 7.5 mm below the PCB, which sets the case depth.

## Pin budget

21 usable GPIO; 18 on the Pro Micro edge pads.

| Function | Left | Right |
|---|---|---|
| Matrix (5 rows × 7 cols) | 12 | 12 |
| Encoder A/B | 2 | 2 |
| RGB data | 1 | 1 |
| LED power switch | 1 | 1 |
| OLED SDA/SCL | 2 | 2 |
| **Total** | **18** | **18** |

Every one of the 18 edge pins is used on both halves; the three inner pads stay unused.

- LED data is on **P0.06**, a full-speed pin.
- The OLED's I2C is on **P0.17** (SDA, pad 5) and **P0.20** (SCL, pad 6), both full-speed pins.
- The encoder is on the NFC pins, the same on both halves: A on **P0.10** (pad 23), B on **P0.09** (pad 24), set up as GPIO with `nfct-pins-as-gpios`.
- **P0.08** drives the LED power switch.
- The pin restrictions were checked against the nRF52840 datasheet in [[15 - datasheet audit]]. Full pin map: [[12 - final design#Controller pin map]].

## Related notes
- [[04 - firmware options]] — ZMK
- [[05 - pcb design]] — schematic and routing
- [[06 - split architecture]] — how the halves connect
- [[08 - electronics & components]] — supporting parts

## Resources
- [nice!nano documentation](https://nicekeyboards.com/docs/nice-nano/)
- [ZMK supported hardware](https://zmk.dev/docs/hardware)

### Video notes
- [[How To Build A Corne Keyboard - Beginners Guide]] — socketing the controller with Mill-Max pins
