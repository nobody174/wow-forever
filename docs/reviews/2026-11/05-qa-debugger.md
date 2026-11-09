# Review 5: QA / Playtester + Debugger

Date 2026-11-09, addon 0.84.2. Read-only. What was run: addon test suite, release-tree check, top-bar sync check, internal link check (`tools/check_links.py`), external link check (`--external`), `build.py` idempotence, the launch-day rehearsal (`tools/rehearse.js --quick`). No game client was available, so anything that needs the game is listed under "Cannot be verified here".

## Results

| Check | Result |
|---|---|
| `addon/tests/run_tests.py` | **32,010 checks passed, 0 failed** (83 test functions) |
| `check_release_tree.py` | ok: version 0.84.2, 315 files |
| `tools/sync_topbar.py --check` | ok: identical on all pages |
| `tools/check_links.py` | ok: 12 pages, 236 local references |
| `check_links.py --external` | ok, with 21 warnings; all but one are noise (see Q4) |
| `gen_talent_data.py --check` / `--drift` | trees match the live snapshot, no drift |
| `rehearse.js --quick` with Edge | **inconclusive**: 229 of 363 failed, every failure is "no probe answer ... page did not finish drawing" (the script expects Chrome's `--dump-dom`; Edge headless did not return the page). Not evidence about the site. The GitHub "Rehearsal" workflow has **never been run** (0 runs). |

## Findings

| # | Sev | Finding | Evidence | Suggested fix |
|---|---|---|---|---|
| Q1 | **High** | **The launch-day rehearsal exists but has never been run anywhere.** It is the only automated browser check of the pages (countdown, 29 plans, Mr.BiZ 27 specs, accessibility), it is manual-dispatch only, and `gh run list --workflow=rehearsal.yml` is empty. Launch has now passed, so its main purpose is gone; its remaining value (page render, Mr.BiZ rows, a11y) is not used. | workflow list, run output | Run it once from the Actions tab now (the GitHub runner has Chrome). If green, put `--only pages,bis,a11y` into a weekly schedule so rendering breakage is caught before a player sees it. |
| Q2 | Med | **`build.py` changes a tracked file on every new day.** `data-version.json` carries `"updated": <today>` and `"state": "beta data"`; the first `build.py` run of the day shows a modified file even with no content change, and the same file drives the "BETA DATA" badge on four pages (Design D2). It is both noise in `git status` and the root of a wrong public label. | `build.py:256-258`, `git diff data-version.json` | Change `DATA_STATE` to a truthful value ("live data" / "beta data (level 30)" per page, see D2), and only rewrite `updated` when the content hash changes. |
| Q3 | Med | **Modules with no direct reference in the test file:** `Diagnostics`, `GameplayChat` (189 lines), `GameplayExtras` (542), `GameplayQuests` (388), `ImportFrame`, `ItemApi`, `Widgets`; one reference only: `Core`, `DecoBook`, `DecoToy`, `Professions`. They may be covered through the feature tables, but nothing names them. `GameplayExtras` and `GameplayQuests` hook game frames (the taint-sensitive kind) and are the largest unreferenced files. | grep count per module in `run_tests.py` | Add one smoke test each that loads the module, runs `Init` with stubs, and asserts it neither errors nor writes a game table. Cheap, and it extends the guard the hardening pass built. |
| Q4 | Low | **External-link warnings are mostly noise, which hides real ones.** 403s are bots blocked by CurseForge and Mobalytics; 7 "InvalidURL" results come from JavaScript string fragments in `bis.html` / `professions.html` (`'+ id +'`) that the checker reads as URLs. One real dead link: `google.com/s2/favicons?domain=wowforeverstatus.com` answers 404 (the Index page's Server status favicon). | check_links output | Teach the checker to skip fragments containing `'` / `+` and to treat 403 from known bot-blockers as "skipped"; fix or drop the favicon. |
| Q5 | Low | **Install size 39 MB** on disk (zip 5.3 MB): seven 4 MB `arrow3d*.tga` sprite sheets (28 MB) for the waypoint-arrow looks. They compress well in the zip, but players see 39 MB under AddOns and each opened look loads a 1024 x 1024 texture. | `du`, release asset | Fine for now. If the addon goes to CurseForge, consider shipping only the default sheet and the two most used looks, or 512 px sheets. |
| Q6 | Info | `.luacheckrc` is only run in CI (not locally), so luacheck failures show up after the push. This happened twice in this session's releases (undefined globals, long lines). | session history | Add `luacheck` to the documented pre-push steps; CI result must be waited for before tagging (already the practice). |

## Open in-game tests (`addon/dev/TESTING.md`)
- **16 items open** (5.32, 5.64 to 5.78) plus a "cannot be tested yet" list (Druid Starsurge / Sunfire / Starfall, Dire Bear at 40, Hunter Strider Kick, ...).
- Header says "checked against 0.80.1 on 2026-10-20" and 5.72 to 5.78 say "(next release)" although they shipped in 0.82.0 to 0.84.2 (Writer W9).
- Section header "(0.79.1: every theme was rebuilt blind, so expect rough edges)" is still the oldest open risk: **the ten looks were never confirmed tab by tab**, and six more releases landed on top of them (0.80 to 0.84).
- Items likely confirmable from what you have already said in this conversation: 5.74 (Aspect), 5.75 (combat banner), 5.76 and 5.78 (Training tab and list: "the talents are readable, tooltips work" and the screenshot of the list), 5.77 (talent art: you sent screenshots; the next-point pulse is the only open part).

## Debugger notes (hypotheses, not defects)
1. **Talent painting file names are guessed** from Classic names (`Interface\TalentFrame\<Class>Frame-TopLeft` etc.). If one is missing in the Forever client the tree shows a flat panel: the code falls back, so the failure is silent. Check once in game with `/dump` of the texture load or just look at all nine classes. (QA: one screenshot per class, 9 pictures.)
2. **"Couldn't read your talents yet"** appeared once and was explained as transient (names not loaded). The cause was found (talent names arrive late); the user-visible text still reads like an error. Worth a retry timer, not a message.
3. **`Training.All()` learned detection** uses `IsPlayerSpell` per spell id. For spells that exist as several ids per rank the "higher rank known" rule covers it, but a Forever-only spell whose id differs from Wowhead's will show as "available" forever. Compare the list with a trainer visit on one character per class: any row that stays "Train now" after you learned it is a mismatch.
4. **Setup / Edit Mode on the release client**: layouts were found not to restore from files (memory note: server-synced). The three-step workaround (SetBinding / layout string) worked; make sure the README and `docs/beta-backup.md` say so, or a new player will lose a setup to the same trap.

## Cannot be verified here
- Anything in the game client: taint log, in-combat behaviour, theme visuals, Edit Mode, trainer flows.
- Phone rendering of the site (Edge headless minimum viewport; Chrome in CI is the better tool, see Q1).
- Mr.BiZ and Professions row-level correctness (see Research).
