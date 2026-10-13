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
SOURCES = os.path.join(HERE, "sources.json")
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
    "Fallen Champion": "Scarlet Monastery",
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
    m = re.match(r"Sold by (.+?) in (.+?)(?: \(.*?\))? for (.+)$", s)
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


# Where a rank 2-3 pick comes from: its own best-pick entry in any spec, else bis/sources.json
# (read from the item's ForeverDB page). Keys copied onto each next item:
NEXT_SRC_KEYS = ["type", "label", "group", "prof", "skill", "instance", "chance", "faction", "conf", "via"]


def source_of(src, conf_word=None):
    """Parsed source dict incl. conf, from a BiS-page source sentence."""
    out = parse_source(src)
    if conf_word is None:
        m = re.search(r"\((Forever client|Classic data|Seen in Forever|Clue)(?:, unconfirmed)?\)\.?$", src.strip())
        conf_word = m.group(1) if m else ""
    out["conf"] = CONF.get(conf_word or "", "unknown")
    return out


def source_index():
    idx = {}
    for path in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        with open(path, encoding="utf-8") as f:
            for rs in json.load(f)["slots"]:
                b = rs.get("best")
                if b and int(b["id"]) not in idx:
                    idx[int(b["id"])] = source_of(b["src"], b.get("conf"))
                    if idx[int(b["id"])]["type"] != "unknown":
                        idx[int(b["id"])]["via"] = SOURCE_NAME
    with open(SOURCES, encoding="utf-8") as f:
        for iid, it in json.load(f)["items"].items():
            src = source_of(it["src"])
            if it.get("via"):
                src["via"] = it["via"]   # the site we read it from, shown as a small credit
            idx.setdefault(int(iid), src)
    return idx


def build():
    specs_out, classes_out, seen_files = {}, [], set()
    sources = source_index()
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
                    if best["type"] != "unknown":
                        best["via"] = SOURCE_NAME
                    if b.get("horde"):
                        best["horde"] = b["horde"]
                    entry["best"] = best
                    nxt = []
                    for n in rs.get("next") or []:
                        item = {"id": int(n["id"]), "name": n["name"]}
                        if n.get("delta") is not None:
                            item["delta"] = n["delta"]
                        src = sources.get(item["id"])
                        if src is None:
                            raise ValueError("%s: no source for next pick %s %r: add it to bis/sources.json"
                                             % (path, item["id"], item["name"]))
                        item.update({k: src[k] for k in NEXT_SRC_KEYS if k in src})
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
    places = load_places()
    tag_places(specs_out, places)
    add_enchants(specs_out)
    quality = load_quality(specs_out)
    return {"updated": UPDATED, "level": LEVEL, "source": {"name": SOURCE_NAME, "url": SOURCE_URL},
            "slots": [{"key": k, "label": v} for k, v in SLOTS], "types": TYPES,
            "classes": classes_out, "specs": specs_out, "places": places, "quality": quality}


# ---------------------------------------------------------------------------
# Places (BiZNav): bis/places.json -> `place` on each row whose source has a known spot
# ---------------------------------------------------------------------------

PLACES_IN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "places.json")
PLACE_KEYS = ["zone", "mapHint", "x", "y", "label", "conf"]


def load_places():
    with open(PLACES_IN, encoding="utf-8") as f:
        places = json.load(f)["places"]
    for key, p in places.items():
        missing = [k for k in ("zone", "x", "y", "label", "conf") if k not in p]
        if missing or p["conf"] not in ("exact", "classic", "approx"):
            raise ValueError("places.json %r: missing %s or bad conf" % (key, missing))
        if not (0 <= p["x"] <= 100 and 0 <= p["y"] <= 100):
            raise ValueError("places.json %r: x / y must be map percent" % key)
    return places


def place_key(row):
    """The places.json key a source would use: instance, vendor name or reputation faction."""
    t = row.get("type")
    if t in ("dungeon", "raid") and row.get("instance"):
        return row["instance"]
    if t == "vendor" and row.get("label"):
        return row["label"].split(",")[0].strip()
    if t == "reputation" and row.get("group", "").startswith("Reputation: "):
        return row["group"][len("Reputation: "):]
    return None


