#!/usr/bin/env python3
"""Compare the WCLBox pull with bis/items.json (read-only) and write bis/own/wclbox-diff.md.

    python bis/tools/wclbox_diff.py

Part of docs/wclbox-migration-plan.md, phase 2. Needs the cache from wclbox_pull.py.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wcl_parse import parse_detail  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "bis" / "own" / "cache" / "wclbox"
OUT = ROOT / "bis" / "own" / "wclbox-diff.md"
QN = {0: "grey", 1: "white", 2: "green", 3: "blue", 4: "epic", 5: "legendary"}
STATS = {"3": "agility", "4": "strength", "5": "intellect", "6": "spirit", "7": "stamina"}


def jl(p):
    out = []
    for line in open(p, encoding="utf-8"):
        try:
            out.append(json.loads(line))
        except ValueError:
            pass            # half-written last line while a pull runs
    return out


def main():
    meta = json.load(open(CACHE / "meta.json", encoding="utf-8"))
    lst = {d["id"]: d for d in jl(CACHE / "list.jsonl")}
    det = {d["id"]: d for d in jl(CACHE / "detail.jsonl")}
    BEFORE = ROOT / "bis" / "own" / "cache" / "before" / "items.git.json"
    old = json.load(open(BEFORE if BEFORE.exists() else ROOT / "bis" / "items.json", encoding="utf-8"))
    oi = {r["id"]: r for r in old["items"]}
    new = {i: parse_detail(d) for i, d in det.items()}
    L = []
    L.append("# WCLBox vs bis/items.json\n")
    L.append("WCLBox build %s | our table build %s | WCLBox list %d items, detail (weapons+armor) %d | our table %d items\n"
             % (meta.get("build") or meta, old.get("build"), len(lst), len(det), len(oi)))
    # coverage
    gear_ids = {i for i, d in lst.items() if d.get("classId") in (2, 4)}
    pulled_q = Counter(QN.get(d["quality"]) for d in det.values())
    missing = [i for i in oi if i not in lst]
    L.append("## Coverage")
    L.append("- ids in our table but not in the WCLBox list: **%d of %d** (%.0f%%)" % (len(missing), len(oi), 100.0 * len(missing) / len(oi)))
    L.append("  - by quality: %s" % dict(Counter(QN.get(oi[i]["q"]) for i in missing)))
    L.append("  - sample: %s" % ", ".join("%d %s" % (i, oi[i]["n"]) for i in missing[:12]))
    L.append("- pulled detail by quality: %s (gear in the list: %d; the pull may have skipped grey/white)" % (dict(pulled_q), len(gear_ids)))
    nonew = [i for i in det if i not in oi and new[i]["inv"] not in (None, 4, 19)]
    L.append("- ids new in WCLBox (gear detail, not in our table): **%d**" % len(nonew))
    L.append("  - by slot: %s" % dict(Counter(det[i]["slot"] for i in nonew).most_common(12)))
    L.append("  - by quality: %s\n" % dict(Counter(QN.get(det[i]["quality"]) for i in nonew)))
    # field diffs
    both = [i for i in det if i in oi]
    diffs = defaultdict(list)
    for i in both:
        a, b = oi[i], new[i]
        if a["q"] != b["q"]:
            diffs["quality"].append((i, a["q"], b["q"]))
        if a["il"] != b["il"]:
            diffs["item level"].append((i, a["il"], b["il"]))
        if a["rl"] != b["rl"]:
            diffs["required level"].append((i, a["rl"], b["rl"]))
        for sid, name in STATS.items():
            if a["st"].get(sid, 0) != b["st"].get(sid, 0):
                diffs[name].append((i, a["st"].get(sid, 0), b["st"].get(sid, 0)))
        other_a = {k: v for k, v in a["st"].items() if k not in STATS and k != "50"}
        other_b = {k: v for k, v in b["st"].items() if k not in STATS and k != "50"}
        if other_a != other_b:
            diffs["other stats (spell power, crit, ...)"].append((i, other_a, other_b))
        if a.get("ar", 0) != b.get("ar", 0):
            diffs["armor"].append((i, a.get("ar", 0), b.get("ar", 0)))
        if "dps" in a or "dps" in b:
            if abs(a.get("dps", 0) - b.get("dps", 0)) > 0.05:
                diffs["dps"].append((i, a.get("dps"), b.get("dps")))
    L.append("## Differences on %d ids in both" % len(both))
    L.append("| field | differs |\n|---|---|")
    for k in ("quality", "item level", "required level", *STATS.values(), "other stats (spell power, crit, ...)", "armor", "dps"):
        L.append("| %s | %d |" % (k, len(diffs[k])))
    L.append("")
    for k, rows in diffs.items():
        L.append("### %s (up to 20 of %d)" % (k, len(rows)))
        L.append("id | name | ours | WCLBox | our src")
        L.append("---|---|---|---|---")
        for i, a, b in rows[:20]:
            L.append("%d | %s | %s | %s | %s" % (i, oi[i]["n"], a, b, oi[i].get("src")))
        L.append("")
    # explain armor / dps
    L.append("## Armor and dps mismatch analysis")
    for k in ("armor", "dps"):
        rows = diffs[k]
        bysrc = Counter(oi[i].get("src") for i, _, _ in rows)
        tot = Counter(oi[i].get("src") for i in both if (("ar" if k == "armor" else "dps") in oi[i] or ("ar" if k == "armor" else "dps") in new[i]))
        ratios = [round(b / a, 3) for _, a, b in rows if a and b]
        L.append("- %s: %d differ; by our src %s (of %s with a value); ratio WCLBox/ours: %s" % (k, len(rows), dict(bysrc), dict(tot), ratios[:15]))
    arm = Counter()
    for i, a, b in diffs["armor"]:
        arm["explained: our armor + our bonusArmor == WCLBox total" if a + oi[i].get("bonusArmor", 0) == b
            else "WCLBox status " + str(det[i].get("status"))] += 1
    L.append("- armor cause: %s (the old table kept bonus armor apart, WCLBox prints one total)" % dict(arm))
    L.append("- dps cause: our DB2-computed dps is an estimate (ratios 0.93 to 1.1); WCLBox prints the game's value. Wowhead-sourced "
             "differences are rounding (14.55 vs 14.5) or items changed in the live build.")
    L.append("- spell power/healing missing in WCLBox on many staves and weapons: the live build removed them (e.g. Rod of the Sleepwalker).")
    # status flags in Mr.BiZ picks
    bis = json.load(open(ROOT / "bis-data.json", encoding="utf-8"))
    ids = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("id", "item") and isinstance(v, int):
                    ids.add(v)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(bis)
    flagged = [(i, lst[i]["status"], lst[i].get("nameEn")) for i in ids if i in lst and lst[i].get("status") in ("changed", "new")]
    gone = [i for i in ids if i not in lst]
    L.append("\n## Mr.BiZ picks (%d distinct ids in bis-data.json)" % len(ids))
    L.append("- flagged `changed`/`new` by WCLBox: %d (%s)" % (len(flagged), dict(Counter(s for _, s, _ in flagged))))
    L.append("- not in WCLBox at all: %d" % len(gone))
    for i, s, n in flagged[:40]:
        L.append("  - %d %s: %s" % (i, n, s))
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
