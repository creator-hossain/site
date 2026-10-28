# -*- coding: utf-8 -*-
"""Corolla Cross edit in the style of reference #9 (dark talk show, frosted-glass list, object rain, selection lower third).

Measured from the reference (720x1296, 30 fps):
  * opens from black through a heavy blur (0.2 -> 0.4 s)
  * FROSTED GLASS BOXES stack into a list: each pops as a small square in the centre, stretches sideways
    (~0.1 s), then a white line icon fades in and the word (Exo-2-like bold techno caps, white -> steel gradient)
    types letter by letter (~0.05 s / letter). Every pop is also a ZOOM CUT (punch in / out); the boxes scale
    with the picture. Slow push-in between cuts.
  * pink -> orange light leak, cut, objects (taka notes) rain in front of the speaker with an orange flash,
    then a dip to black and the speaker comes back darker
  * lower third = a design-tool selection: blue gradient bar with a dashed white frame, white corner handles and a
    blue cursor; first word fades in as the bar stretches, second word rises in, an object (cash fan) rises from
    behind the bar, white Bengali words pop below as spoken; fade to black
usage: compose_v9.py SRC TRACK WORDS CARDIR OUT [--preview t,..]
"""
import sys, os, json, subprocess, math
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, TRACK, WORDS, CARDIR, OUT = sys.argv[1:6]
PREVIEW = sys.argv[7].split(",") if len(sys.argv) > 7 and sys.argv[6] == "--preview" else None
FPS, SRC_FPS = 50, 25
W, H = 720, 1280
SW, SH = 720, 1280
F8 = os.path.join(HERE, "..", "fonts8")
EXO8, EXO9 = f"{F8}/exo2-800.ttf", f"{F8}/exo2-900.ttf"
HB5 = f"{F8}/hind-siliguri-bengali-500-normal.ttf"; HL5 = f"{F8}/hind-siliguri-latin-500-normal.ttf"
ICONS = os.path.join(HERE, "icons")

TR = json.load(open(TRACK)); HX, HTOP, HW = (np.array(TR[k], float) for k in ("hx", "htop", "hw")); SHOT, SHOTS = TR["shot"], TR["shots"]
NSRC = len(HX); DUR = NSRC / SRC_FPS
def _smooth(v, k=11):
    out = v.copy()
    for a, b, _ in SHOTS:
        i0, i1 = int(a * SRC_FPS), min(NSRC, int(b * SRC_FPS))
        if i1 - i0 > k: out[i0:i1] = np.convolve(np.pad(v[i0:i1], k // 2, mode="edge"), np.ones(k) / k, "valid")
    return out
HX, HTOP = _smooth(HX), _smooth(HTOP)
ZSHOT = {}
for k_, (a, b, m) in enumerate(SHOTS):
    hw_ = HW[int(a * SRC_FPS):min(NSRC, int(b * SRC_FPS))]
    ZSHOT[k_] = max(1.0, 118 / float(np.median(hw_))) if m == "T" and len(hw_) else 1.0

WT = {}
for w in json.load(open(WORDS, encoding="utf-8")): WT.setdefault(w["w"], []).append(w["t"])
def wt(w, n=0): return WT[w][n]
CUES = []
def cue(sound, t, gain=0.0, **kw): CUES.append(dict(sound=sound, t=round(t, 3), gain=gain, **kw))

def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def ei2(p): p = clamp(p, 0, 1); return p * p
def seg(t, a, d): return clamp((t - a) / d, 0, 1)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)

@lru_cache(maxsize=None)
def font(path, size): return ImageFont.truetype(path, size)
def place(dst, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0):
    if alpha <= 0.004: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.996:
        a = (np.asarray(im.getchannel("A"), np.float32) * alpha).astype(np.uint8); im = im.copy(); im.putalpha(Image.fromarray(a))
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 > x0 and y1 > y0: dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))
def grad_fill(m, c0, c1):
    k = np.linspace(0, 1, m.height)[:, None, None]; g = (np.array(c0) * (1 - k) + np.array(c1) * k).astype(np.uint8)
    out = Image.fromarray(np.concatenate([np.repeat(g, m.width, 1), np.full((m.height, m.width, 1), 255, np.uint8)], 2)); out.putalpha(m); return out

