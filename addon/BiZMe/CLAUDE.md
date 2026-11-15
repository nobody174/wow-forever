# BiZMe! — Claude Code guide

BiZMe! ("BiZ" = BiS, "Me" = yourself) is a WoW Forever addon in the Road to Forever (R2F) family.
It shows best-in-slot (BiZ) gear per class/spec/level, auto-detects the player's class and spec
from talents, and plans a route to better gear. First and foremost it is for the owner (nobody174)
and his group; public release is NOT a goal yet.

## Start here (every session)
1. Read this file, then ROADMAP.md and BACKLOG.md. Work the top unfinished item in BACKLOG.md.
2. Read the repo root CLAUDE.md (its rules apply here: never hand-edit generated files, credits, tests) and the wow-dev-support-folder pointers. Do not repeat research already recorded there or in bis/README.md, bis/DATA_SOURCES.md, bis/OWN_DATABASE_PLAN.md.
3. Do not touch RoadToForever/ unless the task says so. Integration points are listed below.

## This is NOT greenfield: Mr.BiZ already exists
- Data: bis/ pipeline (ForeverDB per-level picks, levels 10-60, 27 specs) -> bis-data.json (site bis.html) and addon/RoadToForever/BiZData.lua. Sources in bis/sources.json, found_sources.json, quest-weapons.json.
- Addon: RoadToForever/BiZ.lua (BiS tab), BiZData.lua, GearScore.lua, Recorder.lua, QuestWeapons.lua, Nav.lua, Plan.lua.
- Owner decision 2026-11-13: Mr.BiZ keeps picking from ForeverDB (no own ranker). BiZMe reuses that data; it does not build a second database.
- BiZMe = the next-generation, standalone, better-looking version: new native-Blizzard UI, wishlist, upgrade engine, route planning, sharing. Phase 0 starts by inventorying what Mr.BiZ already does so nothing is rebuilt.
- Until BiZMe passes Mr.BiZ, leave Mr.BiZ in R2F untouched. Afterwards R2F can delegate to BiZMe. The owner decides that switch.

## Layout (repo: wow-forever)
- addon/BiZMe/       code + UI (this folder). Docs live here too.
- addon/BiZMe_Data/  data-only addon, LoadOnDemand, generated Lua tables. Never hand-edit generated files.
- Single source of truth for BiS/item data = the existing bis/ pipeline. Extend build_bis.py to also emit BiZMe_Data Lua; the site BiS page keeps reading bis-data.json.

## Rules
- All code, comments, docs in English.
- Reports and findings go in .md files in the repo (docs/), with only a short TL;DR in chat.
- Use Blizzard's own frame templates/atlases so the UI looks native. Prefer a tab on the Character frame. Keep the UI layer thin so skins can be added later.
- "Unknown source" is a first-class state. Never invent item sources; mark unverified data.
- Data from other sites/addons: check their terms first, credit them in README + in-addon About.
- Addons cannot make web requests. User-reported data = exported string pasted manually into the site/an issue.
- Tag nothing as a release. Changes land on main until the owner says otherwise.
- Test in-game by the owner; surface Lua errors to him with file/line, he returns the error log.

## Core design decisions (already made)
- Three layers of lists: BiZ (endgame BiS), Pre-BiZ, per-phase lists, plus computed "best available at level X" (stat weights, BiZ GearScore).
- Priority: level 60 Pre-BiZ first, then BiZ, but leveling must work too.
- Spec = talent tree with most points; always offer manual override and a "viewing as" class/spec selector (alts, helping friends).
- Source filters: dungeon, raid, quest, rep, PvP, crafted (by profession), world.
- "Next best upgrade obtainable now" while leveling. Do not suggest detours for items replaced soon, unless it carries ~5-10 levels.
- Route planning stays simple: ranked upgrade list first, waypoints via BiZNav (R2F) later. No TSP solver.
- Per-character wishlist; shareable "BiZ code" string for Discord.
- Forever item stats may differ from Classic. Verify against Forever sources before trusting any Classic list.

## R2F integration
BiZMe is standalone. R2F detects it (IsAddOnLoaded/GetAddOnInfo) and shows a launcher/tab; R2F may bundle BiZMe in its zip. BiZMe uses BiZNav only if present.
