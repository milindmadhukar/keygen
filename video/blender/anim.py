"""Animated clips for the build video, rendered with EEVEE from blender/keygen.blend.

Run inside Blender (video/blender/render.py does this):

    blender -b blender/keygen.blend --python video/blender/anim.py -- <clip> <outdir> [--preview] [--still N]

Writes <outdir>/<clip>/####.png and <outdir>/<clip>.json (frame count and the 2D screen positions of
named anchors on the last frame, for the video's labels). The studio file is opened and changed in
memory only; nothing is saved.

Frame: metres, KiCad x -> x, KiCad y -> -y, the board's underside at z = 0 (see tools/blend_scene.py).
"""
import json, math, re, sys
from pathlib import Path

import bmesh, bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
CLIP, OUT = argv[0], Path(argv[1])
PREVIEW = "--preview" in argv
STILL = int(argv[argv.index("--still") + 1]) if "--still" in argv else None
MM = 0.001
FPS = 30
ACCENT = (0.62, 0.45, 1.0)          # lavender, the LEDs' outer colour
MID_X = 211.5 * MM                  # between the halves


def log(msg):
    print(f"keygen: {msg}", flush=True)


# ---------------------------------------------------------------- scene

def localise():
    scene = bpy.context.scene
    inst = next(o for o in scene.objects if o.instance_type == "COLLECTION" and o.instance_collection)
    path = bpy.path.abspath(inst.instance_collection.library.filepath)
    bpy.data.objects.remove(inst)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = ["Keygen"]
    col = dst.collections[0]
    scene.collection.children.link(col)
    return col


def part_ref(o):
    while o.parent and o.parent.parent:
        o = o.parent
    return o.name.split(".")[0]


def wbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def centre_of(objs):
    lo, hi = wbox(objs)
    return (lo + hi) / 2


def split_halves(col, mid):
    """Cut every mesh that spans the gap between the halves in two (from tools/blend_render.py)."""
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
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if ((ob.matrix_world @ v.co).x < mid) != on_left],
                             context="VERTS")
            bm.to_mesh(ob.data); bm.free()
    bpy.context.view_layer.update()


class Kit:
    """The keyboard's objects sorted into the groups the build adds one by one."""

    def __init__(self, col):
        self.col = col
        self.sub = {c.name.split(".")[0]: c for c in col.children}
        split_halves(col, MID_X)
        self.meshes = [o for o in col.all_objects if o.type == "MESH"]
        self.lights = [o for o in col.all_objects if o.type == "LIGHT"]
        self.by_ref = {}
        for o in self.sub["Board"].all_objects:
            if o.type == "MESH":
                self.by_ref.setdefault(part_ref(o), []).append(o)

    def is_left(self, o):
        if o.type == "LIGHT":
            return o.matrix_world.translation.x < MID_X
        lo, hi = wbox([o])
        return (lo.x + hi.x) / 2 < MID_X

    def refs(self, pattern):
        rx = re.compile(pattern)
        return [o for r, objs in self.by_ref.items() if rx.fullmatch(r) for o in objs]

    def board_body(self):
        return [o for r, objs in self.by_ref.items() if not re.fullmatch(r"[A-Z]+\d+", r)
                and not r.startswith("OLED") and "nut" not in r for o in objs]

    def switches(self, side="1"):
        """Switch bodies (above the board) of the 33 keys; the sockets are the meshes under it."""
        return [o for o in self.refs(rf"SW{side}(0\d|1\d|2\d|3[0-4])") if wbox([o])[1].z > 0.002]

    def sockets(self, side="1"):
        return [o for o in self.refs(rf"SW{side}(0\d|1\d|2\d|3[0-4])") if wbox([o])[1].z <= 0.002]

    def case(self, part, side="left"):
        return [o for o in self.sub["Case"].objects if o.name.startswith(f"{side} {part}")]

    def plate(self, side="left"):
        return [o for o in self.sub["Plate"].objects if o.name.startswith(side)]

    def wedge(self, side="left"):
        return [o for o in self.sub["Wedges"].objects if o.name.startswith(side)]

    def keycaps(self, side="1"):
        return [o for o in self.sub["Keycaps"].objects if re.match(rf"Keycap SW{side}\d\d$", o.name.split(".")[0])]

    def led_emitters(self):
        return [o for o in self.sub["LEDs"].objects if o.type == "MESH"]

    def led_lights(self):
        return [o for o in self.sub["LEDs"].objects if o.type == "LIGHT"]


