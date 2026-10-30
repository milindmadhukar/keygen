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
| Controller | nRF52840 SuperMini, a nice!nano v2 clone: same 24-pin Pro Micro header and pinout (ZMK board nice_nano//zmk)<br>*2 needed + 3 spare. Charges at about 100 mA (TP4054; BOOST jumper left open): roughly a day for an empty cell. Before soldering, check B+ (pad 13), GND and VCC (pad 16) with a multimeter, and confirm the charge current. Measure USB-C height on arrival (sets case depth).* | 2 | 5 (pack of 5) |  | [AliExpress, A+A+A Store](https://www.aliexpress.com/item/1005007383270623.html) | AU$23.10 per 5 | decided |
| Controller sockets | Machined round-pin female header, 1×12, plus machined round male pins, 1×12<br>*Controller sits hidden on the PCB underside; sockets make it swappable. It rests on the male pins\' plastic carrier: measure the socket and the carrier before printing the case.* | 4 + 4 strips | 10 × 1×40 female + 2 × 1×40 male | [Robu.in, machined male pins](https://robu.in/product/361019140sg107601-jiln-2-54x1-9machined-pin-header-1x40p-180-l7-65-upper-pinpoint0-46-bottom-pinpoint0-46-au1u-pps/) | [AliExpress, MT Technology, female](https://www.aliexpress.com/item/32717301965.html) | AU$5.09 + ₹126 | in cart |
| Hotswap sockets | Kailh MX hotswap socket (CPG151101S11)<br>*66 of the 100 owned, with 34 spare.* | 66 | have 100 | Already owned (100) | AliExpress Kailh official store, 100-pack; [Divinikey 100-pack](https://divinikey.com/products/kailh-hot-swap-sockets) | owned | decided |
| Diodes | 1N4148, through-hole DO-35<br>*34 per half (each encoder's push switch is in the matrix). Cathode toward the row (COL2ROW).* | 68 | 100 | [StacksKB 1N4148 (10-pack)](https://stackskb.com/store/1n4148-through-hole-diode/) | LCSC / AliExpress (100-pack) | ₹15 per 10 (StacksKB), less per 100 | decided |
| Per-key LEDs | SK6812MINI-E (reverse mount, 3.2×2.8 mm)<br>*33 per-key per half, no underglow (the battery sits under the PCB). The only fiddly SMD part; buy plenty (34 spare), joints fail.* | 66 | 100 | Not stocked by Indian stores I checked | LCSC (~$0.08 each) / AliExpress "SK6812MINI-E" 100-pack | ~$0.08 each | decided |
| LED decoupling | 10 µF + 100 nF capacitors, 1206 SMD (C1, C2)<br>*One of each per half, at the LED power switch's output on the LED rail.* | 2 + 2 | 10 + 10 | Robu.in / Lamington Road | LCSC | negligible | decided |
| Rotary encoder | EC11 with push switch, 20 mm D shaft (half shaft)<br>*One per half. The D shaft matches the knob's 6 mm D bore. The 20 mm shaft is measured from the 6.5 mm body: cut 2.4 mm off it before soldering (INSTRUCTIONS.md, When the parts arrive).* | 2 | 2 | [Robu.in, Hongyan EC11](https://robu.in/product/hongyan-ec11h-7ce20p1zd20-rotary-encoder-with-push-button-switch-vertical-plug-in-5-pin/) | AliExpress / LCSC | ₹58 each (₹116) | decided |
| Knob | Aluminium amplifier knob, 17 mm across, 13 mm tall, for a 6 mm D shaft (AliExpress option "D halfshaft 17x13")<br>*Fits the encoder's 6 mm D shaft.* | 2 | 2 | Robu.in / Amazon.in "potentiometer knob aluminium 6mm" | AliExpress | ~₹50–150 | decided |
| OLED | 0.96 in. 128×64 OLED module, SSD1306, I2C, 4-pin (GND VCC SCL SDA)<br>*One per half, held in the top frame on four pegs and plugged into the board. Before cutting the plates or printing the case, measure the delivered board, glass and active area: the top frame holds the glass in a pocket.* | 2 | 3 | Robu.in: search "0.96 inch OLED I2C SSD1306" | AliExpress | ~₹150–250 each | measure first |
| OLED header | 1×4 right-angle male pin header, 2.54 mm (cut from a 1×40 strip)<br>*One per half, in J101 / J201 from the front, its pins pointing under the OLED. The OLED's lead plugs onto it.* | 2 | 5 strips |  | [AliExpress, DQLZV Official Store](https://www.aliexpress.com/item/1005006149080284.html), option 5PCS | AU$1.93 per 5 | in cart |
| OLED lead | Female–female jumper wires, 2.54 mm<br>*Four per half: their plug ends glued side by side into one 4-pin plug for the header, the other ends cut 45 mm away and soldered to the OLED.* | 8 | 8 | Already owned |  | — | decided |

## Power

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Battery | 3.7 V LiPo pouch, up to 5 × 60 × 88 mm including protection board; BatteriesShop KP-355085 candidate (3.5 × 50 × 85 mm, listed 3000 mAh)<br>*Source selected but not ordered. Product image appears to show a protection PCB, while listing calls it optional. Confirm both delivered packs include over-discharge protection and are ≤5 × 60 × 88 mm including the board. Ask the seller to fit JST-PH 2.0 plugs to both packs; bare insulated leads are acceptable if buying plugs locally. Check polarity with a multimeter before plugging in.* | 2 | 2 | [BatteriesShop KP-355085](https://batteriesshop.in/products/37v-3000mah-lithium-polymer-lipo-rechargeable-battery-model-kp-355085) |  | ₹425 each + 18% tax + ₹49 shipping (about ₹1,052 for 2) | decided |
| Battery cable | 2-pin JST-PH 2.0 plug (PHR-2 type) with 10 cm pre-crimped 26 AWG wires, single head<br>*Plugs into the PCB's S2B-PH-K-S socket; the battery's leads are soldered to its wires and insulated with heat-shrink, unless BatteriesShop fits PH 2.0 plugs. Check polarity at the PCB's + pad before plugging in.* | 2 | 10 |  | [AliExpress, XMS Store](https://www.aliexpress.com/item/1005007270514533.html), option Single head / 10PCS / 10CM / 2P | AU$2.61 per 10 | in cart |
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

## Switches & keycaps

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Switches | Akko V3 Lavender Purple Pro: tactile, 5-pin, 40 gf operating / 55 gf bump, 3.8 mm travel, clear PC top, POM stem<br>*Light, rounded tactile and not loud. The clear top lets the per-key LEDs through. 24 spare.* | 66 | 90 (2 × 45) | [StacksKB, pack of 45](https://stackskb.com/store/akko-v3-lavender-purple-pro-switch-pack-of-45/) | AKKO official store | ₹1,099 per 45 (₹2,198) | decided |
| Keycaps | Blank DSA PBT, smoke translucent (LBlack), 52 × 1u, 14 × 1.25u, every key the same<br>*No stabilizers (nothing over 1.25u). One seller, so the smoke shade matches across sizes.* | 66 | 60 × 1u (50 + 10); 20 × 1.25u | — | AliExpress, SZElectronic Store, all in one order to Australia: [1u, 50pcs LBlack](https://www.aliexpress.com/item/1005008827240220.html), [1u, 10pcs LBlack](https://www.aliexpress.com/item/1005010720096151.html), [1.25u, 20pcs LBlack](https://www.aliexpress.com/item/1005008827506189.html) | AU$10.89 + AU$3.89 + AU$8.09 (AU$22.87) | in cart |

## Case

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Case | 3D-printed PETG, gasket-mounted: a bottom shell and a top frame per half (case/bottom/stl/, case/top/stl/)<br>*Each half 175.4 × 143.7 mm; bottom shell 19.0 mm tall, top frame 5.5 mm.* | 2 + 2 | 2 + 2 | [Robu.in 3D printing service](https://robu.in/product/3d-printing-service1/), PETG black, 0.2 mm, 90 % infill | JLC3DP | ₹959 for the four parts | decided |
| Heat-set inserts | M2 × 3 mm brass heat-set inserts, for a 3.2 mm hole<br>*8 per half, in blind holes in the top frame's underside.* | 16 | 25 | Robu.in / StacksKB | AliExpress | TBD | decided |
| Case screws | M2 × 16 mm socket head (ISO 4762)<br>*Bottom shell to top frame, from below, heads in counterbores in the floor.* | 16 | 1 pack of 50 |  | [AliExpress, HZYUEGOU](https://www.aliexpress.com/item/32966941844.html), option 304 stainless steel / M2 / 16mm | AU$2.84 per 50 | in cart |
| Plate standoffs | M2 × 3 mm brass hex female-female standoffs, on a 0.5 mm shim (together the MX plate-to-PCB height)<br>*Five per half, screwed onto the PCB from below; the top bears on the plate.* | 10 | 15 |  | [AliExpress](https://www.aliexpress.com/item/1005008798318304.html) | AU$4.31 per 100 | decided |
| Standoff shims | DIN 988 shim washers, M2: 2 × 5 × 0.5 mm, stainless<br>*One under each standoff, on the PCB, clamped by the screw from below.* | 10 | 15 |  | [AliExpress](https://www.aliexpress.com/item/1005002301164770.html) | AU$3.92 per 50 | decided |
| Plate screws | M2 × 5 mm button head (ISO 7380), 3.5 mm head<br>*One under the PCB into each standoff, 2.9 mm into its thread. Nothing screws into the standoffs from above.* | 10 | 20 |  | [AliExpress](https://www.aliexpress.com/item/32967225441.html) | AU$2.04 per 50 | decided |
| Gaskets | Poron strip, 80 × 4 × 3 mm, cut into 12 mm pieces (12 × 4 × 3 mm)<br>*Two pieces per plate tab, 8 tabs per half. Six pieces per strip.* | 32 pieces | 1 pack of 20 strips |  | [AliExpress, gasket Poron strip](https://www.aliexpress.com/item/1005004800667967.html), option 80x4x3MM | AU$6.93 per 20 | decided |
| Switch pads | Poron ring switch pads, 0.5 mm, open middle<br>*One per switch, stuck on the PCB under it; the open middle keeps the LED window clear.* | 66 | 1 pack of 120 |  | [AliExpress, Apc Accessories Store](https://www.aliexpress.com/item/1005009936259305.html), option PORON | AU$4.13 per 120 | decided |
| Plate foam | EVA foam sheet, 2 mm, A4, black<br>*Cut from the left/right plate-foam DXFs in the build release and taped to the plate's underside with thin double-sided tape, 1 mm above the switch pads.* | 2 sheets | 2 (pack of 10) | [Amazon.in, pack of 10](https://www.amazon.in/dp/B0H4D6P874) | AliExpress | ₹140 per 10 | in cart |
| Case foam | EVA foam sheet, 5 mm, A4, black<br>*Cut by laser or by hand from the 1:1 case-foam files in case/foam/ (one per half, seen from above).* | 2 sheets | 2 (pack of 5) | [Amazon.in, pack of 5](https://www.amazon.in/dp/B0D2NJD4DK) | AliExpress | ₹249 per 5 | in cart |
| Steel plates | Self-adhesive round steel plates, 40 mm, about 0.6 mm thick, black (the plates sold for magnetic phone mounts)<br>*One per half, in a 40.6 mm pocket 1.0 mm deep in the floor's underside, so it sits flush, where the wedge's magnets hold to it. The pocket keeps 15 mm from the controller's antenna end and clear of the battery bay.* | 2 | 5 (pack of 5) | [Amazon.in, LIRAMARK 5 Round Plates](https://www.amazon.in/dp/B0D6N3WY1T) | AliExpress | ₹179 per 5 | in cart |
| Tenting wedges | 3D-printed PETG, optional, 13°: one per half (case/wedge/stl/)<br>*Printed top face down, without supports. The half stands on it on its rubber feet.* | 2 | 2 | [Robu.in 3D printing service](https://robu.in/product/3d-printing-service1/), PETG black, 0.2 mm, 20 % infill | JLC3DP | ₹1,221 for both | decided |
| Wedge magnets | Neodymium disc magnets, 10 × 3 mm, N35<br>*Four per wedge, superglued into its pockets, under the steel plate.* | 8 | 10 |  | [AliExpress, N35 10 × 3 mm](https://www.aliexpress.com/item/1005010134212551.html), option 10x3-10piece | AU$5.09 per 10 | in cart |
| Rubber feet | Self-adhesive silicone bumpers, clear, domed, 8 mm across, 3 mm tall<br>*Four per half on the floor and four under each wedge; on the floor, clear of the screw counterbores and the reset pinhole; taller than a steel plate and its tape.* | 16 | 100 (pack of 100) | [Amazon.in, HASTHIP 3x8mm](https://www.amazon.in/dp/B083DTH5HL) | AliExpress | ₹179 per 100 | in cart |
| Wrist rests | Memory foam wrist rest, black, 130 mm wide, 18 mm tall, fabric top, non-slip base<br>*One in front of each half. When tented, raise it with a strip of the 5 mm case EVA.* | 2 | 2 | [Amazon.in, Techzere](https://www.amazon.in/dp/B08R41X5V6) | AliExpress | ₹299 each | in cart |

## Tools

| Part | Spec | Per kb | Buy | India | Import | Price | Status |
|---|---|---|---|---|---|---|---|
| Soldering | Temperature-controlled iron, 0.5–0.6 mm solder, fine tweezers, solder wick<br>*From the Corne video: 350–370 °C for lead-free, flux makes SK6812s easy.* | — | — | Robu.in / Lamington Road | — | — | check what you have |
| Testing | Multimeter, IPA, thin double-sided tape for the battery and the plate foam (0.3 mm at most)<br>*Test each LED column as you go: one bad joint kills the chain after it.* | — | — | Robu.in / Amazon.in | — | — | check what you have |
| Flux | No-clean 559 flux paste, 10 ml syringe<br>*For the SK6812MINI-E and SOT-23 joints.* | — | 1 | [Amazon.in, SCHOFIC UV-559](https://www.amazon.in/dp/B0F4RKKKX7) | AliExpress | ₹390 | in cart |
| Kapton tape | Polyimide tape, 12 mm wide, 33 m<br>*Masks neighbouring pads while soldering the LEDs.* | — | 1 roll | [Amazon.in, AR Kapton 12 mm](https://www.amazon.in/dp/B0DQYJ7569) | AliExpress | ₹139 | in cart |
| Puller | 2-in-1 keycap and switch puller, steel wire<br>*Switches come out of the hotswap sockets from above, through the plate.* | — | 1 | [StacksKB Switch Puller + Keycap puller](https://stackskb.com/store/switch-puller-keycap-puller/) | AliExpress | ₹200 | decided |
