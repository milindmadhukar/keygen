#!/usr/bin/env python3
"""Render the Blender studio pictures into assets/, with Cycles, from blender/keygen.blend:

assets/render-studio-hero.jpg       the studio camera: both halves, LEDs lit
assets/render-studio-top.jpg        straight down on both halves
assets/render-studio-thumbs.jpg     close up on the knob, the OLED and the thumb cluster
assets/render-studio-side.jpg       low along the back edge: the case's profile and its ports
assets/render-studio-bottom.jpg     the keyboard turned over: the case's underside
assets/render-studio-leds.gif       a rainbow wave running across the per-key LEDs
assets/render-studio-turntable.gif  one turn round the keyboard

Run tools/gen_blend.py first (regen.py does); the views are set up in tools/blend_render.py. The stills are
1920 x 1080; a full run takes about 20 minutes on the CPU.

    python3 tools/render_blender.py              write the assets
    python3 tools/render_blender.py --preview    small and noisy, into /tmp/keygen-preview/ instead

Uses $KEYGEN_BLENDER as the Blender binary if set, else `blender`.
"""
import os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "blender/keygen.blend"
STILLS = ("hero", "top", "thumbs", "side", "bottom")
GIFS = {"leds": (12, 256), "turntable": (12, 128)}     # frames per second, colours (the turntable changes
                                                       # every pixel each frame, so it gets fewer)


def main():
    preview = "--preview" in sys.argv[1:]
    out = Path("/tmp/keygen-preview") if preview else ROOT / "assets"
    out.mkdir(parents=True, exist_ok=True)
    blender = os.environ.get("KEYGEN_BLENDER", "blender")
    with tempfile.TemporaryDirectory() as tmp:
        p = subprocess.run([blender, "-b", str(STUDIO), "--python-exit-code", "1", "--python",
                            str(ROOT / "tools/blend_render.py"), "--", tmp, *(["--preview"] if preview else [])],
                           capture_output=True, text=True)
        print("\n".join(l for l in p.stdout.splitlines() if l.startswith("keygen:")))
        if p.returncode:
            sys.exit(f"blender failed ({p.returncode}):\n{(p.stdout + p.stderr)[-3000:]}")
        for name in STILLS:
            dst = out / f"render-studio-{name}.jpg"
            subprocess.run(["magick", f"{tmp}/{name}.png", "-strip", "-quality", "90", str(dst)], check=True)
            print(f"wrote {dst}")
        for name, (fps, colours) in GIFS.items():
            dst = out / f"render-studio-{name}.gif"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{tmp}/{name}_%04d.png",
                            "-vf", f"split[a][b];[a]palettegen=max_colors={colours}:stats_mode=diff[p];"
                                   "[b][p]paletteuse=dither=sierra2_4a", "-loop", "0", str(dst)], check=True)
            print(f"wrote {dst}: {dst.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
