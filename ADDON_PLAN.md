# Addon plan: Road to Forever (macros + talents)

Status: **built** (scoped 2026-10-01, every planned step shipped 2026-10-02). Steps
1 (data), 2 (site export), 3 (addon MVP, v0.1.0), 4 (updates, v0.2.0), 5 (Tidy up,
Settings, Remove all, key bindings, v0.3.0), 6 (main window, minimap button, logo,
v0.4.0), 7 (release zip on GitHub Releases, v0.5.0), 8 (talent export + the site's
`~hash`, v0.6.0), 9 (talent import preview, v0.7.0), 10 (talent learning, v0.8.0)
and Quick settings (Home tab, v0.9.0, 12.4.1) shipped. No addon version has been
tested in the game yet: what's left is the in-game checks (section 11,
`addon/RoadToForever/TESTING.md`); see `CHANGELOG.md`.
Target: usable before the Nov 4 launch.

| | |
|---|---|
| Addon name | Road to Forever |
| Folder | `addon/RoadToForever/` (in this repo) |
| Slash commands | `/r2f` (main window), `/r2ft` (Talents), `/r2f macros`, `/r2f minimap` (show the minimap button again), `/r2f help`, `/r2f import`, `/r2f copybuild` (step 8, 13.6; kept as a shortcut in step 9, 13.7) |
| Minimap button | yes, draggable around the minimap (section 12; our own button, no embedded libraries, 6.10) |
| Global table | `R2F` (the only global the addon creates) |
| SavedVariables | `R2FDB` (account), `R2FCharDB` (per character) |

This file is the spec. Claude Code: read all of it before building any part,
and keep the design rules in sections 4 and 5. If something here turns out to
be wrong in the game, fix this file in the same commit as the code.

---

## 1. How it works (the whole flow)

```
 Road to Forever site (macros.html)            In-game addon (/r2f)
 ----------------------------------            -------------------------------
 Tick macros (single / group / role / class)
 [Copy import string]  --- clipboard --->  Import window: paste, preview, Import
                                                    |
                                           Macro library (saved, NO slot limit)
                                                    |
                                           Macro Book window (spellbook style)
                                                    |
                                           Drag an icon onto an action bar
                                           -> real macro created at that moment
```

- **Picking happens on the website** (export). The addon only **imports**,
  shows what you imported, and lets you drag macros onto your bars.
- The import string carries the macros themselves, so new or changed macros on
  the site reach the game without an addon update.

## 2. The macro slot limit (and how we live with it)

WoW has 120 account-wide + 30 per-character macro slots on WoW Forever
(confirmed 2026-10-02 by counting the in-game `/macro` Character tab: 5 rows
of 6, not vanilla/Classic Era's 18 — `MAX_CHARACTER_MACROS` isn't defined on
this client, same quirk as other legacy globals, so the addon's fallback
constant had to be corrected to match). That limit is in the
game itself, not just in the `/macro` window:

- Blizzard's action bars (and bar addons like Bartender/Dominos/ElvUI, which use
  the same action slots) can only hold **spells, items and real macros**. Anything
  an addon puts on a normal action bar has to be a real macro, so it uses a slot.
- An addon *could* go past the limit only by drawing its **own** buttons/bars
  (secure action buttons with macro text). That's a separate bar addon, not this
  plan. Parked as an idea in section 10.

How this addon makes the limit a non-issue:

1. **The library has no limit.** Imported macros are stored in the addon's own
   saved data, not in macro slots.
2. **Lazy creation.** A real macro is only created when you drag it onto a bar.
   You only spend slots on macros you actually use.
3. **Tidy up** button: deletes macros this addon created that are no longer on
   any action bar, giving the slots back.
4. **Slot counter** always visible: `Character 7 / 30`, `Account 31 / 120`.
   New macros go into character slots by default and fall back to account slots
   when those are full (setting: Character first / Account first).

## 3. Data changes on the site side (`data.py` + `build.py`)

### 3.1 Sections (decided)

- **Warrior:** General / Tank / DPS (Arms and Fury stay merged in DPS). Done.
- **Paladin:** General / Tank / DPS / Healer. Done.
- **Every other class keeps its current sections** (Shared + specs). No Druid.
- The addon shows whatever sections a class has; it must not assume roles.

### 3.2 Short in-game names (`short`)

WoW macro names max out at 16 characters, and the name is printed on the action
button, where only about 8 to 10 characters show. So every macro gets a short
name. Add `short` to `M()`:

```python
def M(name, code, note="", short=None, icon=None):
```

**Naming rules**

1. Max 16 characters (hard limit). Aim for 10 or fewer.
2. Unique within one class + Universal (two classes may reuse a name: Paladin
   "Judge" never meets a Warrior macro).
3. Use the abbreviation players already use when there is one (HS, VR, MS, BT,
   WW, OP, LoH, BoP, HoJ, FoL).
4. When two spells would get the same letters, spell out the part that differs
   instead of inventing numbers: Shield Block = `SBlock`, Shield Bash = `SBash`.
5. Fixed suffixes and joiners, the same for every class:

| Pattern | Meaning | Example |
|---|---|---|
| `X F` | cast on focus | `Pummel F` |
| `X@` | mouseover version (when a plain version also exists) | `Taunt@` |
| `X>Y` | priority: X if usable, else Y | `VR>Sunder` |
| `X/Y` | modifier: X normally, Y with Shift | `HS/Cleave` |
| `X me` | self-cast version | `LoH me` |
| `X+` | combined opener or combo | `Charge+Rend` |

6. Stance swaps get no tag (the icon already shows the spell).

**Build checks** (`build.py` must fail the build with a clear message when):
- a `short` is longer than 16 characters,
- two macros in the same class + Universal share a `short`,
- a macro has a body but no `short` and its `name` is longer than 16.

**Warrior names**

| Macro | short |
|---|---|
| Victory Rush | `VR` |
| Heroic Strike | `HS` |
| Heroic Strike / Cleave (Shift) | `HS/Cleave` |
| Cleave | `Cleave` |
| Rend | `Rend` |
| Hamstring | `Ham` |
| Sunder Armor | `Sunder` |
| Slam | `Slam` |
| Execute | `Exe` |
| Overpower (to Battle) | `OP` |
| Thunder Clap | `TC` |
| Demoralizing Shout | `Demo` |
| Auto-attack (spam-safe) | `Attack` |
| Battle Shout | `BShout` |
| Bloodrage | `BloodRage` |
| Berserker Rage | `BzRage` |
| Shield Wall | `SWall` |
| Retaliation | `Retal` |
| Intimidating Shout | `IShout` |
| Disarm | `Disarm` |
| Battle / Defensive / Berserker Stance | `Battle` / `Def` / `Berserk` |
| Charge / Intercept (one button) | `Charge` |
| Charge + Rend (opener) | `Charge+Rend` |
| Taunt (to Defensive) | `Taunt` |
| Mocking Blow | `Mock` |
| Challenging Shout | `CShout` |
| Stance dance | `Stances` |
| Pummel / Shield Bash / Taunt focus | `Pummel F` / `SBash F` / `Taunt F` |
| Victory Rush > Sunder Armor | `VR>Sunder` |
| Revenge | `Rev` |
| Sunder + Heroic Strike | `Sunder+HS` |
| Shield Bash | `SBash` |
| Concussion Blow | `Concuss` |
| Shield Slam | `SSlam` |
| Shield Block | `SBlock` |
| Last Stand | `LStand` |
| Charge (Vanguard) | `VCharge` |
| Taunt (mouseover) | `Taunt@` |
| Victory Rush > Heroic Strike | `VR>HS` |
| Sweeping Strikes | `Sweep` |
| Mortal Strike | `MS` |
| Bloodthirst | `BT` |
| Whirlwind | `WW` |
| Pummel (to Berserker) | `Pummel` |
| Piercing Howl | `Howl` |
| Death Wish | `DW` |
| Recklessness | `Reck` |

**Paladin names**

| Macro | short |
|---|---|
| Holy Strike + auto-attack | `HStrike` |
| Judgement | `Judge` |
| Hammer of Wrath / Hammer of Justice | `HoW` / `HoJ` |
| Exorcism | `Exo` |
| Consecration / Holy Wrath | `Consec` / `HWrath` |
| Holy Light / Flash of Light | `HL` / `FoL` |
| Lay on Hands / self | `LoH` / `LoH me` |
| Blessing of Protection / self | `BoP` / `BoP me` |
| Blessing of Freedom | `BoF` |
| Redemption | `Rez` |
| Cleanse / Purify | `Cleanse` / `Purify` |
| Blessing of Might / Wisdom / Kings / Light | `BoM` / `BoW` / `BoK` / `BoL` |
| Blessing of Salvation / Sanctuary | `Salv` / `Sanc` |
| Greater Blessing of Might / Wisdom | `GBoM` / `GBoW` |
| Devotion / Retribution / Concentration / Sanctity Aura | `Devo` / `RetAura` / `Conc` / `SancAura` |
| Auras on one button | `Auras` |
| Divine Shield / Divine Protection | `Bubble` / `DivProt` |
| Voice of Truth | `VoT` |
| Seal of Righteousness / Crusader / Wisdom / Light / Justice / Command / Fury | `SoR` / `SoCru` / `SoW` / `SoL` / `SoJ` / `SoCmd` / `SoF` |
| Seal swap Command <> Righteousness | `Twist` |
| Divine Intervention | `DI` |
| Hammer of Justice / Turn Undead / Repentance / Judgement focus | `HoJ F` / `TU F` / `Repent F` / `Judge F` |
| Repentance | `Repent` |
| Holy Shock | `HShock` |
| Holy Shield | `HShield` |
| Judgement taunt (mouseover) | `Judge@` |
| Righteous Fury | `RFury` |
| Templar's Bulwark | `Bulwark` |

The other six classes get names by the same rules (Claude Code proposes them,
the build checks enforce them).

### 3.3 Icons (`icon`)

- Macros with `#showtooltip` need no icon: the game shows the spell. The
  addon creates them with the question-mark icon (`INV_MISC_QUESTIONMARK`),
  which WoW replaces with the live spell icon.
- Macros without `#showtooltip` (`/petattack`, `/console`, `/targetmarker`,
  `/use 13`) need `icon="..."` (texture name without path), e.g.
  `Ability_GhoulFrenzy` for pet attack. `build.py` warns if one is missing.

### 3.4 Stable ids

Each macro gets an id `<class>/<short>`, e.g. `WARRIOR/VR`, `ANY/Zoom`
(class = English class token as returned by `UnitClass`; Universal = `ANY`).
The id is how the addon recognizes an updated macro. Renaming a `short`
makes it a new macro (the old one stays until removed): avoid renames after
launch.

### 3.5 Outputs

`build.py` adds the ids, short names and icons to the JSON embedded in
`macros.html` (for the export) and to `wow-forever-macros.md` (show the short
name next to each macro).

---

## 4. Website export design (`macros.html` / `template.html`)

**Role: web UI designer.** Keep the site's existing identity. No new palette,
no new fonts.

Tokens already in use (reuse exactly):

| Token | Value | Use in the export UI |
|---|---|---|
| `--bg` | `#0E1428` | page |
| `--panel` | `#161E38` | export tray background |
| `--edge` | `#3A4468` | checkbox border, tray border |
| `--gold` | `#FFD100` | checked state, primary button |
| `--text` / `--muted` | `#E6E2D6` / `#9AA0B8` | labels / helper text |
| Fonts | Marcellus (headings), IBM Plex Sans (UI), IBM Plex Mono (code) | |

### 4.1 Export mode

