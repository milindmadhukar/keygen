"""Video helpers for the render scripts: an MP4 from numbered frames or raw RGB, and a poster.

GitHub does not play a release asset's video in a README, so each MP4 has a poster, one of its
frames with a play mark in the middle, which the docs show linked to the video.
"""
import subprocess
from pathlib import Path

X264 = ["-c:v", "libx264", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


def mp4(pattern, fps, dst, crf=18):
    """Encode numbered frames (an ffmpeg pattern such as name_%04d.png) to an H.264 MP4."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(pattern),
                    *X264, "-crf", str(crf), str(dst)], check=True)


def mp4_raw(frames, size, fps, dst, crf=16):
    """Encode an iterable of RGB byte strings, each size[0] x size[1], to an H.264 MP4."""
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{size[0]}x{size[1]}", "-framerate", str(fps), "-i", "-",
                          *X264, "-tune", "animation", "-crf", str(crf), str(dst)], stdin=subprocess.PIPE)
    for frame in frames:
        p.stdin.write(frame)
    p.stdin.close()
    if p.wait():
        raise RuntimeError(f"ffmpeg failed on {dst}")


def poster(src, dst):
    """src with a play mark in the middle (a dark disc and a white triangle), as dst (JPG or PNG)."""
    w, h = (int(v) for v in subprocess.run(["magick", "identify", "-format", "%w %h", str(src)],
                                            check=True, capture_output=True, text=True).stdout.split())
    cx, cy, r = w / 2, h / 2, min(w, h) * 0.075
    tri = [(cx - 0.35 * r, cy - 0.55 * r), (cx - 0.35 * r, cy + 0.55 * r), (cx + 0.6 * r, cy)]
    quality = ["-quality", "90"] if Path(dst).suffix == ".jpg" else []
    subprocess.run(["magick", str(src), "-strip",
                    "-fill", "rgba(0,0,0,0.55)", "-stroke", "rgba(255,255,255,0.85)",
                    "-strokewidth", str(max(2, round(r * 0.06))),
                    "-draw", f"circle {cx:.0f},{cy:.0f} {cx + r:.0f},{cy:.0f}",
                    "-stroke", "none", "-fill", "rgba(255,255,255,0.92)",
                    "-draw", "polygon " + " ".join(f"{x:.0f},{y:.0f}" for x, y in tri),
                    *quality, str(dst)], check=True)
