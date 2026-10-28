# -*- coding: utf-8 -*-
"""Reference-matched Bangla caption renderer. Usage: gen2.py spec.json out.ass"""
import json, sys

W, H = 720, 1280                 # new video
REF_W = 1024                     # reference video width
K = W / REF_W                    # proportional scale (0.703)

CX = W // 2
BIG, SMALL = round(70 * K), round(36 * K)          # 49 / 25
OUT_B, OUT_S = round(5 * K, 1), round(3 * K, 1)    # outline
SHA_B, SHA_S = round(3 * K, 1), round(2 * K, 1)    # shadow
WHITE, GOLD = r"&H00FFFFFF", r"&H0000C8FF"
COL = {"w": WHITE, "g": GOLD}

HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Big,Baloo Da 2 ExtraBold,{BIG},{WHITE},{WHITE},&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,{OUT_B},{SHA_B},8,0,0,0,1
Style: Small,Baloo Da 2 ExtraBold,{SMALL},{WHITE},{WHITE},&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,{OUT_S},{SHA_S},8,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

def ts(s):
    cs = int(round(s * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); sec, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{sec:02d}.{cs:02d}"

ev = []
def emit(style, a, b, text, layer=0):
    ev.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")

def block(words, end, y, prev=None, prev_y=96):
    """Accumulating word-by-word reveal; 118%->100% pop on each new word."""
    steps = [w[1] for w in words] + [end]
    for i in range(len(words)):
        a, b = steps[i], steps[i + 1]
        if b <= a: continue
        out = ""
        for j, w in enumerate(words[:i + 1]):
            txt, _, c, br = w[0], w[1], COL[w[2]], w[3]
            if j: out += "\\N" if br else " "
            cc = f"\\c{c}" if c != WHITE else ""
            if j == i:
                out += f"{{\\fscx118\\fscy118{cc}\\t(0,130,\\fscx100\\fscy100)}}{txt}{{\\r}}"
            else:
                out += f"{{{cc}}}{txt}{{\\r}}" if cc else txt
        if prev:
            emit("Small", a, b, f"{{\\pos({CX},{prev_y})\\alpha&H55&}}{prev}", 0)
        emit("Big", a, b, f"{{\\pos({CX},{y})}}{out}", 1)

spec = json.load(open(sys.argv[1], encoding="utf-8"))
for blk in spec:
    block(blk["words"], blk["end"], blk.get("y", 125),
          prev=blk.get("prev"), prev_y=blk.get("prev_y", 96))

open(sys.argv[2], "w", encoding="utf-8").write(HEAD + "\n".join(ev) + "\n")
print(f"{len(ev)} events | BIG={BIG} SMALL={SMALL} outline={OUT_B}/{OUT_S}")
