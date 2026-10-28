# -*- coding: utf-8 -*-
"""Corolla Cross edit in the style of reference #6 (vlog look, typewriter captions, ASMR ticks).

Measured from the reference (368x464, ~60 fps):
  * 4:5 frame, vivid grade, opening = over-exposed wash easing to normal + diagonal sticker
  * captions sit beside / above the speaker's head, typed one cluster at a time (~68 ms),
    yellow / white / green fill, thin dark-green outline + soft shadow; erased in random order
  * one block is rotated ~-12 deg with a big '!!' and a glowing icon
  * logo bug top-left swaps between two badges
  * cuts: punch-in (instant x1.22) and a vertical roll/smear glitch
Sound rules (learned): tick per typed cluster (2.4 kHz, 17 ms), low tick on erase,
rising swish on the opening, whoosh on the glitch, click when an icon/'!!' lands.
usage: compose_v6.py SRC TRACK WORDS OUT [--preview t,..]
"""
import sys, json, subprocess, math, random
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, TRACK, WORDS, OUT = sys.argv[1:5]
PREVIEW = sys.argv[6].split(",") if len(sys.argv) > 6 and sys.argv[5] == "--preview" else None
FPS, SRC_FPS = 50, 25
W, H = 720, 900
SW, SH = 720, 1280
BALOO = "/usr/share/fonts/truetype/bnx/BalooDa2-BN-ExtraBold.ttf"
WHITE = (255, 255, 255, 255)
YELLOW = (232, 232, 60); CWHITE = (253, 252, 246); GREEN = (64, 172, 60)
OUTLINE = (41, 56, 27); BANG = (255, 236, 150)

TR = json.load(open(TRACK)); HX, HTOP, HW, SHOT, SHOTS = TR["hx"], TR["htop"], TR["hw"], TR["shot"], TR["shots"]
NSRC = len(HX); DUR = NSRC / SRC_FPS
WT = {}
for w in json.load(open(WORDS, encoding="utf-8")): WT.setdefault(w["w"], []).append(w["t"])
def wt(w, n=0): return WT[w][n]

CUES = []
def cue(sound, t, gain=0.0): CUES.append(dict(sound=sound, t=round(t, 3), gain=gain))

