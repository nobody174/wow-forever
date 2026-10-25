# Changelog

Authoritative history of what's actually shipped: the site AND the addon, one project. Site entries are by date; the addon's detailed
version log is at the bottom. Working
history for whoever builds this next (including a future Claude session) — not
user-facing release notes.

## 2026-10-25 (addon versions checked)
- CurseForge check: Leatrix Maps moved from 1.60.23-forever to 1.60.25-forever (file 9275553, Oct 21, 2026). AtlasLoot Continued moved from 12488 to 12599 (Oct 22, 2026); its file page lists Forever and game version 1.60.1, so the card now uses it.
- Forever Bestiary 0.6.0, Questie v12.1.0+v1.0.6 and ThreatMaster 0.4.0 are still the newest Forever files, so their cards are unchanged.
- Road to Forever card unchanged at 0.80.1 (newest `r2f-v*` tag). `RoadToForever.toc` already says 0.82.0 with no matching tag yet.

## 2026-10-22 (addon versions checked)
- addons.html: Road to Forever card fallback moved to 0.80.1 (newest `r2f-v*` tag, Oct 22, 2026; link, version, zip name). It matches
  `RoadToForever.toc` (`## Version: 0.80.1`).
- CurseForge re-checked the same day: Forever Bestiary 0.6.0, Leatrix Maps 1.60.23-forever, Questie v12.1.0+v1.0.6 and ThreatMaster 0.4.0
  are still the newest Forever files, so their cards are unchanged. AtlasLoot Continued shows a newer file (12599, Oct 22) but its file
  row reads "Classic TBC +2", so Forever is not confirmed; its card stays on 12488 until the file page confirms the flavor.
- The first attempt in the scheduled run was refused by the fetch permission (not answered in time), which is why this check was repeated.

## 2026-10-25 (launch plan: Zephras giver coordinates)
- Waypoints for every Zephras route step (giver NPC coordinates from Wowhead Forever NPC pages, one page at a time with 6 s pauses; 43 of 43
  quests, no block). Site and addon both show them; subzones are not on the NPC pages.

## 2026-10-25 (launch plan: dropdown icons, weapon tooltips)
- `launch-plan.html`: the race and class pickers are custom dropdowns (keyboard friendly) with a race portrait per race and the class icon and class colour per class; the race chip shows the icon. Weapon names are coloured by rarity and show Wowhead's item tooltip on hover (the same `tooltips.js` the Professions page loads); a click still opens the item on Wowhead Forever.

## 2026-10-25 (launch plan: Zephras quest ids, Follow the plan)
- Skyborne route: 14 new steps with Wowhead Forever quest ids (Valanaar start, class quests, Rorian's chain, Shen'dar Village, the cult chain,
  Windfield farm, scholar chain, Valennia's chain, finale), plus quest ids on the pet, camping and Dalaran steps. Data came from Wowhead quest
  pages via the owner's browser: ids, levels, givers and series order; Wowhead has no explicit prerequisites, and coordinates exist for only a
  few NPCs. Step order and text are ours; everything is tagged unverified until a walk at launch.
- Addon 0.82.0: "Follow the plan" switch (steps carry `quests` and optional `reach`; `Plan.AutoTick` on QUEST_TURNED_IN, PLAYER_LEVEL_UP and login;
  `R2FCharDB.plan.follow` / `noauto`).

## 2026-10-25 (launch plan: Human and Night Elf starts)
- Human: Northshire Valley, then Elwynn Forest from Goldshire, then the Stormwind tram to Ironforge. Night Elf: Shadowglen, Dolanaar, the Rut'theran boat to Auberdine, then Darkshore from level 11 (they skip the Ironforge steps). Wowhead Forever confirmed only the zone level ranges (Elwynn 1-10, Teldrassil 1-11, Darkshore 11-19); the rest is Classic knowledge tagged unverified, with capture-in-game waypoints. The "start not written yet" note no longer shows for any race.

## 2026-10-24 (launch plan: race and class, phase 1)
- `launch-plan.html`: the group plans (2 Hunters · Warrior · Druid, 3 Hunters · Druid, Paladin · Hunter · Shaman), Compare mode, the
  key-differences table and the compare selects are gone. Pick a race, then a class (28 Alliance combinations, class list per race);
  "2 Hunters" stays as a side option (Skyborne Hunter plus the duo tactics card). Every class is damage: no tank or healer text.
  The old group text moved into class steps (Hunter pet and ammo, Druid Bear Form and Cat Form, Warrior stance, Paladin and Shaman
  steps, Mage food, Rogue poisons) and Dwarf and Gnome overrides (Coldridge Valley, Kharanos, Loch Modan, Ironforge). Night Elves skip
  the Ironforge road until the owner picks their route; Human and Night Elf show "start not written yet". URL `?race=gnome&class=mage`
  or `?plan=hunter`, localStorage `wf-launch-plan-sel` (the old mode and compare keys are unused; `wf-launch-plan-v1` unchanged).
  "Group play" became "Tips" with race cards.
- Weapons on the site: each step with a level and a zone in its title lists the best quest-reward weapons for the class by dps
  (casters: check stats; nothing past level 32). `bis/build_quest_weapons.py` now also writes `launch-plan-weapons.json` and holds the
  one class weapon table (`CLASS_USE`), which the addon takes from `QuestWeaponData.lua`.
- Addon 0.81.0: the Plan tab reads the character's race and class (`UnitRace`, `UnitClass`) with a Preview control; Horde gets a message;
  `PlanData.lua` is generated from the new page model; waypoints are per race (`launch-plan-waypoints.json`).

## 2026-10-21 (addon versions checked)
- addons.html: Road to Forever card fallback moved to 0.77.1 (newest `r2f-v*` tag, Oct 20, 2026; link, version, zip name). It matches
  `RoadToForever.toc` (`## Version: 0.77.1`). CurseForge cards (AtlasLoot Continued, Forever Bestiary, Leatrix Maps, Questie, ThreatMaster)
  were not re-checked this run: the CurseForge file pages could not be fetched (the fetch permission requests were not answered), so their
  "Versions checked" date was left as is.

## 2026-10-20 (addon versions checked)
- addons.html: Road to Forever card fallback moved to 0.77.0 (newest `r2f-v*` tag, Oct 20, 2026; link, version, date, zip name). It matches
  `RoadToForever.toc` (`## Version: 0.77.0`). The card still updates itself from GitHub in the browser. CurseForge cards (AtlasLoot Continued,
  Forever Bestiary, Leatrix Maps, Questie, ThreatMaster) were not re-checked this run: the CurseForge file lists could not be fetched (permission
  request for the fetch was not answered), so their "Versions checked" date was left as is.

## 2026-10-19 (addon versions checked)
- addons.html: Road to Forever card fallback moved to 0.74.1 (newest `r2f-v*` tag, Oct 19, 2026; link, version, date, zip name). It matches
  `RoadToForever.toc` (`## Version: 0.74.1`). The card still updates itself from GitHub in the browser. CurseForge cards (AtlasLoot Continued,
  Forever Bestiary, Leatrix Maps, Questie, ThreatMaster) were not re-checked this run: CurseForge fetches were refused, so their
  "Versions checked" date was left as is.

## 2026-10-18 (addon versions checked)
- addons.html: Road to Forever card fallback moved to 0.69.1 (newest `r2f-v*` tag, Oct 18, 2026; link, version, date, zip name). The card
  still updates itself from GitHub in the browser. CurseForge cards (AtlasLoot Continued, Forever Bestiary, Leatrix Maps, Questie,
  ThreatMaster) were not re-checked this run: CurseForge pages could not be fetched, so their "Versions checked" date was left as is.

## 2026-10-17 (cheat sheets for every class)
- builds.html: new `GUIDES[level][class][spec]` map (same shape as an inline `build.guide`; `guideHTML()` uses `b.guide` first) covers
  all 47 builds. Level 30 from Icy Veins' Forever spec guides (Sep 17 to Oct 16); Level 60 is Classic-based (no Forever 60 guide exists, hit caps
  and Defense numbers unpublished) and says so in its intro. "high" = the guide gave an ordered stat list for that exact spec, "medium" = our read.
- Ability icons resolve by name from the class's own builds (`iconFor()`); a name with no known icon renders as a text chip (`.talent.noicon`):
  Holy Fire, Rupture, Mongoose Bite, Lay on Hands. Optional `pullLabel` (e.g. "Healing priority") and tip-only extra rows (empty abilities).
- Tested every class x level (18 combos): no page errors, one guide per build card. `python build.py` and addon tests green (25232 checks).

## 2026-10-17 (Druid bear tank cheat sheet)
- builds.html: a build can now carry an optional `guide` (title, confidence, intro, `modes[]` with stat order + pack-pull rotation, foot note),
  rendered by `guideHTML()` as a second `.build-section.guide` card right after its build card, so it sits beside the build on wide
  screens and stacks under it on phones. First user: Druid Level 30 Feral, "Bear tank cheat sheet" (Damage tank: Strength > Stamina >
  Agility > Armor; Pure tank: Stamina > Armor > Agility > Strength; Feral Charge > (Enrage) > Demoralizing Roar > Swipe loop). Stat order
  is our reading of Icy Veins' Forever Feral guide (updated Oct 7) plus the Classic tank guides, so it is badged "medium": re-check in
  beta. Nothing in the talent data or addon changed.
- Same card for Druid Level 60 Feral (Bear tank): Damage tank = Hit (to cap) > Strength > Stamina > Armor > Agility; Pure tank = Stamina >
  Armor > Defense > Agility > Hit. Cards can now carry extra rotation rows per mode (`extra: [{label, abilities, loop, tip}]`): Single
  target for both, Safety (Growl, Challenging Roar, Frenzied Regeneration, Barkskin) for the pure tank. Sources: Mobalytics' Forever Feral
  guide (Oct 14), Icy Veins' Forever Feral guide (Oct 7), Icy Veins' Classic Feral tank stat and rotation pages. No Forever guide covers 60 tank
  stats yet, so it is badged "medium". Icons for Growl, Challenging Roar, Frenzied Regeneration and Barkskin are the standard Classic names
  but could not be checked against Wowhead from the cloud: confirm they show on the live page. Hit cap (9% in Classic), Defense and whether
  Barkskin / Frenzied Regeneration exist in Forever are unverified.

## 2026-10-16 (Addon version check)
- addons.html: Leatrix Maps 1.60.21-forever → 1.60.23-forever (file 9175962, Oct 14; Forever + 1.60.1, release R, confirmed on the
  file page). Road to Forever fallback values 0.62.1 → 0.66.1 (r2f-v0.66.1, Oct 15; toc agrees, pre-release until 1.0.0).
  AtlasLootClassic Continued 12488 (file 9187862), Forever Bestiary 0.6.0 (beta, the only Forever type it ships) and ThreatMaster
  0.4.0 unchanged. "Versions checked on CurseForge" set to Oct 16, 2026.

## 2026-10-15 (Addon version check, afternoon)
- addons.html: AtlasLootClassic Continued 12487 → 12488 (file 9187862, Oct 15; Forever + 1.60.1 listed like 12487), Leatrix Maps
  1.60.20-forever → 1.60.21-forever (file 9170659, Oct 14). Forever Bestiary 0.6.0, ThreatMaster 0.4.0 and Road to Forever
  0.62.1 unchanged. "Versions checked on CurseForge" set to Oct 15, 2026.

## 2026-10-15 (Addons page trim)
- addons.html: removed the ForeverPlus, Questie and TomTom cards from "What we use" (owner baked their functions into the Road
  to Forever addon). The daily addon version check reads the `data-addon` slugs on the page, so it stops checking them
  automatically. The scheduled check now runs on Haiku.

## 2026-10-15 (Addon version check)
- addons.html: Road to Forever fallback values 0.62.0 → 0.62.1 (r2f-v0.62.1, Oct 15). AtlasLootClassic Continued (12487),
  Forever Bestiary (0.6.0), ForeverPlus (0.9.2), Leatrix Maps (1.60.20-forever), Questie (v12.1.0+v1.0.6) and TomTom
  (v4.3.12-release) unchanged. ThreatMaster could not be checked (no CurseForge URL WebFetch would accept in the
  unattended run), card left at 0.4.0. "Versions checked on CurseForge" set to Oct 15, 2026.

## 2026-10-14 (Addon version check)
- addons.html: AtlasLootClassic Continued 12482 → 12487 (Oct 12), Forever Bestiary 0.5.0 → 0.6.0 (Oct 13, beta, the only
  Forever release type it ships), ForeverPlus 0.8.6 → 0.9.2 (Oct 13), Questie v12.0.4+v1.0.5 → v12.1.0+v1.0.6 (Oct 12).
  Road to Forever fallback values 0.41.0 → 0.54.0 (r2f-v0.54.0, Oct 14). Leatrix Maps (1.60.20-forever) and TomTom
  (v4.3.12-release) unchanged. ThreatMaster could not be checked (WebFetch permission for its CurseForge page timed out
  in the unattended run), card left at 0.4.0. "Versions checked on CurseForge" set to Oct 14, 2026.

## 2026-10-13 (Planning files cleaned up)
- BACKLOG.md rewritten as a numbered open-only list; ROADMAP.md took the unscheduled ideas. Everything below from the old BACKLOG is DONE and now lives here:
  - Site data and export: Data (1) and Site export (2), 2026-10-01.
  - Addon builds: MVP 0.1.0 (3), Updates 0.2.0 (4), Tidy up / Settings / Remove all / keybindings 0.3.0 (5), Main window + minimap 0.4.0 (6),
    first GitHub release 0.5.0 (7, tag prefix `r2f-v*`), Talent export 0.6.0 (8), Talent import preview 0.7.0 (9), Talent learning 0.8.0 (10),
    Quick settings 0.9.0, Interface number fix 0.9.1 (`16001`), C_Traits reader 0.10.4 / 0.10.5, free points + one-click learning 0.11.0.
  - Addon round 2: import replaces 0.14.0, Settings tab 0.15.0, movable bags 0.16.0, Reminders 0.17.0, Launch Plan in game 0.18.0, rank-aware macros 0.19.0,
    replace-ForeverPlus steps 1-4 (0.21.0 - 0.26.0: Gameplay tab, mail, bag slots, loot, quest automation, gossip skipper, tracking reminder).
  - Weapons from quests along the route (0.53.0). Level slider dropped, enchant lines in Mr.BiZ, Talents tab Clear (0.50.0).
  - Item rarity colours baked into the Mr.BiZ data (`bis/quality.json`, all 340 items, 0.48.1 + site).
  - Level 20 builds removed (2026-10-12); level 30 builds exist for every class (gaps listed in BACKLOG).
  - Decisions kept in ROADMAP / BACKLOG: Warrior and Paladin use role sections; logo / ornament stays as is.

## 2026-10-13 (Addon version check: CurseForge not reached)
- addons.html: Road to Forever fallback values refreshed 0.38.1 → 0.41.0 (link, `v` tag, version/date line, zip name;
  r2f-v0.41.0 published Oct 13, 2026). The scheduled CurseForge check couldn't run (WebFetch permission for
  curseforge.com timed out in the unattended run), so the other seven cards and the "Versions checked on CurseForge"
  date (Oct 12, 2026) were left as they were.

## 2026-10-13 (Addons page: Road to Forever follows the newest release)
- addons.html: the Road to Forever card now looks up the newest `r2f-vX.Y.Z` release on GitHub when the page loads
  (highest version, drafts ignored, answer cached 10 minutes) and updates its link, version tag, version/date line and
  zip name. The written-in values (now 0.38.1, were stuck at 0.29.1) are the fallback if GitHub can't be reached. Tested in
  headless Chrome with a deliberately stale copy: it moved from 0.29.1 to 0.38.1.

## 2026-10-13 (Weapons along the route)
- addon 0.53.0: the Plan tab's weapon lines now include quest rewards (QuestWeaponData.lua, generated by bis/build_quest_weapons.py from
  bis/quest-weapons.json; QuestWeapons.lua matches them to steps by zone in the title and level range, class, faction, upgrade over the worn item).
  Owner's answers: upgrade = better than worn (BiZ score), only the best per slot per step, bundle the table with a Wowhead credit.

## 2026-10-13 (BiZNav 3D arrow)
- addon 0.52.0: the arrow is a 3D sprite sheet (addon/art/blender_arrow3d.py renders 100 angles in headless Blender, addon/art/export_arrow3d.py packs
  media/arrow3d.tga, 1024 x 1024, 102 px cells). Nav.lua picks the frame from the turn angle. Tweaks switch "3D arrow" (on by default; off = flat dart).
  Test stub now records SetTexCoord.

## 2026-10-13 (BiZNav corpse arrow)
- addon 0.51.0: the BiZNav arrow points at your corpse when you die and restores the previous arrow when you are alive again (Nav.lua,
  Tweaks switch on by default, TESTING.md section 43).

## 2026-10-13 (Mr.BiZ enchants, game entrances, quest weapons per class)
- bis.html: the best enchant shows on the closed slot row ("Enchant: Chest - Lesser Stats"); the open row lists the 2nd and 3rd best stand-ins
  (professions.html's LADDER) under it.
- bis/enchants_from_professions.js now also prints each enchant's `alts` (and `--names`); bis/build_bis.py adds `ids` (enchantment ids, from the new
  bis/enchant_ids.json) and `alts` to every enchant row (bis-data.json and BiZData.lua; one alt per line, luacheck's 130 columns).
- bis/tools/wago_enchant_ids.py (new): writes bis/enchant_ids.json from wago.tools' DB2 tables for the Forever beta build (SpellName + SpellEffect
  Effect 53). The addon reads the enchant id from your worn item's link and compares it. Rerun it when professions.html gets new enchants.
- launch-plan-waypoints.json: dungeon points have `dungeon` = the entrance's name; the addon asks `C_EncounterJournal.GetDungeonEntrancesForMap`
  for the position (gen_plan_data.js passes the field through).
- bis/tools/wh_quest_weapons.py, bis/quest-weapons.json (273 quest-reward weapons up to level 32) and bis/quest-weapons-by-class.md (the plan's five
  classes on the plan's zones). Research only, nothing in the addon yet.

## 2026-10-13 (Plan positions, quest-weapon research)
- launch-plan-waypoints.json: 6 of the 19 "position not known yet" points filled from Wowhead Forever's zone maps (Zephras Isle trainers,
  vendors and The Great Outdoors giver; the Ironforge Paladin trainer), conf `approx`, sources `wh-zephras` / `wh-ironforge`. PlanData.lua regenerated.
