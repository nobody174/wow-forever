"""Turn the downloaded per-level ForeverDB pages (foreverdb_levels.py) into bis/raw/levels/<spec>.json.

    python bis/tools/foreverdb_segments.py [spec ...]

For every slot the file keeps one entry per RUN of levels with the same pick (best item, score, stats, source, next picks):
    {"build": "1.60.1.70790",
     "weights": [{"from": 10, "w": "1.2 hit, ..."}, ...],
     "slots": [ [ {"from": 10, "slot": "Head", "best": {...}, "next": [...]} , {"from": 25, ...} ], ... 17 slots ... ]}
`from` is the first level the entry applies to; it holds up to the next entry's `from` (the last one up to level 60).
Pages whose wording the parser does not know stop that spec with the slot named (never a guess).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import foreverdb_check as chk  # noqa: E402
import foreverdb_fetch as fetch  # noqa: E402

CACHE = chk.ROOT / "bis" / "own" / "cache" / "levels"
OUT = chk.ROOT / "bis" / "raw" / "levels"
LO, HI = 10, 60


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")] or sorted(p.name for p in CACHE.iterdir() if p.is_dir())
    problems = 0
    for stem in wanted:
        pages = {}
        for lvl in range(LO, HI + 1):
            f = CACHE / stem / ("%d.html" % lvl)
            if not f.exists():
                print("%s: level %d is not downloaded yet" % (stem, lvl))
                problems += 1
                break
            try:
                pages[lvl] = fetch.parse_page(f.read_text(encoding="utf-8"))
            except fetch.Unknown as e:
                print("PROBLEM %s level %d: %s" % (stem, lvl, e))
                problems += 1
                break
        else:
            n_slots = {len(p["slots"]) for p in pages.values()}
            if n_slots != {17}:
                print("PROBLEM %s: slot counts %s" % (stem, sorted(n_slots)))
                problems += 1
                continue
            builds = {p["build"] for p in pages.values()}
            weights, slots = [], [[] for _ in range(17)]
            for lvl in range(LO, HI + 1):
                p = pages[lvl]
                if not weights or weights[-1]["w"] != p["weights"]:
                    weights.append({"from": lvl, "w": p["weights"]})
                for i, entry in enumerate(p["slots"]):
                    runs = slots[i]
                    if not runs or {k: v for k, v in runs[-1].items() if k != "from"} != entry:
                        runs.append(dict({"from": lvl}, **entry))
            data = {"build": sorted(builds)[-1], "weights": weights, "slots": slots}
            (OUT / (stem + ".json")).write_text(fetch.dump(data), encoding="utf-8")
            print("%-24s %3d runs in 17 slots, weights changed %d time(s), build %s" % (
                stem, sum(len(r) for r in slots), len(weights) - 1, ",".join(sorted(builds))))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
