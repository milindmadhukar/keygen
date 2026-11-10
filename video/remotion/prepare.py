#!/usr/bin/env python3
"""Copy the repo's pictures into public/assets and list the rendered clips in src/clips.json."""
import json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
dst = HERE / "public/assets"
dst.mkdir(parents=True, exist_ok=True)
for f in (ROOT / "assets").iterdir():
    if f.suffix in (".png", ".jpg", ".svg", ".gif") and (not (dst / f.name).exists() or
                                                        (dst / f.name).stat().st_mtime < f.stat().st_mtime):
        shutil.copy2(f, dst / f.name)
clips = {}
for j in sorted((HERE / "public/clips").glob("*.json")):
    if (j.with_suffix(".mp4")).exists():
        clips[j.stem] = json.loads(j.read_text())
(HERE / "src/clips.json").write_text(json.dumps(clips, indent=1))
print(f"assets copied; clips: {', '.join(clips) or 'none'}")
