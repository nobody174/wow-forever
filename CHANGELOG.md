# Changelog

Authoritative history of what's actually shipped on wow-forever-macro. Working
history for whoever builds this next (including a future Claude session) — not
user-facing release notes.

## 2026-10-03 (Addon v0.10.5: tolerate position jitter in talent nodes)

Follow-up to v0.10.4, found with live data: a dump of all 50 nodes of a Paladin's
trait tree has 13 distinct posX values, with Protection's first column at both 5020
and 5030 (10 units of jitter in Blizzard's data; real column steps are 590-600).
v0.10.4 ranked every distinct value as its own column, saw 5 Protection columns and
refused the tree ("couldn't read your talents yet"). `Talents.lua` now snaps values
closer than 20% of the median gap onto one grid line (X before the pane split, and
Y) before ranking. The tolerance is relative, so it doesn't depend on the scale, and
it changes nothing when there's no jitter. Real fixture reads 4/4/4 columns with link +
hash equal to `talentcalc.js`; synthetic Y jitter, multi-pair jitter, other scales,
a too-close-but-real column and a jitter-majority refusal are tested. See
`ADDON_PLAN.md` 13.11. Suite: 9389 checks, 0 failed (9259 before); luacheck 0
warnings. Tag `r2f-v0.10.5`.

## 2026-10-03 (Addon v0.10.4: read talents through C_Traits, corrects v0.10.3)

v0.10.3's premise was wrong: `LoadAddOn("Blizzard_TalentUI")` returns `false,
"MISSING"` on WoW Forever and the Classic talent globals never exist, so Preview
still failed. Talents live in the trait system (`C_Traits`), the API WeakAuras
Forever reads them with. `Talents.ReadTrees()` now reads the active trait config;
node positions are ranked into tier/column (verified against 8 real Paladin nodes
and Wowhead's row/col for the same node ids), and the three panes, which are one
trait tree on Forever (Paladin: 1 tree, 50 nodes = Wowhead's 17+16+17), are split by
the gaps between columns. Same output shape, so links, hash, preview and learning
order are unchanged. Learning on Forever is now always guided (the addon no longer
calls `LearnTalent` without Classic's `GetTalentInfo` confirming the address).
Tooltips via `SetSpellByID`; `TRAIT_CONFIG_UPDATED` handled. See `ADDON_PLAN.md`
13.10 for evidence and what's still unverified (non-Paladin classes, Prot/Ret
positions). Suite: 9259 checks, 0 failed; luacheck 0 warnings. Tag `r2f-v0.10.4`.

## 2026-10-02 (Addon v0.10.3: fix Talent Preview on a fresh login)

> Superseded by v0.10.4 above: the Blizzard_TalentUI premise was wrong.

Reported from real in-game testing: Preview always failed with "couldn't read
your talents yet" until the player had separately opened their real Talent
window. Root cause confirmed via `/dump GetNumTalentTabs()` in-game: that
function (and `GetTalentInfo`) don't exist as globals until Blizzard's own
on-demand `Blizzard_TalentUI` addon loads, same as `Blizzard_Calendar`/
`Blizzard_MacroUI`. Found the fix by reading RXPGuides, a working third-party
addon already on the client, which already solves this exact problem and
separately has a proven working `LoadAddOn` call to copy the pattern from.
`Talents.ReadTrees()` now force-loads `Blizzard_TalentUI` itself. See
`ADDON_PLAN.md` 13.9. Full suite re-run: 8770 checks, 0 failed. Tag
`r2f-v0.10.3`.

## 2026-10-02 (Addon v0.10.2: version/author footer on the Home tab)

Requested from real in-game testing: no way to see the addon's version or who
made it without opening the TOC file. Added a quiet line at the bottom of the
Home tab that reads the TOC's own `## Version:`/`## Author:` fields through
`GetAddOnMetadata` (`C_AddOns` first, bare global fallback, plain no-version
line if neither exists — never a second hardcoded copy). Hovering it shows the
TOC's `## Notes:` text. See `ADDON_PLAN.md` 12.4.2. Full suite re-run: 8688
checks, 0 failed. Tag `r2f-v0.10.2`.

## 2026-10-02 (Addon v0.10.1: fix the per-character macro slot limit — 18 to 30)

Reported from real in-game testing: the Macro Book's Character counter should
read out of 30, not 18. `Macros.Limits()`'s fallback (used because
`MAX_CHARACTER_MACROS` isn't defined on WoW Forever's client, same quirk as
other legacy globals found this week) was hardcoded to vanilla/Classic Era's
18. User confirmed the real number by counting WoW Forever's `/macro`
Character tab directly: 30 slots (5 rows of 6). Fixed the one constant;
updated `ADDON_PLAN.md`, `BACKLOG.md`, `TESTING.md` and the Lua test stub/
assertions to match. Full suite re-run: 8608 checks, 0 failed. Tag
`r2f-v0.10.1`.

