"""Writes bis/quest-weapons.json: weapons that are quest rewards, from Wowhead Forever's item list pages.

For each weapon type the page's `var listviewitems` carries reqlevel, quality, dps, source (4 = quest reward) and
sourcemore = [{n: quest name, ti: quest id, c: zone id, t: 5}]. Zone ids are turned into names through the zone page title.
Only green or better items up to MAXLEVEL are kept. Run it by hand when the beta data changes:

    python bis/tools/wh_quest_weapons.py [maxlevel]

Needs the internet (www.wowhead.com/forever), nothing else. Part of bis/archive/quest-weapons-research.md.
"""
import json, os, re, subprocess, sys

def curl(url):
    r = subprocess.run(["curl", "-s", "-L", "-m", "60", "-A", "Mozilla/5.0", url], capture_output=True)
    return r.stdout.decode("utf-8", "replace")

def listview_items(html):
    """The page's `var listviewitems = [...]` array as a list of dicts."""
    i = html.find("var listviewitems = ")
    if i < 0:
        return []
    j = html.index("[", i)
    depth = 0
    instr = False
    esc = False
    chunk = None
    for k in range(j, len(html)):
        c = html[k]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            continue
        if c == '"':
            instr = True
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                chunk = html[j:k + 1]
                break
    if chunk is None:
        return []
    # a few keys are unquoted JS (firstseenpatch: 0); quote any bare key outside strings
    out = []
    instr = False
    esc = False
    n = len(chunk)
    k = 0
    while k < n:
        c = chunk[k]
        if instr:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            k += 1
            continue
        if c == '"':
            instr = True
            out.append(c)
            k += 1
            continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*(?=\s*:)", chunk[k:k + 60])
        if m and out and out[-1] in "{, ":
            out.append('"' + m.group(0) + '"')
            k += len(m.group(0))
            continue
        out.append(c)
        k += 1
    try:
        return json.loads("".join(out))
    except Exception as e:
        print("json error", e)
        return []


ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "bis", "quest-weapons.json")
MAXLEVEL = int(sys.argv[1]) if len(sys.argv) > 1 else 32

# page path -> short name used in the file
TYPES = {
    "weapons/one-handed-axes": "1h axe", "weapons/two-handed-axes": "2h axe",
    "weapons/one-handed-maces": "1h mace", "weapons/two-handed-maces": "2h mace",
    "weapons/one-handed-swords": "1h sword", "weapons/two-handed-swords": "2h sword",
    "weapons/daggers": "dagger", "weapons/staves": "staff", "weapons/polearms": "polearm",
    "weapons/fist-weapons": "fist", "weapons/bows": "bow", "weapons/guns": "gun",
    "weapons/crossbows": "crossbow", "weapons/wands": "wand", "weapons/thrown": "thrown",
    "armor/shields": "shield",
}

_zone_names = {}


def zone_name(zid):
    if zid in _zone_names:
        return _zone_names[zid]
    html = curl("https://www.wowhead.com/forever/zone=%s" % zid)
    m = re.search(r"<title>([^<]*?) - Zone - Forever", html)
    _zone_names[zid] = m.group(1) if m else None
    return _zone_names[zid]


def main():
    rows = []
    for path, kind in TYPES.items():
        items = listview_items(curl("https://www.wowhead.com/forever/items/" + path))
        kept = 0
        for it in items:
            if 4 not in (it.get("source") or []):
                continue
            if it.get("reqlevel", 0) > MAXLEVEL or it.get("quality", 0) < 2:
                continue
            quests = [x for x in (it.get("sourcemore") or []) if x.get("t") == 5]
            if not quests:
                continue
            q = quests[0]
            rows.append({"id": it["id"], "name": it["name"], "type": kind, "reqlevel": it.get("reqlevel", 0),
                         "quality": it.get("quality", 0), "dps": it.get("dps"), "slot": it.get("slot"),
                         "quest": q.get("n"), "questId": q.get("ti"), "zoneId": q.get("c"),
                         "side": it.get("side")})
            kept += 1
        print("%-10s %3d items listed, %3d quest rewards kept" % (kind, len(items), kept))
    for r in rows:
        r["zone"] = zone_name(r["zoneId"]) if r["zoneId"] else None
    rows.sort(key=lambda r: (r["reqlevel"], r["type"], r["name"]))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"_about": "Quest-reward weapons up to level %d from Wowhead Forever's item lists (side: 1 Alliance, 2 Horde, "
                             "absent both). Generated by bis/tools/wh_quest_weapons.py." % MAXLEVEL,
                   "maxlevel": MAXLEVEL, "items": rows}, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", os.path.normpath(OUT), len(rows), "items")


if __name__ == "__main__":
    main()
