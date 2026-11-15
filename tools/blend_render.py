"""Blender side of tools/render_blender.py; run inside Blender on the studio file, not on its own:

    blender -b blender/keygen.blend --python tools/blend_render.py -- <outdir> [--preview] [view ...]

Writes into <outdir>:

hero.png              the studio camera, as set up in blender/keygen.blend
top.png               straight down on both halves
thumbs.png            close up on the left half's knob, OLED and thumb cluster
oled.png              close up on the left half's OLED, showing its status screen, and the knob
side.png              low along the back edge: the case's profile, the USB-C ports and power switches
bottom.png            straight down on the keyboard turned over on the floor: the case's underside
leds_####.png         the hero view, a rainbow wave running across the LEDs (a looping video's frames)
turntable_####.png    one turn round the keyboard (a looping video's frames)
bootup_####.png       close-up of both OLEDs showing the firmware boot sequence
film_####.png         the hero film: the OLEDs boot in the dark, the LEDs sweep on, the camera glides low
                      along the keys under a rainbow wave and rises to the studio camera as the LEDs
                      settle into the studio colours

<outdir> keeps what is done: a still or frame already there, whole, is not rendered again, so a run
that stops part way picks up where it left off. Before each still and frame, a hot GPU or CPU waits to
cool, and the GPU rests between frames (tools/thermal.py).

The stills render with Cycles; the animations, 1920 x 1080 at 30 frames a second, with EEVEE (on the GPU,
with shadows, so the LEDs light only the caps). The linked parts are swapped for a local copy first, so
the LEDs and the camera can be animated. --preview renders small and noisy, and only a few frames of each
animation, to check a change quickly.
"""
import bisect, colorsys, math, sys, time
from array import array
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import thermal

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = Path(argv[0])
PREVIEW = "--preview" in argv
VIEWS = [a for a in argv[1:] if not a.startswith("--")] or ["hero", "top", "thumbs", "oled", "side", "leds",
                                                             "turntable", "film", "bottom"]

STILL = dict(width=1920, height=1080, samples=128)
MOTION = dict(width=1920, height=1080, samples=16)    # EEVEE samples per frame: about half the heat of 32, alike at 1080p
FPS = 30
LED_FRAMES, TURN_FRAMES = 4 * FPS, 8 * FPS
WAVE_SPAN = 0.7            # hues across the keyboard at once in the LED wave
PREVIEW_FRAMES = 6         # frames of each animation that --preview renders, spread over its length


def log(msg):
    print(f"keygen: {msg}", flush=True)


def localise():
    """Replace the linked Keygen collection instance with an appended copy of the collection."""
    scene = bpy.context.scene
    inst = next(o for o in scene.objects if o.instance_type == "COLLECTION" and o.instance_collection)
    lib = inst.instance_collection.library
    path = bpy.path.abspath(lib.filepath)
    bpy.data.objects.remove(inst)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = ["Keygen"]
    col = dst.collections[0]
    scene.collection.children.link(col)
    return col


def bounds(col):
    """The case's bounding box: the outermost part, and free of stray GLB geometry."""
    case = next(c for c in col.children if c.name.split(".")[0] == "Case")
    pts = [o.matrix_world @ Vector(c) for o in case.all_objects if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def turn_over(col, lo, centre):
    """Turn the keyboard upside down about its long axis and lay it on the floor, resting on its
    highest point (the knobs), so the studio lights fall on the case's underside."""
    zmax = max((o.matrix_world @ Vector(c)).z for o in col.all_objects if o.type == "MESH" for c in o.bound_box)
    pivot = bpy.data.objects.new("Turned over", None)
    bpy.context.scene.collection.objects.link(pivot)
    for o in col.all_objects:
        if o.parent is None:
            o.parent = pivot
    pivot.rotation_euler.y = math.pi                         # (x, y, z) -> (2 cx - x, y, lo + zmax - z)
    pivot.location = (2 * centre.x, 0, lo.z + zmax)
    for o in col.all_objects:                                # LEDs off: they would light the floor through the caps
        if o.type == "LIGHT":
            o.hide_render = True
    light = bpy.data.lights.new("Underside light", "AREA"); light.energy = 6.0; light.size = 0.5
    lo_ = bpy.data.objects.new("Underside light", light)
    lo_.location = centre + Vector((-0.5, -0.4, 0.5)); look_at(lo_, centre)
    bpy.context.scene.collection.objects.link(lo_)


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, lens=50, fstop=None, ortho=None):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    look_at(cam, target)
    cam.data.lens = lens
    cam.data.clip_start = 0.005
    if ortho:
        cam.data.type = "ORTHO"; cam.data.ortho_scale = ortho
    if fstop:
        focus = bpy.data.objects.new(f"{name} focus", None); focus.location = target
        bpy.context.scene.collection.objects.link(focus)
        cam.data.dof.use_dof = True; cam.data.dof.focus_object = focus; cam.data.dof.aperture_fstop = fstop
    return cam


