"""Frost & Void slices for the R2F addon (22 files). Colours from the Frost & Void board (Arcane.dc.html).
Usage: python make_frost.py <output_dir>
Scale notes: orbs are drawn for a 32 px canvas shown at 44 px (k=1.375, so the 26 px board orb = 18.9 px in the texture);
check box 1:1 (32 px canvas, 20 px disc); switch tracks 64x32 shown 44x22; glass caps drawn at radius 16 (= the whole cap).
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_azeroth as base
from make_azeroth import S, blank, down, grid, hexc, paint, rrect_sdf

CY, VI, BL, WH, MU, ORB = "#7fe7ff", "#7b5cff", "#3fa4ff", "#ffffff", "#a9b0d6", "#12142b"
phi = lambda z: 1.0 / (1.0 + np.exp(-1.702 * z))
cov = lambda sdf: (sdf < 0).astype(float)
def lerp_stops(t, stops):
    ts = [s[0] for s in stops]; cs = [hexc(s[1]) for s in stops]
    return np.stack([np.interp(t, ts, [c[k] for c in cs]) for k in range(3)], -1)
def ringmask(sdf_outer_box, bw):  # border ring of a box given its outer sdf: -bw < sdf < 0
    return ((sdf_outer_box < 0) & (sdf_outer_box >= -bw)).astype(float)
def soft(d, k, amp, lim):  # glow outside a shape: d = distance outside (>=0); fades to 0 at lim
    return np.where(d >= 0, amp * np.exp(-(d / k) ** 2) * np.clip(1 - d / lim, 0, 1), 0)

def make_frame():
    w = h = 128; dst = blank(w, h); X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 0, w, h, 30)
    paint(dst, ringmask(sdf, 1) * 0.30, hexc(CY))
    for cx, sx in ((0, 1), (w, -1)):       # L brackets, 10 px arms, 1.5 px stroke, 17 px in from each outer edge
        for cy, sy in ((0, 1), (h, -1)):
            ax, ay = cx + sx * 17.5, cy + sy * 17.5
            hor = (np.abs(Y - ay) <= 0.75) & (((X - ax) * sx >= -0.75) & ((X - ax) * sx <= 10))
            ver = (np.abs(X - ax) <= 0.75) & (((Y - ay) * sy >= -0.75) & ((Y - ay) * sy <= 10))
            paint(dst, (hor | ver).astype(float), hexc(CY))
    return down(dst)

def make_panel():
    n = 256; rng = np.random.default_rng(7); SS = 6
    img = np.zeros((n * SS, n * SS), float)
    Y, X = (np.mgrid[0:n * SS, 0:n * SS] + 0.5) / SS
    stars = [(rng.uniform(0, n), rng.uniform(0, n), rng.choice([0.6, 0.5, 0.7]), rng.random() < 0.6) for _ in range(7)]
    col = np.zeros((n * SS, n * SS, 3)); a = np.zeros((n * SS, n * SS))
    for sx, sy, r, white in stars:
        dx = np.abs(X - sx); dx = np.minimum(dx, n - dx); dy = np.abs(Y - sy); dy = np.minimum(dy, n - dy)
        m = (np.hypot(dx, dy) < r) * 0.9
        c = np.array(hexc("#ffffff" if white else "#cfe9ff"), float)
        col = np.where(m[..., None] > a[..., None], c, col); a = np.maximum(a, m)
    base_c = np.array(hexc("#0c0d22"), float)
    rgb = base_c * (1 - a[..., None]) + col * a[..., None]
    rgb = rgb.reshape(n, SS, n, SS, 3).mean((1, 3))
    return Image.fromarray(np.round(np.dstack([rgb, np.full((n, n), 255.0)])).astype(np.uint8), "RGBA")

def make_glow(color, amp):
    w = h = 128; dst = blank(w, h); X, Y = grid(w, h)
    s = np.clip(np.hypot(X - 64, Y - 64) / 64, 0, 1); paint(dst, amp * (1 - s) ** 2 * (1 + 2 * s), hexc(color)); return down(dst)

def make_glass(display):
    w = h = 64; dst = blank(w, h); X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 0, w, h, 16); m = cov(sdf)
    paint(dst, m * (0.08 + (0.02 - 0.08) * Y / h), hexc(WH))     # white 8% -> 2% (vertical in the texture, stretches with it)
    if display:
        e = np.minimum(np.minimum(X, w - X), np.minimum(Y, h - Y))
        paint(dst, m * 0.07 * (1 - phi(e / 4.0)) * np.clip(1 - e / 14, 0, 1) * 2, hexc(CY))  # faint cyan inner glow, <= 14 px
    inner = cov(rrect_sdf(X, Y, 1, 1, w - 1, h - 1, 15)); inner_dn = cov(rrect_sdf(X, Y, 1, 2, w - 1, h - 1, 15))
    paint(dst, np.clip(inner - inner_dn, 0, 1) * 0.14, hexc(WH))   # inset 0 1px 0 rgba(255,255,255,.14)
    paint(dst, ringmask(sdf, 1) * 0.22, hexc(CY)); return down(dst)

K = 44 / 32  # orb canvas shown at 44 px
def make_orb(kind):
    w = h = 32; dst = blank(w, h); X, Y = grid(w, h)
    r = 13 / K; dist = np.hypot(X - 16, Y - 16) - r; bw = 1.0
    if kind == "hover": paint(dst, soft(dist, 2.3, 0.5, 6), hexc(CY))
    if kind == "on":
        paint(dst, soft(dist, 2.6, 0.7, 6), hexc(CY))
        paint(dst, ((dist >= 0) & (dist < 4 / K)) * 0.12, hexc(CY))
    if kind == "on":
        t = np.clip(np.hypot(X - 16, Y - 16) / (r * 2 ** 0.5), 0, 1); fill = lerp_stops(t, [(0, "#22305a"), (1, ORB)])
    else: fill = hexc(ORB)
    paint(dst, cov(dist), fill)
    ring_a, ring_c = (0.5, MU) if kind == "normal" else (1.0, CY)
    paint(dst, ((dist < 0) & (dist >= -bw)) * ring_a, hexc(ring_c))
    if kind == "on":                       # dashed ring at +7 px (board inset -7 px), 1 px dashed cyan .55
        R = (13 + 7) / K; th = np.arctan2(Y - 16, X - 16) % (2 * np.pi); per = 2 * np.pi * R / 21
        dash = ((th * R) % per) < per / 2
        paint(dst, (np.abs(np.hypot(X - 16, Y - 16) - R) < bw / 2) * dash * 0.55, hexc(CY))
    return down(dst)

def make_link(fade=False):
    w, h = 8, 64; dst = blank(w, h); X, Y = grid(w, h)
    a = (1 - 0.85 * Y / h) if fade else 0.35
    paint(dst, ((X >= 3) & (X < 5)) * 0.5 * a, hexc(CY)); return down(dst)

def make_button(kind):
    w, h = 128, 32; dst = blank(w, h); X, Y = grid(w, h)
    x0, y0, x1, y1 = 3, 3, w - 3, h - 3
    sd = rrect_sdf(X, Y, x0, y0, x1, y1, 12); m = cov(sd)
    if kind in ("primary", "primary_hover"):
        paint(dst, soft(np.hypot(np.maximum(0, sd), 0), 2.0, 0.55 if kind == "primary_hover" else 0.45, 3.2) * (np.where(Y > 16, 1.0, 0.8)), hexc(VI))
        L = (x1 - x0 + y1 - y0) * 0.7071; t = np.clip(((X - 64) * 0.7071 + (Y - 16) * 0.7071) / L + 0.5, 0, 1)
        g = lerp_stops(t, [(0, VI), (1, BL)])
        if kind == "primary_hover": g = np.minimum(g * 1.1, 255)
        paint(dst, m, g); return down(dst)
    if kind == "hover":
        paint(dst, soft(np.maximum(sd, -1) + 0 * sd, 1.8, 0.35, 3.2), hexc(CY))
        dx = np.minimum(X - x0, x1 - X); dy = np.minimum(Y - y0, y1 - Y)
        ins = np.where(dx >= 12, 1.0, phi(dx / 4)) * phi(dy / 4)
        paint(dst, m * 0.12 * (1 - ins), hexc(CY))
    paint(dst, m * 0.06, hexc(WH))
    paint(dst, ringmask(sd, 1) * (1.0 if kind == "hover" else 0.38), hexc(CY))
    img = down(dst)
    if kind == "disabled":
        a = np.asarray(img, float); a[..., 3] *= 0.4; img = Image.fromarray(np.round(a).astype(np.uint8), "RGBA")
    return img

def make_check(on):
    w = h = 32; dst = blank(w, h); X, Y = grid(w, h); dist = np.hypot(X - 16, Y - 16) - 10
    if on:
        paint(dst, soft(dist, 2.4, 0.6, 6), hexc(CY))
        t = np.hypot(X - 16, Y - 16) / (10 * 2 ** 0.5)
        a = np.where(t < 0.30, 1.0, np.where(t < 0.34, 1 - (1 - 0.15 / 1.0) * (t - 0.30) / 0.04, 0.15))
        paint(dst, cov(dist) * a, hexc(CY))
    else: paint(dst, cov(dist) * 0.05, hexc(WH))
    paint(dst, ((dist < 0) & (dist >= -1)) * (1.0 if on else 0.6), hexc(CY if on else MU)); return down(dst)

def make_switch(on):
    w, h = 64, 32; dst = blank(w, h); X, Y = grid(w, h); sd = rrect_sdf(X, Y, 0, 0, w, h, 16); m = cov(sd); bw = 1.52
    if on:
        t = X / w
        va = 0.5 + (0.4 - 0.5) * t; col = lerp_stops(t, [(0, VI), (1, CY)])
        paint(dst, m * va, col)
    else: paint(dst, m * 0.06, hexc(WH))
    paint(dst, ringmask(sd, bw) * (1.0 if on else 0.5), hexc(CY if on else MU)); return down(dst)

def make_knob(on):
    w = h = 32; dst = blank(w, h); X, Y = grid(w, h); r = 11.5; dist = np.hypot(X - 16, Y - 16) - r
    if on: paint(dst, soft(dist, 2.0, 0.8, 4.5), hexc(CY))
    D = 2 * r; cx, cy = 16 - r + 0.36 * D, 16 - r + 0.28 * D
    t = np.clip(np.hypot(X - cx, Y - cy) / (np.hypot(0.64, 0.72) * D), 0, 1)
    g = lerp_stops(t, [(0, "#ffffff"), (0.2, "#ffffff"), (1, CY)] if on else [(0, "#ffffff"), (1, MU)])
    paint(dst, cov(dist), g); return down(dst)

def make_slider(fill):
    w, h = 128, 16; dst = blank(w, h); X, Y = grid(w, h); sd = rrect_sdf(X, Y, 0, 5, w, 11, 3); m = cov(sd)
    if fill: paint(dst, m, lerp_stops(X / w, [(0, VI), (1, CY)]))
    else:
        paint(dst, np.where(sd > 0, soft(np.maximum(sd, 0), 2.0, 0.15, 5), 0), hexc(CY))   # outer glow 0 0 12px cyan .15, compressed
        paint(dst, m * 0.10, hexc(WH))
    ins = cov(rrect_sdf(X, Y, 0, 5, w, 11, 3)) * (1 - cov(rrect_sdf(X, Y, 0, 6, w, 12, 3)))  # inset 0 1px 2px black .5, top edge
    paint(dst, ins * 0.5 * np.exp(-((Y - 5) / 1.6) ** 2), (0, 0, 0)); return down(dst)

def make_slider_knob():
    w = h = 32; dst = blank(w, h); X, Y = grid(w, h); r = 9.5; dist = np.hypot(X - 16, Y - 16) - r
    paint(dst, soft(dist - 4, 1.4, 0.55, 2.4) * (dist >= 4), hexc(CY))
    paint(dst, ((dist >= 0) & (dist < 4)) * 0.16, hexc(CY))
    D = 2 * r; cx, cy = 16 - r + 0.36 * D, 16 - r + 0.28 * D
    t = np.clip(np.hypot(X - cx, Y - cy) / (np.hypot(0.64, 0.72) * D), 0, 1)
    paint(dst, cov(dist), lerp_stops(t, [(0, "#ffffff"), (0.14, "#ffffff"), (0.38, "#d4ecff"), (0.72, CY), (1, VI)])); return down(dst)

def main(out):
    os.makedirs(out, exist_ok=True)
    f = {"frame": make_frame(), "panel": make_panel(), "glow_violet": make_glow(VI, 0.35), "glow_cyan": make_glow(CY, 0.22),
         "glass": make_glass(False), "display": make_glass(True), "orb_normal": make_orb("normal"), "orb_hover": make_orb("hover"),
         "orb_on": make_orb("on"), "link": make_link(), "link_fade": make_link(True),
         "check_off": make_check(False), "check_on": make_check(True), "switch_off": make_switch(False), "switch_on": make_switch(True),
         "switch_knob_off": make_knob(False), "switch_knob_on": make_knob(True), "slider_track": make_slider(False),
         "slider_fill": make_slider(True), "slider_knob": make_slider_knob()}
    for k in ("normal", "hover", "primary", "primary_hover", "disabled"): f["btn_" + k] = make_button(k)
    for n, im in f.items(): im.save(os.path.join(out, f"frost_{n}.png"))
    print(len(f), "files ->", out)
if __name__ == "__main__": main(sys.argv[1])
