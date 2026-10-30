#!/usr/bin/env python3
"""Regenerate every generated file whose sources changed, and nothing else.

Each step below is one generator with the files it reads and the files it writes. A step's inputs
are its script, the tools/ modules that script imports (found by reading the imports), and its data
files; their contents are hashed together. tools/regen.lock holds each step's hash from its last
run and is committed with the outputs, so the repo itself records that they are current. A step
runs when its hash differs from the lock or one of its outputs is missing. Steps run in order, so a
step that reads another's outputs (the case renders read the case STEP files) sees them fresh.

The PCB itself (gen_pcb.py through silkscreen_art.py) is a source here, not a step: those scripts
edit pcb/keygen.kicad_pcb and are run by hand.

The binary outputs (renders, Gerbers, case files, the schematic PDF, 3D models) are gitignored:
tools/publish.py uploads them to GitHub releases on every push to main (.githooks/pre-push). Their
steps still hash into tools/regen.lock, so a commit still waits until they match its sources.

Steps in LOCAL write files that are never published (the Blender parts file). Their hashes go in
tools/regen.local.lock (also ignored), and --check skips them, so a commit never depends on them;
a plain run and the Stop hook keep them current.

Steps in ON_REQUEST (the Blender parts file and the studio renders) run only when asked for, with
--blender or by name with --force: a plain run, the Stop hook and --check skip them, so they can lag
behind their sources until the next time someone renders.

    python3 tools/regen.py               run the stale steps
    python3 tools/regen.py --blender     the same, with the Blender steps
    python3 tools/regen.py --check       list the stale steps, exit 1 if any (the pre-commit hook)
    python3 tools/regen.py --force [STEP ...]   rerun steps even if current (every step if none named)
    python3 tools/regen.py --hook        the Claude Code Stop hook: run the stale steps, report as JSON

Wired up in .claude/settings.json (Stop) and .githooks/pre-commit. One run at a time: a run waits
for another that holds the lock (in the git directory), and the Stop hook skips instead of waiting.
"""
import argparse, ast, fcntl, fnmatch, hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
LOCK = TOOLS / "regen.lock"
LOCAL_LOCK = TOOLS / "regen.local.lock"
PY = "python3"
CAD = str(Path.home() / ".venvs/keygen-cad/bin/python")     # build123d + shapely, see notes/17
PCB = "pcb/keygen.kicad_pcb"
SUBMODULES = ("lib/marbastlib", "lib/Keebio-Parts.pretty", "lib/KeyV2")  # hashed by their checked-out commit

