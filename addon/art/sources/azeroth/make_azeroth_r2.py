"""Round 2 of the Azeroth Reforged slices for the R2F addon.

Builds on make_azeroth.py (round 1 helpers). Colours come from the Azeroth Reforged board.
Usage: python make_azeroth_r2.py <output_dir> <path to Cinzel-700.ttf>
"""
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_azeroth as base  # noqa: E402
from make_azeroth import S, blank, down, grid, hexc, paint, rrect_sdf, tile_noise, vgrad  # noqa: E402


# ------------------------------------------------------------ A) corrected frame colours
def frame_profile_r2(d):
    """Exact board colours: gold #8A6A2A outer, #C9A24B inner, near-black #0D0B07 gap. No tinted highlight pixels."""
    rgb = np.zeros(d.shape + (3,))
    a = np.zeros(d.shape)

    def seg(lo, hi, col):
        m = (d >= lo) & (d < hi)
        rgb[m] = hexc(col)
        a[m] = 1.0

    seg(0, 2, "#8a6a2a")
    seg(2, 4, "#20190c")
    seg(4, 8, "#0d0b07")
    seg(8, 10, "#c9a24b")
    seg(10, 13, "#2a2112")
    m = (d >= 13) & (d < base.FRAME_DEPTH)
    rgb[m] = hexc("#2a2112")
    a[m] = 1 - (d[m] - 13) / 3
    return rgb, a


base.frame_profile = frame_profile_r2  # corner and strips in make_azeroth look this name up


def make_banner():
    """Gold edge #FFE29A -> #A8761C -> #6E4A10, plate #2C2418 -> #171108, flat (no glow) so it stays clearly darker."""
    w, h = 256, 64
    dst = blank(w, h)
    X, Y = grid(w, h)
    ox, oy, bw, bh = 1.5, 1.5, 253.0, 61.0

    def shape(x0, y0, ww, hh):
        return [(x0, y0), (x0 + ww, y0), (x0 + 0.97 * ww, y0 + hh / 2), (x0 + ww, y0 + hh),
                (x0, y0 + hh), (x0 + 0.03 * ww, y0 + hh / 2)]

    paint(dst, base.poly_mask(w, h, shape(ox, oy, bw, bh)),
          vgrad(Y, oy, oy + bh, [(0, "#ffe29a"), (0.55, "#a8761c"), (1, "#6e4a10")]))
    paint(dst, base.poly_mask(w, h, shape(ox + 4, oy + 4, bw - 8, bh - 8)),
          vgrad(Y, oy + 4, oy + bh - 4, [(0, "#2c2418"), (1, "#171108")]))
    return down(dst)


def make_stone(base_hex, amps, seeds, stripe):
    n = 256
    v = (amps[0] * tile_noise(n, 24, seeds[0]) + amps[1] * tile_noise(n, 7, seeds[1])
         + amps[2] * tile_noise(n, 1.6, seeds[2]))
    yy, xx = np.mgrid[0:n, 0:n]
    if stripe:
        v = v + ((xx + yy) % 8 < 3) * stripe
    rgb = hexc(base_hex)[None, None, :] + v[..., None] * np.array([1.0, 0.95, 0.82])[None, None, :]
    rgba = np.concatenate([np.clip(rgb, 0, 255), np.full((n, n, 1), 255.0)], -1)
    return Image.fromarray(np.round(rgba).astype(np.uint8), "RGBA")


def phi(z):
    """Normal CDF (logistic approximation), used to reproduce CSS box-shadow blur."""
    return 1.0 / (1.0 + np.exp(-1.702 * z))


BTN_STYLES = {
    "normal": dict(grad=("#3d382f", "#2a261f"), border="#0f0c07", hi=0.34, glow=0.0),
    "hover": dict(grad=("#47412f", "#30291c"), border="#0f0c07", hi=0.42, glow=0.0),
    "selected": dict(grad=("#52411f", "#2f2412"), border="#c9a24b", hi=0.50, glow=0.28),
}


