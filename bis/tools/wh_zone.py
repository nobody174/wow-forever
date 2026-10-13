"""Fetch a Wowhead Forever zone page and print what its map lists (name, category, coords).
usage: python whzone.py "<zone name>" [filter words...]"""
import json, re, subprocess, sys, urllib.parse

UA = "Mozilla/5.0"

def curl(url):
    r = subprocess.run(["curl", "-s", "-L", "-m", "40", "-A", UA, url], capture_output=True)
    return r.stdout.decode("utf-8", "replace")

def zone_id(name):
    d = json.loads(curl("https://www.wowhead.com/forever/search/suggestions-template?q=" + urllib.parse.quote(name)))
    for r in d.get("results", []):
        if r.get("type") == 7 and r["name"].lower() == name.lower():
            return r["id"]
    for r in d.get("results", []):
        if r.get("type") == 7:
            return r["id"]

def show_on_map(html):
    i = html.find("new ShowOnMap(")
    if i < 0:
        return {}
    j = i + len("new ShowOnMap(")
    depth = 0
    for k in range(j, len(html)):
        c = html[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[j:k + 1])
    return {}

if __name__ == "__main__":
    name = sys.argv[1]
    words = [w.lower() for w in sys.argv[2:]]
    zid = zone_id(name)
    print("zone", name, "->", zid)
    data = show_on_map(curl("https://www.wowhead.com/forever/zone=%s" % zid))
    for cat, items in data.items():
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            label = it.get("name") or "?"
            desc = it.get("description") or ""
            txt = (label + " " + desc + " " + cat).lower()
            if words and not any(w in txt for w in words):
                continue
            print("%-14s %-34s %-26s %s" % (cat, label[:34], desc[:26], it.get("coords")))
