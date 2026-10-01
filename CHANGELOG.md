# Changelog

Authoritative history of what's actually shipped on wow-forever-macro. Working
history for whoever builds this next (including a future Claude session) — not
user-facing release notes.

## 2026-10-01 (Addon plan, step 2: site export mode)

- `macros.html` (via `template.html`) has a **Pick macros for the game** toggle
  at the right end of the spec row (question-mark macro icon, spec-pill style).
  Turning it on shows a checkbox on every macro pill, a tri-state checkbox on
  every group heading and section heading, and checkboxes on search results
  (so you can search "taunt" and tick across classes). Ticking a pill's box
  never switches the code panel; clicking the pill text still does. Selected
  pills get a 60% gold border. Real `<input type="checkbox">`s, visually
  replaced, keyboard and screen-reader accessible.
- A sticky **export tray** slides up at the bottom: "N macros selected", class
  chips with counts, Clear, **Copy import string** (shows "Copied" for 2 s plus
  "Now type /r2f in the game and click Import."), a Select menu ("Select all for
  <class>", "Select everything"), an empty-state hint, and an expandable "How to
  import (3 steps)". Stacks into two rows with full-width buttons under 640 px.
- Copy import string builds the `R2F1:` format from `ADDON_PLAN.md` section 7
  (records in page order, `\x1F`/`\x1E` separators, UTF-8 safe base64), using
  the ids/short names/icons build.py already embeds. Selection persists in
  localStorage `wf-export-v1`; unknown ids are dropped on load.
- Build-time judgment calls are written into `ADDON_PLAN.md` section 4.5
  (Universal's section is sent as `Universal`, Download link goes to the
  Releases page until step 7, "Select everything" is ~83 KB, etc.).
- Tested in headless Chromium (Playwright): toggle, pill/group/section
  cascades, keyboard toggling, reload persistence, search ticking, menu,
  mobile layout, and a decode round trip of the copied string against the
  source data; plus a byte-for-byte match against an independent Python
  encoding of two Universal macros.

## 2026-10-01 (Addon plan, step 1: macro data)

- `M()` in `data.py` now takes `short` (in-game macro name, max 16 chars) and
  `icon` (texture name, for macros with no `#showtooltip` spell to show its own
  icon). Every macro across Universal and all 8 classes got a `short` name,
  following `ADDON_PLAN.md` section 3.2's naming rules (abbreviations players
  already use, ` F` = focus, `@` = mouseover, `X>Y` = priority, `X/Y` = Shift
  modifier, `X+Y` = combo, ` me` = self-cast). Warrior and Paladin names came
  straight from the plan's tables; the other six classes' names were proposed
  by Claude Code and approved by the user before committing.
- `build.py` assigns each macro a stable id (`<CLASS>/<short>`, `ANY/<short>`
  for Universal) and fails the build with a clear message on a `short` over 16
  characters, a duplicate `short` within a class + Universal, or a macro with a
  body but no `short` whose `name` is over 16 characters. Ids and short names
  now also flow into the JSON embedded in `macros.html` and into
  `wow-forever-macros.md` (short name shown in backticks next to the full name).
- Full spec: `ADDON_PLAN.md`. This is step 1 of 10; see `BACKLOG.md` for what's
  next (site export mode, then the addon itself).

## 2026-10-01 (Warrior + Paladin macro pass)

- Warrior and Paladin macros regrouped into role sections: **General** (all specs),
  **Tank**, **DPS** (+ Paladin **Healer**). `template.html`/`build.py` render
  "General" like "Shared". New `melee()` helper and `stance(..., attack=True)`.
- Warrior: every melee strike now has `/startattack [harm]` (Heroic Strike,
  Cleave, Rend, Hamstring, Sunder, Slam, Execute, Overpower, Revenge, Shield Bash,
  Concussion Blow, Shield Slam, Mortal Strike, Bloodthirst, Pummel, Mocking Blow,
  Charge + Rend opener). Intimidating Shout deliberately left without it.
- Warrior new: Victory Rush (Forever, level 20, any stance, verified on Wowhead's
  Forever spell page), Victory Rush > Sunder (tank) and Victory Rush > Heroic
  Strike (DPS) one-button priority macros (beta-test flagged), Heroic Strike /
  Cleave on Shift, Charge for Vanguard tanks (no stance swap), mouseover Taunt,
  Sweeping Strikes. Slam moved to General (level 20 in Forever).
