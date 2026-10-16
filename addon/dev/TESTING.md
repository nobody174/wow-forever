# Road to Forever: what still needs testing in game

Reply with the number: `4.2 done`, `7.3 needs more testing`, `13.2 not working: <what you saw>`. Passed items are removed (numbers stay the
same, so there are gaps) and are listed at the bottom. The old long version is in git history (`git log -- addon/dev/TESTING.md`).
This is the only place to look: the site's pages have no test lists. Checked against the 0.62.0 interface on 2026-10-15.

**Layout today (0.62.0):** a sidebar on the left: **Home** at the top, **JOURNEY** (Plan, Talents, BiZ) and **TOOLS** (Macros, Tweaks), with
Size / Opacity sliders and a Reload UI button in the window's top bar. There is no Settings or Gameplay tab any more: the game and
minimap options are on Home, the macro slot choice and Remove all are under Macros > Options, and the old Gameplay tab is **Tweaks**
(pages: Quests, Vendors & loot, Chat & screen, Bags, Alerts, Waypoint arrow, Class icons).

**Setup:** newest release zip unzipped into AddOns, `/console scriptErrors 1`, TomTom off (BiZNav replaces it), Questie on.
Level 20+ character is best. Use a test character for anything marked **TEST CHAR**.
**Taint check, any time:** `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`: no entries.

## 2. Macros (Macros tab; the Options button holds Import, "New macros go to" and Remove all)


## 4. Talent learning (TEST CHAR, never a main)

13. **0.62.1, group picks:** nothing to see until the owner publishes a pick on the site (Saved builds > Group picks, owner login) and a new release is made; then Talents tab > Recommended shows a "Group picks" section for that class.
## 5. Home and Tweaks extras






