"""Generates macros.html and wow-forever-macros.md from data.py + template.html.
Run after any change to data.py or template.html: `python build.py`
"""
import json
from data import *

# Group ordering used when rendering a spec's macro groups (both HTML and MD).
ORDER = [DPS, HEAL, CLEAN, AUTO, BUFF, PANIC, TARGET, QOL, FOCUS, MISC]

def sort_groups(groups):
    return sorted(groups, key=lambda g: ORDER.index(g["type"]))

# Example patterns shown at the top of the markdown cheatsheet, one per macro style.
INTRO_RULES = [
    ("Damage (Priest — target-of-target aware)", dps("SPELL")),
    ("Damage (every other class)", dpsHarm("SPELL")),
    ("Mouseover heal / utility", heal("SPELL")),
    ("Friend-or-foe (Dispel Magic)", util("SPELL")),
    ("Buffs (adds self fallback)", buff("SPELL")),
    ("Spam-safe channel", chan("SPELL")),
    ("Wand", WAND),
]


# =============================================================================
# Markdown build (wow-forever-macros.md)
# =============================================================================

def macro_markdown(m):
    """Render one macro entry as markdown: name + note line, then a code block."""
    if not m["code"]:
        return f"*{m['note']}*\n"
    heading = f"**{m['name']}**"
    if m["note"]:
        heading += f" — {m['note']}"
    return f"{heading}\n```\n{m['code']}\n```\n"


md = []
md.append("# WoW Forever Macro Cheatsheet (nobody174 style)\n")
md.append(
    "Copy/paste macros for Priest, Shaman, Paladin, Warlock, Hunter and Warrior. "
    "Each class has a **Shared** section (every spec uses it) plus spec-only extras.\n"
)

md.append("## Patterns\n")
for name, code in INTRO_RULES:
    md.append(f"**{name}**\n```\n{code}\n```\n")

md.append("## Notes\n")
md.append(
    "- Spells without a rank cast your highest rank automatically.\n"
    "- Buff macros add `[@player]` as a last fallback so they self-buff with no target. "
    "Delete it if you want the strict two-clause style.\n"
    "- Item macros (`/use ...`) need the item name edited to the rank you carry.\n"
    "- WoW Forever changes some classes/systems; if a spell name is renamed or missing "
    "in beta, swap the name and keep the pattern.\n"
    "- Macro limit is 255 characters; every macro here fits.\n"
)

md.append("## Universal (all classes)\n")
for group in UNIVERSAL:
    md.append(f"### {group['type']}\n")
    for m in group["macros"]:
        md.append(macro_markdown(m))

for cls in CLASSES:
    md.append(f"## {cls['name']}\n")
    for section in cls["sections"]:
        title = "Shared (all specs)" if section["spec"] == "Shared" else section["spec"]
        md.append(f"### {cls['name']} — {title}\n")
        for group in sort_groups(section["groups"]):
            md.append(f"#### {group['type']}\n")
            for m in group["macros"]:
                md.append(macro_markdown(m))

with open("wow-forever-macros.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md))


# =============================================================================
# HTML build (macros.html)
# =============================================================================

payload = {
    "universal": {
        "name": "Universal",
        "color": "#FFD100",
        "sections": [{"spec": "All classes", "groups": UNIVERSAL}],
    },
    "classes": CLASSES,
    "order": ORDER,
    "patterns": [{"name": name, "code": code} for name, code in INTRO_RULES],
}

with open("template.html", encoding="utf-8") as f:
    template = f.read()

html = (
    template
    .replace("__DATA__", json.dumps(payload))
    .replace("__PAGE_MACROS__", 'aria-current="page"')
    .replace("__PAGE_BUILDS__", "")
    .replace("__PAGE_ADDONS__", "")
    .replace("__PAGE_LAUNCH__", "")
)

with open("macros.html", "w", encoding="utf-8") as f:
    f.write(html)

print("built")
