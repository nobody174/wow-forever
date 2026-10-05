# WoW Forever Macros

Macro cheatsheet for World of Warcraft: Forever (Classic+ on the Classic client, vanilla spell names, level cap 60).
Live site: GitHub Pages from `main` / root → https://nobody174.github.io/wow-forever-macros/

Small multi-page site: `index.html` is the countdown/landing page ("Road to Forever"), `macros.html` is the macro cheatsheet, `builds.html` lists talent
builds per class, `addons.html` lists addons, `launch-plan.html` is the launch-week
leveling plan, `talents.html` is our own talent calculator. All six share a top bar
(site title, Macros / Builds / Addons / Launch Plan / Talent Calc links, current page
highlighted).

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
  Also holds the addon **export mode** ("Export macros" toggle, checkboxes,
  export tray, `R2F1:` import string, selection in localStorage `wf-export-v1`);
  spec and build decisions in `ADDON_PLAN.md` sections 4 and 7.
- `build.py` — generates `macros.html` and `wow-forever-macros.md` from `data.py` +
  `template.html`.
- `macros.html`, `wow-forever-macros.md` — generated output. Never hand-edit; run
  `python build.py`.
- `index.html` — hand-written landing page. Hero background (`assets/hero.webp`),
  title, countdown to the WoW Forever launch, and the visitor's local launch time via
  `Intl.DateTimeFormat`. Countdown target: `2026-11-04T23:00:00Z`. Left-side overlay
  (`.side-links`) has a `.plaque-row` on top with two featured cards side by side
  (Cozy Sleeping Bag, external; Library Books, links to `library-books.html`), then two side-by-side
  boxed columns (`.link-cols`): "General Resources" (Zockify, Wowhead, Icy Veins,
  Warcraft Tavern, Mobalytics, ForeverChanges) and "Tools" (talent calculators,
  Legacy Calculator, Best-in-Slot Gear, Dungeon Loot Tables, Hunter Pet Database).
  Each link is its own compact icon+title card (`.mini-plaque`/`.mini-icon`), title
  only — no per-link description. New tool/resource links go in whichever column
  fits; keep favicons via `google.com/s2/favicons?domain=...` and verify with curl
  before adding. Hand-edit directly.
