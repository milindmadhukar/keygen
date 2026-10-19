#!/usr/bin/env python3
"""Generate the Keygen KiCad schematics (left and right half) from the key table below.

Every connection is a net label placed on a pin endpoint, so the drawing is a tidy grid of
parts rather than a web of wires. Re-run after changing the tables; it overwrites
pcb/<side>/keygen-<side>.kicad_sch and the project files.
"""
import copy, json, shutil, sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sexp import Sym, dump, find, first, lib_symbol, pins

ROOT = Path(__file__).resolve().parent.parent
STOCK = Path("/usr/share/kicad/symbols")
MARB = ROOT / "lib/marbastlib/symbols"
PCB = ROOT / "pcb"
U = lambda: str(uuid.uuid4())
S = Sym

# --------------------------------------------------------------------------------------
# Design tables
# --------------------------------------------------------------------------------------
# nRF52840 Pro Micro pad -> (pin name, electrical type). Pads 1-12 down the left edge,
# 13-24 down the right edge (USB at the top), matching marbastlib's nice_nano/SuperMini
# footprints.
MCU_PINS = {
    1: "P0.06", 2: "P0.08", 3: "GND", 4: "GND", 5: "P0.17", 6: "P0.20", 7: "P0.22",
    8: "P0.24", 9: "P1.00", 10: "P0.11", 11: "P1.04", 12: "P1.06",
    13: "B+", 14: "GND", 15: "RST", 16: "VCC", 17: "P0.31", 18: "P0.29", 19: "P0.02",
    20: "P1.15", 21: "P1.13", 22: "P1.11", 23: "P0.10", 24: "P0.09",
}
MCU_TYPES = {"GND": "power_in", "B+": "power_in", "VCC": "power_out", "RST": "input"}

# Net on each MCU pad (both halves). Pads not listed get a no-connect flag.
MCU_NETS = {
    1: "LED_DIN",            # SK6812 data via SPI MOSI (ZMK led_strip)
    2: "UART_TX",            # TRRS tip   (right firmware swaps TX/RX, see note)
    5: "UART_RX",            # TRRS ring1
    3: "GND", 4: "GND", 14: "GND",
    13: "VBAT", 15: "RST", 16: "VCC",
    7: "ROW0", 8: "ROW1", 9: "ROW2", 10: "ROW3", 11: "ROW4",
    12: "COL0", 22: "COL1", 21: "COL2", 20: "COL3", 19: "COL4", 18: "COL5", 17: "COL6",
}
MCU_NETS_RIGHT = {6: "ENC_A", 24: "ENC_B"}   # P0.20, P0.09 (NFC pin: nfct-pins-as-gpios)

# (row, col, legend, keycap width). Columns run outer (0) -> inner (6) on both halves.
KEYS = {
    "left": [
        (0, 0, "=", 1.25), (0, 1, "1", 1), (0, 2, "2", 1), (0, 3, "3", 1), (0, 4, "4", 1), (0, 5, "5", 1),
        (1, 0, "Tab", 1.25), (1, 1, "Q", 1), (1, 2, "W", 1), (1, 3, "E", 1), (1, 4, "R", 1), (1, 5, "T", 1),
        (2, 0, "Esc", 1.25), (2, 1, "A", 1), (2, 2, "S", 1), (2, 3, "D", 1), (2, 4, "F", 1), (2, 5, "G", 1), (2, 6, "Alt", 1),
        (3, 0, "Shift", 1.25), (3, 1, "Z", 1), (3, 2, "X", 1), (3, 3, "C", 1), (3, 4, "V", 1), (3, 5, "B", 1), (3, 6, "Ctrl", 1),
        (4, 0, "`", 1), (4, 1, "Caps", 1), (4, 2, "Left", 1), (4, 3, "Right", 1), (4, 4, "Super", 1.25), (4, 5, "Bksp", 1.5), (4, 6, "Del", 1.5),
    ],
    "right": [
        (0, 0, "-", 1.25), (0, 1, "0", 1), (0, 2, "9", 1), (0, 3, "8", 1), (0, 4, "7", 1), (0, 5, "6", 1),
        (1, 0, "\\", 1.25), (1, 1, "P", 1), (1, 2, "O", 1), (1, 3, "I", 1), (1, 4, "U", 1), (1, 5, "Y", 1),
        (2, 0, "'", 1.25), (2, 1, ";", 1), (2, 2, "L", 1), (2, 3, "K", 1), (2, 4, "J", 1), (2, 5, "H", 1), (2, 6, "Alt", 1),
        (3, 0, "Shift", 1.25), (3, 1, "/", 1), (3, 2, ".", 1), (3, 3, ",", 1), (3, 4, "M", 1), (3, 5, "N", 1), (3, 6, "Ctrl", 1),
        (4, 0, "]", 1), (4, 1, "[", 1), (4, 2, "Down", 1), (4, 3, "Up", 1), (4, 4, "Fn", 1.25), (4, 5, "Space", 1.5), (4, 6, "Enter", 1.5),
    ],
}
ENCODER_POS = {"right": (0, 6)}   # encoder push switch sits in the matrix here
UNDERGLOW = 6

