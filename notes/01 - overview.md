---
created: 2026-03-09
updated: 2026-10-22T15:00
name: 01 - overview
---

> [!success] Keygen
> A flat, wireless split keyboard built on the Redox layout: 66 QWERTY keys, a 2×2 + 1.25u thumb cluster per hand, a knob and an OLED status screen on each half, and per-key RGB that also shows status. Two nRF52840 controllers run ZMK, hidden under the PCB with USB-C through the case. Full spec: [[12 - final design]].

## Project vision

A custom split ergonomic keyboard built from scratch, covering the full hardware stack: microcontroller firmware, PCB design in KiCad, and a 3D-printed case. It is a one-off build.

## What Keygen has

### Physical layout
- **Two separate halves**, positioned and tented independently
- **Column-staggered** keys, six columns per hand plus an extra bottom row
- **Thumb cluster** per hand: a 2×2 block (two 1u over two 1.25u, rotated 30°) plus one 1.25u key
- **Hotswap sockets** (Kailh MX), so switches change without soldering

### Electronics
- **USB-C** on each half, through the case
- **Bluetooth** to the host (5 profiles) and between the halves, with a LiPo battery per half
- **OLED status screen** (0.96 in., 128×64) on each half: output, Bluetooth profile, layer and battery on the left; the right half's own battery and link on the right
- **Per-key RGB** (SK6812MINI-E), which also shows status: caps lock, layer, Bluetooth profile, battery level
- **Rotary encoder** on each half's inner edge: the left one scrolls (press: middle click), the right one sets the volume (press: mute)

### Build quality
- **Creamy, quiet sound** from light tactile switches and foam layers in the case
- **Weight** in the case base so the halves stay put

## Multiple hosts

Five Bluetooth profiles plus USB-C on the left half cover several computers. Profiles are selected from the System layer; see [[12 - final design#Nav, Fn and System layers]].

## Status (2026-10-22)

- Layout, schematic and keymap decided
- PCB routed, DRC clean with schematic parity, datasheet audit passed ([[15 - datasheet audit]])
- Manufacturing files and assembly BOM exported
- Switch plate and gasket-mounted case designed and generated from the PCB ([[09 - case design]])
- Next: order the boards and plates, print the case ([[09 - case design]]), choose the tenting

## Related notes
- [[02 - layout design]] — key layout and geometry
- [[07 - switch & keycap selection]] — switches and keycaps
- [[13 - bill of materials]] — shopping list

## Resources
- [GOLEM Keyboard Resources](https://golem.hu) - keyboard building guides
- [Ergo Keyboards Database](https://yal-tools.github.io/ergo-keyboards) - reference for existing designs
