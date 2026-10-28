# -*- coding: utf-8 -*-
"""Corolla Cross edit in the style of reference #5 (+ its sound grammar).

Visual vocabulary measured from the reference:
  2-line captions, each with its own look (orange / green-glow / cyan-glow / blue box /
  red box / gold / red-glow / lime bar); line 2 types cluster by cluster with a pop;
  small icon pops beside it.  Green energy-burst around the person -> white -> scene.
  Purple ray scene with the product (here: the car, cut out) and tracking-in text.
  Blue dashed callout pills, orange ring shrinking onto the subject, frosted logo card
  dropping with a bounce, cream scene with pink boxes stamped in, pink offer circle with
  a rotated stamp, zooming image-grid card, two-tone big text.  4:5 output with blurred sides.
usage: compose_v5.py SRC MATTE TRACK WORDS CARCUT OUT [--preview t,..]
"""
import sys, json, subprocess, math
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, MAT, TRACK, WORDS, CARCUT, OUT = sys.argv[1:7]
PREVIEW = sys.argv[8].split(",") if len(sys.argv) > 8 and sys.argv[7] == "--preview" else None
FPS, SRC_FPS = 50, 25
W, H = 720, 1280
ANEK = "/usr/share/fonts/truetype/bnx/AnekBN.ttf"
ANEK7 = "/usr/share/fonts/truetype/bnx/anek-bangla-bengali-700-normal.ttf"
INTER = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
SX = 0.92
WHITE = (255, 255, 255, 255)

TR = json.load(open(TRACK)); HX, HTOP, HW, SHOT, SHOTS = TR["hx"], TR["htop"], TR["hw"], TR["shot"], TR["shots"]
NSRC = len(HX); DUR = NSRC / SRC_FPS
WT = {}
for w in json.load(open(WORDS, encoding="utf-8")): WT.setdefault(w["w"], []).append(w["t"])
def wt(w, n=0): return WT[w][n]

# ======================================================== SOUND RULES (learned from reference #5)
SFX_RULES = {
    "line1":       [("blip", 0.00, -3)],                  # small first caption line
    "line2":       [("blip2", -0.02, 0)],                 # big second line starts typing
    "box_line":    [("blip2", -0.02, 0), ("soft_whoosh", -0.05, -4)],   # boxed line wipes in
    "icon":        [("pop", -0.01, -4)],                  # little icon beside a caption
    "pill":        [("blip", 0.00, 0, dict(f0=720))],     # blue dashed callout pill pops
    "tag":         [("blip", 0.00, -2, dict(f0=980))],    # small tag under a caption
    "ring":        [("soft_whoosh", -0.05, 0)],           # orange ring shrinks onto the subject
    "energy_out":  [("burst", "lead75", 0)],              # green energy burst -> white
    "flash_in":    [("thud_whoosh", "centre", 0)],        # flash back to the talking shot
    "scene":       [("swoosh", "centre", 0)],             # whoosh into a designed scene
    "logo_drop":   [("bounce", 0.00, 0)],                 # frosted card lands
    "brand_line":  [("sparkle", -0.03, 0)],               # glowing red headline
    "stamp_box":   [("stamp", 0.00, 0)],                  # pink box stamped in
    "head_line":   [("blip", 0.00, -2)],                  # scene header types in
    "two_tone":    [("blip2", 0.00, 0)],                  # big two-tone line
    "circle_pop":  [("pop", 0.00, 0)],                    # pink circle pops
    "offer_stamp": [("sweep_stamp", 0.00, 0)],            # rotated stamp tag
}
CUES = []
def cue(event, t, gain=0.0):
    for r in SFX_RULES[event]:
        snd, off, g = r[:3]; kw = r[3] if len(r) > 3 else {}
        CUES.append(dict(event=event, sound=snd, t=round(t, 3), off=off, gain=g + gain, kw=kw))

