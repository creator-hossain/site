# -*- coding: utf-8 -*-
"""Reference-matched Bangla caption animator.

Motion copied from the reference ad:
  * each new word enters at ~55% scale, rotated ~-14deg, settling to 100%/0deg in ~110ms
  * when a phrase finishes it shrinks and slides up into the small history block
  * emphasised words stay gold once spoken

libass sizes a font by (ascent-descent), not by the em square, so every PIL
measurement is scaled by RATIO to match what libass will actually draw.
"""
import json, sys
from PIL import ImageFont
from fontTools.ttLib import TTFont

W, H   = 720, 1280
CX     = W // 2
FONT   = "/usr/share/fonts/truetype/bnx/BalooDa2-BN-ExtraBold.ttf"
FAMILY = "BalooBN"

_t    = TTFont(FONT)
RATIO = _t["head"].unitsPerEm / float(_t["hhea"].ascent - _t["hhea"].descent)

BIG, SMALL = 84, 44                     # ASS Fontsize (rendered em = size * RATIO)
LH_BIG     = int(BIG   * RATIO * 1.34)
LH_SMALL   = int(SMALL * RATIO * 1.34)
MAXW       = 640                        # wrap width, rendered px
Y_TOP      = 104                        # centre of the first history line
GAP        = 10
HIST_CAP   = 13
MAX_HIST_L = 3

WHITE, GOLD = r"&H00FFFFFF", r"&H0000C8FF"
POP_MS    = 185       # word entry: scale + un-shear, ease-out
POP_SCALE = 55        # entry scale %
POP_SHEAR = 0.28      # entry x-shear (inline \\frz displaces the word, \\fax does not)
POP_ACCEL = 0.55      # <1 = decelerating, reproduces the reference's long settle
MERGE_MS = 180

_f = {}
def font(px):
    if px not in _f: _f[px] = ImageFont.truetype(FONT, px)
    return _f[px]
def wd(txt, px): return font(px).getlength(txt) * RATIO

def ts(s):
    cs = int(round(s * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); sec, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{sec:02d}.{cs:02d}"

EV = []
def ev(style, a, b, text, layer=0):
    if b - a > 0.012: EV.append((a, f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}"))

def col(c): return "" if c == "w" else f"\\c{GOLD}"
def run(ws): return " ".join((f"{{{col(c)}}}{t}{{\\r}}" if c == "g" else t) for t, c in ws)

def wrap(words, px):
    lines, cur, sp = [], [], wd(" ", px)
    for w in words:
        trial = cur + [w]
        if cur and sum(wd(t, px) for t, _ in trial) + sp * (len(trial) - 1) > MAXW:
            lines.append(cur); cur = [w]
        else:
            cur = trial
    if cur: lines.append(cur)
    return lines

def line_w(ln, px): return sum(wd(t, px) for t, _ in ln) + wd(" ", px) * (len(ln) - 1)

def layout(hist):
    """-> (history line list, y per history line, y of first big line)"""
    hl = wrap(hist, SMALL)[-MAX_HIST_L:] if hist else []
    hy = [Y_TOP + i * LH_SMALL for i in range(len(hl))]
    y0 = Y_TOP + len(hl) * LH_SMALL + GAP + int(LH_BIG * 0.5)
    return hl, hy, y0

def draw(a, b, hist, shown, anim_idx):
    """One event per line, centred. Only the new word is animated - because the
    line is centred, libass re-centres the rest every frame, so the earlier words
    glide into place on their own instead of jumping."""
    hl, hy, y0 = layout(hist)
    for y, ln in zip(hy, hl):
        ev("Small", a, b, f"{{\\pos({CX},{y})\\an5}}{run(ln)}")
    idx = 0
    for li, ln in enumerate(wrap(shown, BIG)):
        y = y0 + li * LH_BIG
        if anim_idx is not None and idx <= anim_idx < idx + len(ln):
            k = anim_idx - idx
            parts = []
            for j, (t, c) in enumerate(ln):
                if j: parts.append(" ")
                if j == k:
                    parts.append(
                        f"{{{col(c)}\\fscx{POP_SCALE}\\fscy{POP_SCALE}\\fax{POP_SHEAR}"
                        f"\\t(0,{POP_MS},{POP_ACCEL},\\fscx100\\fscy100\\fax0)}}{t}{{\\r}}")
                else:
                    parts.append(f"{{{col(c)}}}{t}{{\\r}}" if c == "g" else t)
            body = "".join(parts)
        else:
            body = run(ln)
        ev("Big", a, b, f"{{\\pos({CX},{y})\\an5}}{body}", 1)
        idx += len(ln)

def merge(a, hist_before, words, dur=MERGE_MS):
    """the finished phrase shrinks + slides into its place in the new history block"""
    big = wrap(words, BIG)
    _, _, y0 = layout(hist_before)
    nh = (hist_before + words)[-HIST_CAP:]
    hl, hy, _ = layout(nh)
    tgt = hy[-len(big):] if len(hy) >= len(big) else hy + [hy[-1]] * (len(big) - len(hy))
    sc = int(round(SMALL / float(BIG) * 100))
    for li, ln in enumerate(big):
        ev("Big", a, a + dur / 1000.0,
           f"{{\\an5\\move({CX},{y0 + li * LH_BIG},{CX},{tgt[li]},0,{dur})"
           f"\\t(0,{dur},\\fscx{sc}\\fscy{sc})}}{run(ln)}", 1)

HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Big,{FAMILY},{BIG},{WHITE},{WHITE},&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,4,3,5,0,0,0,1
Style: Small,{FAMILY},{SMALL},{WHITE},{WHITE},&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,2.6,2,5,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

def build(spec, tail):
    flat = [(si, ph) for si, seg in enumerate(spec) for ph in seg["phrases"]]
    hist = []
    for n, (si, ph) in enumerate(flat):
        nxt_seg  = flat[n + 1][0] if n + 1 < len(flat) else None
        nxt_start = flat[n + 1][1]["words"][0][2] if n + 1 < len(flat) else tail
        ends_seg = nxt_seg != si                      # last phrase of this segment
        words = [(w[0], w[1]) for w in ph["words"]]
        # when the segment ends here the phrase simply holds until the next one starts
        hold  = nxt_start if ends_seg else ph["end"]
        steps = [w[2] for w in ph["words"]] + [hold]
        for i in range(len(words)):
            draw(steps[i], steps[i + 1], hist, words[:i + 1], i)
        if ends_seg:
            hist = []                                  # history clears between segments
            continue
        gap = nxt_start - ph["end"]
        if gap >= 0.05:
            dur = int(min(MERGE_MS, gap * 1000) )      # never overrun the next phrase
            merge(ph["end"], hist, words, dur)
            hist = (hist + words)[-HIST_CAP:]
            draw(ph["end"] + dur / 1000.0, nxt_start, hist, [], None)
        else:
            hist = (hist + words)[-HIST_CAP:]
    EV.sort(key=lambda p: p[0])
    return HEAD + "\n".join(l for _, l in EV) + "\n"

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    tail = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
    open(sys.argv[2], "w", encoding="utf-8").write(build(spec, tail))
    print(f"{len(EV)} events | RATIO={RATIO:.4f} BIG={BIG} SMALL={SMALL} "
          f"LH={LH_BIG}/{LH_SMALL}")
