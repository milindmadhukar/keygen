#!/usr/bin/env python3
"""Connect ground pads that the GND pour couldn't reach.

For every GND pad KiCad's DRC reports as unconnected, try spots around the pad until one is
clear of every other copper item, hole and board edge, then add a short track from the pad
and a via there, so the pad reaches the other layer's pour. Refill, re-check, repeat.
"""
import json, math, re, subprocess, sys, tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
mm, ToMM = pcbnew.FromMM, pcbnew.ToMM
VIA_D, VIA_DRILL, TRACK_W, CLEAR = 0.6, 0.3, 0.3, 0.22

def unconnected_gnd_pads():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "drc.json"
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "-o", str(out), str(PCB)], capture_output=True)
        data = json.loads(out.read_text())
    pads = set()
    for x in data["unconnected_items"]:
        for it in x["items"]:
            m = re.match(r"Pad (\S+) \[(/\w+/GND)\] of (\S+)", it["description"])
            if m: pads.add((m.group(3), m.group(1)))
    return pads

def blocked(b, pos, radius, layer, ignore, both=False):
    """True if a circle of `radius` at pos would come within CLEAR of anything except `ignore`
    and other copper on the same (ground) net."""
    acc = mm(radius + CLEAR)
    net = ignore.GetNetCode()
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p is ignore: continue
            if p.GetNetCode() == net and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH: continue
            on = p.IsOnLayer(layer) or (both and (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)))
            if (on or p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH)) and p.HitTest(pos, acc):
                return True
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.Edge_Cuts and g.HitTest(pos, acc): return True
    for t in b.GetTracks():
        if t.GetNetCode() == net: continue
        if (both or isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() == layer) and t.HitTest(pos, acc): return True
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.HitTest(pos, mm(radius + 0.5)): return True
    return False

def segment_clear(b, a, c, layer, ignore):
    n = max(2, int(math.dist((a.x, a.y), (c.x, c.y)) / mm(0.2)))
    for i in range(1, n + 1):
        q = pcbnew.VECTOR2I(int(a.x + (c.x - a.x) * i / n), int(a.y + (c.y - a.y) * i / n))
        if ignore.HitTest(q, 0): continue                  # still inside the pad itself
        if blocked(b, q, TRACK_W / 2, layer, ignore): return False
    return True

def stitch(b, ref, padnum):
    fp = b.FindFootprintByReference(ref)
    pad = next(p for p in fp.Pads() if p.GetNumber() == padnum)
    layer = pcbnew.B_Cu if pad.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
    c = pad.GetPosition()
    for r in (1.3, 1.6, 2.0, 2.5, 3.0, 3.6):
        for k in range(24):
            a = 2 * math.pi * k / 24
            v = pcbnew.VECTOR2I(int(c.x + mm(r) * math.cos(a)), int(c.y + mm(r) * math.sin(a)))
            if blocked(b, v, VIA_D / 2, layer, pad, both=True): continue   # a via spans both layers
            if not segment_clear(b, c, v, layer, pad): continue
            tr = pcbnew.PCB_TRACK(b); tr.SetStart(c); tr.SetEnd(v); tr.SetWidth(mm(TRACK_W)); tr.SetLayer(layer); tr.SetNet(pad.GetNet())
            via = pcbnew.PCB_VIA(b); via.SetPosition(v); via.SetWidth(mm(VIA_D)); via.SetDrill(mm(VIA_DRILL)); via.SetNet(pad.GetNet())
            b.Add(tr); b.Add(via)
            return True
    return False

def main(rounds=4):
    for rnd in range(rounds):
        todo = unconnected_gnd_pads()
        print(f"round {rnd + 1}: {len(todo)} unconnected GND pads")
        if not todo: break
        b = pcbnew.LoadBoard(str(PCB))
        done = sum(stitch(b, ref, num) for ref, num in sorted(todo))
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(str(PCB), b)
        print(f"  stitched {done}, no room for {len(todo) - done}")
        if done == 0: break

if __name__ == "__main__":
    main(rounds=int(sys.argv[1]) if len(sys.argv) > 1 else 1)   # later rounds just stack vias in cut-off islands