- bis/quest-weapons-research.md + bis/tools/wh_items.py, wh_zone.py: research for weapons from quests along the route (the Hall of Thanes gun and the
  Wetlands bow the owner remembered are real: Calibrated Blunderbuss, Raptor's End). Nothing built yet; decisions listed in the note.
- Item rarity colours baked into Mr.BiZ (Claude Desktop, 0.48.1): all 340 values re-checked against Wowhead's tooltip API, 0 mismatches.

## 2026-10-13 (Warlock macros)
- Warlock Shared: "Shadow Bolt + Imp Firebolt" replaced by **Shadow Bolt (target / target's target)**; new
  **Corruption mouseover** and **Bane of Agony mouseover**; new **Pet attack mouseover** (Class QoL, icon
  Ability_GhoulFrenzy, no #showtooltip). All use the owner's tested order: mouseover, own enemy target, friendly
  target's enemy target, with `nodead`. "Curse of Agony" renamed **Bane of Agony** everywhere (Forever's name): the
  Affliction macros and the builds page rotations. The Imp Firebolt line is gone with the old Shadow Bolt macro.

## 2026-10-13 (Talented legacy perk switch)
- talentcalc.js / talentcalc.css: a switch for the **Talented** legacy perk (+5 talent points; talent points start at
  level 5 instead of 10). Setting `wf-talented` ("5" or absent), shared by every calculator on a page and across tabs
  (`storage` event). The calculators' Level stat counts it (points + 9 - 5) and show a small "Talented" badge. API:
  `TalentCalc.talented()`, `setTalented(on)`, `mountTalentedSwitch(el)`, `instance.level()`.
- talents.html: the switch sits above the class roster (Talents mode only). builds.html: the switch sits under the
  intro, and a build with more than 21 points says under its title at which level it is reached ("26 points: reached
  at level 30 with the Talented perk"). Cache bump `?v=20261013a` on both pages.
- The Warrior Fury and Priest Discipline level 30 codes from the owner are 26-point builds (Fury `-4505010505001`,
  Disc `023303131300121-3-`, both checked against Wowhead's Forever data: valid); they are NOT added to builds.html yet
  (rotations pending), see BACKLOG.
- Addon: Talents tab has the same switch (`R2FDB.settings.talented`, default off) and a line under the build
  summary with the level the build is reached at. See addon/RoadToForever/CHANGELOG.md "Unreleased".

## 2026-10-12 (Builds: level 20 removed)
- builds.html: the Level 20 prebuilt builds are gone (the beta cap is 30, and level 30 builds include those points).
  Level buttons are now 30 and 60; the page opens on 30; old `?level=20` links fall back to 30. Removed the `DATA`
  (level 20) object from the script; builds live in `DATA30` / `DATA60`. Warlock 30's note no longer points at a
  level-20 rotation.
- builds.html: fixed the unreadable text on the active (gold) class / spec / level buttons: a leftover rule set
  light text on the gold gradient; the dark text is back.

## 2026-10-12 (Addon versions checked)
- addons.html: Leatrix Maps 1.60.12-forever -> 1.60.20-forever (Oct 10), Questie v12.0.3+v1.0.4 -> v12.0.4+v1.0.5
  (Oct 6), TomTom v4.3.11-release -> v4.3.12-release (Oct 6); Forever confirmed on each file page. "Versions checked"
  -> Oct 12, 2026. Road to Forever stays 0.29.1 (newest tag; 0.30.0 in the .toc isn't tagged yet).

## 2026-10-12 (Mr.BiZ: source credit per item)
- Every known source now says which site it was read from (`via`: ForeverDB / Wowhead), small grey text after the
  source line on bis.html and "(ForeverDB)" after "From: ..." in the addon tooltip. Unknown sources credit nobody.

## 2026-10-12 (Mr.BiZ round 3: a source for every rank, stand-ins, icon colours)
- `bis/sources.json`: where each rank 2-3 pick comes from, for the 193 that aren't a best pick in any spec, read from
  each item's ForeverDB page (124 found); 60 of the other 69 filled from Wowhead's Forever item pages in the owner's
  Chrome (crafted skill, quest + faction, drops with Wowhead's count/outof %); 9 still unknown. `build_bis.py` puts type / label / group / conf on every
  next pick (best picks' own sources first); a next pick with no entry stops the build. Vendor sentences without
  coordinates parse; Fallen Champion = Scarlet Monastery.
- bis.html: every rank in the open list shows its source line (icon, where, confidence). When filters hide the best,
  the row shows the next rank that passes (a "stand-in" with its biz rank and % behind); only slots where nothing
  passes say "Hidden by your filters". Filtered ranks are greyed in the open list. Source icons have their own colour
  (quest yellow, dungeon purple, PvP red...), off chips grey theirs. The wishlist groups next picks by source too.
- Addon (still 0.30.0): same stand-ins, a grey source line under every rank, and "From: ..." in the Mr.BiZ tooltip line.

## 2026-10-12 (Mr.BiZ round 2: nav, dropdowns, biz ranks)
- Top bar on every page reordered by the player's path, grouped by type: Launch Plan / Builds / Talent / Legacy Calc /
  Mr.BiZ / Professions / Macros / Addons (was Macros / Builds / BiS / Addons / Professions / Launch Plan / Talent).
  The BiS tab is now "Mr.BiZ".
- bis.html: custom dropdowns with class colours and class icons, spec in class colour with Tank / DPS / Healer role
  icons, faction in Alliance blue / Horde red with banner icons, profession icons in the Profession filter. Level picker:
  30 (beta cap) and 60 "in the works" (shows what's coming). Icons on the source chips and each row's source line.
- Biz ranks on the site and in the addon: Bizzest / Bizzer / Biz / Almost biz, "The Bizz" tag when the best is 20%+
  ahead of the next pick. Addon tab label "BiS" -> "BiZ" (still 0.30.0, not tagged yet).

## 2026-10-12 (Mr.BiZ: BiS page + addon tab)
- New `bis.html` (top bar "BiS", after Builds, on every page): class + spec pickers (specs grouped Tank / DPS / Healer),
  faction, level 30. One row per slot: item name coloured by quality (Wowhead's Forever tooltip JSON, cached in
  localStorage `wf-bis-quality-v1`), Wowhead hover tooltip (tooltips.js, `domain=forever`), click = Wowhead item page,
  source, score, confidence badge, wishlist star. Chevron opens ranks 2-3 with % behind plus Wowhead / ForeverDB links.
  Filter chips per source type (Raid greyed until there's raid data), Profession, Show (all / known / Forever data only).
  Wishlist per character (localStorage `wf-bis-wish-v1`), grouped by where to get the items; Copy for the addon / Paste
  from game share it with the addon (`R2FW1:<id>:<class/spec>:<slot>,...`). Prefs in `wf-bis-v1`; `#class/spec` hash.
- Data: `bis/raw/<class>-<spec>.json` (ForeverDB's level 30 PvE BiS pages, all 27 specs, 2026-10-12) ->
  `python bis/build_bis.py` -> `bis-data.json` + `addon/RoadToForever/BiZData.lua`; build.py runs it too.
- Addon 0.30.0: the same list as a BiS tab (see addon/RoadToForever/CHANGELOG.md).

## 2026-10-11 (Warrior: Retaliation with 2H)
- data.py, Warrior General > Panic / defensive: "Retaliation with 2H (from Defensive)" (`Retal2H`):
  `/equip` 2H, `[nostance:1]` Battle Stance, `[stance:1]` Retaliation, `[stance:1]` Defensive Stance.
  Two presses (stance must register before Retaliation). Marked test: does the swap back to
  Defensive fire in the same press as Retaliation? A 3rd press can't do it (Forever macros stop at
  a known spell on cooldown), so the note points to the Stance swap button as fallback.

## 2026-10-10 (Server status link on the front page)
- index.html: "Server status ↗" link under the countdown and a "Server Status" plaque in
  General Resources, both to wowforeverstatus.com (unofficial realm/login/queue tracker by
  Skellee Belly). Link only: the site has no API, badge or embed.
- Hero readability: the local launch time and the status link sit on dark panels (like the
  countdown tiles) with light/gold text; the status link is a gold-bordered button.

## 2026-10-09 (Charge pinned to Rank 1; rank-aware macros planned)
- Owner dump: unranked "Charge" = spell 1240289, Forever's level-46 Charge, unknown at 18, so
  `/cast Charge` fails (Rend unranked works). The three Charge macros (Charge, Charge+Rend,
  VCharge) now use `Charge(Rank 1)` in `#showtooltip` and `/cast`. ADDON_PLAN 16: the addon
  will write the highest known rank into game macros and raise it when a rank is learned.

## 2026-10-09 (Forever macros don't fall through: Warrior combos split)
- Owner test on the live client: `/cast Revenge` + `/cast Sunder Armor` never casts Sunder when
  Revenge isn't lit; `/cast Sunder` alone works; Sunder first casts only Sunder. On Forever's
  modern client a macro stops at the first spell you know but can't use right now, so
  "try A, else B" macros don't work. Conditions (`[stance]`, `[mod]`, `[combat]`...) still do.
- Warrior: "Victory Rush > Revenge > Sunder Armor" and "Victory Rush > Heroic Strike" removed;
  back to separate buttons: Sunder Armor (`Sunder`), Revenge (`Rev`), Victory Rush (`VR`), each
  with /startattack. "Shield Block + Revenge > Sunder Armor" -> "Shield Block + Sunder Armor"
  (same short `SBlk+Sund`, marked test: does Sunder still fire while Shield Block is on
  cooldown?). Builds page rotation notes updated.
- BACKLOG: audit of the other classes' multi-cast macros, waiting on that one test.

## 2026-10-09 (Launch Plan waypoint data for the in-game Plan tab)
- `launch-plan-waypoints.json`: map points for 36 of the 45 launch-day steps (58 points), per
  group plan where they differ. Confidence per point: 4 exact (Forever sources: Hall of Thanes
  entrance Ironforge 43.5, 52.0; Earthseer Farsen Dun Morogh 64.8, 58.5), 33 Classic positions,
  2 approximate areas (Excavation Site, Alcaz Island), 19 to check in game (Zephras Isle,
  Stormwind Harbor dock, Riverglades, Mount Hyjal, new dungeons). ADDON_PLAN 15.5 updated:
  launch-day phases only, plan picker like the site, zone-name map resolution, `/r2f here`.

## 2026-10-08 (Warrior combo macros: fixed icon)
- Rev>Sund, SBlk+Sund and VR>HS had a bare `#showtooltip`, so the game used the first spell
  (Victory Rush) for icon and tooltip and showed a red "?" before level 20. Now
  `#showtooltip Sunder Armor` / `Shield Block` / `Heroic Strike`. Same short names, so an
  import updates the macros already on the bars.

## 2026-10-08 (Warrior Protection at every level; ForeverLayers removed)
- Builds: the Level 20 Warrior "Tank" build was all Arms talents. Replaced with a real
  Protection build (Shield Specialization 5, Improved Bloodrage 2, Improved Thunder Clap 3,
  Improved Revenge 1), Mobalytics' Forever order, with a Shield Block / Revenge rotation.
  Vanguard needs 15 points in Protection, so it arrives at level 25 (in the Level 30 build).
- Warrior spec buttons read "Protection" instead of "Tank" on Level 20, 30 and 60.
- Addons: ForeverLayers removed (owner's request); CLAUDE.md list updated.

## 2026-10-08 (Builds: Level 60 tab, Druid, tank/healer/DPS builds with rotations)
- New **Level 60** tab (51 points): Warrior Tank + Fury, Paladin Protection + Holy + Retribution,
  Druid Bear + Restoration, Shaman Restoration + Enhancement + Elemental, Priest Holy + Shadow,
  Hunter Beast Mastery + Marksmanship, Rogue Combat, Mage Frost + Fire, Warlock Affliction +
  Destruction. No guide has Forever level-60 builds yet (Mobalytics: "full talent trees will come
  with launch"), so these are our proposals from Wowhead's live Forever trees, marked as such.
- Level 30: Warrior Tank and Paladin Retribution replaced with Mobalytics' Forever 1-30 builds
  (the tank's Bastion point moved to Defiance: Bastion needs 25 points in the tree); new Paladin
  Holy, Priest Holy, Shaman Restoration + Elemental, Druid Feral (Mobalytics) + Restoration.
- **Druid** added to the Builds roster (Level 30 and 60; no level-20 build).
- Every build at every level now has a rotation (single target / AoE, tank, healer or DPS);
  the 11 older level-30 builds got theirs too.
- Validation: each new build was checked in the browser against Wowhead's live Forever data
  (talent names, max ranks, 5-points-per-row gates, prerequisite arrows, 21/51 points) and its
  share code generated there; every rotation icon was checked on wow.zamimg.com.

## 2026-10-11 (Addon 0.29.1: group-buff icon always movable when unlocked)
- Unlocked, the missing-buff icon always shows (dimmed if nothing is missing) so it can be dragged.

## 2026-10-11 (Addon 0.29.0: missing group buffs, bag Sort button, faster talent learning)
- Group buff reminder (icons for Fortitude / Mark of the Wild / Thorns / Intellect / Blessing... you lack, by the classes in your group), a Sort button above the backpack, and talent learning that notices each point within 0.1 s instead of waiting the timeout. Never run in game yet (TESTING.md 40).

## 2026-10-10 (Addon 0.28.4: ability name from "just became usable")
- No glow event for Revenge on this client; the alert names the reactive spell that just became usable instead.

## 2026-10-10 (Addon 0.28.3: mail list uses the full in-game name)
- Mail button now fills "Venom Oathbreaker" (GetUnitName) instead of Name-Realm; each alt remembers it at login.

## 2026-10-10 (Addon 0.28.2: /r2f who)
- Probe for the mail list: shows every name the client gives the character, to find the "Venom Oathbreaker" form.

## 2026-10-10 (Addon 0.28.1: active Gameplay page highlighted, not greyed)
- Owner feedback on the four pages: the active one looked disabled. Now gold text + gold bar, still enabled.

## 2026-10-10 (Addons page: version tag)
- A small `v0.28.0` tag next to "Road to Forever" on its addon card (CLAUDE.md's version-check steps say to keep it current).

## 2026-10-10 (Addon 0.28.0: Gameplay tab in four pages, plain names, the ability name in the alert)
- UX pass on the Gameplay tab (ADDON_PLAN 18): pages Quests / Vendors & loot / Screen & chat / Alerts, plain option
  names with a grey hint line, last page remembered. The alert reads the ability name from the glow event's spell id
  (the combat-text announcement hides it); `/r2f reactlog` shows what it saw. Fixed: last-used tab Plan / Gameplay /
  Settings was forgotten at login. Never run in game yet (TESTING.md 35).

## 2026-10-10 (Addon 0.27.2: hide-the-game's-text needs a /reload)
- Owner test of 0.27.1: our alert works; the game's own "<Revenge>" text stayed because the game only reads its setting
  at load. The box now says "/reload" in chat. No Edit Mode option exists for that text (checked in the extracted game code).

## 2026-10-10 (Addon 0.27.1: URGENT, 0.27.0 tainted the game's combat text; Gameplay tab scrolls)
- 0.27.0 shifted `CombatText.textLocations` to move the "<Revenge>" text: writing into a game table taints it and this
  client then refuses arithmetic on the tainted values (96 errors in a fight). Removed; replaced by our own movable
  alert fed by the game's `COMBAT_TEXT_UPDATE` "SPELL_ACTIVE" event, plus an option to hide the game's own text via
  its setting. Lesson recorded in CLAUDE.md: never write into game tables or frames' data. The Gameplay tab now scrolls.

## 2026-10-10 (Addon 0.27.0: movable floating combat text)
- Owner: the "<Revenge>" text still needed to move: replaced the fixed raise with a draggable marker (move +
  lock boxes) that shifts the game's floating-combat-text scroll path. Never run in game yet (TESTING.md 33).

## 2026-10-10 (Addon 0.26.1: tracking reminder gone while tracking, quest-log box left of the collapse button)
- Fixes from the owner's test of 0.26.0. `/r2f auras` out of combat in a party reads buffs on the player and on a
  party member with readable spell ids, so a group-buff reminder is possible out of combat (combat still untested).

## 2026-10-10 (Addon 0.26.0: shop-line skipper, tracking reminder, aura probe)
- ForeverPlus replacement, the rest: GossipAuto in a safe form (single whitelisted-icon line, no quests, Shift
  pauses; plus `/r2f gossip` to learn more icons), the minimap tracking reminder (Find Minerals / Herbs / Treasure),
  and an `/r2f auras` probe because aura reads are restricted on this client (`C_Secrets.ShouldAurasBeSecret`,
  `RequiresUnitAuraAccess`): the group-buff reminder needs its result. Never run in game yet (TESTING.md 34).

## 2026-10-10 (Addon 0.25.0: quest-log track-all, raise floating combat text)
- Extracted game code (CASC, `D:\WoW-Extract`) answered two open items: the quest log is the map-frame quest log
  (header buttons from `QuestScrollFrame.headerFramePool`), so QuestZoneTracking could be built (box per zone header);
  and the "<Revenge>" text is the game's own floating combat text (`SPELL_ACTIVE`, setting "Reactive ability alerts"),
  whose scroll path the new "Raise floating combat text" box moves up. Never run in game yet (TESTING.md 33).

## 2026-10-10 (Addons page now lists only what the owner uses)
- Removed Archivist for Forever, ForeverAuras and Leatrix Plus from addons.html and CLAUDE.md (owner: only Leatrix Maps
  is used of the Leatrix addons). The list is now AtlasLootClassic Continued, Forever Bestiary, ForeverPlus (until Road to
  Forever replaces it), Leatrix Maps, Questie, ThreatMaster, TomTom, plus our own Road to Forever.

## 2026-10-10 (Prat 3.0 dropped, the backpack "178" explained)
- Owner confirmed copy chat (`/r2f copychat`) works: Prat 3.0 removed from addons.html and CLAUDE.md's addon list.
- The "178" on the backpack button matched the arrows of the owner's logged-in character: it is the game's own
  ammunition count. Nothing to fix; our free-slot number stays at the top of the button.

## 2026-10-10 (Addon 0.24.1: Hunter ammo reads the bags)
- The client has no ammo slot (slot 0 answers id 0, count 1): the 0.17.0 ammo reminder read it and would have
  shown "1" for every Hunter. Now: arrows (bow, crossbow) or bullets (gun) counted over all bags by item class.
  Released as r2f-v0.24.1; addons page points at it.

## 2026-10-09 (Addon 0.24.0: copy chat, to drop Prat 3.0)
- `/r2f copychat [window]` and an optional corner button on every chat window: the chat text in a box to
  select and copy, plain text or raw. Prat 3.0 can go from the owner's addon list once he has tried it
  (addons.html still lists it as an addon we use). Never run in game yet (TESTING.md 32).

## 2026-10-09 (Addon 0.23.2: mail uses Name-Realm)
- Owner test: mail to an alt needs the full name on this client. The Gameplay mail button fills in
  `Name-Realm`. Backpack "178" is still unidentified (not the item total: that is 334). Released as
  r2f-v0.23.2; addons page points at it.

## 2026-10-09 (Addon 0.23.1: single quest rewards are taken)
- Owner test: auto turn-in stopped at a quest with exactly one reward. Now one (or no) reward is turned in,
  two or more are left for the player. Also found: the "178" on the backpack button is the game's own
  `MainMenuBarBackpackButtonCount` text (not from any addon); what it counts is still unknown. Released as
  r2f-v0.23.1; addons page points at it.

## 2026-10-09 (Addon 0.23.0: Gameplay step 3, quest automation)
- ADDON_PLAN 17 step 3: accept quests, hand in quests (never picks a reward; Shift pauses), reward sell
  prices. All off by default. Bag-slot number moved to the top of the backpack button. Never run in game
  yet (TESTING.md 31).

## 2026-10-09 (Addon 0.22.0: Gameplay step 2)
- ADDON_PLAN 17 step 2: mail to your own characters, free bag slots on the backpack, fast loot (all off
  by default). QuestZoneTracking waits for the quest log's frame names (needs a look in game). Never run
  in game yet (TESTING.md 30).

## 2026-10-09 (Addon 0.21.0: Gameplay tab, first five ForeverPlus features)
- ADDON_PLAN 17 step 1: the Reminders tab became the Gameplay tab (automatic features, screen features,
  reminders); new features, all off by default: repair at vendors, sell grey items, block duels, hide
  red error spam, XP bar text. Never run in game yet (TESTING.md 29). Buff reminders (group buffs
  others can give you, Find Minerals / Herbs / Treasure) added to the plan as step 5.

## 2026-10-09 (Stance swap macro, addon list icon, ForeverPlus replacement plan)
- Warrior `Stances` macro (was "Stance dance Battle -> Defensive -> Berserker"): owner test, it did
  nothing in Defensive Stance (the next step was Berserker Stance, not available before level 30).
  Now "Stance swap (Battle <> Defensive)": `#showtooltip [stance:1] Defensive Stance; Battle Stance`
  + `/cast [stance:1] Defensive Stance; Battle Stance`. Same short, so an import updates it in place.
  `StanceTog` (Ctrl = Berserker, Alt = Defensive) is unchanged.
- Thunder Clap has no macro on purpose (removed with the other plain casts in the 2026-10-08 cleanup).
- Addon 0.20.1: `## IconTexture` so the addon list shows our logo instead of "?".
- ADDON_PLAN 17 (new): what to build to replace ForeverPlus, and the tab layout. Planning only.

## 2026-10-09 (Addon 0.20.0: bags rebuilt, Reload UI in the minimap menu)
- Owner test: movable bags didn't move with only R2F enabled, while ForeverPlus' BagWindow module
  (Shift+drag) did. Blizzard's title-bar button swallows drags that start on the title; the fix is
  ForeverPlus' own: a grip over the title while Shift is held. R2F's version now does the same
  (Movable bags + Lock bags, per character, classic and combined windows) and no longer calls
  `UpdateContainerFrameAnchors` (the taint ForeverPlus documented). The minimap button's right-click
  menu got a Reload UI line. Released as r2f-v0.20.0; addons page points at it.

## 2026-10-09 (Addon 0.19.1 + Warrior tank macros: Charge + Rend for Vanguard, Shield Block + Revenge)
- Owner test of 0.19.0: `/r2f ranks` didn't find the Charge rank the character has. 0.19.1 reads the
  rank from the spellbook as well and tries every known-check; `/r2f rankdebug <spell>` shows what
  the client answers. Released as r2f-v0.19.1; addons page points at it.
- Warrior Tank, owner request: `VCharge` is now "Charge + Rend (Vanguard, any stance)": Charge when
  out of combat (no stance swap), then Rend on the next press, `/startattack` first. New test macro
  `SBlk+Rev` (Shield Block + Revenge on one button; Shield Block is first because a macro stops at
  the first spell you know but can't use, so Revenge only goes out while Shield Block is usable).
  `/startattack` stays on the FIRST line of every melee macro on purpose: with the stop rule above a
  `/startattack` placed after the spell would be skipped whenever the spell can't be used (no rage,
  on cooldown), which is exactly when auto-attack must still start.

## 2026-10-09 (Addon 0.19.0: rank-aware macros)
- ADDON_PLAN 16: found in game that on Forever an unranked name can resolve to a rank the character
  doesn't know (`Charge` at level 18). Addon 0.19.0 writes `Name(Rank K)` (highest known rank) into
  the game macros it creates / updates / replaces, raises ranks when a spell is learned (queued in
  combat), leaves edited macros alone, keeps library bodies as the site sends them, and adds
  `/r2f ranks`. The site's three Charge macros keep their `Charge(Rank 1)` stopgap, which the addon
  raises. Never run in game yet (TESTING.md 27). Released as r2f-v0.19.0; addons page points at it.

## 2026-10-09 (Addon 0.18.0: Launch Plan in game, TomTom waypoints)
- ADDON_PLAN 15.5, step 5 of addon round 2: a Plan tab (four group plans, launch-day steps,
  per-character ticks, next step on Home), a Waypoint button per point (TomTom, or the `/way`
  line in chat; zone names resolved to uiMapIDs at run time), `/r2f here` to capture the 19
  `check` positions in the beta. `build.py` now also runs `addon/tools/gen_plan_data.js`
  (node) to write `addon/RoadToForever/PlanData.lua` from `launch-plan.html` +
  `launch-plan-waypoints.json`. Never run in game yet (TESTING.md 26). Released as r2f-v0.18.0; addons page points at it.

## 2026-10-09 (Addon 0.17.0: Reminders tab, Hunter ammo low)
- ADDON_PLAN 15.4, step 4 of addon round 2: a Reminders tab (stance icon + options moved out
  of Settings), the first new reminder Hunter ammo low (red under a user-set threshold, hidden
  when fine, draggable / lockable / sized like the stance icon), shared framed-icon code in
  `Reminders.lua`, each reminder only for its class. Never run in game yet (TESTING.md 25).
  Released as r2f-v0.17.0; addons page points at it.

## 2026-10-08 (Addon 0.16.0: movable bags; Forever Bag Mover removed from the list)
- ADDON_PLAN 15.3, step 3 of addon round 2: Movable bags + Lock bags on the Settings tab
  (`Bags.lua`), per character, classic `ContainerFrame1..N` and the combined bag
  `ContainerFrameCombinedBags` detected at run time, re-applied after the game re-anchors,
  nothing moves in combat. Forever Bag Mover is gone from addons.html and CLAUDE.md since
  the addon replaces it. Never run in game yet (TESTING.md 24). Released as r2f-v0.16.0; addons page points at it.

## 2026-10-08 (Addon 0.15.0: Settings tab, tree names, Home "what's next")
- ADDON_PLAN 15.2, step 2 of addon round 2: Settings as the 4th tab (Quick settings moved
  there from Home, floating panel and Macro Book button removed), real talent tree names per
  class (same as talentcalc.js CLASSES, checked by a test), the two black squares in the
  Macro Book (selected class circle and Universal tab; cause: checked texture drawn without
  additive blending) replaced by an additive glow with an icon fallback, Home reduced to
  free talent points / library and bar counts / macro slot use. Never run in game yet
  (TESTING.md 23). Released as r2f-v0.15.0; addons page points at it.

## 2026-10-08 (Import replaces, not only adds: site K lines + addon 0.14.0)
- ADDON_PLAN 15.1, step 1 of addon round 2. `template.html` importString() now appends one
  `K <CLASS> id,id,...` record per carried class (all ids that class has on the site; throws
  if an id ever contains a comma). Addon 0.14.0 removes library entries the site dropped,
  deletes the unedited unused game macros made from them (Tidy up rules, combat-queued),
  keeps and lists on-bar / edited ones, and has a "Replace my library for these classes"
  checkbox in the Import window. Old strings without K stay add-only. 228 new tests
  (`test_import_replaces`). Never run in game yet (TESTING.md 22). Released as r2f-v0.14.0; addons page points at it.

## 2026-10-08 (Addon 0.13.0: Warrior stance icon)
- Road to Forever addon 0.13.0: a Warrior stance icon (blue Battle, green Defensive, red
  Berserker frame), draggable, with Lock and a size slider in Settings, plus `/r2f stance`.
  Tested in game by the owner: works. Released as r2f-v0.13.0; addons page points at it.

## 2026-10-08 (Macro cleanup for every class, Warrior rules)
- Same rules as the Warrior pass: removed plain casts (`/cast X`, `/cast [harm] X`: same as
  dragging the spell from the spellbook), duplicates covered by a smarter macro, "No dispel"
  placeholders, spam auto-attack where melee macros already `/startattack`, and pet-bar
  commands (follow / passive / defensive, the plain pet attack variants). Kept everything with
  real logic: mouseover / target-of-target / focus targeting, /stopcasting interrupts,
  spam-safe channels, no-cancel toggles, cancel-aura panic buttons, combos and sequences.
- Counts: Priest 43 -> 35, Warlock 60 -> 22, Mage 36 -> 14, Rogue 44 -> 25, Shaman 43 -> 21,
  Hunter 52 -> 16, Paladin 53 -> 30, Universal 15 -> 13 (potions: plain /use).
- Stormstrike now starts auto-attack (melee); Raptor Strike + Wing Clip got `/startattack`.
  Discipline's duplicate "Inner Focus + Greater Heal" removed (Holy keeps it).
- Empty specs dropped: Mage Fire and Frost, Rogue Combat. Addon `Library.SECTION_ORDER`
  updated to match (no release needed); tests derive the Paladin count from the fixture.

## 2026-10-08 (Warrior macro cleanup: 59 -> 28)
- Owner review. Removed plain casts that add nothing over the spellbook (Thunder Clap, Demoralizing
  Shout, Battle Shout, Bloodrage, Challenging Shout, Last Stand, Piercing Howl, Death Wish) and
  duplicates: Victory Rush, Heroic Strike, Cleave (kept HS/Cleave Shift), Rend (Charge + Rend covers
  it), Sunder, Revenge, Shield Block, Sunder + HS, Auto-attack (every melee macro has /startattack),
  Berserker Rage, Intimidating Shout, the three stance buttons (stance dance), Shield Wall /
  Retaliation / Recklessness (Stance cooldown covers them), Taunt focus, Taunt + gear, "No dispel".
- Merged: Victory Rush > Sunder into "Victory Rush > Revenge > Sunder Armor" (`Rev>Sund`, trash);
  Shield Bash + Pummel into "Interrupt (Pummel / Shield Bash)" (`Kick`, by stance, no swap);
  the two focus interrupts into "Interrupt focus" (`Kick F`).
- Empty groups dropped. Addon tests now use surviving Warrior macros (Ham/OP/Mock/Disarm) and
  derive the Warrior count from the fixture; also fixed the stale TOC-version check (all pass).

## 2026-10-08 (Warrior tank: Revenge > Sunder)
- New Tank macro "Revenge > Sunder Armor" (`Rev>Sund`): Revenge when it's usable, else Sunder;
  `/run UIErrorsFrame:Clear()` hides the "not ready" error.
- "Shield Block + Sunder Armor" (`SBlk+Sund`, same short name so the game macro updates) now
  also tries Revenge before Sunder.
- Revenge note: Defensive Stance, after block/dodge/parry, 5 rage, 5 sec cooldown (Wowhead Forever).

## 2026-10-08 (Launch Plan: hunter pet quest)
- `h-pet`: location confirmed in beta by the owner (Zephras Isle). Now describes the chain:
  trainer at 10 -> three taming quests (one specific beast each, Taming Rod) -> Tame Beast.
  Still open: which three beasts (tag "which 3 beasts", test item `h-t-pet` reworded).

## 2026-10-08 (Launch Plan: "2 Hunters" plan back)
- Fourth group option `hunter` ("2 Hunters", Alliance Skyborne): the Dual Hunter plan dropped on
  2026-09-30, restored as an option next to 2 Hunters · Warrior · Druid (the default), 3 Hunters ·
  Druid and Paladin · Hunter · Shaman. It is the existing `hunter` base the other plans inherit,
  so its checklist needed no new items. Added: its Key differences column, the Hunter duo
  tactics card (from commit 0ddddc0), a "Dungeons and the other two" card, and it shares the
  Skyborne racials / Crowded camps / Professions & gold cards. Works in Compare.

## 2026-10-08 (Crafters: disenchant value)
- Every green, blue or purple armor/weapon recipe on Crafters shows `DE ≈ <value>` under its
  material cost: the expected value of what it disenchants into (chance × average count ×
  the price on this page). Hover lists the outcomes. Green text = worth more disenchanted
  than the materials cost. Whites, bags, shirts, kits and consumables show nothing.
- Uses the Classic 1.12 disenchant table (armor mostly dust, weapons mostly essence,
  blues one shard, epics shards/Nexus) by item level: **not verified for Forever**.
- Item metadata cache bumped to `wf-item-meta-v3` (new weapon flag `w`); live AH fetch
  also asks for the disenchant materials not in MATS (Illusion Dust, Eternal Essences,
  Brilliant Shards, Nexus Crystal).

## 2026-10-08 (Warrior macros: Thunder Clap, Shield Block + Sunder)
- Thunder Clap: no stance swap any more (plain cast). In Forever it works in Battle and
  Defensive Stance; the old macro swapped out of Berserker.
- New Tank macro "Shield Block + Sunder Armor" (`SBlk+Sund`): Shield Block (off the global
  cooldown) fires with Sunder in one press. Marked "Test in beta".
- Owner reviewed the remaining stance-swap macros; Charge keeps its swap until the Vanguard
  talent is taken (the Tank section already has the no-swap Vanguard Charge).

## 2026-10-07 (Crafters: recipe names in item quality colours)
- Crafted items show in their WoW quality colour (grey, white, green, blue, purple, orange),
  from Wowhead's tooltip data (cache bumped to `wf-item-meta-v2`). Enchants stay white.

## 2026-10-07 (Vendor prices for 22 materials)
- `VENDOR_ITEM`: vendor prices the owner checked in game (threads, dyes, spices, flux, vials,
  Simple Wood, Copper Rod, Star Wood, Maple Seed, Salt, milk, water...). A vendor item now
  costs the cheaper of vendor and live AH (AH water was 10c vs 23c at the vendor), on the
  cost views, shopping list and Crafters. Fine Thread 1s -> 90c, Simple Wood 38c -> 35c.

## 2026-10-07 (Crafters: by slot, highest level first)
- Each profession tab lists recipes in collapsible slot sections (Head, Neck, Shoulders,
  Cloak, Chest, Shirt, Bracers, Hands, Belt, Legs, Boots, Rings, Trinkets, Weapons,
  Shields & off-hands, Ranged, then Bags & quivers, Armor kits, Consumables, Materials &
  other), highest required level first; open/closed state remembered. Slot and level come
  from Wowhead's Forever tooltip data per item (cached per browser, `wf-item-meta-v1`);
  enchants are slotted by name and keep the game's strongest-first order.
- "By slot / A–Z" switch on the card. Alt character names no longer shown, class only.

## 2026-10-07 (Crafters: grouped by player, hunter Falseaim, no gathering professions)
- `crafters.json`: third export, Falseaim (Hunter): Cooking 193, First Aid 77,
  Leatherworking 152 (64 recipes, incl. Forceful/Mystic Heavy and Medium Armor Kits).
  All three characters carry `owner: "Venom"`, so they show as one Venom card.
- Import preview has "Show under player" (owner); cards group by owner, class tags show
  which character makes what (hover shows the character name).
- Mining, Herbalism, Skinning and Fishing are hidden (First Aid too, later the same day). Same-name recipes are kept apart
  by id (two "Dark Leather Boots").

## 2026-10-07 (Crafters: one card per name, Wowhead tooltips)
- Same-name characters merge into one card: professions combined (Cooking from both
  Venoms = 30 recipes), class tags (Priest / Paladin) on each recipe, best skill on the chip.
- Recipe names link to Wowhead Forever with hover tooltips (icon + stats) via Wowhead's
  tooltips.js.

## 2026-10-07 (Crafters: Venom the Paladin; addon 0.12.2 Home button)
- `crafters.json`: second export, Venom (Paladin, Oathbreaker): Blacksmithing 110 (50),
  Cooking 188 (28), First Aid 75 (5), Mining 95 (5). Same name as the Priest on
  Falselight, so they're two cards told apart by class.
- Addon 0.12.2: **Export professions** button on the Home tab. Released as r2f-v0.12.2.

## 2026-10-07 (First real profession export: Venom)
- First in-game export from addon 0.12.x works (modern profession window, `api` =
  "modern"): Venom (Priest, Falselight) with Cooking 150 (20), Enchanting 170 (51) and
  Tailoring 150 (73), every recipe with materials. Saved to `crafters.json`.
- All 24 enchants that are both in the page data and the export have the same materials
  in game; every hand-listed Venom recipe is in the export. Venom's colour is Priest white.

## 2026-10-07 (Addon 0.12.1: export on modern profession windows)
- 0.12.0 showed no Export button in game. 0.12.1 also reads the modern profession window
  (`C_TradeSkillUI`), and adds `/r2f profdebug` for diagnosis. Released as r2f-v0.12.1.

## 2026-10-07 (Crafters: profession export from the addon, addon v0.12.0)
- Addon 0.12.0: reads every recipe from open profession windows (trade + Classic craft
  window), Export button on the profession window and `/r2f profs` give an `R2FP1:`
  string (ADDON_PLAN 14, TESTING.md 21; never run in game yet). Released as r2f-v0.12.0.
- professions.html: new **Crafters** view: per character, profession tabs with skill and
  every recipe with material cost at live AH prices; "Who can make…?" search; paste an
  export to preview, owner saves it to `crafters.json` for everyone. Imported characters
  feed the BiS / Our crafts views.
- Venom also learned Bracer Stamina, Boots Lesser Stamina and Bracer Spirit (CRAFTERS).

## 2026-10-07 (Venom: Cloak Defense, Shield Lesser Stamina, Chest Greater Stamina, Boots Lesser Agility)
- `CRAFTERS`: + those four (all BiS or a stand-in) and Lesser Mystic Wand (not shown);
  later Bracer Stamina (BiS), Boots Lesser Stamina, Bracer Spirit.

## 2026-10-07 (Venom: five more from the trainer)
- `CRAFTERS`: 2H Lesser Impact, Bracer Lesser Intellect (BiS), Chest Minor Stats (same bonus
  as BiS Lesser Stats), Chest Intellect and Runed Golden Rod (neither in any ladder, not shown).

## 2026-10-07 (Venom learned 8 more enchants)
- `CRAFTERS`: Bracer Lesser/Minor Strength, 2H Lesser Intellect (BiS), 2H Lesser Spirit,
  Bracer Minor/Lesser Spirit, Shield Lesser Protection, Weapon Minor Beastslayer, Gloves
  Mining. The last five aren't BiS or a stand-in, so Our crafts doesn't list them.

## 2026-10-07 (Live prices: middle price for scarce items)
- Owner's in-game check vs AHledger (scan ~1 h earlier): 15 of 20 materials within ~5%.
  Greater Nether Essence showed 3g (one cheap listing of 6) vs 9g in game, so items with
  fewer than 10 listed now use the median instead of the cheapest listing.
- Owner's in-game prices saved to prices.json as the site fallback (adds Bauxite).

## 2026-10-07 (Front page: small Beta corner ribbon)
- The big red rotated "BETA" stamp (it covered the adventurers in every background) is now
  a small red corner ribbon in the hero's top right (`.beta-ribbon`, index.html).

## 2026-10-07 (New front page backgrounds, What's new page, Discord feedback)
- Front page: four new painted backgrounds (made by the owner outside Claude) rotate every
  2 days; old `hero.webp` removed. Link-preview image rebuilt from the first one.
- New `news.html` (What's new, Coming next, "Send an idea on Discord") fed by `news.json`.
- Shared footer on every page via `footer.js`: What's new with a "new" dot, Coming next,
  and the Discord #r2f-feedback invite; stays above the Addons/Macros bottom trays.

## 2026-10-07 (Professions: shopping list, craft or buy; link previews)
- Professions: **Shopping list** drawer (gold button under the top bar, bottom right on
  phones, `#list` opens it). "+ Shopping list" in every open row (BiS ladder, Our crafts,
  cost views) adds an enchant or kit; the drawer totals the materials at the page's
  prices, with −/+ per item, "Copy list" as plain text and "Clear list". Per browser
  (localStorage `wf-prof-list-v1`).
- Professions: **craft or buy** for armor kits. Live AH price of the finished kit next
  to its craft cost ("craft saves 11s" / "AH 22s cheaper"); details in the open row.
  Right now buying a Heavy Armor Kit is cheaper than crafting it.
- All pages: tab icon (`assets/favicon.png`, `assets/icon-180.png`), page description
  and link-preview tags (Discord etc.) with `assets/og.jpg` (hero crop + title).

## 2026-10-07 (Professions: live AH prices)
- Professions: material costs now use live auction house prices from AHledger (cheapest
  listing per item, refreshed every 10 minutes). Market picker (Normal/PvP, Alliance/Horde;
  EU shows up automatically once AHledger has it) or "Site prices". Each material shows
  where its price comes from (AH with stock count, vendor, site, your price). Owner's saved
  prices stay as the fallback; "Prices from AHledger" credit added.

## 2026-10-07 (Professions: one section per gear piece)

- Gear is split into Neck, Back, Chest, Wrist, Hands, Legs and Feet (weapons into
  One-hand, Two-hand, Ranged), on every Professions view. Armor kits show under both
  Hands and Legs. BiS view has jump links to each piece; the class filter hides pieces
  and links with nothing for that class.

## 2026-10-07 (Professions rework: stand-ins, our crafters, compact lists)

- BiS enchants is now the main view: one compact row per BiS enchant, grouped Gear /
  Weapons / Shield; open a row for BiS → 2nd best → 3rd best (gold/silver/copper medals)
  with materials, cost, who can make it and where to get it (muted, inside the row).
  Stand-ins researched in Wowhead's Forever data, e.g. Chest Minor Stats (skill 150, city
  trainer) is listed with the same +2 all stats as BiS Lesser Stats; Cloak Defense gives
  the same +60 armor as Greater Defense at skill 155; Bracer Lesser Agility (+4, Desolace)
  beats the list's Minor Agility (+3).
- New **Our crafts** view: recipes someone in the group makes that are BiS or a stand-in,
  tagged with the crafter (Venom), what each is used for and its cost. Junk enchants
  (Chest Lesser Absorption etc.) are no longer listed anywhere.
- Enchanting costs now list only BiS enchants; material price editor folded into one
  "N of M priced" bar; unpriced recipes show a quiet "—". Leatherworking costs use the
  same compact rows and include Thick Armor Kit.

## 2026-10-06 (Where each missing recipe comes from)

- BiS enchants: every recipe's source checked against Wowhead's WoW Forever data and
  shown as a badge (City trainer, Artisan trainer, Merchant's Favor, Vendor, Quest /
  centaurs, Rare drop), with the NPCs, zones and costs in the row details.
- Big Forever difference: 14 of the 15 trainer recipes (Enchanting 155–225) are not
  taught by city trainers, only by Kitta Firewind (Elwynn), Vanessa Sellers (Alterac),
  Melanie Sable (Riverglades) and Annora (Uldaman); Horde Hgarth. They get their own group.
- Corrections vs ForeverChanges: Bracer Lesser Healing Power also comes from the quest
  "Mysterious Mysticism" and from Molkar (Gelkis) for 15 totems, not only Gorhak for 60;
  Cloak Minor Agility is also a world drop; Iron Shield Spike plans drop in BFD, RFK,
  SM and SFK, not from the two mobs ForeverChanges named.

## 2026-10-06 (Professions page)

- New **Professions** tab (`professions.html`) with three views: **Enchanting costs**
  (the owner's 20 known enchants at AH prices), **Leatherworking costs** (Heavy,
  Forceful and Mystic Heavy Armor Kits; shows when buying a Heavy Armor Kit on the AH
  beats crafting it) and **BiS enchants** (every enchant ForeverChanges' level-30 BiS
  lists recommend across all 36 class/spec pages, marked "I can do" / "Missing", with
  class filter, skill box and per-recipe materials, sources and specs).
- Prices: one shared material list (Soul Dust used by both professions). Site-wide
  prices in `prices.json`, which the owner updates from the page via the same GitHub
  owner login as Group picks; visitors can try their own prices (kept per browser).
- Builds page: every build card links "Enchants for <Class>" to the BiS list filtered to
  that class. Index Tools: "BiS Enchants" link.
- Top bar: new Professions tab on every page; the bar now stacks at 1180px (was 960px)
  so "Road to Forever" doesn't wrap beside six tabs.

## 2026-10-06 (Legacy link removed from index Tools)

- Removed "Legacy Calculator" from the index Tools column: it's in the top bar
  now (Talent / Legacy Calc).

## 2026-10-06 (Our own Legacy calculator)

- New **Legacy calculator** on the Talent Calc page, our own code instead of linking
  to Wowhead's. A Talents / Legacy switch under the title swaps between the two;
  links are `talents.html#legacy/...`. Three trees (Professions, Adventure,
  Resourcefulness), 16 points, the 5/10-point gates, linked perks, "not in the game
  yet" slots, cast/cooldown on Dedicated Study, tooltips, touch +/− sheet, Copy link.
  Rules copied from testing Wowhead's calculator click by click.
- Always up to date: like the talent calc, it loads Wowhead's live Forever Legacy
  data (`nether.wowhead.com/forever/data/legacy-calculator`), and the credit line
  shows the game build the data is from.
- Top bar tab renamed "Talent / Legacy Calc" on every page. Index Tools "Legacy
  Calculator" and the Launch Plan's Legacy section now open ours.
- Top bar now stacks (title above the buttons) at 960px wide and below instead of
  820px, so "Road to Forever" doesn't wrap next to the longer tab name.
- New file `legacycalc.js`; Legacy styles appended to `talentcalc.css` (`lc-`);
  cache-bust bumped to `?v=20261006a` on talents.html and builds.html.

## 2026-10-06 (Tools column wider)

- Index Tools column is now wider than General Resources (same total panel
  width, so it doesn't push further into the countdown), and "Dungeon Loot
  Tables" fits on one line. MythicSim link renamed "DPS Sim Tier List (Lvl 60,
  predicted)" -> "DPS Tier List (Lvl 60)" so it fits on one line too.

## 2026-10-06 (Index Tools column trimmed)

- Removed the two external talent calculator links (Zockify, ForeverChanges)
  from the index Tools column; our own Talent Calc in the top bar replaces them.
- Removed Wowhead's "DPS Tier List (Beta, Lvl 20)": still level-20 only
  (last updated 2026-09-24) and no level-30 PvE DPS list exists yet
  (Mobalytics' is 1–20 leveling, SeeMeta's is theory-crafted raid tiers).
  Re-add if Wowhead or another source publishes a level-30 one.

## 2026-10-05 (Addons in a 2–3 column grid)

- Addon cards now sit side by side: 3 per row on wide screens, 2 on laptops,
  1 on phones, with smaller name/Download buttons. Opening a card's Details
  only grows that card. Page about 40% shorter. AtlasLootClassic Continued is
  labelled "AtlasLoot Continued" to fit (full name on hover). Shorter intro
  with the install folder.

## 2026-10-05 (Compact addon cards)

- Addons page is much shorter: each card is now one compact row with the
  Select checkbox in a strip on the left, the addon name on the left and the
  Download button on the right of the same line, the version underneath, and
  the description/notes folded behind a small "Details" toggle.

## 2026-10-05 (Downloads without leaving the page)

- CurseForge **Download** buttons now open CurseForge's download page in a
  small pop-up that our page closes again after 9 seconds, once the file has
  started; you stay on the Addons page the whole time. Tested in the owner's
  Chrome (ThreatMaster arrived, pop-up closed itself). Falls back to a normal
  new tab when pop-ups are blocked.

## 2026-10-05 (Addon downloads: what CurseForge allows)

- Tested in the owner's Chrome: CurseForge won't let other sites start its
  files (forgecdn links and the `/api/v1/.../download` address never produced a
  file; only CurseForge's own download page did). So each CurseForge
  **Download** button now opens CurseForge's download page for that exact
  Forever file in a new tab, where the file starts after ~5 seconds. Road to
  Forever still downloads directly from its GitHub release.
- The bottom tray's button steps through the ticked addons ("Next: Questie
  (2 of 3)"), one per press, since browsers allow one new tab per click.

## 2026-10-05 (Download addons straight from the Addons page)

- Every addon card has a **Download** button that fetches its WoW Forever file
  through CurseForge's own download address (Road to Forever from its GitHub
  release), plus a Select checkbox. A bar at the bottom downloads every ticked
  addon in one go (one after another; the browser may ask once to allow
  multiple downloads). The addon name still opens its CurseForge page.
- Verified in a real browser: all 12 CurseForge download links resolve to the
  right Forever file (1.60.1) and the Road to Forever 0.11.0 release zip exists.
- **WeakAuras Forever was removed from CurseForge** (project and files 404 in a
  real browser; WebFetch had served a cached copy). Replaced with
  **ForeverAuras** 0.50.6-BETA.1 (WeakAuras fork for Forever, `/fa`); the
  Battle Shout aura recommendation moved to its card with `/fa` import steps.

## 2026-10-05 (Six more addons on the Addons page)

- **New "Our own addon" section** at the top of `addons.html`: Road to Forever
  0.11.0 (tag `r2f-v0.11.0`, Oct 3), linking to its GitHub release, with a
  "test with one talent point first" warning for the untested C_Traits learning
  and install steps.
- **Added to "What we use"** (each linked to its WoW Forever file, verified on
  the file page): Archivist for Forever 1.0.7, AtlasLootClassic Continued
  12482, Forever Bestiary 0.5.0, Prat 3.0 3.9.112, Questie v12.0.3+v1.0.4.
  List re-sorted alphabetically.
- CLAUDE.md's addon check covers the new slugs, multi-flavor files and how to
  version-check our own addon from its `r2f-v*` tags.

## 2026-10-05 (Addon versions from CurseForge)

- **Addons page:** every addon card now shows its latest WoW Forever version and
  upload date, and its button links straight to that Forever file on CurseForge
  (not the project page, so nobody grabs a Retail/Classic build). A "Versions
  checked on CurseForge" date sits under the lede. Checked today: Forever Bag
  Mover 0.5.0, ForeverLayers 1.1.1, ForeverPlus 0.8.6, Leatrix Maps
  1.60.12-forever (link was pinned to old 1.60.03), Leatrix Plus
  1.60.11-forever, ThreatMaster 0.4.0, TomTom v4.3.11 (multi-flavor file incl.
  Forever), WeakAuras Forever 1.3.0.
- **Daily version check:** a scheduled task re-runs the check every morning and
  pushes updates; procedure documented in CLAUDE.md under `addons.html`.

## 2026-10-05 (Library Books checklist page)

- **New page `library-books.html`:** all 40 WoW Forever library books in an
  8-trip Alliance route from Stormwind (A–H, plus a "not collectable for
  Alliance" group: 2 Horde-only turn-ins, 2 books missing in Forever). Each book
  has a checkbox, location note, a `/way` chip that copies a TomTom command, and
  tags (Alliance-only turn-in, Group, Hard solo, L60 → Jennea Cannon). Progress
  bar marks the 10/20/25 reward tiers. Ticks persist per browser in localStorage
  `wf-library-books-v1` (keyed by book id; keep ids stable). Filter All / To do /
  Done, Reset all with an in-page confirm. Data is the `BOOKS` + `TRIPS` objects
  in the page script. Coordinates are the Forever beta spots (Zockify, WoWSoD
  Pro/Wowhead data, ForeverChanges), checked 2026-10-05.
- **Landing page:** the Cozy Sleeping Bag plaque now sits in a `.plaque-row`
  beside a new "Library Books" plaque (stacks on narrow screens). Book icon is
  hotlinked from `wow.zamimg.com` like the class icons.

## 2026-10-03 (Warrior macro additions, BACKLOG fix, WeakAuras recommendation)

- **New Warrior (General) macros:** a stance toggle (click swaps Battle <>
  Defensive, Ctrl = Berserker, Alt = Defensive — kept alongside the existing
  3-way stance dance), a stance-cooldown button (Retaliation/Shield
  Wall/Recklessness, whichever matches your current stance), a one-button
  ranged weapon macro (Bow/Gun/Crossbow/Thrown), and an off-hand <> shield
  swap (Class QoL, template with your own item names).
- **New Warrior (Tank) macro:** Taunt + equip a 1-hander and shield in one
  press (template, your own item names).
- **Fixed a wrong BACKLOG finding:** "Weapon-swap macro doesn't mention the
  combat restriction" assumed WoW blocks weapon swaps in combat — it doesn't;
  only armor swaps are blocked. Removed the finding.
- **Addons page:** added a recommended WeakAuras aura under the WeakAuras
  Forever card — "Battle Shout reminder (Warrior)" (wago.io/MtMe4SbEJ), with
  the 3-step Copy import string / `/wa` / Import / Done flow.

Ran `python build.py`; every macro still ≤255 characters (longest new one is
the stance-cooldown macro at 162).

## 2026-10-03 (Rogue macro fixes and additions)

- **Fixed:** melee strikes (Sinister Strike, Backstab, Eviscerate, Hemorrhage,
  Mutilate, Rupture, Garrote, Ambush, Cheap Shot, Kidney Shot) now use
  `melee()` so they include `/startattack [harm]`. Left Sap, Gouge, Blind,
  Distract, Kick and Expose Armor alone — `/startattack` breaks the
  damage-breaks-stealth/CC ones, and Expose Armor isn't a melee strike.
- **Fixed:** Distract is ground-targeted (`[@cursor]`), not a harm-target cast
  — it never actually worked as `dpsHarm()`.
- **Fixed:** the two poison macros used `/use Main Hand Weapon` / `/use Off
  Hand Weapon`, which aren't real slash commands and never worked. Replaced
  with one macro: left-click applies to slot 16 (main hand), right-click to
  slot 17 (off hand), with a `/click StaticPopup1Button1` line to confirm the
  "replace enchant" popup.
- **New:** mouseover versions of Gouge, Blind, Kick and Pick Pocket
  (`[@mouseover, harm, nodead][harm, nodead]`), alongside the existing
  target/focus versions.
- **New:** one-button ranged weapon macro (Bow/Gun/Crossbow/Thrown, picked by
  `[equipped:...]`).
- **New:** grenade at cursor (Iron Grenade, swap to the one you carry).
- **New:** sharpening stone, same left/right-click pattern as the poison fix
  (Rough Sharpening Stone, swap to the one you carry).

Ran `python build.py`; every macro still ≤255 characters (longest unchanged
at 204, none of the new/changed Rogue macros come close — longest new one is
the ranged-weapon macro at 133).

## 2026-10-03 (Addon v0.11.0: free talent points from C_Traits + one-click "traits" learning)

Two fixes in one release. (1) Free talent points read 0 on WoW Forever while
Blizzard's window showed 17 unspent (real screenshot): `Minimap.FreeTalentPoints` only
knew Classic's `UnitCharacterPoints`. `Talents.FreePointsInfo()` is now the single
source: `C_Traits.GetTreeCurrencyInfo(configID, treeID, true)` (applied points), else
`UnitCharacterPoints` unchanged; "unknown" is shown as unknown, not 0, and keeps Learn
off. (2) New "traits" learn mode for Forever: `C_Traits.PurchaseRank(configID, nodeID)`
per point, `C_Traits.CommitConfig` when the purchase is visibly staged, confirmed by
applied rank AND free points dropping (events only trigger re-reads; 2 s timeout is
final); never commits the player's own staged changes; any anomaly stops the run and
falls back to guided mode for the session; traits points are never re-sent. Classic
direct and guided modes unchanged; plan/order code byte-identical to v0.10.5 (source
test). Never run against a real Forever server: TESTING.md 20 (one point, disposable
character first). See `ADDON_PLAN.md` 13.12. Suite: 10927 checks, 0 failed (9389
before); luacheck 0 warnings. Tag `r2f-v0.11.0`.

## 2026-10-03 (Addon v0.10.5: tolerate position jitter in talent nodes)

Follow-up to v0.10.4, found with live data: a dump of all 50 nodes of a Paladin's
trait tree has 13 distinct posX values, with Protection's first column at both 5020
and 5030 (10 units of jitter in Blizzard's data; real column steps are 590-600).
v0.10.4 ranked every distinct value as its own column, saw 5 Protection columns and
refused the tree ("couldn't read your talents yet"). `Talents.lua` now snaps values
closer than 20% of the median gap onto one grid line (X before the pane split, and
Y) before ranking. The tolerance is relative, so it doesn't depend on the scale, and
it changes nothing when there's no jitter. Real fixture reads 4/4/4 columns with link +
hash equal to `talentcalc.js`; synthetic Y jitter, multi-pair jitter, other scales,
a too-close-but-real column and a jitter-majority refusal are tested. See
`ADDON_PLAN.md` 13.11. Suite: 9389 checks, 0 failed (9259 before); luacheck 0
warnings. Tag `r2f-v0.10.5`.

## 2026-10-03 (Addon v0.10.4: read talents through C_Traits, corrects v0.10.3)

v0.10.3's premise was wrong: `LoadAddOn("Blizzard_TalentUI")` returns `false,
"MISSING"` on WoW Forever and the Classic talent globals never exist, so Preview
still failed. Talents live in the trait system (`C_Traits`), the API WeakAuras
Forever reads them with. `Talents.ReadTrees()` now reads the active trait config;
node positions are ranked into tier/column (verified against 8 real Paladin nodes
and Wowhead's row/col for the same node ids), and the three panes, which are one
trait tree on Forever (Paladin: 1 tree, 50 nodes = Wowhead's 17+16+17), are split by
the gaps between columns. Same output shape, so links, hash, preview and learning
order are unchanged. Learning on Forever is now always guided (the addon no longer
calls `LearnTalent` without Classic's `GetTalentInfo` confirming the address).
Tooltips via `SetSpellByID`; `TRAIT_CONFIG_UPDATED` handled. See `ADDON_PLAN.md`
13.10 for evidence and what's still unverified (non-Paladin classes, Prot/Ret
positions). Suite: 9259 checks, 0 failed; luacheck 0 warnings. Tag `r2f-v0.10.4`.

## 2026-10-02 (Addon v0.10.3: fix Talent Preview on a fresh login)

> Superseded by v0.10.4 above: the Blizzard_TalentUI premise was wrong.

Reported from real in-game testing: Preview always failed with "couldn't read
your talents yet" until the player had separately opened their real Talent
window. Root cause confirmed via `/dump GetNumTalentTabs()` in-game: that
function (and `GetTalentInfo`) don't exist as globals until Blizzard's own
on-demand `Blizzard_TalentUI` addon loads, same as `Blizzard_Calendar`/
`Blizzard_MacroUI`. Found the fix by reading RXPGuides, a working third-party
addon already on the client, which already solves this exact problem and
separately has a proven working `LoadAddOn` call to copy the pattern from.
`Talents.ReadTrees()` now force-loads `Blizzard_TalentUI` itself. See
`ADDON_PLAN.md` 13.9. Full suite re-run: 8770 checks, 0 failed. Tag
`r2f-v0.10.3`.

## 2026-10-02 (Addon v0.10.2: version/author footer on the Home tab)

Requested from real in-game testing: no way to see the addon's version or who
made it without opening the TOC file. Added a quiet line at the bottom of the
Home tab that reads the TOC's own `## Version:`/`## Author:` fields through
`GetAddOnMetadata` (`C_AddOns` first, bare global fallback, plain no-version
line if neither exists — never a second hardcoded copy). Hovering it shows the
TOC's `## Notes:` text. See `ADDON_PLAN.md` 12.4.2. Full suite re-run: 8688
checks, 0 failed. Tag `r2f-v0.10.2`.

## 2026-10-02 (Addon v0.10.1: fix the per-character macro slot limit — 18 to 30)

Reported from real in-game testing: the Macro Book's Character counter should
read out of 30, not 18. `Macros.Limits()`'s fallback (used because
`MAX_CHARACTER_MACROS` isn't defined on WoW Forever's client, same quirk as
other legacy globals found this week) was hardcoded to vanilla/Classic Era's
18. User confirmed the real number by counting WoW Forever's `/macro`
Character tab directly: 30 slots (5 rows of 6). Fixed the one constant;
updated `ADDON_PLAN.md`, `BACKLOG.md`, `TESTING.md` and the Lua test stub/
assertions to match. Full suite re-run: 8608 checks, 0 failed. Tag
`r2f-v0.10.1`.

## 2026-10-02 (heal() and util() macros: add self-cast fallback)

Reported from real gameplay: Holy Light (and every other `heal()` macro — Flash
Heal, Healing Wave, etc.) did nothing at all with no mouseover and no friendly
target, since `/cast [@mouseover, help, exists][help] SPELL` has no fallback
clause. Added `[@player]` as a third clause, matching the pattern `buff()`
already used, so these now heal yourself instead of fizzling.

Also added the same fallback to `util()` (friend-or-foe spells: Dispel Magic,
Remove Curse, Penance, Holy Shock) for consistency — user's explicit call,
accepting that Dispel Magic/Remove Curse self-cast with no target could strip
one of your OWN beneficial buffs, same risk a Dispel Magic button always has
used on the wrong target. Fixed two hand-written "Inner Focus + Greater Heal"
macros (Discipline, Holy) that duplicated the old pattern by hand instead of
calling `heal()`. Left the Soulstone mouseover item-macro alone (self-casting
a soulstone on yourself doesn't make sense). Updated `CLAUDE.md`'s documented
macro style rules and `build.py`'s markdown-cheatsheet pattern notes to match.
Rebuilt `macros.html`/`wow-forever-macros.md`; every macro still ≤255 chars
(longest unchanged at 204).

## 2026-10-02 (Addon v0.10.0: Macro Book class picker, Remove from library confirm, Tidy up tooltip)

Requested from the first real in-game testing session (not in the original addon
plan): on a Paladin, the tester imported Warrior macros and saw no Warrior tab,
since the book only showed the logged-in class (ADDON_PLAN.md 5.7).

- **Addon v0.10.0** (tag `r2f-v0.10.0`): `UI/MacroBook.lua` gets a class picker (row of
  `UI-Classes-Circles` check buttons, own class pinned first, only classes with
  library macros, hidden when no other class has any). Other classes are browsed
  **read-only**: drag/click refused in the book and, independently, in
  `Macros.Ensure`/`Create`/`Replace` via the new `Macros.UsableHere`; grey icons, no
  `Learn later`, Shift-click and the right-click menu still work. Slot counters and
  on-bars checks stay this character's, with a note while previewing. Browsed class is
  a session-only Lua local (relog/reload = own class), nothing new in SavedVariables.
  Import prefers a new Universal/own-class tab (`Import.Diff` `firstNewOwn`), else opens
  the imported class's preview. DPS tab icon follows the tab's class.
- **Remove from library** (right-click) now has a confirm popup, removes the library
  entry only (real macro and its record untouched; re-import counts it as new); allowed
  on previewed classes too. **Tidy up** gets a tooltip that contrasts it with Remove
  from library. Single right-click delete chosen over a bulk check-box mode.
- **Tests:** `run_tests.py` 8608 checks pass (was 8310): new `test_class_picker` and
  `test_remove_from_library` on template + fallback paths; 23 hand mutations each fail
  the suite. luacheck 0 warnings. Decisions in `ADDON_PLAN.md` 5.10; in-game checks in
  `addon/RoadToForever/TESTING.md` 17.

## 2026-10-02 (Addon v0.9.1: fix the Interface number — addon wasn't loading)

First real in-game install (0.9.0) showed the addon in the AddOns list but
flagged "Incompatible" — the game refused to load any of it, so there were no
errors to see, no minimap icon, and `/r2f` did nothing. Root cause: the TOC's
`## Interface: 11507` was always a Classic Era placeholder, documented as
needing a real beta check (ADDON_PLAN.md section 11) that hadn't happened
until this report came in. Confirmed the real number via `/dump
GetBuildInfo()` on the live Forever client: `tocversion=16001`. Fixed the TOC,
updated ADDON_PLAN.md/TESTING.md to mark this beta check done, re-ran the full
test suite (8310 checks, 0 failed). Tag `r2f-v0.9.1`, no addon code changed.

## 2026-10-02 (Addon plan: Quick settings, Road to Forever addon v0.9.0)

- **Addon v0.9.0** (tag `r2f-v0.9.0`): the last item of the addon build. Home tab gets
  **Quick settings**, three check boxes that set CVars directly (new `QuickSettings.lua`):
  Max camera zoom = `cameraDistanceMaxZoomFactor 4` (unticked = `GetCVarDefault`, never
  a hardcoded number), Hide guild names = `UnitNamePlayerGuild 0/1`, Hide PvP titles =
  `UnitNamePlayerPVPTitle 0/1`. Boxes are redrawn from `GetCVar` on every Home refresh
  (tab open, combat change, new `CVAR_UPDATE` handler), nothing stored in
  SavedVariables; writes are read back (refused/clamped values reported). Out of combat
  only: boxes grey out, and `QuickSettings.Set` checks `R2F.InCombat()` before
  `SetCVar` (refused, not queued). Global `GetCVar`/`SetCVar`/`GetCVarDefault` with a
  `C_CVar` fallback; a missing CVar greys its box out.
- **Macro Book** hides exactly `ANY/Zoom`, `ANY/HideGuild`, `ANY/HidePvP` (exact-id
  lookup, only while the matching box can work) with a note on the Universal tab. The
  three macros stay on the website (`data.py` untouched) and in the addon's library.
- **Tests:** `run_tests.py` 8310 checks pass (was 8006): new `test_quick_settings` on
  both template and fallback paths (CVar stubs in `wow_stubs.lua`), ids checked against
  macros.html's data, look-alike ids not hidden; 15 hand mutations each fail the
  suite. luacheck 0 warnings. Decisions in `ADDON_PLAN.md` 12.4.1; in-game checks in
  `addon/RoadToForever/TESTING.md` 16 (incl. whether `SetCVar` is really
  combat-blocked for these CVars, unconfirmed).

## 2026-10-02 (Addon plan, step 10: talent learning, Road to Forever addon v0.8.0)

- **Addon v0.8.0** (tag `r2f-v0.8.0`): Learn talents is live. Confirm popup (`Learn N
  talent points? Only a trainer reset can undo this.`), then a resumable, event-driven
  state machine at the end of `Talents.lua` learns step 9's `LearnOrder` one point at a
  time: re-verify on the live game (preview/conflicts, tier rule, `GetTalentPrereqs`,
  free points), `LearnTalent` (its only call site, combat-checked), wait for
  `CHARACTER_POINTS_CHANGED` or the 0.5 s `C_Timer` timeout, re-read the rank; a point
  that didn't land stops the run with 13.5's message. `PLAYER_REGEN_DISABLED` stops it
  mid-run; Learn talents continues a stopped run (no second popup) and waits for a point
  still in flight instead of re-sending it (no double rank). Popup accepted in combat
  -> `Macros.RunOrQueue`. Tab: `Learning X / N`, rest locked, Cancel -> Stop, stop/done
  line. Fallbacks: Blizzard's talent preview if present and switched on (fill only,
  Blizzard's button commits); **guided mode** (new `UI/TalentGuide.lua`) when
  `LearnTalent` is missing or blocked (`ADDON_ACTION_FORBIDDEN`/`BLOCKED`, or the first
  point refused): our own glow frame on `UIParent` anchored over Blizzard's talent
  button, `Click X (2 of 21)`, nothing of Blizzard's modified.
- **Tests:** `run_tests.py` 8006 checks pass (was 6223): a fake server in
  `wow_stubs.lua` (Classic's learn rules, async answers, combat raises), full/partial/
  resumed runs, every stop path and message, combat interrupt + resume, no double send,
  re-verification cases, guided mode, preview mode; a source test pins the single
  `LearnTalent` call. 24 hand mutations each fail the suite. luacheck 0 warnings.
  Decisions in `ADDON_PLAN.md` 13.8; in-game checks in `addon/RoadToForever/TESTING.md`
  15 (**not run on a real client yet**; do them on a test character first).

## 2026-10-02 (Addon plan, step 9: talent import preview, Road to Forever addon v0.7.0)

- **Addon v0.7.0** (tag `r2f-v0.7.0`): the Talents tab replaces its step-6 placeholder
  (new `UI/TalentPanel.lua`). Paste a site talent link (full URL, `talents.html#...`,
  `#...` or bare `class/code`), Preview: three 4x7 mini trees (learned / learned now
  with gold glow and `+N` / later / not in build / red conflict), tree headers
  `current -> planned`, the game's talent tooltip + `Build: X / Y`, and 13.4's
  summary line. `Talents.lua` gained `ParseLink` / `Preview` / `Plan` / `Summary` /
  `LearnOrder`, mapping digits through step 8's own `ReadTrees` (no second sort).
  Hash on import: match -> preview; none -> yellow "Older link" line; different ->
  13.3's stop message, except on a non-English client, where it gets a yellow "can't
  be checked" line (names are translated, so it could never match; ADDON_PLAN 13.6's
  hand-off). Sanity checks (rank over max, no such talent / tree) show as red
  conflicts. Learn talents is present but disabled until step 10; Copy my build is a
  button on the tab (`/r2f copybuild` kept as a shortcut). Last link remembered per
  character; preview re-runs on `CHARACTER_POINTS_CHANGED` / `PLAYER_LEVEL_UP`; Home's
  Talents line shows free talent points (12.4). Read-only, so it works in combat.
- **Tests:** `run_tests.py` 6223 checks pass (was 5837): every link the real
  `talentcalc.js` makes for the fixture builds parses and previews as exactly that
  build; all hash cases; every summary sentence word for word; mini-tree states and
  widgets on template and fallback paths; the fake client's `LearnTalent` raises and is
  never called, and a source scan finds no talent-learning call. 18 hand mutations of
  the new code each fail the suite. luacheck 0 warnings. Decisions in `ADDON_PLAN.md`
  13.7; in-game checks in `addon/RoadToForever/TESTING.md` 14.

## 2026-10-02 (Addon plan, step 8: talent export + `~hash`, Road to Forever addon v0.6.0)

- **Site, `talentcalc.js`:** every talent link the site hands out now ends in a
  4-character check, `talents.html#<class>/<code>~<hash>` (ADDON_PLAN.md 13.3):
  djb2 over the class's talent names in link order (`,` between talents, `;`
  between trees, UTF-8 bytes), `mod 36^4` in base36, zero-padded. New
  `instance.link()` (Copy link in both modes, builds.html's Open in Talent Calc,
  talents.html's address bar), `TalentCalc.treeHash` / `hashFor` / `cleanCode`.
  `instance.encode()` and stored codes (saved builds, `group-builds.json`) stay
  without the hash. **Readers ignore everything from `~`** (calculator, talents.html
  hash, saved-builds import), so old and new links both open; before this a hash
  with digits would have been read as extra ranks (`35~111` -> `350111`).
  `talentsaved.js`: its Copy link adds the hash once the page has the data.
  `?v=20261001b` -> `?v=20261002a` for all three files on talents.html and builds.html.
- **Addon v0.6.0** (tag `r2f-v0.6.0`): new `Talents.lua` reads the character's
  talents (`GetNumTalentTabs` / `GetNumTalents` / `GetTalentInfo`, sorted tier then
  column = the link's digit order), encodes them exactly like the site, adds the same
  hash from the game's own talent names, and shows the full site link in the copy
  box (`/r2f copybuild` until the Talents tab gets its button in step 9/10).
  Read-only, so it works in combat (reasoning in ADDON_PLAN.md 13.6). The copy box
  takes a per-use hint line.
- **Cross-checked, not hand-traced:** `addon/tests/run_tests.py` runs the real
  `talentcalc.js` in Node (`talent_link_check.js`) and `Talents.lua` under Lua 5.1
  on one fixture (`talent_fixture.json`: unsorted ids, a non-ASCII name, an empty
  tree) plus a Python reference: identical hash per class and identical links for 7
  builds, matching hand-worked codes. Also run once on Wowhead's live Forever data
  (9 classes, hash + one link each, 18/18 identical; data not stored). Mutations of
  either side (separators, sort, UTF-8, modulus, zero/dash stripping, the `~` rule)
  each fail the suite. `run_tests.py` 5837 checks pass (was 5655; +166 talent
  checks on the template and fallback paths, +16 "TOC file exists" checks for the
  new file), luacheck 0 warnings; a Playwright run of talents.html /
  builds.html confirmed the hashed links, the `~` rule, the saved-builds import and
  the new `?v=`. Decisions in `ADDON_PLAN.md` 13.6 (incl. a locale caveat for step 9);
  in-game checks in `addon/RoadToForever/TESTING.md` 13.

## 2026-10-02 (Addon plan, step 7: release pipeline, Road to Forever addon v0.5.0)

- **Release workflow** `.github/workflows/release.yml`: pushing an `r2f-v*` tag
  builds `RoadToForever-<version>.zip` with `git archive --prefix=RoadToForever/
  HEAD:addon/RoadToForever` (top folder `RoadToForever/`, unzips straight into
  `Interface/AddOns/`; `addon/tests` and `addon/art` can't get in) and publishes it
  as a GitHub Release via `softprops/action-gh-release@v2`. 0.x tags are
  pre-releases, 1.0.0+ normal releases. Release notes = that version's section of
  `addon/RoadToForever/CHANGELOG.md`. The run fails if the tag's version differs
  from the TOC's `## Version:`.
- **Tag prefix settled:** `r2f-v*` is final (the plan's `addon-v*` was never used;
  the four existing `r2f-v0.1.0`..`0.4.0` tags stay as they are, without releases).
- Addon bumped to **0.5.0** (tag `r2f-v0.5.0`, the first real release) with no Lua
  change, to keep "each plan step = next minor version, tag = TOC version".
- **Macros page:** the export tray's "How to import" step 1 now names the zip and
  says to unzip it into `Interface\AddOns\`. The Download link stays on the
  Releases page (`/releases/latest` skips pre-releases, so it has nothing to show
  until 1.0.0).
- Verified locally: the workflow's `git archive` command on the commit's tree gives
  the expected 19 files under `RoadToForever/`, every extracted `.lua` compiles
  under Lua 5.1, luacheck 0 warnings, `run_tests.py` 5655 checks pass, YAML parses,
  actionlint clean, the version/notes steps replayed for good, mismatched and
  malformed tags. The workflow itself
  can only run on GitHub (`TESTING.md` 12). Decisions in `ADDON_PLAN.md` 8.1.

## 2026-10-02 (Addon plan, step 6: Road to Forever addon v0.4.0, main window, minimap button, logo)

- The addon now has **one main window** (`UI/MainWindow.lua`) with Home / Macros /
  Talents tabs at the bottom and the new logo as portrait (tag `r2f-v0.4.0`). The
  step-3 Macro Book was reparented into the Macros tab (same code and public
  functions, no separate window). **Home** (`UI/Home.lua`) shows library / on-bars
  counts, a Talents placeholder and Import macros. Position and last tab are saved.
- **Minimap button** (`Minimap.lua`): logo icon, tooltip, left-click toggles the
  window, right-click menu (MenuUtil when the client has it, else our own menu
  frame; never UIDropDownMenu), drag around the rim (round and square minimaps),
  lock/hide from the menu, Settings or `/r2f minimap`. **No libraries embedded:**
  LibDataBroker-1.1 is "All Rights Reserved" with no reuse grant, and LibDBIcon
  can't load without it, so the button is our own; if another addon already loaded
  LibDBIcon, it's registered through that copy. Findings per library in
  `ADDON_PLAN.md` 6.10.
- **Logo:** hand-written `addon/art/logo.svg` (gold road curling into an infinity
  sign on a navy disc), exported by `addon/art/export_logo.py` (resvg + Pillow) to
  `media/logo64.tga` / `logo128.tga` (32-bit with alpha).
- Full slash-command set (`/r2f`, `/r2f macros`, `/r2f talents`, `/r2ft`,
  `/r2f minimap`, `/r2f help`, `/r2f import` kept); the three key bindings now open
  the main window's tabs.
- Tests: `addon/tests/run_tests.py` now 5655 checks (was 5346), new main-window,
  Home, reparented-book, minimap, menu, slash-command, LibDBIcon-backend and TGA
  cases on both template and fallback paths; luacheck 0 warnings. Decisions in
  `ADDON_PLAN.md` 6.10; in-game checks in `addon/RoadToForever/TESTING.md` 11.

## 2026-10-02 (Addon plan, step 5: Road to Forever addon v0.3.0, Settings, Remove all, key bindings)

- The Macro Book's **Settings** button opens a new panel (`UI/Settings.lua`):
  Character / Account slots first (`R2FDB.settings.slotsFirst`, steers every new
  `CreateMacro`, never moves existing macros), Show / Lock minimap button (stored in
  `R2FDB.minimap` in LibDBIcon's format for step 6, which must add
  `R2F.Minimap.Apply`), and **Remove all Road to Forever macros** (tag `r2f-v0.3.0`).
- **Remove all** deletes every unedited macro the addon made, on bars or not, in
  character and account slots, clears all created-macro tracking, keeps edited
  macros as the player's own (ADDON_PLAN 5.8; the step brief said "regardless of
  edited", the spec won, see 6.9) and leaves the library alone. Same combat rule as
  Tidy up: greyed out in combat, queued if accepted in combat.
- **Key bindings** via `Bindings.xml` (loaded by the client, deliberately not in the
  TOC): Toggle Road to Forever / Open Macros (both toggle the Macro Book for now),
  Open Talents (placeholder until steps 6/9).
- Tidy up re-checks "not on a bar" at delete time (a queued Tidy could otherwise
  delete a macro put on a bar meanwhile).
- Tests: `addon/tests/run_tests.py` now 5346 checks (was 5202), new Tidy-up slot,
  slotsFirst, Remove all, Settings UI, combat and Bindings.xml cases on both
  template and fallback paths; luacheck 0 warnings. Decisions in `ADDON_PLAN.md`
  6.9; in-game checks in `addon/RoadToForever/TESTING.md` 7, 9, 10.

## 2026-10-02 (Addon plan, step 4: Road to Forever addon v0.2.0, updates)

- Re-importing now updates real macros the addon already made, if the player
  hasn't edited them (`EditMacro`, same combat-checked/queued write path as every
  other macro write). Hand-edited macros are left alone, the library still takes
  the new version, and the import preview + chat say which were updated and which
  kept (tag `r2f-v0.2.0`).
- **Changed marker** in the Macro Book: a green up-arrow on macros on your bars
  that an import changed, cleared the first time you hover it (stored per
  character in `R2FCharDB.changed`).
- On login, a character's own unedited macros catch up with the shared library
  (an import on another character can't reach them). Dragging an older macro
  from the book updates it first.
- Tests: `addon/tests/run_tests.py` now 5202 checks (was 5131), new update /
  kept-edit / Changed-flag / combat-queue / login-sync cases; luacheck 0 warnings.
  Decisions in `ADDON_PLAN.md` 6.8; in-game checks in `addon/RoadToForever/TESTING.md` 8.

## 2026-10-02 (Addon plan, step 3: Road to Forever addon v0.1.0)

- New `addon/RoadToForever/`: the in-game addon's first version (tag
  `r2f-v0.1.0`). `/r2f` opens a spellbook-style **Macro Book** (Universal + own
  class tabs, 2 x 6 grid, tooltips, paging, slot counter); **Import** reads the
  site's `R2F1:` string with a new/updated/unchanged preview into an unlimited
  account-wide library; dragging or clicking a macro creates the real macro
  (character slots first) and puts it on the cursor, with a Replace / Keep mine
  popup when the name is taken; **Tidy up** deletes unused unedited macros the
  addon made. Nothing touches macros in combat. Addon details:
  `addon/RoadToForever/CHANGELOG.md`.
- Not run in the game yet: `addon/RoadToForever/TESTING.md` is the beta
  checklist (Interface number, templates, CreateMacro+PickupMacro, icons, relog,
  combat, paste speed).
- Out-of-game tests in `addon/tests/` (not shipped): real Lua 5.1 via `lupa`
  against a fake client, with import strings generated by the site's own
  `importString()` code (all 389 site macros round-trip into the addon), plus a
  luacheck run under the same Lua 5.1 (0 warnings). Build-time judgment calls
  are in `ADDON_PLAN.md` section 6.7.

## 2026-10-01 (Addon plan, step 2: site export mode)

- `macros.html` (via `template.html`) has a **Pick macros for the game** toggle
  at the right end of the spec row (question-mark macro icon, spec-pill style).
  Turning it on shows a checkbox on every macro pill, a tri-state checkbox on
  every group heading and section heading, and checkboxes on search results
  (so you can search "taunt" and tick across classes). Ticking a pill's box
  never switches the code panel; clicking the pill text still does. Selected
  pills get a 60% gold border. Real `<input type="checkbox">`s, visually
  replaced, keyboard and screen-reader accessible.
- A sticky **export tray** slides up at the bottom: "N macros selected", class
  chips with counts, Clear, **Copy import string** (shows "Copied" for 2 s plus
  "Now type /r2f in the game and click Import."), a Select menu ("Select all for
  <class>", "Select everything"), an empty-state hint, and an expandable "How to
  import (3 steps)". Stacks into two rows with full-width buttons under 640 px.
- Copy import string builds the `R2F1:` format from `ADDON_PLAN.md` section 7
  (records in page order, `\x1F`/`\x1E` separators, UTF-8 safe base64), using
  the ids/short names/icons build.py already embeds. Selection persists in
  localStorage `wf-export-v1`; unknown ids are dropped on load.
- Build-time judgment calls are written into `ADDON_PLAN.md` section 4.5
  (Universal's section is sent as `Universal`, Download link goes to the
  Releases page until step 7, "Select everything" is ~83 KB, etc.).
- Tested in headless Chromium (Playwright): toggle, pill/group/section
  cascades, keyboard toggling, reload persistence, search ticking, menu,
  mobile layout, and a decode round trip of the copied string against the
  source data; plus a byte-for-byte match against an independent Python
  encoding of two Universal macros.

## 2026-10-01 (Addon plan, step 1: macro data)

- `M()` in `data.py` now takes `short` (in-game macro name, max 16 chars) and
  `icon` (texture name, for macros with no `#showtooltip` spell to show its own
  icon). Every macro across Universal and all 8 classes got a `short` name,
  following `ADDON_PLAN.md` section 3.2's naming rules (abbreviations players
  already use, ` F` = focus, `@` = mouseover, `X>Y` = priority, `X/Y` = Shift
  modifier, `X+Y` = combo, ` me` = self-cast). Warrior and Paladin names came
  straight from the plan's tables; the other six classes' names were proposed
  by Claude Code and approved by the user before committing.
- `build.py` assigns each macro a stable id (`<CLASS>/<short>`, `ANY/<short>`
  for Universal) and fails the build with a clear message on a `short` over 16
  characters, a duplicate `short` within a class + Universal, or a macro with a
  body but no `short` whose `name` is over 16 characters. Ids and short names
  now also flow into the JSON embedded in `macros.html` and into
  `wow-forever-macros.md` (short name shown in backticks next to the full name).
- Full spec: `ADDON_PLAN.md`. This is step 1 of 10; see `BACKLOG.md` for what's
  next (site export mode, then the addon itself).

## 2026-10-01 (Warrior + Paladin macro pass)

- Warrior and Paladin macros regrouped into role sections: **General** (all specs),
  **Tank**, **DPS** (+ Paladin **Healer**). `template.html`/`build.py` render
  "General" like "Shared". New `melee()` helper and `stance(..., attack=True)`.
- Warrior: every melee strike now has `/startattack [harm]` (Heroic Strike,
  Cleave, Rend, Hamstring, Sunder, Slam, Execute, Overpower, Revenge, Shield Bash,
  Concussion Blow, Shield Slam, Mortal Strike, Bloodthirst, Pummel, Mocking Blow,
  Charge + Rend opener). Intimidating Shout deliberately left without it.
- Warrior new: Victory Rush (Forever, level 20, any stance, verified on Wowhead's
  Forever spell page), Victory Rush > Sunder (tank) and Victory Rush > Heroic
  Strike (DPS) one-button priority macros (beta-test flagged), Heroic Strike /
  Cleave on Shift, Charge for Vanguard tanks (no stance swap), mouseover Taunt,
  Sweeping Strikes. Slam moved to General (level 20 in Forever).
- Warrior fixes for Forever: Thunder Clap no longer forces Battle Stance (now
  usable in Defensive too), level notes on Berserker-stance abilities (30+),
  Shield Wall/Shield Block/Revenge notes updated to Forever values.
- Paladin: added "Auras on one button" (Shift/Ctrl modifiers).
- Sources: foreverchanges.pro (Warrior spellbook + changes), Wowhead Forever
  (Victory Rush), classicwowforever.com and kami-labs.fr macro lists.

## 2026-10-01 (level-30 Paladin + Warrior)

- Added level-30 builds to `DATA30` in `builds.html`: Paladin Retribution and
  Protection (Tank), Warrior Protection (Tank) and Arms. Warrior Fury has no
  level-30 build (Arms took its place at 30). Crusade still isn't in Wowhead's data,
  so the Ret build doesn't use it.

## 2026-10-01 (level-30 builds)

- `builds.html` got a "Level 20 / Level 30" toggle row under the class roster
  (`?level=30` in the URL works too). Level-20 builds are unchanged in `DATA`; the
  new level-30 builds live in `DATA30` (Priest Shadow, Warlock Affliction, Mage
  Arcane/Frost/Frost AoE/Fire, Rogue Combat, Shaman Enhancement, Hunter BM), each
  stored as a talents.html share `code` that the calculator loads directly
  (`mountSync` gets `code` instead of `preset` when a build has one). Their `talents`
  list (name/rank/icon, no desc) is only the static fallback row. No level-30
  rotations yet. Paladin and Warrior show "No level-30 build yet".
- Checked the "Crusade" Paladin talent question: neither Wowhead's Forever data nor
  Mobalytics' Forever calculator has a talent called Crusade (both list the same 50
  Paladin talents, 17 in Retribution), so our calculator isn't missing anything.

## 2026-10-01 (pink button)

- Added a tiny round pink button next to Unmute in the landing page top bar
  (`.sound-btns` wraps both). Each press plays the full "Ha! Gayyyy!" YouTube clip
  (`yOQqBMz70iM`) once through the same hidden player; no loop. While it plays the
  main button shows "Mute" and can stop it; the ENDED handler resets it after.

## 2026-10-01 (music clip)

- Landing page Unmute button now plays only the 1:05-1:12 chorus hook of the
  YouTube track (`loadVideoById` with `startSeconds`/`endSeconds`) once per click,
  instead of autoplaying the full song muted on a loop. When the clip ends the
  button resets to "Unmute" so it can be replayed; clicking "Mute" mid-clip pauses.

## 2026-10-01 (later)

- Replaced the landing page hero image (`assets/hero.webp`) with a new one: four
  Skyborne adventurers (Warrior tank, Druid healer, two Hunters with a panther and
  a wolf) standing on a cliff path above a sea of clouds at sunset, a floating sky
  isle with ruins/waterfalls in the distance. Generated via Gemini (full scene in
  one pass, after SDXL-only attempts — background generation, character inpainting,
  and compositing separately — kept hitting style/lighting mismatches or garbled
  faces); any leftover baked-in title text was removed with a local SDXL inpaint
  pass (small-resolution, not the 4x-upscaled version — doing it at full upscale
  size maxed out the GPU's 12GB VRAM and produced nothing). Final image was a plain
  LANCZOS resize to 2560×1080, not an AI upscaler — both 4x-UltraSharp and
  4x-AnimeSharp distorted the painterly faces into a waxy/photoreal look when
  tried. See the Personal Dev Support Folder's `local-tools-inventory.md` for the
  working ComfyUI ⁄ inpainting ⁄ ESRGAN setup notes from this session.

## 2026-10-01

- **Owner login for Group picks.** Group picks moved from a hard-coded array to
  `group-builds.json` in the repo. The site owner signs in on the Group picks tab with
  a GitHub fine-grained token (this repo only, Contents read/write; kept in the
  browser, checked with GitHub) and can then publish a saved build to the group, or
  edit/remove picks, straight from the site; each change is a commit that Pages
  redeploys in about a minute. Nobody else needs repo access, and visitors only read.
  Replaces the "Copy as group pick, paste into the file" workflow.
- **Saved builds sidebar** on the Talent Calc and Builds pages (`talentsaved.js`),
  so we can keep builds and look them up together instead of passing links around.
  Every calculator gets a gold "Save build" button; a floating "Saved builds" button
  opens a right-hand drawer styled like the Buyable quests one. **My builds** is
  stored per browser (name, note, class/tree/points summary; open, copy link, edit,
  delete, import a pasted link, copy all as links for the group chat; saving after
  opening a build offers "Update" or "Save as new"). **Group picks** is a curated list
  in the repo (`GROUP_PICKS`) seeded with the level-20 BM Hunter and Warrior Tank
  builds for the 2 Hunters · Warrior · Druid plan; "Copy as group pick" turns any
  saved build into a ready-to-paste entry. No backend: GitHub Pages is static, so
  shared lists live in the repo, not in a database.
- Shared calculator files are now loaded with a `?v=` cache-busting query on both
  pages: the first live check served a cached old `talentcalc.js` next to the new
  sidebar script and Group picks failed to render.

## 2026-09-30 (evening)

- Talent calc tree tabs (Builds cards) made much more visible: framed nav-style
  buttons, the open tree filled with the class color, trees with points in class color
  with a filled point badge (`tc-has`), empty trees grey.
- Builds page: every build card now has a live, preloaded talent calculator (compact
  mode: tree tabs, opens on the build's main tree, points editable, "Reset to build",
  "Copy link", "Open in Talent Calc"). Presets come from each build's talent names +
  ranks, matched against Wowhead's Forever data (all 13 builds verified valid). The old
  icon row stays as the fallback if the data can't load. Calculator engine moved to
  shared `talentcalc.js` + `talentcalc.css` (tc- prefixed), used by talents.html and
  builds.html. Also fixed builds.html being wider than a phone screen (hidden rotation
  tooltips).
- New **Talent Calculator** page (`talents.html`), our own code, replacing the external
  Zockify link in the top bar (now `talents.html` on all six pages; index.html's nav
  gained the link it was missing). All 9 classes including Druid, live Wowhead Forever
  data (Sep 24 beta trees: Strider Kick, Twist of Light, Templar's Bulwark present,
  Wyvern Sting gone), prerequisite arrows, tier/prereq/removal rules, 51-point cap,
  required level, per-tree reset, shareable `#class/digits` links, hover tooltips with
  next rank, touch bottom sheet with −/+.
- Removed the remaining "Venom & Trollmann" mentions from page text (Addons and Builds
  ledes) and docs; the site now says "we" throughout. Hero image still shows the old
  dwarf/gnome group with nameplates — replacement (4 Skyborne: Warrior, Druid healer,
  2 Hunters, no names) tracked in BACKLOG.
- Site renamed "Road to Forever" (was "Venom & Trollmann's Road to Forever") in the
  top bar on all five pages, the index `<title>` and hero `<h1>`; launch-plan lede
  now says "How we get ahead…". ROADMAP's locked site-title decision updated.
- Launch Plan: dropped Dual Mage, Dual Hunter and Triple Hunter. New Skyborne plans
  **2 Hunters · Warrior · Druid** (`hwd`: Warrior tanks, Druid heals) and
  **3 Hunters · Druid** (`h3d`: Druid flexes tank/heal), alongside Paladin · Hunter ·
  Shaman. Hunter texts folded into a shared `hunter` base profile (data key only);
  `base` now resolves up a chain. New steps: Druid Bear Form and Warrior Defensive
  Stance at 10 (Classic quests, flagged), plus beta checks. Ghost Wolf confirmed at
  20 (unverified tag removed). Compare defaults to hwd vs trio; stale saved modes
  (mage/hunter) fall back to hwd. Mage Legacy card removed.

## 2026-09-30 (afternoon)

- Launch Plan: two new plans next to Dual Mage / Dual Hunter. **Triple Hunter**
  (`hunter3`, inherits the hunter plan, with its own loot/pet/tank-and-healer notes)
  and **Paladin · Hunter · Shaman** (`trio`): Dwarves (Alliance Skyborne can't be
  Paladin or Shaman), Coldridge → Dun Morogh → Ironforge, then the shared route.
  Trio-only steps: Holy Strike/Seal of Fury/Righteous Fury/Consecration trainer
  levels, Shaman totem quests, Ghost Wolf, plus beta checks. Compare now picks any
  two plans; Key differences table is data-driven (`DIFFS`); "Duo play" renamed
  "Group play" with per-plan cards; new trio Legacy path card.

## 2026-09-30

Forever class-change pass (research: Warcraft Tavern, Mobalytics, Output Lag,
forever-hunter wiki, Zockify, classicwowforever.com). New `BETA` note prefix in
data.py marks macros that still need confirming in beta.

- Paladin: removed all "Judge + reseal" and "Crusader opener" castsequences
  (Judgement no longer consumes seals in Forever). Added Holy Strike + auto-attack,
  Divine Shield / BoP self with press-again cancel, Voice of Truth, Seal swap
  (Twist of Light, beta), new Holy section (Holy Shock friend or foe). Protection:
  Seal of Fury, Judgement taunt (mouseover + focus), Templar's Bulwark. Blessing of
  Kings moved Protection → Shared.
- Hunter: removed Wyvern Sting + focus (removed in Forever). Added Hunter's Mark +
  send pet, Volley at cursor (no cooldown now), Feign Death (clean), Intimidation +
  pet attack (replaced plain Intimidation). Multi-Shot note about its new cast time.
- Priest: Silence gets /stopcasting; added Prayer of Mending (Holy), Penance (Disc).
- Warlock: Wrack (Affliction), Incinerate (Destruction), Bane of Havoc focus; Dark
  Pact flagged for beta.
- Mage: Ice Block press-again cancel, Presence of Mind + Pyroblast, Arcane Blast.
- Rogue: Envenom → Venom, Pick Pocket + Sap.
- Shaman: Earth Shock (+ focus) get /stopcasting; Riptide, Water Shield, Lava Burst,
  Flame Shock > Lava Burst; Elemental Mastery macros flagged for beta; Stormstrike
  note updated.
- Warrior (Protection): Sunder + Heroic Strike.
- Hunter (Survival): added Strider Kick and a "Survival melee button" (Raptor Strike +
  Mongoose Bite + Strider Kick, beta-flagged). Strider Kick confirmed as the in-game name
  (Blizzard forum thread). Lacerate not added: it reads as the bleed from the Lacerating
  Strikes talent, not a button.
- Builds page, Paladin: Ret gets Holy Strike + Consecration (AoE); Prot swaps Seal of
  Righteousness for Seal of Fury (level 10, Judgement taunts), adds Holy Strike and
  Consecration (class spell at 20 in Forever, per wowforevertools.com trainer list).
  Icons checked against Wowhead's Forever tooltip data: Holy Strike really uses
  `classicon_paladin` in game (file 626003); Seal of Fury uses `spell_holy_sealoffury`,
  the same icon as Righteous Fury.

## 2026-09-29

- Universal › Misc / UI: removed "Mark mouseover/target with skull" and "…with cross".
  Duplicates of "Skull mark mouseover / target" under Targeting helpers, which already
  explains the marker numbers and the /tm vs ThreatMaster gotcha.
- Macros page: "Style patterns" on the Universal tab is now a collapsible section,
  collapsed by default (`details.patterns-wrap` in template.html).
- Warlock: "Shadow Bolt" became "Shadow Bolt + Imp Firebolt" (`/petattack [harm]`,
  `/cast [pet:Imp, harm] Firebolt`, `/cast [harm] Shadow Bolt`).
- Hunter: added "Aspect toggle: Cheetah ↔ Hawk" (`/castsequence reset=combat Aspect of
  the Cheetah, Aspect of the Hawk`) next to the existing combat-based aspect macro.
  Each press swaps aspects; resets to Cheetah after combat.

## 2026-09-28 (evening)

- Moved the Buyable quests button from bottom-right to top-right, just under the
  sticky top bar (follows the bar's height on mobile). Sidebar unchanged.
- Launch Plan: added a "Buyable quests" sidebar (floating button bottom-right, TOC
  link, or `#buyable`). Lists quests that can be finished with Auction House/vendor
  items instead of farming, sorted along our route (phase 1/2/3 + off-route) or by
  zone, with item counts, quest level, a gray-XP warning where our route reaches the
  zone too late, per-browser "done" checkboxes, and a Wowhead Forever search link.
  Harvesting the Harvesters is confirmed on Forever's Wowhead; the rest is Classic
  data, with a few recalled-from-Classic entries tagged "verify in beta".

## 2026-09-28

- Hunter: added three pet attack macros next to "Pet attack TT / target" —
  "Pet attack mouseover", "Pet attack mouseover / TT" and "Pet attack / Shift =
  follow" (Shift+press calls the pet back). No #showtooltip on purpose: /petattack
  isn't a spell, so #showtooltip would only show a red "?"; each note tells the
  player to pick the pet bar's Attack icon (Ability_GhoulFrenzy) in the macro window.

## 2026-09-29 (night)

- Found the real cause of the earlier "ThreatMaster steals Alt+1/Alt+2" report:
  it's not a keybind conflict at all — ThreatMaster registers the `/tm` slash
  command for itself, which collides with WoW's built-in `/targetmarker`
  shorthand. Any macro using `/tm` to mark a target silently calls ThreatMaster
  instead once the addon is installed. Traced this by reading through
  ThreatMaster's full Lua source (confirmed it sets no keybindings anywhere)
  and working through in-game diagnostics with the user.
- Fixed every macro in data.py that used the `/tm` shorthand (the two Universal
  mark-mouseover/target macros and Mage's Polymorph + Diamond mark) to use the
  full `/targetmarker` command instead, so they no longer collide with
  ThreatMaster. Updated CLAUDE.md with a standing rule to prefer full command
  names over shorthands that a popular addon might claim.
- Rewrote the ThreatMaster addons.html warning to describe the actual slash-
  command conflict and its fix, replacing the earlier (incorrect) theory that
  it silently claimed the Alt+1/Alt+2 keybinds directly.

## 2026-09-29 (evening)

- Flagged a known issue on ThreatMaster's addon card: it silently claims Alt+1
  and Alt+2, breaking any other keybinds on those combos, with no setting for
  it anywhere in-game or in the addon's own options. Confirmed by disabling
  the addon (the bindings came right back). Added a `--warn` color variable to
  addons.html for this kind of inline caveat.

## 2026-09-29 (later)

- Clarified that MythicSim's DPS tier list is a level-60 endgame simulation
  (confirmed: "one raid-boss target, level 63... Most specs use talents from a
  published level 60 guide build"), not a beta/leveling-relevant ranking —
  relabeled it "DPS Sim Tier List (Lvl 60, predicted)".
- Added Wowhead's level-20-scoped DPS PvE tier list ("DPS Tier List (Beta, Lvl
  20)") as the beta-relevant counterpart. Its actual tier content couldn't be
  independently verified (page is JS-rendered, unreadable via automated fetch),
  so it's linked as a real/maintained/correctly-scoped source, not a
  confirmed-accurate one.

## 2026-09-29

- Restyled the class-roster buttons on macros.html and builds.html to match the
  top-bar nav's framed gradient-button look (uppercase, bordered panel, hover
  glow, bright gradient when selected) instead of the plain flat/outline buttons
  they used before. builds.html's spec-picker pills got the same treatment.
- Addons: removed Platynator (replaced in-game by a working Plater setup) and
  added ForeverLayers, WeakAuras Forever, ThreatMaster, and TomTom. Redesigned
  every addon card to a single framed nav-style button linking to CurseForge
  (name only, no separate "CurseForge" pill) with the description below, and
  sorted the "What we use" list alphabetically.

## 2026-09-28 (night)

- Rebuilt builds.html as a JS-rendered class/spec picker (was static HTML per
  class before): pick a class from the icon roster, and — for classes with more
  than one build — pick a spec (Mage: Arcane / Frost (Ice Lance) / Frost
  (Piercing Ice) / Fire; Paladin: Retribution / Protection; Warrior: Tank /
  Fury). Added a Rotation section to every build (single-target and AoE ability
  lists, icons + arrows matching the talent-card style, a repeat glyph on
  loop-based rotations, and a confidence badge: "high" for build-matched guides,
  "medium" where reasoned from mechanics with no exact source found).
- Added 3 new Mage builds: Frost (Piercing Ice) and Fire, alongside the existing
  Frost (Ice Lance) build now relabeled, plus the previously-discussed Arcane
  spread as its own build.
- Fixed several wrong icons found during this pass (real icon filenames can be
  very unintuitive vs spell names): Rogue's Sinister Strike (was showing an
  unrelated TBC-era talent's icon), 3 Mage Arcane talent icons, Shaman's AoE
  (added Fire Nova Totem detonating off an already-placed Searing Totem — kept
  both, they're complementary not either/or), Hunter's AoE (added Multi-Shot,
  learnable at level 18), Warrior Fury's AoE (swapped Piercing Howl, a slow, for
  Cleave, an actual AoE damage tool).
- Made the builds-grid give same-size, side-by-side cards for multi-build
  classes (Paladin, Warrior) instead of one card growing taller from longer
  rotation text — capped card width and rotation-note line length.

## 2026-09-28 (evening)

- Added "DPS Sim Tier List" (mythicsim.com) to the landing page's Tools column —
  a simulated (not real-parse) DPS ranking, the only source found so far that
  discloses its methodology and is dated after the Sept 24 wand/Wizard Oil nerf
  patch. Chosen after a research pass found several other tier-list sites
  contradicting each other and predating that patch (see prior research in this
  conversation — not separately logged since no file changed for that research).

## 2026-09-28 (later)

- Replaced the Paladin "Hybrid (Prot/Ret)" build card on builds.html with two
  separate cards: Retribution (PvE) — the pure 0/0/11 build (Benediction 5/5 →
  Conviction 5/5 → Seal of Command 1/1) — and Protection (Tank) — the 0/11/0 build
  (Redoubt 5/5 → Precision 3/3 → Anticipation 2/5 → Shield Specialization 1/3).
  Verified talent existence/ranks/icons against foreverchanges.pro and
  cross-checked against community leveling-build guides.

## 2026-09-28

- Reorganized the landing page's side-links overlay: split into "General Resources"
  (Zockify, Wowhead, Icy Veins, Warcraft Tavern, Mobalytics, ForeverChanges) and
  "Tools" (2 talent calculators, Legacy Calculator, Best-in-Slot Gear, Dungeon Loot
  Tables, a new Hunter Pet Database link to beastmaster.io) as two side-by-side
  boxed columns, each link its own compact icon+title card. Cozy Sleeping Bag stays
  its own featured card above them with a shortened one-line description. Moved the
  Talent Calc link out of the top nav into the new Tools column.
- Corrected: beastmaster.io/forever is a Hunter pet database (588 tameable pets),
  not a talent calculator as originally assumed — filed it under Tools accordingly.

## 2026-09-27 (late evening)

- Launch Plan: fixed the Legacy points misunderstanding. Everyone starts at 0 points
  (earned from challenges, first at level 25); 16 is the per-character spend cap at
  launch, not a starting pool. Reagent Economy sits in Resourcefulness column 3 (needs
  10 points in that tree, so point 11 at the earliest), so it's no longer the "first
  pick". New "Legacy points" section: how points work, fastest sources, column gates
  (col 1 open / col 2 = 5 in tree / col 3 = 10 in tree), Well Rested and Talented
  explained, a perk-by-column table per tree (from Wowhead's Legacy Calculator), and a
  mage path (Thrill 5 → Resourcefulness 11 → Reagent Economy at 16) vs hunter path
  (Thrill 5 → Adventure → Frequent Flier at 11). Added level-25 and level-45 Legacy
  steps, two beta checks (Novice Spelunker dungeon list, respec rules), and updated
  the Compare table row.

## 2026-09-27 (night)

- Launch Plan: confirmed in-game that Aspect of the Cheetah trains at level 20 —
  dropped the `unverified` tag on that step. Tightened the Reagent Economy wording
  after checking its actual in-game tooltip ("class abilities no longer require
  reagents purchasable from vendors"): ammo is a weapon consumable, not a spell
  reagent, so it's almost certainly not covered — the beta test-list item now
  asks to confirm that exclusion rather than asking an open "does it cover ammo?"
  question.

## 2026-09-27 (evening)

- Launch Plan now has a Dual Mage / Dual Hunter / Compare switch. The route is the
  same for both; the hunter plan adds the level-10 pet quest, ammo/pet-food stocking,
  loot rules, pet roles, Aspect of the Cheetah, and swaps the Legacy, Deadmines-detour,
  dungeon-group and duo-play advice. Compare shows a key-differences table plus every
  phase side by side (shared steps full width, with a "show only differences"
  filter). Steps are now data-driven (`PHASES`/`DUO` in the page script); existing
  checkbox ids were kept so saved progress carries over. Choice is shareable via
  `?plan=`.

## 2026-09-27 (even later)

- Mage: added "Polymorph + Diamond mark" — marks the target with a diamond
  (`/tm ... 3`) and casts Polymorph in one macro, so the group can see at a
  glance which target is sheeped and not to break it.

## 2026-09-27 (later)

- Fixed the top bar on `launch-plan.html`, `macros.html`, `builds.html`, and
  `addons.html` (plus `template.html`, which `macros.html` is generated from):
  they were still using the older flex `space-between` layout, which pushes the
  nav links to the right edge instead of centering them like `index.html`'s top
  bar (title left / nav centered) has done since an earlier session. All 5 now
  share the same 3-column grid topbar style — pages without a mute button simply
  leave the third grid column empty.

## 2026-09-27

- Added `launch-plan.html`: the launch-week plan for the Alliance Skyborne mage duo
  (Zephras → Dalaran → Ironforge/Hall of Thanes → Darkshore → Ashenvale → Wetlands →
  Hillsbrad → Dalaran dungeon, then an unverified 30→60 outline), with checklists that
  save per browser, a table of all 9 new dungeons, duo/camping/Legacy tips and a
  beta-verification list. Added a Launch Plan link to the top bar on every page
  (`__PAGE_LAUNCH__` placeholder in template.html, rebuilt macros.html).
- Fixed 5 rank-badge errors across the builds.html talent cards, found after the
  user caught a wrong rank on Mage's Elemental Precision: Mage Elemental Precision
  3/3→5/5 (also reordered so Frostbite comes before Ice Shards, matching the
  actual level-up order); Priest Spirit Tap 1/1→5/5 and Twin Disciplines 2/2→2/5;
  Warlock Pandemic 1/1→1/3; Warrior Deflection 2/2→2/5. Cross-checked every
  talent's true max rank against foreverchanges.pro's WoW Forever talent
  calculator — everything else in every card was already correct.

## 2026-09-26 (later)

- Added the Rogue level-20 talent build card to builds.html (Improved Sinister
  Strike 2/2 → Improved Eviscerate 3/3 → Precision 3/3 → Malice 3/5), closing the
  last remaining gap in the armor-order build lineup (Priest, Warlock, Mage,
  Rogue, Shaman, Hunter, Paladin, Warrior — all 8 classes now have a build).
  Verified talent existence/ranks/icons against foreverchanges.pro's WoW Forever
  talent calculator.

## 2026-09-26

- Repointed the Cozy Sleeping Bag plaque on the landing page to
  foreverchanges.pro/cozy-sleeping-bag (covers both the buff explanation and the
  full quest-chain steps in one place). Simplified the plaque to the standard
  single-link pattern, dropping the old Wowhead title/description + separate
  "Quest chain route" sub-link structure and its now-unused CSS.
- Added community-recommended macros after a research pass across Reddit/Wowhead/
  Icy Veins/Warcraft Tavern: Mage Counterspell and Frost Nova now `/stopcasting`
  first so the interrupt/root fires instantly instead of queuing behind your
  current cast (same fix applied to the Counterspell focus variant); Rogue Kick
  gets the same `/stopcasting` treatment, and Rogue gained a missing Cheap Shot
  stealth-opener entry; Shaman gained a Windfury Weapon + Lightning Shield
  `castsequence` refresh macro; Warrior gained a Charge + Rend opener and a
  Battle/Defensive/Berserker stance-dance macro.
- Ran a full shortening audit across every class's macros — found nothing further
  to trim; the helper-function pattern already keeps every macro at its minimum
  legal form.
- Redesigned the macro cheatsheet's group display: each macro-type group (Damage/
  offensive, Wand, etc.) now shows a row of pill buttons (one per macro) plus a
  single code panel below that swaps when a pill is clicked, instead of listing
  every macro's own card. Modeled after warcrafttavern.com/forever's Hunter macro
  guide. Applies to every class and Universal; search results still use the old
  always-expanded list since search spans multiple groups/classes at once.
- Hunter: added an experimental "Raptor Strike + Mongoose Bite + Wing Clip" test
  macro (separate from the existing Raptor Strike + Wing Clip combo) to check
  whether WoW Forever's client fires more than one ability per GCD when chained.
- Hunter: combined Raptor Strike and Wing Clip into one macro (casts Wing Clip
  right after Raptor Strike).

## 2026-09-25

- Added a ForeverChanges (foreverchanges.pro) link plaque to the landing page's
  side-links overlay — reference site for talent/spell/item/dungeon changes vs.
  Classic.
- Added a full Mage class to the macro cheatsheet (Shared + Arcane/Fire/Frost), same
  class-icon treatment as the other classes, plus a Mage level-20 talent build card
  on the Builds page (Elemental Precision → Ice Shards → Frostbite → Ice Lance).
- Reordered the class roster on both the Macros page and the Builds page by armor
  type (Cloth → Leather → Mail → Plate): Priest, Warlock, Mage, Rogue, Shaman,
  Hunter, Paladin, Warrior. Rogue has no talent build yet, so it's skipped on the
  Builds page for now.
- Renamed the stale "TT-aware DPS" group label (left over from the dps()/dpsHarm()
  split below) to "Damage / offensive" everywhere it appears, since only Priest
  actually needs target-of-target awareness.
- Added talent build cards to the Builds page for Paladin (hybrid Prot/Ret), Priest,
  Shaman, Warlock, and both Warrior specs (Tank, Fury) — same icon+arrow+tooltip
  pattern established with the Hunter build.
- Added a full Rogue class to the macro cheatsheet (Shared + Assassination/Combat/
  Subtlety), same class-icon treatment as the other 6 classes.
- Split the dps() helper: Priest keeps target-of-target-aware DPS macros
  (`[@targettarget, harm, exists][harm] SPELL`); every other class (Shaman,
  Paladin, Warlock, Hunter, Warrior, Rogue) now uses plain `[harm] SPELL` via a
  new dpsHarm() helper, since only Priest actually needs TT awareness.

## 2026-09-24

- Added Leatrix Plus to the Addons page (modular UI quality-of-life addon).
- Added class icons (real in-game icons via Wowhead CDN) to the macros page roster,
  plus a self-hosted Universal-tab icon (wow4ever.quest's dwarf+bear emblem).
- Fixed Style Patterns cards forcing a horizontal scrollbar on longer macros — widened
  the card grid and wrapped long lines instead of scrolling.
- Added the real Addons page content: ForeverPlus, Platynator, Leatrix Maps, Forever
  Bag Mover (verified via the addon's local `.toc` after "ForeverBagMover" turned up
  no public trace — actual name is "Forever Bag Mover" by ColbyDolby), plus a link to
  wow4ever.quest's addon compatibility tracker.
- Added a third landing-page overlay plaque linking to wowtbc.gg's dungeon loot tables.
- Added two landing-page overlay link "plaques" (Zockify, Cozy Sleeping Bag with a
  ComfyUI-generated icon + quest-chain sub-link) and a new Addons top-bar page.
- Ran a Project Reviewer / Design Critic / Security Auditor pass: removed two stale
  pre-restructure files (`index.md`, `wow-forever-macros.html`) that were still live
  on the deployed site, removed dead `.tag` CSS, fixed `CLAUDE.md` doc drift, added a
  discoverability link to `wow-forever-macros.md`.
- Reformatted `data.py`/`build.py` for readability (one macro per line, section
  dividers, named functions) — verified byte-identical build output, no content change.
- Added `#showtooltip` to every spell-casting macro; added a Misc / UI group
  (camera zoom, guild/PvP title hiding, target marking, weapon swap).
- Made macro groups collapsible (`<details>`/`+`-`−` toggle); restyled the top-bar
  nav links as raised game-UI buttons.
- Ran the 10 WoW-specific AI roles applicable to a macro-only project (Macro Engineer,
  API Compliance Auditor, Debugger, Healing/Tank/PvP Macro specialists, QA Playtester,
  API Research Analyst, Technical Writer, Knowledge Base Architect) against the
  project. Most came back clean; the one fix applied: expanded "TT-aware" on first use
  in the macros page lede, since it's real jargon that was never explained anywhere.
  Confirmed via WoW Forever community usage that `/console` CVar macros (zoom, hide
  guild/PvP names) are real working patterns on this client, not stale Classic
  assumptions.

## 2026-09-24 (earlier) — Multi-page site build

- Turned the single-page cheatsheet into a multi-page site: `index.html` (landing/
  countdown), `macros.html` (generated cheatsheet), `builds.html` (placeholder).
- Built the landing page: ComfyUI-generated hero background (SDXL base + inpainting,
  6 heroes at Frostforge Pass gate, "Venom"/"Trollmann" nameplates in Cinzel),
  countdown to `2026-11-04T23:00:00Z`, local-timezone launch time.
- `build.py` now outputs `macros.html` instead of `index.html`.

## Earlier

- Initial macro cheatsheet: `data.py`/`build.py`/`template.html` generating a
  single-page site for Priest, Shaman, Paladin, Warlock, Hunter, Warrior — TT-aware
  DPS, mouseover healing, cleanse/dispel, wand/auto-attack, buffs, panic/defensive,
  targeting helpers, class QoL, and focus macros for every spec.

---

# Addon version history (0.x, detailed)

The in-game addon's developer log, merged in on 2026-10-13 (it used to be `addon/dev/CHANGELOG.md`). Newest first, by version, not by date.
The short player-facing notes shipped in the zip are still `addon/RoadToForever/CHANGELOG.md`. Old command names here (`/r2f who`, `/r2f rankdebug`...)
now live under `/r2f debug`. The detailed log stops at 0.30.0 (0.31 - 0.53 are in the dated entries above and in the addon's own
CHANGELOG); entries from 0.54.0 on are written here again.

## 2026-10-15 (Beta labels)
- builds.html and professions.html ledes now say level 30 data comes from the beta and can change before the November 4 launch (Mr.BiZ already did).

## 2026-10-15 (Workflow action versions)
- ci.yml / release.yml: actions/checkout v4 -> v6, setup-python v5 -> v6, setup-node v4 -> v6, softprops/action-gh-release v2 -> v3 (all on the Node 24 runtime; the inputs we use are unchanged). The release step is only exercised by the next tag.

## 2026-10-15 (Mr.BiZ cross-check tooling)
- bis/own/: tooltips.py (cached Wowhead tooltip fetch), stats.py (tooltip -> stats), check_scores.py, check_order.py, report.md, README.md. First run: ForeverDB's score is exactly stats x weights (1% hit = 10, 1% crit = 14); about 26 best picks differ in stats, nearly all level-scaled items; 19 of 414 slots would be ordered differently under our scoring. Nothing in the site or addon changed.

## 2026-10-15 (Plan positions)
- launch-plan-waypoints.json: Stormwind Harbor boat (22, 56), Dalaran dungeon entrance (8, 59), the Drowned City (21, 27), Steamwheedle Port boat (67, 22, approx), Mount Hyjal (53, 33 on the Kalimdor map, approx; zone "Kalimdor"), Blackmaw Hold gate (38, 32, approx), all read off the map by the owner. PlanData.lua regenerated.

## 0.66.3 (2026-10-16): guided talent mode removed
- Deleted UI/TalentGuide.lua (the glow over Blizzard's talent button) and the guided mode in Talents.lua / TalentPanel.lua / Locale.lua / Core.lua (owner's yes; last present in r2f-v0.66.2). `Talents.LearnMode()` returns "none" where it returned "guided" (no write API, or the session saw a write blocked): Learn talents then only prints `TALENT_UNAVAILABLE` (spend the points in Blizzard's window, /reload tries again), no popup, nothing written; a resumed run whose mode turned "none" stops with the same line. "staged" stops are no longer resumable. The note line on the Talents tab and the TALENT_GUIDE_* / TALENT_CONFIRM_GUIDED lines are gone. Direct, traits and preview learning untouched. Tests: the guided block became "learning off" checks; the source test checks the file and its TOC line are gone (24519 checks pass).

## 0.80.1 (2026-10-21): Swing timer in the setups

- **The swing timer is switched on by the setups and the general settings.** Setup Hunter and Setup Druid now turn on the game's "Enable Swing Timer" (Options > Advanced Options), and Undo puts it back. "My general settings" saves and applies it too. The addon does not know the setting's internal name, so it searches the game's list of settings for names containing "swing" and only touches ones that are plain on/off. `/r2f general swing` lists what it finds (send me that if the timer does not turn on).

## 0.80.0 (2026-10-21): General settings

- **My general settings** (new): set one character up the way you like it, then right-click the minimap button > **Save my general settings** (or `/r2f general save`). On any other character, right-click > **Apply my general settings** (or `/r2f general apply`): it lists what it will do, asks, then sets the same game settings (camera, auto loot, names and nameplates, class colours, silhouette, raid frames, floating combat text, chat behaviour and more), switches on the same Action Bars, and sets up your chat windows (made if missing, with their message types and channels, font size, colour, locked) and the class colours on names in chat. The Combat Log window is never touched. Graphics, sound and the Edit Mode layouts (where the chat windows sit) are already shared by your account, and what is on the buttons stays per class (Setup Hunter / Setup Druid). `/r2f general clear` forgets the saved settings. Written without being able to try it in the game: see TESTING 5.68. New file General.lua; the minimap menu and the menu tests got the two new entries.

## 0.79.2 (2026-10-21): Paladin seal timer

- **The Paladin seal timer no longer jumps to 1800.** When the game hides your buffs (in a fight, or right as you cast), the timer counts down from its own guess, and that guess for a seal was 30 minutes instead of the real 30 seconds. It now starts from 30 seconds; whenever the game lets the addon read the buff, the real time is used as before. Test: the seal case in the combat-timer block now expects ~30.

## 0.79.1 (2026-10-21): Cooldown numbers in combat

- **Cooldown numbers now work in combat.** In a fight the game hands addons the cooldown as a value they cannot read, so our own numbers went blank. The "Cooldown numbers on the buttons" box now turns on the game's own setting "Show Numbers for Cooldowns" (the game draws those itself, in combat too) and puts the old value back when you untick it. Our own numbers are only the fallback for a client without that setting (and stay blank in combat there). `/r2f debug bars` now also says whether the setting exists and how many cooldowns are unreadable.

## 0.79.0 (2026-10-21): Action bar overlays

- **Tweaks > Action bars** (new page, all four boxes off until ticked): **Red when out of range** (a red veil over the icon while the spell cannot reach your target), **Red when you lack mana, rage or energy**, **Cooldown numbers on the buttons** (the seconds left as a number on the button: 2h, 5m, 12, then 3.4 under ten seconds, yellow under 5 s and red under 2 s; the global cooldown gets none) and **Bigger cooldown numbers**. It works on the main bar and every extra bar (Action Bars 2 to 8). The addon only reads the game's buttons and draws its own frames on top of them, so nothing of the game's is changed and it cannot taint. If you also see the game's own small cooldown numbers, turn off "Show Numbers for Cooldowns" in the game's options. `/r2f debug bars` prints what this client gives, for a bug report.

## 0.78.0 (2026-10-21): Route log

- **Route log** (`/r2f route start [name]`, `/r2f route note <text>`, `/r2f route stop`, `/r2f route` for the status): off until you start it. While it records it writes down, in your own saved variables only, a timeline of your play: quests offered (by whom, where), accepted (quest level, objectives), objective progress (where a kill or item counted), handed in (xp, money) and abandoned; levels, zone changes and deaths; the NPCs you open a window with (quest giver, trainer, vendor, flight master, innkeeper); your own notes; and your position every ten seconds (the path you walked). Every record has the time since the start, your level and xp and the map position. It stores class and race, never your character name. A run that is on when you log out goes on at the next login. `python addon/tools/route_report.py` turns the saved file into a readable timeline, a quest table (with the quests each hand-in unlocked) and the path length per map.

## 0.77.2 (2026-10-21): Setup only where its layout exists

- **Setup Hunter / Setup Druid are now only offered to characters that have the matching Edit Mode layout saved** ("Hunter", "Warrior/Druid"). Everyone else sees no menu entry and no help lines for them, and `/r2f setup` just says the layout is missing. They are the owner's personal shortcuts; the README no longer describes them.

## 0.77.1 (2026-10-21): Setup Druid key bindings

- **Setup Druid sets the Druid's key bindings, for this character only.** The Warrior / Druid layout has its own bars (forms), so its keys differ from the account's: Q, E, F, CapsLock, the mouse wheel, Ctrl-1 to 5 and the rest now point at the Druid's buttons (59 bindings, taken from your Druid's own bindings file). It turns on "Character Specific Key Bindings" for that character, so your other characters keep the account keys. "Undo last setup" puts the old keys back.
- Setup Druid: your General macro is found under the name **atk** (it also still accepts "Attack"). The Hearthstone (both setups) is on bar 6 button **12**.

## 0.77.0 (2026-10-21): Setup Druid

- **"Setup Druid"** (minimap menu, or `/r2f setup druid`): the same one-click setup as the Hunter's (Action Bars 2 to 6, auto loot, raid frame options, the Edit Mode layout "Warrior/Druid", every button emptied first), with the Druid's buttons. Main bar: Attack (your own General macro) 2, Healing Touch 8, Regrowth 9, Rejuvenation 10, Moonfire 11, Wrath 12. Bar 3: the Teleport: Moonglade spell on button 4. Bar 4: Cat / Bear Form on 5. Bar 5: Thorns 3, Mark of the Wild 4.
- **Both setups (Hunter and Druid) now also place:** the racial spells Walk on Air (bar 2 button 7) and Read Ley Line (bar 2 button 10), taken from your spellbook; the Hearthstone from your bags (bar 6 button 11); and your own General macros Sit, Mark1 and Mark2 (bar 6 buttons 1, 2 and 3), found by name. Anything not found (not learned yet, not in your bags, no General macro of that name) is listed in the chat and its button left empty. "Undo last setup" empties these buttons too.

## 0.76.4 (2026-10-20): Theme test fixes, round 4

- **Setup Hunter's reload button** now opens the chat line with `/reload` ready: press Enter. Calling the reload from our button after the setup was blocked by the game, so this uses the game's own chat code instead (the window's Reload UI button was never affected).
- **Launch plan:** the Waypoint button no longer overlaps the place text (after the wider tick boxes of 0.76.2), and the "Quest shopping list" button is as wide as its label and a little lower.
- **Ember & Iron:** the logo and the close button are clear of the corner rivets.
- **The "Choose a look" gallery closes together with the main window.**

## 0.76.3 (2026-10-20): Theme test fixes, round 3

- **Talented perk switch** (Builds tab) now sits on the class row, right after the class name, so it can no longer touch the Load button in any look.
- **Frost & Void:** the group with Size, Opacity, Reload UI and the close button is smaller again and moved further in from the top right frame.

## 0.76.2 (2026-10-20): Theme test fixes, round 2

- **More fixes from the 0.76.1 test:**
  - Obsidian Night: on Home the Share card is taller, so "Export professions" sits under its text. The Launch plan shopping list has more room between the switch and the quest name, and so do the step rows. The Talented perk switch on the Builds tab is clear of the Load button. The source switches under the doll on the Gear tab have more room between them.
  - Frost & Void and Scribe's Tome: the logo, the title and the Size / Opacity / Reload UI / close group are smaller and moved in from the frame (down and to the left), so nothing touches the top corners any more.
  - Azeroth Reforged (and any look after visiting Scribe's Tome): the sidebar headings JOURNEY / CHARACTER / UI no longer sit under the buttons; they go back to their own places when you leave the contents look.

## 0.76.1 (2026-10-19): Theme test fixes

- **Fixes from the first test of 0.76.0:**
  - Obsidian Night and Gnomish Workshop: the Home cards in the lower rows sat above the window as blank boxes (they were placed upwards instead of downwards). They now sit under the countdown.
  - The window close button showed the picture of the look you came from; it now always matches the look in use.
  - The new looks are 40 px taller, so the buttons along the bottom of the Talents page (Reset, Save loadout, Loadouts, Recommended, Share, Learn this build) are inside the window. Pages in Ember & Iron, Frost & Void, Azeroth Reforged and Scribe's Tome start a little lower so the Tweaks tab buttons no longer touch the top bar.
  - Frost & Void: the group with Size, Opacity, Reload UI and the close button is smaller and fits its pill; the top right corner bracket is gone (it sat on the close button).
  - Scribe's Tome: no white glow over the contents line under the mouse.
  - **The "Choose a look" gallery now wears the look in use**: its frame, cards and text come from that look (a flat panel in its colours for Classic).

## 0.76.0 (2026-10-19): Themes get their own layouts, two light themes, the gallery

- **Every look now has its own layout, not just its own colours.** Each theme sets its window width, its own close (X) button, where Size and Opacity live and how Home is laid out:
  - **Frost & Void:** a wider window, a round close button, and Home as glass cards with the countdown as a ring (days in the middle, hours and minutes under it).
  - **Ember & Iron:** a wide window with a 4 x 2 tile sidebar, a title card that follows the page and a "Window gauges" panel holding Size and Opacity; Home has the big countdown plate, then "Work orders" rows and the settings in two columns.
  - **Obsidian Night:** a wider window with a top bar, cards on Home (countdown in mono numbers with the minutes in teal, launch plan, training, share) and a footer strip with the version line.
  - **Azeroth Reforged:** a wider window with the ornate gold frame and a crest on top, big stone countdown boxes under "Forever launches in" on a nested gold-dashed Home panel.
- **Two new light themes:** **Scribe's Tome** (a leather-bound book: the sidebar is a table of contents with dotted leaders and page numbers, the countdown is three wax seals) and **Gnomish Workshop** (cream and chunky, coloured tabs along the top, coloured cards, digit boxes for the countdown and a sun mascot). Fonts: Cormorant Garamond, Baloo 2 and Nunito (bundled, free to use, licence files included).
- **"Choose a look" gallery:** the Theme button on Home opens a gallery of all looks with a picture each. Click a card to try it on your window; "Keep this look" keeps it, "Revert" (or eight seconds, or closing the gallery) goes back. "Surprise me" tries a random one.
- **Own close buttons** for every look except Classic; Size / Opacity no longer have tick marks outside Classic and Azeroth.
- **Setup Hunter: the reload prompt** now opens from a timer, which should stop "Interface action failed because of an AddOn" when you press "Reload now" (not yet confirmed in game).

## 0.75.3 (2026-10-19): Setup reload prompt

- Setup.Finish offers ReloadUI via R2F.UI.Confirm; removed the 2.5 s hidden-bar check and SETUP_RELOAD.

## 0.75.2 (2026-10-19): Setup Hunter raid frames + clear all

- Setup.lua: `raidFrames` sets CVars raidFramesDisplayClassColor / raidFramesDisplayPowerBars / raidOptionDisplayPets to 1 (old values in `undo.cvars`); `clearAll` empties slots of bars 1-8 before placing (spells recorded for Undo).

## 0.75.1 (2026-10-19): Setup Hunter follow-ups

- Setup.lua `placeOne`: a spell on a target slot is picked up and recorded in `undo.cleared` (Undo restores it with PickupSpell/PlaceAction); non-spell occupants still skipped. Only the setup's own slots are cleared, not whole bars.
- Bars not showing until /reload: 2.5 s after SetActionBarToggles the multi bar frames are checked and `SETUP_RELOAD` printed if any is hidden (cause not found in the extracted UI; the toggle itself works).
- AutoShot macro `#showtooltip 18`.

## 0.75.0 (2026-10-19): Setup Hunter

- `Setup.lua`: `Setup.LIST.hunter` (class, layout name "Hunter", bars 2-6, auto loot, `place` rows = bar, button, library id, expected key). `Setup.Slot(bar, button)`: bar 1 = slots 1-12, Action Bar 2 = 61-72, 3 = 49-60, 4 = 25-36, 5 = 37-48, 6 = 145-156, 7 = 157-168, 8 = 169-180 (the pages in `multiactionbars.lua` of the game's UI). Bars via `SetActionBarToggles` (what the Options checkboxes call), auto loot via the `autoLootDefault` CVar, layout via `C_EditMode.SetActiveLayout(index)` where the index counts the two presets first and our saved layouts after (read from `EditModeManagerFrame.layoutInfo.layouts`, fallback `C_EditMode.GetLayouts()` + 2 presets), macros via `Macros.Ensure` (cursor) + `PlaceAction` one button at a time on timers, never over a filled button; keys checked with `GetBindingKey`, never rebound. State for undo in `R2FDB.setupUndo`. Entry points: minimap menu, `/r2f setup <name|undo>`. New data.py Hunter macros Serpent, AspMonkey, AspHawk, PetFollow. `addon/tools/backup_wtf.py` + `docs/beta-backup.md`: copy of the beta's Config.wtf, bindings, macros, Edit Mode layouts and our saved variables outside the repo. Druid setup (layout "Warrior/Druid") is next. TESTING 5.43.

## 0.74.1 (2026-10-19): ThreatMaster in the minimap menu

- `Minimap_.ThreatMasterAvailable / On / Toggle`: shown when `SlashCmdList.THREATMASTER` exists (ThreatMaster registers /tm and /threatmaster), calls it with "" in a pcall (its handler toggles its own window and saves `ThreatMasterDB.shown`); the tick reads that saved option (shown unless false). Nothing of its frames or the game's damage meter frames is touched. TESTING 5.42.

## 0.74.0 (2026-10-19): Frost & Void image set and orb chain

- 25 slices from Claude Desktop (`addon/art/sources/frost`, GAMMA 1.0). Set name `frost` (theme key stays "arcane", `deco = "frost"`). `buildArcane`: tiled starfield panel + a vertical `shade` gradient for the board's #14163A to #07070F, two ADD-blended glows, 9-slice frame (rounded 30, caps 32), 9-slice glass behind the pages (caps shown at 22), orb art 44x44 centred 16 px from the button's left, chain line `frost_link` tiled between the first and last orb. `MainWindow.SetNavLayout("chain")`: buttons 134 x 32, 38 px apart, group headings and the sidebar background hidden. Buttons use `SHAPE.frost` (16 px caps, 3 px pad), slider fill is the baked gradient clipped by texture coordinates (like Ember). `bgFloor` kept in the theme so it stays nearly opaque. Sora Regular / SemiBold instances cut from the variable font with fontTools. TESTING 5.41.

## 0.73.0 (2026-10-18): Obsidian Night image set and tab layout

- 20 slices from Claude Desktop (`addon/art/sources/obsidian`, GAMMA 1.0). `Deco.lua`: per-set `SHAPE` table (button caps / pad, groove thickness, knob size; the Obsidian button art is inset 3 px, so the button art reaches 3 px beyond the button via `bar.shape`), `buildObsidian` (9-slice frame, plate behind the pages on an anchor region, rule under the tabs, tab pills with `tab_on` / `tab_hover`, separators). `MainWindow.SetNavLayout(layout)` now takes nil / "grid" / "top": "top" lays the buttons out as a tab row (widths `TOP_W`, separators after Launch plan and Gear, `NavSeparators()`), hides the sidebar background, makes the window `WIN_H + 44` high and repositions every page (`placePages`). Theme "obsidian": `deco`, fonts (Space Grotesk Medium instance and JetBrains Mono Bold instance made from the variable fonts with fontTools), rule colour. Ember: selected tile label `#FFE8B0`. TESTING 5.40.

## 0.72.1 (2026-10-18): Ember top line, themed row highlight

- `ember_frame.png` rows 6-9 were opaque white (the "faint highlight" in the notes); softened to alpha 40 in the source PNG only (`make_ember.py` still has the white: ask Desktop to fix the generator). New role `highlight` (classic white = the game's own look, others the accent) tints the Home entry's highlight texture. Lesson: an edit helper must compute the new text BEFORE opening the file for writing (an assertion left `Home.lua` empty once; restored from git, not committed).

## 0.72.0 (2026-10-18): Ember & Iron image set

- 24 slices from Claude Desktop (`addon/art/sources/ember`, converted with `slices_to_tga.py`, GAMMA 1.0) in `media/ember`. `Deco.lua` is per image set now: `imageSet(th)` picks the set from the theme's `deco` token when `R2F.Images[set]`; shared controls (buttons, switches, tick boxes, slider track / knob / fill, card or display plate) use `P(name)`; Ember adds `buildEmber` (panel tile, heat strip, 9-slice frame, plate, rivets, slot tiles). `MainWindow.SetNavLayout(grid)` moves the same nav buttons between the list and the 2 x 3 tile grid and hides the group headings; labels switch to `L.NAV_TILE`. Slider fill for Ember is one baked-gradient picture clipped by texture coordinates. `Theme.lua`: the "forge" theme (key kept, so saved choices survive) gets `deco = "ember"`, `titleColor`, `font.number`; `R2FNumber` uses Chakra Petch. Fonts added to `media/fonts` with OFL files. TESTING 5.39.

## 0.71.4 (2026-10-18): small spacing fixes

- Nav gem 12 px at right -4, label offset 32; Theme button width = label + 32 (170 to 200 px), re-fitted on a theme change. From the 0.71.3 screenshot.

## 0.71.3 (2026-10-18): page buttons, thinner sliders, title fit

- `Tab.LayoutPageButtons` (Gameplay): width = label width + 28 (84 to 170 px), wrap at 500 px, re-run on a theme change. Slider groove / fill 10 px high, knob 22 px (the design's 10 / 22). `Deco.FitTitle`: scales the window title down to 200 px in image mode. Corpse arrow confirmed in game (0.68.2).

## 0.71.2 (2026-10-18): no pre-darkening

- `GAMMA = {"azeroth": 1.0}`: the owner's game had `Gamma 1.5` in Config.wtf (Brightness 50, Contrast 50), and a texture is drawn as v ** (1 / Gamma), which is exactly the 0.67 measured in 0.71.1. The artwork is made for the default (1.0), so the converter no longer compensates. Default to be confirmed in game with `/dump GetCVarDefault("Gamma")` (not in the interface files).

## 0.71.1 (2026-10-18): gamma, switches, all buttons

- Measured on the owner's screenshot of 0.71.0: texture value v was drawn as about 255 * (v / 255) ** 0.67 (panel tile mean 43 shown as 77, inset 22 as 49, button 51 as 97). `slices_to_tga.py` now pre-darkens the colour channels with `GAMMA = {"azeroth": 1.5}` (alpha untouched); tune that number if a different graphics gamma setting changes the look. Switch leftovers: `SetVertexColor` on the code-drawn caps reset their alpha, so the parts are hidden with `SetShown` now. `UI.ThemeButton` (tint, font, `Deco.AddButton`) is applied to all 21 `UIPanelButtonTemplate` buttons in `UI/*.lua`; the primary button (gold art, dark text) is used for "Export professions".

## 0.71.0 (2026-10-18): Azeroth round-2 slices, countdown cards

- 34 slices from Claude Desktop (round 2, sha-identical to the `_1` download), converted with `slices_to_tga.py`. `Deco.lua`: nav icons (NAV_ICON, tinted per state with the design's label colours), heading images with word widths 76 / 100 / 17 for the fading line, `Deco.Card` (9-slice card art or a flat rectangle for other themes), `Deco.StyleSwitch` (UI.Switch 44x22 track + knob, UI.BlackBox check images), slider fill clipped to the value (`updateFill`), button states (normal / hover / disabled, primary variant ready, not used yet). `Home.CountdownParts` / `UpdateCountdown` with `R2FNumber` font. Not drawn from the design (flat in code, per Desktop): panel and inset top-to-bottom gradients. TESTING 5.38.

## 0.70.1 (2026-10-18): countdown, sidebar names, image buttons

- `Home.CountdownText` / `Home.LAUNCH_AT` (1793833200 = 2026-11-04 23:00 UTC), OnUpdate once a second on the Home page frame. `MainWindow.NAV` regrouped (journey / character / UI) and `TAB_PLAN`, `TAB_TALENTS`, `TAB_BIS` renamed ("Launch plan", "Builds & talents", "Gear (Mr.BiZ)"); tests updated. `Deco.AddButton` draws UIPanelButtonTemplate buttons (Reload UI, Theme) from the button art in image mode and hides the template art. Still missing against the design: nav icons, themed checkbox / switch / primary button, countdown cards, letter-spaced headings (need more art from Claude Desktop).

## 0.70.0 (2026-10-18): Azeroth Reforged image slices

- `addon/art/slices_to_tga.py <theme>` converts `addon/art/sources/<theme>/*.png` (made by Claude Desktop from the design board, with its generator script and notes) to 32-bit TGA in `media/<theme>/` and writes the generated `Images.lua` flag (`R2F.Images.azeroth`). `UI/Deco.lua` image mode: tiled panel and inset, 4 mirrored corners + 4 tiled edges, gems on the sockets (centre 10, 10), banner 248x62 overhanging 20 px, 3-slice sidebar buttons per state (hover through HookScript), nav gems, divider, slider track 3-slice + knob via `SetThumbTexture` (template track textures hidden while on). Without the flag or files the rectangle look remains. The test stand-in's slider thumb is a real Texture now. Sidebar art is squashed from 32 to 26 px high (buttons keep Classic's size). Not yet seen in the client: TESTING 5.37.

## 0.69.1 (2026-10-18): hotfix

- `Deco.box` created its lines on a Texture (`d.insetEdge`) -> `attempt to call a nil value`; it now takes the owning frame and the region to anchor to. `wow_stubs.lua`: CreateTexture / CreateFontString on a Texture or FontString raise an error like the game (the stub accepted it, which is why 0.69.0 passed its tests). Ember & Iron moves to 0.70.0.

## 0.69.0 (2026-10-18): Azeroth Reforged decoration

- `UI/Deco.lua` (textures only, built once, shown for a theme with `deco = "azeroth"`, hidden otherwise): gradient panel (`Texture:SetGradient`, flat fallback), inset, inner frame line, four round corner gems from `media/dot`, banner behind the title, gradient nav buttons with a gem, group headings with a fading line. `Theme.lua`: `deco` / `font` tokens, `setFace` swaps the face of our own font objects only and falls back to the game font when `SetFont` is refused. Bundled `media/fonts`: Cinzel (variable font, default weight) and Alegreya Sans Regular with their OFL files. README credits updated. Not yet seen in the client: TESTING 5.36. Next: Ember & Iron (0.69.1).

## 0.68.2 (2026-10-18): corpse arrow

- `Nav.lua`: `corpsePos` walks the parent maps (`mapChain`), `showCorpseSoon` retries at 0.6 / 1.5 / 3 / 6 s, ZONE_CHANGED_NEW_AREA as a ghost, `Nav.DebugCorpse` (`/r2f debug corpse`). CORPSE_POSITION_UPDATE is not an event of this client (not in its API documentation), so the old code never got that wake-up. Cause not seen in game; TESTING 5.35.

## 0.68.1 (2026-10-18): text-colour pass (step 1 of 0.69.0)

- `Theme.Role` / `Theme.PaintText|PaintTex|PaintVertex|PaintBackdrop` (repainted on every theme change) replace every hardcoded grey / white / gold text colour and dark overlay in `UI/*.lua`; seven own font objects (`R2FHeading[Large|Small]`, `R2FBody[Small]`, `R2FDim[Small]`, copies of the game's fonts, never the game's own) carry the page text; `UI.ThemeButton` tints Reload UI and the Theme button; slider knobs follow the `thumb` role. Classic's roles equal the old literals (test), a test fails if a page goes back to a literal colour or a `GameFont*` name. Semantic colours (class and quality colours, red / green status, pink wishlist) stay. Next: Azeroth Reforged decoration (0.69.0).

## 0.68.0 (2026-10-17): UI themes

- `Theme.lua` (colour tokens: panel, sidebar, rule, accent, rim, switch on/off), `settings.theme`, Home > Theme button via UI.ContextMenu (no UIDropDownMenu), `MainWindow.ApplyLook` reads the tokens and listens to `Theme.OnChange`, UI.Switch / UI.BlackBox repaint on a change. Classic keeps the dialog border and the original colours; other themes hide the dialog border (a tint only muddies its bronze art) and draw a 2 px line (`r2fRimLines`). Draft by Claude Desktop (branch r2f-themes), reviewed and finished here. Not yet seen in the real client: TESTING 5.33. Deferred: light themes (pages hardcode white / gold text), structural layouts, an effects setting.

## 0.67.0 (2026-10-17): recorder

- `Recorder.lua` (LOOT_OPENED, MERCHANT_SHOW, QUEST_DETAIL / QUEST_COMPLETE, read only) -> `R2FDB.recorder`; `bis/tools/recorder_import.py` merges the files; `refresh_sources.py` rebuilds all source tables; `DATA_SOURCES.md` records the research; README credits added. TESTING 5.32.

## 0.66.10 (2026-10-17): timers started by the cast

- `Timers.OnCast` now creates the estimate itself (def.fixed 1800 for seals, def.perCombo {6,3} for Slice and Dice via GetComboPoints sampled on UNIT_SPELLCAST_SENT) with the spell's own icon, instead of only restarting an earlier readable look. Tests added. TESTING 5.25 again.

## 0.66.9 (2026-10-17): revert one-click copy

- `CopyToClipboard` is blocked for addons (taint popup; pcall does not help). Back to the box. Library ledger row added.

## 0.66.8 (2026-10-17): one-click copy in the quest shopping list

- Item lines call the game's `CopyToClipboard(name, true)` (pcall, needs a positive length back); Shift or a refusal falls back to the `R2FCopyItem` box. Tests cover both paths. TESTING 5.31 asks for an in-game check.

## 0.66.7 (2026-10-17): no runes, click-to-copy shopping list, Shaper's Terrace position
- data.py: Forever has no runes (those are Season of Discovery). Starsurge, Sunfire, Starfall and Lacerate are Forever's own spells (notes corrected, still "Test in beta"); Strider Kick is a level-30 Hunter talent. Removed the five macros whose spells exist in the client only as old Season of Discovery rune spells with no Forever version: Skull Bash (mouseover and focus), Survival Instincts, Lifebloom, Nourish. Rebuilt macros.html, wow-forever-macros.md, MacroData.lua (the addon's bundled set changes with the next release).
- Plan tab, Quest shopping list: each item is its own clickable line; a click opens a small box with just the item name selected (Ctrl+C, then paste into the auction house search); it closes when you click elsewhere. Our own box only, nothing is written into the game's search field. Tests added. TESTING 5.31.
- launch-plan-waypoints.json: Shaper's Terrace entrance 50.4, 7.8 in Un'Goro Crater (owner, approximate). PlanData.lua rebuilt; the check-point test now injects its own unknown spot because no real one is left.

## 0.66.7 (2026-10-17): own item database, M0 started
- `bis/tools/db2_pull.py` (19 DB2 tables of a Forever build from wago.tools), `bis/tools/wh_tooltip_pull.py` (resumable Wowhead tooltip cache, one writer, lock file), `bis/tools/items_build.py` (item table from DB2 + tooltips, with a cross-check report). First cross-check: quality, item level and required level agree for 400 of 400 sample items; stats and armor differences are understood (OWN_DATABASE_PLAN.md section 9). Nothing ships to players yet.

## 0.66.6 (2026-10-17): No weather quick setting
- QuickSettings.lua: a fifth Home box "No weather (rain, snow, dust)" = `weatherDensity 0`, off = the game's own default (read from the client like the zoom). The minimap block on Home moved down one row. Tests: five boxes, the box sets 0 and gives the default back.

## 0.66.6 (2026-10-17): plan for our own Mr.BiZ database
- `bis/OWN_DATABASE_PLAN.md`: research (where item data, stat numbers, sources and scores come from; measured: Item table 31,875 rows, only 7,694 of 18,797 equippable items have a static ItemSparse row, the rest come as server hotfix data; stat numbers = percent x RandPropPoints budget, reproduced exactly for 77 of 77 checked items; local client keeps hotfix rows in DBCache.bin), design (item, source and weight tables, scoring formula, eligibility, ranking labels), size, effort (M0-M4, about 3-4 weeks) and risks.

## 0.66.6 (2026-10-17): Mr.BiZ data refreshed from ForeverDB (fetcher built)
- `bis/tools/foreverdb_fetch.py` (new): reads ForeverDB's BiS pages (the "Every slot" list, 27 requests, 1 per second) and writes `bis/raw/*.json` in the existing shape; prints a per-slot diff; `--write` replaces raw/. Ran it: the data moved from builds 70205-70338 to 70425 (31 best picks, 49 next-pick lists, source labels such as Clue -> Seen in Forever and fuller drop sources). `bis/sources.json`: 14 sources for picks that became next-picks (13 from their old best-pick entries, 1 from its item page); `bis/quality.json`: 3 new ids from the Wowhead tooltip API; `build_bis.py` UPDATED 2026-10-17. bis-data.json and BiZData.lua rebuilt (the addon copy ships with the next release). Test pins updated to the new data (route weapons: the Warrior Fury weapon at p3-stv).

## 0.66.6 (2026-10-17): Mr.BiZ data pipeline plan, weapons check
- ADDON_PLAN 19.3: the pipeline plan (detect, fetch, sources, quality, build, review, ship; cadence, safeguards, rules for ForeverDB and Wowhead, owner decisions). New `bis/tools/foreverdb_check.py` (read-only drift check against ForeverDB's server-rendered BiS pages): ForeverDB is on build 1.60.1.70425, our raw files on four older builds; 31 of 459 best picks and 49 more lists changed, 11 of 27 specs differ.
- Weapons: all 273 quest-reward weapons re-read from Wowhead's tooltip API, none differ. `QuestWeapons.lua`: the class weapon table now follows Forever's (ForeverDB "Trainers & weapon skills"): Rogues can use one-handed axes (the Plan tab's "Weapon:" lines count them); test added. Wowhead's list pages answered 403 after a run of 25 pages, so the quest links were not re-verified.

## 0.66.5 (2026-10-17): builds and talent snapshot follow Wowhead's changed trees
- Wowhead changed its live Forever talent trees (talents renamed, removed, added, moved: e.g. Malediction -> Grim Reach, Wake of Fire -> Improved Fire Blast, Improved Fire Nova -> Trial by Fire, Shadow Affinity / Improved Fade / Call of Thunder gone, Dark Inspiration and Elemental Mastery new, Mental Strength / Improved Power Word: Shield / Missile Barrage / Lava Burst and more moved or re-ranked). Share codes are one digit per talent in row/col order, so 17 of the 49 builds on builds.html silently meant other talents or opened empty (Priest Shadow and Healer/PvP, Warlock Affliction, Mage Arcane, Fire and Frost, Shaman Elemental, Restoration and Enhancement, Priest Holy, Discipline). Audit method: every build's code decoded with the old trees (from the old TalentData snapshot) = what the author meant; renamed talents followed by icon, removed talents dropped, ranks clamped to the new max, tier / prerequisite rules checked against the new trees, then encoded with the new trees. All 49 builds now match their talent lists and are valid.
- Where a removed talent freed points, a small stated adjustment keeps the point total and the tier gates: L30 Priest Healer/PvP Martyrdom +1 and Twilight Focus -1 (Improved Power Word: Shield moved a row down); L30 Warlock Affliction Grim Reach 2 and Suppression +1 (Malediction gone); L30 Shaman Elemental Convection +1 (Call of Thunder gone); L60 Priest Holy Silent Resolve +1, Mental Strength +1, Spiritual Guidance -2; L60 Priest Shadow Dark Inspiration +3 (Shadow Affinity gone); L60 Warlock Affliction Improved Life Tap +2, Grim Reach +2, Soul Harvest +1 (Malediction gone); L60 Mage Fire Critical Mass +2 (Fire Power max is 3 now); L60 Shaman Elemental Elemental Mastery +1 (Call of Thunder gone). To be re-checked in the beta.
- addon TalentData.lua re-snapshotted from Wowhead (the Talents tab sandbox and Recommended builds); `gen_talent_data.py --drift` (new) exits 1 when Wowhead's live trees differ from the snapshot. The rotation note "Hot Streak" on the L30 Mage Fire build now says Heating Up (the talent's real name). Tests use the new Priest Shadow code.

## 0.66.5 (2026-10-17): banner size and position, reload message
- CombatBanner.lua (new): the combat banner moved from the Alerts page to the Class icons page as its own section (Show / Lock / Size slider, drag it where you want it while unlocked; `R2FDB.banner` = shown, lock, scale, x, y; the 0.66.4 Alerts switch carries over; default place a hand below the top edge). Tests rewritten.
- GameplayExtras.lua: "Hide Blizzard's alert text" no longer prints "type /reload" at every login: the saved choice is re-applied at login and now does nothing (and says nothing) when the game's setting is already off; unticking only writes when the value differs. Regression test added.

## 0.66.4 (2026-10-16): combat banner
- GameplayExtras.lua: new Tweaks > Alerts feature "Show a banner when combat starts and ends" (`combatbanner`, off by default): "Entering Combat" (red) / "Leaving Combat" (green) in `GameFontNormalHuge` near the top of the screen (our own frame on UIParent, strata HIGH, 150 px down) for 2 s, driven by PLAYER_REGEN_DISABLED / ENABLED. Tests: `test_combat_banner`. TESTING 5.26.

## 0.66.4 (2026-10-16): seal and Slice and Dice timers in combat
- Timers.lua: `Timers.Remaining` no longer gives up when ONE aura in the list is hidden (secret values): an unreadable aura is skipped and ours is looked for in the rest. If ours (or the whole list) is hidden, the countdown continues from the last readable look (`seen[key]` = expires, duration, icon) and the number is shown with a leading "~"; `Timers.OnCast` (UNIT_SPELLCAST_SUCCEEDED, player) restarts the estimate from the last full duration when the buff's spell is cast in the fight; a readable list without the buff clears it; an estimate that has run out shows nothing. New events: UNIT_SPELLCAST_SUCCEEDED, PLAYER_REGEN_DISABLED / ENABLED. New `/r2f debug timers`. Never a guess: nothing seen before + everything hidden = nothing shown. Tests: `test_timers_in_combat`. TESTING 5.25. (Why: the owner saw the timers vanish in fights; whether the game hides the list or only single auras is unknown until `/r2f debug timers` is run in a fight.)

## 0.66.3 (2026-10-16): quest shopping list in the Plan tab
- gen_plan_data.js also reads QUESTS and the buy PHASES of launch-plan.html and writes `R2F.PlanData.quests` (phases + list: name, zone, quest level, phase, status, items with counts, note, xp); `--expected` carries the quests for the test. Plan.lua: `Plan.QuestGroups / QuestBought / SetQuestBought / QuestProgress` (ticks in `R2FCharDB.plan.bought`, created in Library.lua). UI/Plan.lua: a "Quest shopping list" button (top right of the tab) swaps the launch-day list for the quest list grouped by route phase, each quest with a tick box, its items ("3x Boar Intestines, ..."), the note and a "verify in beta" mark; "Back to the steps" returns. Tests: same quests in the same order as the site, rows, ticks saved per character, back to the steps.

## 0.66.3 (2026-10-16): food nag quiet on flights and in capitals
- Timers.lua: the "No food" nag stays hidden on a flight path (`UnitOnTaxi`) and in Stormwind, Ironforge, Darnassus, Undercity, Orgrimmar and Thunder Bluff (classic city map ids 1453 to 1458, or the English zone name as a fallback; `Timers.QuietSpot`). The timers re-check on ZONE_CHANGED_NEW_AREA and PLAYER_CONTROL_LOST / GAINED. Tests added; the globals are in .luacheckrc.

## 2026-10-16 (Addons page: what Road to Forever contains)
- addons.html: the Road to Forever card's Details now open with a short list of what the addon contains (macros, talents incl. Learn this build, launch plan and arrows, Mr.BiZ, training and Home, reminders and counters, Tweaks, professions export) instead of one long paragraph. The old "Test first" warning about talent learning is gone (it works, tested in game 2026-10-16). `.note ul` gets the same spacing as `.note ol`.

## 2026-10-16 (Macro fall-through audit closed)
- "Cooldown + spell" pair macros stay, each with its warning note (PAIR_MACROS in data.py; decided 2026-10-15 after the Shield Block + Revenge test). The last open check, Warlock Shadow Bolt + Imp Firebolt, needed nothing: that combined macro was replaced on 2026-10-13 by the single-spell Shadow Bolt (target / target's target), so there is no pair left to fall through. No data.py change.

## 0.66.2 (2026-10-16)

- GameplayExtras.lua: R2FDB.chars is keyed by the full in-game name (two characters called Venom, Venom Oathbreaker and Venom Madstorm, overwrote each other, so the Shaman never showed in the mail list); an old bare-name entry is dropped at the next login of that character; OtherCharacters compares full names. Test added.
- data.py: SkullMark icon INV_Misc_Bone_HumanSkull_01 (Ability_MarkOfSkull is not a game icon, it showed as "?"). Rebuilt.
- launch-plan-waypoints.json: Thendal Village (Zephras start), Valanaar (Skycutter), The Sky Enclave (Dalaran portal; zone Alterac Mountains, 1416) from the owner's /r2f here; Rog'Mar, Krol'dok (43, 42) and Dire Maul (59, 43) approx. PlanData.lua regenerated.
- Talents.lua: `/r2f debug traits` (what the last traits points answered). Found with it: the second rank of a multi-rank talent (Sanctified Judgement) got `CommitConfig` = false right after the previous point's commit, so "Learn this build" stopped ("waiting in Blizzard's window") and the next session fell back to guided mode. A false commit is now asked again every 0.3 s up to 6 times (only while nothing else is staged), before the point's 2 s timeout decides. Tests: stub `commitRejectsTimes`, `runShortTimers`.
- Tried and reverted the same day: deleting the guided talent mode. The owner's client uses it (Learn this build only names the talent), so it stays until the addon learns talents itself (BACKLOG 2.5a).

## 0.66.1 (2026-10-15)

- data.py: Hunter "Raptor Strike + Wing Clip" restored (removed in 0.56.1, 13e2525, because a macro can stop at the first spell it can't cast; owner asked for it back); Paladin "Judgement + Holy Strike" added (BETA). Rebuilt macros.html, wow-forever-macros.md, MacroData.lua. TESTING.md: corpse arrow (10) and Druid macros (13, except 9 and 11) confirmed.

## 0.66.0 (2026-10-15)

- Timers.lua: two more TRACK entries with a `class` (seal for Paladin matching `^Seal of`, sliceanddice for Rogue); frames and the Class icons section only for that class; Library defaults (stance's spot). Tests: test_class_timers. TESTING.md 5.22.

## 0.65.2 (2026-10-15)

- Training.lua: the trainer merge and Training.Status treat a rank-less saved line as the same spell as a ranked one at the same level (the trainer words a spell "Rank 2" only once rank 1 is known). Test added. TESTING.md: 7.16 confirmed, 5.20 text matches 0.64.4.

## 0.65.1 (2026-10-15)

- Removed media/arrow_plate.tga and media/arrow_slab.tga (unreferenced; arrow_gilded.tga kept at the owner's request). TESTING.md: talent learning 4.2, 4.3, 4.4, 4.6, 4.7, 4.9, 4.11 confirmed by the owner; 4.5 still open.

## 0.65.0 (2026-10-15)

- Library.lua: new first-install defaults taken from the owner's SavedVariables (reminder shown/lock/scale/x/y, nav style gilded + small, fct outline thick + position, talented on, Thorns off, minimap 270). Gameplay switches unchanged (off). Tests updated to the new defaults.

## 0.64.4 (2026-10-15)

- Timers.lua: a `nagOnly` entry hides its icon and border while it shows the nag (locked), text centred. Tests added.

## 0.64.3 (2026-10-15)

- Timers.lua: `nagOnly` flag on the food entry. While Well Fed is on, the frame stays hidden (no icon, no timer); the "No food" nag still needs the player's `remindMissing` checkbox (off by default). Tests updated.

## 0.64.2 (2026-10-15)

- Timers.Applies: a TRACK entry without `learned` applies to everyone (the food entry never showed on a client that has IsPlayerSpell; the test client has none, so the test now stubs it). Version message wording.

## 0.64.1 (2026-10-15)

- Version.lua (addon message prefix R2FV, "V<tab>x.y.z" to GUILD and PARTY / RAID; numbers compared, newest kept in R2FDB.newerVersion; feature `updatecheck` on, in Tweaks > Chat & screen; `/r2f update`; Home line); Timers.lua wellfed entry (`like = { "^Well Fed" }`, clock format, optional "No food" nag with `readable` flag so secret auras never nag); launch-plan-waypoints.json positions.

## 0.64.0 (2026-10-15)

- Rested.lua (GetXPExhaustion / UnitXPMax, events PLAYER_XP_UPDATE / UPDATE_EXHAUSTION / PLAYER_UPDATE_RESTING), `general = true` reminder, R2FDB.rested, `/r2f rested`.

## 0.63.2 (2026-10-15)

- UI/Reminders.lua BuildInto(f, x, y, width, filter, col) + TotalHeight(col) / MaxHeight; registry `general = true` (repair, tracking, timers); icons page builds two columns (ICON_W 200).

## 0.63.1 (2026-10-15)

- UI/MacroBook.lua SECTION_ICONS Balance / Feral; Minimap.lua menu item for the damageMeterEnabled CVar through QuickSettings.Read / Write (only shown when the client has the setting).

## 0.63.0 (2026-10-15)

- UI/Gameplay.lua: PAGES alerts / arrow / icons (Alerts & HUD split, two rows of page buttons, ResetPage per page); Timers.lua (buff countdown reminders: TRACK list, Walk on Air spells 1259416 / 1308663 / aura 1259417, R2FDB.timers); Calc.Order greedy deepest-first; data.py plain Charge, `PAIR_MACROS` warning; talentcalc.js "+5 points" button per card (`?v=20261015a`).

## 0.62.1 (2026-10-15)
- gen_talent_data.py writes `groupBuilds` from group-builds.json into TalentData.lua (`--check` covers it); Calc.GroupPicks and a "Group picks" section in the Recommended menu on the Talents tab. group-builds.json is empty today, so nothing shows until the owner publishes picks on the site and a release is made.

## 2026-10-15 (Addons page and news)
- addons.html: the Road to Forever card fallback refreshed to 0.62.0 and its Details mention what the addon does now; news.json has an entry for the addon's new looks, build-in-order and reminders.

## 0.62.0 (2026-10-15)

- Repair.lua (GetInventoryItemDurability over slots 1-19, worst piece, threshold slider 5-90 default 25) and Pet.lua (UnitExists / UnitIsDead on "pet", GetPetHappiness for Hunters, quiet when mounted / dead) as reminder modules in the Reminders registry (`applies` for Hunter / Warlock); R2FDB.repair / R2FDB.pet defaults in Library.lua; `/r2f repair [lock]`, `/r2f pet [lock]`; the Loadouts menu entry uses Talents.MyBuildLink. First release with the Node 24 action versions (see 2026-10-15 Workflow action versions).

## 0.61.0 (2026-10-15)

- blender_arrow_render.py: camera 40 degrees up, lens 28, dist 2.2 (CAM_DIST 2.8 for the long arrow and dart; env R2F_ELEV / R2F_LENS / R2F_DIST for experiments) instead of 52 / 70 / 5.3. blender_arrow3d.py and _dart.py now use the shared render file. New blender_arrow3d_picture.py lays a cut-out PNG (addon/art/sources/<key>_cut.png from make_image_looks.py) on the ground; gilded / plate / slab became 100-frame sheets (media/arrow3d_<key>.tga, `sheet = true`). The flat media/arrow_gilded|plate|slab.tga from 0.60.0 are no longer used. No frame is clipped at the cell edge.

## 0.60.0 (2026-10-15)

- Picture looks "gilded", "plate", "slab": the owner generated them with Google Gemini (gemini-2.5-flash-image) from a prompt written here; the originals are addon/art/sources/*.jpg and addon/art/make_image_looks.py cuts the plain background out, centres and shrinks them to 128 px TGAs (media/arrow_<key>.tga). Nav.STYLES entries without `sheet` use one texture turned by SetRotation; Gameplay picker has a third row. AI-generated images: check Gemini's terms if the addon ever goes on CurseForge (BACKLOG 2.8 hold).

## 0.59.0 (2026-10-15)

- New 3D looks "block" and "needle" (blender_arrow3d_block.py, blender_arrow3d_needle.py; shared helpers blender_arrow_parts.py and blender_arrow_render.py; media/arrow3d_block.tga and arrow3d_needle.tga; exporter STYLES, Nav.STYLES / STYLE_ORDER, Library nav.style, Locale NAV_STYLE_BLOCK / NAV_STYLE_NEEDLE; the picker wraps to a second row). Owner wanted home-made looks instead of the downloaded icon packs (Smashicons / Vecteezy, not used). The earlier two scripts still carry their own copy of the helpers.

## 0.58.0 (2026-10-14)

- blender_arrow3d.py: stone point (notched flint, flake scars, sinew lashing) and barb-by-barb vanes; the previous gold dart model is kept as blender_arrow3d_dart.py -> media/arrow3d_dart.tga. export_arrow3d.py `--style arrow|dart|all`. Nav.STYLES / Nav.Style / Nav.SetStyle, db.nav.style, Tweaks buttons Flat / Gold dart / Stone arrow (the arrow3d switch stays as the flat on/off underneath; its tick box is gone from the page). A new look = a script, a STYLES line in the exporter, a Nav.STYLES entry and a NAV_STYLE_ text.

## 0.57.1 (2026-10-14)

- Import.Commit message with new / updated / unchanged counts; Home nextTalentHead + gold line; TalentPanel PAGE.h 630 / WIN_H 664, nextHint on its own row; removed the doll-slot enchant line added in 0.56.3 (duplicate of the item tooltip's Mr.BiZ line, owner 2026-10-14).

## 0.57.0 (2026-10-14)

- addon/art/blender_arrow3d.py rewritten (shaft cylinder, barbed gold broadhead with ridge, two flat vanes + one upright fin, nock, dark outline plate; camera dist 5.3), media/arrow3d.tga re-exported with export_arrow3d.py (100 frames, none clipped at the cell edge). Owner asked for "an arrow like you shoot", no bow. The flat 2D arrow (export_arrow.py) is unchanged.

## 0.56.3 (2026-10-14)

- UI/BiZ.lua: doll slot tooltip adds `BiZ.Enchants(spec, slot)[1]` (pink); the side panel's enchant heading pink. Closes the "enchant line under the item name" backlog item.

## 0.56.2 (2026-10-14)

- Calc.NextPoint (shared by the Talents tab and Talents.NextPointLine); TalentPanel.syncFull saves the followed build as cdb.followLink (own class only); Home ui.nextTalent and the Training level-up handler print the line.

## 0.56.1 (2026-10-14)

- data.py fall-through fix (BACKLOG 4.3 "Fix now"): Hunter Raptor Strike + Wing Clip -> two macros, Survival melee button -> Raptor Strike / Mongoose Bite / Strider Kick, Rogue Pick Pocket + Sap -> Sap. build.py regenerated macros.html, the .md and MacroData.lua.

## 0.56.0 (2026-10-14)

- TalentCalc.lua `Calc.Order` / `Calc.Prefix` (tier, tree, column order, every rank together, a same-row prerequisite moved first; matches Talents.LearnOrder), tested for every recommended build; TalentPanel.lua stepper (`Step`, `syncFull`: `state.full` = the build, `state.shown` = the code the stepper left, a different code on the board = new build), tooltip order line, `nextPointText` from `plan.trees[t].talents[k].rank`. Order is computed at runtime from the board, so no data generation and it works for any link or loadout.

## 0.55.5 (2026-10-14)

- TalentPanel.lua: prerequisite arrows (drawLinks): a bar + a rotated ChatFrameExpandArrow head per link, drawn on `linkFrame` above the cells, grey / gold by `Calc.Rank >= q[2]`. STEP_Y 38 -> 44, PAGE.h 566 -> 602, MainWindow WIN_H 600 -> 636. Verified only by the tests (no in-game look yet): see TESTING 4.8.

## 0.55.4 (2026-10-14)

- Nav.lua savePos/place: the arrow frame's scale (Nav.SIZES) differs from UIParent's, so GetCenter offsets saved in mixed scales made the arrow jump after a drag. Now saved in UIParent units and converted by the scale ratio in place(); build() sets the scale before placing.

## 0.55.3 (2026-10-14)

- ImportFrame.lua doImport: an import holding only another class's records (plus Universal) opens that class's preview even when nothing in it is new (before, `firstNew` was nil on a repeat import and the book stayed on the browsed class).
- BiZ.EnchantTipLine colour green -> pink (1, 0.5, 0.85); two run_tests checks updated.
- builds.html DATA30: 11 new builds (Hunter MM + SV, Warlock Destruction + Demonology, Rogue Assassination + Subtlety, Druid Balance, Warrior Fury two-hander + dual-wield (26 pts), Priest Discipline leveler + Healer/PvP (26 pts)); existing single-build Warlock / Rogue / Hunter got `spec` names. All codes validated against TalentData (gates, prerequisites, ranks) with the decoded rows and icons generated from it; rotations are "medium". TalentData.lua regenerated. Source: Claude Desktop research 2026-10-14 (Mobalytics, LepreStore, wowvendor, wowforever.gg).

## 0.55.2 (2026-10-14)

- Gameplay.lua sellGray: batches of 4 every 0.25 s with a re-scan (items that stay after 2 tries are skipped; sold items are counted when they leave the bag). GameplayChat.lua Chat.Text: pcall per line, skips `issecretvalue` lines, returns a hidden count; the window shows a reason instead of staying blank (the owner's first real test of Copy chat came up empty; cause not proven, this adds the counters needed to see it). GameplayExtras mail menu foot note. UI.CheckedGlow adds a gold UI-ActionButton-Border ring on checked buttons. Tests: test_sell_batches_and_chat_secret; the vendor and mail tests follow the new behaviour. addon/dev/TESTING.md: confirmed items moved out.

## 0.55.1 (2026-10-14)

- Core.lua `open` command, Locale EMPTY_LIBRARY / help text, test_open_command. addon/dev/TESTING.md rewritten against the real 0.55.0 interface (sidebar, Tweaks pages, Home / Macros > Options, `/r2f debug ...`).

## 2026-10-14 (Druid macros)
- data.py: Druid class block after Rogue (Shared 23, Balance 7, Feral 24, Restoration 7 = 61 macros); new helpers bear() / bear_self() / cat() / cat_self() (one /cast with `[noform:N]` conditions because Forever macros stop after the first GCD action). Spell names and levels from Wowhead's Forever druid ability list; macro ideas from classicwowforever.com, forg.gg, rankedboost.com and the Forever beta forum thread on the Cat Form + Prowl macro. NOT tested in game: the form numbers (Bear 1, Cat 3, or 2 without Aquatic Form) and the rune abilities are marked "Test in beta".
- template.html: Druid class icon; Library.lua SECTION_ORDER[DRUID]; MacroData.lua regenerated; news.json entry; addon 0.55.0.

## 0.54.2 (2026-10-14)

- BiZ.EnchantTipLine (BiZ.lua) + GearScore.lua tooltip hook: the green enchant line on item tooltips (equip location -> Mr.BiZ slot key, 2h-only enchants filtered, the link's own enchant id decides "in place" / stand-in). Locale BIZ_TIP_ENCHANT*. Test: test_enchant_tooltip. Looked at Sixty Upgrades through Claude in Chrome (CLAUDE_CODE_ENABLE_CFC=1 in user settings; Claude Code's native host registered by `claude --chrome`).

## 0.54.1 (2026-10-14)

- gen_talent_data.py lists a "Bear tank / Cat" build under Tank and DPS; UI/BiZ.lua colours the enchant line green (0.1, 1, 0.1).

## 0.54.0 (2026-10-14): Talents tab rebuilt as a sandbox calculator

- **TalentData.lua (new, generated)**: all nine classes' trees (466 talents: name, icon, row, column, max rank, tier points, prerequisites, a
  description per rank) from the same Wowhead Forever script the site's calculator loads, plus our recommended builds from builds.html.
  `addon/tools/gen_talent_data.py` writes it (fetches Wowhead, so it is run by hand, not by build.py); `--check` compares the bundled builds with
  builds.html (the tests run it). Talents are in link order, so digit k of a share code is talent k, exactly like the site.
- **TalentCalc.lua (new)**: the rules of talentcalc.js without UI (51 points, 5 points per row, prerequisites, removal blocked when something
  depends on a point), share code, `~hash` over the names in link order, `Recommended(class)` (Tank / DPS / Healer, level 60 first).
- **UI/TalentPanel.lua rewritten**: class-icon row (any class), the board from TalentData (never your real talents), click +1 / right-click -1 /
  Shift all, our own tooltip text (works for classes you don't play), Load (a pasted link; refused when its hash differs from the bundled trees
  or the build is invalid), Copy link, Reset, Save loadout, Loadouts, Recommended, Share (Party / Raid / Guild, any class), Learn this build
  (own class only, through the existing learning engine, which compares the board with your real talents and needs a trainer reset first).
- Removed: `Talents.EditPlan` / `LinkFromCodes` (the old planner), the Edit build switch, Preview, Copy my build button, the free-points line on the tab.
- Tweaks tab: the search box and its results are removed (code, strings and test).
- Tests: `test_talent_calc` (bundled data well-formed, rules, every recommended build valid and round-tripping, same digits and hash as
  talentcalc.js on the fixture), `test_talent_sandbox_ui` (class circles, other class's tooltip, recommended menu, sharing, link round trip),
  `test_talent_data_fresh`; the preview and learning tests now feed the small fixture through `use_fixture_data` and
  `TalentPanel.SetBoardUnchecked` (a test hook).
- Not built yet: prerequisite arrows between talents (the tooltip lists what a talent needs), a "start from my current talents" button.

## 0.30.0 (2026-10-12): Mr.BiZ, the BiS tab

**Never run in game yet: TESTING.md 41.**

- Every rank has a source: a grey line under each pick in the open list and "From: ..." in the tooltip. When your
  filters hide the best, the row shows the best pick they let through ("Bizzer, your filters hide the best").
- Biz ranks, same as the site: the expanded list says Bizzest / Bizzer / Biz (Almost biz for 4th and lower), with
  "The Bizz" when the best is 20%+ ahead of the next pick (also in gold on the row and in the tooltip). Tab label "BiZ".

- **New BiZ tab (Mr.BiZ)**, between Plan and Gameplay; also `/biz`, `/mrbiz` (`/biz wish` opens the wishlist) and `/r2f bis`.
  `/bis` is left alone: ForeverBiS, Forever Leveling BiS and ForeverBiS-Helper already use it.
- Best in slot for every class and spec (27, all level 30 PvE, the beta cap), the same list as the site's new BiS page
  (`BiZData.lua`, generated by `bis/build_bis.py` from ForeverDB's BiS pages). Opens on your own class; pick another
  class or spec from the two buttons at the top (specs grouped Tank / DPS / Healer).
- Each slot: icon, the item name **in its quality colour** (green / blue / purple from the game), where it comes from,
  its score, and how sure the source is (Seen / Client / Classic / Clue / Unknown). **Hover any item for the game's own
  item tooltip** plus a Mr.BiZ line (best in slot, or "#2 ... 12% behind the best"). Click the name: the next best picks
  open under it. Shift-click: link it in chat.
- Source filters (Dungeon, World drop, Quest, Crafted, Vendor, Reputation, PvP, Known sources only). A slot whose best
  pick is filtered out stays in the list as "Hidden by your filters" and still opens on click. A Horde-only quest reward
  is marked "Horde only" for Alliance characters (and the other way round).
- **Wishlist per character**: tick the box next to any item. The Wishlist view groups it by where you get it (a dungeon,
  a profession, a vendor), biggest group first. Export / Import list share it with the site (`R2FW1:` string).
- Saved: `R2FCharDB.biz` (class, spec per class, filters, wishlist).

## 0.29.1 (2026-10-11): the group-buff icon can always be moved

- Owner: couldn't move the missing-buff icons. With "Lock the icons' position" unticked, nothing was shown when you
  were in a group with nothing missing, so there was nothing to grab. Unlocked, the icon now always shows (dimmed when
  nothing is missing); drag it, then tick the lock.

## 0.29.0 (2026-10-11): missing group buffs, bag Sort button, faster talent learning

**Never run in game yet: TESTING.md 40.**

- **Missing group buffs** (Gameplay > Alerts, next to your class icons). In a party or raid, the classes in it decide which
  buffs to look for: Priest -> Power Word: Fortitude, Druid -> Mark of the Wild and Thorns, Mage -> Arcane Intellect, Paladin ->
  any Blessing (also off: Divine Spirit, Shadow Protection, Battle Shout, Trueshot Aura). A framed icon per buff you
  don't have, a row if several; gone the moment you have it. Switch each buff on or off; Show / Lock / Size like the other
  icons. It is locked by default: untick "Lock the icons' position" while alone to get a dimmed sample icon to drag, then
  lock it. If the game hides your auras (combat / instances) it shows nothing instead of guessing.
- **Sort button on the bags** (Gameplay > Vendors & loot, OFF until ticked): a small Sort button above the backpack
  window (or the combined bag) that runs the game's own bag clean-up. Not in combat.
- **Faster talent learning.** Each point waited for the game's event or the full timeout (2 s per point in the one-click mode)
  before the next; now a learned point is noticed within 0.1 s. Nothing else about the safety checks changed.
- Every class now has the group-buff section in Alerts, so the "No reminders for your class" line is gone.

## 0.28.4 (2026-10-10): the ability name in the alert, second try

- Owner's `/r2f reactlog` showed the game announces "Revenge is ready" with the name hidden and sends NO bar-glow
  event for it, so 0.28.0's glow lookup had nothing to read. The alert now also watches which of Revenge, Overpower,
  Riposte, Counterattack, Mongoose Bite, Victory Rush has just become usable and uses that name. Other abilities still
  show "Ability ready". `/r2f reactlog` now also logs `USABLE <name>`.

## 0.28.3 (2026-10-10): the mail list uses the full in-game name

- **Fix:** the mail button filled in the account-style login name; this client names some characters with a
  surname as UnitName's second value instead of a realm (found with `/r2f debug who`). Each character now remembers that full name and the
  list fills it in. **Log in once on each alt with this version** so it is remembered; alts not seen again keep the old form.

## 0.28.2 (2026-10-10): /r2f who

- **`/r2f who`** lists every way the client names your character (UnitName, UnitFullName, PvP name, realm names,
  the character window title...). Used to find where a two-part name comes from, so the mail list can fill in the
  right name for every alt.

## 0.28.1 (2026-10-10): the active Gameplay page stands out

- Owner: the page you are on looked greyed out (the button was disabled), which reads as "not learned / not working".
  It now stays enabled, with gold text, a gold bar under it and the button kept lit; the other pages are normal white.

## 0.28.0 (2026-10-10): Gameplay tab redesign, plain names, the real ability name in the alert

**Never run in game yet: TESTING.md 35.**

- **The alert says which ability.** The game's own announcement hides the spell name from addons, but the
  "spell glows on your bar" event (`SPELL_ACTIVATION_OVERLAY_GLOW_SHOW`) carries a spell id; the name is read from
  that (a glow from the last second, or one that comes just after the announcement, fills it in). If your client
  sends no glow for that ability the alert still says "Ability ready". **`/r2f reactlog`** prints the last
  announcements it saw (paste it to us if the name stays missing).
- **Gameplay tab redesign (UX pass, ADDON_PLAN 18).** Four small pages picked with buttons along the top instead of
  one long scrolling list: **Quests**, **Vendors & loot**, **Screen & chat**, **Alerts**. The page you used last is
  remembered. Each option has a plain name and a grey one-line explanation under it (the tooltip keeps the full text).
- **Plain names** everywhere on the tab: "Auto-accept quests", "Auto turn-in quests", "Skip the NPC chat before
  shops", "Auto-repair at vendors", "Auto-sell grey items", "Fast looting", "Show free bag slots", "Hide red error
  messages", "Always show XP numbers", "Decline duel requests", "Show an 'ability ready' alert", "Lock the alert's
  position", "Hide Blizzard's alert text"... and the class icons: "Warrior stance icon", "Hunter ammo counter",
  "Tracking reminder" with "Show the icon / Lock its position / Size".
- **Fix:** the main window reopened on Home after every login if you had last used Plan, Gameplay or Settings (the
  saved-tab check only knew the first three tabs).

## 0.27.2 (2026-10-10): "Hide the game's own reactive text" needs a /reload

- Owner test of 0.27.1: our `Ability ready` alert showed where he put it, but the game's own "<Revenge>" text was
  still there. The game's combat text reads its "Reactive ability alerts" setting (`floatingCombatTextReactives_v2`) when
  it loads, and when its own options change it, not when another addon changes the setting. So the hide box takes
  effect after a `/reload`; the addon now says so in chat. (Making the game re-read it now would mean calling its code
  from ours, which is what tainted it in 0.27.0.) There is no Edit Mode setting for this text: the game's code has none.
- The alert says "Ability ready" instead of the spell name: the announcement's spell name is a hidden ("secret") value on
  this client.

## 0.27.1 (2026-10-10): URGENT fix for 0.27.0 (Lua errors in fights), Gameplay tab scrolls

- **0.27.0 broke the game's floating combat text** ("attempt to perform arithmetic on field 'startY' (a secret
  number value, while execution tainted by 'RoadToForever')", 96 errors in one fight). Cause: it wrote into
  Blizzard's `CombatText.textLocations` table to move the "<Revenge>" text. Writing into a game table taints it, and
  on this client tainted values refuse arithmetic. **That code is gone.** After updating, `/reload` once (the old
  tainted table lives until the UI reloads).
- The replacement never touches the game's data: **Reactive alert (own text, movable)** listens for the game's own
  announcement (`COMBAT_TEXT_UPDATE` / `SPELL_ACTIVE`) and shows `<Revenge>` in OUR text at a marker you drag
  (**Lock reactive alert position** hides the marker); **Hide the game's own reactive text** switches off the game's
  setting `floatingCombatTextReactives_v2` (through QuickSettings; your value is put back when unticked). If the event
  text is a secret value the alert says "Ability ready". All three are OFF by default.
- A test now fails if any file writes into `CombatText` / `textLocations`.
- The Gameplay tab **scrolls** (mouse wheel): with 17 features the lower boxes ran off the bottom of the window.

## 0.27.0 (2026-10-10): move the floating combat text where you want it

**Never run in game yet: TESTING.md 33 item 2 (rewritten).**

- The fixed "Raise floating combat text" box (0.25.0) is replaced by **Move floating combat text** (Gameplay >
  Screen): a marker with the Revenge icon appears on screen; drag it where the "<Revenge>" alert (and damage
  numbers) should start. The game's whole scroll path (start and end) is shifted by the marker's offset from the
  screen centre; the shift is re-applied after every relayout and taken out when the box is unticked.
  **Lock floating combat text position** hides the marker and keeps the spot. Needs floating combat text switched
  on in the game's options (the box is greyed out until the game has loaded it).
- Saved in `R2FDB.fct` (x, y, lock); applied at login without opening the tab.

## 0.26.1 (2026-10-10): two fixes from the 0.26.0 test

- **Tracking reminder:** it stayed up, grey, while a tracking was on (unlocked). It is now only shown while a tracking
  is NEEDED (none of the ticked ones active) and gone otherwise. To place it, switch your tracking off: it appears and
  can be dragged.
- **Quest log track-all box:** it sat on top of the game's collapse / expand button. It is now to the LEFT of that
  button (`header.CollapseButton`).
- Probe result for the buff reminder (owner, out of combat, in a party of two): `/r2f auras` reads 1 buff on the player
  and 6 on party1, all with readable spell ids; secret restrictions "yes", auras secret "no" outside combat.

## 0.26.0 (2026-10-10): shop-line skipper, tracking reminder, aura probe

**Never run in game yet: TESTING.md 34.**

- **Skip the shop line at NPCs** (Gameplay tab, Automatic; OFF by default). Many NPCs open a gossip window with one
  line before their shop. This picks that line, and only when: it is the ONLY option, it is Available, the NPC offers
  no quests, and its ICON is one of the game's shop / trainer / bank / flight-map / auction-house icons (file ids
  132060, 132058, 132050, 132057, 528409, read from the game files; this build's gossip options have no "type").
  The innkeeper's "make this your home" and plain chat lines are never picked. Shift pauses it.
  **`/r2f gossip`** prints the open NPC window's options with their icon ids, so the whitelist can grow from real data.
- **Minimap tracking reminder** (Gameplay tab, Reminders column; any class that has Find Minerals / Herbs / Treasure):
  the framed icon shows while you know at least one ticked tracking type and none of them is active; hidden otherwise
  (when locked). Three boxes choose which types to remind about. Draggable, lockable, resizable like the other
  reminders. No aura reading, works in combat. (Part of the "buff reminders" ForeverPlus feature the owner used.)
- **`/r2f auras`** (probe): says whether this client lets an addon read buffs on you and your party, in and out of
  combat (the game's API files mark aura reads as restricted "secret" values). The group-buff reminder waits for
  its answer.

## 0.25.0 (2026-10-10): quest-log track-all boxes, raise the "<Revenge>" text

**Never run in game yet: TESTING.md 33.** Both OFF until ticked on the Gameplay tab (Screen).

- **Quest log: track-all box per zone.** A small check box on every zone heading in the quest log: tick it to
  track every quest under that heading, untick to untrack them all. Built on `C_QuestLog.AddQuestWatch` /
  `RemoveQuestWatch` (the game's own way is the right-click menu on the heading). Frame names read in the
  game's UI code (`QuestScrollFrame.headerFramePool`, `questLogIndex`); where the box lands on the heading
  is unverified.
- **Raise floating combat text.** The "<Revenge>" alert the owner sees at the bottom middle of the screen is the
  game's floating combat text ("Reactive ability alerts" setting, CVar `floatingCombatTextReactives_v2`; found in
  `Blizzard_CombatText`). It scrolls from y 384 down to 159 when scrolling is set to "down". This box raises that
  whole scroll path by 200 (also damage numbers). Needs floating combat text switched on in the game's options.

## 0.24.1 (2026-10-10): Hunter ammo counts the real ammunition

- **Bug found by an owner test of the 178 on the backpack:** this client has no ammo slot
  (`GetInventoryItemID("player", 0)` is 0 and `GetInventoryItemCount("player", 0)` is 1), so the Hunter ammo
  reminder from 0.17.0 would have shown a wrong "1" (red) for every Hunter. It now counts the ammunition the
  equipped ranged weapon fires, over all bags: arrows for a bow or crossbow, bullets for a gun (item class 6,
  weapon in slot 18). No ranged weapon (or a thrown weapon) = nothing to count: the icon stays hidden, grey with
  "-" while unlocked. A ranged weapon and no ammunition = red 0.
- The "178" on the backpack button is still unexplained (it is the game's own `Count` text on the backpack
  button; it is not the ammo slot, not the item total, not the slot total).

## 0.24.0 (2026-10-09): copy chat (replaces Prat 3.0 for copying)

**Never run in game yet: TESTING.md 32.**

- **`/r2f copychat`** opens a window with the newest 200 lines of your main chat window in a box you can
  select and copy (Ctrl+A, Ctrl+C); **`/r2f copychat 3`** does it for chat window 3. Oldest line first.
  A **Plain text** tick (on by default) strips colour codes, links and icons so pasted text is readable.
- **Copy chat button** (Gameplay tab, Screen, off by default): a small C in the corner of every chat window;
  click it for that window's text.
- Read-only: only the chat windows' stored lines are read. Written from scratch (Prat 3.0 is GPLv3, none of
  its code is used).
- Backpack: still open whether the game's own "178" on the backpack button should be hidden while our free-slot
  number is on (it is not the item total or the slot total).

## 0.23.2 (2026-10-09): mail uses the full character name

- Owner test of 0.22.0: the mail button filled in a bare name ("Alice") and the mail didn't go: on this
  client a recipient needs the full name, "Name-Realm". The button now fills in `Name-Realm` (the game's
  normalised realm name, else the realm name without spaces).

## 0.23.1 (2026-10-09): single quest rewards are taken

- Owner test of 0.23.0: accept and hand in work, but a quest with exactly ONE reward stopped at the reward
  window. With one reward there is nothing to choose, so it is now turned in; with two or more choices the
  window still stays open and the addon never picks.

## 0.23.0 (2026-10-09): Gameplay step 3 (quest automation)

**Never run in game yet: TESTING.md 31.** All three are OFF until ticked on the Gameplay tab. Hold
**Shift** to pause the two that act.

- **Accept quests:** accepts a quest when its window opens and picks the next quest a quest giver offers
  (gossip list or quest greeting). A quest the game accepted by itself is left alone.
- **Hand in quests:** completes finished quests at the quest giver. **It never picks a reward**: the
  quest is only turned in when it has no reward choice at all; with one or more choices the window
  stays open for you. With both boxes on, a finished quest is handed in before a new one is picked.
- **Show reward sell prices:** writes what each reward choice sells for to a vendor in the corner of its
  button; the best is green (not marked when there is only one choice).
- The quest APIs on this client are partly unverified, so the modern gossip functions are tried first with
  the classic ones as the fallback, and anything missing does nothing.
- Free bag slots: the number now sits at the TOP of the backpack button, so it no longer lands on top of
  the game's own count at the bottom.

## 0.22.0 (2026-10-09): Gameplay step 2 (mail to your characters, free bag slots, fast loot)

**Never run in game yet: TESTING.md 30.** All three are OFF until ticked on the Gameplay tab.

- **Mail: pick your own characters.** A small button after the recipient field in the mail window lists
  your other characters on this realm and faction (class colour, level); click one to fill in the name.
  The addon remembers every character that logs in with it (name, class, level, faction), so log in on
  each once.
- **Free bag slots on the backpack.** The number of free general-purpose bag slots (quivers and ammo pouches
  not counted) on the backpack button; red at 3 or fewer. Greyed out if the client has no such button.
- **Fast loot.** Loots every slot at once when the loot window opens. Only when the game's own auto-loot
  would loot (the auto-loot key flips it). Greed rolling on greens is NOT included.
- Quest log "track all in this zone" is not built yet: it needs the quest log's frame names on this client.

## 0.21.0 (2026-10-09): Gameplay tab, first five features (ADDON_PLAN 17 step 1)

**Never run in game yet: TESTING.md 29.**

- **The Reminders tab is now the Gameplay tab** (Home / Macros / Talents / Plan / Gameplay /
  Settings). `/r2f gameplay` opens it (`/r2f reminders` still works and opens the same tab).
  Left column: **Automatic** and **Screen** features; right column: **Reminders** (your class's
  stance / ammo icons and their options, exactly as before).
- **Everything ships OFF.** One check box per feature; each says in chat what it did.
  - **Repair at vendors:** repairs everything with your own gold when you open a vendor that can
    repair; says the cost; does nothing if you can't afford it.
  - **Sell grey items:** at a vendor, sells grey (poor quality) items that have a vendor price.
    Nothing else is ever sold; says the count and total.
  - **Block duels:** declines every duel request, says who.
  - **Hide red error spam:** hides "Not enough rage", "Ability is not ready yet", "Out of range",
    wrong facing and similar lines above the action bar (matched against the client's own texts).
  - **XP bar text always shown:** uses the game's own setting and puts your old value back when
    you untick it (can't be changed in combat).
- A feature the client can't do is greyed out with a tooltip; an error in one feature is reported
  once and never stops the others.
- Written from scratch; ForeverPlus was only used as a list of what these features do.

## 0.20.1 (2026-10-09): addon list icon

- The addon list in the game's AddOns window showed a "?" icon: the TOC now has
  `## IconTexture` (our logo, `media/logo64`).

## 0.20.0 (2026-10-09): bags rebuilt (Shift+drag), Reload UI in the minimap menu

**Never run in game yet: TESTING.md 24 (rewritten) and 28.**

- **Movable bags didn't work in game** (owner test of 0.19.x, with every other addon off). Cause,
  confirmed in ForeverPlus' BagWindow module: Blizzard puts an invisible button over the whole
  title bar that opens the bag menu when the mouse goes down, so a drag that starts on the title
  never reaches the window. Now **hold Shift and drag** (title or empty background): while Shift is
  held a grip of our own covers the title bar, without Shift the title is the game's again (click
  for its menu). **Movable bags** on, **Lock bags** off. Position still saved per character.
- **No more taint risk:** 0.16.0 called the game's `UpdateContainerFrameAnchors()` when Movable was
  switched off. That runs the game's bag placement in our name and can make the game refuse item use
  ("blocked from an action"; ForeverPlus hit this on 2026-10-04). Switching Movable off now puts each
  window back where the game last placed it, read off the frame.
- Windows anchored to a moved bag that would fall off the screen are hung off the other side.
- `/r2f bags` warns when ForeverPlus (which also moves the bag window) is loaded: use one of the two.
- **Minimap button right-click menu: Reload UI** (last line), instead of typing /reload.

## 0.19.1 (2026-10-09): rank detection from the spellbook, /r2f rankdebug

**Never run in game yet.**

- Owner test of 0.19.0: `/r2f ranks` said "you know no rank of it yet" for Charge on a character
  that has Charge Rank 1 (and `/cast Charge(Rank 1)` works), so the spell-id check missed it:
  `C_Spell.GetSpellInfo("Charge(Rank 1)")` gives id 1240287, but `IsPlayerSpell` of it didn't say yes.
- The highest known rank is now also read from the spellbook itself (the "Rank N" text of each
  entry, modern `C_SpellBook` or the classic tab functions), and several "do I know this id"
  checks are tried (`IsPlayerSpell`, `IsSpellKnown`, `C_SpellBook.IsSpellKnown`,
  `C_SpellBook.IsSpellInSpellBook`, `IsSpellKnownOrOverridesKnown`). The higher answer wins.
- New `/r2f rankdebug <spell>` (e.g. `/r2f rankdebug Charge`): prints the spell id of the plain
  name and of each `(Rank N)`, what every known-check answers, what the spellbook lists, and the
  rank the addon would use. Paste it to us if a macro still isn't ranked.

## 0.19.0 (2026-10-09): rank-aware macros (ADDON_PLAN 16)

**Never run in game yet: TESTING.md 27.**

- **Why:** on WoW Forever an unranked spell name can resolve to a rank you don't know: on a
  level-18 Warrior `/cast Charge` failed (the name gave the level-46 Charge) while `/cast Rend`
  worked. The addon now fixes this in the game macros it makes.
- When the addon **creates, updates or replaces** a game macro, every spell name in its `/cast`,
  `/castsequence` and `#showtooltip` lines is checked with `C_Spell.GetSpellInfo`: if the plain
  name is a spell you don't know, the highest rank you do know is written in (`Charge(Rank 1)`).
  Spells that resolve to something you know (Rend) are left alone, and so are spells you haven't
  learned any rank of yet. A name that already pins a rank (the site's `Charge(Rank 1)`) is raised
  when you know a higher one, never lowered. A ranked text over 255 characters isn't used.
- **Learning a spell** (`LEARNED_SPELL_IN_TAB` / `SPELLS_CHANGED`) re-checks the macros the addon
  made and raises ranks, after a one second pause; in combat the update waits for the end of the
  fight. Macros you edited yourself are never touched.
- **The library keeps the site's text.** Only what is written into game macros is ranked; the book,
  imports and the "edited / updated" checks compare the live macro with its ranked version, so a
  ranked macro is not mistaken for an edited or outdated one.
- New `/r2f ranks`: which spells in your macros have a plain name you don't know, the rank used
  instead, and the macros it is in (also macros kept unranked because of the 255 limit).

## 0.18.0 (2026-10-09): Launch Plan in game, TomTom waypoints (ADDON_PLAN 15.5)

**Never run in game yet: TESTING.md 26.**

- **New tab: Plan** (Home / Macros / Talents / Plan / Reminders / Settings; `/r2f plan`). Pick
  the group plan (2 Hunters · Warrior · Druid, 2 Hunters, 3 Hunters · Druid, Paladin · Hunter
  · Shaman: the site's plans with the site's override / `base` rules), then tick off the
  launch-day steps (launch night, phases 1 to 3). Ticks and the chosen plan are saved per
  character. The pre-launch and beta lists are not included.
- **Home shows the next step** ("Next: [12] Skycutter to Dalaran ...") and opens the tab.
- **Waypoints:** each step with known places lists them. A **Waypoint** button sets a TomTom
  waypoint (`TomTom:AddWaypoint`, zone names turned into uiMapIDs at run time); without TomTom
  the button (**Show /way**) prints the `/way Zone x y label` line to chat. Points with no known
  position yet show their label and "position not known yet" (no button); points taken from
  Classic or only roughly known say "may have moved".
- **`/r2f here`** prints your zone, uiMapID and x, y (and a `/way` line), so the missing
  positions can be captured in the beta and sent to us.
- The plan data (`PlanData.lua`) is generated from `launch-plan.html` and
  `launch-plan-waypoints.json` by `python build.py` (needs node); a test fails if the checked-in
  file is out of date or the addon's plan filtering differs from the site's own `resolve()`.

## 0.17.0 (2026-10-09): Reminders tab, Hunter ammo low (ADDON_PLAN 15.4)

**Never run in game yet: TESTING.md 25.**

- **New tab: Reminders** (Home / Macros / Talents / Reminders / Settings). It lists the
  on-screen reminder icons that apply to your class, each with its own Show, Lock and size
  slider. `/r2f reminders` opens it. A class without a reminder sees a line saying so.
- **The Warrior stance icon and its options moved here** from the Settings tab (same
  settings and saved position, `/r2f stance` unchanged).
- **New reminder: Hunter ammo low** (`Ammo.lua`). A framed icon with the number of arrows or
  bullets left (the equipped ammo, counted across quiver / pouch and bags). It turns red under
  a threshold you set on the tab (default 200, steps of 50, 50 to 1000) and is hidden while
  the ammo is fine, unless it is unlocked so you can move it. No ammo equipped shows a red 0.
  `/r2f ammo` shows or hides it, `/r2f ammo lock` locks it. Hunters only.
- Reminders are read-only (inventory getters only, no protected calls), so they work in
  combat, and their controls stay enabled in combat. Shared code for the framed icon,
  dragging and saved position is in `Reminders.lua`; adding a reminder means registering it.

## 0.16.0 (2026-10-08): movable bags (ADDON_PLAN 15.3)

**Never run in game yet: TESTING.md 24.** Which bag windows WoW Forever uses is
unconfirmed, so both kinds are handled and `/r2f bags` says what was found.

- **New: Movable bags / Lock bags** (`Bags.lua`), two more Quick settings on the Settings
  tab. Movable: drag the backpack and bags anywhere (grab the title or background, not an
  item). The position is saved per character (`R2FCharDB.bags`) and re-applied right after
  the game re-anchors the bags (`hooksecurefunc` on `UpdateContainerFrameAnchors`, plus
  `OnShow` on every window). Lock: keeps the spot, stops dragging. Replaces the Forever Bag
  Mover addon.
- Works with the classic bag windows (`ContainerFrame1..N`, saved per bag id so the
  backpack keeps its spot) and the modern combined bag (`ContainerFrameCombinedBags`),
  whichever the client has, or both.
- Nothing is moved, hooked or dragged in combat (bag windows hold protected item buttons);
  what was skipped runs when combat ends. The two boxes grey out in combat and when no bag
  window is found. Turning Movable off lets the game re-stack the bags; saved spots are
  kept for the next time.
- New `/r2f bags`: which bag windows were found and the movable / lock state.

## 0.15.0 (2026-10-08): Settings tab, tree names, Home as "what's next" (ADDON_PLAN 15.2)

**Never run in game yet: TESTING.md 23.**

- **Settings is the 4th tab** (Home / Macros / Talents / Settings). The Settings button
  left the Macro Book and the floating panel is gone; `/r2f settings` opens the tab.
  Left column: Macros (slots first, Remove all) and Minimap (show, lock). Right column:
  **Quick settings** (moved from Home: max camera zoom, hide guild names, hide PvP
  titles) and, for Warriors, the stance icon options (Show, Lock, size; they move to
  Reminders in step 4).
- **Home is a short "what's next" list:** free talent points, macros in the library and on
  your bars, and macro slot use (`7 of 30 character slots, 12 of 120 account slots used`),
  plus the Import / Export professions buttons.
- **Talents tab shows real tree names** (Arms / Fury / Protection ...) instead of
  "Tree 1 / 2 / 3": the same names and order as the site's talent calculator, for all nine
  classes. Names the game itself gives still win.
- **Black squares fixed (best guess, check in game):** the selected class circle and the
  selected side tab (Universal) were drawn with `SetCheckedTexture(..., "ADD")`, but the
  second argument only works for highlight textures, so the glow texture was drawn with
  normal blending as a black square. Selected state is now the same square glow as the
  hover highlight, blended additively (`UI.CheckedGlow`); icons that can't be named fall
  back to the question-mark icon (`UI.SetNormalIcon`).

## 0.14.0 (2026-10-08): import replaces, not only adds (ADDON_PLAN 15.1)

**Never run in game yet: TESTING.md 22.**

- The site's import string now ends with one `K <CLASS> id,id,...` record per class it
  carries (every id that class has on the site, picked or not). On import, library
  entries of a carried class that are not in that list are gone from the site and leave
  your library. Macros you just didn't pick are in the list and stay. Fixes the
  "207 macros in your library" pile-up after the site's 2026-10-08 macro cleanup.
- Game macros made from removed entries follow Tidy up's rules: unedited and not on a bar
  are deleted (queued until combat ends); on a bar, or edited by you, are kept and listed
  in chat ("kept, still on your bars: ...", "kept, edited by you: ..."). Kept ones stay
  tracked, so Tidy up can take them later. Macros still on the site but changed there
  update in place, as before.
- The preview says `12 macros were removed from the site and leave your library.` plus
  how many of them exist as game macros.
- Import window: new checkbox **Replace my library for these classes** (clean slate:
  removes everything of the carried classes that is not in the pasted string).
- Strings without `K` records (older site copies) keep the add-only behaviour. Older
  addons skip the new records and show "1 skipped" (harmless).

## 0.13.0 (2026-10-08): Warrior stance icon

**Tested in game by the owner (2026-10-08): works.**

- **New: stance icon** (`Stance.lua`), Warriors only. One icon showing the current
  stance, with a coloured frame: Battle blue, Defensive green, Berserker red. Drag it
  anywhere; Settings has Show, Lock and a size slider (50% to 300%). `/r2f stance`
  shows or hides it, `/r2f stance lock` locks it. Unlocked, it also shows with no stance
  so it can be placed before level 10.
- Section order follows the site's macro cleanup (2026-10-08): Mage has no Fire/Frost
  tabs and Rogue no Combat tab any more (all their macros were plain casts). Older
  versions just keep the unused names in their order table; nothing breaks.

## 0.12.2 (2026-10-07): Export professions button on Home

- **Export professions** button on the Home tab, next to Import (same as `/r2f profs`
  and the Export button on the profession window). Owner's request after the first real
  exports worked: a button in the addon window instead of typing a command.

## 0.12.1 (2026-10-07): profession export on modern profession windows

- 0.12.0 showed no Export button and no "saved N recipes" line in game: WoW Forever runs
  on a modern client, so the Classic profession functions are probably missing. Now also
  reads the modern profession window (`C_TradeSkillUI`: recipe ids, `GetRecipeInfo`,
  `GetRecipeSchematic` basic reagents), listens to `TRADE_SKILL_LIST_UPDATE` /
  `TRADE_SKILL_DATA_SOURCE_CHANGED`, and puts the Export button on `ProfessionsFrame` too.
- `/r2f profs` reads the open window itself if nothing was saved yet.
- New `/r2f profdebug`: one chat block showing which profession functions and windows this
  client has, how many rows the open window has, and what's saved. Paste it to us if the
  export still doesn't work.

## 0.12.0 (2026-10-07): export your professions for the site

**Never run in game yet: TESTING.md 21.**

- **New: profession export** (ADDON_PLAN 14). Open a profession window (Enchanting,
  Leatherworking, Tailoring, First Aid, ...) and the addon saves every recipe this
  character knows, with skill level and each recipe's materials (item ids + counts).
  Chat says "saved N Enchanting recipes". An **Export** button sits on the profession
  window next to its close button; `/r2f profs` does the same. Both show one
  `R2FP1:` string to copy, for the site's Professions page (Crafters).
- Reads both the trade skill window and Classic's craft window (Enchanting); opens all
  headers and clears "Have materials" first so the list is complete.
- Base64 encoding added (the export string is plain base64, safe in chat and Discord).

## 0.11.0 (2026-10-03): free talent points on WoW Forever + one-click learning through C_Traits

**The new learning path has never run against a real WoW Forever server. Test it with
ONE point on a disposable character first (TESTING.md 20), never on a main's build.**
Full design, confidence levels and the "not verified" list: `ADDON_PLAN.md` 13.12.

- **Fix: free talent points said 0** while Blizzard's window showed "Unspent Talents:
  17" (real screenshot), so Learn talents stayed grey. The count now comes from
  `C_Traits.GetTreeCurrencyInfo` (applied points, staged changes excluded), with
  Classic's `UnitCharacterPoints` kept unchanged for Classic-era clients. One function
  for the whole addon (`Talents.FreePointsInfo`; the minimap tooltip, Home, the Talents
  tab and the learning engine all use it). When no API gives a usable answer the addon
  now says **"couldn't read"** (Talents tab, Home) instead of a misleading "No free
  talent points", and Learn stays disabled.
- **New: "traits" learning mode** (WoW Forever). Learn talents spends points itself:
  `C_Traits.PurchaseRank(configID, nodeID)` per point, then `C_Traits.CommitConfig`
  when the purchase turns out to be staged (like Blizzard's own Apply Changes), one
  point at a time. Same order, popup, `Learning X / N`, combat stop, Stop / resume and
  no-double-send rules as before. A point only counts when its applied rank went up
  AND the free points went down. Anything unexpected (refused, error, failed commit,
  unconfirmed point) stops the run and switches to the existing guided mode for the
  rest of the session. Your own un-applied changes in Blizzard's window are never
  committed: the run stops and asks you to apply or undo them first.
- Classic's direct mode and guided mode are unchanged.
- Tests: fake trait servers (staged + commit, immediate, async, no commit) and every
  failure case; free points from the currency (17 with the legacy call saying 0),
  Classic path, unknown. Suite: 10927 checks, 0 failed (9389 before); 22 of 23 hand
  mutations fail the suite (the 23rd is equivalent); luacheck 0 warnings.

## 0.10.5 (2026-10-03): fix — Paladin talents unreadable (position jitter)

Follow-up to 0.10.4's C_Traits reader, found by live testing: a dump of all 50
real nodes of a Paladin's talent tree showed Protection's first column at both
posX 5020 and 5030. That's a few units of jitter in Blizzard's own layout data
(real columns are 590-600 apart), but 0.10.4 counted it as a fifth Protection
column, refused the tree, and Preview / Copy my build said "couldn't read your
talents yet." Full analysis: `ADDON_PLAN.md` 13.11.

- **Fix:** positions that are much closer together than a grid step (under 20% of
  the median gap) count as one row/column before rows and columns are numbered.
  The step is measured from the data itself, so it works at any scale. It applies
  to columns and to rows. Real columns that are just a little closer together than
  usual stay separate.
- Nothing changes when there's no jitter (Holy, and every earlier test, read
  exactly as before).
- Tests: the real 13 posX values in a 50-node Paladin tree read as 4/4/4 columns
  (was 4/5/4 -> nil), link + hash equal to the site's `talentcalc.js`; plus
  synthetic row jitter, several jitter pairs, other grid scales, a too-aggressive
  tolerance caught, and a jitter-majority tree refused. Suite: 9389 checks, 0
  failed (9259 before); luacheck 0 warnings.
- Still to confirm in game (TESTING.md 19): 0.10.5 on the Paladin, other classes.

## 0.10.4 (2026-10-03): fix — read talents through C_Traits (corrects 0.10.3)

0.10.3's fix was wrong: it force-loaded `Blizzard_TalentUI`, but on WoW Forever
`LoadAddOn("Blizzard_TalentUI")` answers `false, "MISSING"` and the Classic talent
functions never exist. So Preview and Copy my build still said "couldn't read your
talents yet." WoW Forever keeps its talents in the trait system (`C_Traits`), the
same API WeakAuras Forever reads them with. Full evidence: `ADDON_PLAN.md` 13.10.

- **Fix:** `Talents.ReadTrees()` reads the active talent config through
  `C_SpecializationInfo` / `C_Traits` / `C_Spell`. Rows and columns come from the
  nodes' positions (ranked, so any scale works; checked against 8 real Paladin nodes
  and Wowhead's row/col for the same ids). The three panes (e.g. Holy / Protection /
  Retribution) are one trait tree on Forever, split by the gaps between columns.
  Same output shape as before, so links, the `~hash`, the preview and the learning
  order are unchanged. Every call is guarded: a missing or not-ready API means
  "couldn't read yet", never an error.
- **Learning is guided on WoW Forever.** `LearnTalent(tab, index)` addresses
  talents the Classic way, which this client doesn't have, so the addon no longer
  calls it unless Classic's `GetTalentInfo` confirms the exact talent at that
  address. On Forever, Learn talents names each talent to click in Blizzard's window
  and writes nothing itself.
- Talent tooltips use `GameTooltip:SetSpellByID`; `TRAIT_CONFIG_UPDATED` refreshes
  the Talents tab like `CHARACTER_POINTS_CHANGED`.
- Removed: the `Blizzard_TalentUI` force-load and its tests. The test stub now models
  `C_Traits` (and answers `MISSING` for `Blizzard_TalentUI`), plus a realistic
  Forever client with no Classic talent API at all.
- Suite: 9259 checks, 0 failed (8770 before); luacheck 0 warnings.
- Still to confirm in game (TESTING.md 19): every class other than Paladin, the
  Protection/Retribution positions, pending (un-applied) points.

## 0.10.3 (2026-10-02): fix — Talent Preview failed on a fresh login

> Superseded by 0.10.4: `Blizzard_TalentUI` turned out not to exist on WoW Forever.

Reported from real in-game testing: pasting a talent link and clicking Preview
always showed "couldn't read your talents yet. Try again in a moment," even
though the character genuinely had talent points spent. `/dump
GetNumTalentTabs()` confirmed the cause directly: the function doesn't exist
as a global until Blizzard's own on-demand `Blizzard_TalentUI` addon has
loaded, which normally only happens the first time the player opens the real
Talent window by hand — the addon never tried to make that happen itself, it
only checked whether it already had.

- **Fix:** `Talents.ReadTrees()` now force-loads `Blizzard_TalentUI` via
  `LoadAddOn` (tries `C_AddOns.LoadAddOn` first, falls back to the bare
  global, `pcall`-wrapped) before checking for the talent functions, so
  Preview and Copy my build work the first time without the player needing
  to open their Talent window separately first. A one-shot retry 0.5s later
  covers the (believed unlikely) case where the force-load succeeds but the
  data isn't queryable in the exact same tick.
- Found by reading a third-party addon (RXPGuides) already working on the
  same WoW Forever client — it already solved this exact problem for its own
  talent-related features, and separately already has a proven, working
  `LoadAddOn` call for a different on-demand Blizzard addon. See
  `ADDON_PLAN.md` 13.9 for the full investigation and reasoning.
- The Lua test stub (`wow_stubs.lua`) previously defined the talent functions
  as always-available globals — an inaccurate model of the real client that
  every prior talent test was unknowingly built against. Fixed to match
  reality: they're now genuinely load-on-demand in the stub too.
- Full suite re-run: 8770 checks, 0 failed (up from 8688), including new
  tests specifically covering the cold-login scenario, no-LoadAddOn-at-all,
  and a refused load — each confirmed to fail cleanly, no errors.

## 0.10.2 (2026-10-02): version/author footer on the Home tab (ADDON_PLAN.md 12.4.2)

**Requested from real in-game testing, 2026-10-02** — there was no way to see
the addon's version or who made it without opening the TOC file.

- A quiet line at the bottom of the Home tab reads the TOC's own `## Version:`
  / `## Author:` fields through `GetAddOnMetadata` (tries `C_AddOns` first,
  falls back to the bare global, never a second hardcoded copy that could
  drift out of sync): `Road to Forever v0.10.2 · by nobody174 ·
  nobody174.github.io/wow-forever`.
- If neither metadata API exists on this client, shows a plain line with no
  version instead of erroring.
- Hovering it shows the TOC's `## Notes:` text as a one-line "what is this."
- Full suite re-run: 8688 checks, 0 failed.

## 0.10.1 (2026-10-02): fix — character macro slot limit was wrong

Reported from real in-game testing: the Macro Book's Character counter should
read out of 30, not 18.

- **Fix:** `Macros.Limits()`'s fallback (used when the game doesn't define
  `MAX_CHARACTER_MACROS`, which WoW Forever's client doesn't) was hardcoded to
  the vanilla/Classic Era value, 18. The user counted WoW Forever's real
  `/macro` Character tab directly: **30** slots (5 rows of 6). Fixed the
  constant; no other logic changed, since everything already correctly reads
  through `Macros.Limits()` rather than hardcoding 18 anywhere else.
- Updated the Lua test stub (`wow_stubs.lua`) and every test assertion that
  checked the old 18/138 numbers to match. Full suite re-run: 8608 checks,
  0 failed.
- Account-wide limit (120) is unchanged and still unverified directly — only
  the per-character number was actually in question.

## 0.10.0 (2026-10-02): class picker, Remove from library asks first, Tidy up tooltip

**Requested from first real in-game testing, 2026-10-02** — not part of the original
build plan (steps 3 to 10 + Quick settings). On a Paladin, the tester imported Warrior
macros: chat said `imported 51 macros.`, but no Warrior tab ever appeared, because the
book only showed the class you're logged in as. Decisions in `ADDON_PLAN.md` 5.10. Not
tested in the game yet; see `TESTING.md` section 17.

- **Class picker in the Macro Book:** when your library has macros for another class, a
  row of class icons appears at the top of the book (your class first). Click one to
  look at that class's macros from any character, e.g. to prepare an alt.
- **Other classes are preview only:** their macros show grey, with tooltips, and
  Shift-click still puts them in chat, but they can't be dragged to your bars (a Warrior
  can't cast Paladin spells; the addon refuses and says `Log in on a Paladin character
  to use this macro.`). Universal macros keep working in every view.
- The slot counters and gold "on your bars" checks always describe the character you're
  playing; a note says so while you preview another class.
- The book remembers the class you picked while you play, and opens on your own class
  again after a relog or `/reload`.
- After an import, the book opens on your own class if the import brought anything new
  for it, otherwise on the imported class's preview.
- **Remove from library** (right-click a macro) now asks first. It only takes the macro
  out of your book: a macro you already made from it stays in the game and on your bars
  (Tidy up or Remove all can delete it later). Importing it again brings it back as new.
  Works on previewed classes too, so a class imported by mistake can be cleared out.
- **Tidy up has a tooltip** saying what it deletes (unedited Road to Forever macros that
  aren't on any bar) and that it never changes your library.

## 0.9.1 (2026-10-02): fix — addon wouldn't load at all

First real in-game install of 0.9.0 reported: addon shows in the list, no
minimap icon, `/r2f` does nothing, no Lua errors. Turned out the game flagged
it "Incompatible" (yellow) in the AddOns list and refused to load any of it —
so there was nothing to error, since nothing ever ran.

- **Fix:** `## Interface: 11507` was a Classic Era placeholder, never actually
  checked against a real WoW Forever client. The real value, confirmed via
  `/dump GetBuildInfo()` on a live Forever client, is **16001**
  (`version="1.60.1", build="70170", tocversion=16001`).
- No code changed — this is the TOC fix alone. Everything built in 0.1.0
  through 0.9.0 should now actually load for the first time.

## 0.9.0 (2026-10-02): Quick settings (ADDON_PLAN.md 12.4.1)

Not tested in the game yet; see `TESTING.md` section 16.

- **Quick settings on the Home tab:** three check boxes that change game settings
  directly, with no macro and no macro slot: **Max camera zoom** (zoom the camera out
  further; untick = the game's own default), **Hide guild names** and **Hide PvP
  titles**. They always show your game's current setting, also when you changed it
  some other way (`/console`, the game's options, another addon).
- **Not in combat:** the boxes grey out in combat and can't be changed until it ends.
- **The Macro Book no longer shows** the Zoom out more, Hide guild names and Hide PvP
  titles macros, since Quick settings does the same for free. A line on the Universal
  tab says so. They're still on the website for players without the addon, and a real
  macro you already made from one keeps working.
- If your game lacks one of these settings, its box is greyed out and its macro shows
  in the book again.

## 0.8.0 (2026-10-02): talent learning (ADDON_PLAN.md step 10)

Not tested in the game yet. **This version can learn talents, which only a trainer
reset undoes: do `TESTING.md` section 15 on a test character first.**

- **Learn talents works.** After a Preview with no red problems, click **Learn
  talents**: `Learn 21 talent points? Only a trainer reset can undo this.` [Learn]
  [Cancel]. The addon then learns exactly the gold `+N` points of the preview, one at a
  time, tier by tier, and checks each one against your game first (tier, prerequisite,
  free points, nothing else changed). The button counts `Learning 7 / 21`; the rest of
  the tab is locked and Cancel becomes **Stop**. Done: `Learned 21 talent points.` and
  the trees redraw.
- **It stops instead of guessing:** if the game doesn't take a point (`Stopped at
  Improved Thunder Clap: the game didn't accept the point. 14 of 21 learned.`), if you
  enter combat (`Stopped: you entered combat. 9 of 21 learned. Click Learn talents to
  continue.`), or if your talents change meanwhile. After combat or Stop, Learn talents
  continues where it stopped, without asking again.
- **Not in combat:** Learn talents is greyed out in combat; a popup accepted just as
  combat starts waits until combat ends.
- **Guided mode:** if the game doesn't let addons learn talents, the addon opens
  Blizzard's talent window instead and puts a pulsing gold glow on the next talent to
  click (`Click Cruelty (2 of 21)`). It never changes Blizzard's window.
- If the game turns out to have Blizzard's own talent preview, Learn talents fills that
  preview and you confirm with Blizzard's Learn button.

## 0.7.0 (2026-10-02): talent import preview (ADDON_PLAN.md step 9)

Not tested in the game yet; see `TESTING.md` section 14. **Nothing is learned yet:**
this version only shows what a build would do. Learning comes in the next version.

- **The Talents tab is real now** (`/r2ft`). Paste a link from the site's talent
  calculator (Copy link; a full URL, `talents.html#...`, `#...` or just
  `warrior/...` all work) and click **Preview**: three small talent trees show what
  you already have, what would be learned now (gold glow, `+2`), what has to wait for
  more points (`later`), what isn't in the build (grey), and any problem (red).
  Hover a talent for the game's own tooltip plus `Build: 3 / 3`.
- **A summary line** says how many points the build uses and how many you have free,
  e.g. `This build uses 21 points. You have 16 free: 16 will be learned now, 5
  later.`, or what's in the way (`You already have 2 points in Improved Rend, which
  this build doesn't use. Reset your talents at a trainer first.`).
- **Safety checks:** a link for another class is refused (`This is a Paladin build.
  You're playing a Warrior.`); a link whose check (`~xxxx`) doesn't match your game's
  talent trees is refused; an older link without a check gets a yellow warning; a
  link asking for more ranks than a talent has, or points in a talent your tree
  doesn't have, is shown as a problem. On a non-English game client links can't be
  checked (talent names are translated), so you get the yellow warning instead.
- **Copy my build** is a button on the Talents tab (`/r2f copybuild` still works).
- **Learn talents** is there but greyed out until the next version.
- The tab remembers the last link per character and updates live when you spend
  points or level up. Home's Talents entry shows your free talent points.
- Works in combat: previewing only reads your talents.

## 0.6.0 (2026-10-02): Copy my build (ADDON_PLAN.md step 8)

Not tested in the game yet; see `TESTING.md` section 13.

- **`/r2f copybuild`** reads your current talents and shows them as a link to the
  Road to Forever talent calculator, already selected: press Ctrl+C and paste it in
  your browser or Discord. The link opens the site's calculator with your build.
  It only reads your talents (it never learns or changes anything), so it also
  works in combat.
- Links end in a short check (`~` and 4 characters) made from your class's talent
  names. The site's links now carry the same check, so the next version can warn you
  when a link was made with different talent trees than your game has.
- The Talents tab still has its placeholder; it now mentions `/r2f copybuild`. The
  Talents tab's own Copy my build button comes with the talent import version.
- `/r2f help` lists the new command.

## 0.5.0 (2026-10-02): first downloadable release (ADDON_PLAN.md step 7)

No change to what the addon does in the game: same code as 0.4.0. This is the
first version you can download as a zip instead of copying the folder from the
repository. Not tested in the game yet; see `TESTING.md`.

- **Download:** `RoadToForever-0.5.0.zip` on the GitHub Releases page (linked from
  the Macros page's "How to import" steps). Unzip it into your game's
  `Interface\AddOns\` folder; it contains one `RoadToForever` folder.
- Marked as a **pre-release** on GitHub, like every 0.x version, because nothing
  has been checked in the real game client yet.

## 0.4.0 (2026-10-02): main window, minimap button, logo (ADDON_PLAN.md step 6)

Not tested in the game yet; see `TESTING.md` section 11.

- **One window with three tabs** at the bottom: **Home**, **Macros** and
  **Talents**. The Macro Book is now the Macros tab (same book, same buttons),
  and the window has the Road to Forever logo as its portrait. It remembers where
  you put it and which tab you used last.
- **Home** shows how many macros are in your library and how many are on your
  bars, a Talents entry (coming in a later version), and an **Import macros**
  button. Click an entry to go to that tab.
- **Minimap button** with the logo: left-click opens/closes the window, right-click
  opens a menu (Open Road to Forever, Macros, Talents, Lock button position, Hide
  minimap button), drag it around the minimap. The tooltip shows your library
  count (and free talent points, if any). The Show / Lock minimap button settings
  now work. If you have another addon that uses LibDBIcon, the button goes through
  it, so minimap-button collector addons see it too.
- **Slash commands:** `/r2f` (window, last tab), `/r2f macros`, `/r2f talents` or
  `/r2ft`, `/r2f minimap` (hide/show the button), `/r2f import`, `/r2f help`.
- **Key bindings:** Toggle Road to Forever opens the window on your last tab;
  Open Macros / Open Talents open (or close) that tab.
- The Talents tab is a placeholder until the talent versions.

## 0.3.0 (2026-10-02): Settings, Remove all, key bindings (ADDON_PLAN.md step 5)

Not tested in the game yet; see `TESTING.md` sections 7, 9 and 10.

- **Settings** button in the Macro Book now works. It opens a small panel:
  - **New macros go to:** Character slots first / Account slots first. Only for
    macros made from then on; macros you already have stay where they are.
  - **Show minimap button / Lock minimap button**: saved now, used once the
    minimap button arrives (next version).
  - **Remove all Road to Forever macros**: after a confirm listing them, deletes
    every macro the addon made that you haven't edited, also ones on your action
    bars, in character and account slots. Macros you edited are kept as your own.
    Your macro library is not touched, so you can drag them out again. Greyed out
    in combat; if you accept it in combat, it runs when combat ends.
- **Key bindings** (Key Bindings menu, "Road to Forever"): Toggle Road to Forever
  and Open Macros open/close the Macro Book; Open Talents is a placeholder until
  the Talents window exists.
- **Tidy up** checks again, right when it deletes, that each macro is still not on
  a bar (matters when you accepted it in combat and it ran afterwards). Long name
  lists in popups are shortened (`... and 12 more`).

## 0.2.0 (2026-10-02): updates and Changed markers (ADDON_PLAN.md step 4)

Not tested in the game yet; see `TESTING.md` section 8.

- **Re-importing updates your macros.** When an import changes a macro you
  already made in the game, and you haven't edited it, the real macro gets the
  new text (and icon) right away. The preview says so before you click Import
  (`2 macros you already made in the game will be updated too.`), and chat
  confirms it afterwards.
- **Your edits are kept.** If you changed one of these macros yourself, it's left
  exactly as it is; the preview and chat say which ones (`kept your edits to HS`),
  and the library still has the new version: drag it from the book and choose
  Replace if you want it.
- **Changed marker:** a small green up-arrow on the macro's icon in the Macro Book
  when an import changed a macro that's on your action bars. Hover it to see what
  changed; the arrow goes away once you've seen it. Kept-edited macros on your bars
  get the arrow too, with a tooltip explaining your version was kept.
- **Other characters catch up on login.** The library is shared by all your
  characters, so macros you made on another character are brought up to date the
  next time you log in on it (only unedited ones). Dragging an older macro from the
  book also updates it first.
- In combat, these updates wait until combat ends (one chat line says so), and are
  checked again then, so anything you edited meanwhile is still left alone.
- The Import window is a little taller so the longer preview fits.

## 0.1.0 (2026-10-02): first version, Macro Book MVP (ADDON_PLAN.md step 3)

Not tested in the game yet; see `TESTING.md` for the beta checklist.

- `/r2f` opens the **Macro Book**, a spellbook-style window: side tabs for
  Universal and your class's sections, 2 x 6 macros per page, short names with
  the group underneath, the spell's icon (desaturated `Learn later` for spells
  you don't know yet), full tooltip (name, short name, body, note), page buttons,
  slot counter (`Character x / 18`, `Account y / 120`, red when full).
- **Import** window: paste the string from the site's "Copy import string",
  preview (`N macros: x new, y updated, z unchanged`, other-class and skipped
  counts), Import. The library is saved account-wide and has no size limit;
  every class's macros are kept.
- **Drag or click** a macro to create the real macro and put it on your cursor.
  Character slots first, account slots when those are full. Already created =
  just picked up again. A macro with the same name that isn't ours, or ours
  after you edited it, asks `Replace it?` [Replace] [Keep mine].
- **Tidy up** deletes Road to Forever macros that aren't on any action bar and
  that you haven't edited (with a confirm listing them).
- Right-click a macro: Remove from library, Copy text. Shift-click: body in chat.
- Combat-safe: no macro is created, edited, deleted or picked up in combat;
  Import / Tidy up grey out with `In combat`; a Tidy up confirmed in combat runs
  when combat ends.
- Settings (step 5), re-import updates of existing macros (step 4) and the main
  window + minimap button (step 6) are not in this version.