def set_visible(objs, on, frame=None):
    for o in objs:
        o.hide_render = not on
        o.hide_viewport = not on
        if frame is not None:
            o.keyframe_insert("hide_render", frame=frame)


def show_from(objs, frame):
    """Hidden before `frame`, shown from it."""
    for o in objs:
        o.hide_render = True; o.keyframe_insert("hide_render", frame=0)
        o.hide_render = False; o.keyframe_insert("hide_render", frame=frame)


def ease(objs):
    for o in objs:
        ad = o.animation_data
        if ad and ad.action:
            for fc in fcurves(ad.action):
                for k in fc.keyframe_points:
                    if fc.data_path == "hide_render":
                        k.interpolation = "CONSTANT"
                    else:
                        k.interpolation = "BEZIER"; k.easing = "AUTO"


def fcurves(action):
    if hasattr(action, "fcurves") and action.fcurves is not None:
        try:
            return list(action.fcurves)
        except Exception:
            pass
    out = []                                            # Blender 5 layered actions
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                out.extend(bag.fcurves)
    return out


def world_to_local_delta(o, d):
    """A world-space translation as a change to o.location."""
    if o.parent is None:
        return d.copy()
    m = (o.parent.matrix_world @ o.matrix_parent_inverse).to_3x3()
    return m.inverted() @ d


def move(o, d, f0, f1, appear=True):
    """Keyframe o from (rest + d) at f0 to rest at f1, hidden before f0 if `appear`."""
    rest = o.location.copy()
    o.location = rest + world_to_local_delta(o, d)
    o.keyframe_insert("location", frame=f0)
    o.location = rest
    o.keyframe_insert("location", frame=f1)
    if appear:
        show_from([o], f0)


def roots(objs):
    """The outermost of `objs` in each parent chain, so a part moves once."""
    s = set(objs)
    out = []
    for o in objs:
        p, top = o.parent, o
        while p is not None:
            if p in s:
                top = p
            p = p.parent
        if top not in out:
            out.append(top)
    return out


def drop(objs, f0, f1, height=14 * MM, axis=Vector((0, 0, 1))):
    for o in roots(objs):
        move(o, axis * height, f0, f1)


