"""Download the game's own item tables (DB2) for one Forever build as CSV, into bis/own/cache/db2/<build>/ (gitignored).

    python bis/tools/db2_pull.py [build]        # default: the newest build wago.tools lists for 1.60.1.*
    python bis/tools/db2_pull.py --list         # the builds wago.tools knows

Source: https://wago.tools/db2/<Table>/csv?build=<build> (public, no key). Part of bis/OWN_DATABASE_PLAN.md, milestone M0.
Existing files are kept (delete the folder to refresh). A table wago does not have is reported and skipped.
"""
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "bis" / "own" / "cache" / "db2"
UA = {"User-Agent": "Mozilla/5.0 (RoadToForever data pull; https://github.com/nobody174/wow-forever)"}

TABLES = [
    "Item", "ItemSparse", "ItemSearchName",
    "RandPropPoints",
    "ItemArmorQuality", "ItemArmorTotal", "ItemArmorShield",
    "ItemDamageOneHand", "ItemDamageOneHandCaster", "ItemDamageTwoHand", "ItemDamageTwoHandCaster",
    "ItemDamageAmmo", "ItemDamageThrown", "ItemDamageWand",
    "ItemEffect", "ItemXItemEffect",
    "ItemSet", "ItemSetSpell",
    # crafting (M2): which spell makes which item, with which reagents, at what skill
    "SkillLine", "SkillLineAbility", "SpellName", "SpellEffect", "SpellReagents", "Map", "Faction",
]


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def builds():
    page = get("https://wago.tools/builds")
    return sorted(set(re.findall(r"1\.60\.1\.\d+", page)), key=lambda b: int(b.rsplit(".", 1)[1]))


def main():
    if "--list" in sys.argv:
        print(", ".join(builds()))
        return 0
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    build = args[0] if args else builds()[-1]
    out = CACHE / build
    out.mkdir(parents=True, exist_ok=True)
    print("build", build, "->", out)
    for t in TABLES:
        f = out / (t + ".csv")
        if f.exists() and f.stat().st_size > 0:
            print("  %-26s cached (%d KB)" % (t, f.stat().st_size // 1024))
            continue
        try:
            body = get("https://wago.tools/db2/%s/csv?build=%s" % (t, build), binary=True)
        except Exception as e:
            print("  %-26s FAILED: %s" % (t, e))
            continue
        first = body[:8000].replace(b"\xef\xbb\xbf", b"").splitlines()[0].strip().split(b",")
        if b"ID" not in first:                  # a table's header row has an ID column (not always the first)
            print("  %-26s not a table (first bytes %r)" % (t, body[:30]))
            continue
        f.write_bytes(body)
        print("  %-26s %d KB" % (t, len(body) // 1024))
        time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
