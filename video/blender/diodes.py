#!/usr/bin/env python3
"""Write video/blender/diodes.json: each diode's pad 1 and pad 2 centres (mm, KiCad frame), from the
PCB. Its SOD-123 footprint has no 3D model, so anim.py builds the diode bodies from these."""
import json
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
board = pcbnew.LoadBoard(str(ROOT / "pcb/keygen.kicad_pcb"))
out = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("D") and ref[1:].isdigit():
        pads = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
        out[ref] = {n: [pcbnew.ToMM(pads[n].x), pcbnew.ToMM(pads[n].y)] for n in ("1", "2")}
(ROOT / "video/blender/diodes.json").write_text(json.dumps(out, indent=0))
print(f"{len(out)} diodes")
