"""One command to rebuild every item-source table and print how many of Mr.BiZ's picks have a source (OWN_DATABASE_PLAN.md, M2).

    python bis/tools/refresh_sources.py            # DB2 tables, crafting, AtlasLoot import, recorder merge, coverage report
    python bis/tools/refresh_sources.py --scan     # also: which installed addons carry Forever item ids, and under which licence

Run it after a new beta build, after updating AtlasLoot Continued, and whenever recorder files arrive (put them next to this one's
arguments:  --recorded file1.lua file2.lua). The Classic dump (classic_sources.py) is only rebuilt with --classic because it is slow.
"""
import glob
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / "bis" / "own" / "cache"
ADDONS = Path("D:/World of Warcraft/_classic_beta_/Interface/AddOns")


def run(script, *args):
    print("\n$ %s %s" % (script, " ".join(args)))
    r = subprocess.run([sys.executable, str(HERE / script), *args], cwd=str(ROOT))
    if r.returncode:
        print("  (exit %d)" % r.returncode)


def scan_addons():
    print("\ninstalled addons that carry Forever item ids (>= 200000) in Lua data:")
    for folder in sorted(p for p in ADDONS.iterdir() if p.is_dir()):
        hits = 0
        for f in folder.rglob("*.lua"):
            try:
                hits += len(re.findall(r"\b2[0-9]{5}\b", f.read_text(encoding="utf-8", errors="replace")[:3_000_000]))
            except OSError:
                pass
        if hits > 50:
            lic = "?"
            for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
                p = folder / name
                if p.exists():
                    lic = p.read_text(encoding="utf-8", errors="replace")[:120].strip().splitlines()[0]
                    break
            toc = next(iter(folder.glob("*.toc")), None)
            if lic == "?" and toc:
                m = re.search(r"## X-License: (.*)", toc.read_text(encoding="utf-8", errors="replace"))
                lic = m.group(1) if m else "no licence file"
            print("  %-40s %6d ids  licence: %s" % (folder.name, hits, lic))


def coverage():
    def load(name, key=None):
        p = CACHE / name
        if not p.exists():
            return {}
        d = json.load(open(p, encoding="utf-8"))
        return d[key] if key else d

    sets = [("classic", load("classic_sources.json")), ("craft", load("craft_sources.json")),
            ("atlasloot", load("atlasloot_sources.json", "items"))]
    rec = load("../recorded.json")
    recorded = set()
    for kind in ("drops", "objects"):
        for v in (rec.get(kind) or {}).values():
            recorded.update(v.get("i", {}))
    for v in (rec.get("vendors") or {}).values():
        recorded.update(v.get("i", {}))
    for v in (rec.get("quests") or {}).values():
        for key in ("c", "r"):
            ids = v.get(key) or []
            recorded.update(str(i) for i in (ids.values() if isinstance(ids, dict) else ids))
    sets.append(("recorded", {k: 1 for k in recorded}))
    picks = {}
    for f in glob.glob(str(ROOT / "bis" / "raw" / "*.json")):
        for s in json.load(open(f))["slots"]:
            if s.get("best"):
                picks[s["best"]["id"]] = s["best"]
    cnt, none = Counter(), []
    for i, b in picks.items():
        k = "+".join(n for n, d in sets if str(i) in d)
        cnt[k or "none"] += 1
        if not k:
            none.append("%s %s (%s)" % (i, b["name"], b.get("src")))
    print("\nbest picks: %d, with a source: %d, without: %d" % (len(picks), len(picks) - len(none), len(none)))
    print("  by origin:", dict(cnt))
    for n in none:
        print("   -", n)


def main():
    if "--classic" in sys.argv:
        run("classic_sources.py")
    run("db2_pull.py")
    run("craft_sources.py")
    run("atlasloot_import.py")
    files = []
    if "--recorded" in sys.argv:
        files = sys.argv[sys.argv.index("--recorded") + 1:]
    run("recorder_import.py", *files)
    coverage()
    if "--scan" in sys.argv:
        scan_addons()


if __name__ == "__main__":
    main()
