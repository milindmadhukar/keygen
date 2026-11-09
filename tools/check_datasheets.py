#!/usr/bin/env python3
"""Datasheet audit of the routed PCB: is every part wired the way its datasheet says?

check_schematic.py proves the schematic matches the design tables in gen_schematic.py, and
`kicad-cli pcb drc --schematic-parity` proves the PCB matches the schematic. Neither asks whether
the tables themselves are right for the parts. This script does, against the PCB file that gets
fabricated: the controller pinout and its orientation under the board, which nRF52840 pins carry
which signal (NFC, near-radio, bootloader pins), the battery path through the switch, LED / diode /
encoder / switch pinouts, antenna clearance, and the current budget.

Every fact is copied from a PDF in docs/datasheets/ (see the README there) and cited where it is
used. Prints PASS / WARN / FAIL per check and exits 1 if anything FAILs. WARN is something that
works but is outside a datasheet limit or needs a firmware/assembly step; read them.
"""
import math, re, sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
from sexp import find, first, parse
import gen_schematic as g

ROOT = Path(__file__).resolve().parent.parent
SIDES = {"left": "1", "right": "2"}          # reference prefix digit: U101 / U201

# --------------------------------------------------------------------------------------
# Datasheet facts
# --------------------------------------------------------------------------------------
# nice!nano v2 pinout (nice-nano-v2-pinout.png, from nicekeyboards.com/docs/nice-nano/pinout-schematic),
# viewed from the component side with USB-C at the top. Pro Micro numbering: left column 1-12 top
# to bottom, right column 13-24 top to bottom. The image's back view shows the columns swapped.
NICE_NANO = {
    1: "P0.06", 2: "P0.08", 3: "GND", 4: "GND", 5: "P0.17", 6: "P0.20", 7: "P0.22", 8: "P0.24",
    9: "P1.00", 10: "P0.11", 11: "P1.04", 12: "P1.06",
    13: "B+", 14: "GND", 15: "RST", 16: "VCC", 17: "P0.31", 18: "P0.29", 19: "P0.02", 20: "P1.15",
    21: "P1.13", 22: "P1.11", 23: "P0.10", 24: "P0.09",
}
# nRF52840_PS_v1.1.pdf
#  - Table 142, aQFN73 ball assignments (p. 578), "Recommended usage" column: these pins are
#    "Standard drive, low frequency I/O only" ("Low frequency I/O is signals with a frequency up to
#    10 kHz"). The nice!nano pinout colours the same pins "Low Frequency".
#  - §UICR NFCPINS (p. 44): P0.09 = NFC1, P0.10 = NFC2 are NFC antenna pads until NFCPINS.PROTECT is
#    cleared. GPIO electrical spec (p. 157): 4 pF pads and 1-10 uA leakage between them when driven to
#    different levels.
#  - Absolute maximum ratings (p. 612): any I/O -0.3 V to VDD + 0.3 V.
#  - No boot-strap pins: every GPIO resets to a disconnected input; P0.18 is nRESET (the nice!nano's RST).
LOW_FREQ = {"P0.02", "P0.03", "P0.09", "P0.10", "P0.28", "P0.29", "P0.30", "P0.31",
            "P1.01", "P1.02", "P1.03", "P1.04", "P1.05", "P1.06", "P1.07",
            "P1.10", "P1.11", "P1.12", "P1.13", "P1.14", "P1.15"}
NFC_PINS = {"P0.09": "NFC1", "P0.10": "NFC2"}
# Adafruit_nRF52_Bootloader 0.6.0, src/boards/nice_nano/board.h: BUTTON_1 (DFU) = P0.18 ("unusable:
# RESET"), BUTTON_2 (FRESET) = P0.19 ("no connection"); master: "This board has no buttons". Neither
# reaches an edge pad, so nothing wired here can push the board into DFU at power-up.
BOOT_SAMPLED = {"P0.18", "P0.19"}
# Used on the nice!nano itself (pinout + schematic): VCC cut-off (low = off), blue LED, reset, 32 kHz crystal.
NICE_NANO_INTERNAL = {"P0.13": "VCC cut-off", "P0.15": "blue LED", "P0.18": "nRESET",
                      "P0.00": "32 kHz crystal", "P0.01": "32 kHz crystal"}

# How fast each net toggles. LED data is SPI MOSI at 4 MHz (ZMK's ws2812-spi). ZMK scans the matrix every 1 ms while a key is held: about 1 kHz.
def role(net):
    if net == "LED_DIN": return "fast", "SK6812 data (SPI, 4 MHz)"
    if re.match(r"ROW\d$", net): return "slow", "matrix row (input, ~1 kHz)"
    if re.match(r"COL\d$", net): return "slow", "matrix column (output, ~1 kHz)"
    if net.startswith("ENC_"): return "slow", "encoder (input, < 1 kHz)"
    if net == "LED_EN": return "slow", "LED boost enable (output, changes when the LEDs turn on or off)"
    if net in ("OLED_SDA", "OLED_SCL"): return "fast", "OLED I2C (400 kHz)"
    return None, net