def make_button(kind):
    """Board colours, plus a brighter 1 px top edge with a dark line under it for stronger edge-to-body contrast."""
    st = BTN_STYLES[kind]
    w, h = 128, 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 0, w, h - 1, 4)
    paint(dst, ((rrect_sdf(X, Y, 0, 1, w, h, 4) < 0) & (sdf >= 0)).astype(float), (0, 0, 0))
    paint(dst, (sdf < 0).astype(float), hexc(st["border"]))
    inner = (sdf < -1).astype(float)
    paint(dst, inner, vgrad(Y, 1, h - 2, [(0, st["grad"][0]), (1, st["grad"][1])]))
    if st["glow"]:
        # board: inset 0 0 14px rgba(255,190,80,.28) -> blur sigma 7, strongest at the edge (.14), fading by ~14 px
        dx = np.minimum(X, w - X)
        cover = np.where(dx >= 16, 1.0, phi(dx / 7)) * phi(Y / 7) * phi((h - 1 - Y) / 7)
        paint(dst, inner * st["glow"] * (1 - cover), hexc("#ffbe50"))
    paint(dst, inner * ((Y >= 1) & (Y < 2)) * st["hi"], hexc("#ffecb4"))
    paint(dst, inner * ((Y >= 2) & (Y < 3)) * 0.30, (0, 0, 0))
    return down(dst)


# ------------------------------------------------------------ B) navigation icons (the board's own SVG paths)
ICONS = {
    "home": "M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10",
    "plan": "M4 5l5-2 6 2 5-2v16l-5 2-6-2-5 2zM9 3v16M15 5v16",
    "talents": "M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6-5.4-3-5.4 3 1.2-6-4.5-4.2 6.1-.7z",
    "gear": "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
    "macros": "M4 5h16v14H4zM8 10l3 2-3 2M13 15h4",
    "tweaks": "M4 7h10M18 7h2M4 17h2M10 17h10M14 5v4M6 15v4",
}
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Z": 0}


def parse_path(d):
    toks = re.findall(r"[MmLlHhVvCcZz]|-?\d*\.?\d+", d)
    i, cmd = 0, None
    cur = start = (0.0, 0.0)
    subs, pts = [], []
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                pts.append(start)
                subs.append(pts)
                pts, cur = [], start
                continue
        c, rel = cmd.upper(), cmd.islower()
        vals = [float(t) for t in toks[i:i + ARGS[c]]]
        i += ARGS[c]
        ox, oy = cur if rel else (0.0, 0.0)
        if c == "M":
            if pts:
                subs.append(pts)
            cur = start = (vals[0] + ox, vals[1] + oy)
            pts = [cur]
            cmd = "l" if rel else "L"
        elif c == "L":
            cur = (vals[0] + ox, vals[1] + oy)
            pts.append(cur)
        elif c == "H":
            cur = (vals[0] + ox, cur[1])
            pts.append(cur)
        elif c == "V":
            cur = (cur[0], vals[0] + oy)
            pts.append(cur)
        elif c == "C":
            p0 = cur
            p1, p2, p3 = (vals[0] + ox, vals[1] + oy), (vals[2] + ox, vals[3] + oy), (vals[4] + ox, vals[5] + oy)
            for t in np.linspace(0, 1, 25)[1:]:
                u = 1 - t
                pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
            cur = p3
    if pts:
        subs.append(pts)
    return subs


def make_icon(name, stroke=2.2):
    """Pure white line icon, 32x32, transparent background (the addon tints it)."""
    SS = 8
    k = 32 / 24
    img = Image.new("L", (32 * SS, 32 * SS), 0)
    dr = ImageDraw.Draw(img)
    for sub in parse_path(ICONS[name]):
        p = [(x * k * SS, y * k * SS) for x, y in sub]
        for a, b in zip(p[:-1], p[1:]):
            dr.line([a, b], fill=255, width=int(round(stroke * SS)))
        rr = stroke * SS / 2
        for x, y in p:
            dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    mask = np.asarray(img, float).reshape(32, SS, 32, SS).mean((1, 3))
    out = np.zeros((32, 32, 4))
    out[..., :3] = 255
    out[..., 3] = mask
    return Image.fromarray(np.round(out).astype(np.uint8), "RGBA")


# ------------------------------------------------------------ C) countdown card
def make_card():
    w = h = 128
    dst = blank(w, h)
    X, Y = grid(w, h)
    body = rrect_sdf(X, Y, 0, 0, w, h - 2, 12)  # rows 0..125, rows 126-127 are the drop shadow
    paint(dst, ((rrect_sdf(X, Y, 0, 2, w, h, 12) < 0) & (body >= 0)).astype(float), (0, 0, 0))
    paint(dst, (body < 0).astype(float), hexc("#0b0a07"))
    inner = (body < -1).astype(float)
    paint(dst, inner, vgrad(Y, 1, h - 3, [(0, "#35302a"), (1, "#201c16")]))
    # board: inset 0 -10px 18px rgba(0,0,0,.45) -> sigma 9, the shape shifted up 10 px, so the bottom gets the most
    dx = np.minimum(X, w - X)
    cover = np.where(dx >= 24, 1.0, phi(dx / 9)) * phi((Y + 10) / 9) * phi(((h - 2) - 10 - Y) / 9)
    paint(dst, inner * 0.45 * (1 - cover), (0, 0, 0))
    paint(dst, ((body >= -2) & (body < -1)).astype(float), hexc("#6e5320"))  # thin gold inner line
    return down(dst)