FP = {
    "mcu": "marbastlib-xp-promicroish:nice_nano_H_USBup",
    "sw": "marbastlib-mx:SW_MX_HS_CPG151101S11_{}u",
    "diode": "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
    "led": "LED_SMD:LED_SK6812MINI-E_3.2x2.8mm_P1.5mm_ReverseMount",
    "cap": "Capacitor_SMD:C_0805_2012Metric",
    "enc": "Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm",
    "trrs": "Keebio-Parts:TRRS-PJ-320A",
    "pwr": "marbastlib-various:SW_MSK12C02-HB",
    "rst": "Button_Switch_THT:SW_PUSH_6mm_H5mm",
    "bat": "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
}

# --------------------------------------------------------------------------------------
# Library symbols
# --------------------------------------------------------------------------------------
def font(size=1.27): return [S("effects"), [S("font"), [S("size"), size, size]]]
def hidden(): return [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]
def prop(name, value, x=0, y=0, hide=False):
    return [S("property"), name, value, [S("at"), x, y, 0], hidden() if hide else font()]

def make_pin(kind, x, y, ang, name, number, length=2.54):
    return [S("pin"), S(kind), S("line"), [S("at"), x, y, ang], [S("length"), length],
            [S("name"), name, font()], [S("number"), number, font()]]

def nice_nano_symbol():
    body = [S("symbol"), "nice_nano_v2_0_1",
            [S("rectangle"), [S("start"), -10.16, 17.78], [S("end"), 10.16, -15.24],
             [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]]]
    pinunit = [S("symbol"), "nice_nano_v2_1_1"]
    for pad, name in MCU_PINS.items():
        left = pad <= 12
        i = (pad - 1) if left else (pad - 13)
        y = 15.24 - i * 2.54
        pinunit.append(make_pin(MCU_TYPES.get(name, "bidirectional"), -12.7 if left else 12.7, y, 0 if left else 180, name, str(pad)))
    return [S("symbol"), "nice_nano_v2", [S("pin_names"), [S("offset"), 1.016]],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
            prop("Reference", "U", 0, 20.32), prop("Value", "nRF52840 Pro Micro (nice!nano v2)", 0, -17.78),
            prop("Footprint", FP["mcu"], hide=True),
            prop("Datasheet", "https://nicekeyboards.com/docs/nice-nano/pinout-schematic", hide=True),
            prop("Description", "nRF52840 Pro Micro-format board, nice!nano v2 pinout (24 edge pads)", hide=True),
            body, pinunit, [S("embedded_fonts"), S("no")]]

def trrs_symbol():
    body = [S("symbol"), "TRRS_PJ-320A_0_1",
            [S("rectangle"), [S("start"), -5.08, 5.08], [S("end"), 2.54, -7.62],
             [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]]]
    pu = [S("symbol"), "TRRS_PJ-320A_1_1"]
    for num, name, y in (("2", "T", 2.54), ("3", "R1", 0), ("4", "R2", -2.54), ("1", "S", -5.08)):
        pu.append(make_pin("passive", 5.08, y, 180, name, num))
    return [S("symbol"), "TRRS_PJ-320A", [S("pin_names"), [S("offset"), 1.016]],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
            prop("Reference", "J", -1.27, 7.62), prop("Value", "PJ-320A", -1.27, -10.16),
            prop("Footprint", FP["trrs"], hide=True), prop("Datasheet", "", hide=True),
            prop("Description", "3.5 mm TRRS jack, pads numbered as Keebio TRRS-PJ-320A (1 sleeve, 2 tip, 3 ring1, 4 ring2)", hide=True),
            body, pu, [S("embedded_fonts"), S("no")]]