def settings(scene, s, engine="CYCLES"):
    k = 0.25 if PREVIEW else 1.0
    scene.render.resolution_x, scene.render.resolution_y = int(s["width"] * k), int(s["height"] * k)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if engine == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = max(4, int(s["samples"] * k))
        scene.cycles.use_denoising = True
        return
    scene.render.engine = "BLENDER_EEVEE"           # every light casts shadows: else the LEDs shine through the case
    ee = scene.eevee
    ee.taa_render_samples = max(4, int(s["samples"] * k))
    ee.use_shadows = True
    ee.shadow_ray_count, ee.shadow_step_count = 1, 4
    ee.use_raytracing = True
    ee.ray_tracing_options.resolution_scale = "1"
    for light in bpy.data.lights:
        light.use_shadow = True


def done(path):
    """A whole PNG is already at path (a run cut off mid-write leaves a part of one)."""
    try:
        with open(path, "rb") as f:
            f.seek(-12, 2)
            return b"IEND" in f.read()
    except OSError:
        return False


def render(scene, path):
    """Render the current frame to path, unless it is already there."""
    if not PREVIEW and done(path):
        return False
    thermal.wait_cool(log=log)
    scene.render.filepath = str(path)
    start = time.monotonic()
    bpy.ops.render.render(write_still=True)
    if scene.render.engine != "CYCLES":                      # rest the GPU
        time.sleep(thermal.REST * (time.monotonic() - start))
    return True


def still(scene, name, cam, aspect=16 / 9):
    settings(scene, dict(STILL, height=round(STILL["width"] / aspect)))
    scene.camera = cam
    log(f"rendered {name}" if render(scene, OUT / f"{name}.png") else f"{name}: already done")


def frames_to_render(count, preview):
    """Every frame, or with --preview a few spread over the whole animation."""
    if not PREVIEW:
        return list(range(1, count + 1))
    return sorted({1 + round(i * (count - 1) / (preview - 1)) for i in range(preview)})


def animation(scene, name, cam, count, each_frame=None, preview=PREVIEW_FRAMES):
    """Render frames 1..count to <name>_####.png, calling each_frame(frame) first to set the scene."""
    settings(scene, MOTION, engine="EEVEE")
    scene.camera = cam
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, count
    for f in frames_to_render(count, preview):
        path = OUT / f"{name}_{f:04d}.png"
        if not PREVIEW and done(path):
            continue
        scene.frame_set(f)
        if each_frame:
            each_frame(f)
        render(scene, path)
        if f % 30 == 0 or f == count:
            log(f"{name} frame {f}/{count}")
    log(f"rendered {name}: {count} frames")


def boot_frames(side):
    """Read the firmware simulator's 1-bit 128 x 64 frames, keeping their durations."""
    raw = (OUT / f"boot-{side}.frames").read_bytes()
    stride = 2 + 128 * 64 // 8
    if len(raw) % stride:
        raise ValueError(f"invalid boot-{side}.frames length")
    times, images, elapsed = [], [], 0
    for offset in range(0, len(raw), stride):
        elapsed += int.from_bytes(raw[offset:offset + 2], "little")
        times.append(elapsed)
        images.append(raw[offset + 2:offset + stride])
    return times, images


