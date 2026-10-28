# -*- coding: utf-8 -*-
"""Mattes with a configurable model size + contrast curve + temporal smoothing."""
import sys, glob, os, time
import numpy as np, onnxruntime as ort
from PIL import Image

model, src_dir, out_dir, size = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
lo, hi = (float(sys.argv[5]), float(sys.argv[6])) if len(sys.argv) > 6 else (0.35, 0.75)
SMOOTH = int(sys.argv[7]) if len(sys.argv) > 7 else 1    # 0 = independent frames
os.makedirs(out_dir, exist_ok=True)
MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count() or 4
s = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"]); nm = s.get_inputs()[0].name

fs = sorted(glob.glob(os.path.join(src_dir, "*.png"))); t0 = time.time(); raw = []
for f in fs:
    im = Image.open(f).convert("RGB"); W, H = im.size
    x = np.asarray(im.resize((size, size), Image.BILINEAR), np.float32) / 255.0
    x = ((x - MEAN) / STD).transpose(2, 0, 1)[None]
    d = s.run(None, {nm: x})[0][0, 0]
    d = (d - d.min()) / (d.max() - d.min() + 1e-8)
    raw.append(np.clip((d - lo) / (hi - lo), 0, 1))        # contrast curve kills half-detections
el = time.time() - t0
print(f"  {len(fs)} frames in {el:.1f}s ({el/len(fs):.2f}s/frame) @ {size}px")
for i, f in enumerate(fs):
    d = np.mean(raw[max(0, i-SMOOTH): i+SMOOTH+1], axis=0) if SMOOTH else raw[i]
    Image.fromarray((d*255).astype(np.uint8)).resize((W, H), Image.LANCZOS)\
         .save(os.path.join(out_dir, os.path.basename(f)))
print(f"  wrote -> {out_dir}")
