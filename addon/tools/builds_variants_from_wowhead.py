#!/usr/bin/env python3
"""Add ALL of Wowhead's Forever level 60 build variants (raid, dungeon, PvP, leveling, named variants) to builds.html.

Companion of builds_from_wowhead.py (which sets each spec's first build). Every [talent=...] build on a guide page becomes an entry
labelled by its heading ("Raid", "Dungeon", "PvP", "Shockprot" ...). Identical codes are merged ("Raid / Dungeon"), a code equal to the
spec's existing main entry is skipped, specs we had no entry for (Discipline, Arcane, ...) get all of theirs. Generated entries carry
`wh: 1` and are removed and rebuilt on every run (idempotent). PvE variants of a spec that has a main entry copy its rotation.

  python addon/tools/builds_variants_from_wowhead.py            dry run (prints the labels)
  python addon/tools/builds_variants_from_wowhead.py --apply    writes builds.html
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import builds_from_rankedboost as rb  # noqa: E402
import builds_from_wowhead as bw  # noqa: E402

ROOT = rb.ROOT
CLASSES = ("priest", "warlock", "mage", "rogue", "druid", "shaman", "hunter", "paladin", "warrior")
SPECS = {"priest": ["discipline", "holy", "shadow"], "warlock": ["affliction", "demonology", "destruction"],
         "mage": ["arcane", "fire", "frost"], "rogue": ["assassination", "combat", "subtlety"],
         "druid": ["balance", "feral", "restoration"], "shaman": ["elemental", "enhancement", "restoration"],
         "hunter": ["beast-mastery", "marksmanship", "survival"], "paladin": ["holy", "protection", "retribution"],
         "warrior": ["arms", "fury", "protection"]}
ROLE = {"dps": "", "tank": " (Tank)", "healer": " (Healer)"}
SKIP_H3 = ("which build", "fire or shadow")


def page(cls, spec, role):
    url = "https://www.wowhead.com/forever/guide/classes/%s/%s/talent-builds-pve-%s" % (cls, spec, role)
    r = subprocess.run(["curl", "-sL", "-m", "30", "-A", "Mozilla/5.0", "-w", "\n%{http_code}", url],
                       capture_output=True, text=True, encoding="utf-8")
    body, code = r.stdout.rsplit("\n", 1)
    if code != "200":
        return None
    body = body.replace("\/", "/").replace('\\"', '"')
    seq, h2, h3 = [], "", ""
    for lv, txt, c, cd in re.findall(r"\[h([23])[^\]]*\](.*?)\[/h[23]\]|\[talent=([a-z]+)/([^_\]]+)_t0", body):
        if lv:
            txt = re.sub(r"\[icon[^\]]*\]\[/icon\]", "", txt).strip()
            if lv == "2":
                h2, h3 = txt, ""
            else:
                h3 = txt
        elif c == cls:
            seq.append((h2, h3, cd))
    return seq


def label(h2, h3):
    t = h2.lower()
    if "pvp" in t:
        base = "PvP"
    elif "leveling" in t or "open world" in t or "openworld" in t:
        base = "Leveling"
    elif "raid" in t and "dungeon" in t:
        base = "Raid / Dungeon"
    elif "raid" in t:
        base = "Raid"
    elif "dungeon" in t:
        base = "Dungeon"
    else:
        base = "PvE"
    v = h3
    if v and not any(s in v.lower() for s in SKIP_H3):
        v = re.sub(r"\b(Build|PvE|PvP|DPS|Raid)\b", "", v).replace("Retribution (Unsealed Wrath)", "Unsealed Wrath")
        v = re.sub(r"\s+", " ", v.replace('"', "").replace("\\", "")).strip(" ()")
        if v:
            return base + " " + v
    m = re.search(r"\b(Melee|Weaving|Hybrid|Fury-prot)\b", h2)
    return base + (" " + m.group(1) if m else "")


def main():
    apply = "--apply" in sys.argv
    trees = rb.parse_trees()
    path = os.path.join(ROOT, "builds.html")
    text = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    html = text.replace("\r\n", "\n")
    html = re.sub(r"    \{\n      spec: [^\n]*wh: 1,\n(?:      [^\n]*\n)*?    \},\n", "", html)
    a, b = html.index("const DATA60 = {"), html.index("\nconst GUIDES")
    d60 = html[a:b]
    mains = {}   # (class, spec) -> (code, rotation line)
    for m in re.finditer(r'    \{\n      spec: "(.*?)", title: "(\w+) — Level 60 .*?", code: "(.*?)".*?\n(?:      talents:.*\n)(      rotation: .*\n)?', d60):
        mains.setdefault((m.group(2).lower(), m.group(1)), (m.group(3), (m.group(4) or "").rstrip("\n")))
    new = {c: [] for c in CLASSES}
    firsts = []
    for cls in CLASSES:
        for spec in SPECS[cls]:
            for role in ("dps", "tank", "healer"):
                seq = page(cls, spec, role)
                if not seq:
                    continue
                name = " ".join(w.capitalize() for w in spec.split("-"))
                if cls == "druid" and spec == "feral":
                    name = "Feral (Bear)" if role == "tank" else "Feral (Cat)"
                main = mains.get((cls, name))
                if main and seq:
                    firsts.append((main[0], label(seq[0][0], seq[0][1])))
                merged, order = {}, []
                for h2, h3, raw in seq:
                    ranks = bw.decode(raw, trees[cls])
                    for ti, t in enumerate(trees[cls]):
                        for k, x in enumerate(t["t"]):
                            ranks[ti][k] = min(ranks[ti][k], x["m"])
                    n = sum(map(sum, ranks))
                    if n != 51 or rb.legal_fill(trees[cls], ranks) != ranks:
                        print("SKIP (illegal / %d points): %s %s %s" % (n, cls, name, raw))
                        continue
                    code = rb.encode(ranks)
                    lb = label(h2, h3)
                    if code in merged:
                        if lb not in merged[code][0]:
                            merged[code][0].append(lb)
                        continue
                    merged[code] = ([lb], ranks)
                    order.append(code)
                used = {}
                for code in order:
                    if main and code == main[0]:
                        continue
                    labels, ranks = merged[code]
                    lb = " / ".join(labels)
                    used[lb] = used.get(lb, 0) + 1
                    if used[lb] > 1:
                        lb += " " + str(used[lb])
                    items = ['["%s","%d/%d","%s"]' % (x["n"].replace('"', '\\"'), ranks[ti][k], x["m"], x["i"])
                             for ti, t in enumerate(trees[cls]) for k, x in enumerate(t["t"]) if ranks[ti][k]]
                    title = "%s — Level 60 %s %s%s" % (cls.title(), name, lb, ROLE[role])
                    meta = "From Wowhead's Forever build guide: the %s build (checked 2026-11-21)." % lb
                    e = ['    {', '      spec: "%s", title: "%s", code: "%s", meta: "%s", wh: 1,' % (name, title, code, meta),
                         '      talents: tN([%s]),' % ", ".join(items)]
                    if main and main[1] and "PvP" not in lb:
                        e.append(main[1])
                    e.append('    },')
                    new[cls].append("\n".join(e))
                    print(title, code)
    print(sum(len(v) for v in new.values()), "variant entries")
    if not apply:
        return
    out = html
    for code, lb in firsts:
        out = out.replace("code: \"%s\", meta: \"From Wowhead's Forever build guide (standard PvE build, checked 2026-11-21).\"" % code,
                          "code: \"%s\", meta: \"From Wowhead's Forever build guide: the %s build (checked 2026-11-21).\"" % (code, lb))
    for cls in CLASSES:
        i = out.index("\n  %s: [\n" % cls.title(), out.index("const DATA60"))
        j = out.index("\n  ],", i)
        out = out[:j] + "\n" + "\n".join(new[cls]) + out[j:]
    open(path, "w", encoding="utf-8", newline="").write(out.replace("\n", nl))
    print("builds.html written")


if __name__ == "__main__":
    main()
