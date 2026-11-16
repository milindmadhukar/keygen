#!/usr/bin/env python3
"""Make the Bambu Studio print project for the case: case/3mf/keygen-case.3mf.

Four plates, one part each: both bottom shells floor-down as the STLs lie, and both top frames
flipped deck-down. The printer, filament and print settings are in case/3mf/keygen-print.json: the
process there names the Bambu preset it starts from and the settings Keygen changes (90 % infill,
5 walls, 5 bottom layers, no supports, the textured PEI plate). This script resolves each preset's
chain of parents from the installed Bambu Studio's presets (~/.config/BambuStudio/system/BBL),
builds the project with the Bambu Studio command line and slices every plate, failing if a plate
does not slice or has a part off it. It writes the sliced project, so it opens in Bambu Studio
ready to send, and prints each plate's time and filament. The tenting wedges are not in it.

Needs bambu-studio on the PATH; its presets are not hashed by tools/regen.py, so a Bambu Studio
update reaches the project on the next change to the case, or with --force print-3mf.
"""
import json, struct, subprocess, sys, tempfile, zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "case/3mf/keygen-print.json"
OUT = ROOT / "case/3mf/keygen-case.3mf"
BAMBU = Path.home() / ".config/BambuStudio"
PARTS = [("bottom", "left"), ("bottom", "right"), ("top", "left"), ("top", "right")]


def preset(kind, name, own=None):
    """A Bambu preset with its parents merged in, as the command line needs it."""
    def load(n):
        for d in (BAMBU / "user/default" / kind, BAMBU / "system/BBL" / kind):
            if (d / f"{n}.json").exists():
                return json.loads((d / f"{n}.json").read_text())
        sys.exit(f"gen_print3mf: no Bambu Studio {kind} preset {n!r}; open Bambu Studio once to install its presets")
    chain = [own or load(name)]
    while chain[-1].get("inherits"):
        chain.append(load(chain[-1]["inherits"]))
    out = {}
    for c in reversed(chain):
        out.update(c)
    out.pop("inherits", None)
    out.update(type=kind, name=chain[0]["name"], **{"from": "system", "instantiation": "true"})
    return out


def flipped(src, dst):
    """The STL turned 180 degrees about Y, so the top frame lies deck-down."""
    b = src.read_bytes()
    n = struct.unpack("<I", b[80:84])[0]
    d = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])).copy()
    for f in ("n", "v"):
        a = d[f].reshape(len(d), -1, 3)
        a[..., 0] *= -1
        a[..., 2] *= -1
    dst.write_bytes(b[:84] + d.tobytes())


def bambu(args, cwd):
    r = subprocess.run(["bambu-studio", *args], cwd=cwd, capture_output=True, text=True)
    result = json.loads((cwd / "result.json").read_text()) if (cwd / "result.json").exists() else {}
    if r.returncode or result.get("return_code", 0):
        sys.exit(f"gen_print3mf: bambu-studio failed: {result.get('error_string') or r.stdout[-2000:]}")


def main():
    conf = json.loads(CONF.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        files = {"machine": preset("machine", conf["machine"]),
                 "process": preset("process", conf["process"]["name"], conf["process"]),
                 "filament": preset("filament", conf["filament"])}
        files["machine"]["curr_bed_type"] = conf["process"]["curr_bed_type"]
        for k, v in files.items():
            (tmp / f"{k}.json").write_text(json.dumps(v, indent=1))
        stls = []
        for part, side in PARTS:
            src = ROOT / f"case/{part}/stl/keygen-{side}-{part}.stl"
            if part == "top":
                dst = tmp / src.name
                flipped(src, dst)
                src = dst
            stls.append(str(src))
        project = tmp / "keygen-case.3mf"
        bambu(["--load-settings", f"{tmp}/machine.json;{tmp}/process.json", "--load-filaments", f"{tmp}/filament.json",
               "--arrange", "1", "--orient", "0", "--export-3mf", str(project), *stls], tmp)
        sliced = tmp / "sliced.3mf"
        bambu(["--slice", "0", "--export-3mf", str(sliced), str(project)], tmp)
        info = zipfile.ZipFile(sliced).read("Metadata/slice_info.config").decode()
        import xml.etree.ElementTree as ET
        names = {}
        for o in ET.fromstring(zipfile.ZipFile(project).read("Metadata/model_settings.config")).iter("object"):
            names[o.get("id")] = next(m.get("value") for m in o.iter("metadata") if m.get("key") == "name")
        plates = {}
        for p in ET.fromstring(zipfile.ZipFile(project).read("Metadata/model_settings.config")).iter("plate"):
            meta = {m.get("key"): m.get("value") for m in p.iter("metadata")}
            plates[meta["plater_id"]] = names.get(meta.get("object_id"), "?")
        total_t = total_g = 0.0
        for p in ET.fromstring(info).iter("plate"):
            meta = {m.get("key"): m.get("value") for m in p.findall("metadata")}
            if meta.get("outside") == "true":
                sys.exit(f"gen_print3mf: plate {meta['index']} has a part off the plate")
            t, g = int(meta["prediction"]), float(meta["weight"])
            total_t += t; total_g += g
            print(f"plate {meta['index']}: {plates.get(meta['index'], '?')}, {t // 3600} h {t % 3600 // 60:02d} min, {g:.0f} g")
        print(f"total {int(total_t) // 3600} h {int(total_t) % 3600 // 60:02d} min, {total_g:.0f} g {conf['filament']} "
              f"on a {conf['machine']}")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_bytes(sliced.read_bytes())


if __name__ == "__main__":
    main()
