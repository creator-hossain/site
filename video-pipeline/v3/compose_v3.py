# -*- coding: utf-8 -*-
"""Corolla Cross edit in the style of reference #3 (dark talking head + pastel UI scenes).

Measured from the reference, frame by frame:
  captions: small white line blurs in (~125 ms); big cyan line rises + blurs in with a
            cyan glow (~250 ms); yellow pill pops with overshoot
  pastel:   near-white bg with soft colour blobs; white cards w/ soft shadow; header fades,
            titles blur in, underline grows from the centre, bars/lines draw left->right,
            icons/pills pop with overshoot, red-playhead waveform
  frame:    footage shrinks into a cyan-glowing rounded frame, badge + button pop
  cuts:     talk->pastel = cyan wash then white; pastel->talk = zoom-blur then warm leak
usage: compose_v3.py SRC_DIR TRACK WORDS SOURCE_VIDEO OUT [--preview t1,t2,..]
"""
import sys, json, subprocess, math
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, TRACK, WORDS, SRC_VIDEO, OUT = sys.argv[1:6]
PREVIEW = sys.argv[7].split(",") if len(sys.argv) > 7 and sys.argv[6] == "--preview" else None

FPS, SRC_FPS = 50, 25
W, H = 720, 1280
ANEK800 = "/usr/share/fonts/truetype/bnx/AnekBN.ttf"
ANEK700 = "/usr/share/fonts/truetype/bnx/anek-bangla-bengali-700-normal.ttf"
INTER_B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
INTER_M = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
INTER_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
SX = 0.90                                  # reference Bangla ~90% of Anek's width

# sampled palette
CYAN = (56, 255, 250, 255); GLOW = (53, 255, 252, 255)
YELLOW = (252, 249, 95, 255); HILITE = (249, 200, 119, 255)
TEAL = (49, 207, 211, 255); TEAL_TXT = (39, 155, 170, 255)
ORANGE = (247, 176, 61, 255); PURPLE = (118, 41, 227, 255)
RED = (222, 49, 71, 255); INK = (20, 20, 24, 255); GREY = (110, 112, 122, 255)
WHITE = (255, 255, 255, 255); DARK_BG = (6, 14, 22); BADGE = (30, 38, 52, 255)
PASTEL = (248, 248, 251); BEIGE = (238, 237, 228)

TR = json.load(open(TRACK)); HX, HTOP, HW, SHOT, SHOTS = TR["hx"], TR["htop"], TR["hw"], TR["shot"], TR["shots"]
NSRC = len(HX); DUR = NSRC / SRC_FPS
WT = {}
for w in json.load(open(WORDS, encoding="utf-8")): WT.setdefault(w["w"], []).append(w["t"])
def wt(word, n=0): return WT[word][n]

# ============================================================ helpers
def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def ei2(p): p = clamp(p, 0, 1); return p * p
def eoback(p, s=1.8):
    p = clamp(p, 0, 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def seg(t, a, d): return clamp((t - a) / d, 0, 1)
def is_bn(s): return any("ঀ" <= c <= "৿" for c in s)

@lru_cache(maxsize=None)
def font(path, size): return ImageFont.truetype(path, size)

@lru_cache(maxsize=None)
def text_img(txt, size, fill, path=None, sx=None, stroke=0, stroke_fill=None, shadow=None):
    """metric-box text image; shadow=(dy, alpha, blur)."""
    if path is None: path = ANEK800 if is_bn(txt) else INTER_B
    if sx is None: sx = SX if is_bn(txt) else 1.0
    f = font(path, size); asc, desc = f.getmetrics()
    pad = stroke + 10 + (shadow[2] * 3 if shadow else 0)
    vpad = pad + int(size * 0.2)
    adv = f.getlength(txt)
    w, h = int(adv + 2 * pad), int(asc + desc + 2 * vpad)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        S = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(S).text((pad, vpad + shadow[0]), txt, font=f, fill=(0, 0, 0, shadow[1]),
                               stroke_width=stroke, stroke_fill=(0, 0, 0, shadow[1]))
        out.alpha_composite(S.filter(ImageFilter.GaussianBlur(shadow[2])))
    L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(L).text((pad, vpad), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    out.alpha_composite(L)
    if sx != 1: out = out.resize((max(1, int(w * sx)), h), Image.LANCZOS)
    out.info["adv"] = adv * sx; out.info["px"] = pad * sx
    return out

def fit(txt, maxw, hi=200, lo=24, path=None):
    if path is None: path = ANEK800 if is_bn(txt) else INTER_B
    sx = SX if is_bn(txt) else 1.0
    for s in range(hi, lo - 1, -2):
        if font(path, s).getlength(txt) * sx <= maxw: return s
    return lo

@lru_cache(maxsize=None)
def glow_text(txt, size):
    """big cyan caption: soft cyan glow + dark drop shadow + fill (reference)."""
    base = text_img(txt, size, CYAN, stroke=2, stroke_fill=(0, 120, 120, 255), shadow=(4, 200, 6))
    a = base.getchannel("A")
    g = Image.new("RGBA", base.size, (GLOW[0], GLOW[1], GLOW[2], 0)); g.putalpha(a.point(lambda v: int(v * 0.85)))
    g = g.filter(ImageFilter.GaussianBlur(12))
    out = Image.new("RGBA", base.size, (0, 0, 0, 0)); out.alpha_composite(g); out.alpha_composite(base)
    out.info.update(base.info); return out

def blurred(im, r):
    if r < 0.4: return im
    pad = int(r * 3)
    big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(im, (pad, pad)); b = big.filter(ImageFilter.GaussianBlur(r)); b.info.update(im.info)
    return b

def place(dst, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0):
    if alpha <= 0.004: return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.996:
        a = (np.asarray(im.getchannel("A"), np.float32) * alpha).astype(np.uint8)
        im = im.copy(); im.putalpha(Image.fromarray(a))
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 > x0 and y1 > y0: dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def rr(w, h, r, fill, ss=3, outline=None, width=0):
    im = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=fill,
                                         outline=outline, width=int(width * ss))
    return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)