def tag_places(specs, places):
    used = set()
    for sp in specs.values():
        for sl in sp["slots"]:
            for row in ([sl["best"]] if "best" in sl else []) + sl.get("next", []):
                key = place_key(row)
                if key in places:
                    row["place"] = key
                    used.add(key)
    unused = sorted(set(places) - used)
    if unused:
        raise ValueError("places.json entries no BiZ row uses: %s" % unused)


# ---------------------------------------------------------------------------
# Item quality (rarity colour) baked in from bis/quality.json, so names are coloured before the game /
# Wowhead answers. Owner decision 2026-10-13. Ids missing from the file are left out (live lookup then).
# ---------------------------------------------------------------------------

QUALITY_IN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quality.json")


def load_quality(specs):
    with open(QUALITY_IN, encoding="utf-8") as f:
        known = {int(k): v for k, v in json.load(f)["quality"].items()}
    ids = sorted({r["id"] for sp in specs.values() for sl in sp["slots"] if "best" in sl
                  for r in [sl["best"]] + sl.get("next", [])})
    missing = [i for i in ids if i not in known]
    if missing:
        print("note: no baked quality for %d items (refresh bis/quality.json): %s" % (len(missing), missing[:10]),
              file=sys.stderr)
    return {str(i): known[i] for i in ids if i in known}


# ---------------------------------------------------------------------------
# Enchants: professions.html's BiS enchant list (ForeverChanges' spec pages), per spec and slot
# ---------------------------------------------------------------------------

# ForeverChanges page (as professions.html names it) for each of our specs: always a PvE page. Feral uses the
# tank page (ForeverDB's Feral list is the bear tank), Fury the Arms page, Subtlety Combat, Discipline Holy
# (those three only have PvP pages or none).
ENCHANT_PAGE = {
    "priest/discipline": "Priest Holy", "priest/holy": "Priest Holy", "priest/shadow": "Priest Shadow PvE",
    "warlock/affliction": "Warlock PvE", "warlock/demonology": "Warlock PvE", "warlock/destruction": "Warlock PvE",
    "mage/arcane": "Mage Arcane PvE", "mage/fire": "Mage Fire PvE", "mage/frost": "Mage Frost PvE",
    "rogue/assassination": "Rogue Assassination PvE", "rogue/combat": "Rogue Combat PvE", "rogue/subtlety": "Rogue Combat PvE",
    "druid/feral": "Druid Tank", "druid/balance": "Druid Balance PvE", "druid/restoration": "Druid Restoration",
    "shaman/elemental": "Shaman Elemental PvE", "shaman/enhancement": "Shaman Enhancement PvE",
    "shaman/restoration": "Shaman Restoration",
    "hunter/beast-mastery": "Hunter PvE", "hunter/marksmanship": "Hunter PvE", "hunter/survival": "Hunter PvE",
    "paladin/protection": "Paladin Tank", "paladin/retribution": "Paladin Retribution PvE", "paladin/holy": "Paladin Holy PvE",
    "warrior/protection": "Warrior Tank", "warrior/arms": "Warrior Arms PvE", "warrior/fury": "Warrior Arms PvE",
}
# Enchant slot (professions.html) -> our gear slots.
ENCHANT_SLOTS = {
    "Neck": ["neck"], "Back": ["back"], "Chest": ["chest"], "Wrist": ["wrist"], "Hands": ["hands"], "Legs": ["legs"],
    "Feet": ["feet"], "Hands, Legs": ["hands", "legs"], "Shield": ["offhand"], "Weapon": ["mainhand"],
    "2H Weapon": ["mainhand"], "Ranged": ["ranged"],
}
ENCHANT_KEYS = ["name", "eff", "prof", "skill", "kind", "ids"]
ALT_KEYS = ["name", "eff", "prof", "skill", "ids"]


def load_enchants():
    import subprocess
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enchants_from_professions.js")
    out = subprocess.run(["node", script, os.path.join(ROOT, "professions.html")], capture_output=True, text=True,
                         check=True)
    return json.loads(out.stdout)


ENCHANT_IDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enchant_ids.json")


def load_enchant_ids():
    """name -> [enchantment ids] from bis/enchant_ids.json (bis/tools/wago_enchant_ids.py); {} when the file is absent."""
    try:
        with open(ENCHANT_IDS, encoding="utf-8") as f:
            return json.load(f)["ids"]
    except FileNotFoundError:
        print("note: bis/enchant_ids.json is missing, so Mr.BiZ cannot tell which enchant you wear "
              "(run bis/tools/wago_enchant_ids.py)", file=sys.stderr)
        return {}


