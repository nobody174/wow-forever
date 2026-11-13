#!/usr/bin/env python3
"""Pull WCLBox's open item data (https://wowforever.wclbox.com/api/open/v1) into a resumable local cache.

    python bis/tools/wclbox_pull.py --list-only      # phase 1: the whole item list (about 220 calls)
    python bis/tools/wclbox_pull.py                  # phase 1 if missing, then phase 2: detail of every weapon and armor
    python bis/tools/wclbox_pull.py --limit 50       # try phase 2 on 50 items first
    python bis/tools/wclbox_pull.py --min-quality 2  # skip grey and white gear in phase 2 (default 1: skip grey only)

Cache (gitignored): bis/own/cache/wclbox/meta.json, list.jsonl (one list item per line), detail.jsonl (one detail per line).
Safe to stop and restart at any time: ids already in detail.jsonl are skipped. Run it on the owner's PC (the cloud sandbox cannot
reach WCLBox).

Their rules (docs, "usage conventions", read 2026-11-13): 5 requests per second per IP with a burst of 20 (this script uses about 3 per
second), page the full data with limit=100, cache 5 minutes, credit the source on the page that shows the data. Part of
docs/wclbox-migration-plan.md, phase 1.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "bis" / "own" / "cache" / "wclbox"
UA = {"User-Agent": "RoadToForever-data-pull (https://github.com/nobody174/wow-forever)", "Accept": "application/json"}
GAP = 0.34            # seconds between requests, about 3 per second
GEAR = (2, 4)         # classId: weapon, armor
KEEP = ("id", "name", "nameEn", "quality", "itemLevel", "requiredLevel", "slot", "type", "classId", "status", "set",
        "classes", "formerName", "tooltipEn")


def get(base, path, tries=1):
    """GET path, stopping on 429 / 5xx / network errors (no retry loop; rerun to resume). Returns parsed JSON, or None on 404 / 400."""
    wait = 3.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(base + path, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode("utf-8"))
            time.sleep(GAP)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                time.sleep(GAP)
                return None
            if e.code not in (429, 500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        print("  retry %d after %.0fs: %s" % (attempt + 1, wait, path), file=sys.stderr)
        time.sleep(wait)
        wait = min(wait * 2, 120)
    raise IOError("giving up on " + path)


def read_jsonl(path):
    out = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def phase_list(base, meta):
    info = get(base, "")
    if not info:
        raise SystemExit("API info not answering")
    total, build = info["items"], info["foreverBuild"]
    print("WCLBox: %d items, client build %s (%s)" % (total, build, info.get("buildDate")))
    if meta.get("build") and meta["build"] != build:
        print("  note: the cached build was %s; the old cache is replaced" % meta["build"])
        for f in ("list.jsonl", "detail.jsonl"):
            if (CACHE / f).exists():
                (CACHE / f).unlink()
    meta.update({"build": build, "buildDate": info.get("buildDate"), "items": total})
    path = CACHE / "list.jsonl"
    have = read_jsonl(path)
    if len(have) >= total:
        print("list already complete (%d)" % len(have))
        return have
    have = []
    with path.open("w", encoding="utf-8") as f:
        offset = 0
        while offset < total:
            page = get(base, "/items?limit=100&offset=%d&sort=id&order=asc" % offset)
            if page is None or not page.get("items"):
                break
            for it in page["items"]:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
                have.append(it)
            offset += 100
            if offset % 2000 == 0:
                print("  list %d / %d" % (min(offset, total), total))
    (CACHE / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("list done: %d items" % len(have))
    return have


def phase_detail(base, items, min_quality, limit):
    path = CACHE / "detail.jsonl"
    done = {d["id"] for d in read_jsonl(path)}
    todo = [i["id"] for i in items if i.get("classId") in GEAR and (i.get("quality") or 0) >= min_quality and i["id"] not in done]
    print("detail: %d to fetch, %d already cached" % (len(todo), len(done)))
    if limit:
        todo = todo[:limit]
    started, n, fails, failed = time.time(), 0, 0, []
    with path.open("a", encoding="utf-8") as f:
        for iid in todo:
            try:
                d = get(base, "/items/%d" % iid)
                fails = 0
            except IOError as e:
                fails += 1
                failed.append(iid)
                print("  skipped %d (%s); a rerun fetches it" % (iid, e), file=sys.stderr)
                if fails >= 5:
                    raise SystemExit("5 failures in a row: stopping (progress is kept)")
                continue
            n += 1
            if d is not None:
                f.write(json.dumps({k: d.get(k) for k in KEEP}, ensure_ascii=False) + "\n")
                f.flush()
            if n % 200 == 0:
                rate = n / (time.time() - started)
                print("  detail %d / %d (%.1f per second, about %d min left)" % (n, len(todo), rate, (len(todo) - n) / rate / 60))
    print("detail done: %d fetched this run, %d skipped after an error" % (n, len(failed)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-only", action="store_true")
    ap.add_argument("--keep-cache", action="store_true",
                    help="finish the cached build even if WCLBox has a newer one (no list refetch, no cache wipe)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-quality", type=int, default=1)
    ap.add_argument("--base", default="https://wowforever.wclbox.com/api/open/v1", help="API base (tests point it at a local mock)")
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    mp = CACHE / "meta.json"
    meta = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
    if a.keep_cache:
        items = read_jsonl(CACHE / "list.jsonl")
        print("keeping the cached build %s (%d list items)" % (meta.get("build"), len(items)))
    else:
        items = phase_list(a.base, meta)
    if not a.list_only:
        phase_detail(a.base, items, a.min_quality, a.limit)


if __name__ == "__main__":
    main()
