"""Obsidian Night slices for the R2F addon (22 files). Colours from the Obsidian Night board CSS.
Usage: python make_obsidian.py <output_dir>
Conventions: buttons, tabs, plates 1:1; switch tracks shown 64x32 -> 44x22 so their 1 px border is drawn 1.5 px;
check box shown 32 -> 24 so its 1 px border is drawn 1.33 px.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_azeroth as base
from make_azeroth import S, blank, down, grid, hexc, paint, rrect_sdf

BORDER, CARD, TEAL, FIELD, EDGE2, BTN = "#2a2f3a", "#171a21", "#35d6c4", "#12151b", "#3a4150", "#1c2029"
phi = lambda z: 1.0 / (1.0 + np.exp(-1.702 * z))
cov = lambda sdf: (sdf < 0).astype(float)

def shape(w, h, x0, y0, x1, y1, r, bw):
    X, Y = grid(w, h)
    outer = rrect_sdf(X, Y, x0, y0, x1, y1, r)
    inner = rrect_sdf(X, Y, x0 + bw, y0 + bw, x1 - bw, y1 - bw, max(r - bw, 0.5))
    return X, Y, cov(outer), cov(inner)

def make_frame():
    w = h = 128; d = blank(w, h)
    X, Y, o, i = shape(w, h, 0, 0, w, h, 16, 1)
    paint(d, np.clip(o - i, 0, 1), hexc(BORDER)); return down(d)

def make_plate():
    w = h = 128; d = blank(w, h)
    X, Y, o, i = shape(w, h, 0, 0, w, h, 12, 1)
    paint(d, o, hexc(BORDER)); paint(d, i, hexc(CARD))
    sh = cov(rrect_sdf(X, Y, 1, 2, w - 1, h - 1, 11))  # inset 0 1px 0 rgba(255,255,255,.05)
    paint(d, np.clip(i - sh, 0, 1) * 0.05, hexc("#ffffff")); return down(d)

def make_tab_hover():
    w, h = 64, 32; d = blank(w, h); X, Y = grid(w, h)
    paint(d, cov(rrect_sdf(X, Y, 0, 0, w, h, 8)), hexc(CARD)); return down(d)

def make_tab_on():
    w, h = 64, 32; d = blank(w, h); X, Y = grid(w, h)
    paint(d, cov(rrect_sdf(X, Y, 0, 0, w, h, 8)) * 0.08, hexc(TEAL))
    xa, xb, ya, yb, s = 10.0, 54.0, 25.0, 27.0, 1.8   # underline y 25..27, glow stays inside the canvas
    gx = np.where((X >= 12) & (X <= w - 12), 1.0, phi((X - xa) / s) * phi((xb - X) / s))
    gl = gx * phi((Y - ya) / s) * phi((yb - Y) / s)
    taper = np.clip(np.minimum(np.minimum(Y, h - Y), np.minimum(X, w - X)) / 3.0, 0, 1)
    paint(d, gl * taper * 0.8, hexc(TEAL))
    paint(d, cov(rrect_sdf(X, Y, xa, ya, xb, yb, 1)), hexc(TEAL)); return down(d)

def make_tab_sep():
    w, h = 8, 32; d = blank(w, h); X, Y = grid(w, h)
    paint(d, ((X >= 3) & (X < 5) & (Y >= 7) & (Y < 25)) * 0.5, hexc(BORDER)); return down(d)

def make_button(kind):
    w, h = 128, 32; d = blank(w, h); X, Y = grid(w, h)
    x0, y0, x1, y1 = 3, 3, w - 3, h - 3     # body inset 3 px so the outer ring / glow fit in the canvas
    o = cov(rrect_sdf(X, Y, x0, y0, x1, y1, 8)); i = cov(rrect_sdf(X, Y, x0 + 1, y0 + 1, x1 - 1, y1 - 1, 7))
    sd = rrect_sdf(X, Y, x0, y0, x1, y1, 8)
    if kind in ("hover", "primary_hover"):
        paint(d, ((sd >= 0) & (sd < 3)) * 0.12, hexc(TEAL))  # 0 0 0 3px rgba(teal,.12)
    if kind in ("primary", "primary_hover"):
        paint(d, np.clip(1 - sd / 2.6, 0, 1) ** 1.5 * (sd >= 0) * 0.28, hexc(TEAL))  # soft glow, compressed to 3 px
    teal_border = kind != "normal" and kind != "disabled"
    paint(d, np.clip(o - i, 0, 1), hexc(TEAL if teal_border else BORDER))
    if kind in ("primary", "primary_hover"):
        paint(d, i * 0.10, hexc(TEAL))
    else:
        paint(d, i, hexc(BTN))
    img = down(d)
    if kind == "disabled":
        a = np.asarray(img, float); a[..., 3] *= 0.4; img = Image.fromarray(np.round(a).astype(np.uint8), "RGBA")
    return img

def make_check(on):
    w = h = 32; d = blank(w, h); X, Y = grid(w, h)
    bw = 1.33; x0, x1 = 3, 29
    o = cov(rrect_sdf(X, Y, x0, x0, x1, x1, 5)); i = cov(rrect_sdf(X, Y, x0 + bw, x0 + bw, x1 - bw, x1 - bw, 5 - bw))
    paint(d, o, hexc(TEAL if on else EDGE2)); paint(d, i, hexc(TEAL if on else FIELD))
    if on:
        SS = 8; im = Image.new("L", (w * SS, h * SS), 0)
        ImageDraw.Draw(im).line([(10 * SS, 16.5 * SS), (14 * SS, 20.5 * SS), (22.5 * SS, 11.5 * SS)], fill=255, width=int(2.8 * SS), joint="curve")
        paint(d, np.asarray(im.resize((w * S, h * S), Image.BILINEAR), float) / 255.0, hexc("#0e0f13"))
    return down(d)

def make_switch(on):
    w, h = 64, 32; d = blank(w, h); X, Y = grid(w, h); bw = 1.5
    o = cov(rrect_sdf(X, Y, 0, 0, w, h, 16)); i = cov(rrect_sdf(X, Y, bw, bw, w - bw, h - bw, 16 - bw))
    paint(d, o, hexc(TEAL if on else EDGE2))
    if on:  # teal 20% fill inside a teal border: clear the interior then paint the translucent fill
        img = down(d); a = np.asarray(img, float) / 255.0
        ii = np.asarray(down(_mask(i, w, h)), float)[..., 3] / 255.0
        a[..., 3] = np.clip(a[..., 3] * (1 - ii) + ii * 0.2, 0, 1)
        rgb = np.asarray(hexc(TEAL), float) / 255.0; a[..., :3] = np.where(ii[..., None] > 0, rgb, a[..., :3])
        return Image.fromarray(np.round(a * 255).astype(np.uint8), "RGBA")
    paint(d, i, hexc(FIELD)); return down(d)

def _mask(m, w, h):
    d = blank(w, h); paint(d, m, (255, 255, 255)); return d

def make_knob(on):
    w = h = 32; d = blank(w, h); X, Y = grid(w, h); r = 10
    dist = np.hypot(X - 16, Y - 16) - r
    if on:
        paint(d, np.where(dist >= 0, 0.7 * np.exp(-(dist / 2.4) ** 2), 0), hexc(TEAL))
    paint(d, cov(dist), hexc(TEAL if on else "#8a91a3")); return down(d)

def _groove(w, h):
    X, Y = grid(w, h); return X, Y, cov(rrect_sdf(X, Y, 0, 6, w, 10, 2))

def make_slider(fill):
    w, h = 128, 16; d = blank(w, h); X, Y, m = _groove(w, h)
    paint(d, m, hexc(TEAL if fill else BORDER)); return down(d)

def make_slider_knob():
    w = h = 32; d = blank(w, h); X, Y = grid(w, h); r = 8
    dist = np.hypot(X - 16, Y - 16) - r
    glow = np.where(dist >= 0, 0.6 * np.exp(-(dist / 3.0) ** 2) * np.clip(1 - dist / 8.2, 0, 1), 0)
    paint(d, glow, hexc(TEAL))
    paint(d, ((dist >= 0) & (dist < 4)) * 0.16, hexc(TEAL))  # 0 0 0 4px rgba(teal,.16)
    cx, cy = 16 - 8 + 0.34 * 16, 16 - 8 + 0.28 * 16
    t = np.hypot(X - cx, Y - cy) / np.hypot(16 - 0.34 * 16, 16 - 0.28 * 16)
    st = [0, 0.14, 0.42, 1.0]; cols = [hexc("#ffffff"), hexc("#ffffff"), hexc("#c9fff7"), hexc(TEAL)]
    rgb = np.stack([np.interp(t, st, [c[k] for c in cols]) for k in range(3)], -1)
    paint(d, cov(dist), rgb); return down(d)

def make_display():
    w = h = 64; d = blank(w, h)
    X, Y, o, i = shape(w, h, 0, 0, w, h, 12, 1)
    paint(d, o, hexc(BORDER)); paint(d, i, hexc(CARD))
    paint(d, i * 0.10 * np.clip(1 - np.hypot(X - 62, Y - 2) / 14, 0, 1), hexc(TEAL)); return down(d)

def main(out):
    os.makedirs(out, exist_ok=True)
    f = {"frame": make_frame(), "plate": make_plate(), "tab_hover": make_tab_hover(), "tab_on": make_tab_on(), "tab_sep": make_tab_sep(),
         "check_off": make_check(False), "check_on": make_check(True), "switch_off": make_switch(False), "switch_on": make_switch(True),
         "switch_knob_off": make_knob(False), "switch_knob_on": make_knob(True), "slider_track": make_slider(False),
         "slider_fill": make_slider(True), "slider_knob": make_slider_knob(), "display": make_display()}
    for k in ("normal", "hover", "primary", "primary_hover", "disabled"): f["btn_" + k] = make_button(k)
    for n, im in f.items(): im.save(os.path.join(out, f"obsidian_{n}.png"))
    print(len(f), "files ->", out)
if __name__ == "__main__": main(sys.argv[1])
