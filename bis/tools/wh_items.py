"""List quest-reward weapons from Wowhead Forever's item list pages.
usage: python whitems.py <path e.g. weapons/guns> [maxlevel]"""
import json, re, subprocess, sys

def curl(url):
    r = subprocess.run(["curl", "-s", "-L", "-m", "60", "-A", "Mozilla/5.0", url], capture_output=True)
    return r.stdout.decode("utf-8", "replace")

def listview_items(html):
    """The page's `var listviewitems = [...]` array as a list of dicts."""
    i = html.find("var listviewitems = ")
    if i < 0:
        return []
    j = html.index("[", i)
    depth = 0
    instr = False
    esc = False
    chunk = None
    for k in range(j, len(html)):
        c = html[k]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            continue
        if c == '"':
            instr = True
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                chunk = html[j:k + 1]
                break
    if chunk is None:
        return []
    # a few keys are unquoted JS (firstseenpatch: 0); quote any bare key outside strings
    out = []
    instr = False
    esc = False
    n = len(chunk)
    k = 0
    while k < n:
        c = chunk[k]
        if instr:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            k += 1
            continue
        if c == '"':
            instr = True
            out.append(c)
            k += 1
            continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*(?=\s*:)", chunk[k:k + 60])
        if m and out and out[-1] in "{, ":
            out.append('"' + m.group(0) + '"')
            k += len(m.group(0))
            continue
        out.append(c)
        k += 1
    try:
        return json.loads("".join(out))
    except Exception as e:
        print("json error", e)
        return []

if __name__ == "__main__":
    path = sys.argv[1]
    maxlvl = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    html = curl("https://www.wowhead.com/forever/items/" + path)
    items = listview_items(html)
    print("items parsed:", len(items))
    rows = []
    for it in items:
        if 4 in (it.get("source") or []) and it.get("reqlevel", 0) <= maxlvl and it.get("quality", 0) >= 2:
            sm = it.get("sourcemore") or []
            q = [(x.get("n"), x.get("c"), x.get("ti")) for x in sm if x.get("t") == 5]
            rows.append((it.get("reqlevel"), it["id"], it["name"], it.get("quality"), it.get("dps"), q))
    rows.sort()
    for r in rows:
        print(r)