# SK12D07VG5_ShouHan.pdf (p. 4 drawing): the middle pin (2) is the common pole, joined to 1 in one
# position and 3 in the other, and it makes before it breaks ("SHORTING"). Rated 300 mA at 50 V DC (p. 2).
SLIDE_COMMON, SLIDE_RATED_MA = "2", 300
# AO3401A_AOS.pdf (p. 1): SOT-23, top view G bottom left (1), S bottom right (2), D top (3). Body diode
# anode on D, cathode on S. VDS -30 V, VGS +-12 V, ID -4 A, VGS(th) -0.5..-1.3 V, RDS(on) < 85 mOhm at
# VGS = -2.5 V, VSD up to 1 V, RthJA 125 C/W (steady state, max).
AO_PINS = {"1": "G", "2": "S", "3": "D"}
AO_RDS_25V_MOHM, AO_VGS_MAX, AO_VSD_V, AO_RTH_JA = 85, 12, 0.7, 125
# TPS61023_TI.pdf: SOT-563 (DRL), p. 3: 1 FB, 2 EN, 3 VIN, 4 GND, 5 SW, 6 VOUT. p. 5: VREF 580-610 mV
# (595 typ, PWM), EN high above 1.2 V, valley switch limit 2.7-3.7 A, shutdown 0.1 uA with VOUT
# disconnected, VOUT 2.2-5.5 V, OVP 5.5-6.0 V. p. 4: L 0.37-2.9 uH, C_OUT >= 4 uF effective.
# p. 12: VOUT = VREF x (1 + R1/R2); p. 18: layout example.
BOOST_PINS = {"1": "FB", "2": "EN", "3": "VIN", "4": "GND", "5": "SW", "6": "VOUT"}
BOOST_VREF = (0.580, 0.595, 0.610)
BOOST_EN_HIGH, BOOST_ILIM_A, BOOST_EFF = 1.2, 2.7, 0.9
# SN74LV1T125_TI.pdf: SOT-23-5 (DBV), p. 3: 1 OE (active low), 2 A, 3 GND, 4 Y, 5 VCC. p. 6: VIH 2.03 V
# at VCC 4.5-5.0 V, 2.11 V at 5.5 V. p. 1: inputs 5.0 V tolerant, also with VCC at 0 V.
BUF_PINS = {"1": "OE", "2": "A", "3": "GND", "4": "Y", "5": "VCC"}
BUF_VIH_5V = 2.11
# nRF52840_PS_v1.1.pdf, GPIO electrical specification (p. 157): VOH >= VDD - 0.4 V at 0.5 mA
# (standard drive). The nice!nano runs the nRF52840 at 3.3 V.
NRF_VDD, NRF_VOH_DROP = 3.3, 0.4
# SuperMini charger (vendor schematic, TP4054): 100 mA; with its BOOST link bridged, as Keygen's
# build does, about 300 mA. SW_MA is the most the battery switch carries: the boost's input at the
# LED brightness cap from a 3.0 V cell. LiPo 3.0-4.2 V.
CHARGE_MA, VBAT_MIN, VBAT_MAX = 300, 3.0, 4.2
# SK6812MINI-E_Opsco_rev02.pdf §4/§5, seen from the lens side:
#   1 VDD (top left)      4 DIN (top right)
#   2 DOUT (bottom left)  3 GND (bottom right, chamfered corner)
# so going clockwise from the lens: VDD -> DIN -> GND -> DOUT. KiCad numbers the pins differently
# (1 VSS, 2 DIN, 3 VDD, 4 DOUT), which is why this checks positions, not numbers.
# §8: VDD 3.7-5.5 V. §9: 12 mA per colour. §10: 1 mA static per LED, VIH = 0.7 VDD.
SK_LENS_CW = ["VDD", "DIN", "VSS", "DOUT"]
SK_VDD_MIN, SK_MA_PER_LED, SK_STATIC_MA = 3.7, 3 * 12, 1.0
# 1N4148_Vishay.pdf: band = cathode. KiCad's DO-35 footprint puts pad 1 (silk "K") under the band.
# Alps_EC11E.pdf (mounting hole drawing): A C B in a row, C (common) in the middle; push switch D/E
# on the opposite side.
# JST_PH.pdf: pin 1 / pin 2 only. LiPo packs come wired either way round; check before plugging in.

# --------------------------------------------------------------------------------------
results = []
def report(status, area, msg):
    results.append((status, area, msg))

def ok(cond, area, msg, fail_msg=None, warn=False):
    report("PASS" if cond else ("WARN" if warn else "FAIL"), area, msg if cond else (fail_msg or msg))

