# Backlog

Open work only (Shape B: the active todo list). Done items live in [CHANGELOG.md](CHANGELOG.md); someday ideas in
[ROADMAP.md](ROADMAP.md); what needs in-game testing in [addon/dev/TESTING.md](addon/dev/TESTING.md).

## 1. Bugs
None open (the "macros missing after a relog" bug is gone since 2026-10-15, owner).

## 2. Addon
1. **Talents tab follow-ups** (0.54.0 is built, ADDON_PLAN 20): re-run `python addon/tools/gen_talent_data.py` whenever Wowhead changes the trees or builds.html gets a build; then delete TalentGuide.lua and the old guided mode.
2. **Plan points without a position** (19 `check` points in `launch-plan-waypoints.json`: Skycutter / Dalaran portal, Stormwind boat, Riverglades,
   Shen'dralas, Mount Hyjal, new dungeons): `/r2f here` at the spot, send the lines, set `zone/x/y/conf: "exact"`, run `python build.py`. Also re-check the
   `classic` points ("may have moved").
3. **Weapons along the route**: check the Classic weapon table against Forever; extend past level 32 when the beta does.
4. **More reminders**: pet missing / dead / unhappy and repair needed shipped in 0.62.0 (verify in game); rested XP shipped in 0.64.0; still open: the +5% experience food buff (waiting for its name from the owner). Walk on Air countdown shipped; more countdowns on request (Timers.TRACK).
5. **Buff "upper display"**: built (Buffs.lua). The aura probe (TESTING 7.12) showed the game hands out your buffs readably out of combat; what it does in a fight / in a dungeon is still to be sent, the reminder stays silent when the list is unreadable.
8. **CurseForge upload / sharing**: HOLD until the owner says the addon works 100% for him and his friends.
9. Releases: push tags ONE OR TWO at a time (GitHub starts no build for more than three).


## 3. Mr.BiZ data
1. **9 rank 2-3 items with no source** (`bis/sources.json`: 271911, 271920, 276631, 277219, 282283, 282653, 282658, 284399, 284401): checked 2026-10-15, ForeverDB's own item pages say "where it comes from isn't known yet" for all nine, so there is nothing to add; check again after launch. Two drop zones are Forever-new ids Wowhead didn't name (16611 Rath'mael, 16732 Shadetooth).
2. **Data pipeline** (ADDON_PLAN 19, to write): keep the list current from ForeverDB / Wowhead / addon reports; Wowhead throttles (403 after ~70 quick
   pages); reuse permission for republishing is an open question.
3. **ForeverChanges as a source**: compared only (`bis/foreverchanges-compare.md`); nothing imported.

## 4. Site: builds and macros
1. **Marksmanship tree**: Mobalytics lists an Improved Serpent Sting that Wowhead's Forever data does not have yet; our code ends before it, but old share links could shift if it is added (check share links then). All level 30 builds are owner-confirmed (2026-10-15).
1b. **Talent pick order**: owner rule (2026-10-15): reach the deepest talents the build asks for as early as possible (5 points per row), then fill the rest; done in 0.63.0 (`Calc.Order`, deepest first). Still open: one-click "learn next point" after TESTING 4.2 passes.
1d. **Fury / Warrior "+5 Talented points" option**: builds.html already has the Talented switch; check the 26-point builds (Fury dual-wield, Priest Healer / PvP) show it clearly.
3. **Macro fall-through audit**: decided 2026-10-15. "Cooldown + spell" pair macros stay; while the first spell is on cooldown the button does nothing (owner test, Shield Block + Revenge), and every such macro now says so in its note (`PAIR_MACROS` in data.py). Check Warlock Shadow Bolt + Imp Firebolt.
4. **"Test in beta" macros** (42 of them carry the label; 33 are the Druid set, see TESTING 13; the other 9 are TESTING 14).
5. **Paladin "Crusade" talent**: missing from Wowhead's Forever data; when it appears, re-check the level-30 Ret build (`DATA30` code shifts by one talent).
6. **`/console` combat lockdown**: unconfirmed which CVars are blocked in combat (low priority).

## 5. Launch-day refresh (launch 2026-11-04)
1. **Professions BiS**: re-scrape ForeverChanges' level-60 lists, re-check `ALT` / `LADDER` and sources, update the "checked" dates.
2. **AH market**: when AHledger lists EU markets, switch `DEFAULT_MARKET` in professions.html and save fresh site prices.
3. **Builds and launch plan**: re-check builds and the `unverified` steps past level 30; compare our level-60 builds with the first real guides.

## 6. Owner to do
1. Create the GitHub token and sign in once at the owner login (Group picks); publish real 60 builds for the group.
