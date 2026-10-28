# -*- coding: utf-8 -*-
"""SFX kit for reference #6 (measured): typewriter tick, erase tick, rising swish, glitch whoosh, click."""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v4"))
from sfx import SR, _t, _noise, _band, _lp, _hp, _st, _norm, _tv_band, _verb, _pad, peak_db

def tick(f0=2400.0):
    """typed cluster: 17 ms tonal tick at ~2.4 kHz (ref: 2.3-2.5 kHz, 17 ms, every ~68 ms)."""
    t = _t(0.03); env = (1 - np.exp(-t / 0.0008)) * np.exp(-t / 0.0055)
    f = f0 * (1 + 0.04 * np.exp(-t / 0.004))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env + _hp(_noise(len(t)), 5000) * np.exp(-t / 0.0015) * 0.15
    return _st(x, x * 0.97)

def erase():
    """letters start disappearing: lower, slightly longer tick (ref: 1.5 kHz, 30 ms)."""
    t = _t(0.045); env = (1 - np.exp(-t / 0.001)) * np.exp(-t / 0.011)
    x = np.sin(2 * np.pi * 1520 * t) * env + _band(_noise(len(t)), 900, 3000) * env * 0.25
    return _st(x, x * 0.97)

def swish():
    """opening: noisy sweep rising 3 -> 8.5 kHz in ~0.2 s."""
    d = 0.22; t = _t(d); p = t / d
    cen = 3000 * (8500 / 3000) ** p; env = np.sin(np.pi * np.clip(p, 0, 1)) ** 1.2
    l = _tv_band(_noise(len(t)), cen, 2.2) * env; r = _tv_band(_noise(len(t)), cen, 2.2) * env
    return _st(_norm(l), _norm(r))

def whoosh():
    """vertical-roll glitch: 0.3 s bell-shaped broadband whoosh, weight below 2 kHz."""
    d = 0.32; t = _t(d); p = t / d; env = np.sin(np.pi * p) ** 1.5
    def ch(): return _lp(_norm(_noise(len(t))), 2600) + _norm(_lp(_noise(len(t)), 300)) * 0.6
    return _verb(_st(ch() * env, ch() * env), 0.35, 0.12)

def click():
    """'!!' / icon lands: broadband click + short 2.5 kHz tone."""
    t = _t(0.06); env = np.exp(-t / 0.008)
    x = _band(_noise(len(t)), 300, 9000) * np.exp(-t / 0.003) + np.sin(2 * np.pi * 2500 * t) * env * 0.6
    return _st(x, x * 0.95)

def _fade(fn):
    def g(*a, **k):
        x = fn(*a, **k); n = min(len(x), int(0.004 * SR)); x = x.copy(); x[-n:] *= np.linspace(1, 0, n)[:, None]; return x
    return g
KIT = {k: _fade(v) for k, v in dict(tick=tick, erase=erase, swish=swish, whoosh=whoosh, click=click).items()}
# calibrated vs reference #6: tick by prominence over local background (17.6 dB),
# erase/swish/whoosh/click by band level vs voice p90 (all within 0.3 dB)
LEVEL = dict(tick=-21.5, erase=-18.7, swish=-17.1, whoosh=-5.2, click=-3.6)
