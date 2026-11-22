# BiZMe! roadmap (inside Mr.BiZ)

Revised 2026-11-15 after the code review (`docs/plan-review.md`; the bigger changes await owner approval). Mr.BiZ already has per-level lists (10-60),
spec auto-detect, filters, wishlist, upgrade arrows and a BiZNav arrow: see `docs/mrbiz-inventory.md`.

## Status 2026-11-15 (owner: "follow the plan until all are done")
Done and released in addon 0.88.0 (tests 5.84-5.94 are in addon/dev/COMPLETED_TESTING.md unless still listed in TESTING.md): Phase 1 data (places, sources), Phase 2 core (Next upgrades, Viewing as with inspect, tooltip rank line, wishlist owned marks), Phase 3 BiZ code, Phase 4 first route (Guide me), Phase 5 first step (Character slot marks).
Open: taint test of the Character marks, docked panel, wishlist on-screen tracker, load-on-demand split (measured 14.4 MB of 21 MB; deferred), Pre-BiZ/phases (no data), more places (reputation vendors, quest givers without a spot).

## Phase 0 - Inventory, plan review, research (done 2026-11-15, awaiting approval)
mrbiz-inventory.md, plan-review.md, addon-audit.md, ui-study.md, data-sources.md. Exit: owner approves plan-review.md.

## Phase 1 - Data and measurements (no new ranking)
(a) Places: grow `bis/places.json` and source coverage so level-60 picks can be routed (12 of 433 today); unknown-source triage list.
(b) Measure the 3.5 MB BiZData in game; decide on a load-on-demand split.
(c) `/r2f debug ej` read-only test (does the client's Encounter Journal give loot / entrances?).
(d) Refresh picks to the live build when ForeverDB moves (`bis/README.md`); show the data build in the tab.

## Phase 2 - BiZMe core (addon logic first, then UI)
Worn-vs-BiZ per slot, "already have it", reachable-now filter, next-best-upgrade engine (carry rule from the runs), wishlist tracker with auto-tick, named "viewing as" profiles (friends' gear read by inspecting the target, stored as a dated snapshot),
tooltip rank line, hybrid roles in spec detection. Pure Lua functions with tests before UI.

## Phase 3 - Share
`R2FB1:` BiZ code (class/spec, level, wishlist; no gear), site decoder in bis.html, Discord-friendly text. `R2FW1` stays valid.

## Phase 4 - Route
Ranked upgrade list, BiZNav waypoints over the places data, Launch Plan hints. No TSP.

## Phase 5 - Look
Docked Character-frame panel + slot overlays via hooks (not a real tab: hard rule 4), Blizzard templates per `docs/ui-study.md`, after a taint test.

## Parked
- Pre-BiZ / BiZ / per-phase lists: ForeverDB level 60 has no raids, so level 60 is already Pre-BiZ; build the split when raids or phases exist (reserve a `phase` field).
- Computed best-at-level lists / own stat weights: dropped (owner decision 2026-11-13, no own ranker).
- 3D preview: already built.
