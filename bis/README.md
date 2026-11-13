# Mr.BiZ data

`raw/levels/<class>-<spec>.json` holds one spec's best-in-slot picks for **every level from 10 to 60** (PvE), as runs of levels with the same pick,
read from ForeverDB's public pages (`https://foreverdb.net/bis/<class>/<spec>?lvl=<level>`). `build_bis.py` turns the 27 files into
`../bis-data.json` (the site's `bis.html`) and `../addon/RoadToForever/BiZData.lua` (the addon's BiS tab). Both keep per spec and slot the runs
`[from level, best row, [next rows], note?]` and one shared `rows` table; the site and the addon resolve a run into the pick for one level
(`slotsAt` in bis.html, `BiZ.SlotsAt` in BiZ.lua). The site opens on the level you chose last (`?lvl=39` opens that level); the addon follows your
own level until you step it on the tab.

## Refresh the data

1. `python bis/tools/foreverdb_levels.py` downloads every spec at every level into `bis/own/cache/levels/` (not in git): 27 x 51 pages, one per
   second with a user agent that names this project (about 25 minutes; it resumes, pages already there are skipped; delete the folder for a full refresh).
2. `python bis/tools/foreverdb_segments.py` parses the pages into `raw/levels/` (wording the parser does not know stops that spec with the slot named:
   add a rule to `SOURCE_START` in `foreverdb_fetch.py` and to `parse_source` in `build_bis.py`, never a guess).
3. `python bis/build_bis.py`: an unknown source sentence stops the build; "no source for next pick <id>" means add it to `sources.json`
   (`python bis/tools/foreverdb_sources.py` reads the item pages and fills it in); new item ids get their rarity by running `python bis/tools/items_build.py` (WCLBox cache, into `quality.json`), then `build_bis.py` again.
3b. `python bis/tools/recorder_import.py` (merge the recorder files) then `python bis/tools/found_sources.py`: fills picks whose source ForeverDB leaves unknown from
   our recordings, ForeverDungeonJournal (installed addon, read only) and `bis/own/web_sources.json` (hand-added `{"<id>": {"src": "<sentence>", "via": "<site>"}}`);
   run it before `build_bis.py`. Credits: ForeverDungeonJournal (loot lists), ForeverDB, Wowhead, and the players whose recordings are merged.
4. `python addon/tests/run_tests.py`, look at `bis.html` locally, bump `UPDATED` in `build_bis.py`.

Credit ForeverDB (picks, weights) and Wowhead (tooltips, item pages) wherever the data shows; both lines are on the page.
