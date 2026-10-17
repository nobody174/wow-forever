"""Validate our item table (bis/items.json) against ForeverDB: for every item on its BiS pages (best picks and the two next picks that
carry stats), our stats x the spec's weights must give ForeverDB's printed score. Part of OWN_DATABASE_PLAN.md milestone M0.

    python bis/tools/items_validate.py            # summary + the items that disagree
    python bis/tools/items_validate.py --all      # every row

ForeverDB prints one `score` per best pick (ranks 2-3 only a % behind), so only best picks can be checked exactly.
Units: ForeverDB weighs hit / crit as ratings (1.0% hit = 10, crit = 14), which is also how items.json stores them.
"""
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS = json.loads((ROOT / "bis" / "items.json").read_text(encoding="utf-8"))
BY_ID = {r["id"]: r for r in ITEMS["items"]}

# client stat id -> the word ForeverDB's weights use
WORD = {"3": "Agility", "4": "Strength", "5": "Intellect", "6": "Spirit", "7": "Stamina", "12": "defense", "13": "dodge",
        "14": "parry", "15": "block", "31": "hit", "32": "crit", "36": "haste", "37": "expertise", "38": "attack power",
        "41": "healing", "42": "spell damage", "43": "mana per 5 sec", "45": "spell power", "84": "Holy Damage Done",
        "85": "Fire Damage Done", "86": "Nature Damage Done", "87": "Frost Damage Done", "88": "Shadow Damage Done",
        "89": "Arcane Damage Done", "50": "Bonus Armor"}


def weights_of(text):
    w = {}
    for part in text.split(","):
        m = re.match(r"\s*(.+?)\s+(\d+(?:\.\d+)?)\.?\s*$", part)
        if m:
            w[m.group(1)] = float(m.group(2))
    return w


def counts_dps(spec, slot):
    if slot in ("Main hand", "Off hand"):
        return not spec.startswith("hunter")
    return slot == "Ranged or relic" and spec.startswith("hunter")


def our_stats(rec, spec, slot):
    out = {}
    for sid, v in rec["st"].items():
        if sid in WORD:
            out[WORD[sid]] = out.get(WORD[sid], 0) + v
    if rec.get("ar") is not None:
        out["armor"] = rec["ar"]
    if rec.get("bonusArmor"):
        out["Bonus Armor"] = rec["bonusArmor"]
    if rec.get("dps") and counts_dps(spec, slot):
        out["weapon DPS"] = rec["dps"]
    return out


def score(st, w):
    return sum(w.get(k, 0) * v for k, v in st.items())


def main():
    show_all = "--all" in sys.argv
    rows = bad = missing = 0
    seen_ids, seen_bad = set(), set()
    reasons = {}
    for f in sorted(glob.glob(str(ROOT / "bis" / "raw" / "*.json"))):
        spec = Path(f).stem
        d = json.load(open(f, encoding="utf-8"))
        w = weights_of(d["weights"])
        for s in d["slots"]:
            b = s.get("best")
            if not b:
                continue
            rows += 1
            seen_ids.add(b["id"])
            rec = BY_ID.get(b["id"])
            if rec is None:
                missing += 1
                reasons.setdefault("not in our table", []).append((spec, s["slot"], b["id"], b["name"]))
                continue
            mine = round(score(our_stats(rec, spec, s["slot"]), w), 1)
            theirs = b["score"]
            if abs(mine - theirs) > max(0.15, 0.04 * theirs):
                bad += 1
                seen_bad.add(b["id"])
                why = "weapon without dps" if rec.get("c") == 2 and not rec.get("dps") else (
                    "unknown equip text" if rec.get("unk") else "stats differ")
                reasons.setdefault(why, []).append((spec, s["slot"], b["id"], b["name"], theirs, mine, b["stats"], rec["st"]))
            elif show_all:
                print("ok  %-24s %-14s %-34s %6s %6s" % (spec, s["slot"], b["name"][:34], theirs, mine))
    print("%d best-pick rows, %d distinct items; %d rows agree with ForeverDB's score, %d differ, %d items missing from our table" % (
        rows, len(seen_ids), rows - bad - missing, bad, missing))
    for why, lst in reasons.items():
        print("\n%s: %d rows" % (why, len(lst)))
        for r in lst[:40]:
            print("  ", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
