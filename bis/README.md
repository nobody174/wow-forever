# Mr.BiZ data

`raw/<class>-<spec>.json` holds one spec's best-in-slot list, copied from ForeverDB's public BiS page
(`https://foreverdb.net/bis/<class>/<spec>`, level 30 PvE, the beta cap). `build_bis.py` turns the 27 files into
`../bis-data.json` (the site's `bis.html`) and `../addon/RoadToForever/BiZData.lua` (the addon's BiS tab).

## Refresh the data

1. For each spec, read its ForeverDB page and write the "Every slot" list into `raw/<class>-<spec>.json`:
   `{"build", "weights", "slots": [{"slot", "best": {"id", "name", "score", "stats", "src", "conf", "ease", "horde"?},
   "next": [{"id", "name", "delta"}], "note"?}]}`, 17 slots in page order, `best: null` + `note` for an empty slot.
   Item ids come from the `/item/<id>` links. (On 2026-10-12 this was done with WebFetch, one page at a time; the
   cloud shell can't reach foreverdb.net.)
2. Ranks 2-3 need a source too. If the build says "no source for next pick <id>", read
   `https://foreverdb.net/item/<id>` and add it to `sources.json` (`{"name", "src"}`, src in the BiS-page wording, e.g.
   `Drops from Lady Sarevess in Blackfathom Deeps, 40% (Classic data).`, `Quest reward: Frostmaw, level 37 · Horde
   (Classic data).`, `Crafted: Tailoring (Forever client).`, or `Where it comes from isn't known yet`).
3. `python bis/build_bis.py` (or `python build.py`). An unknown source sentence stops the build: add a rule to
   `parse_source` (or an instance to `DUNGEONS` / `CREATURE_INSTANCE` / `RAIDS`).
4. `python addon/tests/run_tests.py`, test `bis.html` locally, bump `UPDATED` in `build_bis.py`.

Credit ForeverDB (picks, weights) and Wowhead (tooltips, item pages) wherever the data shows; both lines are on the page.
