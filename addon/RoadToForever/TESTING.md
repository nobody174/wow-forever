# Road to Forever: in-game test checklist (v0.2.0, addon steps 3 and 4)

Nothing in this addon has run in the real WoW client yet. Out of the game it was
tested under real Lua 5.1 against a fake client (`addon/tests/`), which checks
logic, not the client. This list covers what only the game can confirm
(`ADDON_PLAN.md` section 11). Tick each item in the beta, and fix
`ADDON_PLAN.md` + the code in the same commit if something turns out different.

**Setup:** copy `addon/RoadToForever/` into `World of Warcraft\_classic_era_\Interface\AddOns\`
(or the Forever client's AddOns folder), start the game, enable "Road to Forever"
on the character screen. Turn Lua errors on: `/console scriptErrors 1`.

## 1. Loads at all

- [ ] **Interface number.** In game: `/dump select(4, GetBuildInfo())`. Put that
      number in `RoadToForever.toc` (`## Interface:`; `11507` now is a placeholder for
      Classic Era 1.15.7). **Pass:** the addon is not listed as "out of date" on the
      character screen's AddOns list.
- [ ] Log in. **Pass:** no Lua error. `/r2f` opens the Macro Book. `/r2f help` prints a line.
- [ ] `/dump R2F` shows a table; `/dump R2FDB.version` shows `1`.

## 2. Templates exist (section 11)

The addon tries each template and falls back if it's missing, so check which one
you got:

- [ ] **PortraitFrameTemplate.** `/dump R2FMacroBook ~= nil`. **Pass:** `true` and the
      book has the round class-icon portrait top left, a gold title "Road to Forever"
      and an X button. If `R2FMacroBookB` exists instead, the client only had
      `ButtonFrameTemplate`; if `R2FMacroBookPlain`, neither (plain dialog border,
      no portrait). Fallbacks work but look less native: note which one in ADDON_PLAN 11.
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
      Universal tab shows `You also have macros for Hunter (..), Mage (..), ...`.

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
- [ ] Slot counter `Character x / 18` and `Account y / 120` match `/macro`. Turns red
      when full. **Also confirm the limits really are 120 + 18 (section 11).**
- [ ] Shift-click a macro with the chat box open: the body appears in one line.
- [ ] Right-click: menu with `Remove from library` / `Copy text`. Copy text opens a
      box with the body highlighted; Ctrl+C works.

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
- [ ] Fill all 18 character slots, drag a new one. **Pass:** it goes to an account
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

## Known gaps in v0.2.0 (by design, later steps)

- Settings button is disabled (step 5). New macros go to character slots first.
- An icon-only change to a macro made with v0.1.0 isn't pushed until its body
  changes too (v0.1.0 didn't store the icon; ADDON_PLAN 6.8).
- No main window, minimap button or full slash-command set (step 6). `/r2f` opens
  the Macro Book directly, `/r2f import` opens the Import window.
- Other classes' macros have no tabs; they're kept and listed on the Universal tab.
