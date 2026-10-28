# -*- coding: utf-8 -*-
"""U2Net cutout: image in -> RGBA with background removed."""
import sys
import numpy as np, onnxruntime as ort
from PIL import Image

MODEL, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(src).convert("RGB"); W, H = im.size

x = np.asarray(im.resize((320, 320), Image.LANCZOS), dtype=np.float32) / 255.0
x = (x - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
x = x.transpose(2, 0, 1)[None].astype(np.float32)

s = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
d = s.run(None, {s.get_inputs()[0].name: x})[0][0, 0]
d = (d - d.min()) / (d.max() - d.min() + 1e-8)

a = Image.fromarray((d * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
out = im.convert("RGBA"); out.putalpha(a)
out.save(dst)
cov = (np.asarray(a) > 128).mean()
print(f"saved {dst}  subject covers {cov*100:.1f}% of frame")
