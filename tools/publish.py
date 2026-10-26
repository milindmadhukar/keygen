#!/usr/bin/env python3
"""Publish the generated binaries to GitHub releases, and fetch release files back.

The renders, the manufacturing and CAD files and the datasheets are not in git (see .gitignore).
They are assets of three releases of the repo, each under a fixed tag, so their download URLs
never change (https://github.com/<repo>/releases/download/<tag>/<file>):

media       the pictures in the README and the notes: assets/*.png, *.jpg, *.gif
build       PCB and plate Gerbers, case and plate STLs and STEPs, foam cut files, the plate print
            PDFs and the schematic PDF
datasheets  the part datasheets that docs/datasheets/README.md cites

    python3 tools/publish.py [RELEASE ...]      upload what changed (media and build if none named;
                                                the pre-push hook runs this when main is pushed)
    python3 tools/publish.py --dry-run [...]    list what would change, change nothing
    python3 tools/publish.py --fetch [RELEASE ...]   download media or datasheets into place
                                                (build's files come from tools/regen.py)

An asset is uploaded when its SHA-256 differs from the release's copy and deleted when nothing
produces it any more (datasheets are only ever added). Each release's notes name the commit its
files were built from. Needs the GitHub CLI, logged in.
"""
import argparse, hashlib, json, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "milindmadhukar/keygen"
RELEASES = {
    "media": dict(
        title="README pictures",
        about="The renders and animations shown in the README and the design notes.",
        globs=["assets/*.png", "assets/*.jpg", "assets/*.gif"], prune=True),
    "build": dict(
        title="Build files",
        about="Everything needed to order and make Keygen: the PCB Gerbers (one zip per half, and both "
              "together), the switch plate Gerbers, DXFs and 1:1 print PDFs, the case STLs to print and "
              "STEPs, the foam cut files, and the schematic PDF. Ordering notes: fab/ORDER.md and "
              "case/plate/PLATE.md in the repo.",
        globs=["fab/*.zip", "pcb/keygen-schematic.pdf", "case/keygen-case.step", "case/*/stl/*.stl",
               "case/*/step/*.step", "case/*/dxf/*.dxf", "case/*/svg/*.svg", "case/*/pdf/*.pdf",
               "case/*/gerber/*.zip"], prune=True),
    "datasheets": dict(
        title="Part datasheets",
        about="The manufacturers' datasheets that docs/datasheets/README.md cites, page by page. They "
              "belong to their manufacturers; the README there gives each one's source.",
        globs=["docs/datasheets/*.pdf", "docs/datasheets/*.png"], prune=False),
}
DEFAULT = ("media", "build")


def gh(*args, capture=True):
    p = subprocess.run(["gh", *args], capture_output=capture, text=True)
    if p.returncode:
        sys.exit(f"gh {' '.join(args[:3])} failed:\n{p.stderr.strip() if capture else ''}")
    return p.stdout


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout.strip()


def local_files(name):
    files = sorted({p for g in RELEASES[name]["globs"] for p in ROOT.glob(g) if p.is_file()})
    seen = {}
    for f in files:
        if f.name in seen:
            sys.exit(f"{name}: two files would share the asset name {f.name}: {seen[f.name]} and {f}")
        seen[f.name] = f
    return seen


def remote(name):
    """The release's assets as {name: sha256 or None}, or None if there is no such release."""
    p = subprocess.run(["gh", "api", f"repos/{REPO}/releases/tags/{name}"], capture_output=True, text=True)
    if p.returncode:
        return None
    return {a["name"]: (a.get("digest") or "").removeprefix("sha256:") or None for a in json.loads(p.stdout)["assets"]}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notes(name, commit):
    r = RELEASES[name]
    subject = git("log", "-1", "--format=%s", commit)
    return (f"{r['about']}\n\nBuilt from {commit[:7]} ({subject}) and kept current by `tools/publish.py`, "
            f"which replaces these files whenever `main` is pushed. Download a file at "
            f"`https://github.com/{REPO}/releases/download/{name}/<file>`.")


def publish(name, commit, dry):
    files = local_files(name)
    if not files:
        sys.exit(f"{name}: no files to publish; run python3 tools/regen.py first"
                 + (" (or --fetch datasheets)" if name == "datasheets" else ""))
    assets = remote(name)
    if assets is None:
        print(f"{name}: creating the release")
        if dry:
            assets = {}
        else:
            gh("release", "create", name, "-R", REPO, "--target", "main", "--title", RELEASES[name]["title"],
               "--notes", notes(name, commit), f"--latest={'true' if name == 'build' else 'false'}")
            assets = {}
    changed = [f for n, f in files.items() if assets.get(n) != sha256(f)]
    stale = [n for n in assets if n not in files] if RELEASES[name]["prune"] else []
    for f in changed:
        print(f"{name}: upload {f.relative_to(ROOT)}")
    for n in stale:
        print(f"{name}: delete {n}")
    if dry:
        return
    if changed:
        gh("release", "upload", name, "-R", REPO, "--clobber", *map(str, changed), capture=False)
    for n in stale:
        gh("release", "delete-asset", name, n, "-R", REPO, "--yes")
    if changed or stale:
        gh("release", "edit", name, "-R", REPO, "--notes", notes(name, commit))
    print(f"{name}: {len(files)} files, {len(changed)} uploaded, {len(stale)} deleted")


def fetch(name):
    if name == "build":
        sys.exit("build: its files come from python3 tools/regen.py, not from the release")
    dest = ROOT / Path(RELEASES[name]["globs"][0]).parent
    dest.mkdir(parents=True, exist_ok=True)
    assets = remote(name)
    if assets is None:
        sys.exit(f"{name}: no such release")
    for n, digest in assets.items():
        path = dest / n
        if path.exists() and sha256(path) == digest:
            continue
        print(f"{name}: fetch {path.relative_to(ROOT)}")
        urllib.request.urlretrieve(f"https://github.com/{REPO}/releases/download/{name}/{n}", path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("releases", nargs="*", choices=[[], *RELEASES], metavar="RELEASE")
    ap.add_argument("--fetch", action="store_true", help="download release files into place")
    ap.add_argument("--dry-run", action="store_true", help="list what would change")
    ap.add_argument("--commit", default="HEAD", help="the commit the files were built from (default HEAD)")
    a = ap.parse_args()
    if a.fetch:
        for name in a.releases or ("media", "datasheets"):
            fetch(name)
        return
    commit = git("rev-parse", a.commit)
    for name in a.releases or DEFAULT:
        publish(name, commit, a.dry_run)


if __name__ == "__main__":
    main()
