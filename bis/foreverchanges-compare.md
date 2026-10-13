# ForeverChanges vs our Mr.BiZ data (2026-10-13)

Question: should ForeverChanges (https://foreverchanges.pro/bis) be a second Mr.BiZ source next to ForeverDB?
Method: the index page and four spec pages were read (fetched through a page summariser, so item ids were copied from its
answer, not scraped; treat the numbers as indicative). Compared with `bis-data.json` (ForeverDB, level 30).

## What ForeverChanges has

- 36 level-30 pages: per class a PvE list plus PvP / Tank / variant lists (`/bis/<class>`, `/bis/<class>/pvp`,
  `/bis/<class>/tank`, `/bis/mage/fire`, `/bis/paladin/shockadin`, `/bis/druid/balance` ...).
- Per slot a **ranked list of 5 to 7 items** (we show best + 2 next), each with an item id, source (dungeon boss, quest,
  profession and skill, rare, auction house) and, per slot, the best enchant or armor kit. Trinkets are listed for every spec.
- Their PvE pages are for **26-point builds** (21 + the Talented legacy perk), e.g. "Arms 26" or "Marksmanship 26".
- No scores or weights: the ranking is editorial.

## How it compares (4 specs, 60 slots)

| | ForeverDB (ours) | ForeverChanges |
|---|---|---|
| Items per slot | 3 (best + 2) | 6 |
| Their #1 equals our #1 | | 17 of 60 slots (28%) |
| Their #1 is in our top 3 | | 25 of 60 slots (42%) |
| Items listed per spec | about 45 | about 90; only about a third are shared |
| Trinkets | missing for some specs (Hunter Marksmanship, Warrior Arms have none) | every spec |
| Score / "how far behind" | yes (stat weights) | no |

Per spec: Hunter Marksmanship shared 32 of 84 items, Mage Fire 30 of 96, Priest Holy 27 of 94, Warrior Protection 32 of 88.
Slots where both agree on #1 in Warrior Arms: neck, shoulder, waist, legs, feet, ring, ranged (7 of 14).

## Reading

- The two sources disagree a lot on the top pick, so they are not interchangeable. A merge would need a rule.
- ForeverChanges fills the real gaps in ours: trinkets, a deeper list (6 not 3), PvP and tank variants, and some pages
  built for the 26-point (Talented) setup.
- Ours has the score and the gap to the next pick, which ForeverChanges does not.

## Suggested way in (not done)

1. Keep ForeverDB as the score source. Add ForeverChanges as a **second opinion** per slot: a small "ForeverChanges #1"
   line (or a marker on an item both lists rank high), plus their trinkets where ours has none.
2. Store it as `bis/raw-fc/<spec>.json` like `bis/raw/`, generated into BiZData with `via = "ForeverChanges"`
   (the data already has a `via` credit per item, shown in the tooltip).
3. A scraper needs ForeverChanges' own data endpoint; the pages are JavaScript pages ("Loading the page...").
   Ask the site's owner before bulk-reading it (the Professions page already uses their enchant lists, credited).
4. Decide first: should Mr.BiZ show 26-point (Talented) or 21-point picks? The perk switch exists on the site and in
   the Talents tab; Mr.BiZ could follow it.
