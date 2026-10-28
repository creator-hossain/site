# -*- coding: utf-8 -*-
import sys, json, subprocess, numpy as np, wave
sys.path.insert(0, sys.argv[1]); import sfx6
SRCV, CUES, OUT, LVF = sys.argv[2:6]; SR = sfx6.SR
raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", SRCV, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
voice = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
m = voice.mean(1); n = len(m) // 480; vref = 20 * np.log10(np.percentile(np.sqrt((m[:n * 480].reshape(n, 480) ** 2).mean(1)), 90))
LV = json.load(open(LVF)); bus = np.zeros((len(voice) + SR * 2, 2)); log = []; rng = np.random.default_rng(3); cache = {}
for c in json.load(open(CUES)):
    snd = c["sound"]
    if snd not in cache: cache[snd] = sfx6.KIT[snd]()
    x = cache[snd]
    if snd == "tick":                                   # tiny pitch/level variation so a long run sounds natural
        x = sfx6.KIT["tick"](2400 * (1 + rng.uniform(-0.05, 0.05)))
    target = vref + LV[snd] + c["gain"] + (rng.uniform(-1.2, 1.2) if snd == "tick" else 0)
    x = x * 10 ** ((target - sfx6.peak_db(x)) / 20)
    i = max(0, int(c["t"] * SR)); bus[i:i + len(x)] += x[:len(bus) - i]; log.append((c["t"], snd))
mix = voice + bus[:len(voice)]; pk = np.abs(mix).max()
if pk > 0.93: mix = np.where(np.abs(mix) > 0.8, np.sign(mix) * (0.8 + 0.13 * np.tanh((np.abs(mix) - 0.8) / 0.13)), mix)
w = wave.open(OUT, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
json.dump(log, open(OUT.rsplit(".", 1)[0] + "_log.json", "w"))
print(f"voice p90 {vref:.1f} dBFS | {len(log)} cues | peak {20*np.log10(pk):.1f} dBFS")
