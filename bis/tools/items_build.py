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
        if rec["c"] == 2:
            d = weapon_dps(folder, rec, sp)
            if d:
                rec["dps"], rec["spd"] = d
        out[iid] = rec
    return out


RANGED_K = 0.772        # bows, guns, crossbows: the beta prints about 77% of the one-hand damage table (measured, see the report)
_dmg = {}


def weapon_dps(folder, rec, sp):
    """Damage per second from the item-level damage tables x quality (the 1h / 2h / wand / thrown table by weapon kind)."""
    inv, sub = rec["inv"], rec["s"]
    name = ("ItemDamageTwoHand" if inv == 17 else "ItemDamageWand" if sub == 19 else "ItemDamageThrown" if sub == 16
            else "ItemDamageOneHand")
    if name not in _dmg:
        _dmg[name] = {int(r["ItemLevel"]): r for r in table(folder, name).values()}
    row = _dmg[name].get(rec["il"])
    delay = f(sp, "ItemDelay") / 1000.0
    if not row or delay <= 0:
        return None
    v = f(row, "Quality_%d" % rec["q"])
    if sub in (2, 3, 18):
        v *= RANGED_K
    return round(v, 1), delay


# "Equip:" sentence -> (client stat id, scale). The number in the sentence times the scale is the stored value (ratings: hit 10 per
# 1%, crit 14, block 5, dodge 12, parry 20 in Classic; the first three measured on Forever items, the last two from Classic).
# None in the id slot = a sentence that is known and carries no stat for gear scoring (procs, skills, professions).
SCHOOL_STAT = {"Holy": "84", "Fire": "85", "Nature": "86", "Frost": "87", "Shadow": "88", "Arcane": "89"}
RES_STAT = {"Fire": "51", "Frost": "52", "Holy": "53", "Shadow": "54", "Nature": "55", "Arcane": "56"}   # Holy assumed (no sample)
EQUIP_RULES = [
    (r"^Increases damage and healing done by magical spells and effects by up to (\d+)", "45", 1),
    (r"^Increases damage done by magical spells and effects by up to (\d+)", "45", 1),
    (r"^Increases healing done by (?:magical )?spells and effects by up to (\d+)", "41", 1),
    (r"^Increases healing done by up to (\d+)(?!\s+and)", "41", 1),
    (r"^Improves your chance to get a critical strike by ([\d.]+)%", "32", 14),
    (r"^Improves your chance to hit by ([\d.]+)%", "31", 10),
    (r"^Decreases your chance to hit by ([\d.]+)%", "31", -10),
    (r"^Increases your chance to Block attacks with a shield by ([\d.]+)%", "15", 5),
    (r"^Increases your chance to Dodge an attack by ([\d.]+)%", "13", 12),
    (r"^Increases your chance to Parry an attack by ([\d.]+)%", "14", 20),
    (r"^Increased Defense \+(\d+)", "12", 1),
    (r"^\+(\d+) Attack Power\.?$", "38", 1),
    (r"^\+(\d+) Attack Power (?:when|against|in )", "", 0),
    (r"^Increases your attack speed and casting speed by ([\d.]+)%", "36", 10),
    (r"^Reduces chance to be Dodged or Parried by ([\d.]+)%", "37", 10),
    (r"^Increases damage done to \w+ by magical spells and effects by up to (\d+)", "", 0),
    (r"^Increased (Two-Handed Axes|Daggers|Polearms|Swords|Fishing|Mining|Herbalism|Skinning) \+(\d+)", "", 0),
    (r"^Your spells pierce (\d+) (\w+) Resistance", "", 0),
]