@lru_cache(maxsize=None)
def card(w, h, r=22):
    """white card with the reference's soft drop shadow."""
    pad = 46
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); sh.alpha_composite(rr(w, h, r, (40, 40, 80, 46)), (pad, pad + 12))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    out.alpha_composite(rr(w, h, r, WHITE), (pad, pad))
    return out

def card_at(dst, x0, y0, w, h, alpha=1.0, dy=0.0, scale=1.0, r=22):
    c = card(int(w), int(h), r); place(dst, c, x0 + w / 2, y0 + h / 2 + dy, alpha=alpha, scale=scale)

def pill(txt, size, fill, tcol, padx=26, h=None, path=None, ring=None):
    ti = text_img(txt, size, tcol, path=path)
    hh = h or int(size * 1.7); ww = int(ti.info["adv"] + 2 * padx)
    if ring:
        P = rr(ww + 2 * ring[1], hh + 2 * ring[1], (hh + 2 * ring[1]) / 2, ring[0])
        P.alpha_composite(rr(ww, hh, hh / 2, fill), (ring[1], ring[1])); off = ring[1]
    else:
        P = rr(ww, hh, hh / 2, fill); off = 0
    place(P, ti, off + ww / 2, off + hh / 2 + 1)
    return P

# ============================================================ footage
@lru_cache(maxsize=6)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")

def camera(si, t, kind="talk"):
    k = SHOT[si]; a, b, mode = SHOTS[k]
    push = 1 + min(0.05, 0.005 * (t - a))
    if mode == "T" and kind == "talk":
        z = 140 / HW[si] * push
        cw, ch = W / z, H / z
        x0 = clamp(HX[si] - (W / 2) / z, 0, W - cw); y0 = clamp(HTOP[si] - 250 / z, 0, H - ch)
    else:
        z = (1.05 if kind == "talk" else 1.0) * push
        cw, ch = W / z, H / z; x0 = (W - cw) / 2; y0 = (H - ch) / 2
    fr = src_frame(si).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    return fr.filter(ImageFilter.UnsharpMask(radius=2, percent=60 if z > 1.5 else 30, threshold=2))

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r2 = ((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H * 0.45) / (H * 0.62)) ** 2
VIGN = np.clip(1 - 0.70 * _r2, 0.18, 1)[..., None]
BOTTOM = np.clip((_yy - H * 0.58) / (H * 0.32), 0, 1)[..., None] ** 1.4
def grade(img):
    """reference look: darker, cooler shadows, strong vignette, dark floor for captions."""
    a = np.asarray(img, np.float32) / 255
    a = np.clip((a - 0.5) * 1.15 + 0.5, 0, 1) * 0.66
    a = a * VIGN * (1 - 0.55 * BOTTOM)
    a = a + np.array([-0.01, 0.006, 0.018]) * (1 - a)       # teal shadows
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

# ============================================================ backgrounds
def _pastel(base, blobs):
    a = np.ones((H, W, 3), np.float32) * np.array(base, np.float32)
    for cx, cy, rx, ry, col, k in blobs:
        g = np.exp(-(((_xx - cx) / rx) ** 2 + ((_yy - cy) / ry) ** 2))[..., None]
        a = a * (1 - k * g) + np.array(col, np.float32) * k * g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
PASTEL_BG = _pastel(PASTEL, [(80, 180, 320, 300, (210, 240, 238), 0.55), (660, 260, 330, 320, (232, 222, 250), 0.6),
                             (380, 1180, 420, 300, (252, 240, 215), 0.55), (700, 900, 260, 260, (232, 226, 250), 0.35)])
