# WCLBox vs bis/items.json

WCLBox build 1.60.1.70888 | our table build 1.60.1.70450 | WCLBox list 21855 items, detail (weapons+armor) 11859 | our table 12684 items

## Coverage
- ids in our table but not in the WCLBox list: **2432 of 12684** (19%)
  - by quality: {'white': 369, 'grey': 739, 'blue': 454, None: 9, 'green': 149, 'legendary': 4, 'epic': 708}
  - sample: 41 OLDRecruit's Belt, 42 OLDSquire's Belt, 46 OLDFootpad's Belt, 50 OLDInitiate's Belt, 54 OLDNovice's Belt, 58 OLDAcolyte's Belt, 77 Deprecated Outfitter Cloth Armor, 86 Deprecated Old Belt, 87 Deprecated Old Boots, 88 Deprecated Old Pants, 90 OLDDwarven Initiate's Belt, 91 OLDDwarven Initiate's Pants
- pulled detail by quality: {'white': 1166, 'epic': 1881, 'blue': 3746, 'green': 5049, None: 4, 'legendary': 13} (gear in the list: 12269; the pull may have skipped grey/white)
- ids new in WCLBox (gear detail, not in our table): **1896**
  - by slot: {'Two-Hand': 173, 'Hands': 140, 'Feet': 139, 'Legs': 138, 'One-Hand': 128, 'Chest': 127, 'Wrist': 118, 'Shoulder': 118, 'Waist': 118, 'Head': 113, 'Finger': 87, 'Ranged': 86}
  - by quality: {'epic': 629, 'blue': 1076, 'green': 184, 'white': 4, 'legendary': 3}

## Differences on 9843 ids in both
| field | differs |
|---|---|
| quality | 37 |
| item level | 17 |
| required level | 58 |
| agility | 21 |
| strength | 19 |
| intellect | 34 |
| spirit | 17 |
| stamina | 73 |
| other stats (spell power, crit, ...) | 334 |
| armor | 384 |
| dps | 908 |

### dps (up to 20 of 908)
id | name | ours | WCLBox | our src
---|---|---|---|---
25 | Worn Shortsword | 1.0 | 1.1 | db2
35 | Bent Staff | 1.3 | 1.4 | db2
36 | Worn Mace | 1.0 | 1.1 | db2
753 | Dragonmaw Shortsword | 14.55 | 14.5 | tip
766 | Flanged Mace | 2.9 | 3.0 | db2
767 | Long Bo Staff | 4.4 | 4.2 | db2
768 | Lumberjack Axe | 3.9 | 3.8 | db2
778 | Kobold Excavation Pick | 2.9 | 2.7 | db2
781 | Stone Gnoll Hammer | 3.9 | 3.8 | db2
810 | Hammer of the Northern Wind | 39.6 | 39.5 | db2
812 | Glowing Brightwood Staff | 38.06 | 51.3 | tip
851 | Cutlass | 7.0 | 6.8 | db2
852 | Mace | 6.5 | 6.3 | db2
853 | Hatchet | 7.4 | 7.2 | db2
854 | Quarter Staff | 9.6 | 9.4 | db2
864 | Knightly Longsword | 20.6 | 20.3 | db2
866 | Monk's Staff | 31.25 | 31.2 | tip
873 | Staff of Jordan | 29.86 | 40.4 | tip
880 | Staff of Horrors | 15.15 | 15.1 | tip
923 | Longsword | 12.3 | 12.2 | db2

