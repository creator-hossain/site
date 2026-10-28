# -*- coding: utf-8 -*-
"""Reference-2 style compositor (course-promo look) for the Corolla Cross footage.

Layer order on full-frame shots:  footage -> text BEHIND -> person (matte) -> text IN FRONT
PIP shots: blue gradient + thin guide lines -> pulse rings -> footage masked to a
circle / rounded card -> white border -> speech bubble / white label boxes.
Transitions: the full-frame shot shrinks into the PIP shape (and back), ease-out.

usage: compose.py SRC_DIR MATTE_DIR TRACK_JSON SOURCE_VIDEO OUT.mp4 [--preview t1,t2,...]
"""
import sys, os, json, subprocess
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, MAT, TRACK, SRC_VIDEO, OUT = sys.argv[1:6]
PREVIEW = sys.argv[7].split(",") if len(sys.argv) > 7 and sys.argv[6] == "--preview" else None

FPS, SRC_FPS, DUR = 50, 25, 13.0
W, H = 720, 1280
import os
FONTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")   # fonts shipped in the repo (works on Windows too)
ANEK800 = os.path.join(FONTDIR, "bnx", "AnekBN.ttf")
ANEK700 = os.path.join(FONTDIR, "bnx", "anek-bangla-bengali-700-normal.ttf")
SX = 0.87                                    # reference glyphs are ~87% as wide as Anek
WHITE = (255, 255, 255, 255)
BLUE_OL = (3, 123, 254, 255)                 # sampled from the reference headline outline
BLUE_FILL = (1, 158, 254, 255)               # sampled from the reference angled word
BLUE_DEEP = (0, 52, 130, 255)
BG_TL, BG_BR = (34, 85, 164), (9, 147, 215)  # sampled reference gradient

_tr = json.load(open(TRACK))
HX, HTOP = _tr["hx"], _tr["htop"]
NSRC = len(HX)

