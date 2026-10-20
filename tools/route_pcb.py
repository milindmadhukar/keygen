#!/usr/bin/env python3
"""Route pcb/keygen.kicad_pcb with Freerouting, then pour ground.

Steps: net classes (power 0.4 mm, signal 0.25 mm) -> antenna keep-outs under each controller ->
Specctra DSN export -> Freerouting (headless) -> SES import -> GND pour on both layers of
each half -> save. Run tools/gen_pcb.py first; this script routes whatever placement it finds.
"""
import math, subprocess, sys, time
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
            z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.2))   # reach into tight gaps
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD pads solid, TH pads thermal
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)  # no floating copper islands
            z.SetThermalReliefGap(mm(0.4)); z.SetThermalReliefSpokeWidth(mm(0.4))
            o = z.Outline(); o.NewOutline()
            for x, y in pts: o.Append(x, y)
            b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    n = stitch_fill(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    m = stitch_fragments(b)
    if m: pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    print(f"ground stitching vias: {n} on grid, {m} joining separate fill pieces")

def stitch_fill(b, pitch=6.0, margin=0.65):
    """Ground stitching: a via wherever the GND fill fully covers it on BOTH layers (with margin),
    on a coarse grid. The fill already keeps clearance from other copper, so these vias can't
    clash; they join front and back fill pieces into one ground."""
    fills = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.GetNetname().endswith("/GND"): continue
        side = z.GetNetname().split("/")[1]
        fills.setdefault(side, {})[z.GetLayer()] = (z.GetFilledPolysList(z.GetLayer()), z.GetNet())
    have = [t.GetPosition() for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    ring = [(math.cos(a) * mm(margin), math.sin(a) * mm(margin)) for a in [k * math.pi / 4 for k in range(8)]] + [(0, 0)]
    added = 0
    for side, layers in fills.items():
        if pcbnew.F_Cu not in layers or pcbnew.B_Cu not in layers: continue
        (fpoly, net), (bpoly, _) = layers[pcbnew.F_Cu], layers[pcbnew.B_Cu]
        bb = fpoly.BBox()
        y = bb.GetTop()
        while y < bb.GetBottom():
            x = bb.GetLeft()
            while x < bb.GetRight():
                if all(fpoly.Contains(pcbnew.VECTOR2I(int(x + dx), int(y + dy))) and
                       bpoly.Contains(pcbnew.VECTOR2I(int(x + dx), int(y + dy))) for dx, dy in ring) and \
                   all(math.hypot(x - h.x, y - h.y) > mm(2.0) for h in have):
                    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
                    v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net); b.Add(v)
                    have.append(v.GetPosition()); added += 1
                x += mm(pitch)
            y += mm(pitch)
    return added

def stitch_fragments(b, pitch=0.5, margin=0.6, min_gap=0.9):
    """Add a GND via only where it joins two fill pieces (front/back) that aren't connected yet.
    Pieces are joined already by through-hole GND pads and existing GND vias that touch both."""
    gz = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.GetNetname().endswith("/GND"): continue
        gz.setdefault(z.GetNetname(), {})[z.GetLayer()] = z.GetFilledPolysList(z.GetLayer())
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, c): parent[find(a)] = find(c)
    def frag(poly, x, y):
        for i in range(poly.OutlineCount()):
            if poly.Contains(pcbnew.VECTOR2I(int(x), int(y)), i): return i
        return None
    def touching(poly, x, y, r):
        out = set()
        for k in range(16):
            a = k * math.pi / 8
            f = frag(poly, x + math.cos(a) * r, y + math.sin(a) * r)
            if f is not None: out.add(f)
        return out
    added = 0
    vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    for netname, layers in gz.items():
        if pcbnew.F_Cu not in layers or pcbnew.B_Cu not in layers: continue
        F, B = layers[pcbnew.F_Cu], layers[pcbnew.B_Cu]
        parent.clear()                                    # piece keys are per net
        nodes = [("F", i) for i in range(F.OutlineCount())] + [("B", i) for i in range(B.OutlineCount())]
        for n in nodes: find(n)
        conn = []   # (x, y, radius) copper that spans both layers on this net
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() == netname and p.IsOnLayer(pcbnew.F_Cu) and p.IsOnLayer(pcbnew.B_Cu):
                    c = p.GetPosition(); conn.append((c.x, c.y, max(p.GetSize().x, p.GetSize().y) / 2 + mm(0.7)))
        for v in vias:
            if v.GetNetname() == netname:
                c = v.GetPosition(); conn.append((c.x, c.y, mm(0.45)))
        for x, y, r in conn:
            fs = [("F", i) for i in touching(F, x, y, r)] + [("B", i) for i in touching(B, x, y, r)]
            for a, c in zip(fs, fs[1:]): union(a, c)
        net = b.FindNet(netname)
        have = [v.GetPosition() for v in vias]
        ring = [(math.cos(k * math.pi / 4) * mm(margin), math.sin(k * math.pi / 4) * mm(margin)) for k in range(8)]
        bb = F.BBox(); y = bb.GetTop()
        while y < bb.GetBottom():
            x = bb.GetLeft()
            while x < bb.GetRight():
                fi, bi = frag(F, x, y), frag(B, x, y)
                if fi is not None and bi is not None and find(("F", fi)) != find(("B", bi)) and                    all(frag(F, x + dx, y + dy) == fi and frag(B, x + dx, y + dy) == bi for dx, dy in ring) and                    all(math.hypot(x - h.x, y - h.y) > mm(min_gap) for h in have):
                    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
                    v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net); b.Add(v)
                    have.append(v.GetPosition()); union(("F", fi), ("B", bi)); added += 1
                x += mm(pitch)
            y += mm(pitch)
    return added

