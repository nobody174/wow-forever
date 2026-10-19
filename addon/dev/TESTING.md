# Road to Forever: open tests

Reply with the number: `5.25 done`, `5.38 needs more testing`, `5.41 not working: <what you saw>`. Numbers never change (gaps are fine).
**Only open tasks live here.** A confirmed test moves to `COMPLETED_TESTING.md`.
Checked against release 0.76.1 on 2026-10-19.

**Setup:** newest release zip in AddOns, `/console scriptErrors 1`. Taint check: `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`.

## To test (0.76.1: every theme was rebuilt blind, so expect rough edges and tell me where)
For every look (Home > Theme > "Open the gallery"): compare with its picture in Downloads, then open each tab (Plan, Talents, Gear, Macros, Tweaks).
- **5.32 Recorder:** loot a few creatures, open a vendor, open a quest. `/r2f record` prints counts; `/r2f record off` / `on` work. **Send me `WTF/Account/<account>/SavedVariables/RoadToForever.lua` before the 21st** (teammates too).
- **5.43 Setup Hunter, the reload button only:** run Setup Hunter, press "Reload now": the game must reload with no "Interface action failed" message.
- **5.58 Fixes from your first test (0.76.1):** Obsidian / Gnomish Home cards sit under the countdown (no boxes above the window); the Talents buttons along the bottom are inside the window in every look; the Tweaks tab no longer touches the top bar in Ember / Frost; Frost's top-right group fits its pill; Scribe has no white glow on the contents lines; the close X matches the look.
- **5.50 Gallery:** Home > Theme opens "Choose a look". Click a card: the window changes at once, "PREVIEWING" shows, Keep / Revert (8s) appear. Keep keeps it; Revert, the countdown and closing the gallery put the old look back. "Surprise me" tries another. Do the thumbnails look right, nothing cut off? In 0.76.1 the gallery wears the look in use (frame, cards, text): check it in each look.
- **5.51 Frost & Void** (`frost_new_preview.png`, `Frost & Void.png`): wider window, round close X, Size / Opacity in a pill top right; Home is glass cards; the ring shows the days with a violet-to-cyan arc, hours / minutes / date under it. Cards line up, nothing overlaps, text readable?
- **5.52 Ember & Iron** (`Ember & Iron.png`): 4 x 2 tiles, title card changes with the tab, "Window gauges" with working Size / Opacity sliders; Home: wide countdown plate, four work-order rows (click "Launch plan" opens the plan), Quick settings and Minimap below in two columns. Square close X.
- **5.53 Obsidian Night** (`Obsidian Night.png`): wider window, top bar and footer strip, cards on Home, big mono countdown (minutes teal), version line in the footer strip. Does every tab fit?
- **5.54 Azeroth Reforged** (`Azeroth Reforged.png`): ornate frame, crest on top (title centred on it, not crossing the sliders), nested gold-dashed Home panel, three big stone boxes. Are the colours solid enough now?
- **5.55 Scribe's Tome** (`scribes Tomb.png`): book look, contents list with dotted leaders and page numbers, bookmark flag on the open page, "BOOK I..III" headings; Home with three wax seals. Is all text readable (dark on parchment) on every tab?
- **5.56 Gnomish Workshop** (`gnomish workshop.png`): coloured tabs, the open tab cream, cards (blue / yellow / green / pink), digit boxes, sun with the tip. Is all text readable on every tab?
- **5.57 Light themes, readability:** open Plan, Talents, Gear, Macros and Tweaks in Scribe's Tome and Gnomish Workshop: any white or gold text that is hard to read on the light page? Tell me which tab and where.

## Cannot be tested yet (needs higher level / talents / release)
4.13 group picks (needs an owner publish) · 13.9 Druid Starsurge / Sunfire / Starfall / Lacerate macros · 13.11 Dire Bear Form at 40 · 14.1 Hunter Strider Kick · 14.2 Paladin Twist of Light seal swap · 14.4 Shaman Elemental Mastery
