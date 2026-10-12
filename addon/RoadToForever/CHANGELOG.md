# Road to Forever changelog

## 0.33.0 (2026-10-12)

- The Settings tab is gone; its settings now live on Home (quick game settings, minimap button, bags). `/r2f settings` opens Home.
- Macros page has an Options button: where new macros go (character / account slots) and Remove all.
- The free talent points line moved from Home to the Talents page.
- Home is wider and shows the launch plan, the share card and the settings together.

## 0.32.1 (2026-10-12)

- Shift-click on a Mr.BiZ item now links it in chat even when the game doesn't know the item yet
  (opens the chat box if none is open).
- The Mr.BiZ model stands still; drag it to turn it.
- Size and Opacity sliders have tick marks for each 10% step.

## 0.32.0 (2026-10-12): Mr.BiZ paper doll

- **Mr.BiZ redesigned**: your character's 3D model (turns slowly, drag to turn it) with the 17
  gear slots around it. Each slot shows the best pick's icon in its quality colour. Click a slot
  and the panel on the right lists its options (best pick and the next ranked ones, with source,
  score and how far behind), each with a wishlist switch. Source filters are switches under the
  doll. The Wishlist view is unchanged apart from the look.

## 0.31.1 (2026-10-12): look fixes

- The window is a solid dark panel again (Opacity slider fades it, default 100%).
- Switches are slim: green when on, black with a grey rim when off.
- The quest log "mark all in this zone" box is a small black square with a green tick.
- Size slider runs 50% to 150% and Size / Opacity show their percentage, in steps of 10.

## 0.31.0 (2026-10-12): new window, phase 1 (test build)

- **New window shell**: a larger flat window (820 x 600) with a sidebar instead of the bottom tabs
  (Home; Journey: Plan, Talents, BiZ; Tools: Macros, Gameplay; Options: Settings).
- **Top bar**: logo and name, Size and Opacity sliders, Reload UI button, close.
- **On/off switches** replace the tick boxes everywhere.
- The pages inside are still the old layouts, centred; they get reflowed in the next phases.

## 0.30.0 (2026-10-12): public test build

- **Macros**: import macros from the site, browse them in a spellbook-style book, drag them
  to your bars. Imports update macros the addon made and never touch ones you edited.
  Spell ranks are written in correctly for WoW Forever.
- **Talents**: paste a link from the site, preview it, learn the points one at a time with a
  confirmation. `/r2f copybuild` sends your build back to the site.
- **Plan**: the launch-day checklist with tick boxes and TomTom waypoints.
- **Mr.BiZ**: best in slot per class and spec (level 30) with sources and a wishlist
  (`/biz`).
- **Gameplay** (all off until ticked): auto-repair, sell grey items, quest helpers, fast loot,
  free bag slots, copy chat, an "ability ready" alert and class icons (stance, ammo,
  tracking, missing group buffs).
- **Settings**, a minimap button, movable bags, and `/r2f profs` to share your professions
  with the site.
- **BiZ tab polish**: a real down arrow on the class and spec buttons, "Bizzest" shown on the best pick, roomier rows, and item colours remembered between sessions.
- Troubleshooting commands are grouped under `/r2f debug`; `/r2f help` lists only the commands
  you use day to day.