# ---------------------------------------------------------------- helpers
def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def eoback(p, s=1.6):
    p = clamp(p, 0, 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def seg(t, a, d): return clamp((t - a) / d, 0, 1)

@lru_cache(maxsize=None)
def font(path, size): return ImageFont.truetype(path, size)

@lru_cache(maxsize=None)
def styled(txt, size, passes, path=ANEK800, sx=SX, shadow_blur=0):
    """passes: ((dx,dy,fill,stroke,stroke_fill),...) drawn back-to-front on one canvas."""
    f = font(path, size)
    ms = max(p[3] for p in passes); md = max(max(abs(p[0]), abs(p[1])) for p in passes)
    bb = f.getbbox(txt, stroke_width=ms)
    pad = ms + md + 6 + shadow_blur * 3
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ox, oy = pad - bb[0], pad - bb[1]
    for i, (dx, dy, fill, st, sf) in enumerate(passes):
        L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(L).text((ox + dx, oy + dy), txt, font=f, fill=fill,
                               stroke_width=st, stroke_fill=sf)
        if i == 0 and shadow_blur: L = L.filter(ImageFilter.GaussianBlur(shadow_blur))
        out.alpha_composite(L)
    if sx != 1: out = out.resize((max(1, int(w * sx)), h), Image.LANCZOS)
    return out

def fit(txt, maxw, maxh, path=ANEK800, hi=320, lo=40):
    for s in range(hi, lo - 1, -4):
        bb = font(path, s).getbbox(txt)
        if (bb[2] - bb[0]) * SX <= maxw and (bb[3] - bb[1]) <= maxh: return s
    return lo

def place(dst, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0, anchor="c"):
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

# ---------------------------------------------------------------- text looks
def big_behind(txt, maxw=640, maxh=205):
    s = fit(txt, maxw, maxh)
    return styled(txt, s, ((5, 6, BLUE_OL, 3, BLUE_OL), (0, 0, WHITE, 2, BLUE_OL)))
def side(txt):
    return styled(txt, 46, ((2, 3, (0, 0, 0, 120), 0, None), (0, 0, WHITE, 0, None)),
                  path=ANEK700, shadow_blur=2)
def angled(txt):
    s = fit(txt, 560, 170)
    return styled(txt, s, ((5, 8, BLUE_DEEP, 7, BLUE_DEEP), (0, 0, BLUE_FILL, 7, WHITE)))
def word_dark(txt, size, path):
    return styled(txt, size, ((0, 0, (22, 22, 22, 255), 0, None),), path=path)

# ---------------------------------------------------------------- footage
@lru_cache(maxsize=8)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
@lru_cache(maxsize=8)
def src_matte(si): return Image.open(f"{MAT}/f_{si + 1:04d}.png").convert("L")

def camera(si, z, head_top_out):
    """virtual camera: zoom z, head centred horizontally, head-top at head_top_out."""
    cw, ch = W / z, H / z
    x0 = clamp(HX[si] - (W / 2) / z, 0, W - cw)
    y0 = clamp(HTOP[si] - head_top_out / z, 0, H - ch)
    box = (x0, y0, x0 + cw, y0 + ch)
    fr = src_frame(si).resize((W, H), Image.LANCZOS, box=box)
    fr = fr.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    mt = src_matte(si).resize((W, H), Image.BILINEAR, box=box)
    return fr, mt

HT_FULL = 175                  # head top on full-frame shots (reference ~184)
def zfull(t): return 1.95 + 0.010 * t      # waist-up framing like the reference

# ---------------------------------------------------------------- blue world
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
    if kind == "circle":
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
    d.ellipse([c - R2, c - R2, c + R2, c + R2], outline=(255, 255, 255, int(95 * (1 - q) * alpha)),
              width=int(5 * SS))
    place(dst, L.resize((size, size), Image.BOX), cx, cy)

# ---------------------------------------------------------------- timeline
FLASH = 0.06
S1 = dict(a=0.00, b=2.05)
T1 = dict(a=2.05, b=2.30)          # full -> circle
S2 = dict(a=2.30, b=5.25)
T2 = dict(a=5.25, b=5.50)          # circle -> full
S3 = dict(a=5.50, b=9.20)
T3 = dict(a=9.20, b=9.50)          # full -> card
S4 = dict(a=9.50, b=13.0)

CIRC = (360, 452, 170); CIRC_Z, CIRC_HT = 1.23, 350
CARD = (112, 184, 608, 684, 26); CARD_Z, CARD_HT = 0.95, 250

def fade(t, a, d=0.20): return eo3(seg(t, a, d))
def outfade(t, a, d=0.10): return 1 - eo3(seg(t, a, d))

def texts_S1(t, k=1.0, dy=0.0):
    """(behind, front) layer lists for scene 1; k = extra alpha, dy = vertical drift."""
    beh = [(big_behind("আপনারা"), 360, 158 + dy, fade(t, 0.20) * k),
           (side("কিন্তু"), 150, 372 + dy, fade(t, 0.65) * k),
           (side("ইতোমধ্যেই"), 572, 372 + dy, fade(t, 1.09) * k),
           (big_behind("আমাদের", 600, 150), 360, 505 + dy, fade(t, 1.72) * k)]
    return beh, []

SWING_T = 8.00
def texts_S3(t, k=1.0, dy=0.0):
    beh = [(big_behind("বেশ কয়েকটি"), 360, 158 + dy, fade(t, 5.55) * k),
           (side("ইউনিট"), 150, 372 + dy, fade(t, 6.29) * outfade(t, 7.00) * k),
           (side("কিন্তু"), 572, 372 + dy, fade(t, 6.66) * outfade(t, 7.00) * k),
           (side("আমাদের"), 150, 372 + dy, fade(t, 7.09) * k),
           (side("চিটাগাং"), 572, 372 + dy, fade(t, 7.52) * k)]
    fr = []
    if t >= SWING_T:
        e = eo3(seg(t, SWING_T, 0.24))
        fr.append((angled("রেডি স্টকে"), lerp(668, 400, e), lerp(600 + dy, 905 + dy, e),
                   eo3(seg(t, SWING_T, 0.08)) * k, lerp(84, 36, e)))
    return beh, fr

BUBBLES = [  # (pop time, words[(text, t)])
    (2.26, [("চিটাগাং", 2.17), ("স্টকের", 2.67), ("করোলা", 3.12), ("ক্রস", 3.51)]),
    (3.80, [("সম্পর্কে", 3.84), ("ধারণা", 4.40), ("চলে", 4.79), ("এসেছে", 5.06)]),
]
BOXES = [  # (y, words[(text, t)])
    (744, [("আমাদের", 10.08), ("শোরুমেও", 10.50)]),
    (834, [("পার্ল", 10.99), ("কালার", 11.36)]),
    (924, [("ব্ল্যাক", 11.99), ("কালার", 12.47)]),
]

# ---------------------------------------------------------------- scene renderers
def full_shot(t, si, z, head_top, beh, front, flash=0.0):
    fr, mt = camera(si, z, head_top)
    out = fr.convert("RGBA")
    for im, cx, cy, a in beh: place(out, im, cx, cy, alpha=a)
    if flash > 0:
        fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), flash)
    person = fr.convert("RGBA"); person.putalpha(mt)
    out.alpha_composite(person)
    for im, cx, cy, a, ang in front: place(out, im, cx, cy, alpha=a, angle=ang)
    return out

