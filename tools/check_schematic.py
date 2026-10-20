#!/usr/bin/env python3
"""Verify the generated schematics: KiCad ERC must be clean, and the netlist KiCad exports
must match the design tables in gen_schematic.py connection by connection."""
import json, subprocess, sys, tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sexp import find, first, parse
import gen_schematic as g

ROOT = Path(__file__).resolve().parent.parent
fails = []
def check(cond, msg):
    if not cond: fails.append(msg)

def netlist(sch):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "n.net"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(out), str(sch)],
                       check=True, capture_output=True)
        tree = parse(out.read_text())
    nets, fps = {}, {}
    for c in find(first(tree, "components"), "comp"):
        fps[first(c, "ref")[1]] = first(c, "footprint")[1] if first(c, "footprint") else ""
    for n in find(first(tree, "nets"), "net"):
        nets[first(n, "name")[1].lstrip("/")] = {(first(x, "ref")[1], first(x, "pin")[1]) for x in find(n, "node")}
    return nets, fps

def erc(sch):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "erc.json"
        subprocess.run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all", "-o", str(out), str(sch)],
                       capture_output=True)
        data = json.loads(out.read_text())
    return [(v["severity"], v["type"], v["description"], [i["description"] for i in v["items"]])
            for s in data["sheets"] for v in s["violations"]]

sch = ROOT / "pcb/keygen.kicad_sch"
for sev, typ, desc, items in erc(sch):
    check(False, f"ERC {sev} {typ}: {desc} {items[:2]}")
all_nets, all_fps = netlist(sch)
for side in ("left", "right"):
    base = g.BASE[side]
    # Rename this half's refs back to SW1/U1/... and keep only its sheet-local nets.
    def local(ref):
        import re
        m = re.match(r"(#?[A-Z]+)(\d+)$", ref)
        n = int(m[2])
        return f"{m[1]}{n - base}" if base < n < base + 100 else None
    nets = {}
    for name, nodes in all_nets.items():
        mine = {(local(r), p) for r, p in nodes if local(r)}
        if not mine: continue
        check(len(mine) == len(nodes), f"net {name} mixes left and right parts")
        nets[name.split("/", 1)[1] if name.startswith(side + "/") else name] = mine
    fps = {local(r): f for r, f in all_fps.items() if local(r)}
    by_pin = {pin: net for net, pins in nets.items() for pin in pins}
    net_of = lambda ref, pin: by_pin.get((ref, pin))

    keys = g.KEYS[side]
    enc = g.ENCODER_POS.get(side)
    cells = sorted([(r, c, lab, w) for r, c, lab, w in keys] + ([(enc[0], enc[1], "enc", None)] if enc else []))
    for n, (r, c, lab, w) in enumerate(cells, 1):
        d = f"D{n}"
        check(net_of(d, "1") == f"ROW{r}", f"{side} {d} cathode on {net_of(d,'1')}, want ROW{r}")
        mid = net_of(d, "2")
        if w is None:
            check(net_of("ENC1", "S1") == f"COL{c}", f"{side} encoder S1 not on COL{c}")
            check(net_of("ENC1", "S2") == mid, f"{side} encoder S2 not joined to {d} anode")
        else:
            sw = f"SW{n}"
            check(net_of(sw, "1") == f"COL{c}", f"{side} {sw} ({lab}) pin1 on {net_of(sw,'1')}, want COL{c}")
            check(net_of(sw, "2") == mid and mid is not None, f"{side} {sw} ({lab}) not joined to {d} anode")
            check(len(nets[mid]) == 2, f"{side} {mid} has {len(nets[mid])} nodes")
            check(fps[sw].endswith(f"_{'%g' % w}u"), f"{side} {sw} footprint {fps[sw]} not {w}u")

    pads = {**g.MCU_NETS, **(g.MCU_NETS_RIGHT if side == "right" else {})}
    for pad, net in pads.items():
        check(net_of("U1", str(pad)) == net, f"{side} U1 pad {pad} on {net_of('U1', str(pad))}, want {net}")
    for pad in set(g.MCU_PINS) - set(pads):
        check(net_of("U1", str(pad)) is None or net_of("U1", str(pad)).startswith("unconnected"),
              f"{side} U1 pad {pad} should be unused")
    for r in range(5):
        want = sum(1 for cell in cells if cell[0] == r) + 1
        check(len(nets[f"ROW{r}"]) == want, f"{side} ROW{r} has {len(nets[f'ROW{r}'])} nodes, want {want}")
    for c in range(7):
        want = sum(1 for cell in cells if cell[1] == c and cell[3] is not None) + 1 + (1 if enc and enc[1] == c else 0)
        check(len(nets[f"COL{c}"]) == want, f"{side} COL{c} has {len(nets[f'COL{c}'])} nodes, want {want}")

    nled = len(keys)
    for i in range(1, nled + 1):
        L = f"LED{i}"
        # KiCad stock SK6812MINI-E numbering (mirrored datasheet view for reverse mount)
        pins = {nm: net_of(L, num) for num, nm in (("1", "VSS"), ("2", "DIN"), ("3", "VDD"), ("4", "DOUT"))}
        check(pins["VDD"] == "VCC" and pins["VSS"] == "GND", f"{side} {L} power {pins}")
        want_in = "LED_DIN" if i == 1 else net_of(f"LED{i-1}", "4")
        check(pins["DIN"] == want_in and want_in, f"{side} {L} DIN {pins['DIN']} not fed by previous LED ({want_in})")
    check(("U1", "1") in nets["LED_DIN"], f"{side} LED_DIN not driven by U1 pad 1")

    expect = {
        "GND": {("U1", "3"), ("U1", "4"), ("U1", "14"), ("BT1", "2"), ("SW91", "2"), ("C1", "2"), ("C2", "2"), ("SW90", "1")},
        "VBAT": {("U1", "13"), ("Q1", "3")},
        "BAT_RAW": {("BT1", "1"), ("Q1", "2"), ("SW90", "3"), ("R1", "2")},
        "BAT_GATE": {("Q1", "1"), ("SW90", "2"), ("R1", "1")},
        "RST": {("U1", "15"), ("SW91", "1")},
    }
    if enc:
        expect["GND"].add(("ENC1", "C"))
        expect["ENC_A"] = {("U1", "6"), ("ENC1", "A")}
        expect["ENC_B"] = {("U1", "24"), ("ENC1", "B")}
    for net, want in expect.items():
        have = {p for p in nets.get(net, set()) if not p[0].startswith("#")}
        if net == "GND": have = {p for p in have if not p[0].startswith("LED")}
        check(have == want, f"{side} {net}: extra {sorted(have - want)} missing {sorted(want - have)}")
    check(len([p for p in nets["VCC"] if p[0].startswith("LED")]) == nled, f"{side} VCC LED count")
    for ref, fp in fps.items():
        check(ref.startswith("#") or fp, f"{side} {ref} has no footprint")
    print(f"{side}: {len(fps)} parts, {len(nets)} nets checked")

if fails:
    print(f"\n{len(fails)} problem(s):"); [print(" -", f) for f in fails]; sys.exit(1)
print("OK: ERC clean and every connection matches the design tables")
