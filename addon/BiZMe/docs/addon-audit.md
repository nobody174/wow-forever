# Addon audit: other BiS addons (2026-11-15)

Read-only look at `D:\World of Warcraft\_forever_\Interface\AddOns` (file lists, headers, data headers, key modules). Nothing copied, nothing run. Treated as untrusted.
Method limits: I read headers, TOC files, comments, data heads and the main modules; I did not read every line, and nothing was run in game, so behaviour claims are from code/comments.

## TL;DR
- **BIS** is a retail addon (spec ids, Interface 120100 too) with no Forever data: ignore.
- Three addons ship **per-level or per-phase BiS with sources**: ForeverMyBis (MIT, per level 10-60, faction-split, 5 MB), ForeverWoWBiS (levels + `pretop` pre-raid, generated from foreverwow.gg), ForeverLevelingBiS (scored from item data and stat models, with quests).
- **Pre-raid/phase concept exists elsewhere**: ForeverWoWBiS `pretop`, SpecBisTooltip `P1`, ForeverCompanion "Pexing 20-60" phases. Nobody has raids yet either.
- **Good ideas to take (as ideas):** worn-vs-pick score on item tooltips, "Equip best", wishlist tracker with auto-hide for owned items, Character-frame slot overlays via hooks, top-5 per slot at your level with a "how much better" figure, random-suffix item scoring from the link, a public API for other addons.
- **Licences:** only ForeverMyBis is MIT. ForeverLevelingBiS and SpecBisTooltip are All Rights Reserved; the others state nothing (= reserved). Copy no code or data.
- **Everyone** gets Forever drops the same way (site data export or recordings); no one has the client's loot tables.

## Table: addon x the nine points
| | BIS 0.8.6 | ForeverBiS beta-0.0.81 | ForeverCompanion 0.5.1 | ForeverLevelingBiS 1.3.0 | ForeverMyBis 0.2.18 | ForeverWoWBiS 2026.11.14 | SpecBisTooltip 1.1.0 |
|---|---|---|---|---|---|---|---|
| 1 Data origin | Hand "presets" of stat order per retail spec id | ForeverChanges lists, baked into one 914 KB Lua file | "Forever Companion Studio" generator (French header); Wowhead for nodes/maps; lists labelled PEXING-20..60 | `tools/scraper/scrape.py` (items, quests, 2026-11-13) + `tools/statmodel/build.py` (stat-model weights) | `web/scripts/export-addon.ts` from forevermybis.com, "client build 1.60.1.70938" | `python -m foreverbis addon` from foreverwow.gg, daily | Hand-maintained plus Wowhead exports (`datawowhead*.lua`), BiS pool "CLASSIC"; per-phase `BIS,PVE,P1` dated 04.11.2026 |
| 2 Format/size/update | Tiny; no Forever data | 914 KB `ForeverBiS_Data.lua`, schema 2 (`lists[class].phases[id].slots[]` with `source{kind,text,zone,boss}`) | `Data/*.lua` ~1.7 MB, dataVersion 113, 2026-11-11 | `Data/Items.lua` 1.6 MB (7,436 items), `Quests.lua` 0.6 MB, `ModelWeights.lua` 107 KB; localized names 4 x ~0.4 MB | `Loadouts.lua` **5.0 MB**, `Items.lua` 1.8 MB; changelog in data ("17 items with updated stats from Forever's hotfixes") | `Data.lua` **6.1 MB**, `Sources.lua` **3.3 MB** | `datasources-classic.lua` 0.6 MB + forever file |
| 3 Coverage | Retail specs only | Level 30 only (one phase `lvl30`), per class lists | Phases 20/30/40/50/60, classes x specs, plus rotations, talents, professions, AH prices | Levels 1-60 by weights; classes x specs (hunter has 4 profiles, druid 4); quests/dungeon/crafted/BoE | Levels 10-60 per spec, per faction (alliance/horde), top-8 candidates with scores (`{id, score}`) | Levels (page URLs `level-N/`) + `pretop` pre-raid; per spec/slot top 5; faction split `a:`/`h:` | Phase lists per class/spec/item; BiS vs pre-BiS marking in tooltip |
| 4 Spec detection | Retail `GetSpecialization` | Player adapter | per session + manual; remembers phase only ("class/spec follow detection + session") | `ns.Specs` in Classic tab order; main spec chosen; weapon setups | **Detect.lua**: reads the Forever Trait tree; groups node `posX` by gaps to find the three trees, then points per tree (same idea as ours) | `state.primary` from talents, changes fire `OnChange` | `GetItemTyp(class, specId, ...)` by spec id |
| 5 Source info | none | text sentence + zone + boss; dungeon icon notice | Loot.lua boss tables (180 KB), Nodes (herb/ore map) | per-item `sources={type,id,name,zoneId,level,reqLevel,side}`; **Waypoint.lua**: pins quest giver on world map / TomTom | per item `src` text + `p` (profession) + `b` (bind) | `Sources.lua`: `q/d/v/c/o` kind, name, level per itemID; **Spots.lua** grind spots on the world map; `Map.lua` | `quest;reward=7940` style tags, `unknown=unknown` |
| 6 Scoring | none (user stat order) | none | Scales module (gear scales) | `Scoring.lua` 65 KB, weight brackets per level (`upTo=9, 14, ...`), crit%/hit% terms, speed handling, profiles, user-editable weights | `Score.lua`: weighted sum (stats, armor, dps) with `lv` weights <60 and `max` at 60; reads link stats for random-suffix items; "Fit score" | `Score.lua`: site's per-slot `scores` + link stats for suffix items | n/a (list rank only) |
| 7 UI | options, minimap | Paper doll (model + one icon per slot), item list, filter bar, own Skin/Theme, dropdowns | Large frame 570x640 per list, Baganator/OpenMap optional, Ace3 | **Skins (Elwynn)** with painted frame art, band, floor; CharacterPanel docked to `CharacterFrame`; wish tracker; quest panel; API | One 94 KB UI file, `BackdropTemplate`, `DressUpModel`/`PlayerModel`, "what's new" pane, equip pane with check boxes | **Hooks `PaperDollItemSlotButton_Update`** to overlay Character slots; My BiS panel (500 wide, 34 px rows, top 5 on the right); minimap | Tooltip lines, options |
| 8 Licence/libs | none in folder | none stated | Ace3, LibDBIcon; none stated | **All Rights Reserved** (CurseForge 1719370); exposes API.md "free of charge, credit welcome" | **MIT**; site forevermybis.com | none stated; CurseForge 1754003 | **All Rights Reserved** (D4KiR); D4Lib |
| 9 Weaknesses | Wrong game flavour | Level 30 only; 914 KB; stale | French-only comments; heavy (2.5 MB, 61 files, many unrelated features) | Large and complex (UI.lua 181 KB); All Rights Reserved | 5 MB of data; sources are free-text | 9.4 MB total; data frozen to site updates; sources are text with no places | Sources unknown for many (`unknown=unknown`); no per-level |