def add_enchants(specs):
    data = load_enchants()
    ids = load_enchant_ids()
    pages = {lbl for e in data for lbl in e["specs"]}
    for sid, page in ENCHANT_PAGE.items():
        if sid not in specs:
            raise ValueError("ENCHANT_PAGE: no spec %r" % sid)
        if page not in pages:
            raise ValueError("ENCHANT_PAGE %r: professions.html has no page %r" % (sid, page))
    missing = sorted(set(specs) - set(ENCHANT_PAGE))
    if missing:
        raise ValueError("ENCHANT_PAGE has no page for %s" % missing)
    for e in data:
        if e["slot"] not in ENCHANT_SLOTS:
            raise ValueError("enchant %r: unknown slot %r (add it to ENCHANT_SLOTS)" % (e["name"], e["slot"]))
    for sid, sp in specs.items():
        page = ENCHANT_PAGE[sid]
        by_slot = {}
        for e in data:
            if page not in e["specs"]:
                continue
            row = {"name": e["name"], "eff": e["eff"], "prof": e["prof"], "skill": e["skill"]}
            if e["slot"] == "2H Weapon":
                row["kind"] = "2h"
            if e["name"] in ids:
                row["ids"] = ids[e["name"]]
            alts = []
            for a in e.get("alts", []):
                alt = {"name": a["name"], "eff": a["eff"], "prof": a["prof"], "skill": a["skill"]}
                if a["name"] in ids:
                    alt["ids"] = ids[a["name"]]
                alts.append(alt)
            if alts:
                row["alts"] = alts
            for key in ENCHANT_SLOTS[e["slot"]]:
                by_slot.setdefault(key, []).append(row)
        sp["enchants"] = by_slot
        sp["enchantPage"] = page


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


def lua_ids(ids):
    return "{ " + ", ".join(str(int(i)) for i in ids) + " }"


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
             "chance", "faction", "horde", "via", "place"]


NEXT_KEYS = ["id", "name", "delta"] + NEXT_SRC_KEYS + ["place"]


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
                    out.extend(wrap("            {", ["%s = %s" % (k, lua_val(n[k])) for k in NEXT_KEYS if k in n],
                                    " },", "              "))
                out.append("          },")
                out.append("        },")
            else:
                out.append("        { slot = %s, note = %s }," % (lua_str(sl["slot"]), lua_str(sl["note"])))
        out.append("      },")
        # BiS enchants per slot (professions.html, ForeverChanges' page named in enchantPage).
        out.append("      enchantPage = %s," % lua_str(sp["enchantPage"]))
        out.append("      enchants = {")
        for slot in [k for k, _ in SLOTS if k in sp["enchants"]]:
            rows = sp["enchants"][slot]
            out.append("        %s = {" % slot)
            for r in rows:
                parts = ["%s = %s" % (k, lua_ids(r[k]) if k == "ids" else lua_val(r[k])) for k in ENCHANT_KEYS if k in r]
                if not r.get("alts"):
                    out.extend(wrap("          {", parts, " },", "            "))
                    continue
                out.extend(wrap("          {", parts, ",", "            "))
                out.append("            alts = {")
                for alt in r["alts"]:
                    aparts = ["%s = %s" % (k, lua_ids(alt[k]) if k == "ids" else lua_val(alt[k]))
                              for k in ALT_KEYS if k in alt]
                    out.extend(wrap("              {", aparts, " },", "                "))
                out.append("            } },")
            out.append("        },")
        out.append("      },")
        out.append("    },")
    out.append("  },")
    # Item quality by id (bis/quality.json), 8 per line (luacheck: 130 columns).
    out.append("  quality = {")
    qs = sorted(data["quality"].items(), key=lambda kv: int(kv[0]))
    for i in range(0, len(qs), 8):
        out.append("    " + " ".join("[%s] = %d," % (k, v) for k, v in qs[i:i + 8]))
    out.append("  },")
    # BiZNav: where a source is (bis/places.json); rows point here with `place = "<key>"`.
    out.append("  places = {")
    for key in sorted(data["places"]):
        p = data["places"][key]
        out.extend(wrap("    [%s] = {" % lua_str(key), ["%s = %s" % (k, lua_val(p[k])) for k in PLACE_KEYS if k in p],
                        " },", "      "))
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