- Warrior fixes for Forever: Thunder Clap no longer forces Battle Stance (now
  usable in Defensive too), level notes on Berserker-stance abilities (30+),
  Shield Wall/Shield Block/Revenge notes updated to Forever values.
- Paladin: added "Auras on one button" (Shift/Ctrl modifiers).
- Sources: foreverchanges.pro (Warrior spellbook + changes), Wowhead Forever
  (Victory Rush), classicwowforever.com and kami-labs.fr macro lists.

## 2026-10-01 (level-30 Paladin + Warrior)

- Added level-30 builds to `DATA30` in `builds.html`: Paladin Retribution and
  Protection (Tank), Warrior Protection (Tank) and Arms. Warrior Fury has no
  level-30 build (Arms took its place at 30). Crusade still isn't in Wowhead's data,
  so the Ret build doesn't use it.

## 2026-10-01 (level-30 builds)

- `builds.html` got a "Level 20 / Level 30" toggle row under the class roster
  (`?level=30` in the URL works too). Level-20 builds are unchanged in `DATA`; the
  new level-30 builds live in `DATA30` (Priest Shadow, Warlock Affliction, Mage
  Arcane/Frost/Frost AoE/Fire, Rogue Combat, Shaman Enhancement, Hunter BM), each
  stored as a talents.html share `code` that the calculator loads directly
  (`mountSync` gets `code` instead of `preset` when a build has one). Their `talents`
  list (name/rank/icon, no desc) is only the static fallback row. No level-30
  rotations yet. Paladin and Warrior show "No level-30 build yet".
- Checked the "Crusade" Paladin talent question: neither Wowhead's Forever data nor
  Mobalytics' Forever calculator has a talent called Crusade (both list the same 50
  Paladin talents, 17 in Retribution), so our calculator isn't missing anything.

## 2026-10-01 (pink button)

- Added a tiny round pink button next to Unmute in the landing page top bar
  (`.sound-btns` wraps both). Each press plays the full "Ha! Gayyyy!" YouTube clip
  (`yOQqBMz70iM`) once through the same hidden player; no loop. While it plays the
  main button shows "Mute" and can stop it; the ENDED handler resets it after.

## 2026-10-01 (music clip)

- Landing page Unmute button now plays only the 1:05-1:12 chorus hook of the
  YouTube track (`loadVideoById` with `startSeconds`/`endSeconds`) once per click,
  instead of autoplaying the full song muted on a loop. When the clip ends the
  button resets to "Unmute" so it can be replayed; clicking "Mute" mid-clip pauses.

## 2026-10-01 (later)

