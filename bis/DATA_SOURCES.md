# Where Forever item and loot data comes from (research, 2026-10-17)

Question: which databases and addons carry the most up-to-date WoW Forever loot, vendor and quest data, what are they allowed to be used for,
and how do we, a group of three, get as much of it as possible without depending on anyone staying alive. Method: read the pages, licenses and
repositories (not the marketing text), then test each source against the 133 best picks of Mr.BiZ at level 30.

## The shape of the problem

* The game client carries **what an item is** (stats, level, recipes, reagents) but **not where it drops**. Loot tables, vendor stock and quest
  rewards live on Blizzard's servers (checked: no loot, vendor or Encounter Journal tables in this client; the client's own `questcache.wdb`
  holds only the quests this PC has seen).
* So every site and addon gets **Forever-new** drops the same way: **players record them** (ZugZugDB says "NPC, quest and object data comes from
  player recordings"; Forever Guide has a "record loot not in any database" feature; ForeverCodex pools recipes from its users) and a few
  people type the results into lists (ForeverChanges, AtlasLoot's `data-forever.lua`).
* **Old (Classic) content is solved**: the open CMaNGOS / VMaNGOS data (GPL v2) is what almost everyone uses, labelled "Classic data".
* Therefore nobody has a complete, authoritative Forever list. The freshest ones are the ones with the most players recording. A group of three
  cannot out-record them; it can **read what is open, record what it sees, and keep the pipeline re-runnable**.

## The sources

| Source | What it has for Forever | Licence / terms | Freshness (2026-10-17) | Can we use it? |
|---|---|---|---|---|
| **Game client (DB2)** via wago.tools or our own CASC read | items, stats, recipes, reagents, factions, maps | Blizzard's game data; we publish our own computed numbers | the beta build | **Yes, the base.** Done (M0) |
| **CMaNGOS classic-db** | Classic drops (with group chances), vendors, quest rewards, pickpocket, chests | GPL v2 | 1.12 data, repo updated 2026-09-23 | **Yes, credit + licence note.** Done (`classic_sources.py`) |
| **AtlasLoot Continued** (installed in the beta client) | Forever dungeons with bosses, npc ids, levels, loot per boss (35 zones, 3,617 items), PvP, crafting, collections; Factions still empty | **GPL v2** (LICENSE in the addon) | v12488, updated 2026-10-15, community maintained | **Yes, credit + licence note.** Importer done (`atlasloot_import.py`); lifted coverage of the 133 picks from 106 to 118 |
| **QuestieDB** `forever` branch (Questie, GPL v3) | quests, NPCs, objects, items for Forever, with its own validators | GPL (Questie); the QuestieDB repo shows no licence field | pushed 2026-10-17 | **Read only for now.** Its own `docs/forever-data.md` says the Forever data is the Era data with converted coordinates and "new entities are not provided", so it does not add Forever-new loot. Useful for coordinates, quest givers, vendor positions |
| **ForeverDB** (what Mr.BiZ copies today) | best-in-slot lists with sources ("Classic data / Forever client / Seen in Forever / Clue") | robots.txt and llms.txt allow assistants; no explicit licence | updated with each build (1.60.1.70425 on 2026-10-16) | **Test oracle only** (decision 2026-10-17) |
| **WCLBox** (wowforever.wclbox.com) | items, item sources, dungeons, quests, BiS | an open read-only JSON API (`/api/open/v1`, CORS), asks to be cited by name and URL; data from the game client | live | **Allowed and offered**, but the API only does item search and tooltips; sources are on web pages. Cite if we use it |
| **ZugZugDB** | items, spells, zones from the client; NPC / quest / object data from player recordings; a CSV of all records | terms forbid scraping, walking the id space and bulk copying; Classic data credited under GPL v2 | live | **No scraping.** Link and credit only |
| **Wowhead Forever** | item pages with "dropped by / sold by / reward from"; tooltip API | terms could not be read (403/404); item pages answer 403 to scripts | live | **Not as a pipeline input.** Our one-time tooltip pull (11,503 ids) is finished; do not repeat it. Credit stays on the site where its tooltips show |
| **Forever Guide** (CurseForge, 70k downloads) | 22,000 items, 35 dungeons with chances, 800 class quests, 404 rares, 2,495 recipes, loot recorder | **All Rights Reserved** | updated daily | **No.** It combines the same sources (Forever client, QuestieDB, ForeverChanges, Wowhead, WoWSims, cmangos) and records loot; we cannot copy it |
| **ForeverCodex / ItemQuester Forever / ForeverArtisan** | crowd-sourced recipes, quest and profession info | All Rights Reserved / unspecified | daily | **No** (ideas only) |
| **Metaforge, WoWTBC.gg** | item sets, dungeon indexes (WoWTBC.gg page shows no drops) | no terms found | live | Not needed |
| **ForeverChanges** | loot lists and BiS pages, the base of several addons | 403 to scripts, no terms read | live | Same as ForeverDB: oracle only |
| **Our own recorder** (to build) | exactly what the three of us see: loot, vendor stock, quest rewards, reputation vendors | ours | as fresh as we play | **Yes. This is the independent part.** |

## Result at level 30 (the 133 distinct best picks of Mr.BiZ)

* Sources found from open data alone: **118 of 133** (Classic 66, crafting 40, AtlasLoot's Forever dungeons adds 12 more and overlaps the rest).
* Still unknown: **15**, all Forever-new quest rewards and reputation vendors (Theramore Expeditionary Force, Booty Bay, Blackfathom Deeps
  pieces, "where it comes from isn't known yet" entries). These are what the recorder is for.

## Decision (owner's rule: credit in the README, never depend on anyone)

1. **Primary inputs:** the game client, CMaNGOS, AtlasLoot Continued's data file. All three are open (Blizzard data / GPL v2) and **snapshotted
   into our repo's cache**, so nothing breaks if a site stops updating; refresh = re-run a script when the addon or dump updates.
2. **Own recordings** fill the rest, and our recorder merges the three players' files.
3. **Websites are checks, not inputs** (ForeverDB, ForeverChanges, Wowhead, WCLBox). No scraping of sites whose terms forbid it.
4. **Credits** go in the README and on the site's Mr.BiZ credit line: Blizzard (game data), CMaNGOS / VMaNGOS contributors (GPL v2),
   AtlasLoot Continued authors (GPL v2), plus the sites we compare against. GPL data we redistribute keeps its licence note.
5. **Refresh rhythm:** on release day (4 to 5 November) and after each hotfix build: DB2 pull, AtlasLoot re-import, recorder merge, validation report.

Open question for the owner: AtlasLoot's maintainers add Forever data as players report it, so its file is the best open sample of what the
community knows; its `Factions` module for Forever is still empty. We should watch it, and our recorder's output could be offered back to it
(GPL v2 lets us contribute).
