# Road to Forever: open tests

Reply with the number: `5.25 done`, `5.38 needs more testing`, `5.41 not working: <what you saw>`. Numbers never change (gaps are fine). A checklist page with boxes and comment fields is built from this file: `python tools/testing_html.py`, then open `addon/dev/TESTING.html`.
**Only open tasks live here.** A confirmed test moves to `COMPLETED_TESTING.md`.
Checked against release 0.84.2 on 2026-11-09 (labels updated). Round of 2026-11-21 processed.

**Setup:** newest release zip in AddOns, `/console scriptErrors 1`. Taint check: `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`.

## To test
The looks (Home > Theme > "Open the gallery") were checked by the owner on 2026-11-09: "the themes look good". Only report a look that breaks on a tab you open.

- **5.98 Login with the new shared helper (unreleased, 2026-11-21):** `/console scriptErrors 1`, then `/reload` and log in on two characters of different classes. No Lua error popup may appear, and the Gameplay, Buffs, Combat banner, Timers and Recorder tweaks must still work as before (just open Tweaks and tick one that shows something, for example the combat banner). If an error appears, send me its text.

- **5.102 Builds page on the site (site, no addon needed; changed 2026-11-21 after your note):** open https://nobody174.github.io/wow-forever/builds.html on Level 60 for Warrior (many variants) and for Priest (Discipline is new). Now each spec has ONE heading and its spec button once (Arms, Fury, Protection), with all its builds (PvE, PvP, Raid, Dungeon ...) listed under it and one cheat sheet at the end. Check that it reads clean, every build shows its tree and a Wowhead label, and Saved builds still works after a reload.

## Cannot be tested yet (needs higher level / talents / release)
4.13 group picks (needs an owner publish) · 13.9 Druid Starsurge / Sunfire / Starfall / Lacerate macros · 13.11 Dire Bear Form at 40 · 14.1 Hunter Strider Kick · 14.2 Paladin Twist of Light seal swap · 14.4 Shaman Elemental Mastery
