#!/bin/sh
# Build every target in build.yaml in ZMK's Docker image and copy the UF2s to firmware/out/.
# The west workspace (ZMK, Zephyr, modules: about 4 GB) lives in $KEYGEN_ZMK_WS, outside the repo.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
ws=${KEYGEN_ZMK_WS:-$HOME/.cache/keygen-zmk}
image=zmkfirmware/zmk-build-arm:4.1

mkdir -p "$ws" "$here/out"
rm -rf "$ws/firmware"
mkdir "$ws/firmware"
tar -C "$here" --exclude=./out -cf - . | tar -C "$ws/firmware" -xf -

docker run --rm -i -u "$(id -u):$(id -g)" -e HOME=/tmp \
    -v "$ws:/work" -v "$here/out:/out" -w /work "$image" python3 - <<'PY'
import filecmp, shutil, subprocess, sys, yaml

def run(*cmd): subprocess.run(cmd, check=True)

run("sh", "-c", "[ -d .west ] || west init -l firmware")
if not shutil.os.path.exists("west.yml.built") or not filecmp.cmp("firmware/west.yml", "west.yml.built"):
    run("west", "update", "--fetch-opt=--filter=tree:0")
    shutil.copy("firmware/west.yml", "west.yml.built")
run("west", "zephyr-export")

failed = []
for t in yaml.safe_load(open("firmware/build.yaml"))["include"]:
    name = t["shield"]
    cmd = ["west", "build", "-p", "auto", "-s", "zmk/app", "-d", f"build/{name}", "-b", t["board"]]
    if "snippet" in t: cmd += ["-S", t["snippet"]]
    cmd += ["--", "-DZMK_CONFIG=/work/firmware", f"-DSHIELD={name}", *t.get("cmake-args", "").split()]
    print(f"\n=== {name}", flush=True)
    if subprocess.run(cmd).returncode:
        failed.append(name); continue
    shutil.copy(f"build/{name}/zephyr/zmk.uf2", f"/out/{name}-nice_nano.uf2")

print("\nfailed: " + ", ".join(failed) if failed else "\nall builds OK: firmware/out/*.uf2")
sys.exit(1 if failed else 0)
PY
