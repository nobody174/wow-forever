"""Cross-check 1: do the stats we read from Wowhead reproduce ForeverDB's scores for the items on its own BiS pages?

For every best pick in bis/raw/*.json: stats from the Wowhead tooltip x the spec's weights, against ForeverDB's printed `score` (and its
printed `stats` line). Prints the items that disagree. Run:  python bis/own/check_scores.py
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats import parse          # noqa: E402
from tooltips import get_many    # noqa: E402

RAW = os.path.join(HERE, "..", "raw")


def weights_of(text):
    w = {}
    for part in text.split(","):
        m = re.match(r"\s*(.+?)\s+(\d+(?:\.\d+)?)\.?\s*$", part)
        if m:
            w[m.group(1)] = float(m.group(2))
    return w


# ForeverDB turns the percent stats into a rating-like number before it weighs them (1.0% hit = 10; crit and haste to be found out)
CONV = {"hit": 10.0, "crit": 14.0}


def counts_dps(spec, slot):
    """ForeverDB counts a weapon's DPS in the main hand / off hand of melee specs and in the ranged slot of Hunters only."""
    if slot in ("Main hand", "Off hand"):
        return not spec.startswith("hunter")
    return slot == "Ranged or relic" and spec.startswith("hunter")


def score(st, w, conv, spec="", slot=""):
    total = 0.0
    for k, v in st.items():
        if k == "weapon DPS" and not counts_dps(spec, slot):
            continue
        total += w.get(k, 0) * v * conv.get(k, 1)
    return total


def main():
    specs = {}
    ids = []
    for f in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        specs[os.path.basename(f)[:-5]] = d
        for s in d["slots"]:
            if s.get("best"):
                ids.append(s["best"]["id"])
    tips = get_many(ids)
    bad = 0
    unk = {}
    for name, d in specs.items():
        w = weights_of(d["weights"])
        for s in d["slots"]:
            b = s.get("best")
            if not b or b["id"] not in tips:
                continue
            st, unknown = parse(tips[b["id"]]["tooltip"])
            for u in unknown:
                unk.setdefault(u, []).append(b["id"])
            mine = round(score(st, w, CONV, name, s["slot"]), 1)
            if abs(mine - b["score"]) > max(0.15, 0.04 * b["score"]):
                bad += 1
                print("%-22s %-10s %-34s theirs %-6s ours %-6s | %s | %s" % (name, s["slot"], b["name"][:34], b["score"], mine, b["stats"], st))
    print("\n%d best picks differ" % bad)
    print("unrecognised equip lines (%d):" % len(unk))
    for u, v in sorted(unk.items(), key=lambda kv: -len(kv[1]))[:25]:
        print("  %3d  %s  (e.g. %d)" % (len(v), u[:110], v[0]))


if __name__ == "__main__":
    main()
