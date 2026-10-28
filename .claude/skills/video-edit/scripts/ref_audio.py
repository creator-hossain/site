# -*- coding: utf-8 -*-
"""Sound-design analysis of a reference video: where are the SFX, how loud, how wide.

usage: python ref_audio.py REF.mp4 OUTDIR [--step 0.1]
  -> OUTDIR/ref.wav, OUTDIR/spec.png (mid on top, side below, 0.1 s ticks)
  -> prints: L/R correlation (low = SFX are wide / in the side channel), voice p90 level,
     and a table of band energies per step for mid and side (sub, low-mid, mid, high, air).
Read it like this: voice lives in MID 150-2000 Hz; a jump in SIDE or in sub/air bands where the voice is quiet = an SFX.
Levels in the calib scripts are always "dB relative to the voice p90 10 ms RMS of the mid".
"""
import sys, os, subprocess, argparse
import numpy as np
from scipy import signal
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("out"); ap.add_argument("--step", type=float, default=0.1)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); SR = 48000
wav = os.path.join(a.out, "ref.wav")
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", a.ref, "-ac", "2", "-ar", str(SR), wav], check=True)
raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", wav, "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
mid, side = x.mean(1), (x[:, 0] - x[:, 1]) / 2
n = len(mid) // 480; vref = 20 * np.log10(np.percentile(np.sqrt((mid[:n * 480].reshape(n, 480) ** 2).mean(1)), 90) + 1e-12)
print(f"duration {len(mid) / SR:.2f}s | L/R corr {np.corrcoef(x[:, 0], x[:, 1])[0, 1]:.2f} | voice p90 (10 ms) {vref:.1f} dBFS")

bands = [(28, 80), (80, 300), (300, 2000), (2000, 6000), (6000, 16000)]
def env(v, lo, hi):
    y = signal.sosfiltfilt(signal.butter(4, [lo, hi], btype="band", fs=SR, output="sos"), v); h = int(SR * a.step); k = len(y) // h
    return 20 * np.log10(np.sqrt((y[:k * h].reshape(k, h) ** 2).mean(1)) + 1e-9) - vref
M = [env(mid, *b) for b in bands]; S = [env(side, *b) for b in bands]
print("   t |  MID sub  low  mid   hi  air |  SIDE sub  low  mid   hi  air   (dB vs voice p90)")
for i in range(len(M[0])):
    print(f"{i * a.step:5.1f} | " + " ".join(f"{e[i]:4.0f}" for e in M) + " | " + " ".join(f"{e[i]:4.0f}" for e in S))

rows = []
for v in (mid, side):
    hop = 240; f, t, Sx = signal.spectrogram(v, SR, nperseg=2048, noverlap=2048 - hop)
    fb = np.geomspace(40, 18000, 220); D = 10 * np.log10(Sx[np.searchsorted(f, fb)] + 1e-13); D = np.clip((D - D.max() + 80) / 80, 0, 1)[::-1]
    im = Image.fromarray((np.stack([D ** 0.8, D ** 2, D ** 4 * 0.6 + D * 0.2], -1) * 255).astype(np.uint8)).resize((len(t), 300)); d = ImageDraw.Draw(im)
    for k in range(int(len(t) * hop / SR / 0.1) + 1):
        xx = int(k * 0.1 * SR / hop); d.line([xx, 0, xx, 14 if k % 10 == 0 else 4], fill=(255, 255, 255))
        if k % 10 == 0: d.text((xx + 2, 14), str(k // 10), fill=(255, 255, 255))
    rows.append(im)
c = Image.new("RGB", (rows[0].width, 610)); c.paste(rows[0], (0, 0)); c.paste(rows[1], (0, 310)); c.save(os.path.join(a.out, "spec.png"))
print("spectrogram ->", os.path.join(a.out, "spec.png"), "(top = mid, bottom = side)")