# ================================================================ glass list
@lru_cache(maxsize=None)
def icon(name, size):
    im = Image.open(f"{ICONS}/{name}.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    return grad_fill(im.getchannel("A"), (250, 252, 255), (150, 185, 230))

@lru_cache(maxsize=None)
def glyph_word(txt, size):
    """techno caps word, white -> steel gradient, soft dark drop; returns per-letter x offsets too."""
    f = font(EXO8, size); asc, desc = f.getmetrics(); pad = 10
    w = int(f.getlength(txt)) + 2 * pad; h = asc + desc + 2 * pad
    xs = [pad + f.getlength(txt[:i]) for i in range(len(txt) + 1)]
    return f, w, h, xs, pad + asc

@lru_cache(maxsize=None)
def word_upto(txt, size, n, last_a):
    f, w, h, xs, base = glyph_word(txt, size)
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    for i in range(n):
        d.text((xs[i], base), txt[i], font=f, fill=255 if i < n - 1 else int(255 * last_a / 8), anchor="ls")
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (10, 18, 35, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.55)))
    out.alpha_composite(sh, (0, 0)); out.alpha_composite(sh, (0, 0)); out.alpha_composite(grad_fill(m, (255, 255, 255), (196, 208, 228)))
    return out

BOX_H, BOX_GAP, BOX_TOP = 108, 26, 540
def box_w(txt, size): return int(min(530, max(380, 30 + 86 + glyph_word(txt, size)[1] + 26)))
def fit_size(txt):
    s = 66
    while glyph_word(txt, s)[1] > 380 and s > 36: s -= 2
    return s

def frosted(img, blurred, x0, y0, w, h, alpha=1.0):
    """frosted glass panel: blurred picture, lifted + cooled, white rim, light top sheen, soft shadow."""
    x0, y0, w, h = int(x0), int(y0), int(w), int(h)
    if w < 4 or h < 4: return
    r = min(int(h * 0.2), w // 2)
    sh = Image.new("L", (w + 40, h + 40), 0); ImageDraw.Draw(sh).rounded_rectangle([20, 26, w + 19, h + 25], r, fill=int(120 * alpha))
    shc = Image.new("RGBA", sh.size, (0, 0, 0, 0)); shc.putalpha(sh.filter(ImageFilter.GaussianBlur(10))); img.alpha_composite(shc, (x0 - 20, y0 - 20)) if x0 >= 20 and y0 >= 20 else place(img, shc, x0 + w / 2, y0 + h / 2 + 6)
    bx0, by0, bx1, by1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if bx1 <= bx0 or by1 <= by0: return
    reg = np.asarray(blurred.crop((bx0, by0, bx1, by1)).convert("RGB"), np.float32)
    k = np.linspace(0, 1, by1 - by0)[:, None, None]
    reg = reg * 0.50 + np.array([118, 134, 162], np.float32) * (0.36 + 0.10 * (1 - k))
    panel = Image.fromarray(np.clip(reg, 0, 255).astype(np.uint8)).convert("RGBA")
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=int(255 * alpha))
    panel.putalpha(m.crop((bx0 - x0, by0 - y0, bx1 - x0, by1 - y0))); img.alpha_composite(panel, (bx0, by0))
    rim = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(rim)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, outline=(235, 242, 255, int(150 * alpha)), width=2)
    d.rounded_rectangle([3, 3, w - 4, h - 4], r - 2, outline=(255, 255, 255, int(40 * alpha)), width=1)
    place(img, rim, x0 + w / 2, y0 + h / 2)

