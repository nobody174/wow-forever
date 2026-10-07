# Road to Forever (addon) changelog

Version history of the in-game addon itself. The site's history is in the
repo's root `CHANGELOG.md`.

## 0.12.2 (2026-10-07): Export professions button on Home

- **Export professions** button on the Home tab, next to Import (same as `/r2f profs`
  and the Export button on the profession window). Owner's request after the first real
  exports worked: a button in the addon window instead of typing a command.

## 0.12.1 (2026-10-07): profession export on modern profession windows

- 0.12.0 showed no Export button and no "saved N recipes" line in game: WoW Forever runs
  on a modern client, so the Classic profession functions are probably missing. Now also
  reads the modern profession window (`C_TradeSkillUI`: recipe ids, `GetRecipeInfo`,
  `GetRecipeSchematic` basic reagents), listens to `TRADE_SKILL_LIST_UPDATE` /
  `TRADE_SKILL_DATA_SOURCE_CHANGED`, and puts the Export button on `ProfessionsFrame` too.
- `/r2f profs` reads the open window itself if nothing was saved yet.
- New `/r2f profdebug`: one chat block showing which profession functions and windows this
  client has, how many rows the open window has, and what's saved. Paste it to us if the
  export still doesn't work.

## 0.12.0 (2026-10-07): export your professions for the site

**Never run in game yet: TESTING.md 21.**

- **New: profession export** (ADDON_PLAN 14). Open a profession window (Enchanting,
  Leatherworking, Tailoring, First Aid, ...) and the addon saves every recipe this
  character knows, with skill level and each recipe's materials (item ids + counts).
  Chat says "saved N Enchanting recipes". An **Export** button sits on the profession
  window next to its close button; `/r2f profs` does the same. Both show one
  `R2FP1:` string to copy, for the site's Professions page (Crafters).
- Reads both the trade skill window and Classic's craft window (Enchanting); opens all
  headers and clears "Have materials" first so the list is complete.
- Base64 encoding added (the export string is plain base64, safe in chat and Discord).

## 0.11.0 (2026-10-03): free talent points on WoW Forever + one-click learning through C_Traits

**The new learning path has never run against a real WoW Forever server. Test it with
ONE point on a disposable character first (TESTING.md 20), never on a main's build.**
Full design, confidence levels and the "not verified" list: `ADDON_PLAN.md` 13.12.

- **Fix: free talent points said 0** while Blizzard's window showed "Unspent Talents:
  17" (real screenshot), so Learn talents stayed grey. The count now comes from
  `C_Traits.GetTreeCurrencyInfo` (applied points, staged changes excluded), with
  Classic's `UnitCharacterPoints` kept unchanged for Classic-era clients. One function
  for the whole addon (`Talents.FreePointsInfo`; the minimap tooltip, Home, the Talents
  tab and the learning engine all use it). When no API gives a usable answer the addon
  now says **"couldn't read"** (Talents tab, Home) instead of a misleading "No free
  talent points", and Learn stays disabled.
- **New: "traits" learning mode** (WoW Forever). Learn talents spends points itself:
  `C_Traits.PurchaseRank(configID, nodeID)` per point, then `C_Traits.CommitConfig`
  when the purchase turns out to be staged (like Blizzard's own Apply Changes), one
  point at a time. Same order, popup, `Learning X / N`, combat stop, Stop / resume and
  no-double-send rules as before. A point only counts when its applied rank went up
  AND the free points went down. Anything unexpected (refused, error, failed commit,
  unconfirmed point) stops the run and switches to the existing guided mode for the
  rest of the session. Your own un-applied changes in Blizzard's window are never
  committed: the run stops and asks you to apply or undo them first.
- Classic's direct mode and guided mode are unchanged.
- Tests: fake trait servers (staged + commit, immediate, async, no commit) and every
  failure case; free points from the currency (17 with the legacy call saying 0),
  Classic path, unknown. Suite: 10927 checks, 0 failed (9389 before); 22 of 23 hand
  mutations fail the suite (the 23rd is equivalent); luacheck 0 warnings.

## 0.10.5 (2026-10-03): fix — Paladin talents unreadable (position jitter)

Follow-up to 0.10.4's C_Traits reader, found by live testing: a dump of all 50
real nodes of a Paladin's talent tree showed Protection's first column at both
posX 5020 and 5030. That's a few units of jitter in Blizzard's own layout data
(real columns are 590-600 apart), but 0.10.4 counted it as a fifth Protection
column, refused the tree, and Preview / Copy my build said "couldn't read your
talents yet." Full analysis: `ADDON_PLAN.md` 13.11.

- **Fix:** positions that are much closer together than a grid step (under 20% of
  the median gap) count as one row/column before rows and columns are numbered.
  The step is measured from the data itself, so it works at any scale. It applies
  to columns and to rows. Real columns that are just a little closer together than
  usual stay separate.
- Nothing changes when there's no jitter (Holy, and every earlier test, read
  exactly as before).
