"""Ember & Iron slices for the R2F addon (24 files). Colours and shapes from the Ember & Iron board.

The board's "cut" shape chamfers the TOP-LEFT and BOTTOM-RIGHT corners only (top-right and bottom-left stay square).
Everything is drawn 1:1 with the board's pixel sizes (tile 64x64, chamfer 8 px, rings 2+1 px).
Usage: python make_ember.py <output_dir>
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_azeroth as base  # noqa: E402
from make_azeroth import S, blank, down, grid, hexc, paint, rrect_sdf, tile_noise, vgrad  # noqa: E402

STEEL, DARK, MID = "#57524c", "#121110", "#3f3b36"
ORANGE, AMBER = "#ff7a2e", "#ffc247"


def phi(z):
    return 1.0 / (1.0 + np.exp(-1.702 * z))


def cut_poly(x0, y0, x1, y1, c):
    """Board clip-path: chamfer on top-left and bottom-right only."""
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]


def cutbox(w, h, c, box=None):
    """Mask of a chamfered box plus the distance (px) from its rectangular edge, as CSS inset box-shadows measure it."""
    x0, y0, x1, y1 = box or (0, 0, w, h)
    X, Y = grid(w, h)
    m = base.poly_mask(w, h, cut_poly(x0, y0, x1, y1, c))
    d = np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - y0, y1 - Y))
    return X, Y, m, d


def edge_cover(X, Y, w, h, sigma, taper):
    """Blur coverage of the box for an inset glow; forced to 1 beyond `taper` px so stretched middles stay plain."""
    dx, dy = np.minimum(X, w - X), np.minimum(Y, h - Y)
    fx = np.where(dx >= taper, 1.0, phi(dx / sigma))
    fy = np.where(dy >= taper, 1.0, phi(dy / sigma))
    return fx * fy


# ------------------------------------------------------------ window parts
def make_frame():
    """128x128 border for a 9-slice with 32 px caps. 3 px dark outline, 3 px steel ring, 4 px top highlight."""
    w = h = 128
    dst = blank(w, h)
    X, Y = grid(w, h)
    outer = base.poly_mask(w, h, cut_poly(0, 0, w, h, 8))
    inner = base.poly_mask(w, h, cut_poly(3, 3, w - 3, h - 3, 8))
    box6 = ((X >= 6) & (X < w - 6) & (Y >= 6) & (Y < h - 6)).astype(float)
    paint(dst, np.clip(outer - inner, 0, 1), hexc("#0c0b0a"))
    paint(dst, inner * (1 - box6), hexc(STEEL))
    paint(dst, inner * box6 * ((Y >= 6) & (Y < 10)), (255, 255, 255) if False else hexc("#ffffff"))
    dst[..., 3] = np.where((inner * box6 > 0) & (Y >= 6) & (Y < 10) & (dst[..., 3] < 1), 0.08, dst[..., 3])
    return down(dst)


def make_panel():
    n = 256
    v = 1.0 * tile_noise(n, 24, 31) + 1.6 * tile_noise(n, 7, 32) + 0.8 * tile_noise(n, 1.6, 33)
    xx = np.mgrid[0:n, 0:n][1]
    v = v + (xx % 4 == 0) * 6.0  # board: repeating 1px vertical lines at 4 px, white 3%
    rgb = hexc("#2a2725")[None, None, :] + v[..., None]
    rgba = np.concatenate([np.clip(rgb, 0, 255), np.full((n, n, 1), 255.0)], -1)
    return Image.fromarray(np.round(rgba).astype(np.uint8), "RGBA")


def make_heat():
    w, h = 128, 16
    dst = blank(w, h)
    X, Y = grid(w, h)
    paint(dst, 0.2 * Y / h, hexc(ORANGE))  # board: transparent -> rgba(255,122,46,.2), constant along x so it tiles
    return down(dst)


def make_rivet():
    w = h = 16
    dst = blank(w, h)
    X, Y = grid(w, h)
    paint(dst, (np.hypot(X - 8, Y - 9) < 4.5).astype(float), (0, 0, 0))  # 0 1px 0 #000
    t = np.clip(np.hypot(X - (3.5 + 0.34 * 9), Y - (3.5 + 0.30 * 9)) / 6.06, 0, 1)
    c0, c1 = hexc("#aaa49a"), hexc("#3b3834")
    paint(dst, (np.hypot(X - 8, Y - 8) < 4.5).astype(float), c0[None, None, :] + (c1 - c0)[None, None, :] * t[..., None])
    return down(dst)


def make_plate():
    w = h = 64
    dst = blank(w, h)
    X, Y, m, d = cutbox(w, h, 8)
    paint(dst, m, hexc("#161412"))
    paint(dst, m * (d < 3), hexc(STEEL))
    paint(dst, m * (d < 2), hexc(DARK))
    return down(dst)


def make_display():
    """Countdown plate. The board's 40 px inner orange glow is compressed into the 16 px caps so the middle stays plain."""
    w = h = 64
    dst = blank(w, h)
    X, Y, m, d = cutbox(w, h, 8)
    paint(dst, m, hexc("#0b0a09"))
    paint(dst, m * 0.14 * (1 - edge_cover(X, Y, w, h, 8, 16)), hexc(ORANGE))
    paint(dst, m * (d < 3), hexc(MID))
    paint(dst, m * (d < 2), hexc(DARK))
    return down(dst)


