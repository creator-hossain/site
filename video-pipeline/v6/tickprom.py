import sys
import numpy as np, json, sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calib6 import load, rms, band
def prom(wav, ts):
    a, sr = load(wav); mid = a.mean(1); e, dt = rms(band(mid, sr, 2100, 2800), sr, 3)
    vals = []
    for t in ts:
        i = int(t / dt); pk = e[max(0, i - 3):i + 8].max(); bg = np.median(e[max(0, i - 14):max(1, i - 4)])
        vals.append(pk - bg)
    return float(np.median(vals))
REF = [6.661, 6.728, 6.796, 9.69, 9.758, 9.827, 13.131, 13.201, 13.263, 9.877, 10.014, 13.012]
log = json.load(open(sys.argv[2])); mine = [t for t, s in log if s == "tick"]
r, m = prom("aud/ref.wav", REF), prom(sys.argv[1], mine)
print(f"tick prominence  REF {r:.1f} dB   MINE {m:.1f} dB")
json.dump({"tick_prom_adj": round(r - m, 1)}, open("tickadj.json", "w"))
