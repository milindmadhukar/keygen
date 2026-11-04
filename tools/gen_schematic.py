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
_NS = uuid.UUID("6f0c8a52-4b1e-4d7a-9a51-0d5b2a7e3c11")      # Keygen namespace for stable IDs
_count = [0]
def U(key=None):
    """Deterministic UUIDs: symbols, sheets and the root are keyed by name so the PCB's links to
    them survive regenerating the schematic; everything else uses generation order."""
    if key is None:
        _count[0] += 1; key = f"item:{_count[0]}"
    return str(uuid.uuid5(_NS, key))
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
    2: "LED_EN",             # P0.08: LED power switch (ZMK ext-power), high = LEDs powered
    3: "GND", 4: "GND", 14: "GND",
    5: "OLED_SDA", 6: "OLED_SCL",   # P0.17, P0.20: the OLED's I2C (both full speed)
    13: "VBAT", 15: "RST",
    16: "VCC",               # switched 3.3 V (P0.13, held on in firmware): powers the OLED
    23: "ENC_A", 24: "ENC_B",       # P0.10, P0.09 (NFC pins: nfct-pins-as-gpios)
    7: "ROW0", 8: "ROW1", 9: "ROW2", 10: "ROW3", 11: "ROW4",
    12: "COL0", 22: "COL1", 21: "COL2", 20: "COL3", 19: "COL4", 18: "COL5", 17: "COL6",
}

# (row, col, legend, keycap width). Columns run outer (0) -> inner (6) on both halves.
KEYS = {
    "left": [
        (0, 0, "=", 1.25), (0, 1, "1", 1), (0, 2, "2", 1), (0, 3, "3", 1), (0, 4, "4", 1), (0, 5, "5", 1),
        (1, 0, "Tab", 1.25), (1, 1, "Q", 1), (1, 2, "W", 1), (1, 3, "E", 1), (1, 4, "R", 1), (1, 5, "T", 1),
        (2, 0, "Esc", 1.25), (2, 1, "A", 1), (2, 2, "S", 1), (2, 3, "D", 1), (2, 4, "F", 1), (2, 5, "G", 1), (2, 6, "Alt", 1),
        (3, 0, "Shift", 1.25), (3, 1, "Z", 1), (3, 2, "X", 1), (3, 3, "C", 1), (3, 4, "V", 1), (3, 5, "B", 1), (3, 6, "Ctrl", 1),
        (4, 0, "`", 1), (4, 1, "Caps", 1), (4, 2, "Left", 1), (4, 3, "Right", 1), (4, 4, "Super", 1.25), (4, 5, "Bksp", 1.25), (4, 6, "Del", 1.25),
    ],
    "right": [
        (0, 0, "-", 1.25), (0, 1, "0", 1), (0, 2, "9", 1), (0, 3, "8", 1), (0, 4, "7", 1), (0, 5, "6", 1),
        (1, 0, "\\", 1.25), (1, 1, "P", 1), (1, 2, "O", 1), (1, 3, "I", 1), (1, 4, "U", 1), (1, 5, "Y", 1),
        (2, 0, "'", 1.25), (2, 1, ";", 1), (2, 2, "L", 1), (2, 3, "K", 1), (2, 4, "J", 1), (2, 5, "H", 1), (2, 6, "Alt", 1),
        (3, 0, "Shift", 1.25), (3, 1, "/", 1), (3, 2, ".", 1), (3, 3, ",", 1), (3, 4, "M", 1), (3, 5, "N", 1), (3, 6, "Ctrl", 1),
        (4, 0, "]", 1), (4, 1, "[", 1), (4, 2, "Down", 1), (4, 3, "Up", 1), (4, 4, "Fn", 1.25), (4, 5, "Space", 1.25), (4, 6, "Enter", 1.25),
    ],
}
ENCODER_POS = {"left": (0, 6), "right": (0, 6)}   # each encoder's push switch sits in the matrix here