# ======================================================== helpers
def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def ei2(p): p = clamp(p, 0, 1); return p * p
def eoback(p, s=1.8):
    p = clamp(p, 0, 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def bounce_out(p):
    p = clamp(p, 0, 1)
    if p < 1 / 2.75: return 7.5625 * p * p
    if p < 2 / 2.75: p -= 1.5 / 2.75; return 7.5625 * p * p + 0.75
    if p < 2.5 / 2.75: p -= 2.25 / 2.75; return 7.5625 * p * p + 0.9375
    p -= 2.625 / 2.75; return 7.5625 * p * p + 0.984375
def seg(t, a, d): return clamp((t - a) / d, 0, 1)
def is_bn(s): return any("ঀ" <= c <= "৿" for c in s)

@lru_cache(maxsize=None)
def font(p, s): return ImageFont.truetype(p, s)
def fpath(txt, path=None): return path or (ANEK if (is_bn(txt) or any(c.isdigit() for c in txt)) else INTER)
def fsx(txt, path=None): return SX if fpath(txt, path) != INTER else 1.0

@lru_cache(maxsize=None)
def look(txt, size, fill, stroke=None, sw=0, glow=None, gr=0, shadow=True, path=None):
    """text with vertical gradient fill, dark stroke, outer glow and soft drop shadow."""
    p = fpath(txt, path); sx = fsx(txt, path); f = font(p, size); asc, desc = f.getmetrics()
    pad = sw + gr * 2 + 12; vpad = pad + int(size * 0.22); adv = f.getlength(txt)
    w, h = int(adv + 2 * pad), int(asc + desc + 2 * vpad)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad, vpad), txt, font=f, fill=255)
    ms = Image.new("L", (w, h), 0); ImageDraw.Draw(ms).text((pad, vpad), txt, font=f, fill=255, stroke_width=sw, stroke_fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        s_ = Image.new("RGBA", (w, h), (0, 0, 0, 0)); s_.putalpha(ms.point(lambda v: int(v * 0.55)))
        s_ = s_.filter(ImageFilter.GaussianBlur(4)); out.alpha_composite(s_.transform((w, h), Image.AFFINE, (1, 0, -2, 0, 1, -4)))
    if glow:
        g = Image.new("RGBA", (w, h), glow + (0,)); g.putalpha(ms.point(lambda v: int(v * 0.9)))
        g = g.filter(ImageFilter.GaussianBlur(gr)); out.alpha_composite(g); out.alpha_composite(g)
    if stroke and sw:
        st = Image.new("RGBA", (w, h), stroke + (255,)); st.putalpha(ms); out.alpha_composite(st)
    ys = np.where(np.asarray(m).max(1) > 20)[0]; y0, y1 = (ys.min(), ys.max()) if len(ys) else (0, h)
    k = np.clip((np.arange(h) - y0) / max(1, y1 - y0), 0, 1)[:, None, None]
    c0, c1 = np.array(fill[0], np.float32), np.array(fill[1], np.float32)
    rgb = np.repeat(c0 * (1 - k) + c1 * k, w, 1)
    fl = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA"); fl.putalpha(m); out.alpha_composite(fl)
    if sx != 1: out = out.resize((max(1, int(w * sx)), h), Image.LANCZOS)
    out.info.update(adv=adv * sx, px=pad * sx, path=p, sx=sx, size=size); return out

def blurred(im, r):
    if r < 0.4: return im
    p_ = int(r * 3); b = Image.new("RGBA", (im.width + 2 * p_, im.height + 2 * p_), (0, 0, 0, 0))
    b.alpha_composite(im, (p_, p_)); b = b.filter(ImageFilter.GaussianBlur(r)); b.info.update(im.info); return b

def place(dst, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0, anchor="c"):
    if alpha <= 0.004: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.996:
        a = (np.asarray(im.getchannel("A"), np.float32) * alpha).astype(np.uint8); im = im.copy(); im.putalpha(Image.fromarray(a))
    x = int(round(cx - im.width / 2)) if anchor == "c" else int(round(cx)); y = int(round(cy - im.height / 2))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 > x0 and y1 > y0: dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def rr(w, h, r, fill, ss=3, outline=None, width=0):
    im = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=fill, outline=outline, width=int(width * ss))
    return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)

def clusters(s):
    out = []
    for ch in s:
        cp = ord(ch)
        att = (0x0981 <= cp <= 0x0983) or cp == 0x09BC or (0x09BE <= cp <= 0x09CD) or cp == 0x09D7 or cp in (0x200C, 0x200D)
        if out and ch != " " and out[-1] != " " and (att or out[-1].endswith("্")): out[-1] += ch
        else: out.append(ch)
    return out

def cluster_xs(im, txt):
    p, sx, size = im.info["path"], im.info["sx"], im.info["size"]; cl = clusters(txt); xs = [im.info["px"]]; pre = ""
    for c in cl: pre += c; xs.append(im.info["px"] + font(p, size).getlength(pre) * sx)
    return cl, xs

def typed_pop(dst, im, txt, t0, t, cx, cy, step=0.06, mode="pop", spread=0.0):
    """reveal cluster by cluster. mode 'pop': each cluster scales 1.45->1 with blur (ref captions);
    'drop': falls from below with a bounce (ref 'এর look'); spread>0: letters start spaced out and close in."""
    cl, xs = cluster_xs(im, txt); left = cx - im.info["adv"] / 2 - im.info["px"]
    for i, c in enumerate(cl):
        if c == " ": continue
        p = seg(t, t0 + i * step, 0.16)
        if p <= 0: break
        a, b = int(xs[i]) - (5 if i else 18), int(xs[i + 1]) + (5 if i < len(cl) - 1 else 18)
        piece = im.crop((max(0, a), 0, min(im.width, b), im.height)); pc = left + (max(0, a) + min(im.width, b)) / 2
        if spread: pc = cx + (pc - cx) * (1 + spread * (1 - eo3(seg(t, t0, 0.5))))
        if mode == "pop":
            place(dst, blurred(piece, 6 * (1 - eo3(p))), pc, cy, alpha=eo3(p * 2), scale=lerp(1.45, 1.0, eoback(p, 1.4)))
        else:
            place(dst, piece, pc, cy + 120 * (1 - bounce_out(p)), alpha=eo3(p * 3))

def fit(txt, maxw, hi, lo=26, path=None):
    p = fpath(txt, path); sx = fsx(txt, path)
    for s in range(hi, lo - 1, -2):
        if font(p, s).getlength(txt) * sx <= maxw: return s
    return lo

# ======================================================== caption looks (sampled from the reference)
LOOKS = {
 "white":  dict(fill=((255, 255, 255), (238, 238, 238)), stroke=(20, 20, 20), sw=3),
 "orange": dict(fill=((255, 186, 60), (238, 110, 18)), stroke=(70, 28, 0), sw=4),
 "green":  dict(fill=((150, 255, 140), (40, 205, 70)), stroke=(0, 70, 25), sw=3, glow=(70, 255, 100), gr=10),
 "cyan":   dict(fill=((160, 245, 255), (40, 190, 232)), stroke=(0, 55, 80), sw=3, glow=(70, 220, 255), gr=10),
 "gold":   dict(fill=((255, 244, 110), (244, 190, 22)), stroke=(70, 45, 0), sw=4),
 "red":    dict(fill=((255, 110, 100), (220, 30, 42)), stroke=(95, 0, 12), sw=3, glow=(255, 60, 60), gr=11),
 "lime":   dict(fill=((228, 255, 96), (160, 222, 30)), stroke=(30, 70, 0), sw=4, glow=(170, 255, 60), gr=8),
 "yellow": dict(fill=((255, 246, 90), (255, 214, 30)), stroke=(80, 20, 0), sw=3),
 "lgreen": dict(fill=((170, 255, 150), (90, 230, 90)), stroke=(0, 60, 20), sw=3),
}
BOXES = {"blue": ((54, 128, 240), (22, 86, 214)), "red": ((236, 50, 44), (196, 18, 30)), "lime": ((170, 245, 60), (120, 210, 30))}
def L(txt, size, name): return look(txt, size, **LOOKS[name])

