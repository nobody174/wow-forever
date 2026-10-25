# Site pages: landing, news, builds, launch plan, talents

Per-page notes for the hand-written pages. Moved out of CLAUDE.md 2026-10-16.

- `index.html` — hand-written landing page. Rotating hero backgrounds (`assets/hero-1..4.webp`),
  title, countdown to the WoW Forever launch, and the visitor's local launch time via
  `Intl.DateTimeFormat`. Countdown target: `2026-11-04T23:00:00Z`. Left-side overlay
  (`.side-links`) has a `.plaque-row` on top with two featured cards side by side
  (Cozy Sleeping Bag, external; Library Books, links to `library-books.html`), then two side-by-side
  boxed columns (`.link-cols`): "General Resources" (Zockify, Wowhead, Icy Veins,
  Warcraft Tavern, Mobalytics, ForeverChanges) and "Tools" (BiS Enchants = our own `professions.html#bis`, Mr.BiZ BiS Gear = our own `bis.html` (replaced the external ForeverChanges link 2026-10-13), Dungeon Loot Tables, Hunter Pet Database, DPS Tier List (Lvl 60) = MythicSim).
  The Tools column is `.link-group.tools` (`flex:1.3`, wider than General
  Resources) so every title fits on one line; keep titles short enough for that.
  No external talent or Legacy calculators here — our own `talents.html` (top bar) replaces them.
  Each link is its own compact icon+title card (`.mini-plaque`/`.mini-icon`), title
  only — no per-link description. New tool/resource links go in whichever column
  fits; keep favicons via `google.com/s2/favicons?domain=...` and verify with curl
  before adding. Hand-edit directly.

- `news.html` + `news.json` + `footer.js` — **What's new** page (latest changes, Coming
  next, Discord ideas button) rendered from `news.json` (`{discord, news: [{date, title,
  text, link}], next: [{title, text}]}`, newest news first). `footer.js` (loaded with
  `defer` on every page, incl. template.html) injects the shared footer: What's new (red dot
  when `news[0].date` differs from localStorage `wf-news-seen`, which news.html sets),
  Coming next, and "Send an idea" = the Discord invite to the #r2f-feedback forum
  (`https://discord.gg/Yh2sTMZksq`). It lifts itself above fixed bottom trays (`.tray`,
  `.xtray`). When something visitor-facing ships, add a plain-words entry at the top of
  `news.json` (and keep `next` in step with BACKLOG) — that's what lights the dot.
- `prices.json` — site-wide AH prices for professions.html (written by the owner from the
  site; hand edits fine, keep valid JSON and copper integers).
- `library-books.html` — hand-written library-book checklist + Alliance route
  from Stormwind. Not in the top-bar nav (linked from the index plaque), but it
  carries the shared top bar CSS like every other page. Book data is the `BOOKS`
  object (id → name, zone, coords, where, tags) and the route is `TRIPS` (steps
  are either a book id or a travel line). Checkboxes persist in localStorage
  `wf-library-books-v1`, keyed by book id — keep ids stable. Hand-edit directly.
- `builds.html` — hand-written, JS-rendered page. Each build card's header has an
  "Enchants for <Class> →" link to `professions.html#bis/<class>`. A class-icon roster (same pattern
  as `macros.html`) picks one class at a time; classes with more than one build
  (Mage: Arcane/Frost Ice Lance/Frost Piercing Ice/Fire; Paladin: Retribution/
  Protection; Warrior: Tank/Fury) get a second spec-picker row. All build+talent+
  rotation content lives in the `DATA30` / `DATA60` objects in the page's script (level 20 builds removed 2026-10-12) — edit builds
  there, not as hand-written HTML. Each build has a talent row (icons + hover
  tooltips, arrows between picks) and a Rotation section (single-target/AoE ability
  lists, same icon+arrow style, a repeat icon on loop-based rotations, plus a
  confidence badge: "high" = matches a build-specific guide, "medium" =
  reasoned from mechanics/ability-level-gating with no exact build-matched source
  found — flagged for the user to double-check in beta). Pattern notes:
  Verify talent icons against Wowhead before adding. A build may also carry an optional `guide`
  (cheat-sheet card shown right after it, see `guideHTML()`; builds without an inline guide read `GUIDES[level][class][spec]`, icons by name via `iconFor()`, text chip when unknown; optional `pullLabel`): `{title, confidence, intro, modes: [{name, sub,
  stats[], statTip, pull[abilities], pullLoop, pullTip}], foot}`. Used by Druid Level 30 Feral (bear tank
  stat order + pack pull) at Level 30 and Level 60; a mode can add `extra: [{label, abilities, loop, tip}]` rows. Hand-edit directly.

