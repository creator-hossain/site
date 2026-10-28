# -*- coding: utf-8 -*-
"""Corolla Cross edit in the style of reference #10 (podcast band layout with many pop-in graphics).

Measured from the reference (1024x1280, 60 fps):
  * layout: sharp video BAND in the middle, the same picture blown up + blurred above/below, logo bug top-left
  * title: yellow rounded Latin word + small blue icon tile, white->cyan Bengali line under it, both dark-outlined,
    fade in/out with a blur
  * red alert: band turns red monochrome, yellow->black highlighter bar with black Bengali text, two tilted red
    warning triangles; a bass-drop impact
  * speech bubble: white rounded box with a tail over the speaker's head, black text, pops in
  * counter: big yellow number counting up, one digit replaced by a blue icon disc, red->blue pill under it
  * crown + small white line + big glowing white/green Bengali question at the bottom of the band
  * info card: navy gradient card, thin gold rim, gold 4-point stars on two corners, title, dashed rule, typed text
  * subtitle band: red->navy gradient strip with a white top line, small blue label, big red outlined line,
    white pills popping in one by one
  * icon tiles: white rounded tiles with a teal rim, colour icon + caption, added one by one into a row
usage: compose_v10.py SRC TRACK WORDS OUT [--preview t,..]
"""
import sys, os, json, subprocess, math, textwrap
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, TRACK, WORDS, OUT = sys.argv[1:5]
PREVIEW = sys.argv[6].split(",") if len(sys.argv) > 6 and sys.argv[5] == "--preview" else None
FPS, SRC_FPS = 50, 25
W, H = 720, 1280; SW, SH = 720, 1280
BY, BH = 190, 900                         # the sharp video band
F8 = os.path.join(HERE, "..", "fonts8")
BALOO = "/usr/share/fonts/truetype/bnx/BalooDa2-BN-ExtraBold.ttf"
POP8, POP6 = f"{F8}/poppins-latin-800-normal.ttf", f"{F8}/poppins-latin-600-normal.ttf"
HB6, HL6, HL5 = f"{F8}/hind-siliguri-bengali-600-normal.ttf", f"{F8}/hind-siliguri-latin-600-normal.ttf", f"{F8}/hind-siliguri-latin-500-normal.ttf"
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
    ZSHOT[k_] = max(1.0, 100 / float(np.median(hw_))) if m == "T" and len(hw_) else 1.0

WT = {}
for w in json.load(open(WORDS, encoding="utf-8")): WT.setdefault(w["w"], []).append(w["t"])
def wt(w, n=0): return WT[w][n]
CUES = []
def cue(sound, t, gain=0.0, **kw): CUES.append(dict(sound=sound, t=round(t, 3), gain=gain, **kw))

def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def eback(p, s=1.7): p = clamp(p, 0, 1) - 1; return 1 + (s + 1) * p ** 3 + s * p ** 2
def seg(t, a, d): return clamp((t - a) / d, 0, 1)

@lru_cache(maxsize=None)
def font(path, size): return ImageFont.truetype(path, size)
def place(dst, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0):
    if im is None or alpha <= 0.004: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.996:
        a = (np.asarray(im.getchannel("A"), np.float32) * alpha).astype(np.uint8); im = im.copy(); im.putalpha(Image.fromarray(a))
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 > x0 and y1 > y0: dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))
def grad(m, c0, c1, horiz=False):
    n = m.width if horiz else m.height; k = np.linspace(0, 1, n)
    g = (np.array(c0) * (1 - k[:, None]) + np.array(c1) * k[:, None]).astype(np.uint8)
    arr = np.repeat(g[None], m.height, 0) if horiz else np.repeat(g[:, None], m.width, 1)
    out = Image.fromarray(np.concatenate([arr, np.full((m.height, m.width, 1), 255, np.uint8)], 2)); out.putalpha(m); return out
@lru_cache(maxsize=None)
def icon(name, size): return Image.open(f"{ICONS}/{name}.png").convert("RGBA").resize((size, size), Image.LANCZOS)

