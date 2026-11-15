"""Which vendor sells which item, and where: the client's own CollectableSourceVendorSparse table (game data, from wago.tools).

The game ships (for the appearance collection) one row per "vendor sells item": item id, creature id, a world position and the area.
Positions are world coordinates on a continent; UiMapAssignment holds each zone map's world bounds, which turns them into the map
percent the BiZNav arrow uses. Creature names come from QuestieDB (bis/own/cache/questiedb_live.json, see questiedb_decode.py).

Output: bis/own/cache/vendor_spots.json   {"vendors": {creatureId: {name, map, zone, x, y, items: [...]}}, "items": {itemId: [creatureIds]}}
Check:  the converted spot of every vendor QuestieDB also places is compared with QuestieDB's (printed at the end).

Usage (repo root):  python bis/tools/collectable_vendors.py [build]     (needs bis/tools/db2_pull.py to have run for that build)
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIS = os.path.normpath(os.path.join(HERE, ".."))
DB2 = os.path.join(BIS, "own", "cache", "db2")
LIVE = os.path.join(BIS, "own", "cache", "questiedb_live.json")
OUT = os.path.join(BIS, "own", "cache", "vendor_spots.json")
ZONES = r"D:\World of Warcraft\_forever_\Interface\AddOns\QuestieDB\support\Forever\Zones\areaIdToUiMapId.lua"


def newest_build():
    builds = sorted((d for d in os.listdir(DB2) if os.path.exists(os.path.join(DB2, d, "CollectableSourceVendorSparse.csv"))),
                    key=lambda b: [int(x) for x in b.split(".")])
    return builds[-1]


def read(build, table):
    with open(os.path.join(DB2, build, table + ".csv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def zone_names():
    out = {}
    for m in re.finditer(r"^\s*\[(\d+)\] = (\d+),\s*--\s*(.+)$", open(ZONES, encoding="utf-8").read(), re.M):
        out.setdefault(int(m.group(2)), m.group(3).strip())
    return out


def main():
    build = sys.argv[1] if len(sys.argv) > 1 else newest_build()
    print("build", build)
    rows = read(build, "CollectableSourceVendorSparse")
    assign = []
    for r in read(build, "UiMapAssignment"):
        if float(r["UiMin_0"]) == 0 and float(r["UiMax_0"]) == 1 and int(r["UiMapID"]) not in (947, 1414, 1415, 1463, 1464):
            assign.append({"ui": int(r["UiMapID"]), "map": int(r["MapID"]), "area": int(r["AreaID"]),
                           "x0": float(r["Region_0"]), "y0": float(r["Region_1"]), "x1": float(r["Region_3"]), "y1": float(r["Region_4"])})
    names = zone_names()
    live = json.load(open(LIVE, encoding="utf-8"))["npc"] if os.path.exists(LIVE) else {}

    def to_map(map_id, wx, wy, area=0):
        """-> (uiMapId, x%, y%) of the smallest zone map whose world bounds contain the point."""
        best = None
        for a in assign:
            if a["map"] != map_id:
                continue
            if min(a["x0"], a["x1"]) <= wx <= max(a["x0"], a["x1"]) and min(a["y0"], a["y1"]) <= wy <= max(a["y0"], a["y1"]):
                size = abs(a["x1"] - a["x0"]) * abs(a["y1"] - a["y0"])
                if area and a["area"] == area:
                    size = 0          # the row names the zone: that map wins over any overlapping neighbour
                if best is None or size < best[0]:
                    # world +x is north, +y is west: map x runs west -> east, map y north -> south
                    best = (size, a["ui"], (a["y1"] - wy) / (a["y1"] - a["y0"]) * 100, (a["x1"] - wx) / (a["x1"] - a["x0"]) * 100)
        return best[1:] if best else None

    vendors, items = {}, {}
    unplaced = 0
    for r in rows:
        cid = int(r["CreatureID"])
        pos = to_map(int(r["VendorMapID"]), float(r["VendorPosition_0"]), float(r["VendorPosition_1"]), int(r["AreaTableID"]))
        item = int(r["VendorItemID"])
        v = vendors.setdefault(cid, {"name": (live.get(str(cid)) or {}).get("name"), "spots": [], "items": []})
        if pos:
            ui, x, y = pos
            spot = [ui, round(x, 1), round(y, 1), names.get(ui, "")]
            if spot not in v["spots"]:
                v["spots"].append(spot)
        else:
            unplaced += 1
        if item not in v["items"]:
            v["items"].append(item)
        items.setdefault(item, [])
        if cid not in items[item]:
            items[item].append(cid)
    print("%d rows, %d vendors, %d items, %d rows with no zone map" % (len(rows), len(vendors), len(items), unplaced))
    named = sum(1 for v in vendors.values() if v["name"])
    print("vendors with a name from QuestieDB: %d of %d" % (named, len(vendors)))
    json.dump({"build": build, "vendors": {str(k): v for k, v in vendors.items()}, "items": {str(k): v for k, v in items.items()}},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    # check against QuestieDB's own spawn positions (same creature id)
    dev, n = [], 0
    for cid, v in vendors.items():
        rec = live.get(str(cid))
        sp = rec.get("spawns") if rec else None
        if not (sp and v["spots"]):
            continue
        sp_items = sp.items() if isinstance(sp, dict) else [(i + 1, p) for i, p in enumerate(sp)]
        for area, pts in sp_items:
            for ui, x, y, _zone in v["spots"]:
                if int(area) in names or True:
                    for px, py in [(p[0], p[1]) for p in pts if p and len(p) >= 2]:
                        if abs(px - x) < 15 and abs(py - y) < 15:
                            dev.append(abs(px - x) + abs(py - y))
                            break
        n += 1
    if dev:
        dev.sort()
        print("checked %d vendors against QuestieDB: %d spots within 15%%, median error %.2f%%, 90th percentile %.2f%%" % (
            n, len(dev), dev[len(dev) // 2], dev[int(len(dev) * 0.9)]))
    print("wrote", OUT)


main()
