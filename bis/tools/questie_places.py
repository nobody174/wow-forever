"""Add vendor and quest-giver places to bis/places.json from the installed QuestieDB (Forever flavor), and cross-check dungeon entrances.

Input:  bis/own/cache/questiedb_live.json  (python -I bis/tools/questiedb_decode.py writes it from the addon's .toc)
        QuestieDB/support/Forever/Zones/areaIdToUiMapId.lua  (zone id -> map id and name)
        QuestieDB/support/Forever/Zones/dungeons.lua         (dungeon entrance points, for the cross-check)
Mr.BiZ rows are matched by name: vendor rows by the vendor's name, quest rows by the quest title (place key "quest:<title>", see
build_bis.place_key). A place is written only when the answer is unambiguous; everything else is listed, never guessed.
Credit: QuestieDB / Questie (GPL v3). Entries get conf "classic" (Classic positions converted by QuestieDB to Forever map percent) and via "QuestieDB".

Usage (repo root):  python bis/tools/questie_places.py [--write] [--dungeons]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(BIS, ".."))
LIVE = os.path.join(BIS, "own", "cache", "questiedb_live.json")
VSPOTS = os.path.join(BIS, "own", "cache", "vendor_spots.json")
RECORDED = os.path.join(BIS, "own", "recorded.json")
QDIR = r"D:\World of Warcraft\_forever_\Interface\AddOns\QuestieDB\support\Forever\Zones"
VENDOR = 4          # npcFlags bit (mangos UNIT_NPC_FLAG_VENDOR)
SPREAD = 4.0        # an NPC that wanders within this many map percent counts as one spot


def load_areas():
    out = {}
    for m in re.finditer(r"^\s*\[(\d+)\] = (\d+),\s*--\s*(.+)$", open(os.path.join(QDIR, "areaIdToUiMapId.lua"), encoding="utf-8").read(), re.M):
        if int(m.group(2)):
            out[int(m.group(1))] = (int(m.group(2)), m.group(3).strip())
    return out


def centroid(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    if max(xs) - min(xs) > SPREAD or max(ys) - min(ys) > SPREAD:
        return None
    return round(sum(xs) / len(xs), 1), round(sum(ys) / len(ys), 1)


def spots(rec, areas):
    """[(area, (x, y), mapId, zoneName)] for an NPC record: one per zone with a single cluster, battlegrounds and unmapped zones left out."""
    out = []
    sp = rec.get("spawns") or {}
    # Lua tables with keys 1..n come out of CBOR as lists: index + 1 is the zone id
    items = sp.items() if isinstance(sp, dict) else [(i + 1, v) for i, v in enumerate(sp)]
    for area, pts in items:
        a = int(area)
        if a not in areas or not pts:
            continue
        pts = [(p[0], p[1]) for p in pts if 0 <= p[0] <= 100 and 0 <= p[1] <= 100]
        c = centroid(pts) if pts else None
        if c:
            out.append((a, c, areas[a][0], areas[a][1]))
    return out


def starters(q):
    sb = q.get("startedBy")
    if isinstance(sb, list) and sb:
        return sb[0] or []
    if isinstance(sb, dict):
        return sb.get("1") or []
    return []


def main():
    write = "--write" in sys.argv
    areas = load_areas()
    live = json.load(open(LIVE, encoding="utf-8"))
    npcs = live["npc"]
    by_name = {}
    for i, n in npcs.items():
        if n.get("name"):
            by_name.setdefault(n["name"], []).append((int(i), n))
    qby = {}
    for i, q in live["quest"].items():
        if q.get("name"):
            qby.setdefault(q["name"], []).append((int(i), q))
    data = json.load(open(os.path.join(ROOT, "bis-data.json"), encoding="utf-8"))
    pf = os.path.join(BIS, "places.json")
    places = json.load(open(pf, encoding="utf-8"))
    print("QuestieDB:", live["build"], "|", len(npcs), "npcs", len(live["quest"]), "quests")

    # ---- vendors ------------------------------------------------------------------------------------------------------------
    want = {}
    for r in data["rows"]:
        if r.get("type") == "vendor" and r.get("label") and not r.get("place"):
            name = r["label"].split(",")[0].strip()
            zm = re.match(r"^[^,]+,\s*([^(]+?)\s*(?:\(|$)", r["label"])
            want.setdefault(name, set()).add(zm.group(1).strip() if zm else "")
    v_added, v_skip = [], []
    for name in sorted(want):
        key = name
        if key in places["places"]:
            continue
        fits = []
        for npc_id, rec in by_name.get(name, []):
            if not (rec.get("npcFlags", 0) & VENDOR):
                continue
            for a, c, mapid, zone in spots(rec, areas):
                if want[name] <= {""} or any(zone.lower() == z.lower() or z.lower() in zone.lower() for z in want[name]):
                    fits.append((npc_id, a, c, mapid, zone))
        if not fits and os.path.exists(VSPOTS):
            # the game's own vendor table (collectable_vendors.py): creatures QuestieDB has no spawn for
            for v in json.load(open(VSPOTS, encoding="utf-8"))["vendors"].values():
                if v["name"] == name and len(v["spots"]) == 1 and v["spots"][0][3]:
                    ui, x, y, zone = v["spots"][0]
                    if want[name] <= {""} or any(z.lower() in zone.lower() for z in want[name]):
                        fits.append((0, 0, (x, y), ui, zone))
        via = "QuestieDB"
        if not fits and os.path.exists(RECORDED):
            # a spot our own recorder saw (Recorder.lua notes where you stood at the vendor): bis/own/recorded.json
            for nid, v in (json.load(open(RECORDED, encoding="utf-8")).get("vendors") or {}).items():
                pos = v.get("pos")
                if pos and (npcs.get(nid) or {}).get("name") == name:
                    fits.append((int(nid), 0, (pos["x"], pos["y"]), pos["m"], v.get("z") or ""))
                    via = "our own recordings"
        if len({(f[3], f[2]) for f in fits}) == 1:
            npc_id, a, c, mapid, zone = fits[0]
            places["places"][key] = {"zone": zone, "mapHint": mapid, "x": c[0], "y": c[1], "label": name + ", " + zone,
                                     "conf": "seen" if via == "our own recordings" else "classic", "via": via}
            v_added.append((name, zone, c))
        else:
            v_skip.append((name, sorted(want[name]), len(fits)))
    print("vendors placed %d, left %d" % (len(v_added), len(v_skip)))
    for s in v_skip:
        print("  vendor left:", s)

    # ---- reputation: the faction's quartermaster ("<faction> Quartermaster", vendor flag) when he has exactly one spot -------------------
    r_added, r_left = [], []
    for fac in sorted({r["group"][len("Reputation: "):] for r in data["rows"] if r.get("type") == "reputation" and r.get("group", "").startswith("Reputation: ")}):
        if fac in places["places"]:
            continue
        fits = []
        for nid, n in npcs.items():
            if (n.get("subName") or "") == fac + " Quartermaster" and n.get("npcFlags", 0) & VENDOR:
                for a, c, mapid, zone in spots(n, areas):
                    fits.append((n["name"], c, mapid, zone))
        if len({(f[2], f[1]) for f in fits}) == 1:
            name, c, mapid, zone = fits[0]
            places["places"][fac] = {"zone": zone, "mapHint": mapid, "x": c[0], "y": c[1],
                                     "label": "%s, %s quartermaster (%s)" % (name, fac, zone), "conf": "classic", "via": "QuestieDB"}
            r_added.append(fac)
        else:
            r_left.append((fac, len(fits)))
    print("reputation placed %s, left %s" % (r_added, r_left))

    # ---- quests -------------------------------------------------------------------------------------------------------------
    q_rows = {}
    for r in data["rows"]:
        if r.get("type") != "quest" or r.get("place"):
            continue
        m = re.match(r"^Quest: (.+?)(?: \(a choice\))?(?: \(level (\d+)\))?$", r.get("label", ""))
        if not m or re.fullmatch(r"Quest \d+", m.group(1)):
            continue
        q_rows.setdefault(m.group(1), set()).add((int(m.group(2)) if m.group(2) else None, r.get("faction")))
    q_added, q_amb, q_none = [], [], []
    for title in sorted(q_rows):
        key = "quest:" + title
        if key in places["places"]:
            continue
        levels = {lv for lv, _ in q_rows[title] if lv}
        facs = {f for _, f in q_rows[title] if f}
        cands = []
        for qid, q in qby.get(title, []):
            if levels and not (q.get("questLevel") in levels or q.get("requiredLevel") in levels):
                continue
            for npc_id in starters(q):
                rec = npcs.get(str(npc_id))
                if not rec:
                    continue
                if facs and rec.get("friendly") in ("A", "H") and {"A": "alliance", "H": "horde"}[rec["friendly"]] not in facs:
                    continue
                for a, c, mapid, zone in spots(rec, areas):
                    cands.append((qid, npc_id, rec["name"], c, mapid, zone))
        distinct = {(c[4], c[3]) for c in cands}
        if len(distinct) == 1:
            qid, npc_id, npc, c, mapid, zone = cands[0]
            places["places"][key] = {"zone": zone, "mapHint": mapid, "x": c[0], "y": c[1],
                                     "label": "%s, from %s (%s)" % (title, npc, zone), "conf": "classic", "via": "QuestieDB"}
            q_added.append(title)
        elif distinct:
            q_amb.append(title)
        else:
            q_none.append(title)
    print("quests placed %d, ambiguous %d, no giver spot %d (of %d titles)" % (len(q_added), len(q_amb), len(q_none), len(q_rows)))
    print("  ambiguous (first 10):", q_amb[:10])
    print("  no spot (first 10):", q_none[:10])

    if "--dungeons" in sys.argv:
        t = open(os.path.join(QDIR, "dungeons.lua"), encoding="utf-8").read().split("\nif Expansions")[0]
        print("\nDungeon entrances: places.json vs QuestieDB dungeons.lua (map percent)")
        for m in re.finditer(r'^\s*\[(\d+)\] = \{"([^"]+)",(?:\{[^}]*\}|nil),(\d+),(.*)$', t, re.M):
            locs = re.findall(r"\{(\d+),\s*([\d.]+),\s*([\d.]+)\}", m.group(4))
            name = m.group(2)
            for k in (name, "The " + name, name.replace("The ", "")):
                p = places["places"].get(k)
                if p and locs:
                    best = min(locs, key=lambda l: abs(float(l[1]) - p["x"]) + abs(float(l[2]) - p["y"]))
                    dev = abs(float(best[1]) - p["x"]) + abs(float(best[2]) - p["y"])
                    print("  %-34s ours %5.1f,%5.1f (%s)  Questie %s,%s area %s  %s" % (
                        k, p["x"], p["y"], p.get("via", p.get("conf")), best[1], best[2], best[0], "OK" if dev < 3 else "DIFFERS"))
                    break

    if write and (v_added or q_added or r_added):
        places["_sources"]["questie"] = "QuestieDB forever flavor (GPL v3), NPC spawns and quest starters, read 2026-11-15: bis/tools/questiedb_decode.py + questie_places.py"
        with open(pf, "w", encoding="utf-8", newline="\n") as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("wrote", pf)


main()
