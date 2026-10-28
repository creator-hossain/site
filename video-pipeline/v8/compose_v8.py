# -*- coding: utf-8 -*-
"""Corolla Cross edit in the style of reference #8 (person keyed onto an illustrated sky 'world').

Measured from the reference (1280x736, 30 fps):
  * world in : person flashes green -> diagonal GLASS WIPE (bright refracting edge) -> pale sky (203,240,250) with a
               sun glow top-left; the person's colour cycles red > orange > yellow > green > teal > normal;
               the illustration rises from the bottom (ease-out ~0.3 s), sits behind the person
  * big topic word in Poppins ExtraBold navy (26,65,125) fades + rises in; a translucent white pill grows out of a
    thin line on top of it, navy Poppins SemiBold text inside ('Solar' / 'energy use')
  * a flat 3D map (extruded, drop shadow) slides in from the edge, small navy Hind Siliguri words appear beside it
  * world out: every graphic slides off to the right (ease-in), glass wipe back to the real background
  * caption box: pale box (214,233,241) grows from its right edge, words rise into it one by one as spoken
    (clipped by the box); pair = pale box + navy box (34,56,122) with white words, offset to the right
  * light leak: warm orange light from the left -> pure white -> cut -> washed picture settles, warm edge lingers
  * jump cut covered by a glowing white blur of the person; fade to black at the end
usage: compose_v8.py SRC MATTE TRACK WORDS CARDIR OUT [--preview t,..]
"""
import sys, os, json, subprocess, math
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, MAT, TRACK, WORDS, CARDIR, OUT = sys.argv[1:7]
PREVIEW = sys.argv[8].split(",") if len(sys.argv) > 8 and sys.argv[7] == "--preview" else None
FPS, SRC_FPS = 50, 25
W, H = 720, 1280
SW, SH = 720, 1280
F8 = os.path.join(HERE, "..", "fonts8")
POP8, POP6 = f"{F8}/poppins-latin-800-normal.ttf", f"{F8}/poppins-latin-600-normal.ttf"
HIND = {600: (f"{F8}/hind-siliguri-bengali-600-normal.ttf", f"{F8}/hind-siliguri-latin-600-normal.ttf"),
        700: (f"{F8}/hind-siliguri-bengali-700-normal.ttf", f"{F8}/hind-siliguri-latin-700-normal.ttf")}
NAVY = (26, 62, 122); INK = (30, 58, 102); BOXF = (214, 233, 241); BOXN = (34, 56, 122); BOXT = (226, 234, 255)
SKY_T, SKY_B = np.array([206, 241, 251.]), np.array([186, 231, 248.])

