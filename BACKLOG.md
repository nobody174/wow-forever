# Backlog

Open work only (Shape B: the active todo list). Done items live in [CHANGELOG.md](CHANGELOG.md); someday ideas in
[ROADMAP.md](ROADMAP.md); what needs in-game testing in [addon/dev/TESTING.md](addon/dev/TESTING.md).

## 0. Launch-day reminders (2026-11-04)
The one page to follow on the day: [docs/launch-day.md](docs/launch-day.md).
1. **Back up the beta settings once the release client is installed** (and again right before the beta ends 2026-10-21): `python addon/tools/backup_wtf.py`, then restore into the release client per `docs/beta-backup.md`. Backup goes to `D:\Claude AI Projects\wow-beta-backup\<date>`, outside the repo.
2. Run "Setup Hunter" once on the fresh character before anything else is placed (it now empties every action button first).
3. Launch-day data refresh (BiS / items) before the countdown ends.

4. **Ground markers (`/wm`)**: do not work solo; test in a group, then add macros/coordinates for the Hunter trainer and the general goods vendor in the Skyborne starting zone.

## 0b. Themes: follow-ups after the 0.76.0 test
1. **Other tabs per theme** (Plan, Talents, Gear, Macros, Tweaks): they sit on each theme's page plate but are still the old layouts. Redesign each to match its theme's Home once the Home layouts are confirmed in game.
2. **Frost & Void**: the ring only shows the last 30 days; the "Your journey" checklist and extra sidebar entries (Professions, Reminders, Settings) of the mockups are not built (no matching pages). Theme settings panel (effects level, text size, high contrast, profiles, day / night) of theme_picker.png is not built either.
3. **Hover preview** in the gallery (the mockup previews on hover; ours previews on click with Keep / Revert).

## 0c. Launch route (owner, 2026-10-21)
0. Known gate from run 1: "Harvesting Windstones" (Dalia the Collector, 43.3,24.0) cannot be picked up before level 2.
1. Walk the Skyborne Hunter start with the route log (TESTING 5.65), then turn the file (`python addon/tools/route_report.py`) into the launch plan steps: quest ids, givers, coordinates, level gates, follow-ups, a good order.
2. ~~Follow the plan~~ built in 0.82.0 (see 0d.1); it moves the arrow on through the existing "arrow follows the plan" setting.

