# WoW Forever Macros

Macro cheatsheet for World of Warcraft: Forever (Classic+ on the Classic client, vanilla spell names, level cap 60).
Live site: GitHub Pages from `main` / root → https://nobody174.github.io/wow-forever-macros/

Small multi-page site: `index.html` is the countdown/landing page ("Venom & Trollmann's
Road to Forever"), `macros.html` is the macro cheatsheet, `builds.html` lists talent
builds per class, `addons.html` lists addons, `launch-plan.html` is the launch-week
leveling plan. All five share a top bar (site title, Macros / Builds / Addons /
Launch Plan / Talent Calc links, current page highlighted).

Class roster order on both `macros.html` and `builds.html` follows armor type,
Cloth → Leather → Mail → Plate: Priest, Warlock, Mage, Rogue, Shaman, Hunter,
Paladin, Warrior. Keep new classes inserted in this order on both pages.

## Files
- `data.py` — single source of truth for every macro. Edit macros HERE only.
- `template.html` — HTML/CSS/JS shell (shared top bar + macro cheatsheet UI);
  `__DATA__` is replaced with the macro JSON at build time, `__PAGE_MACROS__` /
  `__PAGE_BUILDS__` / `__PAGE_ADDONS__` / `__PAGE_LAUNCH__` are replaced with `aria-current="page"` markers.
  Each macro-type group (Damage/offensive, Wand, etc.) renders as a "tabbed picker":
  a row of pill buttons (one per macro in that group) plus a single code panel below
  that swaps when a pill is clicked, styled after warcrafttavern.com/forever's macro
  guide layout. Search results still use the old always-expanded list style
  (`groupHTML`/`details.section`), since search spans multiple classes/groups at once.
- `build.py` — generates `macros.html` and `wow-forever-macros.md` from `data.py` +
  `template.html`.
- `macros.html`, `wow-forever-macros.md` — generated output. Never hand-edit; run
  `python build.py`.
- `index.html` — hand-written landing page. Hero background (`assets/hero.webp`),
  title, countdown to the WoW Forever launch, and the visitor's local launch time via
  `Intl.DateTimeFormat`. Countdown target: `2026-11-04T23:00:00Z`. Left-side overlay
  (`.side-links`) has a featured Cozy Sleeping Bag card on top, then two side-by-side
  boxed columns (`.link-cols`): "General Resources" (Zockify, Wowhead, Icy Veins,
  Warcraft Tavern, Mobalytics, ForeverChanges) and "Tools" (talent calculators,
  Legacy Calculator, Best-in-Slot Gear, Dungeon Loot Tables, Hunter Pet Database).
  Each link is its own compact icon+title card (`.mini-plaque`/`.mini-icon`), title
  only — no per-link description. New tool/resource links go in whichever column
  fits; keep favicons via `google.com/s2/favicons?domain=...` and verify with curl
  before adding. Hand-edit directly.
- `builds.html` — hand-written, JS-rendered page. A class-icon roster (same pattern
  as `macros.html`) picks one class at a time; classes with more than one build
  (Mage: Arcane/Frost Ice Lance/Frost Piercing Ice/Fire; Paladin: Retribution/
  Protection; Warrior: Tank/Fury) get a second spec-picker row. All build+talent+
  rotation content lives in the `DATA` object in the page's script — edit builds
  there, not as hand-written HTML. Each build has a talent row (icons + hover
  tooltips, arrows between picks) and a Rotation section (single-target/AoE ability
  lists, same icon+arrow style, a repeat icon on loop-based rotations, plus a
  confidence badge: "high" = matches a build-specific level-20 guide, "medium" =
  reasoned from mechanics/ability-level-gating with no exact build-matched source
  found — flagged for the user to double-check in beta). See `builds_page_pattern`
  project memory for the full pattern and icon-verification rules. Hand-edit
  directly.
- `addons.html` — hand-written page listing the addons Venom & Trollmann actually run
  (Forever Bag Mover, ForeverLayers, ForeverPlus, Leatrix Maps, Leatrix Plus,
  ThreatMaster, TomTom, WeakAuras Forever — all CurseForge links, sorted
  alphabetically) plus a link to wow4ever.quest's addon compatibility tracker.
  Each card is a single framed nav-style button (`.addon-btn`) with the addon
  name linking to CurseForge, description below — not a separate name+link pair.
  Hand-edit directly.
- `launch-plan.html` — hand-written launch plan for the Alliance Skyborne duo
  (+ possible druid) with a Dual Mage / Dual Hunter / Compare switch. Checklists
  (before-launch / launch-night / 12→20 / 20→30 / 30→60 / test-in-beta) and the
  duo-play cards are rendered by JS from the `PHASES` and `DUO` objects at the
  bottom of the file — edit steps there, not in the HTML. An item is shared by both
  plans unless it has a `mage`/`hunter` key (object = override fields for that
  class, `false` = hidden for that class); Compare renders shared items full-width
  and class-specific ones side by side. The "Key differences" table and rules/
  dungeon sections are static HTML. Mode comes from `?plan=mage|hunter|compare`,
  then localStorage `wf-launch-plan-mode`. Checkboxes persist per browser in
  localStorage (key `wf-launch-plan-v1`, keyed by item id — keep ids stable; shared
  steps share one checkbox across both plans). Steps past level 30 are tagged `unverified` until beta/launch
  confirms them. Launch time uses the same `2026-11-04T23:00:00Z` target as index.html.
  Hand-edit directly.
- `assets/hero.webp` — landing page hero background (dwarf/gnome group in front of
  Frostforge Pass gate, nameplates "Venom" and "Trollmann" over the two dwarves).
  Generated via local ComfyUI (SDXL base + inpainting), finalized with Pillow
  (crop/resize to 2560×1080, nameplate overlay in Cinzel, exported as WebP < 500KB).
- `assets/sleepingbag.webp` — small icon (256×256) for the Cozy Sleeping Bag overlay
  plaque on `index.html`. Generated via local ComfyUI (SDXL base txt2img), finalized
  with Pillow (resize, exported as WebP).
- `assets/universal-icon.webp` — roster icon for the "Universal" tab on `macros.html`
  (dwarf+bear emblem, self-hosted from wow4ever.quest's own logo, converted to WebP).
  Class roster icons (Priest/Shaman/Paladin/Warlock/Hunter/Warrior/Rogue/Mage) are
  NOT local assets — they're hotlinked from Wowhead's icon CDN (`wow.zamimg.com`)
  directly in `template.html`'s `CLASS_ICONS` map.
- `assets/drafts/` — gitignored scratch folder for image-generation drafts/
  intermediates (hero and icon art both land here). Not part of the deployed site.

## Workflow
1. Macro changes: edit `data.py` (or `template.html` for cheatsheet layout/top bar
   changes), then run `python build.py`.
   The top bar CSS (3-column grid: title left / nav centered / optional right-side
   item like index.html's mute button) must stay identical across all 5 pages —
   `index.html`, `builds.html`, `addons.html`, `launch-plan.html` are hand-written and
   each carry their own copy, while `macros.html` gets its copy from `template.html`.
   A hand-edit to one page's topbar CSS needs to be repeated in the other 4, or they
   drift out of sync (this happened once already — see CHANGELOG 2026-09-27).
2. Landing/builds page changes: hand-edit `index.html` / `builds.html` directly.
3. Check every macro is <= 255 characters.
4. Test locally with `python -m http.server` before pushing.
5. Commit with a clear message and push to `main` (Pages redeploys in ~1 minute).
6. The moment something ships, move it out of `BACKLOG.md`/`ROADMAP.md` and into
   `CHANGELOG.md` — see [ROADMAP.md](ROADMAP.md) and [BACKLOG.md](BACKLOG.md)
   (Shape B: BACKLOG is the active todo list, ROADMAP is the someday bucket).

## Macro style rules (strict)
- Short, one-liners whenever possible. No bloated conditions.
- DPS, Priest only (needs target-of-target): `/cast [@targettarget, harm, exists][harm] SPELL`
- DPS, every other class (Shaman/Paladin/Warlock/Hunter/Warrior/Rogue — no TT needed):
  `/cast [harm] SPELL`
- Heal/utility (friendly only): `/cast [@mouseover, help, exists][help] SPELL`
- Friend-or-foe spells (e.g. Dispel Magic): `/cast [@mouseover, exists][exists] SPELL`
- Buffs: `/cast [@mouseover, help, exists][help][@player] SPELL`
- Spam-safe channels (Warlock): `/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] SPELL`
  — chan() keeps TT; only the dps() helper was split by class, chan()/stance() were not.
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
Each class has a "Shared" section (all specs) plus spec sections. Macro types:
Damage / offensive, Mouseover healing / utility, Cleanse / dispel, Wand / auto-attack,
Buffs, Panic / defensive, Targeting helpers, Class QoL, Focus, Misc / UI.
Misc / UI lives only in the UNIVERSAL block (camera/UI console commands, target
marking, gear-swap macros — not spell-specific, so not part of any class section).
Classes: Priest, Shaman, Paladin, Warlock, Hunter, Warrior, Rogue, Mage.
Use helpers: dps() (Priest only — target-of-target-aware), dpsHarm() (every other
class — plain [harm] targeting, no TT), heal(), util(), buff(), chan(), foc(),
plain(), me(), stance(). Every helper prepends #showtooltip; hand-written
multi-line /cast or /castsequence macros must add #showtooltip as their own
first line. Pure utility commands (/console, /tm, /target, /focus, /petattack,
/use item) do not get #showtooltip.
