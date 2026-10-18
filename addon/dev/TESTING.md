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


5.38. **Azeroth Reforged round 2 (0.71.0, brightness fixed in 0.71.1):** compare with `azeroth_reforged.png`.
- Darker brown and stronger gold than in 0.70.1? (The slices match the design's colours; if it still looks lighter in game, say where and I look for a tint on our side.)
- Sidebar: an icon on every button, gold when selected, muted otherwise; JOURNEY / CHARACTER / UI as letter-spaced gold words with a fading line.
- Home, top right: three stone cards 18 / 01 / 44 with DAYS / HOURS / MINUTES under the numbers and the date below. Do the numbers fit the cards? Does the narrower Launch plan entry look fine?
- Switches on Home (Quick settings, Minimap) are the new track with a knob (amber when on); tick boxes in the quest log are the new check box.
- Size / Opacity sliders: dark groove, amber filled part up to the knob, amber pearl knob.
- Buttons: Reload UI and Theme show the stone art; a greyed-out button looks greyed.
- Classic and Obsidian must look as before (plain dark cards for the countdown).
- Anything cut off, wrongly placed or overlapping: tell me where.

5.39. **Ember & Iron (0.72.0):** Home > Theme > Ember & Iron, compare with `ember_preview.png` (Downloads).
- Frame: steel border with cut corners (top-left and bottom-right), four rivets, a glow of heat along the bottom edge, steel panel with fine vertical lines.
- Sidebar: two columns of three tiles (HOME / PLAN, TALENTS / GEAR, MACROS / TWEAKS), the current one glowing orange, icons and labels inside; no JOURNEY / CHARACTER / UI headings. Does a label touch the tile edge?
- Home: the countdown on one wide dark plate (18 / 17 / ... numbers in Chakra Petch), Quick settings switches orange with a grey or orange knob, Reload UI and other buttons steel with an orange primary one ("Export professions").
- Sliders: dark groove with an orange-to-amber fill and a molten bead knob.
- Switch to Azeroth Reforged and Classic and back: sidebar list returns, nothing of Ember left behind. Fonts: condensed headings (Barlow Condensed); if something is cut off or overlaps say where.
- Does the page content (Plan, Talents, BiS, Macros, Tweaks) still fit and read well on the steel plate?

5.40. **Obsidian Night (0.73.0):** Home > Theme > Obsidian Night.
- No sidebar: a row of tabs under the top bar (Home, Launch plan, Builds, Gear, Macros, Tweaks), the open one with a teal underline; hover lights a tab. The window is taller by 44 px. Is it still fully on your screen, and does every page (Home, Launch plan, Builds & talents, Gear, Macros, Tweaks) fit in the new space, especially Builds & talents (the tall one)?
- Rounded frame, dark card behind the page, teal buttons / switches / tick boxes, thin teal sliders with a pearl knob, the countdown on one dark plate.
- Text: is it readable and not cut off with the new font (Space Grotesk)? Numbers in JetBrains Mono.
- Buttons: the glow of hover / primary is inside the art; do the buttons look slightly bigger than their text area?
- Switch back to Classic / Azeroth / Ember: the sidebar and the window height come back each time.
- Ember & Iron: the open tile's name should be paler than before (readable on the glow).

5.41. **Frost & Void (0.74.0):** Home > Theme > Frost & Void.
- Window: deep indigo with faint stars, a violet glow lower left, a cyan glow upper right, rounded corners with small corner brackets.
- Sidebar: six round orbs in a chain (a thin line joins them), icons inside, the open one glowing cyan with a ring, no sidebar background. Do the orbs line up with their names? Is the line behind them, not through the names?
- Home: the countdown on a glass card, glass behind the pages, violet-to-blue primary button ("Export professions"), pill switches with a glowing pearl, round tick boxes in the quest log.
- Sliders: groove filling from violet to cyan, a pearl knob.
- Text readable in Sora; at the lowest Opacity the window should stay nearly solid.
- Switch to the other themes and back: nothing of Frost & Void should stay behind.

5.42. **ThreatMaster on the minimap menu (0.74.1):** right-click the minimap button: a "ThreatMaster (/tm)" tick next to "Damage meter (Blizzard)". Tick it: the ThreatMaster window shows or hides like /tm does, and the tick follows. No error, also if you use it in combat? (Tell me if the game blocks anything.)

## Cannot be tested yet (reason)
- 4.13 group picks: nothing to see until the owner publishes a pick on the site (Saved builds > Group picks, owner login) and a new release is made.
- 13.9 (owner: not seen in the beta yet, check after release) Druid spells that Forever gives its own versions of (Starsurge, Sunfire, Starfall, Lacerate): they are not runes (corrected 2026-10-17). Needs the level: does each macro cast it, and how is it learned (trainer or talent)? The Skull Bash, Survival Instincts, Lifebloom and Nourish macros were removed (those spells exist only as Season of Discovery leftovers).
- 13.11 (owner: beta stops at level 30) Level 40: does "Bear Form" in the macros need to become "Dire Bear Form"?
- 14.1 Hunter **Strider Kick** only (Raptor Strike and Mongoose Bite confirmed): not in the beta yet.
- 14.2 Paladin **Seal swap: Command <> Righteousness**: needs the Twist of Light talent (not enough points in the beta). The seal-swap macro itself works (confirmed 2026-10-17); only the Twist of Light talent is untested.
- 14.4 Shaman **Elemental Mastery + Chain Lightning / Lightning Bolt**: the talent is in the Elemental tree now (the deepest row, 31 points in), so not reachable at level 30.
