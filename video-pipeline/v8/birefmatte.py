# -*- coding: utf-8 -*-
"""BiRefNet mattes for the frames that get keyed onto a new background (person crop -> 1024^2 -> full-frame matte)."""
import sys, os, json, time
import numpy as np, onnxruntime as ort
from PIL import Image
model, src, track, out = sys.argv[1:5]; idx = [int(x) for x in sys.argv[5].split(",")] if "," in sys.argv[5] else None
if idx is None:
    a, b = sys.argv[5].split(":"); idx = list(range(int(a), int(b)))
os.makedirs(out, exist_ok=True)
TR = json.load(open(track)); HX, HTOP, HW = TR["hx"], TR["htop"], TR["hw"]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
s = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"]); nm = s.get_inputs()[0].name
MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
t0 = time.time()
for k, i in enumerate(idx):
    p = os.path.join(out, f"f_{i + 1:04d}.png")
    if os.path.exists(p) or HW[i] <= 0: continue
    im = Image.open(f"{src}/f_{i + 1:04d}.png").convert("RGB"); W, H = im.size
    hx, ht, hw = HX[i], HTOP[i], HW[i]
    x0 = int(max(0, hx - hw * 3.6)); x1 = int(min(W, hx + hw * 3.6)); y0 = int(max(0, ht - hw * 0.8)); y1 = H
    cr = im.crop((x0, y0, x1, y1))
    x = np.asarray(cr.resize((1024, 1024), Image.BILINEAR), np.float32) / 255
    x = ((x - MEAN) / STD).transpose(2, 0, 1)[None]
    d = s.run(None, {nm: x})[0][0, 0]; d = 1 / (1 + np.exp(-d))
    m = Image.fromarray((np.clip(d, 0, 1) * 255).astype(np.uint8)).resize(cr.size, Image.LANCZOS)
    full = Image.new("L", (W, H), 0); full.paste(m, (x0, y0)); full.save(p)
    if k in (0, 4): print(f"  {k + 1} frames {time.time() - t0:.1f}s", flush=True)
print(f"done {len(idx)} in {time.time() - t0:.0f}s")
