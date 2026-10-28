# -*- coding: utf-8 -*-
"""Full 42s Corolla Cross edit in the style of reference #2 (course promo).

Every text look and motion below was measured frame-by-frame from the reference:
  headline behind the person (fade) . side words (fade) . 2nd headline (blur-in)
  angled word swinging in from vertical . bubble typewriter . white label boxes
  cyan box (wipe w/ overshoot, words blur-fade, exits sliding left) . big white blur-in
  big Latin word (blur-in, exits right) . count-up number (fade + rise) . pill pop
  caption under a card w/ highlighted keyword . card slides in from the right
Transitions: footage folds into a circle / card (words fly outward), card cut-in
(1.25 -> 1.0), shape opens back to full frame, white silhouette flash, light leak.

usage: compose_full.py SRC MATTE TRACK SOURCE_VIDEO OUT [--preview t1,t2,..]
"""
import sys, json, subprocess
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, MAT, TRACK, SRC_VIDEO, OUT = sys.argv[1:6]
PREVIEW = sys.argv[7].split(",") if len(sys.argv) > 7 and sys.argv[6] == "--preview" else None

FPS, SRC_FPS = 50, 25
W, H = 720, 1280
ANEK800 = "/usr/share/fonts/truetype/bnx/AnekBN.ttf"
ANEK700 = "/usr/share/fonts/truetype/bnx/anek-bangla-bengali-700-normal.ttf"
INTER = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
SX = 0.87                                   # reference Bangla glyphs ~87% of Anek's width
WHITE = (255, 255, 255, 255)
INK = (22, 22, 22, 255)
BLUE_OL = (3, 123, 254, 255)                # sampled: headline outline
BLUE_FILL = (1, 158, 254, 255)              # sampled: angled word
BLUE_DEEP = (0, 52, 130, 255)
CYAN = (0, 183, 253, 255)                   # sampled: every cyan box / pill ring
CARD_DARK = (21, 29, 50, 255)               # sampled: course-card header
PURPLE = (104, 75, 235, 255)                # sampled: course-card button
BG_TL, BG_BR = (34, 85, 164), (9, 147, 215) # sampled: blue gradient

_tr = json.load(open(TRACK))
HX, HTOP, HW, SHOT, SHOTS = _tr["hx"], _tr["htop"], _tr["hw"], _tr["shot"], _tr["shots"]
NSRC = len(HX)
DUR = NSRC / SRC_FPS

# ================================================================ helpers
def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def ei3(p): p = clamp(p, 0, 1); return p ** 3
def eoback(p, s=1.7):
    p = clamp(p, 0, 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def seg(t, a, d): return clamp((t - a) / d, 0, 1)
def is_bn(s): return any("ঀ" <= c <= "৿" for c in s)

@lru_cache(maxsize=None)
def font(path, size): return ImageFont.truetype(path, size)

@lru_cache(maxsize=None)
def styled(txt, size, passes, path=ANEK800, sx=SX, shadow_blur=0):
    """Renders txt on a box built from font METRICS (not ink), so words share a baseline.
    passes: ((dx,dy,fill,stroke,stroke_fill),...) back-to-front."""
    f = font(path, size)
    asc, desc = f.getmetrics()
    ms = max(p[3] for p in passes); md = max(max(abs(p[0]), abs(p[1])) for p in passes)
    pad = ms + md + 8 + shadow_blur * 3
    vpad = pad + int(size * 0.18)
    adv = f.getlength(txt)
    w, h = int(adv + 2 * pad), int(asc + desc + 2 * vpad)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for i, (dx, dy, fill, st, sf) in enumerate(passes):
        L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(L).text((pad + dx, vpad + dy), txt, font=f, fill=fill, stroke_width=st, stroke_fill=sf)
        if i == 0 and shadow_blur: L = L.filter(ImageFilter.GaussianBlur(shadow_blur))
        out.alpha_composite(L)
    if sx != 1: out = out.resize((max(1, int(w * sx)), h), Image.LANCZOS)
    out.info["px"] = pad * sx          # image left edge -> pen start
    out.info["adv"] = adv * sx         # advance width
    return out

def wfont(word, heavy=True):
    """Bangla -> Anek (condensed like the reference); Latin/digits -> Inter Display."""
    if is_bn(word): return (ANEK800 if heavy else ANEK700), SX
    return INTER, 1.0

def fit(txt, maxw, maxh, path=ANEK800, sx=SX, hi=320, lo=30):
    for s in range(hi, lo - 1, -4):
        bb = font(path, s).getbbox(txt)
        if (bb[2] - bb[0]) * sx <= maxw and (bb[3] - bb[1]) <= maxh: return s
    return lo

# --- looks
SHADOW = ((0, 3, (0, 0, 0, 165), 0, None), (0, 0, WHITE, 0, None))
def look_white(txt, size, heavy=True, shadow=True):
    p, sx = wfont(txt, heavy)
    return styled(txt, size, SHADOW if shadow else ((0, 0, WHITE, 0, None),), path=p, sx=sx,
                  shadow_blur=5 if shadow else 0)
def look_dark(txt, size, heavy=True):
    p, sx = wfont(txt, heavy); return styled(txt, size, ((0, 0, INK, 0, None),), path=p, sx=sx)
def look_headline(txt, size):
    p, sx = wfont(txt)
    return styled(txt, size, ((5, 6, BLUE_OL, 3, BLUE_OL), (0, 0, WHITE, 2, BLUE_OL)), path=p, sx=sx)
def look_angled(txt, size):
    p, sx = wfont(txt)
    return styled(txt, size, ((5, 8, BLUE_DEEP, 7, BLUE_DEEP), (0, 0, BLUE_FILL, 7, WHITE)), path=p, sx=sx)

def blurred(im, r):
    if r < 0.4: return im
    pad = int(r * 3)
    big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(im, (pad, pad))
    return big.filter(ImageFilter.GaussianBlur(r))

# --- compositing with an optional "fly-out" transform (used while folding into a shape)
XF = {"fly": 1.0, "am": 1.0}
def place(dst, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0, anchor="c"):
    fly = XF["fly"]
    if fly != 1.0:
        if anchor == "l":   # convert to centre so the outward scaling is consistent
            cx = cx + im.width * scale / 2; anchor = "c"
        cx = 360 + (cx - 360) * fly; cy = 640 + (cy - 640) * fly; scale *= fly
    alpha *= XF["am"]
    if alpha <= 0.004: return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.996:
        a = (np.asarray(im.getchannel("A"), np.float32) * alpha).astype(np.uint8)
        im = im.copy(); im.putalpha(Image.fromarray(a))
    x = int(round(cx - im.width / 2)) if anchor == "c" else int(round(cx))
    y = int(round(cy - im.height / 2))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 > x0 and y1 > y0:
        dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def line_layout(imgs, gap):
    """x offsets (pen positions) for word images on one line + total width."""
    xs, x = [], 0.0
    for i, im in enumerate(imgs):
        xs.append(x); x += im.info["adv"] + (gap if i < len(imgs) - 1 else 0)
    return xs, x

def rr(w, h, r, fill, ss=2):
    im = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=fill)
    return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)