def car_icon(col=(255, 214, 40)):
    S = 3; im = Image.new("RGBA", (84 * S, 60 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w = 5 * S
    d.rounded_rectangle([6 * S, 24 * S, 78 * S, 44 * S], 8 * S, outline=col + (255,), width=w)
    d.line([(18 * S, 24 * S), (28 * S, 10 * S), (58 * S, 10 * S), (68 * S, 24 * S)], fill=col + (255,), width=w, joint="curve")
    for cx in (22, 62): d.ellipse([(cx - 8) * S, 38 * S, (cx + 8) * S, 54 * S], fill=(30, 30, 30, 255), outline=col + (255,), width=w)
    return im.resize((84, 60), Image.LANCZOS)
def bang_icon():
    S = 3; im = Image.new("RGBA", (56 * S, 56 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(28 * S, 2 * S), (54 * S, 52 * S), (2 * S, 52 * S)], fill=(228, 30, 40, 255))
    d.rectangle([25 * S, 18 * S, 31 * S, 38 * S], fill=WHITE); d.ellipse([24 * S, 41 * S, 32 * S, 49 * S], fill=WHITE)
    return im.resize((56, 56), Image.LANCZOS)

# ======================================================== elements
class El:
    t0 = 0.0; t1 = 0.0; tail = 0.16
    def live(self, t): return self.t0 - 0.02 <= t < self.t1 + self.tail
    def out_k(self, t): return eo3(seg(t, self.t1, self.tail))

class Cap(El):
    """two-line caption. l1/l2 = (text, time, look) ; box = 'blue'|'red'|'lime' wraps line 2 or 1."""
    def __init__(s, cy, t1, l1=None, l2=None, box2=None, box1=None, icon=None, s1=46, s2=78, brand=False):
        s.cy, s.t1, s.l1, s.l2, s.box1, s.box2, s.icon = cy, t1, l1, l2, box1, box2, icon
        ts = []
        if l1:
            s.i1 = L(l1[0], fit(l1[0], 600, s1), l1[2]); ts.append(l1[1]); cue("box_line" if box1 else "line1", l1[1])
        if l2:
            s.i2 = L(l2[0], fit(l2[0], 640, s2), l2[2]); ts.append(l2[1])
            cue("box_line" if box2 else ("brand_line" if brand else "line2"), l2[1])
        if icon: cue("icon", icon[1])
        s.t0 = min(ts)
    def _box(s, dst, im, t0, t, cy, name):
        w = im.info["adv"] + 36; h = im.info["size"] * 1.18; x0 = 360 - w / 2
        bw = w * eo3(seg(t, t0 - 0.06, 0.16))
        if bw > 2:
            c0, c1 = BOXES[name]; k = np.linspace(0, 1, int(h))[:, None, None]
            g = np.repeat(np.array(c0) * (1 - k) + np.array(c1) * k, int(w), 1).astype(np.uint8)
            B = Image.fromarray(g).convert("RGBA").crop((0, 0, int(bw), int(h)))
            place(dst, B, x0, cy + 2, anchor="l")
    def draw(s, dst, t):
        k = s.out_k(t); Lyr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); y = s.cy
        if s.l1:
            if s.box1: s._box(Lyr, s.i1, s.l1[1], t, y, s.box1); typed_pop(Lyr, s.i1, s.l1[0], s.l1[1] + 0.06, t, 360, y, 0.035)
            else:
                e = eo3(seg(t, s.l1[1], 0.16)); place(Lyr, blurred(s.i1, 6 * (1 - e)), 360, y + 14 * (1 - e), alpha=e)
            y += s.i1.info["size"] * 0.55 + (s.i2.info["size"] * 0.55 if s.l2 else 0) + 4
        if s.l2:
            if s.box2: s._box(Lyr, s.i2, s.l2[1], t, y, s.box2)
            step = min(0.07, 0.5 / max(1, len(clusters(s.l2[0]))))
            typed_pop(Lyr, s.i2, s.l2[0], s.l2[1] + (0.06 if s.box2 else 0), t, 360, y, step)
        if s.icon:
            im, ti, side = s.icon; p = seg(t, ti, 0.3)
            if p > 0:
                ref = s.i1 if (side == "l1" and s.l1) else s.i2
                yy = s.cy if side == "l1" else y
                place(Lyr, im, 360 + ref.info["adv"] / 2 + 34, yy - 8, alpha=eo3(p * 3), scale=lerp(0.2, 1, eoback(p, 2.0)), angle=lerp(-40, 0, eo3(p)))
        place(dst, blurred(Lyr, 8 * k), 360, 640, alpha=1 - k)

def dashed_pill(txt, size, col=(40, 162, 232)):
    ti = look(txt, size, ((255, 255, 255), (255, 255, 255)), shadow=False)
    w, h = int(ti.info["adv"] + size * 1.2), int(size * 1.55); S = 3
    im = Image.new("RGBA", ((w + 12) * S, (h + 12) * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6 * S, 6 * S, (w + 6) * S, (h + 6) * S], h * S / 2, fill=col + (255,))
    # dashed white border just inside the edge
    r = (h / 2 - 5) * S; x0, y0, x1, y1 = 11 * S, 11 * S, (w + 1) * S, (h + 1) * S
    pts = []
    for k in range(240):
        a = k / 240
        per = 2 * (x1 - x0 - 2 * r) + 2 * math.pi * r; dist = a * per; straight = x1 - x0 - 2 * r
        if dist < straight: pts.append((x0 + r + dist, y0))
        elif dist < straight + math.pi * r: q = (dist - straight) / r - math.pi / 2; pts.append((x1 - r + r * math.cos(q), y0 + r + r * math.sin(q)))
        elif dist < 2 * straight + math.pi * r: pts.append((x1 - r - (dist - straight - math.pi * r), y1))
        else: q = (dist - 2 * straight - math.pi * r) / r + math.pi / 2; pts.append((x0 + r + r * math.cos(q), y0 + r + r * math.sin(q)))
    for k in range(0, len(pts) - 1, 2): d.line([pts[k], pts[k + 1]], fill=WHITE, width=int(2.4 * S))
    im = im.resize((w + 12, h + 12), Image.LANCZOS); place(im, ti, (w + 12) / 2, (h + 12) / 2 + 1)
    sh = Image.new("RGBA", (im.width + 20, im.height + 20), (0, 0, 0, 0)); sh.alpha_composite(im, (10, 14))
    a_ = sh.getchannel("A").filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.35))
    shadow = Image.new("RGBA", sh.size, (0, 0, 0, 0)); shadow.putalpha(a_); shadow.alpha_composite(im, (10, 10)); return shadow