args = [a for a in sys.argv[1:] if not a.startswith("-")]
board = pcbnew.LoadBoard(args[0] if args else str(ROOT / "pcb/keygen.kicad_pcb"))
mm = pcbnew.ToMM
outline = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(outline, False)
def fp(ref): return board.FindFootprintByReference(ref)
def net(pad):
    n = pad.GetNetname()
    return n.rsplit("/", 1)[-1] if pad.GetNetCode() > 0 and not n.startswith("unconnected-") else None
def pads(ref): return {p.GetNumber(): p for p in fp(ref).Pads() if p.GetNumber() not in ("", "MP")}
def pad_net(ref, num): return net(pads(ref)[num])
def nodes(side, name):
    """(ref, pad) of every pad on /side/name."""
    return {(f.GetReference(), p.GetNumber()) for f in board.GetFootprints() for p in f.Pads()
            if p.GetNetname() == f"/{side}/{name}"}

def lib_pins(lib, name):
    """pin number -> name for a stock KiCad symbol, following `extends`."""
    tree = parse((Path("/usr/share/kicad/symbols") / lib).read_text())
    syms = {s[1]: s for s in find(tree, "symbol")}
    s = syms[name]
    if first(s, "extends"): s = syms[first(s, "extends")[1]]
    return {first(p, "number")[1]: first(p, "name")[1] for u in find(s, "symbol") for p in find(u, "pin")}

def pin_names(ref):
    """pin number -> name of a placed part's schematic symbol (stock or the project's own library),
    if its footprint has a pad for every pin."""
    v = fp(ref).GetValue()
    if "TPS61023" in v:
        tree = parse((ROOT / "pcb/lib/keygen.kicad_sym").read_text())
        sym = next(x for x in find(tree, "symbol") if x[1] == "TPS61023")
        names = {first(q, "number")[1]: first(q, "name")[1] for u in find(sym, "symbol") for q in find(u, "pin")}
    elif "LV1T125" in v:
        names = lib_pins("Logic_LevelTranslator.kicad_sym", "SN74LV1T125DBV")
    else:
        return {}
    names = {k: n.replace("~{", "").replace("}", "") for k, n in names.items()}
    return names if set(names) == set(pads(ref)) else {}

# --------------------------------------------------------------------------------------
# 1. Controller pinout and orientation
# --------------------------------------------------------------------------------------
A = "controller pinout"
diff = {p: (g.MCU_PINS[p], NICE_NANO[p]) for p in NICE_NANO if g.MCU_PINS.get(p) != NICE_NANO[p]}
ok(not diff, A, "schematic symbol's 24 pads match the nice!nano v2 pinout",
   f"schematic symbol disagrees with the nice!nano pinout: {diff}")

for side, d in SIDES.items():
    u = fp(f"U{d}01")
    P = pads(f"U{d}01")
    # USB end: the footprint's "USB" text (marbastlib), which must sit at the board's top edge.
    usb = next(t for t in u.GraphicalItems() if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() == "USB")
    c, up = u.GetPosition(), usb.GetPosition() - u.GetPosition()
    L = up.EuclideanNorm()
    beyond = lambda a: pcbnew.VECTOR2I(int(c.x + up.x / L * pcbnew.FromMM(a)), int(c.y + up.y / L * pcbnew.FromMM(a)))
    ok(outline.Contains(beyond(33.3 / 2 - 3)) and not outline.Contains(beyond(33.3 / 2 + 1)) and up.y < 0, A,
       f"{side}: USB-C end of U{d}01 reaches the board's top edge", f"{side}: USB-C end of U{d}01 is not at the top edge")
    # Seen from the component side with USB up, pad 1 (P0.06) is on the LEFT. On the back of the
    # board the component side faces away from the PCB, so from the front it appears on the RIGHT.
    p1 = P["1"].GetPosition() - c
    cross = up.x * p1.y - up.y * p1.x                  # > 0: pad 1 clockwise of USB (right of it)
    back = u.GetLayer() == pcbnew.B_Cu
    ok((cross > 0) == back, A,
       f"{side}: pad 1 (P0.06) lands where the nice!nano's P0.06 is, with the controller under the board "
       "component side (chip, USB-C) facing AWAY from the PCB",
       f"{side}: pinout is mirrored for a controller mounted on the {'back' if back else 'front'}")
    ok(pad_net(f"U{d}01", "13") == "VBAT" and pad_net(f"U{d}01", "16") == "VCC", A,
       f"{side}: B+ (pad 13) on VBAT, the LEDs run from the battery; VCC (pad 16, the switched 3.3 V) powers the OLED")
    # nice!nano schematic: P0.13 drives VCC's cut-off switch (low = off); the firmware's gpio-hog holds it high
    oled = pads(f"J{d}01")
    want = {"1": "GND", "2": "VCC", "3": "OLED_SCL", "4": "OLED_SDA"}
    ok({n: net(p) for n, p in oled.items()} == want, A,
       f"{side}: OLED header J{d}01 is GND, VCC, SCL, SDA (the usual 0.96 in. module's order), SCL on P0.20, SDA on P0.17",
       f"{side}: OLED header J{d}01 pins {({n: net(p) for n, p in oled.items()})}")
    gnd = [n for n in ("3", "4", "14") if pad_net(f"U{d}01", n) != "GND"]
    ok(not gnd, A, f"{side}: all three GND pads (3, 4, 14) on GND", f"{side}: GND pads {gnd} not on GND")

