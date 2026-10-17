"""Our own ranking (OWN_DATABASE_PLAN.md, M1 first slice): per spec and slot, the best items of bis/items.json under a set of weights.

    python bis/tools/rank.py            # parity report against ForeverDB's best picks (bis/raw/*.json)
    python bis/tools/rank.py --misses   # also list every best pick that is not our number one
    python bis/tools/rank.py --level 60 # the launch pool (no reference lists exist for 60 yet, so no parity figure is meaningful)

Eligibility (class armor and weapon use, level cap, junk filter) lives here; the weights are an input (`weights_for`). For now the
weights come from ForeverDB's `weights` line so that the machinery can be tested against a known answer ("oracle weights");
M1b replaces them with weights derived from the game's spell and combat tables (plan section 4.2). Nothing else of ForeverDB is used.
"""
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import items_validate as V          # noqa: E402  (stat words, score)

ROOT = V.ROOT
LEVEL_CAP = 30            # --level 60 for the launch lists
MIN_QUALITY = 2
MAX_ILVL = 50            # the highest item level of any level-30 pick on the reference lists is 47; above that is raid / level 60 gear

CLASS_OF = {"priest": "PRIEST", "warlock": "WARLOCK", "mage": "MAGE", "rogue": "ROGUE", "druid": "DRUID", "shaman": "SHAMAN",
            "hunter": "HUNTER", "paladin": "PALADIN", "warrior": "WARRIOR"}
# Armor worn at the list's level (cloth 1, leather 2, mail 3, plate 4): the top tier opens at level 40, so at 30 Hunters and
# Shamans stop at leather, Warriors and Paladins at mail.
ARMOR_MAX = {"PRIEST": 1, "MAGE": 1, "WARLOCK": 1, "ROGUE": 2, "DRUID": 2, "HUNTER": 2, "SHAMAN": 2, "PALADIN": 3, "WARRIOR": 3}
ARMOR_MAX_40 = {"HUNTER": 3, "SHAMAN": 3, "PALADIN": 4, "WARRIOR": 4}      # from level 40 (mail for Hunters / Shamans, plate)
# Forever's class weapon table (same as addon/RoadToForever/QuestWeapons.lua); item subclass id -> kind
KIND = {0: "1h axe", 1: "2h axe", 2: "bow", 3: "gun", 4: "1h mace", 5: "2h mace", 6: "polearm", 7: "1h sword", 8: "2h sword",
        10: "staff", 13: "fist", 15: "dagger", 16: "thrown", 18: "crossbow", 19: "wand"}
_KINDS = ["1h axe", "2h axe", "1h mace", "2h mace", "1h sword", "2h sword", "dagger", "fist", "polearm", "staff", "bow", "gun",
          "crossbow", "thrown", "wand", "shield"]
_USE_TEXT = {
    "WARRIOR": "1h axe 2h axe 1h mace 2h mace 1h sword 2h sword dagger fist polearm staff bow gun crossbow thrown shield",
    "PALADIN": "1h axe 2h axe 1h mace 2h mace 1h sword 2h sword polearm shield",
    "HUNTER": "1h axe 2h axe 1h sword 2h sword dagger fist polearm staff bow gun crossbow thrown",
    "ROGUE": "dagger fist 1h axe 1h mace 1h sword bow gun crossbow thrown",
    "PRIEST": "dagger 1h mace staff wand", "MAGE": "dagger 1h sword staff wand", "WARLOCK": "dagger 1h sword staff wand",
    "DRUID": "dagger fist 1h mace 2h mace polearm staff", "SHAMAN": "1h axe 2h axe 1h mace 2h mace dagger fist staff shield",
}
USE = {c: {k for k in _KINDS if re.search(r"(?<![\w])" + re.escape(k) + r"(?![\w])", txt)} for c, txt in _USE_TEXT.items()}
DUAL_WIELD = {"WARRIOR", "ROGUE", "HUNTER", "SHAMAN"}
# slot name (ForeverDB's rows) -> inventory types
SLOT_INV = {"Head": {1}, "Neck": {2}, "Shoulder": {3}, "Back": {16}, "Chest": {5, 20}, "Wrist": {9}, "Hands": {10}, "Waist": {6},
            "Legs": {7}, "Feet": {8}, "Finger": {11}, "Trinket": {12}, "Main hand": {13, 17, 21}, "Off hand": {13, 14, 22, 23},
            "Ranged or relic": {15, 25, 26, 28}}
JUNK = re.compile(r"Testing|QATest|^(Test|TEST)|\bTEST\b|^Monster|^\d+ (Epic|Rare|Green)|JEFF|Deprecated|\bPH\b|^zz|Unused|\(old\)|Reuse|^Dummy", re.I)