# ------------------------------------------------------------ D) controls
def css_saturate(rgb, s):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.stack([
        (0.213 + 0.787 * s) * r + (0.715 - 0.715 * s) * g + (0.072 - 0.072 * s) * b,
        (0.213 - 0.213 * s) * r + (0.715 + 0.285 * s) * g + (0.072 - 0.072 * s) * b,
        (0.213 - 0.213 * s) * r + (0.715 - 0.715 * s) * g + (0.072 + 0.928 * s) * b], -1)


def make_primary(hover):
    w, h = 128, 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 0, w, h - 1, 4)
    paint(dst, ((rrect_sdf(X, Y, 0, 1, w, h, 4) < 0) & (sdf >= 0)).astype(float), (0, 0, 0))
    paint(dst, (sdf < 0).astype(float), hexc("#0f0c07"))
    paint(dst, ((sdf >= -2) & (sdf < -1)).astype(float), hexc("#fff0b8"))
    inner = (sdf < -2).astype(float)
    paint(dst, inner, vgrad(Y, 2, h - 3, [(0, "#ffd77a"), (1, "#c98a1f")]))
    # board: inset 0 -3px 6px rgba(120,60,0,.4) -> sigma 3, shifted up 3 px
    paint(dst, inner * 0.4 * (1 - phi(((h - 3) - 3 - Y) / 3)), (120, 60, 0))
    if hover:
        dst[..., :3] = np.minimum(dst[..., :3] * 1.15, 255)  # board: filter brightness(1.15)
    return down(dst)


def make_disabled():
    """The board's 'Off' button: the normal stone button with filter saturate(.3) brightness(.8)."""
    w, h = 128, 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 0, w, h - 1, 4)
    paint(dst, ((rrect_sdf(X, Y, 0, 1, w, h, 4) < 0) & (sdf >= 0)).astype(float), (0, 0, 0))
    paint(dst, (sdf < 0).astype(float), hexc("#0f0c07"))
    paint(dst, ((sdf >= -2) & (sdf < -1)).astype(float), hexc("#8a6a2a"))
    inner = (sdf < -2).astype(float)
    paint(dst, inner, vgrad(Y, 2, h - 3, [(0, "#4a443a"), (1, "#2c2821")]))
    paint(dst, inner * ((Y >= 2) & (Y < 3)) * 0.25, hexc("#ffecb4"))
    dst[..., :3] = np.clip(css_saturate(dst[..., :3], 0.3) * 0.8, 0, 255)
    return down(dst)


def make_check(on):
    w = h = 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 4, 4, 28, 28, 4)  # same box for on and off
    paint(dst, (sdf < 0).astype(float), hexc("#8a6a2a"))
    inner = (sdf < -1.5).astype(float)
    paint(dst, inner, vgrad(Y, 5.5, 26.5, [(0, "#16130e"), (1, "#241f16")]))
    paint(dst, inner * 0.7 * (1 - phi((Y - 5.5 - 2.7) / 2.0)), (0, 0, 0))  # board: inset 0 2px 3px rgba(0,0,0,.7)
    if on:
        SS = 8
        img = Image.new("L", (w * SS, h * SS), 0)
        dr = ImageDraw.Draw(img)
        pts = [(9.5 * SS, 16.5 * SS), (13.5 * SS, 20.5 * SS), (22.5 * SS, 11.5 * SS)]
        dr.line(pts, fill=255, width=int(3.4 * SS), joint="curve")
        tick = np.asarray(img.resize((w * S, h * S), Image.BILINEAR), float) / 255.0
        paint(dst, tick, hexc("#ffd77a"))
    return down(dst)


def make_switch_track(on):
    w, h = 64, 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 0, w, h, 16)
    paint(dst, (sdf < 0).astype(float), hexc("#8a6a2a"))
    inner = (sdf < -1.5).astype(float)
    stops = [(0, "#7a4d10"), (1, "#c98a1f")] if on else [(0, "#16130e"), (1, "#241f16")]
    paint(dst, inner, vgrad(Y, 1.5, 30.5, stops))
    paint(dst, inner * 0.7 * (1 - phi((Y - 1.5 - 2.9) / 2.2)), (0, 0, 0))  # board: inset 0 2px 3px rgba(0,0,0,.7)
    return down(dst)