# ------------------------------------------------------------ nav tiles (64x64, shown 1:1)
def make_slot(kind):
    w = h = 64
    dst = blank(w, h)
    X, Y, m, d = cutbox(w, h, 8)
    if kind == "on":
        paint(dst, m, vgrad(Y, 0, h, [(0, "#3a2a1c"), (1, "#1f1713")]))
        rho = np.hypot(X - 32, Y - 80) / 86.2  # radial-gradient(circle at 50% 125%, rgba(255,122,46,.75), transparent 62%)
        paint(dst, m * 0.75 * np.clip(1 - rho / 0.62, 0, 1), hexc(ORANGE))
        paint(dst, m * 0.5 * (1 - phi(X / 10) * phi((w - X) / 10) * phi(Y / 10) * phi((h - Y) / 10)), hexc(ORANGE))
        paint(dst, m * (d < 2), hexc(ORANGE))
    else:
        stops = [(0, "#3a3733"), (1, "#1f1d1b")] if kind == "normal" else [(0, "#4a3b2c"), (1, "#26201a")]
        paint(dst, m, vgrad(Y, 0, h, stops))
        paint(dst, m * (Y < 4) * 0.07, hexc("#ffffff"))
        paint(dst, m * (d < 3), hexc(STEEL))
        paint(dst, m * (d < 2), hexc(DARK))
    return down(dst)


# ------------------------------------------------------------ buttons (128x32, 16 px caps, chamfer 7)
def make_button(kind):
    w, h = 128, 32
    dst = blank(w, h)
    X, Y, m, d = cutbox(w, h, 7)
    if kind == "primary" or kind == "primary_hover":
        fill = vgrad(Y, 0, h, [(0, "#ffd36a"), (0.62, ORANGE), (1, "#c4480c")])
        ring, top, bottom = "#5a2204", 0.5, 0.0
    elif kind == "disabled":
        fill = hexc("#2a2826")
        ring, top, bottom = DARK, 0.14, 0.45
    else:
        stops = [(0, "#4d4a46"), (1, "#2a2826")] if kind == "normal" else [(0, "#6a4222"), (1, "#2e1d10")]
        fill = vgrad(Y, 0, h, stops)
        ring, top, bottom = DARK, 0.14, 0.45
    paint(dst, m, fill)
    paint(dst, m * (Y < 3) * top, hexc("#ffffff"))  # inset 0 3px 0 rgba(255,255,255,.x)
    if bottom:
        paint(dst, m * (Y >= h - 3) * bottom, (0, 0, 0))  # inset 0 -3px 0 rgba(0,0,0,.45)
    paint(dst, m * (d < 2), hexc(ring))
    if kind == "primary_hover":
        dst[..., :3] = np.minimum(dst[..., :3] * 1.12, 255)  # board: filter brightness(1.12)
    return down(dst)


# ------------------------------------------------------------ check box, switch, slider
def make_check(on):
    w = h = 32
    dst = blank(w, h)
    X, Y, m, d = cutbox(w, h, 5.3, box=(3, 3, 29, 29))  # 26 px box, shown at 24 px
    paint(dst, m, hexc(DARK))
    if on:
        cov = phi((X - 3) / 5.3) * phi((29 - X) / 5.3) * phi((Y - 3) / 5.3) * phi((29 - Y) / 5.3)
        paint(dst, m * 0.6 * (1 - cov), hexc(ORANGE))
    paint(dst, m * (d < 2.7), hexc(ORANGE if on else STEEL))
    if on:
        SS = 8
        img = Image.new("L", (w * SS, h * SS), 0)
        ImageDraw.Draw(img).line([(9.5 * SS, 16.5 * SS), (13.5 * SS, 20.5 * SS), (22.5 * SS, 11.5 * SS)],
                                 fill=255, width=int(4 * SS), joint="curve")
        paint(dst, np.asarray(img.resize((w * S, h * S), Image.BILINEAR), float) / 255.0, hexc(AMBER))
    return down(dst)


def make_switch_track(on):
    w, h = 64, 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 0, w, h, 5.8)
    paint(dst, (sdf < 0).astype(float), hexc(ORANGE if on else STEEL))
    paint(dst, (sdf < -2.9).astype(float), hexc(DARK))
    return down(dst)


