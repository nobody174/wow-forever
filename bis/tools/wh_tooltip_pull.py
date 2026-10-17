"""Pull Wowhead Forever's item tooltips for a list of item ids into a resumable cache (bis/own/cache/tooltips.jsonl, one JSON object per line).

    python bis/tools/wh_tooltip_pull.py ids.txt        # one id per line; ids already in the cache are skipped
    python bis/tools/wh_tooltip_pull.py ids.txt --limit 200

Used for the items whose stats are not in the client's static files (OWN_DATABASE_PLAN.md 3.2). Politeness: the tooltip API
(`nether.wowhead.com/forever/tooltip/item/<id>`) at 0.45 s per request, a descriptive user agent; on HTTP 403 or 429 it sleeps
5 minutes and tries again (up to 6 times in a row, then stops: re-run later). Safe to stop and restart at any time.
"""
import json
import sys
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "bis" / "own" / "cache" / "tooltips.jsonl"
LOCK = CACHE.with_suffix(".lock")
UA = {"User-Agent": "RoadToForever-data-check (https://github.com/nobody174/wow-forever)"}
DELAY = 0.45


def cached_ids():
    ids = set()
    if CACHE.exists():
        with open(CACHE, encoding="utf-8") as f:
            for line in f:
                try:
                    ids.add(json.loads(line)["id"])
                except Exception:
                    pass            # a half-written last line after a hard stop
    return ids


def fetch(i):
    url = "https://nether.wowhead.com/forever/tooltip/item/%d" % i
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    if limit is not None and str(limit) in args:
        args.remove(str(limit))
    ids = [int(x) for x in Path(args[0]).read_text().split()]
    have = cached_ids()
    todo = [i for i in ids if i not in have]
    if limit:
        todo = todo[:limit]
    print("%d ids in the list, %d cached, %d to fetch" % (len(ids), len(have), len(todo)), flush=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists() and "--force" not in sys.argv:
        print("another pull seems to be running (%s). If it is not, delete that file or add --force." % LOCK.name)
        return 2
    LOCK.write_text(str(os.getpid()))
    done = fails = 0
    with open(CACHE, "a", encoding="utf-8") as out:
        for n, i in enumerate(todo, 1):
            for attempt in range(6):
                try:
                    j = fetch(i)
                    out.write(json.dumps({"id": i, "j": j}, ensure_ascii=False, separators=(",", ":")) + "\n")
                    done += 1
                    break
                except urllib.error.HTTPError as e:
                    if e.code in (403, 429):
                        print("  HTTP %d at id %d: sleeping 5 minutes (try %d of 6)" % (e.code, i, attempt + 1), flush=True)
                        out.flush()
                        time.sleep(300)
                        continue
                    out.write(json.dumps({"id": i, "error": e.code}) + "\n")
                    fails += 1
                    break
                except Exception as e:
                    out.write(json.dumps({"id": i, "error": str(e)[:80]}) + "\n")
                    fails += 1
                    break
            else:
                print("stopped: still blocked after 6 tries; re-run later", flush=True)
                LOCK.unlink()
                return 1
            if n % 250 == 0:
                out.flush()
                print("  %d / %d fetched (%d errors)" % (n, len(todo), fails), flush=True)
            time.sleep(DELAY)
    LOCK.unlink()
    print("done: %d fetched, %d errors" % (done, fails), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
