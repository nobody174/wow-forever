# Road to Forever: what still needs testing in game

Reply with the number: `4.2 done`, `7.3 needs more testing`, `13.2 not working: <what you saw>`. Passed items are removed (numbers stay the
same, so there are gaps) and are listed at the bottom. The old long version is in git history (`git log -- addon/dev/TESTING.md`).
This is the only place to look: the site's pages have no test lists. Checked against the 0.62.0 interface on 2026-10-15.

**Layout today (0.62.0):** a sidebar on the left: **Home** at the top, **JOURNEY** (Plan, Talents, BiZ) and **TOOLS** (Macros, Tweaks), with
Size / Opacity sliders and a Reload UI button in the window's top bar. There is no Settings or Gameplay tab any more: the game and
minimap options are on Home, the macro slot choice and Remove all are under Macros > Options, and the old Gameplay tab is **Tweaks**
(pages: Quests, Vendors & loot, Chat & screen, Bags, Alerts & HUD).

**Setup:** newest release zip unzipped into AddOns, `/console scriptErrors 1`, TomTom off (BiZNav replaces it), Questie on.
Level 20+ character is best. Use a test character for anything marked **TEST CHAR**.
**Taint check, any time:** `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`: no entries.

## 2. Macros (Macros tab; the Options button holds Import, "New macros go to" and Remove all)
15. **New in 0.56.1, split macros:** import the site string again. Hunter: Raptor Strike (starts auto-attack in melee), Wing Clip; Survival: Raptor Strike, Mongoose Bite (needs a dodge first), Strider Kick; Rogue: Sap. Each does its one thing on a hostile target. The old combined macros stay on your bars until you remove them.
16. **0.57.1:** import the same string twice: the second chat line says "0 new, 0 updated, N unchanged".

## 4. Talent learning (TEST CHAR, never a main)
2. One point: click ONE tier-1 talent on the board (after a trainer reset), Learn this build, Cancel (nothing changes), Learn: applied within ~2 s, chat "Learned 1 talent point.", free points one lower, no "Interface action failed", survives `/reload`.
3. If it stops with "didn't accept" or "waiting in Blizzard's window": note the exact message and what Blizzard's window shows.
4. **Open until the owner drops it:** 5 points across tier 1 and 2: counts `Learning 1 / 5` ..., exact build at the end, none pending.
9. **New in 0.56.0, build in order:** load a Recommended build: `<` `>` appear under the board right of "points spent". `<` takes one point off, `>` puts it back; the line "Build in order: point 12 of 21" and "reached at level N" follow; hovering a talent says "Build order: points 1 to 5 (levels 10 to 14)". Walk it from 0 to the end: is the order sensible to play? Clicking a talent yourself starts a new build (the stepper counts from your edit). On your own class with the build on the board: "Next point in this build: X (point n, level L)" on the right, and it moves on after you learn a point. Learn this build while stepped back learns only what is shown.
5. Your own unapplied click in Blizzard's window (not the addon's board) stops the run ("changes that aren't applied yet"), nothing learned.
6. Combat mid-run stops cleanly and continues after combat without a popup; Stop then Learn does not buy a point twice.
7. Full build, then Copy link: the link equals the site's for that build.
11. **New in 0.62.0, start from my talents:** Talents tab > Loadouts: the first entry "My current talents (start from here)" puts your real talents on the board; edit from there, Learn works as before.

13. **0.62.1, group picks:** nothing to see until the owner publishes a pick on the site (Saved builds > Group picks, owner login) and a new release is made; then Talents tab > Recommended shows a "Group picks" section for that class.
## 5. Home and Tweaks extras
4. Training reminder (Tweaks > Alerts & HUD): at level-up chat names the new spells; Home's "Training" block lists what to train after you visit your trainer once. Home's "Next talent point" now has its own heading and a gold line (0.57.1): easy to see now?
10. **New in 0.56.2:** put a build on the Talents board on your own class (Recommended), then open Home: right column under Training says "Next talent point: X (point n, level L)". Learn a point of it, or level up: chat prints the line after the training line, and it moves on. A different build on the board changes it.
12. **New in 0.62.0, reminders:** Tweaks > Alerts & HUD > Icons for your class now has **Gear repair reminder** (every class) and, for a Hunter / Warlock, **Pet reminder**. Repair: wear something down (or lower the "Turn red below" slider to 90) and check the red percentage appears, and goes after repairing; `/r2f repair`, `/r2f repair lock`. Pet: dismiss your pet: "No pet"; let it die: "Dead"; a Hunter pet at unhappy: "Unhappy"; nothing while mounted or dead; `/r2f pet`.