FP = {
    "mcu": "keygen:nice_nano_H_USBup",
    "sw": "keygen:SW_MX_HS_CPG151101S11_{}u",      # marbastlib + switch outline (see keygen_footprints)
    "diode": "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
    "led": "LED_SMD:LED_SK6812MINI-E_3.2x2.8mm_P1.5mm_ReverseMount",
    "cap": "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder",
    "enc": "keygen:EC11_Case_Mount",                 # board-only, no pads: holds the 3D models at the shaft
    "enc_header": "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Horizontal",
    "pwr": "keygen:SW_SK12D07VG5",
    "fet": "Package_TO_SOT_SMD:SOT-23",
    "res": "Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder",
    "rst": "Button_Switch_THT:SW_PUSH_6mm_H5mm",
    "bat": "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
    "hole": "MountingHole:MountingHole_2.2mm_M2",
    "oled": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",   # the OLED's own pins solder in
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

SHAPES = "${KIPRJMOD}/lib/keygen.3dshapes"
VENDOR3D = {"marbastlib": "${KIPRJMOD}/../lib/marbastlib/3dmodels"}
PCB_T = 1.6        # board thickness, mm
# The controller on the underside, z down from the PCB's underside. SOCKET_H and PIN_CARRIER_H are the
# figures that depend on the parts bought: measure them once they arrive and set them here, and the
# case's floor and USB-C port follow (tools/case_geometry.py).
SOCKET_H = 3.0     # machined female header body under the PCB
PIN_CARRIER_H = 1.9   # plastic carrier of the machined male pins, on the socket; the controller rests on it
CONTROLLER_H = SOCKET_H + PIN_CARRIER_H   # PCB underside to the controller
NANO_T = 1.6       # nRF52840 SuperMini board
USB_C = (8.94, 3.26)   # its mid-mount USB-C receptacle, width x height, centred on the board's thickness
# The power switch, a Shou Han SK12D07VG5 right-angle slide switch (LCSC C431548 drawing, p. 4), on
# the underside at the top edge. Its pins stand in one row under the middle of the body; the knob comes
# out of the front face, parallel to the board. tools/case_geometry.py sizes the case's slot from these.
SLIDE_BODY = (8.7, 4.4, 4.7)      # along the pin row, front to back, and height off the board
SLIDE_KNOB = (2.0, 4.0, 2.0)      # across, out of the front face, and thick
SLIDE_KNOB_Z = 2.55               # knob centre off the board
SLIDE_TRAVEL = 2.0
SLIDE_PIN_L = 2.6                 # pins and mounting tabs past the body's seat

def model(path, offset=(0, 0, 0), rotate=(0, 0, 0)):
    return [S("model"), path, [S("offset"), [S("xyz"), *offset]], [S("scale"), [S("xyz"), 1, 1, 1]],
            [S("rotate"), [S("xyz"), *rotate]]]

def vendor_model(node, base):
    """Re-point a footprint's model at the copy inside the repo, keeping its offset/rotation."""
    node = copy.deepcopy(node); node[1] = base + "/" + node[1].split("/")[-1]; return node

# Parts on the back flip their models with them; anything that has to stand on the FRONT
# (switch, keycap) is turned over and pushed through the board so the flip puts it back on top.
ON_FRONT = dict(rotate=(0, 180, 0))
CAP_MODEL_Z = 11.5   # keycap model origin above the PCB top; tools/gen_keycaps.py places the cap from it
KNOB_MODEL_Z = 14.5  # knob underside above the PCB top: case_geometry.KNOB_Z (check_mechanical.py checks)

def wrl_box_mesh(boxes):
    """VRML (KiCad units: 0.1 inch) for a list of (x0,y0,z0,x1,y1,z1,rgb) boxes in mm."""
    out = ["#VRML V2.0 utf8"]
    for x0, y0, z0, x1, y1, z1, rgb in boxes:
        v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
        pts = ",".join(f"{x/2.54:.4f} {y/2.54:.4f} {z/2.54:.4f}" for x, y, z in v)
        faces = "0,2,3,1,-1,4,5,7,6,-1,0,1,5,4,-1,2,6,7,3,-1,0,4,6,2,-1,1,3,7,5,-1"
        out.append(f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {rgb} }} }} "
                   f"geometry IndexedFaceSet {{ coord Coordinate {{ point [{pts}] }} coordIndex [{faces}] }} }}")
    return "\n".join(out) + "\n"

