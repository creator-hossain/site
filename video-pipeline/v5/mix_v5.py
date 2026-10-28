# -*- coding: utf-8 -*-
"""voice + rule-placed SFX (reference #5 kit/levels)."""
import sys, json, subprocess, numpy as np, wave
sys.path.insert(0, sys.argv[1]); import sfx5
SRCV, CUES, OUT = sys.argv[2:5]; SR = sfx5.SR
raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", SRCV, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
voice = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
m = voice.mean(1); n = len(m) // 480; vref = 20 * np.log10(np.percentile(np.sqrt((m[:n * 480].reshape(n, 480) ** 2).mean(1)), 90))
LV = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else sfx5.LEVEL
bus = np.zeros((len(voice) + SR * 3, 2)); log = []; cache = {}
for c in json.load(open(CUES)):
    snd, kw = c["sound"], c.get("kw", {}); key = (snd, json.dumps(kw, sort_keys=True))
    if key not in cache: cache[key] = sfx5.KIT[snd](**kw)
    x = cache[key]; target = vref + LV[snd] + c["gain"]; x = x * 10 ** ((target - sfx5.peak_db(x)) / 20)
    off = c["off"]; d = len(x) / SR
    start = c["t"] - d if off == "lead" else c["t"] - 0.75 * 0.9 if off == "lead75" else c["t"] - 0.4 * d if off == "centre" else c["t"] + off
    i = max(0, int(start * SR)); bus[i:i + len(x)] += x[:len(bus) - i]; log.append((round(start, 3), c["event"], snd, round(LV[snd] + c["gain"], 1)))
mix = voice + bus[:len(voice)]; pk = np.abs(mix).max()
if pk > 0.93: mix = np.where(np.abs(mix) > 0.8, np.sign(mix) * (0.8 + 0.13 * np.tanh((np.abs(mix) - 0.8) / 0.13)), mix)
w = wave.open(OUT, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
json.dump(log, open(OUT.rsplit(".", 1)[0] + "_log.json", "w"), ensure_ascii=False)
np.save(OUT.rsplit(".", 1)[0] + "_sfx.npy", bus[:len(voice)].astype(np.float32))
print(f"voice p90 {vref:.1f} dBFS | {len(log)} cues | peak {20*np.log10(pk):.1f} -> {20*np.log10(np.abs(mix).max()):.1f} dBFS")
