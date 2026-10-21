"""Turn the route log's SavedVariables (/r2f route start ... stop) into a readable timeline and a quest table.

    python addon/tools/route_report.py [RoadToForever.lua ...] [--run N] [--out FILE]

With no file it reads the beta client's SavedVariables on this PC (every account). Each input is a
WTF/Account/<account>/SavedVariables/RoadToForever.lua; send yours to the owner like the recorder's. The report lists, per run:
the timeline (every quest offered, accepted, progressed, handed in, every level, zone, NPC and note, with the time and the map
position), a quest table (when, at what level, who, how long it took, which quests it unlocked right after), the NPCs met and the
length of the path walked per map. Part of the launch route work (BACKLOG: route log).
"""
import argparse
import math
import sys
from pathlib import Path

import lupa

DEFAULT = Path("D:/World of Warcraft/_classic_beta_/WTF/Account")
FOLLOW_SECONDS = 90          # a quest accepted this soon after a hand-in is listed as unlocked by it


def to_py(v):
    if lupa.lua_type(v) == "table":
        keys = list(v.keys())
        if keys and all(isinstance(k, (int, float)) for k in keys) and sorted(keys) == list(range(1, len(keys) + 1)):
            return [to_py(v[k]) for k in sorted(keys)]
        return {(str(int(k)) if isinstance(k, float) and k == int(k) else str(k)): to_py(v[k]) for k in keys}
    return v


def read_runs(path):
    lua = lupa.LuaRuntime()
    lua.execute(Path(path).read_text(encoding="utf-8", errors="replace"))
    db = lua.globals().R2FDB
    route = db["route"] if db is not None else None
    if route is None:
        return []
    runs = to_py(route).get("runs") or []
    return runs if isinstance(runs, list) else list(runs.values())


def clock(seconds):
    seconds = int(seconds or 0)
    return "%d:%02d:%02d" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)


def where(ev):
    if ev.get("m") is None:
        return ""
    return " @ %s %.1f,%.1f" % (ev["m"], ev.get("x", 0), ev.get("y", 0))


def describe(ev):
    e = ev.get("e")
    q = ev.get("q")
    title = ev.get("title") or ""
    if e == "start":
        return "START in %s / %s" % (ev.get("z"), ev.get("sz"))
    if e == "login":
        return "login (run continued)"
    if e == "stop":
        return "STOP"
    if e == "offer":
        return 'offered #%s "%s" by %s (%s)' % (q, title, ev.get("npcName"), ev.get("npc"))
    if e == "accept":
        objs = "; ".join(o[0] if isinstance(o, list) else str(o) for o in (ev.get("obj") or []))
        return 'ACCEPT #%s "%s" quest level %s  [%s]' % (q, title, ev.get("ql"), objs)
    if e == "have":
        return 'already had #%s "%s"' % (q, title)
    if e == "prog":
        return 'progress #%s: %s (%s/%s)' % (q, ev.get("tx"), ev.get("n"), ev.get("of"))
    if e == "handin":
        return 'hand-in window #%s "%s" at %s (%s)' % (q, title, ev.get("npcName"), ev.get("npc"))
    if e == "done":
        return "DONE #%s  +%s xp, %s copper" % (q, ev.get("xpGain"), ev.get("copper"))
    if e == "drop":
        return 'abandoned #%s "%s"' % (q, title)
    if e == "level":
        return "LEVEL UP to %s" % ev.get("to")
    if e == "zone":
        return "zone %s / %s" % (ev.get("z"), ev.get("sz"))
    if e == "npc":
        return "%s %s (%s) in %s" % (ev.get("kind"), ev.get("name"), ev.get("id"), ev.get("sz"))
    if e == "dead":
        return "DIED in %s" % ev.get("sz")
    if e == "bind":
        return "hearthstone bound in %s" % ev.get("sz")
    if e == "note":
        return 'NOTE: %s' % ev.get("tx")
    return str(ev)


