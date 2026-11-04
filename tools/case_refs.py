#!/usr/bin/env python3
"""Write the case-relevant positions from pcb/keygen.kicad_pcb into the note
notes/14 - case & plate requirements.md (between the case-refs markers), so the case and plate
design always uses the current PCB. Positions are mm from the top-left corner of each half's
bounding box, looking at the top (switch side) of the board."""
import re
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / "notes/14 - case & plate requirements.md"   # tools/sync_notes.sh copies it to the vault
WHAT = {"U": "Controller (underside), USB-C at the top edge", "SW90": "Power slide switch (underside), knob through the top wall", "SW91": "Reset button (underside) -> floor pinhole",
        "BT": "Battery JST-PH connector (underside)", "ENC": "Rotary encoder shaft (top)", "H": "M2 mounting hole",
        "J[12]01": "OLED wiring pin 1 (top); the module is above it, in the top frame",
        "J[12]02": "Encoder lead header pin 1 (underside)"}

def describe(ref):
    for k, v in WHAT.items():
        if k.startswith("SW") and ref.startswith("SW") and ref[-2:] == k[-2:]: return v
        if k.startswith("J") and re.fullmatch(k, ref): return v
        if not k.startswith(("SW", "J")) and re.match(rf"{k}\d+$", ref): return v
    return None

def table():
    b = pcbnew.LoadBoard(str(ROOT / "pcb/keygen.kicad_pcb"))
    mm = pcbnew.ToMM
    polys = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(polys, False)
    out = []
    for i in range(polys.OutlineCount()):
        o = polys.Outline(i)
        xs = [mm(o.CPoint(j).x) for j in range(o.PointCount())]; ys = [mm(o.CPoint(j).y) for j in range(o.PointCount())]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        side = "Left" if (x0 + x1) / 2 < 200 else "Right"
        out.append(f"**{side} half**: board outline {x1 - x0:.1f} × {y1 - y0:.1f} mm (bounding box)\n")
        out.append("| Ref | What | x | y |\n|---|---|---|---|")
        rows = []
        for fp in b.GetFootprints():
            r = fp.GetReference(); d = describe(r)
            p = fp.GetPosition(); x, y = mm(p.x), mm(p.y)
            if d and x0 <= x <= x1 and y0 <= y <= y1:
                rows.append((r, d, x - x0, y - y0))
        for r, d, x, y in sorted(rows):
            out.append(f"| {r} | {d} | {x:.1f} | {y:.1f} |")
        out.append("")
    return "\n".join(out)

if __name__ == "__main__":
    t = NOTE.read_text()
    new = "<!-- case-refs:start -->\n" + table() + "\n<!-- case-refs:end -->"
    t = re.sub(r"<!-- case-refs:start -->.*?<!-- case-refs:end -->", lambda m: new, t, flags=re.S)
    NOTE.write_text(t)
    print(f"updated {NOTE.name}")
