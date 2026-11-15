"""Add profession trainer places (for crafted picks) to bis/places.json from QuestieDB.

A crafted pick has no single spot, so Mr.BiZ points at where to learn the profession's higher ranks: the best trainer in a capital city for each
faction. Keys are "trade:<Profession>:alliance" and "trade:<Profession>:horde"; build_bis.place_key gives a crafted row "trade:<Profession>" and the
addon picks the variant for your faction (BiZ.Place). Trainer rank comes from the NPC's title (Artisan > Expert > Master > Journeyman).

Usage (repo root):  python bis/tools/trainer_places.py [--write]      (needs bis/own/cache/questiedb_live.json)
Credit: QuestieDB / Questie (GPL v3).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIS = os.path.normpath(os.path.join(HERE, ".."))
LIVE = os.path.join(BIS, "own", "cache", "questiedb_live.json")
ZONES = r"D:\World of Warcraft\_forever_\Interface\AddOns\QuestieDB\support\Forever\Zones\areaIdToUiMapId.lua"
WORDS = {"Tailoring": "Tailor", "Leatherworking": "Leatherworker", "Blacksmithing": "Blacksmith", "Enchanting": "Enchanter",
         "Engineering": "Engineer"}
RANKS = ["Artisan", "Expert", "Master", "Journeyman"]
CAPITALS = {"alliance": [1519, 1537, 1657], "horde": [1637, 1638, 1497]}     # preference order
NPC_FLAG_TRAINER = 16


def main():
    write = "--write" in sys.argv
    live = json.load(open(LIVE, encoding="utf-8"))["npc"]
    areas = {}
    for m in re.finditer(r"^\s*\[(\d+)\] = (\d+),\s*--\s*(.+)$", open(ZONES, encoding="utf-8").read(), re.M):
        areas[int(m.group(1))] = (int(m.group(2)), m.group(3).strip())
    pf = os.path.join(BIS, "places.json")
    places = json.load(open(pf, encoding="utf-8"))
    added = []
    for prof, word in WORDS.items():
        for side, letter in (("alliance", "A"), ("horde", "H")):
            best = None
            for nid, n in live.items():
                title = n.get("subName") or ""
                if not (n.get("npcFlags", 0) & NPC_FLAG_TRAINER) or word not in title or "Master " in title and "Master" not in RANKS:
                    continue
                if n.get("friendly") not in (letter, "AH"):
                    continue
                if re.search(r"Dragonscale|Elemental|Tribal|Shadoweave|Gnome|Goblin|Mooncloth|Gnomish", title):
                    continue                      # specialisation trainers
                rank = next((i for i, r in enumerate(RANKS) if title.startswith(r)), None)
                if rank is None:
                    continue
                sp = n.get("spawns") or {}
                items = sp.items() if isinstance(sp, dict) else [(i + 1, v) for i, v in enumerate(sp)]
                for area, pts in items:
                    a = int(area)
                    if a in CAPITALS[side] and len(pts) == 1:
                        key = (rank, CAPITALS[side].index(a))
                        if best is None or key < best[0]:
                            best = (key, n["name"], title, a, pts[0])
            if best:
                _, name, title, a, (x, y) = best
                mapid, zone = areas[a]
                k = "trade:%s:%s" % (prof, side)
                places["places"][k] = {"zone": zone, "mapHint": mapid, "x": x, "y": y,
                                       "label": "%s trainer: %s, %s" % (prof, name, zone), "conf": "classic", "via": "QuestieDB"}
                added.append((k, name, title, zone, x, y))
    for a in added:
        print("%-34s %s (%s) %s %.1f, %.1f" % a)
    if write and added:
        with open(pf, "w", encoding="utf-8", newline="\n") as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("wrote", pf)


main()
