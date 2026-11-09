# Project review, November 2026: summary

Date 2026-11-09, addon 0.84.2. Six read-only reviews, run one after the other. Nothing in the project was changed except these report files.

| # | Role(s) | Report |
|---|---|---|
| 1 | Code Reviewer, with taint / WoW API lens (Code Style Enforcer folded in) | [01-code-review.md](01-code-review.md) |
| 2 | Research Analyst + Data Analyst | [02-research-data.md](02-research-data.md) |
| 3 | Design Critic (UI/UX) | [03-design-critic.md](03-design-critic.md) |
| 4 | Technical Writer + Editor / Proofreader | [04-writer-editor.md](04-writer-editor.md) |
| 5 | QA / Playtester + Debugger | [05-qa-debugger.md](05-qa-debugger.md) |
| 6 | Critic / Devil's Advocate (Architect folded in) | [06-critic-architect.md](06-critic-architect.md) |

Not run: UI Concept Designer (it makes new designs, not reviews), a separate Architect and Style Enforcer pass (covered inside 1 and 6).

## Verdict
The code and the numbers are in good shape. The public face, and the process around the code, are what need work. Nothing found is a safety problem; the biggest items are about the project still speaking as if the game had not launched.

## Do first (high)
1. **Post-launch pass on the site** (Research R2, Design D1/D2/D3/D5, Writer W1, QA Q2): beta ribbon, "launches tonight", the BETA DATA badge (set by `DATA_STATE = "beta data"` in `build.py`), "before launch on November 4", the Legacy-perk card, and the Addons page telling people to use `_classic_beta_` (the real folder is `_forever_`).
2. **Mage macro that cannot work** (R1): "Remove Curse (friend or foe)" must be **Remove Lesser Curse** (Wowhead Forever, level 18). Plus Shaman Elemental Mastery x2 and Paladin Salvation / Light / Sanctuary: spells not in the current data (R5).
3. **Mr.BiZ is the level 30 beta list from 2026-10-17** (R3), and the professions prices/enchants are from 10-06/10-07 (R4). This is the BACKLOG "launch-day refresh" that did not happen.
4. **Addon README is incomplete about what the addon writes** (W2): Setup places macros, clears buttons, sets key bindings, toggles action bars; the README says it only does three other things.
5. **Make the data refresh reproducible** (Critic 2): the RankedBoost conversion scripts exist only in a temp folder; commit them.

## Do next (medium)
- Run the GitHub "Rehearsal" workflow once; it has never run (Q1). Then schedule a weekly subset.
- Close the 16 open in-game tests and update `TESTING.md` (QA, W9); several you have already confirmed in this session. Do a test week before more features (Critic 1).
- Add a build-time check of macro spell names against the trainer/talent data (R7) and one smoke test each for the unreferenced, frame-hooking modules (Q3).
- Addon README: seven tabs, Training / Aspect missing (W3), terminology table (W7), shorter shipped changelog (W5).
- Docs: fold BACKLOG section 0 into the post-launch section (W10); a 150-line `ARCHITECTURE.md` instead of reading a 3,253-line plan (W11); `docs/maintainers.md` (Critic 5).
- Small code items: Setup combat re-check in the wait loop (C1), TomTom stand-in robustness (C3), cache `Training.All()` (C4), tooltip fallback for unknown ids (C5).
- Builds page: remember last class (D4); balance the class buttons 9 = one row (D6).

## Later (low)
`R2F.Util` for the duplicated helpers (C8), split `run_tests.py` (C7), SavedVariables migration test (Architect), trainer list including quest-given spells (R8), install size (Q5), link-checker noise (Q4), changelog size (W12).

## What is good (keep)
Hooks only, combat refusals, secret-value guards, validated addon messages; 32,010 passing checks; generated files that tests and CI keep in step with their sources; a single consistent site design with a clear gold-for-action language; honest "unverified / seen / clue" tagging; plain, direct copy; well-organised `docs/` with "read when you touch X".

## Suggested order of work
Week 1: items 1, 2, 4 (a day or two of copy and small fixes), then 3 (data refresh, needs the browser pipeline) and 5. Week 2: test week and the medium list. Features wait until the 16 open tests are closed.
