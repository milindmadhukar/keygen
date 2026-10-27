---
created: 2026-10-19
name: 13 - bill of materials
tags:
  - keyboards
---
# Bill of Materials

> [!info] Generated file
> Generated from `~/Code/keygen/bom/bom.csv` by `tools/render_bom.py`. Edit the CSV, not this note. The rendered page is `plan/bom.html`. Design context: [[12 - final design]].

Quantities cover **the keyboard with spares**. Prices are what the listings showed on 2026-10-20 to 2026-10-22; `~` marks a rough guide.

> [!tip] Buying strategy
> - **AliExpress** (shipped to Australia, brought to India by hand): SK6812MINI-E LEDs (not stocked in India), controllers, batteries, knobs, switch pads, gaskets, keycaps
> - **StacksKB:** switches and diodes
> - **Robu.in:** encoders and small parts
> - **Amazon.in:** EVA foam
> - **JLCPCB:** the boards
>
> The exact listings are in `bom/CHECKLIST.md` in the repo.

## Electronics

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Controller | nRF52840 SuperMini, a nice!nano v2 clone: same 24-pin Pro Micro header and pinout (ZMK board nice_nano//zmk)<br>*2 needed + 3 spare. Charges at about 100 mA (no BOOST jumper): roughly a day for an empty 2500 mAh cell. Before soldering, check B+ (pad 13), GND and VCC (pad 16) with a multimeter, and confirm the charge current. Measure USB-C height on arrival (sets case depth).* | 2 | 5 (pack of 5) |  | [AliExpress, A+A+A Store](https://www.aliexpress.com/item/1005007383270623.html) | AU$23.10 per 5 | decided |
| Controller sockets | Low-profile machined round-pin female header, 1×12, plus matching round male pins<br>*Controller sits hidden on the PCB underside; sockets make it swappable. 2 strips per controller.* | 8 strips | 10 strips | Robu.in / Lamington Road: search "machined round female header 2.54" | AliExpress: "Mill-Max low profile socket pro micro" | ~₹30–60 per 1×40 strip | decided |
| Hotswap sockets | Kailh MX hotswap socket (CPG151101S11)<br>*66 of the 100 owned, with 34 spare.* | 66 | have 100 | Already owned (100) | AliExpress Kailh official store, 100-pack; [Divinikey 100-pack](https://divinikey.com/products/kailh-hot-swap-sockets) | owned | decided |
| Diodes | 1N4148, through-hole DO-35<br>*34 per half (each encoder's push switch is in the matrix). Cathode toward the row (COL2ROW).* | 68 | 100 | [StacksKB 1N4148 (10-pack)](https://stackskb.com/store/1n4148-through-hole-diode/) | LCSC / AliExpress (100-pack) | ₹15 per 10 (StacksKB), less per 100 | decided |
| Per-key LEDs | SK6812MINI-E (reverse mount, 3.2×2.8 mm)<br>*33 per-key per half, no underglow (the battery sits under the PCB). The only fiddly SMD part; buy plenty (34 spare), joints fail. Alternative: JLCPCB assembles them.* | 66 | 100 | Not stocked by Indian stores I checked | LCSC (~$0.08 each) / AliExpress "SK6812MINI-E" 100-pack | ~$0.08 each | decided |
| LED decoupling | 10 µF + 100 nF capacitors, 1206 SMD (C1, C2)<br>*One of each per half, at the LED power switch's output on the LED rail.* | 2 + 2 | 10 + 10 | Robu.in / Lamington Road | LCSC | negligible | decided |
| Rotary encoder | EC11 with push switch, 20 mm D shaft (half shaft)<br>*One per half. The D shaft matches the knob's 6 mm D bore.* | 2 | 2 | [Robu.in, Hongyan EC11](https://robu.in/product/hongyan-ec11h-7ce20p1zd20-rotary-encoder-with-push-button-switch-vertical-plug-in-5-pin/) | AliExpress / LCSC | ₹58 each (₹116) | decided |
| Knob | Aluminium amplifier knob, 17 mm across, 13 mm tall, for a 6 mm D shaft (AliExpress option "D halfshaft 17x13")<br>*Fits the encoder's 6 mm D shaft.* | 2 | 2 | Robu.in / Amazon.in "potentiometer knob aluminium 6mm" | AliExpress | ~₹50–150 | decided |
| OLED | 0.96 in. 128×64 OLED module, SSD1306, I2C, 4-pin (GND VCC SCL SDA)<br>*One per half, soldered straight into the board on its own header pins. Check the pin order printed on the module: GND, VCC, SCL, SDA. Some modules swap GND and VCC.* | 2 | 3 | Robu.in: search "0.96 inch OLED I2C SSD1306" | AliExpress | ~₹150–250 each | decided |

## Power

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Battery | 3.7 V LiPo pouch 505080 (5 × 50 × 80 mm), about 2500 mAh (listed 3000 mAh), JST-PH 2.0 2-pin lead, with a protection board<br>*The controller has no over-discharge cut-off, so the cell needs a protection board: ask the seller, and add a DW01A module to a cell without one. Lies in a bay sunk into the case floor, under the outer and middle key columns, held with double-sided tape, its lead end towards the battery connector: 2.9 mm below assumed 2 mm underside parts at rest, 1.4 mm at full gasket travel and at least 15 mm from the controller's antenna end. The connector is about 40 mm from the cell's lead end, so a lead of 60 mm or more reaches it. Check the red wire lands on the PCB's + pad before plugging in. Flown to India in hand luggage, connectors taped.* | 2 | 2 |  | [AliExpress, Easylander 505080](https://www.aliexpress.com/item/1005002973787972.html) | AU$14.44 for 2 + AU$7.05 shipping | decided |
| Battery connector | JST-PH 2-pin, side-entry through-hole (S2B-PH-K-S)<br>*Side entry so the battery lead runs flat under the PCB.* | 2 | 10 | Robu.in "JST PH 2.0 2 pin" | LCSC | negligible | decided |
| P-channel MOSFETs | AO3401A P-channel MOSFET, SOT-23 (Q101/Q102, Q201/Q202)<br>*Q1 carries the battery current so the 50 mA slide switch only drives its gate (source to the battery, drain to B+). Q2 switches the LEDs' supply from B+.* | 4 | 10 | Robu.in / Lamington Road | LCSC | negligible | decided |
| Gate resistor | 1 MΩ resistor, 1206 (R101/R201)<br>*Holds the MOSFET off between switch positions.* | 2 | 10 | Robu.in / Lamington Road | LCSC | negligible | decided |
| LED switch N-MOSFET | AO3400A N-channel MOSFET, SOT-23 (Q103/Q203)<br>*P0.08 drives its gate; it pulls the LED switch's gate low to turn the LEDs on.* | 2 | 10 | Robu.in / Lamington Road | LCSC | negligible | decided |
| LED switch resistors | 100 kΩ resistor, 1206 (R102/R103, R202/R203)<br>*R2 holds the LED switch off; R3 holds its N-MOSFET off while the controller boots or sleeps.* | 4 | 10 | Robu.in / Lamington Road | LCSC | negligible | decided |
| Y cable | USB-A to 2 × USB-C cable, 1.8 m, black, data and charging<br>*Powers both halves from one computer port, wired mode through the left half. The listing does not say which leg carries data: on arrival, plug only the left half into each leg in turn and see which one the computer finds as a keyboard, then plug the right half into the other.* | 1 | 1 |  | [AliExpress, Asia Market Choice Store](https://www.aliexpress.com/item/1005012373354214.html), option Black 1.8m | AU$6.14 | optional |
| Power switch | MSK12C02 side-actuated SPDT slide switch (SMD, large pads)<br>*Side-actuated so it pokes out of the case edge; the same part most wireless split boards use. Hand-solderable.* | 2 | 10 | Robu.in / AliExpress "MSK12C02" | LCSC / AliExpress | ~₹10–20 each | decided |
| Reset button | 6×6 mm tactile switch, through-hole, 5 mm tall (SW_PUSH_6mm_H5mm)<br>*On the underside next to the controller; press it through a pinhole in the case floor. ZMK can also enter the bootloader from a key.* | 2 | 10 | Robu.in / StacksKB | LCSC | ~₹2–5 each | decided |

## Fabrication

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Main PCBs | 2-layer FR4, 1.6 mm, lead-free HASL, 1 oz, black mask, left and right designs (each half ~16 × 13 cm)<br>*Minimum 5 per design, so 5 left + 5 right. Mark on PCB: Remove Mark.* | 2 | 5 + 5 | [Lion Circuits](https://lioncircuits.com/) as a fallback (Bengaluru, ₹3,400 per design) | [JLCPCB](https://cart.jlcpcb.com/quote), UPS to India | US$15.40 per design + US$9.83 shipping, plus customs | in cart |
| Switch plate | Clear polycarbonate solid sheet, 1.5 mm, 6 × 24 in. (152 × 610 mm), CNC-routed into both halves with case/plate/dxf/<br>*Each half (169.8 × 130.6 mm) needs a 178 × 139 mm piece; a strip holds three. Routed, not laser-cut. Cutting notes in case/plate/PLATE.md. The Gerbers in case/plate/gerber/ order the same plate in FR-4 from a PCB fab instead.* | 2 | 1 pack of 2 sheets | [Amazon.in, V-LITE 1.5 mm](https://www.amazon.in/dp/B0GXG2SW48), size 6x24IN, then a CNC router service |  | ₹704 per 2 | decided |
| LED assembly (optional) | JLCPCB assembly of the SK6812MINI-E only<br>*Avoids hand-soldering 66 LEDs; adds cost and lead time.* | — | optional | — | JLCPCB | TBD | optional |

## Switches & keycaps

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Switches | Akko V3 Lavender Purple Pro: tactile, 5-pin, 40 gf operating / 55 gf bump, 3.8 mm travel, clear PC top, POM stem<br>*Light, rounded tactile and not loud. The clear top lets the per-key LEDs through. 24 spare.* | 66 | 90 (2 × 45) | [StacksKB, pack of 45](https://stackskb.com/store/akko-v3-lavender-purple-pro-switch-pack-of-45/) | AKKO official store | ₹1,099 per 45 (₹2,198) | decided |
| Keycaps | Blank DSA PBT, smoke translucent (LBlack), 50 × 1u, plus 2 × 1u accents in mixed colours, 14 × 1.25u<br>*No stabilizers (nothing over 1.25u). One seller, so the smoke shade matches across sizes.* | 66 | 60 × 1u (50 + 10 mixed); 20 × 1.25u | — | AliExpress, SZElectronic Store, all in one order to Australia: [1u, 50pcs LBlack + 10pcs Mix](https://www.aliexpress.com/item/1005008827240220.html), [1.25u, 20pcs LBlack](https://www.aliexpress.com/item/1005008827506189.html) | AU$10.40 + AU$3.98 + AU$8.09 (AU$22.47) | in cart |

## Case

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Case | 3D-printed PETG, gasket-mounted: a bottom shell and a top frame per half (case/bottom/stl/, case/top/stl/)<br>*Each half 175.4 × 143.7 mm; bottom shell 17.1 mm tall, top frame 5.5 mm.* | 2 + 2 | 2 + 2 | [Robu.in 3D printing service](https://robu.in/product/3d-printing-service1/), PETG black, 0.2 mm, 90 % infill | JLC3DP | ₹893 for the four parts | decided |
| Heat-set inserts | M2 × 3 mm brass heat-set inserts, for a 3.2 mm hole<br>*8 per half, in blind holes in the top frame's underside.* | 16 | 25 | Robu.in / StacksKB | AliExpress | TBD | decided |
| Case screws | M2 × 16 mm socket head (ISO 4762)<br>*Bottom shell to top frame, from below, heads in counterbores in the floor.* | 16 | 1 pack of 50 |  | [AliExpress, HZYUEGOU](https://www.aliexpress.com/item/32966941844.html), option 304 stainless steel / M2 / 16mm | AU$2.84 per 50 | in cart |
| Plate standoffs | M2 × 3 mm brass hex female-female standoffs, on a 0.5 mm shim (together the MX plate-to-PCB height)<br>*Five per half, screwed onto the PCB from below.* | 10 | 15 |  | [AliExpress](https://www.aliexpress.com/item/1005008798318304.html) | AU$4.31 per 100 | decided |
| Standoff shims | DIN 988 shim washers, M2: 2 × 5 × 0.5 mm, stainless<br>*One under each standoff, on the PCB, clamped by the screw from below.* | 10 | 15 |  | [AliExpress](https://www.aliexpress.com/item/1005002301164770.html) | AU$3.92 per 50 | decided |
| Plate screws | M2 × 4 mm button head (ISO 7380), 3.5 mm head<br>*Under the PCB into the standoffs at H101, H104, H201, H203 and H205, where no screw goes in on top.* | 5 | 10 |  | [AliExpress](https://www.aliexpress.com/item/32967225441.html) | AU$2.04 per 50 | decided |
| Plate screws (short) | M2 × 3 mm button head (ISO 7380), 3.5 mm head<br>*At H102, H103, H105, H202 and H204: one on top of the plate and one under the PCB into each standoff, so the two stay 0.6 mm apart.* | 10 | 20 |  | [AliExpress](https://www.aliexpress.com/item/32967225441.html) | AU$2.04 per 50 | decided |
| Gaskets | Poron strip, 80 × 4 × 3 mm, cut into 12 mm pieces (12 × 4 × 3 mm)<br>*Two pieces per plate tab, 8 tabs per half. Six pieces per strip.* | 32 pieces | 1 pack of 20 strips |  | [AliExpress, gasket Poron strip](https://www.aliexpress.com/item/1005004800667967.html), option 80x4x3MM | AU$6.93 per 20 | decided |
| Switch pads | Poron ring switch pads, 0.5 mm, open middle<br>*One per switch, stuck on the PCB under it; the open middle keeps the LED window clear.* | 66 | 1 pack of 120 |  | [AliExpress, Apc Accessories Store](https://www.aliexpress.com/item/1005009936259305.html), option PORON | AU$4.13 per 120 | decided |
| Plate foam | EVA foam sheet, 2 mm, A4, black<br>*Cut by laser or by hand from the 1:1 plate-foam files in case/foam/ (one per half, seen from above). Rests on the switch pads under the plate; no thicker than 2.8 mm, or it lifts the plate.* | 2 sheets | 2 (pack of 10) | [Amazon.in, pack of 10](https://www.amazon.in/dp/B0H4D6P874) | AliExpress | ₹140 per 10 | decided |
| Case foam | EVA foam sheet, 5 mm, A4, black<br>*Cut by laser or by hand from the 1:1 case-foam files in case/foam/ (one per half, seen from above).* | 2 sheets | 2 (pack of 5) | [Amazon.in, pack of 5](https://www.amazon.in/dp/B0D2NJD4DK) | AliExpress | ₹249 per 5 | decided |
| Steel plates | Self-adhesive steel plates, 65 × 45 × 0.6 mm, black (the plates sold for magnetic phone mounts)<br>*One per half on the inner half of the floor, long side across, for the tenting stand's magnet. No closer than 15 mm to the controller's antenna end.* | 2 | 2 (pack of 2) | [Amazon.in, LIRAMARK 2 Big Rectangle Plates](https://www.amazon.in/dp/B0D6MZCBJL) | AliExpress | ₹99 per 2 | in cart |
| Tenting stands | Magnetic tenting stand for split keyboards, black: a magnetic puck on a height- and angle-adjustable arm, detachable<br>*The puck holds to the steel plate on each half's floor; the stand comes off to lay the half flat.* | 2 | 1 pack of 2 |  | [AliExpress, GEVBAY Store](https://www.aliexpress.com/item/1005010608928916.html), option BK 2pcs | AU$20.52 per 2 | in cart |
| Rubber feet | Self-adhesive silicone bumpers, clear, domed, 8 mm across, 3 mm tall<br>*Four per half on the floor, clear of the screw counterbores and the reset pinhole; taller than a steel plate and its tape.* | 8 | 100 (pack of 100) | [Amazon.in, HASTHIP 3x8mm](https://www.amazon.in/dp/B083DTH5HL) | AliExpress | ₹179 per 100 | in cart |
| Wrist rests | Memory foam wrist rest, black, 130 mm wide, 18 mm tall, fabric top, non-slip base<br>*One in front of each half. When tented, raise it with a strip of the 5 mm case EVA.* | 2 | 2 | [Amazon.in, Techzere](https://www.amazon.in/dp/B08R41X5V6) | AliExpress | ₹299 each | in cart |

## Tools

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Soldering | Temperature-controlled iron, 0.5–0.6 mm solder, fine tweezers, solder wick<br>*From the Corne video: 350–370 °C for lead-free, flux makes SK6812s easy.* | — | — | Robu.in / Lamington Road | — | — | check what you have |
| Testing | Multimeter, IPA, thin double-sided tape for the battery (0.3 mm at most)<br>*Test each LED column as you go: one bad joint kills the chain after it.* | — | — | Robu.in / Amazon.in | — | — | check what you have |
| Flux | No-clean 559 flux paste, 10 ml syringe<br>*For the SK6812MINI-E and SOT-23 joints.* | — | 1 | [Amazon.in, SCHOFIC UV-559](https://www.amazon.in/dp/B0F4RKKKX7) | AliExpress | ₹390 | in cart |
| Kapton tape | Polyimide tape, 10 mm wide<br>*Masks neighbouring pads while soldering the LEDs.* | — | 1 roll | [Amazon.in, SCHOFIC 10 mm](https://www.amazon.in/dp/B08VH8MLT1), option 10MM | AliExpress | ₹240 | in cart |
| Puller | 2-in-1 keycap and switch puller, steel wire<br>*Switches come out of the hotswap sockets from above, through the plate.* | — | 1 | [StacksKB Switch Puller + Keycap puller](https://stackskb.com/store/switch-puller-keycap-puller/) | AliExpress | ₹200 | decided |