TR = json.load(open(TRACK)); HX, HTOP, HW, SHOT, SHOTS = (np.array(TR[k], float) if k in ("hx", "htop", "hw") else TR[k] for k in ("hx", "htop", "hw", "shot", "shots"))
NSRC = len(HX); DUR = NSRC / SRC_FPS
def _smooth(v, k=9):
    out = v.copy()
    for a, b, _ in SHOTS:
        i0, i1 = int(a * SRC_FPS), min(NSRC, int(b * SRC_FPS))
        if i1 - i0 > k: out[i0:i1] = np.convolve(np.pad(v[i0:i1], k // 2, mode="edge"), np.ones(k) / k, "valid")
    return out
HX, HTOP = _smooth(HX), _smooth(HTOP)
ZSHOT = {}
for k_, (a, b, m) in enumerate(SHOTS):
    seg_hw = HW[int(a * SRC_FPS):min(NSRC, int(b * SRC_FPS))]
    ZSHOT[k_] = max(1.0, 118 / float(np.median(seg_hw))) if m == "T" and len(seg_hw) else 1.0

WT = {}
for w in json.load(open(WORDS, encoding="utf-8")): WT.setdefault(w["w"], []).append(w["t"])
def wt(w, n=0): return WT[w][n]
CUES = []
def cue(sound, t, gain=0.0, **kw): CUES.append(dict(sound=sound, t=round(t, 3), gain=gain, **kw))

def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def ei3(p): p = clamp(p, 0, 1); return p ** 3
def eio(p): p = clamp(p, 0, 1); return 0.5 - 0.5 * math.cos(math.pi * p)
def seg(t, a, d): return clamp((t - a) / d, 0, 1)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_yi, _xi = np.mgrid[0:H, 0:W]

# ================================================================ text
@lru_cache(maxsize=None)
def font(path, size): return ImageFont.truetype(path, size)
def _bn(ch): return "ঀ" <= ch <= "৿" or ch in "‌‍"
def _runs(txt):
    runs = []
    for ch in txt:
        b = _bn(ch) if not (ch == " " and runs) else runs[-1][0]
        if runs and runs[-1][0] == b: runs[-1][1] += ch
        else: runs.append([b, ch])
    return runs
@lru_cache(maxsize=None)
def hind_mask(txt, size, weight=600):
    """mixed Bengali/Latin text (Hind Siliguri) -> L mask tightly around the line box, plus baseline y."""
    fb, fl = font(HIND[weight][0], size), font(HIND[weight][1], size)
    asc, desc = fb.getmetrics(); pad = int(size * 0.3)
    runs = [(fb if b else fl, s) for b, s in _runs(txt)]; adv = sum(f.getlength(s) for f, s in runs)
    m = Image.new("L", (int(adv + 2 * pad), asc + desc + 2 * pad), 0); d = ImageDraw.Draw(m); x = pad
    for f, s in runs: d.text((x, pad + asc), s, font=f, fill=255, anchor="ls"); x += f.getlength(s)
    return m, pad, adv
def colorize(m, col, col2=None):
    out = Image.new("RGBA", m.size, col + (255,))
    if col2 is not None:
        k = np.linspace(0, 1, m.height)[:, None, None]; g = (np.array(col) * (1 - k) + np.array(col2) * k).astype(np.uint8)
        out = Image.fromarray(np.concatenate([np.repeat(g, m.width, 1), np.full((m.height, m.width, 1), 255, np.uint8)], 2))
    out.putalpha(m); return out

def place(dst, im, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.004: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.996:
        a = (np.asarray(im.getchannel("A"), np.float32) * alpha).astype(np.uint8); im = im.copy(); im.putalpha(Image.fromarray(a))
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 > x0 and y1 > y0: dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

# ================================================================ world assets
def _shadowed(img, ext=0, ext_col=None, sh=(6, 16), blur=10, sh_a=0.35):
    """flat object -> extruded 3D slab (darker copy shifted down) + soft drop shadow."""
    pad = 40; w, h = img.size; out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad + ext), (0, 0, 0, 0))
    a = img.getchannel("A")
    s = Image.new("RGBA", out.size, (20, 40, 70, 0)); sm = Image.new("L", out.size, 0); sm.paste(a, (pad + sh[0], pad + sh[1] + ext))
    s.putalpha(sm.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * sh_a))); out.alpha_composite(s)
    if ext:
        for k in range(ext, 0, -1):
            sl = Image.new("RGBA", img.size, ext_col + (255,)); sl.putalpha(a); out.alpha_composite(sl, (pad, pad + k))
    out.alpha_composite(img, (pad, pad)); return out

def make_map():
    rings = json.load(open(os.path.join(HERE, "bd_rings.json")))
    k = math.cos(math.radians(23.7)); lon0, lat1 = 88.0, 26.65; S = 4
    tw = 205; sc = tw / ((92.68 - lon0) * k)
    def pr(lo, la): return ((lo - lon0) * k * sc * S + 4 * S, (lat1 - la) * sc * S + 4 * S)
    hh = int((lat1 - 20.7) * sc) + 8
    m = Image.new("L", ((tw + 8) * S, hh * S), 0); d = ImageDraw.Draw(m)
    for r in rings: d.polygon([pr(*p) for p in r], fill=255)
    m = m.resize((tw + 8, hh), Image.LANCZOS)
    flag = Image.new("RGBA", m.size, (0, 106, 78, 255)); fd = ImageDraw.Draw(flag)
    cx, cy, rr = m.width * 0.47, m.height * 0.40, m.width * 0.24
    fd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(244, 42, 65, 255))
    edge = m.filter(ImageFilter.MinFilter(5)); rim = Image.new("RGBA", m.size, (120, 200, 160, 255)); rim.putalpha(Image.fromarray(np.clip(np.asarray(m, int) - np.asarray(edge, int), 0, 255).astype(np.uint8)))
    flag.putalpha(m); flag.alpha_composite(rim)
    px, py = pr(91.83, 22.34); px, py = px / S, py / S       # Chittagong pin
    pd = ImageDraw.Draw(flag); pd.ellipse([px - 9, py - 9, px + 9, py + 9], fill=(255, 255, 255, 255), outline=NAVY + (255,), width=4)
    return _shadowed(flag, 9, (0, 66, 48))

