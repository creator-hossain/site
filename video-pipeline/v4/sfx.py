# -*- coding: utf-8 -*-
"""Synthesised SFX kit, modelled on the sounds measured in reference #4.

Every sound is stereo-wide (decorrelated L/R) like the reference, where all
effects sit in the side channel while the voice stays mono in the centre.
"""
import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(11)

def _t(d): return np.arange(int(d * SR)) / SR
def _noise(n): return RNG.standard_normal(n)
def _band(x, lo, hi, order=4):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos"); return signal.sosfilt(sos, x)
def _lp(x, f, order=4):
    sos = signal.butter(order, f, btype="low", fs=SR, output="sos"); return signal.sosfilt(sos, x)
def _hp(x, f, order=4):
    sos = signal.butter(order, f, btype="high", fs=SR, output="sos"); return signal.sosfilt(sos, x)
def _st(l, r=None): return np.stack([l, l if r is None else r], 1)
def _norm(x): return x / (np.max(np.abs(x)) + 1e-9)

def _tv_band(x, centers, q=1.4):
    """time-varying band-pass: centre frequency follows `centers` (one value per sample)."""
    n = 2048; hop = 512; win = np.hanning(n)
    out = np.zeros(len(x) + n); wsum = np.zeros(len(x) + n)
    f = np.fft.rfftfreq(n, 1 / SR)
    xp = np.concatenate([x, np.zeros(n)])
    for s in range(0, len(x), hop):
        fr = xp[s:s + n] * win; c = centers[min(s + n // 2, len(centers) - 1)]
        g = np.exp(-0.5 * (np.log2((f + 1) / c) * q) ** 2)
        out[s:s + n] += np.fft.irfft(np.fft.rfft(fr) * g) * win; wsum[s:s + n] += win ** 2
    return out[:len(x)] / np.maximum(wsum[:len(x)], 1e-6)

def _verb(x, t60=0.6, mix=0.18):
    """small stereo room: convolve with decaying decorrelated noise."""
    n = int(t60 * SR); env = np.exp(-6.9 * _t(t60) / t60)
    irl, irr = _lp(_noise(n), 6000) * env, _lp(_noise(n), 6000) * env
    irl /= np.sqrt((irl ** 2).sum()); irr /= np.sqrt((irr ** 2).sum())
    m = x.mean(1)
    wl = signal.fftconvolve(m, irl)[:len(m)]; wr = signal.fftconvolve(m, irr)[:len(m)]
    return x * (1 - mix) + _st(wl, wr) * mix * 0.6

def _pad(x, tail=0.5): return np.concatenate([x, np.zeros((int(tail * SR), 2))])

# ------------------------------------------------------------------ sounds
def swish(d=0.34):
    """big caption word: airy high swish (4-11 kHz) + faint 110 Hz body."""
    t = _t(d); env = (1 - np.exp(-t / 0.012)) * np.exp(-t / (d * 0.32))
    l, r = _band(_noise(len(t)), 3500, 11500) * env, _band(_noise(len(t)), 3500, 11500) * env
    body = np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.05) * 0.25
    return _st(_norm(l) + body, _norm(r) + body)

def tick():
    """small-line word: very short dry click."""
    t = _t(0.03); env = np.exp(-t / 0.006)
    return _st(_hp(_noise(len(t)), 4500) * env, _hp(_noise(len(t)), 4500) * env)

def pop():
    """icon / tile pop: two-step bloop (~650 -> ~1300 Hz) over a short 100 Hz body (ref #17/#18)."""
    t = _t(0.26)
    f = np.where(t < 0.07, 650.0, 1300.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = (1 - np.exp(-t / 0.002)) * np.where(t < 0.07, 1.0, np.exp(-(t - 0.07) / 0.06))
    tone = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * env
    body = np.sin(2 * np.pi * 100 * t) * np.exp(-t / 0.09) * 0.6
    clk = _hp(_noise(len(t)), 6000) * np.exp(-t / 0.004) * 0.25
    x = _st(tone + body + clk, tone * 0.92 + body + clk)
    return _verb(_pad(x, 0.25), 0.35, 0.15)

def chime(f0=700.0):
    """bullet line: noisy pluck attack + a two-note fifth (f0, 1.5 f0) ringing ~1 s with slight flutter."""
    t = _t(1.2); l = np.zeros_like(t); r = np.zeros_like(t)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 7.5 * t)
    for k, a, dec in ((1.0, 1.0, 0.6), (1.5, 0.8, 0.5), (2.0, 0.25, 0.25), (3.0, 0.12, 0.15)):
        l += a * np.sin(2 * np.pi * f0 * k * t) * np.exp(-t / dec)
        r += a * np.sin(2 * np.pi * f0 * k * 1.003 * t + 0.4) * np.exp(-t / dec)
    atk = 1 - np.exp(-t / 0.004)
    pl = _band(_noise(len(t)), 200, 4000) * np.exp(-t / 0.05) * 0.9
    pr = _band(_noise(len(t)), 200, 4000) * np.exp(-t / 0.05) * 0.9
    x = _st(l * atk * trem * 0.6 + pl, r * atk * trem * 0.6 + pr)
    return _verb(_pad(x, 0.4), 0.8, 0.22)

def swoosh(d=1.1, peak=0.55, lo=250, hi=2200):
    """panel / phone slide: low-heavy broadband whoosh with flutter, sweeps up then down, pans L->R."""
    t = _t(d); p = t / d
    env = np.where(p < peak, (p / peak) ** 1.6, np.exp(-(p - peak) / (1 - peak) * 3.0))
    flut = 1 + 0.35 * _lp(_noise(len(t)), 30) / (np.std(_lp(_noise(len(t)), 30)) + 1e-9) * 0.3
    cen = np.where(p < peak, lo * (hi / lo) ** (p / peak), hi * (0.35) ** ((p - peak) / (1 - peak)))
    def ch():
        sweep = _tv_band(_noise(len(t)), cen, 0.55)
        rum = _lp(_noise(len(t)), 300) * 1.6
        return _norm(sweep) + _norm(rum) * 0.8
    l, r = ch() * env * flut, ch() * env * flut
    pan = np.clip(p * 1.4 - 0.2, 0, 1)
    l, r = _lp(l, 3800), _lp(r, 3800)                 # ref: almost nothing above ~4 kHz
    return _verb(_st(_norm(l * (1 - 0.4 * pan)), _norm(r * (0.6 + 0.4 * pan))), 0.5, 0.12)

def thump():
    """label pill wipe: soft sub thump (55-70 Hz, 0.35 s) + faint air on top."""
    t = _t(0.42); f = 72 - 18 * (1 - np.exp(-t / 0.08))
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.13)
    b = np.tanh(1.6 * np.sin(ph) * env)
    air = _band(_noise(len(t)), 7000, 12000) * np.exp(-t / 0.02) * 0.06
    return _st(b + air, b + air * 0.9)