LISTS = [   # (t_end, items: (t_pop, text, icon))
    (9.15, [(2.00, "CHITTAGONG", "map-pin"), (3.35, "COROLLA CROSS", "car-front"), (7.60, "READY STOCK", "package-check")]),
    (23.80, [(17.25, "ZVG13", "car"), (18.50, "2023 MODEL", "calendar-check"), (21.25, "TWO-TONE", "palette"), (22.55, "MODELLISTA KIT", "sparkles")]),
    (27.24, [(25.00, "AUTO PARKING", "parking-square"), (26.00, "360 CAMERA", "camera")]),
    (31.64, [(27.30, "ALLOY WHEELS", "disc-3"), (28.00, "FOG LIGHTS", "lightbulb"), (28.75, "SEAT HEATER", "thermometer-sun"), (29.80, "CRUISE CONTROL", "gauge")]),
    (35.64, [(32.70, "33,000 KM", "gauge-circle"), (34.60, "GRADE 4", "award")]),
]

def draw_list(img, blurred, items, t, K):
    kz, cx, cy = K
    def T(x, y): return cx + (x - cx) * kz, cy + (y - cy) * kz
    for i, (tp, txt, ic) in enumerate(items):
        if t < tp: continue
        size = fit_size(txt); bw = box_w(txt, size); y = BOX_TOP + i * (BOX_H + BOX_GAP)
        p_sq = seg(t, tp, 0.07); p_w = seg(t, tp + 0.07, 0.12)
        w_now = lerp(BOX_H * 0.62, bw, eo3(p_w)); h_now = lerp(BOX_H * 0.62, BOX_H, eo3(p_sq))
        a = lerp(0.3, 1.0, eo3(p_sq))
        x0, y0 = T(W / 2 - w_now / 2, y + BOX_H / 2 - h_now / 2)
        frosted(img, blurred, x0, y0, w_now * kz, h_now * kz, a)
        if p_w < 0.6: continue
        bl, _ = T(W / 2 - bw / 2, y)
        ia = seg(t, tp + 0.15, 0.08)
        if ia > 0: place(img, icon(ic, int(70 * kz)), bl + (30 + 35) * kz, y0 + BOX_H * kz / 2, alpha=ia)
        nt = (t - (tp + 0.19)) / 0.045
        if nt > 0:
            n = min(len(txt), int(nt) + 1); la = 8 if n == len(txt) and nt >= len(txt) else int(clamp((nt - int(nt)) * 8 + 1, 1, 8))
            wd = word_upto(txt, size, n, la)
            if kz != 1: wd = wd.resize((int(wd.width * kz), int(wd.height * kz)), Image.BICUBIC)
            place(img, wd, bl + (116 - 10) * kz + wd.width / 2, y0 + BOX_H * kz / 2 + 2 * kz)

# ================================================================ lower third (selection box)
EXOC = EXO8
@lru_cache(maxsize=None)
def lt_word(txt, size, col):
    f = font(EXOC, size); asc, desc = f.getmetrics(); w = int(f.getlength(txt)) + 8; h = asc + desc + 8
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((4, 4 + asc), txt, font=f, fill=255, anchor="ls")
    m = m.resize((int(w * 0.9), h), Image.LANCZOS)
    return grad_fill(m, col, tuple(int(c * 0.82) for c in col))
@lru_cache(maxsize=None)
def bn_word(txt, size):
    f = font(HB5 if any("ঀ" <= c <= "৿" for c in txt) else HL5, size); asc, desc = f.getmetrics(); pad = 12
    w = int(f.getlength(txt)) + 2 * pad; h = asc + desc + 2 * pad
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad, pad + asc), txt, font=f, fill=255, anchor="ls")
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.7)))
    out.alpha_composite(sh); fl = Image.new("RGBA", (w, h), (250, 250, 250, 255)); fl.putalpha(m); out.alpha_composite(fl); return out, f.getlength(txt), pad