def make_swatch():
    S = 2; d0 = 150; im = Image.new("RGBA", ((d0 + 110) * S, (d0 + 10) * S), (0, 0, 0, 0))
    def disc(c0, c1, x):
        g = Image.new("RGBA", (d0 * S, d0 * S)); k = np.linspace(0, 1, d0 * S)[:, None, None]
        arr = (np.array(c0) * (1 - k) + np.array(c1) * k).astype(np.uint8)
        g = Image.fromarray(np.concatenate([np.repeat(arr, d0 * S, 1), np.full((d0 * S, d0 * S, 1), 255, np.uint8)], 2))
        mk = Image.new("L", g.size, 0); ImageDraw.Draw(mk).ellipse([0, 0, d0 * S - 1, d0 * S - 1], fill=255); g.putalpha(mk)
        hl = Image.new("L", g.size, 0); ImageDraw.Draw(hl).ellipse([d0 * S * 0.18, d0 * S * 0.1, d0 * S * 0.62, d0 * S * 0.38], fill=150)
        hlc = Image.new("RGBA", g.size, (255, 255, 255, 0)); hlc.putalpha(Image.fromarray(np.minimum(np.asarray(hl.filter(ImageFilter.GaussianBlur(14))), np.asarray(mk))))
        g.alpha_composite(hlc); im.alpha_composite(g, (x * S, 0))
    disc((252, 252, 248), (205, 206, 198), 0); disc((74, 74, 82), (8, 8, 12), 110)
    return _shadowed(im.resize((im.width // S, im.height // S), Image.LANCZOS), 8, (120, 130, 150))

def make_badge():
    S = 2; w, h = 230, 170; im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], 22 * S, fill=(255, 255, 255, 255), outline=NAVY + (255,), width=5 * S)
    t = "AUCTION GRADE"; f = font(POP6, 19 * S); d.text((w * S / 2, 36 * S), t, font=f, fill=NAVY, anchor="mm")
    cx, cy, r = w * S / 2, 108 * S, 46 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(222, 38, 48, 255)); d.text((cx, cy + 4 * S), "4", font=font(POP8, 70 * S), fill=(255, 255, 255), anchor="mm")
    im = im.resize((w, h), Image.LANCZOS).rotate(6, resample=Image.BICUBIC, expand=True)
    return _shadowed(im, 7, (150, 165, 190))

def make_platform():
    S = 2; w, h = 1240, 300; im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 40 * S, w * S, h * S], fill=(118, 142, 172, 255))                         # rim
    top = Image.new("RGBA", (w * S, (h - 40) * S)); k = np.linspace(0, 1, (h - 40) * S)[:, None, None]
    arr = (np.array([246, 250, 252]) * (1 - k) + np.array([176, 196, 216]) * k).astype(np.uint8)
    top = Image.fromarray(np.concatenate([np.repeat(arr, w * S, 1), np.full(((h - 40) * S, w * S, 1), 255, np.uint8)], 2))
    mk = Image.new("L", top.size, 0); ImageDraw.Draw(mk).ellipse([0, 0, w * S, (h - 40) * S - 1], fill=255); top.putalpha(mk)
    im.alpha_composite(top, (0, 0)); ring = Image.new("L", im.size, 0)
    ImageDraw.Draw(ring).ellipse([60 * S, 30 * S, (w - 60) * S, (h - 70) * S], outline=255, width=3 * S)
    rc = Image.new("RGBA", im.size, (255, 255, 255, 0)); rc.putalpha(ring.point(lambda v: int(v * 0.7))); im.alpha_composite(rc)
    return im.resize((w, h), Image.LANCZOS)

def load_car(name, flip, scale):
    c = Image.open(os.path.join(CARDIR, f"cut_u2net_car_{name}.png")).convert("RGBA"); a = np.asarray(c.getchannel("A"), np.float32)
    c.putalpha(Image.fromarray((np.clip((a - 70) / 185, 0, 1) * 255).astype(np.uint8)))
    if flip: c = c.transpose(Image.FLIP_LEFT_RIGHT)
    bb = c.getbbox(); c = c.crop((0 if flip else bb[0], bb[1], bb[2] if flip else W, bb[3]))   # keep the frame-edge side flush
    return c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)