# name, command, data inputs (globs), outputs (globs; each must match something)
STEPS = [
    ("keycaps", [PY, "tools/gen_keycaps.py"], ["lib/KeyV2"],
     ["pcb/lib/keygen.3dshapes/Keycap_*.wrl", "pcb/lib/keygen.3dshapes/Keycap_*.stl"]),
    ("schematic", [PY, "tools/gen_schematic.py"], [*SUBMODULES],
     ["pcb/keygen.kicad_sch", "pcb/left.kicad_sch", "pcb/right.kicad_sch", "pcb/lib/keygen.kicad_sym",
      "pcb/lib/keygen.pretty/*.kicad_mod"]),
    ("schematic-pdf", ["kicad-cli", "sch", "export", "pdf", "-o", "pcb/keygen-schematic.pdf", "pcb/keygen.kicad_sch"],
     ["pcb/*.kicad_sch", "pcb/keygen.kicad_pro", "pcb/lib/keygen.kicad_sym"], ["pcb/keygen-schematic.pdf"]),
    ("zmk-layout", [PY, "tools/gen_zmk_layout.py"], [],
     ["firmware/boards/shields/keygen/keygen-layouts.dtsi"]),
    ("keymap", [PY, "tools/render_keymap.py"],
     ["firmware/keygen.keymap", "firmware/boards/shields/keygen/keygen-layouts.dtsi"], ["assets/keymap-*.svg"]),
    ("oled-assets", [PY, "tools/gen_oled_assets.py"], [],
     ["firmware/module/src/ui/kg_assets.c", "firmware/module/src/ui/kg_assets.h"]),
    ("oled", [PY, "tools/render_oled.py"], ["firmware/module/src/ui/**", "firmware/module/sim/**"],
     ["assets/oled-*.svg", "assets/oled-*.gif"]),
    ("models", [CAD, "tools/gen_models.py"], [],
     ["pcb/lib/keygen.3dshapes/Knob_17mm.step", "pcb/lib/keygen.3dshapes/OLED_096_I2C.step"]),
    ("plate", [PY, "tools/gen_plate.py"], [PCB],
     ["pcb/plate/keygen-plate.kicad_pcb", "case/plate/gerber/*.zip", "case/plate/dxf/*.dxf", "case/plate/PLATE.md"]),
    ("plate-print", [PY, "tools/plate_print.py"], [PCB], ["case/plate/pdf/keygen-plate-print.pdf"]),
    ("plate-print-portrait", [PY, "tools/plate_print.py", "--portrait"], [PCB],
     ["case/plate/pdf/keygen-plate-print-portrait.pdf"]),
    ("case-footprint-print", [CAD, "tools/case_footprint_print.py"], [PCB],
     ["case/plate/pdf/keygen-case-footprint-portrait.pdf"]),
    ("case", [CAD, "tools/gen_case.py"], [PCB],
     ["case/keygen-case.step", "case/bottom/stl/*.stl", "case/top/stl/*.stl", "case/plate/stl/*.stl", "case/plate/step/*.step",
      "case/wedge/stl/*.stl", "case/wedge/step/*.step",
      "case/foam/dxf/*.dxf", "case/foam/svg/*.svg", "case/foam/step/*.step"]),
    ("case-renders", [PY, "tools/render_case.py"],
     [PCB, "pcb/keygen.kicad_pro", "pcb/plate/keygen-plate.kicad_pcb", "case/*.step", "case/wedge/step/*.step", "pcb/lib/**", *SUBMODULES],
     ["assets/render-case*.png", "assets/render-plate.png"]),
    ("board-renders", [PY, "tools/render_board.py"], [PCB, "pcb/keygen.kicad_pro", "pcb/lib/**", *SUBMODULES],
     ["assets/render-hero.png", "assets/render-top.png", "assets/render-bottom.png",
      "assets/render-bare*.png"]),
    ("routing-render", [PY, "tools/render_routing.py"], [PCB], ["assets/pcb-routing.png"]),
    ("assembly-maps", [PY, "tools/render_assembly.py"], [PCB], ["assets/assembly-*.png"]),
    ("blender", [PY, "tools/gen_blend.py"],
     [PCB, "pcb/keygen.kicad_pro", "pcb/lib/**", *SUBMODULES, "case/*/stl/*.stl", "tools/blend_scene.py",
      "assets/oled-*.svg"],
     ["blender/keygen-parts.blend"]),
    ("studio-renders", [PY, "tools/render_blender.py"],
     [PCB, "pcb/keygen.kicad_pro", "pcb/lib/**", *SUBMODULES, "case/*/stl/*.stl", "tools/gen_blend.py",
      "tools/blend_scene.py", "tools/blend_render.py", "blender/keygen.blend", "tools/render_oled.py",
      "assets/oled-*.svg"],
     ["assets/render-studio-*.jpg", "assets/render-studio-*.gif"]),
    ("studio-tented", [PY, "tools/render_blender.py", "--tented"],
     [PCB, "pcb/keygen.kicad_pro", "pcb/lib/**", *SUBMODULES, "case/*/stl/*.stl", "tools/gen_blend.py",
      "tools/blend_scene.py", "tools/blend_render.py", "blender/keygen.blend", "tools/render_oled.py",
      "assets/oled-*.svg"],
     ["assets/render-studio-tented-*.jpg", "assets/render-studio-tented-*.gif"]),
    ("fab", [PY, "tools/export_fab.py"], [PCB, "pcb/keygen.kicad_pro"],
     ["fab/keygen-gerbers.zip", "fab/keygen-left-gerbers.zip", "fab/keygen-right-gerbers.zip", "fab/ORDER.md"]),
    ("assembly-bom", [PY, "tools/export_bom.py"], ["pcb/*.kicad_sch", "bom/bom.csv"], ["fab/BOM.md", "fab/BOM-*.csv"]),
    ("bom-page", [PY, "tools/render_bom.py"], ["bom/bom.csv"], ["plan/bom.html", "notes/13 - bill of materials.md"]),
]
LOCAL = {"blender"}
ON_REQUEST = {"blender", "studio-renders", "studio-tented"}


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout


def repo_files():
    """Every file in the work tree, relative to the root: tracked, untracked and ignored. The
    generated binaries are ignored (tools/publish.py publishes them), yet they are outputs to look
    for and inputs to hash."""
    return sorted(set(git("ls-files", "-co", "--exclude-standard", "-z").split("\0")[:-1])
                  | set(git("ls-files", "-oi", "--exclude-standard", "-z").split("\0")[:-1]))


def local_imports(script, seen=None):
    """The tools/ modules a script imports, transitively."""
    seen = seen if seen is not None else set()
    for node in ast.walk(ast.parse((ROOT / script).read_text())):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) and node.module else []
        for n in names:
            dep = f"tools/{n.split('.')[0]}.py"
            if dep not in seen and (ROOT / dep).exists():
                seen.add(dep)
                local_imports(dep, seen)
    return seen


