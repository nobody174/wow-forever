"""Add vendor places to bis/places.json from the QuestieDB `forever` snapshot (bis/own/cache/questiedb/foreverNpcDB.lua).

Mr.BiZ vendor rows are keyed by the vendor's name (see build_bis.place_key). For every such name that has no place yet, this looks the
NPC up in QuestieDB's NPC table (spawn coordinates as map percent per zone) and writes a place when exactly one spawn fits the zone named in
the row label. Names QuestieDB does not know (Forever-new vendors) and spawns in battlegrounds are listed, never guessed.

Credit: QuestieDB / Questie (GPL v3). Entries get conf "classic" (Classic positions, converted to map percent by QuestieDB) and via "QuestieDB".

Usage (repo root):  python bis/tools/questie_places.py [--write]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(BIS, ".."))
NPC_DB = os.path.join(BIS, "own", "cache", "questiedb", "foreverNpcDB.lua")

# Classic AreaTable zone id (QuestieDB) -> (UiMapID, zone name). Only zones with a world map; battlegrounds are left out on purpose.
AREAS = {
    17: (1413, "The Barrens"), 36: (1416, "Alterac Mountains"), 12: (1429, "Elwynn Forest"), 40: (1436, "Westfall"),
    11: (1437, "Wetlands"), 1519: (1453, "Stormwind City"), 1637: (1454, "Orgrimmar"), 215: (1412, "Mulgore"),
    14: (1411, "Durotar"), 85: (1420, "Tirisfal Glades"), 1: (1426, "Dun Morogh"), 44: (1433, "Redridge Mountains"),
    331: (1440, "Ashenvale"), 400: (1441, "Thousand Needles"), 33: (1434, "Stranglethorn Vale"), 8: (1435, "Swamp of Sorrows"),
    148: (1439, "Darkshore"), 406: (1442, "Stonetalon Mountains"), 405: (1443, "Desolace"), 357: (1444, "Feralas"),
    15: (1445, "Dustwallow Marsh"), 440: (1446, "Tanaris"), 16: (1447, "Azshara"), 361: (1448, "Felwood"),
    490: (1449, "Un'Goro Crater"), 618: (1452, "Winterspring"), 1537: (1455, "Ironforge"), 1638: (1456, "Thunder Bluff"),
    1657: (1457, "Darnassus"), 1497: (1458, "Undercity"), 3: (1418, "Badlands"), 28: (1422, "Western Plaguelands"),
    139: (1423, "Eastern Plaguelands"), 267: (1424, "Hillsbrad Foothills"), 47: (1425, "The Hinterlands"),
    51: (1427, "Searing Gorge"), 46: (1428, "Burning Steppes"), 10: (1431, "Duskwood"), 38: (1432, "Loch Modan"),
    45: (1417, "Arathi Highlands"), 130: (1421, "Silverpine Forest"), 141: (1438, "Teldrassil"), 41: (1430, "Deadwind Pass"),
    4: (1419, "Blasted Lands"), 1377: (1451, "Silithus"), 493: (1450, "Moonglade"),
}


def load_npcs(path):
    text = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^\[(\d+)\] = \{'((?:[^'\\]|\\.)*)',[^\n]*?,(\d+|nil),(\d+|nil),(\d+),(\{.*?\}|nil),(?:nil|\{[^\n]*?\}),", text, re.M):
        name = m.group(2).replace("\\'", "'")
        spawns = {}
        if m.group(6) != "nil":
            for zm in re.finditer(r"\[(\d+)\]=\{((?:\{[\d.]+,[\d.]+\},?)+)\}", m.group(6)):
                spawns[int(zm.group(1))] = [(float(a), float(b)) for a, b in re.findall(r"\{([\d.]+),([\d.]+)\}", zm.group(2))]
        out.setdefault(name, []).append((int(m.group(1)), spawns))
    return out


def main():
    write = "--write" in sys.argv
    data = json.load(open(os.path.join(ROOT, "bis-data.json"), encoding="utf-8"))
    pf = os.path.join(BIS, "places.json")
    places = json.load(open(pf, encoding="utf-8"))
    npcs = load_npcs(NPC_DB)
    print("read %d NPC names" % len(npcs))
    want = {}
    for r in data["rows"]:
        if r.get("type") == "vendor" and r.get("label") and not r.get("place"):
            name = r["label"].split(",")[0].strip()
            zm = re.match(r"^[^,]+,\s*([^(]+?)\s*(?:\(|$)", r["label"])
            want.setdefault(name, set()).add(zm.group(1).strip() if zm else "")
    added, notfound, skipped = [], [], []
    for name in sorted(want):
        if name in places["places"]:
            continue
        cands = npcs.get(name)
        if not cands:
            notfound.append(name)
            continue
        best = None
        zoneless = want[name] <= {""}      # the row names no zone: accept only when the NPC has exactly one spawn
        fits = []
        for npc_id, spawns in cands:
            for area, pts in spawns.items():
                if area in AREAS and len(pts) == 1 and (zoneless or AREAS[area][1] in want[name]):
                    fits.append((npc_id, area, pts[0]))
        if len(fits) == 1 and (not zoneless or sum(len(sp) for _, sp in cands) == 1):
            best = fits[0]
        if not best:
            skipped.append((name, sorted(want[name]), [(i, list(s)) for i, s in cands]))
            continue
        npc_id, area, (x, y) = best
        mapid, zone = AREAS[area]
        places["places"][name] = {"zone": zone, "mapHint": mapid, "x": x, "y": y, "label": name + ", " + zone,
                                  "conf": "classic", "via": "QuestieDB"}
        added.append((name, zone, x, y))
    for a in added:
        print("add  %s: %s %.2f, %.2f" % a)
    for s in skipped:
        print("SKIP %s (row zone %s): QuestieDB spawns %s" % s)
    print("not in QuestieDB (Forever-new?):", notfound)
    if write and added:
        places["_sources"]["questie"] = ("QuestieDB forever snapshot (GPL v3), NPC spawns, read 2026-11-15: bis/tools/questie_places.py")
        with open(pf, "w", encoding="utf-8", newline="\n") as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("wrote", pf)


main()