def make_bg():
    k = (_yy / H)[..., None]; a = SKY_T * (1 - k) + SKY_B * k
    for (cx, cy, r, s) in ((170, 330, 150, 0.85), (170, 330, 420, 0.45)):
        g = np.exp(-(((_xx - cx) ** 2 + (_yy - cy) ** 2) / (r * r)))[..., None] * s; a = a + (255 - a) * g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

BG = make_bg(); PLATFORM = make_platform()
ELEMS = dict(map=make_map(), swatch=make_swatch(), badge=make_badge())

@lru_cache(maxsize=None)
def big_word(txt):
    s = 160
    while font(POP8, s).getlength(txt) > 600: s -= 4
    f = font(POP8, s); asc, desc = f.getmetrics(); m = Image.new("L", (int(f.getlength(txt)) + 40, asc + desc + 20), 0)
    ImageDraw.Draw(m).text((20, 10 + asc), txt, font=f, fill=255, anchor="ls"); m = m.crop(m.getbbox())
    return colorize(m, NAVY), s

@lru_cache(maxsize=None)
def pill_full(txt, size):
    f = font(POP6, size); tw = f.getlength(txt); h = int(size * 1.55); w = int(tw + size * 1.3)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=(255, 255, 255, 200), outline=(255, 255, 255, 235), width=2)
    d.text((w / 2, h / 2 + 1), txt, font=f, fill=INK, anchor="mm"); return im

def pill_at(txt, size, p):
    """thin line (p<0.25) then grows outward from the centre."""
    full = pill_full(txt, size); w, h = full.size
    if p <= 0: return None
    if p < 0.25: ww = 5; a = p / 0.25
    else: ww = int(lerp(5, w, eo3((p - 0.25) / 0.75))); a = 1
    x0 = (w - ww) // 2; m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([x0, 0, x0 + ww - 1, h - 1], min(h // 2, ww // 2), fill=int(255 * a))
    out = full.copy(); out.putalpha(Image.fromarray(np.minimum(np.asarray(full.getchannel("A")), np.asarray(m)))); return out

# ================================================================ worlds
WORLDS = [
    dict(t0=0.233, slide=5.22, wipe_out=5.50, car=("29.0", False, 0.86), word=("Corolla", wt("করোলা")), pill=("cross", wt("ক্রস")),
         elem=("map", wt("চিটাগাং") - 0.12, "L"),
         lines=[[("Chittagong", wt("চিটাগাং")), ("স্টক", wt("স্টকের"))], [("ধারণা", wt("ধারণা")), ("চলে", wt("চলে")), ("এসেছে", wt("এসেছে"))]]),
    dict(t0=9.17, slide=None, wipe_out=None, end=15.40, car=("16.4", True, 1.0), word=("2 Colors", wt("দুইটাই")), pill=("available", wt("অ্যাভেলেবল", 1)),
         elem=("swatch", wt("পার্ল") - 0.12, "R"),
         lines=[[("পার্ল", wt("পার্ল")), ("কালার", wt("কালার"))], [("ব্ল্যাক", wt("ব্ল্যাক")), ("কালার", wt("কালার", 1))]]),
    dict(t0=31.64, slide=35.30, wipe_out=35.60, car=("17.6", False, 0.86), word=("33,000", wt("33,000")), pill=("km", wt("কিলো")),
         elem=("badge", wt("অকশন") - 0.12, "L"), held=31.60,
         lines=[[("অকশন", wt("অকশন")), ("গ্রেড", wt("গ্রেড"))], [("রয়েছে", wt("রয়েছে")), ("৪", wt("ফোর"))]]),
]
for w_ in WORLDS:
    w_["car_im"] = load_car(*w_["car"])
    w_["end"] = w_.get("end") or (w_["wipe_out"] + 0.16)

def world_of(t):
    for w_ in WORLDS:
        if w_["t0"] <= t < w_["end"]: return w_
    return None

