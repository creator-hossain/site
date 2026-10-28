import sys, json, subprocess, numpy as np, wave
sys.path.insert(0, sys.argv[1]); import sfx8
SRCV, CUES, OUT, LVF = sys.argv[2:6]; SR = sfx8.SR
raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", SRCV, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
voice = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
m = voice.mean(1); n = len(m) // 480; vref = 20 * np.log10(np.percentile(np.sqrt((m[:n * 480].reshape(n, 480) ** 2).mean(1)), 90))
LV = json.load(open(LVF)); bus = np.zeros((len(voice) + SR * 4, 2)); log = []
def med_db(x):
    mm = x.mean(1); k = len(mm) // 960; r = np.sqrt((mm[:k * 960].reshape(k, 960) ** 2).mean(1)); return 20 * np.log10(np.median(r[r > 1e-6]))
for c in json.load(open(CUES)):
    snd = c["sound"]
    if snd not in LV: continue
    x = sfx8.KIT[snd](c["dur"]) if snd == "music" else sfx8.KIT[snd]()
    ref = med_db(x) if snd == "music" else sfx8.peak_db(x)       # the bed is set by its median level, hits by their peak
    x = x * 10 ** ((vref + LV[snd] + c["gain"] - ref) / 20)
    i = max(0, int(c["t"] * SR)); bus[i:i + len(x)] += x[:len(bus) - i]; log.append((c["t"], snd, c.get("dur", 0)))
mix = voice + bus[:len(voice)]; pk = np.abs(mix).max()
if pk > 0.89:   # look-ahead peak limiter (no clipping distortion on the sub rumbles)
    from scipy.ndimage import maximum_filter1d
    env = maximum_filter1d(np.abs(mix).max(1), int(0.006 * SR)); g = np.minimum(1.0, 0.89 / np.maximum(env, 1e-9))
    rel = np.exp(-1 / (0.08 * SR)); gs = g.copy()
    for i in range(1, len(gs)): gs[i] = min(g[i], gs[i - 1] * rel + (1 - rel))      # instant attack, 80 ms release
    gs = np.convolve(gs, np.ones(int(0.004 * SR)) / int(0.004 * SR), "same"); mix = mix * np.minimum(gs, g * 1.02)[:, None]
w = wave.open(OUT, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
json.dump(log, open(OUT.rsplit(".", 1)[0] + "_log.json", "w")); print(f"voice p90 {vref:.1f} | {len(log)} cues | peak {20*np.log10(pk):.1f}")
