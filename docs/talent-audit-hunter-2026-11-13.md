# Talent audit, step 1: the Hunter dump (2026-11-13)

Source: `/r2f debug talentdump` (addon 0.87.1) on a Hunter, release client build 1.60.1.x, compared with `TalentData.lua`
(Wowhead snapshot 2026-11-08). Checkpoint 3 of `docs/claude-code-wclbox-handoff.md`. One class only so far.

## What the game exposes (C_Traits on Forever)
| Need | Field | Reliable? |
|---|---|---|
| name | entry -> definition `spellID`, then `C_Spell.GetSpellName` (no name field) | yes |
| ranks | node `maxRanks`, `activeRank` (`currentRank`, `ranksPurchased` too) | yes |
| position | node `posX`, `posY` | mostly: see "parked nodes" |
| prerequisite | node `visibleEdges` = `{targetNode, type=2, isActive, visualStyle}`; source = the prerequisite, target = the dependent | yes, 8 of 8 data prerequisites present |
| points needed in the tree | condition `spentAmountRequired` | **relative**: it is the points still missing (required minus points already spent in that tree), 0 once met. `isGate` is false everywhere. Only equals our `p` (5 x row) on a tree with 0 spent |
| tree points | currency `spentInTree`, `spent`, `quantity`, `maxQuantity` (39 at the time) | yes |

## Hunter against TalentData
- Beast Mastery 16/16 and Survival 18/18 talents match on name, max rank, row and column. Marksmanship matches on all 16.
- Prerequisites: all 8 in our data exist in the game with the same direction. The game lists one extra edge, Bestial Wrath -> Intimidation
  (the reverse of our Intimidation -> Bestial Wrath); low importance.
- Row gates: Survival (0 points spent) 5, 10 ... 30 = our `p`. Marksmanship (8 spent) shows 2, 7, 12, 17, 22 = ours minus 8. Beast Mastery (31 spent) shows 0.
  So the gates agree with our data; the field cannot be compared on a character with points in the tree without adding the points spent in it.

## Parked nodes (the real finding)
Two extra nodes sit far off the grid, at exactly ten times a grid coordinate:
- Improved Serpent Sting (spell 19464, Marksmanship, rank 0/5, unavailable) at posX 6820, **posY 39300** (a row would be 3930). Not in our data.
- A second Lightning Reflexes (node 104982, rank 0/5) at **posX 102800**, posY 5740 (the real one is node 110859 at 10280, 5130).
They look like removed or moved talents parked out of sight, not talents a player can take.

Consequence: `Talents.ReadTrees()` refuses a tree with more than 7 tiers or a fourth pane, so on this Hunter it returns nil. Fed this
exact dump, the addon's reader answers nil; with the two coordinates corrected it reads 16 / 17 / 19 nodes. Check the Talents tab on a Hunter: it should say it cannot read the tree.
Proposed fix: ignore nodes whose posX or posY is far outside the grid (the real range is about 1000 to 11000 by 2100 to 5800). Wowhead's data does
not list Improved Serpent Sting, which agrees with it being parked.

## Next
1. Decide the parked-node rule and fix `readTreesLive`, with a fixture of this dump (one deliberate difference per test).
2. Build `/r2f talentcheck`: per class, compare the live tree with `TalentData.lua` on name, max rank, row, column and prerequisite edges (not on `p`
   unless the points spent are added back); print "matches" or the differences; the game wins, differences go to `BACKLOG.md`.
3. More classes: one dump per class, same command (TESTING 5.82).
