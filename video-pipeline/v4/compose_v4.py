# -*- coding: utf-8 -*-
"""Corolla Cross edit in the style of reference #4 + rule-driven sound design.

Visual grammar (measured from the reference):
  caption stack  small white line (word fade) / BIG gradient word typed cluster-by-cluster
                 (blur + 1.25x -> sharp, ~0.12 s per cluster) / third line typed smaller
  overlays       frosted purple bullet panel sliding from the top, white glass icon tiles
                 popping, frosted label pills wiping in, photo strip, white card scene with
                 typewriter text, phone mock-up, lavender scene, purple CTA button
Sound grammar  every element announces its sound through SFX_RULES (learned from ref #4);
               the cue list is written next to the video and mixed by mix_v4.py.
usage: compose_v4.py SRC MATTE TRACK WORDS SOURCE_VIDEO OUT [--preview t,..]
"""
import sys, json, subprocess, math
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, MAT, TRACK, WORDS, SRC_VIDEO, OUT = sys.argv[1:7]
PREVIEW = sys.argv[8].split(",") if len(sys.argv) > 8 and sys.argv[7] == "--preview" else None
FPS, SRC_FPS = 50, 25
W, H = 720, 1280
ANEK = "/usr/share/fonts/truetype/bnx/AnekBN.ttf"
ANEK7 = "/usr/share/fonts/truetype/bnx/anek-bangla-bengali-700-normal.ttf"
INTER_BI = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
INTER_SBI = "/usr/share/fonts/opentype/inter/Inter-SemiBoldItalic.otf"
INTER_B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
SX = 0.92
WHITE = (255, 255, 255, 255)
# gradients sampled from the reference captions (top colour, bottom colour)
G_BLUE = ((205, 228, 252), (112, 178, 246))
G_RED = ((255, 132, 124), (238, 98, 104))
G_PURPLE = ((242, 148, 250), (204, 84, 240))
G_MAGENTA = ((236, 110, 238), (186, 66, 226))
G_PINK = ((244, 154, 206), (206, 104, 226))
G_DEEP = ((112, 40, 196), (156, 74, 226))
PANEL = (144, 124, 160); PILL = (137, 101, 152); CTA_COL = (124, 58, 237)

TR = json.load(open(TRACK)); HX, HTOP, HW, SHOT, SHOTS = TR["hx"], TR["htop"], TR["hw"], TR["shot"], TR["shots"]
NSRC = len(HX); DUR = NSRC / SRC_FPS
WT = {}
for w in json.load(open(WORDS, encoding="utf-8")): WT.setdefault(w["w"], []).append(w["t"])
def wt(w, n=0): return WT[w][n]

# ================================================================ SOUND RULES (learned from reference #4)
# visual event -> [(sound, time offset relative to the event, gain dB)]
# offsets: negative = sound starts before the picture (risers lead the cut)
SFX_RULES = {
    "small_word": [("tick", 0.00, 0)],          # each word of the small white line
    "big_word":   [("swish", -0.02, 0)],        # BIG gradient word starts typing
    "third_line": [("swish", -0.02, -5)],       # smaller third line types
    "tile_pop":   [("pop", -0.01, 0)],          # glass icon tile pops
    "bullet":     [("chime", 0.00, 0)],         # line appears in the purple panel
    "panel_in":   [("swoosh", -0.15, 0)],       # big frosted panel slides in
    "panel_out":  [("soft_whoosh", -0.10, -3)],
    "pill":       [("thump", 0.00, 0)],         # frosted label pill wipes in
    "strip_in":   [("swoosh", -0.10, -4)],      # photo strip slides in
    "card_pop":   [("pop", 0.00, -6)],          # photo card in the strip
    "big_cut":    [("riser", "lead", 0), ("boom", -0.03, 0)],   # scene change / b-roll cut
    "soft_cut":   [("soft_whoosh", "centre", 0)],               # blur / flash transitions
    "phone_in":   [("swoosh", -0.12, 0)],
    "type_word":  [("type_tick", 0.00, 0)],     # typewriter word in the white-card scene
    "head_line":  [("swish", -0.02, -4)],       # header line typed in the lavender scene
    "count":      [("counter", 0.00, 0)],       # number counting up
    "cta":        [("pop", 0.00, 0), ("shimmer", 0.22, 0)],
}
CUES = []
def cue(event, t, gain=0.0, **kw):
    """gain = extra dB on top of the rule (e.g. quieter repeats)."""
    for snd, off, g in SFX_RULES[event]:
        CUES.append(dict(event=event, sound=snd, t=t, off=off, gain=g + gain, **kw))

# ================================================================ helpers
def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def ei2(p): p = clamp(p, 0, 1); return p * p
def eoback(p, s=1.8):
    p = clamp(p, 0, 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def seg(t, a, d): return clamp((t - a) / d, 0, 1)
def is_bn(s): return any("ঀ" <= c <= "৿" for c in s)

@lru_cache(maxsize=None)
def font(p, s): return ImageFont.truetype(p, s)
def pick(txt, path=None):
    if path: return path, (SX if is_bn(txt) else 1.0)
    return (ANEK, SX) if is_bn(txt) or any(c.isdigit() for c in txt) else (INTER_B, 1.0)

@lru_cache(maxsize=None)
def mask_img(txt, size, path=None):
    p, sx = pick(txt, path); f = font(p, size); asc, desc = f.getmetrics()
    pad = 14; vpad = pad + int(size * 0.22); adv = f.getlength(txt)
    w, h = int(adv + 2 * pad), int(asc + desc + 2 * vpad)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad, vpad), txt, font=f, fill=255)
    if sx != 1: m = m.resize((max(1, int(w * sx)), h), Image.LANCZOS)
    m.info["adv"], m.info["px"], m.info["sx"], m.info["path"] = adv * sx, pad * sx, sx, p
    return m

