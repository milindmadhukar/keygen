#!/usr/bin/env bash
# Build the Keygen build-guide video: voiceover, music, Blender clips, Remotion, loudness.
#
#   video/build.sh            everything (each step skips what is already done)
#   video/build.sh --render   only the Remotion render and the final mix
#
# Needs Piper in $TMPDIR/piper-venv with its voice in $TMPDIR/piper-voices (see video/tts/make_vo.py),
# Blender 5.2 (video/blender/render.py), node, ffmpeg. Writes video/out/keygen-build-guide.mp4.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
cd "$ROOT"

if [[ "${1:-}" != "--render" ]]; then
  "$TMPDIR/piper-venv/bin/python" video/tts/make_vo.py
  secs=$(python3 -c "import json;d=json.load(open('video/remotion/src/timings.json'));print(d['frames']/d['fps'])")
  python3 video/music/pad.py "$secs"
  python3 video/blender/render.py
fi

cd video/remotion
[[ -d node_modules ]] || npm ci --no-fund --no-audit
python3 prepare.py
mkdir -p out ../out
./node_modules/.bin/remotion render src/index.ts BuildGuide out/raw.mp4 --concurrency=4 --log=error
ffmpeg -v error -y -i out/raw.mp4 -c:v copy -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 192k \
  -movflags +faststart ../out/keygen-build-guide.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact ../out/keygen-build-guide.mp4
