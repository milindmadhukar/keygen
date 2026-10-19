#!/usr/bin/env python3
"""Route pcb/keygen.kicad_pcb with Freerouting, then pour ground.

Steps: net classes (power 0.4 mm, signal 0.25 mm) -> antenna keep-outs under each controller ->
Specctra DSN export -> Freerouting (headless) -> SES import -> GND pour on both layers of
each half -> save. Run tools/gen_pcb.py first; this script routes whatever placement it finds.
"""
import subprocess, sys, time
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "pcb/keygen.kicad_pcb"
DSN, SES = PCB.with_suffix(".dsn"), PCB.with_suffix(".ses")
JAR = ROOT / "tools/freerouting-2.5.0.jar"
POWER = ("GND", "VCC", "VBAT", "BAT_RAW")
mm = pcbnew.FromMM

def netclasses(b):
    ns = b.GetDesignSettings().m_NetSettings
    d = ns.GetDefaultNetclass()
    d.SetTrackWidth(mm(0.25)); d.SetClearance(mm(0.2)); d.SetViaDiameter(mm(0.6)); d.SetViaDrill(mm(0.3))
    p = pcbnew.NETCLASS("Power")
    p.SetTrackWidth(mm(0.4)); p.SetClearance(mm(0.2)); p.SetViaDiameter(mm(0.7)); p.SetViaDrill(mm(0.35))
    ns.SetNetclass("Power", p)
    ns.ClearNetclassPatternAssignments()
    for n in POWER:
        ns.SetNetclassPatternAssignment(f"*/{n}", "Power")
    ns.RecomputeEffectiveNetclasses() if hasattr(ns, "RecomputeEffectiveNetclasses") else None
    for net in b.GetNetsByName().values():
        if net.GetNetCode() > 0 and any(net.GetNetname().endswith("/" + n) for n in POWER):
            net.SetNetClass(p)

def rule_area(b, pts, name):
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True); z.SetZoneName(name)
    z.SetDoNotAllowZoneFills(True)            # no ground pour under the chip antenna
    z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    b.Add(z)

def antenna_keepouts(b):
    """The nRF52840 Pro Micro boards carry their chip antenna at the end opposite USB-C."""
    for fp in b.GetFootprints():
        if fp.GetReference() in ("U101", "U201"):
            c = fp.GetPosition(); cx, cy = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
            rule_area(b, [(cx - 10, cy + 8), (cx + 10, cy + 8), (cx + 10, cy + 19), (cx - 10, cy + 19)],
                      f"antenna-{fp.GetReference()}")

def outlines(b):
    polys = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(polys, False)
    out = []
    for i in range(polys.OutlineCount()):
        ol = polys.Outline(i)
        out.append([(ol.CPoint(j).x, ol.CPoint(j).y) for j in range(ol.PointCount())])
    return out

def ground_pours(b):
    for z in [z for z in b.Zones() if not z.GetIsRuleArea()]:
        b.Remove(z)
    for pts in outlines(b):
        xs = [p[0] for p in pts]
        side = "left" if sum(xs) / len(xs) < pcbnew.FromMM(200) else "right"
        net = b.FindNet(f"/{side}/GND")
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(b)
            z.SetLayer(layer); z.SetNet(net); z.SetZoneName(f"GND-{side}")
            z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.25))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            z.SetThermalReliefGap(mm(0.4)); z.SetThermalReliefSpokeWidth(mm(0.4))
            o = z.Outline(); o.NewOutline()
            for x, y in pts: o.Append(x, y)
            b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

def main(passes=100, import_only=False):
    b = pcbnew.LoadBoard(str(PCB))
    for t in list(b.GetTracks()): b.Remove(t)                    # route from scratch
    for z in list(b.Zones()): b.Remove(z)
    netclasses(b)
    antenna_keepouts(b)
    if import_only:                                              # reuse the last Freerouting result
        return finish(b)
    if not pcbnew.ExportSpecctraDSN(b, str(DSN)): sys.exit("DSN export failed")
    t0 = time.time()
    r = subprocess.run(["java", "-jar", str(JAR), "--gui.enabled=false", "-de", str(DSN), "-do", str(SES),
                        "-mp", str(passes)], capture_output=True, text=True)
    log = (r.stdout + r.stderr).splitlines()
    print("\n".join(l for l in log if any(k in l.lower() for k in ("pass", "unrouted", "complete", "error", "incomplete")))[-3000:])
    if not SES.exists(): sys.exit(f"Freerouting produced no session file (exit {r.returncode})")
    print(f"freerouting: {time.time() - t0:.0f} s")
    finish(b)

def finish(b):
    if not pcbnew.ImportSpecctraSES(b, str(SES)): sys.exit("SES import failed")
    ground_pours(b)
    pcbnew.SaveBoard(str(PCB), b)
    print(f"tracks: {len(b.GetTracks())}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--import-only" in args: main(import_only=True)
    else: main(int(args[0]) if args else 100)
