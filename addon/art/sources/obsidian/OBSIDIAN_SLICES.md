# Obsidian Night: slice notes (20 PNGs, 32-bit RGBA)
Regenerate: `python make_obsidian.py <out_dir>`. Art is for default gamma (no pre-darkening). Nothing has been seen in WoW.
Checks passed: exact sizes, plain 9-slice middles (max diff 0), glows inside the canvas, colours vs board.

| File | Size | 9-slice / notes | Show at |
|---|---|---|---|
| obsidian_frame | 128x128 | 24 px caps, 1 px #2A2F3A, radius 16, interior transparent | window |
| obsidian_plate | 128x128 | 24 px caps, #171A21, 1 px border, radius 12, row y=1 white 5% (top inner edge) | page area |
| obsidian_tab_hover | 64x32 | 12 px caps, #171A21 radius 8 | tab size |
| obsidian_tab_on | 64x32 | 12 px caps, teal 8% fill, 2 px underline at y 25..27 (x 10..54 in the caps, plain between) + glow inside the canvas | tab size |
| obsidian_tab_sep | 8x32 | 1 px line, 18 px tall, centred: drawn as two columns (x=3,4) at 50% so it reads as 1 px centred | 8x32 |
| obsidian_btn_normal/hover/primary/primary_hover/disabled | 128x32 | 12 px caps, radius 8 | see below |
| obsidian_check_off/on | 32x32 | box 26 px (3..29), radius 5, border drawn 1.33 px so it is 1 px at 24 px | 24x24 |
| obsidian_switch_off/on | 64x32 | 16 px pill caps; border drawn 1.5 px so it is about 1 px at 44x22 | 44x22 |
| obsidian_switch_knob_off/on | 32x32 | disc diameter 20 (about 14 px at 22), on has a teal glow inside the canvas | 22x22 |
| obsidian_slider_track / fill | 128x16 | 4 px groove (y 6..10), 8 px caps, radius 2; fill is the same shape in #35D6C4 | 16 px high |
| obsidian_slider_knob | 32x32 | pearl radius 8: radial at 34% 28%, white 0-14%, #C9FFF7 42%, teal 100%; ring 4 px at 16%; glow inside canvas | 32x32 |
| obsidian_display | 64x64 | 16 px caps, #171A21, 1 px border, radius 12, teal 10% radial in the top-right cap only | about 300x150 |

## Important: button geometry
Hover and primary need an outer ring and glow (board: 3 px ring, 18 px blur). To keep them inside the canvas, the body of ALL five buttons is inset 3 px on every side (body 122x26 inside the 128x32 canvas, same in every state, so nothing jumps on hover). Size the widget so that body matches your button, i.e. add 6 px to the width and height. The glow is compressed to those 3 px.
Disabled = normal at 40% alpha. Primary fill is 10% teal alpha (transparent), so it shows what is behind it, as on the board.

## Text colours (board)
text #E8EAF0, muted #8A91A3, teal #35D6C4 (selected tab, primary button text, countdown accent), amber #FFB547, red #FF5C6C, tab text #8A91A3 (hover #E8EAF0, selected #35D6C4), labels Space Grotesk 500 / JetBrains Mono 500 11px .14em uppercase.

## Colour samples: my PNG vs the board
Translucent pieces are composited over the colour they sit on in the board (window #0E0F13 or card #171A21) and compared with the board's CSS blend.
| File | Point | My PNG | Board |
|---|---|---|---|
| frame | border (x=0,y=64) | #2A2F3A | #2A2F3A |
| plate | fill | #171A21 | #171A21 |
| plate | border (x=0,y=64) | #2A2F3A | #2A2F3A |
| plate | top inner edge (y=1) | #23252C | #23252C |
| tab_hover | fill | #171A21 | #171A21 |
| tab_on | fill over window | #111F21 a0.08 | #111F21 |
| tab_on | underline | #35D6C4 | #35D6C4 |
| btn_normal | fill | #1C2029 | #1C2029 |
| btn_normal | border (y=3) | #2A2F3A | #2A2F3A |
| btn_hover | border (y=3) | #35D6C4 | #35D6C4 |
| btn_hover | ring (y=1) over window | #132729 a0.12 | #132728 |
| btn_primary | border (y=3) | #35D6C4 | #35D6C4 |
| btn_primary | fill over card | #1A2D32 a0.10 | #1A2D31 |
| btn_disabled | fill alpha (40%) | #1C2029 a0.40 | #1C2029 @0.40 |
| check_off | fill | #12151B | #12151B |
| check_off | border (x=3) | #3A4150 | #3A4150 |
| check_on | fill | #35D6C4 | #35D6C4 |
| check_on | tick | #0E0F13 | #0E0F13 |
| switch_off | fill | #12151B | #12151B |
| switch_off | border (y=0) | #3A4150 | #3A4150 |
| switch_on | fill over window | #163736 a0.20 | #163736 |
| switch_on | border (y=0) | #35D6C4 | #35D6C4 |
| switch_knob_off | disc | #8A91A3 | #8A91A3 |
| switch_knob_on | disc | #35D6C4 | #35D6C4 |
| slider_track | groove | #2A2F3A | #2A2F3A |
| slider_fill | fill | #35D6C4 | #35D6C4 |
| slider_knob | centre-ish (lit) | #FFFFFF | ~#FFFFFF (highlight stop) |
| slider_knob | far rim (x=10,y=22) | #39D7C5 a0.62 | ~#35D6C4 |
| display | fill | #171A21 | #171A21 |
| display | border (x=0,y=32) | #2A2F3A | #2A2F3A |
| display | glow (56,6) over card | #182329 | #182329 |
