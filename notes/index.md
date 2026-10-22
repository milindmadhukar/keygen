---
created: 2026-03-09T19:08
updated: 2026-10-22T15:00
title: Keygen Custom Keyboard
name: Keygen Custom Keyboard
---
# Keygen Custom Keyboard

> [!success] Current design
> **[[12 - final design]]**: a flat wireless Redox-based split with 66 QWERTY keys, a knob and an OLED status screen on each half, per-key RGB, and hidden nRF52840s running ZMK. Parts and shops: **[[13 - bill of materials]]**. Case and plate checklist: **[[14 - case & plate requirements]]**. PCB checked against the part datasheets: **[[15 - datasheet audit]]**. Build plan repo: [milindmadhukar/keygen](https://github.com/milindmadhukar/keygen).

Keygen is a one-off split ergonomic keyboard built from scratch: a custom two-layer PCB designed in KiCad 10, a nice!nano v2 per half, Bluetooth between the halves and to the computer (or USB-C on the left half), a LiPo per half, ZMK firmware, and a 3D-printed tented case. The PCB is routed and DRC clean, the manufacturing files are exported, and the ZMK config builds; ordering, assembly and the case come next.

## Notes

| Note | Covers |
|---|---|
| [[01 - overview]] | The project and its goals |
| [[02 - layout design]] | Key layout and thumb cluster |
| [[03 - microcontroller selection]] | The nRF52840 controller |
| [[04 - firmware options]] | ZMK |
| [[05 - pcb design]] | PCB design and fabrication |
| [[06 - split architecture]] | The two halves and how they connect |
| [[07 - switch & keycap selection]] | Switches, keycaps, foam |
| [[08 - electronics & components]] | Parts on the board |
| [[09 - case design]] | The case |
| [[10 - assembly & build guide]] | Soldering, bring-up and flashing |
| [[11 - learning resources & references]] | Sources and references |
| [[12 - final design]] | The design as a whole (source of truth) |
| [[13 - bill of materials]] | Shopping list |
| [[14 - case & plate requirements]] | What the case and plate must fit |
| [[15 - datasheet audit]] | The PCB checked against each datasheet |
| [[16 - hardware reference]] | Electronics, PCB rules, plate, case, foam and silkscreen artwork in detail |
| [[17 - building from source]] | The scripts that generate the schematic, PCB, plate, case and outputs |

## Video Notes

Transcript-distilled notes from the saved build videos live in the [[video notes]] subfolder and are indexed in [[11 - learning resources & references]].
