# Weapon upgrades along the route: research (2026-10-13)

The owner's point: the Plan tab's "Weapon:" lines only appear for 9 of 27 specs, but a Hunter (for one) clearly gets weapons from quests
on the way. He was right. The reason for the gap is how it was built, not that there is nothing to find.

## Why the Plan tab finds so little today

`BiZ.RouteWeapons` (`addon/RoadToForever/BiZ.lua`) only looks at the Mr.BiZ picks (best + 2 next per slot, from ForeverDB's
level-30 lists) and only counts a pick as "on the route" when its source is a **dungeon or a vendor** whose place is named in a plan
step's title. Quest rewards and world drops have no place, so they never match. Most weapon picks are quests, crafted or world drops.

## The data exists: Wowhead Forever's item lists

Each item list page (for example `https://www.wowhead.com/forever/items/weapons/guns`) carries a `var listviewitems = [...]` array with, per item:
`reqlevel`, `quality`, `dps`, `source` (`4` = quest reward) and `sourcemore` = `[{ n: quest name, ti: quest id, c: zone id, t: 5 }]`.
That is quest, quest id and zone, for every weapon type, without a browser. The zone id resolves to a name through
`https://www.wowhead.com/forever/zone=<id>` (title), so a quest reward can be tied to the plan step for that zone and level.

Checked by script (`bis/tools/wh_items.py`, quality green or better, required level 32 or less):

**Guns (16 quest rewards)**: the owner's Hall of Thanes gun is **Calibrated Blunderbuss** (rare, required level 9, 9.6 dps), the reward of the quest
**Old Ironforge Incursion** in **The Hall of Thanes** (zone 16919). Others on the way: Misplaced Shooter (10, Leonid's Letter), Daryl's Hunting Rifle (11,
A Hunter's Boast, Loch Modan), Privateer Musket (13, The Guns of Northwatch, The Barrens), Walton's Second-Favorite
Gun (14, Unwelcome Guests), Owlsight Rifle (17), Moonsight Rifle (23, Scramble), Nail Spitter and Master Hunter's Rifle (28), Flash Rifle,
Shrapnel Blaster, Blasting Hackbut (30), Sidegunner Shottie (32).

**Bows (11 quest rewards)**: the owner's Wetlands bow is **Raptor's End** (required level 22, 12.1 dps), the reward of **Ormer's Revenge** in **Wetlands**
(zone 11). Others: Bow of Hours (5, Catching Wind, **Zephras Isle**), Militia Bow (1), Orcish Battle Bow (9), Daryl's Hunting Bow (11), Bow of Plunder (19),
Cliffrunner's Aim (20), Precision Bow (23), Lunaris Bow (25), Master Hunter's Bow (28).

So the Hall of Thanes (plan step `p1-hot`, Ironforge) and Wetlands are both steps of the launch plan, and both have a ranged weapon that the Mr.BiZ lists do not mention.

## All five plan classes (script run 2026-10-13)

`bis/tools/wh_quest_weapons.py` now reads every weapon type and writes `bis/quest-weapons.json` (273 quest-reward weapons, green or better, required level
32 or less). `bis/quest-weapons-by-class.md` filters that to the zones and dungeons of the plan and to what each class can use (Classic proficiencies,
unverified for Forever): **Hunter 58, Warrior 97, Paladin 67, Shaman 70, Druid 42** quest weapons on the route. Examples beyond the Hunter ones above:
Phytoblade (Wetlands, 1h sword 12.9 dps), Edge of the People's Militia (Westfall, 2h sword), Mountaineer's Greataxe (Loch Modan, 2h axe 11.2), Woodsman Sword
(Darkshore, 2h sword 13.0), Daryl's Shortsword (Loch Modan), and several dagger and staff rewards for Druids and Shamans on Zephras Isle.

## What a real fix needs (not built)

1. A script, `bis/quest_weapons.py`, reading every weapon page (guns, bows, crossbows, 1h/2h swords, axes, maces, daggers, staves, polearms,
   fist weapons, wands, thrown) and writing `bis/quest-weapons.json`: item id, name, type, required level, quality, dps, quest, quest id, zone name.
2. Which classes can use which weapon type (a small fixed table) and a **score per spec**: the stats come from
   `https://nether.wowhead.com/forever/tooltip/item/<id>` (the site already parses these), the weights from `BiZData.specs[id].weights`. Without a score,
   "upgrade" means nothing, because a level 9 rare gun is only an upgrade if it beats the weapon you would have anyway.
3. Matching a quest to a plan step: by zone name in the step's title (as dungeons are matched now) and the step's level range, so a level 28 quest
   is not shown at a level 12 step.
4. Show them as "Weapon: ... (quest: Old Ironforge Incursion)" on the matching step, best per slot marked, like the dungeon and vendor ones.
5. Check with the owner in game: reward choice (some quests give a choice of weapons), whether the quest is faction-locked, and that the quest exists in the beta.

Decisions needed before building: (a) compare with what you probably already have (your equipped item, or the Mr.BiZ pick) or show every usable quest
weapon? (b) how many lines per step (the 1 best per slot, or all)? (c) is it OK to bundle a Wowhead-derived weapon table in the addon (the BiS data already
credits sources; this one would credit Wowhead)?
