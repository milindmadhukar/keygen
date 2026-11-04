# Datasheets

The datasheets `tools/check_datasheets.py` checks the PCB against. Every fact it uses is cited
here with the page it comes from. All are English, except where noted below.

The files are in the [datasheets release](https://github.com/milindmadhukar/keygen/releases/tag/datasheets);
`python3 tools/publish.py --fetch datasheets` downloads them into this folder.

| File | Part | Source | Used for |
|---|---|---|---|
| [`nRF52840_PS_v1.1.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/nRF52840_PS_v1.1.pdf) | Nordic nRF52840 Product Specification v1.1 | [SparkFun mirror](https://cdn.sparkfun.com/assets/d/2/6/2/6/nRF52840_PS_v1.1.pdf) (Nordic's own PDF needs a browser; the [online spec](https://docs.nordicsemi.com/bundle/ps_nrf52840/page/pin.html) has the same pin table) | Table 142, aQFN73 ball assignments (p. 578): "Standard drive, low frequency I/O only" pins, ≤ 10 kHz. UICR NFCPINS (p. 44). NFC pad capacitance and leakage (p. 157). GPIO output high, VOH ≥ VDD − 0.4 V at 0.5 mA (p. 157). Absolute maximum ratings, I/O ≤ VDD + 0.3 V (p. 612) |
| [`nice-nano-v2-pinout.png`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/nice-nano-v2-pinout.png) | nice!nano v2 pinout | [nicekeyboards.com](https://nicekeyboards.com/docs/nice-nano/pinout-schematic) | Pad order (the nRF52840 SuperMini shares it), high- and low-frequency pins, P0.13 VCC cut-off |
| [`nice-nano-v2-schematic.png`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/nice-nano-v2-schematic.png) | nice!nano v2 schematic | same page | Internal pins: P0.13 drives the XC6220 VCC regulator's enable, P0.15 is the LED, P0.00/P0.01 the 32 kHz crystal; BQ24075 charger |
| [`SK6812MINI-E_Opsco_rev02.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/SK6812MINI-E_Opsco_rev02.pdf) | SK6812MINI-E reverse-mount RGB LED | [Adafruit](https://cdn-shop.adafruit.com/product-files/4960/4960_SK6812MINI-E_REV02_EN.pdf) | §4/§5 pinout (1 VDD, 2 DOUT, 3 GND, 4 DIN, viewed from the lens side). §8 VDD 3.7–5.5 V. §9 12 mA per colour. §10 1 mA static, VIH = 0.7 VDD. p. 9 example circuit shows a bypass capacitor at each LED and input protection resistance |
| [`SK12D07VG5_ShouHan.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/SK12D07VG5_ShouHan.pdf) | Shou Han SK12D07VG5 right-angle power slide switch | [LCSC C431548](https://www.lcsc.com/product-detail/C431548.html) | p. 4: body 8.7 × 4.4 × 4.7 mm; three pins at 2 mm pitch and two mounting tabs 8.3 mm apart, in one row under the middle of the body; middle pin common, make-before-break ("SHORTING"); 2 × 2 mm knob, 4 mm out of the body and centred 2.55 mm off the board, 2 mm travel. p. 2: rated 300 mA at 50 V DC, 130–330 gf. p. 3: 5,000 cycles. **Notes partly in Chinese**: translated below |
| [`AO3401A_AOS.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/AO3401A_AOS.pdf) | AO3401A P-channel MOSFET (battery switch, LED power switch) | [Alpha & Omega](https://www.aosmd.com/res/datasheets/AO3401A.pdf) | p. 1: SOT-23 pinout (1 G, 2 S, 3 D), body diode D to S, VGS ±12 V, ID −4 A, RθJA 125 °C/W. p. 2: VGS(th) −0.5 to −1.3 V, RDS(on) < 85 mΩ at VGS = −2.5 V, VSD 0.7 V typ |
| [`AO3400A_AOS.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/AO3400A_AOS.pdf) | AO3400A N-channel MOSFET (LED power switch driver) | [Alpha & Omega](https://www.aosmd.com/res/datasheets/AO3400A.pdf) | p. 1: SOT-23 pinout (1 G, 2 S, 3 D), VGS ±12 V, ID 5.7 A. p. 2: VGS(th) 0.65 to 1.45 V, RDS(on) < 48 mΩ at VGS = 2.5 V |
| [`Alps_EC11E.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/Alps_EC11E.pdf) | Alps EC11E rotary encoder | [Alps Alpine](https://tech.alpsalpine.com/cms.media/product_catalog_ec_01_ec11e_en_611f078659.pdf) | Terminal row A C B (C = common, in the middle); switch D/E on the opposite side |
| [`HongYan_EC11H-7CE20P1ZD20F10.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/HongYan_EC11H-7CE20P1ZD20F10.pdf) | Selected HongYan EC11H encoder, 20 mm D shaft | [HongYan drawing hosted by Robu](https://robu-prod-media.s3.ap-south-1.amazonaws.com/uploads/2024/12/15.EC11H-7CE20P1ZD20F10-%E8%A7%84%E6%A0%BC%E4%B9%A6.pdf) | p. 1: body 12 × 11.7 mm, 6.5 mm tall; 7 mm bushing; recommended mounting holes 1.8 × 2.1 mm with +0.1 mm tolerance; unmarked dimensional tolerances ±0.3 mm below 10 mm and ±0.5 mm from 10 to 100 mm. The PCB uses larger 2.0 × 2.8 mm oval slots. |
| [`1N4148_Vishay.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/1N4148_Vishay.pdf) | 1N4148 (DO-35) | [Vishay](https://www.vishay.com/docs/81857/1n4148.pdf) | The band marks the cathode |
| [`JST_PH.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/JST_PH.pdf) | JST PH connector (S2B-PH-K) | [JST](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf) | Pin numbering only. JST defines no battery polarity |
| [`Kailh_CPG151101S11.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/Kailh_CPG151101S11.pdf) | Kailh MX hotswap socket | [LCSC C2803348](https://www.lcsc.com/product-detail/C2803348.html) | Bilingual (Chinese/English) |
| [`Cherry_MX.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/Cherry_MX.pdf) | Cherry MX switch | [Digi-Key](https://media.digikey.com/pdf/Data%20Sheets/Cherry%20PDFs/MX%20Series.pdf) | PCB layout |
| [`Omron_B3F.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/Omron_B3F.pdf) | 6 × 6 mm THT tactile switch (reset) | [Omron](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3f.pdf) | Generic part for the 6 mm reset footprint |
| [`Samsung_CL_MLCC.pdf`](https://github.com/milindmadhukar/keygen/releases/download/datasheets/Samsung_CL_MLCC.pdf) | Samsung CL-series MLCC catalogue | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/02336ea48ea44ca18c72517dd3cb7b47.pdf?productCode=C15850) | 1206 10 µF / 100 nF |

Facts with no datasheet behind them, from the vendors' own docs and source code:

- **Bootloader pins.** Adafruit_nRF52_Bootloader 0.6.0
  [`src/boards/nice_nano/board.h`](https://github.com/adafruit/Adafruit_nRF52_Bootloader/blob/0.6.0/src/boards/nice_nano/board.h)
  sets DFU = P0.18 ("unusable: RESET") and FRESET = P0.19 ("no connection"). Current master says
  "This board has no buttons". No edge pad is read at power-up. Double-tapping RST within 500 ms
  enters the bootloader.
- **NFC pins in ZMK.** On ZMK's Zephyr 4.1, `CONFIG_NFCT_PINS_AS_GPIOS` is gone. Use
  `&uicr { nfct-pins-as-gpios; };` ([ZMK blog](https://zmk.dev/blog/2025/12/09/zephyr-4-1)).
  Once written, the setting stays until UICR is erased.
- **SuperMini power.** The vendor's [schematic](https://img.alicdn.com/imgextra/i1/3009214883/O1CN01dX5XEt1lwSylaBst7_!!3009214883.jpg)
  ([forum post](https://chat.nologo.tech/d/80/14)): a TP4054 charger set to 100 mA, with an unfitted
  0 Ω BOOST link (about 300 mA); USB feeds VDDH through a diode while a P-MOSFET, its gate on USB,
  takes the battery off VDDH. USB 5 V reaches no header pin.
- **No wired split.** [ZMK split docs](https://zmk.dev/docs/features/split-keyboards): wired
  split is one transport per build and experimental, and a TRRS cable must never be plugged or
  unplugged while either half has power. With a battery in each half that is always, so the board
  has no TRRS jack.
- **Antenna.** nicekeyboards publishes no antenna position or keep-out. The renders show bare
  board at the end away from USB-C, so the check keeps the last 6 mm of that end clear.

## SK12D07VG5, English translation of the Chinese notes

- Title (拨动开关): slide switch, SK12D07VG5. Specification, 2nd edition, 17 June 2020.
- p. 2, general: rated 300 mA at 50 V DC; used at −25 to +70 °C; tested at 5–35 °C, 45–85 %
  humidity and 86–106 kPa unless stated otherwise.
- p. 2, electrical: contact resistance (接触电阻) 30 mΩ max, measured at 1 kHz below 100 mA.
  Insulation resistance (绝缘电阻) 250 MΩ min at 100 V DC for 1 min, between terminals and between
  the body and the pins. Withstand voltage (耐电压) 250 V AC for 1 min with a 0.5 mA trip current,
  without breakdown.
- p. 2, mechanical: operating force (动作力) 130–330 gf ±80 gf. Travel (动作行程) 2 ± 0.2 mm,
  measured moving the knob from one position to the next with twice the operating force. Knob
  strength (操作部强度): 500 gf on the knob's tip along its travel for 30 s leaves it working.
- p. 3, durability (耐久性): 5,000 cycles without load at 15–18 per minute, contact resistance
  500 mΩ max afterwards.
- p. 4, drawing: “*” marks the three key dimensions (注：“*”表示关键尺寸(3个)): a, the knob's
  length (4 mm); b, its travel (2 mm); c, the pin spacing (4 mm across the outer pins).