class Pills(El):
    """callout pills (blue, dashed border) pop in tilted with overshoot."""
    def __init__(s, items, t1, event="pill"):
        s.items = [(dashed_pill(txt, size), tt, x, y, ang) for txt, tt, x, y, ang, size in items]; s.t1 = t1
        s.t0 = min(i[1] for i in s.items)
        for _, tt, *_ in s.items: cue(event, tt)
    def draw(s, dst, t):
        k = s.out_k(t)
        for im, tt, x, y, ang in s.items:
            p = seg(t, tt, 0.32)
            if p > 0: place(dst, im, x, y, alpha=eo3(p * 3) * (1 - k), scale=lerp(0.25, 1, eoback(p, 2.2)), angle=lerp(ang - 25, ang, eo3(p)))

class Ring(El):
    """orange ring starts wide and closes onto the subject."""
    def __init__(s, t0, t1, cx, cy, r):
        s.t0, s.t1, s.cx, s.cy, s.r = t0, t1, cx, cy, r; cue("ring", t0)
    def draw(s, dst, t):
        k = s.out_k(t); p = eo3(seg(t, s.t0, 0.5)); r = lerp(s.r * 2.3, s.r, p); S = 2
        im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.ellipse([(s.cx - r) * S, (s.cy - r * 0.92) * S, (s.cx + r) * S, (s.cy + r * 0.92) * S], outline=(246, 176, 52, int(255 * (1 - k))), width=6 * S)
        im = im.resize((W, H), Image.LANCZOS); g = im.filter(ImageFilter.GaussianBlur(6)); dst.alpha_composite(g); dst.alpha_composite(im)

