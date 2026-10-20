#!/usr/bin/env python3
"""Assembly BOMs from the schematic: what to solder where, per half.

fab/BOM-left.csv, fab/BOM-right.csv   one row per part type: references, qty, value, footprint
fab/BOM.md                            the same as readable tables + totals for 1 and 2 keyboards,
                                      with where-to-buy pulled from bom/bom.csv

References: left half 1xx, right half 2xx (printed on the PCB silkscreen except LEDs/diodes/
switches, whose labels are hidden; use KiCad's PCB view to find those).
"""
import csv, re, subprocess, tempfile
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCH = ROOT / "pcb/keygen.kicad_sch"
OUT = ROOT / "fab"

# (match on footprint/value) -> (part, row name in bom/bom.csv, solder note)
KINDS = [
    (r"SW_MX_HS_CPG151101S11_1u", "MX switch, 1u key", "Hotswap sockets", "Kailh socket on the back; switch + 1u keycap on top"),
    (r"SW_MX_HS_CPG151101S11_1\.25u", "MX switch, 1.25u key", "Hotswap sockets", "Kailh socket on the back; switch + 1.25u keycap"),
    (r"SW_MX_HS_CPG151101S11_1\.5u", "MX switch, 1.5u key (tall thumb)", "Hotswap sockets", "Kailh socket on the back; switch + 1.5u keycap, turned 90°"),
    (r"D_DO-35", "1N4148 diode", "Diodes", "through-hole, back side; band (cathode) toward the square pad"),
    (r"SK6812MINI-E", "SK6812MINI-E LED", "Per-key LEDs", "SMD, reverse-mount on the back; mind the corner mark"),
    (r"nice_nano|nRF52840", "nRF52840 Pro Micro (nice!nano v2)", "Controller", "on the back, socketed (Mill-Max/low-profile); bridge BOOST"),
    (r"MSK12C02", "MSK12C02 power slide switch", "Power switch", "SMD, back side at the top edge, lever out"),
    (r"SW_PUSH_6mm", "6 mm reset button", "Reset button", "through-hole, back side"),
    (r"JST_PH", "JST-PH 2-pin battery connector", "Battery connector", "through-hole side-entry, back side; check battery polarity first"),
    (r"EC11|ROT_Alps", "EC11 rotary encoder", "Rotary encoder", "through-hole, front side (right half only)"),
    (r"10uF", "10 µF capacitor (0805)", "LED decoupling", "SMD, next to the first LED"),
    (r"100nF", "100 nF capacitor (0805)", "LED decoupling", "SMD, next to the first LED"),
    (r"AO3401A", "AO3401A P-MOSFET (SOT-23)", "Battery switch MOSFET", "SMD, back side, between the controller and the power switch"),
    (r"^1M$", "1 MΩ resistor (0805)", "Gate resistor", "SMD, back side, below the MOSFET"),
]
SKIP = re.compile(r"^(#|H\d)")          # power flags, mounting holes (not parts)


def schematic_parts():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "bom.csv"
        subprocess.run(["kicad-cli", "sch", "export", "bom", "--fields", "Reference,Value,Footprint",
                        "--labels", "Ref,Value,Footprint", "--ref-range-delimiter", "", "-o", str(out), str(SCH)],
                       check=True, capture_output=True)
        rows = list(csv.DictReader(out.open()))
    parts = []
    for r in rows:
        for ref in r["Ref"].split(","):
            ref = ref.strip()
            if ref and not SKIP.match(ref):
                parts.append((ref, r["Value"], r["Footprint"]))
    return parts


def kind_of(value, footprint):
    for pat, name, bomrow, note in KINDS:
        if re.search(pat, footprint) or re.search(pat, value):
            return name, bomrow, note
    return value, "", ""


def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def group(parts, side):
    lo, hi = (100, 200) if side == "left" else (200, 300)
    g = OrderedDict()
    for ref, value, fp in sorted(parts, key=lambda p: natural(p[0])):
        n = natural(ref)[1]
        if not lo <= n < hi: continue
        name, bomrow, note = kind_of(value, fp)
        e = g.setdefault(name, {"refs": [], "value": value, "footprint": fp, "bomrow": bomrow, "note": note})
        e["refs"].append(ref)
    return g


def shops():
    rows = list(csv.DictReader((ROOT / "bom/bom.csv").open()))
    return {r["part"]: r for r in rows}


def compress(refs):
    """SW101,SW102,SW103 -> SW101–SW103"""
    out, run = [], []
    for r in refs:
        p, n = natural(r)
        if run and natural(run[-1]) == (p, n - 1): run.append(r)
        else:
            if run: out.append(run)
            run = [r]
    if run: out.append(run)
    return ", ".join(", ".join(r) if len(r) < 3 else f"{r[0]}–{r[-1]}" for r in out)