def quest_table(events):
    quests = {}
    for ev in events:
        q = ev.get("q")
        if q is None:
            continue
        row = quests.setdefault(q, {"title": ev.get("title"), "first": ev["t"]})
        row["title"] = row["title"] or ev.get("title")
        e = ev["e"]
        if e == "offer":
            row.setdefault("offered", ev["t"])
            row["giver"] = ev.get("npcName")
        elif e == "accept":
            row["accepted"] = ev["t"]
            row["lv_accept"] = ev.get("lv")
            row["ql"] = ev.get("ql")
        elif e == "done":
            row["done"] = ev["t"]
            row["lv_done"] = ev.get("lv")
            row["xp"] = ev.get("xpGain")
        elif e == "drop":
            row["dropped"] = ev["t"]
        elif e == "handin":
            row["turnin"] = ev.get("npcName")
    for q, row in quests.items():
        if "done" in row:
            row["unlocked"] = [q2 for q2, r2 in quests.items()
                               if q2 != q and "accepted" in r2 and 0 <= r2["accepted"] - row["done"] <= FOLLOW_SECONDS]
    return quests


def path_length(trail):
    """Length of the walked path per map, in map-percent units (sum of the steps between two points on the same map)."""
    out = {}
    prev = None
    for p in trail:
        if prev and prev[1] == p[1]:
            out[p[1]] = out.get(p[1], 0) + math.hypot(p[2] - prev[2], p[3] - prev[3])
        prev = p
    return out


def render(run, index=1):
    events = run.get("events") or []
    lines = ["# Route log run %d: %s (%s %s, level %s at the start)" % (
        index, run.get("label") or "unnamed", run.get("race"), run.get("class"), run.get("level")), ""]
    lines.append("## Timeline")
    for ev in events:
        lines.append("%s  L%s  %s%s" % (clock(ev.get("t")), ev.get("lv", "?"), describe(ev), where(ev)))
    quests = quest_table(events)
    lines += ["", "## Quests (in the order they were accepted)", "",
              "| # | quest | giver | level at accept | quest level | accepted | done | took | xp | unlocked right after |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for q, r in sorted(quests.items(), key=lambda kv: kv[1].get("accepted", kv[1]["first"])):
        took = clock(r["done"] - r["accepted"]) if "done" in r and "accepted" in r else ""
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            q, r.get("title") or "?", r.get("giver") or "", r.get("lv_accept", ""), r.get("ql", ""),
            clock(r["accepted"]) if "accepted" in r else "", clock(r["done"]) if "done" in r else ("abandoned" if "dropped" in r else ""),
            took, r.get("xp", ""), ", ".join("#%s" % u for u in r.get("unlocked", []))))
    npcs = [ev for ev in events if ev.get("e") == "npc"]
    if npcs:
        lines += ["", "## NPCs met", ""]
        for ev in npcs:
            lines.append("- %s %s (%s) %s" % (ev.get("kind"), ev.get("name"), ev.get("id"), where(ev).strip()))
    lengths = path_length(run.get("trail") or [])
    if lengths:
        lines += ["", "## Path walked (map percent units, per map)", ""]
        for m, n in sorted(lengths.items()):
            lines.append("- map %s: %.0f" % (m, n))
    lines += ["", "(%d events, %d path points)" % (len(events), len(run.get("trail") or []))]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--run", type=int, help="only this run number (1 = the first)")
    ap.add_argument("--out", help="write the report to this file instead of the screen")
    args = ap.parse_args()
    files = args.files or [str(p) for p in sorted(DEFAULT.glob("*/SavedVariables/RoadToForever.lua"))]
    parts = []
    for f in files:
        for i, run in enumerate(read_runs(f), start=1):
            if args.run and i != args.run:
                continue
            parts.append(render(run, i))
    text = "\n\n".join(parts) if parts else "no route log runs found"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print("wrote", args.out)
    else:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", "replace"))


if __name__ == "__main__":
    main()
