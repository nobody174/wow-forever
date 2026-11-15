"""Read dungeon entrance coordinates from the installed ForeverDungeonJournal (read only) and add the ones Mr.BiZ needs to bis/places.json.

Only the facts are taken (name, map id, x, y); the addon's descriptive text, art and code are not copied (it ships no licence).
Credit: ForeverDungeonJournal (Exehn). Entries are marked conf "approx" and via "ForeverDungeonJournal" until confirmed in game.
Existing places.json entries are never overwritten; a differing value is reported.

Usage (repo root):  python bis/tools/dj_entrances.py [path-to-DungeonEntrances.lua] [--write]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIS = os.path.normpath(os.path.join(HERE, ".."))
DEFAULT_SRC = r"D:\World of Warcraft\_forever_\Interface\AddOns\ForeverDungeonJournal\Data\DungeonEntrances.lua"

# UiMapID -> zone name (Classic zone maps; ids seen in the file)
ZONES = {1413: "The Barrens", 1416: "Alterac Mountains", 1420: "Tirisfal Glades", 1421: "Silverpine Forest",
         1426: "Dun Morogh", 1429: "Elwynn Forest", 1432: "Loch Modan", 1434: "Stranglethorn Vale",
         1435: "Swamp of Sorrows", 1436: "Westfall", 1437: "Wetlands", 1440: "Ashenvale", 1441: "Thousand Needles",
         1442: "Stonetalon Mountains", 1443: "Desolace", 1444: "Feralas", 1445: "Dustwallow Marsh",
         1446: "Tanaris", 1447: "Azshara", 1448: "Felwood", 1449: "Un'Goro Crater", 1450: "Moonglade",
         1451: "Silithus", 1452: "Winterspring", 1453: "Stormwind City", 1454: "Orgrimmar", 1455: "Ironforge",
         1456: "Thunder Bluff", 1457: "Darnassus", 1458: "Undercity", 1417: "Arathi Highlands",
         1418: "Badlands", 1419: "Blasted Lands", 1422: "Western Plaguelands", 1423: "Eastern Plaguelands",
         1424: "Hillsbrad Foothills", 1425: "The Hinterlands", 1427: "Searing Gorge", 1428: "Burning Steppe",
         1430: "Deadwind Pass", 1431: "Duskwood", 1433: "Redridge Mountains", 1438: "Teldrassil",
         1439: "Darkshore", 1411: "Durotar", 1412: "Mulgore"}
# Mr.BiZ source (instance) name -> journal entrance name. Dungeons with several wings share the entrance of the wing the journal lists.
ALIAS = {"Deadmines": "The Deadmines", "The Deadmines": "The Deadmines", "The Hall of Thanes": "Hall of Thanes",
         "Hall of Thanes": "Hall of Thanes", "Dire Maul": "Dire Maul: East", "Stratholme": "Stratholme: Living",
         "Blackrock Spire": "Lower Blackrock Spire", "Scarlet Monastery": "Scarlet Monastery: Library"}


def parse(path):
    text = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'\["([^"]+)"\]\s*=\s*\{\s*mapID\s*=\s*(\d+),\s*x\s*=\s*([\d.]+),\s*y\s*=\s*([\d.]+),\s*label\s*=\s*"([^"]*)"', text):
        out[m.group(1)] = {"mapID": int(m.group(2)), "x": round(float(m.group(3)) * 100, 1),
                           "y": round(float(m.group(4)) * 100, 1), "label": m.group(5)}
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    src = args[0] if args else DEFAULT_SRC
    ent = parse(src)
    print("read %d entrances from %s" % (len(ent), src))
    data = json.load(open(os.path.join(BIS, "..", "bis-data.json"), encoding="utf-8"))
    used = {r["instance"] for r in data["rows"] if r.get("type") in ("dungeon", "raid") and r.get("instance")}
    pf = os.path.join(BIS, "places.json")
    places = json.load(open(pf, encoding="utf-8"))
    added, same, differ, missing = [], [], [], []
    for inst in sorted(used):
        name = ALIAS.get(inst, inst)
        e = ent.get(name)
        if not e:
            missing.append(inst)
            continue
        zone = ZONES.get(e["mapID"])
        if not zone:
            print("unknown map id %d for %s" % (e["mapID"], inst))
            continue
        new = {"zone": zone, "mapHint": e["mapID"], "x": e["x"], "y": e["y"], "label": e["label"], "conf": "approx",
               "via": "ForeverDungeonJournal"}
        old = places["places"].get(inst)
        if old:
            (same if abs(old["x"] - e["x"]) < 1 and abs(old["y"] - e["y"]) < 1 else differ).append((inst, old, new))
        else:
            places["places"][inst] = new
            added.append(inst)
    print("added:", added)
    print("already there, same spot:", [i[0] for i in same])
    for inst, old, new in differ:
        print("DIFFERS %s: have %s,%s (%s) journal %s,%s (%s)" % (inst, old["x"], old["y"], old["conf"], new["x"], new["y"], new["zone"]))
    print("no journal entrance (not added):", missing)
    if write and added:
        places["_sources"]["dj"] = "ForeverDungeonJournal Data/DungeonEntrances.lua (coordinates only, read 2026-11-15, unconfirmed): bis/tools/dj_entrances.py"
        with open(pf, "w", encoding="utf-8", newline="\n") as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("wrote", pf)


main()