The cheatsheet stays clean by default. A toggle button, **Pick macros for the
game**, sits at the right end of the spec row (same style as the spec pills,
with WoW's question-mark macro icon in front of the text). Turning it on:

- shows a checkbox inside the left edge of every macro pill,
- shows a group checkbox next to each group heading ("Damage / offensive"),
- shows a section checkbox next to each section heading ("Warrior — Tank"),
- slides up the export tray at the bottom.

Turning it off hides the checkboxes but **keeps the selection**.

### 4.2 Checkboxes

- Real `<input type="checkbox">`, visually replaced (keyboard and screen readers
  still work).
- 16 px square, 1 px `--edge` border, inner fill `#10152C`, 3 px radius.
- Checked: gold check mark (inline SVG, 2 px stroke) with a soft gold glow
  (`box-shadow: 0 0 6px rgba(255,209,0,.45)`), echoing WoW's own checkbox.
- Group and section checkboxes are tri-state: empty / gold bar (some) / check (all).
- Clicking a pill's checkbox selects it **without** switching the code panel
  (stop propagation); clicking the pill text still switches the panel as today.
- A selected pill gets a gold border at 60% opacity, so the selection is visible
  even with the checkbox small.
- Focus: 2 px gold outline, 2 px offset.
- Checkboxes also appear on search results, so you can search "taunt" and tick
  across classes.

### 4.3 Export tray

Sticky to the bottom of the viewport, full content width, `--panel` background,
1 px `--edge` top border, 12 px vertical padding.

```
+---------------------------------------------------------------------------+
| 14 macros selected   Warrior 11  Universal 3       [Clear]  [Copy import string] |
| How to import (3 steps)                                                    |
+---------------------------------------------------------------------------+
```

- Count in Marcellus 18 px; class chips in the class color (same chip style as
  the roster) with the count per class.
- **Clear**: ghost button (transparent, `--edge` border).
- **Copy import string**: primary, same gold gradient as the current-page nav
  button. After copying, its label becomes `Copied` for 2 seconds and a line
  below reads: `Now type /r2f in the game and click Import.`
- **Select all for Warrior** (current class) and **Select everything** live in a
  small menu on the left of the tray.
- If any selected macro is for a class other than the one you'll log in with,
  that's fine: the addon keeps them for that class's characters.
- "How to import" expands to 3 numbered steps (a real sequence):
  1. Install the addon (Download link, zip from GitHub Releases).
  2. Pick macros here and click Copy import string.
  3. In the game, type `/r2f`, click Import, paste with Ctrl+V, click Import.
- Mobile (< 640 px): tray stacks in two rows, buttons full width.
- Empty state (export mode on, nothing ticked): `Tick the macros you want in the
  game, or select a whole group with its checkbox.`

### 4.4 Selection storage

`localStorage` key `wf-export-v1` = array of macro ids. Survives class switches
and reloads. Ids that no longer exist after a site update are dropped silently.

### 4.5 Decisions made while building it (step 2, 2026-10-01)

- **Toggle placement:** the spec pills and the toggle share a `.spec-row`; the
  toggle is outside `#specs` so it stays visible on Universal (no spec pills)
  and during search (spec pills are cleared), where cross-class picking happens.
- **Checkbox is a sibling of the pill `<button>`, not inside it.** Interactive
  content inside a `<button>` is invalid HTML and breaks keyboard/screen-reader
  access. A `.pill` wrapper holds both; CSS places the checkbox over the pill's
  left edge so it still reads as one pill.
- **"Stop propagation"** is implemented as an early return in the page's one
  delegated click handler (`if(e.target.closest(".xcb")) return;`), which has
  the same effect: ticking never switches the code panel.
- **Selected-pill gold border and checkboxes only show in export mode**, so the
  cheatsheet stays clean when the mode is off (selection is still kept).
- **Export mode itself is not remembered** across reloads (page opens clean, as
  4.1 asks); only the selection is.
- **Search view:** each result group gets a group checkbox (in its `<summary>`;
  an `<input>` is its own activation target, so ticking does not open/close the
  group) and each result macro its own checkbox. There are no section headings
  in search, so no section checkboxes there.
- **Clicking a partial (gold bar) group/section box selects all of it**; a
  second click clears it (native checkbox behaviour from indeterminate).
- **Record order** in the import string = page order (class roster order, then
  section, then group order), not tick order, so the same selection always
  gives the same string.
- **`section` field for Universal macros = `Universal`** (the page calls the
  section "All classes"; in the game it's the Universal tab, 5.2).
- **`class` field** = the part of the id before the first `/` (build.py's token);
  the site does not re-derive class tokens.
- **Download link** points to the repo's Releases page
  (`github.com/nobody174/wow-forever-macros/releases`). Re-checked in step 7: it
  stays on `/releases`, not `/releases/latest` (8.1).
- **Size:** "Select everything" (389 macros) makes an ~83 KB string, well past
  the 20 KB test in section 7. A whole class + Universal is 10 to 16 KB
  (measured: Rogue 9.9 KB to Warrior 15.6 KB). The beta paste-speed check should also try the full 83 KB string.

---

## 5. In-game design: the Macro Book

**Role: in-game UI/frame designer.** It must look like part of the WoW UI, not
like a web page in the game. Rule: **Blizzard templates, fonts and textures
only**. Then it automatically matches the client, including any Forever reskin.
The one exception is our logo (minimap button + main window portrait, section 12.1).

The model is the **Spellbook**: players already know you drag spells out of it.

```
 +--[class icon portrait]-- Road to Forever: Macros -----------------[X]-+
 |                                                                    |Uni|
 |  [icon] VR               [icon] HS                                 |---|
 |         Damage                  Damage                             |Gen|
 |  [icon] HS/Cleave        [icon] Sunder                             |---|
 |         Damage                  Damage                             |Tnk|
 |  ... 2 columns x 6 rows = 12 per page ...                          |---|
 |                                                                    |DPS|
 |  Character 7 / 30    Account 31 / 120          Page 1 of 3  [<][>] |
 |  [Import]  [Tidy up]                                    [Settings] |
 +--------------------------------------------------------------------+
```

### 5.1 Frame

- `PortraitFrameTemplate` (or `ButtonFrameTemplate` if that's what the Forever
  client has; check with `/fstack` in beta). Portrait = player's class icon
  (`Interface\TargetingFrame\UI-Classes-Circles` + `CLASS_ICON_TCOORDS`).
- Title: `Road to Forever` in `GameFontNormal` (gold). The Macro Book is the
  **Macros** tab of the main window (section 12.4).
- Size about 540 x 500, movable by the title bar, position saved, closes with Esc
  (add to `UISpecialFrames`).
- Open/close sounds: `SOUNDKIT.IG_SPELLBOOK_OPEN` / `IG_SPELLBOOK_CLOSE`; page
  turn: `SOUNDKIT.IG_ABILITY_PAGE_TURN`.

### 5.2 Side tabs (right edge, like spellbook skill-line tabs)

One tab per section that has imported macros, in this order: Universal, then
the class's sections (General, Tank, DPS, Healer, or the spec names for the
other classes). Icons:

| Tab | Icon |
|---|---|
| Universal | `INV_Misc_Book_09` |
| General / Shared | the class icon |
| Tank | `INV_Shield_06` |
| DPS | `Ability_DualWield` (melee) or `Spell_Fire_FlameBolt` (casters) |
| Healer | `Spell_Holy_HolyBolt` |
| Spec names (other classes) | that spec's usual icon |

Tooltip on a tab: section name + "12 macros".

Since v0.10.0 "the class" is the class being **browsed** in the class picker
(5.10): your own by default, or another class's sections shown read-only.

### 5.3 Macro slots (the grid)

- Each entry looks like a spellbook entry: 36 px icon in the standard
  `Interface\Buttons\UI-Quickslot2` border, name to the right in `GameFontNormal`
  (gold) using the **short** name, subtext below in `GameFontHighlightSmall`
  grey = the macro's group ("Damage", "Panic", "Focus", ...).
- Icon: for `#showtooltip` macros, look up the spell icon
  (`GetSpellTexture(name)`), else the macro's `icon`, else the question mark.
  A spell the character doesn't know yet (low level) shows desaturated with
  subtext `Learn later`.
- **On your bars** marker: a small gold check in the icon's top-right corner
  when a real macro with this id is on an action bar.
- **Changed** marker: if the import updated a macro that's already on your bars,
  a small green up-arrow until you hover it.
- Left-click or drag: picks the macro up (creating it if needed), exactly like a
  spellbook spell. Shift-click: puts the macro body in chat for sharing.
- Right-click: small menu: `Remove from library`, `Copy text`. Since v0.10.0
  Remove from library asks first (confirm popup, 5.10).

### 5.4 Tooltip (GameTooltip)

```
Victory Rush                       (white, the full site name)
VR                                 (gold, the in-game name)
#showtooltip Victory Rush          (grey, the macro body, one line per line)
/startattack [harm]
/cast [harm] Victory Rush
New in Forever (level 20). ...     (light blue, the site note, wrapped)
Drag to an action bar.             (green, like Blizzard's usage hints)
```

### 5.5 Bottom bar

- Slot counter, two values: `Character 7 / 30` and `Account 31 / 120`. Turns
  red when full.
- Page text `Page 1 of 3` + spellbook prev/next page buttons.
- Buttons (`UIPanelButtonTemplate`): **Import**, **Tidy up**, **Settings**.

### 5.6 Import window

Opens over the Macro Book.

- Multi-line edit box (`InputScrollFrameTemplate`), placeholder text:
  `Paste the import string from the Macros page (Ctrl+V).`
- As soon as text is pasted, a preview appears:
  `14 macros: 10 new, 3 updated, 1 unchanged. 3 are for another class and will be kept for those characters.`
- Buttons: **Import** (enabled when valid), **Cancel**.
- Bad string: `That isn't a Road to Forever import string. Copy it again from the Macros page.`
- After import: the window closes, the Macro Book jumps to the first tab with
  new macros, and chat prints `Road to Forever: imported 14 macros.`

### 5.7 Other-class macros

The library keeps every class you imported. On a Warrior you only see Universal
+ Warrior tabs. A line at the bottom of the Universal tab:
`You also have macros for Paladin (53). Log in on that character to use them.`

**Changed in v0.10.0 (5.10):** the book now has a class picker, so other classes
can be browsed read-only from any character. The line stays in your own view and
now ends `Click a class icon at the top to look at them; log in on that character
to use them.`

### 5.8 Settings (small panel)

- New macros go to: Character slots first / Account slots first.
- Show minimap button / Lock minimap button (section 12.2).
- `Remove all Road to Forever macros` (confirm popup; deletes only macros this
  addon created and you haven't edited).
- Built in step 5 (v0.3.0); decisions in 6.9.

### 5.9 Text and messages

All player-facing strings live in one `Locale.lua` table (English only for now).
Errors say what happened and what to do:

| Situation | Message (red, `UIErrorsFrame`) |
|---|---|
| Drag in combat | `You can't create macros in combat.` |
| No free slot anywhere | `No free macro slots. Click Tidy up or delete a macro in /macro.` |
| Name taken by your own macro | popup: `You already have a macro called "VR". Replace it?` [Replace] [Keep mine] |

### 5.10 Decisions made while building it (class picker + Remove from library, v0.10.0, 2026-10-02)

**Not in the original plan.** Requested from the first real in-game test
(2026-10-02): the player imported Paladin macros on a Paladin (fine), then exported
**Warrior** macros from the site and imported them while still on the Paladin. Chat
said `imported 51 macros.`, but no Warrior tab appeared, because by 5.7 the book only
showed Universal + the class you're logged in as. They expected to pick any class
inside the addon and browse it from any character (e.g. to prepare an alt before ever
logging into it). In the same release, on the same file: a confirm popup for **Remove
from library** and a **tooltip on Tidy up**, also asked for after that session.

**The picker (UI/frame designer)**
- **A row of class circles**, top left of the book (from x 70, right of the portrait,
  y -46, 24 px buttons 30 px apart), the selected one checked; a label to the right:
  `Paladin (your class)` in gold or `Warrior (preview)` in grey. Icons are the
  `UI-Classes-Circles` slices the General/Shared tabs already use; highlight and
  checked textures are the side tabs' (`ButtonHilight-Square`, `CheckButtonHilight`).
  Plain `CheckButton`s, **no dropdown template**: `UIDropDownMenu` is the taint source
  6.7/6.10 already rule out, nine icons fit in one row, and icons say "class" faster
  than a list. A class without `CLASS_ICON_TCOORDS` gets the question mark instead of
  a wrong slice of the sheet. No template is used, so there is nothing to fall back
  from; the look is unverified in the client (TESTING.md 17).
- **Which classes:** exactly the classes with at least one library macro
  (`Library.ClassCounts`; Universal excluded, it shows in every view), in the site's
  roster order (cloth -> plate, Druid with leather), **your class pinned first** with
  an extra 8 px gap after it, even when you have no class macros of your own (it's the
  way back, and its view still has Universal).
- **No picker at all** when no other class has macros: one choice is no choice, and
  the book then looks exactly as before v0.10.0.
- **Picking a class** shows Universal + that class's tabs (same tab, grid, paging and
  tooltip code, fed another class), opening on the class's first section. The DPS tab
  icon now follows the **tab's** class, not the player's (a Mage browsing Paladin sees
  the melee icon).
- **A browsed class that empties** (all its macros removed) drops back to your own, so
  the book can't be stuck on a class missing from the picker.

**Read-only other classes (Taint & secure execution)**
- **Option chosen: strictly read-only for other classes, full interaction for your
  own** (the simpler, safer of the two options in the brief). Read-only = no drag, no
  click-to-pick-up, no Replace popup: a Warrior can't cast a Paladin's spells, so a
  macro made from one would fail on the bar ("Unknown spell") and still cost one of the
  30 + 120 slots, and Replace would even overwrite one of the player's own macros with
  it. Allowed while previewing: tooltips, Shift-click to chat (5.3), and the
  right-click menu (Copy text; Remove from library, below).
- **Per macro, not per view:** the test is `Macros.UsableHere(e)` = Universal or your
  class. So while previewing Warrior, the Universal tab is fully usable (Universal
  macros work on any class); only the Warrior tabs are read-only.
- **Two independent layers.** The book refuses drag/click on a read-only slot itself
  (red `Log in on a Warrior character to use this macro.`, 5.7's wording) without
  calling Macros at all; and **`Macros.Ensure`, `Macros.Create` and `Macros.Replace`
  refuse another class's macro on their own**, first thing, so no present or future
  code path can create one. A wrong-class `CreateMacro` would be a real bug, not a
  cosmetic one, so the gate lives where the write happens. `Macros.UsableHere` falls
  back to `UnitClass` if `R2F.playerClass` isn't set yet.
- **Look of a read-only slot:** icon desaturated (like an unusable spellbook entry),
  subtext = the group, **never `Learn later`** (this character will never learn that
  spell); the tooltip ends with the red line above and a green `Shift-click to put it
  in chat.` instead of `Drag to an action bar.`. Icons are mostly the question mark:
  the client only returns textures for spells this character knows; the site's `icon`
  field is used when the macro has one.
- No new globals (picker frames are unnamed), no hooks, no Blizzard template, nothing
  written to Blizzard tables. Changed flags stay own-class only (6.8; Macros.lua's
  `visible` now reuses `UsableHere`).

**Counters and on-your-bars checks while previewing**
- **They always describe the character you're playing.** `Character x / 30` /
  `Account y / 120` come from `GetNumMacros()` and the gold check from this character's
  action slots: live game state, true whatever class is browsed. Blanking them would
  hide real information (an account-slot macro made from a Warrior entry on another
  character CAN sit on this Paladin's bars, and the check then shows it).
- **The UI says so instead:** while previewing, a note above the counters on every tab
  of the preview: `Previewing Warrior macros: read-only on this character. The slot
  counts and gold checks below are for the character you're playing.`
- The 5.7 line is left out while previewing (the picker row already shows the other
  classes, and the bottom area only holds about four lines); the Quick-settings note
  (12.4.1) still shows on the Universal tab.

**Remember vs. default**
- **Remembered for the session only, in a Lua local** (`state.browse` in MacroBook.lua),
  **not in SavedVariables.** Closing and reopening the window, or switching to Home /
  Talents and back, keeps the browsed class; a relog or `/reload` always opens on your
  own class. The brief suggested "persist in R2FCharDB (or similar)" and also "always
  default back to your own class when the window is first opened fresh (e.g. after a
  relog)". A saved value that every login has to ignore is dead data, and the only thing
  it could ever do is cause the surprise the second rule forbids. Session memory gives
  both rules exactly. The tests check that nothing about browsing lands in
  SavedVariables, and that a simulated relog (SavedVariables carried into a fresh
  runtime) opens on your class.
- **An import may open a preview.** After an import the book jumps to the first tab
  with new macros (5.6). It now prefers a new Universal / own-class section
  (`Import.Diff`'s new `firstNewOwn`), so a mixed "Select everything" import still
  lands on your class. Only when the import brought nothing new for you (the original
  report: Warrior macros imported on a Paladin) does it open that class's preview.
  That isn't the surprise the default rule is about: the player just chose that class
  on the site, and seeing it is exactly what they expected. `ShowSection` on Universal
  or your class returns to your own view.

**The 5.7 line: kept, not made clickable.** One line can name several classes
(`Hunter (51), Mage (36), ...`), so a single click target would be ambiguous, and
per-class hit areas inside a font string would mean measuring rendered text widths,
which is fragile across fonts and clients. The picker circles sit right above the grid,
so the line now points at them instead (`Click a class icon at the top to look at
them; ...`).

**Remove from library (right-click menu, 5.3)**
- **It already existed** (step 3) and removed on the spot. v0.10.0 adds a **confirm
  popup** (`UI.Confirm`, the dialog Tidy up / Remove all use): `Remove <name> (<short>)
  from your library? It disappears from the Macro Book. Any macro you already made from
  it stays in the game and on your bars; Tidy up or Remove all can delete it later.`
  [Remove] [Cancel]. The entry is re-read when Remove is clicked (an import may have run
  while the popup was open); already gone = nothing happens.
- **Library only, never the real macro** (6.7 unchanged): its created record stays, so
  the button on the bar keeps working and Tidy up / Remove all can still delete it.
- **Re-import = "new" again:** `Import.Diff` compares against the library only, so a
  removed id comes back counted as `new`, not `updated`. If its real macro is still
  ours and unedited, it then follows the library like every tracked macro (what Ensure
  and the login sync would do anyway), and the gold check comes back.
- **Allowed for other classes while previewing too.** The brief's safer default was
  own-class only, with leave to decide otherwise. Removing writes SavedVariables only,
  never a game macro, so it isn't what read-only protects against; the library is
  account-wide; and without it a class imported by mistake, with no character of that
  class (exactly how the user ended up with Warrior macros on a Paladin), could never
  leave the book. The popup still asks first.
- **Right-click, not a bulk check box + Delete button.** The user also suggested a check
  box on each macro plus a Delete button next to Import / Tidy up. Single right-click won:
  the menu item already existed and 5.3 specifies it; the bottom bar has no room for a
  fourth button without shrinking the others; and check boxes on a spellbook-style grid
  would fight the drag / click / Shift-click gestures every slot already has. Cost:
  removing a whole imported-by-mistake class is one popup per macro. If that matters,
  the natural next step is a "Remove this class's macros" item on the picker circle (one
  popup for the lot), not check boxes.

**Tidy up tooltip**
- Hovering **Tidy up** shows `Tidy up` (white); gold `Deletes the macros Road to
  Forever made in your game that aren't on any action bar and that you haven't edited,
  to give you those macro slots back. Macros on a bar, and macros you edited, are left
  alone.`; grey `Your library doesn't change: the macros stay in this book and can be
  dragged out again. To take a macro out of the book itself, right-click it and choose
  Remove from library.` The last line **contrasts the two removals** on purpose: Tidy up
  = real game macros, library untouched; Remove from library = the library, real macros
  untouched. Shown while greyed out in combat too (`SetMotionScriptsWhileDisabled`, like
  Home's Quick settings boxes), with red `Can't be used in combat.`

**Testing.** `run_tests.py` adds `test_class_picker` and `test_remove_from_library`, both
on the template and fallback paths (8310 -> 8608 checks; the existing tests unchanged
except step 3's Remove test, which now accepts the popup). Covered: no picker with only
your class; the user's exact flow through the real Import window (Warrior string on a
Paladin opens the Warrior preview); picker = classes with macros only, roster order,
own class first and marked, label texts, tooltips, class circle vs question mark; drag /
click refused with the message and **no `CreateMacro` / `EditMacro` call**; `Macros.Ensure`
/ `Create` / `Replace` each refusing on their own; the book never calling `Ensure` for a
preview; no Replace popup over the player's own same-named macro; grey icons and no
`Learn later` (with a control showing the same page on a Warrior does say `Learn later`);
Shift-click; Universal draggable in a preview; counters and the gold check from this
character while previewing (an account-slot macro on this character's bar, live after
`ACTIONBAR_SLOT_CHANGED`); back to your class = drag works; the 5.7 line in your own view
only; browsing kept across close/reopen and tab switches, nothing saved, a simulated relog
opens on your class; an emptied class falls back; a mixed import prefers your class
(`firstNewOwn`, through the Import window); a Mage browsing Paladin gets the melee DPS
icon; no new globals. Remove: popup first, Cancel keeps it, Remove takes it out of the
library and grid, real macro untouched (no delete/edit call, same body, still on the bar),
record kept, Tidy up still offers it, re-import = `new`, back in the grid with its check;
accept after it's gone = no-op; a previewed class's macro removable, Copy text works there;
Tidy up tooltip lines and the combat line. **23 hand mutations** of the new code (each
guard, desaturation, Learn later, tooltip, blanked checks, picker rules, saving/resetting
the browsed class, empty-class fallback, notes, DPS icon, `ShowSection`, `firstNewOwn`, no
confirm, dropping the record, stale accept, both Tidy tooltip parts) each fail the suite.
luacheck 0 warnings. In-game checks: TESTING.md 17.

---

## 6. Addon architecture

**Role: WoW addon architect.**

### 6.1 Files

```
addon/RoadToForever/
  RoadToForever.toc
  Locale.lua        strings
  Base64.lua        decode only (~40 lines, no library)
  Import.lua        parse + validate + diff against the library
  Library.lua       SavedVariables access, ids, hashes
  Macros.lua        create / update / pick up / tidy (all real-macro calls live here)
  UI\Widgets.lua    shared: window shell + template fallbacks, confirm dialog,
                    multi-line edit box, copy box (added in step 3, 6.7)
  UI\MacroBook.lua  frame, tabs, grid, paging, tooltip
  UI\ImportFrame.lua
  TESTING.md        in-game beta checklist; CHANGELOG.md addon version history
  UI\Settings.lua
  UI\MainWindow.lua shared window, bottom tabs Home / Macros / Talents
  UI\Home.lua       Home tab
  UI\TalentPanel.lua talent link box, preview trees, Learn button
  UI\TalentGuide.lua guided mode: glow over Blizzard's talent button (step 10, 13.8)
  Talents.lua       parse link, map to the game's trees, plan, learn, export
  QuickSettings.lua Home tab's Quick settings: CVar read/write + the Macro Book's
                    hidden-macro list (v0.9.0, 12.4.1)
  Minimap.lua       own minimap button + right-click menu; uses LibDBIcon only if
                    another addon has loaded it (6.10)
  Bindings.xml      "Toggle Road to Forever", "Open Macros", "Open Talents"
                    (step 5; NOT listed in the TOC, the client loads it itself, 6.9)
  Core.lua          events, slash commands, init
  libs\            NOT shipped. Planned for LibStub, CallbackHandler-1.0,
                    LibDataBroker-1.1, LibDBIcon-1.0; dropped in step 6 over
                    LibDataBroker's license (6.10)
  media\logo64.tga  minimap icon (64x64, 32-bit with alpha)
  media\logo128.tga main window portrait
addon/art/logo.svg  logo source (not shipped); addon/art/export_logo.py exports the .tga files
addon/tests/        out-of-game tests (not shipped): run_tests.py, run_luacheck.py
.github/workflows/release.yml  builds the release zip on r2f-v* tags (section 8)
addon/.luacheckrc   allowed globals / WoW API list for luacheck
```

No embedded libraries (step 6 decided against them for the minimap button, 6.10).

### 6.2 TOC

```
## Interface: 16001 (confirmed 2026-10-02 via /dump GetBuildInfo(); tocversion=16001)
## Title: |cffffd100Road to Forever|r
## Notes: Import macros and talent builds from the Road to Forever site.
## Author: nobody174
## Version: @project-version@
## SavedVariables: R2FDB
## SavedVariablesPerCharacter: R2FCharDB
```

### 6.3 Saved data

```lua
R2FDB = {
  version = 1,
  library = {            -- every imported macro, any class, no limit
    ["WARRIOR/VR"] = { class="WARRIOR", section="General", group="Damage / offensive",
                       name="Victory Rush", short="VR", icon=nil,
                       body="#showtooltip Victory Rush\n/startattack [harm]\n/cast [harm] Victory Rush",
                       note="...", hash="a1b2c3", imported=1759350000 },
  },
  settings = { slotsFirst = "character", windowPos = {...}, lastTab = "home" },
  minimap = { hide = false, minimapPos = 220, lock = false },  -- LibDBIcon format
}
R2FCharDB = {
  created = {            -- real macros this addon created on this character
    ["WARRIOR/VR"] = { name="VR", hash="a1b2c3", account=false,
                       icon="INV_MISC_QUESTIONMARK" },  -- icon we wrote (step 4)
  },
  changed = {            -- Changed markers (5.3, step 4), cleared on first hover
    ["WARRIOR/VR"] = "updated",   -- or "edited" (site changed, your edit kept)
  },
  lastTalentLink = "warrior/--50203123300101~k7f2",
}
```

Account-slot macros are also recorded in `R2FDB.createdAccount`.

### 6.4 Real-macro rules (`Macros.lua`)

- Find a macro by **name** (`GetMacroIndexByName`), never by stored index
  (indices shift when macros are added or deleted).
- **Ensure** (on drag/click): if a macro named `short` exists and is ours
  (in `created`, hash matches) -> pick it up. If it doesn't exist ->
  `CreateMacro(short, icon or "INV_MISC_QUESTIONMARK", body, perCharacter)`, record
  it, then `PickupMacro`. If it exists but isn't ours -> the Replace / Keep mine
  popup.
- **Update** (after import): for each changed id with a real macro that is ours
  and unedited (current body hash == stored hash) -> `EditMacro`. If the player
  edited it -> leave it, mark it `Changed` and say so in the import summary.
- **Tidy up**: read action slots 1-120 (`GetActionInfo`) -> set of macro names on
  bars -> delete our unedited macros not in that set. Confirm popup lists them.
  Note in the popup: bar addons that don't use the standard action slots aren't
  seen (rare).
- Every write checks `InCombatLockdown()` first. Writes requested in combat
  (e.g. updates after an import) are queued and run on `PLAYER_REGEN_ENABLED`.

### 6.5 Events (role: event flow)

| Event | What the addon does |
|---|---|
| `ADDON_LOADED` (own name) | init/migrate saved data |
| `PLAYER_LOGIN` | read class (`UnitClass`), build tabs |
| `PLAYER_REGEN_DISABLED` | grey out Import/Tidy/drag, show `In combat` on the bottom bar |
| `PLAYER_REGEN_ENABLED` | re-enable, run queued writes |
| `UPDATE_MACROS` | refresh slot counter and markers (only if the book is open) |
| `ACTIONBAR_SLOT_CHANGED` | refresh On-your-bars markers (throttled, only if open) |
| `LEARNED_SPELL_IN_TAB` | refresh icons / Learn later state |
| `CHARACTER_POINTS_CHANGED` | talent learning: confirm the last point landed, then spend the next |
| `PLAYER_LEVEL_UP` | refresh free talent points on Home and Talents |
| `ADDON_ACTION_FORBIDDEN` / `ADDON_ACTION_BLOCKED` | (step 10) ours + `LearnTalent`: switch to guided mode (13.8) |
| `CVAR_UPDATE` | (v0.9.0) redraw Home's Quick settings boxes from the live CVars (throttled, only while Home shows, 12.4.1) |

### 6.6 Taint and secure code (role: taint auditor)

- No secure templates, no hooks on Blizzard frames, no changes to Blizzard
  tables. Don't load or touch `Blizzard_MacroUI`.
- Only one global (`R2F`); everything else `local` or on `R2F`.
- Macro creation/editing/pickup only out of combat. Nothing runs from
  `OnUpdate` except a throttled refresh while the window is open.

### 6.7 Decisions made while building it (step 3, v0.1.0, 2026-10-02)

**Globals and Blizzard tables**
- **"Only one global" means one Lua namespace.** The WoW API forces a few more
  names into `_G`, all R2F-prefixed: the SavedVariables `R2FDB` / `R2FCharDB`,
  `SLASH_R2F1` (+ the `R2F` field in `SlashCmdList`), and the frame names
  `R2FMacroBook`, `R2FImport`, `R2FConfirm`, `R2FCopy`, `R2FImportScroll`,
  `R2FCopyScroll` (a `...Plain` / `...B` suffix on fallbacks). The windows need
  names because `UISpecialFrames` (Esc to close, 5.1) works by name, and the scroll
  templates name their scroll bar `$parentScrollBar`. The test suite fails if any
  other global appears. Appending to `UISpecialFrames` and adding `SlashCmdList.R2F`
  are the only writes into Blizzard tables.
- **Own confirm dialog, not `StaticPopupDialogs`.** Writing into that shared table
  is a known taint path for protected popups; our dialog is a plain frame with
  Blizzard's dialog textures and `UIPanelButtonTemplate` buttons. Same look.
- **Own right-click menu, not `UIDropDownMenu`/`EasyMenu`/`MenuUtil`.** Avoids the
  dropdown taint problems and the open "which menu API does Forever have"
  question (11) for a two-item menu. It closes when the mouse leaves it. Step 6's
  minimap menu still has to answer that question.
- **Side tabs are built from the spellbook's textures**
  (`SpellBook-SkillLineTab`, `ButtonHilight-Square`, `CheckButtonHilight`), not
  `SpellBookSkillLineTabTemplate`: that template's scripts call Blizzard's
  spellbook functions. Page buttons use the `UI-SpellbookIcon-*Page-*` textures.

**Templates that may not exist (11)**
- Each template is checked with `C_XMLUtil.GetTemplateInfo` when the client has
  it, then created inside `pcall` and accepted only if the child keys we use exist
  (`CloseButton`, `EditBox`). Fallback chains:
  `PortraitFrameTemplate` -> `ButtonFrameTemplate` -> dialog-border frame with
  `UIPanelCloseButton` (no portrait); `InputScrollFrameTemplate` ->
  `UIPanelScrollFrameTemplate` + our own multi-line `EditBox`. Both paths are run
  by the tests. Which one the client used is visible by frame name (TESTING.md 2).
- On the template's edit box we use `HookScript("OnTextChanged")` (our own frame),
  so the template's own scroll-to-cursor handler keeps working.

**Order and labels**
- **Tab order:** the import string carries section names but not their order, so
  `Library.SECTION_ORDER` mirrors data.py's sections per class (and
  `Library.GROUP_ORDER` mirrors `ORDER`). `addon/tests/run_tests.py` fails if they
  drift from data.py. Sections the addon doesn't know yet go after the known ones
  in first-imported order (`R2FDB.sectionSeen`).
- **Entry order in a tab:** group order, then the record's position in the most
  recent import that contained it. The site writes page order and remembers the
  selection, so re-imports are normally supersets and keep this consistent.
- **Subtext under a name** = the group's text before ` / ` (`Damage / offensive`
  -> `Damage`, `Panic / defensive` -> `Panic`), or `Learn later`.
- **`Learn later`** only for macros whose `#showtooltip` spell isn't known and that
  `/cast` something; an item not in the client's cache just shows its fallback icon.
- **Shift-click** puts the body in chat with lines joined by ` ; ` (chat is one line).

**Real macros (6.4)**
- **Hash** = djb2 of the body, 8 hex digits (`Library.Hash`), taken from the body
  read *back* from the game after `CreateMacro`/`EditMacro`, in case the client
  normalises text on save (otherwise every macro would look edited).
- **Same name, identical body** (e.g. saved data lost, or typed in by hand): adopted
  as ours silently, no popup.
- **Keep mine** = nothing happens: your macro stays and nothing goes on the cursor.
  Replace = `EditMacro` in its current slot, then pick it up.
- **Our macro, edited by the player** counts as "isn't ours" for Ensure (popup).
- **Drag/click in combat is refused** with the 5.9 message, not queued: putting a
  macro on the cursor seconds later would surprise the player. Only writes that can
  wait are queued (Tidy up confirmed in combat; step 4's updates via `Macros.Update`).
- **UI combat state uses a flag from the events**, because `InCombatLockdown()` is
  still false while `PLAYER_REGEN_DISABLED` is handled. Macro writes still check
  `InCombatLockdown()` itself, which is what the game enforces.
- **Import is greyed out in combat** although it only writes SavedVariables, so
  every book button behaves the same in combat (6.5).
- **On your bars** = `GetActionInfo(slot) == "macro"`, name from `GetActionText`
  with `GetMacroInfo` as fallback, slots 1-120.
- **Remove from library** leaves a real macro made from it; it stays recorded, so
  Tidy up can still delete it later.
- **`Macros.Update` ships now but isn't called yet**; step 4 wires it into the import
  (done in v0.2.0, see 6.8).

**Import validation (7), additions**
- Whitespace anywhere in the pasted string is ignored. The id must equal
  `<class>/<short>` exactly; duplicate ids keep the first. `short` and `body` limits
  count UTF-8 characters, like build.py's `len()`. Invalid records are counted as
  skipped in the preview (`N could not be read and will be skipped.`).

**Scope for v0.1.0**
- **Tidy up ships in step 3** (with its confirm popup), since the Macros.lua rules
  include it; Settings / Remove all / keybindings stay in step 5. The Settings
  button is in place but disabled with a "later version" tooltip.
- **No main window yet:** `/r2f` toggles the Macro Book as its own window and
  `/r2f import` opens the Import window. Step 6 moves both into the main window's
  Macros tab (12.4) and adds the full slash-command set (12.3).
- **Other classes** have no tabs; the Universal tab shows the 5.7 line.

**Versioning**
- The TOC says `## Version: 0.1.0` directly (not `@project-version@`, 6.2) because
  nothing packages the addon yet; step 7's release workflow can switch to the
  token. Addon versions are tagged `r2f-v<version>` (first: `r2f-v0.1.0`).
  **Settled in step 7 (8.1):** `r2f-v*` is the one tag prefix, the release workflow
  builds from it, and the TOC keeps a literal version (no token).
- `## Interface: 16001` — confirmed 2026-10-02 against a real WoW Forever client
  (`GetBuildInfo()` returns `version="1.60.1", build="70170", tocversion=16001`).
  The original placeholder (`11507`, Classic Era 1.15.7) made the game flag the
  addon "incompatible" in the AddOns list and refuse to load it at all — with no
  Lua error, since nothing ever ran. First real in-game bug, found and fixed the
  same day the 0.9.0 zip was first installed. Shipped as `## Version: 0.9.1`.

**Testing outside the game**
- `python addon/tests/run_tests.py` runs the addon under real PUC Lua 5.1 (via the
  `lupa` Python package) against a fake client (`addon/tests/wow_stubs.lua`; its
  macro calls raise if made in combat). Import strings come from
  `addon/tests/make_fixtures.js`, which runs the site's own `importString()` code
  from macros.html in Node. `python addon/tests/run_luacheck.py <luacheck src> <argparse dir>`
  runs luacheck's library API under the same Lua 5.1 with `addon/.luacheckrc`.

### 6.8 Decisions made while building it (step 4, v0.2.0, 2026-10-02)

**When a real macro is updated**
- **One check, `classify` in Macros.lua**, read-only and safe in combat, compares a
  real macro with a library entry or an incoming import record: `none` (no real
  macro of ours), `unchanged` (already that body and icon), `edited` (live body hash
  != stored hash: the player's, never touched), `needed` (ours, unedited, different).
  The preview, the import, Ensure, the login sync and `Macros.Update` all use it.
- **"Updated" in the preview counts library records; the update itself only cares
  about the body and icon.** A record whose note or group changed is "updated" in
  the 5.6 counts but causes no `EditMacro` and no Changed marker.
- **Icon changes count**, for macros without `#showtooltip` (those always get the
  question mark). The game reports a macro's icon back as a file id, not the name we
  passed, so the created record now stores the icon name we wrote (`icon`) and we
  compare against that. v0.1.0 records have no `icon`: treated as up to date, so an
  icon-only site change to one of those waits for its next body change.
- **The hash covers the body only.** A player who changed only the icon of one of
  our macros still counts as unedited, and an update resets the icon. Accepted:
  it's rare and the body is what matters.
- **A body the player edited into exactly the new site text** counts as `unchanged`
  (nothing to write). Ensure's existing "identical body = adopt" rule then re-records
  it as ours on the next drag.
- **One write path.** `write()` in Macros.lua is the only `EditMacro` call (Replace,
  Update, Ensure). Every caller checks `InCombatLockdown()` first or goes through the
  existing `RunOrQueue` queue.

**Import (5.6) and combat**
- **The plan is taken before the library is written** (`Import.Diff` ->
  `Macros.PlanUpdates`), so the preview can say what will happen to the real macros.
  The writes then read the new library entries (`Import.Commit`). "Kept edited" only
  lists macros whose site text changed in this import, so an edited macro isn't
  reported again on every re-import of the same string.
- **Preview wording:** the 5.6 counts line stays exactly as specced. A second line
  is added only when it applies: `2 macros you already made in the game will be
  updated too. 1 you edited yourself will be left as it is.`
- **After import, chat:** `imported 14 macros.`, then `updated 2 of your macros to the
  new version.` and `kept your edits to HS. To get the new version, drag it from the
  book and choose Replace.` (names listed, so the player knows which).
- **Edited macros are left exactly as they are** but the library still takes the
  new version: the library always mirrors the latest import, and Replace in the book
  is the one way to take the site's text over your own (a choice only the player
  can make).
- **Combat:** Import stays greyed out in combat (6.7), so normally this never runs
  in combat. If it does (and for the login sync after a `/reload` in combat), the
  updates are queued as ONE job for `PLAYER_REGEN_ENABLED` with one chat line,
  instead of one queued job and line per macro. The job re-checks every macro when
  it runs, so one the player edited meanwhile is still left alone. The library write
  is SavedVariables only and happens right away.

**Changed marker (5.3)**
- **Set for** updated macros (including queued ones, marked at once) and kept-edited
  macros, **only if the real macro is on an action bar** at that moment (5.3: "a
  macro that's already on your bars"), and only for Universal / the player's own
  class (the only tabs, 5.7). Kinds: `updated` (tooltip, green: `Updated by your
  last import.`) and `edited` (orange: the site has a new version, yours was kept,
  Replace to take it). 6.4's "mark it Changed" for edited macros is this `edited` kind.
- **Stored per character** (`R2FCharDB.changed`): bars are per character, so an
  account-wide flag would show on alts without the macro on a bar, and hovering on
  one character would clear it for another that never saw it.
- **Cleared on the first tooltip**, not at import: clearing at import means nobody
  ever sees it, and clearing on any later action would leave arrows nobody knows
  how to remove. Also cleared when the library entry is removed, the real macro is
  forgotten/deleted (Tidy up), Replace installs the new version, or at login when it
  can no longer be shown. So no flag can get stuck.
- **Look:** a 16 px arrow at the icon's top-left (the On-your-bars check is
  top-right; both can show). Blizzard texture only:
  `Interface\Buttons\UI-ScrollBar-ScrollUpButton-Up` cropped to the arrow and tinted
  green with `SetVertexColor`. Unverified in the client (TESTING.md 8).

**Other characters (beyond 6.4's text)**
- **Login sync.** The library is account-wide but character-slot macros and their
  records are per character, so an import on one character can't update another's
  macros. On `PLAYER_LOGIN`, `Macros.SyncOnLogin` updates this character's unedited
  macros (and account macros) that are behind the library, same rules, and prints
  one chat line. If the game hasn't loaded the macros yet at `PLAYER_LOGIN`, every
  lookup misses and nothing is written (TESTING.md 8 checks this).
- **Ensure updates a stale macro before picking it up**, so the book never hands out
  an older version than the library (also the safety net if the login sync missed).

**Layout**
- Import window is 340 px tall (was 320) so a two-line preview that wraps can't run
  into the buttons.

### 6.9 Decisions made while building it (step 5, v0.3.0, 2026-10-02)

**Tidy up (6.4)**
- **Already shipped in step 3** (6.7); step 5 kept it and tightened one thing:
  `Macros.Tidy` now re-checks "not on a bar" (not only "unedited") at the moment it
  deletes. A Tidy up confirmed in combat runs later from the queue, and the player
  may have put one of the listed macros on a bar by then.
- **Action slots read = 1-120** (6.4). The "30" in "120 + 30" (section 2) is the
  per-character *macro* slots, not action slots; a Classic-style client has 120
  action slots (bars and the stance/stealth bonus bars included). Tests cover
  slots 1, 73 and 120.
- **Combat pattern (unchanged, now the rule for every destructive button):** the
  button is greyed out in combat (Tidy up in the book, Remove all in Settings); a
  confirm popup opened before combat and accepted during it is **queued** via
  `RunOrQueue`, not refused, and the job re-reads everything when it runs. Drag stays
  the one refused action (6.7: nothing should land on the cursor later).
- **Long name lists** in the Tidy up / Remove all popups are cut after 20 names
  (`and 12 more`, `UI.NameList`), so the dialog can't grow off the screen.

**Remove all (5.8)**
- **Spec vs. the step-5 brief.** The brief for this step described Remove all as
  deleting every macro we made "regardless of edited status". 5.8 itself says it
  "deletes only macros this addon created and you haven't edited". **5.8 wins** (this
  file is the spec): a player's edited macro is their work, and no button in this
  addon deletes it. If the owner wants the unconditional wipe, it's a one-line change
  in `Macros.RemoveAllPlan` (put every live macro in `delete`) plus the popup text.
- **Difference from Tidy up:** Remove all ignores the action bars. It deletes every
  unedited macro we made, **including ones on your bars** (those buttons go empty);
  the popup says so. Tidy up is the routine slot-saver; Remove all is "take
  Road to Forever's macros out of my game".
- **Tracking is cleared completely** (`R2FCharDB.created` and `R2FDB.createdAccount`
  end up empty, Changed flags too). Edited macros that were kept become plain
  player macros: the addon never touches them again, and dragging the same entry
  from the book later asks Replace / Keep mine (it's "not ours" now).
- **`R2FDB.library` is not touched**: the imported macros stay in the book and can be
  dragged out again.
- **Scope = this character + account slots.** The game only exposes the logged-in
  character's character-slot macros, so other characters' records stay in their own
  `R2FCharDB` until Remove all is used on that character.
- Only edited macros left (nothing to delete): the popup says so with an OK button,
  and OK just stops tracking them. Nothing tracked at all: a chat line, no popup.

**Settings panel (5.8)**
- **Own small dialog** (`R2FSettings`, dialog backdrop like the Import window, Esc
  closes it), opened/closed by the book's Settings button. Step 6 can move it into
  the main window.
- **New macros go to** (radio pair) writes `R2FDB.settings.slotsFirst` =
  `"character"` / `"account"`. Step 3 already wired it into `Macros.ChooseSlot`, which
  every `CreateMacro` asks, so the panel was the missing piece. **It doesn't move
  existing macros:** WoW has no "move to the other macro tab" call, so it would take
  delete + create, which empties every action button holding the macro. The panel
  says "Only for macros made from now on."
- **Minimap settings are stored now, used in step 6.** "Show minimap button" =
  `not R2FDB.minimap.hide`, "Lock minimap button" = `R2FDB.minimap.lock`; the table
  is exactly LibDBIcon's format from 6.3 (`{ hide = bool, lock = bool, minimapPos =
  number }`, each field filled by `Library.Init` if missing), so **step 6 passes
  `R2FDB.minimap` to `LibDBIcon:Register` as-is.** After every change the panel calls
  `R2F.Minimap.Apply()` if it exists: **step 6 must provide `R2F.Minimap.Apply`**
  (show/hide + lock/unlock from `R2FDB.minimap`, e.g. `LibDBIcon:Show/Hide/Lock/Unlock`).
  Until then the boxes only store the value and a grey line says the button comes in
  a later version (hidden automatically once `R2F.Minimap.Apply` exists).
- **Combat:** only Remove all greys out. The other settings write SavedVariables
  only, which is fine in combat, so the Settings button stays enabled.
- **Check boxes / radios** come from `UICheckButtonTemplate` / `UIRadioButtonTemplate`
  (fallback: radio -> check box -> plain CheckButton with `UI-CheckBox-*` textures).
  Labels are our own font strings (the templates' text regions differ per client).
  After a click the boxes are redrawn from the saved value, not from `GetChecked`,
  so the radio pair can never show both or neither.

**Key bindings (6.1)**
- **`Bindings.xml` is not in the TOC.** The client loads a file named exactly
  `Bindings.xml` from the addon folder on its own; listing it would also parse it as
  a UI XML file, where `<Bindings>` isn't valid.
- **Labels** are the globals Blizzard's menu looks up: `BINDING_HEADER_ROADTOFOREVER`,
  `BINDING_NAME_R2F_TOGGLE`, `BINDING_NAME_R2F_MACROS`, `BINDING_NAME_R2F_TALENTS`, set in
  `Locale.lua`. These four are the only new globals; their names are fixed by the
  client, so they can't be R2F-prefixed (6.7's global rule, extended; the tests allow
  exactly these). `category="ADDONS"` files them under AddOns in the newer key-binding
  menu (unverified in Forever, 11).
- **Actions** (`R2F.Bindings` in Core.lua), until step 6's main window exists:
  **Toggle Road to Forever** and **Open Macros** both toggle the Macro Book (what
  `/r2f` does). Open Macros toggles rather than only opening, like Blizzard's
  Spellbook key, so one key opens and closes it. **Open Talents** prints
  `the Talents window comes in a later version.` **Step 6:** Toggle = main window on
  its last tab; Open Macros = main window on the Macros tab (close if already there);
  Open Talents = the Talents tab (content arrives in step 9). Change only the three
  functions in `R2F.Bindings`; `Bindings.xml` stays as it is.
- Binding code is plain (insecure) Lua on key press; it only opens our own
  non-secure frames, which is allowed in combat, and never writes a macro.

**Testing**
- `run_tests.py` adds step-5 tests: Tidy up across slots 1/73/120 + run-time
  re-check + combat queue; `slotsFirst` steering `CreateMacro` (directly and through
  the Settings radios); Remove all (both scopes, on-bar macros, edited kept, stale
  records, tracking + Changed flags cleared, library untouched, combat refusal and
  queue, the popup text); minimap check boxes + the `R2F.Minimap.Apply` hook; the key
  bindings; `Bindings.xml` parsed as XML (labels exist, each binding calls a real
  `R2F.Bindings` function, file not in the TOC). The UI tests run on both the template
  and the fallback paths. Rendering, the key-binding menu and the popups in the real
  client are TESTING.md 9 and 10.

### 6.10 Decisions made while building it (step 6, v0.4.0, 2026-10-02)

**Libraries: none embedded (licensing).** 12.2 planned LibStub +
CallbackHandler-1.0 + LibDataBroker-1.1 + LibDBIcon-1.0 in `libs\`. Each one's
license was checked at its authoritative source on 2026-10-02:

| Library | Version checked | License found | Where |
|---|---|---|---|
| LibStub | minor 2, WowAce SVN trunk r109 | Public domain ("LibStub is hereby placed in the Public Domain", file header; TOC `X-License: Public Domain`; WowAce page: Public Domain) | `repos.wowace.com/wow/libstub/trunk/`, `wowace.com/projects/libstub` |
| CallbackHandler-1.0 | minor 8, WowAce SVN trunk r29 | BSD (TOC `X-License: BSD-2.0`; WowAce page: BSD License; Ace3's `LICENSE.txt` is the BSD text) | `repos.wowace.com/wow/callbackhandler/trunk/`, `wowace.com/projects/callbackhandler`, `github.com/WoWUIDev/Ace3` |
| LibDBIcon-1.0 | minor 56, WowAce SVN trunk r162 | **Ace3 Style BSD** on the project page (redistribution allowed with the notice; only "a stand alone version" needs permission), even though its TOC still says `X-License: All Rights Reserved` (the stale-placeholder quirk) | `curseforge.com/wow/addons/libdbicon-1-0/license`, `wowace.com/projects/libdbicon-1-0` |
| LibDataBroker-1.1 | minor 4, GitHub `tekkub/libdatabroker-1-1` commit `1a63ede` (2008) | **All Rights Reserved** on its WowAce project page; the repository has no LICENSE file, the .lua has no license header, the README and wiki say nothing about reuse | `wowace.com/projects/libdatabroker-1-1`, `github.com/tekkub/libdatabroker-1-1` |

LibStub, CallbackHandler and LibDBIcon could be shipped, but **LibDBIcon refuses
to load without LibDataBroker** (`error("LibDBIcon-1.0 requires
LibDataBroker-1.1.")`), and LibDataBroker has no grant to redistribute it at all.
It is embedded by countless addons in practice, but "everyone does it" is not a
license, and this repo is meant to go public on GitHub/CurseForge. Shipping three
libraries that can't run without the fourth would be dead weight, so **nothing
is vendored** and there is no `libs\` folder. If tekkub's terms are ever
clarified (or a LibDataBroker with a stated license appears), embedding is a
small change: `Minimap.Init` already speaks the LibDBIcon API.

**What Minimap.lua does instead (two backends, picked at `PLAYER_LOGIN`):**
- **`libdbicon`**: another installed addon already loaded LibDataBroker-1.1 and
  LibDBIcon-1.0 (common: many popular addons embed them). We create our LDB
  launcher in that copy and `Register` with `R2FDB.minimap` as-is (6.9), so
  collector addons and LibDBIcon's own options see our button. Using a library
  another addon loaded is what LibStub is for, and we redistribute nothing.
  A broken/old copy (`Register` errors) falls back to our own button (`pcall`).
- **`own`** (otherwise): a 31 px `Button` named `R2FMinimapButton` parented to
  `Minimap`, built from the textures LibDBIcon itself uses
  (`MiniMap-TrackingBorder`, `UI-Minimap-Background`,
  `UI-Minimap-ZoomButton-Highlight`), our `logo64` inside. Dragging (OnDragStart
  -> OnUpdate only while dragging -> OnDragStop) stores `minimapPos` in degrees,
  counter-clockwise from 3 o'clock: **LibDBIcon's convention**, so the saved spot
  carries over if a player's backend changes. `GetMinimapShape()` (set by square
  minimap addons) is honoured per quadrant, round by default. The name is
  R2F-prefixed (collector addons find buttons by name).
- **No `Minimap` frame at all** (a UI replacement without it): no button, no
  error; `/r2f minimap` and Settings still store the value.
- **`R2F.Minimap.Apply()`** (6.9's hook) puts `hide` / `lock` / `minimapPos` on
  whichever backend is live. The menu and `/r2f minimap` call `Settings.Refresh`
  so an open Settings panel follows them; Settings' old "comes in a later
  version" line is gone.

**Right-click menu API (11).** `MenuUtil.CreateContextMenu` when the client has it
(title / buttons / divider / checkbox, built from one item list,
`Minimap.MenuItems`). Without it, **not `UIDropDownMenu`/`EasyMenu`**: they write
Blizzard's shared `UIDROPDOWNMENU_*` state, the classic taint source (6.7 made
the same call for the book's menu). The fallback is `UI.ContextMenu`, a small
named frame (`R2FMenu`, Esc closes it) in tooltip/quest-log textures with a title
row, buttons, a divider and a check row. Both paths are tested.

**Tooltip (12.2).** As specced; `Drag to move.` is left out while the button is
locked (it can't be dragged then). Free talent points come from Classic's
`UnitCharacterPoints("player")` (guarded; newer clients removed it).

**Main window (12.4).**
- **The Macro Book was reparented, not rebuilt.** `UI/MainWindow.lua` owns the
  window (`UI.Window("R2FMain", 540, 500, "windowPos")`, so the same template
  chain and fallbacks as step 3: `R2FMain` / `R2FMainB` / `R2FMainPlain`) and
  makes one page frame per tab filling it. `MacroBook.Build(page)` draws the
  book's slots, side tabs and bottom bar into the Macros page at the old offsets
  (same window size). The book's public functions keep their meaning, so
  Core/Import/Settings and the step-3 to step-5 tests still drive it: `Show` /
  `Toggle` = main window on the Macros tab, `IsShown` = visible (`IsVisible`,
  since a page keeps its own shown flag while the window is closed). There is no
  separate `R2FMacroBook` window any more; the window's saved spot
  (`settings.windowPos`) carries over from the book.
- **Portrait = `logo128`** (12.4) instead of the class icon (5.1): the window is
  shared by all tabs. The title follows the tab: `Road to Forever`,
  `Road to Forever: Macros`, `Road to Forever: Talents`.
- **Bottom tabs:** `PanelTabButtonTemplate` -> `CharacterFrameTabButtonTemplate`
  -> plain `UIPanelButtonTemplate` buttons, each checked like every template
  (6.7). Named `<window>Tab1..3` (older `PanelTemplates_*` and the Classic
  template's `$parent` textures need names). Selection via Blizzard's
  `PanelTemplates_SetTab` on our own frame (no taint: it only touches the frame
  passed in); without it, the selected tab is disabled. Gaps between tabs
  (3 / -15 / 4 px) are guesses until the beta (TESTING.md 11).
- **Default tab = Home** (6.3's `lastTab = "home"`): first open shows Home with
  the Import button and the how-to line; after that, the last tab used
  (`settings.lastTab`, validated by `Library.Init`).
- **Size is fixed** (540 x 500). 12.4 says "position, size and last tab are
  saved": position and last tab are; the book's 2 x 6 grid is laid out for that
  size, so a resize handle would only add empty space. Revisit with the Talents
  tab (step 9) if it needs more room.
- **Home** (`UI/Home.lua`): two big spellbook-style entries (44 px icon in the
  quick-slot border, the whole row clickable): Macro Book with
  `N macros in your library, M on your bars` (N = whole library, all classes;
  M = macros this addon made, character + account records, that are on this
  character's action slots, the book's gold-check rule) and Talents with
  `Coming in a later version` (12.4's free-points text arrives with the talent
  steps). Below: **Import macros** (greyed out in combat like the book's Import,
  6.7) and a one-line how-to. Counts refresh on `UPDATE_MACROS` /
  `ACTIONBAR_SLOT_CHANGED`, throttled to 0.2 s like the book.
- **Talents tab** is a placeholder text until steps 8 to 10 (`UI/TalentPanel.lua`).
  **Step 9 (13.7)** replaced it with the link box, preview trees and Copy my build,
  and Home's Talents line with the free points (12.4); the 540 x 500 size was
  enough, so the window stays fixed.
- **Settings and Import stay their own dialogs** over the window (6.9 allowed
  moving Settings in; not needed).

**Entry points.** `/r2f`, the minimap left-click and the **Toggle** key toggle the
window on its last tab. **Open Macros** / **Open Talents** keys open that tab, or
close the window if that tab is already showing (6.9). `/r2f macros`,
`/r2f talents` and `/r2ft` only open (typing a command never hides what you asked
for). `/r2f minimap` toggles hide with a chat line either way. `/r2f import`
(step 3) still works (Macros tab + Import window). `/r2f help` prints the list,
anything else prints `unknown command`. Menu > Open Road to Forever opens on the
last tab.

**Globals (6.6/6.7 extended).** New: `SLASH_R2FT1` (+ `SlashCmdList.R2FT`) for
`/r2ft`, and R2F-prefixed frame names `R2FMain` (`...B`/`...Plain`),
`R2FMainTab1..3`, `R2FMinimapButton`, `R2FMenu`. Nothing else; the tests' global
audit allows exactly these. `LibStub` is only **read** (via `_G`), never created:
if it exists, another addon made it.

**Logo (12.1).** Hand-written `addon/art/logo.svg` (128 grid: navy radial disc,
gold road narrowing from the bottom edge with a dashed navy centre line, joining
an infinity band 16 units wide = 8 px at 64 px, darker gold edge, pale highlight
along the top). `addon/art/export_logo.py` rasterises it with **resvg** (real SVG
renderer, `resvg_py`, run with `py -3.12`; cairosvg is installed but has no cairo
DLL on this machine), at 4x then Lanczos-downscaled, and writes the TGAs with
Pillow: uncompressed type 2, 32 bpp, 8 alpha bits, transparent outside the disc.
The script re-reads its own output and checks header, size and alpha; the test
suite checks the same. The 20 px preview was checked by eye; the in-game check is
TESTING.md 11.

**Testing.** `run_tests.py` adds step-6 tests on both template and fallback paths
(Apply vs `R2FDB.minimap`, drag angles, square minimap, tooltip, both menu
backends and every item, all slash commands, bindings, tab switching + titles +
saved last tab, Home counts and buttons, the reparented book's refresh / tabs /
drag / tooltip / paging / menu), a fake LibDBIcon for the `libdbicon` backend
(plus a broken copy and no Minimap), and the TGA headers. Spot mutations of the
new code (hide ignored, lastTab not saved, counts ignoring bars, `IsShown` instead
of `IsVisible`, lock ignored, square shape ignored) each fail tests.

---

## 7. Import string format

```
R2F1:<base64 of the payload>
```

Payload (UTF-8 text):

```
v=1
<record>\30<record>\30...
```

Each record = fields joined by `\31` (unit separator), in this order:
`id, class, section, group, name, short, icon, body, note`.
Body keeps its real newlines. Empty icon = `""`.

- Version prefix `R2F1:` lets a future `R2F2:` change the format; the addon
  rejects unknown versions with: `This import string is from a newer site
  version. Update the addon.`
- The site builds it with `btoa(unescape(encodeURIComponent(text)))` (UTF-8 safe);
  the addon decodes with `Base64.lua`.
- Size check: 50 macros is about 10 KB of text. Test that pasting 20 KB into the
  edit box is fine; if it's slow, switch to LibDeflate compression (`R2F2:`).
- Validation: every field present, `short` <= 16, body <= 255, class is a known
  token or `ANY`. Invalid records are skipped and counted in the preview.

---

## 8. Release

- GitHub Actions (`.github/workflows/release.yml`): on a pushed `r2f-v*` tag, zip
  `addon/RoadToForever/` into a Release (`RoadToForever-<version>.zip`, folder
  inside the zip). Built in step 7, decisions in 8.1.
- Site: Download link in the export tray's How to import steps -> Releases page.
- Later: CurseForge project (auto-updates through the CurseForge app).

**How to release a version:** bump `## Version:` in `RoadToForever.toc`, add the
`## <version> (date): ...` section to `addon/RoadToForever/CHANGELOG.md`, commit,
then `git tag r2f-v<version>` and `git push origin main r2f-v<version>`. The run
shows under the repo's Actions tab.

### 8.1 Decisions made while building it (step 7, v0.5.0, 2026-10-02)

- **Tag prefix: `r2f-v*`, final.** The original text here said `addon-v*`, but
  steps 3 to 6 had already pushed `r2f-v0.1.0` .. `r2f-v0.4.0` (6.7). Those tags
  are public, so they are not renamed, and a second prefix would only mean two
  ways to tag the same thing. The workflow triggers on `r2f-v*` only. The four
  older tags don't get releases (the workflow didn't exist when they were
  pushed); `r2f-v0.5.0` is the first release.
- **Zip = `git archive --prefix=RoadToForever/ HEAD:addon/RoadToForever`.** Archiving
  the folder's *tree* and re-rooting it gives `RoadToForever/RoadToForever.toc`
  at the top of the zip, so it unpacks straight into `Interface/AddOns/` (WoW
  loads an addon only when the folder name equals the `.toc` name). It packs
  tracked files only (no stray local files), `addon/tests` and `addon/art` are
  outside that tree, and the same command runs on a PC, which is how step 7
  checked the zip without GitHub (TESTING.md 12). No `zip` step, no extra script.
- **Everything in `addon/RoadToForever/` ships**, including `CHANGELOG.md` and
  `TESTING.md` (small, harmless in an AddOns folder, and they tell a tester what
  the version is meant to do). `Bindings.xml` and `media/` ship because the client
  needs them. No libraries (6.10).
- **TOC keeps a literal `## Version:` (no `@project-version@`, 6.2).** That token
  is filled by the CurseForge/BigWigs packager, which we don't use; with plain
  `git archive` it would ship as the literal text `@project-version@`. Instead the
  workflow **fails if the tag's version differs from the TOC's** (or isn't plain
  `x.y.z`), so a release can never carry a wrong in-game version. The version
  reaches the shell steps through `env`, not pasted into the script. Revisit when the CurseForge project (later)
  brings its packager.
- **0.x = pre-release, 1.0.0+ = normal release**, decided by the version string
  (`0.*`). Every 0.x version is untested in the real client (TESTING.md), so the
  Releases page must not present it as finished.
- **Download link stays on `/releases`, not `/releases/latest`.** GitHub's
  "latest" skips pre-releases, so while every release is 0.x it has nothing to
  point at. `/releases` lists the newest release (pre-release or not) first.
  Switch the link to `/releases/latest` when 1.0.0 ships. The step only made the
  link's text clearer (the zip's name, unzip into `Interface\AddOns\`).
- **Release notes = that version's section of the addon `CHANGELOG.md`** (heading
  `## <version> (`, up to the next `## `), plus an install line; a plain line if
  the section is missing. Title `Road to Forever <version>`. Action:
  `softprops/action-gh-release@v2` (the common one), `fail_on_unmatched_files`
  so a missing zip fails the run instead of making an empty release.
- **Step 7 bumped the addon to 0.5.0 although no Lua changed.** Every step from 3
  on takes the next minor version and its tag always equals the TOC version (the
  workflow now enforces that), so "step 7 = 0.5.0" keeps one version line for the
  whole plan. The 0.5.0 zip is functionally 0.4.0; its CHANGELOG entry says so.
- **What couldn't be tested here:** the workflow only runs on GitHub. Before the
  push: YAML parsed, actionlint 1.7.12 clean (without shellcheck), every shell
  step traced by hand, and the packaging, version-check (matching, mismatched
  and malformed tags) and notes commands run locally on the same tree. The `r2f-v0.5.0`
  push is the workflow's first real run (TESTING.md 12). **Result:** green; the
  release is a pre-release with the CHANGELOG notes and one asset, identical to
  the local zip; `/releases/latest` was confirmed to redirect to `/releases`
  while only pre-releases exist.

## 9. Build order (each step shippable)

1. **Data**: `short` + `icon` + ids in `data.py`, build checks, short names shown
   in the markdown. Warrior and Paladin first (tables above), then the rest.
2. **Site export**: export mode, checkboxes, tray, Copy import string.
3. **Addon MVP**: import window, library, Macro Book for own class + Universal,
   click/drag creates the macro, slot counter, combat lock.
4. **Updates**: re-import updates unedited macros; Changed markers.
5. **Tidy up**, Settings, Remove all, keybindings.
6. **Main window + minimap**: Home / Macros / Talents tabs, logo, minimap
   button (own, not LibDBIcon: 6.10) with right-click menu, `/r2f`, `/r2ft`, `/r2f minimap`. Moves the
   step-3 Macro Book (`R2F.MacroBook`) and Import window into the main window
   (6.7).
7. **Release** zip + Download link. CurseForge later. Tag prefix settled:
   `r2f-v*` (8.1).
8. **Talent export** (read-only, no risk): Copy my build as a link. Site links get
   the `~hash` check (section 13.3). Done in v0.6.0; decisions in 13.6.
9. **Talent import preview**: paste link, mini trees, summary, warnings. Nothing learned.
   Done in v0.7.0; decisions in 13.7.
10. **Talent learning**: Learn talents + confirm popup, point-by-point learning
    (or the guided fallback if `LearnTalent` is blocked). Done in v0.8.0; decisions
    in 13.8.
11. **Quick settings** (added to the backlog 2026-10-01, after step 10): three Home
    check boxes that set CVars directly, and the Macro Book hides the three site
    macros they replace. Done in v0.9.0; decisions in 12.4.1. This was the last
    planned build step.
12. **Class picker + Remove from library confirm + Tidy up tooltip** (not planned:
    requested after the first real in-game test, 2026-10-02). Browse any class in
    the library read-only from any character. Done in v0.10.0; decisions in 5.10.

## 10. Later / ideas

- Own action bar mode (secure buttons with macro text) for players who want
  more than 138 macros on bars. Big job; only if really needed.
- Talent leveling order on the site (which talent first), so a partial build
  learns your priorities instead of top-down.
- Export from the game back to the site (share your edited macros).

## 11. Things to confirm in the beta

- [x] TOC `## Interface:` number — confirmed `16001` 2026-10-02. Note:
      `select(4, GetBuildInfo())` itself came back empty on this client; use
      `select(4, GetBuildInfo())` only after confirming `GetBuildInfo()` returns
      4 values via a plain `/dump GetBuildInfo()` first (this client returns
      `version, build, date, tocversion` — 4 values — so the call should have
      worked; the empty result is unexplained and worth a second look, but a
      plain full dump always works as the fallback).
- [x] Slot limits — confirmed 2026-10-02: account is still 120 (unverified
      directly but unchanged from Classic conventions), character is **30**, not
      vanilla/Classic Era's 18 (`/dump MAX_CHARACTER_MACROS` came back nil, same
      as the Interface-number quirk; confirmed by counting the real `/macro`
      Character tab: 5 rows of 6). Fixed in `Macros.lua`'s fallback constant.
- [ ] `PortraitFrameTemplate`, `InputScrollFrameTemplate`, spellbook tab and page
      button templates exist in the Forever client (`/fstack` on the spellbook).
- [ ] `CreateMacro` then `PickupMacro` in the same click works (else a 0-second
      `C_Timer.After`).
- [ ] Question-mark icon + `#showtooltip` shows the spell icon on the bar.
- [ ] Macros created by the addon survive a relog (server sync).
- [ ] Pasting a 20 KB string into the edit box is fast enough (also try the
      ~83 KB "Select everything" string, section 4.5).
- [ ] Macros are readable at `PLAYER_LOGIN` and `EditMacro` works from there
      (login sync, 6.8); the green Changed arrow texture looks right (6.8).
- [ ] `Bindings.xml` is picked up without a TOC entry, the three bindings show under
      a "Road to Forever" header (AddOns section, `category="ADDONS"`) and work;
      `UIRadioButtonTemplate` / `UICheckButtonTemplate` exist (Settings) (6.9).
- [ ] Minimap button (our own, 6.10) drags around the round minimap and saves its
      spot, looks like other minimap buttons, and the logo reads at that size (12.1).
- [ ] Right-click menu API: does `MenuUtil` exist? (If not, our own menu frame is
      used; `UIDropDownMenu`/`EasyMenu` are deliberately never used, 6.10.)
- [ ] Bottom tab template: `PanelTabButtonTemplate` or `CharacterFrameTabButtonTemplate`
      (main window, 6.10).
- [ ] `LearnTalent(tab, index)` works from our button click (else guided mode), **and
      from an event/timer callback** (every point after the first is sent from
      `CHARACTER_POINTS_CHANGED`, 13.8). `GetTalentPrereqs` returns `tier, column,
      isLearnable`. Points land within 0.5 s (else raise `Talents.LEARN_TIMEOUT`).
- [ ] Classic has no talent preview/commit (or, if Forever adds one, use it): what does
      `/dump GetCVarBool("previewTalents"), AddPreviewTalentPoints` say (13.8)?
- [ ] Guided mode: Blizzard's talent window is `TalentFrame` or `PlayerTalentFrame`,
      buttons `<frame>Talent<i>` = talent index i, `ToggleTalentFrame` exists (13.8).
- [ ] Sorting `GetTalentInfo` by tier then column gives the same order as our
      share links (test with the level-30 builds). Since step 8 this has a direct
      test: `/r2f copybuild`'s `~hash` must equal the site's for your class
      (TESTING.md 13); equal hashes prove names, order and tab order all match.
- [ ] Talent tab order (`GetTalentInfo(tab, ...)` for tab 1..3) matches `talentcalc.js`
      `CLASSES` order. Step 8 doesn't call `GetTalentTabInfo` at all (its return
      shape differs between client versions); the hash check above covers the order.
- [x] `GetNumTalentTabs` / `GetNumTalents` / `GetTalentInfo` exist: **no** (answered
      2026-10-02; `Blizzard_TalentUI` is `MISSING`). Talents are read via `C_Traits`
      since v0.10.4 (13.10). The sort/tab-order items above now mean the C_Traits
      reader's tier/column ranks and pane split; the per-class hash check is the test.
- [ ] C_Traits reader (13.10): Protection/Retribution posX and every class other than
      Paladin unseen; `activeRank` vs pending points; `SetSpellByID` tooltip; which
      event fires on Apply Changes; does `GetTalentTabInfo` exist (else `Tree 1..3`).
      Talent names come back in English on an English client (the hash is over names).
- [ ] `GameTooltip:SetTalent(tab, index)` shows the talent tooltip from our mini
      trees, and `GetTalentTabInfo(tab)` returns the tree name first or second
      (13.7; else the headers read `Tree 1..3`). `InputBoxTemplate` exists (link box).
- [ ] The mini trees read well at 26 px (13.7: talent-frame ring tints, glow, badge).
- [ ] Class picker (5.10): the row of class circles fits between the portrait and the
      grid; `SetMotionScriptsWhileDisabled` exists (Tidy up tooltip while greyed out).
- [ ] Quick settings (12.4.1): `GetCVar` / `SetCVar` / `GetCVarDefault` exist and know
      `cameraDistanceMaxZoomFactor`, `UnitNamePlayerGuild`, `UnitNamePlayerPVPTitle`;
      the client takes `cameraDistanceMaxZoomFactor 4` without clamping it; whether
      `SetCVar` on these three is really blocked in combat (we refuse in combat either
      way); `CVAR_UPDATE` fires on a `/console` change.

---

## 12. Main window, minimap button and logo

**Roles: in-game UI/frame designer + graphic designer.**

### 12.1 Logo

- **Idea:** "Road to Forever" as one shape: a road that starts at the bottom of
  the circle, narrows into the distance and curls into an infinity sign (∞).
  It ties into the site's hero art (a path climbing toward the sky isles).
- **Colors:** the site's own: gold road `#FFD100` with a darker gold edge
  `#C79C00` and a thin pale highlight `#FFE566` along the top; background disc a
  radial navy from `#2A335A` (center) to `#0E1428` (edge).
- **Small-size rule:** it must read at 18 to 20 px on the minimap. So: no text,
  no letters, only the road + ∞, thick strokes (at least 8 px on the 64 px
  version), strong contrast against the navy.
- **Files:** draw it as vector `addon/art/logo.svg` (hand-made SVG so it stays
  crisp; ComfyUI is fine for exploring ideas, not for the final). A small script
  exports `media/logo64.tga` and `media/logo128.tga` (32-bit, transparent
  outside the circle, power-of-two sizes as WoW needs). Check it in-game at the
  real size before calling it done.
- Later the same logo can be the site favicon, so site and addon feel like one thing.

### 12.2 Minimap button

- ~~Built with **LibDataBroker-1.1 + LibDBIcon-1.0** (embedded in `libs\`).~~
  **Changed in step 6 (6.10):** our own button from the same Blizzard textures
  LibDBIcon uses (standard round minimap-button border, so it looks native),
  **dragging around the minimap edge** (position saved), square-minimap support.
  If another installed addon already loaded LibDataBroker + LibDBIcon, the
  button is registered through that copy instead, which also makes it visible to
  minimap-button collector addons. Nothing is embedded.
- **Left-click:** open/close the main window (on the tab you used last).
- **Right-click:** menu:

```
 Road to Forever          (gold title, not clickable)
 Open Road to Forever
 Macros
 Talents
 ------------------
 Lock button position     (check item)
 Hide minimap button
```

- **Drag:** move it around the minimap (disabled when locked).
- **Tooltip:**

```
Road to Forever                         (gold)
38 macros in your library               (white)
5 free talent points                    (white, only when > 0)
Left-click to open.                     (green)
Right-click for options.                (green)
Drag to move.                           (green)
```

- **Hide minimap button:** hides it and prints in chat:
  `Road to Forever: minimap button hidden. Type /r2f minimap to show it again.`
  Also a checkbox in Settings.

### 12.3 Slash commands

| Command | Opens |
|---|---|
| `/r2f` | main window, last used tab |
| `/r2f macros` | Macros tab |
| `/r2ft` or `/r2f talents` | Talents tab |
| `/r2f minimap` | shows the minimap button again (toggles) |
| `/r2f copybuild` | Copy my build popup (step 8; since step 9 also a Talents tab button, the command stays as a shortcut, 13.7) |
| `/r2f help` | prints the list above |

### 12.4 Main window

One window (`PortraitFrameTemplate`, portrait = `logo128`), three bottom tabs
in Blizzard's character-frame tab style (`PanelTabButtonTemplate`, or the
Classic `CharacterFrameTabButtonTemplate`):

| Tab | Content |
|---|---|
| **Home** | two large entries in spellbook-slot style: **Macro Book** (`38 macros in your library, 12 on your bars`) and **Talents** (`5 free talent points`, or `No free talent points`). Clicking one switches tab. Below: Import macros button. Below that: **Quick settings** (12.4.1). |
| **Macros** | the Macro Book (section 5) |
| **Talents** | section 13.4 |

Window position, size and last tab are saved. Esc closes it. Same sounds as the
Spellbook.

**Quick settings (Home tab, built in v0.9.0).** Three check boxes that change game
settings directly with `SetCVar`, so no macro and no macro slot is used:

```
 Quick settings
 These change your game settings directly. No macro or macro slot needed.
 [x] Max camera zoom      cameraDistanceMaxZoomFactor 4   (unticked = GetCVarDefault)
 [ ] Hide guild names     UnitNamePlayerGuild 0           (unticked = 1)
 [ ] Hide PvP titles      UnitNamePlayerPVPTitle 0        (unticked = 1)
```

- The boxes read the current value with `GetCVar` whenever the Home tab is drawn,
  so a value set some other way shows correctly. Out of combat only.
- The three site macros that do the same (`ANY/Zoom`, `ANY/HideGuild`,
  `ANY/HidePvP` in data.py's Universal "Misc / UI" group) **stay on the website**
  for players without the addon; the addon **hides them from the Macro Book**.

### 12.4.1 Decisions made while building it (Quick settings, v0.9.0, 2026-10-02)

**Where the code lives.** `QuickSettings.lua` (new, top level like `Macros.lua` /
`Talents.lua`: logic, no frames) holds the three items (`QuickSettings.ITEMS`: CVar,
on value, off value, the site macro id it replaces), reads/writes the CVars and
answers the Macro Book's `HidesMacro(id)`. `UI/Home.lua` draws the boxes. One table
drives both, so the boxes and the hidden macros can't drift apart.

**Reading (Event flow).**
- The boxes are redrawn from `GetCVar` on every Home refresh: tab opened (the
  existing `MainWindow` page hook), combat start/end (`Home.SetCombat`), and the new
  `CVAR_UPDATE` (fires when anything changes a CVar: `/console`, Blizzard's options,
  another addon, ours). `CVAR_UPDATE` goes through Home's existing 0.2 s throttle and
  does nothing while Home isn't showing. `PLAYER_ENTERING_WORLD` isn't needed: CVars
  are loaded before any addon code runs, and nothing is read until Home is drawn.
- **Nothing is stored in SavedVariables.** The game saves CVars itself; a stored copy
  could only disagree with the live value, and the box must show reality.
- **"Ticked" = the live value equals the on value**, compared as numbers when both
  are numbers (a client may report `4` as `4.000000`). A zoom at 2.2 set by something
  else shows unticked; ticking it sets 4.
- After a click the box is redrawn from the live value again (6.9's rule: never from
  `GetChecked`), and the click flips the *live* value, not the box's own state, so a
  stale box can't write the wrong way.

**Writing.**
- **Zoom unticked = `GetCVarDefault("cameraDistanceMaxZoomFactor")`, never a typed-in
  number.** The default differs between client versions and Forever may change it;
  a guessed "default" would leave the player on a camera distance they never chose,
  with nothing on screen saying so. If the client has no `GetCVarDefault` (or it
  returns nothing), unticking is **refused** with `Couldn't read the game's default
  for this setting, so it was left as it is.` (ticking still works). Guild and PvP
  titles have fixed off values (`1`), as specced.
- **Read back after `SetCVar`** (`pcall`-guarded). If the game refused the value,
  raised, or stored something else (e.g. clamped the zoom to its own maximum), the
  player sees `The game didn't accept that setting.` and the box shows the live value.
- **API lookup:** the global `GetCVar` / `SetCVar` / `GetCVarDefault` first (Classic
  Era), else `C_CVar.<same name>` (newer clients keep only that table). Missing
  `SetCVar`, or `GetCVar` returning nil for that CVar (unknown in this client): the
  box is greyed out with the tooltip `Your game doesn't have this setting.`

**Combat (Taint & secure execution).**
- **Refused in combat, as BACKLOG specifies** ("Out of combat only"). The boxes grey
  out on `PLAYER_REGEN_DISABLED` (the Import button's rule, 6.7) with `Can't be changed
  in combat.` in the tooltip, and `QuickSettings.Set` itself checks `R2F.InCombat()`
  (event flag + `InCombatLockdown()`) **before** `SetCVar`, as the backstop for a click
  landing between the event and the redraw (`You can't change game settings in combat.`).
- **Refused, not queued:** a click is not a confirmed popup (6.9 queues only those),
  and a setting flipping by itself after the fight would be a surprise (6.7's drag
  rule).
- **Whether the real client blocks `SetCVar` for these three CVars in combat is
  unconfirmed.** Some CVars are combat-protected in newer clients (mostly nameplate
  ones); these three are probably not. The gate is implemented anyway because the
  BACKLOG item states it as a requirement, it costs nothing (nobody needs to change
  camera zoom mid-pull), and it keeps every write in this addon under one rule. If the
  beta shows they're unprotected, the gate can stay. TESTING.md 16 checks it.
- No frames are named (no new globals), nothing of Blizzard's is hooked or written;
  `SetCVar` from addon code out of combat is an ordinary call. A source test pins every
  CVar API use to `QuickSettings.lua` and the combat check before the write.

**The Macro Book (hiding the three).**
- **Exact ids, not a pattern:** `ANY/Zoom`, `ANY/HideGuild`, `ANY/HidePvP`, the ids
  build.py makes from data.py (`ANY/` + `short`). A pattern ("contains Zoom", "body
  has /console") would also hide unrelated macros: a player's or the site's future
  macro that mentions the camera, or a class macro whose short happens to be `Zoom`.
  The tests check the ids **against data.py's own output** (each must be the
  `/console <cvar> <on>` macro in macros.html), so renaming a `short` on the site fails
  the tests instead of silently showing the macro again.
- **Hidden only in the grid** (`MacroBook` filters each tab's entries; a tab left empty
  disappears; the tab tooltip counts what's shown). They **stay in the library**: an
  import still stores them (the preview counts them as usual), and a real macro a
  player already made from one is still tracked, updated, tidied and removed like any
  other. Home's `N macros in your library` keeps counting the whole library.
- **Only while its box can work:** if this client lacks the CVar or `SetCVar`, the
  macro is shown again, so the player always has one way to get the setting.
- **A line on the Universal tab** says where they went, when the library has any of
  them: `Zoom, guild names and PvP titles are Quick settings on the Home tab, so no
  macro is needed.` (after the 5.7 other-classes line).

**Layout.** Heading `Quick settings` (GameFontNormal) + a grey note, then the three
boxes (`UI.CheckButton`: same `UICheckButtonTemplate` -> plain CheckButton chain as
Settings, 6.9) under Home's import hint, 26 px apart; labels grey out with the box.
Each box has a tooltip naming the CVar. Positions are unverified in the client
(TESTING.md 16).

**Testing.** `run_tests.py` adds `test_quick_settings` (template and fallback paths).
The stubs got `GetCVar` / `SetCVar` / `GetCVarDefault` (strings; a default of `1.7`,
deliberately not a usual one; `SetCVar` logs every call, raises in combat, can clamp
or raise on demand, and fires `CVAR_UPDATE`). Covered: the items vs data.py; boxes read
values set elsewhere on open, after `CVAR_UPDATE` and on re-opening Home; tick/untick
write exactly `4` / the default (two different defaults) / `0` / `1`; flip from the
live value; no `GetCVarDefault` (refused, message) and the `C_CVar` fallbacks; combat
by event flag and by lockdown alone (refused, nothing written, boxes greyed, tooltip),
working again after; clamp and raise reported; the book hides exactly the three ids
while look-alikes (`ANY/ZoomIn`, `ANY/HideGuilds`, `WARRIOR/Zoom`, wrong case/space)
stay, every other Universal macro shows, tab count, the note, library and Home count
unchanged; an unknown CVar or no `SetCVar` brings the macro back and greys the box; a
library holding only the three; nothing in SavedVariables; no new globals; the source
pins. 15 hand mutations of the new code (combat gate, hardcoded default, hide
regardless, pattern match, toggle direction, read-back, numeric compare, pcall,
`C_CVar` fallback, book filter, empty tab, note, live read, combat greying,
`CVAR_UPDATE`) each fail the suite.

### 12.4.2 Version/author footer (v0.10.1, 2026-10-02)

**Why.** Real in-game testing: no way to see the addon's version, who made it, or
where it came from short of opening the TOC file by hand.

**Where it lives.** One line at the very bottom of the Home tab (`UI/Home.lua`,
`buildFooter`), below Quick settings, `GameFontDisableSmall` (the same quiet style
`Settings.lua`'s slot-order note already uses) so it doesn't compete with the real
content above it. Built once with the page, like every other Home widget — it isn't
re-read on every tab open, since the version/author genuinely can't change mid-session.

**Source of truth.** Reads the TOC's own `## Version:` / `## Author:` fields through
`GetAddOnMetadata`/`C_AddOns.GetAddOnMetadata`, never a second hardcoded string, so the
footer can't quietly drift out of sync with the TOC the way two independent copies of
the same fact eventually do.

**API existence check.** Same pattern as every other client-API uncertainty in this
project (section 11): the metadata function moved from a bare global to `C_AddOns` at
some point, and this project has already found this exact client leaves some legacy
globals undefined (`GetBuildInfo()`'s 4th return value, `MAX_CHARACTER_MACROS`). Tries
`C_AddOns.GetAddOnMetadata` first, falls back to the bare global, and if neither exists
(or the call itself errors — wrapped in `pcall`) shows a plain line with no version
number rather than erroring or showing a blank. Not an error state: just an older/odd
API surface, same stance as the rest of this addon's defensive checks.

**Content:** `Road to Forever v<version> · by <author> · nobody174.github.io/wow-forever`
when both fields are readable; `Road to Forever · nobody174.github.io/wow-forever` with
no version/author shown otherwise. Hovering the line shows the TOC's own `## Notes:`
text (held as its own locale string rather than re-read live, matching how every other
tooltip in this addon is built) as a one-line "what is this and why" — the same text
already seen in the AddOns list, so the in-game and TOC descriptions can't contradict
each other either.

**Tested:** real version/author shown when either metadata API exists; the "neither
exists" fallback line (no version, no error) via `C_AddOns = nil, GetAddOnMetadata =
nil`; the legacy-only path (`C_AddOns = nil`, bare global only) still reads real values;
hover shows and clears the tooltip; no new globals (the hit-frame marker is a table
field, not a global). Both the template and Blizzard-template-less fallback UI paths.

---

## 13. Talent import / export

### 13.1 Flow

```
 Site talent calc / Builds page          In-game Talents tab
 ------------------------------          ------------------------------------
 [Copy link]  --- clipboard --->  paste link -> Preview (nothing learned)
                                         -> Learn talents -> confirm popup
                                         -> points learned one by one
 talents.html#warrior/...  <--- clipboard ---  [Copy my build]
```

The link from **Copy link** is the import format. No separate string.

### 13.2 Reading the link

- Accept any of: full URL, `talents.html#warrior/3232...`, `#warrior/3232...`,
  `warrior/3232...`. Lua pattern: `(%a+)/([%d%-]*)(~?%w*)`.
- Class must match the character (`select(2, UnitClass("player")):lower()`).
  Wrong class: `This is a Paladin build. You're playing a Warrior.`
- Mapping to the game: for each talent tab (`GetNumTalentTabs`), list every
  talent with `GetTalentInfo(tab, i)` -> name, icon, tier, column, rank, maxRank.
  (**13.10:** those don't exist on WoW Forever; the same lists now come from
  `C_Traits`, panes split by position. The sort below is unchanged.)
  **Sort by tier, then column.** Digit k of that tree's part of the link = planned
  rank of the k-th talent in this sorted list (that's how the site encodes it:
  Wowhead's row/column order). Missing trailing digits = 0.

### 13.3 Mismatch protection (the `~hash`)

The link only stores numbers, not talent names, so if the site's data and the
game differ (like the missing Crusade talent) points could land on the wrong
talent. Fix:

- The site appends a short check to every copied link:
  `talents.html#warrior/3232020303201~k7f2`. The check is a hash of that class's
  talent names in link order, all three trees (djb2, base36, 4 characters).
  Same function in `talentcalc.js` and `Talents.lua`.
- `talentcalc.js` ignores everything from `~` when reading a link, so old and
  new links both still open. Bump the `?v=` on both pages when changing it.
- The addon computes the same hash from the game's names:
  - match -> safe;
  - different -> stop: `This link was made with different talent trees than
    your game has. Nothing was learned. Make a new link on the site or wait for
    the site to update.`;
  - no hash (old link) -> allowed, with a yellow line `Older link: can't check it
    against your talent trees.`
- Extra sanity checks always: no planned rank above a talent's max rank, no
  points in a tree position that doesn't exist.

### 13.4 Talents tab design

```
 +-- Road to Forever: Talents ---------------------------------------------+
 | Talent link [ talents.html#warrior/--50203123300101~k7f2     ] [Preview]  |
 |                                                       [Copy my build]    |
 |  Arms  0 -> 0        Fury  0 -> 0         Protection  0 -> 21             |
 |  [mini tree]         [mini tree]          [mini tree]                     |
 |                                                                          |
 |  This build uses 21 points. You have 21 free. All 21 will be learned.     |
 |                                         [Cancel]  [Learn talents]         |
 +--------------------------------------------------------------------------+
```

- **Mini trees:** three trees side by side, each a 4 x 7 grid of 26 px talent
  icons in the talent-frame slot border, tree name + `current -> planned` above.
  - already learned: normal icon, rank in the corner (white);
  - will be learned now: gold border glow + `+2` in gold;
  - in the build but no points left yet: dim, dashed-looking gold outline, `later`;
  - not in the build: desaturated;
  - conflict (you have points the build doesn't): red border.
- Hover = the game's own talent tooltip (`GameTooltip:SetTalent(tab, i)`) plus a
  line `Build: 3 / 3`.
- **Summary line** (one of):
  - `This build uses 21 points. You have 21 free. All 21 will be learned.`
  - `This build uses 21 points. You have 16 free: 16 will be learned now, 5 later.`
  - `You already have 2 points in Improved Rend, which this build doesn't use. Reset your talents at a trainer first.` (red, Learn disabled)
  - `No free talent points.` (Learn disabled)
- **Learn talents** (`UIPanelButtonTemplate`, disabled in combat and while
  anything is red) -> confirm popup (`StaticPopup`):
  `Learn 21 talent points? Only a trainer reset can undo this.` [Learn] [Cancel]
- While learning: button reads `Learning 7 / 21`, everything else locked.
- Done: `Learned 21 talent points.` in chat + the trees refresh.
- **Copy my build:** reads your current ranks, builds the link exactly like the
  site (per tree: digits in sorted order, trailing zeros removed; trees joined
  with `-`, trailing `-` removed; then `~hash`), prefixes
  `https://nobody174.github.io/wow-forever-macros/talents.html#`, and shows it in
  a small popup with the text selected: `Press Ctrl+C, then paste it in your
  browser or Discord.`

### 13.5 Learning engine (`Talents.lua`)

- **Plan:** points to add = planned rank - current rank, per talent. Any negative
  = conflict (stop before anything).
- **Order:** tier 1 of all trees, then tier 2, and so on; within a tier, tree
  order then column. This always satisfies the tier requirement (5 points per
  tier in that tree) and prerequisites (they're higher up), and with fewer free
  points it fills from the top. Before each point, double-check the tier
  requirement and `GetTalentPrereqs`.
- **One point at a time:** `LearnTalent(tab, i)`, wait for
  `CHARACTER_POINTS_CHANGED` (or 0.5 s timeout), re-read the rank. If it didn't go
  up: stop and show `Stopped at Improved Thunder Clap: the game didn't accept the
  point. 14 of 21 learned.`
- Stop at once on `PLAYER_REGEN_DISABLED` (combat) with `Stopped: you entered
  combat. 9 of 21 learned. Click Learn talents to continue.`
- Classic learns a talent the moment it's clicked (no preview/commit like Wrath).
  Our Preview + confirm popup is the "accept" step. If the Forever client turns
  out to have Blizzard's preview API, use that instead and let Blizzard's own
  Learn button confirm.
- **Fallback if `LearnTalent` is blocked for addons:** guided mode. Open the
  Blizzard talent window and put a pulsing gold glow (our own texture, parented
  to `UIParent`, anchored over the talent button; never modify Blizzard's
  frames) on the next talent to click, with `Click Improved Bloodrage (2 of 21)`.
  Advance on `CHARACTER_POINTS_CHANGED`.

### 13.6 Decisions made while building it (step 8, v0.6.0, 2026-10-02)

**The hash, exactly (13.3 left the details open).** Both sides build one string
from the class's talent names in link order: talents in a tree joined with `,`,
the three trees joined with `;` (Warrior: `Arms names;Fury names;Protection names`).
Then djb2 (h = 5381; h = h * 33 + byte, wrapped to 32 bits) over the string's
**UTF-8 bytes**, then `h mod 36^4` written in base36 (`0-9a-z`), zero-padded to 4
characters. Why each part:
- **Link order (tier, then column)** because that is the digit order of the link
  itself: if the game's sorted list differs from the site's anywhere (a talent
  missing like Crusade, renamed, moved, or the tabs in another order), digit k
  would land on a different talent, and exactly then the hash differs.
- **Separators** so a talent that moves from the end of one tree to the start of
  the next (same names, same overall order) still changes the hash; a plain
  concatenation would not see that. Talent names contain neither `,` nor `;`.
- **UTF-8 bytes**, because WoW's Lua strings are UTF-8 bytes; JavaScript strings are
  UTF-16, so `talentcalc.js` converts first (`unescape(encodeURIComponent(...))`).
  Hashing UTF-16 units would give a different hash for any non-ASCII name.
- **mod 36^4, zero-padded** (not "the first 4 base36 digits"), so the result is
  always exactly 4 characters and neither side needs slicing rules.
- **Names only, no ranks or icons** (13.3 as written). Max ranks are checked
  separately in step 9 (13.3's "extra sanity checks").
- **Implementations:** `talentcalc.js` `hashText` / `treeHash` (exported as
  `TalentCalc.treeHash(raw, cls)`), `Talents.lua` `Talents.HashText` / `Talents.Hash`.
  `addon/tests/run_tests.py` runs the real `talentcalc.js` in Node
  (`addon/tests/talent_link_check.js`, a tiny fake DOM) and `Talents.lua` under Lua
  5.1 on the same fixture (`addon/tests/talent_fixture.json`) and requires identical
  output, plus a third Python implementation. During step 8 the same comparison also
  ran once on Wowhead's live Forever data (all 9 classes, the hash and one link
  each: 18/18 identical); that data isn't stored in the repo.

**Link shape.** Every link we hand out is `<class>/<code>~<hash>`: always with the
`/` and the hash, even with no points (`warrior/~<hash>`), on both sides. The code is
the site's existing one, unchanged (per tree one digit per talent, trailing zeros
removed; trees joined with `-`, trailing `-` removed). The addon's full link
prefixes `https://nobody174.github.io/wow-forever-macros/talents.html#`.

**Site side (`talentcalc.js`; `?v=20261002a` on talents.html and builds.html).**
- `instance.encode()` stays the **stored** form, without hash (saved builds, Group
  picks in `group-builds.json`): `talentsaved.js` sums a code's digits to show the
  point split, and a hash like `~k7f2` would add its digits to the last tree.
  New `instance.link()` = encode + hash, used by every link the site hands out:
  **Copy link** (both modes), **Open in Talent Calc** (builds.html), the talents.html
  **address bar** (people copy it as a link too), and the saved-builds sidebar's
  Copy link (`TalentCalc.hashFor(cls)`, from the data the page already loaded; no
  hash before it has loaded).
- **Reading ignores everything from `~`** (`TalentCalc.cleanCode`): in `applyCode`
  (so both `opts.code` and `setCode`), talents.html's `fromHash`, and the saved-builds
  import (which stores the bare code). It was needed, not cosmetic: before step 8 the
  reader took the hash's characters as more digits of the last tree, so a check with
  digits could become a valid but **wrong** build (`35~111` read as `350111`).
  Tested on both paths.

**Addon side (`Talents.lua`, v0.6.0).**
- **API used: `GetNumTalentTabs`, `GetNumTalents`, `GetTalentInfo` only**, with
  Classic's return shape `name, iconTexture, tier, column, rank, maxRank` (tier and
  column 1-based, `rank` = learned points). `GetTalentTabInfo` isn't needed (its
  returns differ between client versions). Missing API or no tabs yet: chat line
  `couldn't read your talents yet...`, no popup, no error (TESTING.md 13 checks the
  real shape).
- **Sort:** tier, then column, then the client's index as a tiebreak (only so
  `table.sort`, which isn't stable, can never make two runs differ; a real tree has
  one talent per cell).
- **Class id** = `select(2, UnitClass("player")):lower()`, the same ids as
  `talentcalc.js` `CLASSES`.
- **Locale limit (for step 9).** The hash is over names, and a non-English client
  returns translated names, so its hash never equals the site's (English, from
  Wowhead). For export that's harmless (the site ignores the hash). **Step 9 must not
  block imports on a non-English client** because of it: treat a mismatch there like
  an old link (yellow "can't check" line) when `GetLocale()` isn't `enUS`/`enGB`, or
  find a locale-free key. Recorded here so step 9 doesn't rediscover it. **Step 9
  took the first option (13.7).**
- **Why no combat check (6.4/6.9 don't apply).** Copy my build only reads talent
  info and shows our own non-secure copy box; it never learns a talent, never writes
  a macro, never calls a protected function. Reading `GetTalentInfo` and showing an
  insecure frame are allowed in combat, so the `InCombatLockdown()` / `RunOrQueue`
  pattern (made for macro writes) isn't used and the command works in combat. A
  test checks it runs in combat with zero macro API calls. Step 10's learning
  (`LearnTalent`) is a write and gets combat rules then (13.5).
- **Popup = the existing copy box** (`UI.ShowCopy`, step 3), which now takes an
  optional hint line: `Press Ctrl+C, then paste it in your browser or Discord.`
  (13.4); without one, Copy text keeps `Press Ctrl+C to copy, then Esc.` The text is
  selected on open and typing can't change it. No new globals.
- **Trigger for now: `/r2f copybuild`** (in `/r2f help`, and mentioned on the
  Talents tab placeholder). 13.4's **Copy my build** button belongs on the Talents
  tab, built in steps 9/10: they add it (calling `R2F.Talents.CopyMyBuild()`) and
  may keep or drop the slash command.

### 13.7 Decisions made while building it (step 9, v0.7.0, 2026-10-02)

Step 9 is the preview only: `Talents.lua` gained `ParseLink`, `Preview`, `Plan`,
`Summary`, `LearnOrder`, `TreeName`, `CurrentPlan`; the tab is `UI/TalentPanel.lua`
(the file 6.1 already named). Nothing learns a talent yet.

**Reading the link (13.2)**
- **Everything up to the last `#` is dropped before 13.2's pattern runs.** On a
  full URL the pattern alone matches `io/` in `github.io/` (class `io`, no digits),
  so "accept a full URL" needs this. The pattern is then anchored
  (`^(%a+)/([%d%-]*)(~?%w*)$`) so trailing junk is refused, not ignored, and the
  class must be one of `talentcalc.js`'s 9 ids. Also: surrounding spaces, quotes and
  Discord's `<...>` are trimmed, case is ignored, `warrior/32a` (letters straight
  after the digits, which the pattern's optional `~` would allow) is refused, and a
  bare trailing `~` means "no hash" (as the site reads it).
- **Mapping reuses step 8's `Talents.ReadTrees()`** (the export's tier/column sort),
  so import and export can't drift apart. It now also keeps the icon.
- **Class names in messages are English** (`warrior` -> `Warrior`), not the client's
  localized names: every message around them is English (5.9).

**The hash on import (13.3)**
- Match -> preview. No hash -> preview + 13.3's yellow line. Different on an
  English client (`GetLocale()` `enUS`/`enGB`, or no `GetLocale`) -> 13.3's stop
  message exactly, no preview, no plan; the tab shows your own trees behind it.
- **Different on a non-English client -> treated like a link without a hash**
  (13.6's hand-off, first option): preview + a yellow line `Your game isn't in
  English, so this link can't be checked against your talent trees.` Why not stop:
  the names are translated, so the hash can **never** match there, even with
  identical trees; stopping would lock every non-English player out of imports for
  good. That client is in exactly the position of an old link (13.3 already allows
  those with a warning), the sanity checks below still run, and step 10 re-reads
  every rank after each point (13.5). The English stop message is left word for word:
  on an English client a language difference can't be the cause, so no
  "might be your language" note was added to it.
- The step-8 hash functions are reused unchanged (`Talents.Hash`); the step-8
  cross-check tests pass as before.

**Sanity checks (always, also with a matching hash)**
- A rank above the talent's max rank (the hash covers names only, 13.6), points past
  a tree's last talent, or points in a tree the class doesn't have are **conflicts,
  not errors**: the preview still draws (the trees show where the problem is) and
  Learn is blocked. Zeros in those places are harmless and ignored.
- **Conflict order in the summary:** link problems first (over max rank, no such
  talent, no such tree), then "you have points this build doesn't use": a trainer
  reset can't fix a bad link. Only the first conflict is in the summary; all of them
  are red in the trees.

**Summary line (13.4)**
- The four 13.4 sentences are produced word for word (tested) when none of the
  build is learned yet. Additions where 13.4's text would be wrong or awkward:
  - part of the build already learned (normal after leveling): `This build uses 21
    points, 5 of them already learned. You have 16 free. All 16 will be learned.`
    (and the `now / later` form). Without this, "All 21 will be learned" would be false.
  - you have more points in a talent than the build uses (not zero): `You have 5
    points in Deflection, but this build only uses 3. Reset your talents at a trainer
    first.` (13.4's "which this build doesn't use" only fits zero).
  - `You already have this whole build.`, `This link has no talent points in it.`,
    and singular forms (`1 point`, `It will be learned.`).
  - Over max rank: `The link puts 4 points in Improved Heroic Strike, which has only
    3 ranks in your game. Make a new link on the site or wait for the site to
    update.`; missing talent/tree: `The link has points in a talent your Fury tree
    doesn't have. ...` / `... a talent tree your class doesn't have. ...`
- Precedence: conflict > empty link > whole build already learned > no free points
  > all now > part now.
- **"Now" vs "later" uses 13.5's learning order** (tier across all trees, then tree,
  then column; `Talents.LearnOrder`), handing out the free points in that order, so
  the preview shows exactly what step 10 will learn first. Step 10 learns in the
  same list.

**The tab (13.4)**
- **Mini trees:** 3 x (4 x 7) grids of 26 px icons, built from the talent frame's own
  textures: the `UI-EmptySlot-White` ring behind each icon tinted per state (the
  talent frame tints the same texture), `TalentFrame-RankBorder` for the rank badge,
  the action-button border glow (gold) for "learned now". States: learned = grey
  ring, white rank; now = gold ring + glow + gold `+N`; later = dim icon, dim gold
  ring, `later` (a dashed outline isn't possible with plain textures, so "dim gold
  + the word" stands in for it); not in build = desaturated, grey ring; conflict /
  over max = red ring. Headers: tree name + `current -> planned`.
- **Tree names** come from `GetTalentTabInfo` (13.6 avoided it because its shape
  differs): first string among its first two returns (Classic = name first, newer =
  id then name), `pcall`-guarded, fallback `Tree 1..3`. Only the header text depends
  on it; the mapping never does.
- **Tooltip:** `GameTooltip:SetTalent(tab, index)` with the client's own index (not
  our sorted position), `pcall`-guarded; missing, failing or empty -> the talent name
  as the first line. Then `Build: X / Y` (planned / max) and, when they apply, the
  now / later / conflict lines.
- **Link box:** `InputBoxTemplate` (named `R2FTalentLink`, fallback plain EditBox on a
  tooltip backdrop `R2FTalentLinkPlain`), grey placeholder `talents.html#<your
  class>/...`. Preview on the button or Enter.
- **The link is remembered per character** (`R2FCharDB.lastTalentLink`, 6.3) when it
  parses, and comes back (previewed again, live) on the next open. **Cancel** clears
  the box and the memory and shows your own trees. Preview with an empty box = Cancel.
- **Before a preview** (and behind a stop message) the trees show the character's own
  talents with rank badges, no build.
- **Live:** the preview is re-run on every refresh (tab shown,
  `CHARACTER_POINTS_CHANGED`, `PLAYER_LEVEL_UP`, throttled 0.2 s like Home), so it
  follows points spent in Blizzard's talent window and level-ups. Both events are
  new in Core (6.5's table); step 10 will also use `CHARACTER_POINTS_CHANGED` to
  confirm each learned point.
- **Learn talents exists but is disabled in step 9**, with a tooltip and a grey note
  `Learning talents comes in a later version. For now, learn them in the talent
  window.` `plan.learnable` (no conflicts, points needed, points free) is already
  computed for step 10, which enables the button from it (and greys it in combat).
- **Copy my build** is now a button on the tab (13.4). **`/r2f copybuild` stays** as a
  shortcut: it's one table entry, already in `/r2f help` and TESTING.md, and works
  without opening the window.
- **Home's Talents line** is 12.4's `5 free talent points` / `1 free talent point` /
  `No free talent points` (same strings and `UnitCharacterPoints` guard as the
  minimap tooltip; `Talents.FreePoints` wraps it).

**Why Preview has no combat check (same reasoning as 13.6).** Preview parses a
string, reads `GetTalentInfo` / `GetTalentTabInfo` / `UnitCharacterPoints` /
`GetLocale` and redraws our own non-secure frames. None of that is protected, so the
`InCombatLockdown()` / `RunOrQueue` pattern (for macro writes, 6.4/6.9) doesn't apply:
Preview, Cancel and Copy my build stay enabled in combat. A test runs them in combat.

**Testing.** `run_tests.py` adds `test_talent_preview` (template and fallback paths)
and `test_talent_source_readonly`: every accepted link form and the refusals; every
link the real `talentcalc.js` produces for the 7 fixture builds parses back and
previews as exactly that build (decode == site encode); class mismatch text; hash
match / mismatch (fake hash and a game missing a talent) / absent / non-English /
`enGB` / no `GetLocale`; over max rank, no such talent, no such tree, harmless zeros;
the 13.4 summary sentences word for word plus the additions; per-talent states,
learning order and tree counts; tree-name shapes; the tab (buttons, placeholder,
cells' ring/glow/badge/`later`/desaturation, headers, tooltip with client index and
fallbacks, Learn disabled even when learnable, live refresh on
`CHARACTER_POINTS_CHANGED`, yellow/red lines, Cancel, memory incl. a reload, Copy my
build); combat; the global audit. The fake client's `LearnTalent` (and the preview-
spend calls) raise and count, and the count stays 0; a source scan finds no
talent-learning call in the addon at all. 18 hand mutations of the new code (digit
offset, no `#` strip, hash rules flipped, learning order, each sanity check, class
check, free-points rule, conflict order, hash slice, a stray `LearnTalent`, Learn
enabled, tooltip index, own-trees view, link memory, Home line, the new event) each
fail the suite. What only the client can show (tooltip, tab info shape, look at
26 px) is TESTING.md 14.

### 13.8 Decisions made while building it (step 10, v0.8.0, 2026-10-02)

Step 10 = learning. The engine is the end of `Talents.lua` (13.5's file); the guided
glow is the new `UI/TalentGuide.lua`; `UI/TalentPanel.lua` enables Learn talents and
shows the run. **The only irreversible write in the addon:** nothing here has run
against a real client yet (TESTING.md 15 before anyone learns a real build with it).

**Which way to learn (detected per click, `Talents.LearnMode`)**
- **`preview`** when `AddPreviewTalentPoints` and `LearnPreviewTalents` are functions
  **and** `GetCVarBool("previewTalents")` is true (`pcall`-guarded). 13.5 says prefer
  Blizzard's preview if Forever has it. The CVar test is there because a client can
  carry the shared Wrath-era functions with the feature switched off; filling an
  invisible preview would learn nothing. In this mode Learn talents fills Blizzard's
  preview (`AddPreviewTalentPoints(tab, index, n)` per talent, in 13.5's order), opens
  the talent window and says `added N talent points to the talent window's preview.
  Click its Learn button to keep them.` **No popup of ours** (nothing is learned until
  Blizzard's own button, which 13.5 makes the confirm step) and **we never call
  `LearnPreviewTalents`** (the commit).
- **`direct`** (expected on Classic/Forever): `LearnTalent(tab, index)`, one point at
  a time, behind our confirm popup.
- **`guided`** when `LearnTalent` isn't a function, or this session saw it **blocked**:
  (a) the game fired `ADDON_ACTION_FORBIDDEN` / `ADDON_ACTION_BLOCKED` for our addon
  and `LearnTalent` (the client's own "refused" signal; Core now registers both), or
  (b) the very first point of the session was refused (rank didn't go up after the
  timeout) while every pre-check had passed and no point had ever worked. (b) is a
  guess, so it's undone the moment the point turns up late (`worked` = true). A
  refusal after a point has worked is just a stop, not guided mode: addons clearly
  can learn then.

**The run (state machine, not a loop)**
- Why: each point is a server round trip. A loop sending 21 `LearnTalent`s in one go
  would send tier-2 points before the server confirmed the tier-1 points they depend
  on, and couldn't notice a refused point or combat starting halfway. So the run is a
  table (`points`, `pos`, `done`, `total`, `phase`, `token`) driven by events:
  `queued` (accepted in combat) -> `learning` (a point sent, waiting) or `guided`
  -> `stopped` / `done`.
- **Points = `Talents.LearnPoints(plan)`**: step 9's `LearnOrder` (tier, tree, column),
  expanded to one entry per point with its target rank, only the `now` points. So the
  run learns exactly the gold `+N` cells of the preview, in that order, and never more
  than the popup said, even if a level-up adds points mid-run (those need a new click).
- **Before every point, `verify`** re-runs the whole preview on the live game (hash,
  sanity checks, conflicts), finds the talent by client index **and name**, and checks:
  already at the target -> skip and count (`have`, e.g. the player clicked it in
  Blizzard's window); exactly one rank short; a free point; Classic's tier rule (5
  points in that tree per tier above the first, on live ranks); prerequisites via
  `GetTalentPrereqs(tab, index)` (Classic: `tier, column, isLearnable` per prereq; we
  look the prereq up in the live tree and require it **maxed**, rather than trusting
  `isLearnable`, whose exact meaning can't be confirmed here; no API / error = no
  extra check, the server and the rank re-read still catch it). Why re-verify instead
  of trusting the plan: the plan is from when the popup opened; the player can spend
  points in Blizzard's window, combat can come and go, Forever's rules may differ.
  A failed check stops **before** `LearnTalent`.
- **One point:** `learnPoint` is the **only `LearnTalent` call in the addon** (a source
  test enforces it): `R2F.InCombat()` first (the event flag + `InCombatLockdown()`,
  6.7), then `pcall(LearnTalent, tab, index)`. Then wait: `CHARACTER_POINTS_CHANGED`
  re-reads the rank; up -> next point; not up -> keep waiting (the event also fires
  for level-ups). `C_Timer.After(0.5)` is the final word (13.5's timeout,
  `Talents.LEARN_TIMEOUT`): not up -> stop, **never continue past it**. A token on the
  run makes a stale timer or event for an older point do nothing.
- **Without `C_Timer`** (not expected in any Classic Era client) the next
  `CHARACTER_POINTS_CHANGED` is final instead, and the Stop button is the way out if
  no event comes.
- **Messages (13.5, word for word where given):** `Stopped at X: the game didn't
  accept the point. 14 of 21 learned.` (+ when guided mode is now suspected: `Your
  game may not let addons learn talents. Click Learn talents to be shown which
  talents to click instead.`); `Stopped: you entered combat. 9 of 21 learned. Click
  Learn talents to continue.`; done: `Learned 21 talent points.` (`1 talent point`).
  Added: `Stopped. X of N learned. Click Learn talents to continue.` (Stop button),
  `Stopped at X: its tier or prerequisite isn't met in your game. ...`, `Stopped: no
  free talent points left. ...`, `Stopped: your talents changed while learning. ...
  Check the preview, then click Learn talents again.`, and `The point in X arrived
  late after all. ...`. They go to chat and to the tab's status line (stop red, done
  green); they outrank the yellow caution line, since they're what just happened.

**Combat (Event flow + Taint auditor)**
- **Interrupt, not just a gate:** `PLAYER_REGEN_DISABLED` -> Core sets `R2F.inCombat`
  **then** calls `Talents.OnCombat()`, which stops the run at once with 13.5's
  message. No `LearnTalent` can go out after that: `learnPoint` checks the flag,
  which is already true. Learn talents greys out in combat (6.9's rule for every
  destructive button) with a tooltip saying why.
- **The point already sent can't be called back.** It's kept as `late`; if it lands,
  it's counted and the stop line updates (`... 6 of 17 learned ...`).
- **No double send on resume.** If Learn talents is clicked again while that point
  may still be on its way (Stop, then Learn at once), the run first **waits** for it
  like for any sent point and only re-sends it after the timeout. Sending it at once
  could land both: one rank more than the build, maybe past the talent's planned
  maximum, which only a trainer reset undoes. Found in this step's own review; a test
  with a 1-rank talent in flight covers it.
- **Popup accepted in combat** (opened before combat): the start goes through
  `Macros.RunOrQueue`, the queue every confirmed write uses (6.9), with `you're in
  combat; learning starts when combat ends.`; the button reads `After combat` and Stop
  can drop it. 6.9's pattern was reused rather than refusing, because the player did
  confirm. A run that's already going is **stopped**, not queued (13.5 is explicit).

**Resuming (13.5: "Click Learn talents to continue")**
- Stops by combat, the Stop button or a refused point are resumable: the next Learn
  talents click **continues the same run** (same `X of N`, no second popup: it's the
  build the player already confirmed), if the link is unchanged and the live preview
  is still learnable. Other stops (tier/prerequisite, no free points, trees changed)
  need a new preview and start over with a new popup.
- **Session only:** the run is a file-local, not SavedVariables. After a `/reload` the
  remembered link previews what's left and a new click asks again: resuming from saved
  data, maybe days later, would act on a confirmation given in another situation.
- Previewing another link or Cancel drops a stopped run and its message.

**The tab while learning (13.4)**
- Learn talents reads `Learning X / N` (X = the point being learned now, 1-based) and
  is disabled; the link box, Preview and Copy my build are locked (harmless reads, but
  a new link mid-run would show another build than the one being learned). **Cancel
  becomes Stop** (the one deliberate addition to "everything else locked": a way out of
  a run waiting on the server or on the player's clicks). After the run the trees
  redraw through step 9's `Refresh` (no second renderer). The run doesn't depend on the
  tab: closing the window doesn't stop it.

**Guided mode (`UI/TalentGuide.lua`)**
- Opens Blizzard's talent window with `ToggleTalentFrame()` (what the N key calls; only
  if the window isn't already open, since Toggle would close it; only out of combat).
  Without it: `open your talent window (default key N) and click the talents named
  here, one at a time.`
- **Frame names** differ by client generation, so both are tried: vanilla's
  `TalentFrame` / `TalentFrameTalent<i>` / `TalentFrameTab<n>` and TBC/Wrath-era
  `PlayerTalentFrame` / `PlayerTalentFrameTalent<i>` / `...Tab<n>`; button i = talent
  index i of the tab shown (`PanelTemplates_GetSelectedTab`, else `.selectedTab`).
  Another tab showing -> the glow goes on that tree's tab button with `Open the Fury
  tab, then click Cruelty (6 of 17)`. Nothing found -> text only.
- **Taint:** the glow is **our** unnamed frame on `UIParent` (`DIALOG` strata, no
  mouse, so clicks reach Blizzard's button), only **anchored** to Blizzard's button.
  Nothing of Blizzard's is written: no scripts, hooks, points, parents or keys (a
  source test and a runtime test check this). Because we may not hook Blizzard's
  OnHide or tab clicks, an invisible host frame of ours runs a **0.2 s throttled
  OnUpdate only while guiding** to follow the window opening/closing and tab changes
  (6.6's "throttled refresh" rule, extended to this case).
- Look: the gold action-button border glow (same texture as "learned now", 13.7) at
  1.8x the button, pulsing via an `AnimationGroup` (Alpha 1 -> 0.3, 0.6 s, bounce;
  steady glow if the API is missing), label `Click Cruelty (2 of 21)` above it. The
  same line goes to chat once per point and to the tab's note line.
- Advances on `CHARACTER_POINTS_CHANGED` through the same `verify`, so a click on a
  talent outside the build stops guided mode (`... your talents changed ...`), a click
  on a later build talent is simply counted when its turn comes, and combat stops it
  like a direct run.

**Not done / limits**
- 13.5's timeout is 0.5 s. A slow server answer becomes a "didn't accept" stop that
  turns into `arrived late after all` when the answer lands; harmless (the run is
  stopped, not continued), but a high-ping player may see it. Raise
  `Talents.LEARN_TIMEOUT` if the beta shows it (TESTING.md 15).
- Every follow-up point is sent from an event/timer callback, not a click. If Forever
  only allows `LearnTalent` from a hardware click, the first point works and the
  second is refused (a plain stop, no guided switch, since one worked). TESTING.md 15
  checks exactly this; the fix would be guided mode for the rest.

**Testing.** `run_tests.py` adds `test_talent_learning` (template and fallback paths)
and `test_talent_source_writes` (replacing step 9's read-only scan). The stubs got a
fake server: `LearnTalent` only queues a request, `TEST.server()` answers with
Classic's rules (free point, max rank, tier, prerequisite maxed; fixture prereqs from
Wowhead's `requires`) and fires `CHARACTER_POINTS_CHANGED`; it raises if called in
combat; a fake Blizzard talent window; `GetTalentPrereqs` in Classic's shape. Covered:
the point order equals step 9's `LearnOrder` and an independent Python sort; the popup
text and its Cancel; a full 17-point run point by point (label, locks, Stop, client
index, ranks after, chat + green line, trees refreshed, stale timers harmless); partial
runs and a level-up; Learn enabled only with zero conflicts (11 cases, also calling
`Learn()` directly); refused point (exact message, nothing sent after, resume, error
inside `LearnTalent`); combat mid-run (exact message, point in flight counted, nothing
sent in combat, resume from 7 / 17), combat flag between answer and next send; popup
accepted in combat (queued, starts after, Stop while queued); Stop + late answer;
window closed mid-run; link changed under the popup / after a stop; re-verification
(prerequisite missing, no `GetTalentPrereqs`, tier, a prerequisite changing mid-run,
a point spent elsewhere, a build point spent elsewhere, free points gone); the
timeout, a late answer, no `C_Timer`; the no-double-send rule; guided mode (popup
line, window opened, glow on the client-index button, advance, tab hint, window
closed/reopened, combat + resume, full run, no talent write, no Blizzard frame
scripted, wrong click, Stop, `PlayerTalentFrame` names, no `ToggleTalentFrame`,
detection by refusal and by `ADDON_ACTION_FORBIDDEN`, other addons' events ignored);
preview mode on/off; globals. 24 hand mutations of the new code (each check above
removed or flipped: combat at the write, timeout continuing, prereq/tier/conflict/
have/free-point checks, combat interrupt, Learn enabling, targets, the in-flight wait,
late answers, resumability, guided switch, tab hint, the combat queue, link check,
CVar, event order, forbidden event, locks, glow hiding, label) each fail the suite.

### 13.9 Fix: Blizzard_TalentUI is load-on-demand (2026-10-02)

> **Superseded by 13.10 (v0.10.4).** The premise below was wrong:
> `LoadAddOn("Blizzard_TalentUI")` returns `false, "MISSING"` on WoW Forever, and
> the Classic talent globals never appear. Kept as the record of what was tried.

**The bug.** Preview on a real WoW Forever client, cold (no Talent window opened
yet this session): "couldn't read your talents yet. Try again in a moment." every
time, with no errors visible to the player. `/dump GetNumTalentTabs()` in-game
confirmed the root cause directly: `attempt to call a nil value` — the function
doesn't exist as a global at all until Blizzard's own on-demand UI addon,
`Blizzard_TalentUI`, has loaded. That addon is not loaded at login, same as
`Blizzard_Calendar`/`Blizzard_MacroUI`/etc.: normally it only loads the first
time the player opens the real in-game Talent window by hand. `Talents.ReadTrees()`
only ever *checked* whether the functions already existed; it never tried to make
them exist, so a player who hadn't separately opened their Talent window got stuck
on this message indefinitely.

**How this was actually found, not guessed.** `C_SpecializationInfo` exists on
this client and looked at first like the real talent API (it has a `GetTalentInfo`
too) — a red herring: that's retail's specialization/PvP-talent API, a different
system, and its `GetTalentInfo` takes a query table, not `(tab, index)`. The real
answer came from reading a third-party addon already running successfully on the
user's own WoW Forever client: `RXPGuides/Talents.lua` explicitly waits on
`ADDON_LOADED("Blizzard_TalentUI")` before touching `GetNumTalentTabs`/
`GetTalentInfo`, and `RXPGuides/functions.lua` has a working, already-proven
`LoadAddOn("Blizzard_Calendar")` call for a different on-demand Blizzard addon,
using exactly the `C_AddOns.LoadAddOn or _G.LoadAddOn` fallback pattern this
addon already uses elsewhere (12.4.2). The user's own screenshot of the real
Talent window (three panes — Holy/Protection/Retribution, "Apply Changes" button,
points already spent shown with coloured borders) confirmed the underlying talent
SYSTEM is still the classic tier/column tri-tree the site and this addon already
assume — only the API surface that reads it had moved, not the data model.

**The fix.** `Talents.ReadTrees()` now calls a new `ensureTalentUI()` first: if
`GetNumTalentTabs` et al. aren't already global, it checks
`IsAddOnLoaded("Blizzard_TalentUI")` and, if not, calls
`LoadAddOn("Blizzard_TalentUI")` (both via `C_AddOns` first, bare-global fallback,
`pcall`-wrapped) before the existing existence check runs. This means Preview and
Copy my build now work the very first time, without the player needing to
separately open their real Talent window first. `TalentPanel.Preview()` also adds
one `C_Timer.After(0.5, ...)` retry specifically for the case where the force-load
succeeds but the talent data isn't queryable in the exact same tick on every
client — cheap insurance, not a redesign; `ReadTrees()` itself stays a plain
synchronous function for every other caller.

**Why this wasn't caught by the test suite until now.** `wow_stubs.lua` defined
`GetNumTalentTabs`/`GetNumTalents`/`GetTalentInfo` as globals unconditionally from
the start — an inaccurate model of the real client that every prior talent test
(steps 8, 9, 10) was unknowingly built against. Fixed: these three are now only
installed when the stub's own `C_AddOns.LoadAddOn("Blizzard_TalentUI")` (also
newly added, alongside `IsAddOnLoaded`) is actually called, exactly mirroring the
real client. Every existing talent test continuing to pass unmodified after this
change (because `ReadTrees()`'s new force-load makes it "just work") is itself
part of the proof the fix is correct, not a coincidence.

**Tested:** `ReadTrees()` succeeds on the very first call with `Blizzard_TalentUI`
never previously loaded (the exact bug scenario); a second call doesn't reload it;
no `LoadAddOn` at all on the client → fails cleanly (`nil`), no error, confirmed
by constructing that scenario with `LoadAddOn`/`C_AddOns.LoadAddOn` removed
*before* the addon's files load (it's captured as a local at load time, so
nil-ing the global afterward doesn't actually test anything — `new_runtime()`
gained a `before_load` parameter for exactly this ordering requirement);
`LoadAddOn` present but refused → also fails cleanly, and isn't wrongly marked
as loaded. Confirmed as a real regression test, not just a passing assertion: with
`ensureTalentUI()`'s call site removed, the suite doesn't just fail a check, it
crashes outright downstream (a `nil` from `ReadTrees()` reaching code that assumed
a table), which is an even stronger signal the fix is load-bearing.

### 13.10 Correction: talents are read through C_Traits (v0.10.4, 2026-10-03)

**Corrects 13.9.** In game, `LoadAddOn("Blizzard_TalentUI")` returns `false,
"MISSING"`: the addon doesn't exist on WoW Forever, not even load-on-demand, and
`GetNumTalentTabs` / `GetTalentInfo` never appear. WoW Forever (the 12.x engine,
interface 16001) keeps Classic's three-pane talent trees in retail's **trait system**
(`C_Traits`), with an "Apply Changes" button like retail. v0.10.3's fix could never
have worked; its tests passed because the stub modelled the wrong premise.

**Evidence (all real, none guessed).**
- **The API chain** is the one WeakAuras Forever 1.3.0 uses on this client
  (`Interface/AddOns/WeakAuras/Prototypes.lua`, `Private.GetTalentData`, reader taken
  from ForeverAuras): `C_SpecializationInfo.GetActiveSpecGroup()` ->
  `GetCombatConfigIDForSpecGroup(group)` -> `C_Traits.GetConfigInfo(configID).treeIDs`
  -> `C_Traits.GetTreeNodes(treeID)` -> `C_Traits.GetNodeInfo(configID, nodeID)` ->
  `GetEntryInfo(configID, entryID).definitionID` -> `GetDefinitionInfo(...).spellID`.
- **A live dump** (`talent_dump.lua`, run on a Paladin 2026-10-02; the output is still in
  the user's saved chat log, `WTF/.../SavedVariables/Prat-3.0.lua`):
  `treeIDs = 1100`, `tree 1100 has 50 nodes`, and 8 nodes with `posX`, `posY`, max rank
  and `C_Spell.GetSpellName(spellID)` name.
- **Wowhead's Forever data** (the site's own source, `talentcalc.js`; a copy from step 8
  was on disk) has the **same node ids** as `C_Traits` (Wowhead talent id = trait node
  id, e.g. 105320 = Light's Vigil), the same names, and row/col for each.
- **The user's screenshot** of Blizzard's Talents window (2026-10-02): Holy /
  Protection / Retribution side by side, left to right, each a 4 x 7 grid, all three on
  the same row lines.

**Positions -> tier / column (proven on real data).** The 8 dumped nodes against
Wowhead's row/col for the same ids:

| node | posX | posY | Wowhead row, col |
|---|---|---|---|
| 105320 Light's Vigil | 1620 | 5730 | 6, 1 |
| 105321 Holy Power | 2220 | 5130 | 5, 2 |
| 105323 Holy Shock | 1620 | 4530 | 4, 1 |
| 105324 Divine Precision | 1020 | 4530 | 4, 0 |
| 105325 Divine Favor | 2220 | 3930 | 3, 2 |
| 105327 Purifying Power | 2220 | 3330 | 2, 2 |
| 105329 Illumination | 1620 | 3930 | 3, 1 |
| 105330 Voice of Truth | 1020 | 3330 | 2, 0 |

So `col = (posX - 1020) / 600`, `row = (posY - 2130) / 600` for Holy, exactly. Note
the direction: **posY grows with the row** (screen coordinates, tier 1 on top). The
first hand-off sketch had posY sorted descending; the table above shows that's
backwards, and a test checks the descending order would not match Wowhead.
`ReadTrees` doesn't hard-code 600 / 1020 / 2130: it **ranks** the distinct values
(tier = rank of the node's posY among the whole tree's distinct posY; column = rank
of its posX among its own pane's distinct posX), which gives the same numbers for any
scale or offset. Ranking needs every tier present somewhere in the class and every
pane to use its first column: Wowhead's Forever data has all 7 rows in every class
and column 0 in all 27 trees (only Warlock Destruction lacks column 3, which doesn't
shift anything). And whatever the absolute numbers, the link digits, the hash and the
learning order only use the **relative order** (tier, then column), which ranking
always preserves.

**The three panes (the open question).** Not a C_Traits field: WeakAuras' reader has
none (it only knows `subTreeID`, retail's hero talents), and neither does its talent
picker, which just draws `posX/posY`. Evidence that the panes are three column groups
inside one tree: Paladin's config has **one** tree with **50** nodes, and Wowhead's
three Paladin trees have 17 + 16 + 17 = **50** talents; the screenshot shows three
non-overlapping column groups on shared rows. So `ReadTrees` splits the tree by X: the
two widest gaps between consecutive distinct posX values are the gutters. In the
screenshot a pane step is ~59 px per column and the panes start ~393 px apart, i.e.
about 6.6 column steps: from a pane's last column to the next pane's first is ~3.6
steps, against exactly 1 step between neighbouring columns inside a pane (all 27
Wowhead trees have contiguous columns). Panes are ordered left to right, which is the site's order
(`CLASSES`: Holy 382, Protection 383, Retribution 381 = the screenshot). If the split
isn't clear-cut (fewer than 3 X values, or the 2nd and 3rd widest gaps equal),
`ReadTrees` returns nil ("couldn't read") instead of guessing. More than 7 tiers or
4 columns in a pane also returns nil (not the grid we verified). A config with three
tree ids (never seen) is read as one pane per tree in config order.

**Contract.** `ReadTrees()` returns the same shape as before: three lists (site tree
order), each sorted by tier then column, entries `name, icon, tier, column, rank,
maxRank, index`. New extras: `nodeID, entryID, spellID, configID`. `index` is now the
talent's position in its pane in `GetTreeNodes` order (it was Classic's talent index).
`rank` = `node.activeRank` (WeakAuras' field; `ranksPurchased` as fallback). Encode,
Hash, ParseLink, Plan, Summary and LearnOrder are unchanged; the hash cross-check
against the real `talentcalc.js` passes unchanged through the new reader.

**What changed downstream, and why.** Three places used `(tab, index)` as Classic's
address, which it no longer is:
- **Learning** (`LearnTalent(tab, index)`, `AddPreviewTalentPoints(tab, index, n)`): a
  wrong address learns the wrong talent, which only a paid reset undoes. `direct` and
  `preview` modes now need Classic's `GetTalentInfo` to exist, and every point checks
  `GetTalentInfo(tab, index)` names this very talent before the write (else the run
  stops, nothing sent). WoW Forever has no `GetTalentInfo`, so there learning is
  always **guided** (the addon writes nothing; it names the talent to click). Real
  auto-learning on Forever would be `C_Traits.PurchaseRank(configID, nodeID)` (+ the
  player's Apply Changes, or `CommitConfig`): not built, a separate step. (**Built in
  13.12**, v0.11.0: the "traits" mode.)
- **Guided glow:** only on a Blizzard button `GetTalentInfo` confirms; on Forever the
  text alone (no glow on a possibly wrong button).
- **Tooltip:** `GameTooltip:SetSpellByID(spellID)` instead of `SetTalent(tab, index)`.
- **Events:** `TRAIT_CONFIG_UPDATED` (what WeakAuras Forever listens to) runs the
  same handler as `CHARACTER_POINTS_CHANGED`.
- `ensureTalentUI()` and the Blizzard_TalentUI force-load are gone. Its one valid idea
  ("not ready yet" right after login) is kept: every call in the chain is
  `pcall`-guarded, a missing piece returns nil, and the Preview's 0.5 s retry stays.
- Tree names still come from `GetTalentTabInfo` if it exists, else `Tree 1..3`.

**Testing.** `wow_stubs.lua` now models `C_SpecializationInfo` / `C_Traits` /
`C_Spell` over the same talent table (one tree 1100, real Holy grid numbers, panes
3930 apart, `GetTreeNodes` interleaving the panes so grouping by order fails), and
`LoadAddOn` answers `MISSING`; `GetNumTalentTabs` / `GetNumTalents` are gone. Classic's
`GetTalentInfo` stays in the default fake client only as the hypothetical Classic client
the direct engine is tested on; `new_runtime(before_load=...)` removes it (and
`LearnTalent`, etc.) for the realistic Forever client. New `test_talent_traits`: the 8
real nodes' ranks against Wowhead's row/col (direction and order, real data only), the
8 real nodes inside a full tree (absolute tier/column; the other 42 nodes synthesized
on the same grid), scale/offset invariance, every refusal, the per-pane layout, live
ranks, the event, and the Forever client (link == `talentcalc.js`, preview learnable,
guided, zero writes, a guided run finishing on `TRAIT_CONFIG_UPDATED`, still guided
with a stray `LearnTalent`), plus a Classic client whose address names another talent
(stopped before `LearnTalent`). The 13.9 tests that checked the force-load were
replaced. Suite: 9259 checks, 0 failed (8770 before; every step 8/9/10 check kept,
two changed on purpose: the tooltip is `SetSpellByID`, and Cruelty's cell moved one
column left because the fixture's truncated Fury tree has no column-0 talent). Hand
mutations (posY sorted descending, no address check, no tie refusal, rank always 0,
LearnMode without the GetTalentInfo gate, panes by node order) each fail the suite.
Outside the repo (Wowhead data isn't stored): all 9 classes from Wowhead's Forever
data laid out on the verified grid, nodes shuffled, read back with exact row/col and
link + hash identical to `talentcalc.js`: 9/9.

**Proven vs not yet.**
- Proven on real data: the API chain works on this client (WeakAuras + the dump);
  Paladin = one tree, 50 nodes = all three panes; Holy's posX/posY are Wowhead's
  col/row on a 600 grid, posY growing downwards; node ids and names = Wowhead's.
- Not yet seen in game (TESTING.md 19): the posX of the Protection and Retribution
  nodes (the gutter is read off the screenshot, not dumped; **now dumped, see 13.11:
  it found jitter that broke Protection**); any class but Paladin
  (one tree per class? same layout?); `activeRank` vs pending, un-applied points;
  `SetSpellByID` tooltips; which event fires when the player applies talents (guided
  mode advances on either); whether `GetTalentTabInfo` exists (else `Tree 1..3`).
  The `~hash` remains the backstop on import: if any of this is wrong for a class,
  Preview stops with the "different talent trees" message (English client) instead of
  mapping digits wrongly. On **export** the site ignores the hash, so a wrong mapping
  would open the wrong build there: TESTING.md 13's hash comparison per class is the
  check for that.

### 13.11 Fix: position jitter in Blizzard's layout data (v0.10.5, 2026-10-03)

**Extends 13.10.** Its first open item ("the posX of the Protection and Retribution
nodes ... never dumped") is now answered with real data, and the answer broke the
reader.

**The bug.** A throwaway diagnostic addon dumped `C_Traits.GetNodeInfo` for all 50
nodes of a Paladin's tree 1100 (2026-10-03). Preview on that character still said
"couldn't read your talents yet." The whole tree has 13 distinct posX values:

```
1020 1620 2220 2820 | 5020 5030 5620 6220 6820 | 9080 9680 10280 10880
gaps: 600 600 600 | 2200 | 10 590 600 600 | 2260 | 600 600 600
```

The two widest gaps (2260, 2200) are the gutters, so `splitPanes` finds the right
three panes. But Protection holds **five** distinct values: 5020 and 5030 are 10 units
apart, where every real column step in the data is 590-600. They are one column with a
few units of jitter in Blizzard's own layout data (not an addon error). `ranks()`
treated every distinct raw value as its own column, so Protection had 5 columns,
the "more than 4 columns" check (13.10's refuse-don't-guess rule) returned nil, and
the player saw the same message as before. Holy (and Retribution) read fine.

**The fix: snap near-equal values onto one grid line before ranking.**
`snapGrid(nodes, key)` in `Talents.lua`:
1. Sort the distinct values; take the gaps between neighbours.
2. Estimate the grid step as the **upper median** of those gaps.
3. Walk the sorted values; a value less than `SNAP_FRACTION` (0.2) x step above the
   current cluster's **first** value joins that cluster, otherwise it starts a new one.
   Each value maps to its cluster's first value.

`ReadTrees` snaps X over the whole tree **before** `splitPanes` (one tree per pane:
per pane), and Y over all panes, then ranks the snapped values exactly as before.

Why each choice:
- **Relative, not a fixed number of units.** 13.10 chose ranks because nothing promises
  the same scale for every class/tree. A fixed 100-unit threshold would merge real
  columns on a grid with a step of 60 and miss 300 units of jitter on a step of 6000;
  both are tests.
- **Median.** Real steps are most of the gaps; jitter (too small) and gutters (too
  large) are outliers on opposite sides, which a median ignores while they are under
  half. The **upper** median still finds the step when exactly half the gaps are
  jitter (tested: 11 of 22, reads right; the lower median fails that test).
- **0.2.** Real jitter is 10 / 600 = 1.7% of a step; 0.2 x 600 = 120. A real column
  only a third (200) or a quarter (150) of a step from its neighbour stays separate
  (tested). The two failure directions aren't equal: **not** snapping jitter only
  shifts column/tier numbers (jitter is far below a step, so the sort order is
  unchanged) or trips the count checks (nil). Snapping two **real** lines together
  puts two talents in one cell and leaves their order to the index tiebreak, which
  could map link digits wrongly. So the fraction is kept small.
- **From the cluster's first value, not the previous one.** A run of small gaps can't
  chain separate grid lines into one cluster (tested).
- **When jitter is the majority** of gaps, the median is a jitter gap, nothing snaps,
  and the column/tier checks refuse (nil) instead of guessing (tested).
- **Gutters after snapping.** `splitPanes` reads the snapped X. On the real values the
  two widest snapped gaps are still 2260 and 2200 after the 4th and 8th line, the next
  is 600 (tested). Jitter gaps are the smallest gaps, so they could never be taken for
  gutters: splitting on raw or snapped X gives the same panes (a hand mutation that
  splits on raw X passes the suite, as expected). Snapping first just means panes are
  cut on the same values their columns are counted on.
- **No jitter = no-op.** Every value snaps to itself on the 8 real Holy nodes and on
  13.10's test tree (tested), so every 13.10 check passes unchanged.

**Testing.** New `test_talent_grid_jitter` (both UI modes), with a 50-node Paladin fixture:
the **real 13 posX values**, Wowhead's Paladin cell layout (node id, row, col, max
rank; placeholder names except the 8 real Holy ones, since Wowhead's data isn't stored
in the repo), posY on the 13.10 grid. The report doesn't say which Protection
column-0 node(s) sat at 5030, so all 6 placements (each one alone, each pair) are read.
- Real data: gaps re-derived; only 5030 snaps (onto 5020); the raw ranking counts 5
  Protection columns (the bug) and with the tolerance off `ReadTrees` is nil (the live
  failure, reproduced); with it, all 6 placements read **17/16/17 talents, 4/4/4
  columns** (raw: 4/5/4), every node at Wowhead's pane/row/col.
- End to end: the link for an empty build and for one with 3 points in the jittered
  node equals the real `talentcalc.js` on the same layout (Wowhead format, temp file),
  also through `MyBuildLink`; the jittered node's points are Protection's 3rd digit.
- Synthetic, to prove it generalises: Y jitter (+7 / -9: 9 raw tiers -> 7); five
  jitter pairs in X and Y, both directions, all three panes; steps of 60, 6000 and 222
  with offsets; 300 units of jitter on a step of 6000.
- Too aggressive: a real column a third of a step from its neighbour (Retribution
  columns at 9080 / 9680 / 9880 / 10480) reads as 4 columns in place; `SNAP_FRACTION`
  0.4 on the same tree fails.
- Fail-safe and chaining, as above.

Suite: 9389 checks, 0 failed (9259 before; every earlier check kept, none changed
except the TOC version). Hand mutations, each failing the suite: fraction 0 (= v0.10.4
behaviour), fraction 0.5, a fixed 100-unit threshold, the lower median, chaining from
the previous value, no Y snap. luacheck: 0 warnings.

**Proven vs not yet.**
- Proven on real data: Paladin's whole tree, all three panes' posX; the gutters; X
  jitter of 10 units in one column; the fix reads it as 4/4/4.
- Not verified: which node(s) carry the 5030 (all placements are tested, so it doesn't
  change the result); Protection's and Retribution's **posY** (not in the report; on
  the Holy grid in the fixture); **Y jitter** has never been seen (Y snapping is a
  defensive generalisation); any class but Paladin. v0.10.5 itself still needs an
  in-game Preview / Copy my build on the Paladin (TESTING.md 19).

### 13.12 Free talent points from C_Traits, and one-click learning through C_Traits (v0.11.0, 2026-10-03)

> **Read the "NOT VERIFIED" list at the end before trusting any of this.** Nothing in
> the new write path has run against a real WoW Forever server. It was built from the
> real `/dump C_Traits` function list plus retail WoW's public C_Traits API, and tested
> against a fake client that copies retail's behaviour. TESTING.md 20 is the in-game
> plan, starting with **one point on a disposable character**.

Two fixes, released together because the second is useless without the first.

#### Fix 1: free talent points read 0 on WoW Forever

**The bug (real screenshot, 2026-10-03).** After a talent reset Blizzard's window said
"Unspent Talents: 17"; the Talents tab said `No free talent points.` and Learn stayed
grey. `Talents.FreePoints()` went through `Minimap.FreeTalentPoints()`, which only knew
Classic's `UnitCharacterPoints("player")`. On Forever's trait-based talents that call
is missing or meaningless, and "missing" was silently turned into 0.

**The source (`Talents.FreePointsInfo()`, the one place; Minimap, Home, the tab and the
engine all read it).**
1. `C_Traits.GetTreeCurrencyInfo(configID, treeID, excludeStagedChanges = true)` for
   each tree of the live config (the same config the reader uses, `liveConfigID()`).
   In retail's trait system, unspent points ARE a trait currency of the tree; this call
   returns `{ {traitCurrencyID, quantity, maxQuantity, spent}, ... }` and `quantity` is
   what's left. Per currency id, so a pool shared by several trees (13.10's one-tree-
   per-pane layout) is counted once. One currency, or several with the same amount, is
   the answer; several that disagree is "unknown" (retail class trees have two: class
   and spec points; which one a Classic pane would use is unknown, so no guess).
   `excludeStagedChanges = true` because everything else reads `activeRank`, the
   APPLIED rank (13.10): free points must be the applied ones too.
2. Otherwise Classic's `UnitCharacterPoints("player")`, same meaning as before. One
   change: on a client that HAS a trait config, a legacy answer of 0 is exactly the
   bug above, so it becomes "unknown" (a positive answer is still believed). On a
   client without a trait config (Classic Era) it is used exactly as before, 0
   included.
3. Neither: **unknown** (`nil`). Not 0.

*Note on `GetTraitCurrencyInfo`* (in the live dump): in retail it takes a
`traitCurrencyID` and describes the currency (flags, type, icon), not the amount, so
it isn't used.

**Unknown is shown as unknown.** `Plan(trees, codes, free)` takes `nil` = unknown:
`plan.free = 0` (nothing learnable), `plan.freeKnown = false`, and the summary says
`Couldn't read your free talent points, so nothing can be learned from here. Learn them
in Blizzard's talent window.` instead of `No free talent points.`; Home says `Free
talent points: couldn't read them`. The minimap tooltip just leaves its line out
(unknown counts as 0 there). Learn is never enabled on an unknown count: the engine's
per-point check needs at least one free point.

**Confidence: medium.** The retail signature and meaning are well known; that Forever's
client has `GetTreeCurrencyInfo` (the dump excerpt we have didn't list it) with the same
shape and a single currency is not confirmed. Every step is `pcall`-guarded and anything
odd is "unknown", never a wrong number.

#### Fix 2: the "traits" learning mode

**Mode selection (`Talents.LearnMode`).** `preview` and `direct` are unchanged and still
come first (they need Classic's `GetTalentInfo`). Then **`traits`** when `C_Traits` and
`C_SpecializationInfo` are tables and `PurchaseRank`, `GetNodeInfo`, `GetConfigInfo`,
`GetTreeNodes` are functions, and this session hasn't switched it off. Else `guided`,
exactly as before. On WoW Forever: `traits`.

**What stays exactly as step 10 (13.8).** The plan, `LearnOrder` and the popup's point
list (tier by tier; `LearnPoints` only gained a `nodeID` field; a source test compares
`LearnOrder`, `verify`, `Encode`, `Hash` byte for byte with v0.10.5); the confirm popup;
`verify()` before every point (whole preview re-run on live ranks, conflicts, exactly one
rank short, a free point, Classic's tier rule); the per-point combat check at the write;
the state machine, tokens, `Learning X / N`, locks, Stop, resumable stops, late
answers; the queue for a popup accepted in combat. Only the "spend this one point"
primitive differs: `learnPoint` (Classic) or `purchasePoint` (traits), chosen by
`r.mode` in the shared `stepSend` (was `stepDirect`).

**The write: signature and flow (`purchasePoint`, the ONLY C_Traits writes in the addon,
a source test enforces it).**
- `C_Traits.PurchaseRank(configID, nodeID)` -> success boolean (retail). The address is
  the trait node itself, which the reader already has for every talent (13.10), so
  there is no Classic `(tab, index)` to translate. **Confidence in the signature:
  medium** (well known in retail, same `(configID, nodeID)` pair as every C_Traits read
  here; not seen called on Forever).
- **Before the call** (any failure = nothing sent): not in combat; the live config is
  the one the run started on (a spec switch changes it); the node, read through the
  reader's own `readNode`, is this very talent (name) and exactly one APPLIED rank
  short; **nothing is staged anywhere in the config** (see below); the node's
  `canPurchaseRank` isn't `false` (else a tier/prerequisite stop) and
  `C_Traits.CanEditConfig(configID)` isn't `false` (else a refusal), both only when the
  client has them; the free points (applied) are recorded for the read-back.
- **The call**, `pcall`-wrapped. An error or `false` = refused. `true` or nothing proves
  nothing: the read-back decides.
- **Staged or applied at once? (the commit-step question).** In retail, `PurchaseRank`
  only STAGES a change in the client's copy of the config (Blizzard's window shows it
  pending and lights "Apply Changes"), and `C_Traits.CommitConfig(configID)` sends what's
  staged to the server, which answers `TRAIT_CONFIG_UPDATED` (or `CONFIG_COMMIT_FAILED`).
  The "Apply Changes" button in the user's screenshot of Forever's own window says the
  same. **Resolved by reading the node right after the call instead of assuming:** a
  server can't answer inside the call, so any rank change visible right then is the
  client's local (staged) copy. So:
  - a rank moved (`activeRank` or `currentRank`/`ranksPurchased` >= target) -> staged:
    `pcall(C_Traits.CommitConfig, configID)`, but only if exactly this one rank moved
    and nothing else is staged; a `false`/error commit = stop. **Without
    `CommitConfig`** the point is left staged and the run waits; the read-back never
    counts a staged point, so it ends as `...waiting in Blizzard's talent window but
    wasn't applied. Click Apply Changes there...` (the player's own button commits it,
    and the late check counts it).
  - nothing moved -> the server may apply it later; wait.
  **Confidence that Forever stages like retail: low-to-medium** (the screenshot's
  button is the only Forever-specific evidence). Both answers are handled; the read-back
  is what makes either one safe.
- **One commit per point, not one at the end.** Each point is then one server round
  trip, like Classic's `LearnTalent`, so every step-10 guard applies unchanged and at
  most one point is ever un-applied. Staging all points and committing once would be
  faster and atomic, but `verify()` (and the whole preview) reads APPLIED ranks, and
  tier-2 points depend on staged tier-1 points that the read side can't see.

**Why a staged-anything check before every purchase and before every commit.** A commit
applies EVERYTHING staged. If the player had half-made changes in Blizzard's window, our
commit would apply talents they never confirmed in our popup. So `pendingElsewhere`
looks at every node of the config (`currentRank`, else `ranksPurchased`, vs
`activeRank`) AND at the currency (free points with vs without staged changes): before
the purchase nothing may be staged (stop `Stopped: Blizzard's talent window has changes
that aren't applied yet. Apply or undo them there first...`, resumable, no write, no
guided switch); before the commit only our one point may be. An unreadable config
counts as "staged" (stop). This check also makes a double send impossible: a point
already staged on our node can't get a second rank stacked on it.

**Completion detection: what proves a point landed (`landed`).** Two independent reads
must agree: the node's **applied** rank (`activeRank`, via `readNode`) reached the
target, **and** the free points (applied, `excludeStagedChanges = true`) are lower than
right before the send. Why both: if `activeRank` on Forever turned out to count staged
ranks (field semantics not verified), the rank alone would say "learned" right after an
un-applied purchase; the free points would still say no. A test runs exactly that
client. Cost: a level-up landing in the same moment can make a real point look
unconfirmed -> a stop (safe direction).

**Events: why `TRAIT_CONFIG_UPDATED`, and why it isn't trusted alone.** In retail it is
the server's "this config changed / your commit went through" event, and the read side
already listens to it (13.10, as WeakAuras Forever does). Staging fires other events
(`TRAIT_NODE_CHANGED`, `TRAIT_TREE_CURRENCY_INFO_UPDATED`), not this one. But Forever's
event behaviour is unverified, so no event counts a point by itself: `TRAIT_CONFIG_UPDATED`,
`CHARACTER_POINTS_CHANGED` and (new in Core) `TRAIT_TREE_CURRENCY_INFO_UPDATED` all just
make the engine re-read the game (`landed`); the timeout re-reads one last time and is
the final word. A test fires the event with nothing applied and the run keeps waiting.
New: `CONFIG_COMMIT_FAILED` (retail; arg configID, other configs ignored) settles the
point as final at once instead of waiting for the timeout.

**Timeout: `Talents.TRAITS_TIMEOUT = 2` s** (Classic's stays 0.5). A traits point is a
purchase and a commit, and the commit is the round trip Blizzard's own window shows an
"applying" wait for. Too short only means a stop + guided mode + `arrived late after
all`; raise it if the beta shows that.

**The fallback to guided mode (the safety design).** Any refusal in this mode (`false`,
an error, a failed commit, `CONFIG_COMMIT_FAILED`, `ADDON_ACTION_FORBIDDEN` naming
`PurchaseRank`/`CommitConfig`, `CanEditConfig` false, or a point not confirmed by the
timeout, including a `true` that changed nothing) stops the run AND sets
`session.traitsBlocked`. From then on `LearnMode()` is `guided` for the rest of the
session: Learn talents continues the SAME run (same `X of N`, no popup) by naming the
talents to click, and no further C_Traits write is fired. Unlike Classic's
`session.blocked`, a late success does NOT clear it (we don't go back to firing
purchases after something looked wrong); a `/reload` tries traits again. Separate flags
from Classic's, so one write path's trouble never switches the other. If the stopped
point is sitting staged, the stop says so (`...waiting in Blizzard's talent window...
Click Apply Changes there to keep it, or undo it there.`) and the late check counts it
when the player applies it.

**No double send in traits mode.** Classic re-sends a point that's still missing after
the post-Stop wait (13.8). Traits never does: a commit still on its way may be invisible
locally, and a second purchase could then land both. Not there after the wait = a
refusal (stop, guided). Plus the staged-anything check above.

**Combat / taint (Taint & Secure Execution Auditor).** Same rules as `LearnTalent`:
`R2F.InCombat()` at the write (first thing in `purchasePoint`), `PLAYER_REGEN_DISABLED`
stops the run at once (a point in flight is counted if it lands), a popup accepted in
combat waits in `RunOrQueue`, Learn greys out in combat. `PurchaseRank` and
`CommitConfig` are called from our own code only (event/timer callbacks after the first
click), never from a Blizzard frame or hook; nothing of Blizzard's is touched. Only
those two writes: the refund / reset / rollback / bulk C_Traits writes in the dump
(`RefundRank`, `RollbackConfig`, `ResetTree`, `PurchaseAllRanks`, `TryPurchaseAllRanks`,
`TryPurchaseToNode`, `CascadeRepurchaseRanks`, `StageConfig`) are never called (source
test). Whether Forever allows `PurchaseRank` from addons at all (or only from a click,
like a protected function) is unknown: the first-point and second-point tests in
TESTING.md 20 are exactly that check, and a forbidden call falls back to guided.

**Also changed.** `prereqsMet` only asks Classic's `GetTalentPrereqs` at an address
`GetTalentInfo` confirms (no change on Classic; on a trait client `(tab, index)` is our
address and could describe another talent). `liveRank` / the late check take the run's
mode. Core registers `TRAIT_TREE_CURRENCY_INFO_UPDATED` and `CONFIG_COMMIT_FAILED`.

**Testing.** `wow_stubs.lua`: staged ranks on every node (`activeRank` = applied,
`currentRank` / `ranksPurchased` = applied + staged), `GetTreeCurrencyInfo` (default on,
same pool as `UnitCharacterPoints`, staged subtracted unless excluded), and opt-in write
stubs `T.installTraitWrites(model)`: `staged` (retail-like: stage, commit, server applies
+ `TRAIT_CONFIG_UPDATED`), `stagedNoCommit`, `immediate` (applied at once, event later,
no commit), `async` (server applies later); failure switches for a refused purchase, an
error, a lie (`true`, nothing changes), `ADDON_ACTION_FORBIDDEN` inside the call, commit
refused / raising / `CONFIG_COMMIT_FAILED` / silently dropped, `activeRank` counting staged
ranks, `canPurchaseRank`, the player's own staged changes and Apply Changes. The default
fake client stays as it was (no writes), so every earlier test runs unchanged.
New `test_talent_traits_learning` (both UI modes), `test_free_points` (both),
`test_talent_source_traits`. Suite: **10927 checks, 0 failed (9389 before; every earlier
check kept and passing; two edited on purpose: the TOC version check now expects 0.11.0,
and one label now reads "Forever client without C_Traits writes")**. luacheck: 0 warnings.

Hand mutations (23), each run against the full suite: 22 fail it -- landed() without the
free-points check; no staged check before the purchase / before the commit; no
currency-based staged detection (caught only after adding a test where node fields
can't show staging); traits point re-sent after the wait; no guided fallback after a
refusal; no combat check before PurchaseRank; never committing; commit result ignored;
PurchaseRank `false` ignored; node name not checked; traits ordered before direct;
`canPurchaseRank` / `CanEditConfig` ignored; `CONFIG_COMMIT_FAILED` not handled; a
forbidden PurchaseRank ignored; free points without the C_Traits source / counting
staged changes / trusting a legacy 0 on a trait client; unknown shown as "no points"
(tab, Home); a late traits success clearing the session block. The 23rd (per-tree
instead of per-currency-id keys in `traitFreePoints`) survives because it is
equivalent: several currencies must agree anyway, so a shared pool reported by three
trees gives the same answer either way. The per-id key is kept as belt and braces.

#### NOT VERIFIED -- needs real in-game testing (TESTING.md 20) before anyone trusts it with a real build

1. **That `C_Traits.PurchaseRank(configID, nodeID)` works for an addon on Forever at all**,
   with that signature, from event/timer callbacks (not only a hardware click).
2. **Whether a purchase is staged (needs `CommitConfig`) or applied at once**, and
   whether `C_Traits.CommitConfig` even exists on Forever (the dump excerpt we have
   doesn't list it). Both paths are built; neither has run for real.
3. **The node fields' meaning on Forever**: `activeRank` = applied and `currentRank` /
   `ranksPurchased` = applied + staged is retail's; the two-way read-back is built so a
   different meaning fails safe, but it's unseen.
4. **Which events fire** on a staged purchase, an applied commit and a failed commit
   (`TRAIT_CONFIG_UPDATED`, `TRAIT_TREE_CURRENCY_INFO_UPDATED`, `CHARACTER_POINTS_CHANGED`,
   `CONFIG_COMMIT_FAILED`). The engine re-reads on any of them and the 2 s timeout is the
   final word, so a missing event only costs time (or a safe stop).
5. **`GetTreeCurrencyInfo` on Forever**: exists? one currency? `quantity` = Blizzard's
   "Unspent Talents"? Does `excludeStagedChanges` work? (Fix 1 depends on it; if it's
   missing, Forever shows "couldn't read" instead of a wrong 0.)
6. **Server round-trip time** vs the 2 s `TRAITS_TIMEOUT`.
7. **`CanEditConfig` / `canPurchaseRank`** semantics on Forever (only used when present;
   a `false` stops before any write).
8. **Prerequisites** in traits mode are only checked by the server (and
   `canPurchaseRank` if present); Classic's `GetTalentPrereqs` doesn't apply there. A
   refused point stops the run (safe).
9. **Any class but Paladin** (13.10/13.11's reading caveats still apply).

**Start with ONE point on a disposable character** (TESTING.md 20 B), never with a main
character's real build.

## 14. Profession export (v0.12.0, 2026-10-07)

Goal (owner's request): read the recipes a character knows and show them on the site's
Professions page under the character's name, per profession, with material costs, so
the group can see who makes what.

### 14.1 In game (`Professions.lua`)
- The game only lists recipes while a profession window is open, so we read on
  `TRADE_SKILL_SHOW` / `CRAFT_SHOW` and re-read (0.4 s debounce) on the UPDATE events.
- Both APIs: trade (`GetTradeSkillLine`, `GetNumTradeSkills`, `GetTradeSkillInfo`,
  `GetTradeSkillItemLink`, `GetTradeSkillReagentInfo`/`ItemLink`) and Classic's craft
  window used by Enchanting (`GetCraftDisplaySkillLine`, `GetNumCrafts`, `GetCraftInfo`,
  `GetCraftItemLink`, `GetCraftReagentInfo`/`ItemLink`). Each call is checked at runtime.
- On show: `ExpandTradeSkillSubClass(0)` / `ExpandCraftSkillLine(0)` and clear the
  "Have materials" / name filters, so collapsed headers can't hide recipes.
- Saved per character in `R2FCharDB.professions[<profession>] = {rank, max, api, ts,
  recipes = {{name, kind = "i"|"s", id, mats = {{id, count, name}}}}}`.
- Read-only: no protected calls, works in combat. Export button = our own plain button
  parented to `TradeSkillFrame` / `CraftFrame`, anchored left of their close button.

### 14.2 Export string
`R2FP1:` + base64 of tab-separated lines (`\n` between lines):
```
C  <name>  <realm>  <CLASS>  <faction>  <unix time>
P  <profession>  <rank>  <max>  <trade|craft>
R  <recipe name>  <i|s><id>  <matId>:<count>,<matId>:<count>
```
`i` = crafted item id, `s` = enchant/spell id; a material without a cached item link
is `n:<name>:<count>`. Base64 because an EditBox treats `|` as an escape code and chat
can mangle tabs.

### 14.3 Site
`professions.html` Crafters view reads `crafters.json`; the owner imports strings
(same owner login as prices / Group picks). See the root CLAUDE.md.

### 14.4 Not verified (TESTING.md 21)
Whether Forever's Enchanting still uses the craft window; `GetCraftDisplaySkillLine`'s
returns; whether `ExpandCraftSkillLine` exists; Export button placement on both frames.

