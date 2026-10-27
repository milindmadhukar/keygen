"""Blender side of tools/gen_blend.py; run inside Blender, not on its own:

    blender -b --factory-startup --python tools/blend_scene.py -- <tmpdir> <repo root> [--reset-studio]

<tmpdir> holds scene.json and board.glb from gen_blend.py. Builds every part in a "Keygen"
collection with its material and saves blender/keygen-parts.blend. If blender/keygen.blend is
missing (or --reset-studio), writes it too: the "Keygen" collection linked from the parts file,
with a camera, lights, a floor, Cycles and a bloom compositor.

Frame: metres, KiCad x -> x and KiCad y -> -y (the GLB's and the case STLs' frame), z up with the
board's underside at 0. The case STLs have the PCB's top face at z = 0, so they are lifted to it.
"""
import colorsys, json, math, re, sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
TMP, ROOT = Path(argv[0]), Path(argv[1])
RESET = "--reset-studio" in argv
PARTS = ROOT / "blender/keygen-parts.blend"
STUDIO = ROOT / "blender/keygen.blend"
SHAPES = ROOT / "pcb/lib/keygen.3dshapes"
MM = 0.001

# Per-key LED colours: "gradient" (lavender at the outer columns to cyan at the inner ones),
# "lavender", "white" or "rainbow". The brightness is W of light per LED.
LED_SCHEME = "gradient"
LED_POWER = 0.06
LED_SIZE = (1.6, 1.6, 0.5)     # mm, the emitting face of the SK6812MINI-E in its cut-out
LED_LIGHT_Z = 3.0              # mm above the plate: each LED's light, where it leaves the switch's LED window
OLED_PX = (128, 64)
OLED_POWER = 3.0               # emission strength of a lit OLED pixel
OLED_FILL = 0.84               # a pixel's lit share of its pitch, each way: the dark grid between pixels


def log(msg):
    print(f"keygen: {msg}", flush=True)


# ---------------------------------------------------------------- materials

def material(name, **inputs):
    """A Principled BSDF material; inputs by socket name. Returns (material, nodes, links, bsdf)."""
    m = bpy.data.materials.new(name)
    if bpy.app.version < (5, 0, 0): m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    for k, v in inputs.items():
        bsdf.inputs[k].default_value = (*v, 1.0) if isinstance(v, tuple) and len(v) == 3 else v
    return m, nt.nodes, nt.links, bsdf


def bump(nodes, links, bsdf, height, strength, distance):
    b = nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    links.new(height, b.inputs["Height"])
    links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return b


def object_coords(nodes):
    return nodes.new("ShaderNodeTexCoord").outputs["Object"]


def noise(nodes, links, scale, detail=2.0):
    n = nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    links.new(object_coords(nodes), n.inputs["Vector"])
    return n


def smoke_pbt():
    """Translucent smoke PBT: clear-ish surface with fine texture, darkened by absorption inside, so
    thin walls pass the LED light and thick parts read black."""
    m, nodes, links, bsdf = material("Keycap smoke PBT", **{
        "Base Color": (0.26, 0.26, 0.28), "Roughness": 0.55, "IOR": 1.53, "Transmission Weight": 1.0})
    bump(nodes, links, bsdf, noise(nodes, links, 9000.0, 4.0).outputs["Fac"], 0.08, 0.00002)
    vol = nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = (0.08, 0.08, 0.085, 1)
    vol.inputs["Density"].default_value = 450.0
    links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    return m


def petg_black():
    """Black PETG, 3D-printed: satin, with 0.2 mm layer lines along z."""
    m, nodes, links, bsdf = material("Case black PETG", **{
        "Base Color": (0.012, 0.012, 0.013), "Roughness": 0.45})
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(object_coords(nodes), sep.inputs["Vector"])
    mul = nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / (0.2 * MM)
    links.new(sep.outputs["Z"], mul.inputs[0])
    sin = nodes.new("ShaderNodeMath"); sin.operation = "SINE"
    links.new(mul.outputs[0], sin.inputs[0])
    bump(nodes, links, bsdf, sin.outputs[0], 0.25, 0.00002)
    return m


def polycarbonate_clear():
    """The switch plate: clear polycarbonate sheet, glossy faces with a faint blue-grey tint."""
    return principled("Plate clear polycarbonate", **{
        "Base Color": (0.93, 0.96, 0.97), "Roughness": 0.03, "IOR": 1.585, "Transmission Weight": 1.0})


def principled(name, **inputs):
    return material(name, **inputs)[0]


