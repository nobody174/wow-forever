"""Fill bis/sources.json for the rank 2-3 picks that are not the best pick anywhere, from ForeverDB's item pages.

    python bis/tools/foreverdb_sources.py            # find the next picks with no source, read their item pages, add them to sources.json
    python bis/tools/foreverdb_sources.py --dry      # only say how many there are

Each page's description carries ForeverDB's sentence ("Where it comes from: Quest reward from X (level 15), a choice of rewards,
Alliance (seen in WoW Forever); Drops from Y ..."). The FIRST source is rewritten in the wording of the BiS pages, which
`build_bis.parse_source` reads: "Quest reward: X (a choice), level 15 · Alliance (Seen in Forever)". Wording this script does not know
stops it with the item named (never a guess). One request per second, pages cached in bis/own/cache/items/ (not in git).
"""
import glob
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "bis"))
import build_bis as bb  # noqa: E402

CACHE = ROOT / "bis" / "own" / "cache" / "items"
UA = {"User-Agent": "RoadToForever-data-check (https://github.com/nobody174/wow-forever)"}
LABEL = {"classic data": "Classic data", "forever client": "Forever client", "seen in wow forever": "Seen in Forever",
         "seen in forever": "Seen in Forever", "clue": "Clue", "clue, unconfirmed": "Clue"}


def missing_next_picks():
    idx = bb.source_index()
    out = {}
    for p in glob.glob(str(ROOT / "bis" / "raw" / "levels" / "*.json")):
        for runs in json.load(open(p, encoding="utf-8"))["slots"]:
            for r in runs:
                for n in r.get("next", []):
                    if n["id"] not in idx:
                        out[n["id"]] = n["name"]
    return out


def fetch(iid):
    f = CACHE / ("%d.html" % iid)
    if f.exists() and f.stat().st_size > 5000:
        return f.read_text(encoding="utf-8")
    for attempt in range(6):
        try:
            page = urllib.request.urlopen(urllib.request.Request("https://foreverdb.net/item/%d" % iid, headers=UA), timeout=40).read().decode("utf-8", "replace")
            break
        except Exception:      # 502 and friends: wait and try again
            time.sleep(10 * (attempt + 1))
    else:
        raise RuntimeError("giving up on item %d" % iid)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(page, encoding="utf-8")
    time.sleep(1.0)
    return page


def sentence(page):
    m = re.search(r'"description": "([^"]*)"', page)
    text = html.unescape(m.group(1)) if m else ""
    k = text.find("Where it comes from:")
    if k < 0:
        return None
    return text[k + len("Where it comes from:"):].strip().rstrip(".").strip()


def convert(first):
    """One ForeverDB source (no ';') -> the BiS-page wording."""
    s = first.strip()
    label = ""
    m = re.search(r" \(([^()]*)\)$", s)
    if m and m.group(1).lower() in LABEL:
        label = LABEL[m.group(1).lower()]
        s = s[:m.start()]
    s = re.sub(r" \(Classic drop rate\)$", "", s)          # "(70% (Classic drop rate) (seen in WoW Forever))"
    m2 = re.search(r" \(([^()]*)\)$", s)
    if not label and m2 and m2.group(1).lower() in LABEL:
        label = LABEL[m2.group(1).lower()]
        s = s[:m2.start()]
    s = s.strip()
    m = re.match(r"Quest reward from (.+?) \(level (\d+)\), a choice of rewards(?:, (Horde|Alliance))?$", s)
    if m:
        out = "Quest reward: %s (a choice), level %s" % (m.group(1), m.group(2)) + (" · " + m.group(3) if m.group(3) else "")
    elif re.match(r"Quest reward from (.+?) \(level (\d+)\)(?:, (Horde|Alliance))?$", s):
        m = re.match(r"Quest reward from (.+?) \(level (\d+)\)(?:, (Horde|Alliance))?$", s)
        out = "Quest reward: %s, level %s" % (m.group(1), m.group(2)) + (" · " + m.group(3) if m.group(3) else "")
    elif re.match(r"Quest reward from (.+?)(?:, (?:a choice of rewards, )?(Horde|Alliance))?$", s):
        m = re.match(r"Quest reward from (.+?)(?:, (?:a choice of rewards, )?(Horde|Alliance))?$", s)
        out = "Quest reward: %s" % m.group(1) + (" · " + m.group(2) if m.group(2) else "")
    elif re.match(r"Crafted with (\w+)$", s):
        out = "Crafted: " + re.match(r"Crafted with (\w+)$", s).group(1)
    elif s.startswith("Drops from "):
        out = re.sub(r" \((?:boss|rare|elite)\)", "", s)
    elif s.startswith("World drop"):
        r = re.search(r"level (\d+)\D+(\d+)", s)
        out = "World drop" + (" level %s-%s" % (r.group(1), r.group(2)) if r else "")
    elif s.startswith(("Inside ", "Found in ")):
        out = s
    elif re.match(r"Sold by (.+)$", s):
        out = s
    else:
        raise ValueError("unknown source wording: %r" % first)
    return out + (" (%s)" % label if label else "") + "."


def main():
    miss = missing_next_picks()
    print("%d next picks have no source yet" % len(miss))
    if "--dry" in sys.argv:
        return
    path = ROOT / "bis" / "sources.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    added = 0
    for n, (iid, name) in enumerate(sorted(miss.items()), 1):
        first = sentence(fetch(iid))
        if first is None or not first:
            src = "Where it comes from isn't known yet."
        else:
            try:
                src = convert(first.split("; ")[0])
            except ValueError as e:      # new wording: keep going, list it, and read the sentence as unknown for now
                print("  UNKNOWN WORDING for item %d: %s" % (iid, e), flush=True)
                src = "Where it comes from isn't known yet."
        bb.parse_source(src)       # must be readable by the build
        data["items"][str(iid)] = {"name": name, "src": src, "via": "ForeverDB"}
        added += 1
        if n % 100 == 0:
            print("  %d / %d" % (n, len(miss)), flush=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("added %d sources" % added)


if __name__ == "__main__":
    main()
