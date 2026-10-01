# Addon plan: Road to Forever Macros

Status: **planned, not started** (scoped 2026-10-01). Build before the Nov 4 launch.
Working name: **Road to Forever Macros** (folder `RoadToForeverMacros`, slash
command `/r2f`).

## Goal

Get macros from this site into the game without copy-pasting them one by one,
and without touching files on disk. An in-game addon browses every macro from
`data.py`, creates the ones you tick, and lets you drag them straight onto your
action bars.

Why an addon and not a script that edits `WTF\...\macros-cache.txt`:

- Classic syncs macros with the server; the local cache file is rewritten at
  logout and can be replaced at login, so file edits get lost. (Confirm in beta.)
- The character folder doesn't say which class the character is. The addon just
  asks the game (`UnitClass("player")`).
- Install paths, account and realm names differ per player. The addon doesn't care.

## What the player sees

`/r2f` (and later a minimap button) opens one window:

```
+--------------------------------------------------------------+
| [Universal][Priest][Warlock][Mage][Rogue][Druid][Shaman]...  |  class icons
| [General] [Tank] [DPS] [Healer]          (only roles that exist)
|--------------------------------------------------------------|
| [x] Select all (this role)                  Slots: 12/18 char |
|  Damage / offensive                         [x] group          |
|   [x] (icon) Victory Rush          [drag]                      |
|   [ ] (icon) HS / Cleave           [drag]                      |
|  Panic / defensive                                             |
|   ...                                                          |
|--------------------------------------------------------------|
| [Install selected]  [Install all for my class]  [Import string]|
+--------------------------------------------------------------+
```

1. **Class icons** across the top (built-in class icon texture, no downloads).
   Opens on your own class. Other classes can be browsed but not installed (their
   spells would show a red "?"); Universal can always be installed.
2. **Role tabs** per class: General / Tank / DPS / Healer, only the ones that class
   has (e.g. Mage: General + DPS; Paladin: all four; Druid: all four).
3. **Checkboxes**: one per macro, one per group ("Damage / offensive"), "Select all"
   per role, plus **Install all for my class**.
4. **Hover** a macro to see its full code and note (the same note as on the site).
5. **Drag and drop**: drag the macro's icon onto an action bar. If the macro doesn't
   exist yet the addon creates it first, then puts it on your cursor
   (`CreateMacro` + `PickupMacro`). Out of combat only.
6. **Import string** button: paste a string copied from the website (see below).

## Website side (`macros.html`)

- A checkbox on each macro, "Select all" per group/role, and a **Copy import
  string** button. The string holds the selected macros (name, short name, icon,
  body) so new or changed macros reach the game without an addon update.
- A **Download addon** link (zip from GitHub Releases), later CurseForge.

## Data changes needed first (in `data.py`)

1. **Role sections for every class**, like Warrior/Paladin already have: General /
   Tank / DPS / Healer. Spec-only extras stay as notes or move into the role that
   uses them (e.g. Priest Shadow -> DPS, Holy + Discipline -> Healer).
2. **Add Druid.** It's missing from the macro site entirely, and the group has a
   Druid healer. Needs General / Tank / DPS / Healer.
3. **Short in-game names.** WoW macro names max out at 16 characters; 155 of our
   374 names are longer today. Add an optional `short` field to `M()` (build.py
   falls back to the full name if it already fits, and fails the build if a name is
   still too long).
4. **Icon field** for macros without `#showtooltip` (pet attack, /console, marks),
   e.g. `icon="Ability_GhoulFrenzy"`. Macros with `#showtooltip` use the question-mark
   icon and let the spell decide.

## How the addon is built

- `build.py` gains a third output: `addon/RoadToForeverMacros/MacroData.lua`
  generated from `data.py`, the same single source of truth as the site. Never
  hand-edit it.
- Files: `RoadToForeverMacros.toc`, `MacroData.lua` (generated), `Core.lua`
  (install/update/remove logic), `UI.lua` (window, tabs, checkboxes, drag),
  `Import.lua` (string decode).
- **Own-macro tracking** in SavedVariables: which macros this addon created and
  a hash of their body, so it can:
  - **update** a macro when the site version changes (same name, new body),
  - **skip** ones you edited yourself (hash differs) unless you say overwrite,
  - offer **Remove all Road to Forever macros**.
- **Slots**: Classic has a limited number of macro slots, believed to be 120
  account-wide + 18 per character (confirm in beta). Class macros default to
  per-character slots; the window shows free slots and blocks an install that
  won't fit, offering account slots instead. "Install all" for Warrior (52 macros)
  will NOT fit in 18 character slots, so the UI should say so up front.
- **Combat lockdown**: all create/edit/pickup actions are disabled in combat; the
  buttons grey out and re-enable on `PLAYER_REGEN_ENABLED`.
- **Import string format**: versioned prefix (`R2F1:`) + encoded list of macros.
  Start with a plain base64 of a simple serialized table (no libraries); switch to
  LibSerialize + LibDeflate (the WeakAuras approach) only if strings get too long.

## Repo / distribution

- Recommended: keep the addon in **this repo** under `addon/`, so `build.py`
  writes the site and the addon from the same `data.py` in one step.
  (Alternative: the separate `wow` repo's "forever addons" folder, with a copy
  step. More moving parts.)
- GitHub Actions zips `addon/RoadToForeverMacros/` into a Release on each tag;
  the site's Download link points at the latest release.
- Later: CurseForge project so it auto-updates through the CurseForge app.

## Things to confirm in beta

- [ ] TOC `## Interface:` number for the Forever client.
- [ ] Exact macro slot limits (account / character).
- [ ] Whether the server overwrites local macro changes (affects nothing in this
      plan, but closes the file-editing question for good).
- [ ] Macros created by an addon keep their icon and body after a relog.
- [ ] `PickupMacro` straight after `CreateMacro` works in the same frame (or needs
      a short delay).

## Build order

1. Data: role sections for all classes, add Druid, `short` names, `icon` field.
2. Addon MVP: generated `MacroData.lua`, `/r2f` window for **your own class**,
   checkboxes, Install selected / Install all, slot counter, combat lock.
3. Drag and drop onto action bars.
4. Browse all classes with class icons (install locked to own class + Universal).
5. Website checkboxes + Copy import string; addon Import window.
6. Release zip + Download link on the site; CurseForge later.