def cursor_img():
    im = Image.new("RGBA", (60, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(6, 6), (50, 24), (30, 30), (22, 52)]; d.polygon(pts, fill=(64, 140, 236, 255), outline=(255, 255, 255, 255)); return im
CURSOR = cursor_img()

def load_car(name, flip, width):
    c = Image.open(os.path.join(CARDIR, f"cut_u2net_car_{name}.png")).convert("RGBA"); a = np.asarray(c.getchannel("A"), np.float32)
    c.putalpha(Image.fromarray((np.clip((a - 70) / 185, 0, 1) * 255).astype(np.uint8))); c = c.crop(c.getbbox())
    if flip: c = c.transpose(Image.FLIP_LEFT_RIGHT)
    return c.resize((width, int(c.height * width / c.width)), Image.LANCZOS)

LTS = [   # (t_in, t_out, word1 (t), word2 (t), behind object, subtitle words)
    dict(t0=10.95, t1=15.30, w1=("PEARL", 11.14), w2=("& BLACK", wt("ব্ল্যাক")), obj=load_car("16.4", False, 330),
         sub=[("দুইটাই", wt("দুইটাই")), ("অ্যাভেলেবল", wt("অ্যাভেলেবল", 1))]),
    dict(t0=37.62, t1=99.0, w1=("PABNA", 37.75), w2=("SHOWROOM", 38.05), obj=load_car("29.0", False, 330),
         sub=[("আব্দুল", wt("আব্দুল")), ("হামিদ", wt("হামিদ")), ("রোড", wt("রোড")), ("পাবনা", wt("পাবনা")), ("সদর", wt("সদর"))]),
]
LT_Y, LT_H, LT_X0, LT_W = 812, 104, 78, 564

def draw_lt(img, L, t):
    if not (L["t0"] <= t < L["t1"]): return
    pb = seg(t, L["t0"], 0.28); x0 = LT_X0; w = LT_W * eo3(pb); y0 = LT_Y
    if w < 3: return
    w2t = L["w2"][1]; po = seg(t, w2t - 0.05, 0.45)
    if po > 0:   # object rises from behind the bar
        ob = L["obj"]; rise = eo3(po); visible = int(ob.height * 0.62 * rise)
        if visible > 2:
            crop = ob.crop((0, 0, ob.width, visible))
            img.alpha_composite(crop, (int(W / 2 + 30 - ob.width / 2), int(y0 + 18 - visible)))
    bar = np.zeros((LT_H, int(w), 4), np.uint8); kx = np.linspace(0, 1, int(w))[None, :]; ky = np.linspace(0, 1, LT_H)[:, None]
    bar[..., 0] = (34 + 30 * kx - 10 * ky).astype(np.uint8); bar[..., 1] = (70 + 40 * kx - 20 * ky).astype(np.uint8)
    bar[..., 2] = (128 + 40 * kx - 30 * ky).astype(np.uint8); bar[..., 3] = 238
    img.alpha_composite(Image.fromarray(bar), (x0, y0))
    tx = x0 + 24
    a1 = seg(t, L["w1"][1] - 0.05, 0.2)
    if a1 > 0:
        im = lt_word(L["w1"][0], 62, (250, 252, 255)); bw_ = im.width
        layer = Image.new("RGBA", (int(w), LT_H), (0, 0, 0, 0)); layer.alpha_composite(im, (24, int(LT_H / 2 - im.height / 2 + 18 * (1 - eo3(a1)))))
        a = (np.asarray(layer.getchannel("A"), np.float32) * eo3(a1)).astype(np.uint8); layer.putalpha(Image.fromarray(a)); img.alpha_composite(layer, (x0, y0))
        a2 = seg(t, w2t, 0.18)
        if a2 > 0:
            im2 = lt_word(L["w2"][0], 54, (205, 218, 238)) if a2 < 1 else lt_word(L["w2"][0], 54, (232, 238, 250))
            layer = Image.new("RGBA", (int(w), LT_H), (0, 0, 0, 0)); layer.alpha_composite(im2, (24 + bw_ + 6, int(LT_H / 2 - im2.height / 2 + 6 + 40 * (1 - eo3(a2)))))
            a = (np.asarray(layer.getchannel("A"), np.float32) * eo3(a2)).astype(np.uint8); layer.putalpha(Image.fromarray(a)); img.alpha_composite(layer, (x0, y0))
    if pb >= 1:   # dashed selection frame + corner handles + cursor
        d = ImageDraw.Draw(img); x1, y1 = x0 + LT_W, y0 + LT_H
        for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x0, y1, x1, y1), (x0, y0, x0, y1), (x1, y0, x1, y1)):
            L_ = math.hypot(bx - ax, by - ay); n = int(L_ / 10)
            for k in range(n):
                if k % 2 == 0:
                    p0, p1 = k / n, min(1, (k + 1) / n); d.line([(ax + (bx - ax) * p0, ay + (by - ay) * p0), (ax + (bx - ax) * p1, ay + (by - ay) * p1)], fill=(240, 245, 255, 230), width=2)
        for (hx, hy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            d.rectangle([hx - 6, hy - 6, hx + 6, hy + 6], fill=(255, 255, 255, 255), outline=(60, 110, 190, 255))
    pc = seg(t, L["t0"] - 0.3, 0.6)
    if pc > 0: place(img, CURSOR, lerp(W + 40, x0 + LT_W + 22, eo3(pc)), lerp(y0 + LT_H + 80, y0 + LT_H + 26, eo3(pc)))
    for (wd, tt) in L["sub"]:
        pass
    # subtitle words below the bar, centred line, each pops as spoken
    words = L["sub"]; size = 50
    ims = [bn_word(w_, size) for w_, _ in words]; sp = font(HB5, size).getlength(" ")
    tot = sum(a for _, a, _ in ims) + sp * (len(ims) - 1); x = W / 2 - tot / 2; yy = y0 + LT_H + 62
    for (im, adv, pad), (_, tt) in zip(ims, words):
        q = seg(t, tt, 0.16)
        if q > 0: place(img, im, x + adv / 2, yy + 14 * (1 - eo3(q)), alpha=eo3(q))
        x += adv + sp

# ================================================================ key rain
def make_key():
    """remote car key: metal blade with notches on top, black glossy fob with chrome rim and three buttons."""
    S = 2; w, h = 120, 300; im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bl = Image.new("L", im.size, 0); bd = ImageDraw.Draw(bl)
    bd.rectangle([w * S / 2 - 13 * S, 8 * S, w * S / 2 + 13 * S, 130 * S], fill=255)
    for k in range(5): bd.polygon([(w * S / 2 + 13 * S, (24 + k * 20) * S), (w * S / 2 + 4 * S, (32 + k * 20) * S), (w * S / 2 + 13 * S, (40 + k * 20) * S)], fill=0)
    bd.polygon([(w * S / 2 - 13 * S, 8 * S), (w * S / 2 + 13 * S, 8 * S), (w * S / 2 + 13 * S, 20 * S)], fill=0)
    im.alpha_composite(grad_fill(bl, (238, 240, 244), (150, 156, 166)))
    d.line([(w * S / 2 - 2 * S, 14 * S), (w * S / 2 - 2 * S, 126 * S)], fill=(120, 126, 136, 255), width=3 * S)
    body = Image.new("L", (w * S, 175 * S), 0); ImageDraw.Draw(body).rounded_rectangle([0, 0, w * S - 1, 175 * S - 1], 40 * S, fill=255)
    im.alpha_composite(grad_fill(body, (62, 64, 72), (12, 12, 16)), (0, 120 * S))
    d.rounded_rectangle([2 * S, 122 * S, w * S - 3 * S, 293 * S], 39 * S, outline=(175, 180, 192, 255), width=3 * S)
    hl = Image.new("L", im.size, 0); ImageDraw.Draw(hl).ellipse([14 * S, 128 * S, 60 * S, 210 * S], fill=80)
    hlc = Image.new("RGBA", im.size, (255, 255, 255, 0)); hlc.putalpha(hl.filter(ImageFilter.GaussianBlur(10 * S))); im.alpha_composite(hlc)
    for k, ic in enumerate(("lock", "unlock", "car")):
        cy = (160 + k * 42) * S; d.rounded_rectangle([w * S / 2 - 30 * S, cy - 16 * S, w * S / 2 + 30 * S, cy + 16 * S], 13 * S, fill=(34, 36, 42, 255), outline=(96, 100, 110, 255), width=2 * S)
        place(im, icon(ic, 22 * S), w * S / 2, cy)
    d.ellipse([w * S / 2 - 7 * S, 274 * S, w * S / 2 + 7 * S, 288 * S], outline=(175, 180, 192, 255), width=2 * S)
    return im.resize((w, h), Image.LANCZOS)
KEY = make_key()
RAIN_T0, RAIN_T1 = 35.64, 37.20
_rng = np.random.default_rng(9)
DROPS = []
for i in range(32):
    s = float(_rng.uniform(0.3, 0.85)) if i % 7 else float(_rng.uniform(1.2, 1.6))
    DROPS.append(dict(ts=float(_rng.uniform(RAIN_T0 - 0.7, RAIN_T1 - 0.35)), x=float(_rng.uniform(-40, W + 40)), s=s,
                      v=float(700 + 520 * s + _rng.uniform(-80, 80)), a0=float(_rng.uniform(-40, 40)), w_=float(_rng.uniform(-140, 140)),
                      f0=float(_rng.uniform(0, 6.28)), fw=float(_rng.uniform(4, 9))))
DROPS.sort(key=lambda d_: d_["s"])
@lru_cache(maxsize=64)
def key_scaled(sq):
    return KEY.resize((max(2, int(KEY.width * sq / 100)), max(2, int(KEY.height * sq / 100))), Image.BICUBIC)
def draw_rain(img, t):
    if not (RAIN_T0 <= t < RAIN_T1 + 0.05): return
    for d_ in DROPS:
        dt = t - d_["ts"]; y = -220 * d_["s"] + d_["v"] * dt + 260 * dt * dt
        if y < -300 or y > H + 300: continue
        im = key_scaled(int(d_["s"] * 100)); fx = abs(math.cos(d_["f0"] + d_["fw"] * dt)) * 0.85 + 0.15
        im = im.resize((max(2, int(im.width * fx)), im.height), Image.BICUBIC)
        if d_["s"] > 1.2: im = im.filter(ImageFilter.GaussianBlur(2.2))
        place(img, im, d_["x"] + 30 * math.sin(dt * 2 + d_["f0"]), y, angle=d_["a0"] + d_["w_"] * dt)

# ================================================================ camera / punch zooms / grade
PUNCH = [(0.0, 1.0)]
for t_end, items in LISTS:
    for k, (tp, *_r) in enumerate(items): PUNCH.append((tp, 1.30 if k % 2 == 0 else 1.0))
    PUNCH.append((t_end, 1.0))
PUNCH += [(10.95, 1.12), (15.40, 1.0), (RAIN_T0, 0.94), (37.40, 1.16)]
PUNCH.sort()
def punch(t):
    k, t0 = 1.0, 0.0
    for tt, kk in PUNCH:
        if tt <= t: k, t0 = kk, tt
    return k * (1 + min(0.06, 0.016 * (t - t0)))

@lru_cache(maxsize=8)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
def cam(si, t, kp):
    k = SHOT[si]; a, b, mode = SHOTS[k]
    if mode == "T":
        z = ZSHOT[k] * kp; cw, ch = W / z, H / z
        x0 = clamp(HX[si] - (W / 2) / z, 0, SW - cw); y0 = clamp(HTOP[si] - lerp(250, 150, (kp - 1) / 0.3) / z, 0, SH - ch)
    else:
        z = kp; cw, ch = W / z, H / z; x0 = (SW - cw) / 2; y0 = (SH - ch) / 2
    return src_frame(si).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)), mode

