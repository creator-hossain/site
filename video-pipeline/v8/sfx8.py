# -*- coding: utf-8 -*-
"""SFX kit for reference #8.

Measured in the reference (side channel, L/R corr 0.2 -> everything is very wide):
  * boom   - world in / out (glass wipe, graphics slide out): deep 25-55 Hz noise rumble that swells in ~0.1 s,
             holds ~0.35 s, dies by 0.55 s; a little mid/air whoosh riding on top (centroid jumps to ~1.2 kHz twice)
  * swell  - map slides in: sub rumble rising for ~0.65 s to a peak, then decaying; a mid/high whoosh at the slide
  * tick   - caption box pops in: 6-16 kHz click, then a 2-6 kHz micro swish ~75 ms later
  * outro  - soft sub swell under the closing fade
  * music  - quiet ambient bed under everything: C#m(add9) notes (C#5 D#5 E5 G#5, bass C#/A) softly re-attacking
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v4"))
from sfx import SR, _t, _band, _lp, _hp, _st, _norm, _tv_band, _verb, peak_db

def _n(n, seed): return np.random.default_rng(seed).standard_normal(n)

def _rumble(env, seed, cut=70):
    n = len(env); return _norm(_lp(_n(n, seed), cut, 4)) * env

def boom(d=0.62):
    t = _t(d); p = t / d
    env = np.clip(t / 0.10, 0, 1) ** 1.5 * np.where(t < 0.42, 1.0, np.exp(-(t - 0.42) / 0.06))
    def ch(seed):
        sub = _rumble(env, seed)
        cen = np.where(t < 0.18, 600 + 5000 * t / 0.18, 1400 * np.exp(-(t - 0.18) / 0.25) + 300)
        wh = _norm(_tv_band(_n(len(t), seed + 7), cen, 0.8)) * np.sin(np.pi * np.clip(p / 0.75, 0, 1)) ** 2
        air = _norm(_hp(_n(len(t), seed + 9), 6000)) * np.exp(-((t - 0.05) / 0.025) ** 2)
        return sub + wh * 0.10 + air * 0.05
    return _st(ch(1), ch(2))

def swell(d=1.15, peak=0.65):
    t = _t(d)
    env = np.where(t < peak, (t / peak) ** 2.2, np.exp(-(t - peak) / 0.28))
    def ch(seed):
        sub = _rumble(env, seed, 80)
        g = np.exp(-((t - (peak - 0.18)) / 0.09) ** 2)
        wh = _norm(_tv_band(_n(len(t), seed + 3), 900 + 3500 * np.clip((t - peak + 0.35) / 0.3, 0, 1), 0.7)) * g
        return sub + wh * 0.09
    return _st(ch(11), ch(12))

def tick():
    t = _t(0.16)
    def ch(seed):
        clk = _hp(_n(len(t), seed), 6500) * np.exp(-t / 0.006)
        s = np.clip((t - 0.06) / 0.015, 0, 1) * np.exp(-np.clip(t - 0.075, 0, None) / 0.03)
        sw = _band(_n(len(t), seed + 1), 2200, 6000) * s
        return _norm(clk) * 0.45 + _norm(sw)
    return _st(ch(21), ch(22))

def outro(d=0.7):
    t = _t(d); env = np.clip(t / 0.3, 0, 1) ** 1.6 * np.clip((d - t) / 0.12, 0, 1)
    return _st(_rumble(env, 31, 75), _rumble(env, 32, 75))

# ------------------------------------------------------------------ music bed
def _note(f, d, seed, vel=1.0):
    """soft bell/e-piano tone: sine + a touch of 2nd/3rd harmonic, slow-ish attack, long decay, slightly detuned L/R."""
    t = _t(d); env = (1 - np.exp(-t / 0.035)) * np.exp(-t / 0.9) * vel
    r = np.random.default_rng(seed).random(2)
    def ch(det, ph):
        w = 2 * np.pi * f * det * t + ph
        return (np.sin(w) + 0.18 * np.sin(2 * w) + 0.05 * np.sin(3 * w)) * env
    return _st(ch(1.0, r[0] * 6), ch(1.0025, r[1] * 6))

def music(dur):
    """C#m(add9) ambient bed: an 8th-note-ish arpeggio of soft tones over a sustained pad and bass (C# / A)."""
    n = int((dur + 2) * SR); out = np.zeros((n, 2)); rng = np.random.default_rng(5)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    arp = [73, 76, 80, 75, 73, 80, 76, 75]               # C#5 E5 G#5 D#5 ...
    step = 0.34; k = 0; t = 0.0
    while t < dur:
        nt = _note(hz(arp[k % len(arp)]), 1.6, k, 0.75 + 0.25 * rng.random()); i = int(t * SR)
        out[i:i + len(nt)] += nt[:n - i]; t += step * (0.92 + 0.16 * rng.random()); k += 1
    # pad + bass, chord root alternating every 4 s (C#m -> A(add9))
    tt = np.arange(n) / SR
    for seg0 in np.arange(0, dur + 2, 4.0):
        root = 49 if int(seg0 / 4) % 2 == 0 else 45   # C#3 / A2
        a = int(seg0 * SR); b = min(n, int((seg0 + 4.0) * SR)); ts = tt[a:b] - seg0
        env = np.clip(ts / 0.6, 0, 1) * np.clip((4.0 - ts) / 0.6, 0, 1)
        for m, g in ((root, 0.55), (root + 12, 0.35), (68, 0.18), (73, 0.15)):
            out[a:b, 0] += np.sin(2 * np.pi * hz(m) * tt[a:b]) * env * g
            out[a:b, 1] += np.sin(2 * np.pi * hz(m) * 1.003 * tt[a:b] + 1.1) * env * g
    out = _verb(out, 1.6, 0.35)
    fade = np.clip(tt / 0.4, 0, 1) * np.clip((dur - tt) / 0.6, 0, 1)
    return out[:int(dur * SR)] * fade[:int(dur * SR), None]

def _fade(fn):
    def g(*a, **k):
        x = fn(*a, **k); m = min(len(x), int(0.01 * SR)); x = x.copy(); x[-m:] *= np.linspace(1, 0, m)[:, None]; return x
    return g
KIT = {k: _fade(v) for k, v in dict(boom=boom, swell=swell, tick=tick, outro=outro, music=music).items()}
LEVEL = dict(boom=-2.0, swell=-8.0, tick=-22.0, outro=-20.0, music=-38.0)   # placeholders, calibrated below
