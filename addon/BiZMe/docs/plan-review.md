# BiZMe! plan review (2026-11-15)

Reviewed against the code (`docs/mrbiz-inventory.md`), the 2026-11-13 decisions (`BACKLOG.md` 5.4, `bis/DATA_SOURCES.md`) and the research
(`docs/addon-audit.md`, `docs/ui-study.md`, `docs/data-sources.md`). Role hats: Project Manager (order, scope), Code Reviewer (conflicts with code and hard rules), Critic.

## Owner answers (2026-11-15)
1. Upgrade gain = score difference, minimum 5% to show an arrow: yes.
2. Detour threshold: owner asked what it means; explained (items replaced soon are not worth a trip). Numbers (5 levels on route, 10 for a trip) awaiting confirmation.
3. Friends' gear: **read by inspecting the targeted character** at that moment, not from a pasted code. BiZ code no longer carries gear. Needs a Forever inspect test
   (`NotifyInspect` / `INSPECT_READY`, range, throttle, out of combat only); profile stores a dated snapshot.
4. WCLBox for stat checks: yes (credit, 5 req/s, 5 min cache).

## For you to approve (the bigger changes)
1. **Drop "computed best-available-at-level lists" (and stat-weight list building).** Mr.BiZ already has ForeverDB's pick for every level 10-60. Computing our own
   lists is the "own ranker" you declined on 2026-11-13. Keep the existing `GearScore` only to *compare your worn item with a pick*.
2. **Pre-BiZ / per-phase is parked, not Phase 1.** ForeverDB level 60 contains zero raid items, so today's level-60 list already *is* Pre-BiZ. There is no phase data to
   build from. Do: relabel level 60 as "Pre-BiZ (no raids yet)" in the UI, keep the data shape ready (`phase` key on runs), build real BiZ vs Pre-BiZ when raids exist
   (watch ForeverWoWBiS `pretop`, ForeverMyBis, ForeverCompanion phases for when others start).
3. **Reorder: Phase 3 (gear vs BiZ, upgrade engine) goes before the Blizzard-look rework and before routing.** It is the BiZMe value for you and your group, runs on data we have, and the
   routing data is not there yet (12 of 433 level-60 best picks have a map place).
4. **Routing needs a data phase first (new Phase 1b: places).** Add dungeon entrances, vendors, quest givers and rep vendors to `bis/places.json`
   from sources we may use (AtlasLoot GPL, CMaNGOS/Questie GPL coordinates, our recorder, in-game `C_Map`/EJ read-outs). No ForeverDungeonJournal copying (no licence text = all rights reserved).
5. **"Character frame tab" becomes "a panel docked to the Character frame", not a real tab.** Adding a tab means calling `PanelTemplates_*` on `CharacterFrame` and writing
   `numTabs`/`Tabs` fields = writing into game-owned tables (hard rule 4). ForeverLevelingBiS and ForeverWoWBiS both dock a panel / hook slot buttons with `hooksecurefunc`
   instead. Plan: slot overlays via hooks + a docked side panel + a button. Decide after a taint test in game (TESTING item).
6. **Split the data (load-on-demand): measured 2026-11-15: the data is 14.4 MB of the addon's 21.2 MB.** A per-class split would hold about 1.6 MB for a single-class player. Recommended in Phase 2 (not urgent); original text: **no longer "optional later".** `BiZData.lua` is 3.5 MB loaded at login (the plan assumed ~440 KB). Measure memory/load time first
   (one in-game `collectgarbage("count")` before/after, 5 minutes), then decide. Cheap first step: lazy-load by class from a `LoadOnDemand` data addon folder inside the same zip.
7. **BiZ code = one new format, versioned, replacing `R2FW1` only by extending it** (`R2FB1:` = class/spec, level, wishlist, optional worn-gear ids). Wishlist import stays valid.
   Site gets a matching decoder so a Discord link `bis.html#code=...` opens the same state.
8. **Add (not in plan):** "already have it" detection (worn/bags/bank) and auto-tick of wishlist items; a small on-screen wishlist tracker; tooltip line "BiZ #2 for Hunter/BM" on any item
   (the score line exists; the rank line does not); unknown-source triage list for the owner's group (what to go record), because the Recorder already exists.
9. **Do not add:** 3D preview "slot icons around it" (already there), a second scoring model, skins before Phase 2 is confirmed in game, any backend.