BEIGE_BG = _pastel(BEIGE, [(360, 520, 520, 520, (244, 243, 236), 0.6)])
def _darkbg():
    a = np.ones((H, W, 3), np.float32) * np.array(DARK_BG, np.float32)
    g = np.exp(-(((_xx - 360) / 520) ** 2 + ((_yy - 560) / 700) ** 2))[..., None]
    a = a + np.array([4, 26, 34], np.float32) * g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
DARK_BG_IMG = _darkbg()

def drift(bg, t):
    """very slow drift so the pastel world breathes (reference blobs float)."""
    dx = 10 * math.sin(t * 0.6); dy = 8 * math.cos(t * 0.45)
    return bg.resize((W, H), Image.BILINEAR, box=(20 + dx, 20 + dy, W - 20 + dx, H - 20 + dy))

# ============================================================ caption layer (talking scenes)
SMALL_Y, BIG_Y, PILL_Y = 880, 962, 1062
def cap_small(dst, txt, t0, t, y=SMALL_Y, size=40):
    if t < t0: return
    im = text_img(txt, size, WHITE, path=ANEK700, shadow=(3, 190, 5))
    e = eo3(seg(t, t0, 0.13)); place(dst, blurred(im, 9 * (1 - e)), 360, y, alpha=e)
def cap_big(dst, txt, t0, t, y=BIG_Y):
    if t < t0: return
    im = glow_text(txt, fit(txt, 640, hi=82))
    e = eo3(seg(t, t0, 0.26)); place(dst, blurred(im, 10 * (1 - e)), 360, y + 46 * (1 - e), alpha=min(1, e * 1.4))
def cap_pill(dst, txt, t0, t, y=PILL_Y):
    if t < t0: return
    P = pill(txt, 40, YELLOW, INK, h=64, ring=((40, 40, 20, 255), 2))
    p = seg(t, t0, 0.24)
    place(dst, P, 360, y, alpha=eo3(p * 3), scale=lerp(0.35, 1.0, eoback(p, 2.2)))

def talk_frame(t, si, caps):
    img = grade(camera(si, t, "talk"))
    for c in caps: c(img, t)
    return img

# ============================================================ badge
BADGE_IMG = None
def badge_img():
    global BADGE_IMG
    if BADGE_IMG is None:
        ti = text_img("করোলা ক্রস • ZVG13", 28, WHITE, path=ANEK800)    # merged font: Bangla + Latin + •
        w, h = int(ti.info["adv"] + 66), 46
        P = rr(w + 4, h + 4, (h + 4) / 2, (120, 130, 150, 160)); P.alpha_composite(rr(w, h, h / 2, BADGE), (2, 2))
        d = ImageDraw.Draw(P); d.ellipse([22, h / 2 - 3, 32, h / 2 + 7], fill=(80, 220, 140, 255))
        place(P, ti, 2 + 40 + ti.info["adv"] / 2, 2 + h / 2 + 1); BADGE_IMG = P
    return BADGE_IMG
BADGE_IN, BADGE_MOVE = wt("ZVG13"), 20.60
def draw_badge(dst, t):
    if t < BADGE_IN: return
    B = badge_img()
    if t < BADGE_MOVE:
        p = seg(t, BADGE_IN, 0.22); place(dst, B, 360, 96, alpha=eo3(p * 2), scale=lerp(0.5, 1, eoback(p)))
    else:
        e = eo3(seg(t, BADGE_MOVE, 0.40))
        place(dst, B, lerp(360, W - B.width / 2 - 26, e), lerp(96, 62, e))