def _bn(ch): return "ঀ" <= ch <= "৿" or ch in "‌‍"
@lru_cache(maxsize=None)
def tmask(txt, path, size, stroke=0, hind=False):
    """text mask (mixed Bengali/Latin when hind=True), with optional stroke; returns (fill mask, stroke mask, advance)."""
    if hind:
        runs = []
        for ch in txt:
            b = _bn(ch) if not (ch == " " and runs) else runs[-1][0]
            if runs and runs[-1][0] == b: runs[-1][1] += ch
            else: runs.append([b, ch])
        fl = [(font(HB6 if b else path, size), s) for b, s in runs]
    else:
        fl = [(font(path, size), txt)]
    asc, desc = fl[0][0].getmetrics(); pad = stroke + int(size * 0.25); adv = sum(f.getlength(s) for f, s in fl)
    m = Image.new("L", (int(adv + 2 * pad), asc + desc + 2 * pad), 0); ms = m.copy(); d = ImageDraw.Draw(m); ds = ImageDraw.Draw(ms); x = pad
    for f, s in fl:
        d.text((x, pad + asc), s, font=f, fill=255, anchor="ls")
        if stroke: ds.text((x, pad + asc), s, font=f, fill=255, anchor="ls", stroke_width=stroke, stroke_fill=255)
        x += f.getlength(s)
    return m, ms, adv
@lru_cache(maxsize=None)
def styled(txt, path, size, c0, c1, stroke=0, scol=(20, 20, 30), glow=None, hind=False, shadow=True):
    m, ms, adv = tmask(txt, path, size, stroke, hind)
    out = Image.new("RGBA", m.size, (0, 0, 0, 0))
    if glow:
        g = Image.new("RGBA", m.size, glow + (0,)); g.putalpha(ms.filter(ImageFilter.GaussianBlur(9)).point(lambda v: min(255, int(v * 1.5)))); out.alpha_composite(g)
    if shadow:
        s_ = Image.new("RGBA", m.size, (0, 0, 0, 0)); s_.putalpha((ms if stroke else m).filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.6)))
        out.alpha_composite(s_.transform(m.size, Image.AFFINE, (1, 0, -2, 0, 1, -3)))
    if stroke:
        sc = Image.new("RGBA", m.size, scol + (255,)); sc.putalpha(ms); out.alpha_composite(sc)
    out.alpha_composite(grad(m, c0, c1)); out.info["adv"] = adv; return out

# ================================================================ camera / band / fill
@lru_cache(maxsize=8)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
def band_box(si, t):
    k = SHOT[si]; a, b, mode = SHOTS[k]; drift = 1 + min(0.03, 0.004 * max(0, t - a))
    if mode == "T":
        z = ZSHOT[k] * drift; cw, ch = W / z, BH / z
        x0 = clamp(HX[si] - (W / 2) / z, 0, SW - cw); y0 = clamp(HTOP[si] - 170 / z, 0, SH - ch)
        head = ((HX[si] - x0) * z, (HTOP[si] - y0) * z + BY, HW[si] * z)
    else:
        z = drift; cw, ch = W / z, BH / z; x0 = (SW - cw) / 2; y0 = (SH - ch) / 2; head = None
    return (x0, y0, x0 + cw, y0 + ch), mode, head

def grade(a):
    a = (a / 255 - 0.5) * 1.05 + 0.51; g = a.mean(2, keepdims=True); a = g + (a - g) * 1.10
    return np.clip(a, 0, 1) * 255