def world_layer(w_, t):
    img = BG.copy(); t0 = w_["t0"]
    dx = W * 1.3 * ei3(seg(t, w_["slide"], 0.34)) if w_["slide"] else 0.0
    # big word + pill (behind the illustration)
    txt, tw_ = w_["word"]; p = seg(t, tw_, 0.16)
    if p > 0:
        bw, s = big_word(txt); cy = 215 + 22 * (1 - eo3(p))
        place(img, bw, W / 2 + dx, cy, alpha=eo3(p), scale=lerp(1.05, 1, eo3(p)))
        ptxt, pt = w_["pill"]; pp = seg(t, pt, 0.36)
        if pp > 0:
            pim = pill_at(ptxt, max(30, int(s * 0.22)), pp)
            if pim is not None: place(img, pim, W / 2 + dx + bw.width * 0.06, cy + bw.height * 0.16)
    # illustration: platform + car, rises from the bottom
    p = seg(t, t0 + 0.20, 0.36)
    if p > 0:
        rise = (1 - eo3(p)) * 520; sc = lerp(0.9, 1.0, eo3(p))
        car = w_["car_im"]; flip = w_["car"][1]
        place(img, PLATFORM, W / 2 + dx, H - 50 + rise, scale=sc)
        cw_ = car.width * sc; ch_ = car.height * sc                        # keep the car's cut edge flush with the frame
        place(img, car, (cw_ / 2 if flip else W - cw_ / 2) + dx, H - 150 * sc - ch_ / 2 + rise, scale=sc)
    # element (map / swatch / badge) slides in from its side + words beside it
    kind, te, side = w_["elem"]; p = seg(t, te, 0.2)
    if p > 0:
        el = ELEMS[kind]; fx = 34 + el.width / 2 - 40 if side == "L" else W - el.width / 2 + 28
        x0 = -el.width / 2 if side == "L" else W + el.width / 2
        place(img, el, lerp(x0, fx, eo3(p)) + dx, 560 if side == "L" else 478)
        lx = 44 if side == "L" else W - 290
        for li, line in enumerate(w_["lines"]):
            size = 40 if li == 0 else 30; y = 318 if li == 0 else 358; x = lx + (0 if li == 0 else 36)
            full, pad, adv = hind_mask(" ".join(wd for wd, _ in line), size)
            xs = x
            for wd, tt in line:
                m, pd, a_ = hind_mask(wd, size); q = seg(t, tt, 0.16)
                if q > 0: place(img, colorize(m, INK), xs + m.width / 2 - pd + 10 * (1 - eo3(q)) + dx, y, alpha=eo3(q))
                xs += a_ + font(HIND[600][0], size).getlength(" ")
    return img

# ================================================================ captions (boxes)
BOXES = [  # (t_in, t_out, light words, navy_in, navy words)
    (5.66, 7.05, [("বেশ", 5.70), ("কয়েকটি", wt("কয়েকটি")), ("ইউনিট", wt("ইউনিট"))], None, []),
    (7.12, 8.97, [("চিটাগাং", wt("চিটাগাং", 1)), ("রেডি", wt("রেডি")), ("স্টকে", wt("স্টকে"))], 8.30, [("অ্যাভেলেবল", wt("অ্যাভেলেবল"))]),
    (17.15, 20.45, [("ZVG13", wt("ZVG13"))], 18.45, [("2023", wt("2023")), ("মডেল", wt("মডেল"))]),
    (20.62, 23.62, [("পার্ল", wt("পার্ল", 1)), ("কালার", wt("কালার", 2)), ("টু", wt("টু")), ("টোন", wt("টোন"))], 21.90,
     [("হার্ড", wt("হার্ড")), ("টপ", wt("টপ")), ("+", wt("এবং", 1)), ("মডেলিস্টা", wt("মডেলিস্টা")), ("বডি", wt("বডি")), ("কিট", wt("কিট"))]),
    (24.95, 27.40, [("অটো", wt("অটো")), ("পার্কিং", wt("পার্কিং"))], 25.95, [("360", wt("360")), ("ক্যামেরা", wt("ক্যামেরা"))]),
    (27.45, 31.45, [("অ্যালয়", 27.55), ("হুইলস", 27.62), ("·", 28.0), ("ফগ", wt("ফগ")), ("লাইট", wt("লাইট"))], 28.65,
     [("সিট", wt("সিট")), ("হিটার", wt("হিটার")), ("·", 29.8), ("ক্রুজ", wt("ক্রুজ")), ("কন্ট্রোল", wt("কন্ট্রোল"))]),
    (36.10, 38.35, [("আজই", wt("আজই")), ("ভিজিট", wt("ভিজিট")), ("করুন", wt("করুন"))], 37.08, [("আমাদের", wt("আমাদের", 3)), ("শোরুম", wt("শোরুম"))]),
    (39.20, 99.0, [("আব্দুল", wt("আব্দুল")), ("হামিদ", wt("হামিদ")), ("রোড", wt("রোড"))], 40.20, [("পাবনা", wt("পাবনা")), ("সদর,", wt("সদর")), ("পাবনা", wt("পাবনা", 1))]),
]
LY, NY = 292, 374

