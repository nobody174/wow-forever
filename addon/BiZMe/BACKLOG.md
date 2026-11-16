# BiZMe! Backlog (top = next)

## Now: Phase 0 (reports delivered 2026-11-15; waiting for owner approval of docs/plan-review.md)
- [x] Inventory -> docs/mrbiz-inventory.md
- [x] Plan review -> docs/plan-review.md (bigger changes listed at its top)
- [x] Addon audit -> docs/addon-audit.md
- [x] UI study (ForeverDungeonJournal) -> docs/ui-study.md
- [x] Data research -> docs/data-sources.md
- [ ] Owner: approve or change plan-review.md items 1-9; four questions answered 2026-11-15 (detour numbers still to confirm).
- [x] Probe results 2026-11-15: memory 21.2 MB (data 14.4 MB); inspect works (0.3 s, 15 items); Encounter Journal empty (confirm with `ej load`, TESTING 5.84). Details in docs/data-sources.md.
- [x] Probes written: `/r2f debug ej | mem | inspect` (TESTING 5.84-5.86); results land in R2FDB.bizProbe. Waiting for the owner's run.
- [ ] Still to test (owner or browser): `/r2f debug ej` (to be written, read-only); foreverwow.gg and forevermybis.com terms; does ForeverDB's BiS page list more than 3 alternatives; addon memory with BiZData.
- [ ] Add ledger rows to the wow-dev-support-folder findings-ledger (EJ functions seen in ForeverDungeonJournal; licences of the BiS addons; Forever trait-tree detection by posX gaps).

## Done 2026-11-15 (see ROADMAP status; owner tests 5.87-5.91)
- [x] BiZMe.lua: worn vs BiZ, reachable now, carry rule (5 / 10 levels), owned items, ranked upgrades, tooltip rank line, profiles + inspect, Guide me.
- [x] UI: Next upgrades view, Viewing as menu, Guide me button, BiZ code button, wishlist owned marks, data build line.
- [x] BiZ code R2FB1 in the addon and on the site; CharMarks.lua (Character slot marks, off until ticked); trainer places for crafted picks.

## Next (in this order)
- [ ] Owner tests 5.87-5.91; fix what they find. Taint test (5.91) decides the docked Character panel (Phase 5).
- [ ] Owner tests 5.92-5.94 (wishlist tracker, tracking foldout, docked panel); polish the panel look per docs/ui-study.md.
- [ ] Places: reputation vendors (Theramore two spots, The Watchers, Powderfuse: none in the data), 57 quest titles still without a spot (17 more placed from ForeverMyBis ql and the Dungeon Journal QuestMaps on 2026-11-16; 20 ambiguous), Ruins of Lordaeron / Hall of Thanes / Stratholme entrances to settle.
- [ ] Unknown sources left (see the count in bis-data.json; 30 more items resolved 2026-11-16 from ForeverMyBis world drops and reputation lines). What is left needs recorder data: ForeverMyBis itself says "Drop: not known yet" for 129 of them; ForeverWoWBiS / ForeverCompanion state no licence, so they stay unused.
- [ ] Pre-BiZ / BiZ / phases when raids exist (no data now).
- [ ] Load-on-demand data split: decide after the memory use is felt (14.4 MB).

## (old) Phase 1
- [x] Gap lists generated: docs/phase1-data-gaps.md (158 distinct level-60 picks: 44 unknown, 108 without place).
- [x] 28 dungeon entrances added from ForeverDungeonJournal (coordinates only, `bis/tools/dj_entrances.py`): routable level-60 picks 12 -> 43 of 433. Left: vendors, rep vendors, quest givers, entrances the journal lacks (Onyxia, AQ, Atal'Byzal, Krol'dok map id 2548).
- [x] 9 vendors placed from the QuestieDB forever snapshot (GPL, `bis/tools/questie_places.py`). Not placed: Pix Xizzix (28 rows) and Winklespark (9), Forever-new vendors QuestieDB does not know; Gaelden Hammersmith (Alterac Valley), Lhara (Darkmoon Faire, two spots); the 'N vendors' rows. Idea: have the recorder save the player's map position when a vendor window opens, so the group can place Forever-new vendors.
- [x] Offline research round (2026-11-15, docs/places-research.md): QuestieDB decoded from its .toc, the client's CollectableSourceVendorSparse table + UiMapAssignment, ForeverMyBis (MIT). Places 9 -> 335; level-60 routable picks 12 -> 195 of 433; unknown-source rows 1,718 -> 967. Left: crafted trainers/recipe vendors, reputation vendors, quest givers without a spot, entrances to settle (Ruins of Lordaeron, Hall of Thanes, Stratholme).
- [ ] Places data: extend `bis/places.json` / sources pipeline; target the level-60 best picks first.
- [ ] Unknown-source triage list (78 level-60 best picks) for the group's recorder.
- [ ] Decide the load-on-demand split (measured: data is 14.4 MB of 21.2 MB; per-class split proposed, plan-review item 6).
- [ ] Show the data build and date in the Mr.BiZ tab.

## Later
- [ ] Phase 2-5 per ROADMAP.md (break down after approval).