def flash(at, f0, length=24, energy=0.6, color=ACCENT, radius=0.02):
    """A soft coloured light that swells and fades over the group as it goes in."""
    l = bpy.data.lights.new("flash", "POINT"); l.color = color; l.shadow_soft_size = radius
    o = bpy.data.objects.new("flash", l); o.location = at
    bpy.context.scene.collection.objects.link(o)
    for f, e in ((0, 0.0), (f0, 0.0), (f0 + length // 3, energy), (f0 + length, 0.0)):
        l.energy = e; l.keyframe_insert("energy", frame=max(f, 0))
    return o


def pivot_parent(objs, at):
    """An empty at `at` with `objs` (their roots) parented to it, keeping their world positions."""
    e = bpy.data.objects.new("pivot", None); e.location = at
    bpy.context.scene.collection.objects.link(e)
    bpy.context.view_layer.update()
    for o in roots(objs):
        w = o.matrix_world.copy()
        o.parent = e
        o.matrix_parent_inverse = e.matrix_world.inverted()
        o.matrix_world = w
    bpy.context.view_layer.update()
    return e


# ---------------------------------------------------------------- camera, light, render

def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_camera(lens=50, fstop=None):
    cam = bpy.data.objects.new("Video camera", bpy.data.cameras.new("Video camera"))
    bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_start = 0.002
    target = bpy.data.objects.new("Video target", None)
    bpy.context.scene.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO"); c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    if fstop:
        cam.data.dof.use_dof = True; cam.data.dof.focus_object = target; cam.data.dof.aperture_fstop = fstop
    bpy.context.scene.camera = cam
    return cam, target


def cam_key(cam, target, f, pos, aim, lens=None):
    cam.location = pos; cam.keyframe_insert("location", frame=f)
    target.location = aim; target.keyframe_insert("location", frame=f)
    if lens:
        cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)


def floor_at(z):
    f = bpy.data.objects.get("Floor")
    if f:
        f.location.z = z


def studio_lights_around(centre):
    """Move the studio's three area lights to keep their offsets round a new subject."""
    offsets = {"Key light": (-0.35, -0.45, 0.55), "Rim light": (0.3, 0.5, 0.3), "Fill light": (0.6, -0.2, 0.25)}
    for name, off in offsets.items():
        o = bpy.data.objects.get(name)
        if o:
            o.location = centre + Vector(off); look_at(o, centre)


def lighting(scene):
    """Brighter than the Cycles studio: a soft top light and a faint world, for EEVEE and video."""
    for name, k in (("Key light", 1.6), ("Rim light", 1.6), ("Fill light", 2.0)):
        o = bpy.data.objects.get(name)
        if o:
            o.data.energy *= k
    for name in ("Rim light", "Fill light"):           # only the key light casts shadows: much faster in EEVEE
        o = bpy.data.objects.get(name)
        if o:
            o.data.use_shadow = False
    key = bpy.data.objects.get("Key light")
    if key and hasattr(key.data, "shadow_resolution_scale"):
        key.data.shadow_resolution_scale = 0.5
    l = bpy.data.lights.new("Top softbox", "AREA"); l.energy = 3.0; l.size = 0.8; l.color = (0.92, 0.94, 1.0)
    l.use_shadow = False
    o = bpy.data.objects.new("Top softbox", l); o.location = (0.21, -0.14, 0.55)
    scene.collection.objects.link(o)
    w = scene.world
    if w and w.node_tree:
        w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.012, 0.016, 1)


def plate_look(kit):
    """The clear polycarbonate plate reads as frosted glass on video."""
    m = bpy.data.materials.new("Video plate")
    if bpy.app.version < (5, 0, 0): m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.55, 0.58, 0.66, 1)
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Alpha"].default_value = 0.28
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    for o in kit.plate("left") + kit.plate("right"):
        o.data.materials.clear(); o.data.materials.append(m)


def eevee(scene):
    scene.render.engine = "BLENDER_EEVEE"
    ee = scene.eevee
    for attr, val in (("taa_render_samples", 8 if PREVIEW else 12), ("use_raytracing", True),
                      ("use_shadows", False), ("shadow_ray_count", 1), ("shadow_step_count", 4),
                      ("use_fast_gi", True), ("fast_gi_method", "GLOBAL_ILLUMINATION")):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, val)
            except Exception as e:
                log(f"eevee {attr}: {e}")
    if hasattr(ee, "ray_tracing_options"):
        ee.ray_tracing_options.resolution_scale = "2"
    k = 0.5 if PREVIEW else 1.0
    scene.render.resolution_x, scene.render.resolution_y = int(1920 * k), int(1080 * k)
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.use_persistent_data = True


def anchors_on(scene, named):
    """Screen positions (0..1, y down) of world points, as seen on the current frame."""
    out = {}
    for name, p in named.items():
        v = world_to_camera_view(scene, scene.camera, p)
        out[name] = [round(v.x, 4), round(1 - v.y, 4)]
    return out


