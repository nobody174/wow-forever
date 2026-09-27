# Changelog

Authoritative history of what's actually shipped on wow-forever-macro. Working
history for whoever builds this next (including a future Claude session) — not
user-facing release notes.

## 2026-09-27

- Added `launch-plan.html`: the launch-week plan for the Alliance Skyborne mage duo
  (Zephras → Dalaran → Ironforge/Hall of Thanes → Darkshore → Ashenvale → Wetlands →
  Hillsbrad → Dalaran dungeon, then an unverified 30→60 outline), with checklists that
  save per browser, a table of all 9 new dungeons, duo/camping/Legacy tips and a
  beta-verification list. Added a Launch Plan link to the top bar on every page
  (`__PAGE_LAUNCH__` placeholder in template.html, rebuilt macros.html).
- Fixed 5 rank-badge errors across the builds.html talent cards, found after the
  user caught a wrong rank on Mage's Elemental Precision: Mage Elemental Precision
  3/3→5/5 (also reordered so Frostbite comes before Ice Shards, matching the
  actual level-up order); Priest Spirit Tap 1/1→5/5 and Twin Disciplines 2/2→2/5;
  Warlock Pandemic 1/1→1/3; Warrior Deflection 2/2→2/5. Cross-checked every
  talent's true max rank against foreverchanges.pro's WoW Forever talent
  calculator — everything else in every card was already correct.

## 2026-09-26 (later)

- Added the Rogue level-20 talent build card to builds.html (Improved Sinister
  Strike 2/2 → Improved Eviscerate 3/3 → Precision 3/3 → Malice 3/5), closing the
  last remaining gap in the armor-order build lineup (Priest, Warlock, Mage,
  Rogue, Shaman, Hunter, Paladin, Warrior — all 8 classes now have a build).
  Verified talent existence/ranks/icons against foreverchanges.pro's WoW Forever
  talent calculator.

## 2026-09-26

- Repointed the Cozy Sleeping Bag plaque on the landing page to
  foreverchanges.pro/cozy-sleeping-bag (covers both the buff explanation and the
  full quest-chain steps in one place). Simplified the plaque to the standard
  single-link pattern, dropping the old Wowhead title/description + separate
  "Quest chain route" sub-link structure and its now-unused CSS.
- Added community-recommended macros after a research pass across Reddit/Wowhead/
  Icy Veins/Warcraft Tavern: Mage Counterspell and Frost Nova now `/stopcasting`
  first so the interrupt/root fires instantly instead of queuing behind your
  current cast (same fix applied to the Counterspell focus variant); Rogue Kick
  gets the same `/stopcasting` treatment, and Rogue gained a missing Cheap Shot
  stealth-opener entry; Shaman gained a Windfury Weapon + Lightning Shield
  `castsequence` refresh macro; Warrior gained a Charge + Rend opener and a
  Battle/Defensive/Berserker stance-dance macro.
- Ran a full shortening audit across every class's macros — found nothing further
  to trim; the helper-function pattern already keeps every macro at its minimum
  legal form.
- Redesigned the macro cheatsheet's group display: each macro-type group (Damage/
  offensive, Wand, etc.) now shows a row of pill buttons (one per macro) plus a
  single code panel below that swaps when a pill is clicked, instead of listing
  every macro's own card. Modeled after warcrafttavern.com/forever's Hunter macro
  guide. Applies to every class and Universal; search results still use the old
  always-expanded list since search spans multiple groups/classes at once.
- Hunter: added an experimental "Raptor Strike + Mongoose Bite + Wing Clip" test
  macro (separate from the existing Raptor Strike + Wing Clip combo) to check
  whether WoW Forever's client fires more than one ability per GCD when chained.
- Hunter: combined Raptor Strike and Wing Clip into one macro (casts Wing Clip
  right after Raptor Strike).

## 2026-09-25

- Added a ForeverChanges (foreverchanges.pro) link plaque to the landing page's
  side-links overlay — reference site for talent/spell/item/dungeon changes vs.
  Classic.
- Added a full Mage class to the macro cheatsheet (Shared + Arcane/Fire/Frost), same
  class-icon treatment as the other classes, plus a Mage level-20 talent build card
  on the Builds page (Elemental Precision → Ice Shards → Frostbite → Ice Lance).
