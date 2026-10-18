# Ember & Iron: slice notes (24 PNGs, 32-bit RGBA)
Regenerate: `python make_ember.py <out_dir>`. Colours are the board's CSS values. Nothing has been seen in WoW.
Cut shape: top-left and bottom-right corners chamfered, the other two square (as on the board).

| File | Size | 9-slice / use | Show at |
|---|---|---|---|
| ember_frame | 128x128 | 32 px caps, plain middle. 3 px dark outline, 3 px steel ring, 4 px faint top highlight. Border only, interior transparent | window size |
| ember_panel | 256x256 | seamless tile, flat #2A2725 mean, 1 px vertical lines every 4 px | tiled |
| ember_heat | 128x16 | tile left to right along the window bottom. Transparent to orange 20% | 128x16, inside the frame |
| ember_rivet | 16x16 | steel dome | 16x16, 14 px from each corner |
| ember_plate | 64x64 | 16 px caps, plain middle (page area) | any |
| ember_display | 64x64 | 16 px caps, plain middle. Orange inner glow lives in the caps | about 222x84 |
| ember_slot_normal/hover/on | 64x64 | draw 1:1, do not stretch (vertical gradient and radial glow) | 64x64 |
| ember_btn_normal/hover/primary/primary_hover/disabled | 128x32 | 16 px caps, plain middle, chamfer 7 | button size |
| ember_check_off/on | 32x32 | box 26 px, tick only in _on | 24x24 |
| ember_switch_off/on | 64x32 | tracks, 16 px caps | 44x22 |
| ember_switch_knob_off/on | 32x32 | same block shape, on has a glow | 22x22 |
| ember_slider_track | 128x16 | 8 px caps, plain middle | 12 px groove |
| ember_slider_fill | 128x16 | whole gradient baked (#C4480C, #FF7A2E at 40%, #FFC247), no stretch; clip to value | same as track |
| ember_slider_knob | 32x32 | bead about 22x18 with glow inside canvas | 32x22 |
| ember_rule | 64x8 | 3 px orange line fading right | 60x3 |

Icons: reuse the white azeroth_icon_* files, 24 px, tint #FFC247 (hover/on) or #B5AFA5 (normal).

## Text colours (board)
Title #FF9A45 (Barlow Condensed 700, 30px, .12em, glow); labels #FF7A2E (Barlow Condensed 700 13px .22em); tile heading #FFC247; page heading #E9E3D8; body #D9D4CC (Barlow 500); muted #8F8A82 / #7B756C; slot labels #B5AFA5 (hover/on #FFC247); countdown #FF9A45 (last #FFD36A), Chakra Petch 700; colon #57524C; button text #E9E3D8 / hover #FFC247 / primary #1A0D02 / disabled #6F6A62.

## Code vs baked
Window panel gradient #34312E to #1F1D1B is NOT baked (panel is a flat tile); recreate in code if wanted. Slot, button, display, check, switch, slider gradients are baked.
Known deviations: slider knob and switch-on glow are shortened to stay inside the canvas; display glow is compressed into the 16 px caps.
