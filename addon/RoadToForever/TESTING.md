# Road to Forever: in-game test checklist (v0.10.0, addon steps 3 to 10 + Quick settings + class picker)

Since v0.4.0 the Macro Book is the **Macros tab** of the main window: wherever an
older section below says "`/r2f` opens the Macro Book" or "open the book", use
`/r2f macros` (plain `/r2f` opens the tab you used last, Home the first time).

Nothing in this addon has run in the real WoW client yet. Out of the game it was
tested under real Lua 5.1 against a fake client (`addon/tests/`), which checks
logic, not the client. This list covers what only the game can confirm
(`ADDON_PLAN.md` section 11). Tick each item in the beta, and fix
`ADDON_PLAN.md` + the code in the same commit if something turns out different.

**Setup:** from v0.5.0 on, download `RoadToForever-<version>.zip` from the repo's
GitHub Releases and unzip it into the AddOns folder below (section 12 checks the
zip itself). Or copy `addon/RoadToForever/` into `World of Warcraft\_classic_era_\Interface\AddOns\`
(or the Forever client's AddOns folder), start the game, enable "Road to Forever"
on the character screen. Turn Lua errors on: `/console scriptErrors 1`.

## 1. Loads at all

- [x] **Interface number.** Confirmed 2026-10-02: `## Interface: 16001` (this
      client's `GetBuildInfo()` returns `tocversion=16001`). The original
      placeholder (`11507`, Classic Era) made the game show the addon as
      "Incompatible" (yellow) and refuse to load it at all — no Lua error,
      since nothing ever ran. Shipped as v0.9.1. If `select(4, GetBuildInfo())`
      comes back empty on your client, use a plain `/dump GetBuildInfo()`
      instead and read the 4th value from the full dump.
- [ ] Log in. **Pass:** no Lua error. `/r2f` opens the main window (Home). `/r2f help`
      prints the command list.
- [ ] `/dump R2F` shows a table; `/dump R2FDB.version` shows `1`.

## 2. Templates exist (section 11)

The addon tries each template and falls back if it's missing, so check which one
you got:

- [ ] **PortraitFrameTemplate.** `/dump R2FMain ~= nil` (v0.4.0; before that the book
      was `R2FMacroBook`). **Pass:** `true` and the window has the round logo portrait
      top left, a gold title "Road to Forever" and an X button. If `R2FMainB` exists
      instead, the client only had `ButtonFrameTemplate`; if `R2FMainPlain`, neither
      (plain dialog border, no portrait). Fallbacks work but look less native: note
      which one in ADDON_PLAN 11.
