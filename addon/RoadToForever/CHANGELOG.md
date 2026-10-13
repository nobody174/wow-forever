# Road to Forever changelog

## 0.47.3 (2026-10-13)

Found by reading Blizzard's own UI code for Forever (the extracted interface files): several things did nothing in game because
the addon asked the game in the old Classic way.

- Mr.BiZ "Required level" slider, Upgrade arrows and the "BiZ score" tooltip line did nothing: they used the global
  GetItemInfo / GetItemInfoInstant, which Forever does not have (Blizzard's own UI only uses C_Item.GetItemInfo). All item
  lookups now go through one helper (ItemApi.lua) that uses C_Item first. The slider now skips picks that need a higher level,
  and the arrows and the score line can appear (Tweaks > Bags > Upgrade arrows, off until you switch it on).
- What to train next did nothing: Forever's class trainer returns the spell's state, level and rank in different places than
  Classic's. It now reads them the way Blizzard's own trainer window does, so Home shows "Train now" and "Next" after you open
  your class trainer once (with "Unavailable" shown, to see spells above your level).
- Mr.BiZ: the best enchant for the selected slot now sits right under the slot's name instead of at the bottom of the list
  (it could be pushed out of view). Click a slot like Neck, Back, Chest, Wrist, Hands, Legs, Feet or a weapon.
- Weapons along the route (Plan tab) only appear for the 9 of 27 specs whose Mr.BiZ weapon comes from a dungeon or vendor on
  the launch plan (Druid Restoration, Mage Frost, Priest Discipline and Holy, all three Rogues, Shaman Elemental, Warrior Fury);
  that is how it was built, not a bug.

## 0.47.2 (2026-10-13)

- Fixed the login error "Attempt to register unknown event LEARNED_SPELL_IN_TAB" (from the new training list). Forever has
  no such event: Blizzard renamed it LEARNED_SPELL_IN_SKILL_LINE. Both names are now tried, and the one the client lacks is
  skipped. This also fixes a quiet gap: spell ranks in the macros and the Macros page now refresh when you learn a
  spell on Forever, which the old name never did there.

## 0.47.1 (2026-10-13)

- Upgrade arrows: potions, quest items and other non-gear no longer get a "BiZ score 0.0" tooltip line, and right after
  login an item you wear that the game hasn't loaded yet no longer makes every bag item look like an upgrade.
- Training: reopening the trainer with "Unavailable" unticked no longer forgets the later spells; spells you learned
  leave the list.
- Home > Training: each line is at most two lines long (two spell names, then "and N more").

## 0.47.0 (2026-10-13)

- Plan tab: weapons along the route. Under a step where you can get one of Mr.BiZ's weapon picks for your spec (main
  hand, off hand, ranged: a dungeon run, or a vendor in that zone), a "Weapon:" line names it with its rank. The best
  one along the route for each slot is marked "best on route". Your spec is the one picked in Mr.BiZ for your class.
  Quest rewards and world drops don't name a place in our data, so they don't show yet.

## 0.46.0 (2026-10-13)

- What to train next, on Home: "Train now" (the spells your level allows, with the total cost) and "Next" (the next
  level that brings something). The list is read from your own class trainer each time you open it, so it is
  Forever's real list with your prices. Open your trainer once (with "Unavailable" shown) to fill it in.
- Tweaks > Alerts & HUD > Training reminder (off until switched on): on level-up, chat says which spells your trainer
  now offers.

## 0.45.0 (2026-10-13)

