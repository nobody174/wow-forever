"""Where do items come from in Classic? Reads the CMaNGOS classic-db dump (open data, GPL, a shallow clone in bis/own/cache/classic-db)
and writes bis/own/cache/classic_sources.json: item id -> list of sources. Part of OWN_DATABASE_PLAN.md, milestone M2.

    git clone --depth 1 https://github.com/cmangos/classic-db.git bis/own/cache/classic-db
    gunzip -c bis/own/cache/classic-db/Full_DB/*.sql.gz > bis/own/cache/classicdb.sql
    python bis/tools/classic_sources.py

Source records (short keys): {"t": "drop"|"vendor"|"quest"|"object"|"pickpocket", ...}
  drop:   c creature id, n name, lv level range "a-b", rk rank (0 normal ... 3 boss), p chance in percent, map map id of its spawns (most common)
  vendor: c npc id, n name, map
  quest:  q quest id, n title, lv quest level, ml min level, z zone or sort id, ch true if it is a choice reward, rc required races mask
  object: o gameobject loot id (chests, nodes), p chance
Loot references (negative mincountOrRef) are followed one level: the reference group's items get the parent creature as source.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / "bis" / "own" / "cache" / "classicdb.sql"
OUT = ROOT / "bis" / "own" / "cache" / "classic_sources.json"
TABLES = ["creature_template", "creature_loot_template", "reference_loot_template", "gameobject_loot_template", "npc_vendor",
          "npc_vendor_template", "quest_template", "pickpocketing_loot_template", "creature", "gameobject_template"]


def split_values(s):
    """Parse the tuples of one INSERT ... VALUES (...),(...); statement."""
    rows, row, i, n = [], [], 0, len(s)
    while i < n:
        c = s[i]
        if c == "(":
            row, i = [], i + 1
            while True:
                if s[i] == "'":
                    j, buf = i + 1, []
                    while True:
                        ch = s[j]
                        if ch == "\\":
                            nxt = s[j + 1]
                            buf.append({"n": "\n", "r": "\r", "0": "\0"}.get(nxt, nxt))
                            j += 2
                        elif ch == "'" and s[j + 1:j + 2] == "'":
                            buf.append("'")
                            j += 2
                        elif ch == "'":
                            break
                        else:
                            buf.append(ch)
                            j += 1
                    row.append("".join(buf))
                    i = j + 1
                else:
                    j = i
                    while s[j] not in ",)":
                        j += 1
                    tok = s[i:j]
                    row.append(None if tok == "NULL" else tok)
                    i = j
                if s[i] == ",":
                    i += 1
                    continue
                if s[i] == ")":
                    rows.append(row)
                    i += 1
                    break
        else:
            i += 1
    return rows


def read_tables():
    cols, data = {}, {t: [] for t in TABLES}
    cur = None
    with open(SQL, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("CREATE TABLE `"):
                cur = line.split("`")[1]
                cols[cur] = []
            elif cur and line.startswith("  `"):
                cols[cur].append(line.split("`")[1])
            elif line.startswith(") ENGINE"):
                cur = None
            elif line.startswith("INSERT INTO `"):
                t = line.split("`")[1]
                if t in data:
                    body = line[line.index("VALUES") + 6:].rstrip().rstrip(";")
                    for r in split_values(body):
                        data[t].append(dict(zip(cols[t], r)))
    return data


def num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def main():
    d = read_tables()
    print({t: len(v) for t, v in d.items()})
    ctpl = {int(r["Entry"]): r for r in d["creature_template"]}
    # most common map of each creature's spawns
    maps = defaultdict(Counter)
    for r in d["creature"]:
        maps[int(r["id"])][int(r["map"])] += 1
    out = defaultdict(list)

    def creature_info(cid):
        t = ctpl.get(cid)
        if not t:
            return None
        lo, hi = int(t["MinLevel"]), int(t["MaxLevel"])
        m = maps[cid].most_common(1)
        return {"c": cid, "n": t["Name"], "lv": "%d-%d" % (lo, hi) if lo != hi else str(lo), "rk": int(t["Rank"]),
                "map": m[0][0] if m else None}

    def with_group_chances(rows):
        """CMaNGOS loot groups: a row with groupid > 0 and chance 0 shares what the group's explicit chances leave over, equally."""
        groups = defaultdict(list)
        for r in rows:
            groups[(r["entry"], int(r["groupid"]))].append(r)
        out_rows = []
        for (entry, gid), rs in groups.items():
            ch = [abs(num(r["ChanceOrQuestChance"])) for r in rs]
            if gid:
                zero = sum(1 for c in ch if c == 0)
                left = max(0.0, 100.0 - sum(ch))
                ch = [c if c else left / zero for c in ch]
            for r, c in zip(rs, ch):
                out_rows.append((r, c))
        return out_rows

    # reference groups: entry -> [(item, chance in percent within the reference)]
    refs = defaultdict(list)
    for r, c in with_group_chances(d["reference_loot_template"]):
        refs[int(r["entry"])].append((int(r["item"]), c, int(r["groupid"])))
    by_loot = defaultdict(list)                        # creature loot id -> creature ids
    for cid, t in ctpl.items():
        lid = int(t["LootId"] or 0)
        by_loot[lid or cid].append(cid)
    for r, ch in with_group_chances(d["creature_loot_template"]):
        entry, item, ref = int(r["entry"]), int(r["item"]), int(r["mincountOrRef"])
        for cid in by_loot.get(entry, []):
            info = creature_info(cid)
            if not info:
                continue
            if ref < 0:                                # a reference to a shared group (equal chance inside the group)
                for it, c2, grp in refs.get(-ref, []):
                    out[it].append(dict(info, t="drop", p=round(ch * c2 / 100.0, 4), via="ref"))
            else:
                out[item].append(dict(info, t="drop", p=round(abs(ch), 4)))
    for r in d["pickpocketing_loot_template"]:
        for cid in by_loot.get(int(r["entry"]), []):
            info = creature_info(cid)
            if info:
                out[int(r["item"])].append(dict(info, t="pickpocket", p=round(abs(num(r["ChanceOrQuestChance"])), 4)))
    vend_tpl = defaultdict(list)
    for r in d["npc_vendor_template"]:
        vend_tpl[int(r["entry"])].append(int(r["item"]))
    for r in d["npc_vendor"]:
        info = creature_info(int(r["entry"]))
        if info:
            out[int(r["item"])].append(dict({k: info[k] for k in ("c", "n", "map")}, t="vendor"))
    for cid, t in ctpl.items():
        vt = int(t.get("VendorTemplateId") or 0)
        if vt and vt in vend_tpl:
            info = creature_info(cid)
            for it in vend_tpl[vt]:
                out[it].append(dict({k: info[k] for k in ("c", "n", "map")}, t="vendor"))
    for r in d["quest_template"]:
        q = int(r["entry"])
        base = {"t": "quest", "q": q, "n": r["Title"], "lv": int(r["QuestLevel"]), "ml": int(r["MinLevel"]), "z": int(r["ZoneOrSort"]),
                "rc": int(r["RequiredRaces"])}
        for k in range(1, 7):
            it = int(r.get("RewChoiceItemId%d" % k) or 0)
            if it:
                out[it].append(dict(base, ch=True))
        for k in range(1, 5):
            it = int(r.get("RewItemId%d" % k) or 0)
            if it:
                out[it].append(dict(base, ch=False))
    for r in d["gameobject_loot_template"]:
        out[int(r["item"])].append({"t": "object", "o": int(r["entry"]), "p": round(abs(num(r["ChanceOrQuestChance"])), 4)})
    OUT.write_text(json.dumps({str(k): v for k, v in out.items()}, separators=(",", ":")), encoding="utf-8")
    kinds = Counter(s["t"] for v in out.values() for s in v)
    print("wrote %s: %d items with a source; %s" % (OUT.name, len(out), dict(kinds)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
