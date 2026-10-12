# Road to Forever: pre-release hardening

Hardening sequence before the first public release (CurseForge): the owner's "4. Hardening" workflow
(Project Reviewer -> Fixer -> Debugger if needed -> Security -> QA -> Devil's Advocate -> Design Critic -> Docs ->
Release Manager / DevOps -> Project Reviewer round 2), with WoW-specific additions: the security step is a Taint &
Secure Execution + WoW API Compliance pass, a Lua performance pass is added (4b), and step 1 includes a
Privacy / Identity check (published as nobody174).

This file sits outside `addon/RoadToForever/`, so it never ships in the addon zip.

Decisions (owner, 2026-10-12):
- Author nobody174, name "Road to Forever" (R2F), license All Rights Reserved.
- H5 Plan tab: make it generic (no names, plans read as example setups).
- H2 error filter: rebuild it without touching Blizzard's frame (owner re-tests in game).
- M3 debug commands: move under `/r2f debug`; `/r2f help` lists player commands only.
- First public release: 1.0.0.

## Progress (Step 2: Fixer)

Done, committed (`2f7948d`), 17885 tests passing:
- [x] H1 dead Copy-my-build URL
- [x] H2 error filter rebuilt on RegisterEvent/UnregisterEvent (no Blizzard reassignment);
      owner still needs to re-test in game
- [x] H3 single-backslash icon path, plus a permanent regression test for the whole bug class
- [x] H4 personal name stripped from GameplayExtras.lua comments, CHANGELOG.md, and
      PlanData.lua (via launch-plan.html + `python build.py`)
- [x] H5 Plan tab's example plans no longer name specific players ("this group" → "example
      setup", the one "Venom + Trollmann" line reworded)
- [x] M3 debug commands moved under `/r2f debug`, `/r2f help` trimmed to player commands,
      old bare command names (`/r2f rankdebug` etc.) still work
- [x] L1 Ammo reminder uses `BAG_UPDATE_DELAYED`, ignores other units' `UNIT_INVENTORY_CHANGED`

Done in the second session (all committed, 17887 tests passing, luacheck 0 warnings):
- [x] M1 dev comments cleaned (about 500 lines touched, proven comment-only with
      `addon/tests/check_comment_only.py`)
- [x] M2 README.md + short player CHANGELOG.md ship; TESTING.md and the dev CHANGELOG.md
      moved to `addon/dev/` (not shipped)
- [x] M4 CI (`.github/workflows/ci.yml`: tests, luacheck, release-tree check); release.yml
      now needs it
- [x] M5 luacheck globals (0 warnings)
- [x] M6 taint audit:
      - TalentGuide: removed `ToggleTalentFrame()` (it ran game logic in our name). The
        addon now only reads whether the window is open and asks the player to press N.
      - Bags: the `frame.r2fDragging` field written onto Blizzard's bag frames is now a
        local `dragging[frame]` table.
      - Professions `prepare()`: C-API only, low taint risk, but it changes the player's
        filter UI state. Needs in-game QA.
      - GameplayQuests: our check boxes are parented to Blizzard's header buttons, no field
        writes, low risk.
- [x] M7 LICENSE, .toc fields, version 1.0.0
- Needs in-game re-test by the owner: rebuilt error filter, guided mode and preview mode
  (no longer open the talent window by themselves).

Not started yet:
- [ ] (deferred, post-1.0 refactor) L2 duplicated helpers (isSecret ×3, vendor price ×2, throttled-refresh ×5, two
      context-menu implementations) — likely low priority