class LogoCard(El):
    """frosted white card falls from above the frame and bounces to rest."""
    def __init__(s, t0, t1):
        s.t0, s.t1 = t0, t1; cue("logo_drop", t0 + 0.28)
        c = rr(520, 200, 40, (255, 255, 255, 120)); c.alpha_composite(rr(500, 180, 32, (236, 236, 238, 255)), (10, 10))
        S = 3; ic = Image.new("RGBA", (150 * S, 150 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(ic)
        d.ellipse([0, 0, 150 * S - 1, 150 * S - 1], fill=(228, 20, 60, 255)); d.ellipse([22 * S, 22 * S, 128 * S, 128 * S], fill=(236, 236, 238, 255))
        d.ellipse([40 * S, 40 * S, 110 * S, 110 * S], fill=(228, 20, 60, 255))
        ic = ic.resize((150, 150), Image.LANCZOS); place(ic, car_icon((255, 255, 255)), 75, 78, scale=0.8)
        place(c, ic, 140, 100); place(c, look("ZVG13", 64, ((40, 40, 46), (40, 40, 46)), shadow=False), 340, 100); s.card = c
    def draw(s, dst, t):
        p = seg(t, s.t0, 0.7); y = lerp(-140, 150, bounce_out(p)); k = s.out_k(t)
        place(dst, s.card, 360, y - 140 * k, alpha=1 - k)

# ======================================================== footage
@lru_cache(maxsize=6)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
@lru_cache(maxsize=6)
def src_matte(si): return Image.open(f"{MAT}/f_{si + 1:04d}.png").convert("L")
def camera(si, t, matte=False, push_extra=0.0):
    k = SHOT[si]; a, b, mode = SHOTS[k]; push = 1 + min(0.06, 0.006 * max(0.0, t - a)) + push_extra
    if mode == "T":
        z = 135 / HW[si] * push; cw, ch = W / z, H / z
        x0 = clamp(HX[si] - (W / 2) / z, 0, W - cw); y0 = clamp(HTOP[si] - 240 / z, 0, H - ch)
    else:
        z = 1.04 * push; cw, ch = W / z, H / z; x0, y0 = (W - cw) / 2, (H - ch) / 2
    box = (x0, y0, x0 + cw, y0 + ch)
    fr = src_frame(si).resize((W, H), Image.LANCZOS, box=box).filter(ImageFilter.UnsharpMask(2, 55, 2))
    mt = src_matte(si).resize((W, H), Image.BILINEAR, box=box) if matte else None
    return fr, mt
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.32 * (((_xx - 360) / 520) ** 2 + ((_yy - 600) / 800) ** 2), 0.55, 1)[..., None]
def grade(img):
    """reference look: warm-green, punchy, a little desaturated, vignette."""
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    a = np.clip((a - 0.5) * 1.1 + 0.5, 0, 1); g = a.mean(2, keepdims=True); a = g + (a - g) * 0.95
    a = a * np.array([1.0, 1.02, 0.95]) * VIG
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

# ======================================================== designed scenes
CAR = Image.open(CARCUT).convert("RGBA"); CAR = CAR.crop(CAR.getbbox())
_a = np.asarray(CAR.getchannel("A"), np.float32)                              # drop the faint matte haze around the car
_a = np.clip((_a - 70) / (255 - 70), 0, 1) * 255
CAR.putalpha(Image.fromarray(_a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))); CAR = CAR.crop(CAR.getbbox())
CAR_F = None
def ray_scene(t, t0, l1, l2):
    a = np.zeros((H, W, 3), np.float32); k = (_yy / H)[..., None]
    a[:] = np.array([206, 150, 242]) * (1 - k) + np.array([224, 182, 250]) * k
    img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    S = 2; R = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(R); cx, cy = 360 * S, 560 * S
    rot = (t - t0) * 9
    for i, col in enumerate([(255, 244, 150, 120), (150, 220, 255, 110), (232, 80, 230, 110), (255, 244, 150, 90), (150, 220, 255, 90)]):
        a0 = math.radians(rot + i * 72); a1 = a0 + math.radians(24); r = 2400
        d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=col)
    img.alpha_composite(R.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2)))
    # the source shot cuts the car at its right edge, so it enters from the right and that edge stays off-frame
    p = eo3(seg(t, t0, 0.5)); sc = lerp(1.08, 1.0, p) * 560 / CAR.height
    car = CAR.resize((int(CAR.width * sc), int(CAR.height * sc)), Image.LANCZOS)
    sh = Image.new("RGBA", (car.width + 80, car.height + 80), (0, 0, 0, 0)); sa = car.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.35))
    sl = Image.new("RGBA", car.size, (40, 0, 60, 0)); sl.putalpha(sa); sh.alpha_composite(sl, (40, 60))
    cx = W + 14 - car.width / 2 + 120 * (1 - p)
    place(img, sh, cx, 520 + 10); place(img, car, cx, 520, alpha=eo3(seg(t, t0, 0.2)))
    im1 = look(l1[0], fit(l1[0], 560, 52), ((90, 70, 240), (60, 40, 210)), shadow=False)
    typed_pop(img, im1, l1[0], l1[1], t, 360, 930, 0.02, spread=0.6)
    im2 = look(l2[0], fit(l2[0], 600, 104), ((168, 30, 210), (120, 10, 180)), shadow=False)
    typed_pop(img, im2, l2[0], l2[1], t, 360, 1030, 0.07, mode="drop")
    return img

def cream_bg():
    a = np.ones((H, W, 3), np.float32) * np.array([239, 235, 226], np.float32)
    for cx, cy, rx, ry, col, k in ((0, 0, 380, 420, (255, 214, 190), 0.6), (720, 0, 360, 380, (205, 236, 210), 0.5),
                                   (0, 1280, 360, 360, (255, 222, 200), 0.4), (720, 1280, 380, 380, (226, 214, 250), 0.4)):
        g = np.exp(-(((_xx - cx) / rx) ** 2 + ((_yy - cy) / ry) ** 2))[..., None]; a = a * (1 - k * g) + np.array(col) * k * g
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")
CREAM = cream_bg()