@lru_cache(maxsize=None)
def box_layout(words, size, weight):
    m, pad, adv = hind_mask(" ".join(w for w, _ in words), size, weight)
    sp = font(HIND[weight][0], size).getlength(" "); xs = []; x = 0
    for w, _ in words: xs.append(x); x += hind_mask(w, size, weight)[2] + sp
    return adv, xs

def draw_box(img, words, t, t_in, t_out, cy, light, xoff=0):
    size, weight = (50, 700) if light else (46, 600)
    while True:
        adv, xs = box_layout(tuple(words), size, weight)
        if adv + 48 <= W - 40 or size < 30: break
        size -= 2
    bh = int(size * 1.62); bw = int(adv + 48); cx = W / 2 + xoff
    R = int(cx + bw / 2); L = int(cx - bw / 2)
    pin = seg(t, t_in, 0.22); pout = seg(t, t_out, 0.18)
    if pin <= 0 or pout >= 1: return
    left = int(lerp(R - 8, L, eo3(pin))); left = int(lerp(left, R, ei3(pout)))
    if R - left < 2: return
    lay = Image.new("RGBA", (bw, bh), (BOXF if light else BOXN) + (238 if light else 255,))
    for (w, tt), x in zip(words, xs):
        q = seg(t, tt, 0.13)
        if q <= 0: continue
        m, pd, _ = hind_mask(w, size, weight)
        im = colorize(m, (24, 50, 92), (46, 98, 152)) if light else colorize(m, BOXT)
        yy = bh / 2 + 2 + bh * 0.62 * (1 - eo3(q))
        a = (np.asarray(im.getchannel("A"), np.float32) * eo3(q)).astype(np.uint8); im.putalpha(Image.fromarray(a))
        lay.alpha_composite(im, (int(24 + x - pd), int(yy - im.height / 2)))
    mk = Image.new("L", (bw, bh), 0); ImageDraw.Draw(mk).rounded_rectangle([left - L, 0, bw - 1, bh - 1], 9, fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel("A")), np.asarray(mk))))
    img.alpha_composite(lay, (L, int(cy - bh / 2)))

# ================================================================ camera / grade / fx
@lru_cache(maxsize=8)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
BM = os.path.join(HERE, "bm")
@lru_cache(maxsize=16)
def _bm(si):
    p = f"{BM}/f_{si + 1:04d}.png"
    return np.asarray(Image.open(p), np.float32) if os.path.exists(p) else None
@lru_cache(maxsize=8)
def src_matte(si):
    """BiRefNet matte (3-frame temporal average) where it exists, else the old u2net matte."""
    c = _bm(si)
    if c is None: return Image.open(f"{MAT}/f_{si + 1:04d}.png").convert("L")
    nb = [_bm(j) for j in (si - 1, si, si + 1) if 0 <= j < NSRC and SHOT[j] == SHOT[si] and _bm(j) is not None]   # never across a cut
    return Image.fromarray(np.clip(np.mean(nb, 0), 0, 255).astype(np.uint8))
def cam(si, t):
    k = SHOT[si]; a, b, mode = SHOTS[k]; drift = 1 + min(0.04, 0.005 * max(0, t - a))
    if mode == "T":
        z = ZSHOT[k] * (1 + min(0.02, 0.002 * max(0, t - a))); cw, ch = W / z, H / z
        x0 = clamp(HX[si] - (W / 2) / z, 0, SW - cw); y0 = clamp(HTOP[si] - 470 / z, 0, SH - ch)
        head = ((HX[si] - x0) * z, (HTOP[si] - y0) * z, HW[si] * z)
    else:
        z = drift; cw, ch = W / z, H / z; x0 = (SW - cw) / 2; y0 = (SH - ch) / 2; head = None
    box = (x0, y0, x0 + cw, y0 + ch)
    fr = src_frame(si).resize((W, H), Image.LANCZOS, box=box)
    mt = src_matte(si).resize((W, H), Image.BILINEAR, box=box) if mode == "T" else None
    return fr, mt, head, mode

