#!/usr/bin/env python3
"""Render bom/bom.csv into plan/bom.html and the vault's BOM note."""
import csv, html, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / "bom" / "bom.csv", newline="")))
md_link = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

def to_html(s):
    out, last = [], 0
    for m in md_link.finditer(s):
        out.append(html.escape(s[last:m.start()]))
        out.append(f'<a href="{html.escape(m[2])}" target="_blank" rel="noopener">{html.escape(m[1])}</a>')
        last = m.end()
    out.append(html.escape(s[last:]))
    return "".join(out)

sections = []
for r in rows:
    if not sections or sections[-1][0] != r["section"]:
        sections.append((r["section"], []))
    sections[-1][1].append(r)

# ---- HTML -------------------------------------------------------------------
head = (ROOT / "plan" / "index.html").read_text()
style = head[head.index("<style>"):head.index("</style>") + len("</style>")]
fonts = "\n".join(l for l in head.splitlines() if "fonts.g" in l)
body = []
for name, items in sections:
    body.append(f"<h2>{html.escape(name)}</h2>\n<div class=\"tablewrap\"><table>\n<thead><tr><th>Part</th><th>Spec</th><th>Per keyboard</th><th>Buy</th><th>India</th><th>Import</th><th>Price</th><th>Status</th></tr></thead><tbody>")
    for r in items:
        st = r["status"]
        pill = "ok" if st == "decided" else "flag"
        note = f'<br><span class="muted">{to_html(r["notes"])}</span>' if r["notes"] else ""
        body.append(f'<tr><td>{to_html(r["part"])}</td><td>{to_html(r["spec"])}{note}</td><td class="num">{to_html(r["per_kb"])}</td><td class="num">{to_html(r["buy"])}</td><td>{to_html(r["india"])}</td><td>{to_html(r["import"])}</td><td class="num">{to_html(r["price"])}</td><td><span class="pill {pill}">{html.escape(st)}</span></td></tr>')
    body.append("</tbody></table></div>")
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Keygen BOM</title>
{fonts}
{style}
</head>
<body>
<div class="wrap">
  <p class="eyebrow">Keygen · bill of materials · generated from bom/bom.csv</p>
  <h1>Bill of materials</h1>
  <p class="lede prose">Everything needed for the keyboard, with spares, and where to get it in India or from abroad. Prices are what the listings showed on 20–22 Oct 2026, or rough guides where marked with ~. <a href="index.html">Back to the build plan</a>.</p>
  <div class="note prose"><strong>Buying strategy:</strong> one AliExpress order, shipped to Australia and brought to India by hand, for the SK6812MINI-E LEDs (not stocked in India), the controllers, the batteries, the knobs, the switch pads, the gaskets and the 1.25u and 1.5u keycaps; StacksKB for switches and diodes, Meckeys for the 1u keycaps, Robu.in for the encoders and small parts, Amazon.in for the EVA foam, and Lion Circuits (Bengaluru) for the boards. The shopping checklist (<code>bom/CHECKLIST.md</code>) has the exact listings.</div>
  {"".join(body)}
</div>
</body>
</html>
"""
(ROOT / "plan" / "bom.html").write_text(page)

# ---- Markdown (vault) -------------------------------------------------------
def md(s): return s.replace("|", "\\|")
lines = ["---", "created: 2026-10-19", "name: 13 - bill of materials", "tags:", "  - keyboards", "---",
         "# Bill of Materials", "",
         "> [!info] Generated file",
         "> Generated from `~/Code/keygen/bom/bom.csv` by `tools/render_bom.py`. Edit the CSV, not this note. The rendered page is `plan/bom.html`. Design context: [[12 - final design]].", "",
         "Quantities cover **the keyboard with spares**. Prices are what the listings showed on 2026-10-20 to 2026-10-22; `~` marks a rough guide.", "",
         "> [!tip] Buying strategy",
         "> - **AliExpress** (shipped to Australia, brought to India by hand): SK6812MINI-E LEDs (not stocked in India), controllers, batteries, knobs, switch pads, gaskets, 1.25u and 1.5u keycaps",
         "> - **StacksKB:** switches and diodes",
         "> - **Meckeys:** 1u keycaps",
         "> - **Robu.in:** encoders and small parts",
         "> - **Amazon.in:** EVA foam",
         "> - **Lion Circuits (Bengaluru):** the boards",
         ">",
         "> The exact listings are in `bom/CHECKLIST.md` in the repo.", ""]
for name, items in sections:
    lines += [f"## {name}", "", "| Part | Spec | Per kb | Buy | India | Import | Price | Status |", "|---|---|---|---|---|---|---|---|"]
    for r in items:
        spec = md(r["spec"]) + (f"<br>*{md(r['notes'])}*" if r["notes"] else "")
        lines.append(f"| {md(r['part'])} | {spec} | {md(r['per_kb'])} | {md(r['buy'])} | {md(r['india'])} | {md(r['import'])} | {md(r['price'])} | {md(r['status'])} |")
    lines.append("")
# notes/ is the source; tools/sync_notes.sh mirrors it into the vault
note = ROOT / "notes" / "13 - bill of materials.md"
note.write_text("\n".join(lines))
print(f"rendered {len(rows)} rows -> plan/bom.html and notes/{note.name}")