- Mr.BiZ: each slot now shows its best enchant for the spec under the picks ("Enchant: Enchant Necklace - Agility",
  with the effect and the Enchanting / Leatherworking skill it needs). Same list as the site's Professions page
  (ForeverChanges' level 30 spec pages); the site's Mr.BiZ shows it too when you open a slot.

## 0.44.0 (2026-10-13)

- Upgrade arrows (Tweaks > Bags, off until you switch it on): a small green arrow on bag items that are better than
  what you wear in that slot, a red one on worse ones, and a "BiZ score" line in item tooltips ("+5.1 vs equipped").
  Items are scored with the stat weights of the spec you picked in Mr.BiZ for your own class (the same weights Mr.BiZ
  ranks with). Rings, trinkets and one-handers compare with the weaker of your two. Armor your class can't wear yet
  (mail before 40 for Hunters and Shamans, plate before 40 for Warriors and Paladins) gets no arrow; weapon skills are
  not checked.
- `/r2f debug gear`: hover an item and type it to see the stats the game gives and how they were scored, so a stat
  Forever names differently can be added.

## 0.43.0 (2026-10-13)

- Mr.BiZ: a "Required level" slider under the source filters (and a "My level" button). Picks that need a higher level
  are skipped, so the slot shows rank 2 or 3 instead, the same way the source filters work. 60 = any level (the
  default); the choice is saved per character. The level comes from the game, so an item the game hasn't loaded yet
  still shows until its level is known.

## 0.42.0 (2026-10-13)

- Home > Quick settings: a "24-hour clock" switch. The game clock by the minimap shows 18:30 instead of 6:30 PM. It is
  the game's own setting, so it also matches what Blizzard's clock options show.

## 0.41.0 (2026-10-13)

- Mr.BiZ + BiZNav: Alt + click an item (in the slot list, on the gear icons or in the wishlist) to point the arrow at
  where you get it: the dungeon entrance (Scarlet Monastery, Shadowfang Keep, Gnomeregan, Razorfen Kraul, Blackfathom
  Deeps, the Stockade), the vendor (Illiyana Moonblaze, Samuel Hawke) or Booty Bay. The item tooltip says where the
  arrow will go. Positions are from Classic, so they're marked "may have moved" until checked in Forever. Quests and
  world drops have no spot yet.

## 0.40.1 (2026-10-13)

- BiZNav arrow: a new, sharper arrow image (our own 128 px gold dart with a dark outline), so Medium and Large look
  clean instead of blurry.
- The diamond pin on the world map is smaller.
- Questie: Ctrl + click on a Questie icon on the world map points the BiZNav arrow at it, the same way it works with
  TomTom (click the same icon again to clear). Questie's "Set TomTom Target" buttons work too. This only works when
  TomTom itself is not installed; with TomTom installed, Questie keeps using TomTom's arrow.

## 0.40.0 (2026-10-13)

- BiZNav arrow size: Small / Medium / Large buttons in Tweaks > Alerts & HUD (also `/bizway size large`). Medium is the
  new default and is bigger than before; Reset page puts it back to Medium.
- `/bizway`: `/bizway 45 34` points the arrow at that spot in the zone you are in; `/bizway go here 45 34` does the same
  with "go here" as the name; `/bizway Dun Morogh 47.4 52.5 Kharanos` sets a spot in another zone; `/bizway clear`
  removes it. `/r2f way` still works the same way.
- World map: Alt + right-click on the map sets the arrow on that spot, and the target shows as a diamond pin on the
  world map (hover it for the name). No minimap pin.

## 0.39.0 (2026-10-13)

- BiZNav, our own waypoint arrow (step 1; replaces TomTom for the Plan tab). The Waypoint button on a Plan step now
  points a small gold arrow at the spot, with the distance in yards and the place name. Drag the arrow to move it,
  right-click it to clear. It says "arrived" and disappears within 10 yards. Inside instances it shows "no position
  here", and for a spot on the other continent it says so instead of pointing.
- `/r2f way <zone> <x> <y> [label]` sets the arrow by hand, like TomTom's /way (e.g. `/r2f way Dun Morogh 47.4 52.5
  Kharanos`). `/r2f clear` removes it.
- TomTom is no longer used. Where the game has no map of that name, the button still prints the /way line.

## 0.38.1 (2026-10-13)

- New Warlock macros in the bundle: Shadow Bolt (target / target's target) replaces "Shadow Bolt + Imp Firebolt";
  Corruption mouseover, Bane of Agony mouseover and Pet attack mouseover are new. They cast on your mouseover enemy, then
  your enemy target, then your friendly target's enemy target, and never on a corpse. Curse of Agony is Bane of Agony in
  Forever and is renamed in the Warlock macros.

## 0.38.0 (2026-10-13)

- Tweaks: a search box (bottom left). Type a word (repair, bags, outline...) to list the options that match; click one to open the page it is on.
- Movable bags and Lock bags moved from Home to Tweaks > Bags, next to the other bag options. Home is shorter.

## 0.37.1 (2026-10-13)

- Loadouts: deleting moved out of the load list into its own "Delete a loadout..." menu, and asks for confirmation before anything is removed.

## 0.37.0 (2026-10-13)

- Talent planner on the Talents tab: switch on "Edit build", then left-click a talent to add a point and right-click to remove one. The build updates as a normal link, so Preview and Learn work on it. It enforces max rank, the tier rule (5 points per tier above) and the 51-point cap. It does not check talent prerequisites (the game gives no reliable list), so double-check those.
- Saved loadouts: "Save loadout" names the current build; "Loadouts" lists them per class (account-wide) to load or delete.
- Share: send a loadout to Party / Raid / Guild. Group members with the addon get it saved under Loadouts, marked with the sender's name. Nothing is applied automatically.

## 0.36.0 (2026-10-13)

- All macros from the site now ship inside the addon (207 macros). They are installed at login, so the Macros page is full from the first start and a new addon version updates them (macros you edited yourself are kept). Nothing to copy and paste any more. The Import option stays in Options for custom picks.

## 0.35.1 (2026-10-13)

- Size / Opacity sliders: pressing the bar away from the thumb no longer changes anything (the previous fix still let the click through). Only dragging the thumb applies.
- Removed the small gold dot on the Tweaks page buttons (it only meant "something on this page is switched on" and confused more than it helped).
- Group buffs: Shaman totems added (Strength of Earth, Grace of Air, Windfury Totem, Mana Spring), off by default until the aura names are confirmed in game. Warlock and Rogue have no group buffs.

## 0.35.0 (2026-10-12)

- Size and Opacity sliders only move when you drag the thumb itself; clicking elsewhere on the bar does nothing.
- Choosing character / account slots first in the Macros Options menu now says so in chat (it only affects macros made from then on).
- The Gameplay tab is now called Tweaks.
- Alerts & HUD: group buffs are grouped per class (Priest, Mage, Druid ...) under fold-out headers showing how many are on; open/closed is remembered.
- Talents tab: a "Talented perk (+5 points)" switch. The Talented legacy perk starts talent points at level 5 instead
  of 10, so a build is reached 5 levels sooner. The game already gives you the points you really have, so the switch only
  changes the level line under a build ("26 points: reached at level 30 with the Talented perk"). Default off.

## 0.34.0 (2026-10-12)

- Size slider no longer runs away while you drag it: the number follows the thumb and the window changes once, when you let go (also if the cursor leaves the bar). Numbers 50 / 100 / 150 are written under the bar.
- Switches are slimmer, rounded at the ends, and the green is a little darker.
- Talent trees are bigger and use the wider page.
- Import macros moved from its own button into the Macros page's Options menu.
- The Gameplay tab is now called QoL, with pages Quests, Vendors & loot, Chat & screen, Bags and Alerts & HUD.
- Alerts & HUD: alert text size slider (50-250%) and outline (none / thin / thick).
- Each QoL page has Reset page, and a small gold dot on a page button shows that something on it is switched on.

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
