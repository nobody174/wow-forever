#!/usr/bin/env python3
"""Rewrite the share codes in builds.html from RankedBoost's recommended builds (how 0.84.2 was made, now repeatable).

RankedBoost's class pages (https://rankedboost.com/world-of-warcraft/forever/build/<class>/) embed a JSON `builds` list;
each build has `alloc` = {Wowhead talent id: rank} for the game build the page names. Wowhead's talent ids are the same ids
the Wowhead Forever data uses, so a build converts exactly: id -> (tree, talent) through gen_talent_data's live fetch,
rank capped at the live maximum (RankedBoost lags the game's hotfixes: it once gave Rogue Lethality 5, the live maximum is 2).

  python addon/tools/builds_from_rankedboost.py            dry run: prints every build that would change
  python addon/tools/builds_from_rankedboost.py --apply    writes builds.html (then: python addon/tools/gen_talent_data.py,
                                                           python build.py, python addon/tests/run_tests.py)
  python addon/tools/builds_from_rankedboost.py --json f   read a saved {class: [builds]} file instead of fetching

Level 60 builds take the whole 51-point build; level 30 builds take the first 21 points in the calculator's own order
(deepest row first, then the tree with more points, then left to right), the same order TalentCalc.Order uses. A build that
is not a legal fill of the live trees after capping is KEPT as it was and reported. The rotation text in builds.html is
NOT touched: re-read it against the new picks (BACKLOG).
"""
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import gen_talent_data as g  # noqa: E402

LUA = os.path.join(ROOT, "addon", "RoadToForever", "TalentData.lua")
CLASSES = ("priest", "warlock", "mage", "rogue", "druid", "shaman", "hunter", "paladin", "warrior")

# (class, level, title tail in builds.html) -> RankedBoost build slug. Extend when builds.html gains a build.
MAP = {
    ("mage", 30, "Arcane"): "auth-mage-arcane-dps",
    ("mage", 30, "Frost AoE"): "auth-mage-frost-dps",
    ("mage", 30, "Fire"): "auth-mage-fire-dps",
    ("mage", 60, "Frost"): "auth-mage-frost-dps",
    ("mage", 60, "Fire"): "auth-mage-fire-dps",
    ("rogue", 30, "Combat"): "auth-rogue-combat-leveling",
    ("rogue", 30, "Assassination"): "auth-rogue-assassination-dps",
    ("rogue", 30, "Subtlety"): "auth-rogue-subtlety-pvp",
    ("rogue", 60, "Combat"): "auth-rogue-combat-dps",
    ("druid", 30, "Feral (Bear tank / Cat)"): "auth-druid-feral-combat-leveling",
    ("druid", 30, "Restoration (Healer)"): "auth-druid-restoration-healing",
    ("druid", 60, "Feral (Bear tank)"): "auth-druid-feral-combat-hybrid",
    ("druid", 60, "Restoration (Healer)"): "auth-druid-restoration-healing",
    ("shaman", 30, "Enhancement"): "auth-shaman-enhancement-leveling",
    ("shaman", 60, "Restoration (Healer)"): "auth-shaman-restoration-healing",
    ("shaman", 60, "Elemental"): "auth-shaman-elemental-dps",
    ("hunter", 30, "Beast Mastery"): "auth-hunter-beast-mastery-leveling",
    ("paladin", 30, "Retribution"): "auth-paladin-retribution-leveling",
    ("paladin", 30, "Protection (Tank)"): "auth-paladin-protection-tank",
    ("paladin", 30, "Holy (Healer)"): "auth-paladin-holy-healing",
    ("paladin", 60, "Protection (Tank)"): "auth-paladin-protection-tank",
    ("paladin", 60, "Holy (Healer)"): "auth-paladin-holy-healing",
    ("paladin", 60, "Retribution"): "auth-paladin-retribution-dps",
    ("warrior", 60, "Fury (DPS)"): "auth-warrior-fury-dps",
}


def fetch_builds():
    out = {}
    for cls in CLASSES:
        url = "https://rankedboost.com/world-of-warcraft/forever/build/%s/" % cls
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        i = page.index('"builds":[') + len('"builds":')
        out[cls], _ = json.JSONDecoder().raw_decode(page[i:])
    return out


def parse_trees():
    """TalentData.lua -> {class: [{name, t: [{n, r, c, m, p, q}]}]} (the generated file, in link order)."""
    classes, cur, tree = {}, None, None
    for line in open(LUA, encoding="utf-8"):
        m = re.match(r"\s+(\w+) = \{ token = ", line)
        if m:
            cur = m.group(1).lower()
            classes[cur] = []
            continue
        m = re.match(r'\s+\{ name = "([^"]+)", talents = \{', line)
        if m and cur:
            tree = {"name": m.group(1), "t": []}
            classes[cur].append(tree)
            continue
        m = re.match(r'\s+\{n="([^"]*)",i="([^"]*)",r=(\d+),c=(\d+),m=(\d+),p=(\d+),q=\{(.*?)\},d=\{', line)
        if m and tree is not None:
            q = [(int(a), int(b)) for a, b in re.findall(r"\{(\d+),(\d+)\}", m.group(7))]
            tree["t"].append(dict(n=m.group(1), i=m.group(2), r=int(m.group(3)), c=int(m.group(4)),
                                  m=int(m.group(5)), p=int(m.group(6)), q=q))
    return classes


