# Maintainer's page (one page: how to keep this project going)

Everything here also lives in more detail elsewhere (`CLAUDE.md`, `docs/pipeline.md`, `addon/HARDENING.md`); this is the gathered short version.

## Daily loop
1. Change the **source** (never a generated file): `data.py`, `builds.html`, `launch-plan-steps.json`, `bis/raw/`, `professions.html` ...
2. `python build.py`, then `python addon/tests/run_tests.py` (look for the "checks passed" line; a crash hides it).
3. Site: look at it locally (`python -m http.server`, then the page). Addon: the owner tests in game (`addon/dev/TESTING.md`).
4. Commit and push to `main`. Pages redeploys in about a minute.

## Addon release
Bump `RoadToForever.toc`, `addon/RoadToForever/CHANGELOG.md` (two plain sentences per release), root `CHANGELOG.md`, add a `news.json` entry, tests green,
commit, `git pull --rebase`, push. **Wait for the `ci.yml` run on that exact commit** (tests + luacheck + release-tree check; luacheck only runs
there). Then `git tag r2f-vX.Y.Z` and push the tag (one or two tags at a time). Check the Release workflow and that `RoadToForever-X.Y.Z.zip` is attached.

## Data refreshes (what needs a browser, and why)
| Data | How | Needs a browser? |
|---|---|---|
| Talent trees | `python addon/tools/gen_talent_data.py` (`--check`, `--drift`) | no (nether.wowhead.com data endpoint answers curl) |
| Recommended builds | `python addon/tools/builds_from_rankedboost.py` then `--apply` | no |
| Trainer list | console snippet in `gen_training_data.py`'s docstring saves `wh_all.json`, then run the script | **yes** (Wowhead blocks plain downloads) |
| Mr.BiZ | `bis/README.md`: ForeverDB pages into `bis/raw/`, `python bis/build_bis.py`; item quality via Wowhead tooltip API | **yes** |
| Professions enchants / prices | `docs/professions-bis.md` (ForeverChanges lists, Wowhead Forever spell pages, `prices.json`) | **yes** |
| Addon versions on addons.html | `docs/addons-page.md` (CurseForge check; blocked from the sandbox) | **yes** |
A browser from a Claude session: a `claude -p --allowedTools "mcp__claude-in-chrome__*"` subprocess (see the project memory note).

## Traps that cost time before
- **Never hand-edit generated files** (`macros.html`, `wow-forever-macros.md`, `bis-data.json`, `MacroData.lua`, `PlanData.lua`, `BiZData.lua`, `TalentData.lua`, `TrainingData.lua`).
- A Python heredoc in the shell collapses double backslashes: put regexes with backslashes in a file, or use `chr(92)`.
- Bump `?v=` on `talentcalc.js`, `talentcalc.css`, `talentsaved.js`, `legacycalc.js` **together**.
- Top bar CSS: edit `tools/sync_topbar.py`, run it, then `python build.py`.
- Git identity is the GitHub noreply address; no personal data in the repo or commits.
- The release client keeps settings on the server: restoring WTF files does not work; in-game `SetBinding` / layout string import did (`docs/beta-backup.md`).
- Reload from our own button is blocked by the game; the Setup puts `/reload` in the chat line instead.

## Where to look
`CLAUDE.md` (rules and the doc table) -> `docs/` (per area) -> `addon/ARCHITECTURE.md` (the addon in one page) -> `ADDON_PLAN.md` (design history, read by section) -> `BACKLOG.md` / `CHANGELOG.md`.
Reviews: `docs/reviews/`.