def show_boot_frame(image, framebuffer):
    """Update the OLED texture. The framebuffer is top-first; Blender pixels are bottom-first."""
    pixels = array("f", [0.0]) * (128 * 64 * 4)
    for y in range(64):
        src, dst = y * 16, (63 - y) * 128 * 4
        for x in range(128):
            value = float((framebuffer[src + x // 8] >> (7 - x % 8)) & 1)
            i = dst + 4 * x
            pixels[i] = pixels[i + 1] = pixels[i + 2] = value
            pixels[i + 3] = 1.0
    image.pixels.foreach_set(pixels)
    image.update()
    image.pack()


def oled_screens(col):
    """Both OLEDs' screen objects, their centres, and a function to put a boot frame on them at a time."""
    screens = [next(o for o in col.all_objects if o.name.startswith(f"OLED {side} screen"))
               for side in ("left", "right")]
    points = [sum((screen.matrix_world @ v.co for v in screen.data.vertices), Vector()) / 4
              for screen in screens]
    sequences = {side: boot_frames(side) for side in ("left", "right")}
    duration = max(times[-1] for times, _ in sequences.values())
    dark = bytes(128 * 64 // 8)

    def show(ms):
        """The boot sequence at ms after power on: dark before it, its last frame after it."""
        for side, (times, images) in sequences.items():
            image = dark if ms < 0 else images[min(bisect.bisect_right(times, ms), len(images) - 1)]
            show_boot_frame(bpy.data.images[f"OLED {side}"], image)
    return points, duration, show


def bootup(scene, col):
    points, duration, show = oled_screens(col)
    target = (points[0] + points[1]) / 2
    cam = camera("Both OLEDs booting", target + Vector((0, -0.035, 0.20)), target, lens=60, fstop=11.0)
    animation(scene, "bootup", cam, math.ceil(duration * FPS / 1000), lambda f: show((f - 1) * 1000 / FPS))


def led_wave(col, frames):
    """Keyframe a rainbow running across the keyboard, one full cycle over the loop."""
    leds = [o for o in col.all_objects if "led_color" in o.keys()]
    lights = {o.name.removesuffix(" light"): o.data for o in col.all_objects if o.type == "LIGHT"}
    xs = [o.location.x for o in leds]
    x0, span = min(xs), max(xs) - min(xs)
    for f in range(1, frames + 1):
        for o in leds:
            hue = ((o.location.x - x0) / span * WAVE_SPAN - (f - 1) / frames) % 1.0
            c = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
            o["led_color"] = (*c, 1.0)
            o.keyframe_insert('["led_color"]', frame=f)
            light = lights.get(o.name.split(".")[0])
            if light:
                light.color = c
                light.keyframe_insert("color", frame=f)


class Leds:
    """The per-key LEDs: set each one's colour and brightness for a frame. Made before anything animates
    them, so it holds the studio scheme."""

    def __init__(self, col):
        self.leds = [o for o in col.all_objects if "led_color" in o.keys()]
        lights = {o.name.removesuffix(" light"): o for o in col.all_objects if o.type == "LIGHT"}
        self.lights = [lights.get(o.name.split(".")[0]) for o in self.leds]
        self.studio = [Vector(o["led_color"][:3]) for o in self.leds]     # the studio scheme
        self.power = next(l.data.energy for l in self.lights if l)
        xs = [o.location.x for o in self.leds]
        self.x0, self.span = min(xs), max(xs) - min(xs)
        self.mid = (min(xs) + max(xs)) / 2

    def x(self, i):
        """0 at the left edge to 1 at the right."""
        return (self.leds[i].location.x - self.x0) / self.span

    def set(self, colour):
        """colour(i): (r, g, b, brightness 0..1) of LED i. Drops any keyframes, the LED wave's."""
        for i, (o, light) in enumerate(zip(self.leds, self.lights)):
            r, g, b, k = colour(i)
            o.animation_data_clear()
            o["led_color"] = (r * k, g * k, b * k, 1.0)
            o.update_tag()
            if light:
                light.data.animation_data_clear()
                light.data.color = (r, g, b)
                light.data.energy = self.power * k
                light.data.update_tag()


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def spline(keys, t):
    """A smooth path through keys [(time, value)], value a tuple: a cubic Hermite with Catmull-Rom
    tangents inside, and at rest at both ends."""
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return keys[0][1]
    if t >= ts[-1]:
        return keys[-1][1]
    i = bisect.bisect_right(ts, t) - 1
    def tangent(j):
        if j in (0, len(keys) - 1):
            return [0.0] * len(keys[j][1])
        dt = ts[j + 1] - ts[j - 1]
        return [(b - a) / dt for a, b in zip(keys[j - 1][1], keys[j + 1][1])]
    t0, t1 = ts[i], ts[i + 1]
    h, u = t1 - t0, (t - t0) / (t1 - t0)
    m0, m1 = tangent(i), tangent(i + 1)
    h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
    return tuple(h00 * p0 + h10 * h * a + h01 * p1 + h11 * h * b
                 for p0, p1, a, b in zip(keys[i][1], keys[i + 1][1], m0, m1))


BOOT_AT = 0.4              # s into the film the OLEDs power on
FILM_LENGTH = 16.5         # s


def film(scene, col, hero, leds):
    """One take: close on both OLEDs booting in the dark; the LEDs sweep on from the middle; a low glide
    along the keys under a rainbow wave; a rise to the studio camera as the LEDs settle into the studio
    scheme."""
    points, _, show = oled_screens(col)
    oled = (points[0] + points[1]) / 2
    target = next(o for o in scene.objects if o.name == "Camera target").location.copy()
    home = hero.matrix_world.translation.copy()
    v = lambda *c: tuple(c)
    # time (s): camera, the point it looks at and focuses on, lens (mm), f-stop
    shots = [
        (0.0, oled + Vector((-0.035, -0.085, 0.17)), oled + Vector((-0.010, 0, 0)), 50, 5.6),
        (5.0, oled + Vector((0.030, -0.075, 0.15)), oled + Vector((0.008, 0, 0)), 50, 5.6),
        (7.8, Vector((0.46, -0.30, 0.11)), Vector((0.32, -0.15, 0.005)), 40, 4.0),
        (10.8, Vector((0.26, -0.36, 0.10)), Vector((0.15, -0.15, 0.005)), 40, 4.0),
        (14.2, home, target, hero.data.lens, hero.data.dof.aperture_fstop),
        (FILM_LENGTH, home.lerp(target, 0.05), target, hero.data.lens, hero.data.dof.aperture_fstop),
    ]
    path = [(t, v(*c, *a, lens, fs)) for t, c, a, lens, fs in shots]
    cam = camera("Film", shots[0][1], shots[0][2], lens=shots[0][3])
    cam.data.dof.use_dof = True
    on = BOOT_AT + 5.0                                   # the LEDs come on as the boot sequence ends
    settle = (11.0, 13.8)                                # the rainbow fades into the studio colours

    def frame(f):
        t = (f - 1) / FPS
        p = spline(path, t)
        cam.location = p[:3]
        look_at(cam, Vector(p[3:6]))
        cam.data.lens = p[6]
        cam.data.dof.aperture_fstop = p[7]
        cam.data.dof.focus_distance = (Vector(p[3:6]) - Vector(p[:3])).length
        show((t - BOOT_AT) * 1000)
        mix = smoothstep(*settle, t)

        def colour(i):
            x = leds.x(i)
            k = smoothstep(0, 0.35, t - on - abs(x - 0.5) * 1.2)      # from the middle outwards
            rgb = Vector(colorsys.hsv_to_rgb((x * WAVE_SPAN - (t - on) / 4.0) % 1.0, 0.85, 1.0))
            return (*rgb.lerp(leds.studio[i], mix), k)
        leds.set(colour)

    animation(scene, "film", cam, round(FILM_LENGTH * FPS), frame, preview=15)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    col = localise()
    lo, hi = bounds(col)
    centre, size = (lo + hi) / 2, hi - lo
    hero = scene.camera
    leds = Leds(col)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"

    if "film" in VIEWS:                                        # first: it ends with the scene as it began
        film(scene, col, hero, leds)
    if "hero" in VIEWS:
        still(scene, "hero", hero)
    if "top" in VIEWS:
        top = camera("Top", centre + Vector((0, 0, 1.0)), centre, ortho=size.x * 1.06)
        still(scene, "top", top)
    if "thumbs" in VIEWS:
        knob = next(o for o in col.all_objects if o.name.startswith("ENC1"))
        target = knob.matrix_world.translation.copy(); target.z = hi.z - 0.008
        target += Vector((-0.03, -0.03, 0))                  # between the knob and the thumb cluster
        cam = camera("Thumbs", target + Vector((-0.10, -0.26, 0.17)), target, lens=60, fstop=4.0)
        still(scene, "thumbs", cam)
    if "oled" in VIEWS:
        screen = next(o for o in col.all_objects if o.name.startswith("OLED left screen"))
        target = sum((screen.matrix_world @ v.co for v in screen.data.vertices), Vector()) / 4
        cam = camera("OLED", target + Vector((-0.04, -0.08, 0.15)), target, lens=70, fstop=8.0)
        still(scene, "oled", cam)
    if "side" in VIEWS:
        target = centre + Vector((0, size.y / 2, size.z * 0.4))
        cam = camera("Side", target + Vector((-0.30, 0.95, 0.06)), target, lens=80, fstop=11.0)
        still(scene, "side", cam, aspect=8 / 3)
    if "turntable" in VIEWS:
        pivot = bpy.data.objects.new("Turntable", None); pivot.location = centre
        scene.collection.objects.link(pivot)
        offset = hero.matrix_world.translation - centre
        cam = camera("Turntable camera", centre + offset, centre, lens=hero.data.lens)
        cam.parent = pivot; cam.location = offset                # the pivot sits at the centre, unturned
        n = TURN_FRAMES
        for f, a in ((1, 0.0), (n + 1, 2 * math.pi)):           # frame n + 1 is frame 1 again: a seamless loop
            pivot.rotation_euler.z = a; pivot.keyframe_insert("rotation_euler", index=2, frame=f)
        animation(scene, "turntable", cam, n)
    if "leds" in VIEWS:
        led_wave(col, LED_FRAMES)
        animation(scene, "leds", hero, LED_FRAMES)
    if "bootup" in VIEWS:
        bootup(scene, col)
    if "bottom" in VIEWS:                                      # last: it moves the keyboard
        turn_over(col, lo, centre)
        bottom = camera("Bottom", centre + Vector((0, 0, 1.0)), centre, ortho=size.x * 1.06)
        still(scene, "bottom", bottom)


main()
