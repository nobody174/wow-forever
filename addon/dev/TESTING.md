# Road to Forever: open tests

Reply with the number: `5.25 done`, `5.38 needs more testing`, `5.41 not working: <what you saw>`. Numbers never change (gaps are fine).
**Only open tasks live here.** A confirmed test moves to `COMPLETED_TESTING.md`.
Checked against release 0.77.1 on 2026-10-20.

**Setup:** newest release zip in AddOns, `/console scriptErrors 1`. Taint check: `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`.

## To test (0.77.1: every theme was rebuilt blind, so expect rough edges and tell me where)
For every look (Home > Theme > "Open the gallery"): compare with its picture in Downloads, then open each tab (Plan, Talents, Gear, Macros, Tweaks).

- **5.32 Recorder, teammates only:** your own numbers are in (35 creatures, 15 vendors, 39 quests) and your file is in the beta backup, so nothing more from you. Teammates: `/r2f record`, then send `WTF/Account/<account>/SavedVariables/RoadToForever.lua` to the owner before the beta ends (the 21st).

- **5.62 Setup Druid (0.77.1):** on a Druid with the layout "Warrior/Druid" saved: minimap menu > "Setup Druid" > "Set up", then Reload now (Enter). Check: main bar 2 atk (your General macro), 8 Healing Touch, 9 Regrowth, 10 Rejuvenation, 11 Moonfire, 12 Wrath; bar 2: 7 Walk on Air, 10 Read Ley Line; bar 3: 4 Teleport: Moonglade; bar 4: 5 Cat/Bear form; bar 5: 3 Thorns, 4 Mark of the Wild; bar 6: 1 Sit, 2 Mark1, 3 Mark2, 12 Hearthstone. Then press the keys: Q, E, F, CapsLock, mouse wheel and Ctrl-1 to 5 should now fire the Druid's buttons, and Options > Key Bindings shows "Character Specific Key Bindings" ticked. The chat lists anything not found: tell me the exact in-game name of the Attack macro and of the Ley Line spell if they were missed. "Undo last setup" empties them again.
- **5.63 Setup Hunter, the new buttons (0.77.1):** same racials (bar 2 buttons 7 and 10), Hearthstone (bar 6 button 12) and Sit / Mark1 / Mark2 (bar 6 buttons 1 to 3) on a Hunter.

## Cannot be tested yet (needs higher level / talents / release)
4.13 group picks (needs an owner publish) · 13.9 Druid Starsurge / Sunfire / Starfall / Lacerate macros · 13.11 Dire Bear Form at 40 · 14.1 Hunter Strider Kick · 14.2 Paladin Twist of Light seal swap · 14.4 Shaman Elemental Mastery