class Tree:
    def __init__(self):
        self.files = repo_files()
        self.subs = {line[1:].split()[1]: line for line in git("submodule", "status").splitlines()}
        self.cache = {}

    def match(self, pattern):
        return [f for f in self.files if fnmatch.fnmatchcase(f, pattern)
                or (pattern.endswith("/**") and f.startswith(pattern[:-2]))]

    def sha(self, path):
        if path not in self.cache:
            self.cache[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        return self.cache[path]

    def digest(self, step):
        name, cmd, inputs, _ = step
        h = hashlib.sha256(json.dumps([c if c not in (PY, CAD) else "python" for c in cmd]).encode())
        scripts = {c for c in cmd if c.startswith("tools/")}
        for s in list(scripts):
            scripts |= local_imports(s)
        files = set(scripts)
        for pattern in inputs:
            if pattern in self.subs:
                h.update(self.subs[pattern].encode())      # its commit, and + if moved off the pin
            else:
                files.update(self.match(pattern))
        for f in sorted(files):
            if (ROOT / f).is_file():
                h.update(f"{f}\0{self.sha(f)}\0".encode())
        return h.hexdigest()

    def missing(self, step):
        return [o for o in step[3] if not self.match(o)]


def load_lock():
    return {k: v for f in (LOCK, LOCAL_LOCK) if f.exists() for k, v in json.loads(f.read_text()).items()}


def save_lock(lock):
    for f, keep in ((LOCK, lambda k: k not in LOCAL), (LOCAL_LOCK, lambda k: k in LOCAL)):
        f.write_text(json.dumps({k: v for k, v in sorted(lock.items()) if keep(k)}, indent=2) + "\n")


def stale(tree, lock, step):
    """Why a step needs to run, or None."""
    if (m := tree.missing(step)):
        return f"missing {', '.join(m)}"
    if lock.get(step[0]) != tree.digest(step):
        return "inputs changed" if step[0] in lock else "never run"
    return None


def hold(wait=True):
    """Take the run lock, so two runs (a Stop hook and a run by hand, or two sessions' hooks) never
    write the same outputs at once. Returns the open lock file, or None if busy and not waiting."""
    f = open(ROOT / git("rev-parse", "--git-common-dir").strip() / "regen.running", "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        if not wait:
            f.close()
            return None
        print("regen: waiting for another run to finish", flush=True)
        fcntl.flock(f, fcntl.LOCK_EX)
    return f


def run(force=(), log=print, on_request=False):
    """Run the stale steps (and the forced ones) in order, the ON_REQUEST ones only if on_request or
    forced. Returns (ran, failure) where failure is (step name, output tail) or None. Call with the
    run lock held."""
    lock, ran = load_lock(), []
    for step in STEPS:
        name, cmd = step[0], step[1]
        if name in ON_REQUEST and name not in force and not on_request:
            continue
        tree = Tree()                                         # rescan: earlier steps may have written files
        why = "forced" if name in force else stale(tree, lock, step)
        if not why:
            continue
        log(f"regen: {name} ({why})")
        before = tree.digest(step)
        t = time.monotonic()
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        out = "\n".join(l for l in (p.stdout + p.stderr).splitlines() if ": Debug: " not in l)
        if p.returncode:
            return ran, (name, "\n".join(out.splitlines()[-40:]))
        if (m := Tree().missing(step)):
            return ran, (name, f"ran, but wrote nothing for {', '.join(m)}\n{out[-2000:]}")
        lock[name] = before
        save_lock(lock)
        ran.append(name)
        log(f"regen: {name} done in {time.monotonic() - t:.0f} s")
    return ran, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="list stale steps; exit 1 if any")
    ap.add_argument("--force", nargs="*", metavar="STEP", help="rerun these steps (all if none named)")
    ap.add_argument("--hook", action="store_true", help="Claude Code Stop hook mode")
    ap.add_argument("--blender", action="store_true", help="also run the Blender steps if stale")
    a = ap.parse_args()
    names = [s[0] for s in STEPS]

    if a.check:
        tree, lock = Tree(), load_lock()
        bad = [(s[0], why) for s in STEPS if s[0] not in LOCAL | ON_REQUEST and (why := stale(tree, lock, s))]
        for name, why in bad:
            print(f"stale: {name} ({why})")
        if bad:
            print("Run python3 tools/regen.py, then commit what it writes.")
        sys.exit(1 if bad else 0)

    if a.hook:
        event = json.loads(sys.stdin.read() or "{}")
        if not (held := hold(wait=False)):
            print(json.dumps({"systemMessage": "tools/regen.py: another run is in progress; skipped"}))
            sys.exit(0)
        ran, fail = run(log=lambda m: None)
        if fail:
            msg = f"tools/regen.py: step '{fail[0]}' failed, so its outputs are stale:\n{fail[1]}"
            if event.get("stop_hook_active"):                 # already sent back once; don't loop
                print(json.dumps({"systemMessage": msg}))
                sys.exit(0)
            print(msg, file=sys.stderr)
            sys.exit(2)                                       # Claude sees it and fixes the source
        if ran:
            print(json.dumps({"systemMessage": "Regenerated: " + ", ".join(ran)}))
        sys.exit(0)

    force = names if a.force == [] else (a.force or [])
    if unknown := set(force) - set(names):
        sys.exit(f"unknown step(s): {', '.join(sorted(unknown))}; steps are {', '.join(names)}")
    held = hold()
    ran, fail = run(force, on_request=a.blender)
    if fail:
        sys.exit(f"regen: {fail[0]} failed:\n{fail[1]}")
    print("regen: " + (f"ran {', '.join(ran)}" if ran else "everything is current"))


if __name__ == "__main__":
    main()
