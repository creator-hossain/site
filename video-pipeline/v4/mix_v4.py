# -*- coding: utf-8 -*-
"""Mix: original voice (centre) + rule-placed SFX (stereo-wide), levels learned from ref #4."""
import sys, json, subprocess, numpy as np
sys.path.insert(0, sys.argv[1]); import sfx
SRCV, CUES, OUT_WAV = sys.argv[2:5]
SR = sfx.SR
raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", SRCV, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True).stdout
voice = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
m = voice.mean(1); n = len(m) // 480
r = np.sqrt((m[:n * 480].reshape(n, 480) ** 2).mean(1)); vref = 20 * np.log10(np.percentile(r, 90) + 1e-12)
print(f"voice p90 10ms RMS = {vref:.1f} dBFS")
bus = np.zeros((len(voice) + SR * 3, 2))
cues = json.load(open(CUES)); cache = {}; log = []
for c in cues:
    snd = c["sound"]; kw = {}
    if snd == "counter": kw["d"] = c.get("dur", 0.85)
    key = (snd, tuple(sorted(kw.items())))
    if key not in cache: cache[key] = sfx.KIT[snd](**kw)
    x = cache[key]
    target = vref + sfx.LEVEL[snd] + c["gain"]
    x = x * 10 ** ((target - sfx.peak_db(x)) / 20)
    off = c["off"]
    if off == "lead": start = c["t"] - len(x) / SR           # riser ends exactly on the cut
    elif off == "centre": start = c["t"] - 0.45 * len(x) / SR  # whoosh peaks on the cut
    else: start = c["t"] + off
    i = max(0, int(start * SR)); bus[i:i + len(x)] += x[:len(bus) - i]
    log.append((round(start, 3), c["event"], snd, round(target - vref, 1)))
mix = np.zeros_like(bus); mix[:len(voice)] += voice; mix += bus
mix = mix[:len(voice)]
pk = np.abs(mix).max()
if pk > 0.93:                                 # soft knee limiter on the peaks only
    mix = np.where(np.abs(mix) > 0.8, np.sign(mix) * (0.8 + 0.13 * np.tanh((np.abs(mix) - 0.8) / 0.13)), mix)
print(f"peak before {20*np.log10(pk):.1f} dBFS, after {20*np.log10(np.abs(mix).max()):.1f} dBFS")
import wave
w = wave.open(OUT_WAV, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
json.dump(log, open(OUT_WAV.rsplit(".", 1)[0] + "_log.json", "w"), ensure_ascii=False)
np.save(OUT_WAV.rsplit(".", 1)[0] + "_sfx.npy", bus[:len(voice)].astype(np.float32))
print(len(log), "cues mixed ->", OUT_WAV)