def slide_switch():
    """SK12D07VG5 footprint, origin on the middle pin (2, the common pole). The knob points to -y.
    The box model is drawn with -y at +y: KiCad turns back-side models end over end."""
    (bw, bd, bh), (kw, kl, kt) = SLIDE_BODY, SLIDE_KNOB
    k = iter(range(100))
    uid = lambda: [S("uuid"), U(f"fp:SW_SK12D07VG5:{next(k)}")]
    text = lambda size: [S("effects"), [S("font"), [S("size"), size, size], [S("thickness"), 0.15]]]
    def line(a, b, layer, w):
        return [S("fp_line"), [S("start"), *a], [S("end"), *b], [S("stroke"), [S("width"), w], [S("type"), S("solid")]],
                [S("layer"), layer], uid()]
    def rect(x0, y0, x1, y1, layer, w):
        c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return [line(a, b, layer, w) for a, b in zip(c, c[1:] + c[:1])]
    fp = [S("footprint"), "SW_SK12D07VG5", [S("version"), 20240108], [S("generator"), "keygen_gen_schematic"],
          [S("layer"), "F.Cu"],
          [S("descr"), "Shou Han SK12D07VG5 slide switch, SPDT, right angle, 4 mm knob, 2 mm travel (LCSC C431548)"],
          [S("tags"), "switch slide SPDT right angle"],
          [S("property"), "Reference", "REF**", [S("at"), 0, bd / 2 + 1.4, 0], [S("layer"), "F.SilkS"], uid(), text(1)],
          [S("property"), "Value", "SW_SK12D07VG5", [S("at"), 0, bd / 2 + 2.8, 0], [S("layer"), "F.Fab"], uid(), text(1)],
          [S("attr"), S("through_hole")]]
    fp += rect(-bw / 2, -bd / 2, bw / 2, bd / 2, "F.Fab", 0.1)
    fp += rect(-kw / 2 - SLIDE_TRAVEL / 2, -bd / 2 - kl, kw / 2 + SLIDE_TRAVEL / 2, -bd / 2, "F.Fab", 0.1)   # knob, both positions
    fp += rect(-bw / 2 - 0.25, -bd / 2 - 0.25, bw / 2 + 0.25, bd / 2 + 0.25, "F.CrtYd", 0.05)
    s0 = bd / 2 + 0.2                                                    # silkscreen behind the pads
    fp += [line((-bw / 2 - 0.1, 1.6), (-bw / 2 - 0.1, s0), "F.SilkS", 0.12),
           line((-bw / 2 - 0.1, s0), (bw / 2 + 0.1, s0), "F.SilkS", 0.12),
           line((bw / 2 + 0.1, s0), (bw / 2 + 0.1, 1.6), "F.SilkS", 0.12)]
    for n, x in (("1", -2.0), ("2", 0.0), ("3", 2.0)):                 # 0.5 x 0.3 mm pins
        fp.append([S("pad"), n, S("thru_hole"), S("rect" if n == "1" else "circle"), [S("at"), x, 0], [S("size"), 1.4, 1.4],
                   [S("drill"), 0.9], [S("layers"), "*.Cu", "*.Mask"], uid()])
    for x in (-4.15, 4.15):                                              # 0.4 x 1.2 mm mounting tabs, 8.3 apart
        fp.append([S("pad"), "", S("thru_hole"), S("oval"), [S("at"), x, 0], [S("size"), 1.2, 2.2],
                   [S("drill"), S("oval"), 0.7, 1.7], [S("layers"), "*.Cu", "*.Mask"], uid()])
    fp.append(model(f"{SHAPES}/SW_SK12D07VG5.wrl"))
    zk = SLIDE_KNOB_Z
    (PCB / "lib/keygen.3dshapes/SW_SK12D07VG5.wrl").write_text(wrl_box_mesh([
        (-bw / 2, -bd / 2, 0.0, bw / 2, bd / 2, bh, "0.10 0.10 0.10"),                         # body
        (-kw / 2, bd / 2, zk - kt / 2, kw / 2, bd / 2 + kl, zk + kt / 2, "0.12 0.12 0.12"),   # knob (front: see docstring)
    ] + [(x - 0.25, -0.15, -SLIDE_PIN_L, x + 0.25, 0.15, 0.0, "0.80 0.80 0.80") for x in (-2.0, 0.0, 2.0)]
      + [(x - 0.2, -0.6, -SLIDE_PIN_L, x + 0.2, 0.6, 0.0, "0.80 0.80 0.80") for x in (-4.15, 4.15)]))
    return fp