- Tests: the real 13 posX values in a 50-node Paladin tree read as 4/4/4 columns
  (was 4/5/4 -> nil), link + hash equal to the site's `talentcalc.js`; plus
  synthetic row jitter, several jitter pairs, other grid scales, a too-aggressive
  tolerance caught, and a jitter-majority tree refused. Suite: 9389 checks, 0
  failed (9259 before); luacheck 0 warnings.
- Still to confirm in game (TESTING.md 19): 0.10.5 on the Paladin, other classes.

## 0.10.4 (2026-10-03): fix — read talents through C_Traits (corrects 0.10.3)

0.10.3's fix was wrong: it force-loaded `Blizzard_TalentUI`, but on WoW Forever
`LoadAddOn("Blizzard_TalentUI")` answers `false, "MISSING"` and the Classic talent
functions never exist. So Preview and Copy my build still said "couldn't read your
talents yet." WoW Forever keeps its talents in the trait system (`C_Traits`), the
same API WeakAuras Forever reads them with. Full evidence: `ADDON_PLAN.md` 13.10.

- **Fix:** `Talents.ReadTrees()` reads the active talent config through
  `C_SpecializationInfo` / `C_Traits` / `C_Spell`. Rows and columns come from the
  nodes' positions (ranked, so any scale works; checked against 8 real Paladin nodes
  and Wowhead's row/col for the same ids). The three panes (e.g. Holy / Protection /
  Retribution) are one trait tree on Forever, split by the gaps between columns.
  Same output shape as before, so links, the `~hash`, the preview and the learning
  order are unchanged. Every call is guarded: a missing or not-ready API means
  "couldn't read yet", never an error.
- **Learning is guided on WoW Forever.** `LearnTalent(tab, index)` addresses
  talents the Classic way, which this client doesn't have, so the addon no longer
  calls it unless Classic's `GetTalentInfo` confirms the exact talent at that
  address. On Forever, Learn talents names each talent to click in Blizzard's window
  and writes nothing itself.
- Talent tooltips use `GameTooltip:SetSpellByID`; `TRAIT_CONFIG_UPDATED` refreshes
  the Talents tab like `CHARACTER_POINTS_CHANGED`.
- Removed: the `Blizzard_TalentUI` force-load and its tests. The test stub now models
  `C_Traits` (and answers `MISSING` for `Blizzard_TalentUI`), plus a realistic
  Forever client with no Classic talent API at all.
- Suite: 9259 checks, 0 failed (8770 before); luacheck 0 warnings.
- Still to confirm in game (TESTING.md 19): every class other than Paladin, the
  Protection/Retribution positions, pending (un-applied) points.

## 0.10.3 (2026-10-02): fix — Talent Preview failed on a fresh login

> Superseded by 0.10.4: `Blizzard_TalentUI` turned out not to exist on WoW Forever.

Reported from real in-game testing: pasting a talent link and clicking Preview
always showed "couldn't read your talents yet. Try again in a moment," even
though the character genuinely had talent points spent. `/dump
GetNumTalentTabs()` confirmed the cause directly: the function doesn't exist
as a global until Blizzard's own on-demand `Blizzard_TalentUI` addon has
loaded, which normally only happens the first time the player opens the real
Talent window by hand — the addon never tried to make that happen itself, it
only checked whether it already had.

