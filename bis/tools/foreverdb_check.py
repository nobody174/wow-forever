"""Read-only drift check: has ForeverDB's best-in-slot data moved since our `bis/raw/*.json` copy?

For every spec it reads https://foreverdb.net/bis/<class>/<spec> (the server-rendered "Every slot" list; robots.txt allows
it, /llms.txt invites assistants to read the pages), takes each slot's best pick, its score and the next two picks, and
compares them with `bis/raw/<class>-<spec>.json`. It also reports the data build and extraction date every page states.
It writes nothing in the repo. One request per second, one page per spec (27 requests).

    python bis/tools/foreverdb_check.py            # summary + the slots that changed
    python bis/tools/foreverdb_check.py --brief    # summary only
    python bis/tools/foreverdb_check.py --cache DIR  # keep the downloaded pages in DIR (re-run without new requests)

Exit code 1 when something changed (so a scheduled run can notice). See ADDON_PLAN.md 19.3 for where this fits.
"""
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "bis" / "raw"
UA = {"User-Agent": "RoadToForever-data-check (https://github.com/nobody174/wow-forever)"}
BASE = "https://foreverdb.net/bis/"

# raw file name -> ForeverDB URL path (Feral is "Feral (Bear)" in ours, ForeverDB calls it tank)
URL_FIX = {"druid-feral": "druid/feral"}


def spec_files():
    for p in sorted(RAW.glob("*.json")):
        yield p.stem, p


def url_for(stem):
    if stem in URL_FIX:
        return BASE + URL_FIX[stem]
    cls, spec = stem.split("-", 1)
    return BASE + cls + "/" + spec


def get(url, cache):
    if cache:
        f = Path(cache) / (re.sub(r"[^a-z0-9]+", "_", url.lower()) + ".html")
        if f.exists():
            return f.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        body = r.read().decode("utf-8", "replace")
    if cache:
        Path(cache).mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding="utf-8")
    time.sleep(1.0)
    return body


def parse(page):
    """-> (build, extracted, [ {slot, best: {id, name, score}, next: [{id, delta}]} ... ])"""
    m = re.search(r"build ([\d.]+), extracted <time datetime=\"([\d-]+)\"", page)
    build, extracted = (m.group(1), m.group(2)) if m else (None, None)
    i = page.find("Every slot")
    j = page.find("</ul>", i)
    slots = []
    for li in re.findall(r"<li>(.*?)</li>", page[i:j], re.S):
        li = html.unescape(li)
        slot = re.search(r"<b>(.*?)</b>", li)
        first = re.search(r'<a href="/item/(\d+)">(.*?)</a>(?: \(Horde:[^)]*\))?, score ([\d.]+)', li)
        nxt = []
        n = li.find("Next best:")
        if n >= 0:
            for iid, delta, same in re.findall(r'<a href="/item/(\d+)">.*?</a> \((?:([−-]?\d+)% vs best|(as good as the best))\)', li[n:]):
                nxt.append({"id": int(iid), "delta": int(delta.replace("−", "-")) if delta else 0})
        slots.append({"slot": slot.group(1) if slot else "?",
                      "best": {"id": int(first.group(1)), "name": first.group(2), "score": float(first.group(3))} if first else None,
                      "next": nxt})
    return build, extracted, slots


def main():
    brief = "--brief" in sys.argv
    cache = sys.argv[sys.argv.index("--cache") + 1] if "--cache" in sys.argv else None
    total = changed_best = changed_next = specs_changed = 0
    builds = set()
    ours_build = set()
    problems = []
    for stem, path in spec_files():
        old = json.loads(path.read_text(encoding="utf-8"))
        ours_build.add(old.get("build"))
        try:
            build, extracted, slots = parse(get(url_for(stem), cache))
        except Exception as e:  # network or layout trouble: say so, keep going
            problems.append("%s: %s" % (stem, e))
            continue
        builds.add((build, extracted))
        lines = []
        for k, (o, n) in enumerate(zip(old["slots"], slots)):
            total += 1
            ob = (o.get("best") or {}).get("id")
            nb = (n["best"] or {}).get("id")
            on = [x["id"] for x in o.get("next", [])]
            nn = [x["id"] for x in n["next"]]
            if ob != nb:
                changed_best += 1
                lines.append("  %-16s best %s -> %s (%s)" % (o["slot"], ob, nb, (n["best"] or {}).get("name")))
            elif on != nn:
                changed_next += 1
                lines.append("  %-16s next %s -> %s" % (o["slot"], on, nn))
        if len(old["slots"]) != len(slots):
            lines.append("  slot count %d -> %d" % (len(old["slots"]), len(slots)))
        if lines:
            specs_changed += 1
            if not brief:
                print(stem)
                print("\n".join(lines))
    print()
    print("ours: build %s" % ", ".join(sorted(str(b) for b in ours_build)))
    print("ForeverDB now: %s" % ", ".join("build %s extracted %s" % b for b in sorted(builds, key=str)))
    print("%d slots checked in %d specs: %d best picks changed, %d slots with only the next picks changed, %d specs differ"
          % (total, len(list(spec_files())), changed_best, changed_next, specs_changed))
    for p in problems:
        print("PROBLEM", p)
    return 1 if (specs_changed or problems) else 0


if __name__ == "__main__":
    sys.exit(main())