## 2026-10-02 (heal() and util() macros: add self-cast fallback)

Reported from real gameplay: Holy Light (and every other `heal()` macro — Flash
Heal, Healing Wave, etc.) did nothing at all with no mouseover and no friendly
target, since `/cast [@mouseover, help, exists][help] SPELL` has no fallback
clause. Added `[@player]` as a third clause, matching the pattern `buff()`
already used, so these now heal yourself instead of fizzling.

Also added the same fallback to `util()` (friend-or-foe spells: Dispel Magic,
Remove Curse, Penance, Holy Shock) for consistency — user's explicit call,
accepting that Dispel Magic/Remove Curse self-cast with no target could strip
one of your OWN beneficial buffs, same risk a Dispel Magic button always has
used on the wrong target. Fixed two hand-written "Inner Focus + Greater Heal"
macros (Discipline, Holy) that duplicated the old pattern by hand instead of
calling `heal()`. Left the Soulstone mouseover item-macro alone (self-casting
a soulstone on yourself doesn't make sense). Updated `CLAUDE.md`'s documented
macro style rules and `build.py`'s markdown-cheatsheet pattern notes to match.
Rebuilt `macros.html`/`wow-forever-macros.md`; every macro still ≤255 chars
(longest unchanged at 204).

## 2026-10-02 (Addon v0.10.0: Macro Book class picker, Remove from library confirm, Tidy up tooltip)

Requested from the first real in-game testing session (not in the original addon
plan): on a Paladin, the tester imported Warrior macros and saw no Warrior tab,
since the book only showed the logged-in class (ADDON_PLAN.md 5.7).

- **Addon v0.10.0** (tag `r2f-v0.10.0`): `UI/MacroBook.lua` gets a class picker (row of
  `UI-Classes-Circles` check buttons, own class pinned first, only classes with
  library macros, hidden when no other class has any). Other classes are browsed
  **read-only**: drag/click refused in the book and, independently, in
  `Macros.Ensure`/`Create`/`Replace` via the new `Macros.UsableHere`; grey icons, no
  `Learn later`, Shift-click and the right-click menu still work. Slot counters and
  on-bars checks stay this character's, with a note while previewing. Browsed class is
  a session-only Lua local (relog/reload = own class), nothing new in SavedVariables.
  Import prefers a new Universal/own-class tab (`Import.Diff` `firstNewOwn`), else opens
  the imported class's preview. DPS tab icon follows the tab's class.
- **Remove from library** (right-click) now has a confirm popup, removes the library
  entry only (real macro and its record untouched; re-import counts it as new); allowed
  on previewed classes too. **Tidy up** gets a tooltip that contrasts it with Remove
  from library. Single right-click delete chosen over a bulk check-box mode.
- **Tests:** `run_tests.py` 8608 checks pass (was 8310): new `test_class_picker` and
  `test_remove_from_library` on template + fallback paths; 23 hand mutations each fail
  the suite. luacheck 0 warnings. Decisions in `ADDON_PLAN.md` 5.10; in-game checks in
  `addon/RoadToForever/TESTING.md` 17.

## 2026-10-02 (Addon v0.9.1: fix the Interface number — addon wasn't loading)

First real in-game install (0.9.0) showed the addon in the AddOns list but
flagged "Incompatible" — the game refused to load any of it, so there were no
errors to see, no minimap icon, and `/r2f` did nothing. Root cause: the TOC's
`## Interface: 11507` was always a Classic Era placeholder, documented as
needing a real beta check (ADDON_PLAN.md section 11) that hadn't happened
until this report came in. Confirmed the real number via `/dump
GetBuildInfo()` on the live Forever client: `tocversion=16001`. Fixed the TOC,
updated ADDON_PLAN.md/TESTING.md to mark this beta check done, re-ran the full
test suite (8310 checks, 0 failed). Tag `r2f-v0.9.1`, no addon code changed.

## 2026-10-02 (Addon plan: Quick settings, Road to Forever addon v0.9.0)

- **Addon v0.9.0** (tag `r2f-v0.9.0`): the last item of the addon build. Home tab gets
  **Quick settings**, three check boxes that set CVars directly (new `QuickSettings.lua`):
  Max camera zoom = `cameraDistanceMaxZoomFactor 4` (unticked = `GetCVarDefault`, never
  a hardcoded number), Hide guild names = `UnitNamePlayerGuild 0/1`, Hide PvP titles =
  `UnitNamePlayerPVPTitle 0/1`. Boxes are redrawn from `GetCVar` on every Home refresh
  (tab open, combat change, new `CVAR_UPDATE` handler), nothing stored in
  SavedVariables; writes are read back (refused/clamped values reported). Out of combat
  only: boxes grey out, and `QuickSettings.Set` checks `R2F.InCombat()` before
  `SetCVar` (refused, not queued). Global `GetCVar`/`SetCVar`/`GetCVarDefault` with a
  `C_CVar` fallback; a missing CVar greys its box out.
- **Macro Book** hides exactly `ANY/Zoom`, `ANY/HideGuild`, `ANY/HidePvP` (exact-id
  lookup, only while the matching box can work) with a note on the Universal tab. The
  three macros stay on the website (`data.py` untouched) and in the addon's library.
- **Tests:** `run_tests.py` 8310 checks pass (was 8006): new `test_quick_settings` on
  both template and fallback paths (CVar stubs in `wow_stubs.lua`), ids checked against
  macros.html's data, look-alike ids not hidden; 15 hand mutations each fail the
  suite. luacheck 0 warnings. Decisions in `ADDON_PLAN.md` 12.4.1; in-game checks in
  `addon/RoadToForever/TESTING.md` 16 (incl. whether `SetCVar` is really
  combat-blocked for these CVars, unconfirmed).

## 2026-10-02 (Addon plan, step 10: talent learning, Road to Forever addon v0.8.0)

- **Addon v0.8.0** (tag `r2f-v0.8.0`): Learn talents is live. Confirm popup (`Learn N
  talent points? Only a trainer reset can undo this.`), then a resumable, event-driven
  state machine at the end of `Talents.lua` learns step 9's `LearnOrder` one point at a
  time: re-verify on the live game (preview/conflicts, tier rule, `GetTalentPrereqs`,
  free points), `LearnTalent` (its only call site, combat-checked), wait for
  `CHARACTER_POINTS_CHANGED` or the 0.5 s `C_Timer` timeout, re-read the rank; a point
  that didn't land stops the run with 13.5's message. `PLAYER_REGEN_DISABLED` stops it
  mid-run; Learn talents continues a stopped run (no second popup) and waits for a point
  still in flight instead of re-sending it (no double rank). Popup accepted in combat
  -> `Macros.RunOrQueue`. Tab: `Learning X / N`, rest locked, Cancel -> Stop, stop/done
  line. Fallbacks: Blizzard's talent preview if present and switched on (fill only,
  Blizzard's button commits); **guided mode** (new `UI/TalentGuide.lua`) when
  `LearnTalent` is missing or blocked (`ADDON_ACTION_FORBIDDEN`/`BLOCKED`, or the first
  point refused): our own glow frame on `UIParent` anchored over Blizzard's talent
  button, `Click X (2 of 21)`, nothing of Blizzard's modified.
- **Tests:** `run_tests.py` 8006 checks pass (was 6223): a fake server in
  `wow_stubs.lua` (Classic's learn rules, async answers, combat raises), full/partial/
  resumed runs, every stop path and message, combat interrupt + resume, no double send,
  re-verification cases, guided mode, preview mode; a source test pins the single
  `LearnTalent` call. 24 hand mutations each fail the suite. luacheck 0 warnings.
  Decisions in `ADDON_PLAN.md` 13.8; in-game checks in `addon/RoadToForever/TESTING.md`
  15 (**not run on a real client yet**; do them on a test character first).

## 2026-10-02 (Addon plan, step 9: talent import preview, Road to Forever addon v0.7.0)

- **Addon v0.7.0** (tag `r2f-v0.7.0`): the Talents tab replaces its step-6 placeholder
  (new `UI/TalentPanel.lua`). Paste a site talent link (full URL, `talents.html#...`,
  `#...` or bare `class/code`), Preview: three 4x7 mini trees (learned / learned now
  with gold glow and `+N` / later / not in build / red conflict), tree headers
  `current -> planned`, the game's talent tooltip + `Build: X / Y`, and 13.4's
  summary line. `Talents.lua` gained `ParseLink` / `Preview` / `Plan` / `Summary` /
  `LearnOrder`, mapping digits through step 8's own `ReadTrees` (no second sort).
  Hash on import: match -> preview; none -> yellow "Older link" line; different ->
  13.3's stop message, except on a non-English client, where it gets a yellow "can't
  be checked" line (names are translated, so it could never match; ADDON_PLAN 13.6's
  hand-off). Sanity checks (rank over max, no such talent / tree) show as red
  conflicts. Learn talents is present but disabled until step 10; Copy my build is a
  button on the tab (`/r2f copybuild` kept as a shortcut). Last link remembered per
  character; preview re-runs on `CHARACTER_POINTS_CHANGED` / `PLAYER_LEVEL_UP`; Home's
  Talents line shows free talent points (12.4). Read-only, so it works in combat.
- **Tests:** `run_tests.py` 6223 checks pass (was 5837): every link the real
  `talentcalc.js` makes for the fixture builds parses and previews as exactly that
  build; all hash cases; every summary sentence word for word; mini-tree states and
  widgets on template and fallback paths; the fake client's `LearnTalent` raises and is
  never called, and a source scan finds no talent-learning call. 18 hand mutations of
  the new code each fail the suite. luacheck 0 warnings. Decisions in `ADDON_PLAN.md`
  13.7; in-game checks in `addon/RoadToForever/TESTING.md` 14.

## 2026-10-02 (Addon plan, step 8: talent export + `~hash`, Road to Forever addon v0.6.0)

- **Site, `talentcalc.js`:** every talent link the site hands out now ends in a
  4-character check, `talents.html#<class>/<code>~<hash>` (ADDON_PLAN.md 13.3):
  djb2 over the class's talent names in link order (`,` between talents, `;`
  between trees, UTF-8 bytes), `mod 36^4` in base36, zero-padded. New
  `instance.link()` (Copy link in both modes, builds.html's Open in Talent Calc,
  talents.html's address bar), `TalentCalc.treeHash` / `hashFor` / `cleanCode`.
  `instance.encode()` and stored codes (saved builds, `group-builds.json`) stay
  without the hash. **Readers ignore everything from `~`** (calculator, talents.html
  hash, saved-builds import), so old and new links both open; before this a hash
  with digits would have been read as extra ranks (`35~111` -> `350111`).
  `talentsaved.js`: its Copy link adds the hash once the page has the data.
  `?v=20261001b` -> `?v=20261002a` for all three files on talents.html and builds.html.
- **Addon v0.6.0** (tag `r2f-v0.6.0`): new `Talents.lua` reads the character's
  talents (`GetNumTalentTabs` / `GetNumTalents` / `GetTalentInfo`, sorted tier then
  column = the link's digit order), encodes them exactly like the site, adds the same
  hash from the game's own talent names, and shows the full site link in the copy
  box (`/r2f copybuild` until the Talents tab gets its button in step 9/10).
  Read-only, so it works in combat (reasoning in ADDON_PLAN.md 13.6). The copy box
  takes a per-use hint line.
- **Cross-checked, not hand-traced:** `addon/tests/run_tests.py` runs the real
  `talentcalc.js` in Node (`talent_link_check.js`) and `Talents.lua` under Lua 5.1
  on one fixture (`talent_fixture.json`: unsorted ids, a non-ASCII name, an empty
  tree) plus a Python reference: identical hash per class and identical links for 7
  builds, matching hand-worked codes. Also run once on Wowhead's live Forever data
  (9 classes, hash + one link each, 18/18 identical; data not stored). Mutations of
  either side (separators, sort, UTF-8, modulus, zero/dash stripping, the `~` rule)
  each fail the suite. `run_tests.py` 5837 checks pass (was 5655; +166 talent
  checks on the template and fallback paths, +16 "TOC file exists" checks for the
  new file), luacheck 0 warnings; a Playwright run of talents.html /
  builds.html confirmed the hashed links, the `~` rule, the saved-builds import and
  the new `?v=`. Decisions in `ADDON_PLAN.md` 13.6 (incl. a locale caveat for step 9);
  in-game checks in `addon/RoadToForever/TESTING.md` 13.

## 2026-10-02 (Addon plan, step 7: release pipeline, Road to Forever addon v0.5.0)

- **Release workflow** `.github/workflows/release.yml`: pushing an `r2f-v*` tag
  builds `RoadToForever-<version>.zip` with `git archive --prefix=RoadToForever/
  HEAD:addon/RoadToForever` (top folder `RoadToForever/`, unzips straight into
  `Interface/AddOns/`; `addon/tests` and `addon/art` can't get in) and publishes it
  as a GitHub Release via `softprops/action-gh-release@v2`. 0.x tags are
  pre-releases, 1.0.0+ normal releases. Release notes = that version's section of
  `addon/RoadToForever/CHANGELOG.md`. The run fails if the tag's version differs
  from the TOC's `## Version:`.
- **Tag prefix settled:** `r2f-v*` is final (the plan's `addon-v*` was never used;
  the four existing `r2f-v0.1.0`..`0.4.0` tags stay as they are, without releases).
- Addon bumped to **0.5.0** (tag `r2f-v0.5.0`, the first real release) with no Lua
  change, to keep "each plan step = next minor version, tag = TOC version".
- **Macros page:** the export tray's "How to import" step 1 now names the zip and
  says to unzip it into `Interface\AddOns\`. The Download link stays on the
  Releases page (`/releases/latest` skips pre-releases, so it has nothing to show
  until 1.0.0).
- Verified locally: the workflow's `git archive` command on the commit's tree gives
  the expected 19 files under `RoadToForever/`, every extracted `.lua` compiles
  under Lua 5.1, luacheck 0 warnings, `run_tests.py` 5655 checks pass, YAML parses,
  actionlint clean, the version/notes steps replayed for good, mismatched and
  malformed tags. The workflow itself
  can only run on GitHub (`TESTING.md` 12). Decisions in `ADDON_PLAN.md` 8.1.

## 2026-10-02 (Addon plan, step 6: Road to Forever addon v0.4.0, main window, minimap button, logo)

- The addon now has **one main window** (`UI/MainWindow.lua`) with Home / Macros /
  Talents tabs at the bottom and the new logo as portrait (tag `r2f-v0.4.0`). The
  step-3 Macro Book was reparented into the Macros tab (same code and public
  functions, no separate window). **Home** (`UI/Home.lua`) shows library / on-bars
  counts, a Talents placeholder and Import macros. Position and last tab are saved.
- **Minimap button** (`Minimap.lua`): logo icon, tooltip, left-click toggles the
  window, right-click menu (MenuUtil when the client has it, else our own menu
  frame; never UIDropDownMenu), drag around the rim (round and square minimaps),
  lock/hide from the menu, Settings or `/r2f minimap`. **No libraries embedded:**
  LibDataBroker-1.1 is "All Rights Reserved" with no reuse grant, and LibDBIcon
  can't load without it, so the button is our own; if another addon already loaded
  LibDBIcon, it's registered through that copy. Findings per library in
  `ADDON_PLAN.md` 6.10.
- **Logo:** hand-written `addon/art/logo.svg` (gold road curling into an infinity
  sign on a navy disc), exported by `addon/art/export_logo.py` (resvg + Pillow) to
  `media/logo64.tga` / `logo128.tga` (32-bit with alpha).
- Full slash-command set (`/r2f`, `/r2f macros`, `/r2f talents`, `/r2ft`,
  `/r2f minimap`, `/r2f help`, `/r2f import` kept); the three key bindings now open
  the main window's tabs.
- Tests: `addon/tests/run_tests.py` now 5655 checks (was 5346), new main-window,
  Home, reparented-book, minimap, menu, slash-command, LibDBIcon-backend and TGA
  cases on both template and fallback paths; luacheck 0 warnings. Decisions in
  `ADDON_PLAN.md` 6.10; in-game checks in `addon/RoadToForever/TESTING.md` 11.

## 2026-10-02 (Addon plan, step 5: Road to Forever addon v0.3.0, Settings, Remove all, key bindings)

- The Macro Book's **Settings** button opens a new panel (`UI/Settings.lua`):
  Character / Account slots first (`R2FDB.settings.slotsFirst`, steers every new
  `CreateMacro`, never moves existing macros), Show / Lock minimap button (stored in
  `R2FDB.minimap` in LibDBIcon's format for step 6, which must add
  `R2F.Minimap.Apply`), and **Remove all Road to Forever macros** (tag `r2f-v0.3.0`).
- **Remove all** deletes every unedited macro the addon made, on bars or not, in
  character and account slots, clears all created-macro tracking, keeps edited
  macros as the player's own (ADDON_PLAN 5.8; the step brief said "regardless of
  edited", the spec won, see 6.9) and leaves the library alone. Same combat rule as
  Tidy up: greyed out in combat, queued if accepted in combat.
- **Key bindings** via `Bindings.xml` (loaded by the client, deliberately not in the
  TOC): Toggle Road to Forever / Open Macros (both toggle the Macro Book for now),
  Open Talents (placeholder until steps 6/9).
- Tidy up re-checks "not on a bar" at delete time (a queued Tidy could otherwise
  delete a macro put on a bar meanwhile).
- Tests: `addon/tests/run_tests.py` now 5346 checks (was 5202), new Tidy-up slot,
  slotsFirst, Remove all, Settings UI, combat and Bindings.xml cases on both
  template and fallback paths; luacheck 0 warnings. Decisions in `ADDON_PLAN.md`
  6.9; in-game checks in `addon/RoadToForever/TESTING.md` 7, 9, 10.

## 2026-10-02 (Addon plan, step 4: Road to Forever addon v0.2.0, updates)

- Re-importing now updates real macros the addon already made, if the player
  hasn't edited them (`EditMacro`, same combat-checked/queued write path as every
  other macro write). Hand-edited macros are left alone, the library still takes
  the new version, and the import preview + chat say which were updated and which
  kept (tag `r2f-v0.2.0`).
- **Changed marker** in the Macro Book: a green up-arrow on macros on your bars
  that an import changed, cleared the first time you hover it (stored per
  character in `R2FCharDB.changed`).
- On login, a character's own unedited macros catch up with the shared library
  (an import on another character can't reach them). Dragging an older macro
  from the book updates it first.
- Tests: `addon/tests/run_tests.py` now 5202 checks (was 5131), new update /
  kept-edit / Changed-flag / combat-queue / login-sync cases; luacheck 0 warnings.
  Decisions in `ADDON_PLAN.md` 6.8; in-game checks in `addon/RoadToForever/TESTING.md` 8.

## 2026-10-02 (Addon plan, step 3: Road to Forever addon v0.1.0)

- New `addon/RoadToForever/`: the in-game addon's first version (tag
  `r2f-v0.1.0`). `/r2f` opens a spellbook-style **Macro Book** (Universal + own
  class tabs, 2 x 6 grid, tooltips, paging, slot counter); **Import** reads the
  site's `R2F1:` string with a new/updated/unchanged preview into an unlimited
  account-wide library; dragging or clicking a macro creates the real macro
  (character slots first) and puts it on the cursor, with a Replace / Keep mine
  popup when the name is taken; **Tidy up** deletes unused unedited macros the
  addon made. Nothing touches macros in combat. Addon details:
  `addon/RoadToForever/CHANGELOG.md`.
- Not run in the game yet: `addon/RoadToForever/TESTING.md` is the beta
  checklist (Interface number, templates, CreateMacro+PickupMacro, icons, relog,
  combat, paste speed).
- Out-of-game tests in `addon/tests/` (not shipped): real Lua 5.1 via `lupa`
  against a fake client, with import strings generated by the site's own
  `importString()` code (all 389 site macros round-trip into the addon), plus a
  luacheck run under the same Lua 5.1 (0 warnings). Build-time judgment calls
  are in `ADDON_PLAN.md` section 6.7.

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
