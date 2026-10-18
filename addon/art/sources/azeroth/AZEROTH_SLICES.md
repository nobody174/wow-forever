# Azeroth Reforged: slice notes, round 2

34 PNGs, 32-bit RGBA, transparent where not stated otherwise. `source/` regenerates all of them
(`python make_azeroth_r2.py <out_dir> <Cinzel-700.ttf>`).
All structural checks pass: exact sizes, seamless tiles, corner matches the strips, middles plain, icons pure white.
Nothing has been seen in WoW.

## What changed in the re-exported files (A)
- **Frame (corner, edge_h, edge_v):** exact board colours, no tinted highlight pixels: outer gold `#8A6A2A` (2 px), `#20190C` (2 px), near-black gap `#0D0B07` (4 px), inner gold `#C9A24B` (2 px), `#2A2112` (3 px), then a 3 px fade. Depth 16 px, corner radius 20 px, socket centre (10, 10), unchanged geometry.
- **Banner:** gold edge `#FFE29A` -> `#A8761C` (55%) -> `#6E4A10`, plate `#2C2418` -> `#171108`. The plate glow from round 1 is gone, so the plate is clearly darker than the edge. Notches unchanged.
- **Buttons normal / hover / selected:** board gradients and outline. Stronger edge contrast: a 1 px light top edge (34% / 42% / 50% instead of 14%) with a dark line right under it. The selected amber glow now follows the board's CSS blur (it was about twice as strong, which flattened the gradient).
- **Panel and inset:** darker, flat-mean seamless tiles with low-contrast grain. Panel mean `#2B271F` (round 1 was `#2F2B23`), inset mean `#16130E`.

## New files
| File | Size | 9-slice / stretch | Show at (on the 820x664 window) |
|---|---|---|---|
| `azeroth_icon_home/plan/talents/gear/macros/tweaks.png` | 32x32 | pure white, 2.2 px stroke, drawn from the board's own SVG paths | 18 x 18 |
| `azeroth_card.png` | 128x128 | 9-slice, 24 px corners, plain middle (inner shadow stays inside the bottom 24 px) | 70 x 84 (caps about 13 px) |
| `azeroth_btn_primary.png`, `_hover.png` | 128x32 | 16 px caps, plain middle | your button size (caps scale with height) |
| `azeroth_btn_disabled.png` | 128x32 | 16 px caps, plain middle. The board's Off button: normal button with saturate(.3) brightness(.8) | same |
| `azeroth_check_off.png`, `_on.png` | 32x32 | box at (4,4)-(28,28) in both, gold tick `#FFD77A` only in `_on` | 24 x 24 |
| `azeroth_switch_off.png`, `_on.png` | 64x32 | 16 px caps, plain middle, track only | 44 x 22 (caps 11 px) |
| `azeroth_switch_knob.png` | 32x32 | neutral pearl, off-state colours. Tint it amber for on if you want | 22 x 22 |
| `azeroth_slider_fill.png` | 128x16 | 8 px caps, plain middle. Same groove geometry as `azeroth_slider_track.png`, so they line up | 13 px high |
| `azeroth_head_journey/character/ui.png` | 128x16 | text baked, Cinzel Bold 12 px, 2.4 px letter spacing, `#C9A24B`, left-aligned at x=1. Text spans 76 / 100 / 17 px | 1:1 (board uses 11 px, so 117 x 15 is also fine) |

