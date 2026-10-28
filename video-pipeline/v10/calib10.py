"""measure SFX classes in reference #10 vs my mix: side-channel peaks (wide SFX), mid sub for the low whooshes."""
import sys, os, json, wave, numpy as np
from scipy import signal
def load(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()).astype(np.float32) / 32768; return a, w.getframerate()
def env(x, sr, lo, hi, ms):
    y = signal.sosfiltfilt(signal.butter(4, [lo, hi], btype="band", fs=sr, output="sos"), x); h = int(sr * ms / 1000); n = len(y) // h
    return 20 * np.log10(np.sqrt((y[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9), ms / 1000
def mx(e, dt, a, b): return e[int(a / dt):max(int(a / dt) + 1, int(b / dt))].max()
def meas(wav, Wn):
    a, sr = load(wav); mid = a.mean(1); side = (a[:, 0] - a[:, 1]) / 2
    n = len(mid) // int(sr / 100); v = np.percentile(20 * np.log10(np.sqrt((mid[:n * int(sr / 100)].reshape(n, -1) ** 2).mean(1)) + 1e-9), 90)
    sd, ds = env(side, sr, 60, 16000, 20); sub, dsub = env(mid, sr, 28, 80, 20); sm, dm = env(side, sr, 150, 2000, 50)
    o = {}
    for k in ("impact", "swish", "pop", "ding", "swell", "tick"): o[k] = np.median([mx(sd, ds, x, y) for x, y in Wn[k]]) - v
    o["lowwhoosh"] = np.median([mx(sub, dsub, x, y) for x, y in Wn["lowwhoosh"]]) - v
    o["music"] = np.median(np.concatenate([sm[int(x / dm):int(y / dm)] for x, y in Wn["music"]])) - v
    return {k: float(x) for k, x in o.items()}
if __name__ == "__main__":
    log = json.load(open(sys.argv[2])); g = lambda s: [t for t, nn, d in log if nn == s]
    R = dict(impact=[(1.95, 2.45)], swish=[(4.65, 5.15)], pop=[(22.2, 22.55), (27.2, 27.65), (28.7, 29.1)], ding=[(13.2, 13.55)],
             swell=[(36.4, 37.0), (39.7, 40.15), (46.4, 46.95)], tick=[(10.3, 10.45)], lowwhoosh=[(18.4, 18.9), (24.4, 25.3)],
             music=[(6.6, 7.9), (30.0, 31.0), (41.0, 43.0)])
    M = dict(impact=[(t, t + 0.5) for t in g("impact")], swish=[(t, t + 0.3) for t in g("swish")], pop=[(t, t + 0.2) for t in g("pop")],
             ding=[(t, t + 0.4) for t in g("ding")], swell=[(t, t + 0.5) for t in g("swell")], tick=[(t - 0.01, t + 0.05) for t in g("tick")],
             lowwhoosh=[(t, t + 0.6) for t in g("lowwhoosh")], music=[(9.3, 10.9), (19.0, 20.4), (21.0, 23.5)])
    here = os.path.dirname(os.path.abspath(__file__)); r = meas(f"{here}/aud/ref.wav", R); m = meas(sys.argv[1], M)
    for k in r: print(f"{k:<9} REF {r[k]:6.1f}  MINE {m[k]:6.1f}  adj {r[k]-m[k]:+.1f}")
    json.dump({k: r[k] - m[k] for k in r}, open(f"{here}/adj10.json", "w"))