- **Fix:** `Talents.ReadTrees()` now force-loads `Blizzard_TalentUI` via
  `LoadAddOn` (tries `C_AddOns.LoadAddOn` first, falls back to the bare
  global, `pcall`-wrapped) before checking for the talent functions, so
  Preview and Copy my build work the first time without the player needing
  to open their Talent window separately first. A one-shot retry 0.5s later
  covers the (believed unlikely) case where the force-load succeeds but the
  data isn't queryable in the exact same tick.
- Found by reading a third-party addon (RXPGuides) already working on the
  same WoW Forever client — it already solved this exact problem for its own
  talent-related features, and separately already has a proven, working
  `LoadAddOn` call for a different on-demand Blizzard addon. See
  `ADDON_PLAN.md` 13.9 for the full investigation and reasoning.
- The Lua test stub (`wow_stubs.lua`) previously defined the talent functions
  as always-available globals — an inaccurate model of the real client that
  every prior talent test was unknowingly built against. Fixed to match
  reality: they're now genuinely load-on-demand in the stub too.
- Full suite re-run: 8770 checks, 0 failed (up from 8688), including new
  tests specifically covering the cold-login scenario, no-LoadAddOn-at-all,
  and a refused load — each confirmed to fail cleanly, no errors.

## 0.10.2 (2026-10-02): version/author footer on the Home tab (ADDON_PLAN.md 12.4.2)

**Requested from real in-game testing, 2026-10-02** — there was no way to see
the addon's version or who made it without opening the TOC file.

- A quiet line at the bottom of the Home tab reads the TOC's own `## Version:`
  / `## Author:` fields through `GetAddOnMetadata` (tries `C_AddOns` first,
  falls back to the bare global, never a second hardcoded copy that could
  drift out of sync): `Road to Forever v0.10.2 · by nobody174 ·
  nobody174.github.io/wow-forever`.
- If neither metadata API exists on this client, shows a plain line with no
  version instead of erroring.
- Hovering it shows the TOC's `## Notes:` text as a one-line "what is this."
- Full suite re-run: 8688 checks, 0 failed.

## 0.10.1 (2026-10-02): fix — character macro slot limit was wrong

Reported from real in-game testing: the Macro Book's Character counter should
read out of 30, not 18.

- **Fix:** `Macros.Limits()`'s fallback (used when the game doesn't define
  `MAX_CHARACTER_MACROS`, which WoW Forever's client doesn't) was hardcoded to
  the vanilla/Classic Era value, 18. The user counted WoW Forever's real
  `/macro` Character tab directly: **30** slots (5 rows of 6). Fixed the
  constant; no other logic changed, since everything already correctly reads
  through `Macros.Limits()` rather than hardcoding 18 anywhere else.
- Updated the Lua test stub (`wow_stubs.lua`) and every test assertion that
  checked the old 18/138 numbers to match. Full suite re-run: 8608 checks,
  0 failed.
- Account-wide limit (120) is unchanged and still unverified directly — only
  the per-character number was actually in question.

## 0.10.0 (2026-10-02): class picker, Remove from library asks first, Tidy up tooltip

**Requested from first real in-game testing, 2026-10-02** — not part of the original
build plan (steps 3 to 10 + Quick settings). On a Paladin, the tester imported Warrior
macros: chat said `imported 51 macros.`, but no Warrior tab ever appeared, because the
book only showed the class you're logged in as. Decisions in `ADDON_PLAN.md` 5.10. Not
tested in the game yet; see `TESTING.md` section 17.

- **Class picker in the Macro Book:** when your library has macros for another class, a
  row of class icons appears at the top of the book (your class first). Click one to
  look at that class's macros from any character, e.g. to prepare an alt.