- `library-books.html` — hand-written library-book checklist + Alliance route
  from Stormwind. Not in the top-bar nav (linked from the index plaque), but it
  carries the shared top bar CSS like every other page. Book data is the `BOOKS`
  object (id → name, zone, coords, where, tags) and the route is `TRIPS` (steps
  are either a book id or a travel line). Checkboxes persist in localStorage
  `wf-library-books-v1`, keyed by book id — keep ids stable. Hand-edit directly.
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
- `addons.html` — hand-written page. An "Our own addon" section on top (Road to
  Forever, `data-addon="roadtoforever"`, links to its GitHub release, not
  CurseForge), then "What we use": Archivist for Forever, AtlasLootClassic
  Continued, Forever Bag Mover, Forever Bestiary, ForeverLayers, ForeverPlus,
  Leatrix Maps, Leatrix Plus, Prat 3.0, Questie, ThreatMaster, TomTom, WeakAuras
  Forever — all CurseForge links, sorted alphabetically (case-insensitive) —
  plus a link to wow4ever.quest's addon compatibility tracker.
  Each card is a single framed nav-style button (`.addon-btn`) with the addon
  name linking to CurseForge, description below — not a separate name+link pair.
  The button links to the addon's **WoW Forever file page**
  (`/wow/addons/<slug>/files/<fileId>`), not the project page, and under it a
  `<div class="ver" data-addon="<slug>">` line shows `Forever version <b>X</b> ·
  <upload date>`. The lede's `#versions-checked` line holds the date of the last
  check. Hand-edit directly.
  **Downloads:** every addon card is a `.dl-card` with `data-slug` (and, for
  CurseForge addons, `data-project` = CurseForge's numeric project id), a
  "Select" checkbox and a gold **Download** button. A fixed tray at the bottom
  (Select all / Clear / Download selected) downloads the ticked ones one after
  another, 900 ms apart (selection in localStorage `wf-addons-selected-v1`).
  Download URLs are built in JS from each card's `.addon-btn` href, so the
  version check only needs to keep that href current: CurseForge →
  `https://www.curseforge.com/api/v1/mods/<data-project>/files/<fileId>/download`
  (the address CurseForge's own Download button uses, so authors keep their
  download counts — don't link the forgecdn file directly); Road to Forever →
  `.../releases/download/r2f-v<ver>/RoadToForever-<ver>.zip` from the tag link.
  A new CurseForge addon needs its project id in `data-project` (shown under
  "About Project" on its CurseForge page, or `"id"` in
  `https://www.curseforge.com/api/v1/mods/<id>/files/<fileId>` JSON).
  **Addon version check (run daily by a scheduled task, or on request):**
  1. For each `data-addon` slug, WebFetch
     `https://www.curseforge.com/wow/addons/<slug>/files/all` and take the newest
     file whose flavor is **Forever** (game version 1.60.x). Use the files list,
     not the project page's "Recent Files" sidebar — the sidebar lags behind
     (on 2026-10-05 it showed Leatrix Maps 1.60.11 while 1.60.12 was out).
     Multi-flavor files count only if Forever is in their flavor list (TomTom
     ships one file for every flavor; open the file page to confirm).
     Never pick a Retail/Classic/MoP/TBC/Titan file. Release type R preferred;
     only use a beta/alpha file if no R exists for Forever.
     Multi-flavor addons (AtlasLootClassic Continued, Prat 3.0, Questie, TomTom)
     show "Forever + N" in the list. CurseForge's list can come back stale or
     filtered to another flavor (on 2026-10-05 Prat's list first showed only
     August files without Forever); if no Forever file shows, read the project
     page's "Latest release ... Forever + N" line and confirm on that file's page
     that 1.60.x / Forever is in its supported versions before using it.
     Watch the slugs: Archivist is `archivist-for-forever` (the plain `archivist`
     is an old Retail addon), Forever Bestiary is `forever-bestiary-pet-hunter`,
     AtlasLoot is `atlasloot-continued`.
     `roadtoforever` is ours and not on CurseForge: its version is the newest
     `r2f-v*` tag (`git ls-remote --tags origin 'r2f-*' | sort -V`), cross-checked
     with `## Version` in `addon/RoadToForever/RoadToForever.toc`, its date is
     the tag's commit date, and the button links to
     `https://github.com/nobody174/wow-forever/releases/tag/r2f-v<version>`
     (the repo was renamed from `wow-forever-macros` to `wow-forever`; GitHub
     redirects the old name). Versions below 1.0.0 are GitHub pre-releases, so
     keep "· pre-release" on the line until 1.0.0; also update the zip name in
     the card's Install note.
  2. If newer: update that card's link file id, version and date.
  3. Always set `#versions-checked` to today's date (e.g. `Oct 6, 2026`).
  4. If a project page 404s, retry once, then check `/files/all` — WeakAuras
     Forever's project page 404'd on 2026-10-05 while its files list worked.
     If both fail, leave the card unchanged and mention it in the commit message.
     WebFetch can serve cached CurseForge pages: WeakAuras Forever was really
     gone on 2026-10-05 (404 in a real browser) while WebFetch still showed its
     files. Its card is now `.card.unavailable` (no Download/Select, "Removed
     from CurseForge"); skip it in the check until it's replaced.
  5. The shell can't reach CurseForge (proxy blocks it); use WebFetch only.
  6. Always commit and push to `main`, even when only the date changed: a
     date-only bump gets its own commit ("Addon versions checked <date>, no changes"), so the
     page shows the check is alive. Add version bumps to CHANGELOG.md.
- `launch-plan.html` — hand-written launch plan with three group plans plus Compare:
  2 Hunters · Warrior · Druid (`hwd`), 3 Hunters · Druid (`h3d`) — both Skyborne,
  Zephras Isle start — and Paladin · Hunter · Shaman (`trio`, Dwarves starting in
  Coldridge Valley, since Alliance Skyborne can't be Paladin or Shaman). Plans are
  defined in the `PLANS` object (label, chips, color class, and `base` = the key
  whose overrides it inherits; all three inherit the shared `hunter` profile, which
  is a data key only, not a selectable plan). Checklists
  (before-launch / launch-night / 12→20 / 20→30 / 30→60 / test-in-beta) and the
  group-play cards are rendered by JS from the `PHASES` and `DUO` objects at the
  bottom of the file — edit steps there, not in the HTML. An item is shared by every
  plan unless it has a key for that plan (or its base): object = override fields,
  `false` = hidden. `DUO` cards list their `plans` ("all" = every plan). Compare shows
  any two plans side by side (two selects; rows whose resolved text matches render
  full-width "Same for both"), and the "Key differences" table is rendered from the
  `DIFFS` array. Legacy path cards are static HTML with `data-plans`. Mode comes from
  `?plan=hwd|h3d|trio|compare` (+ `&a=&b=` for compare), then localStorage
  `wf-launch-plan-mode` / `wf-launch-plan-cmp`. Checkboxes persist per browser in
  localStorage (key `wf-launch-plan-v1`, keyed by item id — keep ids stable; shared
  steps share one checkbox across every plan). A floating "Buyable quests" button (top-right, just under the sticky top bar) (and a
  TOC link, or `#buyable` in the URL) opens a right-hand sidebar listing quests whose
  objectives are tradeable AH/vendor items, switchable between "Along our route"
  (grouped p1/p2/p3/off) and "By zone". Its data is the `QUESTS` array in the second
  `<script>` block (quest level, items, route phase, status forever/classic/verify);
  its checkboxes use their own localStorage key `wf-launch-plan-buy-v1` (ids `bq-*`).
  Steps past level 30 are tagged `unverified` until beta/launch
  confirms them. Launch time uses the same `2026-11-04T23:00:00Z` target as index.html.
  Hand-edit directly.
- `talentcalc.js` + `talentcalc.css` — shared calculator engine used by `talents.html`
  (full mode: all three trees) and `builds.html` (compact mode, one per build card:
  tree tabs, "Reset to build", "Copy link", "Open in Talent Calc"). API:
  `TalentCalc.load()`, `TalentCalc.mountSync(el, raw, {cls, code | preset, compact,
  onChange})`. Builds preload from their `talents` list (`preset: [[name, rank]]`,
  matched by talent name) — keep build talent names identical to Wowhead's Forever
  names or the preset is dropped. All CSS classes are `tc-` prefixed.
  Extra API: `inst.split()`, `inst.mainTree()`, `inst.total()`,
  `TalentCalc.presetCode(raw, cls, preset)`; `opts.saveName` = default name for the
  "Save build" button, which every calculator bar shows when `talentsaved.js` is loaded.
- `talentsaved.js` — "Saved builds" sidebar on `talents.html` and `builds.html` (load
  after `talentcalc.js`; styles are the `ts-` block at the end of `talentcalc.css`).
  Floating gold button under the top bar (bottom-right on narrow screens) opens a
  right-hand drawer, same look as launch-plan's Buyable quests. Two tabs:
  **My builds** (per browser, localStorage `wf-talent-builds-v1`: `{id, code, name,
  note, ts}`; save from any calculator's "Save build", update the build you last
  opened, import a pasted talents.html link, edit/delete, copy one or all links) and
  **Group picks**, read from `group-builds.json` in the repo root
  (`{picks: [{id, name, by, note, code, ts}]}`, code = `"<class>/<digits>"`).
  Only the owner changes Group picks, from the site: "Owner login" (bottom of the
  Group picks tab) takes a GitHub fine-grained token (this repo only, Contents read
  and write), checks it via `GET /user` + repo permissions, and stores it in
  sessionStorage, or localStorage with "Remember on this device" (key `wf-owner-gh`).
  Signed in, "Publish to group" on a saved build and Edit/Remove on picks read the
  latest file + sha and `PUT` it through the GitHub contents API (one retry on a sha
  conflict), so each change is a normal commit on `main` and Pages redeploys it for
  everyone in ~1 minute. Never put a token in the repo. The token sits in the same
  page as Wowhead's data script, which is why it must stay scoped to this one repo.
  Editing `group-builds.json` by hand still works. `#saved` in the URL opens the drawer.
  Pages load `talentcalc.js`, `talentcalc.css` and `talentsaved.js` with a `?v=` query
  string; bump it on both pages whenever any of the three changes, or browsers
  can mix a cached old engine with a new sidebar (happened on 2026-10-01).
- `group-builds.json` — Group picks data (see `talentsaved.js`). Written by the site's
  owner login; hand edits are fine, keep it valid JSON.
- `talents.html` — hand-written talent calculator page (roster + full-mode mount + saved-builds sidebar). Talent data is NOT
  stored in the repo: the page loads Wowhead's public Forever data script
  (`https://nether.wowhead.com/forever/data/talents-classic`) with a `<script>` tag and a
  tiny `WH.setPageData` shim, so it always shows Wowhead's latest beta trees. Data shape
  per tree id: `{ talentId: { id, row, col, icon, name, ranks[], descriptions{1..n},
  requires[{id,qty}], requiredPoints } }`. `CLASSES` maps each class to its 3 tree ids
  in in-game tab order (ids from Wowhead: e.g. Hunter 361 BM / 363 MM / 362 Survival).
  Rules: 51 points, 7×4 grid, `requiredPoints` per tier, prerequisites; removal is
  blocked if it breaks a dependent talent or a deeper tier. Share links are
  `talents.html#<class>/<tree1>-<tree2>-<tree3>`, one digit per talent in row/col order
  (invalid codes reset to empty). Icons hotlinked from `wow.zamimg.com`. Desktop:
  click +1, right-click −1, Shift = max, hover tooltip; touch: tap opens a bottom
  sheet with −/+/Close. Test locally by routing the Wowhead URL to a fixture in the
  same `WH.setPageData(...)` format (the cloud session can't reach Wowhead).
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
- `ADDON_PLAN.md` — plan for the "Road to Forever" in-game addon (macro import,
  talent import/export, minimap button; not built yet). Read it before touching
  anything addon-related, the `short`/`icon` macro fields, or the talent link format.
- `assets/drafts/` — gitignored scratch folder for image-generation drafts/
  intermediates (hero and icon art both land here). Not part of the deployed site.

## Workflow
1. Macro changes: edit `data.py` (or `template.html` for cheatsheet layout/top bar
   changes), then run `python build.py`.
   The top bar CSS (3-column grid: title left / nav centered / optional right-side
   item like index.html's mute button) must stay identical across all 6 pages —
   `index.html`, `builds.html`, `addons.html`, `launch-plan.html`, `talents.html` are
   hand-written and each carry their own copy, while `macros.html` gets its copy from
   `template.html`. A hand-edit to one page's topbar CSS needs to be repeated in the others, or they
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
Classes: Priest, Shaman, Paladin, Warlock, Hunter, Warrior, Rogue, Mage.
Use helpers: dps() (Priest only — target-of-target-aware), dpsHarm() (every other
class — plain [harm] targeting, no TT), heal(), util(), buff(), chan(), foc(),
plain(), me(), stance(), melee(). Every helper prepends #showtooltip; hand-written
multi-line /cast or /castsequence macros must add #showtooltip as their own
first line. Pure utility commands (/console, /targetmarker, /target, /focus,
/petattack, /use item) do not get #showtooltip.

## Slash command conflicts
Always use `/targetmarker`, never the `/tm` shorthand, for raid target-icon
macros — the ThreatMaster addon (see addons.html) claims `/tm` for itself,
which silently breaks any macro using the short form once that addon is
installed, with no error shown. Found and fixed 2026-09-29 after a real
in-game keybind investigation. If a future slash-command shorthand turns out
to collide with a popular addon, prefer the full command name here too.