VIG = (1 - 0.55 * np.clip(((_xx - W / 2) / (W * 0.75)) ** 2 + ((_yy - H * 0.45) / (H * 0.62)) ** 2, 0, 1))[..., None]
def grade(img, dark=0.0):
    """moody talk-show look: lifted contrast, cooler shadows, vignette; 'dark' pulls exposure down (after the dip)."""
    a = np.asarray(img, np.float32) / 255
    a = (a - 0.5) * 1.10 + 0.47; g = a.mean(2, keepdims=True); a = g + (a - g) * 0.95
    a = a * np.array([0.95, 0.98, 1.04]) * 0.9 * (VIG * 0.45 + 0.55) * (1 - dark)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

def leak(img, p, flash=False):
    """pink (top-left) -> orange (bottom-right) light leak, screen-blended."""
    if p <= 0: return img
    a = np.asarray(img.convert("RGB"), np.float32)
    k = np.clip((_xx / W * 0.4 + _yy / H * 0.8), 0, 1)[..., None]
    col = np.array([236, 70, 140], np.float32) * (1 - k) + np.array([255, 150, 40], np.float32) * k
    if flash:
        g = np.exp(-(((_xx - W * 0.9) / (W * 0.7)) ** 2 + ((_yy - H * 0.35) / (H * 0.5)) ** 2))[..., None]; col = np.array([255, 150, 50], np.float32) * g
    a = 255 - (255 - a) * (1 - col / 255 * p)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