- Reordered the class roster on both the Macros page and the Builds page by armor
  type (Cloth → Leather → Mail → Plate): Priest, Warlock, Mage, Rogue, Shaman,
  Hunter, Paladin, Warrior. Rogue has no talent build yet, so it's skipped on the
  Builds page for now.
- Renamed the stale "TT-aware DPS" group label (left over from the dps()/dpsHarm()
  split below) to "Damage / offensive" everywhere it appears, since only Priest
  actually needs target-of-target awareness.
- Added talent build cards to the Builds page for Paladin (hybrid Prot/Ret), Priest,
  Shaman, Warlock, and both Warrior specs (Tank, Fury) — same icon+arrow+tooltip
  pattern established with the Hunter build.
- Added a full Rogue class to the macro cheatsheet (Shared + Assassination/Combat/
  Subtlety), same class-icon treatment as the other 6 classes.
- Split the dps() helper: Priest keeps target-of-target-aware DPS macros
  (`[@targettarget, harm, exists][harm] SPELL`); every other class (Shaman,
  Paladin, Warlock, Hunter, Warrior, Rogue) now uses plain `[harm] SPELL` via a
  new dpsHarm() helper, since only Priest actually needs TT awareness.

## 2026-09-24

- Added Leatrix Plus to the Addons page (modular UI quality-of-life addon).
- Added class icons (real in-game icons via Wowhead CDN) to the macros page roster,
  plus a self-hosted Universal-tab icon (wow4ever.quest's dwarf+bear emblem).
- Fixed Style Patterns cards forcing a horizontal scrollbar on longer macros — widened
  the card grid and wrapped long lines instead of scrolling.
- Added the real Addons page content: ForeverPlus, Platynator, Leatrix Maps, Forever
  Bag Mover (verified via the addon's local `.toc` after "ForeverBagMover" turned up
  no public trace — actual name is "Forever Bag Mover" by ColbyDolby), plus a link to
  wow4ever.quest's addon compatibility tracker.
- Added a third landing-page overlay plaque linking to wowtbc.gg's dungeon loot tables.
- Added two landing-page overlay link "plaques" (Zockify, Cozy Sleeping Bag with a
  ComfyUI-generated icon + quest-chain sub-link) and a new Addons top-bar page.
- Ran a Project Reviewer / Design Critic / Security Auditor pass: removed two stale
  pre-restructure files (`index.md`, `wow-forever-macros.html`) that were still live
  on the deployed site, removed dead `.tag` CSS, fixed `CLAUDE.md` doc drift, added a
  discoverability link to `wow-forever-macros.md`.
- Reformatted `data.py`/`build.py` for readability (one macro per line, section
  dividers, named functions) — verified byte-identical build output, no content change.
- Added `#showtooltip` to every spell-casting macro; added a Misc / UI group
  (camera zoom, guild/PvP title hiding, target marking, weapon swap).
- Made macro groups collapsible (`<details>`/`+`-`−` toggle); restyled the top-bar
  nav links as raised game-UI buttons.
- Ran the 10 WoW-specific AI roles applicable to a macro-only project (Macro Engineer,
  API Compliance Auditor, Debugger, Healing/Tank/PvP Macro specialists, QA Playtester,
  API Research Analyst, Technical Writer, Knowledge Base Architect) against the
  project. Most came back clean; the one fix applied: expanded "TT-aware" on first use
  in the macros page lede, since it's real jargon that was never explained anywhere.
  Confirmed via WoW Forever community usage that `/console` CVar macros (zoom, hide
  guild/PvP names) are real working patterns on this client, not stale Classic
  assumptions.

## 2026-09-24 (earlier) — Multi-page site build

- Turned the single-page cheatsheet into a multi-page site: `index.html` (landing/
  countdown), `macros.html` (generated cheatsheet), `builds.html` (placeholder).
- Built the landing page: ComfyUI-generated hero background (SDXL base + inpainting,
  6 heroes at Frostforge Pass gate, "Venom"/"Trollmann" nameplates in Cinzel),
  countdown to `2026-11-04T23:00:00Z`, local-timezone launch time.
- `build.py` now outputs `macros.html` instead of `index.html`.

## Earlier

- Initial macro cheatsheet: `data.py`/`build.py`/`template.html` generating a
  single-page site for Priest, Shaman, Paladin, Warlock, Hunter, Warrior — TT-aware
  DPS, mouseover healing, cleanse/dispel, wand/auto-attack, buffs, panic/defensive,
  targeting helpers, class QoL, and focus macros for every spec.
