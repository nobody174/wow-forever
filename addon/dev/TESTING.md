# Road to Forever: open tests

Reply with the number: `5.25 done`, `5.38 needs more testing`, `5.41 not working: <what you saw>`. Numbers never change (gaps are fine). A checklist page with boxes and comment fields is built from this file: `python tools/testing_html.py`, then open `addon/dev/TESTING.html`.
**Only open tasks live here.** A confirmed test moves to `COMPLETED_TESTING.md`.
Checked against release 0.84.2 on 2026-11-09 (labels updated). Round of 2026-11-17 processed.

**Setup:** newest release zip in AddOns, `/console scriptErrors 1`. Taint check: `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`.

## To test
The looks (Home > Theme > "Open the gallery") were checked by the owner on 2026-11-09: "the themes look good". Only report a look that breaks on a tab you open.

- **5.69 Swing timer (0.80.1):** on a character where Options > Advanced Options > Enable Swing Timer is OFF, run Setup Hunter / Setup Druid (or Apply my general settings): the swing timer must be ticked afterwards. If not, type `/r2f general swing` and send me what it prints. **Owner result 2026-11-17: the client cannot list its settings, so nothing was found. 2026-11-18: now probes likely names; `/r2f general swing` prints `showSwingTimer = 0` (found). Still to confirm: with it OFF, run Apply my general settings / Setup, `/reload`, then `/r2f general swing` must print `showSwingTimer = 1` and the option must show ticked.**

- **5.82 Talent dump (0.87.1):** on each class you have (one character per class over time), a few seconds after login and out of combat, type `/r2f debug talentdump`. Chat must print `talent dump saved for <CLASS>: N nodes ...` and one `fields:` line each for node, entry, definition, condition and currency (paste those lines). Then `/reload` and send `WTF\Account\<name>\SavedVariables\RoadToForever.lua` (the `talentDump` key). Nothing in the talent window or your points may change. In combat it must say it refuses. **Hunter dump received 2026-11-16 (saved in the SavedVariables); still wanted: one more class when you have a character of it (Priest, Warlock, Mage, Rogue, Druid, Shaman, Paladin, Warrior).** **2026-11-17: a dump was saved again (bundleVersion d881c72dab81, Hunter, configID 695306, 9 edges); still wanted: one other class.** **2026-11-18: a Shaman dump was saved (50 nodes, 7 edges, 43 conditions); still wanted: `/reload` and send the SavedVariables file (talentDump key) so I can read it.**

## Cannot be tested yet (needs higher level / talents / release)
4.13 group picks (needs an owner publish) · 13.9 Druid Starsurge / Sunfire / Starfall / Lacerate macros · 13.11 Dire Bear Form at 40 · 14.1 Hunter Strider Kick · 14.2 Paladin Twist of Light seal swap · 14.4 Shaman Elemental Mastery
