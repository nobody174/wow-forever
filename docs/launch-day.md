# Launch day checklist (servers open 2026-11-04 23:00 UTC, Nov 5 00:00 Norway)

The order matters: settings first, then the addon, then the walk. Everything here is also in BACKLOG 0 and 5; this is the one page to follow.

## Before the servers open
1. **Backup the beta settings** (`python addon/tools/backup_wtf.py`), once more if anything changed. Details: `docs/beta-backup.md`.
2. **Install the release client**, log in once with each character, **log out and close the game completely**, then restore the backup files
   into the release client's `WTF` (same places; do not overwrite `Config.wtf` unless you meant to).
3. **Tag the addon** when every check is green: `python build.py`, `python addon/tests/run_tests.py`, luacheck (see below), then
   `git tag r2f-vX.Y.Z` and push the tag (one or two tags at a time). Install the zip from the release.
4. **Data refresh**: BiS and items (`python build.py` re-reads `bis/`), AH prices (`prices.json`), then push.

## On the first Skyborne Hunter
1. Run **Setup Hunter** before anything else is placed (needs the Edit Mode layout "Hunter" restored first).
2. `/r2f route start hunter-1`, play the start slowly: talk to everyone, take and hand in quests in the order you like.
3. Open the Plan tab: it should say "Alliance Skyborne Hunter" (if not, `/dump UnitRace("player")`, TESTING 5.70). Tick **Follow the plan**
   and watch the steps tick as quests are handed in (TESTING 5.71).
4. Afterwards `python addon/tools/route_report.py`, then correct order, givers, coordinates and gates in `launch-plan.html` PHASES
   and `launch-plan-waypoints.json`, and drop the `unv` tags that held up (TESTING 5.65).

## First days
- Re-check the unverified launch-plan steps past level 30, the level-60 builds and the cheat sheets (BACKLOG 5.3).
- Professions BiS from ForeverChanges' level-60 lists; AH market when AHledger lists EU (BACKLOG 5.1, 5.2).
- Ground markers in a group (BACKLOG 0.4).

## luacheck without installing it
CI runs `luacheck addon/RoadToForever --config addon/.luacheckrc` and the release waits for it. To run it here: download the luacheck source
(github.com/lunarmodules/luacheck, tag v1.2.0) and `argparse.lua` (github.com/mpeterv/argparse, `src/argparse.lua`) into two empty folders
outside the repo, then `python addon/tests/run_luacheck.py <luacheck-1.2.0/src> <folder with argparse.lua>`. Zero warnings = green.