def clamp(v, a, b): return max(a, min(b, v))
def lerp(a, b, p): return a + (b - a) * p
def eo3(p): p = clamp(p, 0, 1); return 1 - (1 - p) ** 3
def eoback(p, s=1.8):
    p = clamp(p, 0, 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def seg(t, a, d): return clamp((t - a) / d, 0, 1)

@lru_cache(maxsize=None)
def font(s): return ImageFont.truetype(BALOO, s)

def clusters(s):
    out = []
    for ch in s:
        cp = ord(ch)
        att = (0x0981 <= cp <= 0x0983) or cp == 0x09BC or (0x09BE <= cp <= 0x09CD) or cp == 0x09D7 or cp in (0x200C, 0x200D)
        if out and ch != " " and out[-1] != " " and (att or out[-1].endswith("্")): out[-1] += ch
        else: out.append(ch)
    return out

@lru_cache(maxsize=4096)
def text_img(txt, size, col):
    """fill + thin dark-green outline + soft dark shadow (reference caption look)."""
    f = font(size); asc, desc = f.getmetrics(); pad = 16; vpad = pad + int(size * 0.2); adv = f.getlength(txt)
    w, h = int(adv + 2 * pad), int(asc + desc + 2 * vpad)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("L", (w, h), 0); ImageDraw.Draw(sh).text((pad + 2, vpad + 4), txt, font=f, fill=200, stroke_width=4, stroke_fill=200)
    s_ = Image.new("RGBA", (w, h), (10, 20, 8, 0)); s_.putalpha(sh.filter(ImageFilter.GaussianBlur(5))); out.alpha_composite(s_)
    L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(L).text((pad, vpad), txt, font=f, fill=col + (255,), stroke_width=max(2, size // 28), stroke_fill=OUTLINE + (255,))
    out.alpha_composite(L); out.info.update(adv=adv, px=pad); return out

def place(dst, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0, anchor="c"):
    if alpha <= 0.004: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.996:
        a = (np.asarray(im.getchannel("A"), np.float32) * alpha).astype(np.uint8); im = im.copy(); im.putalpha(Image.fromarray(a))
    x = int(round(cx - im.width / 2)) if anchor == "c" else int(round(cx)); y = int(round(cy - im.height / 2))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 > x0 and y1 > y0: dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def rr(w, h, r, fill, ss=3):
    im = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=fill)
    return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)

# ================================================================ camera
PUNCH = []                                    # (t_cut, factor) ; zoom holds until the next shot change
@lru_cache(maxsize=6)
def src_frame(si): return Image.open(f"{SRC}/f_{si + 1:04d}.png").convert("RGB")
def zoom_at(t):
    z = 1.0
    for tc, f in PUNCH:
        if t >= tc: z = f
    return z
def cam(si, t):
    k = SHOT[si]; a, b, mode = SHOTS[k]; drift = 1 + min(0.04, 0.004 * max(0, t - a))
    pz = zoom_at(t) if any(tc >= a and tc <= t for tc, _ in PUNCH) else 1.0
    if mode == "T":
        z = max(1.0, 84 / HW[si] * drift * pz); cw, ch = W / z, H / z     # never wider than the source
        x0 = clamp(HX[si] - (W / 2) / z, 0, SW - cw); y0 = clamp(HTOP[si] - 150 / z, 0, SH - ch)
        head = ((HX[si] - x0) * z, (HTOP[si] - y0) * z, HW[si] * z)
    else:
        z = 1.0 * drift * pz; cw, ch = W / z, H / z; x0 = (SW - cw) / 2; y0 = clamp((SH - ch) / 2 + 40, 0, SH - ch)
        head = None
    fr = src_frame(si).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    return fr.filter(ImageFilter.UnsharpMask(2, 50, 2)), head

def grade(img, t):
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    a = np.clip((a - 0.5) * 1.08 + 0.5, 0, 1); g = a.mean(2, keepdims=True); a = g + (a - g) * 1.22
    if t < 0.9:                                  # opening: over-exposed wash easing to normal (reference 0-0.8 s)
        k = 1 - eo3(seg(t, 0.1, 0.8)); a = a + (1 - a) * 0.42 * k; g = a.mean(2, keepdims=True); a = g + (a - g) * (1 - 0.45 * k)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

# ================================================================ captions
class Cap:
    """lines = [(text, colour, size)] typed in order from t0 (68 ms per cluster); erased at t1.
    anchor 'side' = right of the head, 'top' = above the head; rot = block rotation."""
    STEP = 0.068
    def __init__(s, lines, t0, t1, anchor="side", rot=0.0, bang=False, icon=None, dx=0, dy=0, abs_pos=None):
        lines = [(a_, c_, int(z_ * 1.15)) for a_, c_, z_ in lines]      # reference captions are ~10% of frame height
        s.lines, s.t0, s.t1, s.anchor, s.rot, s.bang, s.icon, s.dx, s.dy, s.abs = lines, t0, t1, anchor, rot, bang, icon, dx, dy, abs_pos
        s.cl = [clusters(x[0]) for x in lines]; s.times = []; tt = t0
        for li, cl in enumerate(s.cl):
            row = []
            for c in cl:
                if c == " ": row.append(tt); continue
                row.append(tt); cue("tick", tt); tt += s.STEP
            s.times.append(row); tt += 0.05
        s.t_end = tt
        if bang: s.t_bang = tt + 0.04; cue("click", s.t_bang)
        if icon is not None: s.t_icon = tt + 0.12; cue("click", s.t_icon, -3)
        flat = [(li, ci) for li, cl in enumerate(s.cl) for ci, c in enumerate(cl) if c != " "]
        rnd = random.Random(int(t0 * 1000)); rnd.shuffle(flat)
        s.erase = {k: t1 + i * 0.045 for i, k in enumerate(flat)}
        if t1 < DUR: cue("erase", t1)
        s.t_gone = t1 + len(flat) * 0.045 + 0.05
    def live(s, t): return s.t0 - 0.02 <= t < s.t_gone
    def render_block(s, t):
        rows = []
        for li, ((txt, col, size), cl) in enumerate(zip(s.lines, s.cl)):
            full = text_img(txt, size, col)
            # draw only visible clusters at their final positions (no reflow while typing)
            img = Image.new("RGBA", full.size, (0, 0, 0, 0)); f = font(size); pre = ""
            for ci, c in enumerate(cl):
                x0 = f.getlength(pre); pre += c; x1 = f.getlength(pre)
                on = s.times[li][ci] <= t and not (c != " " and s.erase.get((li, ci), 9e9) <= t)
                if c != " " and on:
                    a, b = int(full.info["px"] + x0) - (4 if ci else 16), int(full.info["px"] + x1) + (4 if ci < len(cl) - 1 else 16)
                    img.alpha_composite(full.crop((max(0, a), 0, min(full.width, b), full.height)), (max(0, a), 0))
            rows.append((img, full.info["adv"], size))
        bw = int(max(r[1] for r in rows) + 60); bh = int(sum(r[2] * 1.02 for r in rows) + (190 if s.icon is not None else 80))
        B = Image.new("RGBA", (bw + 160, bh + 120), (0, 0, 0, 0)); y = 40
        for img, adv, size in rows:
            B.alpha_composite(img, (int(20 + (bw - 40 - adv) / 2 - 16), int(y - size * 0.2))); y += size * 1.02
        if s.bang and t >= s.t_bang and not t >= s.t1:
            p = seg(t, s.t_bang, 0.2); bi = text_img("!!", int(rows[0][2] * 1.6), BANG[:3])
            place(B, bi, bw + 30, 40 + (bh - 80) * 0.45, alpha=eo3(p * 3), scale=lerp(1.8, 1, eo3(p)))
        if s.icon is not None and t >= s.t_icon and not t >= s.t1 + 0.2:
            p = seg(t, s.t_icon, 0.3); place(B, s.icon, bw * 0.62, y + 78, alpha=eo3(p * 3), scale=lerp(0.3, 1, eoback(p, 2)))
        return B
    def content_box(s):
        """bbox of the fully-typed block (before any erase), cached; used for placement."""
        if not hasattr(s, "_box"):
            B = s.render_block(min(s.t_end + 0.5, s.t1 - 0.001)); s._box = (B.size, B.getchannel("A").getbbox())
        return s._box
    def draw(s, dst, t, head):
        B = s.render_block(t); (bw, bh), (x0, y0, x1, y1) = s.content_box()
        cw, chh = x1 - x0, y1 - y0; ox, oy = (x0 + x1) / 2 - bw / 2, (y0 + y1) / 2 - bh / 2   # content centre offset
        sc = 1.0
        if s.abs: tx, ty = s.abs
        elif head is None: tx, ty = 470, 230
        else:
            hx, ht, hw = head; inner = hw * 0.62          # clear of the ear; may overlap the shoulder
            right, left = W - 20 - (hx + inner), (hx - inner) - 20
            room = max(right, left); sc_side = min(1.0, room / cw)
            sc_top = min(1.0, (W - 40) / cw)
            above_room = ht - 26 - 130                                   # space between logo row and the head top
            fits_above = above_room >= chh * sc_top
            side_ok = sc_side >= 0.72 or (not fits_above and sc_side >= 0.5)
            if (s.anchor == "side" and side_ok) or (s.anchor == "top" and not fits_above and sc_side >= 0.5):
                # reference: beside the face, on the side with more room, around eye level - never over the face
                sc = sc_side; tx = (hx + inner + cw * sc / 2) if right >= left else (hx - inner - cw * sc / 2)
                ty = ht + hw * 0.6
            else:
                sc = sc_top; tx = hx; ty = ht - chh * sc / 2 - 14
        tx = clamp(tx + s.dx, cw * sc / 2 + 20, W - cw * sc / 2 - 20)
        ty = clamp(ty + s.dy, chh * sc / 2 + (140 if tx - cw * sc / 2 < 190 else 20), H - chh * sc / 2 - 20)   # keep clear of the logo bug
        place(dst, B, tx - ox * sc, ty - oy * sc, angle=s.rot, scale=sc)

def car_icon(size=120, col=(255, 160, 50)):
    S = 3; im = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); u = size * S / 100
    d.rounded_rectangle([8 * u, 44 * u, 92 * u, 72 * u], 10 * u, fill=col + (255,))
    d.polygon([(22 * u, 46 * u), (34 * u, 26 * u), (66 * u, 26 * u), (78 * u, 46 * u)], fill=col + (255,))
    d.polygon([(36 * u, 31 * u), (49 * u, 31 * u), (49 * u, 45 * u), (29 * u, 45 * u)], fill=(255, 236, 200, 255))
    d.polygon([(52 * u, 31 * u), (64 * u, 31 * u), (71 * u, 45 * u), (52 * u, 45 * u)], fill=(255, 236, 200, 255))
    for cx in (28, 72): d.ellipse([(cx - 10) * u, 62 * u, (cx + 10) * u, 82 * u], fill=(40, 30, 20, 255))
    im = im.resize((size, size), Image.LANCZOS)
    g = Image.new("RGBA", (size + 60, size + 60), (255, 170, 60, 0)); g.putalpha(Image.new("L", g.size, 0))
    ga = Image.new("L", g.size, 0); ga.paste(im.getchannel("A"), (30, 30)); g.putalpha(ga.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.9)))
    g.alpha_composite(im, (30, 30)); return g
