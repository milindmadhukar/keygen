---
created: 2026-06-16
name: Designing Keyboard PCBs with KiCad
source: https://www.youtube.com/watch?v=8WXpGTIbxlQ
type: video-note
---

# Designing Keyboard PCBs with KiCad

> [!quote] My own note on this video
> Really really useful information

End-to-end walkthrough (Scotto / "Scottokeebs") of designing a mechanical keyboard PCB in KiCad, from library setup through schematic capture, footprint assignment, PCB layout, routing, edge cuts, fill zones, Gerber export, and ordering. The example is a 3x3 macropad on a Pro Micro, but every concept scales directly to a full board. Assumes you already understand the **key matrix** (rows + columns + per-switch diodes) — the presenter points to his prior matrix video as a prerequisite.

## Key Takeaways

**Setup**
- Download KiCad from kicad.org, install with defaults. It is the de-facto standard for keyboard PCBs and most community libraries target it.
- Use a prebuilt keyboard library bundle (the video uses the **Scotto KiCad** library from the Scottokeebs repo) — it has symbols/footprints for MX, Choc, Kailh NB/KH switches, LEDs, OLEDs, and microcontrollers, so you do not have to build footprints from scratch.
- Wire up three things in Preferences before starting:
  1. **Configure Paths** — point a path variable (e.g. `SCOTTO_KICAD`) at the library folder so KiCad can find the 3D models. The 3D models matter because you can export the finished PCB to a 3D file and design a case around it.
  2. **Manage Symbol Libraries** — add the `.kicad_sym` file. Symbols are the schematic wiring representation.
  3. **Manage Footprint Libraries** — add all footprint folders. Footprints are the physical pads/holes on the PCB.
- Install the **Fabrication Toolkit** plugin (Plugin & Content Manager, search "jlc") — one button at the end exports the JLCPCB production files and opens the output folder. You can also export Gerbers manually through menus.

**Schematic capture**
- Schematic = the instruction set for the whole board. Get it right and DRC, ratsnest, and routing all become easy because everything downstream is derived from it.
- Press `a` to add symbols. The base "core component" of a keyboard is one **placeholder switch + one placeholder diode**, aligned cleanly on X/Y.
- Build the matrix by copy/pasting that core component into a grid (3x3 here). Keep everything aligned vertically/horizontally so wiring is clean.
- Wire **rows** straight across the diodes, then **columns** down the switch pins. Green junction dots indicate real connections.
- Hotkey gotcha: KiCad hotkeys do not always match what the toolbar says (pressing `s` on the canvas creates a sheet, not "select"). Prefer clicking toolbar tools. `w` = wire tool.
- Instead of spaghetti wires to the MCU, use **Global Labels** — anything sharing a label name joins the same **net**. Label the three rows `row0/1/2` and three columns `col0/1/2`, then drop matching labels on free MCU pins (the video uses a Pro Micro: cols on D1/D0/D4, rows on C6/D7/E6). The exact pins are arbitrary as long as they are free and match your firmware.

**Footprint assignment**
- Open the **footprint assignment tool**; symbols start with no footprint linked.
- Diodes: `DO-35` = through-hole, `SOD-123` = surface-mount (SMD). Values 1N4148 (TH) / 1N4148W (SMD); value is not critical for keyboards.
- Switches: search the library and pick the footprint matching your build — through-hole, **hotswap**, or hybrid sockets. Video uses through-hole MX for simplicity.
- Because footprints are linked from the schematic, you can change them later and re-sync to the PCB without redoing layout.

**PCB layout**
- Click **Update PCB from Schematic** to pull in all footprints (re-run this any time the schematic changes — also the fastest way to recover a footprint you accidentally mangled: delete it and re-update).
- **Grid is switch-specific.** Set a user grid to switch spacing: MX = `19.05 mm`. Choc ~`18x17`. For finer placement, divide: quarter-unit = `4.7625`, eighth-unit = `2.38125` (good for placing diodes).
- Set an **origin point** (`s` on the first switch) so everything else positions relative to it; use right-click > Positioning Tools > **Move with Reference** to place subsequent parts precisely.
- The **ratsnest** (thin blue lines) shows where each pad must connect — derived from the schematic.
- Use **3D Viewer** to sanity-check placement and which side parts sit on. Diodes typically go on the **back**; press `f` to flip a footprint to the back side.

**Routing**
- Dual-layer board: `F.Cu` (front copper) and `B.Cu` (back copper). Use the **Add Track** tool; clicking a pad highlights its required connection.
- Convention shown: route **rows on the front**, **columns on the back** so they can cross without colliding.
- **Vias** (`v` while routing) drop a plated hole to pass a trace front<->back, letting you cross another trace. Add via, continue on the other layer, add another via to come back.
- Bottom-left status shows unrouted count.

