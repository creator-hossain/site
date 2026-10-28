# -*- coding: utf-8 -*-
"""SFX kit for reference #7: wind/water ambience bed, swooshes, airy shine swish, faint click."""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v4"))
import sfx as base
from sfx import SR, _t, _noise, _band, _lp, _hp, _st, _norm, _tv_band, _verb, peak_db

def ambience(dur=3.6):
    """wide wind/water bed: low rumble + mid wash with slow swells, airy top; decorrelated L/R."""
    t = _t(dur); rng = np.random.default_rng(int(dur * 100))
    def ch(seed):
        r = np.random.default_rng(seed)
        low = _lp(r.standard_normal(len(t)), 500); mid = _band(r.standard_normal(len(t)), 500, 2500); air = _band(r.standard_normal(len(t)), 3000, 8000)
        sw = 0.65 + 0.35 * np.sin(2 * np.pi * (0.45 * t + r.random())) * np.sin(2 * np.pi * (0.17 * t + r.random()))
        return _norm(low) * 1.0 + _norm(mid) * 0.55 * sw + _norm(air) * 0.18 * sw
    env = np.clip(t / 0.35, 0, 1) * np.clip((dur - t) / 0.45, 0, 1)
    return _st(ch(1) * env, ch(2) * env)

def swoosh(): return base.KIT["swoosh"](0.9)
def swoosh_soft(): return base.KIT["soft_whoosh"](0.55)

def shine():
    """light sweeping across an object: airy noise swish rising 2.5 -> 9 kHz over 0.45 s."""
    d = 0.45; t = _t(d); p = t / d; env = np.sin(np.pi * p) ** 1.4
    cen = 2500 * (9000 / 2500) ** p
    return _st(_norm(_tv_band(_noise(len(t)), cen, 1.6)) * env, _norm(_tv_band(_noise(len(t)), cen, 1.6)) * env)

def click():
    """label pops: faint mono 70 ms band-noise tick (2-6 kHz)."""
    t = _t(0.08); env = (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.018)
    x = _band(_noise(len(t)), 2000, 6000) * env; return _st(x, x)

def _fade(fn):
    def g(*a, **k):
        x = fn(*a, **k); n = min(len(x), int(0.01 * SR)); x = x.copy(); x[-n:] *= np.linspace(1, 0, n)[:, None]; return x
    return g
KIT = {k: _fade(v) for k, v in dict(ambience=ambience, swoosh=swoosh, swoosh_soft=swoosh_soft, shine=shine, click=click).items()}
# calibrated vs reference #7 (side channel): ambience median & swoosh peak within 0.3 dB.
# click: not measurable in the reference (barely present) -> kept very faint by choice
LEVEL = dict(ambience=-49.2, swoosh=-23.7, swoosh_soft=-27.7, shine=-27.7, click=-40.0)