# ============================================================ scenes
def sc_logo(t, si):
    """ripple ring from a dot, car photo pops in the circle, wordmark wipes in."""
    img = BEIGE_BG.copy(); d = ImageDraw.Draw(img); cx, cy = 360, 500
    t0 = 3.30
    q = seg(t, t0, 0.9); r = lerp(4, 330, eo3(q))
    if q < 1: d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(207, 110, 88, int(150 * (1 - q))), width=3)
    p = seg(t, t0 + 0.05, 0.38)
    if p > 0:
        ph = CAR_PHOTO.copy(); m = Image.new("L", ph.size, 0)
        ImageDraw.Draw(m).ellipse([0, 0, ph.width - 1, ph.height - 1], fill=255); ph.putalpha(m)
        ring = Image.new("RGBA", (ph.width + 16, ph.height + 16), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse([0, 0, ring.width - 1, ring.height - 1], fill=WHITE); ring.alpha_composite(ph, (8, 8))
        place(img, ring, cx, cy, alpha=eo3(p * 2.5), scale=lerp(0.2, 1, eoback(p)), angle=lerp(-25, 0, eo3(p)))
    wm = text_img("Corolla Cross", 84, (38, 38, 38, 255), path=INTER_B)
    w = seg(t, wt("করোলা"), 0.42)
    if w > 0:
        cut = int(wm.width * eo3(w)); part = wm.crop((0, 0, max(1, cut), wm.height))
        img.alpha_composite(part, (int(360 - wm.width / 2), int(760 - wm.height / 2)))
    place(img, text_img("Toyota", 34, (150, 140, 120, 255), path=INTER_SB), 360, 682, alpha=eo3(seg(t, wt("করোলা"), 0.3)))
    sub = text_img("সম্পর্কে ধারণা চলে এসেছে", 40, GREY, path=ANEK700)
    e = eo3(seg(t, wt("সম্পর্কে"), 0.25)); place(img, sub, 360, 860 + 14 * (1 - e), alpha=e)
    return img

def check_badge(col):
    S = 3; im = Image.new("RGBA", (44 * S, 44 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 44 * S - 1, 44 * S - 1], fill=col)
    d.line([(12 * S, 23 * S), (19 * S, 30 * S), (32 * S, 15 * S)], fill=WHITE, width=5 * S, joint="curve")
    return im.resize((44, 44), Image.LANCZOS)
CHECK = None

def sc_compare(t, si):
    global CHECK
    if CHECK is None: CHECK = check_badge(TEAL)
    img = drift(PASTEL_BG, t)
    e = eo3(seg(t, wt("সাথে"), 0.25))
    place(img, text_img("আমাদের শোরুমেও", 46, TEAL_TXT), 360, 214 + 10 * (1 - e), alpha=e)
    for i, (lab, cap, t_in, t_ok, sw) in enumerate([
            ("Pearl White", "পার্ল কালার", wt("পার্ল"), wt("কালার"), ((246, 246, 244), (214, 214, 220), (255, 255, 255))),
            ("Black", "ব্ল্যাক কালার", wt("ব্ল্যাক"), wt("কালার", 1), ((40, 42, 48), (8, 9, 12), (90, 94, 104)))]):
        y0 = 300 + i * 420
        p = seg(t, t_in - 0.30, 0.30)
        if p <= 0: continue
        a = eo3(p); dy = 30 * (1 - a)
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        card_at(L, 100, y0, 520, 270, dy=0)
        place(L, text_img(lab, 30, INK, path=INTER_SB), 100 + 34 + text_img(lab, 30, INK, path=INTER_SB).info["adv"] / 2, y0 + 44)
        # paint sweep (reference: the line inside the card draws left->right)
        q = eo3(seg(t, t_in - 0.12, 0.55)); bw = int(440 * q)
        if bw > 4:
            g = np.linspace(0, 1, 440)[None, :, None]
            c0, c1, c2 = (np.array(c, np.float32) for c in sw)
            band = c0 * (1 - g) + c1 * g
            hl = np.exp(-((np.linspace(0, 1, 120)[:, None, None] - 0.28) / 0.12) ** 2)
            strip = band * (1 - 0.6 * hl) + c2 * 0.6 * hl
            S = Image.fromarray(np.clip(np.broadcast_to(strip, (120, 440, 3)), 0, 255).astype(np.uint8)).convert("RGBA")
            m = rr(440, 120, 26, WHITE).getchannel("A"); S.putalpha(m)
            S = S.crop((0, 0, bw, 120))
            ol = rr(440, 120, 26, (0, 0, 0, 0), outline=(0, 0, 0, 30), width=1.5).crop((0, 0, bw, 120))
            S.alpha_composite(ol); L.alpha_composite(S, (140, y0 + 100))
        c = seg(t, t_ok, 0.22)
        if c > 0: place(L, CHECK, 100 + 520 - 40, y0 + 42, alpha=eo3(c * 3), scale=lerp(0.2, 1, eoback(c, 2.4)))
        ce = eo3(seg(t, t_ok, 0.25))
        place(L, text_img(cap, 42, INK), 360, y0 + 316 + 8 * (1 - ce), alpha=ce)
        place(img, L, 360, 640 + dy, alpha=a)
    return img

FRAME = (70, 190, 650, 1020, 26)
def glow_frame(img, box, alpha=1.0):
    x0, y0, x1, y1, r = box
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], radius=r + 2, outline=GLOW[:3] + (int(255 * alpha),), width=4)
    g = L.filter(ImageFilter.GaussianBlur(14)); g2 = L.filter(ImageFilter.GaussianBlur(5))
    img.alpha_composite(g); img.alpha_composite(g2); img.alpha_composite(L)