def render(scene, frames, anchors=None):
    scene.frame_start, scene.frame_end = 1, frames
    d = OUT / CLIP
    d.mkdir(parents=True, exist_ok=True)
    bpy.context.view_layer.update()
    meta = {"frames": frames, "fps": FPS}
    if anchors:
        scene.frame_set(frames)
        meta["anchors"] = anchors_on(scene, anchors() if callable(anchors) else anchors)
    (OUT / f"{CLIP}.json").write_text(json.dumps(meta, indent=1))
    if STILL is not None:
        scene.frame_set(STILL)
        scene.render.filepath = str(OUT / f"{CLIP}-still.png")
        bpy.ops.render.render(write_still=True)
        log(f"{CLIP}: still {STILL}")
        return
    scene.render.filepath = str(d / "")
    scene.render.use_overwrite = False      # resumable: frames already on disk are skipped
    scene.render.use_placeholder = False
    if "--frames" in argv:
        scene.frame_end = int(argv[argv.index("--frames") + 1])
    import time
    t0 = time.time()
    bpy.ops.render.render(animation=True)
    log(f"{CLIP}: {(time.time() - t0) / (scene.frame_end - scene.frame_start + 1):.1f} s/frame")
    log(f"{CLIP}: {frames} frames")


# ---------------------------------------------------------------- clips

def hide_right(kit):
    set_visible([o for o in kit.meshes + kit.lights if not kit.is_left(o)], False)


def led_lights(kit, on):
    set_visible(kit.led_lights(), on)
    if not on:
        for o in kit.led_lights():
            o.data.energy = 0.0


def top_frame_set(kit):
    """What the top frame carries: the frame, the encoder and its nut, the OLED module and screen."""
    return (kit.case("top") + kit.refs(r"ENC101") + kit.refs(r"J101") +
            [o for o in kit.meshes if o.name.startswith(("left encoder nut", "OLED left screen"))])


def clip_hero(scene, kit):
    """Both halves, lit, the camera sweeping slowly round the front."""
    cam, tgt = make_camera(lens=50, fstop=5.6)
    lo, hi = wbox(kit.case("bottom", "left") + kit.case("bottom", "right"))
    c = (lo + hi) / 2
    size = hi - lo
    n = 300
    for f, a, h, d in ((1, -0.42, 0.62, 1.32), (n, 0.30, 0.50, 1.18)):
        off = Vector((math.sin(a) * size.x * d, -math.cos(a) * size.x * d, size.x * h))
        cam_key(cam, tgt, f, c + off, c + Vector((0, 0, 0.004)))
    ease([cam, tgt])
    render(scene, n)


def clip_explode(scene, kit):
    """The left half's layers lifting apart, bottom shell to keycaps."""
    hide_right(kit); led_lights(kit, False)
    set_visible([o for o in kit.meshes if o.name.startswith("Floor")], False)
    pcb = (kit.board_body() + [o for r, objs in kit.by_ref.items() if re.fullmatch(r"[A-Z]+1\d\d", r)
                               and not r.startswith(("SW1", "ENC", "J101")) for o in objs] +
           kit.sockets() + kit.refs(r"SW19[01]") + [o for o in kit.led_emitters() if kit.is_left(o)])
    pcb = [o for o in pcb if o not in top_frame_set(kit)]
    layers = [("Bottom shell", kit.case("bottom"), -55),
              ("PCB", pcb, 0),
              ("Switch plate", kit.plate(), 26),
              ("Switches", kit.switches(), 44),
              ("Top frame", top_frame_set(kit), 78),
              ("Keycaps", kit.keycaps(), 108)]
    c0 = centre_of(kit.case("bottom"))
    floor_at(c0.z - 0.2)
    rest = {name: centre_of(objs) for name, objs, _ in layers}
    edges = {}
    for name, objs, dz in layers:
        lo, hi = wbox(objs)
        edges[name] = Vector((hi.x, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2 + dz * MM))
        for o in roots(objs):
            r = o.location.copy()
            o.keyframe_insert("location", frame=20)
            o.location = r + world_to_local_delta(o, Vector((0, 0, dz * MM)))
            o.keyframe_insert("location", frame=110)
    ease([o for _, objs, _ in layers for o in roots(objs)])
    cam, tgt = make_camera(lens=40)
    aim = c0 + Vector((0, 0, 0.022))
    cam_key(cam, tgt, 1, aim + Vector((0.16, -0.36, 0.20)), aim)
    cam_key(cam, tgt, 110, aim + Vector((0.24, -0.44, 0.17)), aim + Vector((0, 0, 0.012)))
    ease([cam, tgt])
    studio_lights_around(c0)
    n = 180
    render(scene, n, anchors=edges)