def pink_box(txt, size=40):
    ti = look(txt, size, ((20, 20, 20), (20, 20, 20)), shadow=False)
    w, h = 440, int(size * 1.55); im = Image.new("RGBA", (w + 10, h + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([5, 5, w + 5, h + 5], fill=(240, 182, 180, 255))
    for x in (5, w + 1): d.rectangle([x, 5, x + 4, h + 5], fill=(30, 30, 30, 255))
    d.line([(5, 5), (40, 5)], fill=(30, 30, 30, 255), width=2); d.line([(w - 30, h + 5), (w + 5, h + 5)], fill=(30, 30, 30, 255), width=2)
    return im, ti

def cream_list(t, header, items, big=None, sub=None):
    img = CREAM.copy()
    hi = look(header[0], fit(header[0], 560, 50), ((20, 20, 20), (20, 20, 20)), shadow=False)
    typed_pop(img, hi, header[0], header[1], t, 360, 300, 0.03)
    for i, (txt, tt) in enumerate(items):
        p = seg(t, tt, 0.26)
        if p <= 0: continue
        box, ti = pink_box(txt); y = 400 + i * 96
        place(img, box, 360, y, alpha=eo3(p * 3), scale=lerp(1.35, 1.0, eo3(p)))
        typed_pop(img, ti, txt, tt + 0.04, t, 360, y + 2, 0.012, spread=0.5)
    if big:
        b1 = look(big[0], fit(big[0], 600, 100), ((18, 18, 18), (18, 18, 18)), shadow=False); typed_pop(img, b1, big[0], big[1], t, 360, 860, 0.06, mode="drop")
    if sub:
        b2 = look(sub[0], fit(sub[0], 520, 84), ((150, 150, 150), (120, 120, 120)), shadow=False); typed_pop(img, b2, sub[0], sub[1], t, 400, 960, 0.06, mode="drop")
    return img

def offer_scene(t, t0, small, big, stamp_t):
    img = CREAM.copy(); p = seg(t, t0, 0.4); r = 230 * eoback(p, 1.6)
    if r > 1:
        S = 2; c = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); ImageDraw.Draw(c).ellipse([(360 - r) * S, (640 - r) * S, (360 + r) * S, (640 + r) * S], fill=(240, 190, 190, 255))
        img.alpha_composite(c.resize((W, H), Image.LANCZOS))
    i1 = look(small[0], fit(small[0], 380, 40), ((25, 25, 25), (25, 25, 25)), shadow=False); typed_pop(img, i1, small[0], small[1], t, 360, 590, 0.03)
    i2 = look(big[0], fit(big[0], 380, 110), ((15, 15, 15), (15, 15, 15)), shadow=False); typed_pop(img, i2, big[0], big[1], t, 360, 680, 0.07)
    q = seg(t, stamp_t, 0.3)
    if q > 0:
        tg = rr(230, 92, 16, (226, 32, 44, 255)); d = ImageDraw.Draw(tg); d.rounded_rectangle([6, 6, 224, 86], 12, outline=WHITE, width=3)
        place(tg, look("GRADE 4", 44, ((255, 255, 255), (255, 255, 255)), shadow=False), 115, 47)
        place(img, tg, 520, 760, alpha=eo3(q * 3), scale=lerp(2.0, 1.0, eo3(q)), angle=-24)
    return img

GRID = None
def grid_scene(t, t0):
    global GRID
    if GRID is None:
        G = Image.new("RGBA", (900, 1200), (250, 250, 250, 255))
        frames = [int(x * 25) for x in (16.2, 19.4, 21.0, 22.6, 28.0, 30.4)]
        for i, fi in enumerate(frames):
            ph = Image.open(f"{SRC}/f_{fi:04d}.png").convert("RGB").crop((0, 280, 720, 280 + 720 * 1.1)).resize((420, 370), Image.LANCZOS).convert("RGBA")
            ph.putalpha(rr(420, 370, 14, WHITE).getchannel("A")); G.alpha_composite(ph, (20 + (i % 2) * 440, 20 + (i // 2) * 390))
        GRID = G
    img = CREAM.copy(); p = seg(t, t0, 1.75); z = lerp(1.0, 1.35, ei2(p) * 0.6 + p * 0.4)
    cw, ch = 900 / z, 1200 / z; ox = lerp(0, 900 - cw, p * 0.6); oy = lerp(0, 1200 - ch, p)
    v = GRID.crop((int(ox), int(oy), int(ox + cw), int(oy + ch))).resize((500, 666), Image.LANCZOS)
    v.putalpha(rr(500, 666, 34, WHITE).getchannel("A"))
    sh = Image.new("RGBA", (560, 726), (0, 0, 0, 0)); sh.alpha_composite(rr(500, 666, 34, (30, 30, 30, 70)), (30, 40)); sh = sh.filter(ImageFilter.GaussianBlur(14))
    e = eo3(seg(t, t0, 0.35)); place(img, sh, 360, 640, alpha=e, scale=lerp(0.7, 1, e)); place(img, v, 360, 630, alpha=e, scale=lerp(0.7, 1, e))
    return img

CAR_FRONT = None
def address_scene(t, header, l1, l2):
    img = CREAM.copy(); global CAR_FRONT
    if CAR_FRONT is None:
        c = Image.open(CARCUT.replace("29.0", "16.4")).convert("RGBA"); CAR_FRONT = c.crop(c.getbbox())
    e = eo3(seg(t, header[1] - 0.3, 0.4)); car = CAR_FRONT.resize((560, int(CAR_FRONT.height * 560 / CAR_FRONT.width)), Image.LANCZOS)
    place(img, car, 360 + 40 * (1 - e), 470, alpha=e)
    hi = look(header[0], 40, ((120, 120, 120), (120, 120, 120)), shadow=False); typed_pop(img, hi, header[0], header[1], t, 360, 700, 0.03)
    b1 = look(l1[0], fit(l1[0], 620, 84), ((18, 18, 18), (18, 18, 18)), shadow=False); typed_pop(img, b1, l1[0], l1[1], t, 360, 790, 0.05, mode="drop")
    b2 = look(l2[0], fit(l2[0], 560, 70), ((140, 140, 140), (110, 110, 110)), shadow=False); typed_pop(img, b2, l2[0], l2[1], t, 380, 880, 0.05, mode="drop")
    return img

# ======================================================== energy / flash transitions
def energy(img, t, si, at, d=0.35):
    """green energy around the person (matte edge glow + expanding ring), then white."""
    p = seg(t, at - d, d)
    if p <= 0: return img
    _, mt = camera(si, t, True)
    big = mt.filter(ImageFilter.MaxFilter(int(9 + 26 * p) | 1)).filter(ImageFilter.GaussianBlur(12 + 30 * p))
    # glow lives AROUND the person (ref): remove the body itself, keep only the halo
    halo = np.clip(np.asarray(big, np.float32) * (0.5 + 1.2 * p) - np.asarray(mt, np.float32) * 0.85, 0, 255)
    glow = Image.new("RGBA", (W, H), (110, 255, 90, 0)); glow.putalpha(Image.fromarray(halo.astype(np.uint8)))
    img.alpha_composite(glow)
    rim = Image.new("RGBA", (W, H), (200, 255, 190, 0))
    rim.putalpha(Image.fromarray(np.clip(np.asarray(mt.filter(ImageFilter.MaxFilter(5)), np.float32) - np.asarray(mt, np.float32), 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)))
    img.alpha_composite(rim)
    S = 2; ring = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); r = 120 + 900 * eo3(p)
    ImageDraw.Draw(ring).ellipse([(360 - r) * S, (620 - r * 1.3) * S, (360 + r) * S, (620 + r * 1.3) * S], outline=(190, 255, 170, int(230 * (1 - p))), width=10 * S)
    ring = ring.resize((W, H), Image.LANCZOS); img.alpha_composite(ring.filter(ImageFilter.GaussianBlur(5))); img.alpha_composite(ring)
    if p > 0.6: img = Image.blend(img, Image.new("RGBA", (W, H), (246, 255, 244, 255)), eo3((p - 0.6) / 0.4))
    return img

def flash_in(img, t, at, col=(200, 255, 190), d=0.28):
    if at <= t < at + d: img = Image.blend(img, Image.new("RGBA", (W, H), col + (255,)), 0.8 * (1 - eo3(seg(t, at, d))))
    return img

# ======================================================== edit decision list
E = []
def add(el): E.append(el); return el
# talking 0 - 5.3
add(Cap(820, 0.92, l1=("আপনারা কিন্তু", wt("আপনারা"), "white"), l2=("ইতোমধ্যেই", wt("ইতোমধ্যেই"), "orange"), icon=(car_icon(), wt("ইতোমধ্যেই") + 0.2, "l1")))
add(Cap(820, 3.36, l1=("আমাদের", wt("আমাদের"), "green"), l2=("চিটাগাং স্টকের", wt("চিটাগাং"), "green")))
add(Cap(820, 4.46, l1=("করোলা ক্রস", wt("করোলা"), "cyan"), l2=("সম্পর্কে ধারণা", wt("সম্পর্কে"), "white"), box2="blue", s1=74, s2=54))
add(Cap(820, 5.30, l1=("ধারণা", wt("ধারণা"), "lgreen"), l2=("চলে এসেছে!", wt("চলে"), "yellow"), box2="red", icon=(bang_icon(), wt("চলে") + 0.15, "l1"), s2=66))
# talk 7.62 - 10.3 with callout pills
add(Pills([("রেডি স্টক", wt("রেডি"), 190, 620, -8, 34), ("অ্যাভেলেবল", wt("অ্যাভেলেবল"), 530, 560, 6, 30)], 10.20))
add(Cap(900, 10.24, l2=("সাথে কিন্তু আমাদের শোরুমেও", wt("সাথে"), "cyan"), s2=52))
# cutaway b-roll 10.3 - 12.9
add(Pills([("Pearl White", wt("পার্ল"), 360, 330, -6, 62)], 11.85, event="pill"))
add(Pills([("Pearl", 11.90, 210, 140, -5, 30), ("Black", wt("ব্ল্যাক"), 520, 140, 5, 30)], 12.86, event="tag"))
add(Ring(wt("কালার", 1) - 0.1, 12.86, 380, 560, 270))
# talk 12.9 - 15.4
add(Cap(820, 15.30, l1=("দুইটাই কিন্তু", wt("দুইটাই"), "white"), l2=("অ্যাভেলেবল", wt("অ্যাভেলেবল", 1), "gold")))
add(Pills([("পার্ল", wt("পেয়ে"), 280, 1010, -6, 30), ("ব্ল্যাক", wt("যাচ্ছেন"), 450, 1018, 5, 30)], 15.30, event="tag"))
# b-roll 15.4 - 23.8
add(Cap(880, 17.25, l1=("আমার সামনে যে গাড়িটা", wt("আমার"), "white"), l2=("দেখতেছেন", wt("দেখতেছেন"), "green")))
add(Cap(880, 20.55, l1=("ZVG13 এর", wt("ZVG13"), "white"), l2=("2023 মডেল", wt("2023"), "gold")))
add(Cap(880, 22.36, l1=("পার্ল কালার টু টোন", wt("পার্ল", 1), "white"), l2=("উপরে হার্ড টপ", wt("উপরে"), "lime"), box1="lime", s1=46))
add(Cap(880, 23.75, l1=("এবং", wt("এবং", 1), "white"), l2=("মডেলিস্টা বডি কিট", wt("মডেলিস্টা"), "white"), s2=70))
# talk 23.8 - 26.9
add(LogoCard(24.20, 26.85))
add(Cap(860, 26.05, l1=("গাড়িটির সঙ্গে কিন্তু", wt("গাড়িটির"), "yellow"), l2=("অটো পার্কিং", wt("অটো"), "red"), brand=True))
add(Cap(860, 26.85, l2=("360 ক্যামেরা", wt("360"), "red"), brand=True))
# talk 31.64 - 33.95
add(Cap(840, 33.95, l1=("গাড়িটির মাইলেজ আছে মাত্র", wt("গাড়িটির", 1), "white"), l2=("33,000 কিলো", wt("33,000"), "green")))
# talk 35.64 - 37.2
add(Cap(840, 37.16, l1=("দেরি না করে", wt("দেরি"), "lgreen"), l2=("আজই ভিজিট করুন", wt("আজই"), "yellow"), box2="red", icon=(bang_icon(), wt("ভিজিট"), "l1"), s2=62))
# ending talk 40.85 -
add(Cap(860, 99, l1=("আব্দুল হামিদ রোড, পাবনা সদর", 40.95, "white"), l2=("পাবনা", wt("পাবনা", 1), "green"), s1=40))

RAY = (5.55, 7.62); CUT = (10.30, 12.90); CR1 = (26.97, 31.64); OFF = (33.95, 35.64); GRD = (37.20, 38.95); CR2 = (38.95, 40.85)
RAY_L1 = ("বেশ কয়েকটি ইউনিট", wt("কয়েকটি")); RAY_L2 = ("চিটাগাং স্টকে", wt("আমাদের", 1))
CR1_H = ("সাথে যা যা পাচ্ছেন", 27.20)
CR1_I = [("Alloy Wheels", 27.45), ("Fog Light", wt("ফগ")), ("Seat Heater", wt("সিট")), ("Cruise Control", wt("ক্রুজ"))]
CR1_B = ("সবকিছুই", wt("সবকিছুই")); CR1_S = ("পাচ্ছেন", wt("পাচ্ছেন"))
OFF_S = ("অকশন গ্রেড রয়েছে", wt("অকশন")); OFF_B = ("ফোর", wt("ফোর"))
CR2_H = ("শোরুমের ঠিকানা", wt("শোরুমের")); CR2_1 = ("আব্দুল হামিদ রোড", wt("আব্দুল")); CR2_2 = ("পাবনা সদর, পাবনা", wt("পাবনা"))
# scene-internal sound cues
cue("head_line", RAY_L1[1]); cue("two_tone", RAY_L2[1])
cue("head_line", CR1_H[1])
for _, tt in CR1_I: cue("stamp_box", tt)
cue("two_tone", CR1_B[1]); cue("line1", CR1_S[1])
cue("circle_pop", OFF[0]); cue("line1", OFF_S[1]); cue("line2", OFF_B[1]); cue("offer_stamp", OFF_B[1] + 0.06)
cue("head_line", CR2_H[1]); cue("two_tone", CR2_1[1]); cue("line1", CR2_2[1])
# transitions
for at, ev in ((RAY[0], "energy_out"), (RAY[1], "flash_in"), (CUT[0], "scene"), (CUT[1], "flash_in"), (15.40, "scene"),
               (CR1[0], "scene"), (CR1[1], "flash_in"), (OFF[0], "scene"), (OFF[1], "flash_in"), (GRD[0], "scene"),
               (CR2[0], "scene"), (CR2[1], "energy_out")):
    cue(ev, at)

def render(fi):
    t = fi / FPS; si = min(int(t * SRC_FPS), NSRC - 1)
    if RAY[0] <= t < RAY[1]: img = ray_scene(t, RAY[0], RAY_L1, RAY_L2)
    elif CR1[0] <= t < CR1[1]: img = cream_list(t, CR1_H, CR1_I, CR1_B, CR1_S)
    elif OFF[0] <= t < OFF[1]: img = offer_scene(t, OFF[0], OFF_S, OFF_B, OFF_B[1] + 0.06)
    elif GRD[0] <= t < GRD[1]: img = grid_scene(t, GRD[0])
    elif CR2[0] <= t < CR2[1]: img = address_scene(t, CR2_H, CR2_1, CR2_2)
    else:
        if CUT[0] <= t < CUT[1]:
            cs = min(int((27.40 + (t - CUT[0])) * SRC_FPS), NSRC - 1); img = grade(camera(cs, t, push_extra=0.04)[0])
        else:
            fast = 0.10 * seg(t, 22.4, 1.4) if 22.4 <= t < 23.8 else 0.0
            img = grade(camera(si, t, push_extra=fast)[0])
            if t < 0.13:                                         # opening white silhouette
                _, mt = camera(si, t, True); wl = Image.new("RGBA", (W, H), WHITE)
                wl.putalpha(mt.point(lambda v: int(v * (1 - eo3(seg(t, 0.05, 0.08)))))); img.alpha_composite(wl)
        for el in E:
            if el.live(t): el.draw(img, t)
        if RAY[0] - 0.36 <= t < RAY[0]: img = energy(img, t, si, RAY[0])
        if CR2[1] - 0.36 <= t < CR2[1]: pass
    if CR2[1] - 0.36 <= t < CR2[1]:                              # white burst out of the address scene
        img = Image.blend(img, Image.new("RGBA", (W, H), (246, 255, 244, 255)), eo3(seg(t, CR2[1] - 0.36, 0.36)))
    for at in (RAY[0], CR1[0], OFF[0], GRD[0], CR2[0], 15.40, CUT[0]):
        if at <= t < at + 0.14: img = Image.blend(Image.new("RGBA", (W, H), (250, 250, 248, 255)), img, eo3(seg(t, at, 0.14)))
    for at in (RAY[1], CUT[1], CR1[1], OFF[1], CR2[1]): img = flash_in(img, t, at)
    for at in (CR1[0], OFF[0], GRD[0], 15.40, CUT[0], CR2[0]):   # whoosh cuts: blur ramps up into the cut
        if at - 0.2 <= t < at:
            img = img.filter(ImageFilter.GaussianBlur(12 * ei2(seg(t, at - 0.2, 0.2))))
    return img.convert("RGB").tobytes()

if __name__ == "__main__":
    json.dump(CUES, open(OUT.rsplit(".", 1)[0] + "_cues.json", "w"), ensure_ascii=False, indent=0)
    print(len(CUES), "sound cues")
    if PREVIEW:
        for ts in PREVIEW: Image.frombytes("RGB", (W, H), render(int(round(float(ts) * FPS)))).save(f"{OUT}_{ts}.png")
        print("previews:", ", ".join(PREVIEW)); sys.exit(0)
    n = int(DUR * FPS)
    # 4:5 delivery like the reference: 9:16 picture in the middle, blurred stretched copy on the sides
    ff = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-filter_complex", "[0:v]split[a][b];[b]scale=1024:1280,boxblur=36:2,eq=brightness=-0.02:saturation=1.05[bg];[bg][a]overlay=152:0[v]",
        "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=6)):
            ff.stdin.write(buf)
            if i % 250 == 0: print(f"  frame {i}/{n}", flush=True)
    ff.stdin.close(); ff.wait(); print("done ->", OUT, "exit", ff.returncode)
