# -*- coding: utf-8 -*-
"""Contact sheets of a reference video so Claude can SEE its edit: one grid image per time window.

usage: python ref_sheet.py REF.mp4 OUTDIR [--fps 10] [--window 3] [--width 160]
  -> OUTDIR/sheet_000.png ...  each covers WINDOW seconds at FPS frames/s, labelled with timestamps
  Also prints the hard cuts ffmpeg finds (scene score > 0.25).
Use --fps 2 --window 30 first for an overview, then --fps 10 (or 30) on the windows where something animates.
"""
import sys, os, glob, subprocess, argparse, re, tempfile, shutil
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("out")
ap.add_argument("--fps", type=float, default=10); ap.add_argument("--window", type=float, default=3); ap.add_argument("--width", type=int, default=160)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)

log = subprocess.run(["ffmpeg", "-nostdin", "-i", a.ref, "-vf", "select='gt(scene,0.25)',showinfo", "-f", "null", "-"], capture_output=True, text=True).stderr
print("cuts (s):", " ".join(f"{float(x):.2f}" for x in re.findall(r"pts_time:([0-9.]+)", log)))

tmp = tempfile.mkdtemp()
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", a.ref, "-vf", f"fps={a.fps},scale={a.width}:-2", os.path.join(tmp, "f_%05d.png")], check=True)
fs = sorted(glob.glob(os.path.join(tmp, "f_*.png"))); per = max(1, int(round(a.fps * a.window))); cols = min(10, per)
for k in range(0, len(fs), per):
    ims = [Image.open(f) for f in fs[k:k + per]]; w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, (h + 14) * rows), "black"); d = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x, y = (i % cols) * w, (i // cols) * (h + 14); sheet.paste(im, (x, y + 14)); d.text((x + 2, y + 1), f"{(k + i) / a.fps:.2f}s", fill=(255, 255, 0))
    sheet.save(os.path.join(a.out, f"sheet_{k // per:03d}.png"))
print(f"{(len(fs) + per - 1) // per} sheets -> {a.out}")
shutil.rmtree(tmp, ignore_errors=True)