def sc_frame(t, si):
    """footage shrinks into the glowing frame; badge on top, cyan button below."""
    t0 = 16.95; p = eo3(seg(t, t0, 0.34))
    box = tuple(lerp(a, b, p) for a, b in zip((0, 0, W, H, 0), FRAME))
    img = DARK_BG_IMG.copy()
    fr = grade(camera(si, t, "broll"))
    if t < t0 + 0.12:                                   # still blurred from the glow transition
        fr = fr.filter(ImageFilter.GaussianBlur(lerp(10, 0, seg(t, t0, 0.12))))
    x0, y0, x1, y1, r = box
    bw, bh = int(x1 - x0), int(y1 - y0)
    ch = min(H, W * bh / bw)                         # cover-fit: crop source height to the box aspect
    sub = fr.resize((bw, bh), Image.LANCZOS, box=(0, (H - ch) / 2, W, (H + ch) / 2))
    m = rr(sub.width, sub.height, r, WHITE).getchannel("A"); sub.putalpha(m)
    img.alpha_composite(sub, (int(x0), int(y0)))
    if p > 0.05: glow_frame(img, (int(x0), int(y0), int(x1), int(y1), r), alpha=p)
    b = seg(t, wt("2023"), 0.24)
    if b > 0:
        P = pill("2023 মডেল", 38, GLOW, (6, 30, 36, 255), padx=60, h=66)
        place(img, P, 360, 1090, alpha=eo3(b * 3), scale=lerp(0.4, 1, eoback(b, 2.0)))
    return img

def sc_spec(t, si):
    """header blur-in, prompt box types, timeline bars grow, playhead, Editing... -> Done."""
    img = drift(PASTEL_BG, t)
    h = eo3(seg(t, wt("পার্ল", 1), 0.16))
    place(img, blurred(text_img("পার্ল কালার টু টোন", fit("পার্ল কালার টু টোন", 600, hi=66), INK), 9 * (1 - h)), 360, 236, alpha=h)
    # prompt box
    pb = eo3(seg(t, 20.80, 0.3))
    if pb > 0:
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        L.alpha_composite(rr(600, 96, 48, (196, 180, 246, 255)), (60, 330))
        L.alpha_composite(rr(586, 82, 41, WHITE), (67, 337))
        msg = "ZVG13 · 2023 · Two-Tone"; n = int(len(msg) * seg(t, 20.95, 0.75))
        if n > 0:
            ti = text_img(msg[:n], 30, (40, 40, 48, 255), path=INTER_M); L.alpha_composite(ti, (int(100 - ti.info["px"]), int(378 - ti.height / 2)))
        d = ImageDraw.Draw(L); d.ellipse([588, 352, 640, 404], fill=(18, 18, 22, 255))
        d.polygon([(607, 365), (607, 391), (628, 378)], fill=WHITE)
        place(img, L, 360, 640 + 18 * (1 - pb), alpha=pb)
    # timeline card
    tc = eo3(seg(t, 21.55, 0.3))
    if tc > 0:
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        card_at(L, 50, 500, 620, 430)
        rows = [("হার্ড টপ", TEAL, wt("হার্ড")), ("মডেলিস্টা", ORANGE, wt("মডেলিস্টা")), ("বডি কিট", PURPLE, wt("বডি"))]
        for i, (lab, col, t_in) in enumerate(rows):
            y = 610 + i * 104
            ImageDraw.Draw(L).line([(90, y + 44), (630, y + 44)], fill=(236, 236, 242, 255), width=2)
            q = eo3(seg(t, t_in, 0.40)); bw = int(500 * q)
            if bw > 6:
                B = rr(500, 58, 14, col).crop((0, 0, bw, 58)); L.alpha_composite(B, (110, y - 29))
                ti = text_img(lab, 34, WHITE); a = eo3(seg(t, t_in + 0.12, 0.2))
                if a > 0: place(L, ti, 110 + 22 + ti.info["adv"] / 2, y, alpha=a)
        ph = 110 + 500 * eo3(seg(t, 21.9, 1.7))
        d = ImageDraw.Draw(L); d.line([(ph, 560), (ph, 906)], fill=(240, 120, 140, 200), width=4)
        d.ellipse([ph - 7, 552, ph + 7, 566], fill=(240, 120, 140, 230))
        done = t >= wt("সহ")
        P = pill("Done ✓" if done else "Editing…", 24, (92, 205, 140, 255) if done else ORANGE, WHITE if done else INK,
                 padx=18, h=42, path=INTER_SB)
        ps = lerp(0.6, 1, eoback(seg(t, wt("সহ"), 0.2))) if done else 1.0
        place(L, P, 560, 540, scale=ps)
        place(img, L, 360, 640 + 24 * (1 - tc), alpha=tc)
    return img

PILLS = [("অ্যালয় হুইলস", TEAL, 27.55, 150, 862), ("ফগ লাইট", ORANGE, wt("ফগ"), 300, 912),
         ("সিট হিটার", TEAL, wt("সিট"), 440, 862), ("ক্রুজ কন্ট্রোল", ORANGE, wt("ক্রুজ"), 584, 912)]