def eligible(rec, cls, slot):
    if rec.get("q", 0) < MIN_QUALITY or rec.get("rl", 0) > LEVEL_CAP or rec.get("il", 0) > MAX_ILVL or JUNK.search(rec.get("n") or ""):
        return False
    inv = rec.get("inv")
    if inv not in SLOT_INV[slot]:
        return False
    c, s = rec.get("c"), rec.get("s")
    if c == 4:
        if s in (1, 2, 3, 4):
            # cloth / leather / mail / plate; rings, necks, cloaks are "cloth" (subclass 0 or 1) and fit everyone
            top = ARMOR_MAX_40.get(cls, ARMOR_MAX[cls]) if LEVEL_CAP >= 40 else ARMOR_MAX[cls]
            return s <= top or inv in (2, 11, 12, 16)
        if s == 6:
            return "shield" in USE[cls]
        return s in (0, 8) or (s in (7, 9, 10, 11) and inv == 28)       # misc, relics (class check is not modelled yet)
    if c == 2:
        kind = KIND.get(s)
        if kind not in USE[cls]:
            return False
        if slot == "Main hand":
            return inv in (13, 17, 21)
        if slot == "Off hand":
            return inv == 13 and cls in DUAL_WIELD or inv in (14, 22, 23)
        return slot == "Ranged or relic" and inv in (15, 25, 26)
    return slot == "Ranged or relic" and inv == 28 or (c is None and False)


def weights_for(spec, raw):
    return V.weights_of(raw["weights"])


def rank(spec, slot, w, cls, pool):
    out = []
    for rec in pool:
        if eligible(rec, cls, slot):
            out.append((V.score(V.our_stats(rec, spec, slot), w), rec))
    out.sort(key=lambda t: (-t[0], t[1]["id"]))
    return out


def set_level(level):
    """Level 60 lists: every item up to the cap, no item-level ceiling (the 30 ceiling only keeps raid / level 60 gear out)."""
    global LEVEL_CAP, MAX_ILVL
    LEVEL_CAP = level
    MAX_ILVL = 50 if level <= 30 else 10 ** 6


def main():
    if "--level" in sys.argv:
        set_level(int(sys.argv[sys.argv.index("--level") + 1]))
    pool = [r for r in V.ITEMS["items"] if "c" in r]
    top1 = top3 = rows = 0
    misses = []
    excluded = []
    outscored = 0
    for f in sorted(glob.glob(str(ROOT / "bis" / "raw" / "*.json"))):
        spec = Path(f).stem
        cls = CLASS_OF[spec.split("-")[0]]
        raw = json.load(open(f, encoding="utf-8"))
        w = weights_for(spec, raw)
        taken = {}
        for s in raw["slots"]:
            b = s.get("best")
            if not b:
                continue
            slot = s["slot"]
            ranked = rank(spec, slot, w, cls, pool)
            n = taken.get(slot, 0)               # second ring / trinket row: compare with our second place
            taken[slot] = n + 1
            rows += 1
            ids = [r["id"] for _, r in ranked[:3 + n]]
            if len(ranked) > n and ranked[n][1]["id"] == b["id"] or (slot in ("Finger", "Trinket") and b["id"] in ids[:2]):
                top1 += 1
            if b["id"] in ids:
                top3 += 1
            else:
                rec = V.BY_ID.get(b["id"])
                if rec is None or not eligible(rec, cls, slot):
                    excluded.append((spec, slot, b["id"], b["name"], rec and (rec.get("q"), rec.get("rl"), rec.get("il"), rec.get("c"), rec.get("s"), rec.get("inv"))))
                else:
                    outscored += 1
                misses.append((spec, slot, b["id"], b["name"], b["score"], [(round(sc, 1), r["n"]) for sc, r in ranked[:3]]))
    print("%d best-pick rows: ForeverDB's pick is our #1 in %d (%.0f%%), in our top 3 in %d (%.0f%%)" % (
        rows, top1, 100.0 * top1 / rows, top3, 100.0 * top3 / rows))
    print("of the %d rows outside our top 3: %d are picks our eligibility rules exclude (see --excluded), %d are eligible but out-scored by "
          "items that ForeverDB does not list (we have no source data yet, so unobtainable or off-route items compete)" % (
              rows - top3, len(excluded), outscored))
    if "--excluded" in sys.argv:
        for e in excluded:
            print("  ", e)
    if "--misses" in sys.argv:
        for m in misses:
            print("  ", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
