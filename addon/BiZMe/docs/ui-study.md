# UI study: ForeverDungeonJournal (2026-11-15)

Read-only look at `ForeverDungeonJournal` 2.0.6 (author Exehn; 495 files, mostly map and portrait TGAs; `Core/Journal.lua` is 13,482 lines). No licence text ships with it
(README, TOC and ARCHITECTURE say nothing), so treat it as all rights reserved: study the design, copy no code, art or data. Nothing was run in game; this is from code.

## TL;DR
- It looks "native" because it uses **Blizzard art files and stock templates with a dark tint**, not custom skins: `Interface\FrameGeneral\UI-Background-Rock` background,
  `Interface\DialogFrame\UI-DialogBox-Border` edge, `UIPanelButtonTemplate` (47 uses), `UIPanelScrollFrameTemplate` (7), `UICheckButtonTemplate`, `InputBoxTemplate`, `UIPanelCloseButton`, `BackdropTemplate` (91 frames).
- Layout: 850 x 590 centred window, `DIALOG` strata, movable and clamped; a gold-lined 34 px title strip; a left list (dungeons), a detail area (bosses, loot rows, quests); tabs such as Loot, Quests, Map, Recipes & Patterns.
- Per-dungeon colour themes (`UI/ThemeData.lua`: `frame, content, border, header, left, right, row, rowSelected, lootRow, title, text, muted` as RGBA tables) give each dungeon identity without new art.
- Data-driven: `Data/*.lua` (Dungeons, Bosses, QuestChains, QuestMaps, DungeonEntrances, ...), the UI code only draws.
- Parts relevant to BiZMe: item rows, hover tooltips with an optional auto-comparison, the tooltip "source strip" (`Systems/ItemSource.lua`), favourites.

## What it does well (steal the idea)
1. **One strong frame, quiet chrome.** Dark rock background, thin gold lines, standard buttons. It reads as Blizzard's own UI. We can get the same with stock templates and the same Blizzard files, no new art.
2. **Master-detail layout** (left list, right detail): the same shape as our slot list and slot panel.
3. **Rows with icon, quality-coloured name, source subline, hover = game tooltip plus compare.** We have most of it; the difference is density and the compare.
4. **Tooltip source strip** on items anywhere in the game ("Boss - Dungeon", or "! Quest - Dungeon"), click opens the journal. Our equivalent: a line "BiZ #1 for Hunter/BM at 38" on any item tooltip. It only appends a line from a tooltip hook, so it is taint-safe.
5. **Key binding "open hovered item"**, because hover tooltips vanish. Good for "wish this hovered item".
6. **Per-dungeon themes as plain colour tables**: we could tint the panel per class the same cheap way.
7. Resize, favourites, run log, world-map overlay, language switch: out of scope; note the maintenance cost.

## Cons / avoid
- A single 13,482-line `Journal.lua`; keep our one-file-per-tab rule.
- `BackdropTemplate` everywhere: works on this client; check in game whether Forever has `NineSlice` / atlas frames before choosing (see `blizzard-ui-extraction.md` in the support folder).
- Large custom TGA map art; we need none.
- A free-floating `DIALOG` window; a docked Character-frame panel needs `CharacterFrame` hooks (plan-review item 5).

## Blizzard templates and files it uses
| Need | Used there | Use for BiZMe |
|---|---|---|
| Window background | `Interface\FrameGeneral\UI-Background-Rock` + `Interface\DialogFrame\UI-DialogBox-Border` via backdrop | same files for the docked panel |
| Buttons | `UIPanelButtonTemplate` | replace our own button widget in `UI/BiZ.lua` |
| Scroll | `UIPanelScrollFrameTemplate` | wishlist and route lists (we already try it through `UI.TryTemplate`) |
| Checkbox, edit box | `UICheckButtonTemplate`, `InputBoxTemplate` | source filters, import box |
| Close | `UIPanelCloseButton` | yes |
| Row / pill look | `Interface\Buttons\WHITE8X8` + `Interface\Tooltips\UI-Tooltip-Border` with tints | yes |

## Proposed BiZMe look (Phase 5, not built)
- A **docked panel** on the Character frame's right edge (`CharacterFrame:HookScript("OnShow")`, anchored with `SetPoint`, no writes into its fields), about 340 wide, rock background and gold title strip.
- Slot overlays: a small coloured marker on each Character slot button (green at BiZ, yellow alternative, red upgrade available) through `hooksecurefunc("PaperDollItemSlotButton_Update", ...)`; ForeverWoWBiS does the same.
- The R2F main-window tab stays for the wide "browse any class/level" view.
- Keep widgets behind `UI.*` so a later skin only swaps them.
- Test first (TESTING item): taint check with the panel shown, in combat, on login. Our rule: no writes in combat; the panel is read-only apart from our own wishlist.