# ================================================================ footage / camera
@lru_cache(maxsize=6)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
@lru_cache(maxsize=6)
def src_matte(si): return Image.open(f"{MAT}/f_{si + 1:04d}.png").convert("L")

TARGET_HW = {"full": 155, "circle": 195, "card": 150, "circle2": 175}   # head width on screen
TARGET_HT = {"full": 175, "circle": 350, "card": 250, "circle2": 180}   # head top on screen
BROLL_V = {"full": 640, "circle": 452, "card": 434, "circle2": 330}

def cam_params(si, t, kind):
    k = SHOT[si]; a, b, mode = SHOTS[k]
    push = 1 + min(0.06, 0.006 * (t - a))                    # slow push-in, restarts every shot
    if mode == "T":
        return ("T", TARGET_HW[kind] / HW[si] * push, TARGET_HT[kind])
    return ("B", (1.04 if kind == "full" else 1.12) * push, BROLL_V[kind])

def lerp_params(p0, p1, e): return (p0[0], lerp(p0[1], p1[1], e), lerp(p0[2], p1[2], e))

def camera(si, prm):
    mode, z, v = prm
    cw, ch = W / z, H / z
    if mode == "T":
        x0 = clamp(HX[si] - (W / 2) / z, 0, W - cw); y0 = clamp(HTOP[si] - v / z, 0, H - ch)
    else:                                                    # b-roll: source centre -> (360, v)
        x0 = clamp(360 - (W / 2) / z, 0, W - cw); y0 = clamp(640 - v / z, 0, H - ch)
    box = (x0, y0, x0 + cw, y0 + ch)
    fr = src_frame(si).resize((W, H), Image.LANCZOS, box=box)
    fr = fr.filter(ImageFilter.UnsharpMask(radius=2, percent=60 if z > 1.5 else 35, threshold=2))
    mt = src_matte(si).resize((W, H), Image.BILINEAR, box=box) if mode == "T" else None
    return fr, mt

@lru_cache(maxsize=None)
def head_x_out(k):
    """median on-screen head x for shot k on full-frame framing (for side words)."""
    idx = [i for i in range(NSRC) if SHOT[i] == k]
    a, b, mode = SHOTS[k]
    if mode != "T": return 360.0
    xs = []
    for i in idx[::5]:
        _, z, _ = cam_params(i, a + 1.0, "full")
        x0 = clamp(HX[i] - (W / 2) / z, 0, W - W / z)
        xs.append((HX[i] - x0) * z)
    return float(np.median(xs))

# ================================================================ blue world
def _bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    k = yy / H * 0.75 + xx / W * 0.25
    c = np.stack([BG_TL[i] + (BG_BR[i] - BG_TL[i]) * k for i in range(3)], -1)
    return Image.fromarray(c.clip(0, 255).astype(np.uint8)).convert("RGBA")
BG = _bg()
def _lines():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for x in (150, 570): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 64), width=2)
    for y in (176, 1134): d.line([(0, y), (W, y)], fill=(255, 255, 255, 64), width=2)
    return L
LINES = _lines()

def shape_mask(kind, prm, grow=0.0):
    SS = 2; m = Image.new("L", (W * SS, H * SS), 0); d = ImageDraw.Draw(m)
    if kind.startswith("circle"):
        cx, cy, r = prm; r += grow
        d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=255)
    else:
        x0, y0, x1, y1, rad = prm
        d.rounded_rectangle([(x0 - grow) * SS, (y0 - grow) * SS, (x1 + grow) * SS, (y1 + grow) * SS],
                            radius=max(0, (rad + grow) * SS), fill=255)
    return m.resize((W, H), Image.BOX)

