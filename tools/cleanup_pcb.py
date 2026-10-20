#!/usr/bin/env python3
"""Final tidy-up after routing:
  1. delete dangling vias and dead-end track stubs (left by earlier autorouter runs) and any GND
     via that DRC finds too close to something, repeating until DRC reports none;
  2. set every via to the project sizes;
  3. re-pour ground (islands removed) with stitching vias, and save.
Removing items through the Python API corrupts the board in KiCad 10, so deletions are done
on the file text."""
import json, math, subprocess, sys, tempfile
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import route_pcb
from sexp import parse, dump, first

PCB = route_pcb.PCB


def drc():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "drc.json"
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--units", "mm", "-o", str(out), str(PCB)],
                       capture_output=True)
        return json.loads(out.read_text())


def junk(data):
    vias, tracks = [], []
    for v in data["violations"]:
        for i in v["items"]:
            p = (i["pos"]["x"], i["pos"]["y"])
            d = i["description"]
            if v["type"] == "via_dangling" and d.startswith("Via"):
                vias.append(p)
            elif v["type"] == "track_dangling" and d.startswith("Track"):
                tracks.append(p)
            elif v["type"] in ("clearance", "hole_clearance", "hole_to_hole") and d.startswith("Via [") and "/GND]" in d:
                vias.append(p)
    return vias, tracks


def on_segment(p, a, b, tol=0.02):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2))
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy) < tol


def prune(vias, tracks):
    tree = parse(PCB.read_text())
    keep, rv, rt = [], 0, 0
    for n in tree:
        if isinstance(n, list) and n and n[0] == "via":
            at = first(n, "at")
            if any(abs(float(at[1]) - x) < 0.01 and abs(float(at[2]) - y) < 0.01 for x, y in vias):
                rv += 1
                continue
        if isinstance(n, list) and n and n[0] == "segment":
            s, e = first(n, "start"), first(n, "end")
            a, c = (float(s[1]), float(s[2])), (float(e[1]), float(e[2]))
            if any(on_segment(p, a, c) for p in tracks):
                rt += 1
                continue
        keep.append(n)
    tree[:] = keep
    PCB.write_text(dump(tree) + "\n")
    return rv, rt


def main():
    total_v = total_t = 0
    for _ in range(6):
        vias, tracks = junk(drc())
        if not vias and not tracks:
            break
        rv, rt = prune(vias, tracks)
        total_v += rv
        total_t += rt
        if rv == rt == 0:
            break
    b = route_pcb.load_without_zones()
    route_pcb.normalise(b)
    route_pcb.ground_pours(b)
    pcbnew.SaveBoard(str(PCB), b)
    print(f"removed {total_v} vias and {total_t} track stubs")


if __name__ == "__main__":
    main()
