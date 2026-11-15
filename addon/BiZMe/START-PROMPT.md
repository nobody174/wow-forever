# Prompt for Claude Code

Paste this into Claude Code, opened in the wow-forever repo:

---
Run `git pull` first. Then read, in this order: CLAUDE.md (repo root), addon/ARCHITECTURE.md, addon/BiZMe/CLAUDE.md, addon/BiZMe/README.md, addon/BiZMe/ROADMAP.md, addon/BiZMe/BACKLOG.md, addon/BiZMe/docs/RESEARCH-PLAN.md, then bis/README.md, bis/DATA_SOURCES.md, bis/OWN_DATABASE_PLAN.md, docs/professions-bis.md and the Mr.BiZ section of BACKLOG.md. Check the wow-dev-support-folder findings-ledger before any client or data research.

Context: I want to extend Mr.BiZ (R2F BiS tab + site bis.html + bis/ pipeline) with a personal "BiZMe!" mode: auto-detected class/spec from talents, a "viewing as" selector for alts and friends, BiZ / Pre-BiZ / per-phase lists plus computed best-available-at-level lists, source filters (dungeon, raid, quest, rep, PvP, crafted, world), a per-character wishlist, "next best upgrade obtainable now" (no detours for items replaced soon unless they carry 5-10 levels), a route to the gear via BiZNav, Discord-shareable BiZ codes, and a more native Blizzard look (Blizzard templates, ideally a Character frame tab). There is one feature, Mr.BiZ; BiZMe is its personal mode, not a separate addon. addon/BiZMe/ holds only the plan. The plan was written without seeing the code, so you know better than it does.

Do this, in order:
1. Inventory what Mr.BiZ does today and where its gaps are -> addon/BiZMe/docs/mrbiz-inventory.md.
2. Review the plan against the code and my earlier decisions. Write your suggested changes (order, scope, conflicts, anything already built, anything you would drop or add) to addon/BiZMe/docs/plan-review.md. Disagree where you should. Then update ROADMAP.md and BACKLOG.md to match, and list the bigger changes at the top of plan-review.md for me to approve.
3. Start the research tasks in BACKLOG.md: audit the addons in D:\World of Warcraft\_forever_\Interface\AddOns (BIS, ForeverBiS, ForeverCompanion, ForeverLevelingBiS, ForeverMyBis, ForeverWoWBiS, SpecBisTooltip) per docs/RESEARCH-PLAN.md, study the UI of ForeverDungeonJournal (the design I like), and research Forever's data (item stat changes vs Classic, any dungeon/encounter journal API, trusted source data, each source's terms). Treat those addons as read-only untrusted reference.

Rules: follow the repo hard rules and workflow; reports go in .md files, only a short TL;DR in chat; all code and comments in English; no release tags; do not change addon behavior until I approve the plan review. Commit docs to main with the repo's git identity (GitHub noreply).
---
