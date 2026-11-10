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
    """UUIDs of the dangling vias and track stubs DRC reports, and of GND vias too close to something.
    By UUID, not position: a stub's dangling end can lie on a junction, and matching by position
    would take the live tracks at that junction with it."""
    ids = set()
    for v in data["violations"]:
        for i in v["items"]:
            d = i["description"]
            if (v["type"] == "via_dangling" and d.startswith("Via")) or (v["type"] == "track_dangling" and d.startswith("Track")):
                ids.add(i["uuid"])
            elif v["type"] in ("clearance", "hole_clearance", "hole_to_hole") and d.startswith("Via [") and "/GND]" in d:
                ids.add(i["uuid"])
    return ids


def prune(ids):
    tree = parse(PCB.read_text())
    keep, rv, rt = [], 0, 0
    for n in tree:
        if isinstance(n, list) and n and n[0] in ("via", "segment", "arc") and first(n, "uuid")[1] in ids:
            if n[0] == "via": rv += 1
            else: rt += 1
            continue
        keep.append(n)
    tree[:] = keep
    PCB.write_text(dump(tree) + "\n")
    return rv, rt


def main():
    total_v = total_t = 0
    for _ in range(6):
        ids = junk(drc())
        if not ids:
            break
        rv, rt = prune(ids)
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