def make_switch_knob(on):
    w = h = 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 3, 4.5, 29, 27.5, 4)  # same block for both states, shown at 22 px
    if on:
        paint(dst, np.clip(1 - sdf / 2.6, 0, 1) ** 2 * 0.8 * (sdf >= 0), hexc(ORANGE))
    stops = [(0, "#ffd36a"), (1, ORANGE)] if on else [(0, "#7d776e"), (1, "#4a4640")]
    paint(dst, (sdf < 0).astype(float), vgrad(Y, 4.5, 27.5, stops))
    return down(dst)


def _groove(w, h):
    X, Y = grid(w, h)
    return X, Y, rrect_sdf(X, Y, 0, 2, w, 14, 6)


def make_slider_track():
    w, h = 128, 16
    dst = blank(w, h)
    X, Y, sdf = _groove(w, h)
    paint(dst, np.clip(1 - sdf / 2, 0, 1) * (sdf >= 0) * 0.22, hexc(ORANGE))
    paint(dst, (sdf < 0).astype(float), (0, 0, 0))
    inner = (sdf < -1).astype(float)
    paint(dst, inner, hexc(DARK))
    paint(dst, inner * 0.8 * (1 - phi((Y - 3 - 2) / 2)), (0, 0, 0))
    return down(dst)


def make_slider_fill():
    """Whole gradient baked across the full width (no stretchable middle): #C4480C -> #FF7A2E at 40% -> #FFC247."""
    w, h = 128, 16
    dst = blank(w, h)
    X, Y, sdf = _groove(w, h)
    t = X / w
    cols = [hexc("#c4480c"), hexc(ORANGE), hexc(AMBER)]
    ts = [0, 0.4, 1]
    fill = np.stack([np.interp(t, ts, [c[k] for c in cols]) for k in range(3)], -1)
    paint(dst, (sdf < 0).astype(float), (0, 0, 0))
    inner = (sdf < -1).astype(float)
    paint(dst, inner, fill)
    paint(dst, inner * 0.8 * (1 - phi((Y - 3 - 2) / 2)), (0, 0, 0))
    return down(dst)


def make_slider_knob():
    """The board's 32x22 molten bead, drawn 22x18 so its glow fits inside the 32x32 canvas."""
    w = h = 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 5, 7, 27, 25, 9)
    sh = rrect_sdf(X, Y, 5, 9, 27, 27, 9)
    paint(dst, np.clip(1 - sdf / 4, 0, 1) ** 2 * 0.6 * (sdf >= 0), hexc(ORANGE))
    paint(dst, ((sh < 0) & (sdf >= 0)).astype(float) * 0.5, (0, 0, 0))
    paint(dst, (sdf < 0).astype(float), hexc("#4a1f00"))
    inner = (sdf < -1).astype(float)
    paint(dst, inner, vgrad(Y, 8, 24, [(0, "#fff0c0"), (0.46, "#ffb13a"), (1, "#d9620f")]))
    paint(dst, inner * ((Y >= 8) & (Y < 10)) * 0.75, hexc("#ffffff"))
    return down(dst)


def make_rule():
    w, h = 64, 8
    dst = blank(w, h)
    X, Y = grid(w, h)
    paint(dst, ((Y >= 2.5) & (Y < 5.5)) * np.clip(1 - X / w, 0, 1), hexc(ORANGE))  # linear-gradient(90deg, #ff7a2e, transparent)
    return down(dst)


def main(out):
    os.makedirs(out, exist_ok=True)
    files = {
        "ember_frame.png": make_frame(), "ember_panel.png": make_panel(), "ember_heat.png": make_heat(),
        "ember_rivet.png": make_rivet(), "ember_plate.png": make_plate(), "ember_display.png": make_display(),
        "ember_slot_normal.png": make_slot("normal"), "ember_slot_hover.png": make_slot("hover"),
        "ember_slot_on.png": make_slot("on"),
        "ember_btn_normal.png": make_button("normal"), "ember_btn_hover.png": make_button("hover"),
        "ember_btn_primary.png": make_button("primary"), "ember_btn_primary_hover.png": make_button("primary_hover"),
        "ember_btn_disabled.png": make_button("disabled"),
        "ember_check_off.png": make_check(False), "ember_check_on.png": make_check(True),
        "ember_switch_off.png": make_switch_track(False), "ember_switch_on.png": make_switch_track(True),
        "ember_switch_knob_off.png": make_switch_knob(False), "ember_switch_knob_on.png": make_switch_knob(True),
        "ember_slider_track.png": make_slider_track(), "ember_slider_fill.png": make_slider_fill(),
        "ember_slider_knob.png": make_slider_knob(), "ember_rule.png": make_rule(),
    }
    for n, img in files.items():
        img.save(os.path.join(out, n), "PNG")
    print(len(files), "files written to", out)


if __name__ == "__main__":
    main(sys.argv[1])