- `launch-plan.html` — hand-written launch plan for the 28 Alliance race and class combinations (Human, Dwarf, Gnome,
  Night Elf, Skyborne), picked with two dropdowns (race, then class; the class list is rebuilt on every race change and
  falls back to the race's first class). A side button, "2 Hunters" (preset `hunter` = Skyborne Hunter plus the duo
  tactics card), sits next to them. Every class is treated as damage: no tank or healer text, dungeon steps say "needs
  a group". Data lives in the first `<script>` block: `CLASSES` / `CLASS_ORDER`, `RACES` / `RACE_ORDER` (label, start,
  valid classes, `draft` = start steps not written yet), `PRESETS`, `PHASES`, `TIPS`, `WAYPOINTS`. A step resolves in
  this order: its own fields, `race.<race>`, `cls.<CLASS>`, `preset.<id>`; an object replaces the fields it names,
  `false` hides the step for good; a key may list several names ("dwarf gnome"). `only: { race: [...], cls: [...] }`
  shows a step to those only (class steps carry a coloured class tag). Nothing is thrown away when a plan goes: the old
  group-plan text now lives in class steps (`only.cls`) and race overrides. Checklists (before-launch / launch-night /
  12→20 / 20→30 / 30→60 / test-in-beta) and the Tips cards are rendered by JS. The addon's `gen_plan_data.js` evaluates
  `CLASSES`, `RACES`, `PRESETS`, `PHASES` and `planId` / `parsePlan` / `allPlans` / `allowed` / `override` / `resolve`, so
  keep those as top-level two-space-indented `var`s and `function`s. Selection comes from `?race=gnome&class=mage` or
  `?plan=hunter`, then localStorage `wf-launch-plan-sel` (a plan id, `race:CLASS` or the preset), then Skyborne Hunter.
  Checkboxes persist per browser in localStorage (key `wf-launch-plan-v1`, keyed by item id — keep ids stable; steps
  shared by several races or classes share one checkbox, so progress survives switching). **Weapons:** each step with a
  level and a zone in its title gets the best quest-reward weapons for the class, strongest dps first (top two melee and
  top two ranged; Priest, Mage and Warlock show "check stats" unranked; "No quest weapon data past level 32" on later
  steps; dual wield is not modelled). Data: `launch-plan-weapons.json`, written by `bis/build_quest_weapons.py` (the same
  rows as the addon's `QuestWeaponData.lua` plus dps, Alliance and both-faction only, and the class weapon table
  `CLASS_USE`, the one copy of it). The page fetches it after the first paint. A start-zone step must name its zone in
  its title (for example "Coldridge Valley (Dun Morogh)") or it gets no weapon line. Subzone names inside Elwynn, Dun
  Morogh and Teldrassil are Classic knowledge: tag them `unv`. Legacy path cards are static HTML with `data-race`. A
  floating "Buyable quests" button (top-right, just under the sticky top bar) (and a TOC link, or `#buyable` in the URL)
  opens a right-hand sidebar listing quests whose objectives are tradeable AH/vendor items, switchable between "Along our
  route" (grouped p1/p2/p3/off) and "By zone". Its data is the `QUESTS` array in the second `<script>` block (quest level,
  items, route phase, status forever/classic/verify); its checkboxes use their own localStorage key
  `wf-launch-plan-buy-v1` (ids `bq-*`). Steps past level 30 are tagged `unverified` until beta/launch confirms them. Launch
  time uses the same `2026-11-04T23:00:00Z` target as index.html. Hand-edit directly (except the weapons JSON).
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
  Pages load `talentcalc.js`, `talentcalc.css`, `talentsaved.js` (and talents.html also
  `legacycalc.js`) with a `?v=` query
  string; bump it on both pages whenever any of them changes, or browsers
  can mix a cached old engine with a new sidebar (happened on 2026-10-01).
- `group-builds.json` — Group picks data (see `talentsaved.js`). Written by the site's
  owner login; hand edits are fine, keep it valid JSON.
- `legacycalc.js` — Legacy calculator engine (`window.LegacyCalc`: `load()`,
  `mountSync(el, data, {code, onChange})`, `hideTip()`), shown in the Legacy mode of
  `talents.html`. Like the talent calc, data is NOT in the repo: it loads Wowhead's
  public script `https://nether.wowhead.com/forever/data/legacy-calculator`, which calls
  `WH.setPageData("wow.legacyCalculator.classicplus.calc", {build, cap, trees})`, so new
  perks appear when Wowhead adds them. Tree: `{name, art, blurb, nodes, edges}`; node:
  `{id, x, y, name, icon, maxRanks, locked, requiredSpent, castMs, cdMs, ranks[text]}`;
  x/y are canvas coords, turned into a grid from their distinct values. Rules, checked
  click-for-click against Wowhead's calculator on 2026-10-06: `cap` (16) points total;
  a perk with requiredSpent R needs R points in that tree's perks whose requiredSpent
  is lower than R (gates act like tiers); edge from→to = "to" needs 1 rank in "from";
  a removal is blocked if it breaks any taken perk; `locked` perks ("Unknown", not in
  game) can't be taken and render dashed. Link: `talents.html#legacy/<t1>-<t2>-<t3>`,
  one digit per perk in grid order (row, then column), locked perks included so codes
  don't shift when they're filled in; invalid codes reset to empty. Tree art and icons
  hotlinked from `wow.zamimg.com`. Styles are the `lc-` block at the end of
  `talentcalc.css` (it reuses `.tc-bar`, `.tc-tree`, `.tc-tip`). Test locally by
  routing the Wowhead URL to a `WH.setPageData(...)` fixture (cloud can't reach it).
- `talents.html` — hand-written talent + Legacy calculator page. A Talents / Legacy
  switch (`.lc-mode`) under the title swaps between the class roster + talent calc and
  the Legacy calc; `#legacy...` hashes open Legacy mode, every other hash is a talent
  link. Legacy data only loads the first time Legacy mode opens. The Saved builds
  button is hidden in Legacy mode (`body.lc-on`). Talent part: roster + full-mode mount + saved-builds sidebar. Talent data is NOT
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
