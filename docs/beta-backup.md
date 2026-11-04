# Taking your settings from the beta to the release client

Why: the beta client (`_classic_beta_`) and the release client (`_classic_`) keep separate settings. Your Edit Mode layouts, key
bindings, macros and graphics settings do not follow you. Copy them over once.

## Make the copy
`python addon/tools/backup_wtf.py` copies the files below into `D:\Claude AI Projects\wow-beta-backup\<date>\` (outside the git
repository on purpose: character names and keys do not belong in git). Run it again whenever you change something worth keeping,
and once more on the last beta day.

| File (from `WTF`) | What it holds |
|---|---|
| `Config.wtf` | graphics, gamma, brightness, camera and every other game setting |
| `Account\<id>\bindings-cache.wtf` | your key bindings |
| `Account\<id>\macros-cache.txt` | your macros (the account ones; the addon's own macros come back by themselves) |
| `Account\<id>\edit-mode-cache-account.txt` | your Edit Mode layouts, e.g. "Hunter" and "Warrior/Druid" |
| `Account\<id>\config-cache.wtf` and the other `*-cache` files | account-wide settings |
| `Account\<id>\SavedVariables\RoadToForever.lua` | our addon's settings, theme, recorder data |

## Put it into the release client
1. Install the release client and log in once with each character, then **log out and close the game completely** (the game
   rewrites these files when it closes).
2. Run `python addon/tools/restore_wtf.py` (it only shows the plan), then `python addon/tools/restore_wtf.py --apply` with the game
   closed. It copies bindings, Edit Mode layouts, macros and account settings into the release client (`D:\World of Warcraft\_forever_`),
   keeps what it replaces in `wow-beta-backupefore-restore-<time>`, refuses while Wow.exe runs, and never touches `Config.wtf`,
   SavedVariables or the character folders. **The account folder is NOT the same id** (beta `575003#3`, release `IZAK04`): a copy by
   hand into the beta's id lands nowhere. (Found 2026-11-05: the release client had rewritten these files empty at its first start.)
3. Start the game. Check Edit Mode (layouts), Options > Key Bindings, `/macro`, and the addon's Home page.
Anything that does not come back: the game's own caches are rebuilt from the server, only these files are yours.

## The Setup button
`/r2f setup hunter` (or the minimap menu's "Setup Hunter") needs the Edit Mode layout called "Hunter" to exist in the client where
you press it, so restore the layouts first (the menu entry is hidden until the layout is there). Then pick the "Hunter" layout in Edit Mode once per character.
