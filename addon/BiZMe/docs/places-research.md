# Places and sources: offline research (2026-11-15)

Task from the owner: stop relying on in-game checks; find where items, vendors, quest givers and dungeon entrances are from what other addons, the web and the
game files already hold. Roles used: **Researcher** (survey and licences), **Data analyst** (decoding, cross-checks), **Code reviewer** (tests, pipeline rules), **Knowledge base architect**
(what goes in the repo and where it is written down). Everything below was read from files; nothing needed a game session.

## TL;DR
- The best offline sources were hiding in plain sight: **QuestieDB** keeps its whole Forever database inside its `.toc` (CBOR, decoded by our new `questiedb_decode.py`: 15,563 NPCs, 5,914 quests, 23,862 items),
  and **the client's own DB2 table `CollectableSourceVendorSparse`** (wago.tools) lists 3,568 "vendor sells item" rows with world positions.
- Two independent checks agree: the game table's converted vendor spots match QuestieDB's spawns (150 vendors, median error 0.06 map %, 90th percentile 1.5 %), and 23 of our 28 dungeon entrances
  (from ForeverDungeonJournal) match QuestieDB's entrance list within 3 %.
- Result in Mr.BiZ data: level-60 best picks that can point the BiZNav arrow **12 -> 195 of 433** (level 30: 157 -> 264 of 415); picks with an unknown source: **1,718 rows -> 967** (level 30 best picks: 63 -> 2; level 60: 78 -> 38).
- What is still open at level 60: 116 crafted picks (trainer or recipe vendor places), 29 world drops, 38 unknown, 10 reputation, quest givers without a spot. Details in "Left".

