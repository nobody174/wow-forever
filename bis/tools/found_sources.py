"""Collect where items come from, for the picks Mr.BiZ cannot place, into bis/found_sources.json.

    python bis/tools/found_sources.py [addons folder]

Inputs, best first (an item keeps the first source found):
  1. our own recordings (bis/own/recorded.json, see recorder_import.py): "Seen in Forever"
  2. ForeverDungeonJournal's data (installed addon, read-only): boss loot, shared dungeon loot, quest rewards: "Clue"
     (the addon says itself that it mixes observed Forever items with inherited Classic assignments)
  3. AtlasLoot Continued's Forever tables (bis/own/cache/atlasloot_sources.json, made by atlasloot_import.py; GPL v2): "Clue"
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
