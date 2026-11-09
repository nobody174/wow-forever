# Review 4: Technical Writer + Editor / Proofreader

Date 2026-11-09. Read-only. Scope: README (root and addon), both CHANGELOGs, BACKLOG / ROADMAP, `docs/*.md`, `addon/dev/TESTING.md`, the in-game text (`Locale.lua`, 877 strings), and the visible copy of the site pages. Two audiences are kept apart: **players** (site, addon README, addon CHANGELOG, in-game text) and **maintainers** (CLAUDE.md, docs/, ADDON_PLAN, root CHANGELOG).

## Verdict
The writing is clear, plain and consistent in voice, with short sentences, no hype, honest about what is unverified. The in-game strings are clean (877 checked for doubled words, stray spaces and punctuation: only intentional indents). What is wrong is almost entirely **freshness**: documents written for the weeks before launch were not rewritten when launch happened, and two public documents are now incomplete about what the addon does.

## Player-facing findings

| # | Sev | Where | Finding | Fix |
|---|---|---|---|---|
| W1 | **High** | Site: Index, Builds, Talents, Mr.BiZ, Professions, Launch plan, Addons | **Pre-launch voice after launch.** Examples: "can change before launch on November 4" (Builds, Professions), "When WoW Forever launches on November 4 ..." (Mr.BiZ), "In the beta every character has it; at launch you start with no Legacy points" (Builds and Talents, the Legacy card), "Draft. Levels 1-30 are checked against what the beta shows" (Launch plan), "Forever's addon API is still filling in during beta" (Addons), "Launching tonight?" (Index). `docs/launch-day.md` step 5 even lists "remove the BETA-RIBBON block" and it was not done. | One post-launch copy pass. Write each fact in the present tense, from what the live client does. Where it is not yet known, say "not yet checked in the live game" instead of "beta". Keep a list of every place changed in `CHANGELOG.md`. |
| W2 | **High** | `addon/RoadToForever/README.md` ("What it changes in your game") | The list claims the addon writes to the game only in three ways (macros, Quick settings, bag windows / red error text). That is no longer complete: **Setup** places macros on action bars and clears buttons, **sets key bindings** (`SetBinding` + `SaveBindings`), toggles action bars (`SetActionBarToggles`), applies chat window settings ("General settings"), and a **talent learn** path exists. None of it is in the README; "Setup Hunter / Setup Druid" is not mentioned anywhere in the player README. A README that promises "only these ways" and is then wrong is a trust problem, and it is the first thing CurseForge reviewers read. | Add Setup and General settings to the list, each with "asks first / out of combat / can be undone with Undo". Say that Setup writes key bindings. |
| W3 | Med | Addon README, "It has six pages" | There are seven tabs (Training was added). "Seven looks" is correct. Training, the Hunter aspect reminder and the pet-aware combat banner are not described; `/r2f aspect` is not in the command table. | Update the count, add Training to the page list, add Aspect to the reminders list and the command table. |
| W4 | Med | Addon README, Install | Says "Interface/AddOns/ of your WoW Forever installation". Correct, but the site's Addons page tells people `_classic_beta_` (see Design D3). Two documents, two answers. | One sentence, used in both places: the game folder name for Forever (`_forever_`). |
| W5 | Med | Addon CHANGELOG (shipped to players) | Entries are accurate but heavy: one 0.84.2 bullet carries a game build number, a source site name and the details of capped ranks. For players the first sentence is enough; the rest is maintainer history and already lives in the root CHANGELOG. 0.83.0 also mixes two older items (`/r2f setup show`, Duo progress) under it with no heading. | Keep two sentences per release in the shipped file; move detail to the root CHANGELOG. Put each release's items under its own heading. |
| W6 | Low | Home text in game | The Home card still says "FOREVER LAUNCHES IN" with the date and switches to "Forever is live" at zero. Correct behaviour; but a player who installs after launch sees an extra "countdown" feature that is permanently "live". | Hide the countdown card after launch + 7 days, or replace it with "Season/phase news". Low priority. |
| W7 | Low | Terminology | The same thing has several names: tab **Gameplay** in code and the `/r2f gameplay` command, **Tweaks** in the UI; `/r2f settings` opens **Home**; "Plan" vs "Launch plan"; "Gear" vs "Mr.BiZ" vs "Best in slot" vs "BiS"; "Builds & talents" tab vs "Talents" in commands and docs. A player reading the README and typing commands hits all of them. | Pick the UI name as the canonical one and list command aliases in one table row each (`/r2f tweaks` as an alias is cheap). |
| W8 | Info | In-game strings | `SETUP_FINISHED` starts lowercase ("setup finished. Macros of spells ..."); `BIZ_FOOTER` and `PLAN_BUY_VERIFY` carry "beta". Otherwise clean. | Capitalise; reword with W1. |

## Maintainer-facing findings

| # | Sev | Where | Finding | Fix |
|---|---|---|---|---|
| W9 | Med | `addon/dev/TESTING.md` | Header says "Checked against release 0.80.1 on 2026-10-20"; the addon is at 0.84.2. Items 5.72 to 5.78 say "(next release)" for features that shipped in 0.82-0.84. The 0.84.1 changelog says the talent board art and Training list were **confirmed in game** (5.76-5.78 likely belong in COMPLETED_TESTING). | A five-minute tidy: update the header, replace "(next release)" with the shipped version, move what you confirmed. |
| W10 | Med | `BACKLOG.md` section 0 | "Launch-day reminders (2026-11-04)" is still the first section. The date is past; items 1-3 are either done, owner-only or overdue (item 3 "Launch-day data refresh before the countdown ends" did not happen, see Research R3). Section 5 repeats it. | Fold 0 into 5 as "Post-launch refresh (launch was 2026-11-04)", with each item marked done or overdue. |
| W11 | Med | `ADDON_PLAN.md` (3,253 lines, 216 KB) | CLAUDE.md says to read it before any addon work. At that size nobody does, and it is a build log (sections 19, 17, 18, 20, 21 are out of order; it ends at "since 0.55") rather than a plan. | Documentation Architect pass: a 150-line `addon/ARCHITECTURE.md` (modules, data flow, rules, where each feature lives) and mark ADDON_PLAN as "design history, read by section". CLAUDE.md should point to the short file. |
| W12 | Low | `CHANGELOG.md` (root, 3,161 lines) | Complete and honest, but one file for site + addon, newest first. Finding "when did X change" works; reading it does not. | Split yearly or per area when it passes about 4,000 lines; add a table of contents by date range at the top now. |
| W13 | Low | `CLAUDE.md` | Lists pages without `hunter.html`, which exists and is in the nav. States "level cap 60" (true) but also countdown target in "conventions" which is now history. | Add the page; reword the countdown line as "launch date, passed". |
| W14 | Info | Docs overall | `docs/` is well organised: each file has a "read when you touch X" row in CLAUDE.md, dated, with the why. This is the best-kept part of the repository; keep the habit. | None. |

## Style notes (for future copy)
- Prefer "since the 3-4 November update" to "after the beta" and "launch" (dates age better than events).
- State uncertainty once, on the item, not in a banner on the page ("not yet checked in game" tag on the 33 unverified steps is the right pattern, the "Draft" banner is not).
- Tone is good: direct, no marketing. Keep "Tell us if a class looks off." It invites the right feedback.

## Not covered
- Full proofreading of the 3,000-line CHANGELOGs and ADDON_PLAN (sampled the top entries and the structure only).
- Spelling of the site HTML bodies beyond what was visible in the rendered pages and the strings scan.
