# Backlog

Open work only (Shape B: the active todo list). Done items live in [CHANGELOG.md](CHANGELOG.md); someday ideas in
[ROADMAP.md](ROADMAP.md); what needs in-game testing in [addon/dev/TESTING.md](addon/dev/TESTING.md).

## 0. Launch follow-ups (launch was 2026-11-04; open ones only)
The one page to follow: [docs/launch-day.md](docs/launch-day.md).
1. The launch-day data refresh did not happen: see section 5 (overdue since 2026-11-04). (Beta backup / Setup Hunter: done, owner is playing on the release client.)

4. **Ground markers (`/wm`)**: confirmed working by the owner 2026-11-22 (`/wm 8` = skull; other numbers too). Left: add macros/coordinates for the Hunter trainer and the general goods vendor in the Skyborne starting zone.

## 0b. Themes: follow-ups after the 0.76.0 test
1. **Other tabs per theme** (Talents, Gear, Macros, Tweaks): pilot on Gear started 2026-11-22 (`Deco.TabPanel`, TESTING 5.103); Talents, Macros and Tweaks wait for the owner's feedback. Original note: they sit on each theme's page plate but are still the old layouts. Redesign each to match its theme's Home once the Home layouts are confirmed in game.
2. **Frost & Void**: the ring only shows the last 30 days; the "Your journey" checklist and extra sidebar entries (Professions, Reminders, Settings) of the mockups are not built (no matching pages). Theme settings panel (effects level, text size, high contrast, profiles, day / night) of theme_picker.png is not built either.
3. **Hover preview** in the gallery (the mockup previews on hover; ours previews on click with Keep / Revert).

## 1. Bugs
1. **RankedBoost, level 30:** applied 2026-11-22 for Restoration Druid and Beast Mastery Hunter; the owner left Arcane Mage, Fire Mage and Assassination Rogue as they are (RankedBoost would swap Wand Specialization / Arcane Geometry, Burning Soul -> Accelerant, Venom -> Relentless Strikes). Level 60 is skipped by `builds_from_rankedboost.py` (Wowhead owns it). `--only "<title part>,..."` applies a subset.
None else open (talent-tree drift fixed 2026-11-07; before each release run `python addon/tools/gen_talent_data.py --drift`).

