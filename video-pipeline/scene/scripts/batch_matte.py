# -*- coding: utf-8 -*-
"""Alpha mattes for a folder of frames, one warm ONNX session, temporally smoothed."""
import sys, glob, os, time
import numpy as np, onnxruntime as ort
from PIL import Image

model, src_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out_dir, exist_ok=True)
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count() or 4
s = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"])
name = s.get_inputs()[0].name

fs = sorted(glob.glob(os.path.join(src_dir, "*.png")))
t0 = time.time(); raw = []
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGB"); W, H = im.size
    x = np.asarray(im.resize((320, 320), Image.BILINEAR), dtype=np.float32) / 255.0
    x = ((x - MEAN) / STD).transpose(2, 0, 1)[None]
    d = s.run(None, {name: x})[0][0, 0]
    d = (d - d.min()) / (d.max() - d.min() + 1e-8)
    raw.append(d)
    if i == 4: print(f"  first 5 frames: {time.time()-t0:.1f}s", flush=True)
el = time.time() - t0
print(f"  inference: {len(fs)} frames in {el:.1f}s ({el/max(len(fs),1):.2f}s/frame)")

# temporal smoothing kills the frame-to-frame edge wobble
sm = []
for i in range(len(raw)):
    w = raw[max(0, i-1): i+2]
    sm.append(np.mean(w, axis=0))
for f, d in zip(fs, sm):
    a = Image.fromarray((np.clip(d, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    a.save(os.path.join(out_dir, os.path.basename(f)))
print(f"  wrote {len(fs)} mattes -> {out_dir}")
