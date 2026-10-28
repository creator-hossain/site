# -*- coding: utf-8 -*-
"""Corolla Cross edit in the style of reference #7 (airy blue grade, graphics behind the person).

Measured from the reference (368x464):
  * picture + huge pale-blue word composited BEHIND the person, revealed by a light-flare wipe
  * huge word along the bottom behind the legs, a pale cyan light band rising under it
  * teal label next to an object + a white shine sweeping across the object
  * the sky / top of the background turns blue (200,209,233 -> 105,174,230) behind the person,
    a blue gradient bar drops in top-right with a yellow + white two-line label, then a light burst
  * logo bug top-left swaps between two badges
Sound (learned): wide wind/water ambience bed under the graphic intro + swooshes on the reveals,
faint mono clicks when labels pop. Nothing else.
usage: compose_v7.py SRC MATTE TRACK WORDS CARCUT OUT [--preview t,..]
"""
import sys, json, subprocess, math
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, MAT, TRACK, WORDS, CARCUT, OUT = sys.argv[1:7]
PREVIEW = sys.argv[8].split(",") if len(sys.argv) > 8 and sys.argv[7] == "--preview" else None
FPS, SRC_FPS = 50, 25
W, H = 720, 900
SW, SH = 720, 1280
BALOO = "/usr/share/fonts/truetype/bnx/BalooDa2-BN-ExtraBold.ttf"
PALE = (143, 184, 209); PALE_DK = (116, 148, 183); TEAL = (60, 128, 150); BAR = (114, 177, 230)
YEL = (236, 228, 40); WHITE = (255, 255, 255, 255)

TR = json.load(open(TRACK)); HX, HTOP, HW, SHOT, SHOTS = TR["hx"], TR["htop"], TR["hw"], TR["shot"], TR["shots"]
NSRC = len(HX); DUR = NSRC / SRC_FPS
WT = {}
for w in json.load(open(WORDS, encoding="utf-8")): WT.setdefault(w["w"], []).append(w["t"])
def wt(w, n=0): return WT[w][n]
CUES = []
def cue(sound, t, gain=0.0, **kw): CUES.append(dict(sound=sound, t=round(t, 3), gain=gain, **kw))

def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def eio(p): p = clamp(p, 0, 1); return 0.5 - 0.5 * math.cos(math.pi * p)
def seg(t, a, d): return clamp((t - a) / d, 0, 1)
@lru_cache(maxsize=None)
def font(s): return ImageFont.truetype(BALOO, s)

@lru_cache(maxsize=None)
def label(txt, size, col, glow=None, shadow=True):
    f = font(size); asc, desc = f.getmetrics(); pad = 26; vpad = pad + int(size * 0.2); adv = f.getlength(txt)
    w, h = int(adv + 2 * pad), int(asc + desc + 2 * vpad); out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad, vpad), txt, font=f, fill=255)
    if glow:
        g = Image.new("RGBA", (w, h), glow + (0,)); g.putalpha(m.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.8))); out.alpha_composite(g)
    if shadow:
        s_ = Image.new("RGBA", (w, h), (20, 30, 50, 0)); s_.putalpha(m.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.35)))
        out.alpha_composite(s_.transform((w, h), Image.AFFINE, (1, 0, -1, 0, 1, -2)))
    fl = Image.new("RGBA", (w, h), col + (255,)); fl.putalpha(m); out.alpha_composite(fl)
    out.info.update(adv=adv); return out

@lru_cache(maxsize=None)
def giant(txt, maxw, hi, col0=(128, 174, 206), col1=(88, 128, 176)):
    """huge pale word with a top->bottom gradient and soft white rim (reference 'পদ্মা সেতু')."""
    s = hi
    while font(s).getlength(txt) > maxw and s > 40: s -= 4
    f = font(s); asc, desc = f.getmetrics(); pad = 30; w, h = int(f.getlength(txt) + 2 * pad), int(asc + desc + 2 * pad)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad, pad), txt, font=f, fill=255)
    ys = np.where(np.asarray(m).max(1) > 20)[0]; y0, y1 = ys.min(), ys.max()
    k = np.clip((np.arange(h) - y0) / max(1, y1 - y0), 0, 1)[:, None, None]
    rgb = np.repeat(np.array(col0) * (1 - k) + np.array(col1) * k, w, 1).astype(np.uint8)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rim = Image.new("RGBA", (w, h), (255, 255, 255, 0)); rim.putalpha(m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.7)))
    out.alpha_composite(rim); fl = Image.fromarray(rgb).convert("RGBA"); fl.putalpha(m); out.alpha_composite(fl); return out