def sc_wave(t, si):
    img = drift(PASTEL_BG, t)
    title = "সবকিছুই পাচ্ছেন"; ts = fit(title, 600, hi=76)
    h = eo3(seg(t, 27.30, 0.16))
    hl = seg(t, wt("সবকিছুই"), 0.30)
    if hl > 0:                                          # yellow highlight wipes in behind (reference 'হাইপে')
        tw = text_img(title, ts, INK).info["adv"]; bw = int((tw + 40) * eo3(hl))
        if bw > 2: img.alpha_composite(rr(tw + 40, 86, 12, HILITE).crop((0, 0, bw, 86)), (int(360 - (tw + 40) / 2), 186))
    place(img, blurred(text_img(title, ts, INK), 9 * (1 - h)), 360, 230, alpha=h)
    c = eo3(seg(t, 27.40, 0.30))
    if c > 0:
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        card_at(L, 50, 310, 620, 470)
        fr = grade(camera(si, t, "broll")).convert("RGB")
        sub = fr.resize((588, 438), Image.LANCZOS, box=(0, 330, W, 330 + W * 438 / 588)).convert("RGBA")
        sub.putalpha(rr(588, 438, 16, WHITE).getchannel("A")); L.alpha_composite(sub, (66, 326))
        card_at(L, 50, 990, 620, 130)
        # waveform: bars revealed by the playhead
        x_ph = waveform_playhead(t)
        rng = np.random.RandomState(7); d = ImageDraw.Draw(L)
        for i, x in enumerate(range(80, 640, 10)):
            if x > x_ph: break
            amp = 10 + 34 * abs(math.sin(i * 0.55)) * (0.5 + 0.5 * rng.rand())
            col = PURPLE if (i % 3) else TEAL
            d.rounded_rectangle([x - 3, 1055 - amp / 2, x + 3, 1055 + amp / 2], radius=3, fill=col)
        d.line([(x_ph, 1000), (x_ph, 1110)], fill=(240, 120, 140, 220), width=4)
        for lab, col, t_in, x, y in PILLS:
            p = seg(t, t_in, 0.24)
            if p <= 0: continue
            s = eo3(seg(t, t_in + 0.06, 0.25))
            d.line([(x, y + 24), (x, y + 24 + (1000 - y - 24) * s)], fill=col[:3] + (200,), width=2)
            P = pill(lab, 30, col, INK if col == ORANGE else (8, 40, 44, 255), padx=20, h=50)
            place(L, P, x, y, alpha=eo3(p * 3), scale=lerp(0.3, 1, eoback(p, 2.2)))
        place(img, L, 360, 640 + 24 * (1 - c), alpha=c)
    return img
def waveform_playhead(t):
    pts = [(27.40, 80)] + [(p[2], p[3]) for p in PILLS] + [(31.50, 640)]
    for (ta, xa), (tb, xb) in zip(pts, pts[1:]):
        if t < tb: return lerp(xa, xb, eo3(seg(t, ta, max(0.01, min(0.35, tb - ta)))))
    return 640

def sc_mileage(t, si):
    img = drift(PASTEL_BG, t)
    e = eo3(seg(t, 32.60, 0.22))
    place(img, text_img("মাইলেজ", 44, GREY, path=ANEK700), 360, 236 + 10 * (1 - e), alpha=e)
    back = seg(t, wt("অকশন"), 0.25)                     # card recedes when the big word lands
    c = eo3(seg(t, 32.62, 0.3))
    if c > 0:
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        card_at(L, 70, 330, 580, 400)
        place(L, text_img("Mileage", 28, (60, 60, 70, 255), path=INTER_SB), 70 + 34 + 52, 384)
        d = ImageDraw.Draw(L)
        for k in range(4): d.line([(110, 470 + k * 60), (610, 470 + k * 60)], fill=(238, 238, 244, 255), width=2)
        pts = [(110, 670), (190, 640), (260, 652), (340, 600), (410, 612), (480, 552), (550, 520), (610, 470)]
        q = eo3(seg(t, 32.70, 0.95)) * (len(pts) - 1)
        n = int(q); fr = q - n
        line = pts[:n + 1] + ([(lerp(pts[n][0], pts[n + 1][0], fr), lerp(pts[n][1], pts[n + 1][1], fr))] if n < len(pts) - 1 else [])
        if len(line) > 1:
            S = 2; LL = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
            ImageDraw.Draw(LL).line([(x * S, y * S) for x, y in line], fill=PURPLE, width=6 * S, joint="curve")
            L.alpha_composite(LL.resize((W, H), Image.LANCZOS))
        v = int(round(33000 * (0.5 - 0.5 * math.cos(math.pi * seg(t, wt("33,000"), 0.9)))))
        if t >= wt("33,000"):
            num = text_img(f"{v:,} km", 44, PURPLE, path=INTER_B)
            place(L, num, 610 - num.info["adv"] / 2, 400, alpha=eo3(seg(t, wt("33,000"), 0.15)))
        Lb = blurred(L, 6 * eo3(back)) if back > 0 else L
        place(img, Lb, 360, 640 + 20 * (1 - c), alpha=c * (1 - 0.6 * eo3(back)))
    if t >= wt("অকশন"):
        se = eo3(seg(t, wt("অকশন"), 0.2))
        place(img, text_img("অকশন", 44, GREY, path=ANEK700), 360, 430 + 10 * (1 - se), alpha=se)
    if t >= wt("গ্রেড"):
        big = text_img("গ্রেড ৪", 150, INK); hb = seg(t, wt("গ্রেড") + 0.10, 0.30)
        bw_full = big.info["adv"] + 50
        if hb > 0:
            bw = int(bw_full * eo3(hb)); img.alpha_composite(rr(bw_full, 150, 16, HILITE).crop((0, 0, max(1, bw), 150)), (int(360 - bw_full / 2), 470))
        e = eo3(seg(t, wt("গ্রেড"), 0.14))
        place(img, blurred(big, 12 * (1 - e)), 360, 540, alpha=e, scale=lerp(1.08, 1, e))
    return img

