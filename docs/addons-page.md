# Addons page and the daily version check

How addons.html is built and how the scheduled version check works. Moved out of CLAUDE.md 2026-10-16.

- `addons.html` — hand-written page. An "Our own addon" section on top (Road to
  Forever, `data-addon="roadtoforever"`, links to its GitHub release, not
  CurseForge), then "What we use" (the owner's actual list, 2026-10-10): AtlasLootClassic
  Continued, Forever Bestiary, Leatrix Maps, ThreatMaster and Questie (ForeverPlus and TomTom removed 2026-10-15, their functions are in Road to Forever; Questie restored 2026-10-16 at the owner's request, known issue: party quest progress not showing; keep watching new versions) — all CurseForge links, sorted alphabetically (case-insensitive) —
  plus a link to wow4ever.quest's addon compatibility tracker.
  Compact card layout (2026-10-05): a `.pick` column on the left holding the
  Select checkbox (the whole strip is the click target), then `.card-main` with
  a `.card-head` row — the addon name button (`.addon-btn`, links to CurseForge)
  left-aligned and the gold `.dl-btn` Download right-aligned on the same row —
  then the `.ver` line, then all description/notes inside
  `<details class="more"><summary>Details</summary>…</details>` (collapsed by
  default). New cards must follow this markup. Cards sit in `.addon-grid`
  (auto-fill, min 330px per column; 3 columns from 1100px wide, 2 on laptops,
  1 on phones; `align-items:start` so an opened Details only grows its own
  card). Page `.wrap` is 1180px wide; keep name buttons short enough to sit
  beside Download at 3 columns (AtlasLootClassic Continued is shown as
  "AtlasLoot Continued" with the full name in `title`).
  The button links to the addon's **WoW Forever file page**
  (`/wow/addons/<slug>/files/<fileId>`), not the project page, and under it a
  `<div class="ver" data-addon="<slug>">` line shows `Forever version <b>X</b> ·
  <upload date>`. The lede's `#versions-checked` line holds the date of the last
  check. Hand-edit directly.
  **Downloads:** every addon card is a `.dl-card` with `data-slug` (and, for
  CurseForge addons, `data-project` = CurseForge's numeric project id), a
  "Select" checkbox and a gold **Download** button, built in JS from the card's
  `.addon-btn` href (so the version check only keeps that href current):
  - CurseForge addon → `https://www.curseforge.com/wow/addons/<slug>/download/<fileId>`
    in a small pop-up window (`curseforgeDownload()`), which CurseForge starts
    the file from after ~5 s; our page closes the pop-up after 9 s
    (`POPUP_CLOSE_MS`; a page may close windows it opened, even cross-origin).
    Verified 2026-10-05 in the owner's Chrome: file arrived, pop-up closed. If
    pop-ups are blocked, the link falls back to a normal new tab. Tested
    2026-10-05 in the owner's Chrome: CurseForge does NOT let other sites start
    its files. `edge.forgecdn.net`/`mediafilez.forgecdn.net` links (redirect to
    mediafilez, 503) and `/api/v1/mods/<id>/files/<fileId>/download` from our page
    never produced a file; only CurseForge's own download page did. Don't retry
    these without a real download test (check the Downloads folder, not the
    network log — it showed 503 even for working CurseForge downloads).
  - Road to Forever → `.../releases/download/r2f-v<ver>/RoadToForever-<ver>.zip`,
    downloaded right on the page.
  The bottom tray's gold button walks the ticked addons: each press starts the
  next one ("Next: Questie (2 of 3)"), because browsers allow one pop-up per
  click. A hidden iframe of the download page does NOT work (tested). One combined zip isn't possible: neither forgecdn nor GitHub
  release files allow other sites to read them (CORS), and re-hosting other
  authors' addons ourselves needs their permission. Selection: localStorage
  `wf-addons-selected-v1`.
  **Addon version check (run daily by a scheduled task, or on request):**
  1. For each `data-addon` slug, WebFetch
     `https://www.curseforge.com/wow/addons/<slug>/files/all` and take the newest
     file whose flavor is **Forever** (game version 1.60.x). Use the files list,
     not the project page's "Recent Files" sidebar — the sidebar lags behind
     (on 2026-10-05 it showed Leatrix Maps 1.60.11 while 1.60.12 was out).
     Multi-flavor files count only if Forever is in their flavor list (TomTom
     ships one file for every flavor; open the file page to confirm).
     Never pick a Retail/Classic/MoP/TBC/Titan file. Release type R preferred;
     only use a beta/alpha file if no R exists for Forever.
     Multi-flavor addons (AtlasLootClassic Continued, Questie, TomTom)
     show "Forever + N" in the list. CurseForge's list can come back stale or
     filtered to another flavor (on 2026-10-05 Prat's list first showed only
     August files without Forever); if no Forever file shows, read the project
     page's "Latest release ... Forever + N" line and confirm on that file's page
     that 1.60.x / Forever is in its supported versions before using it.
     Watch the slugs: Forever Bestiary is `forever-bestiary-pet-hunter`,
     AtlasLoot is `atlasloot-continued`.
     **Since 2026-10-13 the Road to Forever card updates itself in the browser:** a small script in
     addons.html asks GitHub's releases API (`/repos/nobody174/wow-forever/releases`, cached 10 min in
     localStorage `wf-r2f-release-v1`) for the highest `r2f-vX.Y.Z` that is not a draft and rewrites the card's link, `v<ver>` tag,
     version/date line and the zip name (`code[data-zip]`). The values written in the HTML are only the fallback when GitHub
     can't be reached, so a release no longer needs an addons.html commit; refresh the fallback now and then
     (link, `.ver-tag`, `.ver` line, zip name). The manual rules below still describe how the fallback is read.
     `roadtoforever` is ours and not on CurseForge: its version is the newest
     `r2f-v*` tag (`git ls-remote --tags origin 'r2f-*' | sort -V`), cross-checked
     with `## Version` in `addon/RoadToForever/RoadToForever.toc`, its date is
     the tag's commit date, and the button links to
     `https://github.com/nobody174/wow-forever/releases/tag/r2f-v<version>`
     (the repo was renamed from `wow-forever-macros` to `wow-forever`; GitHub
     redirects the old name). Versions below 1.0.0 are GitHub pre-releases, so
     keep "· pre-release" on the line until 1.0.0; also update the small `v<version>` tag next to the name
     (`.ver-tag`, data-ver="roadtoforever") and the zip name in
     the card's Install note.
  2. If newer: update that card's link file id, version and date.
  3. Always set `#versions-checked` to today's date (e.g. `Oct 6, 2026`).
  4. If a project page 404s, retry once, then check `/files/all` — WeakAuras
     Forever's project page 404'd on 2026-10-05 while its files list worked.
     If both fail, leave the card unchanged and mention it in the commit message.
     WebFetch can serve cached CurseForge pages: WeakAuras Forever was really
     gone on 2026-10-05 (404 in a real browser) while WebFetch still showed its
     files. It was replaced by ForeverAuras. If an addon disappears again, grey
     its card out with `.card.unavailable` (drop the `dl-card` class and the
     download row, `.ver.gone` line "Removed from CurseForge") and tell the user.
     In a real browser on curseforge.com, `fetch('/api/v1/mods/<id>/files?pageIndex=0&pageSize=10&sort=dateCreated&sortDescending=true')`
     returns the true file list as JSON (`fileName`, `gameVersions`, `releaseType`
     1 = release); use it when the browser tools are available.
  5. The shell can't reach CurseForge (proxy blocks it); use WebFetch only.
  6. Always commit and push to `main`, even when only the date changed: a
     date-only bump gets its own commit ("Addon versions checked <date>, no changes"), so the
     page shows the check is alive. Add version bumps to CHANGELOG.md.