def led_material():
    m, nodes, links, bsdf = material("LED", **{"Base Color": (0, 0, 0), "Emission Strength": 40.0})
    attr = nodes.new("ShaderNodeAttribute"); attr.attribute_type = "OBJECT"; attr.attribute_name = "led_color"
    links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"])
    return m


def knob_aluminium():
    m, nodes, links, bsdf = material("Knob brushed aluminium", **{
        "Base Color": (0.80, 0.81, 0.83), "Metallic": 1.0, "Roughness": 0.28, "Anisotropic": 0.8})
    t = nodes.new("ShaderNodeTangent"); t.direction_type = "RADIAL"; t.axis = "Z"
    links.new(t.outputs["Tangent"], bsdf.inputs["Tangent"])
    return m


def oled_material(side, rows):
    """An OLED's active area showing its status screen: black glass, the lit pixels white, with the
    dark gaps between pixels. rows: the screen's pixel rows, top first, "1" lit."""
    w, h = OLED_PX
    img = bpy.data.images.new(f"OLED {side}", w, h, alpha=False)
    px = []
    for row in reversed(rows):                                      # Blender's images start bottom left
        for c in row:
            px += [1.0, 1.0, 1.0, 1.0] if c == "1" else [0.0, 0.0, 0.0, 1.0]
    img.pixels = px
    img.pack()
    m, nodes, links, bsdf = material(f"OLED {side} screen", **{
        "Base Color": (0.004, 0.004, 0.005), "Roughness": 0.03, "Coat Weight": 1.0,
        "Emission Color": (0.95, 0.97, 1.0), "Emission Strength": OLED_POWER})
    uv = nodes.new("ShaderNodeTexCoord").outputs["UV"]
    tex = nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Closest"
    links.new(uv, tex.inputs["Vector"])
    cells = nodes.new("ShaderNodeVectorMath"); cells.operation = "MULTIPLY"
    cells.inputs[1].default_value = (w, h, 0)
    links.new(uv, cells.inputs[0])
    frac = nodes.new("ShaderNodeVectorMath"); frac.operation = "FRACTION"
    links.new(cells.outputs["Vector"], frac.inputs[0])
    off = nodes.new("ShaderNodeVectorMath"); off.operation = "SUBTRACT"
    off.inputs[1].default_value = (0.5, 0.5, 0)
    links.new(frac.outputs["Vector"], off.inputs[0])
    ab = nodes.new("ShaderNodeVectorMath"); ab.operation = "ABSOLUTE"
    links.new(off.outputs["Vector"], ab.inputs[0])
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(ab.outputs["Vector"], sep.inputs["Vector"])
    edge = nodes.new("ShaderNodeMath"); edge.operation = "MAXIMUM"
    links.new(sep.outputs["X"], edge.inputs[0]); links.new(sep.outputs["Y"], edge.inputs[1])
    inside = nodes.new("ShaderNodeMath"); inside.operation = "LESS_THAN"
    inside.inputs[1].default_value = OLED_FILL / 2
    links.new(edge.outputs[0], inside.inputs[0])
    lit = nodes.new("ShaderNodeMath"); lit.operation = "MULTIPLY"
    links.new(tex.outputs["Color"], lit.inputs[0]); links.new(inside.outputs[0], lit.inputs[1])
    strength = nodes.new("ShaderNodeMath"); strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = OLED_POWER
    links.new(lit.outputs[0], strength.inputs[0])
    links.new(strength.outputs[0], bsdf.inputs["Emission Strength"])
    return m


def materials():
    return {
        "keycap": smoke_pbt(),
        "case": petg_black(),
        "plate": polycarbonate_clear(),
        "mask": principled("PCB black soldermask", **{"Base Color": (0.008, 0.008, 0.01), "Roughness": 0.3,
                                                      "Coat Weight": 0.6, "Coat Roughness": 0.1}),
        "silk": principled("PCB white silkscreen", **{"Base Color": (0.85, 0.85, 0.83), "Roughness": 0.65}),
        "hasl": principled("PCB HASL", **{"Base Color": (0.86, 0.86, 0.88), "Metallic": 1.0, "Roughness": 0.22}),
        "fr4": principled("PCB FR-4 core", **{"Base Color": (0.30, 0.27, 0.13), "Roughness": 0.6}),
        "switch_top": principled("Switch top, clear PC tinted lavender", **{
            "Base Color": (0.78, 0.68, 0.95), "Roughness": 0.04, "IOR": 1.58, "Transmission Weight": 1.0}),
        "switch_bottom": principled("Switch bottom, nylon", **{
            "Base Color": (0.62, 0.52, 0.85), "Roughness": 0.45, "Transmission Weight": 0.55,
            "Subsurface Weight": 0.3}),
        "stem": principled("Switch stem, lavender POM", **{
            "Base Color": (0.55, 0.40, 0.85), "Roughness": 0.35, "Subsurface Weight": 0.25}),
        "knob": knob_aluminium(),
        "oled_glass": principled("OLED glass", **{"Base Color": (0.01, 0.01, 0.012), "Roughness": 0.03,
                                                  "Coat Weight": 1.0}),
        "oled_active": principled("OLED active area, off", **{"Base Color": (0.004, 0.004, 0.005),
                                                                "Roughness": 0.03, "Coat Weight": 1.0}),
        "led": led_material(),
    }


