---
created: 2026-03-09
updated: 2026-10-22T15:00
name: 11 - learning resources & references
---

> [!success] References
> The sources Keygen is built on: the Redox layout, ZMK and its RGB module, the nice!nano v2 pinout, KiCad and its libraries, the parts' shops, and the builds and videos that shaped the design. Build plan repo: [milindmadhukar/keygen](https://github.com/milindmadhukar/keygen). See also [[12 - final design#Sources]].

## Design basis

- [mattdibi/redox-keyboard](https://github.com/mattdibi/redox-keyboard): the base layout (MIT). Key coordinates come from its `img/redox-layout.json`.
- [Keyboard Layout Editor](http://www.keyboard-layout-editor.com/): views and edits the Redox KLE.

## Firmware: ZMK

- [ZMK documentation](https://zmk.dev/docs)
- [Split keyboards](https://zmk.dev/docs/features/split-keyboards)
- [Encoders on the peripheral half](https://zmk.dev/blog/2023/10/05/zmk-sotf-6)
- [Lighting](https://zmk.dev/docs/features/lighting)
- [Displays](https://zmk.dev/docs/features/displays): the OLED status screen
- [Power profiler](https://zmk.dev/power-profiler): battery-life estimates
- [ZMK Studio](https://zmk.dev/docs/features/studio): live remapping
- Per-key RGB module: [gudzpoz/zmk-rgb-matrix](https://github.com/gudzpoz/zmk-rgb-matrix) (fork: [dima-m711/zmk-rgb-matrix](https://github.com/dima-m711/zmk-rgb-matrix))
- [ZMK Discord](https://zmk.dev/community/discord/invite)

## Controller

- [nice!nano v2](https://nicekeyboards.com/nice-nano/): docs and pinout, which the nRF52840 SuperMini shares. One SuperMini per half.
- [GOLEM: Pro Micro pinout](https://golem.hu/article/pro-micro-pinout/): the footprint format it uses

## PCB

- [KiCad](https://www.kicad.org/) 10
- [marbastlib](https://github.com/ebastler/marbastlib) (CERN-OHL-P v2) and [Keebio-Parts](https://github.com/keebio/Keebio-Parts.pretty) (MIT): footprint libraries, git submodules in the repo
- [kiswitch](https://github.com/kiswitch/kiswitch): MX switch 3D model
- [Freerouting](https://github.com/freerouting/freerouting): autorouter for most of the signal routing
- [Lion Circuits](https://www.lioncircuits.com/): the fab (Bengaluru)
- [Keyboard PCB guide by Ruiqi Mao](https://github.com/ruiqimao/keyboard-pcb-guide) and [ai03 PCB designer guide](https://wiki.ai03.me/books/pcb-design/chapter/pcb-designer-guide): KiCad keyboard PCB tutorials
- [GOLEM: keyboard matrix](https://golem.hu/guide/keyboard-matrix/) and [rotary encoders](https://golem.hu/guide/rotary-encoder-programming/)

## Parts and shops

The full list with prices is in [[13 - bill of materials]].

- [nRF52840 SuperMini, A+A+A Store](https://www.aliexpress.com/item/1005007383270623.html) (AliExpress): controllers
- [StacksKB](https://stackskb.com/store/1n4148-through-hole-diode/): 1N4148 diodes
- [Hongyan EC11, Robu.in](https://robu.in/product/hongyan-ec11h-7ce20p1zd20-rotary-encoder-with-push-button-switch-vertical-plug-in-5-pin/): the encoders
- [Easylander 505080](https://www.aliexpress.com/item/1005002973787972.html) (AliExpress): LiPo cells
- Robu.in: JST-PH, MOSFETs, passives, slide switches
- AliExpress: Poron switch pads and gasket strips; Amazon.in: EVA foam
- Meckeys: 1u DSA keycaps; AliExpress: 1.25u and 1.5u

## Builds that shaped the design

From r/ErgoMechKeyboards and GitHub:

- [Third Redox, First Wireless](https://www.reddit.com/r/ErgoMechKeyboards/comments/1fpv3d7/)
- [DIY Wireless Redox using nice!nano](https://www.reddit.com/r/ErgoMechKeyboards/comments/wafgyf/): the same layout and controller
- [The Wolf](https://www.reddit.com/r/ErgoMechKeyboards/comments/1x8d8sb/introducing_the_wolf_keyboard/): wireless ZMK, "really stable". About 4.76 mm of column stagger was essential, and their one regret was too little weight.
- [Dactyl CC](https://www.reddit.com/r/ErgoMechKeyboards/comments/1tp0r9s/dactyl_cc_heavy_balanced_and_uncompromising_split/): wireless ZMK, and ZMK Studio as a must-have.
- [Elora Hyper Case](https://www.reddit.com/r/ErgoMechKeyboards/comments/1ls6857/): small hands with an aggressive stagger
- [Harite](https://github.com/dlip/harite): open-source BLE + USB split
- [I modeled 15 keyboard geometries and human hand anatomy](https://www.reddit.com/r/ErgoMechKeyboards/comments/1x48qa5/i_modeled_15_keyboard_geometries_and_human_hand/): to read before the paper fit test

## Build videos

Each has a transcript note in [[video notes]].

- [How To Build A Corne Keyboard](https://www.youtube.com/watch?v=vzDTdLaAzXc) → [[How To Build A Corne Keyboard - Beginners Guide]]: soldering, the LED chain, per-side component order, tenting legs
  > "Really really nice guide on soldering and mainly the LEDs, I would like to fit everything through hole if possible… tenting is something I should look into"
- [How to Design Mechanical Keyboard PCBs with KiCad](https://www.youtube.com/watch?v=8WXpGTIbxlQ) → [[Designing Keyboard PCBs with KiCad]]: the KiCad workflow from schematic to Gerbers
  > "Really really useful information"
- [How I'm Designing My Dream Keyboard](https://www.youtube.com/watch?v=CZaAxaHlsBY) → [[How Im Designing My Dream Keyboard - Dungeon Delver]]: designing each split half to stand on its own
  > "blue keyboard at 14:11 is very cool"
- [I Built My DREAM Keyboard from SCRATCH](https://www.youtube.com/watch?v=KwFWBdfZKnI) → [[I Built My DREAM Keyboard from Scratch - Modular]]: build order, tools, and pin functions to check
  > "Lot of nice information about mistakes to avoid and tools that I can use."
- [I Built a Ridiculous Keyboard by Hand](https://www.youtube.com/watch?v=VlHgEqLVYqA) → [[I Built a Ridiculous Keyboard by Hand - Dactyl-Manuform]]: a heavy base for split stability

## Inspiration

![[Pasted image 20260426015004.png]]
![[Pasted image 20260426015030.png]]
![[Pasted image 20260426015052.png]]

## Building and testing

- [GOLEM keyboard guides](https://golem.hu/guide/), [tools](https://golem.hu/guide/tools/), [Mill-Max sockets](https://golem.hu/guide/mill-max/)
- [build123d](https://build123d.readthedocs.io/): the Python CAD library the case is written in
- Key testers: [keyboard-test.space](https://keyboard-test.space), [keyboardchecker.com](https://keyboardchecker.com)
- Learning the layout: [keybr.com](https://www.keybr.com/), [Monkeytype](https://monkeytype.com/)

## Related notes

- [[01 - overview]]
- [[02 - layout design]]
- [[03 - microcontroller selection]]
- [[04 - firmware options]]
- [[05 - pcb design]]
- [[06 - split architecture]]
- [[07 - switch & keycap selection]]
- [[08 - electronics & components]]
- [[09 - case design]]
- [[10 - assembly & build guide]]
- [[12 - final design]]
- [[13 - bill of materials]]
- [[14 - case & plate requirements]]
- [[15 - datasheet audit]]
