# Keygen shopping checklist

What to buy for one keyboard with spares, where from, and what it costs. Prices are what the
listings showed on 2026-10-22, GST included unless marked. Specs are in the
[bill of materials](../plan/bom.html). Tick items off here as they arrive.

## To decide first

- [ ] **PCB mask colour.** Lion Circuits, 5 boards of 163 × 126 mm, 2 layers: green ₹3,808 per design
  (5–6 days); black ₹8,149 per design (custom service, ₹2,200 setup, 8–9 days). Two designs.
- [ ] **Plate material and thickness.** [Robu metal laser cutting](https://robu.in/product/metal-laser-cutting/)
  has no 1.5 mm. A test quote for one plate: mild steel 1 mm ₹688, 2 mm ₹746; aluminium 1 mm ₹964,
  2 mm ₹1,075. [SheetCutters](https://www.sheetcutters.com/) quotes 1.5 mm mild steel and aluminium.
  Lion Circuits FR-4: ₹3,400 per design.
- [ ] **Battery.** No in-stock listing fits all of 2500–3000 mAh, ≤ 5 mm, ≤ 60 × 88 mm, JST-PH and
  protection. Candidates under Batteries below.

## Lion Circuits

- [ ] **Main PCBs**, 5 left + 5 right: [instant quote](https://www.lioncircuits.com/quote), settings in
  [`fab/ORDER.md`](../fab/ORDER.md) · ₹3,808 per design (green)
- [ ] **Switch plates**, if FR-4: 5 left + 5 right, settings in
  [`case/plate/PLATE.md`](../case/plate/PLATE.md) · ₹3,400 per design

## Robu.in

- [ ] **OLED**, 3: [0.96 in. I2C OLED, white, pins GND VCC SCL SDA](https://robu.in/product/0-96-inch-i2c-iic-oled-lcd-module-4pin-with-vcc-gnd-white/) · ₹219 each, ₹657. Not the blue one (VCC first).
- [ ] **Rotary encoder**, 3: [Hongyan EC11 with switch, D shaft](https://robu.in/product/hongyan-ec11h-7ce20p1zd20-rotary-encoder-with-push-button-switch-vertical-plug-in-5-pin/) · ₹58 each, ₹174
- [ ] **Controller male pins**, 4 × 1×40: [machined pin header](https://robu.in/product/361019140sg107601-jiln-2-54x1-9machined-pin-header-1x40p-180-l7-65-upper-pinpoint0-46-bottom-pinpoint0-46-au1u-pps/) · ₹63 each, ₹252
- [ ] **Battery connector**, 10: [S2B-PH-K side entry](https://robu.in/product/s2b-ph-klfsn-jst-1x2p-2p-ph-tin-2-25%e2%84%8385%e2%84%83-2a-1-2mm-brass-bend-insert-push-pullp2mm-wire-to-board-connector-rohs/) · ₹8 each, ₹80. Check it is the -S part.
- [ ] **AO3401A P-MOSFET**, 10: [link](https://robu.in/product/ao3401a-umwyoutai-semiconductor-co-ltd-30v-4-2a-50m%CF%8910v-1-4w-400mv-1-piece-p-channel-sot-23-mosfets-rohs/) · ₹36
- [ ] **AO3400A N-MOSFET**, 10: [link](https://robu.in/product/1-month-warranty-414/) · ₹60
- [ ] **1 MΩ 1206 resistor**, 10: [link](https://robu.in/product/1m-ohm-1-4w-1206-surface-mount-chip-resistor-pack-of-100/) · ₹6
- [ ] **100 kΩ 1206 resistor**, 10: [link](https://robu.in/product/100k-ohm-1-4w-1206-surface-mount-chip-resistor-pack-of-50/) · ₹5
- [ ] **10 µF 1206 capacitor**, 10: [link](https://robu.in/product/cl31a106kbhnnne-samsung-electro-samsung-electro-mechanics-cap-smd-mlcc-10-f-50-v-1206-pack-of-1/) · ₹110
- [ ] **100 nF 1206 capacitor**, 10: [link](https://robu.in/product/100nf-1206-surface-mount-multilayer-ceramic-capacitor-pack-of-30/) · ₹80
- [ ] **Power switch MSK12C02**, 10: [link](https://robu.in/product/mini-msk12co2-shou-han-horizontal-attachment-50ma-single-pole-double-throw-spdt-12v-10000-times-white-smd-slide-switches-rohs/) · ₹150
- [ ] **Reset button 6×6×5 mm**, 10: [link](https://robu.in/product/kfc-a06-5-0-tact-switch-4pin6x6x5/) · ₹13
- [ ] **Heat-set inserts M2**, 25: [M2 kit of 500](https://robu.in/product/brass-heat-insert-nut-hot-melt-knurled-threaded-m2-500pcs-kit/) · ₹1,139. Use the M2 × 3 × 3.5 mm OD size.
- [ ] **Plates**, if laser-cut metal: [metal laser cutting](https://robu.in/product/metal-laser-cutting/), upload [`case/plate/dxf/`](../case/plate/dxf/) · ~₹700–1,100 per plate
- [ ] **Case**, 2 bottom shells + 2 top frames in PETG: [FDM printing service](https://robu.in/product/3d-printing-service1/), upload `case/{bottom,top}/stl/` · quote

## StacksKB

- [ ] **Switches**, 90 (2 × 45): [Akko V3 Lavender Purple Pro, pack of 45](https://stackskb.com/store/akko-v3-lavender-purple-pro-switch-pack-of-45/) · ₹1,099 each, ₹2,198
- [ ] **Diodes 1N4148**, 100 (10 × 10): [pack of 10](https://stackskb.com/store/1n4148-through-hole-diode/) · ₹15 each, ₹150

## Meckeys

- [ ] **Keycaps 1u**, 55 (11 × 5), Grey Translucent: [Blank DSA 1u](https://meckeys.com/shop/accessories/keyboard-accessories/keycaps/blank/blank-dsa-keycaps-1u/) · ₹100 per 5, ₹1,100 (5–10 % off for 5+ sets)

## Amazon.in

- [ ] **Plate foam**, EVA 2 mm A4: [black, pack of 10](https://www.amazon.in/dp/B0H4D6P874) · ₹140
- [ ] **Case foam**, EVA 5 mm A4: [black, pack of 5](https://www.amazon.in/dp/B0D2NJD4DK) · ₹249
- [ ] **Gaskets**, 2 mm foam tape, 10 mm wide: [adhesive gasket tape, 10 m](https://www.amazon.in/dp/B09XK7YV9P) · ₹186. Or Poron from AliExpress, below.
- [ ] **Case screws M2 × 6 socket head**, 20: [SS, 25 pcs](https://www.amazon.in/dp/B0CM9M7HTR) · ₹370

## AliExpress (shipped to Australia)

- [ ] **Keycaps 1.25u**, 10, blank DSA PBT transparent black: [listing](https://www.aliexpress.us/item/3256805869245503.html) (check it still exists) ·
- [ ] **Keycaps 1.5u**, 10, blank DSA PBT transparent black: [listing](https://www.aliexpress.us/item/3256805824621950.html) · ~₹237
- [ ] **Knob**, 2, aluminium 17 × 13 mm, 6 mm D shaft (option "D halfshaft 17x13") ·
- [ ] **Plate standoffs M2 × 3.5 mm female-female**, 15 (not sold in India) ·
- [ ] **Plate screws M2 × 4 button head**, 25 ·
- [ ] **Switch pads**, 0.5 mm Poron, hot-swap version with an LED hole, 66+ ·
- [ ] **Poron sheet**, 2 mm (gaskets) or 2.5 mm (plate foam), 150 × 350 mm: [LI AN Keyboard Store](https://www.aliexpress.com/item/1005004850918011.html) · ~₹865 (2 mm), ~₹957 (2.5 mm)

## LCSC (shipped to Australia)

- [ ] **Per-key LEDs SK6812MINI-E**, 100: [C5149201](https://www.lcsc.com/product-detail/C5149201.html) · $0.0651 each, ~$6.51
- [ ] **Controller sockets**, 4 × 1×40 round-hole female header: [C9811](https://www.lcsc.com/product-detail/C9811.html) · ~$2.57

## Controllers

- [ ] **nice!nano v2, genuine**, 3. None sold in India.
  [beekeeb, pack of 2](https://shop.beekeeb.com/products/nicenano) · US$63;
  [Next Keyboard Club](https://posture.works/product/nicenano/) · $32–42, ships to India ·

## Batteries

- [ ] **LiPo 2500–3000 mAh, ≤ 5 mm, ≤ 60 × 88 mm, JST-PH, protected**, 2.
  [Probots KP-355085 3000 mAh, JST-PH, protected](https://probots.co.in/lithium-ion-rechargeable-battery-3-7v-3000mah-kp-355085.html) · ₹529, out of stock;
  [ElectronicsComp KP-405580 3200 mAh](https://www.electronicscomp.com/3.7v-3200mah-lithium-polymer-lipo-rechargeable-battery-model-kp-405580) · ₹549, 1 left, connector not stated ·

## Optional

- [ ] **Charging cable**, USB-C 1-to-2 splitter ·
- [ ] **Weight and tenting**, after tenting is chosen ·

## Already owned

- [x] **Hotswap sockets**, Kailh, 66 of the 100 owned
