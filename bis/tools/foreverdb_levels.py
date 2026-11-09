"""Download ForeverDB's best-in-slot pages for every spec at every level (the "per my level" data of Mr.BiZ).

    python bis/tools/foreverdb_levels.py                 # all 27 specs, levels 10 to 60 (resumes: pages already in the cache are skipped)
    python bis/tools/foreverdb_levels.py --from 10 --to 60 druid-feral hunter-survival

Source: https://foreverdb.net/bis/<class>/<spec>?lvl=<level> (server-rendered, PvE; robots.txt allows it). One request per second with
a user agent that names this project, and a pause when the site answers 429 / 5xx. Pages are kept in bis/own/cache/levels/<spec>/<level>.html
(not in git); `python bis/tools/foreverdb_segments.py` turns them into bis/raw/levels/<spec>.json.
"""
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import foreverdb_check as chk  # noqa: E402

CACHE = chk.ROOT / "bis" / "own" / "cache" / "levels"


def fetch(url):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers=chk.UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(15 * (attempt + 1))
                continue
            raise
        except Exception:
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("giving up on " + url)


def main():
    args = sys.argv[1:]
    lo = int(args[args.index("--from") + 1]) if "--from" in args else 10
    hi = int(args[args.index("--to") + 1]) if "--to" in args else 60
    specs = [a for a in args if not a.startswith("--") and not a.isdigit()]
    wanted = specs or [stem for stem, _ in chk.spec_files()]
    done = new = 0
    for stem in wanted:
        d = CACHE / stem
        d.mkdir(parents=True, exist_ok=True)
        for lvl in range(lo, hi + 1):
            f = d / ("%d.html" % lvl)
            if f.exists() and f.stat().st_size > 20000:
                done += 1
                continue
            page = fetch(chk.url_for(stem) + "?lvl=%d" % lvl)
            if "Every slot" not in page or ("level %d (PvE)" % lvl) not in page:
                print("UNEXPECTED page for %s level %d (%d bytes)" % (stem, lvl, len(page)), flush=True)
                continue
            f.write_text(page, encoding="utf-8")
            new += 1
            time.sleep(1.0)
        print("%-24s ready" % stem, flush=True)
    print("done: %d new, %d already cached" % (new, done), flush=True)


if __name__ == "__main__":
    main()