def sc_title(t, si):
    img = drift(PASTEL_BG, t)
    e = eo3(seg(t, wt("শোরুমের"), 0.25))
    place(img, text_img("শোরুমের ঠিকানা", 44, GREY, path=ANEK700), 360, 470 + 10 * (1 - e), alpha=e)
    T = "আব্দুল হামিদ রোড"; ts = fit(T, 640, hi=110)
    b = eo3(seg(t, wt("আব্দুল"), 0.16))
    place(img, blurred(text_img(T, ts, INK), 12 * (1 - b)), 360, 580, alpha=b, scale=lerp(1.06, 1, b))
    u = eo3(seg(t, wt("আব্দুল") + 0.15, 0.45))
    if u > 0:
        uw = int(560 * u); img.alpha_composite(rr(max(8, uw), 8, 4, TEAL), (int(360 - uw / 2), 668))
    s = eo3(seg(t, wt("পাবনা"), 0.25))
    place(img, text_img("পাবনা সদর, পাবনা", 58, TEAL_TXT), 360, 742 + 12 * (1 - s), alpha=s)
    return img

# ============================================================ edit decision list
def caps_A(img, t):
    cap_small(img, "আপনারা কিন্তু ইতোমধ্যেই আমাদের", wt("আপনারা"), t); cap_big(img, "চিটাগাং স্টকের", wt("চিটাগাং"), t)
def caps_C(img, t):
    if t < wt("আমাদের", 1): cap_small(img, "বেশ কয়েকটি ইউনিট কিন্তু", wt("বেশ"), t)
    else: cap_small(img, "আমাদের চিটাগাং", wt("আমাদের", 1), t)
    cap_big(img, "রেডি স্টকে", wt("রেডি"), t); cap_pill(img, "অ্যাভেলেবল", wt("অ্যাভেলেবল"), t)
def caps_E(img, t):
    cap_small(img, "দুইটাই কিন্তু", wt("দুইটাই"), t); cap_big(img, "অ্যাভেলেবল", wt("অ্যাভেলেবল", 1), t)
def caps_F(img, t):
    cap_small(img, "আমার সামনে যে গাড়িটা দেখতেছেন", wt("আমার"), t, size=38)
def caps_H(img, t):
    cap_small(img, "গাড়িটির সঙ্গে কিন্তু", wt("গাড়িটির"), t)
    if t < wt("360"): cap_big(img, "অটো পার্কিং", wt("অটো"), t)
    else: cap_big(img, "360 ক্যামেরা", wt("360"), t)
def caps_J(img, t):
    cap_small(img, "গাড়িটির মাইলেজ আছে মাত্র", wt("গাড়িটির", 1), t)
def caps_L(img, t):
    if t < wt("আমাদের", 4): cap_small(img, "দেরি না করে", wt("দেরি"), t)
    else: cap_small(img, "আমাদের শোরুম", wt("আমাদের", 4), t)
    cap_big(img, "আজই", wt("আজই"), t); cap_pill(img, "ভিজিট করুন", wt("ভিজিট"), t)
def caps_N(img, t):
    cap_small(img, "আব্দুল হামিদ রোড", 41.02, t); cap_big(img, "পাবনা সদর, পাবনা", 41.08, t)

