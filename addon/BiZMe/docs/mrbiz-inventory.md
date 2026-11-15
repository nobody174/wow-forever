# Mr.BiZ inventory (2026-11-15)

What Mr.BiZ does today, read from the code and the generated data (not from the plan). Numbers measured on `bis-data.json` /
`BiZData.lua` as committed (data from 2026-11-13, ForeverDB build 70862). File and line refs are to `addon/RoadToForever/`.

## TL;DR
- Mr.BiZ already has far more than the plan assumes: **per-level lists for every level 10-60** (27 specs), spec auto-detect from talents, a
  class/spec picker (view any class), source-type filters, a per-character wishlist with Export/Import, enchant advice, upgrade arrows and a
  tooltip score line, a BiZNav arrow (Alt+click), a 3D paper doll, and a "weapons on your launch-plan route" feature.
- Real gaps: no **phases / Pre-BiZ** (the data has none; ForeverDB level 60 has no raid items at all), **routing is nearly empty at level 60**
  (12 of 433 best picks have a map place), **14% of rows have an unknown source**, no gear-vs-BiZ compare per slot, no named "viewing as"
  characters, no BiZ code (only the wishlist string), no Character-frame presence, and the data file is **3.5 MB** of Lua loaded at login.

## 1. Pipeline and data
| Piece | What it is | Notes |
|---|---|---|
| `bis/tools/foreverdb_levels.py`, `foreverdb_segments.py` | download ForeverDB's BiS page for every spec at every level (27 x 51 pages), compress to runs of levels with the same pick -> `bis/raw/levels/<class>-<spec>.json` | ~25 min, resumable, polite (1 req/s); ForeverDB stays a read-only input per the 2026-11-13 decision |
| `bis/sources.json`, `found_sources.json`, `bis/own/web_sources.json`, `recorded.json` | sources for rank 2-3 picks and for picks ForeverDB leaves unknown; `found_sources.py` fills from our recorder, ForeverDungeonJournal (read only) and hand-added web sources | credits listed in `bis/README.md` |
| `bis/places.json` | **9 places** (7 dungeon entrances, 2 NPCs/towns) with zone, map hint, x, y, confidence | the only source for the BiZNav arrow |
| `bis/quality.json`, `bis/items.json` | item colour; item table (from WCLBox since 2026-11-13) | `build_bis.py` does NOT read `items.json`: picks and scores are ForeverDB's |
| `bis/build_bis.py` | parses source sentences into `{type, label, instance, group, prof, skill, qlevel, faction, place, conf, via}`; writes `bis-data.json` + `BiZData.lua` | unknown sentence wording stops the build on purpose |
| Output shape | per spec: `build`, `weights` (text), `runs[slot] = [fromLevel, bestRow, [nextRows], note?]`, `enchants`; shared `rows` (12,543), `places`, `quality` (2,679) | a run is resolved to one level by `BiZ.SlotsAt` |

Size: `BiZData.lua` **3,524,512 bytes**, `bis-data.json` 3,074,094 bytes (the older plan text says 437 KB / 334 KB: outdated since the per-level data).
The addon `require`s all of it at login (it is in the `.toc`, `RoadToForever.toc:61`). Memory and load time in game are **unmeasured** (open question,
see plan-review item 6).

### Data coverage (measured)
- 27 specs x 17 slots x levels 10-60, best pick + next two per slot (a 3-deep list; ForeverChanges has 5-7, see `bis/foreverchanges-compare.md`).
- Rows by source type: dungeon 3,326, crafted 2,819, quest 2,220, **unknown 1,718**, world 1,532, vendor 809, reputation 109, pvp 10, **raid 0**.
- Confidence labels: classic 4,964, client 2,934, seen 2,163, unknown 1,736, clue 746.
- Best picks at level 60 (433 across specs): crafted 116, quest 114, **unknown 78**, vendor 53, dungeon 33 (Blackrock Spire 14, Stratholme 8, Dire Maul 6, BRD 2, RFK 2, Scholo 1), world 29, reputation 10.
- Share of best picks with a map place: level 20: 69/387, 30: 157/415, 40: 72/430, 50: 43/437, **60: 12/433**.
- Empty slots: at level 10 about 8 of 17 slots have no pick; at 20+ a spec has 0-3 empty slots (note text explains why).
- **No phases.** ForeverDB's level 60 list contains no raid item, so what Mr.BiZ calls level 60 is already "pre-raid". There is no BiZ vs Pre-BiZ
  distinction in the data, and nothing to label phases with until raids/phases exist.
