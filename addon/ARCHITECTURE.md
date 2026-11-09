# Road to Forever addon: architecture in one page

Read this first; `ADDON_PLAN.md` is the design history (read one section at a time), `HARDENING.md` the safety rules and decisions.
It sits outside `RoadToForever/`, so it never ships.

## Shape
- One namespace: each file starts `local _, R2F = ...` and adds a table (`R2F.Talents`, `R2F.Training` ...). Modules call each other as `R2F.X.Y(...)`
  **at call time**, so the order of `RoadToForever.toc` is the integration contract: data and helpers first, features next, UI later,
  `UI\MainWindow.lua`, `Minimap.lua` and `Core.lua` last. `Core.lua` owns events, `PLAYER_LOGIN` (each module's `Init`) and the slash commands.
- Saved data: `R2FDB` (account) and `R2FCharDB` (character), defaults and `DB_VERSION` in `Library.lua`. Additive keys only so far; a rename needs a
  migration there plus a test (BACKLOG 5b).
- Text: every player-facing string is in `Locale.lua` (`R2F.L.KEY`). Theme colours and fonts go through `Theme.lua` (`R2F.Theme.PaintText`); a test
  forbids hard-coded text colours in `UI/*.lua`.

## Layers (load order)
1. **Plumbing**: `Locale`, `ItemApi`, `Base64`, `Library` (DB, macro library), `Import`.
2. **Generated data** (never hand-edit, see `docs/pipeline.md`): `MacroData`, `PlanData`, `BiZData`, `TalentData`, `TrainingData`, `QuestWeaponData`.
3. **Features**: macros (`Ranks`, `Macros`, `Setup`, `General`, `Bundle`), talents (`Talents`, `TalentCalc`), `Professions`, plan (`Plan`, `Progress`, `Nav`),
   Mr.BiZ (`BiZ`, `GearScore`, `QuestWeapons`), `Training`.
4. **Tweaks and reminders**: `Gameplay` (the registry: `R2F.Gameplay.Register{key, group, title, tip}`), `GameplayExtras/Quests/Chat`, `ActionBars`, `Bags`,
   and the reminder family on `R2F.Reminders.NewIcon` (`Stance`, `Ammo`, `Repair`, `Pet`, `Aspect`, `Timers`, `Rested`, `CombatBanner`, `Tracking`, `Buffs`);
   `QuickSettings` holds every CVar read and write.
5. **Observation**: `Recorder`, `RouteLog`, `Diagnostics`, `Version` (addon-message version check).
6. **UI**: `UI/Widgets`, one file per tab (`Plan`, `BiZ`, `Gameplay`, `Training`, `Settings`, `MacroBook`, `Home`, `TalentPanel`), the theme system
   (`Images`, `UI/Deco`, `DecoBook`, `DecoToy`, `ThemePicker`), then `MainWindow`.

## Rules that hold everywhere
- **Hooks only**: `hooksecurefunc` / `HookScript`; never replace a game function, never write into a game-owned table or frame field.
- **No writes in combat**: anything that changes game state checks `R2F.InCombat()` first and refuses (does not queue); multi-step flows re-check between steps.
- **Secret values**: unit data and auras go through `pcall` and `issecretvalue` before use.
- **Everything optional is off until ticked**; irreversible actions (learning talents) ask first.
- Input from other players (addon messages) is validated like pasted text and only saved, never applied.

## Adding things
- **A tab**: `UI/<Name>.lua` with `Build(page)` and `Refresh()`, entries in `UI/MainWindow.lua` (TABS, TITLES, LABELS, NAV), `Deco*` nav icon/colour maps, `Locale` keys, toc line.
- **A reminder**: copy `Aspect.lua` (small) - `R2F.Reminders.NewIcon`, db defaults in `Library.lua`, a `Gameplay.Register`, an `Init` call in `Core.lua`.
- **Generated data**: change the source, run `python build.py`; the tests fail if the output is stale.
- Tests: `addon/tests/run_tests.py` runs the real `.toc` under Lua stubs (`wow_stubs.lua`); CI also runs luacheck and `check_release_tree.py`.
