#!/usr/bin/env python3
"""Datasheet audit of the routed PCB: is every part wired the way its datasheet says?

check_schematic.py proves the schematic matches the design tables in gen_schematic.py, and
`kicad-cli pcb drc --schematic-parity` proves the PCB matches the schematic. Neither asks whether
the tables themselves are right for the parts. This script does, against the PCB file that gets
fabricated: the controller pinout and its orientation under the board, which nRF52840 pins carry
which signal (NFC, near-radio, bootloader pins), the battery path through the switch, LED / diode /
encoder / TRRS / switch pinouts, antenna clearance, and the current budget.

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

# How fast each net toggles. LED data is SPI MOSI at 4 MHz (ZMK's ws2812-spi), the split UART runs
# at 115200 baud or more. ZMK scans the matrix every 1 ms while a key is held: about 1 kHz.
def role(net):
    if net == "LED_DIN": return "fast", "SK6812 data (SPI, 4 MHz)"
    if net.startswith("UART_"): return "fast", "split UART"
    if re.match(r"ROW\d$", net): return "slow", "matrix row (input, ~1 kHz)"
    if re.match(r"COL\d$", net): return "slow", "matrix column (output, ~1 kHz)"
    if net.startswith("ENC_"): return "slow", "encoder (input, < 1 kHz)"
    return None, net

# MSK12C02-HB_ShouHan.pdf (drawing; Chinese notes translated in docs/datasheets/README.md): pin 2 is
# the common pole, joined to 1 in one position and 3 in the other. Rated 50 mA at 12 V DC.
MSK_COMMON, MSK_RATED_MA = "2", 50
# SK6812MINI-E_Opsco_rev02.pdf §4/§5, seen from the lens side:
#   1 VDD (top left)      4 DIN (top right)
#   2 DOUT (bottom left)  3 GND (bottom right, chamfered corner)
# so going clockwise from the lens: VDD -> DIN -> GND -> DOUT. KiCad numbers the pins differently
# (1 VSS, 2 DIN, 3 VDD, 4 DOUT), which is why this checks positions, not numbers.
# §8: VDD 3.7-5.5 V. §9: 12 mA per colour. §10: 1 mA static per LED, VIH = 0.7 VDD.
SK_LENS_CW = ["VDD", "DIN", "VSS", "DOUT"]
SK_VDD_MIN, SK_MA_PER_LED, SK_STATIC_MA = 3.7, 3 * 12, 1.0
NICE_NANO_VCC = 3.3
# 1N4148_Vishay.pdf: band = cathode. KiCad's DO-35 footprint puts pad 1 (silk "K") under the band.
# Alps_EC11E.pdf (mounting hole drawing): A C B in a row, C (common) in the middle; push switch D/E
# on the opposite side.
# PJ-320A_XKB.pdf has the contacts but names none of them; tip/ring/sleeve follow the Keebio
# footprint's own labels. Both halves use the same footprint, so a straight cable matches them anyway.
TRRS = {"2": "tip", "3": "ring1", "4": "ring2", "1": "sleeve"}
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
       f"{side}: B+ (pad 13) on VBAT, VCC (pad 16) on the LED rail")
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
    ok(nodes(side, "VBAT") == {(u, "13"), (sw, MSK_COMMON)}, A,
       f"{side}: B+ goes only to the power switch's common pin ({MSK_COMMON}, per MSK12C02 drawing)",
       f"{side}: VBAT = {sorted(nodes(side, 'VBAT'))}")
    ok(nodes(side, "BAT_RAW") == {(bt, plus), (sw, "1")}, A,
       f"{side}: battery + (JST pad {plus}) reaches B+ only through the switch (2-1 = on)",
       f"{side}: BAT_RAW = {sorted(nodes(side, 'BAT_RAW'))}")
    ok(pad_net(bt, "2") == "GND", A, f"{side}: battery - (JST pad 2) on GND")
    pp = pads(bt)[plus].GetPosition()
    silk = [t for t in list(board.Drawings()) + list(fp(bt).GraphicalItems())
            if isinstance(t, pcbnew.PCB_TEXT) and "SilkS" in t.GetLayerName() and "+" in t.GetText()
            and mm((t.GetPosition() - pp).EuclideanNorm()) < 6]
    ok(silk, A, f"{side}: '+' printed next to the battery connector's + pad",
       f"{side}: nothing on the silkscreen marks which JST pad is + (pad {plus}); LiPo packs come wired both "
       "ways round and a reversed pack kills the charger", warn=True)
    ok(pad_net(sw, "3") is None, A, f"{side}: switch pin 3 (off throw) open")
    vcc = {r for r, _ in nodes(side, "VCC")}
    ok(all(re.match(r"(U|LED|C)\d+$", r) for r in vcc), A,
       f"{side}: VCC (switched 3.3 V) feeds only LEDs and their caps", f"{side}: VCC also on {sorted(vcc)}")
    for rail in ("VBAT", "BAT_RAW", "VCC"):
        ok(not any(r.startswith("J") for r, _ in nodes(side, rail)), A, f"{side}: {rail} not on the TRRS jack")
    ok(nodes(side, "RST") == {(u, "15"), (rst, "1")} and pad_net(rst, "2") == "GND", A,
       f"{side}: RST pad -> reset button -> GND")
    caps = {fp(f"C{d}0{i}").GetValue(): fp(f"C{d}0{i}") for i in (1, 2)}
    led1 = fp(f"LED{d}01")
    far = [v for v, cp in caps.items() if mm((cp.GetPosition() - led1.GetPosition()).EuclideanNorm()) > 10]
    ok(not far, A, f"{side}: 10 uF + 100 nF within 10 mm of the first LED", f"{side}: caps {far} far from LED{d}01")

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
    bad = []
    chain = [pad_net(f"LED{d}01", "2")]
    for i in range(1, len(leds) + 1):
        P = {skpins[k]: net(p) for k, p in pads(f"LED{d}{i:02d}").items()}
        if P["VDD"] != "VCC" or P["VSS"] != "GND": bad.append(f"LED{d}{i:02d} power")
        if P["DIN"] != chain[-1]: bad.append(f"LED{d}{i:02d} DIN")
        chain.append(P["DOUT"])
    ok(chain[0] == "LED_DIN" and not bad, A, f"{side}: one chain from P0.06 through all {len(leds)} LEDs, all on VCC/GND",
       f"{side}: chain problems {bad}")
    ok(chain[-1] is None, A, f"{side}: last DOUT left open")

    n = len(leds)
    report("WARN", A, f"{side}: SK6812MINI-E is specified for VDD {SK_VDD_MIN}-5.5 V; the nice!nano's VCC is "
           f"{NICE_NANO_VCC} V (below spec: works in most builds, blue/white dimmer). Data at 3.3 V is fine: "
           f"VIH = 0.7 x VDD = {0.7 * NICE_NANO_VCC:.2f} V")
    report("WARN", A, f"{side}: {n} LEDs x {SK_MA_PER_LED} mA = {n * SK_MA_PER_LED / 1000:.1f} A at full white; the "
           "nice!nano publishes no current limit for VCC. Cap brightness in firmware (CONFIG_ZMK_RGB_UNDERGLOW_BRT_MAX)")
    report("PASS", A, f"{side}: idle drain {n * SK_STATIC_MA:.0f} mA ({n} x {SK_STATIC_MA:.0f} mA static) is cut "
           "with VCC by the nice!nano's P0.13 switch (ZMK ext-power)")

# --------------------------------------------------------------------------------------
# 5. Matrix diodes, encoder, TRRS
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
    if fp(f"ENC{d}01"):
        e = pads(f"ENC{d}01")
        mid = sorted(("A", "B", "C"), key=lambda k: mm(e[k].GetPosition().x))[1]
        ok(mid == "C" and net(e["C"]) == "GND", A, f"{side}: EC11 common C is the middle pin and on GND (Alps EC11E)")
        ok({net(e["A"]), net(e["B"])} == {"ENC_A", "ENC_B"}, A, f"{side}: EC11 A/B on ENC_A/ENC_B (inputs with internal pull-ups)")

A = "TRRS / wired split"
maps = {}
for side, d in SIDES.items():
    j = pads(f"J{d}01")
    maps[side] = {TRRS[k]: net(p) for k, p in j.items()}
    m = maps[side]
    ok(m["sleeve"] == "GND", A, f"{side}: sleeve on GND")
    ok({m["tip"], m["ring1"]} == {"UART_TX", "UART_RX"}, A, f"{side}: tip / ring1 = UART")
    ok(m["ring2"] is None, A, f"{side}: ring2 unused (no power over the cable)")
ok(maps["left"] == maps["right"], A,
   "both halves wire the jack identically: tip = P0.08 and ring1 = P0.17 on both, so the straight TRRS cable joins "
   "P0.08-P0.08 and P0.17-P0.17. The firmware must cross them: left tx = P0.08 / rx = P0.17, "
   "right tx = P0.17 / rx = P0.08")
report("WARN", A, "ZMK's nice!nano board puts its UART on TX P0.06 / RX P0.08 (pro_micro_serial). This board uses "
       "P0.08 / P0.17 and P0.06 is LED data, so each half's overlay needs its own uart0 pinctrl")
report("WARN", A, "TX/RX have no series resistors: a powered half drives the unpowered half's RX pin above its "
       "VDD (nRF52840 abs. max VDD + 0.3 V) through the input clamp diode. Unplug the cable or keep both halves on")

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
report("WARN", "power", f"MSK12C02 is rated {MSK_RATED_MA} mA. Typing on Bluetooth draws a few mA (fine), but the "
       "nice!nano's charge current and any LED current on battery flow through it. Keep RGB off on battery")

# --------------------------------------------------------------------------------------
order = {"FAIL": 0, "WARN": 1, "PASS": 2}
w = max(len(a) for _, a, _ in results)
for status, area, msg in sorted(results, key=lambda r: order[r[0]]):
    if status != "PASS" or "-v" in sys.argv:
        print(f"{status}  {area:<{w}}  {msg}")
counts = {s: sum(1 for r in results if r[0] == s) for s in order}
print(f"\n{counts['PASS']} pass, {counts['WARN']} warn, {counts['FAIL']} fail  (-v lists the passes)")
sys.exit(1 if counts["FAIL"] else 0)
