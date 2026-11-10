#!/usr/bin/env python3
"""A quiet ambient pad under the narration: slow chords of soft, detuned sines.

    python3 video/music/pad.py <seconds>    writes video/remotion/public/music/bed.wav
"""
import sys, wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "video/remotion/public/music/bed.wav"
RATE = 44100
SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 600
CHORD_S = 9.0
# A minor, F major, C major, G major, voiced low and open (MIDI notes)
CHORDS = [[45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [36, 48, 52, 55, 60], [43, 50, 55, 59, 62]]


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def main():
    n = int(SECONDS * RATE)
    t = np.arange(n) / RATE
    out = np.zeros((n, 2))
    seg = int(CHORD_S * RATE)
    fade = int(3.0 * RATE)
    rng = np.random.default_rng(7)
    for i, start in enumerate(range(-fade, n, seg)):
        chord = CHORDS[i % len(CHORDS)]
        a, b = max(start, 0), min(start + seg + fade, n)
        if b <= a:
            continue
        tt = t[a:b]
        env = np.ones(b - a)
        ramp = min(fade, b - a)
        env[:ramp] *= np.sin(np.linspace(0, np.pi / 2, ramp)) ** 2 if start >= 0 else 1
        env[-ramp:] *= np.cos(np.linspace(0, np.pi / 2, ramp)) ** 2
        for note in chord:
            for side, det in ((0, -0.08), (1, 0.08)):
                f0 = hz(note) * (1 + det / 100)
                ph = rng.uniform(0, 2 * np.pi)
                tone = np.sin(2 * np.pi * f0 * tt + ph) + 0.25 * np.sin(4 * np.pi * f0 * tt + ph)
                lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * tt + ph)
                out[a:b, side] += tone * lfo * env / len(chord)
    k = int(0.04 * RATE)                                  # a gentle low-pass: moving average
    for c in range(2):
        out[:, c] = np.convolve(out[:, c], np.ones(k) / k, mode="same")
    g = np.ones(n)
    g[: 4 * RATE] = np.linspace(0, 1, 4 * RATE)
    g[-6 * RATE:] = np.linspace(1, 0, 6 * RATE)
    out *= g[:, None]
    out /= np.abs(out).max() + 1e-9
    out *= 0.6
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    print(f"wrote {OUT.relative_to(ROOT)}: {SECONDS:.0f} s")


main()
