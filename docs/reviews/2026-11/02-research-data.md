# Review 2: Research Analyst + Data Analyst

Date 2026-11-09. Read-only. Question asked: is what we publish still true, and does each data set agree with its source and with the other data sets?

Checks run: `gen_talent_data.py --check` (trees match the live snapshot: **pass**), `--drift` (no output: no drift); every `/cast` and `/use` spell name in `data.py` (274 casts) compared with the shipped trainer list (Wowhead Forever, 2026-11-07) and the talent trees; dates and wording of every data file and page; `news.json` against what shipped.

## Verdict
The numbers (talent trees, trainer list, builds) are in good shape: they were regenerated this week from live sources and are machine-checked. The bigger problem is **time**: the game launched on 2026-11-04 (five days ago) and a lot of the site and the addon still speaks as if it had not. There is also one macro that cannot work.

## Findings

### Wrong or stale facts (fix first)

| # | Sev | Finding | Evidence | Fix |
|---|---|---|---|---|
| R1 | **High** | **Mage macro "Remove Curse (friend or foe)" casts a spell the Mage does not have.** Wowhead Forever's Mage list has *Remove Lesser Curse* (id 475, level 18); there is no *Remove Curse* for Mage. The macro does nothing in game. | `data.py:439` `util("Remove Curse")`; `wh_all.json` mage rows | Rename the spell to `Remove Lesser Curse` (and the macro name), rebuild, owner confirms in game. Add a build-time check (see R7) so this class of error cannot ship again. |
| R2 | **High** | **The whole site still speaks pre-launch.** Launch was 2026-11-04 23:00 UTC. Still live: the "Beta" corner ribbon (the source comment says "remove once the countdown hits zero"), meta descriptions "Countdown to WoW Forever launch", `bis.html` "at the level 30 beta cap ... When WoW Forever launches on November 4", `professions.html` "Based on the level 30 beta: it can change before launch on November ...", launch-plan "Draft ... checked against what the beta shows", "Test in beta" section ("Beta ran until Oct 21"), builds "re-check in beta" on 9 builds, addons.html "still filling in during beta". Counts of the word *beta*: launch-plan 11, builds 9, index 8, bis 7, news 6. | `grep -ci beta` | One "post-launch pass": remove ribbon, retitle the countdown page, rewrite the BiS/professions ledes, turn "Test in beta" into "Confirmed / still to verify" using the live game. See also the Writer review (W1). |
| R3 | **High** | **BiS data is the level 30 beta list** (`bis-data.json` updated 2026-10-17, `level: 30`, ForeverDB). The level 60 tab says "in the works". After launch this is the page people will use most, and it is at least three weeks old; ForeverDB refreshed at least once on 2026-10-16. The addon ships the same data as `BiZData.lua` ("beta build" in its footer text). | `bis-data.json`, `bis.html:365`, `Locale.lua:632` | Re-pull ForeverDB / ForeverChanges, check what changed since 10-17, ship; decide whether the level 60 lists exist yet (the "Launch-day refresh" item in news `next`). |
| R4 | Med | **Enchant prices and recipes are dated.** `prices.json` updated 2026-10-07 (pre-launch beta prices); the page fetches live AHledger prices, so the fallback matters only if AHledger is down, but the "Our crafts" and BiS-enchant lists come from the 10-06 level 30 pages. | `prices.json`, `professions.html:392` | Refresh after the BiS refresh (R3); decide if the 10-07 fallback should be dated on the page. |
| R5 | Med | **40 macros are still marked "Test in beta"** (Druid 28, Hunter 3, Shaman 2, Paladin 2, Warrior 3, ...). The game is live, so each one can now be answered yes/no. Among them: Shaman *Elemental Mastery* (in neither the Nov trees nor the beta trees; the two macros that need it cannot work), Druid *Starsurge / Sunfire / Starfall* (they exist as spells in Wowhead, level 1, no trainer source: probably talent- or rune-granted), Paladin *Blessing of Salvation / Light / Sanctuary* (not in Wowhead's Forever Paladin list at all, so likely not in Forever). | scan of `data.py` notes + names vs `wh_all.json` | Run the in-game test pass for these macros; delete the ones that cannot exist (Elemental Mastery x2, Salvation/Light/Sanctuary if confirmed), drop the "Test in beta" prefix on the ones that work. |
| R6 | Low | **news.json 2026-11-07 vs 11-08.** The 11-07 entry says builds follow "the most popular current build"; 11-08 says "recommended builds". Both are true as history, but the 11-08 entry says "all 51 points at level 60" while Rogue Combat 60 kept the older popular-based build and Assassination 30 had two ranks capped. | `news.json` | Fine as history. Add one line in the BACKLOG item so the exceptions are not forgotten (they are, for rotations, already). |

### Data integrity (internal consistency)

| # | Sev | Finding | Fix |
|---|---|---|---|
| R7 | Med | **No automatic check that macro spell names exist.** 274 casts were checked by hand today; most "misses" are legitimate (stances, forms, pet and quest spells, consumables, Shoot, Auto Shot) but one was a real bug (R1). A check against the trainer list + trees + a small allow-list would catch typos and renamed spells at build time. | Add `tools/check_macro_spells.py` run by `build.py` (warning list, not hard fail), using `TrainingData.lua` and `TalentData.lua`. |
| R8 | Low | **Trainer list is Wowhead's "source 6" only.** Spells with source 4 (shapeshifts, stances, quest-given) and 2 (talent/world) are not in it, so the Training tab will not show *Bear Form*, *Berserker Stance* or *Summon Felhunter* even though they have levels. Wowhead gives them (Bear Form level 10, Berserker Stance 30, Felhunter 30). | Decide: include source 4 rows flagged "quest" (no price) so the Training tab shows the whole path, or state in the tab note that quest-given spells are not listed. |
| R9 | Low | **Costs are Wowhead's list price**; the tab marks them `~`. Reputation discounts and any Forever-specific price changes are only corrected once a trainer is visited. Acceptable, and clearly labelled. | None; keep the note. |
| R10 | Info | The rebuilt builds (RankedBoost) are one outside source; RankedBoost itself is a third-party site with its own errors (it listed Lethality 5 and Seal Fate 5 against live maximums of 2 and 3, which tells us its data lags the game's November change). | Treat as "recommended starting point"; the page already says "tell us if a class looks off". Cross-check the three most-played specs against a second source (Wowhead guide, Icy Veins) before calling them done. |

## What checked out
- Talent trees: identical to the live Wowhead/nether data (`--check`).
- Trainer list: 9 classes, 32-52 rows each, dated 2026-11-07, regenerates from `wh_all.json`.
- Macro style rules (255 chars, no ranks) are enforced by tests; 0 failures.
- Credits (AHledger, ForeverDB, Wowhead) are present where the rules require them (checked in `docs/professions-bis.md`; wording not re-audited here).

## Not covered
- Individual item and enchant numbers on the BiS and professions pages (several thousand rows) were not re-verified against the sources; that needs the browser pipeline and is part of the R3 refresh.
- Launch-plan route facts (zone level ranges, quest steps) not re-verified. The page itself marks unverified lines "unverified"; after launch that tag should be resolved from real play.
