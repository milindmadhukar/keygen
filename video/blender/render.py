#!/usr/bin/env python3
"""Render the video's Blender clips and encode each to video/remotion/public/clips/<clip>.mp4.

    python3 video/blender/render.py [clip ...] [--preview] [--still N] [--force]

Resumable: a clip whose .mp4 exists is skipped (--force re-renders it), and an interrupted clip
picks up from the last frame on disk. Frames live in $TMPDIR/keygen-video-frames/<clip>/ until encoded.

Uses $KEYGEN_BLENDER (else ~/.local/opt/blender-5.2.2-linux-x64/blender), on the discrete GPU.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIPS = ["hero", "explode", "back_power", "back_boost", "back_buffer", "back_thru", "back_controller",
         "back_leds", "back_diodes", "back_sockets", "back_header", "front", "close", "tent", "wave"]
BLENDER = os.environ.get("KEYGEN_BLENDER", str(Path.home() / ".local/opt/blender-5.2.2-linux-x64/blender"))
FRAMES = Path(os.environ.get("TMPDIR", "/var/tmp")) / "keygen-video-frames"
PUBLIC = ROOT / "video/remotion/public/clips"
subprocess.run([sys.executable, str(ROOT / "video/blender/diodes.py")], check=True)


def main():
    args = sys.argv[1:]
    flags = [a for a in args if a.startswith("--")]
    still = args[args.index("--still") + 1] if "--still" in args else None
    names = [a for a in args if not a.startswith("--") and a != still] or CLIPS
    PUBLIC.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, DRI_PRIME="1")
    for name in names:
        extra = ["--preview"] if "--preview" in flags else []
        if still:
            extra += ["--still", still]
        if not still and "--force" not in flags and (PUBLIC / f"{name}.mp4").exists():
            print(f"clip {name}: done, skipped", flush=True)
            continue
        if "--force" in flags:
            shutil.rmtree(FRAMES / name, ignore_errors=True)
        frames = sorted((FRAMES / name).glob("*.png"))
        if frames:                                   # the last frame may have been cut off mid-write
            frames[-1].unlink()
        log = FRAMES / f"{name}.log"                 # tail -f this to watch a clip render
        FRAMES.mkdir(parents=True, exist_ok=True)
        with open(log, "w") as fh:
            p = subprocess.run([BLENDER, "-b", str(ROOT / "blender/keygen.blend"), "--python-exit-code", "1",
                                "--python", str(ROOT / "video/blender/anim.py"), "--", name, str(FRAMES), *extra],
                               stdout=fh, stderr=subprocess.STDOUT, text=True, env=env)
        text = log.read_text()
        print("\n".join(l for l in text.splitlines() if l.startswith("keygen:")), flush=True)
        if p.returncode:
            sys.exit(f"blender failed on {name}:\n{text[-3000:]}")
        if still:
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(FRAMES / name / "%04d.png"),
                        "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(PUBLIC / f"{name}.mp4")], check=True)
        shutil.copy(FRAMES / f"{name}.json", PUBLIC / f"{name}.json")
        shutil.rmtree(FRAMES / name, ignore_errors=True)
        print(f"clip {name}: {json.loads((PUBLIC / f'{name}.json').read_text())['frames']} frames", flush=True)


main()
