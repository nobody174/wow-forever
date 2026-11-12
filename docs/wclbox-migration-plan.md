# Moving item data from Wowhead to WCLBox (plan, 2026-11-13)

Status: **plan only, nothing changed yet.** Decision behind it: `bis/DATA_SOURCES.md` ("Decision, revised 2026-11-13").

## TL;DR
- WCLBox's open item API matches our current data on everything we compared, and it is newer than our table (client build 70888 vs our 70450).
- It can replace the Wowhead-derived **item** data (the stats of 4,990 items, `quality.json`, the runtime item lookups). It cannot replace trainer lists, talent trees, enchant lists or quest-reward lists: it has items only.
- About 20% of the ids in our `bis/items.json` are not in WCLBox's current build, so the clean move is to **rebuild the items table from WCLBox**, then re-run Mr.BiZ. Rankings will shift, which is the point of using live data.

## What we tested (2026-11-13, in Chrome against the live API)
| Check | Result |
|---|---|
| 56 sampled items WCLBox returned (31 whose stats came from Wowhead, 25 from the client) | quality, item level, required level and the five main stats matched **56 of 56** |
| Armor value on those items | 38 of 41 matched (3 differ, not yet explained) |
| Weapon damage per second | 9 of 12 matched (3 differ, probably rounding; to check) |
| Coverage: 400 random ids from `bis/items.json`, asked in batches of 100 | WCLBox returned **318 (about 80%)** |
| Single-item requests | 14 of 70 failed even after retries, consistent with the 20% missing ids (I did not separate "not found" from throttling) |

The sample is small. The full diff in phase 2 is what settles the 3+3 mismatches.

## What can move and what cannot
| Data | Where it is now | WCLBox can replace it? | Plan |
|---|---|---|---|
| `bis/items.json` (12,684 gear items; 4,990 stats from Wowhead tooltips) | `bis/tools/items_build.py` | **Yes.** List gives name, quality, levels, slot, type; item detail gives `tooltipEn` with stats, armor and damage | Rebuild from WCLBox (phase 3) |
| `bis/quality.json` | `bis/tools/wh_quality.py` | **Yes** (`quality` in the list, 100 ids per call) | Delete after phase 3 |
| Runtime item lookups in `bis.html` and `professions.html` (quality, slot, level, bag size, "Use:") | `nether.wowhead.com` tooltip, 4 at a time | **Yes**: list batches for quality, slot, levels; item detail only for bag size and "Use:" | Switch in phase 5. Wowhead's `tooltips.js` hover stays (its own embed, credited) |
| Auction House names | WCLBox live | already | Fallback list becomes complete after phase 3 |
| Quest-reward weapons | `wh_quest_weapons.py` (Wowhead item pages) | **No**, WCLBox has no sources | Separate task: Questie `forever` branch, CMaNGOS, own recorder |
| Trainer spells | `gen_training_data.py` | **No** | Separate task |
| Talent trees | `gen_talent_data.py` (Wowhead data endpoint) | **No** | Owner decision below |
| Enchant lists | Wowhead spell pages | **No** | Separate task |

## Phases
1. **Pull** (Chrome, owner's IP): page the list with `limit=100` (about 220 calls), then the detail of every gear item (about 12,700 calls; at 3 to 4 per second that is roughly an hour, less if we skip grey and white items). Cache to `bis/own/cache/wclbox.jsonl` (gitignored) and commit a compact snapshot of the fields we use.
2. **Diff** against the current `bis/items.json`, field by field. Explain the armor and damage mismatches. List the ids WCLBox lacks and the items it flags as new or changed.
3. **Switch the build**: `items_build.py` reads the WCLBox cache (`src: "wcl"`), `wh_tooltip_pull.py`, `wh_quality.py` and `wh_items.py` are retired once the diff is clean.
4. **Re-rank**: run `bis/build_bis.py`, review what changed in Mr.BiZ against the old output, then regenerate `BiZData.lua` and run the addon tests.
5. **Runtime switch**: `bis.html` and `professions.html` read WCLBox batches instead of the Wowhead tooltip endpoint.
6. **Credits and docs**: WCLBox credit (as it asks: 新手盒子·魔兽世界无限数据库, link to the item page) on Mr.BiZ and Professions, README, `bis/DATA_SOURCES.md`, `docs/pipeline.md`.

## Risks
- WCLBox says its data is test data and may change; the committed snapshot keeps us working if it changes or disappears.
- Mr.BiZ picks will move because live items differ from the beta table. Review before pushing.
- Rate limit is 5 per second per IP (burst 20); the pull must be throttled and resumable.
- A fan-run API can go offline. Page code keeps a fallback (already the case on the Auction House).

## Decisions for the owner
1. Rebuild the whole items table from WCLBox (recommended), or only patch the 4,990 Wowhead-derived items?
2. Talent trees: keep Wowhead's data endpoint for now, or move to the client's own tables (wago.tools, public)?
3. Run the pull now in Chrome as a background job, or later?