## 7. Tweaks tab (everything is OFF until ticked; turn off ForeverPlus' matching modules)
7. Vendors & loot > Mail: list my other characters. `/dump R2FDB.chars` on 2026-10-14 showed 7 characters saved (Despicable, Madfury, Miss, Aoe, Falseaim, Madblade, Venom) and NO Paladin or Shaman: they were never recorded. Tick Road to Forever for them on the character select AddOns screen, log in on each, run `/dump R2FDB.chars` again, then check the mail list. Fast looting (needs the game's Auto Loot; Shift does the opposite) is still open.
16. Hunter ammo (Hunter with a ranged weapon; Icons for your class): the count equals arrows / bullets in all bags; switching weapon type switches the label; red 0 with no ammo; hidden with no ranged weapon when locked; the "warn when under" slider; `/r2f ammo`.

## 8. Waypoint arrow
9. **0.61.0, the arrows point into the scene:** turn so the target is straight ahead: does the arrow look like it points away from you into the distance (not just up)? Turn around so it is behind you: does it point toward you? Sideways: lying on the ground? Is the camera angle right, or should it be lower or higher?
10. **The eight looks** (Tweaks > Alerts & HUD > "Waypoint arrow look": Flat, Gold dart, Stone arrow, Block, Needle, Gilded, Plate, Stone slab): each switches the arrow at once, the chosen button is gold, it stays after `/reload`, Reset page brings back the Stone arrow. Which do you actually keep? Say which to drop so the list stays short. Is the Needle's red end clearly the pointing end, and do the thin ones (Stone arrow, Gilded) read at Small?

## 9. Mr.BiZ (BiZ tab)
11. Hover a gear slot on the doll: ONE enchant line, the pink "Mr.BiZ enchant: ..." from the item tooltip (the extra "Enchant: ..." line from 0.56.3 was removed in 0.57.1). The opened slot's enchant lines on the right are pink too.

## 10. Corpse arrow (1 and 2 confirmed; 3 to 8 not tested yet)
3. Release spirit: the arrow stays on the corpse (does it appear only after release?).
4. Alive again: corpse arrow goes, the earlier arrow returns (none before = none left).
5. Setting another arrow while dead is not replaced on revive.
6. `/reload` as a ghost: arrow points at the corpse again.
7. Switch unticked: no arrow on death.
8. Death inside a dungeon: error, or just no arrow?

## 12. Release and exports
4. `/r2f debug who` on the Paladin: send the lines (which one reads "Thorin Stormborn"?).
5. Interface templates (run each as its own command: `/dump R2FMain ~= nil`, then `/dump R2FMainTab1.r2fTemplate`, then `/dump MenuUtil ~= nil`, then `/dump R2F.Minimap.backend`): note the answers in ADDON_PLAN 11 if not already there.

## 13. Druid macros (0.55.0, all untested in game; use a Druid, level 20+ for Cat)
2. **Form numbers (the key check).** Cat Form + Prowl: press once, you become a cat; press again, you Prowl. If it casts the wrong form or does nothing, tell me your learned forms (Aquatic Form learned? level 16) and the number that works (2 or 3). Same for Claw / Shred / Rake / Dash.
3. Bear: Bear Form (no unshift) does nothing when already a bear; Growl@ taunts the mouseover; Maul queues on the next hit; Swipe, Demoralizing Roar, Enrage, Frenzied Regeneration shift you first and work. One press must be enough (not two).
4. Cat from stealth: Ravage / Pounce from Prowl; Tiger's Fury, Dash, Rip, Ferocious Bite work.
5. Heal from any form (Shift = Regrowth) leaves the form and heals; plain heals (Healing Touch, Regrowth, Rejuvenation) work on mouseover / target / yourself.
6. Cleanse: Abolish Poison, Shift = Remove Curse; Cure Poison / Remove Curse singles.
7. Rebirth in combat / Revive outside it (on a dead friend under the mouse); Innervate; Barkskin and Shift = Nature's Grasp (do they drop your form?).
8. Travel / Aquatic / Cat on one key; Cat Form (Shift = Bear Form); Leave form and dismount; Teleport: Moonglade.
9. Rune abilities (engrave the rune first): Starsurge, Sunfire, Starfall, Lacerate, Skull Bash, Survival Instincts, Lifebloom, Nourish: does the macro cast it? Is the spell name right?
10. Balance: Starfire (back into Moonkin, Ctrl = Wrath), Insect Swarm, Hurricane at cursor.
11. Level 40: does "Bear Form" in the macros need to become "Dire Bear Form"?

## 14. "Test in beta" macros that are not Druid ones
What the label means: a macro whose note starts with "Test in beta" has never been pressed in the real game: we built it from the spell list and
the rules we know. To test one: import the macros (or open the Macro Book), drag it to a bar, stand where its note says (the right class, spec or
level), press it once or twice, and answer `ok`, `does nothing`, `casts the wrong thing` or `error in chat`. For a macro with a talent or rune in its note, take
that talent / engrave that rune first. The Druid ones are section 13; these are the rest:
1. Hunter > Survival: **Raptor Strike**, **Mongoose Bite**, **Strider Kick**: each does its one thing on an enemy in melee range (Mongoose Bite needs a dodge first; Strider Kick is a rune).
2. Paladin > DPS: **Seal swap: Command <> Righteousness**: with the Twist of Light talent, does swapping between swings give the extra seal hit?
3. Warrior > General: **Retaliation with 2H (from Defensive)**: press twice (1st equips the two-hander and swaps to Battle Stance, 2nd casts Retaliation).
4. Shaman > Elemental: **Elemental Mastery + Chain Lightning / Lightning Bolt**: Elemental Mastery was not in the beta trees, so these may simply be useless; say if you ever see the talent.
5. Warrior > Tank: **Shield Block + Sunder Armor** (the Revenge version works, owner 2026-10-15): skip if you do not use it.

---
**Confirmed working (kept for the record):**
- *Window and Home:* the sidebar layout (6 tabs on the left), window position and last tab kept, minimap button (drag, lock, hide, Reload UI), Size / Opacity sliders, Home Quick settings box and footer, `/r2ft`, `/r2f import`, `/biz`, the 24-hour clock box and the three other Quick settings, Settings, profession export.
- *Commands and bindings:* key bindings, `/r2f help`, `/r2f nonsense` (prints unknown command), `/r2f open` (only opens), `/r2f` alone toggles.
- *Macros (2026-10-14):* Import, paste speed, Macro Book (tabs, paging, counters, Shift-click, right-click), icon macros, Replace / Keep mine, full slots and relog, Tidy up, rank-aware macros, Import replaces, combat behaviour, Options menu (slots first, Remove all).
- *Tweaks (2026-10-14):* page buttons and Reset page, auto-repair, decline duels, hide red errors, XP numbers, quests (accept, turn in, reward prices, track-all, skip shop chat), ability alert, tracking reminder, group buffs, Warrior stance icon, Home Quick settings.
- *Macros (earlier):* tooltips, greyed "?" icons, no duplicate on re-drag, Replace popup, basic Tidy up, Druid macros appear in the Macro Book.
- *Talents tab (0.54.0):* the whole sandbox calculator, 3.1 to 3.12 including Share to Party and the Recommended builds.
- *2026-10-14 round:* updates in place (2.8), Universal list without the three Quick settings (2.12), gold ring on the selected class circle / tab (2.14), auto-sell in batches (7.3), `/r2f debug auras` probe (7.12), Copy chat window (7.15), Plan tab (8.1), waypoint arrow (8.2), `/r2f debug here` (8.3), arrow size and drag (8.4), `/bizway clear` and `size` (8.5), world map pin (8.6), BiZ rows, ranks, wishlist, menus, Alt + click arrow, enchant lines and tooltip line (9.1 to 9.7), corpse arrow setting and jump to corpse (10.1, 10.2), release checks (12.1 to 12.3).
- *2026-10-15 round:* the class picker jumps to the imported class (2.11), prerequisite arrows on the Talents tab (4.8), the pink enchant line (9.8), arrow dragging at every size (8.4), the arrow looks with the stone head and feathers (8.5 to 8.8), build in order (4.9, working, layout fixed in 0.57.1).
- *Other:* all of Bags (arrows, sort, movable), Plan weapon lines, Plan Waypoint buttons, `/bizway` with coordinates, Alt + right-click map arrow incl. Questie, 3D arrow, Home Training lines (Train now / Next), Interface number 16001, slot limits 120 + 30.

**Dropped by the owner:** combat drag steps of the old section 6, Questie Ctrl + click (TomTom stand-in code stays, harmless), TomTom waypoint tests, "Required level" slider (removed 0.50.0), the old Classic-API talent learning checks.
