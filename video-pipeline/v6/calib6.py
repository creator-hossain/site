# -*- coding: utf-8 -*-
import numpy as np, json, wave, sys
from scipy import signal
def load(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768; return a, w.getframerate()
def rms(x, sr, hop_ms):
    h = int(sr * hop_ms / 1000); n = len(x) // h; return 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9), hop_ms / 1000
def band(x, sr, lo, hi): return signal.sosfiltfilt(signal.butter(4, [lo, hi], btype="band", fs=sr, output="sos"), x)
def measure(wav, ev):
    a, sr = load(wav); mid = a.mean(1); side = (a[:, 0] - a[:, 1]) / 2
    v = np.percentile(rms(mid, sr, 10)[0], 90); out = {}
    spec = {"tick": (mid, 2100, 2800, 5, 0.015), "erase": (mid, 1300, 1800, 5, 0.03), "swish": (mid, 3000, 9500, 10, 0.25),
            "whoosh": (side, 60, 3000, 10, 0.32), "click": (side, 300, 9000, 5, 0.04)}
    for k, ts in ev.items():
        if not ts: continue
        x, lo, hi, hop, win = spec[k]; e, dt = rms(band(x, sr, lo, hi), sr, hop)
        vals = [e[max(0, int((t - 0.01) / dt)):int((t + win) / dt) + 1] for t in ts]
        vals = [x.max() - v for x in vals if len(x)]
        if vals: out[k] = float(np.median(vals))
    return out
REF = {"tick": [6.661, 6.728, 6.796, 9.69, 9.758, 9.827, 13.131, 13.201, 13.263], "erase": [11.058], "swish": [0.06],
       "whoosh": [12.25], "click": [13.10]}
if __name__ == "__main__":
    log = json.load(open(sys.argv[2])); mine = {}
    times = [t for t, _ in log]
    for t, s in log:
        if s in ("tick", "erase", "click") and sum(1 for x in times if abs(x - t) < 0.03) > 1: continue
        mine.setdefault(s, []).append(t)
    r = measure("aud/ref.wav", REF); m = measure(sys.argv[1], mine); adj = {}
    print(f"{'sound':<8}{'REF':>7}{'MINE':>7}{'adj':>7}")
    for k in REF:
        if k in m: adj[k] = round(r[k] - m[k], 1); print(f"{k:<8}{r[k]:7.1f}{m[k]:7.1f}{adj[k]:7.1f}  n={len(mine[k])}")
    json.dump(adj, open("adj6.json", "w"))
