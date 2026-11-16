"""Collect where items come from, for the picks Mr.BiZ cannot place, into bis/found_sources.json.

    python bis/tools/found_sources.py [addons folder]

Inputs, best first (an item keeps the first source found):
  1. our own recordings (bis/own/recorded.json, see recorder_import.py): "Seen in Forever"
  2. ForeverDungeonJournal's data (installed addon, read-only): boss loot, shared dungeon loot, quest rewards: "Clue"
     (the addon says itself that it mixes observed Forever items with inherited Classic assignments)
  3. AtlasLoot Continued's Forever tables (bis/own/cache/atlasloot_sources.json, made by atlasloot_import.py; GPL v2): "Clue"
  3b. QuestieDB's item table (installed addon, decoded by questiedb_decode.py; GPL v3) and ForeverMyBis's (MIT): "Clue", single answers only
  4. bis/own/web_sources.json, by hand or from a browser: {"<item id>": {"src": "<sentence>", "via": "<site>"}}
Only items that bis-data.json still shows as "source not known yet" are written, so the file never replaces what ForeverDB or
the Classic data already say. build_bis.py reads it. Sentences use the wording of ForeverDB's source lines (parse_source).
Creature names for recorded drops come from the Journal's bosses and bis/own/npc_names.json; a drop whose creature has no name
is listed in the report and left out (a guess would be worse than "not known yet").
"""
import json
import sys
from pathlib import Path

import lupa

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "bis" / "found_sources.json"
REPORT = ROOT / "bis" / "own" / "found_report.md"
DEFAULT = Path("D:/World of Warcraft/_forever_/Interface/AddOns")
NAMES = ROOT / "bis" / "own" / "npc_names.json"
WEB = ROOT / "bis" / "own" / "web_sources.json"
JOURNAL = "ForeverDungeonJournal"


def unknown_ids():
    d = json.loads((ROOT / "bis-data.json").read_text(encoding="utf-8"))
    # Items this tool placed on an earlier run no longer show as unknown in bis-data.json; they stay in the set, so a rerun
    # starts from the same list and gives the same answer.
    earlier = set()
    if OUT.exists():
        earlier = {int(k) for k in json.loads(OUT.read_text(encoding="utf-8"))["items"]}
    return {r["id"]: r["name"] for r in d["rows"] if r.get("type") == "unknown" or r["id"] in earlier}


