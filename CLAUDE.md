# WoW Forever Macros

Macro cheatsheet for World of Warcraft: Forever (Classic+ on the Classic client, vanilla spell names, level cap 60).
Live site: GitHub Pages from `main` / root → https://nobody174.github.io/wow-forever-macros/

Small multi-page site: `index.html` is the countdown/landing page ("Road to Forever"), `macros.html` is the macro cheatsheet, `builds.html` lists talent
builds per class, `addons.html` lists addons, `launch-plan.html` is the launch-week
leveling plan, `talents.html` is our own talent calculator plus Legacy calculator
(Talents / Legacy switch), `professions.html` holds BiS enchants with stand-ins, our crafters
and profession costs. All seven share a top bar
(site title, Macros / Builds / Addons / Professions / Launch Plan / Talent / Legacy Calc
links, current page highlighted).

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
  `template.html`, then runs `addon/tools/gen_plan_data.js` (node) which writes the addon's
  `addon/RoadToForever/PlanData.lua` from `launch-plan.html` (PLANS, PHASES) and
  `launch-plan-waypoints.json` (waypoints for the in-game Plan tab, ADDON_PLAN 15.5). Never
  hand-edit `PlanData.lua`; after changing launch-plan.html's PLANS/PHASES or the waypoints JSON,
  run `python build.py` (the addon tests fail if it is stale).
- `macros.html`, `wow-forever-macros.md` — generated output. Never hand-edit; run
  `python build.py`.
- `index.html` — hand-written landing page. Rotating hero backgrounds (`assets/hero-1..4.webp`),
  title, countdown to the WoW Forever launch, and the visitor's local launch time via
  `Intl.DateTimeFormat`. Countdown target: `2026-11-04T23:00:00Z`. Left-side overlay
  (`.side-links`) has a `.plaque-row` on top with two featured cards side by side
  (Cozy Sleeping Bag, external; Library Books, links to `library-books.html`), then two side-by-side
  boxed columns (`.link-cols`): "General Resources" (Zockify, Wowhead, Icy Veins,
  Warcraft Tavern, Mobalytics, ForeverChanges) and "Tools" (BiS Enchants = our own `professions.html#bis`, Best-in-Slot Gear, Dungeon Loot Tables, Hunter Pet Database, DPS Tier List (Lvl 60) = MythicSim).
  The Tools column is `.link-group.tools` (`flex:1.3`, wider than General
  Resources) so every title fits on one line; keep titles short enough for that.
  No external talent or Legacy calculators here — our own `talents.html` (top bar) replaces them.
  Each link is its own compact icon+title card (`.mini-plaque`/`.mini-icon`), title
  only — no per-link description. New tool/resource links go in whichever column
  fits; keep favicons via `google.com/s2/favicons?domain=...` and verify with curl
  before adding. Hand-edit directly.
