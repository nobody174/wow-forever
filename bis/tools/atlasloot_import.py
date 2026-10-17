"""Read AtlasLoot Continued's Forever data (the community addon installed in the beta client; GPL v2) into item -> sources.
Part of OWN_DATABASE_PLAN.md, M2.

    python bis/tools/atlasloot_import.py [addons folder]

Reads <addons>/AtlasLootContinued_{DungeonsAndRaids,Factions,PvP,Crafting,Collections}/data-forever.lua and writes
bis/own/cache/atlasloot_sources.json: item id -> [{t, where, boss, npc, lv, ...}] plus the version of the addon it was read from.
The files are Lua tables; this is a line reader, not a Lua interpreter, and reports every line shape it did not understand.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "bis" / "own" / "cache" / "atlasloot_sources.json"
DEFAULT = Path("D:/World of Warcraft/_classic_beta_/Interface/AddOns")
MODULES = ["DungeonsAndRaids", "Factions", "PvP", "Crafting", "Collections"]


def read_module(folder, module, out, stats):
    p = folder / ("AtlasLootContinued_" + module) / "data-forever.lua"
    if not p.exists():
        return
    zone = zone_levels = boss = npc = lv = None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        m = re.match(r'^data\["([^"]+)"\]\s*=\s*\{', line)
        if m:
            zone, zone_levels, boss, npc, lv = m.group(1), None, None, None, None
            continue
        m = re.match(r'^\s*name = AL\["(.+?)"\]', line)
        if m:
            if line.startswith("\tname"):          # the table's own name (one tab), bosses sit deeper
                zone_name = m.group(1)
                zone = zone_name
            else:
                boss, npc, lv = m.group(1), None, None
            continue
        m = re.match(r"^\s*npcID = (\d+)", line)
        if m:
            npc = int(m.group(1))
            continue
        m = re.match(r"^\s*Level = (\d+)", line)
        if m:
            lv = int(m.group(1))
            continue
        m = re.match(r"^\s*LevelRange = \{(\d+), (\d+), (\d+)\}", line)
        if m:
            zone_levels = [int(x) for x in m.groups()]
            continue
        m = re.match(r"^\s*\{\s*(\d+),\s*(\d+)\s*(?:,\s*([^}]*))?\},?\s*(?:--\s*(.*))?$", line)
        if m and zone:
            slot, item, extra, comment = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
            if item >= 1000000 or item < 10:        # headers / icons are not items
                continue
            rec = {"m": module, "z": zone, "b": boss, "npc": npc, "lv": lv, "zl": zone_levels, "n": comment}
            if extra and extra.strip():
                rec["x"] = extra.strip()[:80]
            out[item].append(rec)
            stats[module] += 1


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    out, stats = defaultdict(list), Counter()
    for m in MODULES:
        read_module(folder, m, out, stats)
    ver = ""
    toc = folder / "AtlasLootContinued" / "AtlasLootContinued_Vanilla.toc"
    if toc.exists():
        mm = re.search(r"## Version: (\S+)", toc.read_text(encoding="utf-8", errors="replace"))
        ver = mm.group(1) if mm else ""
    OUT.write_text(json.dumps({"version": ver, "items": {str(k): v for k, v in out.items()}}, separators=(",", ":")), encoding="utf-8")
    print("AtlasLoot Continued %s: %d item rows (%s), %d distinct items -> %s" % (ver, sum(stats.values()), dict(stats), len(out), OUT.name))


if __name__ == "__main__":
    main()
