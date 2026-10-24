# Datasheets

The datasheets `tools/check_datasheets.py` checks the PCB against. Every fact it uses is cited
here with the page it comes from. All are English, except where noted below.

| File | Part | Source | Used for |
|---|---|---|---|
| `nRF52840_PS_v1.1.pdf` | Nordic nRF52840 Product Specification v1.1 | [SparkFun mirror](https://cdn.sparkfun.com/assets/d/2/6/2/6/nRF52840_PS_v1.1.pdf) (Nordic's own PDF needs a browser; the [online spec](https://docs.nordicsemi.com/bundle/ps_nrf52840/page/pin.html) has the same pin table) | Table 142, aQFN73 ball assignments (p. 578): "Standard drive, low frequency I/O only" pins, ≤ 10 kHz. UICR NFCPINS (p. 44). NFC pad capacitance and leakage (p. 157). GPIO output high, VOH ≥ VDD − 0.4 V at 0.5 mA (p. 157). Absolute maximum ratings, I/O ≤ VDD + 0.3 V (p. 612) |
| `nice-nano-v2-pinout.png` | nice!nano v2 pinout | [nicekeyboards.com](https://nicekeyboards.com/docs/nice-nano/pinout-schematic) | Pad order (the nRF52840 SuperMini shares it), high- and low-frequency pins, P0.13 VCC cut-off |
| `nice-nano-v2-schematic.png` | nice!nano v2 schematic | same page | Internal pins: P0.13 drives the XC6220 VCC regulator's enable, P0.15 is the LED, P0.00/P0.01 the 32 kHz crystal; BQ24075 charger |
| `SK6812MINI-E_Opsco_rev02.pdf` | SK6812MINI-E reverse-mount RGB LED | [Adafruit](https://cdn-shop.adafruit.com/product-files/4960/4960_SK6812MINI-E_REV02_EN.pdf) | §4/§5 pinout (1 VDD, 2 DOUT, 3 GND, 4 DIN, viewed from the lens side). §8 VDD 3.7–5.5 V. §9 12 mA per colour. §10 1 mA static, VIH = 0.7 VDD |
| `MSK12C02-HB_ShouHan.pdf` | MSK12C02-HB power slide switch | [LCSC C431541](https://www.lcsc.com/product-detail/C431541.html) | Pin 2 is common. Rated 50 mA at 12 V DC, which is why it only drives the MOSFET's gate. **Notes in Chinese**: translated below |
| `AO3401A_AOS.pdf` | AO3401A P-channel MOSFET (battery switch, LED power switch) | [Alpha & Omega](https://www.aosmd.com/res/datasheets/AO3401A.pdf) | p. 1: SOT-23 pinout (1 G, 2 S, 3 D), body diode D to S, VGS ±12 V, ID −4 A, RθJA 125 °C/W. p. 2: VGS(th) −0.5 to −1.3 V, RDS(on) < 85 mΩ at VGS = −2.5 V, VSD 0.7 V typ |
| `AO3400A_AOS.pdf` | AO3400A N-channel MOSFET (LED power switch driver) | [Alpha & Omega](https://www.aosmd.com/res/datasheets/AO3400A.pdf) | p. 1: SOT-23 pinout (1 G, 2 S, 3 D), VGS ±12 V, ID 5.7 A. p. 2: VGS(th) 0.65 to 1.45 V, RDS(on) < 48 mΩ at VGS = 2.5 V |
| `Alps_EC11E.pdf` | Alps EC11E rotary encoder | [Alps Alpine](https://tech.alpsalpine.com/cms.media/product_catalog_ec_01_ec11e_en_611f078659.pdf) | Terminal row A C B (C = common, in the middle); switch D/E on the opposite side |
| `HongYan_EC11H-7CE20P1ZD20F10.pdf` | Selected HongYan EC11H encoder, 20 mm D shaft | [HongYan drawing hosted by Robu](https://robu-prod-media.s3.ap-south-1.amazonaws.com/uploads/2024/12/15.EC11H-7CE20P1ZD20F10-%E8%A7%84%E6%A0%BC%E4%B9%A6.pdf) | p. 1: body 12 × 11.7 mm, 6.5 mm tall; 7 mm bushing; recommended mounting holes 1.8 × 2.1 mm with +0.1 mm tolerance; unmarked dimensional tolerances ±0.3 mm below 10 mm and ±0.5 mm from 10 to 100 mm. The PCB uses larger 2.0 × 2.8 mm oval slots. |
| `1N4148_Vishay.pdf` | 1N4148 (DO-35) | [Vishay](https://www.vishay.com/docs/81857/1n4148.pdf) | The band marks the cathode |
| `JST_PH.pdf` | JST PH connector (S2B-PH-K) | [JST](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf) | Pin numbering only. JST defines no battery polarity |
| `Kailh_CPG151101S11.pdf` | Kailh MX hotswap socket | [LCSC C2803348](https://www.lcsc.com/product-detail/C2803348.html) | Bilingual (Chinese/English) |
| `Cherry_MX.pdf` | Cherry MX switch | [Digi-Key](https://media.digikey.com/pdf/Data%20Sheets/Cherry%20PDFs/MX%20Series.pdf) | PCB layout |
| `Omron_B3F.pdf` | 6 × 6 mm THT tactile switch (reset) | [Omron](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3f.pdf) | Generic part for the 6 mm reset footprint |
| `Samsung_CL_MLCC.pdf` | Samsung CL-series MLCC catalogue | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/02336ea48ea44ca18c72517dd3cb7b47.pdf?productCode=C15850) | 1206 10 µF / 100 nF |

Facts with no datasheet behind them, from the vendors' own docs and source code:

- **Bootloader pins.** Adafruit_nRF52_Bootloader 0.6.0
  [`src/boards/nice_nano/board.h`](https://github.com/adafruit/Adafruit_nRF52_Bootloader/blob/0.6.0/src/boards/nice_nano/board.h)
  sets DFU = P0.18 ("unusable: RESET") and FRESET = P0.19 ("no connection"). Current master says
  "This board has no buttons". No edge pad is read at power-up. Double-tapping RST within 500 ms
  enters the bootloader.
- **NFC pins in ZMK.** On ZMK's Zephyr 4.1, `CONFIG_NFCT_PINS_AS_GPIOS` is gone. Use
  `&uicr { nfct-pins-as-gpios; };` ([ZMK blog](https://zmk.dev/blog/2025/12/09/zephyr-4-1)).
  Once written, the setting stays until UICR is erased.
- **No wired split.** [ZMK split docs](https://zmk.dev/docs/features/split-keyboards): wired
  split is one transport per build and experimental, and a TRRS cable must never be plugged or
  unplugged while either half has power. With a battery in each half that is always, so the board
  has no TRRS jack.
- **Antenna.** nicekeyboards publishes no antenna position or keep-out. The renders show bare
  board at the end away from USB-C, so the check keeps the last 6 mm of that end clear.

## MSK12C02-HB, English translation of the drawing notes

- Title (七脚波动): 7-pin slide switch, MSK12C02-HB. 电路图: circuit diagram (pin ② is the common
  contact, joined to ③ or ① by the slider; ④ is the metal shell). 安装参考图: recommended PCB layout.
- 技术要求, technical requirements:
  1. Part surfaces free of scratches, water marks and deformation; no defects in appearance or
     function.
  2. Rated current 50 mA at 12 V DC. Insulation resistance 100 MΩ min at 100 V DC. Dielectric
     strength 250 V AC for 1 min. Contact resistance 100 mΩ max. After 260 °C reflow, contact
     resistance changes by at most 20 % of its initial value.
  3. Clear switching feel with distinct positions and no sticking. Returns promptly when released.
- Parts list: A clip (phosphor bronze, nickel/silver plated), B base (LCP, black), C knob
  (high-temperature nylon, black), D spring (stainless steel), E contact spring (beryllium copper,
  silver plated), F cover (phosphor bronze, nickel/white plated).