@lru_cache(maxsize=None)
def grad_text(txt, size, grad, path=None, shadow=True):
    m = mask_img(txt, size, path); w, h = m.size
    ys = np.where(np.asarray(m).max(1) > 20)[0]; y0, y1 = (ys.min(), ys.max()) if len(ys) else (0, h)
    k = np.clip((np.arange(h) - y0) / max(1, y1 - y0), 0, 1)[:, None]
    c0, c1 = np.array(grad[0], np.float32), np.array(grad[1], np.float32)
    rgb = (c0 * (1 - k[..., None]) + c1 * k[..., None]).repeat(w, 1)
    fill = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA"); fill.putalpha(m)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (w, h), (20, 10, 30, 0)); sh.putalpha(m.point(lambda v: int(v * 0.45)))
        sh = sh.filter(ImageFilter.GaussianBlur(5)); out.alpha_composite(sh, (0, 0)); out = out.transform(out.size, Image.AFFINE, (1, 0, 0, 0, 1, -4))
    out.alpha_composite(fill); out.info.update(m.info); return out

@lru_cache(maxsize=None)
def white_text(txt, size, path=ANEK7, col=(255, 255, 255)):
    return grad_text(txt, size, (col, col), path)

def blurred(im, r):
    if r < 0.4: return im
    p = int(r * 3); b = Image.new("RGBA", (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    b.alpha_composite(im, (p, p)); b = b.filter(ImageFilter.GaussianBlur(r)); b.info.update(im.info); return b

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
    """Bengali grapheme-ish clusters (consonant + virama chains + signs); Latin per letter."""
    out = []
    for ch in s:
        cp = ord(ch)
        attach = (0x0981 <= cp <= 0x0983) or cp == 0x09BC or (0x09BE <= cp <= 0x09CD) or cp == 0x09D7 or cp in (0x200C, 0x200D)
        if out and ch != " " and out[-1] != " " and (attach or out[-1].endswith("্")): out[-1] += ch
        else: out.append(ch)
    return out

def typed(dst, im, txt, t0, t, cx, cy, step):
    """reveal a rendered word cluster by cluster: each cluster blurs/scales in (reference)."""
    cl = clusters(txt); f = font(im.info["path"], 0) if False else None
    p, sx = im.info["path"], im.info["sx"]
    size = TYPED_SIZE.get(id(im))
    xs = [im.info["px"]]; pre = ""
    for c in cl:
        pre += c; xs.append(im.info["px"] + font(p, size).getlength(pre) * sx)
    left = cx - im.info["adv"] / 2 - im.info["px"]
    for i, c in enumerate(cl):
        if c == " ": continue
        e = eo3(seg(t, t0 + i * step, 0.13))
        if e <= 0: break
        a, b = int(xs[i]) - (6 if i else 14), int(xs[i + 1]) + (6 if i < len(cl) - 1 else 14)
        piece = im.crop((max(0, a), 0, min(im.width, b), im.height))
        pc = left + (max(0, a) + min(im.width, b)) / 2
        place(dst, blurred(piece, 7 * (1 - e)), pc, cy, alpha=e, scale=lerp(1.28, 1.0, e))
TYPED_SIZE = {}
def big_word(txt, size, grad, path=None):
    im = grad_text(txt, size, grad, path); TYPED_SIZE[id(im)] = size; return im

def fit(txt, maxw, hi, lo=30, path=None):
    p, sx = pick(txt, path)
    for s in range(hi, lo - 1, -2):
        if font(p, s).getlength(txt) * sx <= maxw: return s
    return lo

# ================================================================ footage
@lru_cache(maxsize=6)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
@lru_cache(maxsize=6)
def src_matte(si): return Image.open(f"{MAT}/f_{si + 1:04d}.png").convert("L")

def camera(si, t, want_matte=False, hw=None, ht=None):
    if hw is None:   # reference framing: head top ~y300, chest free for captions; wide opener under the top stack
        hw, ht = (112, 470) if t < 3.36 else (170, 300)
    k = SHOT[si]; a, b, mode = SHOTS[k]; push = 1 + min(0.05, 0.005 * (t - a))
    if mode == "T":
        z = hw / HW[si] * push; cw, ch = W / z, H / z
        x0 = clamp(HX[si] - (W / 2) / z, 0, W - cw); y0 = clamp(HTOP[si] - ht / z, 0, H - ch)
    else:
        z = 1.04 * push; cw, ch = W / z, H / z; x0, y0 = (W - cw) / 2, (H - ch) / 2
    box = (x0, y0, x0 + cw, y0 + ch)
    fr = src_frame(si).resize((W, H), Image.LANCZOS, box=box).filter(ImageFilter.UnsharpMask(2, 60 if z > 1.5 else 30, 2))
    mt = src_matte(si).resize((W, H), Image.BILINEAR, box=box) if want_matte else None
    return fr, mt

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.28 * (((_xx - 360) / 520) ** 2 + ((_yy - 600) / 820) ** 2), 0.6, 1)[..., None]
def grade(img):
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    a = np.clip((a - 0.5) * 1.06 + 0.5, 0, 1); g = a.mean(2, keepdims=True); a = g + (a - g) * 0.92
    a = a * VIG
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

def frosted(base, mask, tint, k=0.55, blur=16, border=True):
    """glass: blur what is underneath, tint it, add a faint light rim."""
    bb = mask.getbbox()
    if not bb: return
    x0, y0, x1, y1 = bb; pad = 40
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    reg = base.crop((X0, Y0, X1, Y1)).filter(ImageFilter.GaussianBlur(blur))
    tl = Image.new("RGBA", reg.size, tint + (255,)); reg = Image.blend(reg, tl, k)
    m = mask.crop((X0, Y0, X1, Y1)); reg.putalpha(m); base.alpha_composite(reg, (X0, Y0))
    if border:
        e = np.asarray(m, np.int16); er = np.asarray(m.filter(ImageFilter.MinFilter(5)), np.int16)
        rim = Image.new("RGBA", m.size, (255, 255, 255, 0)); rim.putalpha(Image.fromarray((np.clip(e - er, 0, 255) * 0.55).astype(np.uint8)))
        base.alpha_composite(rim, (X0, Y0))

# ================================================================ elements
class El:
    t0 = 0.0; t1 = 0.0; z = 1
    def live(self, t): return self.t0 - 0.02 <= t < self.t1 + 0.18
    def exit_k(self, t): return eo3(seg(t, self.t1, 0.16))

class Stack(El):
    """small white line / BIG typed gradient word / third typed line."""
    def __init__(s, cy, t1, small=None, big=None, third=None, small_at=None):
        s.cy, s.t1, s.small, s.big, s.third = cy, t1, small, big, third
        times = []
        if small:
            s.sw = [(w, tt) for w, tt in small]
            s.simgs = [white_text(w, 40) for w, _ in s.sw]; times.append(s.sw[0][1])
            for w, tt in s.sw: cue("small_word", tt)
        if big:
            txt, tt, grad = big[:3]; path = big[3] if len(big) > 3 else None
            s.bsize = fit(txt, 640, 150, path=path); s.bimg = big_word(txt, s.bsize, grad, path); s.btxt, s.bt = txt, tt
            times.append(tt); cue("big_word", tt)
        if third:
            txt, tt, grad = third; s.tsize = fit(txt, 560, 66); s.timg = big_word(txt, s.tsize, grad); s.ttxt, s.tt = txt, tt
            times.append(tt); cue("third_line", tt)
        s.t0 = min(times)
    def draw(s, dst, t):
        k = s.exit_k(t); am, br = 1 - k, 8 * k
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); y = s.cy
        if s.small:
            sp = font(ANEK7, 40).getlength(" ") * SX; ws = [i.info["adv"] for i in s.simgs]
            tw = sum(ws) + sp * (len(ws) - 1); x = 360 - tw / 2
            for im, (w, tt), a in zip(s.simgs, s.sw, ws):
                e = eo3(seg(t, tt, 0.14))
                if e > 0: place(L, blurred(im, 6 * (1 - e)), x + a / 2, y, alpha=e)
                x += a + sp
            y += 40 * 0.5 + s.bsize * 0.55 if s.big else 60
        if s.big:
            step = min(0.12, 0.42 / max(1, len(clusters(s.btxt))))
            typed(L, s.bimg, s.btxt, s.bt, t, 360, y, step); y += s.bsize * 0.52 + 30
        if s.third:
            step = min(0.10, 0.40 / max(1, len(clusters(s.ttxt))))
            typed(L, s.timg, s.ttxt, s.tt, t, 360, y + 4, step)
        place(dst, blurred(L, br), 360, 640, alpha=am)