def keygen_footprints():
    """pcb/lib/keygen.pretty + keygen.3dshapes: project copies of the vendored footprints with
    model paths that resolve inside the repo, the 14 mm switch outline, and a simple controller
    model for KiCad's 3D view. The keycap models are tools/gen_keycaps.py's."""
    from sexp import parse as sparse
    shapes = PCB / "lib/keygen.3dshapes"; shapes.mkdir(parents=True, exist_ok=True)
    out = PCB / "lib/keygen.pretty"; out.mkdir(parents=True, exist_ok=True)
    def load(path, name):
        fp = sparse((path / f"{name}.kicad_mod").read_text()); fp[1] = name; return fp
    def save(fp, name): (out / f"{name}.kicad_mod").write_text(dump(fp) + "\n")
    marb = ROOT / "lib/marbastlib/footprints"

    # MX hotswap switches (placed on the back): socket model + switch + keycap on the front
    for size in ("1", "1.25"):
        name = f"SW_MX_HS_CPG151101S11_{size}u"
        fp = load(marb / "marbastlib-mx.pretty", name)
        sock = [vendor_model(m, VENDOR3D["marbastlib"]) for m in find(fp, "model")]
        fp[:] = [n for n in fp if not (isinstance(n, list) and n and n[0] == "model")]
        for d in find(fp, "descr"): d[1] = d[1] + " (Keygen: switch outline + switch/keycap 3D models)"
        h = 7.0
        corners = [(-h, -h), (h, -h), (h, h), (-h, h)]
        for a, b in zip(corners, corners[1:] + corners[:1]):
            fp.append([S("fp_line"), [S("start"), a[0], a[1]], [S("end"), b[0], b[1]],
                       [S("stroke"), [S("width"), 0.15], [S("type"), S("solid")]], [S("layer"), "B.SilkS"], [S("uuid"), U()]])
        fp += sock
        fp.append(model(f"{SHAPES}/SW_Cherry_MX_PCB.wrl", offset=(0, 0, -PCB_T), **ON_FRONT))
        fp.append(model(f"{SHAPES}/Keycap_{size}u.wrl", offset=(0, 0, -(PCB_T + CAP_MODEL_Z)), **ON_FRONT))
        save(fp, name)

    # controller: no public model, so a plain block hanging under the board on its header sockets.
    # KiCad turns models of back-side footprints end over end, so the footprint's USB end (-y)
    # is drawn at +y here.
    b0, b1 = CONTROLLER_H, CONTROLLER_H + NANO_T
    uw, uh = USB_C
    (shapes / "nRF52840_ProMicro.wrl").write_text(wrl_box_mesh([
        (-9.0, -16.65, b0, 9.0, 16.65, b1, "0.10 0.12 0.30"),            # board
        (-uw / 2, 10.0, (b0 + b1 - uh) / 2, uw / 2, 17.4, (b0 + b1 + uh) / 2, "0.75 0.75 0.78"),   # USB-C (+y: see note above)
        (-3.5, -9.0, b1, 3.5, -2.0, b1 + 0.9, "0.15 0.15 0.15"),         # nRF52840
    ] + [(x - 1.25, y - 1.25, 0.0, x + 1.25, y + 1.25, CONTROLLER_H, "0.12 0.12 0.12")    # header sockets and pin carriers
         for x in (-7.62, 7.62) for y in [(-13.97 + 2.54 * i) for i in range(12)]]))
    fp = load(marb / "marbastlib-xp-promicroish.pretty", "nice_nano_H_USBup")
    fp[:] = [n for n in fp if not (isinstance(n, list) and n and n[0] == "model")]
    fp[:] = [[S("attr"), S("through_hole")] if isinstance(n, list) and n and n[0] == "attr" else n for n in fp]
    # the USB end crosses the board's sloped top edge: the outline and the connector box stop at a
    # straight line 0.3 mm inside it, with "USB" in the shortened box and "topside" just under it
    for n in find(fp, "fp_rect") + find(fp, "fp_line"):
        for k in ("start", "end"):
            if first(n, "layer")[1] == "F.SilkS" and first(n, k)[2] == "-17.78": first(n, k)[2] = -16.5
    for n in find(fp, "fp_text"):
        if first(n, "layer")[1] == "F.SilkS" and n[2] in ("USB", "topside"):
            first(n, "at")[2] = {"USB": -14.75, "topside": -12.65}[n[2]]
    fp.append(model(f"{SHAPES}/nRF52840_ProMicro.wrl")); save(fp, "nice_nano_H_USBup")

    save(slide_switch(), "SW_SK12D07VG5")

    # The encoder is fixed to the top frame, over the PCB's opening. Its footprint has no pads: it
    # marks the shaft and carries the encoder and knob models, with the terminals' envelope on F.Fab.
    fp = load(marb / "marbastlib-various.pretty", "ROT_Alps_EC11E-Switch")
    fp[:] = [n for n in fp if not (isinstance(n, list) and n and n[0] in
                                   ("pad", "fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly", "fp_text"))]
    fp[:] = [n if not (isinstance(n, list) and n and n[0] == "model") else vendor_model(n, VENDOR3D["marbastlib"]) for n in fp]
    fp[1] = "EC11_Case_Mount"
    first(next(p for p in find(fp, "property") if p[1] == "Reference"), "layer")[1] = "F.Fab"
    next(p for p in find(fp, "property") if p[1] == "Value")[2] = "EC11_Case_Mount"
    first(fp, "attr")[1:] = [S("board_only"), S("exclude_from_pos_files"), S("exclude_from_bom")]
    fp.append([S("fp_rect"), [S("start"), -7.0, -8.75], [S("end"), 7.0, 9.0], [S("stroke"), [S("width"), 0.1], [S("type"), S("solid")]],
               [S("fill"), S("no")], [S("layer"), "F.Fab"]])
    fp.append(model(f"{SHAPES}/Knob_17mm.step", offset=(0, 0, KNOB_MODEL_Z)))
    save(fp, "EC11_Case_Mount")