def strip_nets(path, drop):
    """Remove nets from a Specctra DSN so Freerouting leaves them alone (their pads stay as obstacles)."""
    import re
    t = path.read_text()
    out, i, removed = [], 0, 0
    for m in re.finditer(r'\(net\s+("[^"]*"|\S+)', t):
        name = m.group(1).strip('"')
        if not drop(name) or m.start() < i: continue
        depth, j = 0, m.start()
        while True:                                   # find the matching close paren
            c = t[j]
            depth += c == "("; depth -= c == ")"
            j += 1
            if depth == 0: break
        out.append(t[i:m.start()]); i = j; removed += 1
    out.append(t[i:])
    t = "".join(out)
    # also drop the names from (class ...) member lists
    t = re.sub(r'\s"?[^\s()"]*/GND"?(?=[\s)])', "", t) if removed else t
    path.write_text(t)
    print(f"DSN: left {removed} ground nets to the pour")

def load_without_zones():
    """Removing filled zones through the Python API corrupts the board object in KiCad 10, so
    strip them from the file text and load the result instead."""
    sys.path.insert(0, str(Path(__file__).parent))
    from sexp import parse, dump
    tree = parse(PCB.read_text())
    tree[:] = [n for n in tree if not (isinstance(n, list) and n and n[0] == "zone")]
    tmp = PCB.with_name("keygen-nozones.kicad_pcb")
    tmp.write_text(dump(tree) + "\n")
    pro = tmp.with_suffix(".kicad_pro")                 # design rules live in the project file
    pro.write_text(PCB.with_suffix(".kicad_pro").read_text())
    b = pcbnew.LoadBoard(str(tmp))
    tmp.unlink(); pro.unlink()
    return b

def main(passes=100, import_only=False, cont=False):
    b = load_without_zones()
    if not cont:
        for t in list(b.GetTracks()): b.Remove(t)                # route from scratch
    else:
        for t in b.GetTracks(): t.SetLocked(True)                # Freerouting must keep these

    netclasses(b)
    antenna_keepouts(b)
    if import_only:                                              # reuse the last Freerouting result
        return finish(b)
    if not pcbnew.ExportSpecctraDSN(b, str(DSN)): sys.exit("DSN export failed")
    strip_nets(DSN, lambda n: n.endswith("/GND"))           # ground comes from the pour, not traces
    t0 = time.time()
    r = subprocess.run(["java", "-jar", str(JAR), "--gui.enabled=false", "-de", str(DSN), "-do", str(SES),
                        "-mp", str(passes)], capture_output=True, text=True)
    log = (r.stdout + r.stderr).splitlines()
    print("\n".join(l for l in log if any(k in l.lower() for k in ("pass", "unrouted", "complete", "error", "incomplete")))[-3000:])
    if not SES.exists(): sys.exit(f"Freerouting produced no session file (exit {r.returncode})")
    print(f"freerouting: {time.time() - t0:.0f} s")
    finish(b)

def normalise(b):
    """KiCad's SES import picks its own via drill; use our sizes (0.6/0.3, power 0.7/0.35)."""
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            power = any(t.GetNetname().endswith("/" + n) for n in POWER)
            t.SetWidth(mm(0.7 if power else 0.6)); t.SetDrill(mm(0.35 if power else 0.3))

def finish(b):
    if not pcbnew.ImportSpecctraSES(b, str(SES)): sys.exit("SES import failed")
    for t in b.GetTracks(): t.SetLocked(False)
    normalise(b)
    ground_pours(b)
    pcbnew.SaveBoard(str(PCB), b)
    print(f"tracks: {len(b.GetTracks())}")

if __name__ == "__main__":
    args = sys.argv[1:]
    passes = int(next((a for a in args if a.isdigit()), 100))
    if "--import-only" in args: main(import_only=True)
    else: main(passes, cont="--continue" in args)
