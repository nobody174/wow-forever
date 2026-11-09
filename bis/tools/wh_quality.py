"""Add the item quality (rarity colour) of every Mr.BiZ item that bis/quality.json does not know yet.

    python bis/tools/wh_quality.py            # reads the ids from bis-data.json, asks Wowhead Forever's tooltip API, writes quality.json

Source: https://nether.wowhead.com/forever/tooltip/item/<id> (field `quality`), 0.45 s per request with a descriptive user agent; on 403 / 429 it
sleeps 5 minutes and retries. Safe to stop and restart: the file is saved every 100 items. Then run `python bis/build_bis.py`.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUALITY = ROOT / "bis" / "quality.json"
UA = {"User-Agent": "RoadToForever-data-check (https://github.com/nobody174/wow-forever)"}


def save(data):
    QUALITY.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main():
    data = json.loads(QUALITY.read_text(encoding="utf-8"))
    known = data["quality"]
    ids = sorted({r["id"] for r in json.loads((ROOT / "bis-data.json").read_text(encoding="utf-8"))["rows"]})
    todo = [i for i in ids if str(i) not in known]
    print("%d items without a baked quality" % len(todo), flush=True)
    waited = 0
    n = 0
    for iid in todo:
        while True:
            try:
                req = urllib.request.Request("https://nether.wowhead.com/forever/tooltip/item/%d" % iid, headers=UA)
                body = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                if e.code in (403, 429) and waited < 6:
                    waited += 1
                    time.sleep(300)
                    continue
                if e.code == 404:
                    body = {}
                    break
                raise
            except Exception:
                time.sleep(10)
        waited = 0
        if isinstance(body.get("quality"), int):
            known[str(iid)] = body["quality"]
        n += 1
        if n % 100 == 0:
            save(data)
            print("  %d / %d" % (n, len(todo)), flush=True)
        time.sleep(0.45)
    save(data)
    print("done: %d looked up" % n, flush=True)


if __name__ == "__main__":
    main()
