# Road to Forever

Companion site and in-game addon for **World of Warcraft: Forever** (Classic+): launch plan, builds, talent calculator, Mr.BiZ best-in-slot
gear, professions, macros and addon list. Site: https://nobody174.github.io/wow-forever/ . The addon lives in `addon/RoadToForever/`.

Developer notes are in `CLAUDE.md`, `ADDON_PLAN.md`, `BACKLOG.md`, `ROADMAP.md` and `CHANGELOG.md`.

## Data and credits

We build on other people's open work and say so:

* **Blizzard Entertainment** owns World of Warcraft, its game data and art. Item, recipe and faction tables are read from the game client.
  This project is not affiliated with or endorsed by Blizzard.
* **CMaNGOS** (classic-db, GNU GPL v2) and the **VMaNGOS** contributors: Classic drop, vendor and quest data, the base of most
  community loot databases.
* **AtlasLoot Continued** (Okrah, Lag and contributors, GNU GPL v2): the community's Forever dungeon loot lists, read from the addon's data file.
* **ForeverDB**, **ForeverChanges**, **Wowhead Forever**, **WCLBox**, **ZugZugDB**: the Mr.BiZ best-in-slot lists started from ForeverDB's
  and we keep checking our own numbers against these sites. Wowhead's tooltips are shown on the site. Prices come from **AHledger**
  (link shown wherever they appear).
* Our own recordings from play (loot, vendors, quest rewards) and our own scoring are being added so that Mr.BiZ does not depend on any one site
  keeping its data current. Research and decisions: `bis/DATA_SOURCES.md` and `bis/OWN_DATABASE_PLAN.md`.

Data we redistribute that comes from GPL sources keeps that licence note.

Fonts bundled with the addon (`addon/RoadToForever/media/fonts`, SIL Open Font License 1.1, licence files next to them): **Cinzel**
(The Cinzel Project Authors) and **Alegreya Sans** (The Alegreya Sans Project Authors), used by the Azeroth Reforged theme. **Barlow Condensed** and **Barlow** (The Barlow Project Authors) and **Chakra Petch** (The Chakra Petch Project Authors) are used by the Ember & Iron theme.