def equip_rule(sentence):
    """-> (stat id, value), () for a known sentence without a gear stat, None when no rule knows it."""
    m = re.match(r"^Increases damage done by (Holy|Fire|Nature|Frost|Shadow|Arcane) spells and effects by up to (\d+)", sentence)
    if m:
        return (SCHOOL_STAT[m.group(1)], int(m.group(2)))
    m = re.match(r"^Increases healing done by up to (\d+) and damage done by up to (\d+) for all magical spells", sentence)
    if m:
        return (("41", int(m.group(1))), ("42", int(m.group(2))))
    for pat, sid, scale in EQUIP_RULES:
        m = re.match(pat, sentence)
        if m:
            if not sid:
                return ()
            return (sid, int(round(float(m.group(1)) * scale)))
    return None


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
    res = re.findall(r"\+(\d+) (Fire|Frost|Nature|Shadow|Arcane|Holy) Resistance", t)
    if res:
        rec["res"] = {school: int(v) for v, school in res}
        for school, v in rec["res"].items():
            rec["st"][RES_STAT[school]] = v
    m = re.search(r"Restores \+?(\d+) mana per 5 sec", re.sub(r"<[^>]+>", "", t))
    if m:
        rec["st"]["43"] = int(m.group(1))
    equip, unknown = [], []
    for m in re.finditer(r"Equip: (.*?)(?:<br>|<!--itemEffects|<div)", t, re.S):
        sentence = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        equip.append(sentence)
        stat = equip_rule(sentence)
        if stat is None and "<!--rtg" in m.group(1):
            # no sentence rule: take the client's own stat id from the marker (Wowhead's id 41 is ambiguous, so rules come first)
            for sid, val in re.findall(r"<!--rtg(\d+)-->\s*(\d+)", m.group(1)):
                rec["st"][sid] = rec["st"].get(sid, 0) + int(val)
        elif stat is None:
            unknown.append(sentence)
        elif stat:
            for sid, val in (stat if isinstance(stat[0], tuple) else (stat,)):
                rec["st"][sid] = rec["st"].get(sid, 0) + val
    if equip:
        rec["eq"] = equip
    if unknown:
        rec["unk"] = unknown
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
        bst = {k: v for k, v in b["st"].items() if k != "50"}      # bonus armor: the tooltip lists it as a stat, we keep it apart
        if a["st"] != bst:
            bad["stats"].append(i)
        else:
            ok["stats"] += 1
        if "dps" in b and "dps" in a:
            if abs(a["dps"] - b["dps"]) > max(0.6, 0.04 * b["dps"]):
                bad["dps"].append(i)
            else:
                ok["dps"] += 1
        if "ar" in b:
            tot = a.get("ar", 0)
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
    for key in ("q", "il", "rl", "stats", "armor", "dps"):
        print("   %-6s agree %4d | differ %4d  %s" % (key, ok[key], len(bad[key]), bad[key][:6] if bad[key] else ""))
    # what do the misses look like?
    shown = 0
    for i in bad["stats"][:5]:
        print("   stats miss", i, db[i]["n"], "inv", db[i]["inv"], "ilvl", db[i]["il"], "q", db[i]["q"], "db2", db[i]["st"], "tooltip", {k: v for k, v in tip[i]["st"].items() if k != "50"})
    for i in bad["armor"][:4]:
        print("   armor miss", i, db[i]["n"], "inv", db[i]["inv"], "ilvl", db[i]["il"], "q", db[i]["q"], "db2", db[i].get("ar"), "+", db[i].get("bonusArmor"), "tooltip", tip[i].get("ar"))
    if "--report" in sys.argv:
        return 0
    labels = {}
    for r in tip.values():
        labels.update(r.pop("_labels", {}))
    merged = dict(tip)
    for i, rec in db.items():               # the client's own numbers win where we have them; the tooltip adds what DB2 lacks
        extra = {k: v for k, v in tip.get(i, {}).items() if k in ("dps", "spd", "eq", "unk", "res")}
        merged[i] = dict(extra, **rec)
        # "Equip:" effects and mana per 5 sec come from spells, not from the static stat rows: add what DB2 lacks from the tooltip
        if i in tip:
            merged[i]["st"] = dict(tip[i]["st"], **rec["st"])
            merged[i]["st"].pop("50", None)
    for r in merged.values():
        r.pop("_labels", None)
    items = [merged[i] for i in sorted(merged)]
    OUT.write_text(json.dumps({"build": folder.name, "stats": labels, "items": items}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("wrote %s: %d items (%d from DB2, %d from tooltips only), %d KB" % (OUT.name, len(items), len(db), len(set(tip) - set(db)), OUT.stat().st_size // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
