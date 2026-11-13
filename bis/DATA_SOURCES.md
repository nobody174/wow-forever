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
| **WCLBox** (wowforever.wclbox.com) | all Forever items (21,855 at build 1.60.1.70888), English and Chinese names, tooltips, sets; item search and tooltips only, sources are on web pages | open read-only JSON API (`/api/open/v1`, CORS `*`, no login). **Terms read 2026-11-13** (their docs, "usage conventions"): credit the data source on your page as 新手盒子·魔兽世界无限数据库, best with a link to the item's own page; limit 5 requests per second per IP (burst 20, then 429); responses are cacheable for 5 minutes; for the full data page with `limit=100` inside the rate limit; icons can be hotlinked, cache them yourself for heavy traffic | live | **Yes, as an input**, with the credit above. `auction-house.html` searches it live for item names |
| **ZugZugDB** | items, spells, zones from the client; NPC / quest / object data from player recordings; a CSV of all records | terms forbid scraping, walking the id space and bulk copying; Classic data credited under GPL v2 | live | **No scraping.** Link and credit only |
| **Wowhead Forever** | item pages with "dropped by / sold by / reward from"; tooltip API; talent and ability lists | **Read in Chrome 2026-11-13.** robots.txt: 28 AI and scraper user agents (incl. ClaudeBot, anthropic-ai, Claude-Web, GPTBot, CCBot, Scrapy) are barred from the whole site; for everyone else `/list`, `/search`, `/random` and `/account` are off limits, Crawl-delay 1. Terms = the ZAM / Fanbyte EULA (corp.fanbyte.com/legal/terms, updated 2025-05-14): a personal, limited, non-commercial licence; no copying, reproducing, distributing or derivative works of the Service; no commercial use or use for a third party's benefit; no circumventing protections. No explicit scraper clause found | live | **Display and single lookups only.** Show it the way it offers (its `tooltips.js` and item links, credit stays on the page), and look things up one at a time in a browser when the owner asks. No bulk pulls and no id walking; prefer WCLBox for item facts. Existing Wowhead-derived data (the 11,503-id tooltip pull, `quality.json`, trainer and talent lists) stays under review, see "Revision 2026-11-13" below |
| **Forever Guide** (CurseForge, 70k downloads) | 22,000 items, 35 dungeons with chances, 800 class quests, 404 rares, 2,495 recipes, loot recorder | **All Rights Reserved** | updated daily | **No.** It combines the same sources (Forever client, QuestieDB, ForeverChanges, Wowhead, WoWSims, cmangos) and records loot; we cannot copy it |
| **ForeverCodex / ItemQuester Forever / ForeverArtisan** | crowd-sourced recipes, quest and profession info | All Rights Reserved / unspecified | daily | **No** (ideas only) |
| **Metaforge, WoWTBC.gg** | item sets, dungeon indexes (WoWTBC.gg page shows no drops) | no terms found | live | Not needed |
| **ForeverChanges** | loot lists and BiS pages, the base of several addons | 403 to scripts, no terms read | live | Same as ForeverDB: oracle only |
| **Our own recorder** (to build) | exactly what the three of us see: loot, vendor stock, quest rewards, reputation vendors | ours | as fresh as we play | **Yes. This is the independent part.** |

## Result at level 30 (the 133 distinct best picks of Mr.BiZ)

* Sources found from open data alone: **118 of 133** (Classic 66, crafting 40, AtlasLoot's Forever dungeons adds 12 more and overlaps the rest).
* Still unknown: **15**, all Forever-new quest rewards and reputation vendors (Theramore Expeditionary Force, Booty Bay, Blackfathom Deeps
  pieces, "where it comes from isn't known yet" entries). These are what the recorder is for.

## Decision (revised 2026-11-13 by the owner)

The first version of this section said "never depend on anyone" and "websites are checks, not inputs". The owner dropped that for this project:
**use other people's databases when their terms allow it, and credit them.**

1. **Use a site as an input when its terms and robots.txt allow it.** Read them in a browser (the sandbox cannot), write what they say in the
   table above, stay inside the rate limit and cache rules, and say where the data came from.
2. **Credit every source** in the README and on the page where its data shows (name and link; use the wording the source asks for).
   GPL data we redistribute keeps its licence note. AHledger's link stays wherever its prices show.
3. **Prefer sources that offer open access:** WCLBox (item API), AHledger (prices), wago.tools (game client tables), CMaNGOS and AtlasLoot (GPL),
   then the game client itself. Snapshotting open data into the repo is still good practice, but it is no longer a rule.
4. **Sites that do not offer data access (Wowhead, ForeverDB, ForeverChanges, ZugZugDB)** are used the way they offer: their embeds and links,
   and single lookups when the owner asks. Dropping our own rule does not change what their terms say; no bulk pulls, no id walking, no scraping
   where the terms or robots.txt forbid it.
5. **Own recordings** still fill what nobody publishes (drops, vendors, quest rewards), and our recorder merges the three players' files.
6. **Refresh rhythm:** on release day and after each hotfix build: DB2 pull, AtlasLoot re-import, recorder merge, validation report.

### Revision 2026-11-13: Wowhead-derived data already in the repo

`bis/items.json` and `quality.json` (item quality, level, stats of about 11,000 older items), `TrainingData.lua` (trainer-sold spells) and the talent
lists came partly from Wowhead's tooltip API and ability lists. The numbers are Blizzard's game data and we cross-checked them against the client,
but Wowhead's terms are non-commercial and no-copy. Done 2026-11-13 for items: `bis/items.json` and `quality.json` now come from WCLBox (`wclbox_pull.py`, `items_build.py`), the runtime item lookups
in bis.html and professions.html use WCLBox, and the three Wowhead item tools (`wh_tooltip_pull.py`, `wh_quality.py`, `wh_items.py`) are gone. Wowhead is
still used for talent trees, trainer lists, enchant lists and quest-reward weapons (`wh_quest_weapons.py`). If the site ever carries ads or paid
access, drop whatever still comes from Wowhead first.

Open question for the owner: AtlasLoot's maintainers add Forever data as players report it, so its file is the best open sample of what the
community knows; its `Factions` module for Forever is still empty. We should watch it, and our recorder's output could be offered back to it
(GPL v2 lets us contribute).
