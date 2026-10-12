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
- **Git history:** the public GitHub repo has 19 commits authored as `nobody174 <vartdal@gmail.com>` (the rest use
  nobodylearn174@gmail.com). The release zip has no git history, but a CurseForge page that links the repo leads
  there. Rewriting public history is irreversible in practice (forks, caches) and is the owner's call; setting the
  repo's git email to the GitHub noreply address stops new ones.
