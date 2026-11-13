"""Our own item table: every equippable weapon and armor of the live game build, from WCLBox's open item API.

Input (local, filled by `wclbox_pull.py` into bis/own/cache/wclbox/): the item list and the detail of every weapon and armor.
Source: 新手盒子·魔兽世界无限数据库 (WCLBox), https://wowforever.wclbox.com. Parsing of the tooltip text is in wcl_parse.py.

    python bis/tools/items_build.py            # build bis/items.json and bis/quality.json
    python bis/tools/items_build.py --report   # print counts only, write nothing

Record (short keys to keep the file small): id, n name, q quality 0-5, il item level, rl required level, inv inventory type,
c class id (2 weapon, 4 armor), s subclass id, st {stat id: value}, ar armor, dps, spd speed in seconds, src "wcl".
Stat ids follow the client (3 agility, 4 strength, 5 intellect, 6 spirit, 7 stamina, 45 spell power ...); `stats` in the file
maps every id that occurs to its label. quality.json holds the rarity of every Mr.BiZ item (read from the WCLBox list).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "bis" / "own" / "cache" / "wclbox"
OUT = ROOT / "bis" / "items.json"
QUALITY = ROOT / "bis" / "quality.json"
EQUIP_INV = {1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 25, 26, 28}
STAT_LABEL = {"3": "Agility", "4": "Strength", "5": "Intellect", "6": "Spirit", "7": "Stamina", "12": "Defense", "13": "Dodge",
              "14": "Parry", "15": "Block", "31": "Hit", "32": "Crit", "36": "Haste", "37": "Expertise", "38": "Attack Power",
              "41": "Healing", "42": "Spell damage", "43": "Mana per 5 sec", "45": "Spell Power", "50": "Armor",
              "51": "Fire Resistance", "52": "Frost Resistance", "53": "Holy Resistance", "54": "Shadow Resistance",
              "55": "Nature Resistance", "56": "Arcane Resistance", "84": "Holy Damage", "85": "Fire Damage",
              "86": "Nature Damage", "87": "Frost Damage", "88": "Shadow Damage", "89": "Arcane Damage"}


# "Equip:" sentence -> (client stat id, scale). The number in the sentence times the scale is the stored value (ratings: hit 10 per
# 1%, crit 14, block 5, dodge 12, parry 20 in Classic; the first three measured on Forever items, the last two from Classic).
# None in the id slot = a sentence that is known and carries no stat for gear scoring (procs, skills, professions).
SCHOOL_STAT = {"Holy": "84", "Fire": "85", "Nature": "86", "Frost": "87", "Shadow": "88", "Arcane": "89"}
# the slot word at the top of a Wowhead tooltip -> the client's inventory type
SLOT_NAME_INV = {"Head": 1, "Neck": 2, "Shoulder": 3, "Chest": 5, "Robe": 20, "Waist": 6, "Legs": 7, "Feet": 8, "Wrist": 9,
                 "Hands": 10, "Finger": 11, "Trinket": 12, "One-Hand": 13, "Shield": 14, "Bow": 15, "Back": 16, "Two-Hand": 17,
                 "Held In Off-hand": 23, "Gun": 26, "Crossbow": 26, "Wand": 26, "Thrown": 25, "Main Hand": 21, "Off Hand": 22,
                 "Relic": 28, "Ranged": 26, "Idol": 28, "Libram": 28, "Totem": 28}
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


def jl(p):
    out = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass            # half-written last line while a pull is running
    return out


def main():
    if not (CACHE / "detail.jsonl").exists():
        print("no WCLBox cache in %s: run bis/tools/wclbox_pull.py first" % CACHE)
        return 1
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from wcl_parse import parse_detail
    meta = json.loads((CACHE / "meta.json").read_text(encoding="utf-8"))
    items, skipped = {}, 0
    for d in jl(CACHE / "detail.jsonl"):
        rec = parse_detail(d)
        if rec["inv"] not in EQUIP_INV or rec["s"] is None:
            skipped += 1
            continue
        items[rec["id"]] = rec
    labels = {sid: STAT_LABEL.get(sid, sid) for r in items.values() for sid in r["st"]}
    print("WCLBox build %s: %d equippable items (%d details skipped: shirts, tabards, unknown type)"
          % (meta.get("build"), len(items), skipped))
    unk = sum(1 for r in items.values() if r.get("unk"))
    print("%d items carry an Equip: sentence no rule knows (kept in `unk`)" % unk)
    if "--report" in sys.argv:
        return 0
    rows = [items[i] for i in sorted(items)]
    OUT.write_text(json.dumps({"build": meta.get("build"), "stats": labels, "items": rows}, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print("wrote %s: %d items, %d KB" % (OUT.name, len(rows), OUT.stat().st_size // 1024))
    write_quality(meta)
    return 0


def write_quality(meta):
    """bis/quality.json: rarity of every item named in bis-data.json (the picks), from the WCLBox list."""
    bis = ROOT / "bis-data.json"
    if not bis.exists():
        return
    ids = sorted({r["id"] for r in json.loads(bis.read_text(encoding="utf-8"))["rows"]})
    q = {d["id"]: d["quality"] for d in jl(CACHE / "list.jsonl")}
    out = {str(i): q[i] for i in ids if i in q}
    data = {"_about": "Item quality (0 poor .. 5 legendary) for every Mr.BiZ item, so names are coloured before the game has the item "
                      "cached. Read from the WCLBox open item API (wowforever.wclbox.com) by bis/tools/items_build.py. build_bis.py "
                      "adds `q` to each row and warns about ids missing here (run items_build.py again after a re-rank).",
            "updated": str(meta.get("build")), "quality": out}
    QUALITY.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote %s: %d of %d ids" % (QUALITY.name, len(out), len(ids)))


if __name__ == "__main__":
    sys.exit(main())