def place(dst, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0):
    if alpha <= 0.004: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.996:
        a = (np.asarray(im.getchannel("A"), np.float32) * alpha).astype(np.uint8); im = im.copy(); im.putalpha(Image.fromarray(a))
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 > x0 and y1 > y0: dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def flare_wipe(im, p, soft=0.18):
    """reveal im left->right behind a bright soft light edge (reference flare wipe)."""
    w, h = im.size; x = np.linspace(0, 1, w)[None, :]
    edge = lerp(-soft, 1 + soft, eo3(p))
    a = np.clip((edge - x) / soft, 0, 1); glow = np.exp(-((x - edge) / (soft * 0.5)) ** 2)
    base = np.asarray(im, np.float32); al = base[..., 3:4] / 255
    rgb = base[..., :3] + (255 - base[..., :3]) * (glow[..., None] * 0.9 * al)
    out = np.concatenate([rgb, base[..., 3:4] * a[..., None] + 255 * glow[..., None] * al * 0.6 * (p < 0.98)], -1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

# ================================================================ camera / grade
@lru_cache(maxsize=6)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
@lru_cache(maxsize=6)
def src_matte(si): return Image.open(f"{MAT}/f_{si + 1:04d}.png").convert("L")
def cam(si, t):
    k = SHOT[si]; a, b, mode = SHOTS[k]; drift = 1 + min(0.04, 0.004 * max(0, t - a))
    if mode == "T":
        z = max(1.0, 90 / HW[si] * drift); cw, ch = W / z, H / z
        x0 = clamp(HX[si] - (W / 2) / z, 0, SW - cw); y0 = clamp(HTOP[si] - 120 / z, 0, SH - ch)
        head = ((HX[si] - x0) * z, (HTOP[si] - y0) * z, HW[si] * z)
    else:
        z = drift; cw, ch = W / z, H / z; x0 = (SW - cw) / 2; y0 = clamp((SH - ch) / 2 + 40, 0, SH - ch); head = None
    box = (x0, y0, x0 + cw, y0 + ch)
    fr = src_frame(si).resize((W, H), Image.LANCZOS, box=box)
    mt = src_matte(si).resize((W, H), Image.BILINEAR, box=box) if mode == "T" else None
    return fr, mt, head, mode

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
def grade(img):
    """reference look: airy, cool, low contrast, slightly desaturated."""
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    a = (a - 0.5) * 0.92 + 0.53; g = a.mean(2, keepdims=True); a = g + (a - g) * 0.85
    a = a * np.array([0.97, 1.0, 1.05])
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

def sky_tint(img, mt, k):
    """top of the background turns blue behind the person (reference 7.3-9.5 s)."""
    if k <= 0: return img
    a = np.asarray(img.convert("RGB"), np.float32)
    fall = np.clip(1 - _yy / (H * 0.55), 0, 1)[..., None] ** 1.3
    blue = np.array([105, 174, 230], np.float32) * (1 - 0.25 * _yy[..., None] / H)
    m = (1 - (np.asarray(mt, np.float32) / 255)[..., None]) if mt is not None else 1.0
    w_ = fall * m * 0.82 * k
    a = a * (1 - w_) + blue * w_
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

def light_band(img, k):
    """pale cyan light rising along the bottom (under the bottom giant word)."""
    if k <= 0: return img
    a = np.asarray(img.convert("RGB"), np.float32); top = H - 300 * eo3(k)
    g = np.clip((_yy - top) / 260, 0, 1)[..., None] * 0.75
    shimmer = 0.06 * np.sin(_xx / 23 + _yy / 41)[..., None]
    a = a * (1 - g) + np.array([212, 236, 246], np.float32) * (g + shimmer * g)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

def shine(img, box, p, ang=-28):
    """white shine sweeping across a region (reference: across the fish)."""
    if not 0 < p < 1: return img
    x0, y0, x1, y1 = box; L = Image.new("L", (W, H), 0); d = ImageDraw.Draw(L)
    cx = lerp(x0 - 120, x1 + 120, eio(p)); w = 70
    pts = [(cx - w, y1 + 60), (cx + w, y1 + 60), (cx + w + (y1 - y0 + 120) * math.tan(math.radians(-ang)), y0 - 60),
           (cx - w + (y1 - y0 + 120) * math.tan(math.radians(-ang)), y0 - 60)]
    d.polygon(pts, fill=230); L = L.filter(ImageFilter.GaussianBlur(26))
    reg = Image.new("L", (W, H), 0); ImageDraw.Draw(reg).rounded_rectangle(box, 40, fill=255); reg = reg.filter(ImageFilter.GaussianBlur(20))
    m = np.minimum(np.asarray(L), np.asarray(reg)).astype(np.float32) / 255 * math.sin(math.pi * p) * 0.85
    a = np.asarray(img.convert("RGB"), np.float32); a = a + (255 - a) * m[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

def burst(img, cx, cy, p):
    """light burst (reference: on the jar while 'আচার' appears)."""
    if not 0 < p < 1: return img
    k = math.sin(math.pi * p); r = 40 + 150 * eo3(p)
    g = np.exp(-(((_xx - cx) ** 2 + (_yy - cy) ** 2) / (r * r)))[..., None] * k
    streak = (np.exp(-((_yy - cy) / 5) ** 2) * np.exp(-((_xx - cx) / (r * 2.2)) ** 2) +
              np.exp(-((_xx - cx) / 5) ** 2) * np.exp(-((_yy - cy) / (r * 1.6)) ** 2))[..., None] * k * 0.8
    a = np.asarray(img.convert("RGB"), np.float32); m = np.clip(g + streak, 0, 1)
    a = a + (255 - a) * m
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

# ================================================================ logo bug (same channel as reference #6)
def _badges():
    a = Image.new("RGBA", (130, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(a)
    d.rounded_rectangle([18, 10, 112, 92], 16, fill=(250, 196, 40, 255), outline=(60, 40, 0, 255), width=3)
    d.polygon([(30, 34), (65, 14), (100, 34)], fill=(60, 40, 0, 255)); place(a, label("ZVG13", 26, (60, 40, 0), shadow=False), 65, 60)
    b = Image.new("RGBA", (170, 54), (0, 0, 0, 0)); ImageDraw.Draw(b).rounded_rectangle([0, 0, 169, 53], 26, fill=(220, 30, 40, 255))
    place(b, label("করোলা ক্রস", 26, (255, 255, 255), shadow=False), 85, 28); return a, b
BADGE_A, BADGE_B = _badges()
SWAPS = [4.8, 10.2, 15.6, 21.0, 26.4, 31.8, 37.2]
def logo_bug(dst, t):
    k = sum(1 for s in SWAPS if t >= s); im = BADGE_A if k % 2 == 0 else BADGE_B; sx = 1.0
    for s in SWAPS:
        if s - 0.14 <= t < s: sx = 1 - seg(t, s - 0.14, 0.14)
        if s <= t < s + 0.14: sx = seg(t, s, 0.14)
    imr = im.resize((max(1, int(im.width * max(sx, 0.02))), im.height), Image.BICUBIC)
    place(dst, imr, 22 + im.width / 2, 20 + im.height / 2)

# ================================================================ timeline
CAR = Image.open(CARCUT).convert("RGBA"); _a = np.asarray(CAR.getchannel("A"), np.float32)
CAR.putalpha(Image.fromarray((np.clip((_a - 70) / 185, 0, 1) * 255).astype(np.uint8))); CAR = CAR.crop(CAR.getbbox())

BEHIND = [  # (t0, t1, kind, payload)  kind: 'top' = picture + giant word behind the head ; 'bottom' = giant word behind the legs
    (0.25, 1.75, "top", ("করোলা ক্রস", True)),
    (1.75, 3.45, "bottom", "চিটাগাং স্টক"),
    (9.25, 12.85, "bottom", "পার্ল • ব্ল্যাক"),
    (32.45, 35.55, "bottom", "33,000 কিলো"),
    (38.95, 41.76, "top", ("পাবনা শোরুম", False)),
]
BARS = [  # (t0, t1, yellow line (t), white line (t))
    (5.60, 9.10, ("রেডি স্টকে", wt("রেডি")), ("অ্যাভেলেবল", wt("অ্যাভেলেবল"))),
    (24.30, 27.20, ("অটো পার্কিং", wt("অটো")), ("360 ক্যামেরা", wt("360"))),
    (35.75, 38.90, ("আজই", wt("আজই")), ("ভিজিট করুন", wt("ভিজিট"))),
]
LABELS = [  # teal label + shine on b-roll (t_label, t_shine, t_end, text, label xy, shine box)
    (wt("ZVG13"), wt("ZVG13") + 0.05, 20.50, "ZVG13 · 2023 মডেল", (330, 150), (40, 330, 700, 760)),
    (wt("পার্ল", 1), wt("পার্ল", 1) + 0.05, 23.70, "পার্ল কালার টু টোন", (330, 150), (20, 260, 700, 760)),
    (wt("অ্যালয়"), wt("অ্যালয়") + 0.05, 29.70, "অ্যালয় হুইলস", (300, 150), (40, 330, 700, 820)),
    (wt("সবকিছুই"), wt("সবকিছুই") + 0.05, 31.55, "সবকিছুই পাচ্ছেন", (330, 150), (40, 300, 700, 820)),
]
TALK_LABELS = [(wt("দুইটাই"), 15.30, "দুইটাই অ্যাভেলেবল"), (wt("গ্রেড"), 35.55, "অকশন গ্রেড ৪")]

# sound cues
cue("ambience", 0.0, dur=3.6)
for t0, t1, kind, _ in BEHIND:
    cue("swoosh", t0 - 0.05)
    if t0 > 4: cue("ambience", t0 - 0.2, -4, dur=min(3.4, t1 - t0 + 0.3))
for t0, t1, y, w_ in BARS: cue("swoosh_soft", t0 - 0.05); cue("click", y[1]); cue("click", w_[1], -2); cue("sparkle", w_[1] + 0.05)
for tl, ts, te, *_ in LABELS: cue("click", tl); cue("shine", ts)
for tl, te, _ in TALK_LABELS: cue("click", tl)

def render(fi):
    t = fi / FPS; si = min(int(t * SRC_FPS), NSRC - 1)
    fr, mt, head, mode = cam(si, t); img = grade(fr)
    bad = False
    if mt is not None and head is not None:
        hx_, ht_, hw_ = head; ma = np.asarray(mt)
        face = ma[int(clamp(ht_ + hw_ * 0.5, 0, H - 1)), int(clamp(hx_, 0, W - 1))]
        bad = face < 128 or ma.mean() > 0.30 * 255          # face missing from the matte, or matte swallowed the car
    if bad:
        # matte grabbed the car instead of the person -> soft body mask from the tracked head
        hx, ht, hw = head; bm = Image.new("L", (W, H), 0); d_ = ImageDraw.Draw(bm)
        d_.ellipse([hx - hw * 0.7, ht - hw * 0.15, hx + hw * 0.7, ht + hw * 1.25], fill=255)
        d_.rounded_rectangle([hx - hw * 1.75, ht + hw * 1.05, hx + hw * 1.75, H], hw * 0.6, fill=255)
        mt = bm.filter(ImageFilter.GaussianBlur(14))
    person = None
    if mt is not None: person = img.copy(); person.putalpha(mt)
    behind_drawn = False; bar_txt = None
    # sky tint + bar
    for t0, t1, yl, wl in BARS:
        if t0 - 0.3 <= t < t1 + 0.3:
            k = eo3(seg(t, t0 - 0.3, 0.6)) * (1 - eo3(seg(t, t1, 0.3)))
            img = sky_tint(img, mt, k)
            bh = 470 * eo3(seg(t, t0, 0.45)); bx0 = 470
            if bh > 2:
                col = np.zeros((int(bh), W - bx0, 4), np.uint8); kk = np.linspace(0, 1, int(bh))[:, None]
                col[..., 0] = 70 + (170 - 70) * kk; col[..., 1] = 140 + (210 - 140) * kk; col[..., 2] = 214 + (245 - 214) * kk
                col[..., 3] = (255 * (1 - kk ** 2.2) * (1 - eo3(seg(t, t1, 0.3)))).astype(np.uint8)
                img.alpha_composite(Image.fromarray(col), (bx0, 0))      # bar lives top-right
            bar_txt = (t0, t1, yl, wl, bx0)
            behind_drawn = True                       # bar is part of the sky: person stays in front
    # graphics behind the person
    for t0, t1, kind, pay in BEHIND:
        if t0 <= t < t1 + 0.3:
            out_k = eo3(seg(t, t1, 0.3)); p = seg(t, t0, 0.55)
            if kind == "top":
                txt, with_car = pay
                G = Image.new("RGBA", (W, 560), (0, 0, 0, 0))
                if with_car:
                    c = CAR.resize((620, int(CAR.height * 620 / CAR.width)), Image.LANCZOS); place(G, c, 400, 330, alpha=0.95)
                gw = giant(txt, 660, 170); place(G, gw, 380, 150)
                G = flare_wipe(G, p)
                if out_k: G.putalpha(G.getchannel("A").point(lambda v: int(v * (1 - out_k))))
                img.alpha_composite(G, (0, 40 + int(20 * (1 - eo3(p)))))
            else:
                img = light_band(img, seg(t, t0, 0.5) * (1 - out_k))
                gw = giant(pay, 690, 170, (150, 196, 222), (96, 132, 176))
                x = lerp(W / 2 + 60, W / 2, eo3(p))
                g2 = flare_wipe(gw, p)
                place(img, g2, x, H - 120, alpha=1 - out_k)
            behind_drawn = True
    if behind_drawn and person is not None: img.alpha_composite(person)       # person stays in front of the graphics
    if bar_txt:                                   # bar labels + burst sit on top so the head never hides them
        t0, t1, yl, wl, bx0 = bar_txt; fade = 1 - eo3(seg(t, t1, 0.25))
        for (txt, tt), cy, colr, sz in ((yl, 170, YEL, 58), (wl, 240, (255, 255, 255), 60)):
            p = seg(t, tt, 0.25)
            if p > 0:
                im = label(txt, sz, colr); s_ = min(1.0, 236 / im.info["adv"])
                place(img, im, bx0 + (W - bx0) / 2, cy + 14 * (1 - eo3(p)), alpha=eo3(p) * fade, scale=s_)
        img = burst(img, 600, 300, seg(t, wl[1] + 0.02, 0.45))
    # teal labels + shine on b-roll
    for tl, ts, te, txt, (lx, ly), box in LABELS:
        if tl - 0.02 <= t < te + 0.25:
            img = shine(img, box, seg(t, ts, 0.9))
            p = seg(t, tl, 0.3); im = label(txt, 58, TEAL, glow=(255, 255, 255))
            place(img, im, lx, ly + 10 * (1 - eo3(p)), alpha=eo3(p) * (1 - eo3(seg(t, te, 0.25))))
    for tl, te, txt in TALK_LABELS:
        if tl - 0.02 <= t < te + 0.25 and head is not None:
            p = seg(t, tl, 0.3); im = label(txt, 50, TEAL, glow=(255, 255, 255))
            place(img, im, clamp(head[0], im.width / 2, W - im.width / 2), head[1] - 40 + 10 * (1 - eo3(p)), alpha=eo3(p) * (1 - eo3(seg(t, te, 0.25))))
    logo_bug(img, t)
    return img.convert("RGB").tobytes()

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