def compose_base(si, t, red=0.0):
    fr = src_frame(si); box, mode, head = band_box(si, t)
    fill = fr.resize((72, 128), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
    fa = np.asarray(fill, np.float32) * 0.70
    band = np.asarray(fr.resize((W, BH), Image.LANCZOS, box=box), np.float32); band = grade(band)
    if red > 0:   # red alert: monochrome red, darker
        lum = (band @ np.array([0.3, 0.59, 0.11], np.float32))[..., None] / 255
        rr = np.clip(np.array([255, 64, 56], np.float32) * (0.04 + 1.15 * lum ** 1.35), 0, 255) * 0.9
        band = band * (1 - red) + rr * red
    fa[BY:BY + BH] = band
    return Image.fromarray(fa.astype(np.uint8)).convert("RGBA"), mode, head

# ================================================================ graphics
def logo_bug():
    im = Image.new("RGBA", (240, 52), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy, r = 24, 26, 20
    d.polygon([(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(30, 390, 60)], fill=(30, 200, 110, 255))
    place(im, icon("car-front-w", 24), cx, cy)
    t = styled("corolla", BALOO, 34, (255, 255, 255), (235, 240, 245), shadow=True); place(im, t, 52 + t.info["adv"] / 2 + 8, 28)
    return im
LOGO = logo_bug()

def title(img, t):
    t0, t1 = 2.00, 4.35
    if not (t0 <= t < t1 + 0.3): return
    a = eo3(seg(t, t0, 0.3)) * (1 - eo3(seg(t, t1, 0.3)))
    l1 = styled("Corolla Cross", BALOO, 66, (255, 240, 90), (255, 168, 20), stroke=4, scol=(70, 30, 0))
    l2 = styled("চিটাগাং স্টকে", BALOO, 54, (250, 255, 255), (90, 205, 255), stroke=4, scol=(10, 25, 60))
    tile = Image.new("RGBA", (74, 56), (0, 0, 0, 0)); ImageDraw.Draw(tile).rounded_rectangle([0, 0, 73, 55], 8, fill=(56, 130, 245, 255)); place(tile, icon("car-front-w", 38), 37, 28)
    lay = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
    place(lay, l1, W / 2 - 34, 70); place(lay, tile, W / 2 - 34 + l1.info["adv"] / 2 + 48, 62, angle=0); place(lay, l2, W / 2, 140)
    blur = (1 - a) * 8
    if blur > 0.3: lay = lay.filter(ImageFilter.GaussianBlur(blur))
    place(img, lay, W / 2, BY + 150, alpha=a)

def bubble(img, t, head, t0, t1, words):
    if not (t0 <= t < t1 + 0.15) or head is None: return
    f = font(HB6, 34); fw = int(sum(tmask(w_, HL6, 34, 0, True)[2] for w_, _ in words) + f.getlength(" ") * (len(words) - 1)) + 48; fh = 64
    sc = eback(seg(t, t0, 0.18)) * (1 - eo3(seg(t, t1, 0.14)))
    if sc <= 0.02: return
    im = Image.new("RGBA", (fw + 16, fh + 34), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new("L", im.size, 0); ImageDraw.Draw(sh).rounded_rectangle([6, 8, fw + 6, fh + 8], 16, fill=120)
    shc = Image.new("RGBA", im.size, (0, 0, 0, 0)); shc.putalpha(sh.filter(ImageFilter.GaussianBlur(5))); im.alpha_composite(shc)
    d.rounded_rectangle([2, 2, fw, fh], 16, fill=(255, 255, 255, 255), outline=(70, 70, 76, 255), width=2)
    d.polygon([(fw - 70, fh - 1), (fw - 40, fh - 1), (fw - 30, fh + 24)], fill=(255, 255, 255, 255))
    d.line([(fw - 70, fh), (fw - 30, fh + 24), (fw - 40, fh)], fill=(70, 70, 76, 255), width=2)
    x = 24
    for w_, tt in words:
        q = seg(t, tt, 0.12)
        if q > 0:
            m, ms, adv = tmask(w_, HL6, 34, 0, True); txt = grad(m, (25, 25, 30), (25, 25, 30))
            a_ = (np.asarray(txt.getchannel("A"), np.float32) * eo3(q)).astype(np.uint8); txt.putalpha(Image.fromarray(a_))
            im.alpha_composite(txt, (int(x - 8), int(fh / 2 - m.height / 2 + 2)))
        x += tmask(w_, HL6, 34, 0, True)[2] + f.getlength(" ")
    hx, ht, hw = head
    place(img, im, clamp(hx - fw / 2 + 50, im.width / 2 + 10, W - im.width / 2 - 10), max(BY + 60, ht - 60), scale=sc)

def triangle_warn(size):
    return icon("alert-triangle", size)
def check_badge(size): return icon("check-circle-2", size)

def highlighter(img, t, t0, t1, txt, alert):
    if not (t0 <= t < t1 + 0.2): return
    a = 1 - eo3(seg(t, t1, 0.2)); pw = eo3(seg(t, t0, 0.25))
    m, ms, adv = tmask(txt, BALOO, 50, 0, False)
    bw, bh = int(adv + 70), 76
    bar = Image.new("L", (bw, bh), 0); ImageDraw.Draw(bar).rectangle([0, 0, int(bw * pw), bh], fill=255)
    k = np.linspace(0, 1, bw)
    col = np.stack([np.interp(k, [0, 0.6, 1], [255, 210, 10]), np.interp(k, [0, 0.6, 1], [242, 236, 12]), np.interp(k, [0, 0.6, 1], [40, 20, 4])], 1).astype(np.uint8)
    lay = Image.fromarray(np.concatenate([np.repeat(col[None], bh, 0), np.full((bh, bw, 1), 255, np.uint8)], 2)); lay.putalpha(bar)
    q = seg(t, t0 + 0.12, 0.18)
    if q > 0:
        tx = grad(m, (16, 16, 16), (40, 30, 10)); aa = (np.asarray(tx.getchannel("A"), np.float32) * eo3(q)).astype(np.uint8); tx.putalpha(Image.fromarray(aa))
        lay.alpha_composite(tx, (int(35 - (m.width - adv) / 2), int(bh / 2 - m.height / 2 + 4)))
    cx, cy = W / 2, BY + 120
    place(img, lay, cx, cy, alpha=a)
    ic = triangle_warn(70) if alert else check_badge(64)
    for (dx, dy, ang, tt) in ((bw / 2 + 18, -bh / 2 - 6, -12, t0 + 0.2), (-bw / 2 - 22, bh / 2 + 6, 10, t0 + 0.28)):
        s = eback(seg(t, tt, 0.18))
        if s > 0.02: place(img, ic, cx + dx, cy + dy, alpha=a, scale=s, angle=ang)

def crown_img():
    return icon("crown", 120)
def crown_seq(img, t):
    t0, t1 = 11.05, 15.30
    if not (t0 <= t < t1 + 0.25): return
    a = 1 - eo3(seg(t, t1, 0.25)); yb = BY + BH - 70; ys = yb - 72
    words = [("পার্ল", wt("পার্ল")), ("কালার", wt("কালার")), ("ও", wt("এবং")), ("ব্ল্যাক", wt("ব্ল্যাক")), ("কালার", wt("কালার", 1))]
    f = font(HB6, 34); tot = f.getlength(" ".join(w for w, _ in words)); x = W / 2 - tot / 2
    for w_, tt in words:
        q = seg(t, tt, 0.14)
        if q > 0:
            im = styled(w_, HL6, 34, (255, 255, 255), (235, 240, 245), stroke=3, scol=(15, 20, 30), hind=True)
            place(img, im, x + im.info["adv"] / 2, ys + 8 * (1 - eo3(q)), alpha=eo3(q) * a)
        x += f.getlength(w_ + " ")
    tb = wt("দুইটাই")
    s = eback(seg(t, tb - 0.08, 0.22))
    if s > 0.02: place(img, crown_img(), W / 2 - 40, ys - 70, alpha=a, scale=s, angle=8 * math.sin(6 * max(0, t - tb)) * math.exp(-2 * max(0, t - tb)))
    q = seg(t, tb, 0.2)
    if q > 0:
        big = styled("দুইটাই অ্যাভেলেবল!", BALOO, 70, (255, 255, 255), (170, 255, 150), stroke=3, scol=(10, 60, 20), glow=(40, 230, 70))
        place(img, big, W / 2, yb, alpha=eo3(q) * a, scale=lerp(1.25, 1, eo3(q)))

def star4(size, col=(255, 200, 40)):
    S = 2; im = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0)); c = size * S / 2; r = size * S / 2; r2 = r * 0.28
    pts = []
    for k in range(8):
        ang = math.pi / 4 * k - math.pi / 2; rr = r if k % 2 == 0 else r2; pts.append((c + rr * math.cos(ang), c + rr * math.sin(ang)))
    ImageDraw.Draw(im).polygon(pts, fill=col + (255,)); return im.resize((size, size), Image.LANCZOS)
STAR = star4(64)
CARD_TXT = "2023 model Corolla Cross in pearl two-tone with a hard top and the Modellista body kit."
CARD_Y = "READY STOCK · CHITTAGONG"
def card(img, t):
    t0, t1 = 17.15, 23.65
    if not (t0 <= t < t1 + 0.2): return
    a = 1 - eo3(seg(t, t1, 0.2)); p = eo3(seg(t, t0, 0.22))
    cw, ch = 290, 400; x0, y0 = 26, BY + 170
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], 18, fill=242)
    g = grad(m, (18, 46, 108), (6, 12, 34)); im.alpha_composite(g)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, cw - 1, ch - 1], 18, outline=(232, 190, 60, 255), width=2)
    d = ImageDraw.Draw(im); q = seg(t, t0 + 0.35, 0.2)
    if q > 0:
        tt_ = styled("ZVG13", POP6, 40, (255, 222, 120), (255, 255, 255), shadow=False); place(im, tt_, cw / 2, 50, alpha=eo3(q))
        for k in range(18):
            xx = 26 + k * 13; d.line([(xx, 86), (xx + 7, 86)], fill=(240, 240, 240, int(220 * eo3(q))), width=2)
    nch = int(max(0, t - (t0 + 0.6)) * 22)
    lines = textwrap.wrap(CARD_TXT, 24); y = 104; shown = 0; f = font(HL5, 21)
    for ln in lines:
        part = ln[:max(0, nch - shown)]; shown += len(ln)
        if part: d.text((cw / 2, y), part, font=f, fill=(236, 240, 248, 255), anchor="mt")
        y += 30
    rest = max(0, nch - shown - 4)
    if rest > 0: d.text((cw / 2, y + 18), CARD_Y[:rest], font=font(POP6, 19), fill=(255, 214, 60, 255), anchor="mt")
    cardim = im
    place(img, cardim, x0 + cw / 2, y0 + ch / 2, alpha=a * p, scale=lerp(0.86, 1, p))
    for (sx, sy, tt) in ((x0 + cw - 4, y0 + 4, t0 + 0.22), (x0 + 6, y0 + ch - 4, t0 + 0.3)):
        s = eback(seg(t, tt, 0.2))
        if s > 0.02: place(img, STAR, sx, sy, alpha=a, scale=s, angle=12 * math.sin(3 * (t - tt)))