# ---------------------------------------------------------------- the board (GLB)

def near(a, b, tol=0.02):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def srgb(c):
    """KiCad colour (sRGB, 0..1) to the linear value the GLB holds."""
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def role(ref, keys, rgb, alpha):
    """What a GLB material on a part of `ref` stands for, or None to keep KiCad's colour."""
    if ref in keys:                                       # the MX switch STEP (the socket keeps its colours)
        if near(rgb, srgb((0.533, 0.235, 0.0))): return "stem"
        if near(rgb, (1.0, 1.0, 1.0)): return "switch_top"
        if near(rgb, srgb((0.098, 0.098, 0.098)), 0.004): return "switch_bottom"
    elif ref.startswith("ENC"):
        if near(rgb, srgb((0xB9 / 255, 0xBD / 255, 0xC4 / 255))): return "knob"
    elif ref.startswith("J"):
        if near(rgb, srgb((0x2A / 255, 0x2C / 255, 0x31 / 255)), 0.004): return "oled_glass"
        if near(rgb, srgb((0x05 / 255, 0x05 / 255, 0x06 / 255)), 0.002): return "oled_active"
    elif not re.match(r"[A-Z]+\d+$", ref):              # the board's own layers (_<board>_copper, ...)
        if alpha < 0.99: return "mask"
        if near(rgb, (0.7, 0.61, 0.0), 0.05) or near(rgb, (0.5, 0.5, 0.5)): return "hasl"
        if min(rgb) > 0.9: return "silk"
        if near(rgb, (0.427, 0.455, 0.294), 0.05): return "fr4"
    return None


def part_ref(o):
    """The reference (SW133, ...) of the part a GLB object belongs to: its ancestor just under the
    importer's root node, without Blender's .001 suffix."""
    while o.parent and o.parent.parent:
        o = o.parent
    return o.name.split(".")[0]


def import_board(col, mats, keys):
    layer = bpy.context.view_layer.layer_collection.children["Keygen"].children[col.name]
    bpy.context.view_layer.active_layer_collection = layer
    bpy.ops.import_scene.gltf(filepath=str(TMP / "board.glb"))
    swapped, fr4_top = 0, None
    done = set()
    for o in col.all_objects:
        if o.type != "MESH" or o.data in done:
            continue
        done.add(o.data)
        ref = part_ref(o)
        for i, m in enumerate(o.data.materials):
            if not m or not m.node_tree or "Principled BSDF" not in m.node_tree.nodes:
                continue
            b = m.node_tree.nodes["Principled BSDF"]
            rgb = tuple(b.inputs["Base Color"].default_value[:3])
            r = role(ref, keys, rgb, b.inputs["Alpha"].default_value)
            if r:
                o.data.materials[i] = mats[r]; swapped += 1
    bpy.context.view_layer.update()
    for o in col.all_objects:
        if o.type == "MESH" and any(m is mats["fr4"] for m in o.data.materials):
            z = max((o.matrix_world @ Vector(c)).z for c in o.bound_box)
            fr4_top = z if fr4_top is None else max(fr4_top, z)
    log(f"board: {len(col.all_objects)} objects from the GLB, {swapped} materials replaced")
    return fr4_top


