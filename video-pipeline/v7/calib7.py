import sys, os, json, wave, numpy as np
from scipy import signal
def load(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768; return a, w.getframerate()
def rms(x, sr, ms): h = int(sr * ms / 1000); n = len(x) // h; return 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9), ms / 1000
def band(x, sr, lo, hi): return signal.sosfiltfilt(signal.butter(4, [lo, hi], btype="band", fs=sr, output="sos"), x)
def meas(wav, amb, sw, clicks):
    a, sr = load(wav); mid = a.mean(1); side = (a[:, 0] - a[:, 1]) / 2; v = np.percentile(rms(mid, sr, 10)[0], 90)
    es, dt = rms(side, sr, 20)
    out = {"ambience": float(np.median(np.concatenate([es[int(x / dt):int(y / dt)] for x, y in amb]))) - v}
    out["swoosh"] = float(np.median([es[int(t / dt):int((t + 0.9) / dt)].max() for t in sw])) - v
    e, dt3 = rms(band(mid, sr, 2000, 6000), sr, 3)
    out["click_prom"] = float(np.median([e[int(t / dt3) - 2:int(t / dt3) + 25].max() - np.median(e[max(0, int(t / dt3) - 30):int(t / dt3) - 5]) for t in clicks]))
    return out
if __name__ == "__main__":
    log = json.load(open(sys.argv[2]))
    amb = [(t + 0.5, t + d - 0.5) for t, s, d in log if s == "ambience"][:1]
    sw = [t for t, s, d in log if s == "swoosh" and t > 5][:3]
    cl = [t for t, s, d in log if s == "click"]
    r = meas(os.path.join(os.path.dirname(os.path.abspath(__file__)), "aud/ref.wav"), [(0.5, 2.6)], [2.8], [5.55, 8.6])
    m = meas(sys.argv[1], amb, sw, cl)
    for k in r: print(f"{k:<11} REF {r[k]:6.1f}  MINE {m[k]:6.1f}  adj {r[k]-m[k]:+.1f}")
    json.dump({k: float(r[k] - m[k]) for k in r}, open("adj7.json", "w"))
