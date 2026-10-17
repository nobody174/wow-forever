# Backlog

Open work only (Shape B: the active todo list). Done items live in [CHANGELOG.md](CHANGELOG.md); someday ideas in
[ROADMAP.md](ROADMAP.md); what needs in-game testing in [addon/dev/TESTING.md](addon/dev/TESTING.md).

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
2. **Data pipeline**: steps 0 and 1 built (ADDON_PLAN 19.3): `python bis/tools/foreverdb_check.py` (drift) and `python bis/tools/foreverdb_fetch.py [--write]` (rewrite `bis/raw`). Done once on 2026-10-17 (data now ForeverDB build 1.60.1.70425). Open: step 2 automation (sources for new next picks: 14 this time, by hand), a scheduled run (owner's PC), and asking ForeverDB about reuse.
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
