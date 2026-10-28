"""measure each SFX class in reference #9 and in my mix (mid channel bands, dB vs voice p90 10 ms RMS)."""
import sys, os, json, wave, numpy as np
from scipy import signal
def load(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()).astype(np.float32) / 32768; return a, w.getframerate()
def env(x, sr, lo, hi, ms):
    y = signal.sosfiltfilt(signal.butter(4, [lo, hi], btype="band", fs=sr, output="sos"), x); h = int(sr * ms / 1000); n = len(y) // h
    return 20 * np.log10(np.sqrt((y[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9), ms / 1000
def mx(e, dt, a, b): return e[int(a / dt):max(int(a / dt) + 1, int(b / dt))].max()
def meas(wav, W):
    a, sr = load(wav); mid = a.mean(1); side = (a[:, 0] - a[:, 1]) / 2
    n = len(mid) // int(sr / 100); v = np.percentile(20 * np.log10(np.sqrt((mid[:n * int(sr / 100)].reshape(n, -1) ** 2).mean(1)) + 1e-9), 90)
    sub, ds = env(mid, sr, 28, 75, 20); hi, dh = env(mid, sr, 3000, 7000, 10); air, da = env(mid, sr, 8000, 16000, 10)
    o = {}
    o["thump"] = np.median([mx(sub, ds, x, y) for x, y in W["thump"]]) - v
    o["click"] = np.median([mx(hi, dh, x, y) for x, y in W["click"]]) - v
    o["burst"] = np.median([mx(air, da, x, y) for x, y in W["burst"]]) - v
    o["hit"] = np.median([mx(sub, ds, x, y) for x, y in W["hit"]]) - v
    o["keys"] = np.median(np.concatenate([hi[int(x / dh):int(y / dh)] for x, y in W["keys"]])) - v
    o["boom"] = np.median([mx(sub, ds, x, y) for x, y in W["boom"]]) - v
    o["type"] = np.median([mx(air, da, x, y) for x, y in W["type"]]) - v
    sm, dm = env(side, sr, 150, 2000, 20); o["music"] = np.median(np.concatenate([sm[int(x / dm):int(y / dm)] for x, y in W["music"]])) - v
    return {k: float(x) for k, x in o.items()}
if __name__ == "__main__":
    log = json.load(open(sys.argv[2])); g = lambda s: [t for t, n, d in log if n == s]
    R = dict(thump=[(1.0, 1.45), (2.1, 2.5), (3.08, 3.45)], click=[(1.02, 1.1), (2.12, 2.2), (3.12, 3.2)], burst=[(3.96, 4.26)],
             hit=[(4.24, 4.4)], keys=[(4.4, 5.4)], boom=[(7.14, 7.6)], type=[(7.36, 7.41), (7.46, 7.51), (7.55, 7.6), (7.6, 7.65), (7.72, 7.77), (7.8, 7.85), (7.88, 7.93), (7.98, 8.03)], music=[(2.6, 3.0), (5.8, 6.6)])
    M = dict(thump=[(t, t + 0.45) for t in g("thump")], click=[(t - 0.02, t + 0.06) for t in g("click")], burst=[(t, t + 0.3) for t in g("burst")],
             hit=[(t, t + 0.2) for t in g("hit")], keys=[(t + 0.2, t + 1.2) for t in g("keys")], boom=[(t, t + 0.45) for t in g("boom")],
             type=[(x - 0.01, x + 0.04) for x in g("type")], music=[(12.6, 13.0), (19.0, 20.4), (38.5, 39.3)])
    here = os.path.dirname(os.path.abspath(__file__)); r = meas(f"{here}/aud/ref.wav", R); m = meas(sys.argv[1], M)
    for k in r: print(f"{k:<6} REF {r[k]:6.1f}  MINE {m[k]:6.1f}  adj {r[k]-m[k]:+.1f}")
    json.dump({k: r[k] - m[k] for k in r}, open(f"{here}/adj9.json", "w"))