def keygen_lib():
    lib = [S("kicad_symbol_lib"), [S("version"), 20241209], [S("generator"), "keygen_gen_schematic"],
           [S("generator_version"), "9.0"], nice_nano_symbol()]
    (PCB / "lib").mkdir(parents=True, exist_ok=True)
    (PCB / "lib/keygen.kicad_sym").write_text(dump(lib) + "\n")

LIBSYMS = {
    "keygen:nice_nano_v2": lambda: nice_nano_symbol(),
    "marbastlib-mx:MX_SW_HS_CPG151101S11": lambda: lib_symbol(MARB / "marbastlib-mx.kicad_sym", "MX_SW_HS_CPG151101S11"),
    "LED:SK6812MINI-E": lambda: flatten(STOCK / "LED.kicad_sym", "SK6812MINI-E", "SK6812"),
    "Device:D": lambda: lib_symbol(STOCK / "Device.kicad_sym", "D"),
    "Device:C": lambda: lib_symbol(STOCK / "Device.kicad_sym", "C"),
    "Device:R": lambda: lib_symbol(STOCK / "Device.kicad_sym", "R"),
    "Transistor_FET:AO3401A": lambda: flatten(STOCK / "Transistor_FET.kicad_sym", "AO3401A", "TP0610T"),
    "Transistor_FET:AO3400A": lambda: flatten(STOCK / "Transistor_FET.kicad_sym", "AO3400A", "Q_NMOS_GSD"),
    "Device:RotaryEncoder_Switch": lambda: lib_symbol(STOCK / "Device.kicad_sym", "RotaryEncoder_Switch"),
    "Device:Battery_Cell": lambda: lib_symbol(STOCK / "Device.kicad_sym", "Battery_Cell"),
    "Switch:SW_SPDT": lambda: lib_symbol(STOCK / "Switch.kicad_sym", "SW_SPDT"),
    "Switch:SW_Push": lambda: lib_symbol(STOCK / "Switch.kicad_sym", "SW_Push"),
    "power:PWR_FLAG": lambda: lib_symbol(STOCK / "power.kicad_sym", "PWR_FLAG"),
    "Mechanical:MountingHole": lambda: lib_symbol(STOCK / "Mechanical.kicad_sym", "MountingHole"),
    "Connector_Generic:Conn_01x04": lambda: lib_symbol(STOCK / "Connector_Generic.kicad_sym", "Conn_01x04"),
    "Connector_Generic:Conn_01x05": lambda: lib_symbol(STOCK / "Connector_Generic.kicad_sym", "Conn_01x05"),
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
    def __init__(self, project, title, root, sheet=None):
        """root: root schematic uuid; sheet: uuid of the sheet symbol in the root (None = root)."""
        self.project, self.root, self.sheet = project, root, sheet
        self.uuid = U(f"file:{title}")
        self.path = "/" + root + ("/" + sheet if sheet else "")
        self.items, self.used = [], []
        self.title = title
        self.nets = {}          # net -> [(ref, pin)]

    def symbol(self, lib_id, ref, value, x, y, footprint="", unconnected=(), nets=None, in_bom=True, fields=(), on_board=None):
        """Place a symbol and connect pins by net name. nets: {pin_number: net}."""
        if lib_id not in self.used: self.used.append(lib_id)
        sym = libsym(lib_id)
        pl = pins(sym)
        node = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x, y, 0], [S("unit"), 1],
                [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes" if in_bom else "no")],
                [S("on_board"), S("yes" if (in_bom if on_board is None else on_board) else "no")], [S("dnp"), S("no")], [S("uuid"), U(f"symbol:{self.path}:{ref}")],
                [S("property"), "Reference", ref, [S("at"), x, y - 6.35, 0], font()],
                [S("property"), "Value", value, [S("at"), x, y + 6.35, 0], font()],
                [S("property"), "Footprint", footprint, [S("at"), x, y, 0], hidden()],
                [S("property"), "Datasheet", "", [S("at"), x, y, 0], hidden()]]
        for k, v in fields:
            node.append([S("property"), k, v, [S("at"), x, y, 0], hidden()])
        for num, *_ in pl:
            node.append([S("pin"), num, [S("uuid"), U()]])
        node.append([S("instances"), [S("project"), self.project,
                     [S("path"), self.path, [S("reference"), ref], [S("unit"), 1]]]])
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
               [S("uuid"), self.root if not self.sheet else self.uuid], [S("paper"), "A2"],
               [S("title_block"), [S("title"), self.title], [S("date"), date], [S("rev"), rev],
                [S("company"), "github.com/milindmadhukar/keygen"],
                [S("comment"), 1, "Generated by tools/gen_schematic.py - edit the script, not this file"]],
               [S("lib_symbols")] + [libsym(i) for i in self.used]]
        doc += self.items
        if not self.sheet:
            doc.append([S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]])
        doc.append([S("embedded_fonts"), S("no")])
        path.write_text(dump(doc) + "\n")


