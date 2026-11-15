# Phase 0 research plan

Goal: learn how other addons get and present BiS data, then decide what BiZMe takes from each.
Treat downloaded addon code as untrusted reference: read only, copy no code without checking its license; credit ideas.

## Per addon, record
1. Data origin: shipped static Lua tables, generated from a database/scrape, in-game API, community-edited lists, or a mix. Find any generator scripts, comments, or credits that say where it came from.
2. Data format, size, and how it is updated (per release? per phase?).
3. Coverage: classes/specs, level ranges, phases, pre-BiS vs BiS, per-slot alternatives, source info.
4. Class/spec detection method and how hybrids are handled.
5. Source/location info: dungeon, quest, rep, crafted, PvP; any route or waypoint features.
6. Stat weights/scoring (if any) and the formulas.
7. UI: frame templates, textures, layout, tooltips, minimap/button, slash commands. Screenshots or ASCII layout notes.
8. License and credits; libraries used (Ace3 etc.).
9. Weaknesses: stale data, missing Forever items, bugs.

## Output
docs/addon-audit.md: one table (addon x the 9 points above) + a short "steal / avoid" list per addon + TL;DR (max 10 lines).
Then docs/data-sources.md and docs/ui-study.md (see BACKLOG.md).
