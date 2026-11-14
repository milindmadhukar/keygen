#!/usr/bin/env python3
"""Render the Blender studio pictures into assets/, with Cycles, from blender/keygen.blend:

assets/render-studio-hero.jpg       the studio camera: both halves, LEDs lit
assets/render-studio-top.jpg        straight down on both halves
assets/render-studio-thumbs.jpg     close up on the knob, the OLED and the thumb cluster
assets/render-studio-oled.jpg       close up on the left OLED's status screen and the knob
assets/render-studio-side.jpg       low along the back edge: the case's profile and its ports
assets/render-studio-bottom.jpg     the keyboard turned over: the case's underside
assets/render-studio-film.mp4       the hero film: the OLEDs boot, the LEDs sweep on, the camera glides
                                    along the keys and rises to the studio camera
assets/render-studio-leds.mp4       a rainbow wave running across the per-key LEDs (loops)
assets/render-studio-turntable.mp4  one turn round the keyboard (loops)
assets/render-studio-bootup.mp4     close-up of both OLEDs running the firmware boot animation
assets/render-studio-<video>-poster.jpg   a frame of each video with a play mark, for the docs to link

Run tools/gen_blend.py first (regen.py does); the views are set up in tools/blend_render.py. The stills are
1920 x 1080 Cycles renders, on the CPU; the videos 1920 x 1080 at 30 frames a second, EEVEE renders on the
discrete GPU (DRI_PRIME=1). A full run takes about an hour and a half.

    python3 tools/render_blender.py              write the assets
    python3 tools/render_blender.py --preview    small and noisy, into $TMPDIR/keygen-preview/ instead, with
                                                 a contact sheet of a few frames for each video
    python3 tools/render_blender.py bootup       just the two-screen boot animation

Uses $KEYGEN_BLENDER as the Blender binary if set, else `blender`.

The frames go to $TMPDIR/keygen-studio/<prefix>/ and stay there until encoded, so a run that stops
part way (a crash, a kill) picks up from the last whole frame when run again; Blender's log is
blender.log there. A change to the scene, the render script or the firmware's screens starts afresh.
"""
import hashlib, os, shutil, subprocess, sys, tempfile
from pathlib import Path

import media, render_oled, thermal

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "blender/keygen.blend"
STILLS = ("hero", "top", "thumbs", "oled", "side", "bottom")
VIDEOS = {"film": 0.62, "leds": 0.0, "turntable": 0.12, "bootup": 0.55}   # where in each its poster is
FPS = 30
# what the frames depend on: a change to any starts the frames afresh
STAMPED = ["blender/keygen.blend", "blender/keygen-parts.blend", "tools/blend_render.py",
           "firmware/module/src/ui/*", "firmware/module/sim/*"]


def stamp():
    h = hashlib.sha256()
    for pattern in STAMPED:
        for f in sorted(ROOT.glob(pattern)):
            h.update(f.relative_to(ROOT).as_posix().encode() + b"\0" + f.read_bytes())
    return h.hexdigest()


def workdir(prefix, preview):
    """The frames directory: kept between runs while the stamp matches, else emptied."""
    if preview:
        return Path(tempfile.mkdtemp(prefix="keygen-preview-"))
    work = Path(tempfile.gettempdir()) / "keygen-studio" / prefix
    if (work / "stamp").exists() and (work / "stamp").read_text() != stamp():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    (work / "stamp").write_text(stamp())
    return work


def main():
    preview = "--preview" in sys.argv[1:]
    requested = [a for a in sys.argv[1:] if not a.startswith("--")]
    views = requested or [*STILLS, *VIDEOS]
    unknown = set(views) - set(STILLS) - set(VIDEOS)
    if unknown: sys.exit(f"unknown Blender views: {sorted(unknown)}")
    prefix = "render-studio"
    out = Path(tempfile.gettempdir()) / "keygen-preview" if preview else ROOT / "assets"
    out.mkdir(parents=True, exist_ok=True)
    blender = os.environ.get("KEYGEN_BLENDER", "blender")
    tmp = workdir(prefix, preview)
    if {"bootup", "film"} & set(views):
        render_oled.simulate(tmp)
    log = tmp / "blender.log"
    with open(log, "w") as fh:
        p = subprocess.Popen([blender, "-b", str(STUDIO), "--python-exit-code", "1", "--python",
                              str(ROOT / "tools/blend_render.py"), "--", str(tmp), *(["--preview"] if preview else []),
                              *views],
                             stdout=fh, stderr=subprocess.STDOUT, text=True, env=dict(os.environ, DRI_PRIME="1"))
        dog = thermal.Watchdog(p.pid, log=lambda m: print(f"keygen: {m}", file=fh, flush=True))
        dog.start()
        p.wait()
        dog.stop()
    text = log.read_text()
    print("\n".join(l for l in text.splitlines() if l.startswith("keygen:")))
    if p.returncode:
        sys.exit(f"blender failed ({p.returncode}), frames kept in {tmp}:\n{text[-3000:]}")
    for name in STILLS:
        if name not in views: continue
        dst = out / f"{prefix}-{name}.jpg"
        subprocess.run(["magick", f"{tmp}/{name}.png", "-strip", "-quality", "90", str(dst)], check=True)
        (tmp / f"{name}.png").unlink()
        print(f"wrote {dst}")
    for name, at in VIDEOS.items():
        if name not in views: continue
        frames = sorted(tmp.glob(f"{name}_*.png"))
        if preview:
            dst = out / f"{prefix}-{name}-preview.jpg"
            subprocess.run(["magick", "montage", *map(str, frames), "-tile", "3x", "-geometry", "+4+4",
                            "-background", "black", str(dst)], check=True)
            print(f"wrote {dst}")
            continue
        dst = out / f"{prefix}-{name}.mp4"
        media.mp4(f"{tmp}/{name}_%04d.png", FPS, dst)
        media.poster(frames[round(at * (len(frames) - 1))], out / f"{prefix}-{name}-poster.jpg")
        print(f"wrote {dst}: {len(frames) / FPS:.1f} s, {dst.stat().st_size / 1e6:.1f} MB, and its poster")
        for f in frames:
            f.unlink()
    if preview:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
