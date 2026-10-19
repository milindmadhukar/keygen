"""Minimal KiCad S-expression reader/writer."""
import re

_tok = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')

class Sym(str):
    """Bare (unquoted) atom."""

def parse(text):
    stack, cur = [], []
    pos = 0
    while pos < len(text):
        m = _tok.match(text, pos)
        if not m or m.end() == pos:
            if text[pos:].strip() == "": break
            raise ValueError(f"parse error at {pos}: {text[pos:pos+40]!r}")
        pos = m.end()
        o, c, s, a = m.groups()
        if o: stack.append(cur); cur = []
        elif c: done = cur; cur = stack.pop(); cur.append(done)
        elif s is not None: cur.append(s[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        elif a is not None: cur.append(Sym(a))
    return cur[0] if len(cur) == 1 else cur

def dump(x, indent=0):
    if isinstance(x, list):
        inner = [dump(i, indent + 1) for i in x]
        flat = "(" + " ".join(inner) + ")"
        if len(flat) < 100 and "\n" not in flat:
            return flat
        head = []
        rest = list(inner)
        while rest and not rest[0].startswith("("):
            head.append(rest.pop(0))
        pad = "\n" + "  " * (indent + 1)
        return "(" + " ".join(head) + "".join(pad + r for r in rest) + "\n" + "  " * indent + ")"
    if isinstance(x, Sym): return str(x)
    if isinstance(x, (int, float)):
        return ("%.4f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)
    return '"' + str(x).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

def find(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]

def first(node, key):
    r = find(node, key)
    return r[0] if r else None

def lib_symbol(path, name):
    lib = parse(open(path).read())
    for s in find(lib, "symbol"):
        if s[1] == name:
            if first(s, "extends"):
                raise ValueError(f"{name} extends another symbol; flatten it first")
            return s
    raise KeyError(f"{name} not in {path}")

def pins(sym):
    """[(number, name, type, x, y, angle)] for body style 1 (and common unit 0)."""
    out = []
    for unit in find(sym, "symbol"):
        m = re.match(r".*_(\d+)_(\d+)$", unit[1])
        if m and m.group(2) not in ("0", "1"): continue
        for p in find(unit, "pin"):
            at = first(p, "at")
            out.append((first(p, "number")[1], first(p, "name")[1], str(p[1]), float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0))
    return out
