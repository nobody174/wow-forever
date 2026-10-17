# Our own Mr.BiZ database: research and plan (2026-10-17)

Owner's question: stop depending on ForeverDB (and credits / permission). Where do the numbers come from, what would it take to make our own
item database and score, how big is it, and how does a ranking know what is Biz, Bizzer and Bizzest?
Everything marked **measured** was checked on 2026-10-17 against the beta build 1.60.1.70450; **estimate** is a planning number.

---

## 1. Where the item data really comes from (research)

An item has three kinds of facts, and each comes from somewhere different.

| Kind of fact | Where it lives | How others get it | Can we get it ourselves? |
|---|---|---|---|
| **What the item is**: name, slot, quality, item level, required level, class and armor type, binding, set, icon | The game's own database files (DB2) inside the install: `Item` (**31,875 rows, measured**), `ItemSparse` (19,257 rows), `ItemSearchName`, `ItemSet` | "Datamining": ForeverDB says its data is "from the WoW Forever beta game client, build 1.60.1.70425, extracted 2026-10-16". Public sites (wago.tools, wow.tools) publish every DB2 table of every build as CSV | **Yes, today.** `https://wago.tools/db2/<Table>/csv?build=1.60.1.70450` answers for the Forever builds (measured: ItemSparse 5.3 MB, Item 1.4 MB, RandPropPoints 32 KB). Or read the files from our own install with CASCConsole (already installed, `D:\Tools`) plus a DB2 reader |
| **The stat numbers** (+14 Shadow Damage Done, +6 Intellect...) | In `ItemSparse` as *percentages of a budget*: the item stores "stat 7 = 70.58%" and the budget comes from `RandPropPoints` by item level, quality and slot. Example (measured): Filigreed Shadow Circlet, item level 30, rare, head: budget 17, stamina 70.58% x 17 = 12, stat 88 at 82.35% x 17 = 14, exactly what ForeverDB shows | Same tables | **Yes.** Armor comes from the `ItemArmor*` tables, weapon damage from `ItemDamage*` x speed, "Equip:" effects (healing done, mp5, hit %) from `ItemXItemEffect` -> `ItemEffect` -> `Spell`/`SpellEffect` |
| **Stats of the older items**, e.g. Holy Shroud | **Not in the static files.** Of **18,797 equippable weapons and armor** in `Item`, only **7,694 have an `ItemSparse` row**; **11,103 do not** (and 1,964 of the 4,020 items new in Forever are among them). Their numbers are sent by the server as "hotfix" rows when the client asks, and the client keeps them in `Cache/ADB/enUS/DBCache.bin` (**measured on this PC: 4.2 MB, header XFTH version 9, build 70425, 62,618 record markers**) | Sites record those hotfix rows (extraction from a client that has seen the items, and from players' addons: ForeverDB names its "Companion and Helper addons") or read each item from the game | **Yes, three ways** (see 3.2): the tooltip API of Wowhead (measured: returns full stats and "Equip:" lines for Holy Shroud), reading `DBCache.bin` ourselves, or **asking the game itself from our own addon** (`C_Item.RequestLoadItemDataByID` + `GetItemStats`, the game computes the numbers for us) |
| **Where it comes from**: boss, vendor, quest, crafting recipe, reputation, PvP rank | Mostly **not in the client**: drop tables, vendor lists and quest rewards live on the server. Crafting recipes are in the client (`SkillLineAbility`, `Spell`, `SpellReagents`) | ForeverDB labels each source: "(Forever client)" crafting and ranks, "(Classic data)" = the open-source CMaNGOS classic-db for old content, "(Seen in Forever)" / "(Clue)" = recorded by players. Wowhead's `sourcemore` works the same way | **Partly.** Crafting: yes from DB2. Classic content: yes from CMaNGOS classic-db (open source SQL). **New Forever content: only from what players record**, so our own addon must record it (we are three players; ForeverDB and Wowhead have thousands). Until then we keep labelling it honestly ("unknown yet") |
| **The score** | Not data: a formula. ForeverDB's score is `sum(stat x weight)` (checked by `bis/own/check_scores.py`: exactly stats x weights, hit 1% = 10, crit 1% = 14 in their units). The only thing that is "theirs" is the weights, and they say they come from their boss-fight simulator | Their sim | **Yes**, by building our own weights (section 4). This is the real work and the only part that needs design decisions |

**Short answer:** the items are Blizzard's data, everybody reads the same files; ForeverDB's value is the work of turning them into a ranked list.
We can do the same. The one place we cannot be fully independent on day one is **drop locations of brand-new Forever content**.

---

## 2. What we use today (so we know what to replace)

| File | What | Origin |
|---|---|---|
| `bis/raw/*.json` (27 files, 459 slots, 305 distinct items, 220 KB) | best pick + next two per slot, score, stats text, source sentence | ForeverDB, copied by `foreverdb_fetch.py` |
| `bis/sources.json` (30 KB) | sources of the rank 2-3 picks | ForeverDB item pages / old data |
| `bis/quality.json` (5.6 KB) | item colour | Wowhead tooltip API |
| `bis/places.json` | where a dungeon / vendor is (for the arrow) | hand-made |
| `bis-data.json` (334 KB, 31 KB gzipped), `BiZData.lua` (437 KB, 36 KB gzipped) | generated outputs for site and addon | `bis/build_bis.py` |
| `bis/own/` (tooltips cache, `stats.py`, `check_scores.py`, `check_order.py`) | our first checks of their scores | ours |

The site and the addon only need `bis-data.json` / `BiZData.lua` in the **same shape as now**, so the UI does not change: the whole plan is
about producing `raw/` ourselves.

---

## 3. The design

### 3.1 Data model (what we store)

- **`items`** (one row per equippable item, level <= the largest level we publish): `id, name, quality, itemLevel, requiredLevel, slot (inventory type), armorType / weaponType, bonding, unique, faction, set, stats {stat: number}, armor, weapon {dps, speed, min, max}, effects [{text, kind, value}], flags`.
- **`sources`** (many per item): `{type: drop|vendor|quest|craft|reputation|pvp|world, where, chance, level, side, confidence: forever-client | classic-data | seen | clue | unknown, via}`.
- **`weights/<spec>.json`**: per spec and mode (PvE / leveling / PvP): `{stat: weight}` plus the rules that are not linear (hit cap, defense cap).
- **`rules`**: class -> armor types and weapon kinds (weapon table verified 2026-10-17; armor: cloth/leather/mail/plate with the level-40 steps from the client), slot groups, two-hand vs one-hand + off hand, unique-equipped, ring and trinket pairs.
- Outputs unchanged: `raw`-equivalent per spec -> `build_bis.py` -> `bis-data.json`, `BiZData.lua`.

### 3.2 Getting every item's stats (three ways, one result)

1. **DB2 tables (the base, ~7,700 equippable items with stats in the static files + all structure).** Pull `Item`, `ItemSparse`, `RandPropPoints`, `ItemArmor*`, `ItemDamage*`, `ItemEffect`, `ItemXItemEffect`, `ItemSet`, `SpellItemEnchantment`, `SkillLineAbility`, `ChrClasses` as CSV (wago.tools now, our own CASC read later). Compute stats = percent x budget (rounded); **first check (measured): for all 77 best-pick items that have a static `ItemSparse` row, every stat number ForeverDB shows is reproduced exactly (percent x `RandPropPoints` budget, rounded) with no tuning; the budget column follows the slot (head, chest, legs = column 0; waist, feet, hands, trinket = 1; neck, wrist, ring = 2...)**. ForeverDB lists only the stats its weights use, so our table will hold more than it shows. Of the 305 distinct items on the Mr.BiZ lists, 168 have a static row; the other 137 are the legacy items of 3.2, so the full validation is the first job of milestone M0.
2. **Legacy items without a static row (11,103).** Options, in order of independence:
   a. **Our own addon asks the game** (best: no third party at all). A debug command walks the item ids from `Item` (18,797), calls `C_Item.RequestLoadItemDataByID`, reads `GetItemInfo` / `GetItemStats` when `GET_ITEM_INFO_RECEIVED` fires and saves the table in SavedVariables. Needs one logged-in session of roughly 20-40 minutes (estimate: the server throttles item queries) and **a feasibility test on ~50 ids first** (not tested yet). Gives the numbers exactly as the game shows them.
   b. **Parse `DBCache.bin`** from an installed client (format documented by wowdev; needs the `ItemSparse` field layout from WoWDBDefs). Only contains what that client has been sent.
   c. **Wowhead's tooltip API** (measured: 273 ids at 0.45 s each, no refusals): one request per item, full tooltip incl. "Equip:" lines. About 11,100 requests = **about 1.4 hours once**, cached on disk, later only new / changed ids. Their list pages are throttled (403 seen today), the tooltip API is not.
3. **Equip effects** ("Increases healing done by up to 33 and damage done by up to 11", "Restores 4 mana per 5 sec", "Improves your chance to hit by 1%") become stats through `ItemEffect` -> `SpellEffect` aura types, or a small set of text patterns for tooltip-only items. A short list of **special items** (on-use and proc trinkets, weapons with procs) cannot be a plain sum: they get a hand-made value model (uptime x effect) in a `specials` table, each with its reason.

### 3.3 Sources (where it comes from)

| Source type | Plan | Independence |
|---|---|---|
| Crafted | `SkillLineAbility` + `Spell` give recipe, skill rank and reagents; whether the recipe is trainer / vendor / drop comes from the same tables or the recipe item's own source | full |
| Classic dungeon and world drops, vendors, quests | CMaNGOS classic-db (open source SQL: creature loot, vendor, quest rewards), imported once, re-diffed per build; marked "Classic data" | full (but Classic, may differ in Forever) |
| Reputation, PvP ranks | `Faction`, `ItemSparse` min reputation / PvP rank fields, rank names from the client | full |
| **New Forever drops, quests and vendors** | **Recorded by our own addon**: loot window (item, source creature id and name, instance), vendor windows (stock), quest reward windows, saved to SavedVariables and imported by a script. Three players is thin; ForeverDB's addon crowd is bigger | partial, grows with play; unknown stays "unknown yet" |

Every source row keeps its **confidence label** (same set as today: Forever client, Classic data, Seen in Forever, Clue, unknown) and its origin.

---

## 4. Scoring: how the ranking knows Biz, Bizzer, Bizzest

### 4.1 The formula (simple, auditable)

`score(item, spec) = sum over stats of value(stat) x weight(spec, stat)`  (plus armor, weapon dps, set share, specials)
Everything per slot is compared on the same scale. Rank 1 = Bizzest, 2 = Bizzer, 3 = Biz, then Almost biz; **"The Bizz"** tag when the next
pick is `THE_BIZZ_GAP` (20) % or more behind; "just as biz" when the gap is 0 (these rules already exist in `bis.html` and the addon; the new database
only has to deliver the numbers).

### 4.2 The weights (the real work)

A weight answers: "how much more damage / healing / survival is one point of this stat worth, compared with one point of the main stat?" We derive it, not copy it:

- **Casters (damage).** One simulated or analytic fight loop per spec from the client's own spell data (`SpellEffect` coefficients and base damage, `SpellMisc` cast time and GCD, `SpellPower` mana cost). Weight of spell power = `d(damage)/d(SP)`; crit = `d(damage)/d(crit%)` with the spell's crit multiplier; hit = value up to the cap (level-difference miss chance from the game tables) and **zero beyond it**; Intellect = mana pool + crit; Spirit = regen only where it matters.
- **Healers.** Throughput vs mana: healing power x spell coefficient, mp5 and Intellect valued by the fight length the plan assumes; crit and haste with their real healing effect.
- **Melee and hunters.** Attack power from Strength / Agility by class ratio, crit from Agility, hit up to the white-hit cap (dual-wield cap higher), expertise (Forever has it), weapon dps dominates for one-hand vs two-hand.
- **Tanks.** Two parts, EHP (Stamina, armor mitigation from the level's armor formula) and threat (TPS); avoidance (dodge, parry, block) weighted by incoming hit mix; defense for the crit-immunity cap, then zero.
- Each weight is a small function with a **unit test and a written reason**; the weights file also records which game-table values it used so it can be re-derived when a build changes spell numbers.
- **Level:** the weights are computed at a representative gear state for the level being scored (level 30 first, 60 later), because 1 crit % is worth more when your damage is bigger.

### 4.3 Eligibility and the rest of the logic (what makes a list correct, not just a sum)

Class armor and weapon skills (levels where mail / plate start), required level and the **level cap of the list**, faction items (Horde / Alliance counterpart, `OppositeFactionItemID`), bind-on-pickup and unique rules,
**two slots** (rings, trinkets: best two distinct items), **two-hand vs one-hand + off hand** (compare the pairs, not the weapons alone), set bonuses (share counted only if the set is realistic), items that need a quest / rank we do not think the player will have (flagged by source ease, not by score, so rank stays pure), and a **"nothing with these stats at level N" rule** for slots without a useful item.

### 4.4 How we know it is right (tests, not trust)

1. Stat reconstruction test: every item on ForeverDB's current lists (305) must reproduce its stat numbers from DB2 / game data. Target: 100% of the stats it shows.
2. Weights test: derived weights must put ForeverDB's, ForeverChanges' and the beta guides' top picks inside **our top 3 in at least 80% of slots** for the first version; every slot where they disagree gets listed with the reason (a different weight, a rule, a special item) so it is a **decision, not an accident**. ForeverDB and ForeverChanges become **test oracles only**, never inputs.
3. The owner's own in-game check (what he actually uses) is the final word: a "disagree" button in the addon / a note in TESTING.

---

## 5. Size, usage and effort

**Space (estimate unless marked measured).**

| What | Size | Where |
|---|---|---|
| DB2 CSV downloads (Item 1.4 MB, ItemSparse 5.3 MB measured; ~10 more tables incl. spells ~20-30 MB) | ~35 MB | `bis/own/cache/` (gitignored) |
| Wowhead tooltip cache for ~11,100 legacy items | ~40-50 MB | same, gitignored |
| Committed item table (equippable, green or better, up to level 60: about 5,000 + 5,000 items x ~120 bytes) | ~1.2 MB (~250 KB gzipped) | `bis/items.json` |
| Sources and weights | < 0.5 MB | `bis/` |
| Outputs shipped to players (unchanged shape) | `bis-data.json` 334 KB (31 KB gzipped), `BiZData.lua` 437 KB (36 KB gzipped) now; roughly 2x if we publish level 60 as well | site + addon |

**Usage.** All offline on the owner's PC; a refresh = download changed tables (about 1 minute), tooltip delta (a few minutes), rebuild (about 10 seconds), tests (about 2 minutes). The site updates on push; the addon copy ships with the next addon release.

**Effort (estimate, working days for me; the owner supplies decisions, one in-game session and testing).**

| Milestone | Content | Days |
|---|---|---|
| **M0 Item pool** | DB2 pull + stat reconstruction + validation against all 305 ForeverDB items; tooltip cache for the legacy items (or the in-game dump); equip effects | 3-5 |
| **M1 Scoring v1** | eligibility rules, role weight models for the 27 specs (level 30), ranking and labels, parity report against ForeverDB / ForeverChanges, `raw/` produced by us | 5-8 |
| **M2 Sources** | craft from DB2, Classic loot/vendor/quest from CMaNGOS, reputation and PvP, addon recorder for new Forever sources | 5-8 |
| **M3 More levels** | level 60 (and 40 / 50 if wanted): same pipeline, bigger pool | 2-3 |
| **M4 Automation** | one command refresh, scheduled drift check, docs, tests in CI | 2-3 |
| **Total** | independent level-30 lists with honest sources | **about 3-4 weeks**; the first useful slice (M0 + the start of M1, a parity report) in about 1.5 weeks |
| Upkeep | per beta build | about 1 hour |

---

## 6. Risks and how we handle them

- **Weights are judgment.** A simulated number can still be wrong. Mitigation: documented formulas, tests, the parity report, owner veto; ForeverDB's numbers stay available as a *check*.
- **Server-side data for older items (11,103).** Mitigation: three independent routes (in-game dump, cache file, Wowhead tooltip).
- **Third-party availability (wago.tools, Wowhead).** Mitigation: caches on disk, builds pinned, and the local CASC read as the fallback (the tools are already on the PC).
- **Throttling.** Tooltip API only, <= 2 requests/second, pauses after any 403 (Wowhead list pages answered 403 today).
- **Beta churn.** New builds change numbers; the refresh is one command and the drift check says when to run it.
- **Legal / credit.** Item data is Blizzard's game data; what we publish are our own computed numbers and rankings. We keep a short "data from the game client" note and still credit Wowhead where its tooltips or item pages are shown (a courtesy and their terms for tooltip use), but nothing in the pipeline depends on anyone's permission once ForeverDB is only a test oracle.
- **Scope creep.** M1 is level 30, PvE, 27 specs, same UI. PvP lists, leveling lists and level 60 wait for M3.

---

## 7. What we need from the owner

1. **Go / no-go** on M0 (3-5 days, low risk, immediately useful: it also gives us a complete item database for tooltips and the Plan weapon lines).
2. **Route for the legacy items:** (a) the in-game dump (one session at the PC, 20-40 min; I build the command first and you run a 50-item test), or (b) the Wowhead tooltip pull (no action from you).
3. **Which lists matter:** only PvE level 30, or also leveling / PvP, and when level 60.
4. **A few role decisions** for the weights (for example Feral cat vs bear, Retribution PvE, whether healers value mp5 over throughput in dungeons), answered once in a short list I will prepare.
5. **Testing:** the final check is you using the lists; the TESTING.md numbers will name what to look at.

## 8. Recommended next step

Start **M0** and stop at its checkpoint: a full item table of the beta (every equippable item with exact stats, source-less) validated against ForeverDB's 305 items. It costs a few days, needs nothing from ForeverDB, and shows whether the rest is as easy as the first measurements suggest. After that, decide on M1 with real numbers.

---

## 9. M0 progress log

**2026-10-17 (started).**
- `bis/tools/db2_pull.py` downloads 19 item tables of a Forever build (7.9 MB, build 1.60.1.70450) into the gitignored cache.
- `bis/tools/wh_tooltip_pull.py` pulls Wowhead tooltips for the 11,103 legacy items + a 400-item cross-check sample (resumable, one writer only, 0.45 s each, about 85 minutes; running in the background today).
- `bis/tools/items_build.py` builds `bis/items.json` and prints the cross-check between the DB2 numbers and the tooltips.
- **Cross-check, first 400 items that exist both ways:** quality, item level and required level agree **400 of 400**. Stats agree 316 of 400 and armor 215 of 228 with the rules built so far; the remaining differences are all of three understood kinds:
  1. stats the tooltip prints as sentences instead of numbered lines (hit, crit, block as "by 1.0%"; the client stores rating numbers: **hit = 10 per 1%, crit = 14 per 1%, block = 5 per 1%**, which is also why ForeverDB's score units look the way they do),
  2. resistances ("+5 Fire Resistance") and school damage ("damage done by Fire spells by up to 23" = stat 85; the school stats run 84 holy, 85 fire, 86 nature, 87 frost, 88 shadow, 89 arcane),
  3. bonus armor (stat 50) that the tooltip folds into the armor line.
  Robes use the chest armor row (fixed), negative stats are kept (fixed).
- **Decision for the legacy items' "Equip:" effects** (about 40-60 sentence shapes): translate the sentences with a small rule table (each rule: sentence pattern -> stat id and scale), validated on the cross-check sample; the alternative (ItemEffect -> Spell -> SpellEffect aura types) is more exact but needs the large spell tables, so it is kept as the fallback for sentences no rule covers.
**2026-10-17 (checkpoint reached).**
- Tooltip pull finished: 11,503 ids asked, 5,390 exist in Forever (6,113 are 404, items of other Classic versions that Forever does not have).
- `bis/items.json` now holds **12,684 equippable items** (7,694 from the client's static DB2 rows, 4,990 from tooltips only), 1.7 MB.
- Equip-sentence rule table in `items_build.py` (`EQUIP_RULES`, 17 rules plus school damage and the "healing and damage" pair): spell power 45, healing 41, spell damage 42, crit x14, hit x10, block x5, dodge x12, parry x20 (dodge / parry scales from Classic, no Forever sample yet), defense, attack power, haste, resistances 51-56, mana per 5 sec 43. Wowhead's own marker id 41 is ambiguous (it labels both "damage and healing" and "healing"), so rules come first and the marker is only the fallback. 121 distinct sentences are known to carry no gear stat (procs, speed, skills; 264 items list one), kept as `unk`.
- Weapon damage per second now computed from `ItemDamageOneHand` / `TwoHand` / `Wand` / `Thrown` x quality (bows, guns and crossbows x0.772, measured on 9 items), within 4% for 93 of 100 weapons that exist both ways; the misses are test items, PvP and level-60+ items.
- **Cross-check against Wowhead's tooltip (400 items both ways):** quality, item level and required level 400/400; armor 228/228; stats 373/400 (the rest: test items, weapon skills and a few scaled items).
- **Validation against ForeverDB (`bis/tools/items_validate.py`): 412 of 415 best-pick rows give exactly ForeverDB's printed score from OUR numbers** (133 distinct items, none missing). The three that differ: Clever Expeditionary's Spellblade (we count +36 spell power ForeverDB does not print) and Talvash's Gold Ring (defense 3 vs 2, a level-scaled item) on two specs. These are for the owner's in-game check.
- Known gaps: 21 weapons without a damage row, 560 tooltip-only records without a class id, Holy resistance id 53 assumed, haste and expertise scales unmeasured (no sample on a best pick).
- **Verdict: M0 passes.** The item table is complete enough to build M1 (scoring and our own lists) on; nothing here needed ForeverDB at run time.
