# Keygen shopping checklist

What to buy for one keyboard with spares, where from, and what it costs. Prices are what the
listings showed on 2026-10-22, GST included. Specs are in the [bill of materials](../plan/bom.html).
Mark the first column `[x]` as things arrive. Anything shipped to Australia is bought on AliExpress
only, and a friend brings it to India.

Order in two stages. First the PCBs, the electronics and the AliExpress cart; build one half on the
bench and test it. Then the plate and the case, measured against the parts in hand. Estimated total
about ₹23,000 with a steel plate, ₹29,000 with FR-4 (at about ₹55 per AU$).

| Got | Item | Qty | Where | Link | Price | Notes |
|---|---|---|---|---|---|---|
| [ ] | Main PCBs, black | 5 left + 5 right | Lion Circuits | [quote](https://www.lioncircuits.com/quote) | ₹3,400 per design, ₹6,800 | Settings in [`fab/ORDER.md`](../fab/ORDER.md). Stage 1 |
| [ ] | Switch plates | 1 left + 1 right | Not decided | | FR-4 ₹3,400 per design; steel ~₹1,000–1,500 per plate | Stage 2. FR-4 from Lion with the Gerbers, or 1.5 mm steel laser-cut from [`case/plate/dxf/`](../case/plate/dxf/) (SheetCutters quotes 1.5 mm; Robu only 1 or 2 mm, which do not suit MX clips) |
| [ ] | Switches, Akko V3 Lavender Purple Pro | 90 (2 × 45) | StacksKB (in cart) | [pack of 45](https://stackskb.com/store/akko-v3-lavender-purple-pro-switch-pack-of-45/) | ₹2,198 | 24 spare |
| [ ] | Diodes 1N4148, DO-35 | 100 (10 × 10) | StacksKB (in cart) | [pack of 10](https://stackskb.com/store/1n4148-through-hole-diode/) | ₹150 | |
| [ ] | Keycaps 1u, blank DSA PBT, LBlack (smoke translucent), pack of 50 | 50 | AliExpress → Australia (in cart) | [SZElectronic Store](https://www.aliexpress.com/item/1005008827240220.html) | AU$10.40 | Option "50pcs LBlack" |
| [ ] | Keycaps 1u, blank DSA PBT, mixed colours, pack of 10 | 10 | AliExpress → Australia (in cart) | [SZElectronic Store](https://www.aliexpress.com/item/1005008827240220.html) | AU$3.98 | Option "10pcs Mix": the last 2 of the 52 × 1u, as accents, plus 8 spares |
| [ ] | Keycaps 1.25u, blank DSA PBT, LBlack (smoke translucent), pack of 20 | 20 | AliExpress → Australia (in cart) | [SZElectronic Store](https://www.aliexpress.com/item/1005008827506189.html) | AU$8.09 | Option "20pcs LBlack": 14 needed (4 of them the tall thumb keys), 6 spare |
| [ ] | Per-key LEDs SK6812MINI-E | 100 | AliExpress → Australia (in cart) | [Venuss 777 Store](https://www.aliexpress.com/item/1005007863635868.html) | AU$5.70 | 34 spare. Not stocked in India |
| [ ] | Controller, nRF52840 SuperMini (nice!nano v2 clone), pack of 5 | 5 (2 + 3 spare) | AliExpress → Australia (in cart) | [A+A+A Store](https://www.aliexpress.com/item/1005007383270623.html) | AU$23.10 | Same 24-pin header as the nice!nano; the board uses no other pads. Before soldering, check B+ (pad 13), GND and VCC (pad 16) with a multimeter, and the charge current (likely 100 mA, no BOOST jumper) |
| [ ] | Controller sockets, round-hole female header 1×40 | 10 | AliExpress → Australia (in cart) | [MT Technology](https://www.aliexpress.com/item/32717301965.html) | AU$5.09 | Round holes take only round pins, not square headers. Measure the height on arrival: it sets how deep the controller sits |
| [ ] | Controller pins, machined male header 1×40 | 4 | Robu.in (in cart) | [machined pin header](https://robu.in/product/361019140sg107601-jiln-2-54x1-9machined-pin-header-1x40p-180-l7-65-upper-pinpoint0-46-bottom-pinpoint0-46-au1u-pps/) | ₹252 | Soldered to the controllers, in place of their square headers. One strip makes three 12-pin rows |
| [ ] | OLED 0.96 in. I2C, white | 3 | Robu.in (in cart) | [OLED white](https://robu.in/product/0-96-inch-i2c-iic-oled-lcd-module-4pin-with-vcc-gnd-white/) | ₹657 | Pin order GND VCC SCL SDA, as the footprint expects. The blue Robu module puts VCC first: avoid it |
| [ ] | Rotary encoder EC11 with switch, D shaft, 20 mm | 3 | Robu.in (in cart) | [Hongyan EC11](https://robu.in/product/hongyan-ec11h-7ce20p1zd20-rotary-encoder-with-push-button-switch-vertical-plug-in-5-pin/) | ₹174 | D shaft ("hemicycle") to match the knob. Probots' EC11 is knurled |
| [ ] | Knob, aluminium 17 × 13 mm, 6 mm D shaft, pack of 10 | 2 | AliExpress → Australia (in cart) | Good Good Cheap Electronics Wholesale Store | AU$11.29 | Option "D halfshaft 17x13" |
| [ ] | Battery, LiPo 505080 (5 × 50 × 80 mm), JST-PH 2.0 | 2 | AliExpress → Australia (in cart) | [Easylander 505080](https://www.aliexpress.com/item/1005002973787972.html) | AU$14.44 + AU$7.05 shipping | Listed 3000 mAh; expect about 2500. Ask the seller about a protection board (the controller has no over-discharge cut-off); if a cell has none, add a DW01A module. Red wire is +. Check India alternatives first. Flown to India in hand luggage, connectors taped |
| [ ] | Battery connector S2B-PH-K-S | 10 | Robu.in (in cart) | [S2B-PH-K](https://robu.in/product/s2b-ph-klfsn-jst-1x2p-2p-ph-tin-2-25%e2%84%8385%e2%84%83-2a-1-2mm-brass-bend-insert-push-pullp2mm-wire-to-board-connector-rohs/) | ₹80 | Check it is the side-entry -S part |
| [ ] | P-MOSFET AO3401A, SOT-23 | 10 | Robu.in (in cart) | [AO3401A](https://robu.in/product/ao3401a-umwyoutai-semiconductor-co-ltd-30v-4-2a-50m%CF%8910v-1-4w-400mv-1-piece-p-channel-sot-23-mosfets-rohs/) | ₹36 | |
| [ ] | N-MOSFET AO3400A, SOT-23 | 10 | Robu.in (in cart) | [AO3400A](https://robu.in/product/1-month-warranty-414/) | ₹60 | |
| [ ] | Resistor 1 MΩ, 1206 | 20 | Robu.in (in cart) | [1 MΩ](https://robu.in/product/1m-ohm-1-4w-1206-surface-mount-chip-resistor-pack-of-100/) | ₹10.80 | 20, not 10: Robu needs at least ₹10 per line |
| [ ] | Resistor 100 kΩ, 1206 | 25 | Robu.in (in cart) | [100 kΩ](https://robu.in/product/100k-ohm-1-4w-1206-surface-mount-chip-resistor-pack-of-50/) | ₹11.25 | 25 for the same reason |
| [ ] | Capacitor 10 µF, 1206 | 10 | Robu.in (in cart) | [10 µF](https://robu.in/product/cl31a106kbhnnne-samsung-electro-samsung-electro-mechanics-cap-smd-mlcc-10-f-50-v-1206-pack-of-1/) | ₹110 | |
| [ ] | Capacitor 100 nF, 1206 | 10 | Robu.in (in cart) | [100 nF](https://robu.in/product/100nf-1206-surface-mount-multilayer-ceramic-capacitor-pack-of-30/) | ₹80 | |
| [ ] | Power switch MSK12C02 | 10 | Robu.in (in cart) | [MSK12C02](https://robu.in/product/mini-msk12co2-shou-han-horizontal-attachment-50ma-single-pole-double-throw-spdt-12v-10000-times-white-smd-slide-switches-rohs/) | ₹150 | Robu spells it MSK12CO2 |
| [ ] | Reset button, 6 × 6 × 5 mm | 10 | Robu.in (in cart) | [tact switch](https://robu.in/product/kfc-a06-5-0-tact-switch-4pin6x6x5/) | ₹13 | |
| [ ] | Case, PETG: 2 bottom shells + 2 top frames | 4 parts | Robu.in | [3D printing service](https://robu.in/product/3d-printing-service1/) | ~₹2,000–3,000 (estimate) | Stage 2. Upload `case/{bottom,top}/stl/`. About 250–315 g of PETG. Shop around: services vary a lot per gram |
| [ ] | Heat-set inserts M2, 3 mm long, 3.5 mm OD, pack of 100 | 16 | AliExpress → Australia (in cart) | [brass heat insert nut](https://www.aliexpress.com/item/1005006798286851.html) | AU$5.19 | Size for the case's 3.2 mm holes. 84 left for other projects |
| [ ] | Case screws M2 × 16, socket head | 20 | Amazon.in / hardware store | | | The M2 × 6 pack linked before is the wrong length now; find M2 × 16 |
| [ ] | Plate standoffs M2 × 3.5 mm, female-female | 15 | Hardware store | | ~₹300 with the screws (estimate) | The length sets the plate height for MX. If 3.5 mm is not stocked, file 4 mm ones down; not 5 mm |
| [ ] | Plate screws M2 × 4, button head | 25 | Hardware store | | | |
| [ ] | Switch pads, Poron ring, pack of 120 | 66 | AliExpress → Australia (in cart) | [Apc Accessories Store](https://www.aliexpress.com/item/1005009936259305.html), option PORON | AU$4.13 | One round each switch on the PCB, under the plate foam. Open middle, so the LED window stays clear. In place of the PE switch-foam sheet |
| [ ] | Plate foam, EVA 2 mm, A4 | 2 sheets | Amazon.in (in cart) | [black, pack of 10](https://www.amazon.in/dp/B0H4D6P874) | ₹140 | Goes between the PCB and the plate, on the switch pads. Cut from `case/foam/svg/`. No thicker than 2.8 mm, or it lifts the plate |
| [ ] | Case foam, EVA 5 mm, A4 | 2 sheets | Amazon.in (in cart) | [black, pack of 5](https://www.amazon.in/dp/B0D2NJD4DK) | ₹249 | Goes on the bottom shell's floor, under the PCB, to fill the hollow case. Cut from `case/foam/svg/` |
| [ ] | Gaskets, Poron strip 80 × 4 × 2 mm, pack of 20 | 32 pieces | AliExpress → Australia (in cart) | [gasket Poron strip](https://www.aliexpress.com/item/1005004800667967.html) | AU$7.00 | Cut each strip into six 12 mm pieces. Two per plate tab: one on the shell's ledge under the tab, one on top of it under the frame. Option 80x4x2MM |
| [ ] | Y cable, USB-A to 2 × USB-C, data and charging | 1 | AliExpress → Australia (in cart) | [Asia Market Choice Store](https://www.aliexpress.com/item/1005012373354214.html), option Black 1.8m | AU$6.14 | Optional. Powers both halves from one port, wired mode through the left. Find the data leg on arrival: plug only the left half into each leg in turn |
| [ ] | Weight and tenting | | | | | After tenting is chosen |
| [x] | Hotswap sockets, Kailh | 66 of 100 | Already owned | | | |
