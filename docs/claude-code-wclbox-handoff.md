# Claude Code handoff: WCLBox item data, live Auction House data, talent audit

Written 2026-11-13 in Claude chat, for Claude Code on the owner's PC. Background and evidence: `docs/wclbox-migration-plan.md` (read it first),
`bis/DATA_SOURCES.md` ("Decision, revised 2026-11-13"). Workflow reminder: chat scoped this, **you implement**; follow `CLAUDE.md` (hard rules,
`python build.py`, addon tests, commit to `main`, changelog + `news.json` when something ships). Reports go in `.md` files in the repo; tell the owner
only a short TL;DR in chat.

## Why this runs on the PC
The cloud sandbox cannot reach WCLBox (403). The PC can. Nothing below needs the sandbox.

## Ground rules
- **Be polite to WCLBox:** at most 3 requests per second (their limit is 5/s per IP, burst 20), one pull at a time, never loop on errors. Their usage
  rules: page the full data with `limit=100`, credit them as 新手盒子·魔兽世界无限数据库 (WCLBox) on every page that shows their data.
- **No new bulk pulls from Wowhead** (its robots.txt blocks AI crawlers; its terms are non-commercial, no-copy). Do not run `wh_tooltip_pull.py`,
  `wh_quality.py` or `wh_items.py` again.
- Never hand-edit generated files (`CLAUDE.md` rule 1). Cache folders under `bis/own/cache/` are gitignored; keep them out of commits.
- Stop and ask the owner at the three **CHECKPOINTS** below. Do not push a re-ranked Mr.BiZ without checkpoint 2.
- Before researching a client or data question, read `../wow-dev-support-folder/06-findings-and-decisions/findings-ledger.md`; at the end add a short,
  generalized ledger row for what we learned about WCLBox (API shape, limits, coverage).

## Track A: item data from WCLBox (do first)

### A1. Pull
1. `git pull`, then read this file and `docs/wclbox-migration-plan.md`.
2. Smoke test: `python bis/tools/wclbox_pull.py --limit 50`. It writes `bis/own/cache/wclbox/{meta.json,list.jsonl,detail.jsonl}`. Check a few lines by
   eye (fields: id, nameEn, quality, itemLevel, requiredLevel, slot, type, classId, status, set, classes, formerName, tooltipEn).
3. Full pull: `python bis/tools/wclbox_pull.py` (about 70 minutes; `--min-quality 2` skips grey and white gear and takes about 40; the default skips
   only grey). It is resumable. If the printed client build differs from `meta.json` the cache restarts on purpose; that is correct.
4. Expect: list = 21,855 items at build 1.60.1.70888 (or newer); detail only for weapons and armor (classId 2 and 4).

### A2. Diff against the current table (read-only)
Write `bis/tools/wclbox_diff.py` that compares `bis/own/cache/wclbox/detail.jsonl` with `bis/items.json` and writes `bis/own/wclbox-diff.md`:
- ids in our table but not in WCLBox (expected about 20%: beta-era ids; list a sample and the counts per quality);
- ids new in WCLBox (not in our table), counts by slot and quality;
- for ids in both: counts of differing quality, item level, required level, the five main stats (3 agility, 4 strength, 5 intellect, 6 spirit,
  7 stamina), armor and damage per second; list up to 20 examples per kind. Parse stats from `tooltipEn` (lines like `+8 Strength`, `65 Armor`,
  `(20.5 damage per second)`). Earlier sample: 56 of 56 matched on quality, levels, main stats; 3 of 41 armor and 3 of 12 dps differed (cause unknown: find it).
- the items WCLBox flags `status: changed` or `new` that are in any current Mr.BiZ pick (`bis-data.json`).

**CHECKPOINT 1:** show the owner the TL;DR of `bis/own/wclbox-diff.md` and get a go before changing the build.

### A3. Rebuild the items table from WCLBox
- `bis/tools/items_build.py` currently reads DB2 tables plus the Wowhead tooltip cache. Add WCLBox as the source (`src: "wcl"`); keep the record format
  (id, n, q, il, rl, inv, c, s, st, ar, dps, spd, src) so `build_bis.py` and the addon keep working. Parse `tooltipEn` with the existing `EQUIP_RULES`
  (spell power, healing, crit, hit, block, dodge, parry, defense, attack power ...). `inv` and `s` (inventory type, subclass) come from WCLBox `slot` and
  `type` (map the names; fall back to DB2 only if needed). Drop ids WCLBox does not have.