def encode(ranks):
    return "-".join("".join(str(x) for x in r).rstrip("0") for r in ranks).rstrip("-")


def tier_met(tree, got, k):
    x = tree["t"][k]
    return sum(got[j] for j, y in enumerate(tree["t"]) if y["r"] < x["r"]) >= x["p"]


def legal_fill(trees, want):
    got = [[0] * len(t["t"]) for t in trees]
    changed = True
    while changed:
        changed = False
        for ti, tree in enumerate(trees):
            for k, x in enumerate(tree["t"]):
                if got[ti][k] < want[ti][k] and tier_met(tree, got[ti], k) and all(got[ti][q - 1] >= n for q, n in x["q"]):
                    got[ti][k] += 1
                    changed = True
    return got


def order_of(trees, ranks):
    walk = [[0] * len(t["t"]) for t in trees]
    weight = [sum(r) for r in ranks]
    out = []
    for _ in range(sum(weight)):
        best = None
        for ti, tree in enumerate(trees):
            for k, x in enumerate(tree["t"]):
                if walk[ti][k] < ranks[ti][k] and tier_met(tree, walk[ti], k) and all(walk[ti][q - 1] >= n for q, n in x["q"]):
                    key = (-x["r"], -weight[ti], ti, x["c"])
                    if best is None or key < best[0]:
                        best = (key, ti, k)
        if not best:
            break
        walk[best[1]][best[2]] += 1
        out.append((best[1], best[2]))
    return out


def prefix(trees, ranks, n):
    got = [[0] * len(r) for r in ranks]
    for ti, k in order_of(trees, ranks)[:n]:
        got[ti][k] += 1
    return got


def main():
    apply = "--apply" in sys.argv
    trees = parse_trees()
    if "--json" in sys.argv:
        rb = json.load(open(sys.argv[sys.argv.index("--json") + 1], encoding="utf-8"))
    else:
        rb = fetch_builds()
    raw = g.fetch()
    node = {}   # (class, wowhead talent id) -> (tree index, talent index in link order)
    for cls, _tok, tlist in g.CLASSES:
        for ti, (tid, _name) in enumerate(tlist):
            lst = sorted(raw.get(str(tid), {}).values(), key=lambda x: (x["row"], x["col"]))
            for k, x in enumerate(lst):
                node[(cls, x["id"])] = (ti, k)

    path = os.path.join(ROOT, "builds.html")
    text = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    html = text.replace("\r\n", "\n")
    edits = []
    for m in re.finditer(r'spec: "(.*?)", title: "(.*?)", code: "(.*?)"', html):
        _spec, title, code = m.groups()
        cls = title.split()[0].lower()
        lvl = int(re.search(r"Level (\d+)", title).group(1))
        slug = MAP.get((cls, lvl, re.sub(r"^.*?Level \d+\s*", "", title)))
        if not slug:
            continue
        build = next((b for b in rb.get(cls, []) if b["slug"] == slug), None)
        if build is None:
            print("MISSING on RankedBoost:", slug)
            continue
        ranks = [[0] * len(t["t"]) for t in trees[cls]]
        for nid, r in build["alloc"].items():
            ti, k = node[(cls, int(nid))]
            cap = trees[cls][ti]["t"][k]["m"]
            if r > cap:
                print("   cap %s: %s %d -> %d" % (slug, trees[cls][ti]["t"][k]["n"], r, cap))
            ranks[ti][k] = min(r, cap)
        if legal_fill(trees[cls], ranks) != ranks:
            print("KEPT (not legal on the live trees after capping): %s" % title)
            continue
        n = 21 if lvl == 30 else sum(map(sum, ranks))
        final = prefix(trees[cls], ranks, n) if lvl == 30 else ranks
        if legal_fill(trees[cls], final) != final or sum(map(sum, final)) != n:
            print("KEPT (prefix not legal): %s" % title)
            continue
        new = encode(final)
        if lvl == 60 and n < 51:
            print("   short: %s has %d of 51 points" % (slug, n))
        if new != code:
            print("%-50s %s -> %s" % (title, code, new))
            edits.append((m.start(), m.end(), title, code, new, final))
    print("%d build(s) would change" % len(edits))
    if not apply:
        return
    out = html
    for start, end, title, code, new, final in sorted(edits, key=lambda e: -e[0]):
        cls = title.split()[0].lower()
        seg_end = out.index("\n", out.index("talents:", end))
        items = []
        for ti, tree in enumerate(trees[cls]):
            for k, x in enumerate(tree["t"]):
                if final[ti][k]:
                    items.append('["%s","%d/%d","%s"]' % (x["n"].replace('"', '\\"'), final[ti][k], x["m"], x["i"]))
        seg = re.sub(r"talents: t30\(\[.*\]\)", lambda mm: "talents: t30([" + ", ".join(items) + "])", out[end:seg_end], count=1, flags=re.S)
        out = out[:start] + out[start:end].replace('code: "%s"' % code, 'code: "%s"' % new, 1) + seg + out[seg_end:]
    open(path, "w", encoding="utf-8", newline="").write(out.replace("\n", nl))
    print("builds.html written")


if __name__ == "__main__":
    main()