Other sizes, for the pieces from round 1: nav gems 16 x 16 (core 8 px like the board's dot), corner gem about 26 x 26, slider knob 28 x 28, slider track 13 px high.
The heading font is Cinzel Bold from Fontsource (SIL Open Font License). Only its outlines are baked into the PNGs; the font is not needed in the addon for these.

## F) Answers

### Text colours on the board
| Use | Colour | Font on the board |
|---|---|---|
| Window title (banner) | `#F4D27A`, shadow 0 2px 0 `#000`, glow rgba(255,190,80,.45) | Cinzel 700, 26 px, spacing .06em |
| Nav label, normal | `#CDBF9C` | Alegreya Sans 500, 16 px |
| Nav label, hover | `#FFF0C4` | same |
| Nav label, selected | `#FFF3CC` (selected border `#C9A24B`) | same |
| Page heading (Home) | `#F1CF7A` | Cinzel 700, 26 px, spacing .04em |
| Small caps headings and card labels | `#C9A24B` (card labels DAYS/HOURS use `#A89868`) | Cinzel 700, 11 px, spacing .2em |
| Body text | `#E9DCB8` | Alegreya Sans 500, 16 px |
| Secondary text (tagline, descriptions) | `#B9AA84` | Alegreya Sans 400, 15 to 16 px |
| Muted text (version, done items) | `#A89868` | Alegreya Sans 500 |
| Countdown numbers | `#FFD77A`, glow rgba(255,180,60,.5), shadow 0 2px 0 `#000` | Cinzel 700, 50 px |
| Button text: normal / primary / disabled | `#EADCB6` / `#2A1A02` / `#7D735C` | Alegreya Sans 700, 15 px |
| Slider labels | `#C9A24B` | Alegreya Sans 500, 12 px |

### What to recreate in code (two end colours, top to bottom)
- **Window panel:** `#3A352C` -> `#25211A`. My `azeroth_panel.png` is a flat grain tile (a vertical gradient cannot tile), mean `#2B271F`. For the exact board look, draw the gradient in code and tell me; I will add a transparent grain overlay tile.
- **Inset behind the pages:** `#1F1B15` -> `#14110D`, plus the board's inner shadow (0 8px 22px black at 65%, strongest at the top). Same situation: tile is flat `#16130E`. I can add a transparent 9-slice shadow overlay.
- **Baked into the images, nothing to do in code:** banner, all buttons, card (gradient and shadow), switch tracks, checkbox, slider groove and fill.

### If it still looks lighter in game
The PNG colours match the board's CSS values to within 1 level for the buttons, banner and frame (table below). So lighter, flatter browns in game point at something on the addon side: a vertex colour or tint multiplying the texture, an alpha below 1, or a blend mode. Worth checking before I darken anything further.

### Banner title size
The banner is shown at most 248 px wide, but the board's 26 px title sits on a 400 px banner. At 248 px the title has to shrink to about 19 px (Cinzel Bold, 1 px spacing, about 190 px wide) to stay on the plate.

## Colour samples: my PNG vs the board
"Board" is the board's own CSS value evaluated at the same position (the board is an HTML page, so these are computed from its source, not from a screenshot). Panel and inset are grain tiles, so 16x16 means are shown. The selected button includes the board's amber inner glow on top of the gradient, so it reads slightly lighter than the bare gradient.

| File | Point | My PNG | Board |
|---|---|---|---|
| panel | top (16x16 mean) | #2B271F | #39342B |
| panel | middle (16x16 mean) | #25211A | #302B23 |
| panel | bottom (16x16 mean) | #29251D | #26221B |
| panel | whole-tile mean vs board mid | #2B271F | #302B23 |
| inset | top (16x16 mean) | #14110D | #1E1A14 |
| inset | middle (16x16 mean) | #17140F | #1A1611 |
| inset | bottom (16x16 mean) | #15120D | #15120E |
| inset | whole-tile mean vs board mid | #16130E | #1A1611 |
| btn_normal | outline | #0F0C07 | #0f0c07 |
| btn_normal | body top (y=8) | #38332B | #38342B |
| btn_normal | body bottom (y=26) | #2C2821 | #2D2821 |
| btn_hover | outline | #0F0C07 | #0f0c07 |
| btn_hover | body top (y=8) | #413B2A | #413B2A |
| btn_hover | body bottom (y=26) | #332C1E | #332C1F |
| btn_selected | outline | #C9A24B | #c9a24b |
| btn_selected | body top (y=8) | #4F3E1D | #4A3A1C |
| btn_selected | body bottom (y=26) | #423218 | #342814 |
| banner | gold edge top (y=2) | #FCDF96 | #FCDF96 |
| banner | plate middle (y=32) | #211A10 | #211A10 |
| banner | gold edge bottom (y=60) | #724D11 | #724D11 |
| corner | outer gold line | #8A6A2A | #8A6A2A |
| corner | near-black gap | #0D0B07 | #0D0B07 |
| corner | inner gold line | #C9A24B | #C9A24B |
| edge_h | outer gold line | #8A6A2A | #8A6A2A |
| edge_h | near-black gap | #0D0B07 | #0D0B07 |
| edge_h | inner gold line | #C9A24B | #C9A24B |
| edge_v | outer gold line | #8A6A2A | #8A6A2A |
| edge_v | near-black gap | #0D0B07 | #0D0B07 |
| edge_v | inner gold line | #C9A24B | #C9A24B |
