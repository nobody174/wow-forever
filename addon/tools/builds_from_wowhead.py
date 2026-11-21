#!/usr/bin/env python3
"""Rewrite the level 60 share codes in builds.html from Wowhead's Forever build guides.

Each guide https://www.wowhead.com/forever/guide/classes/<class>/<spec>/talent-builds-pve-<dps|tank|healer> embeds builds as
[talent=<class>/<code>_t0...]. The code is our own format (ranks per talent, trees joined by "-") behind a version prefix
("v2" or "vkndmh"; strip letters/digit version only, a following "-" means an empty first tree). The FIRST build on a page
(the standard raid/dungeon build) is used. Ranks are capped at the live maximum, an illegal fill is KEPT and reported.

  python addon/tools/builds_from_wowhead.py            dry run
  python addon/tools/builds_from_wowhead.py --apply    writes builds.html (then gen_talent_data.py, build.py, run_tests.py)

Level 30 builds are not touched. The rotation text is NOT rewritten.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import builds_from_rankedboost as rb  # noqa: E402

ROOT = rb.ROOT
PAGE = {  # (class, title tail) -> (spec slug, role suffix)
    ("priest", "Holy (Healer)"): ("holy", "healer"), ("priest", "Shadow"): ("shadow", "dps"),
    ("warlock", "Affliction"): ("affliction", "dps"), ("warlock", "Destruction"): ("destruction", "dps"),
    ("mage", "Frost"): ("frost", "dps"), ("mage", "Fire"): ("fire", "dps"),
    ("rogue", "Combat"): ("combat", "dps"),
    ("druid", "Feral (Bear tank)"): ("feral", "tank"), ("druid", "Restoration (Healer)"): ("restoration", "healer"),
    ("shaman", "Restoration (Healer)"): ("restoration", "healer"), ("shaman", "Enhancement"): ("enhancement", "dps"),
    ("shaman", "Elemental"): ("elemental", "dps"),
    ("hunter", "Beast Mastery"): ("beast-mastery", "dps"), ("hunter", "Marksmanship"): ("marksmanship", "dps"),
    ("paladin", "Protection (Tank)"): ("protection", "tank"), ("paladin", "Holy (Healer)"): ("holy", "healer"),
    ("paladin", "Retribution"): ("retribution", "dps"),
    ("warrior", "Protection (Tank)"): ("protection", "tank"), ("warrior", "Fury (DPS)"): ("fury", "dps"),
}


def first_code(cls, spec, role):
    url = "https://www.wowhead.com/forever/guide/classes/%s/%s/talent-builds-pve-%s" % (cls, spec, role)
    r = subprocess.run(["curl", "-sL", "-m", "30", "-A", "Mozilla/5.0", url], capture_output=True, text=True, encoding="utf-8")
    m = re.search(r"\[talent=%s/([^_\]]+)_t0" % cls, r.stdout.replace("\/", "/"))
    return m.group(1) if m else None


def decode(code, trees):
    code = re.sub(r"^v(?:[a-z]+|\d)", "", code)
    parts = code.split("-")
    parts += [""] * (3 - len(parts))
    ranks = []
    for ti, tree in enumerate(trees):
        s = parts[ti]
        ranks.append([int(s[k]) if k < len(s) else 0 for k in range(len(tree["t"]))])
    return ranks


def main():
    apply = "--apply" in sys.argv
    trees = rb.parse_trees()
    path = os.path.join(ROOT, "builds.html")
    text = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    html = text.replace("\r\n", "\n")
    out = html
    edits = []
    for m in re.finditer(r'spec: "(.*?)", title: "(.*?)", code: "(.*?)"', html):
        _s, title, code = m.groups()
        cls = title.split()[0].lower()
        if "Level 60" not in title:
            continue
        key = (cls, re.sub(r"^.*?Level 60\s*", "", title))
        if key not in PAGE:
            print("NO PAGE MAPPED:", title)
            continue
        wcode = first_code(cls, *PAGE[key])
        if not wcode:
            print("NO CODE FOUND:", title)
            continue
        ranks = decode(wcode, trees[cls])
        for ti, t in enumerate(trees[cls]):
            for k, x in enumerate(t["t"]):
                ranks[ti][k] = min(ranks[ti][k], x["m"])
        n = sum(map(sum, ranks))
        if rb.legal_fill(trees[cls], ranks) != ranks or n != 51:
            print("KEPT (illegal or %d points): %s  wowhead=%s" % (n, title, wcode))
            continue
        new = rb.encode(ranks)
        print("%-45s %s%s" % (title, "same" if new == code else code + " -> ", "" if new == code else new))
        if new != code:
            edits.append((m.start(), m.end(), title, code, new, ranks))
    print("%d build(s) would change" % len(edits))
    if not apply:
        return
    for start, end, title, code, new, final in sorted(edits, key=lambda e: -e[0]):
        cls = title.split()[0].lower()
        seg_end = out.index("\n", out.index("talents:", end))
        items = []
        for ti, tree in enumerate(trees[cls]):
            for k, x in enumerate(tree["t"]):
                if final[ti][k]:
                    items.append('["%s","%d/%d","%s"]' % (x["n"].replace('"', '\\"'), final[ti][k], x["m"], x["i"]))
        seg = re.sub(r"talents: t\w+\(\[.*\]\)", lambda mm: "talents: tN([" + ", ".join(items) + "])", out[end:seg_end], count=1, flags=re.S)
        out = out[:start] + out[start:end].replace('code: "%s"' % code, 'code: "%s"' % new, 1) + seg + out[seg_end:]
    open(path, "w", encoding="utf-8", newline="").write(out.replace("\n", nl))
    print("builds.html written")


if __name__ == "__main__":
    main()
