#!/usr/bin/env python3
"""Builds ah-items.json, the name -> item id index behind auction-house.html. GENERATED: never hand-edit.

AHledger's API only takes item ids, so the page needs its own list of names to search. It is only the fallback for when WCLBox
cannot be reached. Source: the full WCLBox item list (bis/own/cache/wclbox/list.jsonl, filled by bis/tools/wclbox_pull.py; every
Forever item, English names). If that cache is missing the existing ah-items.json is left untouched (nothing is rebuilt from the
narrow repo sources any more). Item names and rarity: 新手盒子·魔兽世界无限数据库 (WCLBox).
Output: {"build": ..., "items": [[id, "name", quality], ...]} sorted by id.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    return json.load(open(os.path.join(ROOT, name), encoding="utf-8"))


def main():
    src = os.path.join(ROOT, "bis", "own", "cache", "wclbox", "list.jsonl")
    meta = os.path.join(ROOT, "bis", "own", "cache", "wclbox", "meta.json")
    if not os.path.exists(src):
        print("ah-items.json: no WCLBox cache (bis/own/cache/wclbox/list.jsonl), left untouched")
        return
    items = {}
    for line in open(src, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        name = d.get("nameEn") or d.get("name")
        if isinstance(d.get("id"), int) and name:
            items[d["id"]] = [d["id"], name, d["quality"] if isinstance(d.get("quality"), int) else 1]
    build = json.load(open(meta, encoding="utf-8")).get("build") if os.path.exists(meta) else None
    out = {"build": build, "items": [items[k] for k in sorted(items)]}
    with open(os.path.join(ROOT, "ah-items.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote ah-items.json: %d items (WCLBox build %s)" % (len(out["items"]), build))


if __name__ == "__main__":
    main()
