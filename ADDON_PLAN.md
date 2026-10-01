# Addon plan: Road to Forever (macros + talents)

Status: **in progress** (scoped 2026-10-01). Steps 1 (data), 2 (site export)
and 3 (addon MVP, v0.1.0, not yet tested in the game) shipped; see `CHANGELOG.md`.
Target: usable before the Nov 4 launch.

| | |
|---|---|
| Addon name | Road to Forever |
| Folder | `addon/RoadToForever/` (in this repo) |
| Slash commands | `/r2f` (main window), `/r2ft` (Talents), `/r2f macros`, `/r2f minimap` (show the minimap button again) |
| Minimap button | yes, draggable around the minimap (section 12) |
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
  (`github.com/nobody174/wow-forever-macros/releases`). Nothing is released until
  step 7; step 7 should re-check this link once the first `addon-v*` zip exists.
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
  Minimap.lua       LibDataBroker launcher + LibDBIcon button + right-click menu
  Bindings.xml      "Toggle Road to Forever", "Open Macros", "Open Talents"
  Core.lua          events, slash commands, init
  libs\            LibStub, CallbackHandler-1.0, LibDataBroker-1.1, LibDBIcon-1.0
  media\logo64.tga  minimap icon (64x64, 32-bit with alpha)
  media\logo128.tga main window portrait
addon/art/logo.svg  logo source (not shipped); build script exports the .tga files
addon/tests/        out-of-game tests (not shipped): run_tests.py, run_luacheck.py
addon/.luacheckrc   allowed globals / WoW API list for luacheck
```

No libraries in v1 (LibDBIcon only when the minimap button is added).

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
    ["WARRIOR/VR"] = { name="VR", hash="a1b2c3", account=false },
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
- **`Macros.Update` ships now but isn't called yet**; step 4 wires it into the import.

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
  token. Addon versions are tagged `r2f-v<version>` (first: `r2f-v0.1.0`). Section 8
  plans the release workflow on `addon-v*` tags: step 7 should pick one prefix
  (simplest: build releases from `r2f-v*`) and note it here.
- `## Interface: 11507` (Classic Era 1.15.7) is a placeholder until the beta check (11).

**Testing outside the game**
- `python addon/tests/run_tests.py` runs the addon under real PUC Lua 5.1 (via the
  `lupa` Python package) against a fake client (`addon/tests/wow_stubs.lua`; its
  macro calls raise if made in combat). Import strings come from
  `addon/tests/make_fixtures.js`, which runs the site's own `importString()` code
  from macros.html in Node. `python addon/tests/run_luacheck.py <luacheck src> <argparse dir>`
  runs luacheck's library API under the same Lua 5.1 with `addon/.luacheckrc`.

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

- GitHub Actions: on a `addon-v*` tag, zip `addon/RoadToForever/` into a
  Release (`RoadToForever-<version>.zip`, folder inside the zip).
- Site: Download link in the export tray's How to import steps -> latest release.
- Later: CurseForge project (auto-updates through the CurseForge app).

## 9. Build order (each step shippable)

1. **Data**: `short` + `icon` + ids in `data.py`, build checks, short names shown
   in the markdown. Warrior and Paladin first (tables above), then the rest.
2. **Site export**: export mode, checkboxes, tray, Copy import string.
3. **Addon MVP**: import window, library, Macro Book for own class + Universal,
   click/drag creates the macro, slot counter, combat lock.
4. **Updates**: re-import updates unedited macros; Changed markers.
5. **Tidy up**, Settings, Remove all, keybindings.
6. **Main window + minimap**: Home / Macros / Talents tabs, logo, LibDBIcon
   button with right-click menu, `/r2f`, `/r2ft`, `/r2f minimap`. Moves the
   step-3 Macro Book (`R2F.MacroBook`) and Import window into the main window
   (6.7).
7. **Release** zip + Download link. CurseForge later. Settle the tag prefix
   (`r2f-v*` vs `addon-v*`, 6.7).
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
- [ ] LibDBIcon button drags around the round minimap and saves its spot.
- [ ] Right-click menu API: `UIDropDownMenu`/`EasyMenu` or the newer `MenuUtil`.
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

- Built with **LibDataBroker-1.1 + LibDBIcon-1.0** (embedded in `libs\`). That
  gives the standard round minimap-button border so it looks native,
  **dragging around the minimap edge** (position saved), square-minimap support,
  and it works with minimap-button collector addons.
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