## Plan items against the code
| Plan item | Verdict | Why / change |
|---|---|---|
| Auto-detect class/spec from talents | **Already built** (`BiZ.OwnSpec`) | Add: hybrid roles (cat vs bear, Ret/Holy), a visible "detected: X / override" line, re-detect on respec (`ForgetOwnSpec` is wired) |
| "Viewing as" selector | **Extend** | Class/spec/level viewing exists. Add named profiles in `R2FDB` (account-wide: name, class, spec, level, optional pasted gear). Friends' gear can only come from a pasted BiZ code (no inspect needed; inspect is out of scope, combat-safe but throttled) |
| BiZ / Pre-BiZ / per-phase | **Park** (item 2 above) | No phase data |
| Computed best at level | **Drop** (item 1) | Per-level data exists |
| Source filters | **Mostly built** | Missing "reachable now" = level, faction, profession skill (from `skill`), reputation standing (needs rep API read), dungeon level range. Build as a pure function in `BiZ.lua` with tests |
| Wishlist per character | **Built** | Add tracker, auto-tick, share via BiZ code |
| Next best upgrade obtainable now | **New, core** | Design below |
| Route via BiZNav | **Partly built** (arrow to one source) | Needs places data (item 4), then a ranked list that reuses `Plan.Waypoint`; no TSP, agreed |
| Discord BiZ codes | **New** | Item 7 |
| Native Blizzard look | **Later, scoped** | Item 5, after the engine. Our `UI.*` widgets stay the thin layer; swap them for templates behind the same calls |
| BiZ GearScore | **Built** (`GearScore.lua`) | Keep; unit-test the stat key coverage against Forever items (`/r2f debug gear`) because stat names differ in places (hit/crit split, spell damage vs spell power) |
| 3D preview | **Built** | Nothing to do |
| Unknown source honesty | **Built** | Keep; add the triage list |

## The upgrade engine (proposal, nothing built)
Per slot, from the data for the viewed level (`BiZ.SlotsAt`): candidates = best + next two (3 deep; if wanted, deeper lists need ForeverChanges data, see data-sources).
1. **Eligible** now: required level <= your level (+ allow items up to N levels ahead for the "carry" rule), faction, class armor/weapon rules (reuse `GS.CanWear`, `QW.CanUse`), profession skill, not an unknown source unless "include unknown" is on.
2. **Obtainable now** (`reachable`): dungeon level range, quest level, vendor/rep (rep standing read from the game), crafted (you have the profession and skill, or the materials are cheap).
3. **Gain** = BiZ score of the candidate minus the worn item, using ForeverDB's own printed score where the data has it, `GearScore` otherwise.
4. **Carry rule** (your rule): the candidate is "worth a detour" if it stays the pick for >= 5-10 more levels. Computable from the runs: `runs[slot]` already says from which level a pick starts, so "how long is this item the best/next" is a lookup; no extra data.
5. Output: ranked list by (gain x carry), each with source, "obtainable: yes/after level N/needs rep", and a BiZNav button.
Open design question for you (item below): do you want gain measured in score or in "slots better than worn"?

## Order I suggest
0. Phase 0 (this folder): done when you approve this review; research docs delivered.
1. **Phase 1 Data**: (a) places + sources coverage (`bis/places.json`, unknown triage), (b) load-on-demand measurement and split decision, (c) keep refresh pipeline current (ForeverDB build 70862 vs live 70938: stale picks list in `bis/own/rerank-review.md`). No new ranking data.
2. **Phase 2 BiZMe core** (addon only, no look changes): worn-vs-BiZ per slot, "already have it", reachable-now, upgrade engine, wishlist tracker + auto-tick, profiles, tooltip rank line.
3. **Phase 3 Share**: BiZ code + site decoder + Discord-friendly text.
4. **Phase 4 Route**: ranked route list over places data, BiZNav waypoints, Launch Plan hints.
5. **Phase 5 Look**: docked Character-frame panel, Blizzard templates/atlases per `docs/ui-study.md`, only after a taint test.
6. **Later**: Pre-BiZ/BiZ/phases when raids exist; own recordings back to AtlasLoot (GPL, the open question in `bis/DATA_SOURCES.md`).

## Conflicts and risks found
- **Hard rule 4** vs Character tab (item 5). **Hard rule 1**: all data changes go through `build_bis.py`; Phase 1 places must be added to `bis/places.json`/sources, never to `BiZData.lua`.
- **Decision 2026-11-13** (keep ForeverDB, no own ranker) vs "computed lists" (item 1).
- **Freshness**: ForeverDB lists are for build 70862, live is 70938; 526 changed and 544 new best picks vs WCLBox (`bis/own/rerank-review.md`). Upgrade advice built on stale picks is the biggest correctness risk; show "data from build X" in the tab.
- **Licences**: ForeverLevelingBiS, SpecBisTooltip: All Rights Reserved; ForeverDungeonJournal, ForeverBiS, ForeverCompanion, ForeverWoWBiS: no licence given (treat as reserved). Only ForeverMyBis is MIT. Read for ideas; copy nothing.
- **Tests**: every Phase 2 function is pure Lua over the data; add them to `run_tests.py` before UI.
- **Memory**: 3.5 MB Lua tables stay in RAM for the whole session (item 6).
- **Spec detection** reads `C_Traits` through our Talents module; if the owner's `/r2f talentcheck` shows a tree misread, spec detection is wrong too. Hunter fixed in 0.87.2/0.87.3.

## Questions for you
1. Upgrade gain: score difference, or "number of slots better than worn"? (I suggest score with a minimum 5% gain to show an arrow.)
2. "Detour" threshold: 5 levels or 10 for a dungeon / quest chain item? (I suggest 5 for a place on your route, 10 for a trip.)
3. Friends' gear: pasted BiZ code only (suggested), or also inspect when you target them?
4. OK to read the live item facts from WCLBox (open API, credit) for stat checks, instead of waiting for a ForeverDB refresh?
