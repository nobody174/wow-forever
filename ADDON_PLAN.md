# Addon plan: Road to Forever (macros + talents)

Status: **in progress** (scoped 2026-10-01). Steps 1 (data), 2 (site export),
3 (addon MVP, v0.1.0), 4 (updates, v0.2.0), 5 (Tidy up, Settings, Remove all,
key bindings, v0.3.0), 6 (main window, minimap button, logo, v0.4.0) and 7
(release zip on GitHub Releases, v0.5.0) shipped, no addon version tested in the
game yet; see `CHANGELOG.md`.
Target: usable before the Nov 4 launch.

| | |
|---|---|
| Addon name | Road to Forever |
| Folder | `addon/RoadToForever/` (in this repo) |
| Slash commands | `/r2f` (main window), `/r2ft` (Talents), `/r2f macros`, `/r2f minimap` (show the minimap button again), `/r2f help`, `/r2f import` |
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

WoW has 120 account-wide + 18 per-character macro slots. That limit is in the
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
4. **Slot counter** always visible: `Character 7 / 18`, `Account 31 / 120`.
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
 |  Character 7 / 18    Account 31 / 120          Page 1 of 3  [<][>] |
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
- Right-click: small menu: `Remove from library`, `Copy text`.

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

- Slot counter, two values: `Character 7 / 18` and `Account 31 / 120`. Turns
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
  Talents.lua       parse link, map to the game's trees, plan, learn, export
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
## Interface: <Forever client number, check in beta with /dump select(4, GetBuildInfo())>
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
- `## Interface: 11507` (Classic Era 1.15.7) is a placeholder until the beta check (11).

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
- **Action slots read = 1-120** (6.4). The "18" in "120 + 18" is the per-character
  *macro* slots, not action slots; a Classic client has 120 action slots (bars and
  the stance/stealth bonus bars included). Tests cover slots 1, 73 and 120.
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
  push is the workflow's first real run (TESTING.md 12).

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
   the `~hash` check (section 13.3).
9. **Talent import preview**: paste link, mini trees, summary, warnings. Nothing learned.
10. **Talent learning**: Learn talents + confirm popup, point-by-point learning
    (or the guided fallback if `LearnTalent` is blocked).

## 10. Later / ideas

- Own action bar mode (secure buttons with macro text) for players who want
  more than 138 macros on bars. Big job; only if really needed.
- Talent leveling order on the site (which talent first), so a partial build
  learns your priorities instead of top-down.
- Export from the game back to the site (share your edited macros).

## 11. Things to confirm in the beta

- [ ] TOC `## Interface:` number (`/dump select(4, GetBuildInfo())`).
- [ ] Slot limits really are 120 account + 18 character.
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
- [ ] `LearnTalent(tab, index)` works from our button click (else guided mode).
- [ ] Classic has no talent preview/commit (or, if Forever adds one, use it).
- [ ] Sorting `GetTalentInfo` by tier then column gives the same order as our
      share links (test with the level-30 builds).
- [ ] `GetTalentTabInfo` tab order matches `talentcalc.js` `CLASSES` order.

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
| `/r2f help` | prints the list above |

### 12.4 Main window

One window (`PortraitFrameTemplate`, portrait = `logo128`), three bottom tabs
in Blizzard's character-frame tab style (`PanelTabButtonTemplate`, or the
Classic `CharacterFrameTabButtonTemplate`):

| Tab | Content |
|---|---|
| **Home** | two large entries in spellbook-slot style: **Macro Book** (`38 macros in your library, 12 on your bars`) and **Talents** (`5 free talent points`, or `No free talent points`). Clicking one switches tab. Below: Import macros button. |
| **Macros** | the Macro Book (section 5) |
| **Talents** | section 13.4 |

Window position, size and last tab are saved. Esc closes it. Same sounds as the
Spellbook.

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