- [ ] **InputScrollFrameTemplate.** Click Import. `/dump R2FImportScroll ~= nil`.
      **Pass:** `true`, the box scrolls, no Lua error when the window opens (watch for
      a `SetMaxLetters` error from the template's OnLoad). `R2FImportScrollPlain`
      means the fallback scroll box was used.
- [ ] Spellbook textures render: side tabs use `SpellBook-SkillLineTab`, page buttons
      `UI-SpellbookIcon-Next/PrevPage-*`, slots `UI-Quickslot2`. **Pass:** no green
      squares (missing texture).
- [ ] Esc closes the Macro Book, the Import window, and the Replace popup.

## 3. Import

- [ ] On the site (macros.html), Pick macros for the game, Select all for your
      class, Copy import string. In game: `/r2f`, Import, Ctrl+V.
      **Pass:** preview line like `66 macros: 66 new, 0 updated, 0 unchanged.`
      appears within about a second; Import is enabled.
- [ ] **Paste speed (section 11).** Paste a 20 KB string (one class + Universal is
      10 to 16 KB), then the ~83 KB "Select everything" string. **Pass:** the game
      doesn't freeze for more than about a second. If it does: note the time; the
      fallback is LibDeflate compression with an `R2F2:` prefix (ADDON_PLAN 7).
- [ ] Click Import. **Pass:** window closes, chat says
      `Road to Forever: imported 66 macros.`, the book opens on the first tab with
      new macros.
- [ ] Paste `hello`. **Pass:** red `That isn't a Road to Forever import string...`,
      Import disabled.
- [ ] Re-import the same string. **Pass:** `... 0 new, 0 updated, 66 unchanged.`
- [ ] Import "Select everything" on a Warrior. **Pass:** preview mentions
      `... are for another class and will be kept for those characters.`; the
      Universal tab shows `You also have macros for Hunter (..), Mage (..), ...`
      (since v0.10.0 the book also shows the class picker row: section 17).

## 4. Macro Book

- [ ] Tabs on the right edge: Universal (book icon), then your class's sections in
      site order (Warrior: General = class icon, Tank = shield, DPS = dual wield).
      Hover a tab: section name + `N macros`.
- [ ] 2 x 6 grid, short names in gold, group in grey under each (`Damage`, `Panic`...).
      Page buttons and `Page 1 of N` work; page-turn sound plays.
- [ ] Hover a macro: full name (white), short name (gold), body (grey), note (blue),
      `Drag to an action bar.` (green).
- [ ] Spells you don't know yet show desaturated with `Learn later`. Learn one at a
      trainer with the book open. **Pass:** it turns to full colour.
- [x] Slot counter `Character x / 30` and `Account y / 120` match `/macro`. Turns red
      when full. **Limits confirmed 2026-10-02: 120 + 30, not Classic Era's 18
      (section 11) — `MAX_CHARACTER_MACROS` is nil on this client; counted the
      real `/macro` Character tab directly (5 rows of 6).**
- [ ] Shift-click a macro with the chat box open: the body appears in one line.
- [ ] Right-click: menu with `Remove from library` / `Copy text`. Copy text opens a
      box with the body highlighted; Ctrl+C works. (Remove from library asks first
      since v0.10.0: section 17.)

## 5. Creating real macros (the important part)

- [ ] **CreateMacro + PickupMacro in the same click (section 11).** Drag `VR` (or any
      macro) from the book. **Pass:** the macro is on your cursor right away and
      drops onto an action bar. Also try a plain left-click. If the cursor stays
      empty but `/macro` shows the new macro, the next-frame retry should still pick
      it up; if not, note it (the fix is a `C_Timer.After(0, ...)` before
      `PickupMacro`, already the fallback path in `Macros.Create`).
- [ ] If both a drag and a click fire for one drag (OnClick after OnDragStart), you'd
      see nothing wrong (the second pick-up is the same macro). Just note it.
- [ ] **Question-mark icon becomes the spell icon (section 11).** The new macro on the
      bar shows the spell's icon (e.g. Victory Rush), not a red question mark.
      `/macro` shows it in the character tab with the question-mark icon chosen.
- [ ] Icon macros (e.g. pet attack, `/use` macros) show their own icon.
- [ ] `/macro`: the new macro's name is the short name (`VR`), body matches the site.
- [ ] Drag the same macro again. **Pass:** no second macro is created.
- [ ] Edit that macro's body in `/macro`, then drag it from the book again.
      **Pass:** popup `You already have a macro called "VR". Replace it?`;
      Keep mine leaves your edit; Replace restores the site version and puts it on
      the cursor.
- [ ] Make your own macro named like one of ours (e.g. `HS`) with a different body,
      then drag `HS` from the book. **Pass:** the same popup.
- [ ] Fill all 30 character slots, drag a new one. **Pass:** it goes to an account
      slot. Fill both. **Pass:** red `No free macro slots. Click Tidy up or delete a macro in /macro.`
- [ ] **Survives a relog (section 11).** Create 2 macros, put them on bars, log out
      fully and back in (and `/reload`). **Pass:** they're still in `/macro` and on
      the bars; dragging them again from the book picks up the same macros (no
      duplicates, no popup), proving the stored hash still matches after the
      server round trip.
- [ ] On-your-bars marker: a small gold check on the icon in the book for macros
      that are on an action bar; it goes away when you remove it from the bar.

## 6. Combat (section 6.4 / 6.6)

- [ ] Open the book, attack a training dummy or a mob. **Pass:** `In combat` appears
      at the bottom, Import and Tidy up grey out immediately.
- [ ] Drag a macro from the book in combat. **Pass:** red
      `You can't create macros in combat.`, nothing on the cursor, no Lua error, no
      "action blocked" message.
- [ ] Leave combat. **Pass:** buttons come back.
- [ ] Open Tidy up's confirm, then enter combat and click Delete. **Pass:** chat says
      it will finish after combat; after combat the macros are deleted.
- [ ] `/console taintLog 1`, play for a while with the book open, `/reload`, check
      `Logs\taint.log` for `RoadToForever`. **Pass:** no entries blaming the addon.

## 7. Tidy up

- [ ] Create 3 macros from the book, put 1 on a bar, edit 1 in `/macro`. Tidy up.
      **Pass:** the popup lists only the one that's unedited and not on a bar
      (plus the note about bar addons); Delete removes it, your other macros stay.
- [ ] Put one of our macros on a stance / stealth bar page (Warrior stance bar,
      Rogue stealth bar: action slots 73-120), not on the main bar. Tidy up.
      **Pass:** it is NOT offered (those slots are read too).
- [ ] **Bar addons (known limit).** With Bartender / Dominos / ElvUI, macros on their
      bars are normally seen (they use the same action slots). A bar addon that draws
      its own buttons outside slots 1-120 (rare) isn't seen, so Tidy up would offer
      those macros; the popup warns about it. Note any bar addon where this happens.
- [ ] Open Tidy up's popup, drag one of the listed macros onto a bar from `/macro`,
      then click Delete. **Pass:** that one is kept (re-checked at delete time).

## 8. Updates and Changed markers (v0.2.0, step 4)

Out of the game, `addon/tests/run_tests.py` covers the logic (which macros get
`EditMacro`, edited ones left alone, the flag set and cleared, the combat queue,
the login sync) against the fake client. What only the game can show:

Setup (a Warrior; use any three of your macros on another class). The site's
string only changes after a site update, so fake an "older version" first:
1. Import your class + Universal from the site. Don't drag anything yet.
2. Make three library entries older than the site, e.g.
   `/run for _, k in ipairs({"VR","HS","Rend"}) do local e = R2FDB.library["WARRIOR/"..k] e.body = e.body .. "\n/say old" end`
3. `/r2f`, drag `VR`, `HS` and `Rend` out (they're created with the `/say old` line).
   Put `VR` and `HS` on action bars; leave `Rend` off the bars.
4. In `/macro`, edit `HS`'s body (anything).
5. Copy the same import string from the site again. Compared with step 2 it is
   an update for those three.

- [ ] Paste it. **Pass:** under the counts line (`... 3 updated ...`), a second line
      `2 macros you already made in the game will be updated too. 1 you edited yourself
      will be left as it is.` The text fits above the buttons (window is 340 px tall).
- [ ] Click Import. **Pass:** chat `updated 2 of your macros to the new version.` and
      `kept your edits to HS. ...`; `/macro` shows `VR` and `Rend` without the
      `/say old` line, your edit on `HS` unchanged; the bar buttons still work (no
      "action blocked").
- [ ] **Arrow texture (unverified).** In the book, `VR` and `HS` (on bars) have a small
      green up-arrow at the top-left of the icon; `Rend` (not on a bar) doesn't.
      **Pass:** it reads as a small green up-arrow, not a green square (missing
      texture) and not a whole round button. The texture is
      `Interface\Buttons\UI-ScrollBar-ScrollUpButton-Up`, cropped with
      `SetTexCoord(0.2, 0.8, 0.2, 0.8)` and tinted with `SetVertexColor`; adjust the
      crop in `UI/MacroBook.lua` `buildSlot` if it looks off, and note it in ADDON_PLAN 6.8.
- [ ] Hover `VR`. **Pass:** tooltip line `Updated by your last import.` (green); the arrow
      disappears. Hover `HS`: orange line about your edit being kept. Close and reopen
      the book, `/reload`: arrows stay gone.
- [ ] Arrows survive a `/reload` before you hover them (stored in `R2FCharDB.changed`).
- [ ] **Combat.** Out of combat this can't be reached through the UI (Import is greyed
      out in combat). If you can, `/reload` while in combat on a character whose
      macros are behind the library (next item). **Pass:** chat says the update waits
      for combat; after combat the macro is updated; no Lua error, no blocked action.
- [ ] **Login sync (unverified: are macros readable at `PLAYER_LOGIN`?).** On
      character A, do setup steps 2 and 3 for one macro (character slot), log out.
      On character B, re-import the site string (puts the library back to the site
      version), log back in on A. **Pass:** chat
      `updated 1 of your macros to the version in your library.` and `/macro` shows the
      new body. If nothing happens, the game hadn't loaded macros yet at
      `PLAYER_LOGIN`: note it; dragging the macro from the book still updates it
      first (Ensure), and the fix is to run the sync on `UPDATE_MACROS` /
      `PLAYER_ENTERING_WORLD` instead.
- [ ] `/console taintLog 1` during the above, then check `Logs\taint.log`. **Pass:** no
      entries blaming RoadToForever (the login sync calls `EditMacro` from an event
      handler, not a click).

## 9. Settings and Remove all (v0.3.0, step 5)

Out of the game, `run_tests.py` covers the logic (the setting steering
`CreateMacro`, Remove all's delete/keep split, tracking cleared, library kept,
combat refusal + queue) on both the template and fallback UI paths. What only the
game can show:

- [ ] Click **Settings** at the bottom right of the book. **Pass:** a small panel
      "Settings" opens with: `New macros go to:` and two round radio buttons
      (Character slots first selected), a grey note under them, two square check
      boxes (Show minimap button ticked, Lock minimap button unticked) and a wide
      `Remove all Road to Forever macros` button. No green squares; nothing overlaps.
      If the radios look like square check boxes, `UIRadioButtonTemplate` is missing
      in this client (the fallback was used): note it in ADDON_PLAN 11.
- [ ] Clicking a radio's or check box's **label text** also toggles it.
- [ ] Choose **Account slots first**, drag a new macro from the book. **Pass:** `/macro`
      shows it in the General (account) tab, and the book's `Account` count went up.
      Switch back to Character first: the next new macro goes to the character tab,
      and the first one stays where it was.
- [ ] Tick/untick the minimap boxes, `/reload`, reopen Settings. **Pass:** the boxes
      remember (`/dump R2FDB.minimap` shows `hide` / `lock`). Since v0.4.0 the minimap
      button follows them at once (section 11).
- [ ] Esc closes the Settings panel; the X button closes it; the Settings button
      opens and closes it.
- [ ] **Remove all.** Make 4 macros from the book: 2 on bars, 1 not, 1 edited in
      `/macro`; also have a macro of your own. Click Remove all. **Pass:** popup
      `Delete 3 Road to Forever macros from the game, including any on your action
      bars?`, the 3 names, `Kept: <edited one>. You edited them...`, and
      `Your macro library stays...`. Click Remove. **Pass:** the 3 are gone from
      `/macro` (their bar buttons are empty), the edited one and your own macro stay,
      chat `removed 3 Road to Forever macros. Your macro library is unchanged. Kept 1
      you edited as your own.` The book still lists every macro; dragging one creates
      it again. Dragging the kept edited one asks Replace / Keep mine.
- [ ] The popup grows with its text and stays on screen with many macros (lists cut
      after 20 names: `... and 12 more`).
- [ ] **Combat.** With Settings open, enter combat. **Pass:** Remove all greys out
      (the radios and boxes still work). Open the Remove all popup before combat,
      accept it in combat. **Pass:** chat says it finishes after combat; after combat
      the macros are deleted; no Lua error, no "action blocked".
- [ ] `/console taintLog 1`, use Settings and Remove all, `/reload`, check
      `Logs\taint.log`. **Pass:** no entries blaming RoadToForever.

## 10. Key bindings (v0.3.0, step 5)

Not testable outside the game at all: the tests only check that `Bindings.xml` is
valid XML, each binding calls a real function and the label globals exist.

- [ ] **Bindings.xml loads without a TOC entry** (it's deliberately not listed).
      Esc > Options > Key Bindings (or the Key Bindings menu in this client).
      **Pass:** a `Road to Forever` header with `Toggle Road to Forever`,
      `Open Macros`, `Open Talents`. Note where it shows: under an AddOns section
      (`category="ADDONS"` worked) or elsewhere (e.g. at the bottom / "Other"). If the
      header is missing entirely, check for an XML error on login and note it.
- [ ] Bind a key to each. **Pass (v0.4.0):** Toggle opens and closes the main window
      on the tab used last; Open Macros opens it on the Macros tab and closes it when
      pressed again on that tab; Open Talents does the same with the Talents tab
      (placeholder text until the talent versions).
- [ ] Press Toggle in combat. **Pass:** the window opens (In combat shown on the
      Macros tab), no "action blocked", no Lua error.
- [ ] Bindings survive a `/reload` and a relog.

## 11. Main window, minimap button, logo (v0.4.0, step 6)

Out of the game, `run_tests.py` covers tab switching, the saved last tab and
position, the Home counts, the reparented book (slots, tabs, drag, tooltip,
paging, menu), every slash command and binding, `R2F.Minimap.Apply`, drag angles,
square minimaps, the tooltip lines, both menu paths (`MenuUtil` and our own), a
fake LibDBIcon, and the TGA headers. Looks and the real client APIs are only
checkable here.

- [ ] **Main window.** `/r2f`. **Pass:** the window opens on **Home**, with the
      round **logo** as portrait (not a green square: the TGA loaded), title
      `Road to Forever`, three tabs **under** the window (Home / Macros / Talents)
      in the character-frame tab style, Home selected. `/dump R2FMainTab1.r2fTemplate`
      says which tab template was used (`PanelTabButtonTemplate`,
      `CharacterFrameTabButtonTemplate`, or `UIPanelButtonTemplate` = fallback).
      Note it in ADDON_PLAN 11; if the tabs overlap badly or have gaps, adjust the
      `gap` values in `UI/MainWindow.lua` `TAB_TEMPLATES`.
- [ ] **Tabs.** Click Macros: the title becomes `Road to Forever: Macros` and the
      Macro Book shows exactly as before (side tabs on the right edge, grid, bottom
      bar). Click Talents: the Talents tab (since v0.7.0 the real tab, section 14).
      A tab sound plays on switching.
- [ ] **Home.** `N macros in your library, M on your bars` matches: N = your whole
      library, M = Road to Forever macros on your action bars. Put one more on a bar
      with Home open: M goes up within a moment. Click the Macro Book entry: Macros
      tab. Click Talents: Talents tab. **Import macros** opens the Import window
      (greyed out in combat). Since v0.7.0 the Talents entry reads `5 free talent
      points` / `No free talent points` (section 14).
- [ ] **Remembered.** Drag the window somewhere, switch to Macros, close it,
      `/reload`, `/r2f`. **Pass:** same spot, Macros tab.
- [ ] Esc closes the window. Spellbook open/close sounds play.
- [ ] **Minimap button.** A round button with the logo on the minimap rim
      (bottom-left at first). **Pass:** it looks like other minimap buttons (gold
      ring, dark background), the road and the infinity sign are recognisable at
      that size (12.1: "check it in-game at the real size"). If not, note what's
      unreadable; the source is `addon/art/logo.svg`, re-export with
      `py -3.12 addon/art/export_logo.py`.
- [ ] Hover it: `Road to Forever` (gold), `N macros in your library` (white),
      `Left-click to open.`, `Right-click for options.`, `Drag to move.` (green).
      With unspent talent points, `5 free talent points` too (checks
      `UnitCharacterPoints` exists in Forever).
- [ ] Left-click opens/closes the window on the last tab.
- [ ] **Drag** it around the minimap: it follows the rim smoothly. `/reload`:
      **Pass:** it's where you left it. With a square-minimap addon, it follows the
      square edge.
- [ ] **Right-click menu (section 11 of the plan: which menu API).**
      `/dump MenuUtil ~= nil`: `true` = Blizzard's menu is used, `false` = our own
      small menu. Either way: gold title `Road to Forever` (not clickable), Open
      Road to Forever, Macros, Talents, a divider, `Lock button position` with a
      check mark state, `Hide minimap button`. Each item does what it says; after
      Lock, dragging does nothing and the tooltip has no `Drag to move.`; Hide
      prints `Road to Forever: minimap button hidden. Type /r2f minimap to show it
      again.` Note which menu API it was in ADDON_PLAN 11.
- [ ] `/r2f minimap` shows it again (chat `minimap button shown.`); again hides it.
      Settings' Show/Lock boxes follow menu and slash-command changes while open.
- [ ] **With another addon that embeds LibDBIcon** (e.g. one with its own minimap
      button) enabled: `/dump R2F.Minimap.backend` says `libdbicon` and the button
      works the same (drag, menu, tooltip, hide/lock); without such an addon it
      says `own`. A minimap-button collector addon picks the button up in either
      case or at least in `libdbicon` mode; note which.
- [ ] **Slash commands:** `/r2f macros`, `/r2f talents`, `/r2ft`, `/r2f import`,
      `/r2f help` (prints 8 lines since v0.6.0), `/r2f nonsense` (prints `unknown command`).
- [ ] `/console taintLog 1`, use the window, tabs, minimap drag and menu (also in
      combat: open/close the window, open the menu), `/reload`, check
      `Logs\taint.log`. **Pass:** no entries blaming RoadToForever.

## 12. The release zip (v0.5.0, step 7)

The release workflow (`.github/workflows/release.yml`) only runs on GitHub's
servers, on a pushed `r2f-v*` tag; nothing on a PC can run it. Out of GitHub, the
workflow's own `git archive` command was run locally and the zip checked (top
folder `RoadToForever/`, TOC inside, no `addon/tests` or `addon/art`, every `.lua`
parses under Lua 5.1), and the YAML parsed. Whether the workflow publishes
correctly is only known from a real tag push (ADDON_PLAN.md 8.1). **v0.5.0, the
first run (2026-10-02):** green; release `Road to Forever 0.5.0`, pre-release,
notes from CHANGELOG, one asset; the downloaded zip is byte-for-byte the same 19
files as the local build. The in-game unzip check below is still open. Check each
new release once:

- [ ] The tag's run (repo > Actions > "Release addon") is green.
- [ ] The release is named `Road to Forever <version>`, is marked **Pre-release**
      for 0.x (a normal release from 1.0.0), its notes are that version's section
      of this folder's `CHANGELOG.md`, and it has exactly one asset,
      `RoadToForever-<version>.zip`.
- [ ] The Macros page's "How to import" Download link opens the Releases page with
      that release on top.
- [ ] Unzip it into `Interface\AddOns\`. **Pass:** you get
      `Interface\AddOns\RoadToForever\RoadToForever.toc` (not a nested
      `RoadToForever\RoadToForever\` or `addon\RoadToForever\`), and the AddOns list
      on the character screen shows Road to Forever.

## 13. Copy my build and the `~hash` (v0.6.0, step 8)

Out of the game, `run_tests.py` runs `Talents.lua` (Lua 5.1, fake `GetTalentInfo`)
and the site's real `talentcalc.js` (Node) on the same talent fixture and requires
the same `~hash` and the same link for 7 builds; it also covers the sort, the
encoder, the copy box, combat and a missing talent API. During step 8 the hash and
one link per class also matched on Wowhead's live Forever data for all 9 classes.
What only the game can show is whether the **game's** talent data agrees with the
site's (ADDON_PLAN 11, 13.6):

- [x] ~~**API shape.** `/dump GetNumTalentTabs(), ...`~~ Answered 2026-10-02: those
      globals don't exist on WoW Forever, and `Blizzard_TalentUI` is `MISSING`.
      Talents are read through `C_Traits` since v0.10.4 (ADDON_PLAN 13.10).
- [ ] **C_Traits read (v0.10.4, ADDON_PLAN 13.10), on a Paladin first.** Fresh
      login, Talents tab, Preview your own `/r2f copybuild` link. **Pass:** no
      "couldn't read your talents yet"; the three mini trees show Holy / Protection /
      Retribution content in that order (left to right), each talent in the same row
      and column as in Blizzard's Talents window, rank badges matching your real
      points. Then the same on every other class you can log in with: the pane split
      (by X gaps) and the row/column ranking are only proven on Paladin's Holy pane.
      Wrong pane contents or order = note the class and run
      `/dump C_Traits.GetConfigInfo(C_SpecializationInfo.GetCombatConfigIDForSpecGroup(C_SpecializationInfo.GetActiveSpecGroup())).treeIDs`.
- [ ] **Applied vs pending points (13.10).** Click a talent in Blizzard's window but
      don't Apply Changes yet, then `/r2f copybuild`. Note whether the link includes
      the pending point (it reads `activeRank`); then Apply and check again.
- [ ] **Copy my build.** Spend a few talent points (or use a character that has
      some). `/r2f copybuild`. **Pass:** a small box with the hint
      `Press Ctrl+C, then paste it in your browser or Discord.` and a link like
      `https://nobody174.github.io/wow-forever-macros/talents.html#warrior/05302~xxxx`,
      already selected. Ctrl+C, paste it into a browser. **Pass:** the site's talent
      calculator opens on your class with **exactly the talents you have in the game**
      (same talents, same ranks, same trees). If points sit on different talents, the
      tier/column sort or the tab order differs from the site's (ADDON_PLAN 11).
- [ ] **The hash matches the site (the key check).** On the site, set the same build
      by hand (or just open the pasted link and click one talent on and off), click
      **Copy link**. **Pass:** the 4 characters after `~` are the same as in the
      addon's link. Different = the game's talent names/order differ from Wowhead's
      Forever data (a missing or renamed talent, like Paladin's Crusade): note the
      class, and expect step 9 to refuse imports for that class until the site's data
      matches. Repeat for every class you can log in with (each class has its own
      hash). A non-English client always differs (names are translated; ADDON_PLAN
      13.6), so do this check on an English client.
- [ ] With **no talent points** spent: `/r2f copybuild` gives `...#warrior/~xxxx` and
      the site opens an empty Warrior calculator.
- [ ] **Combat.** `/r2f copybuild` in combat. **Pass:** the box opens, no
      "action blocked", no Lua error (it only reads).
- [ ] Right-click > Copy text in the Macro Book afterwards still shows its own hint
      (`Press Ctrl+C to copy, then Esc.`).

## 14. Talent import preview (v0.7.0, step 9)

Out of the game, `run_tests.py` parses every link the site's real `talentcalc.js`
makes for the fixture builds and previews each one as exactly that build, checks
the hash rules, the sanity checks, every summary sentence, the per-talent states
and the tab's widgets, on both the template and fallback paths, and proves nothing
learns a talent (the fake `LearnTalent` raises; the source has no call to it).
What only the game can show:

- [ ] **The tab.** `/r2ft`. **Pass:** `Talent link` + a text box with a grey
      `talents.html#<your class>/...` placeholder, `Preview`, `Copy my build`, three
      mini trees with your current talents (rank numbers on learned ones), tree names
      above them (`Arms`, `Fury`, `Protection` for a Warrior). If the names read
      `Tree 1..3`, `GetTalentTabInfo` has another shape: `/dump GetTalentTabInfo(1)`
      and note it in ADDON_PLAN 13.7. `Cancel` and `Learn talents` are greyed out.
      `/dump R2FTalentLink ~= nil`: `true` = `InputBoxTemplate` exists; `false` (and
      `R2FTalentLinkPlain` exists) = the plain fallback box.
- [ ] **Preview a site link.** On the site's talent calculator make a small build for
      your class (fewer points than you have free), Copy link, paste it in the box
      (Ctrl+V), click Preview (or Enter). **Pass:** gold glow and gold `+N` on exactly
      the talents of the build, no Lua error, and `This build uses N points. You have M
      free. All N will be learned.` Nothing changes in Blizzard's talent window
      (preview only).
- [ ] **More points than you have.** A bigger build. **Pass:** `... You have M free: M
      will be learned now, K later.`; the top talents glow, deeper ones are dim gold
      with `later`.
- [ ] **Look at 26 px.** Learned / glowing / `later` / desaturated / red rings are
      clearly different from each other, and the rank badge sits on the corner, not
      off the icon. If not, adjust sizes in `UI/TalentPanel.lua` (`buildCell`).
- [ ] **Tooltip.** Hover a mini-tree talent. **Pass:** the game's own talent tooltip
      (name, rank, description) **for that talent**, plus `Build: X / Y`. Since v0.10.4
      it's `GameTooltip:SetSpellByID(spellID)` (13.10): only a name line = that call
      is missing or failed here (note it in ADDON_PLAN 11); a spell tooltip without
      talent rank text is expected (it's the spell, not Blizzard's talent button).
- [ ] **Conflict.** With a point in a talent the build doesn't use: red ring on it and
      the red line `You already have 1 point in X, which this build doesn't use. Reset
      your talents at a trainer first.`
- [ ] **Wrong class.** Paste another class's link. **Pass:** `This is a Paladin build.
      You're playing a Warrior.` (red), your own trees shown.
- [ ] **Old link.** Delete the `~xxxx` from a link, Preview. **Pass:** yellow `Older
      link: can't check it against your talent trees.` above the preview.
- [ ] **Changed link.** Change the 4 characters after `~`. **Pass (English client):**
      red `This link was made with different talent trees than your game has. ...`,
      no preview. **Non-English client:** a real site link previews with the yellow
      `Your game isn't in English, so this link can't be checked ...` line instead
      (ADDON_PLAN 13.7).
- [ ] **Live.** With a preview showing, spend a point in Blizzard's talent window.
      **Pass:** within a moment the trees and the summary update (e.g. `..., 1 of them
      already learned`); Home's free-points line too.
- [ ] **Remembered.** Preview a link, `/reload`, `/r2ft`. **Pass:** the link is back
      in the box and previewed. Cancel clears it (and it stays cleared after a reload).
- [ ] **Combat.** In combat: Preview, Cancel and Copy my build still work (read-only),
      no "action blocked". Learn talents is greyed out in combat (since v0.8.0, 15).

## 15. Talent learning (v0.8.0, step 10) -- READ ALL OF THIS FIRST

**Since v0.10.4 (ADDON_PLAN 13.10):** WoW Forever has no Classic `GetTalentInfo`, so
the addon never calls `LearnTalent` there; Learn talents is always guided mode
(section 19). The direct/preview checks below only apply to a client that has
Classic's talent API.

**This is the one part of the addon that changes your character for good.** Every
learned point is permanent until a paid trainer reset. Do these checks on a **throwaway
or low-level test character** with only a few free points, never on a main, and do
them in order: each one assumes the one before passed.

**What's proven outside the game** (`run_tests.py`, fake client + fake server): the
order of points (= the gold `+N` cells, tier by tier), one point at a time, the
re-checks before every point (conflicts, tier, prerequisites, free points), the stop
on a refused point / combat / Stop with the exact messages, nothing sent in combat or
after a stop, resuming without sending a point twice, the popup only for a build with
no red conflicts, guided mode's logic and that it never touches Blizzard's frames.
**What only the game can show:** whether `LearnTalent` works for an addon at all, from
an event (not only a click), how fast the server answers, `GetTalentPrereqs`' shape,
the talent window's frame names, whether Forever has Blizzard's talent preview, and how
everything looks. ADDON_PLAN 13.8 has the reasoning.

**Before the first click, check the client (no points spent):**
- [ ] `/dump type(LearnTalent), type(GetTalentPrereqs), type(ToggleTalentFrame)` ->
      expect `function` x3. `LearnTalent` not a function = the addon uses guided mode.
- [ ] `/dump GetCVarBool and GetCVarBool("previewTalents"), type(AddPreviewTalentPoints)`.
      If the first is `true`, Forever has Blizzard's talent preview and Learn talents will
      **fill Blizzard's preview** instead of learning (nothing is learned until you click
      Blizzard's own Learn button). Note the result in ADDON_PLAN 11 either way.
- [ ] `/dump R2F.Talents.LearnMode()` -> expect `direct` (or `preview` per the line above).
- [ ] With a talent that has a prerequisite in view: `/dump GetTalentPrereqs(1, i)`
      (i = that talent's index; `/dump GetTalentInfo(1, i)` to find it). **Pass:** tier,
      column of the prerequisite, then `1` or `nil`.

**One point (the most important test):**
- [ ] Character with **1 free point**. Make a 1-point build on the site (a tier-1
      talent), Copy link, paste, Preview. **Pass:** gold `+1` on that talent; `This build
      uses 1 point. You have 1 free. It will be learned.`; Learn talents enabled; hover
      it: `Learns the gold +N points ...`.
- [ ] Click Learn talents. **Pass:** popup `Learn 1 talent point? Only a trainer reset
      can undo this.` with `[Learn] [Cancel]`. Click **Cancel**: nothing changes (check
      Blizzard's talent window).
- [ ] Learn talents again, **Learn**. **Pass:** within a moment the point is in Blizzard's
      talent window, chat `Learned 1 talent point.`, green line on the tab, the trees
      redraw (rank 1), no Lua error, **no "Interface action failed because of an AddOn"**.
      **If instead** you see `Stopped at X: the game didn't accept the point. 0 of 1
      learned. Your game may not let addons learn talents...`: check the point really
      isn't learned, then note it (ADDON_PLAN 11): `LearnTalent` is blocked for addons
      and the addon will guide you instead (guided-mode checks below).
- [ ] If the point **did** land but the message says `didn't accept` and a moment later
      `The point in X arrived late after all`, the server is slower than 0.5 s: note your
      ping; raise `Talents.LEARN_TIMEOUT` in `Talents.lua` (ADDON_PLAN 13.8).

**Several points (follow-up points are sent from an event, not a click):**
- [ ] 5+ free points, a build of 5 points across tier 1 **and tier 2** of one tree (so
      the tier rule matters). Learn. **Pass:** the button counts `Learning 1 / 5`,
      `Learning 2 / 5`, ...; link box, Preview and Copy my build are greyed out, Cancel
      reads `Stop`; at the end `Learned 5 talent points.` and exactly the build is in
      Blizzard's window. **If only the first point lands** and it stops at the second
      with `didn't accept`: Forever only allows `LearnTalent` from a click. Report it
      (ADDON_PLAN 13.8 "Not done / limits"); guided mode is then the way.
- [ ] A build with a **prerequisite** (e.g. a talent with an arrow). **Pass:** learned
      in order without a stop.
- [ ] More build than free points. **Pass:** the popup counts only the gold points;
      after the run the rest still shows `later`, summary `No free talent points.`

**Stops (do each on a few points):**
- [ ] **Combat mid-run:** start a 5-point run and attack a training dummy / pull a mob
      at once (or have a friend duel you). **Pass:** chat `Stopped: you entered combat.
      X of 5 learned. Click Learn talents to continue.`, **no "action blocked"**, no
      Lua error, no point learned during combat (Blizzard's window), Learn talents grey
      in combat. After combat: Learn talents continues **without a popup**, counting on
      from `X+1`, and finishes with exactly the build (no talent one rank too high).
- [ ] **Stop button:** start a run, click Stop at once. **Pass:** `Stopped. X of N
      learned. ...`; click Learn talents straight away: it continues and the build ends
      **exact** (no point learned twice).
- [ ] **Spend a point elsewhere mid-run** (hard to time; try with a big build): in
      Blizzard's window click a talent **not** in the build. **Pass:** `Stopped: your
      talents changed while learning. ...`, the red conflict line, Learn disabled.
- [ ] **Close the window mid-run** (Esc). **Pass:** the run still finishes (chat).
- [ ] `/reload` after a stop: the link is back, Learn talents asks with a **new** popup
      for what's left (runs aren't saved, ADDON_PLAN 13.8).

**Guided mode** (only reachable for real if `LearnTalent` is blocked; to try it anyway:
`/run LearnTalent = nil` on a test character, then `/reload` afterwards to undo):
- [ ] Learn talents -> popup with the extra line `Your game doesn't let addons learn
      talents, so Blizzard's talent window opens ...` -> Learn. **Pass:** Blizzard's
      talent window opens; a **pulsing gold glow** sits exactly over the first talent;
      the label above it and chat say `Click <name> (1 of N)`; the tab's note line too.
      If the glow is off the button or missing: `/dump TalentFrame ~= nil,
      PlayerTalentFrame ~= nil` and `/fstack` over a talent button; note the names
      (ADDON_PLAN 13.8 / `UI/TalentGuide.lua` `FRAMES`).
- [ ] Click the glowing talent. **Pass:** the glow moves on (`2 of N`); Blizzard's
      button still takes the click normally (the glow doesn't swallow it).
- [ ] A point in another tree: the glow sits on that tree's **tab** with `Open the
      <Tree> tab, then click ...`; switch tab: it moves onto the talent within a moment.
- [ ] Close Blizzard's window: the glow disappears; reopen (N): it's back.
- [ ] Click a talent **not** in the build: guided mode stops (`your talents changed`).
- [ ] At the end: `Learned N talent points.`, glow gone. No Lua error, no taint warning
      when you later open/close the talent window in combat (`/console taintLog 1` and
      check `Logs\taint.log` for `RoadToForever` after a session).

## 16. Quick settings (v0.9.0)

Out of the game, `run_tests.py` checks the three boxes against a fake CVar store: they
read values set elsewhere, write exactly `4` / the game default / `0` / `1`, refuse in
combat, report a refused or clamped value, and the Macro Book hides exactly `ANY/Zoom`,
`ANY/HideGuild`, `ANY/HidePvP` (ADDON_PLAN 12.4.1). What only the game can show:

- [ ] **API.** `/dump GetCVar("cameraDistanceMaxZoomFactor"), GetCVarDefault("cameraDistanceMaxZoomFactor")`,
      `/dump GetCVar("UnitNamePlayerGuild"), GetCVar("UnitNamePlayerPVPTitle")`,
      `/dump SetCVar ~= nil`. **Pass:** every value is a number (as text), `true` at the
      end. Note the zoom default here: ________. A `nil` means that box shows greyed
      out with `Your game doesn't have this setting.` (and its macro is back in the book).
- [ ] **The block.** `/r2f` -> Home. **Pass:** `Quick settings`, a grey note, three
      check boxes under the Import hint, inside the window (not over the bottom tabs),
      labels readable. Hover each: name + what it does.
- [ ] **Reads reality.** Close the window, type `/console UnitNamePlayerGuild 0`, open
      Home. **Pass:** `Hide guild names` is ticked. Type `/console UnitNamePlayerGuild 1`
      with Home open. **Pass:** it unticks within a moment (`CVAR_UPDATE`; if it only
      changes after switching tabs, the event doesn't exist here, which is fine).
- [ ] **Max camera zoom.** Tick it, scroll the camera all the way out. **Pass:** it goes
      clearly further than before; `/dump GetCVar("cameraDistanceMaxZoomFactor")` says
      `4` (if it says something lower, the client clamps it: you'd see `The game didn't
      accept that setting.` and the box unticked; note the value). Untick. **Pass:** the
      dump shows the default noted above, and the camera can't go as far.
- [ ] **Hide guild names / PvP titles.** Stand near a guilded player (and one with a PvP
      rank if you can find one). Tick each. **Pass:** the guild line / rank title
      disappears from their name; untick brings it back.
- [ ] **Survives a relog.** Tick all three, `/reload` (and once a full relog). **Pass:**
      still ticked and still in effect (the game saves CVars itself; the addon stores
      nothing).
- [ ] **Combat.** Attack a training dummy. **Pass:** the three boxes grey out, hover
      says `Can't be changed in combat.`, clicking does nothing, no Lua error, no
      "action blocked". After combat they work again. **Unconfirmed:** whether the game
      itself blocks `SetCVar` for these three in combat. The addon refuses either way
      (the backlog's "out of combat only"); if you want to know, out of the addon:
      `/run C_Timer.After(3, function() SetCVar("UnitNamePlayerGuild", 0) end)`, pull
      within 3 s, and see whether it changes or shows a blocked message. Note the
      result in ADDON_PLAN 12.4.1.
- [ ] **Macro Book.** Import a string that includes Zoom out more / Hide guild names /
      Hide PvP titles (e.g. "Select everything" on the site). `/r2f macros`, Universal
      tab. **Pass:** those three are not in the grid, every other Universal macro is, and
      the line `Zoom, guild names and PvP titles are Quick settings on the Home tab, so
      no macro is needed.` shows at the bottom. A real macro you made from one of them
      before v0.9.0 still works and is untouched.

## 17. Class picker, Remove from library, Tidy up tooltip (v0.10.0)

Asked for after the first real in-game test (2026-10-02): Warrior macros imported on
a Paladin went into the library but never showed. Decisions in ADDON_PLAN 5.10.
**Nothing here has run in the client yet**; the out-of-game tests only prove the
logic. Easiest setup: a Paladin (or any class) with your own class + Universal
imported, then import another class's macros (e.g. Warrior) on the same character.

- [ ] **The original report.** On the Paladin, import a Warrior string. **Pass:** chat
      says `imported N macros.`, the book opens on the **Warrior preview**: a row of
      class circles top left (Paladin first, a small gap, then Warrior), the Warrior
      one highlighted, `Warrior (preview)` in grey next to the row, Universal +
      General / Tank / DPS tabs on the right, Warrior macros in the grid.
- [ ] **Look of the picker row** (unverifiable outside the client). **Pass:** the
      circles sit between the portrait and the first grid row without overlapping
      either (row at y -46, 24 px buttons, starting x 70; the first grid row starts at
      y -80), the selected class has the same yellow checked glow as a selected side
      tab, hover shows the square highlight. The square highlight on a round icon may
      look slightly off: note it if so (a round `UI-Minimap-ZoomButton-Highlight` would
      be the alternative). On the `R2FMainPlain` fallback window (no portrait) the row
      just starts a little to the right.
- [ ] **Read-only.** In the Warrior preview, drag a Warrior macro to a bar and
      left-click one. **Pass:** nothing on the cursor, red `Log in on a Warrior
      character to use this macro.` at the top of the screen, `/macro` shows no new
      macro, **no "action blocked" / taint message**. Icons are grey (likely question
      marks: the client only knows icons of spells you have), subtext is the group,
      never `Learn later`. Hover: the tooltip ends with that red line and green
      `Shift-click to put it in chat.`; Shift-click works.
- [ ] **Universal still works in the preview.** Universal tab while previewing
      Warrior: drag a Universal macro. **Pass:** it lands on the bar as usual.
- [ ] **Counters and checks are yours.** In the preview, `Character x / 30` and
      `Account y / 120` still match `/macro` on the Paladin; the note above them reads
      `Previewing Warrior macros: read-only on this character. The slot counts and
      gold checks below are for the character you're playing.` (it may wrap to two
      lines: check it doesn't run into the last grid row or the counters).
- [ ] **Back to your class.** Click the Paladin circle. **Pass:** `Paladin (your
      class)` in gold, Paladin tabs, drag works again, the note is gone and the
      Universal tab shows `You also have macros for Warrior (51). Click a class icon at
      the top to look at them; ...`.
- [ ] **Remembered, then reset.** Pick Warrior, close the window (Esc), reopen with
      `/r2f macros`: still Warrior. Switch to Home and back: still Warrior. Now
      `/reload` (or relog) and open the book. **Pass:** it opens on your own class.
- [ ] **Tooltips on the circles:** class name, `N macros`, then green `Your class: drag
      these to your bars.` (yours) or red `Preview only. Log in on a Warrior character
      to use these macros.`
- [ ] **Class icons.** "Select everything" import: one circle per class with macros,
      in the site's order (yours first). **Pass:** each circle shows the right class
      (`CLASS_ICON_TCOORDS`); a question mark means the client lacks that class's
      coordinates (note which).
- [ ] **Remove from library.** Right-click one of your own macros that you already
      dragged to a bar, `Remove from library`. **Pass:** a popup `Remove <name> (<short>)
      from your library? ...` with Remove / Cancel; Cancel changes nothing. Remove: the
      macro leaves the book, chat says `removed <short> from the library.`, **the button
      on your bar still works and `/macro` still has it**. Take it off the bar and click
      Tidy up: it's offered for deletion. Re-import the string: the preview counts it as
      **new**, and it's back in the book (gold check back if it's on a bar).
- [ ] **Remove from library while previewing** another class: same popup, the entry goes
      away, nothing changes in `/macro`.
- [ ] **Tidy up tooltip.** Hover Tidy up. **Pass:** white `Tidy up`, gold text on what it
      deletes, grey line saying the library doesn't change and pointing at Remove from
      library. In combat (button greyed out) the tooltip still shows, plus red `Can't be
      used in combat.` (`SetMotionScriptsWhileDisabled`, unverified in this client: if
      no tooltip shows while greyed, note it).

## 18. Version/author footer (v0.10.2)

- [x] **Home tab, bottom.** Open `/r2f` on the Home tab. **Pass:** a quiet grey line
      below Quick settings reads `Road to Forever v<version> · by nobody174 ·
      nobody174.github.io/wow-forever`. Confirmed working in-game 2026-10-02;
      the metadata API exists on this client (version/author show correctly).
- [ ] **Hover the line.** **Pass:** a tooltip shows "Import macros and talent builds
      from the Road to Forever site." (the TOC's own `## Notes:` text).
- [ ] **Fits without overlap.** Check the line doesn't run into Quick settings above it
      or get clipped at the window's bottom edge — this was only measured against the
      fixed 540x500 window size, never seen on a real screen.

## 19. Talent reading through C_Traits (v0.10.4; replaces v0.10.3's section)

v0.10.3's fix (force-loading `Blizzard_TalentUI`) was built on a wrong premise:
that addon is `MISSING` on WoW Forever. v0.10.4 reads talents through `C_Traits`
(ADDON_PLAN.md 13.10, which also lists exactly what is proven and what isn't).

- [ ] **The original bug.** Fresh login (or `/reload`), don't open Blizzard's
      Talents window, `/r2f` → Talents → paste a site link of your class → Preview.
      **Pass:** trees + summary line, not "couldn't read your talents yet."
- [ ] **Copy my build, cold.** Same state, Copy my build. **Pass:** a link; open it on
      the site: same talents and ranks as Blizzard's window. Then the hash check of
      section 13 (the 4 characters after `~` equal the site's Copy link for the same
      build). Equal hashes prove names, order and pane order all match for that class.
- [ ] **Paladin after v0.10.5 (ADDON_PLAN 13.11).** The live 50-node dump found 10
      units of jitter in Protection's first column (5020 / 5030), which made v0.10.4
      refuse the tree. On the same Paladin: Preview your own link and Copy my build.
      **Pass:** no "couldn't read"; Protection's mini tree has its talents in 4
      columns, same cells as Blizzard's window; the hash equals the site's.
- [ ] **Every class you can log in with.** Repeat the two checks above per class:
      the pane split (by X gaps between columns) is only proven on Paladin. If one
      still says "couldn't read", dump its node positions (posX / posY of every node)
      the same way: more jitter than 13.11 handles is the first thing to look for.
- [ ] **Learning is guided on Forever (13.10).** With a learnable preview, Learn
      talents. **Pass:** chat says which talent to click (`Click X (1 of N)`); no
      gold glow on Blizzard's window (expected: the addon can't confirm its buttons);
      nothing is learned by the addon itself. Click the named talent in Blizzard's
      window and **Apply Changes**. **Pass:** the addon moves on to the next talent.
      If it doesn't move until something else happens, note whether it moved on the
      click or only on Apply (which event fires: `/etrace`, look for
      `TRAIT_CONFIG_UPDATED` / `CHARACTER_POINTS_CHANGED`).

## Known gaps in v0.10.0 (by design / later)

- **No bulk Remove from library** (ADDON_PLAN 5.10): removing a whole imported-by-mistake
  class is one right-click + popup per macro.
- **Other classes' icons are mostly question marks** in the preview: the client only
  returns icons for spells this character knows; the site's `icon` field is used when
  the macro has one.
- **The 5.7 line isn't clickable**; use the class circles (ADDON_PLAN 5.10).

## Known gaps in v0.9.0 (by design / later)

- **Quick settings in combat:** refused even if the game would allow it (ADDON_PLAN
  12.4.1); change them out of combat.
- Hidden Quick-settings macros still count in Home's `N macros in your library` (they
  are in the library; only the book hides them).

- **Talent learning has never run on a real client.** Do section 15 on a test character
  before trusting it with a real build.
- The learning timeout is 0.5 s (ADDON_PLAN 13.5); on a slow connection a point can be
  reported as refused and then `arrived late`. The run stops (safe) and continues on the
  next click.
- A run isn't saved over a `/reload`; the link is, and a new click asks again.
- A non-English client can't verify links (the hash is over English names); it gets
  the yellow "can't check" line and the sanity checks only (ADDON_PLAN 13.7).
- The window has a fixed size (ADDON_PLAN 6.10); only position and tab are saved.
- No embedded libraries: without another addon that loads LibDBIcon, the minimap
  button is our own, which some minimap-button collector addons may not pick up
  (ADDON_PLAN 6.10).
- Remove all only reaches this character's character-slot macros (plus account
  ones); use it on each character to clear theirs.
- An icon-only change to a macro made with v0.1.0 isn't pushed until its body
  changes too (v0.1.0 didn't store the icon; ADDON_PLAN 6.8).
- ~~Other classes' macros have no tabs~~: since v0.10.0 the class picker shows them
  read-only (section 17).
