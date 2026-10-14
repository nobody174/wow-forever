# Backlog

Open work only (Shape B: the active todo list). Done items live in [CHANGELOG.md](CHANGELOG.md); someday ideas in
[ROADMAP.md](ROADMAP.md); what needs in-game testing in [addon/dev/TESTING.md](addon/dev/TESTING.md).

## 1. Bugs
1. **Macros missing from bars after a relog** (2026-10-07, seen once, not reproduced). If it returns: check `/macro` first (macro gone = the game
   didn't save it; macro there but bar slot empty = ours).

## 2. Addon
1. **Talents tab follow-ups** (0.54.0 is built, ADDON_PLAN 20): re-run `python addon/tools/gen_talent_data.py` whenever Wowhead changes the trees or builds.html gets a build; then delete TalentGuide.lua and the old guided mode.
2. **Plan points without a position** (19 `check` points in `launch-plan-waypoints.json`: Skycutter / Dalaran portal, Stormwind boat, Riverglades,
   Shen'dralas, Mount Hyjal, new dungeons): `/r2f here` at the spot, send the lines, set `zone/x/y/conf: "exact"`, run `python build.py`. Also re-check the
   `classic` points ("may have moved").
3. **Weapons along the route**: check the Classic weapon table against Forever; extend past level 32 when the beta does.
4. **More reminders** (none picked): pet missing / dead / unhappy, pet food, repair needed, bags almost full, rested XP.
5. **Buff "upper display"** for the group's class buffs: waits on the `/r2f auras` probe results (TESTING 7.12).
6. **Rank-aware macros**: verify in game (TESTING 2.9), then decide whether the three `Charge(Rank 1)` site macros go back to plain `Charge`.
7. **Release workflow upkeep**: the Node 24 action bumps (2026-10-15) are untested on the release step until the next tag: check that run.
8. **CurseForge upload / sharing**: HOLD until the owner says the addon works 100% for him and his friends.
9. Releases: push tags ONE OR TWO at a time (GitHub starts no build for more than three).


## 3. Mr.BiZ data
1. **9 rank 2-3 items with no source** (`bis/sources.json`: 271911, 271920, 276631, 277219, 282283, 282653, 282658, 284399, 284401); two drop zones are
   Forever-new ids Wowhead didn't name (16611 Rath'mael, 16732 Shadetooth).
2. **Data pipeline** (ADDON_PLAN 19, to write): keep the list current from ForeverDB / Wowhead / addon reports; Wowhead throttles (403 after ~70 quick
   pages); reuse permission for republishing is an open question.
3. **ForeverChanges as a source**: compared only (`bis/foreverchanges-compare.md`); nothing imported.

## 4. Site: builds and macros
1. **Level 30 builds: confirm in beta** (added 2026-10-14, all "medium"): Survival (sources disagree), Assassination (last 7 points flexible), Fury, Balance, Discipline; Marksmanship's tree may gain Improved Serpent Sting (check share links).
1b. **Talent pick order, still open**: (a) a guide's real pick order per build (the current order is tier by tier), (b) one-click "learn next point" after TESTING 4.2 passes.
1c. **Group picks in the addon**: the addon cannot fetch group-builds.json; it would have to be baked in at release like MacroData. Owner asked 2026-10-14 whether to add it.
1d. **Fury / Warrior "+5 Talented points" option**: builds.html already has the Talented switch; check the 26-point builds (Fury dual-wield, Priest Healer / PvP) show it clearly.
2. **Re-check the 15 "medium" rotations** (only Priest Shadow, Druid Feral, Paladin Retribution, Warrior Protection are "high").
3. **Macro fall-through audit** (a macro stops at the first `/cast` of a known-but-unusable spell):
   - One test decides the rest: Shield Block + Sunder while Shield Block is on cooldown. Sunder casts = cooldown + spell pairs are fine; nothing = each becomes two
     buttons (Priest Inner Focus + Greater Heal, Warlock Amplify Curse + Agony, Fel Domination, Mage Arcane Power / Presence of Mind, Rogue Cold Blood + Ambush,
     Shaman Elemental Mastery, Hunter Bestial Wrath + Rapid Fire).
   - Check Warlock Shadow Bolt + Imp Firebolt.
4. **"Test in beta" macros**: Dark Pact, Elemental Mastery (not in beta trees), Seal swap (Twist of Light), Voice of Truth, Rogue Venom name, Survival melee Raptor Strike GCD.
5. **Paladin "Crusade" talent**: missing from Wowhead's Forever data; when it appears, re-check the level-30 Ret build (`DATA30` code shifts by one talent).
6. **`/console` combat lockdown**: unconfirmed which CVars are blocked in combat (low priority).

## 5. Launch-day refresh (launch 2026-11-04)
1. **Professions BiS**: re-scrape ForeverChanges' level-60 lists, re-check `ALT` / `LADDER` and sources, update the "checked" dates.
2. **AH market**: when AHledger lists EU markets, switch `DEFAULT_MARKET` in professions.html and save fresh site prices.
3. **Builds and launch plan**: re-check builds and the `unverified` steps past level 30; compare our level-60 builds with the first real guides.

## 6. Owner to do
1. Create the GitHub token and sign in once at the owner login (Group picks); publish real 60 builds for the group.
