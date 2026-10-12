"""Checks that edits to the addon's Lua files changed only comments and whitespace.

Tokenizes each .lua file (Lua 5.1 lexical rules), drops comments and whitespace,
and compares the token stream with the same file at a git revision.

Usage: python addon/tests/check_comment_only.py [REV]   (default REV: HEAD)
Exit code 0 = every changed .lua file has identical code tokens.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ADDON = "addon/RoadToForever"

LONG_OPEN = re.compile(r"\[(=*)\[")


def tokens(src):
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t\r\n\f\v":
            i += 1
            continue
        if src.startswith("--", i):
            m = LONG_OPEN.match(src, i + 2)
            if m:
                end = src.find("]" + m.group(1) + "]", m.end())
                i = n if end < 0 else end + len(m.group(1)) + 2
            else:
                nl = src.find("\n", i)
                i = n if nl < 0 else nl
            continue
        m = LONG_OPEN.match(src, i)
        if m:
            close = "]" + m.group(1) + "]"
            end = src.find(close, m.end())
            end = n if end < 0 else end + len(close)
            out.append(src[i:end])
            i = end
            continue
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1])
            i = j + 1
            continue
        m = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|0[xX][0-9a-fA-F]+|\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|\.\.\.|\.\.|==|~=|<=|>=|.").match(src, i)
        out.append(m.group(0))
        i = m.end()
    return out


def main():
    rev = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    files = subprocess.run(["git", "diff", "--name-only", rev, "--", ADDON],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    bad = 0
    for f in files:
        if not f.endswith(".lua") or not os.path.exists(os.path.join(ROOT, f)):
            continue
        old = subprocess.run(["git", "show", f"{rev}:{f}"], cwd=ROOT, capture_output=True, text=True).stdout
        with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
            new = fh.read()
        a, b = tokens(old), tokens(new)
        if a != b:
            bad += 1
            k = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            print(f"CODE CHANGED: {f} at token {k}: {a[k:k+6]} -> {b[k:k+6]}")
    print(f"{len(files)} file(s) compared, {bad} with code changes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
