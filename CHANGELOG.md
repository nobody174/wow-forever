# Changelog

Authoritative history of what's actually shipped on wow-forever-macro. Working
history for whoever builds this next (including a future Claude session) — not
user-facing release notes.

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
