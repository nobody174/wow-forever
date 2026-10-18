"""Draw the 15 Azeroth Reforged slices for the R2F addon.

Colours and shapes are taken from the Azeroth Reforged board in the Design artifact.
Everything is drawn supersampled and downsampled with premultiplied alpha, so edges are smooth.
Usage: python make_azeroth.py <output_dir>
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

S = 6  # supersampling factor


# ---------------------------------------------------------------- helpers
def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def blank(w, h):
    return np.zeros((h * S, w * S, 4))


def grid(w, h):
    xs = (np.arange(w * S) + 0.5) / S
    ys = (np.arange(h * S) + 0.5) / S
    return np.meshgrid(xs, ys)


def paint(dst, mask, rgb):
    """Composite colour rgb (tuple/array or HxWx3) with coverage mask (HxW, 0..1) over dst."""
    rgb = np.asarray(rgb, float)
    if rgb.ndim == 1:
        rgb = np.broadcast_to(rgb, dst.shape[:2] + (3,))
    sa = np.clip(mask, 0, 1)[..., None]
    da = dst[..., 3:4]
    oa = sa + da * (1 - sa)
    out = np.where(oa > 1e-9, (rgb * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-9), 0)
    dst[..., :3] = out
    dst[..., 3:4] = oa


def down(dst):
    h, w = dst.shape[0] // S, dst.shape[1] // S
    a = dst[..., 3:4]
    pm = (dst[..., :3] * a).reshape(h, S, w, S, 3).mean((1, 3))
    aa = a.reshape(h, S, w, S, 1).mean((1, 3))
    rgb = np.where(aa > 1e-6, pm / np.maximum(aa, 1e-6), 0)
    out = np.concatenate([rgb, aa * 255], -1)
    return Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8), "RGBA")


def rrect_sdf(X, Y, x0, y0, x1, y1, r):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
    qx = np.abs(X - cx) - (hw - r)
    qy = np.abs(Y - cy) - (hh - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def vgrad(Y, y0, y1, stops):
    """Vertical gradient. stops = [(t, '#hex'), ...] with t in 0..1 along y0..y1."""
    t = np.clip((Y - y0) / (y1 - y0), 0, 1)
    ts = [s[0] for s in stops]
    out = np.zeros(Y.shape + (3,))
    cols = [hexc(s[1]) for s in stops]
    for c in range(3):
        out[..., c] = np.interp(t, ts, [col[c] for col in cols])
    return out


def poly_mask(w, h, pts):
    img = Image.new("L", (w * S, h * S), 0)
    ImageDraw.Draw(img).polygon([(x * S, y * S) for x, y in pts], fill=255)
    return np.asarray(img, float) / 255.0


def tile_noise(n, sigma, seed):
    """Tileable gaussian-filtered noise (filtered in the frequency domain, so it wraps)."""
    rng = np.random.default_rng(seed)
    f = np.fft.fft2(rng.standard_normal((n, n)))
    fx = np.fft.fftfreq(n)[:, None]
    fy = np.fft.fftfreq(n)[None, :]
    b = np.fft.ifft2(f * np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))).real
    return b / b.std()


# ---------------------------------------------------------------- frame
FRAME_DEPTH = 16
CORNER_R = 20.0


def frame_profile(d):
    """Colour of the frame at inward distance d (px) from its outer edge. Same for strips and corner."""
    rgb = np.zeros(d.shape + (3,))
    a = np.zeros(d.shape)

    def seg(lo, hi, col):
        m = (d >= lo) & (d < hi)
        rgb[m] = hexc(col)
        a[m] = 1.0

    seg(0, 1, "#a9822f")    # outer gold, lit edge
    seg(1, 2, "#8a6a2a")
    seg(2, 4, "#20190c")
    seg(4, 8, "#0d0b07")    # dark border
    seg(8, 9, "#e2bb62")    # inner gold, lit edge
    seg(9, 10, "#b48d38")
    seg(10, 13, "#2a2112")
    m = (d >= 13) & (d < FRAME_DEPTH)  # soft inner shadow into the panel
    rgb[m] = hexc("#2a2112")
    a[m] = 1 - (d[m] - 13) / 3
    return rgb, a


def make_edge_h():
    w, h = 64, 16
    dst = blank(w, h)
    X, Y = grid(w, h)
    rgb, a = frame_profile(Y)
    paint(dst, a, rgb)
    return down(dst)


def make_edge_v():
    w, h = 16, 64
    dst = blank(w, h)
    X, Y = grid(w, h)
    rgb, a = frame_profile(X)
    paint(dst, a, rgb)
    return down(dst)


def make_corner():
    w = h = 64
    dst = blank(w, h)
    X, Y = grid(w, h)
    R = CORNER_R
    d = np.where((X < R) & (Y < R), R - np.hypot(R - X, R - Y), np.minimum(X, Y))
    rgb, a = frame_profile(d)
    paint(dst, a, rgb)
    # empty gem socket: dark recess with a thin gold bezel, clipped to the frame
    cx = cy = 10.0
    r = np.hypot(X - cx, Y - cy)
    inside = (d >= 0).astype(float)
    bezel = ((r >= 6.4) & (r < 7.8)).astype(float) * inside
    # gradient along X+Y only, so the corner stays symmetric about its diagonal (mirror-safe)
    bez_col = vgrad(X + Y, 2 * cx - 11, 2 * cx + 11, [(0, "#f1cf7a"), (0.5, "#c9a24b"), (1, "#6e4a10")])
    paint(dst, bezel, bez_col)
    recess = (r < 6.4).astype(float) * inside
    rec_col = vgrad(r, 0, 6.4, [(0, "#0a0805"), (1, "#241b0c")])
    paint(dst, recess, rec_col)
    return down(dst)


# ---------------------------------------------------------------- gems
def make_gem():
    w = h = 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    cx = cy = 16.0
    half = 14.0
    dia = np.abs(X - cx) + np.abs(Y - cy)
    body = (dia < half).astype(float)
    paint(dst, ((dia >= half - 1.3) & (dia < half)).astype(float), hexc("#2a1a02"))  # dark outline
    inner = (dia < half - 1.3).astype(float)
    col = vgrad(Y, cy - half, cy + half, [(0, "#ffe29a"), (0.55, "#c48a24"), (1, "#8a5a10")])
    paint(dst, inner, col)
    # facets: lit upper-left, shaded lower-right, plus a small specular spot
    upper_left = inner * ((X - cx) + (Y - cy) < 0) * (np.abs(X - cx) + np.abs(Y - cy) < half * 0.62)
    paint(dst, upper_left * 0.22, hexc("#fff6c8"))
    lower_right = inner * ((X - cx) + (Y - cy) > 0) * (np.abs(X - cx) + np.abs(Y - cy) < half * 0.62)
    paint(dst, lower_right * 0.20, hexc("#3a2204"))
    ring = inner * ((dia >= half * 0.62 - 0.5) & (dia < half * 0.62 + 0.5))
    paint(dst, ring * 0.35, hexc("#2a1a02"))
    spec = np.exp(-(((X - 12.5) / 2.6) ** 2 + ((Y - 11.5) / 2.0) ** 2)) * inner
    paint(dst, spec * 0.75, hexc("#fffbe6"))
    return down(dst)


def make_nav_gem(lit):
    w = h = 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    cx = cy = 16.0
    r = np.hypot(X - cx, Y - cy)
    if lit:
        glow = np.clip(1 - (r - 8) / 7.5, 0, 1) ** 2 * 0.55 * (r >= 8)
        paint(dst, glow, hexc("#ff9d2e"))
    ring_col = hexc("#8a5a1a") if lit else hexc("#5b4620")
    paint(dst, ((r >= 8) & (r < 9.3)).astype(float), ring_col)
    core = (r < 8).astype(float)
    if lit:
        t = np.hypot(X - 13.6, Y - 12.8) / 14.0
        stops = [(0, "#fff2b0"), (0.6, "#ff9d2e"), (1, "#a24b00")]
        ts = [s[0] for s in stops]
        cols = [hexc(s[1]) for s in stops]
        col = np.stack([np.interp(np.clip(t, 0, 1), ts, [c[k] for c in cols]) for k in range(3)], -1)
    else:
        col = vgrad(Y, cy - 8, cy + 8, [(0, "#2a2110"), (1, "#4b3b1c")])
        shade = np.clip((cy - Y) / 8, 0, 1) * 0.35  # inset shadow along the top
        col = col * (1 - shade[..., None])
    paint(dst, core, col)
    return down(dst)


# ---------------------------------------------------------------- banner
def make_banner():
    w, h = 256, 64
    dst = blank(w, h)
    X, Y = grid(w, h)
    ox, oy, bw, bh = 1.5, 1.5, 253.0, 61.0  # 1.5 px margin so nothing touches the canvas edge

    def shape(x0, y0, ww, hh):
        return [(x0, y0), (x0 + ww, y0), (x0 + 0.97 * ww, y0 + hh / 2), (x0 + ww, y0 + hh),
                (x0, y0 + hh), (x0 + 0.03 * ww, y0 + hh / 2)]

    outer = poly_mask(w, h, shape(ox, oy, bw, bh))
    paint(dst, outer, vgrad(Y, oy, oy + bh, [(0, "#ffe29a"), (0.55, "#a8761c"), (1, "#6e4a10")]))
    inner = poly_mask(w, h, shape(ox + 4, oy + 4, bw - 8, bh - 8))
    paint(dst, inner, vgrad(Y, oy + 4, oy + bh - 4, [(0, "#2c2418"), (1, "#171108")]))
    # faint warm glow behind the title and a thin lit line along the top of the inner plate
    glow = np.exp(-(((X - w / 2) / 70) ** 2 + ((Y - h / 2) / 16) ** 2)) * inner
    paint(dst, glow * 0.10, hexc("#ffbe50"))
    topline = inner * ((Y >= oy + 4) & (Y < oy + 5))
    paint(dst, topline * 0.22, hexc("#ffecb4"))
    return down(dst)


# ---------------------------------------------------------------- buttons
BTN_STYLES = {
    "normal": dict(grad=("#3d382f", "#2a261f"), border="#0f0c07", hi=0.14, glow=0.0),
    "hover": dict(grad=("#47412f", "#30291c"), border="#0f0c07", hi=0.20, glow=0.0),
    "selected": dict(grad=("#52411f", "#2f2412"), border="#c9a24b", hi=0.22, glow=0.28),
}


def make_button(kind):
    st = BTN_STYLES[kind]
    w, h = 128, 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    body_sdf = rrect_sdf(X, Y, 0, 0, w, h - 1, 4)  # rows 0..30; row 31 is the drop shadow
    shadow = (rrect_sdf(X, Y, 0, 1, w, h, 4) < 0) & (body_sdf >= 0)
    paint(dst, shadow.astype(float), (0, 0, 0))
    paint(dst, (body_sdf < 0).astype(float), hexc(st["border"]))
    inner = (body_sdf < -1).astype(float)
    paint(dst, inner, vgrad(Y, 1, h - 2, [(0, st["grad"][0]), (1, st["grad"][1])]))
    depth = np.clip(-body_sdf - 1, 0, None)
    if st["glow"]:
        paint(dst, inner * st["glow"] * np.clip(1 - depth / 14, 0, 1) ** 1.5, hexc("#ffbe50"))
    paint(dst, inner * ((Y >= 1) & (Y < 2)) * st["hi"], hexc("#ffecb4"))
    return down(dst)


# ---------------------------------------------------------------- slider
def make_slider_track():
    w, h = 128, 16
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 2, w, 14, 6)
    glow = np.clip(1 - sdf / 2, 0, 1) * (sdf >= 0) * 0.16
    paint(dst, glow, hexc("#ffb43c"))
    paint(dst, (sdf < 0).astype(float), hexc("#7a5a22"))
    inner = (sdf < -1).astype(float)
    paint(dst, inner, hexc("#14110c"))
    paint(dst, inner * np.clip(1 - (Y - 3) / 3.5, 0, 1) * 0.75, (0, 0, 0))
    return down(dst)


def make_slider_knob():
    w = h = 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    cx = cy = 16.0
    r = np.hypot(X - cx, Y - cy)
    R = 12.5
    glow = np.clip(1 - (r - R) / 3.5, 0, 1) ** 2 * 0.5 * (r >= R)
    paint(dst, glow, hexc("#ffbe50"))
    paint(dst, (r < R).astype(float), hexc("#5a3a0a"))
    t = np.clip(np.hypot(X - 12.0, Y - 10.0) / 19.0, 0, 1)
    stops = [(0, "#fff8d8"), (0.09, "#fff8d8"), (0.36, "#ffc552"), (1, "#b36a10")]
    ts = [s[0] for s in stops]
    cols = [hexc(s[1]) for s in stops]
    col = np.stack([np.interp(t, ts, [c[k] for c in cols]) for k in range(3)], -1)
    paint(dst, (r < R - 1).astype(float), col)
    return down(dst)


def make_divider():
    w, h = 128, 8
    dst = blank(w, h)
    X, Y = grid(w, h)
    fade = np.clip(1 - X / w, 0, 1)
    t = np.clip(X / w, 0, 1)
    col = np.stack([hexc("#c9a24b")[k] + (hexc("#8a6a2a")[k] - hexc("#c9a24b")[k]) * t for k in range(3)], -1)
    paint(dst, ((Y >= 3) & (Y < 5)).astype(float) * fade, col)
    paint(dst, (((Y >= 2) & (Y < 3)) | ((Y >= 5) & (Y < 6))).astype(float) * fade * 0.2, hexc("#c9a24b"))
    return down(dst)


# ---------------------------------------------------------------- stone tiles
def make_stone(base, amps, seeds, stripes):
    n = 256
    v = (amps[0] * tile_noise(n, 24, seeds[0]) + amps[1] * tile_noise(n, 7, seeds[1])
         + amps[2] * tile_noise(n, 1.6, seeds[2]))
    yy, xx = np.mgrid[0:n, 0:n]
    if stripes:
        v = v + ((xx + yy) % 8 < 3) * 4.0  # diagonal grain, period 8 divides 256 so it tiles
    warm = np.array([1.0, 0.95, 0.82])
    rgb = hexc(base)[None, None, :] + v[..., None] * warm[None, None, :]
    rgba = np.concatenate([np.clip(rgb, 0, 255), np.full((n, n, 1), 255.0)], -1)
    return Image.fromarray(np.round(rgba).astype(np.uint8), "RGBA")


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    files = {
        "azeroth_corner.png": make_corner(),
        "azeroth_edge_h.png": make_edge_h(),
        "azeroth_edge_v.png": make_edge_v(),
        "azeroth_gem.png": make_gem(),
        "azeroth_banner.png": make_banner(),
        "azeroth_panel.png": make_stone("#2f2b23", (5.0, 4.0, 2.2), (11, 12, 13), True),
        "azeroth_inset.png": make_stone("#19160f", (3.0, 2.5, 1.5), (21, 22, 23), False),
        "azeroth_btn_normal.png": make_button("normal"),
        "azeroth_btn_hover.png": make_button("hover"),
        "azeroth_btn_selected.png": make_button("selected"),
        "azeroth_gem_off.png": make_nav_gem(False),
        "azeroth_gem_on.png": make_nav_gem(True),
        "azeroth_slider_track.png": make_slider_track(),
        "azeroth_slider_knob.png": make_slider_knob(),
        "azeroth_divider.png": make_divider(),
    }
    for name, img in files.items():
        img.save(os.path.join(out_dir, name), "PNG")
        print(name, img.size)


if __name__ == "__main__":
    main(sys.argv[1])
