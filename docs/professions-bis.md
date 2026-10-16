# Professions page, Crafters and Mr.BiZ page

Notes for professions.html (enchants, costs, live prices, Crafters) and bis.html. Moved out of CLAUDE.md 2026-10-16.

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
- `bis.html` — **Mr.BiZ**, hand-written, JS-rendered from `bis-data.json` (GENERATED: never hand-edit). Pickers are custom
  dropdowns (`Drop(id, onPick)`: button + `role="listbox"`, arrow keys / Enter / Esc / type a letter), because native
  `<select>` can't show icons or colours everywhere: Class (WoW class colours `CLASS_COLOR` + class icons), Spec (class
  colour, grouped Tank / DPS / Healer with role icons), Faction (Alliance blue / Horde red + banner icons; Alliance
  default; flags faction-only quest rewards "Horde only"), Level (30 "beta cap"; 60 "in the works" is pickable and
  shows what's coming, never saved, so every visit starts at 30; add real 60 data as its own level when it exists).
  Source chips and row source lines carry small inline SVG icons (`TYPE_ICON`: "?" quest, hammer crafted, crossed
  swords PvP...); crafted rows and the Profession dropdown use the profession's game icon (`PROF_ICON`, zamimg).
  Biz ranks (owner's group joke, keep them): #1 Bizzest, #2 Bizzer, #3 Biz, 4th+ Almost biz, and "The Bizz" tag when
  the next pick is `THE_BIZZ_GAP` (20) % or more behind; delta 0 = "just as biz". The addon uses the same names.
  Every rank has a source (best picks from raw/, ranks 2-3 from `bis/sources.json` when they aren't a best pick
  anywhere), shown as a line under each rank in the open list. Filters: when the best is filtered out the row shows
  the first rank that passes (stand-in, `.row.standin`, its rank name as tag, % behind instead of the score);
  "Hidden by your filters" only when no rank passes. Source icons are coloured per type (`.ti-<type>`), text isn't.
  Each known source carries `via` (the site it was read from: ForeverDB for best picks, ForeverDB or Wowhead per
  entry in sources.json), shown as small grey "· ForeverDB" after the source line (`viaTag`) and in the addon tooltip. Filters: one chip per source
  type in the data (`types`; Raid is greyed until a raid item exists), Profession (crafted items only), Show = all /
  known sources / Forever data only (conf seen + client). A slot whose best pick is filtered out stays as "Hidden by
  your filters" (ranks 2-3 have no source in the data, so it can't fall back to them). Each row: slot, item name =
  Wowhead link `/forever/item=<id>` with `data-wowhead="item=<id>&domain=forever"` (tooltips.js, `iconizeLinks`,
  `refreshTooltips()` after each render), coloured by quality (`.q0`–`.q5`) from
  `https://nether.wowhead.com/forever/tooltip/item/<id>` (4 at a time, cached in localStorage `wf-bis-quality-v1`, same
  approach as the Crafters view), source label, score, confidence badge, chevron (ranks 2-3 with % behind, Wowhead /
  ForeverDB links, stats), wishlist star. Wishlist aside: per character name (select + New; localStorage
  `wf-bis-wish-v1` = `{current, chars: {name: {items: {id: {name, spec, slot}}}}}`), grouped by the best pick's
  `group` (dungeon / profession / vendor...), biggest first. "Copy for the addon" / "Paste from game" use the addon's
  string `R2FW1:<id>:<class/spec>:<slot>,...`. Prefs in `wf-bis-v1`; `bis.html#<class>/<spec>` opens a spec (shareable).
  Credit line (ForeverDB + Wowhead) under the list: keep it.
