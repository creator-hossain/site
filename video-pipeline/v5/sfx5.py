# -*- coding: utf-8 -*-
"""SFX kit for reference #5: harmonic blips, stamps, rising bursts, bounce, sweep.
Reuses the reference-#4 kit (sfx.py) for whoosh / shimmer / pop."""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v4"))
import sfx as base
from sfx import SR, _t, _noise, _band, _lp, _hp, _st, _norm, _tv_band, _verb, _pad, _wide, peak_db

def _harm(f, t, env, n=5, roll=0.55, det=1.0):
    ph = 2 * np.pi * np.cumsum(f) / SR * det
    return sum((roll ** k) * np.sin((k + 1) * ph) for k in range(n)) * env

def blip(f0=880.0, d=0.13):
    """caption / tag entry: dense harmonic blip + low body + a little grit (ref: blocky stacked bands)."""
    t = _t(d); f = f0 * (1 + 0.2 * (1 - np.exp(-t / 0.03)))
    env = (1 - np.exp(-t / 0.003)) * np.exp(-t / (d * 0.45))
    l = _harm(f, t, env, 10, 0.78); r = _harm(f, t, env, 10, 0.78, det=1.004)
    grit = _band(_noise(len(t)), 800, 5000) * env * 0.35
    body = np.sin(2 * np.pi * 150 * t) * np.exp(-t / 0.04) * 0.5
    air = _band(_noise(len(t)), 4000, 9000) * np.exp(-t / 0.02) * 0.15
    return _verb(_pad(_st(_norm(l) + grit + body + air, _norm(r) + grit + body + air), 0.2), 0.3, 0.14)

def blip2(f0=880.0):
    """two quick blips (ref 'Customer' line: two bursts ~0.12 s apart)."""
    a = blip(f0); b = blip(f0 * 1.335); out = np.zeros((len(a) + int(0.12 * SR), 2))
    out[:len(a)] += a; out[int(0.12 * SR):int(0.12 * SR) + len(b)] += b * 0.8; return out

def stamp(f0=420.0):
    """pink box stamped in: dense harmonic boop (0.2 s) + short low body + click."""
    t = _t(0.24); f = f0 * (1 - 0.10 * (1 - np.exp(-t / 0.05)))
    env = (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.075)
    h = _harm(f, t, env, 12, 0.8); grit = _band(_noise(len(t)), 500, 4500) * env * 0.4
    body = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.035) * 0.8
    clk = _hp(_noise(len(t)), 5000) * np.exp(-t / 0.003) * 0.4
    x = _st(_norm(h) + grit + body + clk, _norm(h) * 0.95 + grit + body + clk)
    return _verb(_pad(x, 0.25), 0.35, 0.12)

def burst(d=0.9):
    """energy-burst transition: rough whoosh whose band climbs, low-heavy, fluttery (no clean tone)."""
    t = _t(d); p = t / d
    env = np.where(p < 0.75, (p / 0.75) ** 1.4, np.exp(-(p - 0.75) / 0.25 * 3))
    flut = 1 + 0.5 * np.clip(_lp(_noise(len(t)), 18) / 0.02, -1, 1)
    cen = 250 * (3200 / 250) ** np.clip(p / 0.8, 0, 1)
    def ch(): return _lp(_norm(_tv_band(_noise(len(t)), cen, 0.6)) + _norm(_lp(_noise(len(t)), 220)) * 0.9, 4500)
    return _verb(_st(ch() * env * flut, ch() * env * flut), 0.6, 0.15)

def thud_whoosh(d=0.6):
    """flash back to the talking shot: low-heavy whoosh."""
    return base.swoosh(d, peak=0.35, lo=150, hi=1400)

def bounce():
    """logo card drops and bounces: 4 decaying blips, intervals shrinking."""
    out = np.zeros((int(0.9 * SR), 2)); t = 0.0; gap = 0.16; g = 1.0
    for k in range(4):
        b = blip(620 - 40 * k, 0.1); i = int(t * SR); out[i:i + len(b)] += b[:len(out) - i] * g
        t += gap; gap *= 0.7; g *= 0.6
    return out

def sweep_stamp():
    """offer stamp: a broad low-mid block (200-1500 Hz) with a gently falling harmonic, 0.3 s."""
    t = _t(0.34); f = 260 * (0.8 ** (t / 0.34))
    env = (1 - np.exp(-t / 0.004)) * np.where(t < 0.26, 1.0, np.exp(-(t - 0.26) / 0.03))
    h = _harm(f, t, env, 8, 0.8)
    blk = _band(_noise(len(t)), 200, 1500) * env * 0.8
    def ch(): return _norm(h) + _norm(_band(_noise(len(t)), 200, 1500) * env) * 0.8
    return _verb(_st(ch(), ch()), 0.4, 0.15)

def sparkle():
    """brand text reveal: thin high shimmer lines, only a whisper of whoosh."""
    s = base.KIT["shimmer"](); w = base.KIT["soft_whoosh"](0.5)
    out = np.zeros((max(len(s), len(w)), 2)); out[:len(w)] += w * 0.15; out[:len(s)] += s; return out

def _fade(fn):
    def g(*a, **k):
        x = fn(*a, **k); n = min(len(x), int(0.012 * SR)); x = x.copy(); x[-n:] *= np.linspace(1, 0, n)[:, None]; return x
    return g

KIT = dict(base.KIT)
for k, v in dict(blip=blip, blip2=blip2, stamp=stamp, burst=burst, thud_whoosh=thud_whoosh,
                 bounce=bounce, sweep_stamp=sweep_stamp, sparkle=sparkle).items():
    KIT[k] = _fade(v)
for k in ("blip", "blip2", "stamp", "bounce", "sweep_stamp"):
    KIT[k] = (lambda f: (lambda *a, **kw: _wide(f(*a, **kw), 7.0)))(KIT[k])

# levels (dB vs voice p90 10 ms RMS), calibrated against reference #5 in a measure->adjust loop
# (side channel, 0.35 s windows): blip2/stamp/burst/thud/swoosh/bounce/sparkle within +-1 dB; pop & sweep_stamp estimated
LEVEL = dict(blip=-21.5, blip2=-20.5, stamp=-11.5, burst=-9.5, thud_whoosh=-21.4, swoosh=-3.5, soft_whoosh=-24.0, bounce=-18.9, sweep_stamp=-18.0, sparkle=-11.8, pop=-18.0, shimmer=-16.0)
