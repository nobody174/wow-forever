# Mr.BiZ cross-check: our own scoring next to ForeverDB's (started 2026-10-15)

Owner decision (2026-10-15): do NOT replace ForeverDB yet. Build the machinery now at level 30 so it can be extended to level 60 at launch, and
use it as a cross-check. ForeverDB's weights (`bis/raw/*.json` `weights`) and its sources stay; Wowhead is the item data.

| File | What it does |
|---|---|
| `tooltips.py` | Wowhead Forever item tooltips (`nether.wowhead.com/forever/tooltip/item/<id>`), paced 4 at a time, cached in `cache/tooltips.json` (not in git). Backs off on 403 / 429. |
| `stats.py` | Tooltip HTML -> stats in the words of ForeverDB's weights (`Stamina`, `spell power`, `Shadow Damage Done`, `crit`, `hit`, `weapon DPS`, ...). Lines it does not know are returned as `unknown`. |
| `check_scores.py` | Cross-check 1: our stats x ForeverDB's weights against ForeverDB's printed `score` for every best pick. Lists the picks that differ and the unrecognised equip lines. |
| `check_order.py` | Cross-check 2: are best / 2nd / 3rd in ForeverDB's order under our scoring? Writes `report.md`. |
| `report.md` | The latest output of `check_order.py` (committed so it can be read without running anything). |

Run (repo root): `python bis/own/check_scores.py`, `python bis/own/check_order.py > bis/own/report.md`.

## What the first run (2026-10-15, beta build 1.60.1.70338) showed

* **ForeverDB's score is stats x weights**, exactly (e.g. +14 Shadow Damage Done, +12 Stamina at 1 and 0.1 = 15.2). Conversions it applies to
  percent stats: **1.0% hit = 10**, **1.0% crit = 14** (haste and expertise not seen on a best pick yet). Weapon DPS is counted only in the main
  hand / off hand of melee specs and in the ranged slot of Hunters.
* Of the best picks, the stats agree for all but about 26 (of about 440 spec / slot rows). The ones that do not agree are almost all **items whose stats scale
  with item level** (the tooltip carries a `<!--sc...-->` marker, or "Requires Level 0"): Wowhead's default tooltip shows one item level, ForeverDB
  prints different numbers (for example Zealot's Robe: Wowhead 7 / 7 / 11, ForeverDB 10 / 10 / 15, which is what Wowhead shows at item level 50;
  `?ilvl=<n>` on the tooltip URL changes the numbers). Which level the game really uses for a level 30 character is NOT known: test it in game
  on one of the items in `report.md` before trusting either side.
* The order check (`report.md`) finds 19 slots of 414 where our best of the three is not ForeverDB's best by more than 10 percent. Nearly all
  involve a scaled item, so read them as "check this item in game", not as "ForeverDB is wrong".

## Next (level 60 launch, 2026-11-04)

1. Re-read the raw files for level 60 (`bis/README.md`), rerun both checks, review `report.md`.
2. If the scaling question is settled, pass the right `?ilvl=` in `tooltips.py` for scaled items.
3. Only then consider a bigger candidate universe (Wowhead item list pages per slot, reqlevel limit) so we can find items ForeverDB does
   not list at all. Wowhead throttles after about 70 quick page loads (`www.wowhead.com`); the tooltip API took 150 requests at 4 at a time without problems.
