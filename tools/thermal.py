"""Keep long renders from overheating the machine (an OMEN 16 laptop, whose discrete GPU reaches its
100 °C shutdown in a few minutes of EEVEE at full load).

The GPU junction temperature swings by 20 °C within seconds: it peaks while a frame renders and drops
as soon as it ends. So there are two guards. Between frames, blend_render.py waits while anything is
over PAUSE, and rests the GPU as long as each frame took. Watchdog, run by render_blender.py, polls
twice a second and freezes the Blender process (SIGSTOP) over FREEZE, mid-frame if need be, until it
cools.
"""
import os, signal, threading, time
from pathlib import Path

# (hwmon driver, sensor label): (over this °C, wait until under this)
PAUSE = {("amdgpu", "junction"): (80, 65), ("k10temp", "Tctl"): (95, 80)}
FREEZE = {("amdgpu", "junction"): (92, 70)}
REST = 1.0                 # after each GPU frame, rest this many times as long as it took


def temperatures(keys):
    """{(driver, label): °C} for those of keys this machine has."""
    found = {}
    for hw in Path("/sys/class/hwmon").glob("hwmon*"):
        try:
            driver = (hw / "name").read_text().strip()
        except OSError:
            continue
        for t in hw.glob("temp*_input"):
            label = t.with_name(t.name.replace("_input", "_label"))
            try:
                key = (driver, label.read_text().strip() if label.exists() else "")
                if key in keys:
                    found[key] = max(found.get(key, 0), int(t.read_text()) / 1000)
            except OSError:
                pass
    return found


def over(limits):
    """The sensors over their limit: {key: °C}."""
    return {k: c for k, c in temperatures(limits).items() if c >= limits[k][0]}


def wait_cool(limits=PAUSE, log=print):
    """Wait while any sensor is over its limit, until each that was is back under its resume point."""
    hot = over(limits)
    if not hot:
        return
    log("hot (" + ", ".join(f"{d} {l} {c:.0f} °C" for (d, l), c in hot.items()) + "), pausing")
    start = time.monotonic()
    while any(c > limits[k][1] for k, c in temperatures(hot).items()):
        time.sleep(2)
    log(f"cooled after {time.monotonic() - start:.0f} s")


class Watchdog(threading.Thread):
    """Freeze process pid while a FREEZE sensor is over its limit."""

    def __init__(self, pid, log=print):
        super().__init__(daemon=True)
        self.pid, self.log, self.stopped, self.freezes = pid, log, threading.Event(), 0

    def run(self):
        while not self.stopped.wait(0.5):
            hot = over(FREEZE)
            if not hot:
                continue
            try:
                os.kill(self.pid, signal.SIGSTOP)
            except ProcessLookupError:
                return
            self.freezes += 1
            self.log(f"watchdog: froze Blender at {max(hot.values()):.0f} °C")
            while not self.stopped.is_set() and any(c > FREEZE[k][1] for k, c in temperatures(hot).items()):
                time.sleep(1)
            try:
                os.kill(self.pid, signal.SIGCONT)
            except ProcessLookupError:
                return

    def stop(self):
        self.stopped.set()
        try:
            os.kill(self.pid, signal.SIGCONT)
        except ProcessLookupError:
            pass
