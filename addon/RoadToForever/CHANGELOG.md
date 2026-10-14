# Road to Forever changelog

## 0.55.2 (2026-10-14)

- Auto-sell grey items now sells a few at a time and looks again, so a full bag is cleaned in one vendor visit (before, only part of it sold and you had to talk to the vendor again).
- Copy chat no longer comes up blank: lines the game keeps secret are skipped and counted ("N lines (M hidden by the game)"), and when nothing can be read the window says why.
- Mail: the list of your characters says at the bottom that it only knows characters you logged in on with the addon (same realm and faction).
- The selected class circle / side tab now has a clear gold ring around it (it was too faint).

## 0.55.1 (2026-10-14)

- `/r2f open` opens the window without ever closing it (`/r2f` alone still toggles).
- The empty Macro Book now says to click Options, then Import (Import moved there in 0.32).

## 0.55.0 (2026-10-14)

- **Druid macros** in the Macro Book: Shared, Balance, Feral and Restoration sections (61 macros): heals and cleanses on your mouseover,
  form-swap macros for Bear and Cat (Maul, Swipe, Growl, Claw, Shred, Rake, Rip, Ferocious Bite, Ravage, Pounce, Prowl, Dash...),
  Rebirth in combat / Revive outside it, Travel / Aquatic / Cat on one key, and the Forever rune abilities (marked with the rune they need).
  Import the new string from the site (or the addon installs them itself at login).

## 0.54.2 (2026-10-14)

- Mr.BiZ enchant on the item: hover a piece of gear and its tooltip gets a green line with the enchant Mr.BiZ recommends for that slot and your spec
  ("Mr.BiZ enchant: ... (effect)"), "Mr.BiZ enchant in place" when the best one is already on, or a gold line when a stand-in is on. Shown with the BiZ score line
  (Tweaks > Bags > Upgrade arrows). Same idea as the enchant line on Sixty Upgrades' gear list.

## 0.54.1 (2026-10-14)

- Talents tab, Recommended: the Druid Feral build (bear tank / cat) is listed under both Tank and DPS.
- Mr.BiZ: the enchant name is green, like the game's own enchant text.

## 0.54.0 (2026-10-14)

- **Talents tab rebuilt as a calculator.** Click talents freely on any class: the class icons along the top switch between all nine
  classes' trees (try your friend's Warrior while you play a Priest). Nothing you click changes your real talents, and the board no
  longer mirrors what you have learned. Left-click adds a point, right-click takes one away, Shift goes all the way. The same rules
  as the site's calculator (51 points, 5 points per row, prerequisites), with the talent text on hover for every class.
- **Save loadout, Loadouts, Share** (Party, Raid or Guild; teammates with the addon get it under Loadouts) and **Copy link** work for any class.
- **Recommended**: our Tank, DPS and Healer builds for the class on the board, one click to put them on it.
- **Learn this build** works only for your own class and only when the build fits your talents (after a trainer reset), as before.
- The old Preview / Copy my build / Edit build buttons are gone: **Load** puts a pasted link on the board; `/r2f copybuild` still copies your own talents.
- Tweaks tab: the search box at the bottom is gone (not needed).

## 0.53.1 (2026-10-13)

- Plan tab: hover a "Weapon:" line for the item's own tooltip plus "BiZ score +N over what you wear (your spec)", the quest it is the
  reward of (or the Mr.BiZ source), and a note on how it was compared. You can now see how much of an upgrade it is.

## 0.53.0 (2026-10-13)

