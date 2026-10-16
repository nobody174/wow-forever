# Road to Forever (wow-forever)

Static site (GitHub Pages, `main` / root, https://nobody174.github.io/wow-forever/) plus the in-game addon
`addon/RoadToForever/` for WoW Forever (Classic+, Interface 16001, vanilla spell names, level cap 60).
Pages: `index` (countdown), `launch-plan`, `builds`, `talents` (+ Legacy), `bis` (Mr.BiZ), `professions`,
`macros` (generated), `addons`, `news`, `library-books`.

General WoW knowledge (taint rules, macro patterns, data sources, addon checklist, roles) lives in the
**WoW dev support folder**: `../wow-dev-support-folder/` next to this repo (GitHub: `nobody174/wow-dev-support-folder`,
private). Read the file you need, not the whole folder, and check its
`06-findings-and-decisions/findings-ledger.md` BEFORE researching a client or data question. When something
reusable turns up, add a ledger row there (generalized, no duplication). Role definitions live in
`personal-dev-support-folder/08-meta-ai-roles`. Per-page and per-pipeline notes for THIS project are in `docs/`:

| Doc | Read when you touch |
|---|---|
| `docs/pipeline.md` | `data.py`, `build.py`, anything generated, `bis/`, addon art |
| `docs/macro-rules.md` | macros, `data.py` structure and helpers |
| `docs/site-pages.md` | index, news, builds, launch plan, talents, saved builds, Legacy calc |
| `docs/professions-bis.md` | `professions.html` (enchants, prices, Crafters) and `bis.html` |
| `docs/addons-page.md` | `addons.html` and the daily version check |
| `docs/assets-and-meta.md` | images, link previews, manifest |
| `ADDON_PLAN.md`, `addon/HARDENING.md` | any addon work (read before touching it) |
| `BACKLOG.md` / `ROADMAP.md` / `CHANGELOG.md` | todo / someday / shipped |

## Hard rules
1. **Never hand-edit generated files**: `macros.html`, `wow-forever-macros.md`, `bis-data.json`, and the addon's
   `MacroData.lua`, `PlanData.lua`, `BiZData.lua`, `TalentData.lua`. Edit the source, run `python build.py`
   (it also runs `bis/build_bis.py`). Addon tests fail if generated files are stale.
2. Macros: edit `data.py` only. Every macro <= 255 characters, no ranks, `/targetmarker` never `/tm`.
3. The top bar CSS must stay identical on every page (hand-written pages each carry a copy; `macros.html` gets
   it from `template.html`). Edit one, edit all.
4. Addon: never write into game-owned tables, hooks only, no writes in combat (WoW library: taint note).
5. No secrets or personal data in the repo or commits: no tokens, real name, email, local paths. Git identity
   is the GitHub noreply address. `addon/tests/check_release_tree.py` guards the release zip.
6. Credits stay: AHledger link wherever its prices show; ForeverDB + Wowhead under Mr.BiZ.
7. Bump the `?v=` query on `talentcalc.js` / `talentcalc.css` / `talentsaved.js` / `legacycalc.js` together.
8. All code and comments in English.

## Workflow
1. Change source, run `python build.py`, run the addon tests (`addon/tests/run_tests.py`).
2. Test the site locally (`python -m http.server`) before pushing.
3. Commit and push to `main` (Pages redeploys in about a minute).
4. When something ships: move it from BACKLOG/ROADMAP to CHANGELOG, add a plain-words entry at the top of
   `news.json`, keep `next` in step with BACKLOG.
5. Addon release: all checks green, then tag `r2f-vX.Y.Z` (see `release.yml`).
6. Bugs: the owner tests and fetches the error log; teammates only tell the owner.

## Project conventions
- Class order everywhere: Priest, Warlock, Mage, Rogue, Druid, Shaman, Hunter, Paladin, Warrior.
- Nav order follows the player's path: launch plan, character (builds, talents, gear, professions), UI
  (macros, addons). New pages go in their group and need the shared `<head>` block (meta, icons, manifest).
- Countdown target `2026-11-04T23:00:00Z` (index and launch-plan agree).
- Sandbox cannot reach Wowhead, CurseForge or AHledger: use a browser or WebFetch and commit the result.