### other stats (spell power, crit, ...) (up to 20 of 334)
id | name | ours | WCLBox | our src
---|---|---|---|---
812 | Glowing Brightwood Staff | {'55': 15, '41': 150, '42': 50} | {'55': 15} | tip
873 | Staff of Jordan | {'31': 15, '45': 60} | {'31': 15} | tip
1155 | Rod of the Sleepwalker | {'45': 32} | {} | tip
1317 | Hardened Root Staff | {'45': 20} | {} | tip
1928 | Defias Mage Staff | {'45': 8} | {} | tip
1933 | Staff of Conjuring | {'45': 8} | {} | tip
2042 | Staff of Westfall | {'41': 48, '42': 16} | {} | tip
2100 | Precisely Calibrated Boomstick | {} | {'32': 7} | tip
2169 | Buzzer Blade | {'45': 22} | {} | tip
2243 | Hand of Edward the Odd | {'45': 90} | {} | tip
2271 | Staff of the Blessed Seer | {'45': 28} | {} | tip
2280 | Kam's Walking Stick | {'45': 32} | {} | tip
2567 | Evocator's Blade | {'45': 28} | {} | tip
3227 | Nightbane Staff | {'54': 8, '45': 18} | {'54': 8} | tip
3414 | Crested Scepter | {'45': 32} | {} | tip
3415 | Staff of the Friar | {'41': 52, '42': 17} | {} | tip
3566 | Raptorbane Armor | {'131': 15, '38': 16} | {'38': 16} | db2
3902 | Staff of Nobles | {'41': 22, '42': 7} | {} | tip
4548 | Servomechanic Sledgehammer | {'91': 1, '37': 10} | {'37': 10} | db2
5194 | Taskmaster Axe | {'41': 45, '42': 15} | {} | tip

### armor (up to 20 of 384)
id | name | ours | WCLBox | our src
---|---|---|---|---
868 | Ardent Custodian | 0 | 100 | tip
1486 | Tree Bark Jacket | 44 | 104 | tip
1717 | Double Link Tunic | 218 | 278 | tip
2314 | Toughened Leather Armor | 80 | 84 | db2
3230 | Black Wolf Bracers | 43 | 63 | tip
3844 | Green Iron Hauberk | 238 | 358 | db2
4070 | Jouster's Crest | 1051 | 1101 | tip
5254 | Rugged Spaulders | 67 | 87 | tip
5459 | Defender Axe | 0 | 10 | db2
6335 | Grizzled Boots | 62 | 82 | tip
6447 | Worn Turtle Shell Shield | 490 | 530 | tip
6686 | Tusken Helm | 188 | 308 | tip
6731 | Ironforge Breastplate | 168 | 198 | db2
6733 | Ironforge Gauntlets | 120 | 170 | db2
6742 | Stonefist Girdle | 134 | 234 | tip
6907 | Tortoise Armor | 208 | 248 | tip
7750 | Mantle of Woe | 35 | 68 | tip
7919 | Heavy Mithril Gauntlet | 188 | 268 | db2
7921 | Heavy Mithril Pants | 297 | 417 | db2
7930 | Heavy Mithril Breastplate | 446 | 536 | db2

### agility (up to 20 of 21)
id | name | ours | WCLBox | our src
---|---|---|---|---
1218 | Heavy Gnoll War Club | -10 | 0 | tip
2100 | Precisely Calibrated Boomstick | 14 | 7 | tip
4696 | Lapidis Tankard of Tidesippe | -15 | 0 | tip
9646 | Gnomish Water Sinking Device | -5 | 0 | db2
10781 | Hakkari Breastplate | 5 | 4 | tip
11865 | Rancor Boots | 12 | 9 | tip
11963 | Penance Spaulders | 11 | 8 | tip
11964 | Swiftstrike Cudgel | 7 | 5 | tip
13402 | Timmy's Galoshes | 17 | 18 | tip
17776 | Sprightring Helm | 15 | 11 | tip
17778 | Sagebrush Girdle | 15 | 11 | tip
17782 | Talisman of Binding Shard | 0 | 5 | db2
17783 | Talisman of Binding Fragment | 0 | 5 | db2
18583 | Warglaive of Azzinoth (Right) | 0 | 40 | db2
18584 | Warglaive of Azzinoth (Left) | 0 | 60 | db2
19019 | Thunderfury, Blessed Blade of the Windseeker | 0 | 5 | db2
251485 | Edward's Knife | 2 | 4 | db2
270078 | Guardian Staff | 16 | 11 | tip
270098 | Dank Shoulderpads | 6 | 4 | tip
274931 | Fur-Lined Bracers | 6 | 5 | tip

