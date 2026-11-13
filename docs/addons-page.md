# Addons page

How addons.html is built. Moved out of CLAUDE.md 2026-10-16; rewritten 2026-11-13 when the daily version check was stopped.

- `addons.html` is hand-written. No version checks, no scheduled task: nothing on this page is updated automatically.
- "Our own addon" (Road to Forever, `data-addon="roadtoforever"`) is the only card with a download. Its `.addon-btn` links to the GitHub release, and the Download button and "Select" checkbox feed the bottom tray. Its JS asks the GitHub releases API for the newest `r2f-vX.Y.Z` and rewrites the card's link, `v<ver>` tag, version line and zip name; the values written in the HTML are only the fallback. Refresh the fallback after each addon release: link, `.ver-tag`, `.ver` line and zip name. Versions below 1.0.0 stay marked "· pre-release".
- "What we use" lists the CurseForge addons (AtlasLoot Continued, Forever Bestiary, Leatrix Maps, Questie, ThreatMaster), sorted alphabetically. Each name button links to the addon's CurseForge project page, and the card says to download the WoW Forever (1.60.x) file there by hand. These cards have no Select box, no Download button and no version line, because a copy would go stale. To update one of them, the owner downloads from CurseForge; nothing on the site needs changing.
- Card markup for a new CurseForge addon: a plain `<div class="card">` with `.card-main`, a `.card-head` holding the `.addon-btn` link to the project page, a `.ver` line that points to CurseForge, and `<details class="more">` for the description.
- Only `.dl-card` cards join the tray; the CurseForge cards are plain cards and are not part of it.
- Earlier history (per-file links, the CurseForge pop-up download, the `#versions-checked` date, the daily check) is in CHANGELOG.md and git history.