def rings(dst, cx, cy, r, t, alpha):
    size = int((r + 160) * 2); SS = 2
    L = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(L); c = size * SS / 2
    R = (r + 58) * SS
    d.ellipse([c - R, c - R, c + R, c + R], fill=(255, 255, 255, int(42 * alpha)))
    q = (t * 0.85) % 1.0; R2 = (r + 18 + 120 * q) * SS
    d.ellipse([c - R2, c - R2, c + R2, c + R2], outline=(255, 255, 255, int(95 * (1 - q) * alpha)), width=int(5 * SS))
    L = L.resize((size, size), Image.BOX)
    x, y = int(cx - size / 2), int(cy - size / 2)
    dst.alpha_composite(L.crop((max(0, -x), max(0, -y), size, size)), (max(0, x), max(0, y)))

SHAPES = {"circle": (360, 452, 170), "card": (112, 184, 608, 684, 26), "circle2": (360, 330, 185)}
FULL_SHAPE = {"circle": (360, 640, 1000), "circle2": (360, 640, 1000), "card": (0, 0, W, H, 0)}

# ================================================================ elements
class El:
    space = "full"          # 'full' (on the footage) or 'pip' (on the blue world)
    layer = "front"         # 'behind' = under the person cut-out
    t0 = 0.0; t1 = 0.0; tail = 0.0
    def live(self, t): return self.t0 - 0.02 <= t < self.t1 + self.tail
    def draw(self, dst, t): pass

class Headline(El):
    """big word behind the person; fades in (or blurs in) — reference 'আপনি' / 'ভাবছেন?'"""
    layer = "behind"
    def __init__(s, txt, t0, t1, y, maxw=640, maxh=205, blur=False):
        s.txt, s.t0, s.t1, s.y, s.blur = txt, t0, t1, y, blur
        s.im = look_headline(txt, fit(txt, maxw, maxh))
    def draw(s, dst, t):
        if s.blur:
            e = eo3(seg(t, s.t0, 0.12)); place(dst, blurred(s.im, 12 * (1 - e)), 360, s.y, alpha=e)
        else:
            place(dst, s.im, 360, s.y, alpha=eo3(seg(t, s.t0, 0.20)))

class Side(El):
    """small word flanking the head — reference 'কি' / 'এখনো'"""
    layer = "behind"
    def __init__(s, txt, t0, t1, side, shot, y=372):
        s.txt, s.t0, s.t1, s.side, s.shot, s.y = txt, t0, t1, side, shot, y
        s.im = look_white(txt, 46, heavy=False)
    def draw(s, dst, t):
        hx = head_x_out(s.shot); half = s.im.info["adv"] / 2 + 18
        x = hx - 215 if s.side == "L" else hx + 215
        x = clamp(x, half, W - half)
        place(dst, s.im, x, s.y, alpha=eo3(seg(t, s.t0, 0.20)))

class Angled(El):
    """swings in from vertical at the right edge — reference 'ভাববেন'"""
    def __init__(s, txt, t0, t1, end=(400, 905), ang=36):
        s.txt, s.t0, s.t1, s.end, s.ang = txt, t0, t1, end, ang
        s.im = look_angled(txt, fit(txt, 560, 170))
    def draw(s, dst, t):
        e = eo3(seg(t, s.t0, 0.24))
        place(dst, s.im, lerp(668, s.end[0], e), lerp(600, s.end[1], e),
              alpha=eo3(seg(t, s.t0, 0.08)), angle=lerp(84, s.ang, e))

class Caption(El):
    """plain words at their final positions, each fades in — reference 'ঠিক এই কারণেই'"""
    def __init__(s, words, t1, cy, size=56, cx=360, exit="cut"):
        s.words, s.t0, s.t1, s.cy, s.cx, s.exit = words, words[0][1], t1, cy, cx, exit
        s.tail = 0.22 if exit != "cut" else 0.0
        while True:                                    # shrink until the line fits the frame
            s.imgs = [look_white(w, size) for w, _ in words]
            s.xs, s.tw = line_layout(s.imgs, font(ANEK800, size).getlength(" ") * SX)
            if s.tw <= 660 or size <= 30: break
            size -= 2
    def draw(s, dst, t):
        dx, am = 0.0, 1.0
        if t >= s.t1:
            if s.exit == "cut": return
            q = ei3(seg(t, s.t1, 0.22)); dx = -760 * q if s.exit == "left" else 760 * q; am = 1 - q
        left = s.cx - s.tw / 2 + dx
        for im, x, (w, wt) in zip(s.imgs, s.xs, s.words):
            a = eo3(seg(t, wt, 0.08)) * am
            if a > 0: place(dst, im, left + x - im.info["px"], s.cy, alpha=a, anchor="l")