def flip_left(kit, keep):
    """Turn the left half's board over (about the y axis) so its back faces up."""
    lo, hi = wbox([o for o in kit.board_body() if kit.is_left(o)])
    at = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0.8 * MM))
    piv = pivot_parent(keep, at)
    piv.rotation_euler.y = math.pi
    bpy.context.view_layer.update()
    return at


BACK_GROUPS = [
    ("back_power", r"Q101|R101", "close"),
    ("back_boost", r"U102|L101|C10[134]|R10[234]", "close"),
    ("back_buffer", r"U103|C10[25]|R105", "close"),
    ("back_thru", r"BT101|SW19[01]", "close"),
    ("back_controller", r"U101", "close"),
    ("back_leds", r"LED1\d\d", "wide"),
    ("back_diodes", r"D1\d\d", "wide"),
    ("back_sockets", "sockets", "wide"),
    ("back_header", r"J102", "close"),
]


def clip_back(scene, kit, which):
    """One group of parts going onto the back of the left board, earlier groups already on."""
    hide_right(kit); led_lights(kit, False)
    for name in ("left bottom", "left top", "left plate"):
        set_visible([o for o in kit.meshes if o.name.startswith(name)], False)
    set_visible(kit.keycaps() + kit.switches() + kit.refs(r"ENC101|J101|C1[1-4]\d") +
                [o for o in kit.meshes if o.name.startswith(("left encoder nut", "OLED left screen"))], False)
    set_visible(kit.led_emitters(), False)
    groups = []
    for name, pat, _ in BACK_GROUPS:
        groups.append((name, kit.sockets() if pat == "sockets" else kit.refs(pat)))
    idx = [g[0] for g in BACK_GROUPS].index(which)
    for i, (name, objs) in enumerate(groups):
        if i > idx:
            set_visible(objs, False)
    shown = [o for o in kit.board_body() if kit.is_left(o)] + [o for _, objs in groups[:idx + 1] for o in objs]
    at = flip_left(kit, shown + [o for _, objs in groups[idx + 1:] for o in objs])
    floor_at(-8 * MM)
    objs = groups[idx][1]
    mode = BACK_GROUPS[idx][2]
    c = centre_of(objs)
    n = 150 if mode == "close" else 170
    if which == "back_leds":                               # in number order, as they are soldered
        order = sorted(roots(objs), key=lambda o: part_ref(o))
        for k, o in enumerate(order):
            f0 = 15 + k * 3
            move(o, Vector((0, 0, 10 * MM)), f0, f0 + 12)
    elif which in ("back_diodes", "back_sockets"):
        order = sorted(roots(objs), key=lambda o: (-o.matrix_world.translation.y, o.matrix_world.translation.x))
        for k, o in enumerate(order):
            f0 = 15 + k * 3
            move(o, Vector((0, 0, 12 * MM)), f0, f0 + 12)
    else:
        for k, o in enumerate(roots(objs)):
            f0 = 15 + k * 6
            move(o, Vector((0, 0, (30 if which == "back_controller" else 16) * MM)), f0, f0 + 24)
    ease(roots(objs))
    bc = Vector((at.x, at.y, 0.0))
    studio_lights_around(Vector((bc.x, bc.y, 0)))
    cam, tgt = make_camera(lens=50, fstop=None if mode == "wide" else 9.0)
    if mode == "close":
        cam_key(cam, tgt, 1, c + Vector((0.030, -0.060, 0.085)), c)
        cam_key(cam, tgt, n, c + Vector((0.015, -0.068, 0.095)), c)
        flash(c + Vector((0, 0, 0.012)), 18, length=40, energy=0.35, radius=0.01)
    else:
        aim = Vector((bc.x, bc.y, 0.002))
        cam_key(cam, tgt, 1, aim + Vector((0.05, -0.20, 0.24)), aim)
        cam_key(cam, tgt, n, aim + Vector((0.00, -0.22, 0.26)), aim)
    ease([cam, tgt])
    render(scene, n, anchors={"group": c, "board": bc})