- Spec list quirks: Feral Druid is "Feral (Bear)" only (ForeverDB's Feral page is tank-weighted); no cat list.
- Enchants: only the level-30 ForeverChanges list (`BiZ.ENCHANT_LIST_MAX = 39`); above that the tab shows ForeverDB's own enchant text per slot.

## 2. Addon logic
- `BiZ.lua` (604 lines): level (`BiZ.Level`, follows your level, steppable 10-60, saved per character), `SlotsAt`, `WeightsAt`, class/spec state,
  `OwnSpec` (talent tree with most points via `R2F.Talents.ReadTrees`, cached, `ForgetOwnSpec` on talent change), enchant state vs worn enchant,
  `EnchantTipLine`, `RouteWeapons` (weapon picks reachable at a launch-plan step), rank names (Bizzest/Bizzer/Biz/Almost biz/The Bizz),
  filters (`types[type]=false`, `known`), faction note, wishlist (`wish[itemId]={spec,slot}`, grouped by source group, Export/Import `R2FW1:id:class/spec:slot,...`),
  item quality/icon/tooltip/chat link, `Place`/`Go` (BiZNav arrow via `Plan.Waypoint`).
- `GearScore.lua` (406 lines): score = sum(stat x weight) using ForeverDB's printed weights parsed from `spec.weights` text; the "Upgrade arrows" tweak adds a tooltip
  line (`BiZ score 34.2 (+5.1 vs equipped)`) and up/down markers on bag items; class armor/level gating; weapon skill not checked; `/r2f debug gear`.
- `QuestWeapons.lua` (147 lines): quest-reward weapons on the launch-plan steps (273 weapons, Wowhead-derived; class weapon table).
- `Nav.lua` (725 lines) + `Plan.Waypoint`: the BiZNav arrow, `/bizway`, TomTom stand-in. `Plan.lua`/`Progress.lua`: launch plan steps with levels and quest ids.
- `Recorder.lua` (205 lines): records loot / vendor / quest windows into `R2FDB.recorder`; merged by `bis/tools/recorder_import.py`.
- Saved data: `R2FCharDB.biz = {class, spec[class], level, types, known, wish}`; account `R2FDB.bizQuality` cache.
- Slash: `/biz`, `/mrbiz` (opens the tab; `/biz wish` opens the wishlist).

## 3. UI (`UI/BiZ.lua`, 727 lines, page 650 x 540 in the R2F main window)
- Class and spec drop buttons (own `UI.ContextMenu`, no UIDropDownMenu: taint), level -/+ (click number = follow own level), view switch Best in slot / Wishlist.
- Paper doll: 3D `PlayerModel` (drag to turn), 17 slot buttons around it (best pick icon in quality colour), source-type checkboxes + "known only".
- Right panel: selected slot's best + next two with source, confidence badge, score, "% behind", wishlist switch, enchant block with "you wear" state; tooltips = game item tooltip + rank line + route hint.
- Wishlist view: grouped by source group, biggest first; Export / Import with the site's `R2FW1:` string.
- Look: R2F theme system (Deco, themed plates), **not** Blizzard templates; Widgets are our own (`UI/Widgets.lua`, `UI.CheckButton`, `UI.ContextMenu`, `UI.TryTemplate`).
- No Character-frame attachment anywhere in the addon (grep: `CharacterFrame` only appears in `GameplayExtras.lua` to read the title text).

## 4. Site (`bis.html`, 829 lines, JS-rendered from `bis-data.json`)
Pickers by class/spec/level (`?lvl=39`, `#class/spec`), source-type chips, quality via WCLBox (cached), score, confidence badge, rank 2-3 with % behind, wishlist per
character name in `localStorage` (`wf-bis-wish-v1`), same `R2FW1:` export/import, Wowhead tooltips, credits for ForeverDB + Wowhead (WCLBox credit where it shows).

## 5. Tests and docs that already cover it
`addon/tests/run_tests.py` has ~174 BiZ-related lines (data shape, slot resolution, filters, wishlist round-trip, route weapons, GearScore on stubs).
`docs/professions-bis.md` describes the site page; `bis/README.md` the refresh; `bis/DATA_SOURCES.md` the source terms.

## 6. Gaps against the BiZMe idea (what is really missing)
| Idea | State today |
|---|---|
| Auto-detect class/spec | **Done** (`OwnSpec`), but only the highest-point tree; no hybrid-aware roles (cat vs bear, Ret vs Holy) and no "manual override sticks across respec" notice |
| Viewing as alts/friends | **Partly**: any class/spec/level can be viewed; no named profiles, no remembered "who", no use of another character's actual gear |
| BiZ / Pre-BiZ / per-phase | **Missing**, and the data cannot support it yet (no raids, no phases in ForeverDB) |
| Best available at level | **Done by data** (levels 10-60 from ForeverDB); no computed lists needed |
| Source filters | **Done** (types incl. raid, reputation, pvp, crafted); missing: "reachable now" (level/faction/rep/profession-aware) |
| Per-character wishlist | **Done**; no tracker on screen, no "got it" auto-tick, Export is wishlist-only |
| Next best upgrade obtainable now | **Missing**: GearScore compares one item to the worn one; no engine that picks the best reachable item per slot, no "replaced soon" rule |
| Route via BiZNav | **Arrow to one source** exists; only 9 places, 12/433 at level 60; no ranked route list |
| BiZ codes for Discord | **Missing** (only `R2FW1` wishlist); site has no equivalent link for a spec+level+gear state |
| Native Blizzard look / Character tab | **Missing**; UI is our theme system |
| Gear vs BiZ compare | **Missing** per slot (only enchants are compared with the worn item) |
| Unknown source honesty | **Done** (type `unknown`, confidence badge, "known only" filter) |
