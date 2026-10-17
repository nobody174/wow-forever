# Road to Forever: what still needs testing in game

Reply with the number: `4.2 done`, `7.3 needs more testing`, `13.2 not working: <what you saw>`. Numbers never change
(gaps are fine). **This file holds only open tasks.** When you confirm one it is deleted here and added to
`COMPLETED_TESTING.md` (the record of everything already tested). The old long version is in git history.
Checked against release 0.66.6 on 2026-10-17.

**Layout:** a sidebar on the left: **Home**, **JOURNEY** (Plan, Talents, BiZ) and **TOOLS** (Macros, Tweaks), with Size / Opacity
sliders and a Reload UI button in the top bar. Tweaks pages: Quests, Vendors & loot, Chat & screen, Bags, Alerts, Waypoint arrow, Class icons.

**Setup:** newest release zip unzipped into AddOns, `/console scriptErrors 1`, TomTom off (BiZNav replaces it), Questie on.
Use a test character for anything marked **TEST CHAR**.
**Taint check, any time:** `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`: no entries.

## To test (0.66.6 and the next release)
5.25. **Seal (Paladin) and Slice and Dice (Rogue) timers in a fight:** put a seal up (or Slice and Dice), start a fight and keep watching the icon. It should keep counting down; if the game hides your buffs in the fight the number shows with a "~" in front ("~1750") instead of disappearing. Cast a new seal / Slice and Dice mid-fight: the number jumps to the full time again. After the fight, a number without "~" returns. Then, in the middle of a fight, run `/r2f debug timers` and send me the lines (it says how many of your buffs the game hides and what each timer can read).



5.29. **Rogue weapon lines (next release):** on a Rogue, the Plan tab's "Weapon:" lines may now offer one-handed axes (Forever lets Rogues use them). Nothing to do unless a line shows an axe you cannot actually equip: tell me which.

5.31. **Click an item of the quest shopping list to copy it (next release):** Plan tab > Quest shopping list: every item is a line you can click. A small box opens with just the item name selected (no number): press Ctrl+C, then paste it into the auction house search. Clicking anywhere else closes the box. Does it feel right, or should the click do something else?


## Cannot be tested yet (reason)
- 4.13 group picks: nothing to see until the owner publishes a pick on the site (Saved builds > Group picks, owner login) and a new release is made.
- 13.9 Druid spells that Forever gives its own versions of (Starsurge, Sunfire, Starfall, Lacerate): they are not runes (corrected 2026-10-17). Needs the level: does each macro cast it, and how is it learned (trainer or talent)? The Skull Bash, Survival Instincts, Lifebloom and Nourish macros were removed (those spells exist only as Season of Discovery leftovers).
- 13.11 Level 40: does "Bear Form" in the macros need to become "Dire Bear Form"?
- 14.1 Hunter > Survival **Raptor Strike**, **Mongoose Bite**, **Strider Kick**: skills not acquired in the beta yet.
- 14.2 Paladin **Seal swap: Command <> Righteousness**: needs the Twist of Light talent (not enough points in the beta). The macro itself seems to work.
- 14.4 Shaman **Elemental Mastery + Chain Lightning / Lightning Bolt**: the talent is in the Elemental tree now (the deepest row, 31 points in), so not reachable at level 30.