## 2. Addon
1. **Talents tab follow-ups** (0.54.0 is built, ADDON_PLAN 20): re-run `python addon/tools/gen_talent_data.py` whenever Wowhead changes the trees or builds.html gets a build.
4. **More countdowns** on request (Timers.TRACK). Pet / repair / rested XP / food / Walk on Air / Seal / Slice and Dice reminders are all shipped (CHANGELOG 0.62.0 to 0.66.0).
5e. **Copy beta settings to release** (owner): found 2026-10-16 in `<WoW folder>\_classic_beta_\WTF\<Account>\` (only the beta client exists there yet). Account level: `edit-mode-cache-account.txt` (Edit Mode layouts, 11 KB), `bindings-cache.wtf` (keybinds), `config-cache.wtf`, `macros-cache.txt`, `character-list-order.txt`, `SavedVariables\` (addon settings, incl. RoadToForever). Per character (`70\<Name-Surname>\`): `layout-local.txt`, `edit-mode-cache-character.txt`, `bindings-cache.wtf`, `click-bindings-cache.txt`, `config-cache.wtf`, `macros-cache.txt`, `chat-cache.txt`, `AddOns.txt`, `SavedVariables\`. To copy when the release client exists: same folder shape under its own WTF; rename the character folders to the release realm's names. Nothing was copied or changed.
5d. **Rested XP icon**: owner keeps it. It is already off until ticked (Tweaks > Class icons); nothing to change.
5. **Buff "upper display"**: built (Buffs.lua). The aura probe (TESTING 7.12) showed the game hands out your buffs readably out of combat; what it does in a fight / in a dungeon is still to be sent, the reminder stays silent when the list is unreadable.
8. **CurseForge upload / sharing**: HOLD until the owner says the addon works 100% for him and his friends.
9. Releases: push tags ONE OR TWO at a time (GitHub starts no build for more than three).


## 3. Mr.BiZ data
0. **BiZMe! (personal mode) plan**: Phase 0 reports are in `addon/BiZMe/docs/` (inventory, plan review awaiting owner approval, addon audit, UI study, data research); the work list is `addon/BiZMe/BACKLOG.md`.
1. **9 rank 2-3 items with no source** (`bis/sources.json`: 271911, 271920, 276631, 277219, 282283, 282653, 282658, 284399, 284401): checked 2026-10-15, ForeverDB's own item pages say "where it comes from isn't known yet" for all nine, so there is nothing to add; check again after launch. Two drop zones are Forever-new ids Wowhead didn't name (16611 Rath'mael, 16732 Shadetooth).
2. **Own Mr.BiZ database** (owner, 2026-10-17: independent of ForeverDB, no credits or permission): research and plan done, `bis/OWN_DATABASE_PLAN.md` (item data from the game's DB2 tables + hotfix data, own weights and ranking, about 3-4 weeks; M0 item pool first, 3-5 days). M0 started 2026-10-17 (plan section 9): DB2 tables pulled, Wowhead tooltip pull for the legacy items running (about 85 minutes), `items_build.py` cross-check: quality/item level/required level 400 of 400. Route for legacy items: Wowhead tooltips (no action from the owner); the in-game dump stays an option. Bridge until then: `bis/tools/foreverdb_check.py` / `foreverdb_fetch.py` (data refreshed 2026-10-17).
3. **ForeverChanges as a source**: compared only (`bis/foreverchanges-compare.md`); nothing imported.

## 4. Site: builds and macros
1. **Marksmanship tree**: Mobalytics lists an Improved Serpent Sting that Wowhead's Forever data does not have yet; our code ends before it, but old share links could shift if it is added (check share links then). All level 30 builds are owner-confirmed (2026-10-15).
1b. **Talent pick order**: owner rule (2026-10-15): reach the deepest talents the build asks for as early as possible (5 points per row), then fill the rest; done in 0.63.0 (`Calc.Order`, deepest first). Still open: one-click "learn next point" after TESTING 4.2 passes.
4. **"Test in beta" macros** (42 of them carry the label; 33 are the Druid set, see TESTING 13; the other 9 are TESTING 14).
5. **Paladin "Crusade" talent**: missing from Wowhead's Forever data; when it appears, re-check the level-30 Ret build (`DATA30` code shifts by one talent).
6. **`/console` combat lockdown**: unconfirmed which CVars are blocked in combat (low priority).

## 4b. Flight timer
1. `FlightData.lua` holds 72 Alliance routes (shipped 0.88.1). Horde routes and unflown ones are learned in game; when someone flies them, copy `R2FDB.flightTimes` from their account file and extend the table (see `docs/maintainers.md`).

## 5. Launch-day refresh (launch 2026-11-04)
1. **Professions BiS**: re-scraped 2026-11-21 (ForeverChanges still has only level 30 lists, so nothing at 60 to scrape). Left: Wowhead Forever spell pages (blocked from the shell today) to double-check the changed Cloak Defense / Minor Stats values, and the faded PvP spec tags (FC dropped its PvP pages, cannot be re-verified).
3. **Cheat sheets**: all level 30 and 60 sheets re-checked against Wowhead 2026-11-21. Left: level 30 stat orders (Icy Veins, October; Wowhead has no level 30 stat order and Icy Veins blocks the shell).

4. **Mr.BiZ picks vs the live build** (ForeverDB lists refreshed to build 70959 on 2026-11-21; the WCLBox comparison below is older): WCLBox flags about 1,100 of 1,384 best picks as changed or new compared with ForeverDB's lists (build 70862); list in `bis/own/rerank-review.md`. Owner decision 2026-11-13: **Mr.BiZ keeps picking from ForeverDB** (no own ranker); when ForeverDB's lists move to a newer build, refresh with `bis/README.md` and use the review as a checklist of stale picks. Also: 595 items with Equip lines no rule maps (spell crit/hit, ranged attack power), and pull build 70938 (`wclbox_pull.py`, ~2.5 h).
5. **Talent audit in game (Track B)**: read-only C_Traits dump command first, then `/r2f talentcheck`; see `docs/claude-code-wclbox-handoff.md`.

## 5b. Review findings still open (docs/reviews/2026-11, 2026-11-09)
1. **Run the GitHub "Rehearsal" workflow once** (never run) and put a `--only pages,bis,a11y` subset on a weekly schedule.
2. **In-game tests**: close the open `addon/dev/TESTING.md` items (16 at the review); the themes were confirmed good by the owner on 2026-11-09.
3. **Macros marked "Test in beta"** (about 40): decide each in the live game; Shaman Elemental Mastery x2 and Paladin Blessing of Salvation / Light / Sanctuary are not in the current data and probably cannot work.
4. **Mr.BiZ refresh after the next game patch**: `bis/README.md` (about 25 + 20 + 20 minutes of polite downloads: pages, item sources, item rarity). The Professions page's enchant list is still the ForeverChanges level 30 list; level 60 enchants show per slot in Mr.BiZ (ForeverDB's own text). If ForeverChanges publishes level 60 BiS pages, re-scrape them (they render by script, a browser is needed).
5. **Trainer list**: decide whether to include quest-given spells (Bear Form, Berserker Stance, Felhunter) as "quest" rows without a price.
6. **Maintenance**: `R2F.Util` now has `isSecret` (done 2026-11-21); `safe` / throttle still duplicated and differ per file; split `addon/tests/run_tests.py`; a SavedVariables migration test with a frozen old `R2FDB`; `addon/ARCHITECTURE.md` (150 lines) and `docs/maintainers.md`.
7. **TomTom stand-in** (`Nav.lua`): other addons may call methods it lacks; decide whether to add safe no-ops.
8. **Builds**: a second source for the three most played specs; remember the last class on builds.html; class buttons 9 in one row.

## 6. Owner to do
1. Group picks: not needed for now (owner updates builds through Claude); the token is only for publishing from the site.
