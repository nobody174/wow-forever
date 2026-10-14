"""Wowhead Forever item tooltips, cached on disk (bis/own/cache/tooltips.json, not in git).

    from tooltips import get_many
    data = get_many([id, ...])   # {id: {"name", "quality", "tooltip"}}   (tooltip = Wowhead's HTML)

The tooltip API (https://nether.wowhead.com/forever/tooltip/item/<id>) is polite-paced here: a few requests at a time with a short pause,
and a back-off when the server answers 403 / 429. Run it by hand when the beta data changes; the cache makes a re-run cheap.
"""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache", "tooltips.json")
URL = "https://nether.wowhead.com/forever/tooltip/item/%d"
WORKERS = 4
PAUSE = 0.25


def load_cache():
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as fh:
            return {int(k): v for k, v in json.load(fh).items()}
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({str(k): v for k, v in cache.items()}, fh, ensure_ascii=False)
    os.replace(tmp, CACHE)


def fetch(item_id):
    """One tooltip; None when the item does not exist (the API answers an error object). Backs off on throttling."""
    for attempt in range(6):
        r = subprocess.run(["curl", "-s", "-m", "30", "-w", "\n%{http_code}", URL % item_id], capture_output=True)
        body, _, code = r.stdout.decode("utf-8", "replace").rpartition("\n")
        if code in ("403", "429", "503"):
            time.sleep(5 * (attempt + 1))
            continue
        if code != "200":
            return None
        try:
            d = json.loads(body)
        except ValueError:
            return None
        if not isinstance(d, dict) or "tooltip" not in d:
            return None
        return {"name": d.get("name"), "quality": d.get("quality"), "tooltip": d["tooltip"]}
    raise RuntimeError("throttled on item %d, try again later" % item_id)


def get_many(ids, quiet=False):
    cache = load_cache()
    todo = [i for i in dict.fromkeys(ids) if i not in cache]
    done = 0

    def work(i):
        time.sleep(PAUSE)
        return i, fetch(i)

    try:
        with ThreadPoolExecutor(WORKERS) as ex:
            for i, d in ex.map(work, todo):
                cache[i] = d            # None = no such item (kept, so it is not asked again)
                done += 1
                if done % 100 == 0:
                    save_cache(cache)
                    if not quiet:
                        print("  %d / %d tooltips" % (done, len(todo)), file=sys.stderr)
    finally:
        save_cache(cache)
    return {i: cache[i] for i in ids if cache.get(i)}
