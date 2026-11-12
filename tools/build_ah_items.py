#!/usr/bin/env python3
"""Builds ah-items.json, the name -> item id index behind auction-house.html. GENERATED: never hand-edit.

AHledger's API only takes item ids, so the page needs its own list of names to search. Sources, all already in the repo:
  bis/items.json            every Forever armor and weapon (game DB + tooltips)
  professions.html (MATS)   enchanting / leatherworking materials
  launch-plan-weapons.json  quest reward weapons
  crafters.json             recipe items (k "i") of the imported crafters
Output: {"build": ..., "items": [[id, "name", quality], ...]} sorted by id.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    return json.load(open(os.path.join(ROOT, name), encoding="utf-8"))


def main():
    items = {}

    def add(i, n, q):
        if isinstance(i, int) and n and i not in items:
            items[i] = [i, n, q if isinstance(q, int) else 1]

    bis = load("bis/items.json")
    for it in bis["items"]:
        add(it["id"], it.get("n"), it.get("q"))
    for it in load("launch-plan-weapons.json").get("items", []):
        add(it[0], it[1], it[6] if len(it) > 6 else None)
    for ch in load("crafters.json").get("chars", []):
        for pf in ch.get("profs", []):
            for r in pf.get("recipes", []):
                if r.get("k") == "i":
                    add(r.get("id"), r.get("n"), None)
    page = open(os.path.join(ROOT, "professions.html"), encoding="utf-8").read()
    for _code, name, item in re.findall(r'\["(\w+)", "([^"]*)", "\w+", (?:null|\d+), (\d+)\]', page):
        add(int(item), name, 1)
    out = {"build": bis.get("build"), "items": [items[k] for k in sorted(items)]}
    with open(os.path.join(ROOT, "ah-items.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote ah-items.json: %d items" % len(out["items"]))


if __name__ == "__main__":
    main()