def bubble(dst, t, alpha):
    cur = None
    for pop, words in BUBBLES:
        if t >= pop - 0.001: cur = (pop, words)
    if cur is None: return
    pop, words = cur
    size = 31
    imgs = [word_dark(w, size, ANEK700) for w, _ in words]
    sp = font(ANEK700, size).getlength(" ") * SX
    tw = sum(i.width for i in imgs) + sp * (len(imgs) - 1) - 12 * len(imgs)
    bw, bh, tri = max(430, int(tw + 74)), 70, 14
    SS = 2
    B = Image.new("RGBA", (bw * SS, (bh + tri) * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(B)
    d.rounded_rectangle([0, tri * SS, bw * SS - 1, (bh + tri) * SS - 1], radius=bh * SS // 2, fill=WHITE)
    d.polygon([(bw * SS / 2 - tri * SS, tri * SS + 2), (bw * SS / 2 + tri * SS, tri * SS + 2),
               (bw * SS / 2, 0)], fill=WHITE)
    B = B.resize((bw, bh + tri), Image.LANCZOS)
    x = 37
    for im, (w, wt) in zip(imgs, words):
        a = eo3(seg(t, max(wt, pop), 0.08))
        if a > 0: place(B, im, x - 6, tri + bh / 2, alpha=a, anchor="l")
        x += im.width - 12 + sp
    sc = lerp(0.55, 1.0, eoback(seg(t, pop, 0.20)))
    place(dst, B, 360, 452 + 170 + 32 + (bh + tri) / 2, alpha=alpha * eo3(seg(t, pop, 0.10)), scale=sc)

def boxes(dst, t):
    size, pad, bh = 50, 22, 80
    sp = font(ANEK800, size).getlength(" ") * SX
    for y, words in BOXES:
        t1 = words[0][1]
        if t < t1 - 0.16: continue
        imgs = [word_dark(w, size, ANEK800) for w, _ in words]
        widths = [0.0]; acc = 0.0
        for i, im in enumerate(imgs):
            acc += (im.width - 12) + (sp if i else 0); widths.append(acc + 2 * pad)
        k = sum(1 for _, wt in words if t >= wt)
        if k == 0:                                     # wipe-in before the first word
            bw = widths[1] * eo3(seg(t, t1 - 0.16, 0.15))
        else:
            tk = words[k - 1][1]
            bw = lerp(widths[k - 1] if k > 1 else widths[1], widths[k], eo3(seg(t, tk, 0.12)))
        if bw < 2: continue
        d = ImageDraw.Draw(dst)
        d.rectangle([112, y - bh / 2, 112 + bw, y + bh / 2], fill=WHITE)
        x = 112 + pad
        for im, (w, wt) in zip(imgs, words):
            a = eo3(seg(t, wt, 0.14))
            if a > 0: place(dst, im, x - 6, y + 1, alpha=a, anchor="l")
            x += im.width - 12 + sp

def pip_shot(t, si, kind, e, texts_fn=None, txt_k=0.0, chrome=1.0, zp=1.0):
    """e: 0 = full frame, 1 = settled PIP. txt_k: alpha of the full-frame texts riding along."""
    z_pip = zfull(t) * (CIRC_Z if kind == "circle" else CARD_Z)
    ht_pip = CIRC_HT if kind == "circle" else CARD_HT
    z, ht = lerp(zfull(t), z_pip, e), lerp(HT_FULL, ht_pip, e)
    fr_img, mt = camera(si, z, ht)
    content = fr_img.convert("RGBA")
    if kind == "circle":
        prm = (CIRC[0], lerp(640, CIRC[1], e), lerp(1000, CIRC[2], e))
    else:
        prm = tuple(lerp(a, b, e) for a, b in zip((0, 0, W, H, 0), CARD))
    out = BG.copy()
    if e > 0.01:
        L = LINES if e >= 0.99 else Image.fromarray(
            (np.asarray(LINES, np.float32) * np.array([1, 1, 1, e], np.float32)).astype(np.uint8), "RGBA")
        out.alpha_composite(L)
    if kind == "circle" and chrome > 0:
        rings(out, prm[0], prm[1], prm[2], t, chrome * e)
    m = shape_mask(kind, prm)
    content.putalpha(m); out.alpha_composite(content)
    if texts_fn is not None and txt_k > 0:
        # reference: the words are NOT clipped by the shape - they fly outward
        # (scale up from screen centre) and fade while the footage folds into it
        beh, front = texts_fn(t, k=txt_k)
        fly = 1 + 1.1 * e
        fx = lambda x: 360 + (x - 360) * fly
        fy = lambda y: 640 + (y - 640) * fly
        for im, cx, cy, a in beh: place(out, im, fx(cx), fy(cy), alpha=a, scale=fly)
        # person stays in front of the behind-words, but only inside the shape
        person = fr_img.convert("RGBA")
        person.putalpha(Image.fromarray(np.minimum(np.asarray(mt), np.asarray(m))))
        out.alpha_composite(person)
        for im, cx, cy, a, ang in front: place(out, im, fx(cx), fy(cy), alpha=a, scale=fly, angle=ang)
    bw = 5 * e
    if bw > 0.3:
        ring_m = np.asarray(shape_mask(kind, prm, grow=bw), np.int16) - np.asarray(m, np.int16)
        Wl = Image.new("RGBA", (W, H), WHITE); Wl.putalpha(Image.fromarray(ring_m.clip(0, 255).astype(np.uint8)))
        out.alpha_composite(Wl)
    if kind == "circle" and chrome > 0: bubble(out, t, chrome)
    if kind == "card": boxes(out, t)
    if zp != 1.0:
        cw, ch = W / zp, H / zp
        out = out.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H - ch) / 2 + ch))
    return out

