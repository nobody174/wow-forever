# BiZMe! inside Mr.BiZ — Claude Code guide

DECISION (owner, 2026-11-15): there is ONE feature, **Mr.BiZ**, in the R2F addon and on the site.
"BiZMe!" is the personal mode of it: BiZ (best in slot) for Me (the logged-in character).
No separate addon. This folder (addon/BiZMe/) holds the plan and docs only; code goes in addon/RoadToForever/
(BiZ.lua, GearScore.lua, ...), data in the bis/ pipeline, site in bis.html.

## Start here (every session)
1. `git pull`. Read the repo root CLAUDE.md (hard rules), addon/ARCHITECTURE.md, then this folder's ROADMAP.md and BACKLOG.md.
2. Check wow-dev-support-folder findings-ledger.md before researching a client or data question; add ledger rows for reusable findings.
3. Read bis/README.md, bis/DATA_SOURCES.md, bis/OWN_DATABASE_PLAN.md, docs/professions-bis.md and BACKLOG.md section 3 (Mr.BiZ data) so nothing already decided is redone.
4. You know the code; the plan was written from outside it. Before building, review ROADMAP.md/BACKLOG.md and write your suggested changes (order, scope, things that conflict with the code or existing decisions) to docs/plan-review.md, then update the plan files. Owner approves bigger changes.
5. Then work the top unfinished BACKLOG.md item.

## Product idea
- Mr.BiZ tab gets two modes: **BiZ** (browse lists for any class/spec/level) and **BiZMe!** (your character: auto-detected class/spec, your gear vs BiZ, wishlist, next best upgrade, route).
- Auto-detect spec from talents (tree with most points) with manual override and a "viewing as" selector (alts, helping friends, Discord talk).
- Lists: BiZ (endgame), Pre-BiZ (level 60 first priority), per-phase lists, plus computed "best available at level X" for leveling (stat weights / BiZ GearScore).
- Source filters: dungeon, raid, quest, rep, PvP, crafted (by profession), world. "Reachable now" toggle.
- Upgrade engine: next best upgrade obtainable NOW. While leveling, no detours for items replaced soon unless it carries ~5-10 levels.
- Route: ranked upgrade list first, then waypoints via BiZNav (Nav.lua). No TSP solver.
- Per-character wishlist; shareable "BiZ code" string for Discord (site link too).
- UI: look native. Use Blizzard frame templates/atlases, ideally a tab on the Character frame; keep the UI layer thin so skins can come later. Design inspiration: ForeverDungeonJournal (installed addon, read only).

## Constraints and decisions already made
- Mr.BiZ keeps picking from ForeverDB (owner 2026-11-13, no own ranker); Forever item stats may differ from Classic: verify, never assume.
- Priority: level 60 Pre-BiZ, then BiZ, leveling must work too. First and foremost for the owner and his group; public release is not a goal.
- "Unknown source" is a first-class state. Never invent item sources.
- Addons cannot make web requests: user-reported data = exported string pasted into the site/an issue/a file in the repo. No backend unless the project goes public.
- Other sites' data: check terms, credit them (ForeverDB + Wowhead stay credited under Mr.BiZ).
- Optional later: split the BiZ data into a load-on-demand data addon if memory/size becomes a problem. Not now.
- Reports go in .md files in the repo (docs/), only a short TL;DR in chat. All code and comments in English.
- Follow the repo workflow (build.py, addon tests, push to main, BACKLOG -> CHANGELOG -> news.json). No release tags until the owner says.