### intellect (up to 20 of 34)
id | name | ours | WCLBox | our src
---|---|---|---|---
2226 | Ogremage Staff | -5 | 0 | tip
9527 | Spellshifter Rod | 23 | 17 | tip
9531 | Gemshale Pauldrons | 0 | 8 | tip
11865 | Rancor Boots | 11 | 8 | tip
13216 | Crown of the Penitent | 26 | 20 | tip
17775 | Acumen Robes | 20 | 15 | tip
17777 | Relentless Chain | 14 | 11 | tip
17778 | Sagebrush Girdle | 12 | 9 | tip
18583 | Warglaive of Azzinoth (Right) | 0 | 60 | db2
18584 | Warglaive of Azzinoth (Left) | 0 | 40 | db2
22589 | Atiesh, Greatstaff of the Guardian | 0 | 32 | db2
22630 | Atiesh, Greatstaff of the Guardian | 0 | 29 | db2
22631 | Atiesh, Greatstaff of the Guardian | 0 | 28 | db2
22632 | Atiesh, Greatstaff of the Guardian | 0 | 28 | db2
251486 | Tabitha's Cuffs | 0 | 6 | db2
271946 | Theramore Handwraps | 22 | 23 | db2
272098 | Raider Handwraps | 22 | 23 | db2
272484 | Premier Mail Walkers | 10 | 7 | db2
272538 | Premier Centurion's Linked Boots | 7 | 10 | db2
272625 | Premier Linked Hauberk | 6 | 10 | db2

### quality (up to 20 of 37)
id | name | ours | WCLBox | our src
---|---|---|---|---
2314 | Toughened Leather Armor | 1 | 2 | db2
9527 | Spellshifter Rod | 3 | 2 | tip
9531 | Gemshale Pauldrons | 3 | 2 | tip
10781 | Hakkari Breastplate | 3 | 2 | tip
10782 | Hakkari Shroud | 3 | 2 | tip
11865 | Rancor Boots | 3 | 2 | tip
11963 | Penance Spaulders | 3 | 2 | tip
11964 | Swiftstrike Cudgel | 3 | 2 | tip
12000 | Limb Cleaver | 3 | 2 | tip
12049 | Splintsteel Armor | 3 | 2 | tip
12061 | Blade of Reckoning | 3 | 2 | tip
12062 | Skilled Fighting Blade | 3 | 2 | tip
13216 | Crown of the Penitent | 3 | 2 | tip
13217 | Band of the Penitent | 3 | 2 | tip
17770 | Branchclaw Gauntlets | 3 | 2 | tip
17775 | Acumen Robes | 3 | 2 | tip
17776 | Sprightring Helm | 3 | 2 | tip
17777 | Relentless Chain | 3 | 2 | tip
17778 | Sagebrush Girdle | 3 | 2 | tip
17779 | Hulkstone Pauldrons | 3 | 2 | tip

### spirit (up to 20 of 17)
id | name | ours | WCLBox | our src
---|---|---|---|---
2314 | Toughened Leather Armor | 0 | 7 | db2
3235 | Ring of Scorn | -3 | 0 | db2
5611 | Tear of Grief | -3 | 0 | db2
6751 | Mourning Shawl | -4 | 0 | tip
9531 | Gemshale Pauldrons | 11 | 0 | tip
11963 | Penance Spaulders | 12 | 9 | tip
12049 | Splintsteel Armor | 16 | 12 | tip
22589 | Atiesh, Greatstaff of the Guardian | 0 | 24 | db2
22631 | Atiesh, Greatstaff of the Guardian | 0 | 27 | db2
22632 | Atiesh, Greatstaff of the Guardian | 0 | 27 | db2
273031 | Runemender's Seal | 7 | 6 | tip
274380 | Decaying Flesh Bands | -6 | 0 | tip
274931 | Fur-Lined Bracers | 6 | 5 | tip
275979 | Vigilant Watcher's Signet | 12 | 13 | db2
277286 | Encroacher's Claim | 9 | 6 | db2
277289 | Traveler's Shawl | 5 | 3 | db2
279930 | Saltseer's Helm | 7 | 5 | tip