class CyanBox(El):
    """white words in a cyan box: wipes in from the left with overshoot, grows per word,
    words blur-fade in, exits sliding left — reference 'অক্টোবর 20 তারিখ'"""
    def __init__(s, words, t_box, t1, cy, size=58, x_left=None, exit="left"):
        s.words, s.t0, s.t1, s.cy, s.exit = words, t_box, t1, cy, exit
        s.tail = 0.22
        s.imgs = [look_white(w, size, shadow=False) for w, _ in words]
        gap = font(ANEK800, size).getlength(" ") * SX
        s.xs, s.tw = line_layout(s.imgs, gap)
        s.padx, s.bh = 18, int(size * 1.42)
        s.widths = [s.xs[k] + s.imgs[k].info["adv"] + 2 * s.padx for k in range(len(words))]
        s.x_left = x_left if x_left is not None else 360 - s.widths[-1] / 2
    def full_w(s): return s.widths[-1]
    def draw(s, dst, t):
        k = sum(1 for _, wt in s.words if t >= wt)
        if k == 0: bw = s.widths[0] * eoback(seg(t, s.t0, 0.14))
        else:
            prev = s.widths[k - 2] if k > 1 else s.widths[0]
            bw = lerp(prev, s.widths[k - 1], eoback(seg(t, s.words[k - 1][1], 0.12)))
        if bw < 2: return
        dx, am, br = 0.0, 1.0, 0.0
        if t >= s.t1:
            q = ei3(seg(t, s.t1, 0.22)); dx = -760 * q if s.exit == "left" else 760 * q
            am, br = 1 - q * 0.6, 8 * q
        Wd = int(max(s.widths[-1], bw) + 4)
        L = Image.new("RGBA", (Wd, s.bh + 40), (0, 0, 0, 0))
        ImageDraw.Draw(L).rectangle([0, 20, int(bw), 20 + s.bh], fill=CYAN)
        for im, x, (w, wt) in zip(s.imgs, s.xs, s.words):
            e = eo3(seg(t, wt, 0.10))
            if e > 0: place(L, blurred(im, 6 * (1 - e)), s.padx + x - im.info["px"] - 6 * (1 - e) * 3,
                            20 + s.bh / 2 + 1, alpha=e, anchor="l")
        place(dst, blurred(L, br), s.x_left + dx - (br * 3 if br >= 0.4 else 0), s.cy, alpha=am, anchor="l")

class BigWhite(El):
    """big white word that blurs in — reference 'শিখবেনই না', 'স্কিলটাকে', 'Prepare'"""
    def __init__(s, txt, t0, t1, cy, maxw=620, maxh=150, x_left=None, exit="left"):
        s.txt, s.t0, s.t1, s.cy, s.exit = txt, t0, t1, cy, exit
        s.tail = 0.22 if exit != "cut" else 0.0
        p, sx = wfont(txt)
        s.im = look_white(txt, fit(txt, maxw, maxh, path=p, sx=sx))
        s.x_left = x_left
    def width(s): return s.im.info["adv"]
    def draw(s, dst, t):
        e = eo3(seg(t, s.t0, 0.11)); dx, am, br = 0.0, e, 12 * (1 - e)
        if t >= s.t1:
            if s.exit == "cut": return
            q = ei3(seg(t, s.t1, 0.22)); dx = -760 * q if s.exit == "left" else 760 * q
            am, br = 1 - q * 0.6, 10 * q
        im = blurred(s.im, br); off = br * 3 if br >= 0.4 else 0
        if s.x_left is None: place(dst, im, 360 + dx, s.cy, alpha=am)
        else: place(dst, im, s.x_left - s.im.info["px"] - off + dx, s.cy, alpha=am, anchor="l")

class Count(El):
    """number counts up with ease-out; enters fading + rising — reference '৳20,000' / '1,000+'"""
    def __init__(s, target, t0, t1, cy, dur=0.6, prefix="", suffix="", exit="left"):
        s.target, s.t0, s.t1, s.cy, s.dur, s.pre, s.suf, s.exit = target, t0, t1, cy, dur, prefix, suffix, exit
        s.tail = 0.22
        s.size = fit(f"{prefix}{target:,}{suffix}", 560, 135, path=INTER, sx=1.0)
    def draw(s, dst, t):
        v = int(round(s.target * (0.5 - 0.5 * np.cos(np.pi * seg(t, s.t0, s.dur)))))   # ease-in-out, like the reference
        im = styled(f"{s.pre}{v:,}{s.suf}", s.size, ((5, 6, BLUE_OL, 3, BLUE_OL), (0, 0, WHITE, 2, BLUE_OL)),
                    path=INTER, sx=1.0)
        e = eo3(seg(t, s.t0, 0.12)); dx, am, dy = 0.0, e, 30 * (1 - e)
        if t >= s.t1:
            q = ei3(seg(t, s.t1, 0.22)); dx = -760 * q; am = 1 - q * 0.6
        place(dst, im, 360 + dx, s.cy + dy, alpha=am)

class Pill(El):
    """white pill with a cyan ring, pops 0.3 -> 1.06 -> 1.0 — reference 'Enroll'"""
    def __init__(s, txt, t0, t1, cy, size=50, space="full", exit="fade"):
        s.txt, s.t0, s.t1, s.cy, s.space, s.exit = txt, t0, t1, cy, space, exit
        s.tail = 0.12
        ti = look_dark(txt, size)
        w, h, ring = int(ti.info["adv"] + 92), int(size * 1.75), 7
        P = rr(w + 2 * ring, h + 2 * ring, (h + 2 * ring) / 2, CYAN)
        P.alpha_composite(rr(w, h, h / 2, WHITE), (ring, ring))
        place(P, ti, (w + 2 * ring) / 2 - ti.info["adv"] / 2 - ti.info["px"], (h + 2 * ring) / 2 + 2, anchor="l")
        s.im = P
    def draw(s, dst, t):
        sc = lerp(0.3, 1.0, eoback(seg(t, s.t0, 0.18), 2.2)); am = eo3(seg(t, s.t0, 0.06))
        if t >= s.t1: am *= 1 - eo3(seg(t, s.t1, 0.12))
        place(dst, s.im, 360, s.cy, alpha=am, scale=sc)

