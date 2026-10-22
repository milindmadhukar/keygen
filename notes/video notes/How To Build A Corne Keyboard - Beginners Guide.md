---
created: 2026-06-16
name: How To Build A Corne Keyboard - Beginners Guide
source: https://www.youtube.com/watch?v=vzDTdLaAzXc
type: video-note
---

A complete, beginner-oriented walkthrough of assembling a **Cherry Corne v3** split keyboard from a standard kit. The build is fully through-hole-friendly in the sense that every component is hand-soldered onto two PCBs (one per hand): SMD diodes, hot-swap sockets, RGB LEDs, TRRS jacks, reset switches, OLED sockets and a socketed Elite-C microcontroller. The video then covers flashing QMK via the online configurator + QMK Toolbox, casing the boards in a 3D-printed tented case, and finishing with switches, keycaps and feet. It's especially strong as a soldering and LED-install reference, which is exactly what was wanted from it.

## Key Takeaways

**Soldering setup & technique**
- Adjustable-temperature soldering station is the single most important tool; he runs **350–370 °C** for lead-free solder.
- **Tin the tip** before first use and re-coat it before returning it to the holder to prevent oxidation ("oxidation is your worst enemy"). Clean on a damp sponge.
- Recommended consumables: **no-clean flux** (makes everything dramatically easier), solder wick + desoldering pump for fixes, heat-resistant tape to hold parts while soldering the back, **0.8 mm solder** for general work and **0.5–0.6 mm** for SMD parts, reverse-action and precision tweezers, wire cutters, a soldering mat.
- Work in a ventilated area; use a fan blowing fumes away / out a window, or a small smoke absorber.
- General SMD method: heat one pad, feed a little solder onto it, hold the part with tweezers, re-melt the pad to seat the part, remove iron first then tweezers, then solder the remaining pads. Fix bridges with flux + a swiping motion.

**Component install order (per side)**
1. **42 SMD diodes** — orientation matters: the line on the diode must match the line on the PCB. Use reverse-action tweezers.
2. **RGB underglow LEDs** — 6 per side; recessed corner of the LED matches the marked corner of the PCB. Bad joints can kill not just that LED but the rest of the chain, so joints must be solid.
3. **Per-switch RGB LEDs** — 21 per side; notched corner aligns to marked PCB corner, light shines to the far side.
4. **Hot-swap sockets (Kailh MX)** — 21 per side; press flush with tweezers while soldering, keep iron near pad edge.
5. **TRRS jacks**, **reset switch**, **OLED socket** — taped in place, soldered from the back, tape removed.
6. **Microcontroller** — socketed (not soldered direct) using low-profile sockets + **Mill-Max pins** so the controller can be removed/replaced.
7. **OLED screen** — mounted on cut diode legs through the socket, then trimmed.

**Component choices the creator recommends**
- MCU: **Elite-C** (Pro Micro-compatible, sturdy USB-C that won't rip off). Socket it rather than solder it directly.
- Switches/keycaps must be **MX-compatible**; he uses **Gateron Milky Yellow Pro** (linear, factory-lubed) and **blank PBT DSA-profile** keycaps (uniform height, rearrangeable).
- Hot-swap sockets mean **no soldering of switches** — they just press in.
- Case: 3D-printed with optional honeycomb underglow pattern; transparent acrylic display cover if running OLEDs.

**Firmware**
- Flash with the **online QMK Configurator** → choose `crkbd` rev1, layout `3x6` → Compile → download firmware.
- Install **QMK Toolbox**, connect one half, press reset (should report `ATmega32u4`), open the firmware, Flash. Repeat for the other half.
- Default layout uses layers for numbers/arrows, symbols, and RGB/media controls, with hold-to-shift-layer keys.
- "Test keyboard" mode in the configurator lets you short each socket with tweezers to verify keys before final assembly.

**Tenting**
- The 3D-printed case supports screw-in **tenting legs**: shorter (18 mm) on the front holes, longer (40 mm) on the rear, adjusted with an Allen key. Check all legs touch the desk. Non-tented builds just use rubber corner bumpers instead.

## Notable Timestamps

- **00:00** — Intro; building the Cherry Corne v3 (hot-swap, RGB per-key + underglow, OLED support).
- **01:25** — Full parts list (PCBs, 42 diodes, 42 sockets, TRRS jacks, reset switches, optional LEDs/OLEDs).
- **03:02** — Microcontroller choice (Elite-C) and the case for *socketing* it.
- **04:47** — Switches & keycaps (Gateron Milky Yellow Pro, blank PBT DSA).
- **05:38** — Soldering equipment and consumables.
- **07:40** — Tip tinning / temperature / oxidation advice.
- **08:20** — Soldering the diodes (orientation).
- **09:38** — Installing underglow LEDs.
- **11:08** — Installing per-switch LEDs + fixing bridges.
- **12:33** — Hot-swap sockets.
- **13:30** — TRRS jacks, OLED socket, reset switch.
- **14:30** — Socketing the microcontroller (Mill-Max pins).
- **16:45** — Installing the OLED screen.
- **17:39** — Flashing with QMK Configurator + QMK Toolbox.
- **21:47** — Testing keys by shorting sockets.
- **22:35** — Mounting PCB to case, display cover, switch plate.
- **24:48** — Installing switches and keycaps.
- **25:42** — Tenting legs (18 mm / 40 mm) vs rubber bumpers.

## Relevance to Keygen build

- **Soldering & LEDs (the main reason this video was saved):** This is the strongest reference yet for hand-soldering SK6812-style RGB LEDs and SMD diodes. The flux + swiping-motion technique, orientation rules (recessed/notched corner to marked PCB corner), and the warning that one bad LED joint breaks the whole chain are directly applicable.
- **Through-hole-everything goal:** Worth a nuance — the LEDs and diodes here are still surface-mount (SMD) parts, just hand-soldered. There is no through-hole version of these LEDs on a Corne. If "through-hole if possible" means avoiding reflow/SMD entirely, that isn't achievable for per-key RGB; this video shows the realistic alternative (careful hand-soldering of SMD), or buying a **partially pre-assembled PCB** (the creator sells one with diodes + LEDs pre-soldered) to skip the hardest part.
- **Wired / no-wireless:** Fully aligned. This build is wired (TRRS between halves, USB to host, ATmega32u4 / Elite-C, QMK). No wireless needed, which keeps the LED-heavy build simple.
- **Thumb cluster gap:** The stock Corne has only a **3-key arc thumb cluster per hand**, and this build follows that. The Keygen target is **4 keys per hand in a Kinesis Advantage-style scooped block** — Milind dislikes the Corne/Kyria curved arc arrangement. So the Corne PCB/firmware here is a soldering & wiring reference, **not** the thumb layout to copy. A different board (e.g. a 5-column 3x6+ variant or a custom/handwired layout) or PCB modification will be needed to add the extra thumb key and the scooped block geometry.
- **Rotary encoders:** Not present in this build at all. The stock Corne + this kit have no encoders; adding them is a Keygen-specific extension (encoder footprints or handwiring + QMK encoder config) not covered here.
- **Tenting:** Directly useful — the 3D-printed case with screw-in tenting legs (18 mm front / 40 mm rear, Allen-key adjusted) is a concrete, cheap tenting approach to evaluate for Keygen.

## Related

- [[10 - assembly & build guide]]
- [[08 - electronics & components]]
- [[03 - microcontroller selection]]
- [[06 - split architecture]]
- [[11 - learning resources & references]]
