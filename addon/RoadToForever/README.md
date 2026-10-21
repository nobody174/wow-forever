# Road to Forever

A companion addon for **WoW Forever** (Classic+). It works together with the free
[Road to Forever website](https://nobody174.github.io/wow-forever/): copy your macros and
talent builds from the site into the game, send your talents and professions back to the
site, and see best in slot gear without leaving the game.

Made by nobody174. All Rights Reserved (see `LICENSE`).

## What it does

Open it with `/r2f` (or the minimap button). It has six pages:

- **Home**: the countdown to launch, the next step of your launch plan, what to train next,
  a share card for your professions, and the quick settings (a few game options, the minimap
  button). The **Theme** button opens the "Choose a look" gallery (see Looks below).
- **Launch plan**: the launch-day checklist from the site, with tick boxes. Each step can
  point the built-in arrow (BiZNav) at its spot; `/bizway` and Alt + right-click on the world
  map do the same for any spot. A **Quest shopping list** button swaps the steps for the
  quests whose items you can buy instead of farm, with a tick box for each.
- **Builds & talents**: a talent calculator for every class. Click freely without spending
  anything, pick any class by its icon (try your friend's Warrior while you play a Priest),
  save the build, share it with teammates who also have the addon, start from our
  recommended Tank / DPS / Healer builds, and, only on your own class after a trainer reset,
  learn it one point at a time. A confirmation comes first, and it never learns in combat.
- **Gear (Mr.BiZ)**: best in slot gear for every class and spec, with where it drops, how
  sure the source is, and a per-character wishlist.
- **Macros**: a spellbook-style book of every macro on the site, built into the addon. Drag
  one to your bars to create the real game macro. New addon versions update the macros the
  addon made, but never one you edited yourself. The Options button holds which slots new
  macros use, Import (for a custom pick from the site) and Remove all.
- **Tweaks**: small optional helpers, grouped on eight pages (Quests, Vendors & loot,
  Chat & screen, Bags, Alerts, Waypoint arrow, Class icons, Action bars), all **off until you tick them**:
  auto-repair, sell grey items, quest auto-accept and turn-in, fast looting, free bag slots,
  movable bags, a copy-chat box, an "ability ready" alert, and on-screen icons and reminders
  (Warrior stance, Hunter ammo, pet, gear repair, rested XP, missing tracking, missing group
  buffs, Walk on Air, Seal and Slice and Dice timers, food, a combat banner), and on the
  action bars a red veil when a spell is out of range or you lack the mana, rage or energy,
  and big cooldown numbers.

### Looks

Seven looks for the window: Classic (the original), Azeroth Reforged, Obsidian Night,
Ember & Iron, Frost & Void, Scribe's Tome and Gnomish Workshop. The Theme button on Home opens
a gallery: click a card to try that look on your window, then **Keep this look** or
**Revert** (it also goes back by itself after eight seconds). "Surprise me" tries a random one.
The size and opacity of the window are set at the top (or in the sidebar, in Ember & Iron).

### The route log

Off until you start it (`/r2f route start`). It writes down your route as you play (quests
and the order you did them, levels, the NPCs you opened windows with, your path and your own
notes) in your saved variables only, for working out the best way to start a new character.
`/r2f route note <text>` adds a note, `/r2f route stop` ends it. No character name is stored.

### The recorder

On by default, it writes down in your own saved variables what loot windows, vendors and quest
reward windows showed (`/r2f record` says how much; `/r2f record off` stops it). It is for
building Mr.BiZ's own item database. Nothing is sent anywhere unless you send the file yourself.

It also keeps spell ranks right in the macros it makes: on WoW Forever a plain spell name can
resolve to a rank you haven't learned, so the addon writes in the highest rank you know.

## Install

Unzip into the `Interface/AddOns/` folder of your WoW Forever installation so you get
`Interface/AddOns/RoadToForever/RoadToForever.toc`, then restart the game (or `/reload`).
The addon is for WoW Forever only. It loads no other addons and contacts no servers:
everything moves between the site and the game by copy and paste.

**One thing it sends:** by default it tells your guild and group, through the game's
addon-message channel, which addon version you run (one short line, shown to nobody; it is how
`/r2f update` can tell you a newer version exists, and you can turn it off in Tweaks > Chat &
screen). It sends nothing else about you.

## Getting started

1. On the site, tick macros in **Export macros** and copy the import string. In game, type
   `/r2f import` and paste it.
2. For talents: open the **Builds & talents** tab and click a build together (or paste a link
   from the site's calculator and press **Load**). **Save loadout**, **Share** it, or **Learn
   this build** (your own class, after a trainer reset).
3. `/r2f copybuild` copies your current talents as a link for the site.
4. Open each profession window once, then `/r2f profs` copies your recipes for the site's
   Professions page.

## Commands

| Command | What it does |
| --- | --- |
| `/r2f` | open or close the window (`/r2f open` only opens it) |
| `/bizway <x> <y> [label]`, `/r2f way`, `/r2f clear` | point the arrow at a spot; clear it (`/bizway size large` resizes) |
| `/r2f macros`, `/r2f talents` (`/r2ft`), `/r2f plan`, `/r2f gameplay`, `/r2f settings` | open that tab (`gameplay` = Tweaks, `settings` = Home) |
| `/biz`, `/mrbiz`, `/r2f bis` | best in slot (`/biz wish` opens the wishlist) |
| `/r2f import` | paste a macro import string from the site |
| `/r2f copybuild` | your talents as a link for the site |
| `/r2f profs` | your professions for the site |
| `/r2f copychat [window]` | a box with chat text you can select and copy |
| `/r2f stance`, `/r2f ammo`, `/r2f repair`, `/r2f pet`, `/r2f rested` | show or hide that icon (add `lock` to lock it, except rested) |
| `/r2f reminders` | the reminders settings |
| `/r2f record`, `/r2f record on` / `off` | what the recorder has seen; switch it |
| `/r2f route start`, `/r2f route note <text>`, `/r2f route stop` | the route log |
| `/r2f update` | is there a newer version (as heard from guild and group) |
| `/r2f minimap` | show or hide the minimap button |
| `/r2f debug` | troubleshooting tools; paste what they print into a report |
| `/r2f help` | this list in game |

## What it changes in your game

Most of the addon creates its own frames and reads game data. It writes to the game only in
these ways, each one something a player would do by hand:

- **Macros** you drag out of the book are created as real game macros.
- **Quick settings** on Home and some Tweaks change game settings (camera zoom, guild names,
  PvP titles, the 24-hour clock, weather) the same way the game's own options do.
- It can move the bag windows (Tweaks > Bags) and filter the red error text in the middle of
  the screen (Tweaks > Chat & screen).

Anything that writes waits until you are out of combat. Learning talents is the one action
that can't be undone, so it always asks first.

## Problems and feedback

If something goes wrong, `/r2f debug` lists troubleshooting tools; paste what they print into
your report. `/r2f copychat` is handy for copying Lua errors out of chat.

- Report a bug or send an idea: [Discord](https://discord.gg/Yh2sTMZksq) or
  [GitHub issues](https://github.com/nobody174/wow-forever/issues)
- Website: https://nobody174.github.io/wow-forever/

## Credits

Best in slot data comes from [ForeverDB](https://foreverdb.net/) and Wowhead; the addon
shows the source next to each pick. The quest-reward weapons on the Launch plan tab (and the
item rarity colours) come from [Wowhead](https://www.wowhead.com/forever)'s Forever item data.

The window looks use free fonts bundled with the addon (each with its licence file in
`media/fonts`): Cinzel, Alegreya Sans, Barlow, Barlow Condensed, Chakra Petch, Space Grotesk,
JetBrains Mono, Sora, Cormorant Garamond, Baloo 2 and Nunito.