# --------------------------------------------------------------------------------------
# 2. Pin restrictions (nRF52840 PS + nice!nano)
# --------------------------------------------------------------------------------------
A = "pin functions"
for side, d in SIDES.items():
    used = {NICE_NANO[int(n)]: net(p) for n, p in pads(f"U{d}01").items()
            if net(p) and NICE_NANO[int(n)] not in ("GND", "B+", "VCC", "RST")}
    for pin, n in sorted(used.items()):
        speed, what = role(n)
        notes, fails = [], []
        if speed is None: fails.append("not a signal this design expects on a GPIO")
        if pin in LOW_FREQ:
            (notes if speed == "slow" else fails).append("low-frequency pin (<= 10 kHz)")
        if pin in BOOT_SAMPLED: fails.append("read by the bootloader at power-up")
        if pin in NICE_NANO_INTERNAL: fails.append(f"used on the nice!nano ({NICE_NANO_INTERNAL[pin]})")
        line = f"{side}: {pin} {n}: {what}" + (f"; {', '.join(notes)}" if notes else "")
        if fails:
            report("FAIL", A, f"{line}: {', '.join(fails)}")
        elif pin in NFC_PINS:
            report("WARN", A, f"{line}; {pin} is {NFC_PINS[pin]}: firmware needs `&uicr {{ nfct-pins-as-gpios; }};` "
                   "or the pin stays an NFC pad and the encoder reads dead")
        else:
            report("PASS", A, line)
    free = sorted(p for p in NICE_NANO.values() if p.startswith("P") and p not in used)
    report("PASS", A, f"{side}: unused pins left unconnected: {', '.join(free) or 'none'}")
    hits = sorted(set(used) & (BOOT_SAMPLED | set(NICE_NANO_INTERNAL)))
    ok(not hits, A, f"{side}: no bootloader-sampled or nice!nano-internal pin is wired (nRF52840 has no strap pins)",
       f"{side}: {hits}")

