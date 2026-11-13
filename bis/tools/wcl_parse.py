"""Turn a WCLBox item detail (bis/own/cache/wclbox/detail.jsonl line) into our items.json record.

Shared by wclbox_diff.py and items_build.py. The detail carries `tooltipEn`, a list of plain-text lines such as
"Feet\tCloth", "2 Armor", "+8 Strength", "Equip: Increases healing done ...", "(20.5 damage per second)".
Record keys: id, n, q, il, rl, inv, c, s, st {stat id: value}, ar, dps, spd, eq, unk, src "wcl".
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from items_build import SLOT_NAME_INV, RES_STAT, equip_rule  # noqa: E402  (the rules stay in one place)

BASE_STAT = {"Agility": "3", "Strength": "4", "Intellect": "5", "Spirit": "6", "Stamina": "7"}
WEAPON_SUB = {"One-Handed Axes": 0, "Two-Handed Axes": 1, "Bows": 2, "Guns": 3, "One-Handed Maces": 4, "Two-Handed Maces": 5,
              "Polearms": 6, "One-Handed Swords": 7, "Two-Handed Swords": 8, "Staves": 10, "Staff": 10, "Fist Weapons": 13,
              "Miscellaneous": 14, "Daggers": 15, "Dagger": 15, "Bow": 2, "Crossbow": 18, "Gun": 3, "Polearm": 6, "Wand": 19,
              "Fist Weapon": 13, "Fishing Pole": 20, "Thrown": 16, "Crossbows": 18, "Wands": 19, "Fishing Poles": 20}
ARMOR_SUB = {"Miscellaneous": 0, "Cloth": 1, "Leather": 2, "Mail": 3, "Plate": 4, "Shield": 6, "Shields": 6, "Libram": 7, "Idol": 8, "Totem": 9, "Librams": 7, "Idols": 8,
             "Totems": 9}
SLOT_EXTRA = {"Waist": 6, "Held In Off-Hand": 23, "Off Hand": 22, "Main Hand": 21, "One-Hand": 13, "Two-Hand": 17,
              "Ranged": 26, "Ranged Right": 26, "Shield": 14, "Back": 16, "Trinket": 12, "Finger": 11, "Neck": 2, "Chest": 5,
              "Robe": 20, "Wrist": 9, "Hands": 10, "Legs": 7, "Feet": 8, "Head": 1, "Shoulder": 3, "Relic": 28, "Thrown": 25,
              "Shirt": 4, "Tabard": 19}


SCHOOLS = {"holy": "84", "fire": "85", "nature": "86", "frost": "87", "shadow": "88", "arcane": "89"}
# WCLBox words the Equip sentences differently from Wowhead; (regex, stat id, scale). None id = known, no gear stat.
WCL_RULES = [
    (r"^Increases (?:the )?damage and healing (?:of|from|caused by) all spells and magic effects by up to (\d+)", "45", 1),
    (r"^Increases your critical strike chance by ([\d.]+)%", "32", 14),
    (r"^\+ ?(\d+) attack power\.?$", "38", 1),
    (r"^Regenerates (\d+) mana every 5 seconds", "43", 1),
    (r"^Increases your chances? of hitting your target by ([\d.]+)%", "31", 10),
    (r"^Increases the healing effect of spells by up to (\d+)", "41", 1),
    (r"^Defense (?:skills? )?increased by (\d+)", "12", 1),
    (r"^Increases your chance to dodge attacks by ([\d.]+)%", "13", 12),
    (r"^Increases your chance to parry attacks by ([\d.]+)%", "14", 20),
    (r"^Increases your chance to block attacks with your shield by ([\d.]+)%", "15", 5),
    (r"^Increases the chance of you blocking attacks with your shield by ([\d.]+)%", "15", 5),
    (r"^Reduces the chance of your attacks being dodged or parried by ([\d.]+)%", "37", 10),
    (r"^(?:Restores \d+ HP every|Increases movement speed|Increases your shield's block|Reduces your spell target's|"
     r"Reduces the magic resistance|Attack power against|Increases your stealth|Fishing skill|\w+ skill increased)", "", 0),
]


def wcl_equip(s):
    """-> (stat id, value) | tuple of those | () known without a gear stat | None unknown."""
    m = re.match(r"^Increases the healing effect of all spells and magic effects by up to (\d+)(?: points)?,? and (?:the )?damage"
                 r"(?: effect)? by up to (\d+)", s)
    if m:
        return (("41", int(m.group(1))), ("42", int(m.group(2))))
    m = re.match(r"^Increases (?:the )?damage (?:dealt|caused) by (\w+) spells and effects by up to (\d+)", s)
    if m and m.group(1).lower() in SCHOOLS:
        return (SCHOOLS[m.group(1).lower()], int(m.group(2)))
    for pat, sid, scale in WCL_RULES:
        m = re.match(pat, s)
        if m:
            return (sid, int(round(float(m.group(1)) * scale))) if sid else ()
    return None


def slot_to_inv(slot):
    if slot in SLOT_EXTRA:
        return SLOT_EXTRA[slot]
    for k, v in SLOT_NAME_INV.items():
        if k.lower() == (slot or "").lower():
            return v
    return None


def parse_detail(d):
    """-> record, or None when it is not equippable gear."""
    cid = d.get("classId")
    inv = slot_to_inv(d.get("slot"))
    sub_map = WEAPON_SUB if cid == 2 else ARMOR_SUB
    rec = {"id": d["id"], "n": d.get("nameEn") or d.get("name"), "q": d.get("quality"), "il": d.get("itemLevel") or 0,
           "rl": d.get("requiredLevel") or 0, "inv": inv, "c": cid, "s": sub_map.get(d.get("type")), "st": {}, "src": "wcl"}
    equip, unknown = [], []
    for line in d.get("tooltipEn") or []:
        line = line.strip()
        m = re.match(r"^\+(\d+) (Agility|Strength|Intellect|Spirit|Stamina)$", line)
        if m:
            rec["st"][BASE_STAT[m.group(2)]] = int(m.group(1))
            continue
        m = re.match(r"^(\d+) Armor$", line)
        if m:
            rec["ar"] = int(m.group(1))
            continue
        m = re.match(r"^\+(\d+) Armor$", line)
        if m:
            rec["bonusArmor"] = int(m.group(1))
            continue
        m = re.match(r"^\(([\d.]+) damage per second\)", line)
        if m:
            rec["dps"] = float(m.group(1))
            continue
        m = re.search(r"Speed ([\d.]+)", line)
        if m and "Damage" in line:
            rec["spd"] = float(m.group(1))
            continue
        m = re.match(r"^\+(\d+) (Fire|Frost|Nature|Shadow|Arcane|Holy) Resistance", line)
        if m:
            rec["st"][RES_STAT[m.group(2)]] = int(m.group(1))
            continue
        m = re.match(r"^Equip: (.*)$", line)
        if m:
            s = m.group(1).strip()
            equip.append(s)
            r = wcl_equip(s)
            if r is None:
                r = equip_rule(s)
            m2 = re.match(r"Restores (\d+) mana per 5 sec", s)
            if m2:
                rec["st"]["43"] = int(m2.group(1))
            elif r is None:
                unknown.append(s)
            elif r:
                for sid, val in (r if isinstance(r[0], tuple) else (r,)):
                    rec["st"][sid] = rec["st"].get(sid, 0) + val
    if equip:
        rec["eq"] = equip
    if unknown:
        rec["unk"] = unknown
    return rec