## Per addon: steal / avoid
**BIS.** Steal: nothing. Avoid: retail assumptions.

**ForeverBiS.** Steal: the clean read-model layer over a data table (`Model.phases(route)`), "never touch SavedVariables while files execute" rule, a dungeon notice when you enter an instance with BiS drops. Avoid: free-text sources with the loot list pasted into `text` (the sample line lists every boss).

**ForeverCompanion.** Steal: phase labels as data (`phases = {id,label}`), `meta.dataVersion` + `updated` shown to the user, icon loading via `GET_ITEM_INFO_RECEIVED` (we do too). Avoid: bundling everything (professions, AH, maps) in one addon; our scope is narrower.

**ForeverLevelingBiS.** Steal (idea only): weights per level bracket; the BoE/rarity switches; **a public read-only API** so bag addons show the same numbers (we could expose `R2F_API`); wish tracker with "hide if owned"; "Best you have" tooltip line; "Equip best" in steps, only out of combat, one item at a time, no BoE auto-equip, never leaves the cursor holding an item (matches our no-combat rule). Docking to `CharacterFrame` for a panel. Avoid: skinning with painted frame art as the default (heavy, custom art pipeline); All Rights Reserved.

**ForeverMyBis.** Steal (idea; code is MIT so reuse is *possible* with the MIT notice, but our pipeline owns the data): top-8 contenders with scores per level instead of 3 (our rows are 3-deep); **faction split**; talent-tree detection from `posX` gaps (compare with our `ReadTrees`, same tree-grouping trick), "random suffix" items scored from the link; data changelog. Avoid: 5 MB of data in a single addon; site-dependent export.

**ForeverWoWBiS.** Steal (idea): `pretop` = a separate pre-raid list per spec/slot/level, `OnChange` listeners for level/talents/spec, slot overlays through `hooksecurefunc("PaperDollItemSlotButton_Update")` (taint-safe pattern), top-5 per slot at your level with a "how much better" number, "the best item is often hard to get, the next ones may be easy" as the design statement of the upgrade engine. Avoid: 9 MB of data; text sources with no coordinates.

**SpecBisTooltip.** Steal: phase-keyed tables and "BiS vs pre-BiS" wording in tooltips; the phase naming `P1`. Avoid: heavy D4Lib dependency; All Rights Reserved.

## Facts that matter for the plan
- Spec detection from the Forever trait tree is solved in more than one addon the same way (group nodes by x position). Ours (`Talents.ReadTrees`) is the same idea and the Hunter reader was fixed 2026-11-13.
- Nobody has a better source of unknown Forever drops than we do. The honest "unknown" state is a feature.
- Phases: only labels exist, since the launch; real raid phases are not out. Our data shape should only reserve a `phase` field.
- API style: ForeverLevelingBiS publishes `ForeverLevelingBiS_API` (version 2). We could publish one too (low priority, open question).
