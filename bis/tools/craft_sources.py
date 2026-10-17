"""Crafted items from the game's own tables (OWN_DATABASE_PLAN.md, M2): item id -> [{prof, rank, spell, reagents}].

    python bis/tools/craft_sources.py     # writes bis/own/cache/craft_sources.json and checks it against ForeverDB's "Crafted: <prof> <rank>"

SkillLineAbility says which skill line teaches a spell and at what skill (MinSkillLineRank), SpellEffect (Effect 24 = create item) says
which item the spell makes, SpellReagents lists the materials. Recipe acquisition (trainer / vendor / drop of the pattern) is the next step.
"""
import csv
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = sorted((ROOT / "bis" / "own" / "cache" / "db2").iterdir(), key=lambda p: int(p.name.rsplit(".", 1)[1]))[-1]
PROFS = {"Alchemy", "Blacksmithing", "Enchanting", "Engineering", "Leatherworking", "Tailoring", "Cooking", "First Aid", "Jewelcrafting"}


def rows(name):
    return list(csv.DictReader(open(D / (name + ".csv"), encoding="utf-8")))


def main():
    skill = {int(r["ID"]): r["DisplayName_lang"] for r in rows("SkillLine")}
    effects = defaultdict(list)
    for r in rows("SpellEffect"):
        if r["Effect"] == "24" and int(r["EffectItemType"]) > 0:
            effects[int(r["SpellID"])].append(int(r["EffectItemType"]))
    reagents = {}
    for r in rows("SpellReagents"):
        reagents[int(r["SpellID"])] = [(int(r["Reagent_%d" % k]), int(r["ReagentCount_%d" % k])) for k in range(8) if int(r["Reagent_%d" % k])]
    names = {int(r["ID"]): r["Name_lang"] for r in rows("SpellName")}
    out = defaultdict(list)
    for r in rows("SkillLineAbility"):
        prof = skill.get(int(r["SkillLine"]))
        sp = int(r["Spell"])
        if prof in PROFS and sp in effects:
            for item in effects[sp]:
                out[item].append({"prof": prof, "rank": int(r["MinSkillLineRank"]), "spell": sp, "name": names.get(sp),
                                  "reagents": reagents.get(sp, []), "hi": int(r["TrivialSkillLineRankHigh"]), "lo": int(r["TrivialSkillLineRankLow"]),
                                  "learn": int(r["AcquireMethod"])})
    (ROOT / "bis" / "own" / "cache" / "craft_sources.json").write_text(json.dumps({str(k): v for k, v in out.items()}, separators=(",", ":")))
    print("%d crafted items from %d recipes" % (len(out), sum(len(v) for v in out.values())))
    cnt, bad = Counter(), []
    for f in glob.glob(str(ROOT / "bis" / "raw" / "*.json")):
        for s in json.load(open(f))["slots"]:
            b = s.get("best")
            if not b:
                continue
            m = re.match(r"Crafted: (.+?) (\d+)", b.get("src") or "")
            if not m:
                continue
            recs = out.get(b["id"], [])
            ok = any(r["prof"] == m.group(1) and r["lo"] == int(m.group(2)) for r in recs)
            cnt["agrees" if ok else "differs"] += 1
            if not ok and len(bad) < 8:
                bad.append((b["id"], b["name"], b["src"], [(r["prof"], r["rank"], r["lo"], r["hi"]) for r in recs]))
    print("ForeverDB 'Crafted: <profession> <skill>' rows:", dict(cnt))
    for b in bad:
        print("  ", b)


if __name__ == "__main__":
    main()
