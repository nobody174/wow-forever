# Frost & Void: slice notes (24 requested PNGs + 1 optional extra, 32-bit RGBA)
Regenerate: `python make_frost.py <out_dir>`. Art is for default gamma. Nothing has been seen in WoW.
Checks passed: exact sizes, plain 9-slice middles, mirror-symmetric frame brackets, seamless panel, glows inside the canvas (edge alpha at most 8/255), colours vs board.

| File | Size | 9-slice / use | Show at |
|---|---|---|---|
| frost_frame | 128x128 | 32 px caps, radius 30, 1 px cyan 30% border, 10 px-arm L brackets 17 px in from each edge (1.5 px stroke, mirror-symmetric). Interior transparent | window |
| frost_panel | 256x256 | seamless tile, base #0C0D22 (the mean of the board's 140deg #14163A to #07070F gradient), 7 stars per tile (white / #CFE9FF, 0.5 to 0.7 px radius). Gradient NOT baked: draw it in code | tiled |
| frost_glow_violet / cyan | 128x128 | round glow, peak 35% / 22%, exactly 0 at the edge | scale freely (the board's are 380x240 / 360x220) |
| frost_glass | 64x64 | 16 px caps, corner radius 16 (= the whole cap), border 1 px cyan 22%, white 8% to 2% top to bottom, top inner edge white 14% | element size |
| frost_display | 64x64 | same plus a faint cyan inner glow, at most 14 px from the edges | about 300x150 |
| frost_orb_normal / hover / on | 32x32 | disc 18.9 px in the texture. SHOW THE 32 px CANVAS AT 44x44 centred on the orb: the disc is then the board's 26 px and the glow, 4 px ring and dashed ring (+7 px) fit inside | 44x44 |
| frost_link | 8x64 | 1 px cyan line at 35% (the group lines of the board), 2 columns at 50% so it reads as 1 px centred, tiles top to bottom | any height |
| frost_link_fade (extra) | 8x64 | the first link of the board: 100% at the top fading to 15%, does NOT tile; stretch it over 40 px or use only for that link | 40 px |
| frost_btn_normal / hover / primary / primary_hover / disabled | 128x32 | **16 px caps**, body inset 3 px (122x26), radius 12 | button size + 6 px each way |
| frost_check_off / on | 32x32 | round, 20 px disc | 32x32 (1:1) |
| frost_switch_off / on | 64x32 | 16 px caps, pill, border drawn 1.5 px | 44x22 |
| frost_switch_knob_off / on | 32x32 | pearl, disc 23 px, on adds a glow inside the canvas | 22x22 |
| frost_slider_track | 128x16 | 6 px groove (y 5..11), 8 px caps | 16 px high |
| frost_slider_fill | 128x16 | same groove, whole #7B5CFF to #7FE7FF gradient baked, no stretch; clip to value | same |
| frost_slider_knob | 32x32 | pearl radius 9.5 + 4 px ring at 16% + glow to the edge | 32x32 |

## Deviations to know about
- **Button caps are 16, not 12.** With the 3 px inset and radius 12 the corner curve reaches x=15, so a 12 px cap would cut it. With 16 px caps the middle is plain.
- **Glass radius:** drawn as 16 (the whole cap). If you show the caps at 22 px, the radius is 22 on screen, as on the board.
- **Glass gradient** runs top to bottom (the board's 160deg is nearly vertical) and stretches with the element.
- **Primary hover** has no hover style on the board (the primary rule overrides it), so I made it 10% brighter with a stronger violet shadow. The shadow is compressed to the 3 px margin.
- **Hover glow and inner glow** are compressed to fit inside the canvas. The board's 22 px blur does not fit.
- **Slider:** the groove touches the left and right canvas edges on purpose (flush end caps).

## Text colours (board)
text #F2F4FF, muted #A9B0D6 (inactive nav, secondary), cyan #7FE7FF (labels, selected icon), nav selected weight 600, labels Sora 600 10px .28em uppercase, title Sora 600 14px .34em, countdown number Sora 200 78px with a cyan glow, primary button text #FFFFFF 600.

## Colour samples: my PNG vs the board
Translucent pieces are composited over the colour they sit on (window #0A0A1D, glass and button fills included) and compared with the board's CSS blend.
| File | Point | My PNG | Board |
|---|---|---|---|
| frame | border over window (x=0,y=64) | #2D4D61 a0.30 | #2D4C61 |
| frame | bracket (x=17,y=22) | #7FE7FF | #7FE7FF |
| panel | base (no star) | #0C0D22 | #0C0D22 (mean of board gradient) |
| glass | fill top (y=5) over window | #1C1C2E a0.07 | #1C1C2E |
| glass | fill bottom (y=58) over window | #101022 a0.02 | #101023 |
| glass | border (x=0,y=32) over window | #2D4457 a0.26 | #2D4458 |
| display | centre over window | #161629 a0.05 | #161628 |
| orb_normal | disc | #12142B | #12142B |
| orb_normal | ring (x=6) | #5E6280 a0.47 | #5E6280 |
| orb_hover | ring | #7FE7FF a0.72 | #7FE7FF |
| orb_on | ring | #7FE7FF a0.84 | #7FE7FF |
| orb_on | centre | #212E57 | #22305A |
| btn_normal | fill over window (x=64,y=16) | #18182A a0.06 | #19192B |
| btn_normal | border (y=3) over fill | #3F677B a0.42 | #40677B |
| btn_hover | border (y=3) | #7FE7FF | #7FE7FF |
| btn_primary | left end (x=14,y=16) | #7168FF | ~#7B5CFF (135deg gradient start, #7B5CFF at corner) |
| btn_primary | right end (x=114,y=16) | #4899FF | ~#3FA4FF |
| btn_disabled | alpha | #FFFFFF a0.02 | white 6% x 0.40 = a0.02 |
| check_off | ring over fill | #6E7390 a0.62 | #6E7291 |
| check_on | ring | #7FE7FF | #7FE7FF |
| check_on | core | #7FE7FF | #7FE7FF |
| switch_off | fill over window | #18182A a0.06 | #19192B |
| switch_on | left over window (x=18) | #404387 a0.47 | #404388 |
| switch_on | border (y=0) | #7FE7FF | #7FE7FF |
| switch_knob_off | centre-ish (x=13,y=13) | #F5F5FA | ~#FFFFFF |
| switch_knob_off | far edge (x=22,y=22) | #C4C9E3 | ~#A9B0D6 |
| switch_knob_on | far edge | #B2F1FF | ~#7FE7FF |
| slider_track | groove over window | #232334 a0.10 | #222234 |
| slider_fill | x=2 | #7B5FFF | #7B5CFF |
| slider_fill | x=125 | #7FE4FF | #7FE7FF |
| slider_knob | highlight (x=13,y=13) | #FFFFFF | #FFFFFF |
| slider_knob | far edge (x=22,y=22) | #7ED2FF a0.86 | ~#7B5CFF .. #7FE7FF (72-100%) |
