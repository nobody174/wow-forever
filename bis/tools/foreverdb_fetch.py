"""Rewrite `bis/raw/<class>-<spec>.json` from ForeverDB's server-rendered best-in-slot pages (ADDON_PLAN 19.3, step 1).

    python bis/tools/foreverdb_fetch.py                      # fetch all 27 specs into bis/own/cache/fetched/ and compare with raw/
    python bis/tools/foreverdb_fetch.py priest-shadow ...    # only these specs
    python bis/tools/foreverdb_fetch.py --write              # also replace bis/raw/ (git is the undo)
    python bis/tools/foreverdb_fetch.py --cache DIR          # keep / reuse the downloaded pages (no new requests)

It reads https://foreverdb.net/bis/<class>/<spec> (robots.txt allows it; one request per second, a user agent that names this
project). The page's "Every slot" list is turned into the same shape the hand-made files have: per slot `best` {id, name, score,
stats, src, conf, ease, horde?} and `next` [{id, delta}], or `best: null` + `note`; plus `build` and `weights`.
Wording the parser does not know stops the run with the slot named (never a guess). Afterwards run `python bis/build_bis.py`
(an unknown source sentence there stops the build too), then the addon tests.
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import foreverdb_check as chk  # noqa: E402

ROOT = chk.ROOT
RAW = chk.RAW
OUT_DIR = ROOT / "bis" / "own" / "cache" / "fetched"

SOURCE_START = ("Drops from", "Crafted:", "Quest reward", "Sold by", "World drop", "Inside ", "Needs ", "PvP rank",
                "Where it comes from isn't known yet", "Reward from", "Looted", "Fished", "Mined", "Skinned", "Gathered")
LABELS = ("Classic data", "Forever client", "Seen in Forever", "Clue")
EASE = ("Easy", "Some effort", "Hard", "Not known")


class Unknown(Exception):
    pass


def plain(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def parse_weights(page):
    m = re.search(r"<h2>Stat weights \(PvE\)</h2><p>(.*?)</p>", page, re.S)
    return plain(m.group(1)).rstrip(".") if m else None


def parse_slot(li):
    li = html.unescape(li)
    slot = re.search(r"<b>(.*?)</b>", li).group(1)
    first = re.search(r'<a href="/item/(\d+)">(.*?)</a>(?: \(Horde: ([^)]*)\))?, score ([\d.]+): ', li)
    if not first:
        return {"slot": slot, "best": None, "next": [], "note": plain(li.split("</b>:", 1)[1])}
    iid, name, horde, score = int(first.group(1)), first.group(2), first.group(3), float(first.group(4))
    rest = li[first.end():]
    # "Next best:" belongs to the next picks; the enchant text after it is not ours
    nb = rest.find("Next best:")
    head, tail = (rest[:nb], rest[nb:]) if nb >= 0 else (rest, "")
    text = plain(head)
    # stats end where the source sentence starts
    cut = None
    for p in SOURCE_START:
        k = text.find(". " + p)
        if k >= 0 and (cut is None or k < cut):
            cut = k
    if cut is None:
        raise Unknown("no source sentence found in: %r" % text[:160])
    stats = text[:cut]
    stats = re.sub(r", set bonus share: [^,]*(?:, [+][^,]*)*$", "", stats)
    after = text[cut + 2:]
    # the source sentence runs to the first " (Label" ...); the ease comes right after as "<Ease>: ..."
    ease = None
    for e in EASE:
        k = after.find(". " + e + ":")
        if k >= 0:
            ease = e
            sent = after[:k]
            break
    if ease is None:
        raise Unknown("no ease word in: %r" % after[:160])
    conf = None
    src = sent
    m = re.search(r" \((%s)(?:[,:][^)]*)?\)" % "|".join(LABELS), sent)
    if m:
        conf = m.group(1)
        src = sent[:m.start()]
    elif sent.startswith("PvP rank"):
        src = sent.split(" (Blizzard confirmed", 1)[0]
    elif sent.startswith("Where it comes from isn't known yet"):
        src = "Where it comes from isn't known yet"
    else:
        raise Unknown("no source label in: %r" % sent[:160])
    src = src.rstrip(". ")
    nxt = [{"id": int(i), "name": html.unescape(nm), "delta": int(d.replace("−", "-")) if d else 0}
           for i, nm, d, _ in re.findall(r'<a href="/item/(\d+)">(.*?)</a> \((?:([−-]?\d+)% vs best|(as good as the best))\)', tail)]
    best = {"id": iid, "name": html.unescape(name), "score": int(score) if score == int(score) else score,
            "stats": stats, "src": src, "conf": conf, "ease": ease}
    if horde:
        best["horde"] = horde
    return {"slot": slot, "best": best, "next": nxt}


def parse_page(page):
    m = re.search(r"build ([\d.]+), extracted", page)
    i = page.find("Every slot")
    j = page.find("</ul>", i)
    slots = [parse_slot(li) for li in re.findall(r"<li>(.*?)</li>", page[i:j], re.S)]
    return {"build": m.group(1) if m else None, "weights": parse_weights(page), "slots": slots}


def dump(data):
    """One compact line, the way the hand-made files are written (small git diffs)."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def compare(old, new):
    """Differences that matter: slot by slot, field by field."""
    out = []
    for o, n in zip(old["slots"], new["slots"]):
        if (o.get("best") or {}).get("id") != (n.get("best") or {}).get("id"):
            out.append("%s: best pick changed" % o["slot"])
            continue
        ob, nb = o.get("best") or {}, n.get("best") or {}
        for k in ("score", "stats", "src", "conf", "ease", "horde"):
            if ob.get(k) != nb.get(k):
                out.append("%s: %s %r -> %r" % (o["slot"], k, ob.get(k), nb.get(k)))
        if [x["id"] for x in o.get("next", [])] != [x["id"] for x in n["next"]]:
            out.append("%s: next picks changed" % o["slot"])
        elif [x["delta"] for x in o.get("next", [])] != [x["delta"] for x in n["next"]]:
            out.append("%s: next picks' gap changed" % o["slot"])
    if old.get("weights") != new.get("weights"):
        out.append("weights %r -> %r" % (old.get("weights"), new.get("weights")))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cache = sys.argv[sys.argv.index("--cache") + 1] if "--cache" in sys.argv else None
    if cache and cache in args:
        args.remove(cache)
    write = "--write" in sys.argv
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wanted = args or [stem for stem, _ in chk.spec_files()]
    problems = []
    total = 0
    for stem in wanted:
        path = RAW / (stem + ".json")
        old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        try:
            new = parse_page(chk.get(chk.url_for(stem), cache))
        except Unknown as e:
            problems.append("%s: %s" % (stem, e))
            continue
        except Exception as e:
            problems.append("%s: %s" % (stem, e))
            continue
        (OUT_DIR / (stem + ".json")).write_text(dump(new), encoding="utf-8")
        diff = compare(old, new) if old else ["(new file)"]
        total += len(diff)
        print("%-24s %2d slots, %d differences" % (stem, len(new["slots"]), len(diff)))
        for d in diff[:8]:
            print("      " + d)
        if write:
            path.write_text(dump(new), encoding="utf-8")
    for p in problems:
        print("PROBLEM", p)
    print("%d differences in total%s" % (total, " (raw/ rewritten)" if write else " (nothing written to raw/; --write does)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