## Source survey (what each holds, and whether we may use it)
| Source | Where | What it holds | Licence | Used for |
|---|---|---|---|---|
| **QuestieDB** (Forever flavor) | `AddOns\QuestieDB\QuestieDB_Forever.toc` (18 MB of `## X-Npc-<id>-<field>` lines, base64 of CBOR) + `support\Forever\Zones\*.lua` | NPC names, flags, **spawns per zone (map percent)**, quest starters/finishers, item names and drop/vendor/quest links, **dungeon entrance list incl. Forever-new dungeons**, area id -> map id | GPL v3 (`LICENSE.md`) | vendor and quest-giver spots, entrance cross-check, item sources (single answers) |
| **Game table `CollectableSourceVendorSparse`** | wago.tools DB2 export, build 1.60.1.70938 (also in the client's hotfix cache) | vendor creature id, item id, **world position**, area | Blizzard game data | vendor spots, "sold by" sources |
| **UiMapAssignment** (DB2) | wago.tools | each zone map's world bounds (incl. Forever-new maps 2521, 2548, 2652) | game data | world -> map percent |
| **ForeverMyBis** | `AddOns\ForeverMyBis\Data\Items.lua` | per item source text, `vl` vendor spots, `ql` quest giver spots (map, x, y, name, quest), `dz` dungeon, recipes `cr`/`mt`; 12.6k records | **MIT** (TOC `X-License`) | second opinion; confirmed Pix Xizzix (28.4, 75.8) and Winklespark (62.8, 38.2) |
| **ForeverDungeonJournal** | `Data\DungeonEntrances.lua`, `QuestMaps.lua` | 35 entrances, quest giver coordinates for the new dungeons | no licence text: all rights reserved | **coordinates only** (facts), no text/art/code; entrances cross-checked against QuestieDB |
| ForeverLevelingBiS | `Data\Quests.lua` | quest starts with x, y per quest | All Rights Reserved | read only (not used) |
| ForeverCompanion | `Data\Loot.lua` (dungeons, bosses, items), `Nodes.lua` (gather nodes), `Dictionary.lua` | loot per boss, no entrance coordinates | none stated | ideas only |
| ForeverWoWBiS | `Sources.lua` (`q/d/v/c/o` kinds, names), `Spots.lua` (grind spots) | source names without coordinates | none stated | ideas only |
| RXPGuides | `Guides\*.lua` (`.goto Zone,x,y`, `.target Name`) | NPC positions inside leveling guides, Classic | RestedXP, proprietary | not used (QuestieDB covers it under GPL) |
| Leatrix_Maps | `Leatrix_Maps.lua` | dungeon list with area ids and map art, no entrances | Leatrix | not needed |
| Questie (addon) | `Database\` | packed Lua DB of the live Questie | GPL v3 | same data as QuestieDB; not read separately |
| Journal tables (`JournalInstance`, `JournalEncounter`, `JournalEncounterItem`, `JournalTierXInstance`, `DungeonMap`) | wago.tools | **do not exist for the Forever build** (HTTP 400); in game the Encounter Journal is empty | - | dead end |
| `AreaPOI` (DB2) | wago.tools | 372 points: flight masters and towns (Anvilmar, Brill), **not** dungeon entrances | game data | not useful |
| `CollectableSourceEncounterSparse`, `...QuestSparse` | client hotfix cache (`Cache\ADB\enUS\*.tmp`, 4 bytes = empty) and not on wago | would give boss and quest sources, but the server did not send them | - | dead end for now (recheck after a patch) |
| `D:\WoW-Extract\interface` | Blizzard UI Lua and API docs | `C_EncounterJournal.GetDungeonEntrancesForMap` is documented (and used by Blizzard's map data provider) but returns nothing here | Blizzard code, read only | explained the empty journal |

## How the numbers were produced
1. `python bis/tools/db2_pull.py` (now also pulls `CollectableSourceVendorSparse`, `CollectableSourceInfo`, `UiMapAssignment`, `AreaPOI`) -> `bis/own/cache/db2/<build>/`.
2. `python bis/tools/questiedb_decode.py` -> `bis/own/cache/questiedb_live.json` (decodes CBOR from the addon's `.toc`; layout from QuestieDB's own `src/read/baked.lua`, `src/meta/*.lua`).
3. `python bis/tools/collectable_vendors.py` -> `vendor_spots.json` (world position -> map percent: map x = (Ymax - y) / (Ymax - Ymin), map y = (Xmax - x) / (Xmax - Xmin) of the zone's UiMapAssignment bounds; the row's AreaTableID picks the right zone where maps overlap).
4. `python bis/tools/found_sources.py` (new tiers: the game's vendor table, QuestieDB items, ForeverMyBis) then `python bis/tools/questie_places.py --write` (vendor and quest-giver spots, `--dungeons` for the entrance check) and `python bis/tools/dj_entrances.py --write` (entrances), then `python bis/build_bis.py`.
5. `build_bis.place_key` now also tags quest rows (`quest:<title>`), so a quest reward points at its giver.

## Cross-check of dungeon entrances (ours from ForeverDungeonJournal vs QuestieDB `dungeons.lua`)
Agree within 3 map percent: Shadowfang Keep, Razorfen Kraul, The Stockade (52.4, 70.0 in both), Wailing Caverns, Blackfathom Deeps, Gnomeregan, Razorfen Downs, Scarlet Monastery, Zul'Farrak, Uldaman, The Deadmines,
Blackrock Spire / Depths, Scholomance, Maraudon, Ragefire Chasm, Dire Maul (east), City of Dalaran, Excavation Site: Wetlands (23 entrances).
**Differ, to settle by looking once:** Stratholme (ours 30.0, 15.0 vs QuestieDB 26.5, 10.4 and 41.5, 17.7: two gates), Dire Maul north/west (other entrances), **Ruins of Lordaeron** (ours Tirisfal 63.4, 67.4; QuestieDB Undercity 72.4, 11.4),
**The Hall of Thanes** (ours Ironforge 43.5, 52.0; QuestieDB 27.6, 47.8). QuestieDB itself marks the Stratholme and Scarlet Enclave Forever points as unverified.

## What changed in the data (this session)
- `bis/places.json`: 9 -> 335 places (28 entrances from the journal, 278 quest givers and 20 vendors from QuestieDB and the game's vendor table, 9 by hand). Each carries `via`; conf is `approx` for the journal entrances and `classic` for QuestieDB spots.
- `bis/found_sources.json`: 288 items now have a source where ForeverDB said "not known yet" (QuestieDB 126, ForeverDungeonJournal 108, our recordings 35, the game's vendor table 10, AtlasLoot 8); each shows its origin as the small grey credit next to the source line.
- `bis.html` footer credits Questie / QuestieDB (GPL v3), ForeverDungeonJournal and ForeverMyBis (MIT).

## Left (and the next sources to try)
- **Crafted (116 level-60 picks):** the places are trainers and recipe vendors. QuestieDB's NPC table (flags, `subName` such as "Leatherworking Trainer") and the game's `SkillLineAbility`/trainer data can give these; needs a profession -> trainer mapping and a decision on which city (nearest to the player is only known in game).
- **Quest givers still without a spot** (about 57 titles) and ambiguous ones (20): often object or item starters, or Forever-new quests; ForeverMyBis `ql` and the journal's `QuestMaps.lua` (coordinates only) can fill some.
- **Reputation vendors** (10 at level 60, Theramore Expeditionary Force and similar): QuestieDB faction vendors by name; place key is the faction name, so a rule is needed (the faction's quartermaster).
- **Unknown sources (967 rows, 38 level-60 picks):** read the remaining ForeverMyBis `srcs` variants, ForeverWoWBiS `Sources.lua` (names only), ForeverCompanion `Loot.lua` boss tables; every addition via `found_sources.py` tiers with the origin named.
- **Unnamed vendors**: Captain Dirgehammer and Lady Palanseer (PvP rank vendors) have several spots; the two "N vendors" rows name no vendor.
- Raids and phases: no source has them yet either.
- Recheck after each patch: Journal tables on wago, `CollectableSource*Sparse` hotfix tables, `C_EncounterJournal.GetDungeonEntrancesForMap` (the owner's `/r2f debug ej`).
