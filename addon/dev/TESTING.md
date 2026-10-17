# Road to Forever: what still needs testing in game

Reply with the number: `4.2 done`, `7.3 needs more testing`, `13.2 not working: <what you saw>`. Numbers never change
(gaps are fine). **This file holds only open tasks.** When you confirm one it is deleted here and added to
`COMPLETED_TESTING.md` (the record of everything already tested). The old long version is in git history.
Checked against release 0.66.3 on 2026-10-16.

**Layout:** a sidebar on the left: **Home**, **JOURNEY** (Plan, Talents, BiZ) and **TOOLS** (Macros, Tweaks), with Size / Opacity
sliders and a Reload UI button in the top bar. Tweaks pages: Quests, Vendors & loot, Chat & screen, Bags, Alerts, Waypoint arrow, Class icons.

**Setup:** newest release zip unzipped into AddOns, `/console scriptErrors 1`, TomTom off (BiZNav replaces it), Questie on.
Use a test character for anything marked **TEST CHAR**.
**Taint check, any time:** `/console taintLog 1`, play, `/reload`, search `Logs	aint.log` for `RoadToForever`: no entries.

## To test in the next release (timers in combat)
5.25. **Seal (Paladin) and Slice and Dice (Rogue) timers in a fight:** put a seal up (or Slice and Dice), start a fight and keep watching the icon. It should keep counting down; if the game hides your buffs in the fight the number shows with a "~" in front ("~1750") instead of disappearing. Cast a new seal / Slice and Dice mid-fight: the number jumps to the full time again. After the fight, a number without "~" returns. Then, in the middle of a fight, run `/r2f debug timers` and send me the lines (it says how many of your buffs the game hides and what each timer can read).



5.29. **Rogue weapon lines (next release):** on a Rogue, the Plan tab's "Weapon:" lines may now offer one-handed axes (Forever lets Rogues use them). Nothing to do unless a line shows an axe you cannot actually equip: tell me which.

5.30. **No weather box (0.66.6):** Home > Quick settings, last box "No weather (rain, snow, dust)": tick it, the rain / snow / dust particles stop (move to a place with weather if needed); untick: back to your normal setting. Is the Home page still tidy (the minimap block is one row lower)?

## To test now (0.66.3)
5.23. **Food nag:** Tweaks > Class icons > Food buff > tick "Show No food when I am not fed", take off your food buff: "No food" shows. Board a flight path: it goes away while you fly and returns after landing. Walk into a capital (Stormwind, Ironforge, Darnassus, Undercity, Orgrimmar, Thunder Bluff): it is gone there too. Tell me if a capital still shows it (the map id or zone name differs on Forever).
5.24. **Quest shopping list:** Plan tab > "Quest shopping list" (top right): quests whose items you can buy instead of farm, grouped by phase, with counts ("3x Boar Intestines"). Tick one: it stays ticked after /reload and the line at the top counts it. "Back to the steps" brings the launch list back. Check that nothing overlaps and long notes fit.
7.7. **Mail list, characters sharing a first name:** characters are saved by full name now. Log in once on each of your characters that share a first name, then open the mail list on a third character: both must show. Fast looting (needs the game's Auto Loot; Shift does the opposite) is still open.
8.10. **The eight arrow looks** (Tweaks > Waypoint arrow > "Waypoint arrow look": Flat, Gold dart, Stone arrow, Block, Needle, Gilded, Plate, Stone slab): which do you actually keep? Say which to drop. Is the Needle's red end clearly the pointing end, and do the thin ones (Stone arrow, Gilded) read at Small?
15.7. **Un'Goro Crater, Shaper's Terrace:** stand on it, run `/r2f here`, send the two lines. Also walk to Krol'dok Stronghold (43, 42) and Dire Maul (59, 43) once and tell me if the arrow is off (those came from the web).

## Cannot be tested yet (reason)
- 4.13 group picks: nothing to see until the owner publishes a pick on the site (Saved builds > Group picks, owner login) and a new release is made.
- 13.9 Druid rune abilities (Starsurge, Sunfire, Starfall, Lacerate, Skull Bash, Survival Instincts, Lifebloom, Nourish): needs the level and the runes. Does the macro cast it? Is the spell name right?
- 13.11 Level 40: does "Bear Form" in the macros need to become "Dire Bear Form"?
- 14.1 Hunter > Survival **Raptor Strike**, **Mongoose Bite**, **Strider Kick**: skills not acquired in the beta yet.
- 14.2 Paladin **Seal swap: Command <> Righteousness**: needs the Twist of Light talent (not enough points in the beta). The macro itself seems to work.
- 14.4 Shaman **Elemental Mastery + Chain Lightning / Lightning Bolt**: the talent is not in the beta trees.
