# BiZMe! roadmap (inside Mr.BiZ)

## Phase 0 — Inventory, plan review, research
(a) Inventory current Mr.BiZ (BiZ.lua, GearScore.lua, QuestWeapons.lua, Plan.lua, Nav.lua, bis/ pipeline, bis.html) -> docs/mrbiz-inventory.md.
(b) Review this plan against the code -> docs/plan-review.md (changes welcome).
(c) Audit BIS, ForeverBiS, ForeverCompanion, ForeverLevelingBiS, ForeverMyBis, ForeverWoWBiS, SpecBisTooltip + UI study of ForeverDungeonJournal -> docs/addon-audit.md, docs/ui-study.md.
(d) Forever data research (item stat changes vs Classic, dungeon/encounter journal API, trusted source data) -> docs/data-sources.md.
Exit: gaps vs current Mr.BiZ known, plan adjusted, owner approves.

## Phase 1 — Data additions
Pre-BiZ and per-phase lists, stat weights per spec (computed level lists), richer source data for routing, unknown/unverified flags. Extend bis/build_bis.py; no hand-edited generated files.

## Phase 2 — Viewer and look
Auto-detect + override + "viewing as", per-slot top alternatives, source chips, native Blizzard look (Character frame tab). Site bis.html stays in step.

## Phase 3 — BiZMe: wishlist and upgrade engine
Per-character wishlist, gear vs BiZ compare, tooltip lines, upgrade arrows, BiZ GearScore, "next best upgrade obtainable now".

## Phase 4 — Route
Source -> location/quest/dungeon mapping, ranked route list, BiZNav waypoints, Launch Plan hints.

## Phase 5 — Polish
3D character preview with slot icons around it, skins, BiZ code sharing, user-reported data flow.
