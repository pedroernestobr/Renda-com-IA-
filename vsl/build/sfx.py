"""Efeitos sonoros e trilha sintetizados (sem samples de terceiros).

Gera WAVs 48 kHz em vsl/build/sfx/: whoosh, hit (impacto grave), click,
glitch, riser, pop, ding e uma trilha eletrônica escura em loop.
"""
import os, wave
import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(__file__), "sfx")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, x, stereo_width=0.0):
    x = np.asarray(x, dtype=np.float64)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak * 0.89
    if stereo_width:
        d = int(SR * 0.012)
        l = x
        r = np.concatenate([np.zeros(d), x[:-d]]) * (1 - stereo_width) + x * stereo_width
        st = np.stack([l, r], axis=1)
    else:
        st = np.stack([x, x], axis=1)
    pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def t(sec):
    return np.arange(int(SR * sec)) / SR


def lowpass(x, alpha):
    """One-pole low-pass; alpha may be an array (time-varying cutoff)."""
    y = np.empty_like(x); acc = 0.0
    a = np.broadcast_to(alpha, x.shape)
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc); y[i] = acc
    return y


def env(n, a, d, curve=3.0):
    e = np.ones(n)
    na = max(1, int(SR * a)); nd = max(1, int(SR * d))
    e[:na] = np.linspace(0, 1, na)
    tail = np.linspace(1, 0, min(nd, n - na)) ** curve
    e[na:na + len(tail)] = tail
    e[na + len(tail):] = 0
    return e


# whoosh: noise with a rising-then-falling band
tt = t(0.7)
n = rng.standard_normal(len(tt))
sweep = 0.02 + 0.5 * np.sin(np.pi * tt / tt[-1]) ** 2
w = lowpass(n, sweep) - lowpass(n, sweep * 0.25)
save("whoosh", w * env(len(tt), 0.35, 0.35, 1.5), stereo_width=0.6)

# hit: sub drop + noise transient
tt = t(1.6)
f = 110 * np.exp(-tt * 3.5) + 38
sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2)
tr = lowpass(rng.standard_normal(len(tt)), 0.25) * np.exp(-tt * 28)
save("hit", sub + 0.5 * tr)

# click: short UI tick
tt = t(0.06)
save("click", np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 140) + 0.3 * rng.standard_normal(len(tt)) * np.exp(-tt * 300))

# pop: soft bubble for checks
tt = t(0.18)
f = 520 + 900 * np.exp(-tt * 40)
save("pop", np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 22))

# ding: bright bell for price
tt = t(1.4)
bell = sum(a * np.sin(2 * np.pi * fr * tt) * np.exp(-tt * dk) for fr, a, dk in [(1318, 1, 3), (2637, .5, 5), (3951, .25, 7), (659, .4, 2.5)])
save("ding", bell, stereo_width=0.4)

# glitch: bit-crushed noise bursts
tt = t(0.45)
g = rng.standard_normal(len(tt))
g = np.round(g * 3) / 3
gate = (np.sin(2 * np.pi * 38 * tt) > 0.2).astype(float)
sq = np.sign(np.sin(2 * np.pi * 180 * tt)) * 0.4
save("glitch", (g * 0.6 + sq) * gate * env(len(tt), 0.005, 0.44, 1.2), stereo_width=0.5)

# riser: 1.8 s rising noise + tone
tt = t(1.8)
n = rng.standard_normal(len(tt))
a = 0.01 + 0.4 * (tt / tt[-1]) ** 2
r = lowpass(n, a) * (tt / tt[-1]) ** 2
tone = np.sin(2 * np.pi * np.cumsum(200 + 700 * (tt / tt[-1]) ** 2) / SR) * 0.25 * (tt / tt[-1]) ** 3
save("riser", r + tone, stereo_width=0.5)

# typing: 2.2 s of key taps
tt = t(2.2); k = np.zeros(len(tt))
pos = 0.0
while pos < 2.1:
    i = int(pos * SR); L = int(0.03 * SR)
    seg = rng.standard_normal(L) * np.exp(-np.arange(L) / SR * 180)
    k[i:i + L] += lowpass(seg, 0.5) * rng.uniform(0.5, 1)
    pos += rng.uniform(0.06, 0.13)
save("typing", k)

# music: dark minimal electronic bed, 120 bpm, 16 s loop
BPM = 120; beat = 60 / BPM; L = 32 * beat
tt = t(L); mus = np.zeros(len(tt))
notes = [36, 36, 39, 34]  # C2 C2 Eb2 Bb1 (one bar each, x2)
for bar in range(8):
    midi = notes[bar % 4]; fr = 440 * 2 ** ((midi - 69) / 12)
    for st in range(8):  # eighth-note bass pulses
        s0 = int((bar * 4 + st * 0.5) * beat * SR); ln = int(0.45 * beat * SR)
        x = np.arange(ln) / SR
        saw = 2 * ((fr * x) % 1) - 1
        mus[s0:s0 + ln] += lowpass(saw, 0.06) * np.exp(-x * 7) * 0.55
for b in range(32):  # kick on every beat, hat offbeat
    s0 = int(b * beat * SR); x = t(0.35)
    f = 120 * np.exp(-x * 30) + 45
    kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9)
    mus[s0:s0 + len(x)] += kick * 0.9
    h0 = int((b + 0.5) * beat * SR); xh = t(0.05)
    hat = rng.standard_normal(len(xh)); hat = hat - lowpass(hat, 0.3)
    mus[h0:h0 + len(xh)] += hat * np.exp(-xh * 90) * 0.18
pad = sum(np.sin(2 * np.pi * 440 * 2 ** ((m - 69) / 12) * tt + ph) for m, ph in [(60, 0), (63, 1), (67, 2)])
mus += lowpass(pad, 0.02) * 0.08 * (0.6 + 0.4 * np.sin(2 * np.pi * tt / L))
save("music", mus, stereo_width=0.7)
print("ok", sorted(os.listdir(OUT)))
