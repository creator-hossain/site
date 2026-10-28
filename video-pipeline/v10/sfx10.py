# -*- coding: utf-8 -*-
"""SFX kit for reference #10 (SFX sit wider than the voice; L/R corr 0.92).
  impact   - red alert: transient + bass drop (pitch falls) + short noise
  swish    - speech bubble pops: short airy swish
  pop      - labels / pills: cartoon pop (quick rising blip)
  ding     - crown: bright rising 'bling' (stacked rising blips)
  lowwhoosh- info card / subtitle band: low rumbling whoosh (mostly sub)
  swell    - icon tiles: broadband swell whoosh (~0.45 s)
  tick     - scene cut: click
  count    - counter: fast tiny ticks
  music    - light bed: E - D - A - E, plucked arpeggio + bass + soft pad
"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v4"))
from sfx import SR, _t, _band, _lp, _hp, _st, _norm, _tv_band, _verb, _wide, peak_db
def _n(n, seed): return np.random.default_rng(seed).standard_normal(n)
def dec(x, seed=0): return _st(x, x)

def impact():
    t = _t(0.9); f = 40 + 75 * np.exp(-t / 0.18); ph = 2 * np.pi * np.cumsum(f) / SR
    b = np.sin(ph) * np.exp(-t / 0.35); b2 = np.sin(ph + 2.2) * np.exp(-t / 0.35)      # wide like the reference
    l = b + _band(_n(len(t), 1), 200, 6000) * np.exp(-t / 0.05) * 0.5 + _hp(_n(len(t), 2), 3000) * np.exp(-t / 0.006) * 0.5
    r = b2 + _band(_n(len(t), 3), 200, 6000) * np.exp(-t / 0.05) * 0.5 + _hp(_n(len(t), 4), 3000) * np.exp(-t / 0.006) * 0.5
    return _verb(_st(l, r), 0.6, 0.15)
def swish():
    d = 0.22; t = _t(d); p = t / d; env = np.sin(np.pi * p) ** 2
    cen = 1500 * (7000 / 1500) ** p
    return _st(_norm(_tv_band(_n(len(t), 5), cen, 1.0)) * env, _norm(_tv_band(_n(len(t), 6), cen, 1.0)) * env)
def pop():
    t = _t(0.14); f = 520 + 900 * (1 - np.exp(-t / 0.03)); env = (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env + _hp(_n(len(t), 7), 3000) * np.exp(-t / 0.003) * 0.3
    return _wide(_st(x, x), 9.0)
def ding():
    out = np.zeros(int(0.7 * SR))
    for k, f0 in enumerate((880, 1175, 1568, 2093)):
        t = _t(0.5); env = (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.18)
        x = (np.sin(2 * np.pi * f0 * t) + 0.4 * np.sin(2 * np.pi * f0 * 2 * t)) * env; i = int(k * 0.045 * SR); out[i:i + len(x)] += x[:len(out) - i] * (0.7 + 0.1 * k)
    return _verb(_wide(_st(out, out), 9.0), 0.8, 0.2)
def lowwhoosh():
    d = 0.6; t = _t(d); p = t / d; env = np.where(p < 0.45, (p / 0.45) ** 1.5, np.exp(-(p - 0.45) / 0.18))
    def ch(s): return _norm(_lp(_n(len(t), s), 380)) * env + np.sin(2 * np.pi * 52 * t) * env * 0.6
    return _st(ch(8), ch(9))
def swell():
    d = 0.48; t = _t(d); p = t / d; env = np.where(p < 0.6, (p / 0.6) ** 2, np.exp(-(p - 0.6) / 0.12))
    cen = 400 * (5000 / 400) ** np.clip(p / 0.6, 0, 1)
    return _st(_norm(_tv_band(_n(len(t), 10), cen, 0.6)) * env, _norm(_tv_band(_n(len(t), 11), cen, 0.6)) * env)
def tick():
    t = _t(0.03); e = np.exp(-t / 0.003); return _st(_hp(_n(len(t), 12), 2500) * e, _hp(_n(len(t), 13), 2500) * e)
def count():
    out = np.zeros(int(0.8 * SR)); tt = 0.0; k = 0
    while tt < 0.7:
        t = _t(0.02); x = _band(_n(len(t), 20 + k), 3000, 9000) * np.exp(-t / 0.002); i = int(tt * SR); out[i:i + len(x)] += x; tt += 0.03 + 0.06 * (tt / 0.7) ** 2; k += 1
    return _st(out, out)
def music(dur):
    n = int((dur + 2) * SR); out = np.zeros((n, 2)); hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(40, (64, 68, 71)), (38, (62, 66, 69)), (45, (61, 64, 69)), (40, (64, 68, 71))]   # E D A E
    bar = 2.0
    for k, t0 in enumerate(np.arange(0, dur + 2, bar)):
        b, ch = prog[k % 4]; a = int(t0 * SR); e = min(n, int((t0 + bar + 0.5) * SR)); ts = np.arange(e - a) / SR
        env = np.clip(ts / 0.02, 0, 1) * np.exp(-ts / 1.2) * np.clip((bar + 0.5 - ts) / 0.5, 0, 1)
        out[a:e] += (np.sin(2 * np.pi * hz(b) * ts) * env * 0.8)[:, None]
        pad = np.clip(ts / 0.4, 0, 1) * np.clip((bar + 0.5 - ts) / 0.5, 0, 1) * 0.08
        for m in ch: out[a:e, 0] += np.sin(2 * np.pi * hz(m) * ts) * pad; out[a:e, 1] += np.sin(2 * np.pi * hz(m) * 1.003 * ts + 1) * pad
        for j, m in enumerate([ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12] * 2):
            ts2 = ts - j * bar / 8; e2 = (ts2 > 0) * np.clip(ts2 / 0.004, 0, 1) * np.exp(-np.clip(ts2, 0, None) / 0.25)
            pl = (np.sin(2 * np.pi * hz(m) * ts) + 0.3 * np.sin(4 * np.pi * hz(m) * ts)) * e2 * 0.14
            out[a:e, j % 2] += pl; out[a:e, 1 - j % 2] += pl * 0.6
    out = _verb(out, 1.0, 0.25); tt = np.arange(n) / SR; fade = np.clip(tt / 0.3, 0, 1) * np.clip((dur - tt) / 0.6, 0, 1)
    return out[:int(dur * SR)] * fade[:int(dur * SR), None]
def _fade(fn):
    def g(*a, **k):
        x = fn(*a, **k); m_ = min(len(x), int(0.008 * SR)); x = x.copy(); x[-m_:] *= np.linspace(1, 0, m_)[:, None]; return x
    return g
KIT = {k: _fade(v) for k, v in dict(impact=impact, swish=swish, pop=pop, ding=ding, lowwhoosh=lowwhoosh, swell=swell, tick=tick, count=count, music=music).items()}