## 0d. Launch plan: race and class (hand-off 2026-10-24; phase 1 shipped, see CHANGELOG)
Left, in order (phase 2 and the Human and Night Elf starts are in, see 1 and 3). Class order everywhere: Priest, Warlock, Mage, Rogue, Druid, Shaman, Hunter, Paladin, Warrior.
1. **Phase 2 is built (2026-10-25), confirm at launch.** The Skyborne quest-id steps are seeded from Wowhead Forever and the "Follow the plan" switch is in the addon (0.82.0). Left: walk the start on the first Skyborne Hunter with `/r2f route start hunter-1` and `python addon/tools/route_report.py` (TESTING 5.65), then fix order, givers, coordinates and gates and drop the `unv` tags; the step ids and `quests` lists in `launch-plan.html` PHASES are what to correct. Giver coordinates are in (read 2026-10-25, slow retry, 43 of 43 quests, `exact`); still missing from the seed: subzones, the Rogue and Druid class quest ids are inferred from the trainer names, the quest ids of the later steps (Dalaran onward) and the other races' starts have no quest ids yet. Reuse: `Plan.AutoTick` reads quest flags (`C_QuestLog.IsQuestFlaggedCompleted`), so adding `quests: [...]` to a step is enough.
2. **Phase 3: Dwarf and Gnome starts.** The old trio text is in (Coldridge, Kharanos, Loch Modan, Ironforge). Still to do: Priest, Warlock (Gnome), Rogue and Mage trainer and class-quest steps for the Dwarf and Gnome start, waypoints for them, and a re-check of every Classic fact for Forever (tag `unv`).
3. **Human and Night Elf starts: written 2026-10-25, unverified.** Human: Northshire Valley, then Elwynn Forest from Goldshire, then the shared Stormwind tram to Ironforge. Night Elf (owner's route): Shadowglen, Dolanaar, boat from Rut'theran to Auberdine, straight into Darkshore (they skip the Ironforge steps). Wowhead Forever only confirmed the zone level ranges (Elwynn 1-10, Teldrassil 1-11, Darkshore 11-19); hubs, trainers and the boat are Classic knowledge (tagged `unv`) and the waypoints are `check` points. To do: fill in real coordinates and confirm the Rut'theran boat in game.
4. Priest and Warlock class steps (Warlock Voidwalker quest at 10 and the level 20 pet, Priest trainer visits) are not written; Mage (`ma-food`) and Rogue (`ro-poison`) have one step each from Classic knowledge, tagged `unv`.
5. Confirm Skyborne's English `UnitRace` name in game (TESTING 5.70) so `Plan.RaceId` is exact.

## 1. Bugs
None open (talent-tree drift fixed 2026-10-16; before each release run `python addon/tools/gen_talent_data.py --drift`).

## 2. Addon
1. **Talents tab follow-ups** (0.54.0 is built, ADDON_PLAN 20): re-run `python addon/tools/gen_talent_data.py` whenever Wowhead changes the trees or builds.html gets a build.
2. **Plan points without a position**: only Shaper's Terrace has no position (TESTING 15.7); Krol'dok and Dire Maul are approximate (read online). Also re-check the `classic` points ("may have moved").
3. **Weapons along the route**: checked 2026-10-17 (ADDON_PLAN 19.3): all 273 quest weapons still match Wowhead's tooltips; class weapon table fixed (Rogues use 1h axes). Open: re-verify the weapons' quest links when Wowhead's list pages answer again (`python bis/tools/wh_quest_weapons.py`), and extend past level 32 when the beta cap moves.
4. **More countdowns** on request (Timers.TRACK). Pet / repair / rested XP / food / Walk on Air / Seal / Slice and Dice reminders are all shipped (CHANGELOG 0.62.0 to 0.66.0).
5e. **Copy beta settings to release** (owner): found 2026-10-16 in `<WoW folder>\_classic_beta_\WTF\<Account>\` (only the beta client exists there yet). Account level: `edit-mode-cache-account.txt` (Edit Mode layouts, 11 KB), `bindings-cache.wtf` (keybinds), `config-cache.wtf`, `macros-cache.txt`, `character-list-order.txt`, `SavedVariables\` (addon settings, incl. RoadToForever). Per character (`70\<Name-Surname>\`): `layout-local.txt`, `edit-mode-cache-character.txt`, `bindings-cache.wtf`, `click-bindings-cache.txt`, `config-cache.wtf`, `macros-cache.txt`, `chat-cache.txt`, `AddOns.txt`, `SavedVariables\`. To copy when the release client exists: same folder shape under its own WTF; rename the character folders to the release realm's names. Nothing was copied or changed.
5d. **Rested XP icon**: owner keeps it. It is already off until ticked (Tweaks > Class icons); nothing to change.
5. **Buff "upper display"**: built (Buffs.lua). The aura probe (TESTING 7.12) showed the game hands out your buffs readably out of combat; what it does in a fight / in a dungeon is still to be sent, the reminder stays silent when the list is unreadable.
8. **CurseForge upload / sharing**: HOLD until the owner says the addon works 100% for him and his friends.
9. Releases: push tags ONE OR TWO at a time (GitHub starts no build for more than three).


## 3. Mr.BiZ data
1. **9 rank 2-3 items with no source** (`bis/sources.json`: 271911, 271920, 276631, 277219, 282283, 282653, 282658, 284399, 284401): checked 2026-10-15, ForeverDB's own item pages say "where it comes from isn't known yet" for all nine, so there is nothing to add; check again after launch. Two drop zones are Forever-new ids Wowhead didn't name (16611 Rath'mael, 16732 Shadetooth).
2. **Own Mr.BiZ database** (owner, 2026-10-17: independent of ForeverDB, no credits or permission): research and plan done, `bis/OWN_DATABASE_PLAN.md` (item data from the game's DB2 tables + hotfix data, own weights and ranking, about 3-4 weeks; M0 item pool first, 3-5 days). M0 started 2026-10-17 (plan section 9): DB2 tables pulled, Wowhead tooltip pull for the legacy items running (about 85 minutes), `items_build.py` cross-check: quality/item level/required level 400 of 400. Route for legacy items: Wowhead tooltips (no action from the owner); the in-game dump stays an option. Bridge until then: `bis/tools/foreverdb_check.py` / `foreverdb_fetch.py` (data refreshed 2026-10-17).
3. **ForeverChanges as a source**: compared only (`bis/foreverchanges-compare.md`); nothing imported.

## 4. Site: builds and macros
1. **Marksmanship tree**: Mobalytics lists an Improved Serpent Sting that Wowhead's Forever data does not have yet; our code ends before it, but old share links could shift if it is added (check share links then). All level 30 builds are owner-confirmed (2026-10-15).
1b. **Talent pick order**: owner rule (2026-10-15): reach the deepest talents the build asks for as early as possible (5 points per row), then fill the rest; done in 0.63.0 (`Calc.Order`, deepest first). Still open: one-click "learn next point" after TESTING 4.2 passes.
4. **"Test in beta" macros** (42 of them carry the label; 33 are the Druid set, see TESTING 13; the other 9 are TESTING 14).
5. **Paladin "Crusade" talent**: missing from Wowhead's Forever data; when it appears, re-check the level-30 Ret build (`DATA30` code shifts by one talent).
6. **`/console` combat lockdown**: unconfirmed which CVars are blocked in combat (low priority).

## 5. Launch-day refresh (launch 2026-11-04)
1. **Professions BiS**: re-scrape ForeverChanges' level-60 lists, re-check `ALT` / `LADDER` and sources, update the "checked" dates.
2. **AH market**: when AHledger lists EU markets, switch `DEFAULT_MARKET` in professions.html and save fresh site prices.
3. **Builds and launch plan**: re-check builds and the `unverified` steps past level 30; compare our level-60 builds with the first real guides. Also re-check ALL cheat sheets (`GUIDES` in builds.html, plus the Druid Feral inline ones: Level 60 ones use Classic numbers, Hit caps and Defense; four Druid icons and four text-chip abilities unchecked) once real guides exist. Original note: the Druid "Bear tank cheat sheet" (stat order, Enrage/armor note, green suffixes) (both Level 30 and 60 versions) once real guides exist; the 60 one uses Classic numbers (Hit cap, Defense) and four unchecked icons (Growl, Challenging Roar, Frenzied Regeneration, Barkskin).

## 6. Owner to do
1. Create the GitHub token and sign in once at the owner login (Group picks); publish real 60 builds for the group.