PILLS = [("অটো পার্কিং", wt("অটো")), ("360 ক্যামেরা", wt("360")), ("অ্যালয় হুইলস", wt("অ্যালয়")),
         ("ফগ লাইট", wt("ফগ")), ("সিট হিটার", wt("সিট")), ("ক্রুজ কন্ট্রোল", wt("ক্রুজ"))]
SB_T0, SB_T1 = 23.92, 31.55
@lru_cache(maxsize=None)
def pill_img(txt):
    m, ms, adv = tmask(txt, HL6, 26, 0, True); w, h = int(adv + 40), 46
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], 23, fill=(244, 244, 246, 255), outline=(40, 40, 50, 255), width=2)
    tx = grad(m, (30, 30, 36), (30, 30, 36)); im.alpha_composite(tx, (int(20 - (m.width - adv) / 2), int(h / 2 - m.height / 2 + 2))); return im
def sub_band(img, t):
    if not (SB_T0 <= t < SB_T1): return
    y0, hb = BY + BH - 236, 236
    pb = eo3(seg(t, 24.85, 0.28))
    if pb > 0:
        ww = int(W * pb); k = np.linspace(0, 1, W)[:ww]
        col = np.stack([np.interp(k, [0, 1], [126, 22]), np.interp(k, [0, 1], [14, 30]), np.interp(k, [0, 1], [34, 92])], 1).astype(np.uint8)
        arr = np.concatenate([np.repeat(col[None], hb, 0), np.full((hb, ww, 1), 236, np.uint8)], 2)
        img.alpha_composite(Image.fromarray(arr), (0, y0)); ImageDraw.Draw(img).line([(0, y0), (ww, y0)], fill=(255, 255, 255, 255), width=3)
    q = seg(t, SB_T0, 0.16)
    if q > 0:
        lab = styled("গাড়িটির সঙ্গে কিন্তু", HL6, 28, (255, 255, 255), (230, 236, 255), hind=True, shadow=False)
        w_ = lab.info["adv"] + 30; bx = Image.new("RGBA", (int(w_), 42), (0, 0, 0, 0)); ImageDraw.Draw(bx).rectangle([0, 0, int(w_) - 1, 41], fill=(40, 84, 176, 245), outline=(200, 215, 255, 255))
        place(bx, lab, w_ / 2, 22); place(img, bx, W / 2, y0, alpha=eo3(q), scale=eback(q))
    q = seg(t, 24.40, 0.2)
    if q > 0:
        big = styled("সবকিছুই পাচ্ছেন", BALOO, 62, (255, 40, 50), (220, 10, 30), stroke=3, scol=(255, 255, 255))
        place(img, big, W / 2, y0 + 66 + 14 * (1 - eo3(q)), alpha=eo3(q))
    for i, (txt, tt) in enumerate(PILLS):
        s = eback(seg(t, tt, 0.18))
        if s <= 0.02: continue
        row, col_ = divmod(i, 3); rowpills = [pill_img(p) for p, _ in PILLS[row * 3:row * 3 + 3]]
        tot = sum(p.width for p in rowpills) + 14 * (len(rowpills) - 1); x = W / 2 - tot / 2 + sum(p.width + 14 for p in rowpills[:col_])
        p = rowpills[col_]; place(img, p, x + p.width / 2, y0 + 140 + row * 56, scale=s)