- Keep the old file for comparison until checkpoint 2 (`bis/own/items.before.json`, gitignored).
- Regenerate `bis/quality.json` from the same data, then delete `bis/tools/wh_quality.py`, `wh_tooltip_pull.py`, `wh_items.py` and their doc mentions once nothing reads them
  (`wh_quest_weapons.py` stays: WCLBox has no quest sources).

### A4. Re-rank Mr.BiZ and review
1. `python build.py` (it runs `bis/build_bis.py`). Compare the new `bis-data.json` with the old one: which best picks and ranks 2 and 3 changed, per class,
   spec and level; list items that disappeared (not in the live build). Write `bis/own/rerank-review.md` (counts first, then the changes by class).
2. Install `lupa` (`python -m pip install --user lupa`) and run `python addon/tests/run_tests.py`; all green before any push.

**CHECKPOINT 2:** show the owner the TL;DR of `bis/own/rerank-review.md`. Only after the owner agrees: commit and push.

### A5. Site code and names
- `bis.html` and `professions.html` read item quality, slot, level, bag size and "Use:" text from `nether.wowhead.com/forever/tooltip/item/<id>` 4 at a time.
  Switch to WCLBox: list endpoint `GET .../items?ids=<up to 100>` for quality, slot and levels; item detail (`.../items/<id>`) only for bag size and "Use:" text.
  Cache results (5 min HTTP cache applies; keep the existing localStorage caches under new keys). Keep Wowhead's `tooltips.js` hover tooltips (its own embed).
  Fall back quietly if WCLBox fails. Add the WCLBox credit line to Mr.BiZ and Professions (wording above).
- `tools/build_ah_items.py`: build `ah-items.json` (the Auction House fallback) from the full WCLBox list instead of the narrow repo sources, so the fallback
  covers every item (21,855 names). It must work for anyone who runs `python build.py` without the cache: if `bis/own/cache/wclbox/list.jsonl` is missing, keep
  the existing `ah-items.json` untouched and say so. Keep the file size reasonable (ids, English names, quality).
- Update docs (`docs/pipeline.md`, `docs/professions-bis.md`, `docs/site-pages.md`, `bis/README.md`, `bis/DATA_SOURCES.md`, README credits), `CHANGELOG.md`,
  `news.json` (plain words: item data now comes from the live game build), then push.

## Track B: in-game talent audit in the R2F addon (separate, after Track A)
Goal: the game is the judge of whether `TalentData.lua` is right. Source of the data stays Wowhead's talent endpoint (`addon/tools/gen_talent_data.py`,
with `--drift` before each release).
1. **Scope first, small:** the addon reads the live tree through `C_Traits` (see `addon/RoadToForever/Talents.lua`, "Reading the talents: C_Traits").
   Add a read-only debug command that dumps, for the logged-in class, per talent: name, spell id, max ranks, position (row, column), prerequisite
   (which talent and rank) and the tree currency, to a saved-variables table the owner can send. The owner runs it in game on one character per class.
   Do not write to game-owned tables or act in combat (`CLAUDE.md` rule 4).
2. From the dump, decide which fields are reliable on Forever, then add `/r2f talentcheck` (name to be agreed): compares the live tree with
   `TalentData.lua` and prints "matches" or the exact differences per talent. When they differ, the game wins; log it in `BACKLOG.md`.
3. Add tests in `addon/tests/run_tests.py` (a fixture tree with one deliberate difference). Follow `addon/ARCHITECTURE.md` and `addon/dev/TESTING.md` (the
   in-game test goes there as an open test; the owner confirms it).
4. Optional later: cross-check against the client's own tables (wago.tools Talent / TalentTab). A cross-check only: static client files can miss server hotfixes.

**CHECKPOINT 3:** the owner runs the dump in game (one character per class over time); report which fields the game exposes before building the check.

## Done when
- `bis/items.json` comes from WCLBox at the live build, Mr.BiZ re-ranked and reviewed by the owner, addon tests green, pages credit WCLBox, no Wowhead tooltip
  endpoint calls remain in `bis.html` / `professions.html`, the three `wh_*` item tools are gone.
- `docs/wclbox-migration-plan.md` status line updated, `BACKLOG.md` item 4 moved to `CHANGELOG.md`, findings-ledger row added.
- Track B: dump command shipped; check command scoped from real data.