def flatten(child_lib, child, parent_name):
    """Inline an `extends` symbol: the parent's graphics/pins with the child's properties."""
    lib = __import__("sexp").parse(open(child_lib).read())
    c = next(s for s in find(lib, "symbol") if s[1] == child)
    p = next(s for s in find(lib, "symbol") if s[1] == parent_name)
    out = [S("symbol"), child]
    for n in p[2:]:
        if isinstance(n, list) and n[0] in ("property", "symbol"): continue
        out.append(copy.deepcopy(n))
    out += [copy.deepcopy(n) for n in c[2:] if isinstance(n, list) and n[0] == "property"]
    for n in find(p, "symbol"):
        u = copy.deepcopy(n); u[1] = u[1].replace(parent_name, child, 1); out.append(u)
    return out

def keygen_lib():
    lib = [S("kicad_symbol_lib"), [S("version"), 20241209], [S("generator"), "keygen_gen_schematic"],
           [S("generator_version"), "9.0"], nice_nano_symbol(), trrs_symbol()]
    (PCB / "lib").mkdir(parents=True, exist_ok=True)
    (PCB / "lib/keygen.kicad_sym").write_text(dump(lib) + "\n")

LIBSYMS = {
    "keygen:nice_nano_v2": lambda: nice_nano_symbol(),
    "keygen:TRRS_PJ-320A": lambda: trrs_symbol(),
    "marbastlib-mx:MX_SW_HS_CPG151101S11": lambda: lib_symbol(MARB / "marbastlib-mx.kicad_sym", "MX_SW_HS_CPG151101S11"),
    "LED:SK6812MINI-E": lambda: flatten(STOCK / "LED.kicad_sym", "SK6812MINI-E", "SK6812"),
    "Device:D": lambda: lib_symbol(STOCK / "Device.kicad_sym", "D"),
    "Device:C": lambda: lib_symbol(STOCK / "Device.kicad_sym", "C"),
    "Device:RotaryEncoder_Switch": lambda: lib_symbol(STOCK / "Device.kicad_sym", "RotaryEncoder_Switch"),
    "Device:Battery_Cell": lambda: lib_symbol(STOCK / "Device.kicad_sym", "Battery_Cell"),
    "Switch:SW_SPDT": lambda: lib_symbol(STOCK / "Switch.kicad_sym", "SW_SPDT"),
    "Switch:SW_Push": lambda: lib_symbol(STOCK / "Switch.kicad_sym", "SW_Push"),
    "power:PWR_FLAG": lambda: lib_symbol(STOCK / "power.kicad_sym", "PWR_FLAG"),
}
_cache = {}
def libsym(lib_id):
    if lib_id not in _cache:
        s = copy.deepcopy(LIBSYMS[lib_id]())
        s[1] = lib_id
        _cache[lib_id] = s
    return _cache[lib_id]

# --------------------------------------------------------------------------------------
# Schematic builder
# --------------------------------------------------------------------------------------
class Sheet:
    def __init__(self, project, title):
        self.project, self.root = project, U()
        self.items, self.used = [], []
        self.title = title
        self.nets = {}          # net -> [(ref, pin)]

    def symbol(self, lib_id, ref, value, x, y, footprint="", unconnected=(), nets=None, in_bom=True, fields=()):
        """Place a symbol and connect pins by net name. nets: {pin_number: net}."""
        if lib_id not in self.used: self.used.append(lib_id)
        sym = libsym(lib_id)
        pl = pins(sym)
        node = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x, y, 0], [S("unit"), 1],
                [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes" if in_bom else "no")],
                [S("on_board"), S("yes" if in_bom else "no")], [S("dnp"), S("no")], [S("uuid"), U()],
                [S("property"), "Reference", ref, [S("at"), x, y - 6.35, 0], font()],
                [S("property"), "Value", value, [S("at"), x, y + 6.35, 0], font()],
                [S("property"), "Footprint", footprint, [S("at"), x, y, 0], hidden()],
                [S("property"), "Datasheet", "", [S("at"), x, y, 0], hidden()]]
        for k, v in fields:
            node.append([S("property"), k, v, [S("at"), x, y, 0], hidden()])
        for num, *_ in pl:
            node.append([S("pin"), num, [S("uuid"), U()]])
        node.append([S("instances"), [S("project"), self.project,
                     [S("path"), "/" + self.root, [S("reference"), ref], [S("unit"), 1]]]])
        self.items.append(node)
        nets = nets or {}
        for num, name, kind, px, py, ang in pl:
            sx, sy = round(x + px, 4), round(y - py, 4)
            net = nets.get(num) or nets.get(name)
            if net:
                self.label(net, sx, sy, (ang + 180) % 360)
                self.nets.setdefault(net, []).append((ref, num))
            else:
                self.items.append([S("no_connect"), [S("at"), sx, sy], [S("uuid"), U()]])

    def label(self, net, x, y, ang):
        just = {0: "left", 90: "left", 180: "right", 270: "right"}[int(ang)]
        self.items.append([S("label"), net, [S("at"), x, y, ang],
                           [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S(just), S("bottom")]],
                           [S("uuid"), U()]])

    def text(self, s, x, y, size=1.27):
        self.items.append([S("text"), s, [S("exclude_from_sim"), S("no")], [S("at"), x, y, 0],
                           [S("effects"), [S("font"), [S("size"), size, size]], [S("justify"), S("left"), S("top")]],
                           [S("uuid"), U()]])

    def write(self, path, date="2026-10-19", rev="0.1"):
        doc = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"], [S("generator_version"), "9.0"],
               [S("uuid"), self.root], [S("paper"), "A2"],
               [S("title_block"), [S("title"), self.title], [S("date"), date], [S("rev"), rev],
                [S("company"), "github.com/milindmadhukar/keygen"],
                [S("comment"), 1, "Generated by tools/gen_schematic.py - edit the script, not this file"]],
               [S("lib_symbols")] + [libsym(i) for i in self.used]]
        doc += self.items
        doc += [[S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]], [S("embedded_fonts"), S("no")]]
        path.write_text(dump(doc) + "\n")


