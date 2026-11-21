# Level 60 builds: ours vs Wowhead Forever guides (2026-11-21)

Overlap = talent points shared with the closest Wowhead build (of 51). Split = points per tree.

| Build | Ours (split) | Closest Wowhead (split) | Shared |
|---|---|---|---|
| Priest Holy (Healer) | 20/31/0 | 18/33/0 (holy) | 42/51 |
| Priest Shadow | 11/0/40 | 13/0/38 (shadow) | 44/51 |
| Warlock Affliction | 38/13/0 | 35/11/5 (affliction) | 46/51 |
| Warlock Destruction | 0/14/37 | 7/11/33 (destruction) | 38/51 |
| Mage Frost | 19/0/32 | 18/0/33 (frost) | 44/51 |
| Mage Fire | 12/36/3 | 16/32/3 (fire) | 43/51 |
| Rogue Combat | 15/36/0 | 16/35/0 (combat) | 48/51 |
| Druid Feral (Bear tank) | 7/39/5 | 9/33/9 (feral) | 43/51 |
| Druid Restoration (Healer) | 6/0/45 | 18/0/33 (restoration) | 39/51 |
| Shaman Restoration (Healer) | 0/5/46 | 0/10/41 (restoration) | 46/51 |
| Shaman Enhancement | 10/41/0 | 17/34/0 (enhancement) | 44/51 |
| Shaman Elemental | 32/5/14 | 31/4/16 (elemental) | 45/51 |
| Hunter Beast Mastery | 39/12/0 | 31/20/0 (beast-mastery) | 38/51 |
| Hunter Marksmanship | 12/39/0 | 5/41/5 (marksmanship) | 41/51 |
| Paladin Protection (Tank) | 0/44/7 | 23/28/0 (protection) | 28/51 |
| Paladin Holy (Healer) | 31/20/0 | 32/7/12 (holy) | 38/51 |
| Paladin Retribution | 12/8/31 | 12/8/31 (retribution) | 48/51 |
| Warrior Protection (Tank) | 11/0/40 | 17/2/32 (protection) | 41/51 |
| Warrior Fury (DPS) | 17/34/0 | 17/34/0 (fury) | 46/51 |

## Notes
- Source: Wowhead's Forever build guides, `https://www.wowhead.com/forever/guide/classes/<class>/<spec>/talent-builds-pve-<dps|tank|healer>`. Each page embeds several builds as `[talent=<class>/<code>_t0...]` (dungeon, raid, melee/caster, PvP variants). A plain `curl -A "Mozilla/5.0"` works. Our code format matches theirs after dropping the `v2` version prefix.
- Caveat: Wowhead seems to omit leading empty trees for some builds (Paladin Protection shows 0/44/7 for us but 23/28/0 for them): treat that row as a format artifact until checked by hand.
- Real differences worth a look: Druid Restoration (6/0/45 vs Wowhead 18/0/33), Shaman Enhancement (10/41/0 vs 17/34/0), Hunter Beast Mastery (39/12/0 vs 31/20/0), Warlock Destruction.
- RankedBoost has moved since 0.84.2: `builds_from_rankedboost.py` dry run now reports 11 changed builds (Mage Arcane/Fire L30, Rogue Assassination L30, Druid Resto 30 and 60, Hunter BM 30, Mage Fire 60, Rogue Combat 60, Shaman Resto/Elemental 60, Warrior Fury 60). Not applied.
- No usage data exists for Forever yet; tier lists and guides only. Warcraft Logs rankings become meaningful after real raids.
- Rotation text in builds.html was NOT rewritten.