DIP0, DIP1 = 37.15, 37.40
def render(fi):
    t = fi / FPS; si = min(int(t * SRC_FPS), NSRC - 1); kp = punch(t)
    fr, mode = cam(si, t, kp)
    dark = 0.22 * seg(t, DIP1, 0.01) if t >= DIP1 else 0.0
    img = grade(fr, dark)
    lst = next((L for L in LISTS if L[1][0][0] <= t < L[0]), None)
    if lst is not None:
        blurred = img.filter(ImageFilter.GaussianBlur(14))
        draw_list(img, blurred, lst[1], t, (kp, W / 2, H * 0.55))
    for L in LTS: draw_lt(img, L, t)
    draw_rain(img, t)
    if 35.50 <= t < RAIN_T0: img = leak(img, 0.55 + 0.4 * seg(t, 35.50, 0.14))
    if RAIN_T0 + 0.06 <= t < RAIN_T0 + 0.34: img = leak(img, 0.85 * math.sin(math.pi * seg(t, RAIN_T0 + 0.06, 0.28)), flash=True)
    a = None
    if t < 0.42:              # open from black through blur
        p = seg(t, 0.18, 0.22)
        img = img.filter(ImageFilter.GaussianBlur(26 * (1 - eo3(p)) + 0.01)); a = 0.0 if t < 0.18 else eo3(p)
    elif DIP0 <= t < DIP1 + 0.55:
        a = 1 - seg(t, DIP0, 0.10) if t < DIP1 else eo3(seg(t, DIP1, 0.5))
    elif t > DUR - 0.62:
        a = 1 - seg(t, DUR - 0.62, 0.58)
    if a is not None and a < 1:
        img = Image.fromarray((np.asarray(img.convert("RGB"), np.float32) * a).astype(np.uint8))
    return img.convert("RGB").tobytes()

