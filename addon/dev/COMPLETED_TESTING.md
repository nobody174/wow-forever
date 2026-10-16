# Road to Forever: tested and confirmed in game

The record of what the owner has tested and confirmed. Open tasks are in `TESTING.md`; when an item there is
confirmed it is deleted from that file and added here in the same pass (newest round first). Numbers are the
`section.item` numbers of TESTING.md at the time.

## 2026-10-17 round (0.66.5)
- 5.26 combat banner (lock, drag, size), 5.27 no /reload line at login, 5.28 Recommended builds after the talent-tree update.

## 2026-10-16 round (releases 0.66.2 and 0.66.3 and earlier builds)
- 4.14 Learn this build learns all points itself (commit retry fix, 0.66.2); the skull macro icon; 12.5 interface templates (answers in ADDON_PLAN 11); 2.15 split macros; 2.16 import twice says "0 new, 0 updated, N unchanged"; 4.5 an unapplied click in Blizzard's window stops the run; 5.4 training lines without double names; 5.10 next talent point line; 5.12 repair and pet reminders; 5.16 pick order; 5.17 "+5 points" button on the Builds page; 5.19 Rested XP icon (off by default); 5.21 newer-version notice; 8.9 arrows point into the scene; 9.11 pink enchant line; 12.4 `/r2f debug who`; 14.3, 14.5, 14.6, 14.7 macros.
- Owner note 2026-10-16: the Paladin Seal and Rogue Slice and Dice timers disappear in combat (listed as working earlier; now a backlog item).

## Earlier
- *Window and Home:* the sidebar layout (6 tabs on the left), window position and last tab kept, minimap button (drag, lock, hide, Reload UI), Size / Opacity sliders, Home Quick settings box and footer, `/r2ft`, `/r2f import`, `/biz`, the 24-hour clock box and the three other Quick settings, Settings, profession export.
- *Commands and bindings:* key bindings, `/r2f help`, `/r2f nonsense` (prints unknown command), `/r2f open` (only opens), `/r2f` alone toggles.
- *Macros (2026-10-14):* Import, paste speed, Macro Book (tabs, paging, counters, Shift-click, right-click), icon macros, Replace / Keep mine, full slots and relog, Tidy up, rank-aware macros, Import replaces, combat behaviour, Options menu (slots first, Remove all).
- *Tweaks (2026-10-14):* page buttons and Reset page, auto-repair, decline duels, hide red errors, XP numbers, quests (accept, turn in, reward prices, track-all, skip shop chat), ability alert, tracking reminder, group buffs, Warrior stance icon, Home Quick settings.
- *Macros (earlier):* tooltips, greyed "?" icons, no duplicate on re-drag, Replace popup, basic Tidy up, Druid macros appear in the Macro Book.
- *Corpse arrow (section 10, 2026-10-15):* all of 3 to 8.
- *Druid macros (section 13, 0.55.0, 2026-10-15):* form numbers, bear, cat from stealth, heals from any form, cleanse, rebirth / revive, travel forms, Balance. Still open: 9 (rune abilities) and 11 (Dire Bear Form at level 40).
- *Seal timer (Paladin) and Slice and Dice timer (Rogue), 0.66.0 (5.22, 2026-10-15):* work, also in combat.
- *Food buff, text only (5.20, 2026-10-15):* "No food" red text shows only while not fed.
- *2026-10-16 round:* SkullMark icon (the skull), 4.14 Learn this build learns the points itself (commit retry fix), 12.5 interface templates (answers in ADDON_PLAN 11), 2.15 split macros, 4.5 unapplied click stops the run, 5.4 training lines (no double names), 5.10 next talent point line, 5.12 repair and pet reminders, 5.16 pick order, 5.17 "+5 points" button, 5.19 Rested XP, 5.21 newer-version notice, 2.16 import twice, 8.9 arrows point into the scene, 9.11 pink enchant line, 14.3 / 14.5 / 14.6 / 14.7 macros, 12.4 (`/r2f debug who`: the client gives the full name via GetUnitName; fine).
- *Hunter ammo (7.16, 2026-10-15):* count, weapon-type label, red 0, hidden without a ranged weapon.
- *Talent learning (0.56 to 0.62, 2026-10-15):* 4.2 one point (applied, chat line, survives /reload), 4.3 no "didn't accept" (the addon learns talents itself, no Blizzard-window fallback needed), 4.4 five points across two trees, 4.6 combat (stops in combat, starts again after; Owner: not a real use case), 4.9 build in order (`<` `>`, order walk), 4.7 Copy link equals the site's, 4.11 "My current talents" loadout.
- *Talents tab (0.54.0):* the whole sandbox calculator, 3.1 to 3.12 including Share to Party and the Recommended builds.
- *2026-10-14 round:* updates in place (2.8), Universal list without the three Quick settings (2.12), gold ring on the selected class circle / tab (2.14), auto-sell in batches (7.3), `/r2f debug auras` probe (7.12), Copy chat window (7.15), Plan tab (8.1), waypoint arrow (8.2), `/r2f debug here` (8.3), arrow size and drag (8.4), `/bizway clear` and `size` (8.5), world map pin (8.6), BiZ rows, ranks, wishlist, menus, Alt + click arrow, enchant lines and tooltip line (9.1 to 9.7), corpse arrow setting and jump to corpse (10.1, 10.2), release checks (12.1 to 12.3).
- *2026-10-15 round:* the class picker jumps to the imported class (2.11), prerequisite arrows on the Talents tab (4.8), the pink enchant line (9.8), arrow dragging at every size (8.4), the arrow looks with the stone head and feathers (8.5 to 8.8), build in order (4.9, working, layout fixed in 0.57.1).
- *2026-10-15 evening:* the Druid tab icons in the Macro Book (4.17), the damage meter tick box in the minimap menu (4.18), the size sliders on every reminder icon, the repair reminder.
- *2026-10-15 night:* the Tweaks split into Alerts / Waypoint arrow / Class icons (7.14), the Walk on Air countdown (7.15), Class icons in two columns (7.19).
- *Other:* all of Bags (arrows, sort, movable), Plan weapon lines, Plan Waypoint buttons, `/bizway` with coordinates, Alt + right-click map arrow incl. Questie, 3D arrow, Home Training lines (Train now / Next), Interface number 16001, slot limits 120 + 30.

**Dropped by the owner:** combat drag steps of the old section 6, Questie Ctrl + click (TomTom stand-in code stays, harmless), TomTom waypoint tests, "Required level" slider (removed 0.50.0), the old Classic-API talent learning checks.
