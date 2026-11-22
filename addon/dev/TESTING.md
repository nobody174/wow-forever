# Road to Forever: open tests

Reply with the number: `5.25 done`, `5.38 needs more testing`, `5.41 not working: <what you saw>`. Numbers never change (gaps are fine). A checklist page with boxes and comment fields is built from this file: `python tools/testing_html.py`, then open `addon/dev/TESTING.html`.
**Only open tasks live here.** A confirmed test moves to `COMPLETED_TESTING.md`.
Checked against release 0.84.2 on 2026-11-09 (labels updated). Round of 2026-11-22 processed.

**Setup:** newest release zip in AddOns, `/console scriptErrors 1`. Taint check: `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`.

## To test
The looks (Home > Theme > "Open the gallery") were checked by the owner on 2026-11-09: "the themes look good". Only report a look that breaks on a tab you open.

- **5.103 Gear tab on each look (unreleased, pilot of the theme redesign, 2026-11-22):** open Gear (Mr.BiZ) and go through the looks in the gallery (Home > Theme). Frost & Void, Obsidian Night, Gnomish Workshop and Azeroth Reforged now draw a card behind the paper doll + filters and another behind the slot list on the right; Classic, Ember & Iron and Scribe's Tome stay as they were. Check for each look: do the cards sit behind the doll and the list (nothing sticks out of the window, no slot or text half outside a card), is the text readable on them, and do the Wishlist / Next upgrades / Set views still look fine. Send a screenshot of any look that is off, with its name.

## Cannot be tested yet (needs higher level / talents / release)
4.13 group picks (needs an owner publish) · 13.9 Druid Starsurge / Sunfire / Starfall / Lacerate macros · 13.11 Dire Bear Form at 40 · 14.1 Hunter Strider Kick · 14.2 Paladin Twist of Light seal swap · 14.4 Shaman Elemental Mastery