- Replaced the landing page hero image (`assets/hero.webp`) with a new one: four
  Skyborne adventurers (Warrior tank, Druid healer, two Hunters with a panther and
  a wolf) standing on a cliff path above a sea of clouds at sunset, a floating sky
  isle with ruins/waterfalls in the distance. Generated via Gemini (full scene in
  one pass, after SDXL-only attempts — background generation, character inpainting,
  and compositing separately — kept hitting style/lighting mismatches or garbled
  faces); any leftover baked-in title text was removed with a local SDXL inpaint
  pass (small-resolution, not the 4x-upscaled version — doing it at full upscale
  size maxed out the GPU's 12GB VRAM and produced nothing). Final image was a plain
  LANCZOS resize to 2560×1080, not an AI upscaler — both 4x-UltraSharp and
  4x-AnimeSharp distorted the painterly faces into a waxy/photoreal look when
  tried. See the Personal Dev Support Folder's `local-tools-inventory.md` for the
  working ComfyUI ⁄ inpainting ⁄ ESRGAN setup notes from this session.

## 2026-10-01

- **Owner login for Group picks.** Group picks moved from a hard-coded array to
  `group-builds.json` in the repo. The site owner signs in on the Group picks tab with
  a GitHub fine-grained token (this repo only, Contents read/write; kept in the
  browser, checked with GitHub) and can then publish a saved build to the group, or
  edit/remove picks, straight from the site; each change is a commit that Pages
  redeploys in about a minute. Nobody else needs repo access, and visitors only read.
  Replaces the "Copy as group pick, paste into the file" workflow.
- **Saved builds sidebar** on the Talent Calc and Builds pages (`talentsaved.js`),
  so we can keep builds and look them up together instead of passing links around.
  Every calculator gets a gold "Save build" button; a floating "Saved builds" button
  opens a right-hand drawer styled like the Buyable quests one. **My builds** is
  stored per browser (name, note, class/tree/points summary; open, copy link, edit,
  delete, import a pasted link, copy all as links for the group chat; saving after
  opening a build offers "Update" or "Save as new"). **Group picks** is a curated list
  in the repo (`GROUP_PICKS`) seeded with the level-20 BM Hunter and Warrior Tank
  builds for the 2 Hunters · Warrior · Druid plan; "Copy as group pick" turns any
  saved build into a ready-to-paste entry. No backend: GitHub Pages is static, so
  shared lists live in the repo, not in a database.
- Shared calculator files are now loaded with a `?v=` cache-busting query on both
  pages: the first live check served a cached old `talentcalc.js` next to the new
  sidebar script and Group picks failed to render.

## 2026-09-30 (evening)

- Talent calc tree tabs (Builds cards) made much more visible: framed nav-style
  buttons, the open tree filled with the class color, trees with points in class color
  with a filled point badge (`tc-has`), empty trees grey.
- Builds page: every build card now has a live, preloaded talent calculator (compact
  mode: tree tabs, opens on the build's main tree, points editable, "Reset to build",
  "Copy link", "Open in Talent Calc"). Presets come from each build's talent names +
  ranks, matched against Wowhead's Forever data (all 13 builds verified valid). The old
  icon row stays as the fallback if the data can't load. Calculator engine moved to
  shared `talentcalc.js` + `talentcalc.css` (tc- prefixed), used by talents.html and
  builds.html. Also fixed builds.html being wider than a phone screen (hidden rotation
  tooltips).
- New **Talent Calculator** page (`talents.html`), our own code, replacing the external
  Zockify link in the top bar (now `talents.html` on all six pages; index.html's nav
  gained the link it was missing). All 9 classes including Druid, live Wowhead Forever
  data (Sep 24 beta trees: Strider Kick, Twist of Light, Templar's Bulwark present,
  Wyvern Sting gone), prerequisite arrows, tier/prereq/removal rules, 51-point cap,
  required level, per-tree reset, shareable `#class/digits` links, hover tooltips with
  next rank, touch bottom sheet with −/+.
- Removed the remaining "Venom & Trollmann" mentions from page text (Addons and Builds
  ledes) and docs; the site now says "we" throughout. Hero image still shows the old
  dwarf/gnome group with nameplates — replacement (4 Skyborne: Warrior, Druid healer,
  2 Hunters, no names) tracked in BACKLOG.
- Site renamed "Road to Forever" (was "Venom & Trollmann's Road to Forever") in the
  top bar on all five pages, the index `<title>` and hero `<h1>`; launch-plan lede
  now says "How we get ahead…". ROADMAP's locked site-title decision updated.
- Launch Plan: dropped Dual Mage, Dual Hunter and Triple Hunter. New Skyborne plans
  **2 Hunters · Warrior · Druid** (`hwd`: Warrior tanks, Druid heals) and
  **3 Hunters · Druid** (`h3d`: Druid flexes tank/heal), alongside Paladin · Hunter ·
  Shaman. Hunter texts folded into a shared `hunter` base profile (data key only);
  `base` now resolves up a chain. New steps: Druid Bear Form and Warrior Defensive
  Stance at 10 (Classic quests, flagged), plus beta checks. Ghost Wolf confirmed at
  20 (unverified tag removed). Compare defaults to hwd vs trio; stale saved modes
  (mage/hunter) fall back to hwd. Mage Legacy card removed.

## 2026-09-30 (afternoon)

- Launch Plan: two new plans next to Dual Mage / Dual Hunter. **Triple Hunter**
  (`hunter3`, inherits the hunter plan, with its own loot/pet/tank-and-healer notes)
  and **Paladin · Hunter · Shaman** (`trio`): Dwarves (Alliance Skyborne can't be
  Paladin or Shaman), Coldridge → Dun Morogh → Ironforge, then the shared route.
  Trio-only steps: Holy Strike/Seal of Fury/Righteous Fury/Consecration trainer
  levels, Shaman totem quests, Ghost Wolf, plus beta checks. Compare now picks any
  two plans; Key differences table is data-driven (`DIFFS`); "Duo play" renamed
  "Group play" with per-plan cards; new trio Legacy path card.

## 2026-09-30

Forever class-change pass (research: Warcraft Tavern, Mobalytics, Output Lag,
forever-hunter wiki, Zockify, classicwowforever.com). New `BETA` note prefix in
data.py marks macros that still need confirming in beta.

- Paladin: removed all "Judge + reseal" and "Crusader opener" castsequences
  (Judgement no longer consumes seals in Forever). Added Holy Strike + auto-attack,
  Divine Shield / BoP self with press-again cancel, Voice of Truth, Seal swap
  (Twist of Light, beta), new Holy section (Holy Shock friend or foe). Protection:
  Seal of Fury, Judgement taunt (mouseover + focus), Templar's Bulwark. Blessing of
  Kings moved Protection → Shared.
- Hunter: removed Wyvern Sting + focus (removed in Forever). Added Hunter's Mark +
  send pet, Volley at cursor (no cooldown now), Feign Death (clean), Intimidation +
  pet attack (replaced plain Intimidation). Multi-Shot note about its new cast time.
- Priest: Silence gets /stopcasting; added Prayer of Mending (Holy), Penance (Disc).
- Warlock: Wrack (Affliction), Incinerate (Destruction), Bane of Havoc focus; Dark
  Pact flagged for beta.
- Mage: Ice Block press-again cancel, Presence of Mind + Pyroblast, Arcane Blast.
- Rogue: Envenom → Venom, Pick Pocket + Sap.
- Shaman: Earth Shock (+ focus) get /stopcasting; Riptide, Water Shield, Lava Burst,
  Flame Shock > Lava Burst; Elemental Mastery macros flagged for beta; Stormstrike
  note updated.
- Warrior (Protection): Sunder + Heroic Strike.
- Hunter (Survival): added Strider Kick and a "Survival melee button" (Raptor Strike +
  Mongoose Bite + Strider Kick, beta-flagged). Strider Kick confirmed as the in-game name
  (Blizzard forum thread). Lacerate not added: it reads as the bleed from the Lacerating
  Strikes talent, not a button.
- Builds page, Paladin: Ret gets Holy Strike + Consecration (AoE); Prot swaps Seal of
  Righteousness for Seal of Fury (level 10, Judgement taunts), adds Holy Strike and
  Consecration (class spell at 20 in Forever, per wowforevertools.com trainer list).
  Icons checked against Wowhead's Forever tooltip data: Holy Strike really uses
  `classicon_paladin` in game (file 626003); Seal of Fury uses `spell_holy_sealoffury`,
  the same icon as Righteous Fury.

## 2026-09-29

- Universal › Misc / UI: removed "Mark mouseover/target with skull" and "…with cross".
  Duplicates of "Skull mark mouseover / target" under Targeting helpers, which already
  explains the marker numbers and the /tm vs ThreatMaster gotcha.
- Macros page: "Style patterns" on the Universal tab is now a collapsible section,
  collapsed by default (`details.patterns-wrap` in template.html).
- Warlock: "Shadow Bolt" became "Shadow Bolt + Imp Firebolt" (`/petattack [harm]`,
  `/cast [pet:Imp, harm] Firebolt`, `/cast [harm] Shadow Bolt`).
- Hunter: added "Aspect toggle: Cheetah ↔ Hawk" (`/castsequence reset=combat Aspect of
  the Cheetah, Aspect of the Hawk`) next to the existing combat-based aspect macro.
  Each press swaps aspects; resets to Cheetah after combat.

## 2026-09-28 (evening)

- Moved the Buyable quests button from bottom-right to top-right, just under the
  sticky top bar (follows the bar's height on mobile). Sidebar unchanged.
- Launch Plan: added a "Buyable quests" sidebar (floating button bottom-right, TOC
  link, or `#buyable`). Lists quests that can be finished with Auction House/vendor
  items instead of farming, sorted along our route (phase 1/2/3 + off-route) or by
  zone, with item counts, quest level, a gray-XP warning where our route reaches the
  zone too late, per-browser "done" checkboxes, and a Wowhead Forever search link.
  Harvesting the Harvesters is confirmed on Forever's Wowhead; the rest is Classic
  data, with a few recalled-from-Classic entries tagged "verify in beta".

## 2026-09-28

- Hunter: added three pet attack macros next to "Pet attack TT / target" —
  "Pet attack mouseover", "Pet attack mouseover / TT" and "Pet attack / Shift =
  follow" (Shift+press calls the pet back). No #showtooltip on purpose: /petattack
  isn't a spell, so #showtooltip would only show a red "?"; each note tells the
  player to pick the pet bar's Attack icon (Ability_GhoulFrenzy) in the macro window.

## 2026-09-29 (night)

- Found the real cause of the earlier "ThreatMaster steals Alt+1/Alt+2" report:
  it's not a keybind conflict at all — ThreatMaster registers the `/tm` slash
  command for itself, which collides with WoW's built-in `/targetmarker`
  shorthand. Any macro using `/tm` to mark a target silently calls ThreatMaster
  instead once the addon is installed. Traced this by reading through
  ThreatMaster's full Lua source (confirmed it sets no keybindings anywhere)
  and working through in-game diagnostics with the user.
- Fixed every macro in data.py that used the `/tm` shorthand (the two Universal
  mark-mouseover/target macros and Mage's Polymorph + Diamond mark) to use the
  full `/targetmarker` command instead, so they no longer collide with
  ThreatMaster. Updated CLAUDE.md with a standing rule to prefer full command
  names over shorthands that a popular addon might claim.
- Rewrote the ThreatMaster addons.html warning to describe the actual slash-
  command conflict and its fix, replacing the earlier (incorrect) theory that
  it silently claimed the Alt+1/Alt+2 keybinds directly.

## 2026-09-29 (evening)

- Flagged a known issue on ThreatMaster's addon card: it silently claims Alt+1
  and Alt+2, breaking any other keybinds on those combos, with no setting for
  it anywhere in-game or in the addon's own options. Confirmed by disabling
  the addon (the bindings came right back). Added a `--warn` color variable to
  addons.html for this kind of inline caveat.

## 2026-09-29 (later)

- Clarified that MythicSim's DPS tier list is a level-60 endgame simulation
  (confirmed: "one raid-boss target, level 63... Most specs use talents from a
  published level 60 guide build"), not a beta/leveling-relevant ranking —
  relabeled it "DPS Sim Tier List (Lvl 60, predicted)".
- Added Wowhead's level-20-scoped DPS PvE tier list ("DPS Tier List (Beta, Lvl
  20)") as the beta-relevant counterpart. Its actual tier content couldn't be
  independently verified (page is JS-rendered, unreadable via automated fetch),
  so it's linked as a real/maintained/correctly-scoped source, not a
  confirmed-accurate one.

## 2026-09-29

- Restyled the class-roster buttons on macros.html and builds.html to match the
  top-bar nav's framed gradient-button look (uppercase, bordered panel, hover
  glow, bright gradient when selected) instead of the plain flat/outline buttons
  they used before. builds.html's spec-picker pills got the same treatment.
- Addons: removed Platynator (replaced in-game by a working Plater setup) and
  added ForeverLayers, WeakAuras Forever, ThreatMaster, and TomTom. Redesigned
  every addon card to a single framed nav-style button linking to CurseForge
  (name only, no separate "CurseForge" pill) with the description below, and
  sorted the "What we use" list alphabetically.

## 2026-09-28 (night)

- Rebuilt builds.html as a JS-rendered class/spec picker (was static HTML per
  class before): pick a class from the icon roster, and — for classes with more
  than one build — pick a spec (Mage: Arcane / Frost (Ice Lance) / Frost
  (Piercing Ice) / Fire; Paladin: Retribution / Protection; Warrior: Tank /
  Fury). Added a Rotation section to every build (single-target and AoE ability
  lists, icons + arrows matching the talent-card style, a repeat glyph on
  loop-based rotations, and a confidence badge: "high" for build-matched guides,
  "medium" where reasoned from mechanics with no exact source found).
- Added 3 new Mage builds: Frost (Piercing Ice) and Fire, alongside the existing
  Frost (Ice Lance) build now relabeled, plus the previously-discussed Arcane
  spread as its own build.
- Fixed several wrong icons found during this pass (real icon filenames can be
  very unintuitive vs spell names): Rogue's Sinister Strike (was showing an
  unrelated TBC-era talent's icon), 3 Mage Arcane talent icons, Shaman's AoE
  (added Fire Nova Totem detonating off an already-placed Searing Totem — kept
  both, they're complementary not either/or), Hunter's AoE (added Multi-Shot,
  learnable at level 18), Warrior Fury's AoE (swapped Piercing Howl, a slow, for
  Cleave, an actual AoE damage tool).
- Made the builds-grid give same-size, side-by-side cards for multi-build
  classes (Paladin, Warrior) instead of one card growing taller from longer
  rotation text — capped card width and rotation-note line length.

## 2026-09-28 (evening)

- Added "DPS Sim Tier List" (mythicsim.com) to the landing page's Tools column —
  a simulated (not real-parse) DPS ranking, the only source found so far that
  discloses its methodology and is dated after the Sept 24 wand/Wizard Oil nerf
  patch. Chosen after a research pass found several other tier-list sites
  contradicting each other and predating that patch (see prior research in this
  conversation — not separately logged since no file changed for that research).

## 2026-09-28 (later)

- Replaced the Paladin "Hybrid (Prot/Ret)" build card on builds.html with two
  separate cards: Retribution (PvE) — the pure 0/0/11 build (Benediction 5/5 →
  Conviction 5/5 → Seal of Command 1/1) — and Protection (Tank) — the 0/11/0 build
  (Redoubt 5/5 → Precision 3/3 → Anticipation 2/5 → Shield Specialization 1/3).
  Verified talent existence/ranks/icons against foreverchanges.pro and
  cross-checked against community leveling-build guides.

## 2026-09-28

- Reorganized the landing page's side-links overlay: split into "General Resources"
  (Zockify, Wowhead, Icy Veins, Warcraft Tavern, Mobalytics, ForeverChanges) and
  "Tools" (2 talent calculators, Legacy Calculator, Best-in-Slot Gear, Dungeon Loot
  Tables, a new Hunter Pet Database link to beastmaster.io) as two side-by-side
  boxed columns, each link its own compact icon+title card. Cozy Sleeping Bag stays
  its own featured card above them with a shortened one-line description. Moved the
  Talent Calc link out of the top nav into the new Tools column.
- Corrected: beastmaster.io/forever is a Hunter pet database (588 tameable pets),
  not a talent calculator as originally assumed — filed it under Tools accordingly.

## 2026-09-27 (late evening)

- Launch Plan: fixed the Legacy points misunderstanding. Everyone starts at 0 points
  (earned from challenges, first at level 25); 16 is the per-character spend cap at
  launch, not a starting pool. Reagent Economy sits in Resourcefulness column 3 (needs
  10 points in that tree, so point 11 at the earliest), so it's no longer the "first
  pick". New "Legacy points" section: how points work, fastest sources, column gates
  (col 1 open / col 2 = 5 in tree / col 3 = 10 in tree), Well Rested and Talented
  explained, a perk-by-column table per tree (from Wowhead's Legacy Calculator), and a
  mage path (Thrill 5 → Resourcefulness 11 → Reagent Economy at 16) vs hunter path
  (Thrill 5 → Adventure → Frequent Flier at 11). Added level-25 and level-45 Legacy
  steps, two beta checks (Novice Spelunker dungeon list, respec rules), and updated
  the Compare table row.

## 2026-09-27 (night)

- Launch Plan: confirmed in-game that Aspect of the Cheetah trains at level 20 —
  dropped the `unverified` tag on that step. Tightened the Reagent Economy wording
  after checking its actual in-game tooltip ("class abilities no longer require
  reagents purchasable from vendors"): ammo is a weapon consumable, not a spell
  reagent, so it's almost certainly not covered — the beta test-list item now
  asks to confirm that exclusion rather than asking an open "does it cover ammo?"
  question.

## 2026-09-27 (evening)

- Launch Plan now has a Dual Mage / Dual Hunter / Compare switch. The route is the
  same for both; the hunter plan adds the level-10 pet quest, ammo/pet-food stocking,
  loot rules, pet roles, Aspect of the Cheetah, and swaps the Legacy, Deadmines-detour,
  dungeon-group and duo-play advice. Compare shows a key-differences table plus every
  phase side by side (shared steps full width, with a "show only differences"
  filter). Steps are now data-driven (`PHASES`/`DUO` in the page script); existing
  checkbox ids were kept so saved progress carries over. Choice is shareable via
  `?plan=`.

## 2026-09-27 (even later)

- Mage: added "Polymorph + Diamond mark" — marks the target with a diamond
  (`/tm ... 3`) and casts Polymorph in one macro, so the group can see at a
  glance which target is sheeped and not to break it.

## 2026-09-27 (later)

- Fixed the top bar on `launch-plan.html`, `macros.html`, `builds.html`, and
  `addons.html` (plus `template.html`, which `macros.html` is generated from):
  they were still using the older flex `space-between` layout, which pushes the
  nav links to the right edge instead of centering them like `index.html`'s top
  bar (title left / nav centered) has done since an earlier session. All 5 now
  share the same 3-column grid topbar style — pages without a mute button simply
  leave the third grid column empty.

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
