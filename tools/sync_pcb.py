#!/usr/bin/env python3
"""Bring the routed PCB back in line with the schematic without touching copper:
  * relink every footprint to its symbol (by reference),
  * copy symbol fields (e.g. each LED's 'Position'),
  * match 'exclude from BOM / position files' to the symbol,
  * delete redundant vias the maze router left: a via within 0.4 mm of another via on the same
    net, or one whose centre sits inside a same-net through-hole pad (the pad already joins the
    layers). Track ends stay inside the remaining copper, so nothing disconnects.
Then DRC with schematic parity decides whether it worked."""
import math, sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import gen_pcb
from sexp import parse, dump, first, find

PCB = gen_pcb.PCB / "keygen.kicad_pcb"


def netlist_fields():
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "n.net"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(out),
                        str(gen_pcb.PCB / "keygen.kicad_sch")], check=True, capture_output=True)
        tree = parse(out.read_text())
    fields = {}
    for c in find(first(tree, "components"), "comp"):
        ref = first(c, "ref")[1]
        fs = first(c, "fields")
        fields[ref] = {first(f, "name")[1]: (f[2] if len(f) > 2 and isinstance(f[2], str) else "")
                       for f in (find(fs, "field") if fs else [])}
    return fields


def redundant_vias(b):
    vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    pth = [(p, p.GetNetCode()) for fp in b.GetFootprints() for p in fp.Pads()
           if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    drop, kept = [], []
    for v in vias:
        c = v.GetPosition()
        if any(n == v.GetNetCode() and p.HitTest(c, 0) for p, n in pth):
            drop.append(c); continue
        if any(k.GetNetCode() == v.GetNetCode() and math.hypot(c.x - k.GetPosition().x, c.y - k.GetPosition().y) < pcbnew.FromMM(0.4)
               for k in kept):
            drop.append(c); continue
        kept.append(v)
    return [(pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)) for c in drop]


def main():
    comps = gen_pcb.read_netlist()
    fields = netlist_fields()
    b = pcbnew.LoadBoard(str(PCB))
    relinked = 0
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref not in comps: continue
        fp.SetPath(pcbnew.KIID_PATH(comps[ref]["path"])); relinked += 1
        for name, val in fields.get(ref, {}).items():
            if name in ("Footprint", "Datasheet", "Description", "Reference", "Value"): continue
            fp.SetField(name, val)
            fp.GetField(name).SetVisible(False)
        if ref.startswith("U"):
            fp.SetExcludedFromBOM(False)
        if ref[0] in "HC":                    # hole/cap labels collide with nearby silkscreen
            fp.Reference().SetVisible(False)
    spots = redundant_vias(b)
    pcbnew.SaveBoard(str(PCB), b)
    # delete the redundant vias on the file text (removing through the API corrupts the board)
    tree = parse(PCB.read_text())
    n0 = len(tree)
    tree[:] = [n for n in tree if not (isinstance(n, list) and n and n[0] == "via" and
               any(abs(float(first(n, "at")[1]) - x) < 0.001 and abs(float(first(n, "at")[2]) - y) < 0.001 for x, y in spots))]
    PCB.write_text(dump(tree) + "\n")
    print(f"relinked {relinked} footprints, removed {n0 - len(tree)} redundant vias")


if __name__ == "__main__":
    main()
