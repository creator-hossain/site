# -*- coding: utf-8 -*-
"""SFX kit for reference #9 (near-mono mix, L/R corr 0.97 -> everything sits in the centre).

Measured in the reference:
  * thump  - every glass-box pop / zoom cut: a sub swell (28-75 Hz) starting ~0.18 s before the pop, peaking just
             after it, gone ~0.4 s later
  * click  - at the pop itself: short broadband transient (shutter-like)
  * burst  - into the light leak: 0.3 s broadband noise burst, very bright (8-16 kHz strongest)
  * hit    - on the cut into the rain: sub kick + bright click
  * shimmer during the rain (ringing high partials 1.1-5.5 kHz)  -> here: a KEY JINGLE (the rain is car keys)
  * dip    - soft airy whoosh into the black
  * boom   - lower third: long sub boom (peak ~0.1 s, 1 s tail)
  * type   - keyboard ticks while the lower-third words type in
  * music  - quiet dark C#m bed (bass C#/E/F#/G#, soft pad)
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v4"))
from sfx import SR, _t, _band, _lp, _hp, _st, _norm, _verb, peak_db

def _n(n, seed): return np.random.default_rng(seed).standard_normal(n)
def mono(x): return _st(x, x)

def thump(d=0.45):
    t = _t(d); f = 56 - 10 * np.clip(t / d, 0, 1)
    env = np.where(t < 0.18, (t / 0.18) ** 2, np.exp(-(t - 0.18) / 0.09))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR) * env
    return mono(x + _lp(_n(len(t), 1), 120) * env * 0.4)

def click():
    t = _t(0.06); x = _band(_n(len(t), 2), 900, 9000) * np.exp(-t / 0.004)
    x += _band(_n(len(t), 3), 1500, 7000) * np.exp(-np.clip(t - 0.028, 0, None) / 0.004) * (t > 0.028) * 0.6
    return mono(x)

def intro():
    t = _t(0.3); env = np.sin(np.pi * np.clip(t / 0.3, 0, 1)) ** 2
    c = np.zeros(len(t)); ck = click()[:, 0]; i = int(0.06 * SR); c[i:i + len(ck)] = ck[:len(t) - i]
    return mono(_band(_n(len(t), 4), 2500, 12000) * env * 0.5 + c)

def burst(d=0.30):
    t = _t(d); env = np.clip(t / 0.03, 0, 1) * np.where(t < d - 0.03, 1, np.clip((d - t) / 0.03, 0, 1))
    return mono(_hp(_n(len(t), 5), 1200) * env + _band(_n(len(t), 6), 300, 1200) * env * 0.3)

def hit():
    t = _t(0.5); f = 60 + 60 * np.exp(-t / 0.03)
    k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    c = _hp(_n(len(t), 7), 2000) * np.exp(-t / 0.01)
    return mono(k + c * 0.6)

def keys(d=1.5):
    """car keys raining: lots of tiny metallic strikes (inharmonic partials), denser at the start."""
    t = _t(d); out = np.zeros(len(t)); rng = np.random.default_rng(8); tt = 0.0
    while tt < d - 0.1:
        f0 = rng.uniform(1900, 2600); i = int(tt * SR); n = int(0.3 * SR); tk = _t(0.3)
        s = sum(a * np.sin(2 * np.pi * f0 * r * tk + rng.uniform(0, 6)) * np.exp(-tk / dec)
                for r, a, dec in ((1.0, 1.0, 0.12), (1.61, 0.7, 0.09), (2.27, 0.5, 0.07), (2.93, 0.35, 0.05), (3.71, 0.25, 0.04)))
        s += _hp(_n(n, int(tt * 1000)), 4000) * np.exp(-tk / 0.004) * 0.6
        g = rng.uniform(0.4, 1.0) * np.exp(-tt / 0.9); m_ = min(n, len(out) - i); out[i:i + m_] += s[:m_] * g
        tt += rng.exponential(0.035 + 0.06 * tt)
    return mono(out)

def dip():
    t = _t(0.28); env = (t / 0.28) ** 2.5 * np.clip((0.28 - t) / 0.02, 0, 1)
    return mono(_band(_n(len(t), 9), 1500, 9000) * env)

def boom(d=1.3):
    t = _t(d); f = 46 - 6 * (t / d)
    env = np.clip(t / 0.06, 0, 1) * np.exp(-np.clip(t - 0.06, 0, None) / 0.5)
    return mono(np.sin(2 * np.pi * np.cumsum(f) / SR) * env + _lp(_n(len(t), 10), 90) * env * 0.5)

def type_():
    t = _t(0.05); rng = np.random.default_rng(int(np.random.default_rng().integers(1e6)))
    x = _band(rng.standard_normal(len(t)), 2500, 11000) * np.exp(-t / 0.003) + np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.008) * 0.4
    return mono(x)

def music(dur):
    """dark C#m bed: soft bass line + pad (detuned sines, slow swells) + an occasional soft high note."""
    n = int((dur + 2) * SR); tt = np.arange(n) / SR; out = np.zeros((n, 2)); hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(37, (61, 64, 68)), (40, (59, 64, 68)), (42, (61, 66, 69)), (44, (59, 63, 68))]   # C#2 E2 F#2 G#2 + chords
    L = 1.6
    for k, t0 in enumerate(np.arange(0, dur + 2, L)):
        b, ch = prog[k % len(prog)]; a = int(t0 * SR); e = min(n, int((t0 + L + 0.4) * SR)); ts = tt[a:e] - t0
        env = np.clip(ts / 0.15, 0, 1) * np.exp(-ts / 1.6) * np.clip((L + 0.4 - ts) / 0.4, 0, 1)
        pad = np.clip(ts / 0.5, 0, 1) * np.clip((L + 0.4 - ts) / 0.5, 0, 1)
        for c, g in ((0, 1.0),):
            out[a:e, 0] += np.sin(2 * np.pi * hz(b) * ts) * env * 0.9; out[a:e, 1] += np.sin(2 * np.pi * hz(b) * ts + 0.3) * env * 0.9
        for m in ch:
            out[a:e, 0] += np.sin(2 * np.pi * hz(m) * ts) * pad * 0.16; out[a:e, 1] += np.sin(2 * np.pi * hz(m) * 1.004 * ts + 1) * pad * 0.16
        if k % 2 == 1:
            hn = (73, 76, 80, 75)[(k // 2) % 4]; ts2 = ts - 0.8; e2 = np.clip(ts2 / 0.01, 0, 1) * np.exp(-np.clip(ts2, 0, None) / 0.6) * (ts2 > 0)
            out[a:e, 0] += np.sin(2 * np.pi * hz(hn) * ts) * e2 * 0.2; out[a:e, 1] += np.sin(2 * np.pi * hz(hn) * ts) * e2 * 0.2
    out = _verb(out, 1.4, 0.3); fade = np.clip(tt / 0.3, 0, 1) * np.clip((dur - tt) / 0.6, 0, 1)
    return out[:int(dur * SR)] * fade[:int(dur * SR), None]

def _fade(fn):
    def g(*a, **k):
        x = fn(*a, **k); m_ = min(len(x), int(0.008 * SR)); x = x.copy(); x[-m_:] *= np.linspace(1, 0, m_)[:, None]; return x
    return g
KIT = {k: _fade(v) for k, v in dict(thump=thump, click=click, intro=intro, burst=burst, hit=hit, keys=keys, dip=dip,
                                     boom=boom, type=type_, music=music).items()}