- [x] L3 promise line already gone (grep finds nothing)
- [ ] (skipped, owner's call) L4 import doesn't flag `/run`/`/script` in macro bodies — low priority, likely skip
- [x] L5 talentsaved.js and template.html/macros.html now use nobody174/wow-forever. addons.html still shows 0.29.1 pre-release: update when 1.0.0 is tagged.
- [x] Privacy/identity: re-checked 2026-10-12. No commit carries vartdal@gmail.com (the earlier "19 commits" note was wrong). All 82 public commits use nobodylearn174@gmail.com (plus Claude's noreply). Owner's call whether to switch to GitHub's noreply address for new commits.

Remaining workflow steps after Step 2 finishes: 3 Debugger (only if something unclear turns
up), 4 Taint & Secure Execution + WoW API Compliance audit (M6 above), 4b Lua performance
pass, 5 QA/Playtester, 6 Devil's Advocate on the fixes just made, 7 Design Critic, 8 Docs
(README/CHANGELOG, part of M2), 9 Release Manager/Versioning (M7) + 9b CI (M4), 10 Project
Reviewer round 2 to close the loop. Then: set up the actual CurseForge project page/release.

## Step 1: Project Reviewer, full analysis (2026-10-12)

Scope: every file the release zip contains (`addon/RoadToForever/`, 44 files, ~17,000 lines incl. the generated
BiZData / PlanData), against the goals in ADDON_PLAN.md and a public CurseForge release. Read file by file; UI files
read in part, plus scans for hooks, CVar writes, global writes, timers, URLs, escapes and personal data.

Overall: the logic is careful and defensive (every API guarded, combat rules respected, irreversible talent writes
verified point by point, 17,873 passing tests). What stands between it and a public release is mostly presentation
(internal notes everywhere), three real bugs, a few taint risks and missing public basics.

### High

- **H1 Copy my build gives a dead link.** `Talents.lua:29` builds links on
  `nobody174.github.io/wow-forever-macros/talents.html`; since the repo rename that address is GitHub Pages' 404
  (checked in a browser). Must be `nobody174.github.io/wow-forever/`. The tests pin the old URL too.
- **H2 Error filter writes into Blizzard's own frame.** `Gameplay.lua:229-240` replaces `UIErrorsFrame.AddMessage`
  with our function. That is exactly what the addon's own rule forbids ("never write into the game's tables",
  CLAUDE.md): Blizzard code calls that method, and on this secret-values client tainting it can break the game's
  own code the way the combat-text path did in 0.27.0. Needs another approach (e.g. our own UI_ERROR_MESSAGE
  handler) or removal.
- **H3 Reactive-alert marker shows no icon.** `GameplayExtras.lua:339` uses `"Interface\Icons\..."` with single
  backslashes; Lua 5.1 drops unknown escapes, so the path becomes `InterfaceIcons...` (missing texture).
- **H4 Personal data in the zip.** The owner's character name ("Venom Oathbreaker") in comments
  (`GameplayExtras.lua:25, 39`), "Venom + Trollmann" in the generated `PlanData.lua` (from launch-plan.html), more
  names in CHANGELOG.md / TESTING.md.
- **H5 The Plan tab is our group's private launch plan** (our group compositions, "Venom + Trollmann", our route).
  For strangers on CurseForge it is someone else's checklist. Design call: keep, make generic, or leave it out of
  the public build.

### Medium

- **M1 Internal dev notes throughout the code.** ~2,500 comment lines, many written for us, not for a reader:
  73 references to ADDON_PLAN sections (not in the zip), build "step" numbers, version history ("v0.10.0: ..."),
  "owner test" notes with dates, "the user's screenshot", "TESTING.md 33" pointers, and stale claims ("Nothing here
  has run against the Forever client yet", "Character 7 / 18" macro slots). Rewrite as short comments that explain
  the code; keep the real "why" (taint rules, client quirks).
- **M2 Internal files ship.** TESTING.md (1,221 lines, our in-game checklist) and an 853-line developer CHANGELOG.
  Players need a README and a short changelog.
- **M3 Debug commands in the public help.** `/r2f who, gossip, reactlog, auras, rankdebug, profdebug, bags` are
  tools for us; the help list mixes them with player commands in no order, has outdated text ("for the planned
  buff reminders") and asks to "paste them to us" without saying where.
- **M4 No CI.** The release workflow builds and publishes on a tag without running the tests or luacheck.
- **M5 luacheck can't gate anything yet.** ~355 warnings: mostly `.luacheckrc` lacking WoW API globals, plus unused
  variables and lines over 130 characters.
- **M6 Taint candidates for step 4.** `TalentGuide.lua:189` calls Blizzard's `ToggleTalentFrame()` from addon code
  (opens the talent UI in our name); `Professions.lua` `prepare()` calls Blizzard's filter / expand functions
  (classic trade-skill path); `Bags.lua` moves Blizzard's bag windows (deliberate and combat-guarded; re-check).
- **M7 Missing public basics.** No README, no LICENSE, no `## X-Website` / `## X-License` in the TOC, TOC comments
  point at internal docs. Version: 0.30.0 now; decide whether the first public release is 1.0.0.

### Low

- **L1 Ammo reminder** rescans every bag slot on each `BAG_UPDATE` (fires once per bag); `BAG_UPDATE_DELAYED` would
  coalesce. `UNIT_INVENTORY_CHANGED` is not filtered to the player.
- **L2 Duplicated helpers:** `isSecret` in 3 files, vendor price in 2, the throttled refresh pattern in 5, two
  context-menu implementations (MacroBook's own and `UI.ContextMenu`).
- **L3 UI promises:** "More are planned (pet, repairs, bags)" on the reminders tab.
- **L4 Import:** macros containing `/run` or `/script` aren't called out in the import preview (the tooltip shows
  the full text and nothing is created until dragged, so low).
- **L5 Site, not addon:** `talentsaved.js` still uses `nobody174/wow-forever-macros` for the Group picks API (may
  fail on the rename redirect); template.html's release link uses the old name (redirects fine).

### Privacy / identity

- Code and data: covered by H4 (character and friend names). No email, real name, local paths or tokens found.
- **Git history:** re-checked 2026-10-12: no commit has vartdal@gmail.com. The public commits use nobodylearn174@gmail.com. Setting the repo's git email to the GitHub noreply address stops it showing on new commits.

## Step 4b: Lua performance pass (2026-10-12)
- Checked: OnUpdate scripts (only the Bags drag watcher, Minimap drag, TalentGuide 0.2 s host; all run only while active), timers (no tickers), event registrations (Gameplay features register events only while switched on).
- Fixed: Buffs `UNIT_AURA` bursts are merged into one refresh per 0.2 s (it walked the whole group on every aura change). Quest-zone boxes `QUEST_LOG_UPDATE` / `QUEST_WATCH_LIST_CHANGED` merged into one redraw per 0.1 s.
- Accepted: reactive-alert `SPELL_UPDATE_USABLE` makes 6 `C_Spell.IsSpellUsable` calls per event, only while that alert is on. Cheap; a known-spell filter needs an API not verified on this client.
- Professions export/reading is already debounced (`schedule`).
- Not measured in game: needs the owner's in-game check (use the built-in addon CPU profiler: `/console scriptProfile 1`, then reload).

## Release plan (2026-10-12, owner's decision)
- 0.30.0 is tagged first as a GitHub pre-release test build (the hardened code, TOC 0.30.0). 1.0.0 and CurseForge wait until testing, reviews and the backlog are done.
- To ship 1.0.0: set the TOC to 1.0.0, rename the newest CHANGELOG heading to `## 1.0.0 (<date>): first public release`, update addons.html and news.json.
