"""Build the Mr.BiZ best-in-slot data for the site and the addon.

Input:  bis/raw/<class>-<spec>.json, one per spec, taken from ForeverDB's public
        BiS pages (https://foreverdb.net/bis/<class>/<spec>, level 30 PvE: the beta
        cap). Each holds the stat weights and, per slot, the best item (id, name,
        score, stats, source sentence, confidence label, ease) and the next two
        picks with how far behind they are. See bis/README.md for how to refresh.

Output: bis-data.json                       the site's BiS tab (bis.html)
        addon/RoadToForever/BiZData.lua      the addon's Mr.BiZ tab (generated: never hand-edit)

The source sentence is parsed into a type (one per filter chip on the site and in
game), a short label, the profession / skill, the instance, the drop chance and the
faction, so both front ends filter and group the same way.

Usage (repo root):  python bis/build_bis.py          writes both files
                    python bis/build_bis.py --check  exit 1 if either file is stale
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
RAW = os.path.join(HERE, "raw")
SITE_OUT = os.path.join(ROOT, "bis-data.json")
LUA_OUT = os.path.join(ROOT, "addon", "RoadToForever", "BiZData.lua")

LEVEL = 30
UPDATED = "2026-10-12"
SOURCE_NAME = "ForeverDB"
SOURCE_URL = "https://foreverdb.net/bis"

# Class order: the site's roster order (armor type, Cloth -> Plate; CLAUDE.md), with
# Druid in its leather place. Each spec: (key, name, role).
CLASSES = [
    ("priest", "Priest", [("discipline", "Discipline", "healer"), ("holy", "Holy", "healer"),
                          ("shadow", "Shadow", "dps")]),
    ("warlock", "Warlock", [("affliction", "Affliction", "dps"), ("demonology", "Demonology", "dps"),
                            ("destruction", "Destruction", "dps")]),
    ("mage", "Mage", [("arcane", "Arcane", "dps"), ("fire", "Fire", "dps"), ("frost", "Frost", "dps")]),
    ("rogue", "Rogue", [("assassination", "Assassination", "dps"), ("combat", "Combat", "dps"),
                        ("subtlety", "Subtlety", "dps")]),
    # ForeverDB's Feral page is weighted for tanking (defense, dodge, armor first), so it
    # is listed as Feral (Bear). It has no separate cat list yet.
    ("druid", "Druid", [("feral", "Feral (Bear)", "tank"), ("balance", "Balance", "dps"),
                        ("restoration", "Restoration", "healer")]),
    ("shaman", "Shaman", [("elemental", "Elemental", "dps"), ("enhancement", "Enhancement", "dps"),
                          ("restoration", "Restoration", "healer")]),
    ("hunter", "Hunter", [("beast-mastery", "Beast Mastery", "dps"), ("marksmanship", "Marksmanship", "dps"),
                          ("survival", "Survival", "dps")]),
    ("paladin", "Paladin", [("protection", "Protection", "tank"), ("retribution", "Retribution", "dps"),
                            ("holy", "Holy", "healer")]),
    ("warrior", "Warrior", [("protection", "Protection", "tank"), ("arms", "Arms", "dps"),
                            ("fury", "Fury", "dps")]),
]

# Slots in paper-doll order; the raw files list them in this order too.
SLOTS = [
    ("head", "Head"), ("neck", "Neck"), ("shoulder", "Shoulder"), ("back", "Back"), ("chest", "Chest"),
    ("wrist", "Wrist"), ("hands", "Hands"), ("waist", "Waist"), ("legs", "Legs"), ("feet", "Feet"),
    ("finger1", "Finger"), ("finger2", "Finger"), ("trinket1", "Trinket"), ("trinket2", "Trinket"),
    ("mainhand", "Main hand"), ("offhand", "Off hand"), ("ranged", "Ranged / relic"),
]

# Filter chips, in display order. "unknown" has no chip: unknown sources always show
# (sorted as they are), the site's "Only seen in Forever" switch hides them with the rest.
TYPES = ["dungeon", "raid", "world", "quest", "crafted", "vendor", "reputation", "pvp"]

CONF = {"Seen in Forever": "seen", "Forever client": "client", "Classic data": "classic", "Clue": "clue"}

# Instances named in the sources ("Drops from X" with no "in <place>"). Raids get "raid".
DUNGEONS = {
    "Shadowfang Keep", "Blackfathom Deeps", "Stormwind Stockade", "Ruins of Lordaeron", "Gnomeregan",
    "Razorfen Kraul", "Scarlet Monastery", "City of Dalaran", "The Deadmines", "Wailing Caverns",
    "Ragefire Chasm", "Hall of Thanes", "Excavation Site: Wetlands", "Razorfen Downs", "Uldaman",
}
RAIDS = set()
# Creatures whose instance the source sentence leaves out (Classic data: Scarlet Monastery
# Graveyard rares, a Gnomeregan mob).
CREATURE_INSTANCE = {
    "Ironspine": "Scarlet Monastery",
    "Azshir the Sleepless": "Scarlet Monastery",
    "Scorn": "Scarlet Monastery",
    "Caverndeep Burrower": "Gnomeregan",
}


def parse_source(src):
    """-> dict(type, label, group, prof?, skill?, instance?, chance?, faction?)"""
    s = re.sub(r"\s*\((Forever client|Classic data|Seen in Forever|Clue, unconfirmed|Clue)\)\.?$", "", src.strip())
    s = s.rstrip(".").strip()
    out = {}
    faction = re.search(r" · (Horde|Alliance)$", s)
    if faction:
        out["faction"] = faction.group(1).lower()
        s = s[: faction.start()]

    m = re.match(r"Crafted: (\w+)(?: (\d+))?", s)
    if m:
        out.update(type="crafted", prof=m.group(1))
        if m.group(2):
            out["skill"] = int(m.group(2))
        out["label"] = "%s %s" % (m.group(1), m.group(2)) if m.group(2) else m.group(1)
        out["group"] = m.group(1)
        return out
    m = re.match(r"Sold by (.+?) in (.+?) \(.*?\) for (.+)$", s)
    if m:
        out.update(type="vendor", label="%s, %s (%s)" % (m.group(1), m.group(2), m.group(3)),
                   group="Vendor: %s" % m.group(2))
        return out
    m = re.match(r"Quest reward: (.+?)(?: \(a choice\))?(?:, level (\d+))?$", s)
    if m:
        out.update(type="quest", label="Quest: %s" % m.group(1) + (" (level %s)" % m.group(2) if m.group(2) else ""),
                   group="Quests")
        if m.group(2):
            out["qlevel"] = int(m.group(2))
        return out
    m = re.match(r"Needs (Friendly|Honored|Revered|Exalted) with (.+?)(?: \(.*)?$", s)
    if m:
        out.update(type="reputation", label="%s with %s" % (m.group(1), m.group(2)), group="Reputation: %s" % m.group(2))
        return out
    m = re.match(r"PvP rank (\d+) \((.+?) /", s)
    if m:
        out.update(type="pvp", label="PvP rank %s (%s)" % (m.group(1), m.group(2)), group="PvP")
        return out
    if s.startswith("World drop"):
        rng = re.search(r"level (\d+-\d+)", s)
        out.update(type="world", label="World drop" + (" (level %s mobs)" % rng.group(1) if rng else ""),
                   group="World drops")
        return out
    m = re.match(r"Inside (.+)$", s)
    if m:
        out.update(type="world", label="Inside %s" % m.group(1), group="Containers")
        return out
    m = re.match(r"Drops from trash in (.+?)(?:, ([\d.]+)%)?$", s)
    if m:
        out.update(type="raid" if m.group(1) in RAIDS else "dungeon", instance=m.group(1),
                   label="%s trash" % m.group(1), group=m.group(1))
        if m.group(2):
            out["chance"] = float(m.group(2))
        return out
    m = re.match(r"Drops from (.+?)(?: in (.+?))?(?:, ([\d.]+)%)?$", s)
    if m:
        who, where, chance = m.group(1), m.group(2), m.group(3)
        if chance:
            out["chance"] = float(chance)
        if not where and who in DUNGEONS | RAIDS:
            where, who = who, None
        if not where and who in CREATURE_INSTANCE:
            where = CREATURE_INSTANCE[who]
        if where:
            out.update(type="raid" if where in RAIDS else "dungeon", instance=where, group=where,
                       label=("%s, %s" % (where, who) if who else where) + (" (%s%%)" % chance if chance else ""))
        else:
            out.update(type="world", group="World drops", label="Drops from %s" % who
                       + (" (%s%%)" % chance if chance else ""))
            out["mob"] = who
        return out
    if "isn't known yet" in s:
        out.update(type="unknown", label="Source not known yet", group="Source not known yet")
        return out
    raise ValueError("unrecognised source: %r" % src)


def build():
    specs_out, classes_out, seen_files = {}, [], set()
    for ckey, cname, specs in CLASSES:
        cspecs = []
        for skey, sname, role in specs:
            path = os.path.join(RAW, "%s-%s.json" % (ckey, skey))
            seen_files.add(os.path.basename(path))
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            if len(raw["slots"]) != len(SLOTS):
                raise ValueError("%s: %d slots, expected %d" % (path, len(raw["slots"]), len(SLOTS)))
            slots = []
            for (slot_key, slot_label), rs in zip(SLOTS, raw["slots"]):
                want = slot_label.split(" /")[0]
                if not rs["slot"].startswith(want.split(" ")[0]):
                    raise ValueError("%s: slot %r where %r was expected" % (path, rs["slot"], slot_label))
                entry = {"slot": slot_key}
                b = rs.get("best")
                if b:
                    src = parse_source(b["src"])
                    best = {"id": int(b["id"]), "name": b["name"], "score": b["score"], "stats": b.get("stats", ""),
                            "conf": CONF.get(b.get("conf") or "", "unknown"), "ease": b.get("ease", "")}
                    best.update(src)
                    if b.get("horde"):
                        best["horde"] = b["horde"]
                    entry["best"] = best
                    nxt = []
                    for n in rs.get("next") or []:
                        item = {"id": int(n["id"]), "name": n["name"]}
                        if n.get("delta") is not None:
                            item["delta"] = n["delta"]
                        nxt.append(item)
                    entry["next"] = nxt
                else:
                    entry["note"] = rs.get("note") or "nothing at this level"
                slots.append(entry)
            spec_id = "%s/%s" % (ckey, skey)
            specs_out[spec_id] = {"class": ckey, "spec": skey, "name": sname, "role": role,
                                  "build": raw["build"], "weights": raw["weights"].rstrip("."),
                                  "url": "https://foreverdb.net/bis/%s/%s" % (ckey, skey), "slots": slots}
            cspecs.append(spec_id)
        classes_out.append({"key": ckey, "name": cname, "specs": cspecs})
    extra = {os.path.basename(p) for p in glob.glob(os.path.join(RAW, "*.json"))} - seen_files
    if extra:
        raise ValueError("raw files with no spec in CLASSES: %s" % sorted(extra))
    return {"updated": UPDATED, "level": LEVEL, "source": {"name": SOURCE_NAME, "url": SOURCE_URL},
            "slots": [{"key": k, "label": v} for k, v in SLOTS], "types": TYPES,
            "classes": classes_out, "specs": specs_out}


# ---------------------------------------------------------------------------
# Lua output
# ---------------------------------------------------------------------------

def lua_str(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def lua_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return lua_str(v)
    raise TypeError(v)


def lua_item(d, keys):
    parts = ["%s = %s" % (k, lua_val(d[k])) for k in keys if k in d]
    return "{ " + ", ".join(parts) + " }"


def wrap(prefix, parts, suffix, indent, width=120):
    """prefix + parts joined by ", " + suffix, broken into lines no wider than `width`
    (luacheck's max_line_length is 130)."""
    lines, cur = [], prefix
    for i, part in enumerate(parts):
        piece = part + ("," if i < len(parts) - 1 else "")
        if len(cur) + 1 + len(piece) > width and cur.strip():
            lines.append(cur.rstrip())
            cur = indent + piece
        else:
            cur = (cur + " " + piece) if not cur.endswith(("{", "(")) and cur.strip() else cur + piece
    lines.append(cur + suffix)
    return lines


BEST_KEYS = ["id", "name", "score", "stats", "conf", "ease", "type", "label", "group", "prof", "skill", "instance",
             "chance", "faction", "horde"]


def to_lua(data):
    out = [
        "-- BiZData.lua: Mr.BiZ best-in-slot data. GENERATED by bis/build_bis.py from bis/raw/*.json",
        "-- (ForeverDB's level %d BiS pages, %s). Never hand-edit: change the raw files or the" % (data["level"], data["updated"]),
        "-- script and run `python bis/build_bis.py` (the addon tests fail if this file is stale).",
        "",
        "local _, R2F = ...",
        "",
        "R2F.BiZData = {",
        "  updated = %s," % lua_str(data["updated"]),
        "  level = %d," % data["level"],
        "  source = %s," % lua_str(data["source"]["name"]),
        "  types = { %s }," % ", ".join(lua_str(t) for t in data["types"]),
        "  slots = {",
    ]
    for s in data["slots"]:
        out.append("    { key = %s, label = %s }," % (lua_str(s["key"]), lua_str(s["label"])))
    out.append("  },")
    out.append("  classes = {")
    for c in data["classes"]:
        out.append("    { key = %s, name = %s, specs = { %s } }," % (
            lua_str(c["key"]), lua_str(c["name"]), ", ".join(lua_str(s) for s in c["specs"])))
    out.append("  },")
    out.append("  specs = {")
    for sid, sp in data["specs"].items():
        out.append("    [%s] = {" % lua_str(sid))
        out.append("      class = %s, name = %s, role = %s, build = %s," % (
            lua_str(sp["class"]), lua_str(sp["name"]), lua_str(sp["role"]), lua_str(sp["build"])))
        # Long weight lines split into ".." pieces (luacheck's 130-column limit).
        w, pieces, cur = sp["weights"], [], ""
        for part in w.split(", "):
            nxt = (cur + ", " + part) if cur else part
            if len(nxt) > 90 and cur:
                pieces.append(cur + ", ")
                cur = part
            else:
                cur = nxt
        pieces.append(cur)
        out.append("      weights = %s," % " ..\n        ".join(lua_str(x) for x in pieces))
        out.append("      slots = {")
        for sl in sp["slots"]:
            if "best" in sl:
                b = sl["best"]
                out.append("        { slot = %s," % lua_str(sl["slot"]))
                out.extend(wrap("          best = {", ["%s = %s" % (k, lua_val(b[k])) for k in BEST_KEYS if k in b],
                                " },", "            "))
                out.append("          next = {")
                for n in sl["next"]:
                    out.append("            %s," % lua_item(n, ["id", "name", "delta"]))
                out.append("          },")
                out.append("        },")
            else:
                out.append("        { slot = %s, note = %s }," % (lua_str(sl["slot"]), lua_str(sl["note"])))
        out.append("      },")
        out.append("    },")
    out.append("  },")
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    data = build()
    site = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    lua = to_lua(data)
    if "--check" in sys.argv:
        stale = []
        for path, text in ((SITE_OUT, site), (LUA_OUT, lua)):
            if not os.path.exists(path) or open(path, encoding="utf-8").read() != text:
                stale.append(os.path.relpath(path, ROOT))
        if stale:
            print("stale: %s (run python bis/build_bis.py)" % ", ".join(stale))
            sys.exit(1)
        print("bis data up to date")
        return
    with open(SITE_OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(site)
    with open(LUA_OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(lua)
    n_items = sum(1 for sp in data["specs"].values() for sl in sp["slots"] if "best" in sl)
    print("wrote %s and %s: %d specs, %d slot picks" % (
        os.path.relpath(SITE_OUT, ROOT), os.path.relpath(LUA_OUT, ROOT), len(data["specs"]), n_items))


if __name__ == "__main__":
    main()