class Bubble(El):
    """speech bubble under the circle; pops in, words typed one by one"""
    space = "pip"
    def __init__(s, pop, words, t1, cy):
        s.t0, s.words, s.t1, s.cy = pop, words, t1, cy
        s.imgs = [look_dark(w, 31, heavy=False) for w, _ in words]
        s.xs, s.tw = line_layout(s.imgs, font(ANEK700, 31).getlength(" ") * SX)
        s.bw, s.bh, s.tri = max(430, int(s.tw + 74)), 70, 14
        SS = 2; B = Image.new("RGBA", (s.bw * SS, (s.bh + s.tri) * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(B)
        d.rounded_rectangle([0, s.tri * SS, s.bw * SS - 1, (s.bh + s.tri) * SS - 1], radius=s.bh * SS // 2, fill=WHITE)
        d.polygon([(s.bw * SS / 2 - s.tri * SS, s.tri * SS + 2), (s.bw * SS / 2 + s.tri * SS, s.tri * SS + 2),
                   (s.bw * SS / 2, 0)], fill=WHITE)
        s.base = B.resize((s.bw, s.bh + s.tri), Image.LANCZOS)
    def draw(s, dst, t):
        B = s.base.copy(); x0 = (s.bw - s.tw) / 2
        for im, x, (w, wt) in zip(s.imgs, s.xs, s.words):
            a = eo3(seg(t, max(wt, s.t0), 0.08))
            if a > 0: place(B, im, x0 + x - im.info["px"], s.tri + s.bh / 2, alpha=a, anchor="l")
        sc = lerp(0.55, 1.0, eoback(seg(t, s.t0, 0.20)))
        place(dst, B, 360, s.cy, alpha=eo3(seg(t, s.t0, 0.10)), scale=sc)

class LabelBox(El):
    """white box, dark words, left-aligned under the card: wipe, then word fades — 'স্পেশাল অফার'"""
    space = "pip"
    def __init__(s, words, cy, t1, x=112, size=50):
        s.words, s.cy, s.x, s.t0, s.t1 = words, cy, x, words[0][1] - 0.16, t1
        s.imgs = [look_dark(w, size) for w, _ in words]
        s.xs, _ = line_layout(s.imgs, font(ANEK800, size).getlength(" ") * SX)
        s.pad, s.bh = 22, 80
        s.widths = [s.xs[k] + s.imgs[k].info["adv"] + 2 * s.pad for k in range(len(words))]
    def draw(s, dst, t):
        t1 = s.words[0][1]
        k = sum(1 for _, wt in s.words if t >= wt)
        if k == 0: bw = s.widths[0] * eo3(seg(t, t1 - 0.16, 0.15))
        else:
            prev = s.widths[k - 2] if k > 1 else s.widths[0]
            bw = lerp(prev, s.widths[k - 1], eo3(seg(t, s.words[k - 1][1], 0.12)))
        if bw < 2: return
        L = Image.new("RGBA", (int(s.widths[-1] + 4), s.bh), (0, 0, 0, 0))
        ImageDraw.Draw(L).rectangle([0, 0, int(bw), s.bh - 1], fill=WHITE)
        for im, x, (w, wt) in zip(s.imgs, s.xs, s.words):
            a = eo3(seg(t, wt, 0.14))
            if a > 0: place(L, im, s.pad + x - im.info["px"], s.bh / 2 + 1, alpha=a, anchor="l")
        place(dst, L, s.x, s.cy, anchor="l")

class CardCaption(El):
    """centred caption lines under the card; highlighted words sit on a cyan box — 'তাই Competition'"""
    space = "pip"
    def __init__(s, lines, t1):
        s.lines, s.t1 = lines, t1; s.t0 = lines[0][0][0][1]
        s.built = []
        for words, cy, size in lines:
            imgs = [look_white(w, size, shadow=False) for w, _, _ in words]
            xs, tw = line_layout(imgs, font(ANEK800, size).getlength(" ") * SX)
            s.built.append((words, cy, size, imgs, xs, tw))
    def draw(s, dst, t):
        for words, cy, size, imgs, xs, tw in s.built:
            left = 360 - tw / 2
            for im, x, (w, wt, hl) in zip(imgs, xs, words):
                e = eo3(seg(t, wt, 0.12))
                if e <= 0: continue
                if hl:
                    bx = Image.new("RGBA", (int(im.info["adv"] + 16), int(size * 1.25)), CYAN)
                    place(dst, bx, left + x - 8, cy + 3, alpha=e, anchor="l")
                place(dst, im, left + x - im.info["px"], cy + 8 * (1 - e), alpha=e, anchor="l")

class AddressCard(El):
    """course-card look: dark header + white body + purple button; slides in from the right"""
    space = "pip"
    def __init__(s, t0, t1, l1, l2, btn):
        s.t0, s.t1, s.l1, s.l2, s.btn = t0, t1, l1, l2, btn
        w, h, hh = 500, 520, 250
        C = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        C.alpha_composite(rr(w, h, 30, WHITE))
        head = rr(w, hh + 30, 30, CARD_DARK); C.alpha_composite(head.crop((0, 0, w, hh)), (0, 0))
        tag = look_white("পাবনা শোরুম", 30, shadow=False)
        tb = Image.new("RGBA", (int(tag.info["adv"] + 28), 46), CYAN)
        place(tb, tag, 14 - tag.info["px"], 24, anchor="l"); C.alpha_composite(tb, (28, 34))
        title = look_white("টয়োটা করোলা ক্রস", fit("টয়োটা করোলা ক্রস", 440, 64), shadow=False)
        place(C, title, 28 - title.info["px"], 138, anchor="l")
        sub = styled("ZVG13 • 2023 • পার্ল টু-টোন", 30, ((0, 0, (255, 255, 255, 170), 0, None),))
        place(C, sub, 28 - sub.info["px"], 204, anchor="l")
        lab = styled("শোরুমের ঠিকানা", 28, ((0, 0, (110, 118, 135, 255), 0, None),), path=ANEK700)
        place(C, lab, 28 - lab.info["px"], 286, anchor="l")
        s.card, s.w, s.h = C, w, h
        s.i1, s.i2 = look_dark(l1[0], 40), look_dark(l2[0], 40)
        bt = look_white(btn[0], 36, shadow=False)
        B = rr(444, 76, 38, PURPLE); place(B, bt, 222 - bt.info["adv"] / 2 - bt.info["px"], 39, anchor="l")
        s.bimg = B
    def draw(s, dst, t):
        dx = 760 * (1 - eo3(seg(t, s.t0, 0.32)))
        C = s.card.copy()
        for im, (txt, wt), y in ((s.i1, s.l1, 338), (s.i2, s.l2, 392)):
            e = eo3(seg(t, wt, 0.14))
            if e > 0: place(C, im, 28 - im.info["px"], y + 8 * (1 - e), alpha=e, anchor="l")
        e = seg(t, s.btn[1], 0.2)
        if e > 0: place(C, s.bimg, s.w / 2, 466, alpha=eo3(e * 2), scale=lerp(0.4, 1.0, eoback(e, 2.0)))
        sh = Image.new("RGBA", (s.w + 80, s.h + 80), (0, 0, 0, 0))
        sh.alpha_composite(rr(s.w, s.h, 30, (3, 22, 70, 120)), (40, 52)); sh = sh.filter(ImageFilter.GaussianBlur(18))
        place(dst, sh, 360 + dx, 860 + 12)
        place(dst, C, 360 + dx, 860)

# ================================================================ the edit
WT = {}            # aligned word times
for wd in json.load(open(sys.argv[3].replace("track.json", "aud/words.json"), encoding="utf-8")):
    WT.setdefault(wd["w"], []).append(wd["t"])
def wt(word, n=0): return WT[word][n]

SHOT1, SHOT5, SHOT7, SHOT8 = 0, 4, 6, 7
EL = []
# A 0-2.1  'আপনি কি এখনো ভাবছেন?' pattern
EL += [Headline("আপনারা", wt("আপনারা"), 2.35, 158),
       Side("কিন্তু", wt("কিন্তু"), 2.35, "L", SHOT1), Side("ইতোমধ্যেই", wt("ইতোমধ্যেই"), 2.35, "R", SHOT1),
       Headline("আমাদের", wt("আমাদের"), 2.35, 505, maxw=600, maxh=150, blur=True)]
# B circle + bubble
EL += [Bubble(2.30, [("চিটাগাং", wt("চিটাগাং")), ("স্টকের", wt("স্টকের")), ("করোলা", wt("করোলা")), ("ক্রস", wt("ক্রস"))], 3.88, 452 + 170 + 74),
       Bubble(3.88, [("সম্পর্কে", wt("সম্পর্কে")), ("ধারণা", wt("ধারণা")), ("চলে", wt("চলে")), ("এসেছে", wt("এসেছে"))], 5.52, 452 + 170 + 74)]
# C full: headline + side swap + angled
EL += [Headline("বেশ কয়েকটি", wt("বেশ"), 9.40, 158),
       Side("ইউনিট", wt("ইউনিট"), 6.86, "L", SHOT1), Side("কিন্তু", wt("কিন্তু", 1), 6.86, "R", SHOT1),
       Side("আমাদের", wt("আমাদের", 1), 9.40, "L", SHOT1), Side("চিটাগাং", wt("চিটাগাং", 1), 9.40, "R", SHOT1),
       Angled("রেডি স্টকে", wt("রেডি"), 9.40)]
# D card + label boxes
EL += [LabelBox([("আমাদের", wt("আমাদের", 2)), ("শোরুমেও", wt("শোরুমেও"))], 744, 12.84),
       LabelBox([("পার্ল", wt("পার্ল")), ("কালার", wt("কালার"))], 834, 12.84),
       LabelBox([("ব্ল্যাক", wt("ব্ল্যাক")), ("কালার", wt("কালার", 1))], 924, 12.84)]
# E full: cyan box line + big blur-in word, both slide out left
_eb = BigWhite("অ্যাভেলেবল", wt("অ্যাভেলেবল", 1), 15.16, 862, maxw=600, maxh=130)
_ec = CyanBox([("দুইটাই", wt("দুইটাই")), ("কিন্তু", wt("কিন্তু", 3))], 13.00, 15.16, 772)
_left = 360 - max(_eb.width(), _ec.full_w()) / 2
_eb.x_left = _left + 6; _ec.x_left = _left
EL += [_ec, _eb]
# F/G b-roll: caption, then big Latin + cyan box (exits right) — 'Prepare / করা শুরু করুন'
EL += [Caption([(w, t) for w, t in zip(["আমার", "সামনে", "যে", "গাড়িটা", "দেখতেছেন"],
                                       [wt("আমার"), wt("সামনে"), wt("যে"), wt("গাড়িটা"), wt("দেখতেছেন")])], 17.28, 262, size=62)]
_fl = BigWhite("ZVG13", wt("ZVG13"), 20.36, 236, maxw=560, maxh=118, exit="right")
_fc = CyanBox([("2023", wt("2023")), ("মডেল", wt("এর", 1))], wt("2023") - 0.06, 20.36, 326, exit="right")
_left = 360 - max(_fl.width(), _fc.full_w()) / 2
_fl.x_left = _left + 4; _fc.x_left = _left
EL += [_fl, _fc]
# H b-roll in a card + caption under it with highlighted keywords
EL += [CardCaption([
    ([("পার্ল", wt("পার্ল", 1), True), ("কালার", wt("কালার", 2), False), ("টু", wt("টু"), False), ("টোন", wt("টোন"), False)], 776, 58),
    ([("উপরে", wt("উপরে"), False), ("হার্ড", wt("হার্ড"), True), ("টপ", wt("টপ"), True)], 858, 50),
    ([("মডেলিস্টা", wt("মডেলিস্টা"), True), ("বডি", wt("বডি"), False), ("কিট", wt("কিট"), False), ("সহ", wt("সহ"), False)], 930, 50)],
    23.60)]
# I full: side words, headline behind, angled
EL += [Side("গাড়িটির", wt("গাড়িটির"), 27.24, "L", SHOT5), Side("সঙ্গে", wt("সঙ্গে"), 27.24, "R", SHOT5),
       Headline("অটো পার্কিং", wt("অটো"), 27.24, 158),
       Angled("360 ক্যামেরা", wt("360"), 27.24)]
# J b-roll in a card: four feature boxes + pill
EL += [LabelBox([("অ্যালয়", 27.40), ("হুইলস", wt("হুইলস"))], 744, 31.44),
       LabelBox([("ফগ", wt("ফগ")), ("লাইট", wt("লাইট"))], 834, 31.44),
       LabelBox([("সিট", wt("সিট")), ("হিটার", wt("হিটার"))], 924, 31.44),
       LabelBox([("ক্রুজ", wt("ক্রুজ")), ("কন্ট্রোল", wt("কন্ট্রোল"))], 1014, 31.44),
       Pill("সবকিছুই পাচ্ছেন", wt("সবকিছুই"), 31.40, 1140, size=54, space="pip")]
# K full: headline behind + count-up + cyan boxes + big '৪'
EL += [Headline("মাইলেজ", wt("মাইলেজ"), 35.62, 158),
       Caption([("মাত্র", wt("মাত্র"))], 34.20, 742, size=52, exit="left"),
       Count(33000, wt("33,000"), 34.20, 838, dur=0.45),
       CyanBox([("কিলো", wt("কিলো"))], wt("কিলো") - 0.06, 34.20, 934),
       CyanBox([("অকশন", wt("অকশন")), ("গ্রেড", wt("গ্রেড"))], wt("অকশন") - 0.06, 35.40, 772),
       BigWhite("৪", wt("ফোর"), 35.62, 884, maxw=300, maxh=150, exit="cut")]
# L1 full (after the light leak): small line + big blur-in + pill
EL += [Caption([("দেরি", wt("দেরি")), ("না", wt("না")), ("করে", wt("করে"))], 37.47, 762),
       BigWhite("আজই", wt("আজই"), 37.47, 858, maxw=420, maxh=140, exit="cut"),
       Pill("ভিজিট করুন", wt("ভিজিট"), 37.47, 1000, size=62)]
# L2 circle2 + address card
EL += [AddressCard(38.00, 99, ("আব্দুল হামিদ রোড", wt("আব্দুল")), ("পাবনা সদর, পাবনা", wt("পাবনা")),
                   ("আজই ভিজিট করুন", wt("পাবনা", 1)))]

# blocks: what the frame IS at time t
BLOCKS = [
    ("full", 0.00, 2.10), ("in", 2.10, 2.35, "circle"), ("pip", 2.35, 5.28, "circle"), ("out", 5.28, 5.52, "circle"),
    ("full", 5.52, 9.12), ("in", 9.12, 9.40, "card"), ("pip", 9.40, 12.80, "card"), ("out", 12.80, 13.04, "card"),
    ("full", 13.04, 20.60), ("cut", 20.60, 20.90, "card"), ("pip", 20.90, 23.56, "card"), ("out", 23.56, 23.80, "card"),
    ("full", 23.80, 27.24), ("cut", 27.24, 27.54, "card"), ("pip", 27.54, 31.40, "card"), ("out", 31.40, 31.64, "card"),
    ("full", 31.64, 37.45), ("in", 37.45, 37.72, "circle2"), ("pip", 37.72, 99.0, "circle2"),
]
def block_at(t):
    for b in BLOCKS:
        if b[1] <= t < b[2]: return b
    return BLOCKS[-1]

def draw_items(dst, t, space, layer=None):
    for el in EL:
        if el.space == space and (layer is None or el.layer == layer) and el.live(t):
            el.draw(dst, t)

# ---------------------------------------------------------------- overlays
def _leak():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    def blob(cx, cy, rx, ry): return np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    cool = (blob(60, 1150, 380, 520)[..., None] * np.array([0.35, 1.0, 0.95]) +
            blob(700, 1000, 320, 600)[..., None] * np.array([1.0, 0.35, 0.75]) +
            blob(360, 700, 160, 900)[..., None] * np.array([1.0, 1.0, 1.0]) * 0.7)
    warm = (blob(120, 560, 520, 900)[..., None] * np.array([1.0, 0.42, 0.04]) +
            blob(330, 560, 260, 640)[..., None] * np.array([1.0, 0.80, 0.35]) +
            blob(40, 900, 200, 500)[..., None] * np.array([0.95, 0.15, 0.05]) * 0.8)
    return np.clip(cool, 0, 1).astype(np.float32), np.clip(warm, 0, 1).astype(np.float32)
LEAK_COOL, LEAK_WARM = _leak()
LEAK_A, LEAK_PEAK, LEAK_B = 35.48, 35.64, 36.02
def light_leak(img, t):
    if not (LEAK_A <= t < LEAK_B): return img
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    if t < LEAK_PEAK:
        k = seg(t, LEAK_A, LEAK_PEAK - LEAK_A); fl = LEAK_COOL * eo3(k); wh = clamp((k - 0.55) / 0.45, 0, 1)
    else:
        k = seg(t, LEAK_PEAK, LEAK_B - LEAK_PEAK); fl = LEAK_WARM * (1 - eo3(k)); wh = clamp(1 - k / 0.22, 0, 1)
    a = 1 - (1 - a) * (1 - fl)
    a = a + (1 - a) * wh
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

# ---------------------------------------------------------------- renderers
def full_frame(t, si):
    prm = cam_params(si, t, "full")
    fr, mt = camera(si, prm)
    if t < 0.12:                                        # opening white silhouette (reference frame 0)
        fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), 1.0 if t < 0.06 else 1 - eo3(seg(t, 0.06, 0.06)))
    out = fr.convert("RGBA") if t >= 0.12 else camera(si, prm)[0].convert("RGBA")
    draw_items(out, t, "full", "behind")
    if mt is not None:
        person = fr.convert("RGBA"); person.putalpha(mt); out.alpha_composite(person)
    draw_items(out, t, "full", "front")
    return out

def pip_frame(t, si, kind, e, mode, p=1.0):
    """e: 0 = full frame, 1 = settled shape. mode: 'pip' | 'in' | 'out' | 'cut'."""
    prm = lerp_params(cam_params(si, t, "full"), cam_params(si, t, kind), e)
    fr, mt = camera(si, prm)
    shp = tuple(lerp(a, b, e) for a, b in zip(FULL_SHAPE[kind], SHAPES[kind]))
    if mode == "cut":                                   # card cut-in: settles from 1.25x
        s = lerp(1.25, 1.0, eo3(p)); x0, y0, x1, y1, r = shp; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        shp = (cx - (cx - x0) * s, cy - (cy - y0) * s, cx + (x1 - cx) * s, cy + (y1 - cy) * s, r * s)
    out = BG.copy()
    if e > 0.01:
        out.alpha_composite(LINES if e >= 0.99 else Image.fromarray(
            (np.asarray(LINES, np.float32) * np.array([1, 1, 1, e], np.float32)).astype(np.uint8), "RGBA"))
    chrome = 1.0 if mode != "out" else 1 - eo3(p * 2.2)
    if kind == "circle": rings(out, shp[0], shp[1], shp[2], t, chrome * e)
    m = shape_mask(kind, shp)
    content = fr.convert("RGBA"); content.putalpha(m); out.alpha_composite(content)
    if mode == "in":                                    # full-frame words fly outward, person stays on top
        XF["fly"], XF["am"] = 1 + 1.1 * e, 1 - eo3(p / 0.85)
        draw_items(out, t, "full", "behind")
        if mt is not None:
            person = fr.convert("RGBA"); person.putalpha(Image.fromarray(np.minimum(np.asarray(mt), np.asarray(m))))
            out.alpha_composite(person)
        draw_items(out, t, "full", "front")
        XF["fly"], XF["am"] = 1.0, 1.0
    bw = 5 * e
    if bw > 0.3:
        ring_m = np.asarray(shape_mask(kind, shp, grow=bw), np.int16) - np.asarray(m, np.int16)
        Wl = Image.new("RGBA", (W, H), WHITE); Wl.putalpha(Image.fromarray(ring_m.clip(0, 255).astype(np.uint8)))
        out.alpha_composite(Wl)
    XF["am"] = chrome
    draw_items(out, t, "pip")
    XF["am"] = 1.0
    return out

def zoom_frame(img, zp):
    if abs(zp - 1) < 1e-4: return img
    cw, ch = W / zp, H / zp
    return img.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))

