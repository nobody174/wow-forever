"""Merge the Recorder's SavedVariables (addon/RoadToForever/Recorder.lua) of everyone in the group into bis/own/recorded.json.

    python bis/tools/recorder_import.py [RoadToForever.lua ...]    # default: the beta client's SavedVariables on this PC

Each input is a WTF/Account/<account>/SavedVariables/RoadToForever.lua (send yours to the owner). Counts are summed per creature and item,
so run it once with every file together (the output is rebuilt from the inputs, not added to). Part of OWN_DATABASE_PLAN.md, M2.
What an earlier run wrote stays (counts: the larger value); `--fresh` rebuilds from the inputs only.
"""
import json
import sys
from pathlib import Path

import lupa

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "bis" / "own" / "recorded.json"
DEFAULT = Path("D:/World of Warcraft/_forever_/WTF/Account")


def to_py(v):
    if lupa.lua_type(v) == "table":
        keys = list(v.keys())
        if keys and all(isinstance(k, (int, float)) for k in keys) and sorted(keys) == list(range(1, len(keys) + 1)):
            return [to_py(v[k]) for k in sorted(keys)]
        return {(str(int(k)) if isinstance(k, float) and k == int(k) else str(k)): to_py(v[k]) for k in keys}
    return v


def read(path):
    lua = lupa.LuaRuntime()
    lua.execute(Path(path).read_text(encoding="utf-8", errors="replace"))
    db = lua.globals().R2FDB
    rec = db["recorder"] if db is not None else None
    return to_py(rec) if rec is not None else None


def merge(files):
    out = {"drops": {}, "objects": {}, "vendors": {}, "quests": {}, "sources": []}
    for f in files:
        r = read(f)
        if not r:
            continue
        out["sources"].append({"file": Path(f).name, "since": r.get("since")})
        for kind in ("drops", "objects"):
            for npc, v in (r.get(kind) or {}).items():
                o = out[kind].setdefault(npc, {"k": 0, "z": v.get("z"), "lv": v.get("lv"), "i": {}})
                o["k"] += v.get("k", 0)
                o["lv"] = o["lv"] or v.get("lv")
                for item, n in (v.get("i") or {}).items():
                    o["i"][item] = o["i"].get(item, 0) + n
        for npc, v in (r.get("vendors") or {}).items():
            o = out["vendors"].setdefault(npc, {"z": v.get("z"), "i": {}})
            o["i"].update(v.get("i") or {})
        for q, v in (r.get("quests") or {}).items():
            out["quests"].setdefault(q, v)
    return out


def keep_previous(out):
    """Fold the file written by an earlier run into `out`, so data from clients that are gone (the beta) is not lost.
    Counts use the larger of the two values, not the sum: the same SavedVariables read twice must not double anything."""
    if not OUT.exists():
        return out
    old = json.loads(OUT.read_text(encoding="utf-8"))
    for kind in ("drops", "objects"):
        for npc, v in (old.get(kind) or {}).items():
            o = out[kind].setdefault(npc, {"k": 0, "z": v.get("z"), "lv": v.get("lv"), "i": {}})
            o["k"] = max(o["k"], v.get("k", 0))
            o["lv"] = o["lv"] or v.get("lv")
            for item, n in (v.get("i") or {}).items():
                o["i"][item] = max(o["i"].get(item, 0), n)
    for npc, v in (old.get("vendors") or {}).items():
        o = out["vendors"].setdefault(npc, {"z": v.get("z"), "i": {}})
        for item, n in (v.get("i") or {}).items():
            o["i"].setdefault(item, n)
    for q, v in (old.get("quests") or {}).items():
        out["quests"].setdefault(q, v)
    out["sources"] = (old.get("sources") or []) + [x for x in out["sources"] if x not in (old.get("sources") or [])]
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    files = args or [str(p) for p in DEFAULT.glob("*/SavedVariables/RoadToForever.lua")]
    out = merge(files)
    if "--fresh" not in sys.argv:
        out = keep_previous(out)
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print("%d file(s): %d creatures, %d chests/nodes, %d vendors, %d quests -> %s" % (
        len(files), len(out["drops"]), len(out["objects"]), len(out["vendors"]), len(out["quests"]), OUT.name))


if __name__ == "__main__":
    main()
