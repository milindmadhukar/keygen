#!/usr/bin/env python3
"""Synthesize the build video's voiceover with Piper, and the timings the Remotion scenes follow.

    $TMPDIR/piper-venv/bin/python video/tts/make_vo.py

Reads video/script/scenes.json. Writes video/remotion/public/vo/voice.wav (the whole narration, each
sentence at its place) and video/remotion/src/timings.json (every scene's start and length in frames,
and each sentence's frames and step). Sentences are cached by text in $TMPDIR/keygen-vo-cache.
"""
import hashlib, json, os, re, wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "video/script/scenes.json"
PUBLIC = ROOT / "video/remotion/public/vo"
TIMINGS = ROOT / "video/remotion/src/timings.json"
VOICES = Path(os.environ.get("TMPDIR", "/var/tmp")) / "piper-voices"
CACHE = Path(os.environ.get("TMPDIR", "/var/tmp")) / "keygen-vo-cache"
FPS = 30
LEAD, GAP, TAIL = 0.5, 0.4, 1.0          # seconds: before the first sentence, between, after the last
CHAPTER = 2.6                               # seconds, a chapter card
TITLE_LEAD = 2.2

WORDS = [  # spoken forms, longest first where they overlap
    ("SN74LV1T125", "S N seventy-four L V one T one twenty-five"),
    ("nRF52840", "N R F fifty-two eight forty"),
    ("TPS61023", "T P S sixty-one oh twenty-three"),
    ("AO3401A", "A O thirty-four oh one A"),
    ("1N4148W", "one N forty-one forty-eight W"),
    ("GND, VCC, SCL, SDA", "ground, V C C, S C L, S D A"),
    ("GND and VCC", "ground and V C C"),
    ("NICENANO", "nice nano"), ("UF2", "U F 2"), ("EC11", "E C eleven"), ("M7", "M 7"),
    ("M2 by 16", "M 2 by 16"), ("M2 by 5", "M 2 by 5"), ("M2", "M 2"),
    ("1.25u", "one point two five U"), ("1u", "one U"), ("3D-printed", "three D printed"),
    ("PETG", "P E T G"), ("EVA", "E V A"), ("LiPo", "lie-poe"), ("OLEDs", "oh-leds"), ("OLED", "oh-led"),
    ("MOSFET", "moss-fet"), ("PCBs", "P C Bs"), ("PCB", "P C B"), ("DSA", "D S A"), ("JST", "J S T"),
    ("USB-C", "U S B C"), ("USB", "U S B"), ("VCC", "V C C"), ("CNC", "C N C"), ("BOOST", "boost"),
    ("GENERATE", "generate"), ("A4", "A 4"), ("S1", "S 1"), ("S2", "S 2"), ("MX", "M X"),
]


def ref_words(m):
    letters = " ".join(m.group(1)) if m.group(1) != "LED" else "L E D"
    n = int(m.group(2))
    hundreds, rest = divmod(n, 100)
    tail = f"oh {rest}" if rest < 10 else str(rest)
    return f"{letters} {hundreds} {tail}"


def spoken(text):
    for a, b in WORDS:
        text = re.sub(rf"(?<![\w-]){re.escape(a)}(?![\w])", b, text)
    return re.sub(r"\b(Q|R|U|L|C|D|J|H|BT|SW|LED)(\d{3})\b", ref_words, text)


def synth(voice, cfg, text, key):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{hashlib.sha1((key + text).encode()).hexdigest()[:16]}.wav"
    if not path.exists():
        with wave.open(str(path), "wb") as w:
            voice.synthesize_wav(text, w, syn_config=cfg)
    with wave.open(str(path), "rb") as w:
        return w.getframerate(), w.readframes(w.getnframes())


def main():
    spec = json.loads(SCRIPT.read_text())
    voice = PiperVoice.load(str(VOICES / f"{spec['voice']}.onnx"))
    cfg = SynthesisConfig(length_scale=spec.get("lengthScale", 1.0))
    key = f"{spec['voice']}-{spec.get('lengthScale', 1.0)}"
    rate = None
    pcm = bytearray()
    scenes, frame = [], 0

    def pad_to(seconds):
        nonlocal pcm
        want = int(round(seconds * rate)) * 2
        if len(pcm) < want:
            pcm += bytes(want - len(pcm))

    for sc in spec["scenes"]:
        start = frame
        if sc["kind"] == "chapter":
            length = round(CHAPTER * FPS)
            scenes.append(dict(id=sc["id"], start=start, frames=length, sentences=[]))
            frame += length
            continue
        t = start / FPS + (TITLE_LEAD if sc["kind"] == "title" else LEAD)
        sentences = []
        for item in sc.get("say", []):
            text, step = (item[0], item[1]) if isinstance(item, list) else (item, None)
            r, audio = synth(voice, cfg, spoken(text), key)
            rate = rate or r
            pad_to(t)
            pcm[int(round(t * rate)) * 2:] = b""
            pcm += audio
            dur = len(audio) / 2 / rate
            sentences.append(dict(text=text, step=step, start=round(t * FPS), end=round((t + dur) * FPS)))
            t += dur + GAP
        end = t - GAP + TAIL
        length = round(end * FPS) - start
        scenes.append(dict(id=sc["id"], start=start, frames=length, sentences=sentences))
        frame += length
    pad_to(frame / FPS)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    with wave.open(str(PUBLIC / "voice.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(bytes(pcm))
    TIMINGS.parent.mkdir(parents=True, exist_ok=True)
    TIMINGS.write_text(json.dumps(dict(fps=FPS, frames=frame, scenes=scenes), indent=1))
    print(f"{len(scenes)} scenes, {frame / FPS / 60:.2f} min, voice {len(pcm) / 2 / rate / 60:.2f} min")
    for s in scenes:
        print(f"  {s['id']:<12} {s['frames'] / FPS:6.1f} s")


main()