### stamina (up to 20 of 73)
id | name | ours | WCLBox | our src
---|---|---|---|---
2314 | Toughened Leather Armor | 0 | 2 | db2
2621 | Cowl of Necromancy | -5 | 0 | tip
2944 | Cursed Eye of Paleth | -3 | 0 | db2
4462 | Cloak of Rot | -6 | 0 | tip
4746 | Doomsayer's Robe | -11 | 0 | tip
6199 | Black Widow Band | -5 | 0 | tip
9527 | Spellshifter Rod | 9 | 6 | tip
9531 | Gemshale Pauldrons | 13 | 10 | tip
10781 | Hakkari Breastplate | 22 | 17 | tip
10782 | Hakkari Shroud | 19 | 15 | tip
11865 | Rancor Boots | 13 | 10 | tip
11963 | Penance Spaulders | 11 | 8 | tip
12000 | Limb Cleaver | 8 | 6 | tip
12049 | Splintsteel Armor | 18 | 14 | tip
12061 | Blade of Reckoning | 8 | 6 | tip
12062 | Skilled Fighting Blade | 7 | 0 | tip
13217 | Band of the Penitent | 10 | 0 | tip
17182 | Sulfuras, Hand of Ragnaros | 0 | 12 | db2
17770 | Branchclaw Gauntlets | 7 | 5 | tip
17776 | Sprightring Helm | 21 | 16 | tip

### strength (up to 20 of 19)
id | name | ours | WCLBox | our src
---|---|---|---|---
9531 | Gemshale Pauldrons | 7 | 5 | tip
12000 | Limb Cleaver | 27 | 21 | tip
12049 | Splintsteel Armor | 12 | 9 | tip
17182 | Sulfuras, Hand of Ragnaros | 0 | 12 | db2
17770 | Branchclaw Gauntlets | 12 | 9 | tip
17779 | Hulkstone Pauldrons | 7 | 0 | tip
17782 | Talisman of Binding Shard | 0 | 13 | db2
17783 | Talisman of Binding Fragment | 0 | 13 | db2
269717 | Wildgore Greatsword | 6 | 5 | db2
271941 | Theramore Gauntlets | 22 | 23 | db2
272096 | Raider Gauntlets | 22 | 23 | db2
272538 | Premier Centurion's Linked Boots | 12 | 13 | db2
272647 | Premier Linked Headguard | 11 | 12 | db2
274183 | Premier Knight-Champion's Flatmail Boots | 12 | 13 | db2
274196 | Premier Flatmail Headguard | 11 | 12 | db2
277286 | Encroacher's Claim | 6 | 4 | db2
279870 | Tarnished Locket | -3 | 0 | tip
279891 | Guidance of Ursoc | 13 | 10 | tip
280604 | Rage of the Storm | 0 | 16 | db2

### item level (up to 20 of 17)
id | name | ours | WCLBox | our src
---|---|---|---|---
13397 | Stoneskin Gargoyle Cape | 61 | 62 | tip
13400 | Vambraces of the Sadist | 59 | 60 | tip
13402 | Timmy's Galoshes | 59 | 60 | tip
260308 | Hyjal Postal Clasp | 59 | 58 | tip
269716 | Keen Skinning Knife | 19 | 18 | db2
269717 | Wildgore Greatsword | 19 | 18 | db2
269742 | Walton's Second-Favorite Gun | 20 | 18 | db2
273654 | Crystal Thread Cloak | 30 | 29 | db2
274265 | Brush Cutter | 58 | 57 | tip
274270 | Weed Whacker | 58 | 57 | tip
274271 | Deadhead Blade | 58 | 57 | tip
274931 | Fur-Lined Bracers | 41 | 38 | tip
274932 | Coyote Hide Wraps | 41 | 38 | tip
274952 | Jom-jom's Gabbar | 43 | 42 | tip
274959 | Farholde Horns | 40 | 39 | tip
275052 | Orc Bone Bow | 41 | 39 | tip
275721 | Rocketeer Leggings | 58 | 57 | tip