def render(fi):
    t = fi / FPS
    si = min(int(t * SRC_FPS), NSRC - 1)
    if t < S1["b"]:
        beh, fr_ = texts_S1(t)
        flash = 1.0 if t < FLASH else 1 - eo3(seg(t, FLASH, 0.06))
        img = full_shot(t, si, zfull(t), HT_FULL, beh, fr_, flash=flash)
    elif t < T1["b"]:
        p = seg(t, T1["a"], T1["b"] - T1["a"])
        img = pip_shot(t, si, "circle", eo3(p), texts_S1, txt_k=1 - eo3(p / 0.85))
    elif t < S2["b"]:
        img = pip_shot(t, si, "circle", 1.0, zp=1 + 0.035 * seg(t, S2["a"], S2["b"] - S2["a"]))
    elif t < T2["b"]:
        p = seg(t, T2["a"], T2["b"] - T2["a"])
        img = pip_shot(t, si, "circle", 1 - eo3(p), chrome=1 - eo3(p * 2.2),
                       zp=lerp(1.035, 1.0, eo3(p)))
    elif t < S3["b"]:
        beh, fr_ = texts_S3(t)
        img = full_shot(t, si, zfull(t), HT_FULL, beh, fr_)
    elif t < T3["b"]:
        p = seg(t, T3["a"], T3["b"] - T3["a"])
        img = pip_shot(t, si, "card", eo3(p), texts_S3, txt_k=1 - eo3(p / 0.85))
    else:
        img = pip_shot(t, si, "card", 1.0, zp=1 + 0.035 * seg(t, S4["a"], S4["b"] - S4["a"]))
    return img.convert("RGB").tobytes()

if __name__ == "__main__":
    if PREVIEW:
        for ts in PREVIEW:
            fi = int(round(float(ts) * FPS))
            Image.frombytes("RGB", (W, H), render(fi)).save(f"{OUT}_{ts}.png")
        print("previews:", ", ".join(PREVIEW)); sys.exit(0)
    n = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-nostdin", "-v", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-ss", "0", "-t", str(DUR), "-i", SRC_VIDEO,
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT],
        stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=6)):
            ff.stdin.write(buf)
            if i % 100 == 0: print(f"  frame {i}/{n}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done ->", OUT, "exit", ff.returncode)
