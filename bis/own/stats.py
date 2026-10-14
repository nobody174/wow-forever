"""Item stats out of a Wowhead Forever tooltip, in the vocabulary of ForeverDB's weights (bis/raw/*.json).

    stats(tooltip_html) -> {"Stamina": 12, "spell power": 12, "Shadow Damage Done": 14, "armor": 84, "weapon DPS": 19.4, ...}

Names used (the same words as the weights): Strength, Agility, Stamina, Intellect, Spirit, armor, Bonus Armor, spell power (damage AND
healing), spell damage, healing, <School> Damage Done, attack power, ranged attack power, crit, hit, haste, expertise, defense, dodge,
parry, block, block value, mana per 5 sec, Spell Penetration, weapon DPS. Percent stats (hit, crit...) are kept as the percentage
(1.0 = 1%); the scorer applies ForeverDB's conversion. Lines that are not recognised go to `unknown` (see `parse`).
"""
import html
import re

SCHOOLS = "Arcane|Fire|Frost|Holy|Nature|Shadow"


def text_of(tooltip):
    t = re.sub(r"<!--.*?-->", "", tooltip)
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"</t[dh]>", "  ", t)
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t)


def add(out, key, val):
    out[key] = round(out.get(key, 0) + val, 4)


def parse(tooltip):
    """-> (stats dict, list of unrecognised "Equip:" / "Use:" lines)."""
    t = text_of(tooltip)
    # the set bonus lines and everything after "Sell Price" are not the item's own stats
    t = re.split(r"\(\d/\d\)|Sell Price|Dropped by|Reward from|Sold by", t)[0]
    out, unknown = {}, []
    # white armor ("84 Armor" next to the slot), base stats "+13 Stamina" / "-15 Stamina"
    m = re.search(r"(?<![+\w])(\d+) Armor\b", t)
    if m:
        add(out, "armor", int(m.group(1)))
    for m in re.finditer(r"([+\-−])\s?(\d+) (Strength|Agility|Stamina|Intellect|Spirit)\b", t):
        add(out, m.group(3), (-1 if m.group(1) in "-−" else 1) * int(m.group(2)))
    m = re.search(r"\(([\d.]+) damage per second\)", t)
    if m:
        add(out, "weapon DPS", float(m.group(1)))
    m = re.search(r"Restores \+?(\d+) mana per 5 sec", t)
    if m:
        add(out, "mana per 5 sec", int(m.group(1)))
    for line in re.findall(r"(?:Equip|Use):[^\n]*", t):
        l = line.strip()
        m = re.search(r"Increases damage and healing done by magical spells and effects by up to (\d+)", l)
        if m:
            add(out, "spell power", int(m.group(1)))
            continue
        m = re.search(r"Increases healing done by up to (\d+) and damage done by up to (\d+) for all magical spells", l)
        if m:
            add(out, "healing", int(m.group(1)))
            add(out, "spell damage", int(m.group(2)))
            continue
        m = re.search(r"Increases healing done by (?:magical )?spells and effects by up to (\d+)", l)
        if m:
            add(out, "healing", int(m.group(1)))
            continue
        m = re.search(r"Increases damage done by (%s) spells and effects by up to (\d+)" % SCHOOLS, l)
        if m:
            add(out, "%s Damage Done" % m.group(1), int(m.group(2)))
            continue
        m = re.search(r"Improves your chance to get a critical strike by ([\d.]+)%", l)
        if m:
            add(out, "crit", float(m.group(1)))
            continue
        m = re.search(r"Improves your chance to hit by ([\d.]+)%", l)
        if m:
            add(out, "hit", float(m.group(1)))
            continue
        m = re.search(r"Increased Defense \+(\d+)", l)
        if m:
            add(out, "defense", int(m.group(1)))
            continue
        m = re.search(r"\+(\d+) Attack Power\.", l)
        if m and "against" not in l:
            add(out, "attack power", int(m.group(1)))
            continue
        m = re.search(r"\+(\d+) Ranged Attack Power", l)
        if m:
            add(out, "ranged attack power", int(m.group(1)))
            continue
        m = re.search(r"Restores (\d+) mana per 5 sec", l)
        if m:
            add(out, "mana per 5 sec", int(m.group(1)))
            continue
        m = re.search(r"\+(\d+) Armor\.?$", l.rstrip("."))
        if m:
            add(out, "Bonus Armor", int(m.group(1)))
            continue
        unknown.append(l)
    return out, unknown


def stats(tooltip):
    return parse(tooltip)[0]