# Manufacturer part numbers for a fab's assembly BOM. Verify stock/alternates in the fab's
# parts search before ordering; generic parts list a common equivalent.
MPN = {
    "1N4148 diode": "1N4148 (DO-35, e.g. onsemi 1N4148)",
    "SK6812MINI-E LED": "SK6812MINI-E (OPSCO, LCSC C5149201)",
    "10 µF capacitor (0805)": "CL21A106KAYNNNE (Samsung, 10 µF 25 V X5R 0805)",
    "100 nF capacitor (0805)": "CL21B104KBCNNNC (Samsung, 100 nF 50 V X7R 0805)",
    "MSK12C02 power slide switch": "MSK12C02-HB",
    "AO3401A P-MOSFET (SOT-23)": "AO3401A (Alpha & Omega, SOT-23)",
    "1 MΩ resistor (0805)": "0805W8F1004T5E (UNI-ROYAL, 1 MΩ 1% 0805)",
    "6 mm reset button": "6x6x5 mm THT tactile switch (e.g. TS-1102S-B-B, any 6x6x5)",
    "JST-PH 2-pin battery connector": "S2B-PH-K-S(LF)(SN) (JST)",
    "EC11 rotary encoder": "EC11E (Alps EC11 with push switch, 20 mm shaft)",
    "nRF52840 Pro Micro (nice!nano v2)": "Customer supplied: nice!nano v2 nRF52840 Pro Micro",
}
DESCR = {
    "MX switch": "Kailh MX hotswap socket (CPG151101S11)",
}
def fab_instructions(name, refs):
    side = "TOP" if name.startswith("EC11") else "BOTTOM"
    if name.startswith("MX switch"):
        return "Kailh CPG151101S11 hotswap socket, BOTTOM side. Do NOT fit switches (customer installs)."
    if name.startswith("SK6812"):
        return ("Reverse-mount LED, BOTTOM side, body through the PCB cut-out. "
                "Match the corner mark to the footprint's pin-1 mark.")
    if name.startswith("nRF52840"):
        return "DO NOT FIT: customer solders sockets + controller (BOTTOM side)."
    if name.startswith("1N4148"):
        return "THT, BOTTOM side. Polarity: band (cathode) to the square pad."
    if name.startswith("JST"):
        return "THT side-entry, BOTTOM side. Opening toward the battery pocket."
    return f"{side} side."

def export_fab_bom(parts):
    for side in ("left", "right"):
        g = group(parts, side)
        with (OUT / f"BOM-assembly-{side}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Item Number", "Designator", "Unit Quantity", "Description", "Manufacturer Part Number",
                        "Footprint", "Value", "Assembly Instructions"])
            for i, (name, e) in enumerate(g.items(), 1):
                kind = "MX switch" if name.startswith("MX switch") else name
                size = re.search(r"([\d.]+u)", name).group(1) if kind == "MX switch" else ""
                desc = f"Kailh MX hotswap socket for a {size} key" if kind == "MX switch" else name
                mpn = "CPG151101S11 (Kailh)" if kind == "MX switch" else MPN.get(name, "")
                value = ("Kailh hotswap socket" if name.startswith("MX switch") else
                         "JST-PH 2-pin" if name.startswith("JST") else e["value"])
                w.writerow([i, ",".join(e["refs"]), len(e["refs"]), desc, mpn, e["footprint"], value,
                            fab_instructions(name, e["refs"])])

def main():
    parts = schematic_parts()
    export_fab_bom(parts)
    shop = shops()
    OUT.mkdir(exist_ok=True)
    md = ["# Keygen assembly BOM", "",
          "Generated by `tools/export_bom.py` from the schematic. Left half = references 1xx, right half = 2xx.",
          "The shopping list with spares and prices is `bom/bom.csv` / `plan/bom.html`.", ""]
    totals = OrderedDict()
    for side in ("left", "right"):
        g = group(parts, side)
        with (OUT / f"BOM-{side}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Part", "Qty", "References", "Value", "Footprint", "Notes"])
            for name, e in g.items():
                w.writerow([name, len(e["refs"]), " ".join(e["refs"]), e["value"], e["footprint"], e["note"]])
        md += [f"## {side.title()} half", "", "| Part | Qty | References | Solder notes |", "|---|---|---|---|"]
        for name, e in g.items():
            md.append(f"| {name} | {len(e['refs'])} | {compress(e['refs'])} | {e['note']} |")
            t = totals.setdefault(name, {"qty": 0, "bomrow": e["bomrow"]})
            t["qty"] += len(e["refs"])
        md.append("")
    md += ["## Totals", "", "| Part | 1 keyboard | 2 keyboards | Where to buy |", "|---|---|---|---|"]
    for name, t in totals.items():
        s = shop.get(t["bomrow"], {})
        where = s.get("india", "") or s.get("import", "")
        if name.startswith("MX switch"):
            where = "Kailh sockets: you own 100 (enough for keyboard 1). Switches: still to choose"
        md.append(f"| {name} | {t['qty']} | {2 * t['qty']} | {where} |")
    sw = sum(t["qty"] for n, t in totals.items() if n.startswith("MX switch"))
    md += ["", f"**Switches and keycaps:** {sw} switches per keyboard. Keycaps per keyboard: "
           + ", ".join(f"{t['qty']} × {re.search(r'([\d.]+u)', n).group(1)}" for n, t in totals.items() if n.startswith("MX switch"))
           + ". Not in the schematic as separate parts (the switch footprint stands for socket + switch).",
           "",
           "**Also needed but not on the PCB:** LiPo battery per half (see `bom/bom.csv`), M2 screws/standoffs for "
           "the 10 mounting holes, keycaps, knob.", ""]
    (OUT / "BOM.md").write_text("\n".join(md))
    print((OUT / "BOM.md").read_text())


if __name__ == "__main__":
    main()