def build(side):
    proj = f"keygen-{side}"
    sh = Sheet(proj, f"Keygen - {side} half")
    keys = KEYS[side]
    enc = ENCODER_POS.get(side)

    # ---- key matrix ----------------------------------------------------------------
    X0, Y0, DX, DY = 30.48, 50.8, 40.64, 27.94
    sh.text("KEY MATRIX  (COL2ROW: switch to COLn, diode cathode to ROWn)", X0 - 15.24, Y0 - 20.32, 2)
    n = 0
    cells = [(r, c, lab, w) for r, c, lab, w in keys]
    if enc: cells.append((enc[0], enc[1], "Encoder push", None))
    for r, c, lab, w in sorted(cells):
        n += 1
        x, y = X0 + c * DX, Y0 + r * DY
        k = f"K{r}{c}"
        if w is not None:
            sh.symbol("marbastlib-mx:MX_SW_HS_CPG151101S11", f"SW{n}", lab, x, y,
                      FP["sw"].format(("%g" % w)), nets={"1": f"COL{c}", "2": k})
        else:
            sh.text("Encoder S1/S2 (see ENC1)", x - 10.16, y - 2.54)
            sh.nets.setdefault(k, [])
        sh.symbol("Device:D", f"D{n}", "1N4148", x, y + 10.16, FP["diode"], nets={"1": f"ROW{r}", "2": k})

    # ---- LED chain -----------------------------------------------------------------
    LX0, LY0, LDX, LDY, PER = 30.48, 215.9, 38.1, 30.48, 8
    nled = len(keys) + UNDERGLOW
    sh.text(f"PER-KEY + UNDERGLOW LEDs  ({len(keys)} per-key, {UNDERGLOW} underglow) - "
            "powered from the controller's switched VCC (P0.13); cap brightness in firmware", LX0 - 15.24, LY0 - 20.32, 2)
    for i in range(nled):
        x, y = LX0 + (i % PER) * LDX, LY0 + (i // PER) * LDY
        din = "LED_DIN" if i == 0 else f"LED_D{i}"
        dout = f"LED_D{i+1}" if i < nled - 1 else None
        nets = {"VDD": "VCC", "VSS": "GND", "DIN": din}
        if dout: nets["DOUT"] = dout
        label = keys[i][2] if i < len(keys) else f"Underglow {i - len(keys) + 1}"
        sh.symbol("LED:SK6812MINI-E", f"LED{i+1}", "SK6812MINI-E", x, y, FP["led"], nets=nets,
                  fields=[("Position", label)])

    # ---- controller ----------------------------------------------------------------
    MX, MY = 360.68, 60.96
    sh.text("CONTROLLER  (mounted on the PCB underside, USB-C to the top edge)", MX - 25.4, MY - 30.48, 2)
    mnets = {str(k): v for k, v in MCU_NETS.items()}
    if side == "right": mnets.update({str(k): v for k, v in MCU_NETS_RIGHT.items()})
    sh.symbol("keygen:nice_nano_v2", "U1", "nRF52840 Pro Micro", MX, MY, FP["mcu"], nets=mnets)
    sh.text("UART: tip = P0.08, ring1 = P0.17 on BOTH halves.\nLeft firmware: tx P0.08 / rx P0.17.\n"
            "Right firmware: tx P0.17 / rx P0.08 (crossed in software).\n"
            + ("Encoder B on P0.09 (NFC pin): set nfct-pins-as-gpios.\n" if side == "right" else "")
            + "Spare: " + ("P0.10" if side == "right" else "P0.20, P0.09, P0.10"),
            MX + 25.4, MY - 15.24)

    # ---- power ---------------------------------------------------------------------
    PX, PY = 360.68, 132.08
    sh.text("POWER", PX - 25.4, PY - 17.78, 2)
    sh.symbol("Device:Battery_Cell", "BT1", "LiPo 3.7V ~1000mAh", PX - 20.32, PY, FP["bat"],
              nets={"1": "BAT_RAW", "2": "GND"})
    sh.symbol("Switch:SW_SPDT", "SW90", "MSK12C02 power", PX, PY, FP["pwr"],
              nets={"1": "BAT_RAW", "2": "VBAT"})
    sh.symbol("Switch:SW_Push", "SW91", "Reset", PX + 25.4, PY, FP["rst"], nets={"1": "RST", "2": "GND"})
    sh.symbol("Device:C", "C1", "10uF", PX - 20.32, PY + 22.86, FP["cap"], nets={"1": "VCC", "2": "GND"})
    sh.symbol("Device:C", "C2", "100nF", PX - 7.62, PY + 22.86, FP["cap"], nets={"1": "VCC", "2": "GND"})
    for i, net in enumerate(("GND", "VBAT")):
        sh.symbol("power:PWR_FLAG", f"#FLG0{i+1}", "PWR_FLAG", PX + 12.7 + i * 12.7, PY + 22.86, nets={"1": net}, in_bom=False)
    sh.text("C1/C2 sit next to the first LED of the chain.", PX - 25.4, PY + 33.02)

    # ---- TRRS ----------------------------------------------------------------------
    TX, TY = 360.68, 185.42
    sh.text("TRRS (optional wired split; GND/TX/RX only, never battery power)", TX - 25.4, TY - 15.24, 2)
    sh.symbol("keygen:TRRS_PJ-320A", "J1", "PJ-320A", TX, TY, FP["trrs"],
              nets={"1": "GND", "2": "UART_TX", "3": "UART_RX"})

    # ---- encoder -------------------------------------------------------------------
    if enc:
        EX, EY = 360.68, 228.6
        sh.text("ROTARY ENCODER (EC11) - push switch in the matrix at "
                f"ROW{enc[0]}/COL{enc[1]}", EX - 25.4, EY - 15.24, 2)
        sh.symbol("Device:RotaryEncoder_Switch", "ENC1", "EC11", EX, EY, FP["enc"],
                  nets={"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": f"COL{enc[1]}", "S2": f"K{enc[0]}{enc[1]}"})

    out = PCB / side
    out.mkdir(parents=True, exist_ok=True)
    sh.write(out / f"{proj}.kicad_sch")
    write_project(out, proj)
    return sh


def write_project(out, proj):
    pro = json.loads(Path("/usr/share/kicad/template/kicad.kicad_pro").read_text())
    pro.setdefault("meta", {})["filename"] = f"{proj}.kicad_pro"
    (out / f"{proj}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")
    lib = "${KIPRJMOD}/../../lib"
    (out / "sym-lib-table").write_text(
        "(sym_lib_table\n  (version 7)\n"
        '  (lib (name "keygen")(type "KiCad")(uri "${KIPRJMOD}/../lib/keygen.kicad_sym")(options "")(descr "Keygen project symbols"))\n'
        f'  (lib (name "marbastlib-mx")(type "KiCad")(uri "{lib}/marbastlib/symbols/marbastlib-mx.kicad_sym")(options "")(descr ""))\n'
        ")\n")
    fps = ["marbastlib-mx", "marbastlib-various", "marbastlib-xp-promicroish"]
    rows = "".join(f'  (lib (name "{f}")(type "KiCad")(uri "{lib}/marbastlib/footprints/{f}.pretty")(options "")(descr ""))\n' for f in fps)
    rows += f'  (lib (name "Keebio-Parts")(type "KiCad")(uri "{lib}/Keebio-Parts.pretty")(options "")(descr ""))\n'
    (out / "fp-lib-table").write_text("(fp_lib_table\n  (version 7)\n" + rows + ")\n")


if __name__ == "__main__":
    keygen_lib()
    for side in ("left", "right"):
        sh = build(side)
        nets = sh.nets
        print(f"{side}: {sum(1 for i in sh.items if i[0]=='symbol')} symbols, {len(nets)} nets")
