# -*- coding: utf-8 -*-
import sys

W, H = 1024, 1280
CX = 512
BIG, SMALL = 70, 36
WHITE, GOLD = r"&H00FFFFFF", r"&H0000C8FF"

HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Big,Noto Sans Bengali,{BIG},{WHITE},{WHITE},&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,5,3,8,0,0,0,1
Style: Small,Noto Sans Bengali,{SMALL},{WHITE},{WHITE},&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,3,2,8,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

def t(s):
    cs = int(round(s * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); sec, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{sec:02d}.{cs:02d}"

ev = []
def line(style, a, b, text, layer=0):
    ev.append(f"Dialogue: {layer},{t(a)},{t(b)},{style},,0,0,0,,{text}")

def reveal(words, end, y, prev=None, prev_y=96):
    """words = [(text, start, colour, break_before)] -> accumulating reveal with a pop per word."""
    steps = [w[1] for w in words] + [end]
    for i in range(len(words)):
        a, b = steps[i], steps[i + 1]
        if b <= a: continue
        out = ""
        for j, (txt, _, col, br) in enumerate(words[:i + 1]):
            if j: out += "\\N" if br else " "
            c = f"\\c{col}" if col != WHITE else ""
            if j == i:
                out += f"{{\\fscx118\\fscy118{c}\\t(0,130,\\fscx100\\fscy100)}}{txt}{{\\r}}"
            else:
                out += f"{{{c}}}{txt}{{\\r}}" if c else txt
        if prev:
            line("Small", a, b, f"{{\\pos({CX},{prev_y})\\alpha&H55&}}{prev}", layer=0)
        line("Big", a, b, f"{{\\pos({CX},{y})}}{out}", layer=1)

W_, G_ = WHITE, GOLD
L1 = [("সারাদিন",0.15,W_,0), ("অফিস",0.38,W_,0), ("করে",0.58,W_,0),
      ("বাসায়",0.95,W_,1), ("গিয়েছেন",1.25,W_,0)]
L2 = [("এখন",2.20,W_,0), ("আর",2.35,W_,0),
      ("মনটা",2.52,W_,1), ("চাইছে",2.68,W_,0), ("না",2.84,W_,0)]
L3 = [("আয়োজন",3.15,G_,0)]
L4 = [("রান্না",4.10,W_,0), ("বান্না",4.40,W_,0), ("করতে",4.62,W_,0)]

P2 = "সারাদিন অফিস করে বাসায় গিয়েছেন"
P3 = "এখন আর মনটা চাইছে না"
P4 = "এখন আর মনটা চাইছে না আয়োজন করে"

reveal(L1, 2.18, 125)
reveal(L2, 3.12, 155, prev=P2)
reveal(L3, 4.05, 165, prev=P3)
reveal(L4, 5.83, 165, prev=P4)

open(sys.argv[1], "w", encoding="utf-8").write(HEAD + "\n".join(ev) + "\n")
print(f"{len(ev)} events")
