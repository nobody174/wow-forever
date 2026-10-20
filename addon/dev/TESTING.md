# Road to Forever: open tests

Reply with the number: `5.25 done`, `5.38 needs more testing`, `5.41 not working: <what you saw>`. Numbers never change (gaps are fine).
**Only open tasks live here.** A confirmed test moves to `COMPLETED_TESTING.md`.
Checked against release 0.76.4 on 2026-10-20.

**Setup:** newest release zip in AddOns, `/console scriptErrors 1`. Taint check: `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`.

## To test (0.76.4: every theme was rebuilt blind, so expect rough edges and tell me where)
For every look (Home > Theme > "Open the gallery"): compare with its picture in Downloads, then open each tab (Plan, Talents, Gear, Macros, Tweaks).

- **5.32 Recorder, teammates only:** your own numbers are in (35 creatures, 15 vendors, 39 quests) and your file is in the beta backup, so nothing more from you. Teammates: `/r2f record`, then send `WTF/Account/<account>/SavedVariables/RoadToForever.lua` to the owner before the beta ends (the 21st).
- **5.43 Setup Hunter, the reload button (0.76.4):** run Setup Hunter; when it asks, press "Reload now (then Enter)". The chat line should open with `/reload`; press Enter and the game reloads. (Calling the reload from our own button after the setup was blocked by the game.)
- **5.61 Round 4 (0.76.4):** Launch plan in Ember, Gnomish and Scribe: the Waypoint button no longer overlaps the place text; the "Quest shopping list" button shows its whole label (also open the list itself). Ember: the logo and the X are clear of the corner rivets. The "Choose a look" gallery closes when you close the main window.

## Cannot be tested yet (needs higher level / talents / release)
4.13 group picks (needs an owner publish) · 13.9 Druid Starsurge / Sunfire / Starfall / Lacerate macros · 13.11 Dire Bear Form at 40 · 14.1 Hunter Strider Kick · 14.2 Paladin Twist of Light seal swap · 14.4 Shaman Elemental Mastery