def make_switch_knob():
    """Neutral pearl (the board's off-state knob). The addon can tint it amber for the on state."""
    w = h = 32
    dst = blank(w, h)
    X, Y = grid(w, h)
    r = np.hypot(X - 16, Y - 16)
    paint(dst, (r < 13).astype(float), (0, 0, 0))  # thin dark rim for definition
    t = np.clip(np.hypot(X - 12.1, Y - 10.3) / 25.2, 0, 1)
    c0, c1 = hexc("#e8dcc0"), hexc("#8f836a")
    paint(dst, (r < 12.2).astype(float), c0[None, None, :] + (c1 - c0)[None, None, :] * t[..., None])
    return down(dst)


def make_slider_fill():
    w, h = 128, 16
    dst = blank(w, h)
    X, Y = grid(w, h)
    sdf = rrect_sdf(X, Y, 0, 2, w, 14, 6)
    paint(dst, np.clip(1 - sdf / 2, 0, 1) * (sdf >= 0) * 0.22, hexc("#ffb43c"))
    paint(dst, (sdf < 0).astype(float), hexc("#7a5a22"))
    inner = (sdf < -1).astype(float)
    paint(dst, inner, hexc("#f0b440"))
    paint(dst, inner * 0.75 * (1 - phi((Y - 3 - 2.4) / 1.8)), (0, 0, 0))  # board: inset 0 2px 3px rgba(0,0,0,.75)
    return down(dst)


# ------------------------------------------------------------ E) baked group headings
def make_heading(text, font_path, size=12, spacing=2.4):
    w, h, SS = 128, 16, 8
    font = ImageFont.truetype(font_path, int(size * SS))
    bb = font.getbbox("H")
    y = (h * SS - (bb[3] - bb[1])) / 2 - bb[1]
    img = Image.new("L", (w * SS, h * SS), 0)
    dr = ImageDraw.Draw(img)
    x = 1.0 * SS
    for ch in text:
        dr.text((x, y), ch, font=font, fill=255)
        x += font.getlength(ch) + spacing * SS
    mask = np.asarray(img, float).reshape(h, SS, w, SS).mean((1, 3))
    out = np.zeros((h, w, 4))
    out[..., :3] = hexc("#c9a24b")
    out[..., 3] = mask
    return Image.fromarray(np.round(out).astype(np.uint8), "RGBA")


def main(out_dir, font_path):
    os.makedirs(out_dir, exist_ok=True)
    files = {
        # re-exported (A)
        "azeroth_corner.png": base.make_corner(),
        "azeroth_edge_h.png": base.make_edge_h(),
        "azeroth_edge_v.png": base.make_edge_v(),
        "azeroth_banner.png": make_banner(),
        "azeroth_panel.png": make_stone("#2a261e", (1.4, 2.4, 1.2), (11, 12, 13), 2.0),
        "azeroth_inset.png": make_stone("#16130e", (0.8, 1.5, 0.9), (21, 22, 23), 0),
        "azeroth_btn_normal.png": make_button("normal"),
        "azeroth_btn_hover.png": make_button("hover"),
        "azeroth_btn_selected.png": make_button("selected"),
        # unchanged from round 1
        "azeroth_gem.png": base.make_gem(),
        "azeroth_gem_off.png": base.make_nav_gem(False),
        "azeroth_gem_on.png": base.make_nav_gem(True),
        "azeroth_slider_track.png": base.make_slider_track(),
        "azeroth_slider_knob.png": base.make_slider_knob(),
        "azeroth_divider.png": base.make_divider(),
        # new (B, C, D, E)
        "azeroth_card.png": make_card(),
        "azeroth_btn_primary.png": make_primary(False),
        "azeroth_btn_primary_hover.png": make_primary(True),
        "azeroth_btn_disabled.png": make_disabled(),
        "azeroth_check_off.png": make_check(False),
        "azeroth_check_on.png": make_check(True),
        "azeroth_switch_off.png": make_switch_track(False),
        "azeroth_switch_on.png": make_switch_track(True),
        "azeroth_switch_knob.png": make_switch_knob(),
        "azeroth_slider_fill.png": make_slider_fill(),
        "azeroth_head_journey.png": make_heading("JOURNEY", font_path),
        "azeroth_head_character.png": make_heading("CHARACTER", font_path),
        "azeroth_head_ui.png": make_heading("UI", font_path),
    }
    for n in ICONS:
        files[f"azeroth_icon_{n}.png"] = make_icon(n)
    for name, img in files.items():
        img.save(os.path.join(out_dir, name), "PNG")
    print(len(files), "files written to", out_dir)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
