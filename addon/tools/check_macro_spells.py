#!/usr/bin/env python3
"""Warn about spell names in data.py macros that the shipped game data does not know.

Why: a macro that casts a spell the class does not have does nothing in game (the Mage "Remove Curse" macro, which is
"Remove Lesser Curse" for Mages, shipped like that). The names are compared with what we ship per class:
TrainingData.lua (what the class trainer sells) and TalentData.lua (the talent trees), plus ALLOWED below.

ALLOWED holds spells that are real but are not sold by the trainer or in a talent tree (stances, forms, pet and quest
spells, ranged attacks, consumables). OPEN holds names that are known not to be in the current data: they are listed
every run until someone confirms them in the live game and either deletes the macro or moves the name to ALLOWED.

Usage: python addon/tools/check_macro_spells.py     (exit code 0 always: this is a warning list; build.py prints it)
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

ALLOWED = {
    "Shoot", "Shoot Bow", "Throw", "Auto Shot", "Call Pet", "Feed Pet", "Summon Felhunter", "Summon Voidwalker",
    "Major Soulstone", "Devour Magic", "Seduction", "Spell Lock", "Enslave Demon",
    "Battle Stance", "Defensive Stance", "Berserker Stance", "Taunt",
    "Bear Form", "Aquatic Form", "Cure Poison", "Gift of the Wild", "Teleport: Moonglade", "Prayer of Fortitude",
    "Instant Poison", "Iron Grenade", "Rough Sharpening Stone", "Tough Jerky",
}
OPEN = {
    "Elemental Mastery",                                                        # not in the November talent trees
    "Blessing of Salvation", "Blessing of Light", "Blessing of Sanctuary",      # not in Wowhead's Forever Paladin list
    "Starsurge", "Sunfire", "Starfall",                                         # exist as spells, source unknown
}


def read_names(path, pattern):
    out, cur = collections.defaultdict(set), None
    head = re.compile(r"\s+([A-Z]+) = \{")
    for line in open(path, encoding="utf-8"):
        m = head.match(line)
        if m:
            cur = m.group(1).lower()
            continue
        m = re.match(pattern, line)
        if m and cur:
            out[cur].add(m.group(1).replace('\\"', '"'))
    return out


def main():
    import data
    src = os.path.join(ROOT, "addon", "RoadToForever")
    train = read_names(os.path.join(src, "TrainingData.lua"), r'\s+\{ \d+, \d+, \d+, \d+, "(.*)" \},')
    tal = collections.defaultdict(set)
    cur = None
    for line in open(os.path.join(src, "TalentData.lua"), encoding="utf-8"):
        m = re.match(r"\s+(\w+) = \{ token = ", line)
        if m:
            cur = m.group(1).lower()
            continue
        m = re.match(r'\s+\{n="([^"]*)"', line)
        if m and cur:
            tal[cur].add(m.group(1))
    unknown, still_open = collections.defaultdict(set), collections.defaultdict(set)
    for c in data.CLASSES:
        cn = c["name"].lower()
        known = train.get(cn, set()) | tal.get(cn, set())
        for sec in c["sections"]:
            for g in sec["groups"]:
                for m in g["macros"]:
                    for sp in re.findall(r"/(?:cast|use)\s+(?:\[[^\]]*\]\s*)*([^\n;\[]+)", m["code"]):
                        sp = sp.strip().lstrip("!")
                        if sp in known or sp in ALLOWED or sp.isdigit():
                            continue
                        (still_open if sp in OPEN else unknown)[cn].add(sp)
    for cn in sorted(unknown):
        print("WARN  macro spell not in the shipped game data (%s): %s" % (cn, ", ".join(sorted(unknown[cn]))))
    for cn in sorted(still_open):
        print("note  still unconfirmed in the live game (%s): %s" % (cn, ", ".join(sorted(still_open[cn]))))
    if not unknown:
        print("macro spell names: all known or allowed")


if __name__ == "__main__":
    main()
