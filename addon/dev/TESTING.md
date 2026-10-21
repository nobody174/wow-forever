# Road to Forever: open tests

Reply with the number: `5.25 done`, `5.38 needs more testing`, `5.41 not working: <what you saw>`. Numbers never change (gaps are fine).
**Only open tasks live here.** A confirmed test moves to `COMPLETED_TESTING.md`.
Checked against release 0.79.2 on 2026-10-20.

**Setup:** newest release zip in AddOns, `/console scriptErrors 1`. Taint check: `/console taintLog 1`, play, `/reload`, search `Logs\taint.log` for `RoadToForever`.

## To test (0.79.1: every theme was rebuilt blind, so expect rough edges and tell me where)
For every look (Home > Theme > "Open the gallery"): compare with its picture in Downloads, then open each tab (Plan, Talents, Gear, Macros, Tweaks).

- **5.32 Recorder, teammates only:** your own numbers are in (35 creatures, 15 vendors, 39 quests) and your file is in the beta backup, so nothing more from you. Teammates: `/r2f record`, then send `WTF/Account/<account>/SavedVariables/RoadToForever.lua` to the owner before the beta ends (the 21st).

- **5.64 Setup is hidden where it does not apply (0.79.1):** on your Hunter and Druid the minimap menu still offers the setup and `/r2f help` lists it. (Rename the layout temporarily if you want to see it vanish; no need.)

- **5.65 Route log, a fresh Hunter (0.79.1):** on the new character type `/r2f route start hunter-1`, then play the start slowly and carefully: talk to everyone, take and hand in quests in the order you want to learn, open the trainer and vendors. Add `/r2f route note <text>` whenever something matters (a quest that would not start, a level gate, a good spot). `/r2f route` shows the counts; `/r2f route stop` ends it (it also survives a logout). Then send me `WTF/Account/<account>/SavedVariables/RoadToForever.lua` (no character name is in it). Check: after the first quest accept and hand-in the counts grow, and nothing shows on screen or lags.

- **5.66 Action bar overlays (0.79.1):** Tweaks > Action bars. Tick "Red when out of range": target an enemy and walk away from it, the icon of a ranged spell turns red when too far. Tick "Red when you lack mana, rage or energy": an ability you cannot afford turns red. Tick "Cooldown numbers": cast a spell with a cooldown, a number counts down on its button (and "Bigger" makes it larger). Check it on the main bar, Action Bars 2 to 6 and in Cat / Bear Form (the bar changes). In combat the numbers must keep counting (0.79.1 uses the game's own numbers). Anything wrong (no veil, no numbers, doubled numbers, wrong place, lag)? Run `/r2f debug bars` and tell me what it prints.

- **5.67 Paladin seal timer (0.79.2):** cast Seal of Righteousness (and swap to another seal) out of combat and in a fight. The countdown on the seal icon must start at 30 seconds every time, never 1800. If it still shows 1800, run `/r2f debug timers` and send what it prints.

## Cannot be tested yet (needs higher level / talents / release)
4.13 group picks (needs an owner publish) · 13.9 Druid Starsurge / Sunfire / Starfall / Lacerate macros · 13.11 Dire Bear Form at 40 · 14.1 Hunter Strider Kick · 14.2 Paladin Twist of Light seal swap · 14.4 Shaman Elemental Mastery