**Finishing & manufacturing**
- **DRC** (Design Rules Checker) flags errors. A fresh board throws "malformed outline" — fix by drawing an **Edge.Cuts** outline (rectangle tool on the Edge.Cuts layer). Re-run DRC to confirm clean. Edge cuts can be any shape you like.
- **Fill zones** (add-filled-zone tool, draw over the board, select front+back copper, press `b` to fill): optional, but isolates traces in a copper pour and makes the board look cleaner.
- Note the layer stack-up visible in the viewer: silkscreen/solder-mask on top, copper underneath.
- Export with the Fabrication Toolkit button → produces a `.zip` of production files ready to upload.

**Ordering (JLCPCB / PCBWay etc.)**
- Upload the zip; most options are self-explanatory.
- The one setting that drastically changes price is **surface finish**: **HASL** (solder over pads) is cheapest — example was ~$2 — and perfectly fine for keyboards. **ENIG** (gold pads) jumped to ~$18-20; only worth it for very fine-pitch components, otherwise purely cosmetic (silver vs gold).
- Lead time is a few weeks. Firmware (QMK) is the final step, covered in a follow-up video.

## Notable Timestamps

- **00:22** — Download/install KiCad; why it is the keyboard standard
- **00:37** — Adding the keyboard library bundle (switches, LEDs, OLEDs, MCUs)
- **00:54** — Configure Paths (3D models) + add symbol/footprint libraries
- **02:25** — Install the JLC Fabrication Toolkit plugin for one-click Gerber export
- **02:56** — Start the schematic; switch + diode "core component"
- **03:35** — Building the 3x3 matrix by copy/paste
- **04:16** — Hotkey gotchas; wiring rows then columns
- **05:44** — Global Labels and nets (clean way to wire the matrix to the MCU)
- **05:21** — Adding the Pro Micro controller
- **07:35** — Assigning MCU pins to row/column labels
- **07:42** — Footprint assignment tool; DO-35 vs SOD-123 diodes; TH vs hotswap switches
- **08:46** — Open PCB editor; Update PCB from Schematic
- **09:16** — Grid system; 19.05 mm MX spacing, quarter/eighth-unit grids
- **10:06** — Origin point + Move with Reference for precise placement
- **11:46** — Positioning diodes; ratsnest explained
- **12:24** — 3D viewer; flipping diodes to the back (`f`)
- **13:56** — Routing traces; F.Cu vs B.Cu (rows front / columns back)
- **15:45** — Vias to cross traces between layers (`v`)
- **16:46** — DRC; "malformed outline" error
- **17:06** — Adding the Edge.Cuts board outline
- **17:40** — Fill zones / copper pour (`b`)
- **18:45** — Fabrication Toolkit export → production zip
- **18:57** — Ordering; HASL vs ENIG surface finish and the price impact
- **20:01** — Wrap-up; QMK firmware is the next step

## Relevance to Keygen build

This is the closest match to the actual workflow needed for the Keygen split board. Concrete carry-overs and the split-specific gaps it does not cover:

- **Hotswap sockets**: the video uses through-hole MX for simplicity but explicitly shows the library has hotswap/hybrid footprints — for Keygen, pick the **Kailh MX hotswap socket** footprint at assignment time. The matrix wiring is identical; only the footprint changes.
- **Per-key SK6812 RGB**: not covered here. Each SK6812 MINI-E is wired in a **daisy chain** (DOUT → DIN), not into the matrix, and needs VCC/GND/DATA routing plus decoupling caps — a separate net topology layered on top of what this video teaches. The library does include LED footprints, so symbol/footprint flow is the same.
- **Rotary encoder + OLED header**: also extra components beyond the macropad example. They attach to free MCU pins via Global Labels exactly like the matrix rows/cols shown here (encoder = 2 pins + GND; OLED = I2C SDA/SCL/VCC/GND header).
- **Grid**: set the user grid to the chosen switch spacing — `19.05 mm` for MX. The quarter/eighth-unit grid trick is directly useful for placing diodes, encoder, and OLED neatly.
- **Split-specific considerations the video does NOT address (must research separately):**
  - **Mirrored halves** — a split needs left and right PCBs. Either design two mirrored boards or design a single **reversible PCB** that can be flipped and used as both halves (footprints placed symmetrically, dual silkscreen).
  - **Inter-half link** — add a **TRRS** (or TRS) jack footprint and route the data/VCC/GND link between halves; this is the connection the macropad example never needs.
  - **One MCU per half vs. one MCU + slave** — affects how the matrix nets and the TRRS link are wired.
- **Workflow & ordering** transfer 1:1: schematic-first, Update-PCB-from-Schematic, DRC, Edge.Cuts, fill zones, Fabrication Toolkit export, and **HASL surface finish** (cheap, fine for keyboards) when ordering from JLCPCB/PCBWay.

## Related

- [[05 - pcb design]]
- [[08 - electronics & components]]
- [[03 - microcontroller selection]]
- [[06 - split architecture]]
- [[11 - learning resources & references]]