def oled_screens(col, mats, screens):
    """Lay each OLED's status screen over its module's active area: a plane just above it, the
    image upright to the typist (its top toward the back edge, +y)."""
    found = {}
    for o in col.all_objects:
        if o.type != "MESH" or mats["oled_active"] not in list(o.data.materials):
            continue
        ref = part_ref(o)
        idx = list(o.data.materials).index(mats["oled_active"])
        pts = [o.matrix_world @ o.data.vertices[v].co for p in o.data.polygons if p.material_index == idx
               for v in p.vertices]
        found.setdefault(ref, []).extend(pts)
    if len(found) != 2:
        raise SystemExit(f"keygen: expected two OLED active areas in the GLB, found {sorted(found)}")
    for ref, pts in sorted(found.items()):
        side = "left" if ref[-3] == "1" else "right"
        x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
        y0, y1 = min(p.y for p in pts), max(p.y for p in pts)
        z = max(p.z for p in pts) + 0.005 * MM
        if not 1.9 < (x1 - x0) / (y1 - y0) < 2.1:
            raise SystemExit(f"keygen: {ref}'s active area is {(x1 - x0) / MM:.1f} x {(y1 - y0) / MM:.1f} mm, "
                             "not a 2:1 screen lying along x")
        me = bpy.data.meshes.new(f"OLED {side} screen")
        me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new(name="UVMap")
        for loop, co in zip(uv.data, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop.uv = co
        me.materials.append(oled_material(side, screens[side]))
        o = bpy.data.objects.new(f"OLED {side} screen", me)
        col.objects.link(o)
    log(f"OLEDs: the status screens on {', '.join(sorted(found))}")


# ---------------------------------------------------------------- STL parts

def import_stl(path, col, name):
    bpy.ops.wm.stl_import(filepath=str(path))
    o = bpy.context.selected_objects[0]
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    o.name = o.data.name = name
    o.data.transform(Matrix.Scale(MM, 4))                 # the STLs are in mm
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.set_sharp_from_angle(angle=math.radians(30))
    return o


def keycap_mesh(size):
    col = bpy.data.collections.new("_tmp"); bpy.context.scene.collection.children.link(col)
    o = import_stl(SHAPES / f"Keycap_DSA_{size}u.stl", col, f"Keycap DSA {size}u")
    mesh = o.data
    bpy.data.objects.remove(o); bpy.data.collections.remove(col)
    return mesh


# ---------------------------------------------------------------- LEDs

def led_colour(t):
    """t: 0 at the outer column, 1 at the inner one."""
    if LED_SCHEME == "white":
        return (1.0, 0.95, 0.9)
    if LED_SCHEME == "lavender":
        return colorsys.hsv_to_rgb(0.74, 0.45, 1.0)
    if LED_SCHEME == "rainbow":
        return colorsys.hsv_to_rgb(0.83 * t, 1.0, 1.0)
    return colorsys.hsv_to_rgb(0.76 - 0.26 * t, 0.65, 1.0)      # gradient: lavender -> cyan


def box_mesh(name, sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me


# ---------------------------------------------------------------- parts file

def build_parts():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    data = json.loads((TMP / "scene.json").read_text())
    root = bpy.data.collections.new("Keygen"); bpy.context.scene.collection.children.link(root)
    cols = {}
    for name in ("Board", "Case", "Plate", "Keycaps", "LEDs"):
        cols[name] = bpy.data.collections.new(name); root.children.link(cols[name])
    mats = materials()

    keys = {k["ref"] for k in data["keys"]}
    top = import_board(cols["Board"], mats, keys)
    if top is None:
        raise SystemExit("keygen: no FR-4 board body found in the GLB")
    log(f"board top face at z = {top / MM:.3f} mm")
    oled_screens(cols["Board"], mats, data["oled"])

    for side in ("left", "right"):
        for part, col, mat in (("bottom", "Case", "case"), ("top", "Case", "case"), ("plate", "Plate", "plate")):
            o = import_stl(ROOT / f"case/{part}/stl/keygen-{side}-{part}.stl", cols[col], f"{side} {part}")
            o.location.z = top
            o.data.materials.append(mats[mat])
    log("case: bottom shells, top frames and plates")

    caps = {s: keycap_mesh(s) for s in sorted({k["size"] for k in data["keys"]})}
    for me in caps.values():
        me.materials.append(mats["keycap"])
    cap_z = top + (data["plate_top"] + data["cap_skirt"]) * MM
    for k in data["keys"]:
        o = bpy.data.objects.new(f"Keycap {k['ref']}", caps[k["size"]])
        o.location = (k["x"] * MM, -k["y"] * MM, cap_z)
        o.rotation_euler.z = math.radians(k["rot"] + (180 if k["back"] else 0))
        cols["Keycaps"].objects.link(o)
    log(f"keycaps: {len(data['keys'])} ({', '.join(f'{s}u' for s in caps)})")

    xs = [l["x"] for l in data["leds"]]
    mid = (min(xs) + max(xs)) / 2
    half = max(abs(x - mid) for x in xs)
    emitter = box_mesh("LED emitter", *(s * MM for s in LED_SIZE))
    emitter.materials.append(mats["led"])
    for l in data["leds"]:
        c = led_colour(1 - abs(l["x"] - mid) / half)
        o = bpy.data.objects.new(l["ref"], emitter)
        o.location = (l["x"] * MM, -l["y"] * MM, top - LED_SIZE[2] / 2 * MM)
        o.rotation_euler.z = math.radians(l["rot"])
        o["led_color"] = (*c, 1.0)
        cols["LEDs"].objects.link(o)
        light = bpy.data.lights.new(f"{l['ref']} light", "POINT")
        light.color = c; light.energy = LED_POWER; light.shadow_soft_size = 0.8 * MM
        lo = bpy.data.objects.new(f"{l['ref']} light", light)
        lo.location = (l["x"] * MM, -l["y"] * MM, top + (data["plate_top"] + LED_LIGHT_Z) * MM)
        cols["LEDs"].objects.link(lo)
    log(f"LEDs: {len(data['leds'])}, scheme {LED_SCHEME}")

    bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"
    bpy.ops.wm.save_as_mainfile(filepath=str(PARTS), compress=True)
    log(f"wrote {PARTS.relative_to(ROOT)}")


# ---------------------------------------------------------------- studio file

def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def compositor(scene):
    """A bloom on the render, so the LEDs glow."""
    scene.render.use_compositing = True
    if hasattr(scene, "compositing_node_group"):                     # Blender 5
        nt = bpy.data.node_groups.new("Keygen bloom", "CompositorNodeTree")
        scene.compositing_node_group = nt
        nt.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        out = nt.nodes.new("NodeGroupOutput")
    else:
        scene.use_nodes = True
        nt = scene.node_tree; nt.nodes.clear()
        out = nt.nodes.new("CompositorNodeComposite")
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    settings = {"Type": "Bloom", "Quality": "High", "Threshold": 1.0, "Strength": 0.6, "Size": 0.5}
    for k, v in settings.items():
        if k in glare.inputs:
            glare.inputs[k].default_value = v
        elif k == "Type":
            glare.glare_type = "BLOOM"
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
    nt.links.new(glare.outputs["Image"], out.inputs[0])


def build_studio():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(STUDIO))              # so the library path can be relative
    scene = bpy.context.scene
    with bpy.data.libraries.load(str(PARTS), link=True, relative=True) as (src, dst):
        dst.collections = ["Keygen"]
    keygen = dst.collections[0]
    inst = bpy.data.objects.new("Keygen", None)
    inst.instance_type = "COLLECTION"; inst.instance_collection = keygen
    scene.collection.objects.link(inst)

    case = keygen.children["Case"]                     # frame on the case: the outermost part
    pts = [o.matrix_world @ Vector(c) for o in case.all_objects if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre, size = (lo + hi) / 2, hi - lo

    floor = bpy.data.objects.new("Floor", bpy.data.meshes.new("Floor"))
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.5); bm.to_mesh(floor.data); bm.free()
    floor.location = (centre.x, centre.y, lo.z)
    floor.data.materials.append(principled("Floor", **{"Base Color": (0.02, 0.02, 0.022), "Roughness": 0.6}))
    scene.collection.objects.link(floor)

    target = bpy.data.objects.new("Camera target", None)
    target.location = centre; scene.collection.objects.link(target)
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    cam.data.lens = 50
    cam.location = centre + Vector((0, -size.x * 1.3, size.x * 0.8))
    look_at(cam, centre)
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = target; cam.data.dof.aperture_fstop = 5.6
    scene.collection.objects.link(cam); scene.camera = cam

    for name, offset, energy, area in (("Key light", (-0.35, -0.45, 0.55), 2.5, 0.5),
                                       ("Rim light", (0.3, 0.5, 0.3), 3.0, 0.35),
                                       ("Fill light", (0.6, -0.2, 0.25), 0.4, 0.6)):
        l = bpy.data.lights.new(name, "AREA"); l.energy = energy; l.size = area
        o = bpy.data.objects.new(name, l); o.location = centre + Vector(offset); look_at(o, centre)
        scene.collection.objects.link(o)

    world = bpy.data.worlds.new("Studio")
    if bpy.app.version < (5, 0, 0): world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.003, 0.003, 0.0035, 1)
    scene.world = world

    scene.render.engine = "CYCLES"
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 2400, 1350
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.unit_settings.length_unit = "MILLIMETERS"
    compositor(scene)
    for screen in bpy.data.screens:     # open in the camera view, EEVEE preview lit by the scene; F12 renders in Cycles
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"
                        space.shading.use_scene_lights = space.shading.use_scene_world = True
                        space.region_3d.view_perspective = "CAMERA"
                        space.clip_start = 0.001
    bpy.ops.wm.save_as_mainfile(filepath=str(STUDIO), compress=True)
    log(f"wrote {STUDIO.relative_to(ROOT)}")


build_parts()
if RESET or not STUDIO.exists():
    build_studio()
