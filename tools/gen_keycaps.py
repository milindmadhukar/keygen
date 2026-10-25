#!/usr/bin/env python3
"""Write the DSA keycap models, 1u and 1.25u, from KeyV2 (lib/KeyV2, rendered by OpenSCAD):

pcb/lib/keygen.3dshapes/Keycap_DSA_<size>u.stl   the cap in mm, skirt bottom at z = 0, centred: for Blender
pcb/lib/keygen.3dshapes/Keycap_<size>u.wrl       the same cap for KiCad's 3D view and the renders, in
                                                 smoke black, lifted so that the switch footprint's model
                                                 offset (CAP_MODEL_Z above the PCB) puts its skirt
                                                 CAP_SKIRT above the plate, where the case expects it

The caps are KeyV2's DSA (row 3, uniform) with a cherry stem, no supports and no legends.
Needs an OpenSCAD development snapshot (2025 or later; KeyV2 calls functions held in $ variables,
which 2021.01 cannot), as `openscad` or $KEYGEN_OPENSCAD:

    python3 tools/gen_keycaps.py
"""
import math, os, re, struct, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C

ROOT = Path(__file__).resolve().parent.parent
KEYV2 = ROOT / "lib/KeyV2"
SHAPES = ROOT / "pcb/lib/keygen.3dshapes"
SIZES = ("1", "1.25")
OPENSCAD = os.environ.get("KEYGEN_OPENSCAD", "openscad")
SKIRT_Z = C.PLATE_TOP + C.CAP_SKIRT - C.g.CAP_MODEL_Z      # skirt bottom above the model origin
SMOKE = dict(diffuseColor="0.06 0.06 0.07", specularColor="0.25 0.25 0.27", shininess="0.3",
             transparency="0")
CREASE = math.radians(35)     # KiCad smooths across edges flatter than this


def scad(size):
    # settings go through let(): reassigning KeyV2's $ settings at the top level undoes dsa_row() and u()
    return (f'include <{KEYV2}/includes.scad>\n'
            f'dsa_row(3) u({size}) let($stem_type = "cherry", $support_type = "disable", '
            '$stem_support_type = "disable") key();\n')


def render(size, tmp):
    src, out = tmp / f"cap_{size}.scad", tmp / f"cap_{size}.stl"
    src.write_text(scad(size))
    subprocess.run([OPENSCAD, "--backend=manifold", "--export-format", "binstl", "-o", str(out), str(src)],
                   check=True, capture_output=True)
    return out.read_bytes()


def triangles(stl):
    """Triangles of a binary STL as ((x, y, z) * 3) tuples."""
    n = struct.unpack_from("<I", stl, 80)[0]
    return [struct.unpack_from("<9f", stl, 84 + 50 * i + 12) for i in range(n)]


def centred(tris):
    """The cap centred in x and y, its skirt bottom at z = 0."""
    xs = [t[i] for t in tris for i in (0, 3, 6)]
    ys = [t[i] for t in tris for i in (1, 4, 7)]
    zs = [t[i] for t in tris for i in (2, 5, 8)]
    dx, dy, dz = -(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)
    return [tuple(v + (dx, dy, dz)[i % 3] for i, v in enumerate(t)) for t in tris]


def binary_stl(tris, name):
    out = bytearray(name.encode()[:80].ljust(80, b"\0")) + struct.pack("<I", len(tris))
    for t in tris:
        a, b, c = (t[0:3], t[3:6], t[6:9])
        u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        l = math.hypot(*n) or 1.0
        out += struct.pack("<12fH", *(x / l for x in n), *t, 0)
    return bytes(out)


def wrl(tris, z0):
    """VRML 2 in KiCad's units (0.1 in), shared vertices so creaseAngle can smooth the curved sides."""
    index, pts, faces = {}, [], []
    for t in tris:
        f = []
        for k in range(3):
            p = (round(t[3 * k], 4), round(t[3 * k + 1], 4), round(t[3 * k + 2] + z0, 4))
            if p not in index:
                index[p] = len(pts); pts.append(p)
            f.append(index[p])
        if len(set(f)) == 3:
            faces.append(f)
    mat = " ".join(f"{k} {v}" for k, v in SMOKE.items())
    return ("#VRML V2.0 utf8\n"
            f"Shape {{ appearance Appearance {{ material Material {{ {mat} }} }}\n"
            f"geometry IndexedFaceSet {{ creaseAngle {CREASE:.3f} solid FALSE\n"
            "coord Coordinate { point [\n" + ",\n".join(f"{x/2.54:.5f} {y/2.54:.5f} {z/2.54:.5f}" for x, y, z in pts)
            + "] }\ncoordIndex [\n" + ",\n".join(f"{a},{b},{c},-1" for a, b, c in faces) + "] } }\n")


def main():
    if not (KEYV2 / "includes.scad").exists():
        sys.exit("lib/KeyV2 is missing: git submodule update --init lib/KeyV2")
    v = subprocess.run([OPENSCAD, "--version"], capture_output=True, text=True)
    if int((re.search(r"(\d{4})\.", v.stdout + v.stderr) or [0, 0])[1]) < 2025:
        sys.exit(f"{OPENSCAD} is too old for KeyV2 ({(v.stdout + v.stderr).strip()}); install a development snapshot "
                 "from https://openscad.org/downloads.html#snapshots, or point $KEYGEN_OPENSCAD at one")
    with tempfile.TemporaryDirectory() as tmp:
        for size in SIZES:
            tris = centred(triangles(render(size, Path(tmp))))
            (SHAPES / f"Keycap_DSA_{size}u.stl").write_bytes(binary_stl(tris, f"Keygen DSA {size}u keycap (KeyV2)"))
            (SHAPES / f"Keycap_{size}u.wrl").write_text(wrl(tris, SKIRT_Z))
            w = max(t[i] for t in tris for i in (0, 3, 6)) * 2
            h = max(t[i] for t in tris for i in (2, 5, 8))
            print(f"wrote Keycap_DSA_{size}u.stl, Keycap_{size}u.wrl: {len(tris)} triangles, "
                  f"{w:.2f} mm wide, {h:.2f} mm tall, skirt {C.CAP_SKIRT:g} mm above the plate")


if __name__ == "__main__":
    main()
