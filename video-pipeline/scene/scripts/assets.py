# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
W, H = 720, 1280
import os
FONTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fonts")   # fonts shipped in the repo (works on Windows too)
BN = os.path.join(FONTDIR, "bnx", "BalooDa2-BN-ExtraBold.ttf")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
f = lambda s: ImageFont.truetype(BN, s)

def grid_bg(path):
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):                                   # vertical gradient
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(32 + 10*t), int(118 - 34*t), int(236 - 56*t)))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for x in range(-60, W + 120, 96): gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 28), width=2)
    for y in range(-60, H + 120, 96): gd.line([(0, y), (W, y)], fill=(255, 255, 255, 28), width=2)
    bg = Image.alpha_composite(bg.convert("RGBA"), g)
    v = Image.new("L", (W, H), 0); ImageDraw.Draw(v).ellipse(
        [-W//2, -H//5, W + W//2, H + H//5], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", (W, H), (4, 32, 92, 255))
    bg = Image.composite(bg, dark, v)
    bg.convert("RGB").save(path)

def rounded(size, r, fill):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size[0]-1, size[1]-1], r, fill=fill)
    return im

def shadowed(card, blur=26, off=(0, 14), op=120):
    pad = blur * 3
    out = Image.new("RGBA", (card.width + pad*2, card.height + pad*2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste(Image.new("RGBA", card.size, (3, 22, 70, op)), (pad + off[0], pad + off[1]), card)
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(card, (pad, pad))
    return out

def spec_card(path):
    cw, ch = 600, 360
    c = rounded((cw, ch), 40, (255, 255, 255, 250)); d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, cw-1, 92], 40, fill=(29, 78, 216, 255))
    d.rectangle([0, 56, cw-1, 92], fill=(29, 78, 216, 255))
    t = "টয়োটা করোলা ক্রস"
    d.text(((cw - d.textlength(t, font=f(46)))/2, 16), t, font=f(46), fill=(255, 255, 255))
    rows = [("মডেল", "ZVG13 • 2023"), ("মাইলেজ", "33,000 কিলো"),
            ("অকশন গ্রেড", "৪"), ("কালার", "পার্ল টু-টোন")]
    y = 118
    for k, v in rows:
        d.text((44, y), k, font=f(34), fill=(100, 116, 139))
        d.text((cw - 44 - d.textlength(v, font=f(36)), y - 2), v, font=f(36), fill=(15, 23, 42))
        y += 60
        if y < ch - 50: d.line([(44, y - 12), (cw - 44, y - 12)], fill=(226, 232, 240), width=2)
    shadowed(c).save(path)

def cta_card(path):
    cw, ch = 620, 300
    c = rounded((cw, ch), 40, (255, 255, 255, 250)); d = ImageDraw.Draw(c)
    for i, (txt, sz, col, dy) in enumerate([
            ("আজই ভিজিট করুন", 48, (15, 23, 42), 36),
            ("আব্দুল হামিদ রোড", 36, (71, 85, 105), 100),
            ("পাবনা সদর, পাবনা", 36, (71, 85, 105), 148)]):
        d.text(((cw - d.textlength(txt, font=f(sz)))/2, dy), txt, font=f(sz), fill=col)
    btn = rounded((420, 76), 38, (79, 70, 229, 255)); bd = ImageDraw.Draw(btn)
    bt = "শোরুমে আসুন"
    bd.text(((420 - bd.textlength(bt, font=f(38)))/2, 12), bt, font=f(38), fill=(255, 255, 255))
    c.alpha_composite(btn, ((cw - 420)//2, 206))
    shadowed(c).save(path)

def ring(path, d_=520, w=14):
    im = Image.new("RGBA", (d_ + w*2, d_ + w*2), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([w//2, w//2, d_ + w + w//2, d_ + w + w//2],
                               outline=(255, 255, 255, 235), width=w)
    im.save(path)

def circle_mask(path, d_=520, cx=W//2, cy=470):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([cx - d_//2, cy - d_//2, cx + d_//2, cy + d_//2], fill=255)
    m.filter(ImageFilter.GaussianBlur(1.5)).save(path)

grid_bg(f"{OUT}/bg.png"); spec_card(f"{OUT}/card_spec.png")
cta_card(f"{OUT}/card_cta.png"); ring(f"{OUT}/ring.png"); circle_mask(f"{OUT}/cmask.png")
print("assets:", ", ".join(sorted(os.listdir(OUT))))
