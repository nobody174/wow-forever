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
5.25. **Seal (Paladin) and Slice and Dice (Rogue) timers in a fight (0.66.10):** Paladin: cycle Seal of Command / Righteousness with your macro in a fight; the icon and number must follow the seal you cast last (never stay on the first). Rogue: cast Slice and Dice during a fight; the icon must show with a "~" number (about 6 + 3 per combo point). If something is off, run `/r2f debug timers` in the fight and paste the lines.




5.32. **Recorder (next release):** play as normal. Loot a few creatures, open a vendor window, open a quest with rewards. Then type `/r2f record`: it prints counts of creatures looted, vendors and quests. `/r2f record off` stops it, `/r2f record on` starts again. Nothing should show on screen or lag. After /reload or logout the counts must still be there. Send me your `WTF/Account/<account>/SavedVariables/RoadToForever.lua` before the beta ends (the 21st) and I merge it (teammates too).

5.33. **Themes (0.68.0):** nothing has been seen in the real client yet.
- Fresh look: with no change, the window looks exactly as before (Classic, bronze dialog border).
- Home > **Theme: Classic** button (right of the "Minimap" heading, above its two switches): pick each of the other four (Azeroth Reforged, Obsidian Night, Ember & Iron, Frost & Void). Panel, sidebar, divider line under the title, frame line, title and selected tab colour should change at once without a reload. The bronze border is replaced by a thin coloured line: does it look right, or is there a gap / double border?
- The Theme button must not touch the Quick settings notes, the right-hand column ("What to train next", share text) or the Minimap switches, at window size 0.5, 1 and 1.5 (top-bar Size slider).
- The switches on Home and the tick boxes in the quest log should take the theme's colour (green in Classic).
- The choice survives /reload and relog. Size and Opacity sliders still work in every theme; Frost & Void stays readable at the lowest opacity.
- Open each tab (Plan, Talents, BiS, Macros, Gameplay) in each theme: is the text readable? (Pages still use white and gold text, so only dark themes exist for now.)
- No Lua errors or taint warnings; changing the theme in combat should just recolour the window.


5.35. **Corpse arrow (0.68.2):** die, release your spirit, and see if the arrow points at your corpse (chat says it is set). If not: while still a ghost type `/r2f debug corpse` and paste the lines. Also try dying close to a graveyard and far from one (a ghost in another zone is the case this fixes), and once inside a dungeon.

5.36. **Azeroth Reforged decoration (0.69.0):** Home > Theme > Azeroth Reforged. It should show: a brown stone gradient panel, a gold double line round the window with round gold gems in the four corners, a dark banner with gold edge and gems at the top middle holding the page title, brown gradient buttons in the sidebar (the selected one with a gold edge and a glowing orange gem), a thin gold line fading out after JOURNEY / TOOLS, and a darker inset behind the pages. Headings should be in Cinzel (capital-style serif) and the rest in Alegreya Sans.
- Does any heading or label get cut off or overlap because the new fonts are wider? Which page?
- Does the banner collide with the Size slider on the right? Does it look close to the mockup, or should I ask Claude Desktop for exported images?
- If the game refuses a font you should see the old game font instead of a broken one.
- Switch back to Classic and to Obsidian: all decoration must disappear and the fonts return to the game's.
- Size and Opacity sliders still work (the panel gets see-through with Opacity).

## Cannot be tested yet (reason)
- 4.13 group picks: nothing to see until the owner publishes a pick on the site (Saved builds > Group picks, owner login) and a new release is made.
- 13.9 (owner: not seen in the beta yet, check after release) Druid spells that Forever gives its own versions of (Starsurge, Sunfire, Starfall, Lacerate): they are not runes (corrected 2026-10-17). Needs the level: does each macro cast it, and how is it learned (trainer or talent)? The Skull Bash, Survival Instincts, Lifebloom and Nourish macros were removed (those spells exist only as Season of Discovery leftovers).
- 13.11 (owner: beta stops at level 30) Level 40: does "Bear Form" in the macros need to become "Dire Bear Form"?
- 14.1 Hunter **Strider Kick** only (Raptor Strike and Mongoose Bite confirmed): not in the beta yet.
- 14.2 Paladin **Seal swap: Command <> Righteousness**: needs the Twist of Light talent (not enough points in the beta). The seal-swap macro itself works (confirmed 2026-10-17); only the Twist of Light talent is untested.
- 14.4 Shaman **Elemental Mastery + Chain Lightning / Lightning Bolt**: the talent is in the Elemental tree now (the deepest row, 31 points in), so not reachable at level 30.