def counter(img, t):
    t0, t1 = 32.60, 35.55
    if not (t0 <= t < t1 + 0.2): return
    a = 1 - eo3(seg(t, t1, 0.2)); tc = wt("33,000")
    if t < tc - 0.05: return
    v = int(33000 * eo3(seg(t, tc, 0.7)) / 100) * 100 if t < tc + 0.7 else 33000
    s = f"{v:,}"; f = font(POP8, 86)
    parts = [("txt", s[:-1]), ("icon", None), ("txt", s[-1] + " KM")] if v >= 1000 else [("txt", s + " KM")]
    ims = []
    for kind, val in parts:
        if kind == "txt": ims.append(styled(val, POP8, 86, (255, 230, 40), (255, 190, 0), stroke=3, scol=(60, 40, 0)))
        else:
            dsk = Image.new("RGBA", (82, 82), (0, 0, 0, 0)); ImageDraw.Draw(dsk).ellipse([2, 2, 79, 79], fill=(40, 90, 230, 255), outline=(255, 255, 255, 255), width=3)
            place(dsk, icon("gauge-w", 50), 41, 41); dsk.info["adv"] = 76; ims.append(dsk)
    tot = sum(i.info["adv"] for i in ims); x = W / 2 - tot / 2; cy = BY + 150
    for i in ims:
        place(img, i, x + i.info["adv"] / 2, cy, alpha=a); x += i.info["adv"]
    q = seg(t, tc + 0.35, 0.2)
    if q > 0:
        lab = styled("মাইলেজ মাত্র", HL6, 30, (255, 255, 255), (240, 240, 255), hind=True, shadow=False); w_ = int(lab.info["adv"] + 40)
        m = Image.new("L", (w_, 46), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w_ - 1, 45], 23, fill=255)
        pl = grad(m, (230, 30, 60), (40, 60, 180), horiz=True); place(pl, lab, w_ / 2, 25)
        place(img, pl, W / 2, cy + 72, alpha=a * eo3(q), scale=eback(q))