# (start, end, kind, payload, out-transition)
EDL = [
    (0.00, 3.30, "talk", caps_A, "flash"),
    (3.30, 5.52, "pastel", sc_logo, "blur"),
    (5.52, 9.10, "talk", caps_C, "flash"),
    (9.10, 12.95, "pastel", sc_compare, "blur"),
    (12.95, 15.40, "talk", caps_E, None),
    (15.40, 16.95, "broll", caps_F, "glow"),
    (16.95, 20.60, "frame", sc_frame, "flash"),
    (20.60, 23.80, "pastel", sc_spec, "blur"),
    (23.80, 27.24, "talk", caps_H, "flash"),
    (27.24, 31.64, "pastel", sc_wave, "blur"),
    (31.64, 32.55, "talk", caps_J, "flash"),
    (32.55, 35.64, "pastel", sc_mileage, "blur"),
    (35.64, 38.00, "talk", caps_L, "flash"),
    (38.00, 41.00, "pastel", sc_title, "blur"),
    (41.00, 99.00, "talk", caps_N, "end"),
]
PREV_OUT = {EDL[i + 1][0]: EDL[i][4] for i in range(len(EDL) - 1)}

FLASH_D, BLUR_D, GLOW_D = 0.26, 0.15, 0.16
def warm_leak(img, k):
    """the reference's red/orange leak while the talking shot de-blurs."""
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    g = np.exp(-(((_xx - 140) / 420) ** 2 + ((_yy - 700) / 900) ** 2))[..., None]
    a = 1 - (1 - a) * (1 - np.array([0.85, 0.32, 0.12]) * g * k * 0.50)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

def render(fi):
    t = fi / FPS; si = min(int(t * SRC_FPS), NSRC - 1)
    i, (a, b, kind, pay, out) = next((k, e) for k, e in enumerate(EDL) if e[0] <= t < e[1])
    if kind == "talk": img = talk_frame(t, si, [pay])
    elif kind == "broll":
        img = grade(camera(si, t, "broll")); pay(img, t)
    else: img = pay(t, si)
    if kind in ("pastel",) or kind == "frame": draw_badge(img, t)
    elif t >= BADGE_MOVE: draw_badge(img, t)
    # --- incoming transition
    inc = PREV_OUT.get(a)
    if inc == "flash" and kind in ("pastel", "frame") and t < a + 0.14:
        img = Image.blend(Image.new("RGBA", (W, H), WHITE), img, eo3(seg(t, a, 0.14)))
    if inc == "blur" and t < a + 0.18:                 # reference: blur clears in ~3 frames
        k = 1 - eo3(seg(t, a, 0.18))
        img = warm_leak(img.filter(ImageFilter.GaussianBlur(14 * k)), k)
    # --- outgoing transition
    if out == "flash" and t > b - FLASH_D:
        k = seg(t, b - FLASH_D, FLASH_D)
        cy = Image.new("RGBA", (W, H), (120, 255, 250, 255))
        img = Image.blend(img, cy, 0.35 * eo3(k))
        if k > 0.6: img = Image.blend(img, Image.new("RGBA", (W, H), WHITE), eo3((k - 0.6) / 0.4))
    if out == "blur" and t > b - BLUR_D:
        k = seg(t, b - BLUR_D, BLUR_D); z = 1 + 0.06 * ei2(k)
        cw, ch = W / z, H / z
        img = img.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
        img = img.filter(ImageFilter.GaussianBlur(12 * ei2(k)))
    if out == "glow" and t > b - GLOW_D:
        k = ei2(seg(t, b - GLOW_D, GLOW_D))
        img = Image.blend(img.filter(ImageFilter.GaussianBlur(10 * k)), Image.new("RGBA", (W, H), (150, 230, 240, 255)), 0.25 * k)
    if out == "end" and t > DUR - 0.75:
        k = seg(t, DUR - 0.75, 0.75)
        a_ = np.asarray(img.convert("RGB"), np.float32) / 255
        g = np.exp(-(((_xx - 360) / 520) ** 2 + ((_yy - 760) / 760) ** 2))[..., None]
        a_ = 1 - (1 - a_) * (1 - np.array([0.25, 0.95, 0.95]) * g * eo3(k) * 0.85)
        img = Image.fromarray((np.clip(a_, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    return img.convert("RGB").tobytes()

# logo-slide photo: the car from the b-roll
_cf = Image.open(f"{SRC}/f_{int(16.4 * SRC_FPS):04d}.png").convert("RGB")
CAR_PHOTO = _cf.crop((40, 470, 680, 1110)).resize((300, 300), Image.LANCZOS).convert("RGBA")

if __name__ == "__main__":
    if PREVIEW:
        for ts in PREVIEW:
            Image.frombytes("RGB", (W, H), render(int(round(float(ts) * FPS)))).save(f"{OUT}_{ts}.png")
        print("previews:", ", ".join(PREVIEW)); sys.exit(0)
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", SRC_VIDEO, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=6)):
            ff.stdin.write(buf)
            if i % 250 == 0: print(f"  frame {i}/{n}", flush=True)
    ff.stdin.close(); ff.wait(); print("done ->", OUT, "exit", ff.returncode)
