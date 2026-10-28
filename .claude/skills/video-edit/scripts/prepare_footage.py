# -*- coding: utf-8 -*-
"""Prepare a talking-head footage for the compose scripts.

Writes into OUT:
  src/f_0001.png ...   frames at 25 fps, 720x1280 (centre-cropped to 9:16)
  matte/f_0001.png ... person alpha mattes (u2net_human_seg, contrast curve, 3-frame smoothing inside a shot)
  track.json           {"hx","htop","hw","shot","shots"} - the head position per frame and the shot list
                       (T = talking-head shot, B = b-roll), the format every compose_vN.py reads

usage: python prepare_footage.py VIDEO OUT [--model u2net_human_seg.onnx] [--frames DIR] [--mattes DIR]
       --frames / --mattes reuse existing folders instead of regenerating them
"""
import sys, os, glob, json, subprocess, argparse
import numpy as np
from PIL import Image

FPS, W, H = 25, 720, 1280
ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("out")
ap.add_argument("--model", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "video-pipeline", "models", "u2net_human_seg.onnx"))
ap.add_argument("--frames"); ap.add_argument("--mattes")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

# ---------------------------------------------------------------- frames
src = a.frames or os.path.join(a.out, "src")
if not a.frames:
    os.makedirs(src, exist_ok=True)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", a.video, "-vf",
                    f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                    os.path.join(src, "f_%04d.png")], check=True)
fs = sorted(glob.glob(os.path.join(src, "f_*.png"))); n = len(fs)
print(f"{n} frames ({n / FPS:.2f} s)")

# ---------------------------------------------------------------- shots (frame-difference peaks)
small = np.stack([np.asarray(Image.open(f).convert("L").resize((64, 114), Image.BILINEAR), np.float32) for f in fs])
diff = np.r_[0, np.abs(np.diff(small, axis=0)).mean(axis=(1, 2))]
thr = max(18.0, float(np.median(diff) + 6 * np.median(np.abs(diff - np.median(diff)))))
cuts = [0]
for i in range(1, n):
    if diff[i] > thr and diff[i] >= diff[max(0, i - 2):i + 3].max() and i - cuts[-1] >= FPS // 2: cuts.append(i)
bounds = cuts + [n]

# ---------------------------------------------------------------- mattes
mat = a.mattes or os.path.join(a.out, "matte")
if not a.mattes:
    import onnxruntime as ort
    os.makedirs(mat, exist_ok=True)
    so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count() or 4
    s = ort.InferenceSession(a.model, so, providers=["CPUExecutionProvider"]); nm = s.get_inputs()[0].name
    MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
    raw = []
    for k, f in enumerate(fs):
        x = np.asarray(Image.open(f).convert("RGB").resize((320, 320), Image.BILINEAR), np.float32) / 255
        d = s.run(None, {nm: ((x - MEAN) / STD).transpose(2, 0, 1)[None]})[0][0, 0]
        d = (d - d.min()) / (d.max() - d.min() + 1e-8); raw.append(np.clip((d - 0.45) / 0.35, 0, 1))
        if k % 100 == 0: print(f"  matte {k}/{n}", flush=True)
    shot_of = np.searchsorted(bounds, np.arange(n), side="right") - 1
    for i, f in enumerate(fs):
        nb = [raw[j] for j in (i - 1, i, i + 1) if 0 <= j < n and shot_of[j] == shot_of[i]]   # never smooth across a cut
        Image.fromarray((np.mean(nb, 0) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS).save(os.path.join(mat, os.path.basename(f)))

# ---------------------------------------------------------------- head track from the mattes
hx = np.zeros(n); htop = np.zeros(n); hwf = np.zeros(n); ok = np.zeros(n, bool)
for i, f in enumerate(fs):
    m = np.asarray(Image.open(os.path.join(mat, os.path.basename(f))).convert("L")) > 128
    if m.mean() < 0.01: continue
    rows = np.where(m.sum(1) > W * 0.01)[0]
    if not len(rows): continue
    t = rows[0]; band = m[t:t + int(H * 0.09)]
    ys, xs = np.nonzero(band)
    if not len(xs): continue
    widths = band[int(band.shape[0] * 0.25):int(band.shape[0] * 0.75)].sum(1)
    hx[i], htop[i], hwf[i], ok[i] = xs.mean(), t, np.median(widths[widths > 0]) if (widths > 0).any() else 0, True

shot = [0] * n; shots = []
for k in range(len(cuts)):
    i0, i1 = bounds[k], bounds[k + 1]; sel = ok[i0:i1]
    med = float(np.median(hwf[i0:i1][sel])) if sel.any() else 0.0
    mode = "T" if sel.mean() > 0.6 and med >= 50 else "B"
    shots.append([round(i0 / FPS, 2), round(i1 / FPS, 2) if k < len(cuts) - 1 else 99, mode])
    for i in range(i0, i1):
        shot[i] = k
        if mode == "B": hx[i] = htop[i] = hwf[i] = 0
    if mode == "T":
        idx = np.arange(i0, i1); good = idx[ok[i0:i1]]
        for arr in (hx, htop): arr[i0:i1] = np.interp(idx, good, arr[good])                # fill dropouts
        hwf[i0:i1] = round(med)                                                             # head size is constant per shot
json.dump(dict(hx=[round(float(v), 1) for v in hx], htop=[round(float(v), 1) for v in htop], hw=[float(v) for v in hwf],
               shot=shot, shots=shots), open(os.path.join(a.out, "track.json"), "w"))
print("shots:", shots)
print("wrote", os.path.join(a.out, "track.json"))