TILES = [(wt("অকশন"), "অকশন গ্রেড ৪", "award"), (wt("শোরুম"), "আমাদের শোরুম", "store"),
         (wt("আব্দুল"), "আব্দুল হামিদ রোড", "map-pin"), (wt("পাবনা"), "পাবনা সদর", "building-2")]
RED0, RED1 = 35.70, 37.25
@lru_cache(maxsize=None)
def tile_img(txt, ic):
    w, h = 140, 160; im = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    sh = Image.new("L", im.size, 0); ImageDraw.Draw(sh).rounded_rectangle([8, 12, w + 6, h + 10], 16, fill=110)
    shc = Image.new("RGBA", im.size, (0, 0, 0, 0)); shc.putalpha(sh.filter(ImageFilter.GaussianBlur(5))); im.alpha_composite(shc)
    d = ImageDraw.Draw(im); d.rounded_rectangle([4, 4, w + 3, h + 3], 16, fill=(252, 252, 250, 255), outline=(70, 190, 160, 255), width=3)
    d.ellipse([w / 2 + 4 - 36, 18, w / 2 + 4 + 36, 90], fill=(222, 246, 238, 255)); place(im, icon(ic, 58), w / 2 + 4, 54)
    lines = textwrap.wrap(txt, 9) if len(txt) > 10 else [txt]
    y = 110 if len(lines) == 1 else 102
    for ln in lines[:2]:
        lm = styled(ln, HL6, 22, (30, 30, 34), (30, 30, 34), hind=True, shadow=False); place(im, lm, w / 2 + 4, y); y += 26
    return im
