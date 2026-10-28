# -*- coding: utf-8 -*-
"""3D-extruded, angled kinetic text as ASS (stacked offset copies = depth)."""
import sys, json
W, H = 720, 1280
FAM = "BalooBN"
HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Top,{f},{fs},&H00FFFFFF,&H00FFFFFF,&H00441A04,&H00000000,0,0,0,0,100,100,0,0,1,4,0,5,0,0,0,1
Style: Ext,{f},{fs},&H006E280A,&H006E280A,&H006E280A,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Ext2,{f},{fs2},&H006E280A,&H006E280A,&H006E280A,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Sub,{f},{fs2},&H00FFFFFF,&H00FFFFFF,&H00441A04,&H00000000,0,0,0,0,100,100,0,0,1,3,0,5,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
def ts(s):
    cs=int(round(s*100)); h,cs=divmod(cs,360000); m,cs=divmod(cs,6000); se,cs=divmod(cs,100)
    return f"{h:d}:{m:02d}:{se:02d}.{cs:02d}"

def block(ev, txt, a, b, x, y, rot, depth, dx, dy, style="Top", ext="Ext", pop=240):
    """depth copies behind the face, then the face on top; all share one entry pop."""
    anim = (f"\\fscx62\\fscy62\\fax0.22\\alpha&HFF&"
            f"\\t(0,{pop},0.5,\\fscx100\\fscy100\\fax0\\alpha&H00&)")
    for i in range(depth, 0, -1):
        ev.append(f"Dialogue: {depth-i},{ts(a)},{ts(b)},{ext},,0,0,0,,"
                  f"{{\\an5\\pos({x+i*dx},{y+i*dy})\\frz{rot}\\org({x},{y}){anim}}}{txt}")
    ev.append(f"Dialogue: {depth+1},{ts(a)},{ts(b)},{style},,0,0,0,,"
              f"{{\\an5\\pos({x},{y})\\frz{rot}\\org({x},{y}){anim}}}{txt}")

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    ev = []
    for b_ in spec["blocks"]:
        block(ev, b_["text"], b_["a"], b_["b"], b_["x"], b_["y"], b_.get("rot", 0),
              b_.get("depth", 9), b_.get("dx", 2), b_.get("dy", 3),
              b_.get("style", "Top"), b_.get("ext", "Ext"), b_.get("pop", 240))
    open(sys.argv[2], "w", encoding="utf-8").write(
        HEAD.format(w=W, h=H, f=FAM, fs=spec.get("fs", 96), fs2=spec.get("fs2", 54))
        + "\n".join(ev) + "\n")
    print(f"{len(ev)} events -> {sys.argv[2]}")