- `professions.html` — hand-written page with a four-way switch (`.pf-mode`): **BiS enchants**
  (default), **Our crafts**, **Enchanting costs**, **Leatherworking costs**. Hash links:
  `#bis`, `#bis/<class>` (class filter; builds.html links there), `#ours`, `#enchanting`,
  `#leatherworking`. Layout everywhere: groups Gear / Weapons / Shield, each split into
  pieces (`SECTIONS[].pieces`: Neck, Back, Chest, Wrist, Hands, Legs, Feet; One-hand,
  Two-hand, Ranged; Shield) with the piece as heading (rows inside drop their slot column;
  "Hands, Legs" armor kits show under both). BiS view has jump links to each piece
  (`#p-<id>`, offset by the measured top bar height `--topbar-h`). One compact row per item (`details.row`, `data-k` = recipe name, kept open across
  re-renders), click to expand. Ranking uses coin metals: gold medal = BiS, silver = 2nd
  best, copper = 3rd best, green "+" = stronger than the list's pick, "=" = same bonus but
  easier to get. Design: site tokens (navy/gold, Marcellus + Plex), sentence case, sources
  shown only inside expanded rows in muted text.
  - Data: `DATA` = every enchant ForeverChanges' level-30 BiS pages recommend (36 spec
    pages, 2026-10-06; fields name, prof, skill, slot, eff, mats, specs, src, how).
    `ALT` = stand-in recipes (Wowhead Forever data 2026-10-07: skill, eff, mats, src, how).
    `LADDER[bisName]` = `{alts: [2nd, 3rd], up: [stronger], same: [equal-bonus alts],
    none: "why there is no stand-in"}`. Only stand-ins reachable by about level 30 are
    listed (Shield Stamina +7 and Cloak Lesser Agility drop from level 38+ mobs; Bracer
    Agility, 2H Lesser Agility/Strength have no source in Forever yet — left out).
    Forever values differ from Classic (e.g. Bracer Minor/Lesser Stamina +3/+4, Chest Minor
    Stats listed as +2 all stats) — take values from Wowhead's Forever spell pages, never
    from Classic. `CRAFTERS` = `[{name, color, knows: [recipe names]}]`: who in the group
    makes what (Venom = the owner). Edit it when someone learns a recipe; "Our crafts"
    lists only known recipes that appear in some ladder (BiS or stand-in), so junk like
    Chest Lesser Absorption never shows. BiS rows show the best tier our crafters cover.
  - Costs: one `MATS` list (`[id, name, prof, price]`, copper, `null` = no price yet);
    recipes reference materials by full name. Cost views list BiS enchants only
    (Enchanting) and the armor kits (Leatherworking). A recipe with an unpriced material
    shows a muted "—" with the missing names in its title. The price editor is a collapsed
    `details.prices` ("N of M priced"); Soul Dust shows in both professions and stays in sync.
  - Live prices: on load the cost views fetch AHledger's free API
    (`https://api.ahledger.com/v1/tooltip/<market>?items=<ids>`, ≤100 ids, no key, CORS ok;
    `/v1/markets` fills the market picker, so EU markets appear by themselves when AHledger
    adds them). Price per material = visitor's typed price > for vendor items (`VENDOR_ITEM`, by item id,
    owner-checked vendor prices 2026-10-07) the cheaper of vendor and live AH > live min buyout (median if none or if fewer than `FEW_LISTED` = 10 are listed, since one odd cheap listing sells fast — seen with Greater Nether Essence 2026-10-07; quantity 0 = not on AH) >
    `prices.json`. `LIVE_OFF` lists materials whose AHledger price is known wrong (Sulfuric Acid: ~3s there vs 19s 90c each in game, owner-checked 2026-10-07); they always use the site price. Every `MATS` entry carries its WoW item id (5th field; Forever-only mats
    have 2494xx ids, checked against AHledger names 2026-10-07). Market in localStorage
    `wf-prof-market` (default `forever.normal.alliance.us`, `"site"` = owner prices only),
    last response cached in `wf-prof-live-v1`, refetched every 10 min. AHledger's terms
    REQUIRE the "Prices from AHledger" link wherever their prices show (`#ahl-credit` +
    the price editor hint) — never remove it. The shell can't reach AHledger; test with a
    Playwright route fixture, verify live in Chrome.
  - Craft or buy: `PRODUCT_ITEM` maps kits to their WoW item ids (Heavy 4265, Forceful
    252453, Mystic 252452, Thick 8173); the live fetch includes them and kit rows show
    craft cost vs AH price (`cobTag`/`cobLine`). Enchants can't be sold, so kits only.
  - Shopping list: `list` = `{recipeName: qty}` in localStorage `wf-prof-list-v1`;
    `addBtn(name)` in every open row, drawer `#list-drawer` (same look as launch-plan's
    Buyable quests), `#list` hash opens it.
  - Prices: site-wide prices in `prices.json` (`{updated, by, prices: {matId: copper|null}}`),
    fetched no-store; `MATS` prices are only the fallback. Visitors' own edits are per
    browser (localStorage `wf-prof-prices-v1`) with "Use site prices". The owner signs in
    at the bottom of the cost views with the SAME GitHub token/key as Group picks
    (`wf-owner-gh`) and presses **Save as site prices** (PUT `prices.json` via the contents
    API, one retry on a sha conflict). New material: add it to `MATS` (and prices.json).
    Class filter persists in localStorage `wf-prof-class`, sort toggle in `wf-prof-sorted`.
  - Sources were checked against Wowhead's Forever data in a real browser (the cloud can't
    reach Wowhead): Enchanting skill page `recipes` listview (`source` 6 = trainer,
    5 = vendor, 4 = quest, 2 = drop; `trainingcost` in copper; effects from each spell
    page's meta description), each spell's `taught-by-npc` (city Expert trainers vs only
    Kitta Firewind / Vanessa Sellers / Melanie Sable / Annora / Hgarth), and each formula
    item's `sold-by` / `dropped-by` / `reward-from-q` lists.
- **Crafters** (5th professions.html view, `#crafters`): characters imported from the
  addon's profession export (`R2FP1:` string, addon v0.12.0, ADDON_PLAN 14) and kept in
  `crafters.json` (`{updated, chars: [{name, realm, cls, faction, updated, profs: [{name,
  rank, max, recipes: [{n, k: "i"|"s", id, m: [[itemId|"name", count]]}]}]}]}`). Anyone can
  paste a string and see the preview; only the owner (same `wf-owner-gh` login) saves it
  (PUT crafters.json, replaces the same name+realm, one sha retry). Imported characters
  merge into `CRAFTERS` by name (`mergeCrafters`), so BiS / Our crafts / costs use them;
  the hand-typed `CRAFTERS` list stays as the base until real exports replace it.
  Material prices by item id: MATS rules first, else live AHledger (crafter mat ids are
  added to the live fetch, batched 100 per call; names come from AHledger too).
  "Who can make…?" search filters recipes and material names across everyone.
  Characters are grouped by player: `owner` field (set in the import preview, "Show under
  player", defaults to the character name) or else the name. One card per player
  (`groupCrafters`): professions merged, recipe list = union, each recipe tagged with the
  classes that know it, profession chip shows the best skill (title lists each class).
  Gathering professions and First Aid (Mining, Herbalism, Skinning, Fishing, First Aid; `HIDE_PROFS`) aren't shown.
  Card body default "By slot" (`slotSections`): collapsible `details.cr-sec` per slot
  (`SLOT_ORDER`), open state in `wf-prof-crafter-open`, sort switch in
  `wf-prof-crafter-sort`. Item slot/levels come from
  `https://nether.wowhead.com/forever/tooltip/item/<id>` (CORS ok from the site; parsed:
  first `<table width="100%"><tr><td>SLOT`, `<!--ilvl-->`, `<!--rlvl-->`, "N Slot
  Bag/Quiver", "Use:"), 4 at a time, cached in localStorage `wf-item-meta-v2`; also `quality` → recipe names coloured like in game (`.q0`–`.q5`). Enchants
  (k "s") get their slot from the name (`ENCHANT_SLOT`) and keep export order.
  Recipe names are Wowhead links (`/forever/item=` for k "i", `/forever/spell=` for k "s",
  `data-wowhead="...&domain=forever"`); Wowhead's `tooltips.js` (zamimg) gives hover
  tooltips with icon and stats; `refreshTooltips()` re-scans after each render.
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
  CurseForge), then "What we use" (the owner's actual list, 2026-10-10): AtlasLootClassic
  Continued, Forever Bestiary, ForeverPlus (until Road to Forever replaces it), Leatrix Maps, Questie,
  ThreatMaster, TomTom — all CurseForge links, sorted alphabetically (case-insensitive) —
  plus a link to wow4ever.quest's addon compatibility tracker.
  Compact card layout (2026-10-05): a `.pick` column on the left holding the
  Select checkbox (the whole strip is the click target), then `.card-main` with
  a `.card-head` row — the addon name button (`.addon-btn`, links to CurseForge)
  left-aligned and the gold `.dl-btn` Download right-aligned on the same row —
  then the `.ver` line, then all description/notes inside
  `<details class="more"><summary>Details</summary>…</details>` (collapsed by
  default). New cards must follow this markup. Cards sit in `.addon-grid`
  (auto-fill, min 330px per column; 3 columns from 1100px wide, 2 on laptops,
  1 on phones; `align-items:start` so an opened Details only grows its own
  card). Page `.wrap` is 1180px wide; keep name buttons short enough to sit
  beside Download at 3 columns (AtlasLootClassic Continued is shown as
  "AtlasLoot Continued" with the full name in `title`).
  The button links to the addon's **WoW Forever file page**
  (`/wow/addons/<slug>/files/<fileId>`), not the project page, and under it a
  `<div class="ver" data-addon="<slug>">` line shows `Forever version <b>X</b> ·
  <upload date>`. The lede's `#versions-checked` line holds the date of the last
  check. Hand-edit directly.
  **Downloads:** every addon card is a `.dl-card` with `data-slug` (and, for
  CurseForge addons, `data-project` = CurseForge's numeric project id), a
  "Select" checkbox and a gold **Download** button, built in JS from the card's
  `.addon-btn` href (so the version check only keeps that href current):
  - CurseForge addon → `https://www.curseforge.com/wow/addons/<slug>/download/<fileId>`
    in a small pop-up window (`curseforgeDownload()`), which CurseForge starts
    the file from after ~5 s; our page closes the pop-up after 9 s
    (`POPUP_CLOSE_MS`; a page may close windows it opened, even cross-origin).
    Verified 2026-10-05 in the owner's Chrome: file arrived, pop-up closed. If
    pop-ups are blocked, the link falls back to a normal new tab. Tested
    2026-10-05 in the owner's Chrome: CurseForge does NOT let other sites start
    its files. `edge.forgecdn.net`/`mediafilez.forgecdn.net` links (redirect to
    mediafilez, 503) and `/api/v1/mods/<id>/files/<fileId>/download` from our page
    never produced a file; only CurseForge's own download page did. Don't retry
    these without a real download test (check the Downloads folder, not the
    network log — it showed 503 even for working CurseForge downloads).
  - Road to Forever → `.../releases/download/r2f-v<ver>/RoadToForever-<ver>.zip`,
    downloaded right on the page.
  The bottom tray's gold button walks the ticked addons: each press starts the
  next one ("Next: Questie (2 of 3)"), because browsers allow one pop-up per
  click. A hidden iframe of the download page does NOT work (tested). One combined zip isn't possible: neither forgecdn nor GitHub
  release files allow other sites to read them (CORS), and re-hosting other
  authors' addons ourselves needs their permission. Selection: localStorage
  `wf-addons-selected-v1`.
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
     Multi-flavor addons (AtlasLootClassic Continued, Questie, TomTom)
     show "Forever + N" in the list. CurseForge's list can come back stale or
     filtered to another flavor (on 2026-10-05 Prat's list first showed only
     August files without Forever); if no Forever file shows, read the project
     page's "Latest release ... Forever + N" line and confirm on that file's page
     that 1.60.x / Forever is in its supported versions before using it.
     Watch the slugs: Forever Bestiary is `forever-bestiary-pet-hunter`,
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
     files. It was replaced by ForeverAuras. If an addon disappears again, grey
     its card out with `.card.unavailable` (drop the `dl-card` class and the
     download row, `.ver.gone` line "Removed from CurseForge") and tell the user.
     In a real browser on curseforge.com, `fetch('/api/v1/mods/<id>/files?pageIndex=0&pageSize=10&sort=dateCreated&sortDescending=true')`
     returns the true file list as JSON (`fileName`, `gameVersions`, `releaseType`
     1 = release); use it when the browser tools are available.
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
- `assets/hero-1.webp` … `hero-4.webp` — landing page backgrounds (painted road-to-a-gate
  scenes, made by the owner with free outside image tools, not Claude). `index.html`'s inline
  script right after `<div class="hero" id="hero">` rotates them every 2 days (UTC day / 2,
  same picture for everyone), each with its own `background-position` so the party and gate
  stay in view; `?bg=1..4` previews one. CSS default is hero-1. Sources are the owner's
  downloaded files (1584×672 for hero-1, 1248×832 for the rest), upscaled to 2560/1920 wide.
  `assets/og.jpg` is built from hero-1.
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
- `assets/og.jpg` (1200×630 link-preview image, hero crop + "Road to Forever" in
  Marcellus), `assets/favicon.png` + `assets/icon-180.png` (gold "R" tab icon). Every
  page's `<head>` has description, `og:*`/`twitter:card` tags and the icons — new pages
  need the same block (macros.html gets it from template.html).
- `assets/drafts/` — gitignored scratch folder for image-generation drafts/
  intermediates (hero and icon art both land here). Not part of the deployed site.

## Workflow
1. Macro changes: edit `data.py` (or `template.html` for cheatsheet layout/top bar
   changes), then run `python build.py`.
   The top bar CSS (3-column grid: title left / nav centered / optional right-side
   item like index.html's mute button; stacks into one centered column at
   max-width 1180px so the title never wraps next to the 6-tab nav) must stay identical across all pages —
   `index.html`, `builds.html`, `addons.html`, `launch-plan.html`, `talents.html`,
   `library-books.html`, `professions.html` are
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

## Blizzard's own UI code (extracted from the game, 2026-10-09)
The game's interface Lua/XML for the Forever beta (1.60.1.70291) is extracted, read-only reference, at
`D:\WoW-Extract\interface\` (about 4400 files: `addons/blizzard_*`, `blizzard_framexml`, API documentation).
Read it instead of guessing frame names and function behaviour (e.g. the backpack button's texts live in
`addons/blizzard_mainmenubarbagbuttons/shared/mainmenubarbagbuttons.lua`). It is Blizzard's code: never copy
it into the addon. Tool: CASCConsole (CASCExplorer) in `D:\Tools\CASCConsole`, listfile in
`D:\Tools\CASCConsole_dl\community-listfile.csv`. Re-extract / extract more with
`CASCConsole.exe -m Listfile -e <csv of "fileID;path" lines> -d D:\WoW-Extract -l enUS -p wow_classic_beta -s "D:\World of Warcraft"`
(filter the listfile with grep first; `-m Pattern` finds nothing because names come only from the listfile).