## 7. Tweaks tab (everything is OFF until ticked; turn off ForeverPlus' matching modules)
7. Vendors & loot > Mail: list my other characters. 2026-10-16: Paladin and Shaman are both called "Venom" (Venom Oathbreaker, Venom Madstorm), so the second login overwrote the first. Fixed in the next release (saved by full name). After updating: log in on the Paladin and the Shaman once more, then open the mail list on a third character: both Venoms must show. Fast looting (needs the game's Auto Loot; Shift does the opposite) is still open.


## 8. Waypoint arrow
10. **The eight looks** (Tweaks > Waypoint arrow > "Waypoint arrow look": Flat, Gold dart, Stone arrow, Block, Needle, Gilded, Plate, Stone slab): each switches the arrow at once, the chosen button is gold, it stays after `/reload`, Reset page brings back the Stone arrow. Which do you actually keep? Say which to drop so the list stays short. Is the Needle's red end clearly the pointing end, and do the thin ones (Stone arrow, Gilded) read at Small?

## 9. Mr.BiZ (BiZ tab)

## 10. Corpse arrow (all confirmed)

## 12. Release and exports

## 13. Druid macros (0.55.0, 2 to 8 and 10 confirmed 2026-10-15; 9 (runes) and 11 (level 40) still open; use a Druid, level 20+ for Cat)
9. Rune abilities (engrave the rune first): Starsurge, Sunfire, Starfall, Lacerate, Skull Bash, Survival Instincts, Lifebloom, Nourish: does the macro cast it? Is the spell name right?
11. Level 40: does "Bear Form" in the macros need to become "Dire Bear Form"?

## 14. "Test in beta" macros that are not Druid ones
What the label means: a macro whose note starts with "Test in beta" has never been pressed in the real game: we built it from the spell list and
the rules we know. To test one: import the macros (or open the Macro Book), drag it to a bar, stand where its note says (the right class, spec or
level), press it once or twice, and answer `ok`, `does nothing`, `casts the wrong thing` or `error in chat`. For a macro with a talent or rune in its note, take
that talent / engrave that rune first. The Druid ones are section 13; these are the rest:
1. Hunter > Survival: **Raptor Strike**, **Mongoose Bite**, **Strider Kick**: each does its one thing on an enemy in melee range (Mongoose Bite needs a dodge first; Strider Kick is a rune).
2. Paladin > DPS: **Seal swap: Command <> Righteousness**: with the Twist of Light talent, does swapping between swings give the extra seal hit?
4. Shaman > Elemental: **Elemental Mastery + Chain Lightning / Lightning Bolt**: Elemental Mastery was not in the beta trees, so these may simply be useless; say if you ever see the talent.

## 15. Plan positions for the arrow (6 set from your readings on 2026-10-16; only Shaper's Terrace has no position)
7. Un'Goro Crater: Shaper's Terrace: stand on it, run `/r2f here`, send me the two lines. Also walk to Krol'dok Stronghold (43, 42) and Dire Maul (59, 43) once and tell me if the arrow is off: those two came from the web, not from standing there.

---
**Confirmed working (kept for the record):**
- *Window and Home:* the sidebar layout (6 tabs on the left), window position and last tab kept, minimap button (drag, lock, hide, Reload UI), Size / Opacity sliders, Home Quick settings box and footer, `/r2ft`, `/r2f import`, `/biz`, the 24-hour clock box and the three other Quick settings, Settings, profession export.
- *Commands and bindings:* key bindings, `/r2f help`, `/r2f nonsense` (prints unknown command), `/r2f open` (only opens), `/r2f` alone toggles.
- *Macros (2026-10-14):* Import, paste speed, Macro Book (tabs, paging, counters, Shift-click, right-click), icon macros, Replace / Keep mine, full slots and relog, Tidy up, rank-aware macros, Import replaces, combat behaviour, Options menu (slots first, Remove all).
- *Tweaks (2026-10-14):* page buttons and Reset page, auto-repair, decline duels, hide red errors, XP numbers, quests (accept, turn in, reward prices, track-all, skip shop chat), ability alert, tracking reminder, group buffs, Warrior stance icon, Home Quick settings.
- *Macros (earlier):* tooltips, greyed "?" icons, no duplicate on re-drag, Replace popup, basic Tidy up, Druid macros appear in the Macro Book.
- *Corpse arrow (section 10, 2026-10-15):* all of 3 to 8.
- *Druid macros (section 13, 0.55.0, 2026-10-15):* form numbers, bear, cat from stealth, heals from any form, cleanse, rebirth / revive, travel forms, Balance. Still open: 9 (rune abilities) and 11 (Dire Bear Form at level 40).
- *Seal timer (Paladin) and Slice and Dice timer (Rogue), 0.66.0 (5.22, 2026-10-15):* work, also in combat.
- *Food buff, text only (5.20, 2026-10-15):* "No food" red text shows only while not fed.
- *2026-10-16 round:* SkullMark icon (the skull), 4.14 Learn this build learns the points itself (commit retry fix), 12.5 interface templates (answers in ADDON_PLAN 11), 2.15 split macros, 4.5 unapplied click stops the run, 5.4 training lines (no double names), 5.10 next talent point line, 5.12 repair and pet reminders, 5.16 pick order, 5.17 "+5 points" button, 5.19 Rested XP, 5.21 newer-version notice, 2.16 import twice, 8.9 arrows point into the scene, 9.11 pink enchant line, 14.3 / 14.5 / 14.6 / 14.7 macros, 12.4 (`/r2f debug who`: the client gives "Venom Oathbreaker" via GetUnitName; fine).
- *Hunter ammo (7.16, 2026-10-15):* count, weapon-type label, red 0, hidden without a ranged weapon.
- *Talent learning (0.56 to 0.62, 2026-10-15):* 4.2 one point (applied, chat line, survives /reload), 4.3 no "didn't accept" (the addon learns talents itself, no Blizzard-window fallback needed), 4.4 five points across two trees, 4.6 combat (stops in combat, starts again after; Owner: not a real use case), 4.9 build in order (`<` `>`, order walk), 4.7 Copy link equals the site's, 4.11 "My current talents" loadout.
- *Talents tab (0.54.0):* the whole sandbox calculator, 3.1 to 3.12 including Share to Party and the Recommended builds.
- *2026-10-14 round:* updates in place (2.8), Universal list without the three Quick settings (2.12), gold ring on the selected class circle / tab (2.14), auto-sell in batches (7.3), `/r2f debug auras` probe (7.12), Copy chat window (7.15), Plan tab (8.1), waypoint arrow (8.2), `/r2f debug here` (8.3), arrow size and drag (8.4), `/bizway clear` and `size` (8.5), world map pin (8.6), BiZ rows, ranks, wishlist, menus, Alt + click arrow, enchant lines and tooltip line (9.1 to 9.7), corpse arrow setting and jump to corpse (10.1, 10.2), release checks (12.1 to 12.3).
- *2026-10-15 round:* the class picker jumps to the imported class (2.11), prerequisite arrows on the Talents tab (4.8), the pink enchant line (9.8), arrow dragging at every size (8.4), the arrow looks with the stone head and feathers (8.5 to 8.8), build in order (4.9, working, layout fixed in 0.57.1).
- *2026-10-15 evening:* the Druid tab icons in the Macro Book (4.17), the damage meter tick box in the minimap menu (4.18), the size sliders on every reminder icon, the repair reminder.
- *2026-10-15 night:* the Tweaks split into Alerts / Waypoint arrow / Class icons (7.14), the Walk on Air countdown (7.15), Class icons in two columns (7.19).
- *Other:* all of Bags (arrows, sort, movable), Plan weapon lines, Plan Waypoint buttons, `/bizway` with coordinates, Alt + right-click map arrow incl. Questie, 3D arrow, Home Training lines (Train now / Next), Interface number 16001, slot limits 120 + 30.

**Dropped by the owner:** combat drag steps of the old section 6, Questie Ctrl + click (TomTom stand-in code stays, harmless), TomTom waypoint tests, "Required level" slider (removed 0.50.0), the old Classic-API talent learning checks.