class Strip(El):
    """frosted photo cards across the top, drifting left (reference 2.0-4.7 s)."""
    def __init__(s, t0, t1, frames):
        s.t0, s.t1 = t0, t1; s.cards = []
        for i, fi in enumerate(frames):
            ph = Image.open(f"{SRC}/f_{fi:04d}.png").convert("RGB")
            ph = ph.crop((0, 300, 720, 300 + 720 * 1.15)).resize((170, 196), Image.LANCZOS).convert("RGBA")
            c = rr(186, 212, 18, (255, 255, 255, 120)); m = rr(170, 196, 13, WHITE).getchannel("A"); ph.putalpha(m)
            c.alpha_composite(ph, (8, 8)); s.cards.append(c); cue("card_pop", t0 + 0.08 + i * 0.14)
        cue("strip_in", t0)
    def draw(s, dst, t):
        k = s.exit_k(t); x0 = lerp(760, 30, eo3(seg(t, s.t0, 0.45))) - 55 * (t - s.t0)
        for i, c in enumerate(s.cards):
            p = seg(t, s.t0 + 0.08 + i * 0.14, 0.25)
            place(dst, c, x0 + i * 200 + 93, 196, alpha=eo3(p * 2) * (1 - k), scale=lerp(0.7, 1, eoback(p)))