def read_journal(addons):
    """-> (items {id: (sentence, kind)}, npc names {id: name})"""
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
        function run(src, name, fdj)
            local env = setmetatable({}, { __index = _G })
            local f = assert(load(src, name, "t", env))
            f("ForeverDungeonJournal", fdj)
        end
        function newfdj()
            local anything
            anything = setmetatable({}, { __index = function() return anything end, __call = function() return anything end })
            return { Constants = anything }
        end
    """)
    fdj = lua.eval("newfdj()")
    data = addons / JOURNAL / "Data"
    for name in ("Dungeons.lua", "SharedLoot.lua"):
        lua.globals().run((data / name).read_text(encoding="utf-8", errors="replace"), name, fdj)
    items, names = {}, {}

    def put(item, sentence):
        items.setdefault(int(item), sentence)

    db = fdj["DB"]
    shared = []
    for dungeon, d in db.items():
        for b in (d["bosses"] or {}).values():
            if b["npcID"]:
                names[int(b["npcID"])] = b["name"]
            for it in (b["loot"] or {}).values():
                put(it[1], "Drops from %s in %s (Clue)" % (b["name"], dungeon))
        for q in (d["quests"] or {}).values():
            where = q["level"]
            kind = " (a choice)" if q["rewardChoice"] else ""
            for it in (q["rewardItems"] or {}).values():
                put(it[1], "Quest reward: %s%s%s (Clue)" % (q["name"], kind, ", level %d" % where if where else ""))
    # SharedLoot.lua appends to the same table in the addon; if it kept its own list, read FDJ.SHARED_LOOT-like fields
    for key in ("SharedLoot", "SHARED_LOOT", "sharedLoot"):
        sl = fdj[key]
        if sl:
            shared = list(sl.values())
    for entry in shared:
        try:
            iid, where = entry[1], entry[3]
            dungeon = next(iter(where.keys()))
            boss = where[dungeon][1]
            put(iid, "Drops from %s in %s (Clue)" % (boss, dungeon))
        except Exception:      # a shape we do not know: leave the item alone
            continue
    return items, names


def read_atlasloot():
    """-> (items {id: sentence}, npc names {id: name}) from the dungeon and raid tables only"""
    p = ROOT / "bis" / "own" / "cache" / "atlasloot_sources.json"
    if not p.exists():
        return {}, {}
    items, names = {}, {}
    for iid, recs in json.loads(p.read_text(encoding="utf-8"))["items"].items():
        for r in recs:
            if r.get("m") != "DungeonsAndRaids" or not r.get("z") or not r.get("b"):
                continue
            if r.get("npc"):
                names[int(r["npc"])] = r["b"]
            if r["b"] == "Trash":
                items.setdefault(int(iid), "Drops from trash in %s (Clue)" % r["z"])
            else:
                items.setdefault(int(iid), "Drops from %s in %s (Clue)" % (r["b"], r["z"]))
    return items, names


def read_recorded(names):
    """-> (items {id: sentence}, nameless [(npc, zone, [items])])"""
    p = ROOT / "bis" / "own" / "recorded.json"
    if not p.exists():
        return {}, []
    r = json.loads(p.read_text(encoding="utf-8"))
    out, nameless = {}, []
    for npc, v in (r.get("drops") or {}).items():
        name = names.get(int(npc))
        if name is None:
            nameless.append((npc, v.get("z"), sorted(int(i) for i in v["i"])))
            continue
        for item in v["i"]:
            out.setdefault(int(item), "Drops from %s in %s (Seen in Forever)" % (name, v.get("z") or "the world"))
    for q, v in (r.get("quests") or {}).items():
        title = v.get("t")
        c, rw = v.get("c") or [], v.get("r") or []
        c = list(c.values()) if isinstance(c, dict) else c
        rw = list(rw.values()) if isinstance(rw, dict) else rw
        for item in c + rw:
            out.setdefault(int(item), "Quest reward: %s%s (Seen in Forever)" % (title, " (a choice)" if item in c else ""))
    return out, nameless


QUESTIE_LIVE = ROOT / "bis" / "own" / "cache" / "questiedb_live.json"
QUESTIE_ZONES = Path("D:/World of Warcraft/_forever_/Interface/AddOns/QuestieDB/support/Forever/Zones")


def instance_names():
    """QuestieDB area id -> instance name (support/Forever/Zones/dungeons.lua), the areas that are dungeons."""
    import re
    out = {}
    p = QUESTIE_ZONES / "dungeons.lua"
    if p.exists():
        for m in re.finditer(r'^\s*\[(\d+)\] = \{"([^"]+)"', p.read_text(encoding="utf-8").split(chr(10) + "if Expansions")[0], re.M):
            out[int(m.group(1))] = m.group(2)
    return out


def read_questiedb():
    """-> {item id: sentence} from QuestieDB's item table (GPL v3; bis/tools/questiedb_decode.py makes the cache).

    Only unambiguous answers: one creature drops it, one vendor sells it, one quest rewards it. A creature inside an instance gives
    "Drops from X in <instance>"; an outdoor creature "Drops from X" (the parser would read "in <zone>" as an instance)."""
    if not QUESTIE_LIVE.exists():
        return {}
    d = json.loads(QUESTIE_LIVE.read_text(encoding="utf-8"))
    npcs, quests, items = d["npc"], d["quest"], d["item"]
    inst = instance_names()
    out = {}

    def one(ids):
        ids = [i for i in (ids or []) if str(i) in npcs]
        names = {npcs[str(i)].get("name") for i in ids}
        return npcs[str(ids[0])] if ids and len(names) == 1 else None

    for iid, rec in items.items():
        iid = int(iid)
        npc = one(rec.get("npcDrops"))
        vendor = one(rec.get("vendors"))
        qr = [quests[str(q)] for q in (rec.get("questRewards") or []) if str(q) in quests]
        if npc and npc.get("name"):
            area = npc.get("zoneID")
            if area in inst:
                out[iid] = "Drops from %s in %s (Clue)" % (npc["name"], inst[area])
            else:
                out[iid] = "Drops from %s (Clue)" % npc["name"]
        elif vendor and vendor.get("name"):
            out[iid] = "Sold by %s (Clue)" % vendor["name"]
        elif len(qr) == 1 and qr[0].get("name"):
            lv = qr[0].get("questLevel")
            out[iid] = "Quest reward: %s%s (Clue)" % (qr[0]["name"], ", level %d" % lv if lv else "")
    return out


def read_collectable():
    """-> {item id: sentence} from the client's own vendor table (bis/tools/collectable_vendors.py): "Sold by <vendor> in <zone> (Forever client)".
    Only items a single vendor sells; the sentence names the zone only when the vendor has one mapped spot."""
    p = ROOT / "bis" / "own" / "cache" / "vendor_spots.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for iid, cids in d["items"].items():
        named = [d["vendors"][str(c)] for c in cids if d["vendors"][str(c)]["name"]]
        if len({v["name"] for v in named}) != 1:
            continue
        v = named[0]
        zone = v["spots"][0][3] if len(v["spots"]) == 1 and v["spots"][0][3] else ""
        out[int(iid)] = "Sold by %s%s (Forever client)" % (v["name"], " in " + zone if zone else "")
    return out


def read_fmb(addons):
    """-> {item id: sentence} from ForeverMyBis's item table (MIT, installed addon, read only), its source text mapped to our wording."""
    import re
    p = addons / "ForeverMyBis" / "Data" / "Items.lua"
    if not p.exists():
        return {}
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    items = lua.eval("function(src) local ns = {} assert(load(src))('x', ns) return ns.items end")(
        p.read_text(encoding="utf-8", errors="replace"))
    out = {}
    for iid in items.keys():
        src = items[iid]["src"]
        if not isinstance(src, str):
            continue
        m = re.match(r"^Drops from (.+?), ([^,]+)$", src)
        if m and "not known" not in src:
            who, zone = m.groups()
            if who in ("Trash", "Multiple NPCs"):
                out[int(iid)] = "Drops from trash in %s (Clue)" % zone if who == "Trash" else None
            else:
                out[int(iid)] = "Drops from %s (Clue)" % who
            if out[int(iid)] is None:
                del out[int(iid)]
            continue
        m = re.match(r"^World drop: creatures near level (\d+)", src)
        if m:
            out[int(iid)] = "World drop: creatures near level %s (Clue)" % m.group(1)
            continue
        m = re.match(r"^(.+), (Friendly|Honored|Revered|Exalted)$", src)
        if m:
            out[int(iid)] = "Needs %s with %s (Clue)" % (m.group(2), m.group(1))
            continue
        m = re.match(r"^Sold by (.+?), ([^,]+)$", src)
        if m:
            out[int(iid)] = "Sold by %s in %s (Clue)" % m.groups()
            continue
        m = re.match(r"^Quest: (.+?) \W+ .*?(?:level (\d+))?", src)
        if src.startswith("Quest: "):
            title = re.split(r"\s\W\s", src[7:])[0].strip()
            lv = re.search(r"level (\d+)", src)
            if title:
                out[int(iid)] = "Quest reward: %s%s (Clue)" % (title, ", level %s" % lv.group(1) if lv else "")
    return out


