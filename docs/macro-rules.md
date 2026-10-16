# Macro rules and data.py structure

The project's macro decisions. Generic WoW macro syntax lives in the WoW library (02-macros). Moved out of CLAUDE.md 2026-10-16.

## Macro style rules (strict)
- Short, one-liners whenever possible. No bloated conditions.
- DPS, Priest only (needs target-of-target): `/cast [@targettarget, harm, exists][harm] SPELL`
- DPS, every other class (Shaman/Paladin/Warlock/Hunter/Warrior/Rogue — no TT needed):
  `/cast [harm] SPELL`
- Mouseover-harm with target fallback (interrupts/CC you want to land on
  whatever's under your mouse without changing your actual target — e.g.
  Hammer of Justice): `/cast [@mouseover, harm, exists][harm] SPELL`
  (helper: `dpsMO()`, added 2026-10-02). Applied per-macro on request, not a
  blanket replacement for `dpsHarm()` — ask before converting another one.
- Heal/utility, with self fallback: `/cast [@mouseover, help, exists][help][@player] SPELL`
  — added 2026-10-02: with no mouseover and no friendly target, this used to do
  nothing; now it heals you instead. (First real in-game play session caught this.)
- Friend-or-foe spells (e.g. Dispel Magic), with self fallback:
  `/cast [@mouseover, exists][exists][@player] SPELL`
  — same self-fallback added, accepted deliberately even though it means a
  spell that removes a FRIENDLY buff on self-cast (Dispel Magic, Remove Curse)
  could strip your own buff if you have no target. User's call: consistency
  with heal()/buff() beats the edge case.
- Buffs: `/cast [@mouseover, help, exists][help][@player] SPELL`
- Spam-safe channels (Warlock): `/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] SPELL`
  — chan() keeps TT; only the dps() helper was split by class, chan()/stance() were not.
- Warlock (owner's tested macros, 2026-10-13): mouseover enemy, then your own enemy target, then your friendly
  target's enemy target, never a corpse: `/cast [@mouseover, harm, nodead][harm, nodead][@targettarget, harm, nodead] SPELL`
  (constants `WL_MO`, `WL_TGT` in data.py). Used by Corruption, Bane of Agony (the Forever name; Curse of Agony in
  Classic) and Pet attack mouseover. Shadow Bolt uses `WL_TGT` (no mouseover). These replace the plain `[harm]` rule
  for these Warlock spells only; the pet attack has no #showtooltip, icon `Ability_GhoulFrenzy` (Blizzard's own
  pet-bar Attack icon, `PET_ATTACK_TEXTURE`).
- Focus: `/cast [@focus, harm, exists][harm] SPELL`
- Wand (must stay exactly two lines, never use !Shoot):
  ```
  /cast [@targettarget, harm, exists, nochanneling:Shoot] Shoot
  /cast [harm, nochanneling:Shoot] Shoot
  ```
- Melee: `/startattack [@targettarget, harm, exists][harm]`
- Hunter Auto Shot is the one exception that uses `!Auto Shot`.
- No ranks in spell names (highest rank casts automatically).
- All code and comments in English.

## Structure in data.py
Each class has a "Shared" section (all specs) plus spec sections. Exception:
Warrior and Paladin use role sections instead: "General" (all specs; rendered
like Shared), "Tank", "DPS" (Arms+Fury / Retribution), plus Paladin "Healer".
Melee strikes use the melee() helper (`/startattack [harm]` + `/cast [harm]`);
stance(..., attack=True) adds the same /startattack line. Never add /startattack
to fears or other breakable CC (Intimidating Shout, Repentance). Macro types:
Damage / offensive, Mouseover healing / utility, Cleanse / dispel, Wand / auto-attack,
Buffs, Panic / defensive, Targeting helpers, Class QoL, Focus, Misc / UI.
Misc / UI lives only in the UNIVERSAL block (camera/UI console commands, target
marking, gear-swap macros — not spell-specific, so not part of any class section).
Classes: Priest, Shaman, Paladin, Warlock, Hunter, Warrior, Rogue, Mage, Druid (added 2026-10-14).
Druid: spec sections Shared / Balance / Feral (Bear + Cat) / Restoration. Forever macros stop after the first GCD
action, so a form swap and its ability are ONE /cast with conditions: bear() / bear_self() use `[noform:1] Bear Form; ...`,
cat() / cat_self() use `[noform:3] Cat Form; ...` (3 = Cat's place on the form bar after Bear and Aquatic; 2 until Aquatic
Form is learned, level 16). Rune abilities (Starsurge, Lacerate, Skull Bash...) are marked "Test in beta" with the rune named.
Use helpers: dps() (Priest only — target-of-target-aware), dpsHarm() (every other
class — plain [harm] targeting, no TT), heal(), util(), buff(), chan(), foc(),
plain(), me(), stance(), melee(), bear(), bear_self(), cat(), cat_self(). Every helper prepends #showtooltip; hand-written
multi-line /cast or /castsequence macros must add #showtooltip as their own
first line. Pure utility commands (/console, /targetmarker, /target, /focus,
/petattack, /use item) do not get #showtooltip.
