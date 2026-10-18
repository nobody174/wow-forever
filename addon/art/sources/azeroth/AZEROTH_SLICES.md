# Azeroth Reforged: slice notes for R2F

15 PNGs, all 32-bit RGBA, sizes exactly as in the request. Colours come from the Azeroth Reforged board in the Design artifact. `source/make_azeroth.py` regenerates all of them (`python make_azeroth.py <out_dir>`), so any size or colour can be tweaked and re-exported.

## Frame
- Frame depth is 16 px at texture size. From the outer edge inward: outer gold 2 px, dark brown 2 px, near-black 4 px, bright inner gold 2 px, dark brown 3 px, then a 3 px fade into the panel.
- `azeroth_edge_h.png` is 64x16: rows are depth, so tile it left to right. Flip it vertically for the bottom edge.
- `azeroth_edge_v.png` is 16x64: columns are depth, so tile it top to bottom. Mirror it horizontally for the right edge.
- `azeroth_corner.png` is 64x64, outer corner radius 20 px. Its straight sections are pixel-identical to the strips (checked, max diff 0). It is symmetric about its diagonal, so mirroring it for the other three corners is safe. The area beyond 16 px of depth is transparent.
- The gem socket is empty. Its centre is at (10, 10) in the corner image. Place `azeroth_gem.png` centred on that point; the gem overhangs the frame on purpose.
- The gem is a diamond like the mockup's corner gems (the request said round). If you want round, change `make_gem()` in the script.

## Banner
- `azeroth_banner.png` is 256x64, no text, 1.5 px clear margin all round, notched ends inside the canvas. The addon draws the title text on the dark plate (the plate is inset 4 px from the gold edge).

## Panel and inset
- `azeroth_panel.png` and `azeroth_inset.png` are 256x256, opaque and seamless (checked by comparing the wrap seam with ordinary neighbouring pixels).
- The mockup's top-to-bottom brown gradient is not baked in, because a vertical gradient cannot tile. If you want it, overlay a vertical gradient texture or vertex-colour the tile.

## Sidebar buttons
- `azeroth_btn_normal/hover/selected.png` are 128x32 with 16 px caps. The middle 96 px (x 16 to 111) is identical in every column, so it stretches without distortion.
- Row 31 is the drop shadow, so the visible body is 31 px high.
- Gems: `azeroth_gem_off.png` and `azeroth_gem_on.png` are 32x32, same shape and centre (16, 16), core radius 8 px. The lit one adds a soft orange glow outside that. Show them at about half size on the right of the button.

## Slider
- `azeroth_slider_track.png` is 128x16 with 8 px caps (middle uniform). It is the dark empty groove only.
- The amber filled part from the mockup is not a slice. Tint a plain texture or the left part of the track in code if you want it.
- `azeroth_slider_knob.png` is 32x32: amber pearl, with a 3.5 px soft glow ring inside the canvas.

## Divider
- `azeroth_divider.png` is 128x8: 2 px gold line fading to transparent on the right.

## Not included
- Letter-spaced small-caps headings, nav icons, and the Home countdown cards and journey list. These were out of scope for this round.