- **Other classes are preview only:** their macros show grey, with tooltips, and
  Shift-click still puts them in chat, but they can't be dragged to your bars (a Warrior
  can't cast Paladin spells; the addon refuses and says `Log in on a Paladin character
  to use this macro.`). Universal macros keep working in every view.
- The slot counters and gold "on your bars" checks always describe the character you're
  playing; a note says so while you preview another class.
- The book remembers the class you picked while you play, and opens on your own class
  again after a relog or `/reload`.
- After an import, the book opens on your own class if the import brought anything new
  for it, otherwise on the imported class's preview.
- **Remove from library** (right-click a macro) now asks first. It only takes the macro
  out of your book: a macro you already made from it stays in the game and on your bars
  (Tidy up or Remove all can delete it later). Importing it again brings it back as new.
  Works on previewed classes too, so a class imported by mistake can be cleared out.
- **Tidy up has a tooltip** saying what it deletes (unedited Road to Forever macros that
  aren't on any bar) and that it never changes your library.

## 0.9.1 (2026-10-02): fix — addon wouldn't load at all

First real in-game install of 0.9.0 reported: addon shows in the list, no
minimap icon, `/r2f` does nothing, no Lua errors. Turned out the game flagged
it "Incompatible" (yellow) in the AddOns list and refused to load any of it —
so there was nothing to error, since nothing ever ran.

- **Fix:** `## Interface: 11507` was a Classic Era placeholder, never actually
  checked against a real WoW Forever client. The real value, confirmed via
  `/dump GetBuildInfo()` on a live Forever client, is **16001**
  (`version="1.60.1", build="70170", tocversion=16001`).
- No code changed — this is the TOC fix alone. Everything built in 0.1.0
  through 0.9.0 should now actually load for the first time.

## 0.9.0 (2026-10-02): Quick settings (ADDON_PLAN.md 12.4.1)

Not tested in the game yet; see `TESTING.md` section 16.

