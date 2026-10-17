"""Our own item table (OWN_DATABASE_PLAN.md, milestone M0): every equippable weapon and armor of the beta with exact stats.

Inputs (all local, filled by `db2_pull.py` and `wh_tooltip_pull.py`, in bis/own/cache/):
  * the game's DB2 tables of one Forever build (Item, ItemSparse, RandPropPoints, ItemArmor*, ItemDamage*, ArmorLocation...)
  * Wowhead Forever's tooltip cache (tooltips.jsonl), for the items whose stats the client does not carry in its static files
    (the server sends them as hotfix data) and for cross-checking the DB2 numbers.

    python bis/tools/items_build.py            # build bis/items.json (+ a validation report on stdout)
    python bis/tools/items_build.py --report   # the report only

Record (short keys to keep the file small): id, n name, q quality 0-5, il item level, rl required level, inv inventory type,
c class id (2 weapon, 4 armor), s subclass id, st {stat id: value}, ar armor, dps, spd speed in seconds, src "db2" | "tip".
Stat ids follow the client (3 agility, 4 strength, 5 intellect, 6 spirit, 7 stamina, 45 spell power ...); `stats` in the file
maps every id that occurs to its label (read from the tooltips' own `<!--statN-->` markers).
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "bis" / "own" / "cache"
OUT = ROOT / "bis" / "items.json"
EQUIP_INV = {1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 25, 26, 28}
QUALITY_COL = {2: "Good", 3: "Superior", 4: "Epic"}
# RandPropPoints column group by inventory type (learned from the data, see the validation report)
SLOT_COL = {1: 0, 5: 0, 7: 0, 20: 0, 17: 0, 3: 1, 6: 1, 8: 1, 10: 1, 12: 1, 2: 2, 9: 2, 11: 2, 16: 2, 14: 2, 23: 2,
            13: 3, 21: 3, 22: 3, 15: 4, 25: 4, 26: 4, 28: 4}


def latest_build():
    d = CACHE / "db2"
    return sorted(d.iterdir(), key=lambda p: int(p.name.rsplit(".", 1)[1]))[-1]


def table(folder, name):
    p = folder / (name + ".csv")
    if not p.exists():
        return {}
    return {int(r["ID"]): r for r in csv.DictReader(open(p, encoding="utf-8"))}


def f(row, key, default=0.0):
    try:
        return float(row[key])
    except (KeyError, ValueError, TypeError):
        return default


def db2_items(folder):
    item, sparse = table(folder, "Item"), table(folder, "ItemSparse")
    rpp = table(folder, "RandPropPoints")
    armor_tot = {int(r["ItemLevel"]): r for r in table(folder, "ItemArmorTotal").values()}
    armor_q = table(folder, "ItemArmorQuality")
    armor_loc = table(folder, "ArmorLocation")
    out = {}
    for iid, it in item.items():
        inv = int(it["InventoryType"])
        if it["ClassID"] not in ("2", "4") or inv not in EQUIP_INV or iid not in sparse:
            continue
        sp = sparse[iid]
        q, il = int(sp["OverallQualityID"]), int(sp["ItemLevel"])
        rec = {"id": iid, "n": sp["Display_lang"], "q": q, "il": il, "rl": int(sp["RequiredLevel"]), "inv": inv,
               "c": int(it["ClassID"]), "s": int(it["SubclassID"]), "st": {}, "src": "db2"}
        row = rpp.get(il)
        if row and q in QUALITY_COL:
            budget = f(row, "%s_%d" % (QUALITY_COL[q], SLOT_COL.get(inv, 0)))
            for k in range(10):
                t = int(sp["StatModifier_bonusStat_%d" % k])
                pct = f(sp, "StatPercentEditor_%d" % k)
                if t != -1 and pct != 0:
                    v = int(round(pct * budget / 10000.0))
                    if t == 50:                    # bonus armor is added to the armor line, not a stat of its own
                        rec["bonusArmor"] = v
                    else:
                        rec["st"][str(t)] = v
        # armor: ItemArmorTotal[ilvl][material] x ItemArmorQuality[ilvl][quality] x ArmorLocation[inv][material]
        if rec["c"] == 4 and rec["s"] in (1, 2, 3, 4):
            mat = {1: "Cloth", 2: "Leather", 3: "Mail", 4: "Plate"}[rec["s"]]
            loc = armor_loc.get(5 if inv == 20 else inv)       # a robe wears like a chest piece
            tot, qm = armor_tot.get(il), armor_q.get(il)
            if loc and tot and qm:
                mod = f(loc, {"Cloth": "Clothmodifier", "Leather": "Leathermodifier", "Mail": "Chainmodifier", "Plate": "Platemodifier"}[mat])
                rec["ar"] = int(round(f(tot, mat) * f(qm, "Qualitymod_%d" % q) * mod))
        elif rec["c"] == 4 and rec["s"] == 6:
            shield = table(folder, "ItemArmorShield").get(il)
            if shield:
                rec["ar"] = int(round(f(shield, "Quality_%d" % q)))
        out[iid] = rec
    return out


def parse_tooltip(i, j):
    t = j.get("tooltip", "")
    rec = {"id": i, "n": j.get("name"), "q": j.get("quality"), "st": {}, "src": "tip"}
    m = re.search(r"<!--ilvl-->(\d+)", t)
    rec["il"] = int(m.group(1)) if m else 0
    m = re.search(r"<!--rlvl-->(\d+)", t)
    rec["rl"] = int(m.group(1)) if m else 0
    m = re.search(r"<!--scstart(\d+):(\d+)-->", t)
    if m:
        rec["c"], rec["s"] = int(m.group(1)), int(m.group(2))
    for sid, val, label in re.findall(r"<!--stat(\d+)-->([+-]\d+) ([^<]+)", t):
        rec["st"][sid] = int(val)
        rec.setdefault("_labels", {})[sid] = label.strip()
    m = re.search(r"<!--amr-->(\d+) Armor", t)
    if m:
        rec["ar"] = int(m.group(1))
    m = re.search(r"\(([\d.]+) damage per second\)", t)
    if m:
        rec["dps"] = float(m.group(1))
    m = re.search(r"<!--spd-->([\d.]+)", t)
    if m:
        rec["spd"] = float(m.group(1))
    # "Equip:" effects carry the client's stat id in a marker: <!--rtgN-->value. Wowhead numbers spell power 41, the client 45.
    for sid, val in re.findall(r"<!--rtg(\d+)-->\s*(\d+)", t):
        sid = "45" if sid == "41" else sid
        rec["st"][sid] = rec["st"].get(sid, 0) + int(val)
    res = re.findall(r"\+(\d+) (Fire|Frost|Nature|Shadow|Arcane|Holy) Resistance", t)
    if res:
        rec["res"] = {school: int(v) for v, school in res}
    equip = re.findall(r"Equip: ([^<]+)", t)
    if equip:
        rec["eq"] = [e.strip() for e in equip]
    return rec


def tooltip_items():
    p = CACHE / "tooltips.jsonl"
    out = {}
    if not p.exists():
        return out
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue            # a half-written last line while a pull is running
            if "j" in d:
                out[d["id"]] = parse_tooltip(d["id"], d["j"])
    return out


def compare(db, tip):
    """DB2-computed vs tooltip for the items we have both ways: this is the proof the budget model is right."""
    both = sorted(set(db) & set(tip))
    bad = defaultdict(list)
    ok = Counter()
    for i in both:
        a, b = db[i], tip[i]
        for key in ("q", "il", "rl"):
            if a.get(key) != b.get(key) and not (key == "rl" and not b.get(key)):
                bad[key].append(i)
            else:
                ok[key] += 1
        if a["st"] != b["st"]:
            bad["stats"].append(i)
        else:
            ok["stats"] += 1
        if "ar" in b:
            tot = a.get("ar", 0) + a.get("bonusArmor", 0)
            if abs(tot - b["ar"]) > 1:
                bad["armor"].append(i)
            else:
                ok["armor"] += 1
    return both, bad, ok


def main():
    folder = latest_build()
    db = db2_items(folder)
    tip = tooltip_items()
    print("DB2 build %s: %d equippable items with a static stat row; tooltip cache: %d items" % (folder.name, len(db), len(tip)))
    both, bad, ok = compare(db, tip)
    print("cross-check on %d items that exist both ways:" % len(both))
    for key in ("q", "il", "rl", "stats", "armor"):
        print("   %-6s agree %4d | differ %4d  %s" % (key, ok[key], len(bad[key]), bad[key][:6] if bad[key] else ""))
    # what do the misses look like?
    shown = 0
    for i in bad["stats"][:5]:
        print("   stats miss", i, db[i]["n"], "inv", db[i]["inv"], "ilvl", db[i]["il"], "q", db[i]["q"], "db2", db[i]["st"], "tooltip", tip[i]["st"])
    for i in bad["armor"][:4]:
        print("   armor miss", i, db[i]["n"], "inv", db[i]["inv"], "ilvl", db[i]["il"], "q", db[i]["q"], "db2", db[i].get("ar"), "+", db[i].get("bonusArmor"), "tooltip", tip[i].get("ar"))
    if "--report" in sys.argv:
        return 0
    labels = {}
    for r in tip.values():
        labels.update(r.pop("_labels", {}))
    merged = dict(tip)
    merged.update(db)                       # the client's own numbers win where we have them
    for r in merged.values():
        r.pop("_labels", None)
    items = [merged[i] for i in sorted(merged)]
    OUT.write_text(json.dumps({"build": folder.name, "stats": labels, "items": items}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("wrote %s: %d items (%d from DB2, %d from tooltips only), %d KB" % (OUT.name, len(items), len(db), len(set(tip) - set(db)), OUT.stat().st_size // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
