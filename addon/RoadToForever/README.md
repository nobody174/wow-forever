# Road to Forever

A companion addon for **WoW Forever** (Classic+). It works together with the free
[Road to Forever website](https://nobody174.github.io/wow-forever/): copy your macros and
talent builds from the site into the game, send your talents and professions back to the
site, and see best in slot gear without leaving the game.

Made by nobody174. All Rights Reserved (see `LICENSE`).

## What it does

Open it with `/r2f` (or the minimap button). It has six pages:

- **Home**: the next step of your launch plan, a share card for your professions, and the
  quick settings (game options, minimap button, movable bags).
- **Macros**: a spellbook-style book of every macro on the site, built into the addon. Drag
  one to your bars to create the real game macro. New addon versions update the macros the
  addon made, but never one you edited yourself. The Options button holds which slots new
  macros use, Import (for a custom pick from the site) and Remove all.
- **Talents**: paste a talent link from the site's calculator, preview it against your
  character (what you have, what comes now, what comes later), and learn the points one by
  one. A confirmation comes first, and it never learns in combat.
- **Plan**: the launch-day checklist from the site, with tick boxes and map waypoints
  (TomTom, if you have it).
- **BiS (Mr.BiZ)**: best in slot gear for every class and spec at level 30, with where it
  drops, how sure the source is, and a per-character wishlist.
- **Tweaks**: small optional helpers, all **off until you tick them**: auto-repair, sell
  grey items, quest auto-accept and turn-in, fast looting, free bag slots, a copy-chat box,
  an "ability ready" alert, and on-screen icons for your class (Warrior stance, Hunter ammo,
  missing tracking, missing group buffs).

It also keeps spell ranks right in the macros it makes: on WoW Forever a plain spell name can
resolve to a rank you haven't learned, so the addon writes in the highest rank you know.

## Install

Unzip into the `Interface/AddOns/` folder of your WoW Forever installation so you get
`Interface/AddOns/RoadToForever/RoadToForever.toc`, then restart the game (or `/reload`).
The addon is for WoW Forever only. It loads no other addons, and it makes no network
connections: everything moves between the site and the game by copy and paste.

## Getting started

1. On the site, tick macros in **Export macros** and copy the import string. In game, type
   `/r2f import` and paste it.
2. For talents: build one in the site's talent calculator, copy its link, open the
   **Talents** tab, paste, **Preview**, then **Learn talents**.
3. `/r2f copybuild` copies your current talents as a link for the site.
4. Open each profession window once, then `/r2f profs` copies your recipes for the site's
   Professions page.

## Commands

| Command | What it does |
| --- | --- |
| `/r2f` | open or close the window |
| `/r2f macros`, `/r2f talents` (`/r2ft`), `/r2f plan`, `/r2f gameplay`, `/r2f settings` | open that tab |
| `/biz`, `/mrbiz`, `/r2f bis` | best in slot (`/biz wish` opens the wishlist) |
| `/r2f import` | paste a macro import string from the site |
| `/r2f copybuild` | your talents as a link for the site |
| `/r2f profs` | your professions for the site |
| `/r2f copychat [window]` | a box with chat text you can select and copy |
| `/r2f stance`, `/r2f ammo` | show or hide that icon (add `lock` to lock it) |
| `/r2f minimap` | show or hide the minimap button |
| `/r2f help` | this list in game |

## Safe to use

The addon only creates its own frames and reads game data. It does not edit Blizzard's
interface, and anything that writes (making macros, learning talents) waits until you are out
of combat. Learning talents is the one action that can't be undone, so it always asks first.

## Problems and feedback

If something goes wrong, `/r2f debug` lists troubleshooting tools; paste what they print into
your report. `/r2f copychat` is handy for copying Lua errors out of chat.

- Report a bug or send an idea: [Discord](https://discord.gg/Yh2sTMZksq) or
  [GitHub issues](https://github.com/nobody174/wow-forever/issues)
- Website: https://nobody174.github.io/wow-forever/

## Credits

Best in slot data comes from [ForeverDB](https://foreverdb.net/) and Wowhead; the addon
shows the source next to each pick. The quest-reward weapons on the Plan tab (and the
item rarity colours) come from [Wowhead](https://www.wowhead.com/forever)'s Forever item data.