def grade(img):
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    a = (a - 0.5) * 1.05 + 0.51; g = a.mean(2, keepdims=True); a = g + (a - g) * 1.12
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

def glass(old, new, p, k=0.36):
    """diagonal glass wipe left->right: new on the left of a bright refracting edge."""
    A = np.asarray(old.convert("RGB"), np.float32); B = np.asarray(new.convert("RGB"), np.float32)
    e = lerp(-k * H / 2 - 100, W + k * H / 2 + 100, eio(p)); d = (e + k * (_yy - H / 2)) - _xx
    mn = np.clip(d / 2, 0, 1)[..., None]; out = A * (1 - mn) + B * mn
    band = (d > 0) & (d < 80); sh = (26 * (1 - np.clip(d / 80, 0, 1))).astype(int)
    R = B[_yi, np.clip(_xi + sh, 0, W - 1)] * 1.08 + 22
    out = np.where(band[..., None], R, out)
    hl = (np.exp(-(d / 3.0) ** 2) * 0.9 + np.exp(-((d - 80) / 2.5) ** 2) * 0.35 + np.exp(-(d / 40.0) ** 2) * 0.18)[..., None]
    out = out + (255 - out) * np.clip(hl, 0, 1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")

HUES = [(150, 24, 44), (226, 44, 62), (250, 128, 40), (226, 238, 44), (70, 226, 86), (44, 178, 156)]
def hue_tint(t, t0, pre=True):
    if pre and t0 - 0.035 <= t < t0 + 0.07:
        k = seg(t, t0 - 0.035, 0.105); return ((90, 238, 80) if k < 0.5 else (60, 200, 170)), 0.85 * (1 - 0.4 * k)
    p = seg(t, t0 + 0.17, 0.25)
    if 0 < p < 1:
        f = p * (len(HUES) - 1); i = int(f); c = np.array(HUES[i]) * (1 - (f - i)) + np.array(HUES[min(i + 1, len(HUES) - 1)]) * (f - i)
        return tuple(c), 0.85 * (1 - eo3(seg(t, t0 + 0.36, 0.06)))
    return None, 0
def apply_tint(img, mt, col, s):
    a = np.asarray(img.convert("RGB"), np.float32); lum = (a @ np.array([0.3, 0.59, 0.11], np.float32))[..., None] / 255
    tinted = np.clip(np.array(col, np.float32) * (0.35 + 1.25 * lum), 0, 255)
    m = (np.asarray(mt, np.float32) / 255)[..., None] * s
    return Image.fromarray(np.clip(a * (1 - m) + tinted * m, 0, 255).astype(np.uint8)).convert("RGBA")

def glow_blur(img, mt, white):
    a = np.asarray(img.convert("RGB"), np.float32)
    bl = np.asarray(img.convert("RGB").filter(ImageFilter.GaussianBlur(9)), np.float32)
    bm = (np.asarray(mt.filter(ImageFilter.GaussianBlur(12)), np.float32) / 255)[..., None]
    bl = bl + (255 - bl) * white
    return Image.fromarray(np.clip(a * (1 - bm) + bl * bm, 0, 255).astype(np.uint8)).convert("RGBA")

LEAKS = [15.40, 27.24]
def leak(img, t):
    for c in LEAKS:
        if c - 0.34 <= t < c + 0.42:
            a = np.asarray(img.convert("RGB"), np.float32)
            if t < c:
                p = seg(t, c - 0.34, 0.34); r = 180 + 900 * eo3(p)
                g = np.exp(-(((_xx + 60) ** 2) / (r * r) + ((_yy - 520) ** 2) / ((r * 1.6) ** 2)))[..., None] * min(1, p * 1.6)
                warm = np.array([255, 140, 50], np.float32)
                a = 255 - (255 - a) * (1 - warm / 255 * g * 0.95); wh = ei3(p) ** 1.3
            else:
                q = seg(t, c, 0.42); wh = (1 - eo3(seg(t, c, 0.22))) * 0.95
                g = (np.clip((_xx - W * 0.45) / (W * 0.55), 0, 1) ** 1.5 * (1 - _yy / H * 0.5))[..., None] * (1 - eo3(q)) * 0.7
                a = 255 - (255 - a) * (1 - np.array([255, 150, 60], np.float32) / 255 * g)
            a = a + (255 - a) * wh
            return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    return img

GLASS_CUTS = [23.80]          # b-roll -> talk: glass wipe from the held last b-roll frame
FLASH = 35.64                 # jump cut covered by the person's glowing blur
def held(t):
    si = min(int(t * SRC_FPS), NSRC - 1); return grade(cam(si, t)[0])

def render(fi):
    t = fi / FPS; si = min(int(t * SRC_FPS), NSRC - 1)
    fr, mt, head, mode = cam(si, t); real = grade(fr)
    if mt is not None and head is not None:
        ma = np.asarray(mt); hx_, ht_, hw_ = head
        face = ma[int(clamp(ht_ + hw_ * 0.5, 0, H - 1)), int(clamp(hx_, 0, W - 1))]
        if face < 128 or ma.mean() > 0.35 * 255:
            bm = Image.new("L", (W, H), 0); d_ = ImageDraw.Draw(bm)
            d_.ellipse([hx_ - hw_ * 0.7, ht_ - hw_ * 0.15, hx_ + hw_ * 0.7, ht_ + hw_ * 1.25], fill=255)
            d_.rounded_rectangle([hx_ - hw_ * 1.75, ht_ + hw_ * 1.05, hx_ + hw_ * 1.75, H], hw_ * 0.6, fill=255)
            mt = bm.filter(ImageFilter.GaussianBlur(14))
        mt = mt.point(lambda v: int(clamp((v - 25) * 1.25, 0, 255))).filter(ImageFilter.GaussianBlur(0.8))
    img = real
    w_ = world_of(t)
    if w_ is not None and mode == "T":
        new = world_layer(w_, t); person = real.copy(); person.putalpha(mt); new.alpha_composite(person)
        pin = seg(t, w_["t0"], 0.14)
        if pin < 1:
            old = held(w_["held"]) if "held" in w_ else real
            img = glass(old, new, pin)
        elif w_["wipe_out"] and t >= w_["wipe_out"]:
            img = glass(new, real, seg(t, w_["wipe_out"], 0.14))
        else:
            img = new
        col, s = hue_tint(t, w_["t0"], pre="held" not in w_)
        if col is not None and s > 0: img = apply_tint(img, mt, col, s)
    elif mode == "T":
        nxt = next((x for x in WORLDS if x["t0"] - 0.04 <= t < x["t0"]), None)       # green flash just before the wipe
        if nxt is not None:
            col, s = hue_tint(t, nxt["t0"]); img = apply_tint(img, mt, col, s) if col is not None else img
    for c in GLASS_CUTS:
        if c <= t < c + 0.15: img = glass(held(c - 0.04), img, seg(t, c, 0.14))
    if mode == "T" and FLASH - 0.04 <= t < FLASH + 0.04:
        img = glow_blur(img, mt, 0.7 if t < FLASH else 0.0)
    for (ti, to, lw, ni, nw) in BOXES:
        if ti <= t < to + 0.2:
            draw_box(img, lw, t, ti, to, LY, True)
            if ni is not None: draw_box(img, nw, t, ni, to, NY, False, xoff=34)
    img = leak(img, t)
    if t > DUR - 0.62:
        k = 1 - seg(t, DUR - 0.62, 0.6); a = np.asarray(img.convert("RGB"), np.float32) * k
        img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    return img.convert("RGB").tobytes()

# ================================================================ sound cues (grammar learned from reference #8)
cue("music", 0.0, dur=round(DUR, 3))
for w_ in WORLDS:
    cue("boom", w_["t0"] - 0.12)                                       # world in (glass wipe)
    cue("swell", w_["elem"][1] - 0.41)                                 # map / element slides in
    if w_["slide"]: cue("boom", w_["slide"] + 0.05)                    # graphics slide out + wipe back
for c in GLASS_CUTS: cue("boom", c - 0.12, -6)
for (ti, *_r) in BOXES: cue("tick", ti)                                # caption box pops in (pale box only)
cue("outro", DUR - 0.75)

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
