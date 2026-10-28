# -*- coding: utf-8 -*-
import numpy as np, json, wave, sys
def load(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768; return a, w.getframerate()
def r10(x, sr): h = sr // 100; n = len(x) // h; return 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
def pk(a, t, d=0.35): i = max(0, int(t * 100)); return a[i:i + int(d * 100)].max()
REF = {"blip2": [0.94, 2.86, 3.97, 18.25], "stamp": [32.89, 33.65, 34.30], "burst": [5.21], "thud_whoosh": [14.46],
       "swoosh": [26.42, 31.51, 40.77], "bounce": [24.66], "sweep_stamp": [36.29], "sparkle": [25.26], "pop": [35.43]}
def cls(wav, ev, d=0.35):
    a, sr = load(wav); s = r10((a[:, 0] - a[:, 1]) / 2, sr); v = np.percentile(r10(a.mean(1), sr), 90)
    return {k: float(np.median([pk(s, t, d) - v for t in ts])) for k, ts in ev.items() if ts}
log = json.load(open(sys.argv[2])); mine = {}
for st, ev, so, g in log:
    if so not in REF: continue
    others = [x for x in log if abs(x[0] - st) < 0.35 and x[2] != so and x[2] not in ("blip", "soft_whoosh")]
    if not others: mine.setdefault(so, []).append(st)
r = cls("aud/ref.wav", REF); m = cls(sys.argv[1], mine); adj = {}
print(f"{'sound':<12}{'REF':>7}{'MINE':>7}{'adj':>7}")
for k in REF:
    if k in m: adj[k] = round(r[k] - m[k], 1); print(f"{k:<12}{r[k]:7.1f}{m[k]:7.1f}{adj[k]:7.1f}  n={len(mine[k])}")
json.dump(adj, open("adj5.json", "w"))