def clip_front(scene, kit):
    """The plate settling on the standoffs, then the switches, then the keycaps, then the LEDs on."""
    hide_right(kit)
    set_visible(kit.case("bottom") + top_frame_set(kit) + kit.refs(r"C1[1-4]\d"), False)
    drop(kit.plate(), 10, 45, height=30 * MM)
    sw = sorted(kit.switches(), key=lambda o: (-centre_of([o]).y, centre_of([o]).x))
    for k, o in enumerate(sw):
        f0 = 55 + k * 2
        move(o, Vector((0, 0, 22 * MM)), f0, f0 + 16)
    caps = sorted(kit.keycaps(), key=lambda o: (-o.location.y, o.location.x))
    for k, o in enumerate(caps):
        f0 = 135 + k * 2
        move(o, Vector((0, 0, 22 * MM)), f0, f0 + 16)
    ease(roots(kit.plate() + sw) + caps)
    c = centre_of(kit.plate())
    floor_at(-6 * MM)
    studio_lights_around(Vector((c.x, c.y, 0)))
    cam, tgt = make_camera(lens=45)
    cam_key(cam, tgt, 1, c + Vector((0.10, -0.30, 0.26)), c)
    cam_key(cam, tgt, 260, c + Vector((0.16, -0.32, 0.20)), c + Vector((0, 0, 0.006)))
    ease([cam, tgt])
    render(scene, 260)


def clip_close(scene, kit):
    """The plate-and-PCB unit into the bottom shell, then the top frame, then the keycaps."""
    hide_right(kit); led_lights(kit, False)
    set_visible(kit.refs(r"C1[1-4]\d"), False)
    caps = kit.keycaps()
    top = top_frame_set(kit)
    unit = [o for o in kit.meshes if kit.is_left(o) and o not in top and o not in caps and o.visible_get()
            and not o.name.startswith(("left bottom", "Floor", "left wedge"))]
    unit = [o for o in unit if o.users_collection[0].name.split(".")[0] in ("Board", "Plate", "LEDs")]
    drop(unit, 15, 75, height=45 * MM)
    drop(top, 85, 140, height=45 * MM)
    for k, o in enumerate(sorted(caps, key=lambda o: (-o.location.y, o.location.x))):
        f0 = 150 + k * 2
        move(o, Vector((0, 0, 20 * MM)), f0, f0 + 14)
    ease(roots(unit) + roots(top) + caps)
    c = centre_of(kit.case("bottom"))
    floor_at(wbox(kit.case("bottom"))[0].z)
    studio_lights_around(c)
    cam, tgt = make_camera(lens=42)
    cam_key(cam, tgt, 1, c + Vector((0.20, -0.36, 0.30)), c + Vector((0, 0, 0.02)))
    cam_key(cam, tgt, 240, c + Vector((0.12, -0.38, 0.22)), c)
    ease([cam, tgt])
    render(scene, 240)