# --------------------------------------------------------------------------------------
# 3. Battery path and power rails
# --------------------------------------------------------------------------------------
A = "power"
for side, d in SIDES.items():
    bt, sw, rst, u = f"BT{d}01", f"SW{d}90", f"SW{d}91", f"U{d}01"
    bpins = lib_pins("Device.kicad_sym", "Battery_Cell")       # 1 +, 2 -
    plus = next(n for n, nm in bpins.items() if nm == "+")
    q, r = f"Q{d}01", f"R{d}01"
    qpins = lib_pins("Transistor_FET.kicad_sym", "AO3401A")
    ok(qpins == AO_PINS and len(pads(q)) == 3, A, f"{side}: AO3401A symbol pins 1 G / 2 S / 3 D match the datasheet's SOT-23",
       f"{side}: AO3401A symbol pins {qpins}, datasheet {AO_PINS}")
    ok(nodes(side, "BAT_RAW") == {(bt, plus), (q, "2"), (r, "2")}, A,
       f"{side}: battery + (JST pad {plus}) on the MOSFET's source; the body diode (D -> S) blocks it from B+ when off",
       f"{side}: BAT_RAW = {sorted(nodes(side, 'BAT_RAW'))}")
    ok(nodes(side, "BAT_GATE") == {(q, "1"), (sw, SLIDE_COMMON), (r, "1")}, A,
       f"{side}: gate on the slide switch's common pin ({SLIDE_COMMON}, per SK12D07VG5 drawing) and the gate resistor",
       f"{side}: BAT_GATE = {sorted(nodes(side, 'BAT_GATE'))}")
    ok(pad_net(sw, "1") == "GND", A, f"{side}: switch 2-1 grounds the gate (on)")
    ok(pad_net(bt, "2") == "GND", A, f"{side}: battery - (JST pad 2) on GND")
    pp = pads(bt)[plus].GetPosition()
    silk = [t for t in list(board.Drawings()) + list(fp(bt).GraphicalItems())
            if isinstance(t, pcbnew.PCB_TEXT) and t.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and "+" in t.GetText()
            and mm((t.GetPosition() - pp).EuclideanNorm()) < 6]
    ok(silk, A, f"{side}: '+' printed next to the battery connector's + pad",
       f"{side}: nothing on the silkscreen marks which JST pad is + (pad {plus}); LiPo packs come wired both "
       "ways round and a reversed pack kills the charger", warn=True)
    ok(not pad_net(sw, "3") or pad_net(sw, "3").startswith("unconnected-"), A,
       f"{side}: switch pin 3 unconnected, so its make-before-break slide never joins GND to the battery; "
       f"off, R{d}01 holds the gate at the source",
       f"{side}: switch pin 3 is on {pad_net(sw, '3')}: mid-slide the switch joins pins 1 and 3")
    U2, L1, R2, R3, R4 = f"U{d}02", f"L{d}01", f"R{d}02", f"R{d}03", f"R{d}04"
    ok(pin_names(U2) == BOOST_PINS, A, f"{side}: TPS61023 symbol pins {BOOST_PINS} match the datasheet's SOT-563",
       f"{side}: TPS61023 symbol pins {pin_names(U2)}, datasheet {BOOST_PINS}")
    ok(nodes(side, "VBAT") == {(u, "13"), (q, "3"), (U2, "3"), (L1, "1"), (f"C{d}03", "1")}, A,
       f"{side}: B+ is fed only by the battery MOSFET's drain (Q{d}01 pin 3) and feeds the controller and the "
       f"boost's VIN, inductor and input capacitor",
       f"{side}: VBAT = {sorted(nodes(side, 'VBAT'))}")
    ok(nodes(side, "LED_SW") == {(U2, "5"), (L1, "2")}, A, f"{side}: the inductor joins VIN to the boost's SW pin",
       f"{side}: LED_SW = {sorted(nodes(side, 'LED_SW'))}")
    feeders = {(r_, p_) for r_, p_ in nodes(side, "LED_VDD") if not re.match(r"(LED|C)\d+$", r_)}
    ok(feeders == {(U2, "6"), (R2, "1"), (f"U{d}03", "5")}, A,
       f"{side}: LED_VDD is driven only by the boost's VOUT (U{d}02 pin 6); it feeds the LEDs, the buffer and the divider",
       f"{side}: LED_VDD non-capacitor nodes {sorted(feeders)}")
    ok(nodes(side, "LED_FB") == {(U2, "1"), (R2, "2"), (R4, "1")} and pad_net(R4, "2") == "GND", A,
       f"{side}: feedback divider R{d}02 (VOUT to FB) and R{d}04 (FB to GND)")
    vals = {fp(R2).GetValue(), fp(R4).GetValue()}
    r_top, r_bot = (732e3, 100e3) if vals == {"732k", "100k"} else (None, None)
    if r_top:
        vout = [v * (1 + r_top / r_bot) for v in BOOST_VREF]
        ok(SK_VDD_MIN <= vout[0] and vout[2] <= 5.5, A,
           f"{side}: VOUT = VREF x (1 + 732k/100k) = {vout[1]:.2f} V ({vout[0]:.2f}-{vout[2]:.2f} V over VREF's "
           f"tolerance), inside the SK6812MINI-E's {SK_VDD_MIN}-5.5 V",
           f"{side}: VOUT {vout[0]:.2f}-{vout[2]:.2f} V outside {SK_VDD_MIN}-5.5 V")
    else:
        report("FAIL", A, f"{side}: feedback divider values {vals}, expected 732k / 100k")
    ok(nodes(side, "LED_EN") == {(u, "2"), (U2, "2"), (R3, "1")} and pad_net(R3, "2") == "GND", A,
       f"{side}: P0.08 (pad 2) drives the boost's EN; R{d}03 holds it low before firmware configures P0.08",
       f"{side}: LED_EN = {sorted(nodes(side, 'LED_EN'))}")
    ok(NRF_VDD - NRF_VOH_DROP > BOOST_EN_HIGH, A,
       f"{side}: P0.08 high (>= {NRF_VDD - NRF_VOH_DROP:.1f} V) is above the TPS61023's {BOOST_EN_HIGH} V EN threshold")
    ok(fp(L1).GetValue() == "1uH", A, f"{side}: 1 uH inductor, inside the datasheet's 0.37-2.9 uH")
    near = [r_ for r_ in (L1, f"C{d}01", f"C{d}04", f"C{d}03")
            if mm((fp(r_).GetPosition() - fp(U2).GetPosition()).EuclideanNorm()) > 7]
    ok(not near, A, f"{side}: inductor and input/output capacitors within 7 mm of the boost",
       f"{side}: {near} far from U{d}02")
    ok(nodes(side, "RST") == {(u, "15"), (rst, "1")} and pad_net(rst, "2") == "GND", A,
       f"{side}: RST pad -> reset button -> GND")