### required level (up to 20 of 58)
id | name | ours | WCLBox | our src
---|---|---|---|---
13397 | Stoneskin Gargoyle Cape | 56 | 57 | tip
13400 | Vambraces of the Sadist | 54 | 55 | tip
13402 | Timmy's Galoshes | 54 | 55 | tip
251932 | Sharpened Cirrusfly Stinger | 0 | 1 | tip
259891 | Berdun's Trusty Rifle | 0 | 45 | db2
279835 | Vine Pruner's Cloak | 0 | 1 | tip
279836 | Thorn Protecting Girdle | 0 | 1 | tip
279837 | Fallen Guard's Pendant | 0 | 1 | tip
279838 | Arcane Infused Rod | 0 | 1 | tip
279839 | Spellguard Pauldrons | 0 | 1 | tip
279840 | Renewing Footpads | 0 | 1 | tip
279841 | Defender of Dalaran | 0 | 1 | tip
279842 | Battle Spaulders | 0 | 1 | tip
279843 | Enchanted Sandals | 0 | 1 | tip
279844 | Striking Staff | 0 | 1 | tip
279845 | Solid Gold Band | 0 | 1 | tip
279846 | Larcenist's Belt | 0 | 1 | tip
279847 | Unstable Power Core | 0 | 1 | tip
279848 | Construct Cloak | 0 | 1 | tip
279849 | Runebound Gloves | 0 | 1 | tip

## Armor and dps mismatch analysis
- armor: 384 differ; by our src {'tip': 82, 'db2': 302} (of {'db2': 3943, 'tip': 2967} with a value); ratio WCLBox/ours: [2.364, 1.275, 1.05, 1.465, 1.504, 1.048, 1.299, 1.323, 1.082, 1.638, 1.179, 1.417, 1.746, 1.192, 1.943]
- dps: 908 differ; by our src {'db2': 775, 'tip': 133} (of {'db2': 996, 'tip': 763} with a value); ratio WCLBox/ours: [1.1, 1.077, 1.1, 0.997, 1.034, 0.955, 0.974, 0.931, 0.974, 0.997, 1.348, 0.971, 0.969, 0.973, 0.979]
- armor cause: {'WCLBox status same': 5, 'WCLBox status changed': 40, 'explained: our armor + our bonusArmor == WCLBox total': 296, 'WCLBox status missing': 1, 'WCLBox status new': 42} (the old table kept bonus armor apart, WCLBox prints one total)
- dps cause: our DB2-computed dps is an estimate (ratios 0.93 to 1.1); WCLBox prints the game's value. Wowhead-sourced differences are rounding (14.55 vs 14.5) or items changed in the live build.
- spell power/healing missing in WCLBox on many staves and weapons: the live build removed them (e.g. Rod of the Sleepwalker).

## Mr.BiZ picks (2757 distinct ids in bis-data.json)
- flagged `changed`/`new` by WCLBox: 2032 ({'new': 1060, 'changed': 972})
- not in WCLBox at all: 78
  - 253953 Flame Circlet: new
  - 253955 Shadow Circlet: new
  - 253957 Pearly Circlet: new
  - 253961 Pristine Gown: new
  - 8202 Big Voodoo Pants: changed
  - 253963 Silky Gown: new
  - 286731 Aggor's Refitted Belt: new
  - 253965 Flame Gown: new
  - 8206 Tough Scorpid Leggings: changed
  - 253967 Shadow Gown: new
  - 8208 Tough Scorpid Helm: changed
  - 253969 Pearly Gown: new
  - 253975 Filigreed Pristine Circlet: new
  - 8216 Big Voodoo Cloak: changed
  - 286745 Furlfeather Ring: new
  - 253977 Filigreed Silky Circlet: new
  - 253979 Filigreed Flame Circlet: new
  - 253981 Filigreed Shadow Circlet: new
  - 253983 Filigreed Pearly Circlet: new
  - 8223 Blade of the Basilisk: changed
  - 8225 Tainted Pierce: changed
  - 8226 The Butcher: changed
  - 253987 Pristine Leggings: new
  - 253989 Silky Leggings: new
  - 253991 Flame Leggings: new
  - 278567 Stromgarde Hood: new
  - 253993 Shadow Leggings: new
  - 253995 Pearly Leggings: new
  - 254001 Gilded Slippers: new
  - 254003 Frothing Slippers: new
  - 254005 Fiery Slippers: new
  - 254007 Black Slippers: new
  - 254009 Golden Slippers: new
  - 254013 Earthen Silk Slippers: new
  - 254015 Earthen Silk Hood: new
  - 254017 Earthen Silk Gloves: new
  - 254019 Earthen Silk Cuffs: new
  - 254021 Gilded Handwraps: new
  - 254023 Frothing Handwraps: new
  - 254025 Fiery Handwraps: new