class Panel(El):
    """frosted purple panel slides down from the top; ✦ bullet lines appear (chime each)."""
    def __init__(s, t0, t1, bullets):
        s.t0, s.t1, s.b = t0, t1, bullets; s.z = 0
        s.imgs = [white_text(x, 40, ANEK7) for x, _ in bullets]
        cue("panel_in", t0); cue("panel_out", t1)
        for _, tt in bullets: cue("bullet", tt)
    def draw(s, dst, t):
        h = 120 + 64 * len(s.b)
        y = lerp(-h - 10, 0, eo3(seg(t, s.t0, 0.38))) - (h + 20) * ei2(seg(t, s.t1, 0.30))
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([0, y - 60, W, y + h], 44, fill=255)
        frosted(dst, m, PANEL, 0.52, 18)
        for i, ((txt, tt), im) in enumerate(zip(s.b, s.imgs)):
            e = eo3(seg(t, tt, 0.25))
            if e <= 0: continue
            yy = y + 92 + i * 64; xx = 74 + 26 * (1 - e)
            star(dst, xx - 24, yy, 15, e)
            place(dst, im, xx + 12 + im.info["adv"] / 2, yy, alpha=e)

def star(dst, cx, cy, r, a):
    S = 4; im = Image.new("RGBA", (int(r * 2 * S), int(r * 2 * S)), (0, 0, 0, 0)); c = r * S
    pts = []
    for k in range(8):
        ang = math.pi / 4 * k - math.pi / 2; rr_ = r * S if k % 2 == 0 else r * S * 0.28
        pts.append((c + rr_ * math.cos(ang), c + rr_ * math.sin(ang)))
    ImageDraw.Draw(im).polygon(pts, fill=WHITE); place(dst, im.resize((int(r * 2), int(r * 2)), Image.LANCZOS), cx, cy, alpha=a)

def tile(content):
    """white glass tile: translucent rim + white face + soft shadow (reference icon tiles)."""
    o = Image.new("RGBA", (250, 250), (0, 0, 0, 0))
    sh = Image.new("RGBA", (250, 250), (0, 0, 0, 0)); sh.alpha_composite(rr(196, 196, 34, (20, 20, 40, 70)), (27, 37))
    o.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    o.alpha_composite(rr(196, 196, 34, (255, 255, 255, 135)), (27, 27)); o.alpha_composite(rr(170, 170, 26, (246, 246, 248, 255)), (40, 40))
    place(o, content, 125, 125); return o

def icon_parking():
    im = rr(118, 118, 22, (32, 96, 228, 255)); place(im, grad_text("P", 96, ((255, 255, 255), (255, 255, 255)), INTER_B, False), 59, 62); return im