# --------------------------------------------------------------------------------------
# 4. LEDs: physical pinout against the datasheet, chain order
# --------------------------------------------------------------------------------------
A = "LEDs"
skpins = lib_pins("LED.kicad_sym", "SK6812MINI-E")
for side, d in SIDES.items():
    leds = sorted((f for f in board.GetFootprints() if re.match(rf"LED{d}\d\d$", f.GetReference())),
                  key=lambda f: f.GetReference())
    bad = []
    for f in leds:
        c = f.GetPosition()
        ang = {skpins[p.GetNumber()]: math.atan2(p.GetPosition().y - c.y, p.GetPosition().x - c.x) for p in f.Pads()}
        # Reverse mount: the lens faces through the board. A part on the back is seen lens-first from
        # the front; a part on the front is seen lens-first from the back (mirror).
        if f.GetLayer() == pcbnew.F_Cu: ang = {k: -v for k, v in ang.items()}
        order = sorted(ang, key=ang.get)                 # increasing angle = clockwise on screen (y down)
        i = order.index("VDD")
        if order[i:] + order[:i] != SK_LENS_CW: bad.append(f.GetReference())
    ok(not bad, A, f"{side}: all {len(leds)} SK6812MINI-E land VDD/DIN/GND/DOUT where the datasheet puts them",
       f"{side}: rotated/mirrored pinout on {bad}")
    # The MX electrical pins are on the side opposite the LED window. Verify the actual routed
    # board, including the 90-degree thumb switches, rather than trusting gen_pcb.py's offset.
    keys = g.KEYS[side]
    cells = sorted([(r, c, label, width) for r, c, label, width in keys] +
                   [(r, c, "encoder", None) for r, c in [g.ENCODER_POS[side]]])
    cell_number = {(r, c): i for i, (r, c, _, _) in enumerate(cells, 1)}
    misplaced = []
    for i, (r, c, _, _) in enumerate(keys, 1):
        switch = fp(f"SW{d}{cell_number[(r, c)]:02d}")
        led = fp(f"LED{d}{i:02d}")
        v = led.GetPosition() - switch.GetPosition()
        pin_holes = [p for p in switch.Pads() if p.GetNumber() in ("1", "2") and p.GetDrillSize().x > 0]
        pin_mid = pcbnew.VECTOR2I(sum(p.GetPosition().x for p in pin_holes) // 2,
                                  sum(p.GetPosition().y for p in pin_holes) // 2)
        pin_v = pin_mid - switch.GetPosition()
        cuts = [item.GetBoundingBox() for item in led.GraphicalItems() if item.GetLayer() == pcbnew.Edge_Cuts]
        if cuts:
            x0, x1 = min(b.GetLeft() for b in cuts), max(b.GetRight() for b in cuts)
            y0, y1 = min(b.GetTop() for b in cuts), max(b.GetBottom() for b in cuts)
            opening = (mm(x1 - x0), mm(y1 - y0))
            centred = mm(abs(x0 + x1 - 2 * led.GetPosition().x)) < 0.2 and \
                        mm(abs(y0 + y1 - 2 * led.GetPosition().y)) < 0.2
        else:
            opening, centred = (0, 0), False
        if not (abs(mm(v.EuclideanNorm()) - 5.08) < 0.02 and v.x * pin_v.x + v.y * pin_v.y < 0 and
                centred and min(opening) >= 3.0):
            misplaced.append((switch.GetReference(), led.GetReference(), round(mm(v.EuclideanNorm()), 2), opening))
    ok(not misplaced and len(keys) == len(leds), A,
       f"{side}: all {len(keys)} LEDs sit 5.08 mm from their switches, opposite the switch pins, "
       "with centred light openings at least 3.0 mm across",
       f"{side}: switch/LED opening placement errors: {misplaced}")
    bad = []
    chain = [pad_net(f"LED{d}01", "2")]
    for i in range(1, len(leds) + 1):
        P = {skpins[k]: net(p) for k, p in pads(f"LED{d}{i:02d}").items()}
        if P["VDD"] != "LED_VDD" or P["VSS"] != "GND": bad.append(f"LED{d}{i:02d} power")
        if P["DIN"] != chain[-1]: bad.append(f"LED{d}{i:02d} DIN")
        chain.append(P["DOUT"])
    U3, R5 = f"U{d}03", f"R{d}05"
    ok(pin_names(U3) == BUF_PINS, A, f"{side}: SN74LV1T125 symbol pins {BUF_PINS} match the datasheet's SOT-23-5",
       f"{side}: SN74LV1T125 symbol pins {pin_names(U3)}, datasheet {BUF_PINS}")
    ok(nodes(side, "LED_DIN") == {(f"U{d}01", "1"), (U3, "2")} and pad_net(U3, "1") == "GND" and
       pad_net(U3, "5") == "LED_VDD", A,
       f"{side}: P0.06 drives the buffer's input; its OE is tied low and it runs from LED_VDD",
       f"{side}: LED_DIN = {sorted(nodes(side, 'LED_DIN'))}, OE {pad_net(U3, '1')}, VCC {pad_net(U3, '5')}")
    ok(nodes(side, "LED_DY") == {(U3, "4"), (R5, "1")} and nodes(side, "LED_D0") == {(R5, "2"), (f"LED{d}01", "2")}, A,
       f"{side}: buffer output -> R{d}05 -> the first LED's DIN")
    ok(mm((fp(R5).GetPosition() - fp(f"LED{d}01").GetPosition()).EuclideanNorm()) < 8, A,
       f"{side}: R{d}05 sits beside the first LED, at the far end of the data line")
    ok(chain[0] == "LED_D0" and not bad, A, f"{side}: one chain from the buffer through all {len(leds)} LEDs, all on LED_VDD/GND",
       f"{side}: chain problems {bad}")
    ok(chain[-1] is None, A, f"{side}: last DOUT left open")

    n = len(leds)
    caps = [fp(f"C{d}{g.LED_CAP_BASE + i}") for i in range(1, n + 1)]
    far = [c.GetReference() for c, l in zip(caps, leds) if mm((c.GetPosition() - l.GetPosition()).EuclideanNorm()) > 10]
    fitted = [c.GetReference() for c in caps if not c.IsDNP()]
    ok(not far and len(fitted) == n // g.LED_CAP_EVERY, A,
       f"{side}: a 100 nF footprint beside each of the {n} LEDs (within 10 mm), {len(fitted)} fitted",
       f"{side}: LED capacitors far from their LED {far}, fitted {fitted}")
    vih = BUF_VIH_5V
    ok(NRF_VDD - NRF_VOH_DROP > vih, A,
       f"{side}: LED data: the buffer's VIH is {vih} V at VCC 5.5 V; the nRF52840 guarantees VOH >= "
       f"{NRF_VDD - NRF_VOH_DROP:.1f} V. The buffer drives the chain at the rail, so the first LED's 0.7 x VDD is met")
    report("PASS", A, f"{side}: the boost holds the LEDs at about 4.95 V over the whole cell range ({VBAT_MIN}-{VBAT_MAX} V)")
    capped_white = n * (SK_STATIC_MA + SK_MA_PER_LED * 0.40)
    i_in = 4.95 * capped_white / (BOOST_EFF * VBAT_MIN)
    ok(i_in < BOOST_ILIM_A * 1000, A,
       f"{side}: {n} LEDs at the firmware's 40% cap draw about {capped_white:.0f} mA at 5 V for full white, "
       f"about {i_in:.0f} mA from a {VBAT_MIN} V cell, under the TPS61023's {BOOST_ILIM_A} A minimum switch limit",
       f"{side}: capped full white needs {i_in:.0f} mA from the cell, at the boost's limit")
    report("WARN", A, f"{side}: full white at the 40% cap draws about {4.95 * capped_white / (BOOST_EFF * 3.8):.0f} mA "
           f"from a 3.8 V cell, more than the {CHARGE_MA} mA charger replaces: a white strip can discharge the cell "
           "while USB is connected. Saturated colours and effects stay under it; measure at bring-up")

# --------------------------------------------------------------------------------------
# 5. Matrix diodes, encoder
# --------------------------------------------------------------------------------------
A = "matrix"
for side, d in SIDES.items():
    diodes = [f for f in board.GetFootprints() if re.match(rf"D{d}\d\d$", f.GetReference())]
    bad = [f.GetReference() for f in diodes if not re.match(r"ROW\d$", pad_net(f.GetReference(), "1") or "")]
    ok(not bad, A, f"{side}: all {len(diodes)} 1N4148 cathodes (pad 1, band) on a ROW: matches ZMK diode-direction = \"col2row\"",
       f"{side}: cathode not on a row: {bad}")
    sws = [f for f in board.GetFootprints() if re.match(rf"SW{d}\d\d$", f.GetReference()) and f.GetReference()[-2:] not in ("90", "91")]
    bad = [f.GetReference() for f in sws if not re.match(r"COL\d$", pad_net(f.GetReference(), "1") or "")]
    ok(not bad, A, f"{side}: all {len(sws)} hotswap sockets have one side on a COL", f"{side}: {bad}")
    rows = {pad_net(f"U{d}01", str(p)) for p in range(7, 12)}
    ok(rows == {f"ROW{i}" for i in range(5)}, A, f"{side}: 5 rows and 7 columns all reach the controller")
    e = pads(f"J{d}02")
    ok(net(e["2"]) == "GND", A, f"{side}: encoder lead pin 2 (EC11 common C, the middle pin) on GND")
    ok((net(e["1"]), net(e["3"])) == ("ENC_A", "ENC_B"), A, f"{side}: encoder lead pins 1 and 3 on ENC_A/ENC_B (inputs with internal pull-ups)")
    ok(re.match(r"COL\d$", net(e["4"])) and re.match(r"K\d+$", net(e["5"])), A, f"{side}: encoder lead pins 4 and 5 are the push switch, COL and diode")

# --------------------------------------------------------------------------------------
# 6. Antenna
# --------------------------------------------------------------------------------------
A = "Bluetooth antenna"
ANT_LEN = 6.0                                  # mm from the controller's far (non-USB) end
for side, d in SIDES.items():
    u = fp(f"U{d}01"); c = u.GetPosition()
    usb = next(t for t in u.GraphicalItems() if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() == "USB")
    v = usb.GetPosition() - c; L = math.hypot(v.x, v.y); ux, uy = v.x / L, v.y / L     # towards USB
    end = 33.3 / 2                             # Pro Micro board is 18 x 33.3 mm
    pts = [pcbnew.VECTOR2I(int(c.x + pcbnew.FromMM(-a * ux + w * -uy)), int(c.y + pcbnew.FromMM(-a * uy + w * ux)))
           for a in [end - ANT_LEN + 0.5 * i for i in range(int(ANT_LEN * 2) + 1)] for w in [-9 + 0.5 * k for k in range(37)]]
    hit = []
    for z in board.Zones():
        if z.GetIsRuleArea(): continue
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(layer) and any(z.GetFilledPolysList(layer).Contains(p) for p in pts):
                hit.append(board.GetLayerName(layer))
    ok(not hit, A, f"{side}: no ground pour under U{d}01's antenna end", f"{side}: ground pour under the antenna on {hit}")
    keep = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowZoneFills()
            and all(z.Outline().Contains(p) for p in pts[::25])]
    ok(keep, A, f"{side}: a keep-out rule area protects the antenna end from future refills",
       f"{side}: no keep-out rule area over the antenna end (route_pcb.py adds one, but cleanup_pcb.py / "
       "finish_route.py reload the board without zones and drop it); a future reroute could pour ground there",
       warn=True)
    box = pcbnew.BOX2I(pcbnew.VECTOR2I(min(p.x for p in pts), min(p.y for p in pts)),
                       pcbnew.VECTOR2L(max(p.x for p in pts) - min(p.x for p in pts), max(p.y for p in pts) - min(p.y for p in pts)))
    tr = [t for t in board.GetTracks() if box.Intersects(t.GetBoundingBox())]
    nets = sorted({t.GetNetname().rsplit("/", 1)[-1] for t in tr})
    ok(not tr, A, f"{side}: no traces under the antenna end",
       f"{side}: {len(tr)} track segments ({', '.join(nets)}) cross under the antenna end", warn=True)

