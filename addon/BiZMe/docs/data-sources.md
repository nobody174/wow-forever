# Forever data research for BiZMe (2026-11-15)

Checked: the support-folder ledger (C2, C18, D15-D22), `bis/DATA_SOURCES.md` (terms read 2026-10-17 and 2026-11-13), `bis/own/wclbox-diff.md`, `bis/own/rerank-review.md`, the installed addons.
No new web or in-game requests were made this session; open items are listed under "Still to test".

## TL;DR
- **Item stats do differ from Classic**, and Forever changes them with hotfixes. Of 9,843 items in both our beta table and the live WCLBox list, 908 differ in dps, 384 in armor, 73 in stamina, 58 in required level, 37 in quality, 17 in item level (`bis/own/wclbox-diff.md`); 1,896 gear items are new since our table; of 1,384 best picks, 526 changed and 544 are new against ForeverDB's build. Ledger C2: enchant values differ too. **Never assume Classic numbers.**
- **Item facts: WCLBox open API** (credit required, 5 req/s). The game itself (`GetItemStats` in the addon) is the final check.
- **Encounter Journal API**: the client has `EJ_GetInstanceByIndex`, `EJ_SelectTier`, `EJ_SelectInstance`, `EJ_GetEncounterInfoByIndex`, `EJ_GetCreatureInfo`, and Forever adds its new dungeons "in a separate Encounter Journal tier" (ForeverDungeonJournal's code comments). That addon uses them **only for boss portraits** and never calls a loot function. **Loot through the EJ is untested.** An earlier finding (`bis/DATA_SOURCES.md`) says the client files hold no loot, vendor or EJ loot tables. A read-only dump will settle it (below).
- **Drops, vendors and quest rewards are server data.** Classic content: CMaNGOS (GPL). Forever-new content: player recordings and community sites. Our recorder exists.
- **Trust order for BiZMe:** game client, then WCLBox, then CMaNGOS and AtlasLoot (GPL, credited), then our recorder, then ForeverDB for the picks only, the rest "link and credit only".

## Item stat changes vs Classic
| Evidence | Finding |
|---|---|
| `bis/own/wclbox-diff.md` (2026-11-13, WCLBox 70888 vs our 70450 table) | quality 37, item level 17, required level 58, stamina 73, intellect 34, agility 21, strength 19, spirit 17, other stats 334, armor 384, dps 908 differ among 9,843 shared ids; 2,432 of our 12,684 ids no longer exist (OLD / Deprecated items); 1,896 new gear ids |
| Ledger C2 | Bracer Minor/Lesser Stamina +3/+4 and Chest Minor Stats +2 all stats are not Classic values |
| Ledger D18-D19 | stat = percent x `RandPropPoints` budget by item level, quality and slot; 11,103 older items need server hotfix rows; recomputation matched 77 of 77 |
| `bis/own/rerank-review.md` | best picks against WCLBox: same 266, changed 526, new 544, not in WCLBox 48 |
Consequence: `GearScore` must keep reading stats from the game (it does, `C_Item.GetItemStats`). The score printed in the data is a snapshot and can be stale, so the tab should show the data build.

## Dungeon / encounter journal API
- Seen in use (guarded by `type(fn) == "function"` in ForeverDungeonJournal): `EJ_GetNumTiers`, `EJ_SelectTier`, `EJ_GetInstanceByIndex(i, false)`, `EJ_SelectInstance`, `EJ_GetEncounterInfoByIndex`, `EJ_GetCreatureInfo`.
- Not known to exist: `EJ_GetNumLoot`, `EJ_GetLootInfoByIndex`, `C_EncounterJournal.GetDungeonEntrancesForMap` (entrance coordinates), `EJ_GetInstanceInfo` (map id). ForeverDungeonJournal keeps its own hand-entered data (`Dungeons.lua`, `DungeonEntrances.lua`).
- **Test (to add to `addon/dev/TESTING.md`, read-only):** a `/r2f debug ej` that walks tiers and instances, prints name and map id, counts loot per encounter if the function exists and lists which `C_EncounterJournal` functions exist. Non-zero loot counts would give boss loot and entrances from the client with no third party.

## Where item-to-source data can be trusted
| Source | For | Terms (from `bis/DATA_SOURCES.md`) | Use in BiZMe |
|---|---|---|---|
| Game client / DB2 (wago.tools CSV) | items, recipes, reagents, factions, maps | Blizzard data; we publish our own numbers | yes, the base |
| WCLBox open API | all items, tooltips, status against a build | credit "新手盒子·魔兽世界无限数据库" with an item link; 5 req/s per IP; 5 min cache | yes: item facts, changed/new flags, names |
| CMaNGOS classic-db | Classic drops, vendors, quests | GPL v2: credit and licence note | yes (done: `classic_sources.py`) |
| AtlasLoot Continued | Forever dungeon loot per boss (35 zones, 3,617 items), PvP, crafting | GPL v2 | yes (done: `atlasloot_import.py`); its Factions module is empty |
| QuestieDB `forever` branch | quest givers, NPC and object coordinates | Questie is GPL v3; the DB repo shows no licence field | coordinates only, read for now |
| ForeverDB | the picks and printed scores | no licence; robots.txt allows; owner decided 2026-11-13 it stays the picks source | yes, polite fetch, credited |
| Wowhead Forever | tooltips, pages | ZAM/Fanbyte EULA: personal, non-commercial, no copying or derivatives; robots.txt bars 28 AI/scraper agents | display and single lookups only |
| ForeverChanges | 5-7 deep lists, enchants, loot | 403 to scripts, terms not read | compare only |
| ZugZugDB | NPC, quest, object records | forbids scraping and bulk copying | link only |
| Forever Guide, ForeverCodex, ItemQuester, ForeverArtisan | many | All Rights Reserved / unspecified | no |
| foreverwow.gg, forevermybis.com | the data behind two addons | unknown for the sites (ForeverMyBis addon is MIT) | **terms to read in a browser** before any use |
| Installed addons (DungeonJournal, Leveling BiS, others) | whatever they ship | none or All Rights Reserved | ideas only |

## Gaps to close for BiZMe (data)
1. **Places**: 9 entries in `bis/places.json`; 12 of 433 level-60 best picks can be routed. Candidates: AtlasLoot and Questie coordinates (GPL), a `C_Map` / EJ read-out, positions added to the recorder.
2. **Unknown sources**: 78 of 433 level-60 best picks. A triage list for the group to go and record.
3. **Depth**: 3 picks per slot. ForeverMyBis ships 8 contenders with scores (MIT), ForeverChanges 5-7 (terms unknown). Decide if depth matters for the upgrade engine; check by hand whether ForeverDB's page shows more than 3 (unverified).
4. **Freshness**: ForeverDB lists are for build 70862, live is 70938; the refresh recipe in `bis/README.md` takes about 65 minutes of polite downloads.
5. **Raids / phases**: none exist yet; watch other addons' pre-raid and phase labels.

## Still to test (needs the owner or a browser)
- `/r2f debug ej` (above).
- Read the foreverwow.gg and forevermybis.com terms in a browser.
- Check whether ForeverDB's BiS page lists more than 3 alternatives.
- Measure addon memory with the 3.5 MB data (`collectgarbage("count")` before and after login).
- Reputation standing API on Forever for "reachable now".