# ================================================================ sound cues (grammar learned from reference #9)
cue("music", 0.0, dur=round(DUR, 3))
cue("intro", 0.12)
for t_end, items in LISTS:
    for tp, *_r in items: cue("thump", tp - 0.18); cue("click", tp)
cue("burst", 35.36); cue("hit", RAIN_T0 - 0.02); cue("keys", RAIN_T0 + 0.02); cue("dip", DIP0 - 0.08)
for L in LTS:
    cue("boom", L["w1"][1] - 0.1)
    ts = [L["w1"][1] + 0.05 * k for k in range(len(L["w1"][0]))] + [L["w2"][1] + 0.05 * k for k in range(len(L["w2"][0]))] + [tt for _, tt in L["sub"]]
    for x in ts: cue("type", x)

if __name__ == "__main__":
    CUES.sort(key=lambda c: c["t"]); json.dump(CUES, open(OUT.rsplit(".", 1)[0] + "_cues.json", "w"), ensure_ascii=False, indent=0)
    print(len(CUES), "sound cues")
    if PREVIEW:
        for ts in PREVIEW: Image.frombytes("RGB", (W, H), render(int(round(float(ts) * FPS)))).save(f"{OUT}_{ts}.png")
        print("previews:", ", ".join(PREVIEW)); sys.exit(0)
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=6)):
            ff.stdin.write(buf)
            if i % 250 == 0: print(f"  frame {i}/{n}", flush=True)
    ff.stdin.close(); ff.wait(); print("done ->", OUT, "exit", ff.returncode)