def clip_tent(scene, kit):
    """Both halves lowered onto their wedges."""
    wedges = kit.wedge("left") + kit.wedge("right")
    set_visible(wedges, True)
    lo_all, hi_all = wbox(kit.case("bottom", "left") + kit.case("bottom", "right"))
    floor_z = lo_all.z
    for side, sign in (("left", -1), ("right", 1)):
        w = kit.wedge(side)[0]
        pts = [w.matrix_world @ Vector(c) for c in w.bound_box]
        x = min(p.x for p in pts) if side == "left" else max(p.x for p in pts)
        pivot = Vector((x, 0, max(p.z for p in pts) - w["tent_edge"]))
        half = [o for o in kit.meshes + kit.lights if kit.is_left(o) == (side == "left")]
        body = [o for o in half if o not in kit.wedge(side) and not o.name.startswith("Floor")]
        e_w = pivot_parent(kit.wedge(side), pivot)
        e_b = pivot_parent(body, pivot)
        ang = sign * math.radians(w["tent_angle"])
        for e in (e_w, e_b):
            e.location = Vector((x, 0, floor_z)); e.rotation_euler.y = ang
        # the half starts flat and high, then settles onto its wedge
        e_b.location.z = floor_z + 0.07; e_b.rotation_euler.y = 0
        e_b.keyframe_insert("location", frame=1); e_b.keyframe_insert("rotation_euler", frame=1)
        e_b.keyframe_insert("location", frame=25); e_b.keyframe_insert("rotation_euler", frame=25)
        e_b.location.z = floor_z; e_b.rotation_euler.y = ang
        e_b.keyframe_insert("location", frame=95); e_b.keyframe_insert("rotation_euler", frame=95)
        ease([e_b])
    bpy.context.view_layer.update()
    floor_at(floor_z)
    lo, hi = wbox(kit.case("bottom", "left") + kit.case("bottom", "right"))
    c = (lo + hi) / 2
    size = hi - lo
    cam, tgt = make_camera(lens=32, fstop=8.0)
    cam_key(cam, tgt, 1, c + Vector((0.12, -size.x * 1.55, size.x * 0.62)), c + Vector((0, 0, 0.01)))
    cam_key(cam, tgt, 180, c + Vector((-0.12, -size.x * 1.45, size.x * 0.52)), c + Vector((0, 0, 0.01)))
    ease([cam, tgt])
    render(scene, 180)


def clip_wave(scene, kit):
    """The hero view, a rainbow running across the LEDs."""
    import colorsys
    leds = [o for o in kit.col.all_objects if "led_color" in o.keys()]
    lights = {o.name.removesuffix(" light"): o.data for o in kit.led_lights()}
    xs = [o.location.x for o in leds]
    x0, span = min(xs), max(xs) - min(xs)
    n = 150
    for f in range(1, n + 2, 3):
        for o in leds:
            hue = ((o.location.x - x0) / span * 0.7 - (f - 1) / n) % 1.0
            col = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
            o["led_color"] = (*col, 1.0); o.keyframe_insert('["led_color"]', frame=f)
    cam, tgt = make_camera(lens=50, fstop=5.6)
    lo, hi = wbox(kit.case("bottom", "left") + kit.case("bottom", "right"))
    c = (lo + hi) / 2; size = hi - lo
    cam_key(cam, tgt, 1, c + Vector((0.02, -size.x * 1.05, size.x * 0.75)), c)
    cam_key(cam, tgt, n, c + Vector((-0.02, -size.x * 0.98, size.x * 0.70)), c)
    ease([cam, tgt])
    render(scene, n)


def main():
    scene = bpy.context.scene
    eevee(scene)
    kit = Kit(localise())
    lighting(scene)
    plate_look(kit)
    led_lights(kit, False)          # per-LED point lights off everywhere: the emitters still glow
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
    log(f"clip {CLIP}")
    if CLIP == "hero":
        clip_hero(scene, kit)
    elif CLIP == "explode":
        clip_explode(scene, kit)
    elif CLIP.startswith("back_"):
        clip_back(scene, kit, CLIP)
    elif CLIP == "front":
        clip_front(scene, kit)
    elif CLIP == "close":
        clip_close(scene, kit)
    elif CLIP == "tent":
        clip_tent(scene, kit)
    elif CLIP == "wave":
        clip_wave(scene, kit)
    else:
        sys.exit(f"unknown clip {CLIP}")


main()
