"""Blender side of tools/render_blender.py; run inside Blender on the studio file, not on its own:

    blender -b blender/keygen.blend --python tools/blend_render.py -- <outdir> [--preview] [view ...]

Writes into <outdir>:

hero.png              the studio camera, as set up in blender/keygen.blend
top.png               straight down on both halves
thumbs.png            close up on the left half's knob, OLED and thumb cluster
oled.png              close up on the left half's OLED, showing its status screen, and the knob
side.png              low along the back edge: the case's profile, the USB-C ports and power switches
bottom.png            straight down on the keyboard turned over on the floor: the case's underside
leds_####.png         the hero view, a rainbow wave running across the LEDs (a looping GIF's frames)
turntable_####.png    one turn round the keyboard (a looping GIF's frames)

The linked parts are swapped for a local copy first, so the LEDs and the camera can be animated.
--preview renders small and noisy, to check a change quickly. --tented stands each half on its wedge.
"""
import colorsys, math, sys
from pathlib import Path

import bmesh, bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = Path(argv[0])
PREVIEW = "--preview" in argv
TENTED = "--tented" in argv
VIEWS = [a for a in argv[1:] if not a.startswith("--")] or ["hero", "top", "thumbs", "oled", "side", "leds",
                                                             "turntable", "bottom"]

STILL = dict(width=1920, height=1080, samples=128)
FRAMES = dict(width=640, height=360, samples=16)
LED_FRAMES, TURN_FRAMES = 36, 48
WAVE_SPAN = 0.7            # hues across the keyboard at once in the LED wave


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


def split_halves(col, mid):
    """Cut every mesh that spans the gap between the halves in two, so each half can move on its own."""
    bpy.context.view_layer.update()
    for o in [o for o in col.all_objects if o.type == "MESH"]:
        xs = [(o.matrix_world @ Vector(c)).x for c in o.bound_box]
        if not min(xs) < mid < max(xs):
            continue
        twin = o.copy(); twin.data = o.data.copy()
        for c in o.users_collection:
            c.objects.link(twin)
        for ob, on_left in ((o, True), (twin, False)):
            bm = bmesh.new(); bm.from_mesh(ob.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if ((ob.matrix_world @ v.co).x < mid) != on_left], context="VERTS")
            bm.to_mesh(ob.data); bm.free()


def tent(col, floor_z):
    """Stand each half on its wedge: tilt it about the wedge's outer bottom edge, and set that edge on the floor."""
    wedges = next(c for c in col.children if c.name.split(".")[0] == "Wedges").objects
    bpy.context.view_layer.update()
    box = lambda o: [o.matrix_world @ Vector(c) for o_ in [o] for c in o_.bound_box]
    left = next(o for o in wedges if o.name.startswith("left"))
    right = next(o for o in wedges if o.name.startswith("right"))
    mid = (max(p.x for p in box(left)) + min(p.x for p in box(right))) / 2
    turn = {}
    for w, side, sign in ((left, "left", -1), (right, "right", 1)):
        w.hide_render = w.hide_viewport = False
        pts = box(w)
        x = min(p.x for p in pts) if side == "left" else max(p.x for p in pts)
        pivot = Vector((x, 0, max(p.z for p in pts) - w["tent_edge"]))
        turn[side] = (Matrix.Translation((x, 0, floor_z)) @ Matrix.Rotation(sign * math.radians(w["tent_angle"]), 4, "Y")
                      @ Matrix.Translation(-pivot))
    split_halves(col, mid)
    bpy.context.view_layer.update()
    placed = []
    for o in col.all_objects:
        pts = box(o) if o.type == "MESH" else [o.matrix_world.translation]
        placed.append((o, o.matrix_world.copy(), sum(p.x for p in pts) / len(pts) < mid))
    for o, world, on_left in placed:
        o.parent = None
        o.matrix_world = turn["left" if on_left else "right"] @ world
    bpy.context.view_layer.update()
    log("tented on the wedges")


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


def settings(scene, s):
    k = 0.25 if PREVIEW else 1.0
    scene.render.resolution_x, scene.render.resolution_y = int(s["width"] * k), int(s["height"] * k)
    scene.render.resolution_percentage = 100
    scene.cycles.samples = max(4, int(s["samples"] * k))
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"


def still(scene, name, cam, aspect=16 / 9):
    settings(scene, dict(STILL, height=round(STILL["width"] / aspect)))
    scene.camera = cam
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    log(f"rendered {name}")


def animation(scene, name, cam, frames):
    settings(scene, FRAMES)
    scene.camera = cam
    scene.frame_start, scene.frame_end = 1, frames if not PREVIEW else min(frames, 6)
    scene.render.use_persistent_data = True          # keep the scene between frames; only lights and camera move
    scene.render.filepath = str(OUT / f"{name}_")
    bpy.ops.render.render(animation=True)
    log(f"rendered {name}: {scene.frame_end} frames")


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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    col = localise()
    if TENTED:
        floor_z = bounds(col)[0].z
        tent(col, floor_z)
    lo, hi = bounds(col)
    if TENTED:
        lo.z = floor_z
    centre, size = (lo + hi) / 2, hi - lo
    hero = scene.camera
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"

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
    if "bottom" in VIEWS:                                      # last: it moves the keyboard
        turn_over(col, lo, centre)
        bottom = camera("Bottom", centre + Vector((0, 0, 1.0)), centre, ortho=size.x * 1.06)
        still(scene, "bottom", bottom)


main()
