# BiZMe! Roadmap

## Phase 0 — Inventory, research & audit
(a) Inventory what Mr.BiZ already does (BiZ.lua, GearScore.lua, QuestWeapons.lua, Plan.lua, Nav.lua, bis/ pipeline) -> docs/mrbiz-inventory.md.
(b) Audit the local BiS addons and the Forever data situation. Output: docs/addon-audit.md and docs/data-sources.md.
Exit: we know the gaps vs Mr.BiZ, what Forever changed vs Classic, which UI to copy, and what to reuse.

## Phase 1 — Data contract
Reuse bis-data.json / BiZData.lua. Add what is missing: Pre-BiZ and per-phase lists, stat weights per spec for computed level lists, richer source data for routing, unknown/unverified flags.
Extend build_bis.py to emit BiZMe_Data Lua (load-on-demand).

## Phase 2 — Viewer
Class/spec auto-detect + override + "viewing as". Per-slot list with top alternatives, source filter chips, native Blizzard look (Character frame tab). Site BiS page from same JSON.

## Phase 3 — Wishlist & upgrade engine
Per-character wishlist, gear vs BiZ comparison, tooltip lines, upgrade arrows, BiZ GearScore, "next best upgrade obtainable now".

## Phase 4 — Route
Source -> location/quest/dungeon mapping, ranked route list, BiZNav waypoints, in-Launch-Plan hints.

## Phase 5 — Polish
3D character preview with slots around it, themes/skins, BiZ code sharing, user-reported data flow.