PROJECT = "keygen"
BASE = {"left": 100, "right": 200}          # reference numbering: SW101.. left, SW201.. right

def build(side, root, sheet):
    sh = Sheet(PROJECT, f"Keygen - {side} half", root, sheet)
    base = BASE[side]
    R = lambda prefix, n: f"{prefix}{base + n}"
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
            sh.symbol("marbastlib-mx:MX_SW_HS_CPG151101S11", R("SW", n), lab, x, y,
                      FP["sw"].format(("%g" % w)), nets={"1": f"COL{c}", "2": k})
        else:
            sh.text(f"Encoder S1/S2 (see {R('ENC', 1)})", x - 10.16, y - 2.54)
            sh.nets.setdefault(k, [])
        sh.symbol("Device:D", R("D", n), "1N4148", x, y + 10.16, FP["diode"], nets={"1": f"ROW{r}", "2": k})

    # ---- LED chain -----------------------------------------------------------------
    LX0, LY0, LDX, LDY, PER = 30.48, 215.9, 38.1, 30.48, 8
    nled = len(keys)
    sh.text(f"PER-KEY LEDs  ({nled}) - powered from the battery through the LED power switch (Q2, LED_VDD)",
            LX0 - 15.24, LY0 - 20.32, 2)
    for i in range(nled):
        x, y = LX0 + (i % PER) * LDX, LY0 + (i // PER) * LDY
        din = "LED_DIN" if i == 0 else f"LED_D{i}"
        dout = f"LED_D{i+1}" if i < nled - 1 else None
        nets = {"VDD": "LED_VDD", "VSS": "GND", "DIN": din}
        if dout: nets["DOUT"] = dout
        sh.symbol("LED:SK6812MINI-E", R("LED", i + 1), "SK6812MINI-E", x, y, FP["led"], nets=nets,
                  fields=[("Position", keys[i][2])])

    # ---- controller ----------------------------------------------------------------
    MX, MY = 360.68, 60.96
    sh.text("CONTROLLER  (mounted on the PCB underside, USB-C to the top edge)", MX - 25.4, MY - 30.48, 2)
    mnets = {str(k): v for k, v in MCU_NETS.items()}
    sh.symbol("keygen:nice_nano_v2", R("U", 1), "nRF52840 Pro Micro", MX, MY, FP["mcu"], nets=mnets)
    sh.text("Encoder A/B on P0.10/P0.09 (NFC pins): set nfct-pins-as-gpios.\n"
            "P0.08: LED power switch. P0.17/P0.20: OLED SDA/SCL.\n"
            "VCC (pad 16, switched by P0.13): OLED power; firmware holds P0.13 high.",
            MX + 25.4, MY - 15.24)

    # ---- power ---------------------------------------------------------------------
    PX, PY = 360.68, 132.08
    sh.text("POWER", PX - 25.4, PY - 17.78, 2)
    sh.symbol("Device:Battery_Cell", R("BT", 1), "LiPo 3.7V 3000mAh", PX - 20.32, PY, FP["bat"],
              nets={"1": "BAT_RAW", "2": "GND"})
    # pin 3 stays unconnected: the switch makes before it breaks, so mid-slide it would join 1 and 3
    sh.symbol("Switch:SW_SPDT", R("SW", 90), "SK12D07VG5 power", PX, PY, FP["pwr"],
              nets={"1": "GND", "2": "BAT_GATE"})
    sh.symbol("Switch:SW_Push", R("SW", 91), "Reset", PX + 25.4, PY, FP["rst"], nets={"1": "RST", "2": "GND"})
    sh.symbol("Device:C", R("C", 1), "10uF", PX - 20.32, PY + 22.86, FP["cap"], nets={"1": "LED_VDD", "2": "GND"})
    sh.symbol("Device:C", R("C", 2), "100nF", PX - 7.62, PY + 22.86, FP["cap"], nets={"1": "LED_VDD", "2": "GND"})
    for i, net in enumerate(("GND", "VBAT", "LED_VDD")):
        sh.symbol("power:PWR_FLAG", f"#FLG{base + i + 1}", "PWR_FLAG", PX + 12.7 + i * 12.7, PY + 22.86, nets={"1": net}, in_bom=False)
    sh.text("C1/C2 sit at the LED power switch's output.", PX - 25.4, PY + 33.02)

    # ---- battery load switch ---------------------------------------------------------
    # The slide switch only drives the gate of a P-MOSFET that carries the battery current. Source on
    # the battery, drain on B+: the body diode (drain -> source) blocks the battery when the switch is off.
    QX, QY = 360.68, 185.42
    sh.text("BATTERY SWITCH (P-MOSFET; the slide switch only drives the gate)", QX - 25.4, QY - 15.24, 2)
    sh.symbol("Transistor_FET:AO3401A", R("Q", 1), "AO3401A", QX, QY, FP["fet"],
              nets={"1": "BAT_GATE", "2": "BAT_RAW", "3": "VBAT"})
    sh.symbol("Device:R", R("R", 1), "1M", QX + 15.24, QY, FP["res"], nets={"1": "BAT_GATE", "2": "BAT_RAW"})
    sh.text("Switch 2-1: gate to GND, on. Switch 2-3 (pin 3 unconnected): R1 holds the gate at\n"
            "the source, off. Leave the switch on while charging:\n"
            "off, charge current crosses the body diode (~0.07 W at 100 mA); full charge is not assured.", QX - 25.4, QY + 12.7)

    # ---- LED power switch ------------------------------------------------------------
    # The LEDs run from the battery (B+, after Q1), inside the SK6812MINI-E's 3.7-5.5 V for most of
    # the charge, through a high-side P-MOSFET. P0.08 can't hold Q2's gate at the source (up to
    # 4.2 V), so it drives an N-MOSFET that pulls the gate down. R2 holds Q2 off, R3 holds Q3 off
    # while the controller boots or sleeps.
    LX, LY = 459.74, 132.08
    sh.text("LED POWER SWITCH (P0.08 high = LEDs on)", LX - 25.4, LY - 15.24, 2)
    sh.symbol("Transistor_FET:AO3401A", R("Q", 2), "AO3401A", LX, LY, FP["fet"],
              nets={"1": "LED_GATE", "2": "VBAT", "3": "LED_VDD"})
    sh.symbol("Device:R", R("R", 2), "100k", LX + 20.32, LY, FP["res"], nets={"1": "LED_GATE", "2": "VBAT"})
    sh.symbol("Transistor_FET:AO3400A", R("Q", 3), "AO3400A", LX, LY + 25.4, FP["fet"],
              nets={"1": "LED_EN", "2": "GND", "3": "LED_GATE"})
    sh.symbol("Device:R", R("R", 3), "100k", LX + 20.32, LY + 25.4, FP["res"], nets={"1": "LED_EN", "2": "GND"})

    # ---- encoder -------------------------------------------------------------------
    if enc:
        EX, EY = 360.68, 228.6
        sh.text("CASE-MOUNTED ROTARY ENCODER (EC11) - push switch in the matrix at "
                f"ROW{enc[0]}/COL{enc[1]}", EX - 25.4, EY - 15.24, 2)
        enc_nets = {"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": f"COL{enc[1]}", "S2": f"K{enc[0]}{enc[1]}"}
        sh.symbol("Device:RotaryEncoder_Switch", R("ENC", 1), "EC11", EX, EY, FP["enc"],
                  nets=enc_nets, on_board=False)
        sh.symbol("Connector_Generic:Conn_01x05", R("J", 2), "Encoder lead, 1x5 right angle",
                  EX + 50.8, EY, FP["enc_header"],
                  nets={"1": "ENC_A", "2": "GND", "3": "ENC_B", "4": f"COL{enc[1]}", "5": f"K{enc[0]}{enc[1]}"})
        sh.text("Lead pin order: A / C(GND) / B / S1(COL6) / S2(diode input).",
                EX + 25.4, EY + 20.32)

    # ---- OLED ----------------------------------------------------------------------
    # A generic 0.96" 128x64 SSD1306 module (I2C, pull-ups and regulator on the module), held in the
    # top frame and plugged into a right-angle header in a 1x4 footprint. Pin order as printed on the usual modules.
    OX, OY = 459.74, 228.6
    sh.text("OLED (0.96 in. 128x64 SSD1306, I2C address 0x3C) - check the module's pin order: GND VCC SCL SDA",
            OX - 25.4, OY - 15.24, 2)
    sh.symbol("Connector_Generic:Conn_01x04", R("J", 1), "OLED 0.96in I2C", OX, OY, FP["oled"],
              nets={"1": "GND", "2": "VCC", "3": "OLED_SCL", "4": "OLED_SDA"})

    # ---- mounting holes (placed on the PCB by gen_pcb.py) ----------------------------
    HX, HY = 360.68, 271.78
    sh.text("MOUNTING HOLES (M2)", HX - 25.4, HY - 12.7, 2)
    for i in range(1, 6):
        sh.symbol("Mechanical:MountingHole", R("H", i), "M2", HX - 20.32 + (i - 1) * 10.16, HY, FP["hole"],
                  in_bom=False, on_board=True)
    sh.write(PCB / f"{side}.kicad_sch")
    return sh


def write_root(root, sheets):
    """Top-level sheet holding the left and right halves as hierarchical sheets."""
    items = []
    for page, (side, sid) in enumerate(sheets.items(), start=2):
        x = 38.1 + (page - 2) * 76.2
        items.append([S("sheet"), [S("at"), x, 50.8], [S("size"), 50.8, 30.48],
                      [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")], [S("dnp"), S("no")],
                      [S("stroke"), [S("width"), 0.1524], [S("type"), S("solid")]], [S("fill"), [S("color"), 0, 0, 0, 0.0]],
                      [S("uuid"), sid],
                      [S("property"), "Sheetname", f"{side}", [S("at"), x, 50.038, 0],
                       [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left"), S("bottom")]]],
                      [S("property"), "Sheetfile", f"{side}.kicad_sch", [S("at"), x, 81.8896, 0],
                       [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left"), S("top")]]],
                      [S("instances"), [S("project"), PROJECT, [S("path"), "/" + root, [S("page"), str(page)]]]]])
    note = [S("text"), "Keygen: one PCB carrying both halves joined by snap-off tabs.\n"
            "Left half = references 1xx, right half = 2xx. Each half has its own nets (separate GND, VCC).",
            [S("exclude_from_sim"), S("no")], [S("at"), 38.1, 30.48, 0],
            [S("effects"), [S("font"), [S("size"), 2, 2]], [S("justify"), S("left"), S("top")]], [S("uuid"), U()]]
    doc = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"], [S("generator_version"), "9.0"],
           [S("uuid"), root], [S("paper"), "A4"],
           [S("title_block"), [S("title"), "Keygen"], [S("date"), "2026-10-20"], [S("rev"), "0.1"],
            [S("company"), "github.com/milindmadhukar/keygen"],
            [S("comment"), 1, "Generated by tools/gen_schematic.py - edit the script, not this file"]],
           [S("lib_symbols")], note] + items + [
           [S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]], [S("embedded_fonts"), S("no")]]
    (PCB / f"{PROJECT}.kicad_sch").write_text(dump(doc) + "\n")


def write_project(out, proj):
    if (out / f"{proj}.kicad_pro").exists():
        # keep the existing project: it holds the board's design rules and net classes
        pro = json.loads((out / f"{proj}.kicad_pro").read_text())
    else:
        pro = json.loads(Path("/usr/share/kicad/template/kicad.kicad_pro").read_text())
    pro.setdefault("meta", {})["filename"] = f"{proj}.kicad_pro"
    (out / f"{proj}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")
    lib = "${KIPRJMOD}/../lib"
    (out / "sym-lib-table").write_text(
        "(sym_lib_table\n  (version 7)\n"
        '  (lib (name "keygen")(type "KiCad")(uri "${KIPRJMOD}/lib/keygen.kicad_sym")(options "")(descr "Keygen project symbols"))\n'
        f'  (lib (name "marbastlib-mx")(type "KiCad")(uri "{lib}/marbastlib/symbols/marbastlib-mx.kicad_sym")(options "")(descr ""))\n'
        ")\n")
    fps = ["marbastlib-mx", "marbastlib-various", "marbastlib-xp-promicroish"]
    rows = "".join(f'  (lib (name "{f}")(type "KiCad")(uri "{lib}/marbastlib/footprints/{f}.pretty")(options "")(descr ""))\n' for f in fps)
    rows += '  (lib (name "keygen")(type "KiCad")(uri "${KIPRJMOD}/lib/keygen.pretty")(options "")(descr "Keygen project footprints"))\n'
    rows += f'  (lib (name "Keebio-Parts")(type "KiCad")(uri "{lib}/Keebio-Parts.pretty")(options "")(descr ""))\n'
    (out / "fp-lib-table").write_text("(fp_lib_table\n  (version 7)\n" + rows + ")\n")


if __name__ == "__main__":
    keygen_lib()
    keygen_footprints()
    root = U("root:keygen")
    sheets = {"left": U("sheet:left"), "right": U("sheet:right")}
    for side, sid in sheets.items():
        sh = build(side, root, sid)
        print(f"{side}: {sum(1 for i in sh.items if i[0]=='symbol')} symbols, {len(sh.nets)} nets")
    write_root(root, sheets)
    write_project(PCB, PROJECT)
