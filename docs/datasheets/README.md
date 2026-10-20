# Datasheets

The datasheets `tools/check_datasheets.py` checks the PCB against. Every fact it uses is cited
here with the page it comes from. All are English, except where noted below.

| File | Part | Source | Used for |
|---|---|---|---|
| `nRF52840_PS_v1.1.pdf` | Nordic nRF52840 Product Specification v1.1 | [SparkFun mirror](https://cdn.sparkfun.com/assets/d/2/6/2/6/nRF52840_PS_v1.1.pdf) (Nordic's own PDF needs a browser; the [online spec](https://docs.nordicsemi.com/bundle/ps_nrf52840/page/pin.html) has the same pin table) | Table 142, aQFN73 ball assignments (p. 578): "Standard drive, low frequency I/O only" pins, ≤ 10 kHz. UICR NFCPINS (p. 44). NFC pad capacitance and leakage (p. 157). Absolute maximum ratings, I/O ≤ VDD + 0.3 V (p. 612) |
| `nice-nano-v2-pinout.png` | nice!nano v2 pinout | [nicekeyboards.com](https://nicekeyboards.com/docs/nice-nano/pinout-schematic) | Pad order, high- and low-frequency pins, P0.13 VCC cut-off, 100 mA charge rate (500 mA with BOOST) |
| `nice-nano-v2-schematic.png` | nice!nano v2 schematic | same page | Internal pins: P0.13 drives the XC6220 VCC regulator's enable, P0.15 is the LED, P0.00/P0.01 the 32 kHz crystal; BQ24075 charger |
| `SK6812MINI-E_Opsco_rev02.pdf` | SK6812MINI-E reverse-mount RGB LED | [Adafruit](https://cdn-shop.adafruit.com/product-files/4960/4960_SK6812MINI-E_REV02_EN.pdf) | §4/§5 pinout (1 VDD, 2 DOUT, 3 GND, 4 DIN, viewed from the lens side). §8 VDD 3.7–5.5 V. §9 12 mA per colour. §10 1 mA static, VIH = 0.7 VDD |
| `MSK12C02-HB_ShouHan.pdf` | MSK12C02-HB power slide switch | [LCSC C431541](https://www.lcsc.com/product-detail/C431541.html) | Pin 2 is common. Rated 50 mA at 12 V DC. **Notes in Chinese**: translated below |
| `PJ-320A_XKB.pdf` | PJ-320A 3.5 mm TRRS jack | [LCSC C2884926](https://www.lcsc.com/product-detail/C2884926.html) | Drawing and specs are in English; only the title block is Chinese. It does not name which pin is tip or ring |
| `Alps_EC11E.pdf` | Alps EC11E rotary encoder | [Alps Alpine](https://tech.alpsalpine.com/cms.media/product_catalog_ec_01_ec11e_en_611f078659.pdf) | Terminal row A C B (C = common, in the middle); switch D/E on the opposite side |
| `1N4148_Vishay.pdf` | 1N4148 (DO-35) | [Vishay](https://www.vishay.com/docs/81857/1n4148.pdf) | The band marks the cathode |
| `JST_PH.pdf` | JST PH connector (S2B-PH-K) | [JST](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf) | Pin numbering only. JST defines no battery polarity |
| `Kailh_CPG151101S11.pdf` | Kailh MX hotswap socket | [LCSC C2803348](https://www.lcsc.com/product-detail/C2803348.html) | Bilingual (Chinese/English) |
| `Cherry_MX.pdf` | Cherry MX switch | [Digi-Key](https://media.digikey.com/pdf/Data%20Sheets/Cherry%20PDFs/MX%20Series.pdf) | PCB layout |
| `Omron_B3F.pdf` | 6 × 6 mm THT tactile switch (reset) | [Omron](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3f.pdf) | Generic part for the 6 mm reset footprint |
| `Samsung_CL_MLCC.pdf` | Samsung CL-series MLCC catalogue | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/02336ea48ea44ca18c72517dd3cb7b47.pdf?productCode=C15850) | 0805 10 µF / 100 nF |

Facts with no datasheet behind them, from the vendors' own docs and source code:

- **Bootloader pins.** Adafruit_nRF52_Bootloader 0.6.0
  [`src/boards/nice_nano/board.h`](https://github.com/adafruit/Adafruit_nRF52_Bootloader/blob/0.6.0/src/boards/nice_nano/board.h)
  sets DFU = P0.18 ("unusable: RESET") and FRESET = P0.19 ("no connection"). Current master says
  "This board has no buttons". No edge pad is read at power-up. Double-tapping RST within 500 ms
  enters the bootloader.
- **NFC pins in ZMK.** On ZMK's Zephyr 4.1, `CONFIG_NFCT_PINS_AS_GPIOS` is gone. Use
  `&uicr { nfct-pins-as-gpios; };` ([ZMK blog](https://zmk.dev/blog/2025/12/09/zephyr-4-1)).
  Once written, the setting stays until UICR is erased.
- **Wired split.** [ZMK split docs](https://zmk.dev/docs/features/split-keyboards): full-duplex
  UART, one transport per build, experimental. Never plug or unplug a TRRS cable while either half
  has power.
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

## PJ-320A specifications (from the drawing)

Rated load 30 V 0.5 A. Contact resistance ≤ 30 mΩ. Insulation resistance ≥ 100 MΩ. Withstanding
voltage 500 V AC for 1 minute. Insertion/extraction force 3–20 N. Mating cycles: 5000 minimum.