def main():
    addons = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    unknown = unknown_ids()
    names = {int(k): v for k, v in json.loads(NAMES.read_text(encoding="utf-8")).items()} if NAMES.exists() else {}
    j_items, j_names = read_journal(addons)
    for k, v in j_names.items():
        names.setdefault(k, v)
    a_items, a_names = read_atlasloot()
    for k, v in a_names.items():
        names.setdefault(k, v)
    rec_items, nameless = read_recorded(names)
    q_items = read_questiedb()
    f_items = read_fmb(addons)
    c_items = read_collectable()
    web = json.loads(WEB.read_text(encoding="utf-8")) if WEB.exists() else {}

    found = {}
    for iid, name in sorted(unknown.items()):
        if iid in rec_items:
            found[iid] = {"src": rec_items[iid], "via": "our own recordings"}
        elif str(iid) in web:
            found[iid] = {"src": web[str(iid)]["src"], "via": web[str(iid)].get("via", "")}
        elif iid in j_items:
            found[iid] = {"src": j_items[iid], "via": "ForeverDungeonJournal"}
        elif iid in a_items:
            found[iid] = {"src": a_items[iid], "via": "AtlasLoot Continued"}
        elif iid in c_items:
            found[iid] = {"src": c_items[iid], "via": "the game's vendor table"}
        elif iid in q_items:
            found[iid] = {"src": q_items[iid], "via": "QuestieDB"}
        elif iid in f_items:
            found[iid] = {"src": f_items[iid], "via": "ForeverMyBis"}
    OUT.write_text(json.dumps({"items": {str(k): v for k, v in found.items()}}, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    lines = ["# Found sources (generated by bis/tools/found_sources.py)", "",
             "Items Mr.BiZ shows as 'source not known yet': %d. Placed by this run: %d." % (len(unknown), len(found)), ""]
    by = {}
    for v in found.values():
        by[v["via"]] = by.get(v["via"], 0) + 1
    lines += ["- %s: %d" % (k, n) for k, n in sorted(by.items())]
    lines += ["", "## Recorded drops without a creature name (add them to bis/own/npc_names.json)", ""]
    for npc, zone, its in nameless:
        hit = [i for i in its if i in unknown]
        if hit:
            lines.append("- npc %s (%s): %s" % (npc, zone, ", ".join("%d %s" % (i, unknown[i]) for i in hit)))
    lines += ["", "## Still unknown", ""]
    lines += ["- %d %s" % (i, n) for i, n in sorted(unknown.items()) if i not in found]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("unknown %d, placed %d: %s" % (len(unknown), len(found), by))


if __name__ == "__main__":
    main()