# --------------------------------------------------------------------------------------
# 7. Current through the power switch
# --------------------------------------------------------------------------------------
A = "power"
n = len(g.KEYS["left"])
SW_MA = 4.95 * n * (SK_STATIC_MA + SK_MA_PER_LED * 0.40) / (BOOST_EFF * VBAT_MIN)
report("PASS", "power", f"the SK12D07VG5 (rated {SLIDE_RATED_MA} mA) only switches the MOSFET gate; battery current, including "
       f"{CHARGE_MA} mA charging and the LED boost's input, flows through the AO3401A (4 A)")
drop = SW_MA * AO_RDS_25V_MOHM / 1000
ok(VBAT_MIN > 2.5 and VBAT_MAX < AO_VGS_MAX, "power",
   f"gate to GND gives VGS = -{VBAT_MIN}..-{VBAT_MAX} V: past the -2.5 V rating (RDS(on) < {AO_RDS_25V_MOHM} mOhm, "
   f"{drop:.0f} mV at {SW_MA:.0f} mA) and inside +-{AO_VGS_MAX} V")
heat = AO_VSD_V * CHARGE_MA / 1000
report("WARN", "power", f"switch off with USB plugged in: charge current can cross the body diode, "
       f"about {heat:.2f} W at {CHARGE_MA} mA, +{heat * AO_RTH_JA:.0f} C on the SOT-23; "
       "the charger senses voltage before the diode, so full-charge termination is not assured. "
       "Leave the switch on while charging")
report("PASS", "power", f"the 1 MOhm gate resistor costs {VBAT_MAX:.1f} uA at most while on ({VBAT_MAX} V across it)")
report("PASS", "power", "with the lighting off, the boost is shut down (0.1 uA) and its output disconnected, so the "
       f"{n} dark LEDs ({n * SK_STATIC_MA:.0f} mA) draw nothing; the 100 kOhm enable pull-down costs "
       f"{NRF_VDD / 100 * 1000:.0f} uA only while the lighting is on")

# --------------------------------------------------------------------------------------
order = {"FAIL": 0, "WARN": 1, "PASS": 2}
w = max(len(a) for _, a, _ in results)
for status, area, msg in sorted(results, key=lambda r: order[r[0]]):
    if status != "PASS" or "-v" in sys.argv:
        print(f"{status}  {area:<{w}}  {msg}")
counts = {s: sum(1 for r in results if r[0] == s) for s in order}
print(f"\n{counts['PASS']} pass, {counts['WARN']} warn, {counts['FAIL']} fail  (-v lists the passes)")
sys.exit(1 if counts["FAIL"] else 0)
