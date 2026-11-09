# Review 1: Code Reviewer (with the WoW taint / API-compliance lens)

Date 2026-11-09, addon 0.84.2, 32,010 checks green. Read-only: nothing was changed.
Scope: the addon code written or changed since the 2026-10-12 hardening pass (`addon/HARDENING.md`), plus pattern scans over every non-generated Lua file (hooks, globals, CVars, protected calls, events, OnUpdate, secret values).

## Verdict
Safe to keep shipping. No taint hole, no protected call without a combat guard on the main paths, no unbounded timer or event loop found. The hardening decisions (hooks only, no game-table writes, secret-value guards, combat refusals) have held through 40 more releases. Findings below are all Low to Medium.

## What is good (verified, not assumed)
- Hooks: only `hooksecurefunc` / `HookScript` (Bags, GameplayQuests, GearScore, Nav). No function is replaced. Bags keeps its drag flag in a local table, not on Blizzard's frame.
- CVars: every read and write goes through `QuickSettings.lua`, refused in combat, value read back after the write.
- Protected-looking calls (`PickupAction`, `PlaceAction`, `SetBinding`, `SaveBindings`, `SetActionBarToggles`) live only in `Setup.lua` / `General.lua`, each behind `R2F.InCombat()` checks, and the multi-step setup re-checks combat before every button.
- Secret values: `issecretvalue` guards in every file that touches unit data (Buffs, Timers, Diagnostics, ActionBars, Recorder, RouteLog, GameplayExtras, GameplayChat, Training); CombatBanner reads health through a `pcall` wrapper.
- Addon-message input (Version, Talents share) is validated: strict pattern for the version, length cap 250, link parsed and checked like a pasted one, name stripped of control characters and `|`, shared loadouts capped (`MAX_SHARED`), received data never applied, only saved.
- `OnUpdate` is used in 8 places; all are either on a frame that is hidden when not needed, throttled (Home 1 s, Timers `THROTTLE`), or removed when the work ends (Bags drag watcher, Minimap drag).

## Findings

| # | Sev | Where | Finding | Suggested fix |
|---|---|---|---|---|
| C1 | Low | `Setup.lua` `placeOne` -> `step()` (≈ l.272) | The row loop checks combat before each button, but the 8-try wait loop inside one button (up to 1.2 s) calls `PlaceAction` without re-checking. Combat starting in that window gives an `ADDON_ACTION_BLOCKED` popup and leaves a macro on the cursor (the code does `ClearCursor` on the failure path, so it self-heals). | Add `if R2F.InCombat() then ClearCursor() return done("failed") end` at the top of `step`. |
| C2 | Low | `Talents.lua` `SaveLoadout` | Loadout id is `time() .. "-" .. (#list + 1)`. After a delete, two saves in the same second can get the same id; `DeleteLoadout` then removes the first match. Rare, harmless data mix-up. | Use an incrementing counter kept in the db, or `time()` + `GetTime()` fraction. |
| C3 | Low/Med | `Nav.lua` `InstallTomTomShim` | We write a fake `_G.TomTom` with only `AddWaypoint` / `RemoveWaypoint` when real TomTom is absent. Any other addon that finds `TomTom` and calls another method (for example `SetCrazyArrow`, `GetClosestWaypoint`) will throw an error blamed on that addon. It is written at PLAYER_LOGIN and never when TomTom is installed, which is the right order, but an addon that tests `if TomTom then` gets a table that is incomplete. | Give the shim a metatable `__index` returning a no-op function for unknown names, or document it as a known trade-off. |
| C4 | Low | `Training.lua` `Training.All()` | Rebuilt on every call (about 100-150 spell lookups, one `IsPlayerSpell` each); `Upcoming` -> `Status` calls it twice, Home line a third time per refresh. Not a problem at today's call rate (refresh on events, not per frame), but it is the one function that could become one if someone calls it from an `OnUpdate`. | Cache per `(level, SPELLS_CHANGED)`; invalidate on `SPELLS_CHANGED` / `PLAYER_LEVEL_UP` / trainer events. |
| C5 | Low | `Training.lua` / `UI/Training.lua` | `GameTooltip:SetSpellByID(e.id)` with a shipped id that the client does not know (a Forever-only or removed spell) shows an empty tooltip; the saved-tip fallback only applies if a trainer visit saved one. | Fall back to name + rank + level text when `SetSpellByID` produces zero lines (`GameTooltip:NumLines() == 0`). |
| C6 | Info | `.luacheckrc` | The globals list now holds ~15 names that were added by hand to turn CI green. Fine, but it is a list that only grows. | Prefer `read_globals` for Blizzard API names (already how most are declared); keep `globals` for names the addon itself writes. |
| C7 | Info | `addon/tests/run_tests.py` | One 9,277-line / 673 KB file. Works, but navigating and reviewing diffs is slow, and a syntax error anywhere stops all 32 k checks. | Split by feature (`tests/test_talents.py`, `test_training.py` ...) when you next touch it. Not urgent. |
| C8 | Info | HARDENING L2 | Duplicated helpers (isSecret x3, vendor price x2, throttled refresh x5, two context-menu implementations) are still deferred; each new feature copied the pattern again (Aspect, CombatBanner, Training each wrote their own `safe`). | One `R2F.Util` with `safe(fn, ...)`, `isSecret(v)`, `throttle(fn, secs)` and replace the copies in one mechanical commit with the tests as the net. Best "tech-debt" task on the list. |

## Not covered (be honest)
- `UI/*.lua` layout code was only pattern-scanned, not read line by line (about 9 k lines). Design Critic and QA cover its behaviour.
- Nothing was run in the game client. The "taint-free" statement rests on code reading and on the owner's in-game tests, not on a live taint log.
- Generated data files were not reviewed here (see the Research/Data review).
