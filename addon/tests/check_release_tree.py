"""Checks what the release zip will contain (addon/RoadToForever/, packed by `git archive`).

Fails if:
  * a developer file ships (TESTING.md) or a public file is missing (README.md, LICENSE, CHANGELOG.md);
  * the TOC version, the newest player-changelog section and the TOC's required fields disagree;
  * an internal note leaks into a shipped file (plan/test pointers, personal names).

Usage: python addon/tests/check_release_tree.py        Exit code 0 = fine.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.normpath(os.path.join(HERE, "..", "RoadToForever"))

problems = []


def fail(msg):
    problems.append(msg)


def read(rel):
    with open(os.path.join(TREE, rel), encoding="utf-8") as fh:
        return fh.read()


for name in ("README.md", "LICENSE", "CHANGELOG.md", "RoadToForever.toc", "Bindings.xml"):
    if not os.path.isfile(os.path.join(TREE, name)):
        fail(f"missing shipped file: {name}")
for name in ("TESTING.md", "HARDENING.md", "ADDON_PLAN.md"):
    if os.path.exists(os.path.join(TREE, name)):
        fail(f"developer file would ship: {name}")

toc = read("RoadToForever.toc")
m = re.search(r"^## Version:\s*(\S+)\s*$", toc, re.M)
version = m.group(1) if m else None
if not version or not re.fullmatch(r"\d+\.\d+\.\d+", version):
    fail(f"TOC ## Version is not x.y.z: {version!r}")
for field in ("Title", "Author", "Notes", "X-Website", "X-License", "SavedVariables"):
    if not re.search(rf"^## {field}:\s*\S", toc, re.M):
        fail(f"TOC is missing ## {field}")

cl = read("CHANGELOG.md")
first = re.search(r"^## (\d+\.\d+\.\d+) \(", cl, re.M)
if not first:
    fail("CHANGELOG.md has no '## x.y.z (date)' section")
elif version and first.group(1) != version:
    fail(f"newest CHANGELOG section is {first.group(1)} but the TOC says {version}")

LEAKS = re.compile(r"ADDON_PLAN|TESTING\.md|BACKLOG\.md|ROADMAP\.md|\bVenom\b|Trollmann|Oathbreaker|vartdal|@gmail\.com",
                   re.I)
for dirpath, _, names in os.walk(TREE):
    for n in names:
        if not n.endswith((".lua", ".xml", ".toc", ".md")) or n == "LICENSE":
            continue
        rel = os.path.relpath(os.path.join(dirpath, n), TREE)
        with open(os.path.join(dirpath, n), encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if LEAKS.search(line):
                    fail(f"{rel}:{i}: internal note or personal detail: {line.strip()[:80]}")

if problems:
    print("\n".join(problems))
    print(f"{len(problems)} problem(s)")
    sys.exit(1)
print(f"release tree ok: version {version}, {sum(len(f) for _, _, f in os.walk(TREE))} files")