def render(fi):
    t = fi / FPS
    si = min(int(t * SRC_FPS), NSRC - 1)
    b = block_at(t); kind = b[0]
    if kind == "full":
        img = full_frame(t, si)
    else:
        shape = b[3]; p = seg(t, b[1], b[2] - b[1])
        if kind == "pip":
            img = zoom_frame(pip_frame(t, si, shape, 1.0, "pip"), 1 + 0.035 * p)
        elif kind == "in":
            img = pip_frame(t, si, shape, eo3(p), "in", p)
        elif kind == "out":
            img = zoom_frame(pip_frame(t, si, shape, 1 - eo3(p), "out", p), lerp(1.035, 1.0, eo3(p)))
        else:
            img = pip_frame(t, si, shape, 1.0, "cut", p)
    img = light_leak(img, t)
    return img.convert("RGB").tobytes()

if __name__ == "__main__":
    if PREVIEW:
        for ts in PREVIEW:
            Image.frombytes("RGB", (W, H), render(int(round(float(ts) * FPS)))).save(f"{OUT}_{ts}.png")
        print("previews:", ", ".join(PREVIEW)); sys.exit(0)
    n = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-nostdin", "-v", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-i", SRC_VIDEO, "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT],
        stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=6)):
            ff.stdin.write(buf)
            if i % 250 == 0: print(f"  frame {i}/{n}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done ->", OUT, "exit", ff.returncode)