- **Quick settings on the Home tab:** three check boxes that change game settings
  directly, with no macro and no macro slot: **Max camera zoom** (zoom the camera out
  further; untick = the game's own default), **Hide guild names** and **Hide PvP
  titles**. They always show your game's current setting, also when you changed it
  some other way (`/console`, the game's options, another addon).
- **Not in combat:** the boxes grey out in combat and can't be changed until it ends.
- **The Macro Book no longer shows** the Zoom out more, Hide guild names and Hide PvP
  titles macros, since Quick settings does the same for free. A line on the Universal
  tab says so. They're still on the website for players without the addon, and a real
  macro you already made from one keeps working.
- If your game lacks one of these settings, its box is greyed out and its macro shows
  in the book again.

## 0.8.0 (2026-10-02): talent learning (ADDON_PLAN.md step 10)

Not tested in the game yet. **This version can learn talents, which only a trainer
reset undoes: do `TESTING.md` section 15 on a test character first.**

- **Learn talents works.** After a Preview with no red problems, click **Learn
  talents**: `Learn 21 talent points? Only a trainer reset can undo this.` [Learn]
  [Cancel]. The addon then learns exactly the gold `+N` points of the preview, one at a
  time, tier by tier, and checks each one against your game first (tier, prerequisite,
  free points, nothing else changed). The button counts `Learning 7 / 21`; the rest of
  the tab is locked and Cancel becomes **Stop**. Done: `Learned 21 talent points.` and
  the trees redraw.
- **It stops instead of guessing:** if the game doesn't take a point (`Stopped at
  Improved Thunder Clap: the game didn't accept the point. 14 of 21 learned.`), if you
  enter combat (`Stopped: you entered combat. 9 of 21 learned. Click Learn talents to
  continue.`), or if your talents change meanwhile. After combat or Stop, Learn talents
  continues where it stopped, without asking again.
- **Not in combat:** Learn talents is greyed out in combat; a popup accepted just as
  combat starts waits until combat ends.
- **Guided mode:** if the game doesn't let addons learn talents, the addon opens
  Blizzard's talent window instead and puts a pulsing gold glow on the next talent to
  click (`Click Cruelty (2 of 21)`). It never changes Blizzard's window.
- If the game turns out to have Blizzard's own talent preview, Learn talents fills that
  preview and you confirm with Blizzard's Learn button.

## 0.7.0 (2026-10-02): talent import preview (ADDON_PLAN.md step 9)

Not tested in the game yet; see `TESTING.md` section 14. **Nothing is learned yet:**
this version only shows what a build would do. Learning comes in the next version.

- **The Talents tab is real now** (`/r2ft`). Paste a link from the site's talent
  calculator (Copy link; a full URL, `talents.html#...`, `#...` or just
  `warrior/...` all work) and click **Preview**: three small talent trees show what
  you already have, what would be learned now (gold glow, `+2`), what has to wait for
  more points (`later`), what isn't in the build (grey), and any problem (red).
  Hover a talent for the game's own tooltip plus `Build: 3 / 3`.
- **A summary line** says how many points the build uses and how many you have free,
  e.g. `This build uses 21 points. You have 16 free: 16 will be learned now, 5
  later.`, or what's in the way (`You already have 2 points in Improved Rend, which
  this build doesn't use. Reset your talents at a trainer first.`).
- **Safety checks:** a link for another class is refused (`This is a Paladin build.
  You're playing a Warrior.`); a link whose check (`~xxxx`) doesn't match your game's
  talent trees is refused; an older link without a check gets a yellow warning; a
  link asking for more ranks than a talent has, or points in a talent your tree
  doesn't have, is shown as a problem. On a non-English game client links can't be
  checked (talent names are translated), so you get the yellow warning instead.
- **Copy my build** is a button on the Talents tab (`/r2f copybuild` still works).
- **Learn talents** is there but greyed out until the next version.
- The tab remembers the last link per character and updates live when you spend
  points or level up. Home's Talents entry shows your free talent points.
- Works in combat: previewing only reads your talents.

## 0.6.0 (2026-10-02): Copy my build (ADDON_PLAN.md step 8)

Not tested in the game yet; see `TESTING.md` section 13.

- **`/r2f copybuild`** reads your current talents and shows them as a link to the
  Road to Forever talent calculator, already selected: press Ctrl+C and paste it in
  your browser or Discord. The link opens the site's calculator with your build.
  It only reads your talents (it never learns or changes anything), so it also
  works in combat.
- Links end in a short check (`~` and 4 characters) made from your class's talent
  names. The site's links now carry the same check, so the next version can warn you
  when a link was made with different talent trees than your game has.
- The Talents tab still has its placeholder; it now mentions `/r2f copybuild`. The
  Talents tab's own Copy my build button comes with the talent import version.
- `/r2f help` lists the new command.

## 0.5.0 (2026-10-02): first downloadable release (ADDON_PLAN.md step 7)

No change to what the addon does in the game: same code as 0.4.0. This is the
first version you can download as a zip instead of copying the folder from the
repository. Not tested in the game yet; see `TESTING.md`.

- **Download:** `RoadToForever-0.5.0.zip` on the GitHub Releases page (linked from
  the Macros page's "How to import" steps). Unzip it into your game's
  `Interface\AddOns\` folder; it contains one `RoadToForever` folder.
- Marked as a **pre-release** on GitHub, like every 0.x version, because nothing
  has been checked in the real game client yet.

## 0.4.0 (2026-10-02): main window, minimap button, logo (ADDON_PLAN.md step 6)

Not tested in the game yet; see `TESTING.md` section 11.

- **One window with three tabs** at the bottom: **Home**, **Macros** and
  **Talents**. The Macro Book is now the Macros tab (same book, same buttons),
  and the window has the Road to Forever logo as its portrait. It remembers where
  you put it and which tab you used last.
- **Home** shows how many macros are in your library and how many are on your
  bars, a Talents entry (coming in a later version), and an **Import macros**
  button. Click an entry to go to that tab.
- **Minimap button** with the logo: left-click opens/closes the window, right-click
  opens a menu (Open Road to Forever, Macros, Talents, Lock button position, Hide
  minimap button), drag it around the minimap. The tooltip shows your library
  count (and free talent points, if any). The Show / Lock minimap button settings
  now work. If you have another addon that uses LibDBIcon, the button goes through
  it, so minimap-button collector addons see it too.
- **Slash commands:** `/r2f` (window, last tab), `/r2f macros`, `/r2f talents` or
  `/r2ft`, `/r2f minimap` (hide/show the button), `/r2f import`, `/r2f help`.
- **Key bindings:** Toggle Road to Forever opens the window on your last tab;
  Open Macros / Open Talents open (or close) that tab.
- The Talents tab is a placeholder until the talent versions.

## 0.3.0 (2026-10-02): Settings, Remove all, key bindings (ADDON_PLAN.md step 5)

Not tested in the game yet; see `TESTING.md` sections 7, 9 and 10.

- **Settings** button in the Macro Book now works. It opens a small panel:
  - **New macros go to:** Character slots first / Account slots first. Only for
    macros made from then on; macros you already have stay where they are.
  - **Show minimap button / Lock minimap button**: saved now, used once the
    minimap button arrives (next version).
  - **Remove all Road to Forever macros**: after a confirm listing them, deletes
    every macro the addon made that you haven't edited, also ones on your action
    bars, in character and account slots. Macros you edited are kept as your own.
    Your macro library is not touched, so you can drag them out again. Greyed out
    in combat; if you accept it in combat, it runs when combat ends.
- **Key bindings** (Key Bindings menu, "Road to Forever"): Toggle Road to Forever
  and Open Macros open/close the Macro Book; Open Talents is a placeholder until
  the Talents window exists.
- **Tidy up** checks again, right when it deletes, that each macro is still not on
  a bar (matters when you accepted it in combat and it ran afterwards). Long name
  lists in popups are shortened (`... and 12 more`).

## 0.2.0 (2026-10-02): updates and Changed markers (ADDON_PLAN.md step 4)

Not tested in the game yet; see `TESTING.md` section 8.

- **Re-importing updates your macros.** When an import changes a macro you
  already made in the game, and you haven't edited it, the real macro gets the
  new text (and icon) right away. The preview says so before you click Import
  (`2 macros you already made in the game will be updated too.`), and chat
  confirms it afterwards.
- **Your edits are kept.** If you changed one of these macros yourself, it's left
  exactly as it is; the preview and chat say which ones (`kept your edits to HS`),
  and the library still has the new version: drag it from the book and choose
  Replace if you want it.
- **Changed marker:** a small green up-arrow on the macro's icon in the Macro Book
  when an import changed a macro that's on your action bars. Hover it to see what
  changed; the arrow goes away once you've seen it. Kept-edited macros on your bars
  get the arrow too, with a tooltip explaining your version was kept.
- **Other characters catch up on login.** The library is shared by all your
  characters, so macros you made on another character are brought up to date the
  next time you log in on it (only unedited ones). Dragging an older macro from the
  book also updates it first.
- In combat, these updates wait until combat ends (one chat line says so), and are
  checked again then, so anything you edited meanwhile is still left alone.
- The Import window is a little taller so the longer preview fits.

## 0.1.0 (2026-10-02): first version, Macro Book MVP (ADDON_PLAN.md step 3)

Not tested in the game yet; see `TESTING.md` for the beta checklist.

- `/r2f` opens the **Macro Book**, a spellbook-style window: side tabs for
  Universal and your class's sections, 2 x 6 macros per page, short names with
  the group underneath, the spell's icon (desaturated `Learn later` for spells
  you don't know yet), full tooltip (name, short name, body, note), page buttons,
  slot counter (`Character x / 18`, `Account y / 120`, red when full).
- **Import** window: paste the string from the site's "Copy import string",
  preview (`N macros: x new, y updated, z unchanged`, other-class and skipped
  counts), Import. The library is saved account-wide and has no size limit;
  every class's macros are kept.
- **Drag or click** a macro to create the real macro and put it on your cursor.
  Character slots first, account slots when those are full. Already created =
  just picked up again. A macro with the same name that isn't ours, or ours
  after you edited it, asks `Replace it?` [Replace] [Keep mine].
- **Tidy up** deletes Road to Forever macros that aren't on any action bar and
  that you haven't edited (with a confirm listing them).
- Right-click a macro: Remove from library, Copy text. Shift-click: body in chat.
- Combat-safe: no macro is created, edited, deleted or picked up in combat;
  Import / Tidy up grey out with `In combat`; a Tidy up confirmed in combat runs
  when combat ends.
- Settings (step 5), re-import updates of existing macros (step 4) and the main
  window + minimap button (step 6) are not in this version.