def tiles(img, t):
    vis = [(tt, txt, ic) for tt, txt, ic in TILES if t >= tt]
    if not vis or t >= DUR: return
    hide = 1 - (eo3(seg(t, RED0 - 0.15, 0.15)) * (1 - eo3(seg(t, RED1, 0.25)))) if RED0 - 0.15 <= t < RED1 + 0.25 else 1.0
    if hide <= 0.02: return
    n = len(vis); sp = 156; cy = BY + BH - 112
    for i, (tt, txt, ic) in enumerate(vis):
        tx = W / 2 + (i - (n - 1) / 2) * sp
        if i < n - 1:
            prev = W / 2 + (i - (n - 2) / 2) * sp; tx = lerp(prev, tx, eo3(seg(t, vis[-1][0], 0.25)))
        s = eback(seg(t, tt, 0.22)) if i == n - 1 else 1.0
        place(img, tile_img(txt, ic), tx, cy, alpha=hide * (eo3(seg(t, tt, 0.15)) if i == n - 1 else 1), scale=s)

def render(fi):
    t = fi / FPS; si = min(int(t * SRC_FPS), NSRC - 1)
    red = eo3(seg(t, RED0, 0.06)) * (1 - eo3(seg(t, RED1, 0.12))) if RED0 <= t < RED1 + 0.12 else 0.0
    img, mode, head = compose_base(si, t, red)
    place(img, LOGO, 24 + LOGO.width / 2, BY + 22 + LOGO.height / 2)
    title(img, t)
    bubble(img, t, head, 5.62, 7.10, [("বেশ", 5.62), ("কয়েকটি", wt("কয়েকটি")), ("ইউনিট!", wt("ইউনিট"))])
    highlighter(img, t, 7.60, 9.05, "রেডি স্টকে অ্যাভেলেবল", False)
    crown_seq(img, t); card(img, t); sub_band(img, t); counter(img, t); tiles(img, t)
    highlighter(img, t, RED0 + 0.02, RED1, "আজই ভিজিট করুন", True)
    if t > DUR - 0.6:
        a = 1 - seg(t, DUR - 0.6, 0.56); img = Image.fromarray((np.asarray(img.convert("RGB"), np.float32) * a).astype(np.uint8))
    return img.convert("RGB").tobytes()

# ================================================================ sound cues (grammar learned from reference #10)
cue("music", 0.0, dur=round(DUR, 3))
cue("swish", 5.58)                                                    # speech bubble
cue("pop", 7.60)                                                      # highlighter label (positive)
cue("ding", wt("দুইটাই") - 0.1)                                         # crown + big line
cue("lowwhoosh", 17.12)                                               # info card
cue("pop", SB_T0); cue("lowwhoosh", 24.80, -2)                        # subtitle label, band
for _, tt in PILLS: cue("pop", tt, -3)
cue("count", wt("33,000"))
for tt, *_r in TILES: cue("swell", tt - 0.12)
cue("impact", RED0 - 0.02)                                            # red alert
for c in (15.40, 23.80, 31.64): cue("tick", c)

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