- Plan tab, weapons along the route: a step now shows "Weapon: <item> (quest: <quest name>)" when a weapon you can use is the reward of a quest
  in that step's zone (matched by the zone named in the step title and the step's level range; the reward's level must be reached by
  the end of the step) AND it beats what you wear in that slot (BiZ score with your own spec's weights; an empty slot counts as 0).
  Only the best weapon per slot (main hand, off hand, ranged) is shown on a step, and nothing that is not an upgrade, so the plan does not
  fill up. Mr.BiZ's dungeon and vendor weapon picks follow the same rules ("best on route" is gone). Your class's weapon types (the
  Classic table, unverified for Forever) and your faction are respected. The table of 233 quest weapons up to level 32 is bundled
  (QuestWeaponData.lua, from Wowhead's Forever item lists, credited in the README).

## 0.52.0 (2026-10-13)

- The BiZNav arrow is a 3D arrow now (TomTom "crazy arrow" style): a gold dart with a raised ridge, seen in perspective, picked from
  100 pre-rendered turn angles (media/arrow3d.tga, a 1024 x 1024 sprite sheet made by addon/art/export_arrow3d.py with headless Blender).
  Small, Medium and Large work as before. The game has no height for waypoints, so it shows the direction on the ground only.
  Tweaks > Alerts & HUD > "3D arrow" (on by default); untick it for the flat dart.

## 0.51.0 (2026-10-13)

- Corpse arrow: when you die the BiZNav arrow points at your corpse ("Your corpse"); when you are alive again the arrow you had before
  comes back. A target you set yourself while dead is left alone. Works on the map you are standing on. Tweaks > Alerts & HUD > "Arrow to
  corpse when you die" turns it off (on by default).

## 0.50.0 (2026-10-13)

- Talents tab: a **Clear** button empties the board so you can build from scratch (Edit build switches on); your real talents are not
  touched. "Couldn't read your talents yet" should be rare now: when the game has not loaded the talent names yet, the tab says
  "Reading your talents..." and tries again a few times, and it falls back to the last good structure (saved per character, every talent
  checked against the live config before use).
- Mr.BiZ enchants: the slot panel lists the best enchant, the #2 and #3 stand-ins under it, and what you wear there now ("Your chest
  has the best enchant" / "the #2 enchant" / "a different enchant" / "no enchant"), read from the enchant id in your item link.
- Mr.BiZ: the "Required level" slider and "My level" button are gone (there is not enough data for a lower level; the lists are for the
  beta cap, 30, and later 60).
- Plan tab: the dungeon entrances that had no position (City of Dalaran, The Drowned City, Krol'dok Stronghold, Blackmaw Hold, Shaper's
  Terrace) now take it from the game's own world map (the entrances Leatrix Maps draws), looked up when you press Waypoint.

## 0.49.0 (2026-10-13)

- Plan tab: positions found for steps that said "position not known yet". The Zephras Isle steps now point at the real NPCs
  (hunter, druid and warrior trainers, the general-goods vendors, Raan Wildwind for The Great Outdoors, the cooking trainer), and the
  Paladin trainer in Ironforge. The island has three towns, so most steps list the middle and the southern one. The data comes from
  Wowhead's Forever zone maps (read 2026-10-13); they show "may have moved" until you have been there. 13 points still have no position:
  the Skycutter and Dalaran portal, the Stormwind boat, and every zone and dungeon of levels 35 to 60 (not in the beta yet; Wowhead
  says "we don't know all the details yet").

## 0.48.1 (2026-10-13)

- Mr.BiZ: item names have their rarity colour (green / blue / purple) from the first open, also for items the game
  hasn't loaded yet. The colours ship with the addon (all 340 Mr.BiZ items); what the game says still wins. The site's
  Mr.BiZ page does the same.

## 0.48.0 (2026-10-13)

- Upgrade arrows, the "BiZ score" tooltip line and the Plan's weapon lines now use the spec you really play (your talent
  tree with the most points), not the first spec in Mr.BiZ's list. For a warrior that list starts with Protection, which is why an
  Arms warrior saw Protection upgrades. Browsing another spec in the Mr.BiZ tab no longer changes what the arrows compare against.
  Mr.BiZ also opens on your own spec now.
- What to train next: "Train now" and "Next" list every spell (no more "and 1 more").
- The BiZNav arrow follows the plan: tick the step you are on and the arrow moves to the next step that has a known position
  (chat says "step done, next: ..."). Steps with no known position are skipped. Tweaks > Alerts & HUD > "Arrow follows the plan"
  turns it off. It only reacts to the step you are on (the first one not ticked, or the one you pointed the arrow from).

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
