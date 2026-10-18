"""Round 2 checks: spec rules, colour samples against the board, assembled preview, contact sheet.
Usage: python check_azeroth_r2.py <slice_dir> <font_dir>
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

D, FD = sys.argv[1], sys.argv[2]
OUT = os.path.dirname(D.rstrip("/"))
names = sorted(f for f in os.listdir(D) if f.endswith(".png"))
L = {n: Image.open(os.path.join(D, n)).convert("RGBA") for n in names}
A = {n: np.asarray(i, float) for n, i in L.items()}
ok = True


def report(name, passed, detail=""):
    global ok
    ok &= bool(passed)
    print(("PASS " if passed else "FAIL ") + name + (" - " + detail if detail else ""))


# ---- sizes
EXPECT = {
    "azeroth_corner.png": (64, 64), "azeroth_edge_h.png": (64, 16), "azeroth_edge_v.png": (16, 64),
    "azeroth_gem.png": (32, 32), "azeroth_banner.png": (256, 64), "azeroth_panel.png": (256, 256),
    "azeroth_inset.png": (256, 256), "azeroth_btn_normal.png": (128, 32), "azeroth_btn_hover.png": (128, 32),
    "azeroth_btn_selected.png": (128, 32), "azeroth_gem_off.png": (32, 32), "azeroth_gem_on.png": (32, 32),
    "azeroth_slider_track.png": (128, 16), "azeroth_slider_knob.png": (32, 32), "azeroth_divider.png": (128, 8),
    "azeroth_card.png": (128, 128), "azeroth_btn_primary.png": (128, 32), "azeroth_btn_primary_hover.png": (128, 32),
    "azeroth_btn_disabled.png": (128, 32), "azeroth_check_off.png": (32, 32), "azeroth_check_on.png": (32, 32),
    "azeroth_switch_off.png": (64, 32), "azeroth_switch_on.png": (64, 32), "azeroth_switch_knob.png": (32, 32),
    "azeroth_slider_fill.png": (128, 16), "azeroth_head_journey.png": (128, 16),
    "azeroth_head_character.png": (128, 16), "azeroth_head_ui.png": (128, 16),
}
for n in ("home", "plan", "talents", "gear", "macros", "tweaks"):
    EXPECT[f"azeroth_icon_{n}.png"] = (32, 32)
report("file count", sorted(EXPECT) == names, f"{len(names)} files, expected {len(EXPECT)}")
for n, sz in EXPECT.items():
    img = Image.open(os.path.join(D, n))
    report(f"size {n}", img.size == sz and img.mode == "RGBA" and all(s in (8, 16, 32, 64, 128, 256) for s in sz))

# ---- tiles
for n in ("azeroth_panel.png", "azeroth_inset.png"):
    a = A[n][..., :3]
    sx, sy = np.abs(a[:, 0] - a[:, -1]).mean(), np.abs(a[0] - a[-1]).mean()
    ix, iy = np.abs(a[:, 1:] - a[:, :-1]).mean(), np.abs(a[1:] - a[:-1]).mean()
    report(f"seamless {n}", sx <= ix * 1.5 and sy <= iy * 1.5 and A[n][..., 3].min() == 255,
           f"seam {sx:.2f}/{sy:.2f} vs {ix:.2f}/{iy:.2f}")

# ---- frame
h, v, c = A["azeroth_edge_h.png"], A["azeroth_edge_v.png"], A["azeroth_corner.png"]
report("edge strips constant along their length", np.abs(h - h[:, :1]).max() == 0 and np.abs(v - v[:1]).max() == 0)
report("corner == strips", np.abs(c[:16, 63] - h[:, 0]).max() <= 1 and np.abs(c[63, :16] - v[0]).max() <= 1)
report("corner mirror-safe (symmetric about diagonal)", np.abs(c - c.transpose(1, 0, 2)).max() <= 1)
report("corner interior transparent", c[30:, 30:, 3].max() == 0)

# ---- stretchable pieces: middle columns identical
for n, lo, hi in (("azeroth_btn_normal.png", 16, 112), ("azeroth_btn_hover.png", 16, 112),
                  ("azeroth_btn_selected.png", 16, 112), ("azeroth_btn_primary.png", 16, 112),
                  ("azeroth_btn_primary_hover.png", 16, 112), ("azeroth_btn_disabled.png", 16, 112),
                  ("azeroth_switch_off.png", 16, 48), ("azeroth_switch_on.png", 16, 48),
                  ("azeroth_slider_track.png", 8, 120), ("azeroth_slider_fill.png", 8, 120),
                  ("azeroth_card.png", 24, 104)):
    m = A[n][:, lo:hi]
    report(f"plain middle {n}", np.abs(m - m[:, :1]).max() <= 1, f"cols {lo}..{hi - 1}")
card = A["azeroth_card.png"]
mid = card[24:104, 24:104]
report("card centre plain (rows may only change by the vertical gradient)", np.abs(mid - mid[:, :1]).max() <= 1)

# ---- gems, checkbox, icons, headings
def core(a):
    ys, xs = np.mgrid[0:32, 0:32]
    w = (a[..., 3] / 255.0) * (np.hypot(xs - 15.5, ys - 15.5) < 9.3)
    return (xs * w).sum() / w.sum(), (ys * w).sum() / w.sum(), w.sum()

go, gn = core(A["azeroth_gem_off.png"]), core(A["azeroth_gem_on.png"])
report("nav gems same centre and shape", abs(go[0] - gn[0]) < .1 and abs(go[1] - gn[1]) < .1 and abs(go[2] - gn[2]) < 2)
d = np.abs(A["azeroth_check_on.png"] - A["azeroth_check_off.png"]).max(-1)
ys, xs = np.nonzero(d > 2)
report("checkbox box identical, only the tick differs", xs.min() >= 6 and xs.max() <= 26 and ys.min() >= 8 and ys.max() <= 24,
       f"differences inside x {xs.min()}..{xs.max()}, y {ys.min()}..{ys.max()}")
for n in ("home", "plan", "talents", "gear", "macros", "tweaks"):
    a = A[f"azeroth_icon_{n}.png"]
    vis = a[..., 3] > 0
    pure = (a[vis][:, :3] == 255).all()
    edge = max(a[0, :, 3].max(), a[-1, :, 3].max(), a[:, 0, 3].max(), a[:, -1, 3].max())
    report(f"icon {n}: pure white, not touching the edge", pure and edge == 0, f"covers {vis.sum()} px")
for n in ("journey", "character", "ui"):
    a = A[f"azeroth_head_{n}.png"]
    cols = np.nonzero(a[..., 3].max(0) > 8)[0]
    rows = np.nonzero(a[..., 3].max(1) > 8)[0]
    report(f"heading {n} fits 128x16", a[:, -1, 3].max() == 0 and a[0, :, 3].max() == 0 and a[-1, :, 3].max() == 0,
           f"text spans x {cols.min()}..{cols.max()}, y {rows.min()}..{rows.max()}")
report("banner clear of canvas edge", max(A["azeroth_banner.png"][0, :, 3].max(), A["azeroth_banner.png"][-1, :, 3].max(),
                                          A["azeroth_banner.png"][:, 0, 3].max(), A["azeroth_banner.png"][:, -1, 3].max()) == 0)
print("\nALL PASS" if ok else "\nSOME CHECKS FAILED\n")


# ---- colour samples: our PNG vs the board's CSS value at the same place
def hx(rgb):
    return "#%02X%02X%02X" % tuple(int(round(x)) for x in rgb)


def lerp_stops(t, stops):
    ts = [s[0] for s in stops]
    cols = [np.array([int(s[1][i:i + 2], 16) for i in (1, 3, 5)], float) for s in stops]
    return np.array([np.interp(t, ts, [c[k] for c in cols]) for k in range(3)])


def patch(n, x, y, k=1):
    a = A[n]
    return a[y:y + k, x:x + k, :3].reshape(-1, 3).mean(0)


rows = []


def sample(n, label, x, y, board, k=1):
    rows.append((n, label, hx(patch(n, x, y, k)), board if isinstance(board, str) else hx(board)))


PANEL = [(0, "#3a352c"), (1, "#25211a")]
INSET = [(0, "#1f1b15"), (1, "#14110d")]
for n, stops in (("azeroth_panel.png", PANEL), ("azeroth_inset.png", INSET)):
    for lab, y in (("top", 8), ("middle", 120), ("bottom", 232)):
        sample(n, f"{lab} (16x16 mean)", 120, y, lerp_stops((y + 8) / 256, stops), k=16)
    rows.append((n, "whole-tile mean vs board mid", hx(A[n][..., :3].reshape(-1, 3).mean(0)), hx(lerp_stops(0.5, stops))))
for n, st in (("azeroth_btn_normal.png", BTN := ("#3d382f", "#2a261f", "#0f0c07")),
              ("azeroth_btn_hover.png", ("#47412f", "#30291c", "#0f0c07")),
              ("azeroth_btn_selected.png", ("#52411f", "#2f2412", "#c9a24b"))):
    stops = [(0, st[0]), (1, st[1])]
    sample(n, "outline", 64, 0, st[2])
    sample(n, "body top (y=8)", 64, 8, lerp_stops((8 - 1) / 29, stops))
    sample(n, "body bottom (y=26)", 64, 26, lerp_stops((26 - 1) / 29, stops))
GOLD = [(0, "#ffe29a"), (0.55, "#a8761c"), (1, "#6e4a10")]
PLATE = [(0, "#2c2418"), (1, "#171108")]
sample("azeroth_banner.png", "gold edge top (y=2)", 128, 2, lerp_stops((2.5 - 1.5) / 61, GOLD))
sample("azeroth_banner.png", "plate middle (y=32)", 128, 32, lerp_stops((32.5 - 5.5) / 53, PLATE))
sample("azeroth_banner.png", "gold edge bottom (y=60)", 128, 60, lerp_stops((60.5 - 1.5) / 61, GOLD))
for n, pts in (("azeroth_corner.png", ((60, 1), (60, 5), (60, 9))), ("azeroth_edge_h.png", ((32, 1), (32, 5), (32, 9))),
               ("azeroth_edge_v.png", ((1, 32), (5, 32), (9, 32)))):
    for (x, y), lab, col in zip(pts, ("outer gold line", "near-black gap", "inner gold line"), ("#8A6A2A", "#0D0B07", "#C9A24B")):
        sample(n, lab, x, y, col)
with open(os.path.join(OUT, "azeroth_colour_samples.md"), "w") as f:
    f.write("| File | Point | My PNG | Board |\n|---|---|---|---|\n")
    for r in rows:
        f.write("| %s | %s | %s | %s |\n" % (r[0].replace("azeroth_", "").replace(".png", ""), r[1], r[2], r[3]))
print("colour samples written:", len(rows), "rows")
for r in rows:
    print(f"  {r[0]:26s} {r[1]:26s} mine {r[2]}  board {r[3]}")


# ---- assembled preview (texture scale, 1:1)
def font(w, s):
    return ImageFont.truetype(os.path.join(FD, f"Cinzel-{w}.ttf"), s)


def comp(base, img, xy):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(img, xy)
    base.alpha_composite(layer)


def tile(img, w, h):
    out = Image.new("RGBA", (w, h))
    for yy in range(0, h, img.height):
        for xx in range(0, w, img.width):
            out.paste(img, (xx, yy))
    return out


def slice3(img, w, cap=16):
    out = Image.new("RGBA", (w, img.height))
    out.paste(img.crop((0, 0, cap, img.height)), (0, 0))
    out.paste(img.crop((cap, 0, img.width - cap, img.height)).resize((w - 2 * cap, img.height)), (cap, 0))
    out.paste(img.crop((img.width - cap, 0, img.width, img.height)), (w - cap, 0))
    return out


def slice9(img, w, h, cap):
    out = Image.new("RGBA", (w, h))
    iw, ih = img.size
    xs = [(0, cap, 0, cap), (cap, iw - cap, cap, w - cap), (iw - cap, iw, w - cap, w)]
    ys = [(0, cap, 0, cap), (cap, ih - cap, cap, h - cap), (ih - cap, ih, h - cap, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            out.paste(img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0)), (dx0, dy0))
    return out


def tint(img, hexcol):
    a = np.asarray(img, float).copy()
    a[..., :3] = [int(hexcol[i:i + 2], 16) for i in (1, 3, 5)]
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def text(base, xy, s, f, col, spacing=0.0, anchor="la"):
    dr = ImageDraw.Draw(base)
    if not spacing:
        dr.text(xy, s, font=f, fill=col, anchor=anchor)
        return
    total = sum(f.getlength(ch) + spacing for ch in s) - spacing
    x = xy[0] - total / 2 if anchor[0] == "m" else xy[0]
    for ch in s:  # letter-spaced text: draw glyph by glyph, left-anchored, vertical anchor from the request
        dr.text((x, xy[1]), ch, font=f, fill=col, anchor="l" + anchor[1])
        x += f.getlength(ch) + spacing


W, H = 960, 680
WX, WY, WW, WH = 30, 50, 900, 600
prev = Image.new("RGBA", (W, H), (10, 12, 15, 255))
comp(prev, tile(L["azeroth_panel.png"], WW, WH), (WX, WY))
INX, INY = WX + 250, WY + 90
comp(prev, tile(L["azeroth_inset.png"], WW - 270, WH - 110), (INX, INY))
eh, ev, co = L["azeroth_edge_h.png"], L["azeroth_edge_v.png"], L["azeroth_corner.png"]
comp(prev, tile(eh, WW - 128, 16), (WX + 64, WY))
comp(prev, ImageOps.flip(tile(eh, WW - 128, 16)), (WX + 64, WY + WH - 16))
comp(prev, tile(ev, 16, WH - 128), (WX, WY + 64))
comp(prev, ImageOps.mirror(tile(ev, 16, WH - 128)), (WX + WW - 16, WY + 64))
comp(prev, co, (WX, WY))
comp(prev, ImageOps.mirror(co), (WX + WW - 64, WY))
comp(prev, ImageOps.flip(co), (WX, WY + WH - 64))
comp(prev, ImageOps.flip(ImageOps.mirror(co)), (WX + WW - 64, WY + WH - 64))
for gx, gy in ((10, 10), (WW - 10, 10), (10, WH - 10), (WW - 10, WH - 10)):
    comp(prev, L["azeroth_gem.png"], (WX + gx - 16, WY + gy - 16))
comp(prev, L["azeroth_banner.png"], (WX + 330 - 128, WY - 24))
text(prev, (WX + 330, WY + 8), "Road to Forever", font(700, 19), "#f4d27a", 1.0, "mm")  # fits the plate; 24 px does not

# sidebar
nav = [("selected", "home", "Home", None), (None, "journey", None, None), ("normal", "plan", "Launch plan", None),
       (None, "character", None, None), ("normal", "talents", "Builds", None), ("normal", "gear", "Gear", None),
       (None, "ui", None, None), ("normal", "macros", "Macros", None), ("hover", "tweaks", "Settings", None)]
y = WY + 90
for kind, key, label, _ in nav:
    if kind is None:
        comp(prev, L[f"azeroth_head_{key}.png"], (WX + 30, y + 6))
        y += 28
        continue
    comp(prev, slice3(L[f"azeroth_btn_{kind}.png"], 196), (WX + 28, y))
    col = {"selected": "#fff3cc", "hover": "#fff0c4", "normal": "#cdbf9c"}[kind]
    comp(prev, tint(L[f"azeroth_icon_{key}.png"], col).resize((24, 24), Image.LANCZOS), (WX + 38, y + 4))
    text(prev, (WX + 72, y + 16), label, font(500, 15), col, 0, "lm")
    comp(prev, L["azeroth_gem_on.png" if kind == "selected" else "azeroth_gem_off.png"].resize((16, 16), Image.LANCZOS),
         (WX + 28 + 196 - 26, y + 8))
    y += 38

# page content
text(prev, (INX + 30, INY + 22), "Home", font(700, 26), "#f1cf7a", 1.0)
text(prev, (INX + 30, INY + 58), "FOREVER LAUNCHES IN", font(700, 11), "#c9a24b", 2.4)
for i, (num, lab) in enumerate((("18", "DAYS"), ("01", "HOURS"), ("44", "MINUTES"))):
    cx = INX + 30 + i * 106
    comp(prev, slice9(L["azeroth_card.png"], 96, 112, 24), (cx, INY + 80))
    text(prev, (cx + 48, INY + 122), num, font(700, 40), "#ffd77a", 0, "mm")
    text(prev, (cx + 48, INY + 168), lab, font(700, 11), "#a89868", 2.2, "mm")
by = INY + 214
comp(prev, slice3(L["azeroth_btn_primary.png"], 150), (INX + 30, by))
text(prev, (INX + 30 + 75, by + 16), "Open launch plan", font(500, 12), "#2a1a02", 0, "mm")
comp(prev, slice3(L["azeroth_btn_primary_hover.png"], 150), (INX + 190, by))
text(prev, (INX + 190 + 75, by + 16), "Primary hover", font(500, 12), "#2a1a02", 0, "mm")
comp(prev, slice3(L["azeroth_btn_normal.png"], 150), (INX + 350, by))
text(prev, (INX + 350 + 75, by + 16), "Normal", font(500, 14), "#eadcb6", 0, "mm")
comp(prev, slice3(L["azeroth_btn_disabled.png"], 150), (INX + 510, by))
text(prev, (INX + 510 + 75, by + 16), "Off", font(500, 14), "#7d735c", 0, "mm")
cy = by + 56
comp(prev, L["azeroth_check_off.png"], (INX + 26, cy))
text(prev, (INX + 62, cy + 16), "Show minimap button", font(500, 14), "#e9dcb8", 0, "lm")
comp(prev, L["azeroth_check_on.png"], (INX + 26, cy + 40))
text(prev, (INX + 62, cy + 56), "Lock window", font(500, 14), "#e9dcb8", 0, "lm")
comp(prev, L["azeroth_switch_off.png"], (INX + 300, cy))
comp(prev, L["azeroth_switch_knob.png"], (INX + 300, cy))
comp(prev, L["azeroth_switch_on.png"], (INX + 300, cy + 40))
comp(prev, L["azeroth_switch_knob.png"], (INX + 300 + 32, cy + 40))
comp(prev, slice3(L["azeroth_slider_track.png"], 200, 8), (INX + 420, cy + 8))
comp(prev, slice3(L["azeroth_slider_fill.png"], 130, 8), (INX + 420, cy + 8))
comp(prev, L["azeroth_slider_knob.png"], (INX + 420 + 130 - 16, cy))
comp(prev, L["azeroth_divider.png"], (INX + 420, cy + 56))
prev.convert("RGB").save(os.path.join(OUT, "azeroth_preview.png"))

# contact sheet on a checkerboard (transparency and halo check), small files shown at 2x
SW, SH = 1060, 920
sheet = Image.new("RGBA", (SW, SH))
dr = ImageDraw.Draw(sheet)
for bx in range(0, SW, 16):
    for by_ in range(0, SH, 16):
        s = 190 if (bx // 16 + by_ // 16) % 2 else 130
        dr.rectangle([bx, by_, bx + 15, by_ + 15], fill=(s, s, s, 255))
px, py, rowh = 8, 8, 0
for n in names:
    img = L[n]
    if img.width <= 64 and img.height <= 64:
        img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    if n in ("azeroth_panel.png", "azeroth_inset.png"):
        img = img.resize((128, 128))
    if px + img.width > SW - 8:
        px, py, rowh = 8, py + rowh + 10, 0
    comp(sheet, img, (px, py))
    px += img.width + 10
    rowh = max(rowh, img.height)
sheet.convert("RGB").save(os.path.join(OUT, "azeroth_contact_sheet.png"))