def pin_icon(size=110):
    S = 3; im = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); u = size * S / 100
    d.ellipse([22 * u, 6 * u, 78 * u, 62 * u], fill=(230, 50, 50, 255)); d.polygon([(26 * u, 46 * u), (74 * u, 46 * u), (50 * u, 96 * u)], fill=(230, 50, 50, 255))
    d.ellipse([38 * u, 22 * u, 62 * u, 46 * u], fill=WHITE); im = im.resize((size, size), Image.LANCZOS)
    g = Image.new("RGBA", (size + 60, size + 60), (255, 90, 90, 0)); ga = Image.new("L", g.size, 0); ga.paste(im.getchannel("A"), (30, 30))
    g.putalpha(ga.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.8))); g.alpha_composite(im, (30, 30)); return g

# ================================================================ logo bug (two badges, flip-swap)
def _badges():
    a = Image.new("RGBA", (130, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(a)
    d.rounded_rectangle([18, 10, 112, 92], 16, fill=(250, 196, 40, 255), outline=(60, 40, 0, 255), width=3)
    d.polygon([(30, 34), (65, 14), (100, 34)], fill=(60, 40, 0, 255))
    place(a, text_img("ZVG13", 26, (60, 40, 0)), 65, 58)
    b = rr(160, 48, 24, (220, 30, 40, 255)); place(b, text_img("করোলা ক্রস", 26, (255, 255, 255)), 80, 25)
    return a, b
BADGE_A, BADGE_B = _badges()
SWAPS = [4.9, 10.4, 15.1, 20.2, 26.6, 31.2, 36.4]
def logo_bug(dst, t):
    if t < 0.95: return
    k = sum(1 for s in SWAPS if t >= s)
    im = BADGE_A if k % 2 == 0 else BADGE_B
    sx = 1.0
    for s in SWAPS:
        if s - 0.14 <= t < s: sx = 1 - seg(t, s - 0.14, 0.14)
        if s <= t < s + 0.14: sx = seg(t, s, 0.14)
    a = eo3(seg(t, 0.95, 0.25))
    imr = im.resize((max(1, int(im.width * max(sx, 0.02))), im.height), Image.BICUBIC)
    place(dst, imr, 22 + im.width / 2, 20 + im.height / 2, alpha=a)

# ================================================================ glitch roll transition
GLITCH = []                                    # cut times
def vblur(img, r):
    """vertical-only motion smear (two box passes along y)."""
    r = int(r)
    if r < 1: return img
    a = np.asarray(img, np.float32)
    for _ in range(2):
        c = np.cumsum(np.pad(a, ((r + 1, r), (0, 0), (0, 0)), mode="edge"), axis=0)
        a = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def glitch(t, frame_at):
    """vertical roll with smear: old frame rolls up, new frame rolls in from below (reference 12.27 s)."""
    for c in GLITCH:
        if c - 0.12 <= t < c + 0.20:
            p = seg(t, c - 0.12, 0.32); off = int(H * eo3(p))
            old = frame_at(c - 0.13); new = frame_at(t if t >= c else c)
            canvas = Image.new("RGBA", (W, H)); canvas.paste(old, (0, -off)); canvas.paste(new, (0, H - off))
            r = 34 * math.sin(math.pi * p)
            canvas = vblur(canvas, r)
            if 0.25 < p < 0.75:                   # band displacement in the middle of the roll
                arr = np.asarray(canvas).copy(); rng = np.random.RandomState(int(t * 100))
                for _ in range(5):
                    y0 = rng.randint(0, H - 40); hh = rng.randint(10, 60); arr[y0:y0 + hh] = np.roll(arr[y0:y0 + hh], rng.randint(-60, 60), axis=1)
                canvas = Image.fromarray(arr)
            return canvas
    return None

# ================================================================ edit
CAPS = []
def add(c): CAPS.append(c); return c
for t_, f_ in ((7.55, 1.22), (20.60, 1.18), (25.95, 1.22), (34.10, 1.22)): PUNCH.append((t_, f_))
GLITCH += [15.40, 23.80, 27.24, 31.64, 35.64]
cue("swish", 0.0); cue("swish", 0.42, -6)
for g in GLITCH: cue("whoosh", g - 0.12)

add(Cap([("চিটাগাং স্টকের", YELLOW, 50), ("করোলা ক্রস", CWHITE, 78)], wt("চিটাগাং"), 4.55))
add(Cap([("রেডি স্টকে!", GREEN, 82)], wt("রেডি"), 9.0))
add(Cap([("পার্ল", YELLOW, 60), ("ব্ল্যাক কালার", CWHITE, 70)], wt("পার্ল"), 12.85))
add(Cap([("দুইটাই অ্যাভেলেবল!", CWHITE, 56)], wt("দুইটাই"), 15.05, anchor="top"))
add(Cap([("ZVG13", CWHITE, 70), ("2023 মডেল", CWHITE, 70), ("টু টোন", CWHITE, 58)], wt("ZVG13"), 20.35,
        rot=-12, bang=True, icon=car_icon(), abs_pos=(450, 300)))
add(Cap([("হার্ড টপ", YELLOW, 60), ("মডেলিস্টা বডি কিট", CWHITE, 62)], wt("হার্ড"), 23.62, abs_pos=(400, 230)))
add(Cap([("অটো পার্কিং", GREEN, 74)], wt("অটো"), 25.95))
add(Cap([("360 ক্যামেরা!", CWHITE, 62)], wt("360"), 27.10, anchor="top"))
add(Cap([("ফগ লাইট", YELLOW, 56), ("সিট হিটার", CWHITE, 66)], wt("ফগ"), 29.75, abs_pos=(420, 230)))
add(Cap([("সবকিছুই", CWHITE, 70), ("পাচ্ছেন", CWHITE, 70)], wt("সবকিছুই"), 31.50, rot=-12, bang=True, icon=car_icon(), abs_pos=(450, 300)))
add(Cap([("মাত্র", YELLOW, 56), ("33,000 কিলো", CWHITE, 70)], wt("মাত্র"), 33.95))
add(Cap([("গ্রেড ফোর!", GREEN, 82)], wt("গ্রেড"), 35.50))
add(Cap([("আজই", CWHITE, 72), ("ভিজিট", CWHITE, 72), ("করুন", CWHITE, 72)], wt("আজই"), 38.50, rot=-12, bang=True, icon=pin_icon()))
add(Cap([("আব্দুল হামিদ রোড", YELLOW, 52), ("পাবনা সদর, পাবনা", CWHITE, 60)], wt("আব্দুল"), DUR + 1))

STICKER = None
def sticker(dst, t):
    """opening onomatopoeia running diagonally off the top-right corner, fading out by 0.55 s."""
    global STICKER
    if t >= 0.6: return
    if STICKER is None: STICKER = text_img("ওয়াওওওও!!", 90, CWHITE)
    place(dst, STICKER, 560 + 30 * t, 120 - 20 * t, alpha=1 - eo3(seg(t, 0.35, 0.22)), angle=34)

def base_frame(t):
    si = min(int(t * SRC_FPS), NSRC - 1); fr, head = cam(si, t); return grade(fr, t), head

def render(fi):
    t = fi / FPS
    g = glitch(t, lambda tt: base_frame(tt)[0])
    if g is not None:
        img = g; head = None
    else:
        img, head = base_frame(t)
        for c in CAPS:
            if c.live(t): c.draw(img, t, head)
    sticker(img, t); logo_bug(img, t)
    return img.convert("RGB").tobytes()

if __name__ == "__main__":
    CUES.sort(key=lambda c: c["t"])
    json.dump(CUES, open(OUT.rsplit(".", 1)[0] + "_cues.json", "w"), ensure_ascii=False, indent=0)
    print(len(CUES), "sound cues")
    if PREVIEW:
        for ts in PREVIEW: Image.frombytes("RGB", (W, H), render(int(round(float(ts) * FPS)))).save(f"{OUT}_{ts}.png")
        print("previews:", ", ".join(PREVIEW)); sys.exit(0)
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=6)):
            ff.stdin.write(buf)
            if i % 250 == 0: print(f"  frame {i}/{n}", flush=True)
    ff.stdin.close(); ff.wait(); print("done ->", OUT, "exit", ff.returncode)