def icon_360():
    im = Image.new("RGBA", (130, 130), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([8, 30, 122, 100], outline=(40, 110, 230, 255), width=7)
    place(im, grad_text("360°", 44, ((30, 30, 40), (30, 30, 40)), INTER_B, False), 66, 66); return im
def swatch(c0, c1, c2):
    a = np.linspace(0, 1, 120)[:, None, None]; col = np.array(c0) * (1 - a) + np.array(c1) * a
    col = np.broadcast_to(col, (120, 120, 3)).copy(); col[18:34] = col[18:34] * 0.5 + np.array(c2) * 0.5
    im = Image.fromarray(col.astype(np.uint8)).convert("RGBA"); im.putalpha(rr(120, 120, 24, WHITE).getchannel("A")); return im
def icon_grade():
    im = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    im.alpha_composite(rr(130, 130, 26, (255, 196, 64, 255)), (5, 5))
    place(im, grad_text("৪", 96, ((40, 30, 10), (40, 30, 10)), ANEK, False), 70, 66)
    return im

class Tiles(El):
    def __init__(s, items, t1):
        s.items, s.t1 = [(tile(c), tt, x, y) for c, tt, x, y in items], t1; s.t0 = min(i[1] for i in items)
        for _, tt, _, _ in s.items: cue("tile_pop", tt)
    def draw(s, dst, t):
        k = s.exit_k(t)
        for im, tt, x, y in s.items:
            p = seg(t, tt, 0.26)
            if p > 0: place(dst, im, x, y, alpha=eo3(p * 3) * (1 - k), scale=lerp(0.3, 1.0, eoback(p, 2.0)) * (1 - 0.15 * k))

class Pills(El):
    """frosted purple pills, white italic text, wipe in from the left (thump each)."""
    def __init__(s, items, y0, t1):
        s.items, s.y0, s.t1 = items, y0, t1; s.t0 = items[0][1]
        s.imgs = [grad_text(x, 42, ((255, 255, 255), (255, 255, 255)), INTER_SBI, False) for x, _ in items]
        for _, tt in items: cue("pill", tt)
    def draw(s, dst, t):
        k = s.exit_k(t)
        if k >= 1: return
        for i, ((txt, tt), im) in enumerate(zip(s.items, s.imgs)):
            p = eo3(seg(t, tt, 0.28))
            if p <= 0: continue
            w = im.info["adv"] + 70; h = 74; x0 = 360 - w / 2; y = s.y0 + i * 92
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([x0, y - h / 2, x0 + w * p, y + h / 2], 14, fill=int(255 * (1 - k)))
            frosted(dst, m, PILL, 0.62, 14)
            if p > 0.35:
                tx = Image.new("RGBA", (W, H), (0, 0, 0, 0)); place(tx, im, 360, y + 1, alpha=(1 - k))
                cm = Image.new("L", (W, H), 0); ImageDraw.Draw(cm).rectangle([0, 0, x0 + w * p, H], fill=255)
                tx.putalpha(Image.fromarray(np.minimum(np.asarray(tx.getchannel("A")), np.asarray(cm)))); dst.alpha_composite(tx)

class Count(El):
    """big gradient number counting up (ease-in-out), counter ticks underneath."""
    def __init__(s, t0, t1, cy, target, small, third):
        s.t0, s.t1, s.cy, s.target, s.small, s.third = t0, t1, cy, target, small, third
        s.simgs = [white_text(w, 40) for w, _ in small]
        for _, tt in small: cue("small_word", tt)
        cue("count", t0, dur=0.85); cue("third_line", third[1])
        s.tim = big_word(third[0], 66, G_PINK); s.size = fit(f"{target:,}", 560, 150, path=INTER_BI)
    def draw(s, dst, t):
        k = s.exit_k(t); L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sp = font(ANEK7, 40).getlength(" ") * SX; ws = [i.info["adv"] for i in s.simgs]; x = 360 - (sum(ws) + sp * (len(ws) - 1)) / 2
        for im, (w, tt), a in zip(s.simgs, s.small, ws):
            e = eo3(seg(t, tt, 0.14))
            if e > 0: place(L, blurred(im, 6 * (1 - e)), x + a / 2, s.cy, alpha=e)
            x += a + sp
        if t >= s.t0:
            v = int(round(s.target * (0.5 - 0.5 * math.cos(math.pi * seg(t, s.t0, 0.85)))))
            n = grad_text(f"{v:,}", s.size, G_BLUE, INTER_BI)
            e = eo3(seg(t, s.t0, 0.12)); place(L, blurred(n, 8 * (1 - e)), 360, s.cy + 104, alpha=e, scale=lerp(1.2, 1, e))
        typed(L, s.tim, s.third[0], s.third[1], t, 360, s.cy + 200, 0.1)
        place(dst, blurred(L, 8 * k), 360, 640, alpha=1 - k)

class CTA(El):
    def __init__(s, t0, t1, txt, cy):
        s.t0, s.t1, s.cy = t0, t1, cy; cue("cta", t0)
        ti = grad_text(txt, 40, ((255, 255, 255), (255, 255, 255)), ANEK, False)
        w = int(ti.info["adv"] + 90); s.btn = rr(w, 78, 18, CTA_COL + (255,)); place(s.btn, ti, w / 2, 40); s.w = w
    def draw(s, dst, t):
        p = seg(t, s.t0, 0.28); b = s.btn.copy()
        q = seg(t, s.t0 + 0.22, 0.55)
        if 0 < q < 1:
            sh = Image.new("L", b.size, 0); x = lerp(-120, s.w + 120, eo3(q))
            ImageDraw.Draw(sh).polygon([(x, 0), (x + 46, 0), (x + 6, 78), (x - 40, 78)], fill=150)
            hl = Image.new("RGBA", b.size, (255, 255, 255, 0)); hl.putalpha(Image.fromarray(np.minimum(np.asarray(sh), np.asarray(b.getchannel("A")))))
            b.alpha_composite(hl)
        place(dst, b, 360, s.cy, alpha=eo3(p * 3), scale=lerp(0.4, 1, eoback(p, 2.0)))

# ================================================================ scenes (whole-frame)
def red_scene(t, si, words):
    """reference 'End of the day' scene: red backdrop, person cut out, italic white stack."""
    a = np.zeros((H, W, 3), np.float32)
    g = np.exp(-(((_xx - 360) / 560) ** 2 + ((_yy - 700) / 900) ** 2))[..., None]
    a[:] = np.array([226, 70, 74]) * (1 - g) + np.array([255, 118, 112]) * g
    img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    fr, mt = camera(si, t, True, hw=118, ht=330)
    pe = fr.convert("RGBA"); pe.putalpha(mt); img.alpha_composite(pe)
    for i, (txt, tt) in enumerate(words):
        e = eo3(seg(t, tt, 0.16))
        if e > 0:
            im = grad_text(txt, 74 if i < 3 else 56, ((255, 255, 255), (255, 240, 240)), ANEK)
            place(img, blurred(im, 6 * (1 - e)), 64 + im.info["adv"] / 2 + 20 * (1 - e), 170 + i * 92, alpha=e, angle=0)
    return img

CARD_BOX = (130, 360, 590, 900, 34)
def white_card(t, si, t_in, top_words, bottom_words, e_in):
    """white world, glass card holding the footage, typewriter lines above and below."""
    img = Image.new("RGBA", (W, H), (244, 244, 246, 255))
    x0, y0, x1, y1, r = CARD_BOX; s = lerp(0.55, 1.0, eo3(e_in)); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = (x1 - x0) * s, (y1 - y0) * s
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([cx - w / 2, cy - h / 2 + 16, cx + w / 2, cy + h / 2 + 16], r, fill=(30, 30, 50, 60))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    img.alpha_composite(rr(w + 22, h + 22, r + 8, (255, 255, 255, 255), outline=(220, 220, 228, 255), width=2), (int(cx - w / 2 - 11), int(cy - h / 2 - 11)))
    fr, _ = camera(si, t); ch = (x1 - x0) and H * (w / W)
    sub = fr.resize((int(w), int(h)), Image.LANCZOS, box=(0, (H - W * h / w) / 2, W, (H + W * h / w) / 2)).convert("RGBA")
    sub.putalpha(rr(int(w), int(h), r, WHITE).getchannel("A")); img.alpha_composite(sub, (int(cx - w / 2), int(cy - h / 2)))
    def line(words, y, size):
        imgs = [white_text(x, size, ANEK7, (70, 72, 80)) for x, _ in words]
        sp = font(ANEK7, size).getlength(" ") * SX; ws = [i.info["adv"] for i in imgs]
        # wrap to 2 lines if needed
        rows, cur, cw = [], [], 0
        for im, wd, a in zip(imgs, words, ws):
            if cur and cw + sp + a > 600: rows.append(cur); cur, cw = [], 0
            cur.append((im, wd, a)); cw += (sp if len(cur) > 1 else 0) + a
        if cur: rows.append(cur)
        for ri, row in enumerate(rows):
            tw = sum(a for _, _, a in row) + sp * (len(row) - 1); x = 360 - tw / 2
            for im, (wd, tt), a in row:
                e = eo3(seg(t, tt, 0.10))
                if e > 0: place(img, im, x + a / 2, y + ri * size * 1.25, alpha=e)
                x += a + sp
    line(top_words, 250, 40); line(bottom_words, 980, 38)
    return img

def lavender(t, header, rows, t_phone):
    a = np.zeros((H, W, 3), np.float32); k = (_yy / H)[..., None]
    a[:] = np.array([218, 186, 248]) * (1 - k) + np.array([240, 228, 252]) * k
    img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    for i, (txt, tt) in enumerate(header):
        im = big_word(txt, fit(txt, 600, 78), G_DEEP)
        typed(img, im, txt, tt, t, 360, 160 + i * 92, 0.08)
    ph = phone(t, rows); place(img, ph, 360, 840 + 30 * (1 - eo3(seg(t, t_phone, 0.4))), scale=1.0)
    return img

PH_W, PH_H = 380, 760
def phone(t, rows):
    o = Image.new("RGBA", (PH_W + 60, PH_H + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", o.size, (0, 0, 0, 0)); sh.alpha_composite(rr(PH_W, PH_H, 56, (10, 10, 30, 120)), (30, 46)); o.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    o.alpha_composite(rr(PH_W, PH_H, 56, (28, 28, 32, 255)), (30, 30))
    scr = rr(PH_W - 20, PH_H - 20, 46, (24, 25, 30, 255)); d = ImageDraw.Draw(scr)
    ph = PHONE_PHOTO; scr.alpha_composite(ph, (0, 0))
    m = rr(PH_W - 20, PH_H - 20, 46, WHITE).getchannel("A"); a = np.asarray(scr.getchannel("A")).copy(); a[np.asarray(m) == 0] = 0; scr.putalpha(Image.fromarray(a))
    d.rounded_rectangle([140, 14, 220, 38], 12, fill=(0, 0, 0, 255))
    place(scr, white_text("টয়োটা করোলা ক্রস", 40, ANEK), 22 + white_text("টয়োটা করোলা ক্রস", 40, ANEK).info["adv"] / 2, 300)
    sub = white_text("ZVG13 • 2023 • পার্ল টু-টোন", 26, ANEK7, (170, 172, 182)); place(scr, sub, 22 + sub.info["adv"] / 2, 346)
    d.line([(22, 384), (PH_W - 42, 384)], fill=(60, 62, 70, 255), width=2)
    lab = white_text("শোরুমের ঠিকানা", 26, ANEK7, (150, 152, 162)); place(scr, lab, 22 + lab.info["adv"] / 2, 420)
    for i, (txt, tt) in enumerate(rows):
        e = eo3(seg(t, tt, 0.22))
        if e <= 0: continue
        im = white_text(txt, 34, ANEK7); y = 476 + i * 58
        d.ellipse([22, y - 9, 40, y + 9], fill=(110, 140, 255, int(255 * e)))
        place(scr, im, 54 + im.info["adv"] / 2 + 14 * (1 - e), y, alpha=e)
    btn = rr(PH_W - 64, 66, 14, CTA_COL + (255,)); bt = white_text("এখনই ভিজিট করুন", 32, ANEK); place(btn, bt, (PH_W - 64) / 2, 34)
    place(scr, btn, (PH_W - 20) / 2, 650)
    o.alpha_composite(scr, (40, 40)); return o
_pf = Image.open(f"{SRC}/f_{int(16.4 * SRC_FPS):04d}.png").convert("RGB")
PHONE_PHOTO = _pf.crop((0, 380, 720, 380 + 720 * 0.72)).resize((PH_W - 20, int((PH_W - 20) * 0.72)), Image.LANCZOS).convert("RGBA")

# ================================================================ edit
E = []                         # (t0, t1, element) overlays on TALK / BROLL
def add(el): E.append(el); return el

# A  top stack  (reference 'প্রতিদিন চটকদার / বিজ্ঞাপন / দিচ্ছেন')
add(Stack(250, 3.32, small=[("আপনারা", wt("আপনারা")), ("কিন্তু", wt("কিন্তু")), ("ইতোমধ্যেই", wt("ইতোমধ্যেই")), ("আমাদের", wt("আমাদের"))],
          big=("চিটাগাং", wt("চিটাগাং"), G_BLUE), third=("স্টকের", wt("স্টকের"), G_PINK)))
# B  photo strip + mid stack
add(Strip(3.36, 5.42, [int(t * 25) for t in (16.4, 19.6, 22.2, 29.0, 18.9)]))
add(Stack(872, 5.42, small=[("করোলা", wt("করোলা")), ("ক্রস", wt("ক্রস")), ("সম্পর্কে", wt("সম্পর্কে"))],
          big=("ধারণা", wt("ধারণা"), G_MAGENTA), third=("চলে এসেছে", wt("চলে"), G_PINK)))
# D  after the red scene
add(Stack(872, 9.12, small=[("আমাদের", 7.66), ("চিটাগাং", 7.66)],
          big=("রেডি স্টকে", wt("রেডি"), G_RED), third=("অ্যাভেলেবল", wt("অ্যাভেলেবল"), G_PINK)))
# E  bullet panel + colour tiles + stack
add(Panel(9.30, 12.80, [("শোরুমেও অ্যাভেলেবল", wt("শোরুমেও")), ("পার্ল কালার", wt("পার্ল")), ("ব্ল্যাক কালার", wt("ব্ল্যাক"))]))
add(Tiles([(swatch((250, 250, 248), (214, 214, 222), (255, 255, 255)), wt("পার্ল"), 300, 760),
           (swatch((52, 54, 60), (8, 8, 12), (110, 112, 122)), wt("ব্ল্যাক"), 420, 760)], 12.86))
add(Stack(942, 12.86, small=[("পার্ল", wt("পার্ল")), ("কালার", wt("কালার")), ("এবং", wt("এবং"))],
          big=("ব্ল্যাক কালার", wt("ব্ল্যাক"), G_PURPLE)))
# F
add(Stack(872, 15.30, small=[("দুইটাই", wt("দুইটাই")), ("কিন্তু", wt("কিন্তু", 3))],
          big=("অ্যাভেলেবল", wt("অ্যাভেলেবল", 1), G_PURPLE), third=("পেয়ে যাচ্ছেন", wt("পেয়ে"), G_PINK)))
# G  b-roll
add(Stack(930, 17.20, small=[("আমার", wt("আমার")), ("সামনে", wt("সামনে")), ("যে", wt("যে")), ("গাড়িটা", wt("গাড়িটা")), ("দেখতেছেন", wt("দেখতেছেন"))]))
add(Stack(860, 19.72, big=("ZVG13", wt("ZVG13"), G_PURPLE, INTER_BI), third=("2023 এর মডেল", wt("2023"), G_PINK)))
# I  tiles on top + stack
add(Tiles([(icon_parking(), wt("অটো"), 260, 300), (icon_360(), wt("360"), 440, 300)], 27.10))
add(Stack(872, 27.10, small=[("গাড়িটির", wt("গাড়িটির")), ("সঙ্গে", wt("সঙ্গে")), ("কিন্তু", wt("কিন্তু", 4))],
          big=("অটো পার্কিং", wt("অটো"), G_BLUE), third=("360 ক্যামেরা", wt("360"), G_PINK)))
# J  b-roll + pills
add(Pills([("Alloy Wheels", 27.32), ("Fog Light", wt("ফগ")), ("Seat Heater", wt("সিট")), ("Cruise Control", wt("ক্রুজ"))], 560, 30.40))
add(Stack(930, 31.56, small=[("কিন্তু", wt("কিন্তু", 5))], big=("সবকিছুই", wt("সবকিছুই"), G_MAGENTA), third=("পাচ্ছেন", wt("পাচ্ছেন"), G_PINK)))
# K  mileage count, then grade tile
add(Count(wt("33,000"), 34.24, 860, 33000, [("গাড়িটির", wt("গাড়িটির", 1)), ("মাইলেজ", wt("মাইলেজ")), ("আছে", wt("আছে")), ("মাত্র", wt("মাত্র"))], ("কিলোমিটার", wt("কিলো"))))
add(Tiles([(icon_grade(), wt("গ্রেড"), 360, 640)], 35.58))
add(Stack(872, 35.58, small=[("অকশন", wt("অকশন")), ("গ্রেড", wt("গ্রেড")), ("রয়েছে", wt("রয়েছে"))], big=("ফোর", wt("ফোর"), G_RED)))
# L
add(Stack(872, 37.30, small=[("দেরি", wt("দেরি")), ("না", wt("না")), ("করে", wt("করে"))],
          big=("আজই", wt("আজই"), G_PURPLE), third=("ভিজিট করুন", wt("ভিজিট"), G_PINK)))
add(CTA(41.02, 99, "এখনই ভিজিট করুন", 1050))

# whole-frame scenes / transitions
RED = (5.55, 7.62); CARD = (19.78, 23.82); PHONE_IN = 37.30; LAV = (37.95, 41.00)
RED_WORDS = [("বেশ", wt("বেশ")), ("কয়েকটি", wt("কয়েকটি")), ("ইউনিট", wt("ইউনিট")), ("চিটাগাং স্টকে", wt("চিটাগাং", 1))]
for _, tt in RED_WORDS: cue("big_word", tt, gain=-6)
CARD_TOP = [(w, wt(w, n)) for w, n in (("পার্ল", 1), ("কালার", 2), ("টু", 0), ("টোন", 0))]
CARD_BOT = [(w, wt(w, n)) for w, n in (("উপরে", 0), ("হার্ড", 0), ("টপ", 0), ("এবং", 1), ("মডেলিস্টা", 0), ("বডি", 0), ("কিট", 0), ("সহ", 0))]
for _, tt in CARD_TOP + CARD_BOT: cue("type_word", tt)
LAV_HEAD = [("আমাদের শোরুমের", wt("আমাদের", 4)), ("ঠিকানা", wt("ঠিকানা"))]
LAV_ROWS = [("আব্দুল হামিদ রোড", wt("আব্দুল")), ("পাবনা সদর, পাবনা", wt("পাবনা"))]
for _, tt in LAV_HEAD: cue("head_line", tt)
for _, tt in LAV_ROWS: cue("tile_pop", tt)
cue("phone_in", PHONE_IN)
for t_cut, kind in ((RED[0], "big_cut"), (RED[1], "soft_cut"), (15.40, "big_cut"), (CARD[0], "soft_cut"),
                    (CARD[1], "big_cut"), (27.24, "big_cut"), (31.64, "soft_cut"), (35.64, "soft_cut"), (LAV[1], "soft_cut")):
    cue(kind, t_cut)
CUES.append(dict(event="card_open", sound="swoosh", t=CARD[0], off=-0.05, gain=-3))

def wash(img, t, at, col, peak, d=0.26):
    if at - 0.08 <= t < at + d:
        k = (1 - eo3(seg(t, at, d))) if t >= at else eo3(seg(t, at - 0.08, 0.08))
        img = Image.blend(img, Image.new("RGBA", (W, H), col + (255,)), peak * k)
    return img

def zblur(img, k, z=0.07):
    if k <= 0.01: return img
    zz = 1 + z * k; cw, ch = W / zz, H / zz
    img = img.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    return img.filter(ImageFilter.GaussianBlur(14 * k))

def render(fi):
    t = fi / FPS; si = min(int(t * SRC_FPS), NSRC - 1)
    if RED[0] <= t < RED[1]:
        img = red_scene(t, si, RED_WORDS)
    elif CARD[0] <= t < CARD[1]:
        e_in = seg(t, CARD[0], 0.42)
        img = white_card(t, si, CARD[0], CARD_TOP, CARD_BOT, e_in)
        if e_in < 1:                              # white circle opens over the b-roll (reference 20.0 s)
            under = grade(camera(si, t)[0]); r = 900 * eo3(e_in)
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([360 - r, 640 - r, 360 + r, 640 + r], fill=255)
            under.alpha_composite(Image.composite(img, under, m)); img = under
    elif t >= LAV[0] and t < LAV[1]:
        img = lavender(t, LAV_HEAD, LAV_ROWS, PHONE_IN)
        if t < LAV[0] + 0.25:
            talk = grade(camera(si, t)[0]); img = Image.blend(talk, img, eo3(seg(t, LAV[0], 0.25)))
    else:
        img = grade(camera(si, t)[0])
        for el in sorted(E, key=lambda e: e.z):
            if el.live(t): el.draw(img, t)
        if PHONE_IN <= t < LAV[0]:
            p = eo3(seg(t, PHONE_IN, 0.42)); ph = phone(t, LAV_ROWS)
            place(img, ph, 360, lerp(1700, 840, p), angle=lerp(-12, 0, p))
    # transitions
    if RED[0] - 0.12 <= t < RED[0]: img = zblur(img, seg(t, RED[0] - 0.12, 0.12))
    if RED[0] <= t < RED[0] + 0.12: img = zblur(img, 1 - seg(t, RED[0], 0.12))
    if RED[1] <= t < RED[1] + 0.16: img = zblur(img, 1 - eo3(seg(t, RED[1], 0.16)), 0.04)
    if 15.40 <= t < 15.52: img = zblur(img, 1 - seg(t, 15.40, 0.12), 0.08)
    if CARD[1] - 0.12 <= t < CARD[1]: img = zblur(img, seg(t, CARD[1] - 0.12, 0.12))
    if CARD[1] <= t < CARD[1] + 0.14: img = zblur(img, 1 - seg(t, CARD[1], 0.14))
    if 27.24 <= t < 27.36: img = zblur(img, 1 - seg(t, 27.24, 0.12), 0.08)
    if 31.64 <= t < 31.80: img = zblur(img, 1 - eo3(seg(t, 31.64, 0.16)), 0.04)
    img = wash(img, t, 35.64, (255, 172, 204), 0.55)
    img = wash(img, t, LAV[1], (255, 242, 214), 0.75)
    return img.convert("RGB").tobytes()

if __name__ == "__main__":
    json.dump(CUES, open(OUT.rsplit(".", 1)[0] + "_cues.json", "w"), ensure_ascii=False, indent=0)
    print(len(CUES), "sound cues")
    if PREVIEW:
        for ts in PREVIEW:
            Image.frombytes("RGB", (W, H), render(int(round(float(ts) * FPS)))).save(f"{OUT}_{ts}.png")
        print("previews:", ", ".join(PREVIEW)); sys.exit(0)
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=6)):
            ff.stdin.write(buf)
            if i % 250 == 0: print(f"  frame {i}/{n}", flush=True)
    ff.stdin.close(); ff.wait(); print("done ->", OUT, "exit", ff.returncode)
