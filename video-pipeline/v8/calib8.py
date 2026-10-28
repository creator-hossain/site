"""measure each SFX class in the reference and in my mix (side channel, dB vs voice p90 10 ms RMS of the mid)."""
import sys, os, json, wave, numpy as np
from scipy import signal
def load(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()).astype(np.float32) / 32768; return a, w.getframerate()
def rms(x, sr, ms): h = int(sr * ms / 1000); n = len(x) // h; return 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9), ms / 1000
def band(x, sr, lo, hi): return signal.sosfiltfilt(signal.butter(4, [lo, hi], btype="band", fs=sr, output="sos"), x)
def meas(wav, wins):
    a, sr = load(wav); mid = a.mean(1); side = (a[:, 0] - a[:, 1]) / 2; v = np.percentile(rms(mid, sr, 10)[0], 90)
    es, dt = rms(side, sr, 20); out = {}
    for k in ("boom", "swell", "outro"):
        out[k] = float(np.median([es[int(x / dt):int(y / dt)].max() for x, y in wins[k]])) - v
    eh, dth = rms(band(side, sr, 2000, 16000), sr, 10)
    out["tick"] = float(np.median([eh[int(x / dth):int(y / dth)].max() for x, y in wins["tick"]])) - v
    em, dtm = rms(band(side, sr, 200, 2000), sr, 20)
    out["music"] = float(np.median(np.concatenate([em[int(x / dtm):int(y / dtm)] for x, y in wins["music"]]))) - v
    return out
if __name__ == "__main__":
    log = json.load(open(sys.argv[2]))
    R = dict(boom=[(0.08, 0.75), (4.08, 4.70)], swell=[(2.0, 3.2)], outro=[(9.7, 10.15)], tick=[(4.80, 5.00), (8.44, 8.66)], music=[(5.2, 8.3)])
    M = dict(boom=[(t, t + 0.75) for t, s, d in log if s == "boom"][:4], swell=[(t, t + 1.2) for t, s, d in log if s == "swell"],
             outro=[(t, t + 0.7) for t, s, d in log if s == "outro"], tick=[(t - 0.02, t + 0.2) for t, s, d in log if s == "tick"],
             music=[(12.0, 13.0), (37.5, 39.0)])
    r = meas(os.path.join(os.path.dirname(os.path.abspath(__file__)), "aud/ref.wav"), R); m = meas(sys.argv[1], M)
    for k in r: print(f"{k:<6} REF {r[k]:6.1f}  MINE {m[k]:6.1f}  adj {r[k]-m[k]:+.1f}")
    json.dump({k: float(r[k] - m[k]) for k in r}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "adj8.json"), "w"))