def riser(d=0.75):
    """before a big cut: broadband noise whose filter + level climb (no tonal sweep, like the ref)."""
    t = _t(d); p = t / d
    env = p ** 2.0
    cen = 250 * (6000 / 250) ** p
    def ch(): return _lp(_norm(_tv_band(_noise(len(t)), cen, 0.5)) + _norm(_lp(_noise(len(t)), 400)) * 0.6 * p, 4500)
    return _st(ch() * env, ch() * env)

def boom():
    """cut impact: low-heavy noise burst with rumble tail + a little sub (ref #26 / #76)."""
    t = _t(1.1)
    def ch():
        n = _lp(_noise(len(t)), 1300) * np.exp(-t / 0.22)
        rum = _lp(_noise(len(t)), 160) * np.exp(-t / 0.45) * 2.2
        return _norm(n) + _norm(rum) * 0.9
    f = 40 + 50 * np.exp(-t / 0.05)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - np.exp(-t / 0.003)) * np.exp(-t / 0.3) * 0.5
    x = _st(np.tanh(ch() * 0.8 + sub), np.tanh(ch() * 0.8 + sub))
    return _verb(x, 0.9, 0.18)

def soft_whoosh(d=0.5):
    """small transitions (blur / flash): short airy whoosh."""
    return swoosh(d, peak=0.45, lo=800, hi=5000)

def type_tick():
    """typewriter text in the white-card scene: soft keyboard tap."""
    t = _t(0.05); env = np.exp(-t / 0.01)
    k = _band(_noise(len(t)), 1500, 5000) * env + np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.006) * 0.3
    return _st(k, k * 0.9)

def counter(d=1.0, rate=22):
    """count-up: rapid soft ticks that slow down with the number (ease-out)."""
    out = np.zeros((int((d + 0.1) * SR), 2)); tk = tick()
    p = 0.0
    while True:
        # time of next tick follows the ease-in-out count curve
        tt = d * (np.arccos(1 - 2 * min(p, 1)) / np.pi); i = int(tt * SR)
        if p > 1 or i + len(tk) >= len(out): break
        out[i:i + len(tk)] += tk * (0.8 + 0.2 * RNG.random())
        p += 1 / (rate * d)
    return out

def shimmer():
    """BOOK-NOW sheen: quick bright arpeggio."""
    out = np.zeros((int(1.0 * SR), 2))
    for k, f in enumerate((1318.5, 1760.0, 2637.0)):
        c = chime(f) * 0.5; i = int(k * 0.06 * SR); n = min(len(c), len(out) - i); out[i:i + n] += c[:n]
    return out

def _wide(x, ms=11.0):
    """reference SFX are stereo-wide (they live in the side channel): Haas-delay the right side."""
    d = int(ms / 1000 * SR); r = np.concatenate([np.zeros(d), x[:, 1]])[:len(x)]
    return np.stack([x[:, 0], 0.55 * x[:, 1] + 0.45 * r], 1) if d < len(x) else x

WIDE = {"pop", "thump", "chime", "tick", "type_tick", "shimmer", "counter"}

def _fade(fn):
    def g(*a, **k):
        x = fn(*a, **k); n = min(len(x), int(0.012 * SR))
        x = x.copy(); x[-n:] *= np.linspace(1, 0, n)[:, None]; return x
    return g

KIT = dict(swish=swish, tick=tick, pop=pop, chime=chime, swoosh=swoosh, thump=thump,
           riser=riser, boom=boom, soft_whoosh=soft_whoosh, type_tick=type_tick, counter=counter, shimmer=shimmer)
KIT = {k: _fade(v) for k, v in KIT.items()}
KIT = {k: ((lambda f: (lambda *a, **kw: _wide(f(*a, **kw))))(v) if k in WIDE else v) for k, v in KIT.items()}

# ------------------------------------------------------------------ levels learned from the reference
# peak 10 ms RMS of each sound class, dB relative to the voice's p90 10 ms RMS.
# Calibrated in a measure->adjust loop against reference #4 (side channel, 0.35 s window): all within +-0.6 dB.
LEVEL = dict(boom=-7.8, riser=0.8, swoosh=-10.5, soft_whoosh=-12.0, chime=-8.6, swish=-24.4, counter=-14.0, shimmer=-14.0, thump=-15.0, pop=-27.4, type_tick=-30.0, tick=-31.4)

def peak_db(x):
    m = x.mean(1); n = len(m) // 480
    if n == 0: return -120.0
    r = np.sqrt((m[:n * 480].reshape(n, 480) ** 2).mean(1)); return 20 * np.log10(r.max() + 1e-12)
