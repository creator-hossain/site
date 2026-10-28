# Sound design: learn it from the reference, then calibrate

## 1. Find the SFX
Run `scripts/ref_audio.py`. Then:
- **L/R correlation** low (< 0.5): the SFX are wide and sit in the **side** channel while the voice stays in the mid - analyse the side channel (v4-v8). High (~0.9+): the mix is near mono; look for SFX in bands the voice does not use (sub 28-80 Hz, air 6-16 kHz) and in voice pauses (v9, v10).
- In the band table, an SFX is a jump in side energy or in sub/air while the voice band is quiet. Read its shape: sub swell = boom/thump, bright short = click/tick/pop, rising band = whoosh/riser, steady tonal notes = music bed (find its key with an FFT peak list).
- Line each SFX up with what happens on screen at that time (contact sheets). That gives the **grammar**: which visual event gets which sound, and which events stay silent.

## 2. Synthesize, place, mix
- Sounds are synthesized in `sfx*.py` (noise bands, swept band-pass, sine bodies, small reverb, Haas widening `_wide`). Copy the closest kit and tweak the shape to match the reference spectrogram.
- The compose script emits cues (`cue("pop", t)`) tied to the same times as the graphics, so sound and picture stay in sync.
- `mix_*.py` sets each sound by its peak (beds by their median) relative to the voice, adds a look-ahead limiter, writes the WAV.

## 3. Calibrate (the step that makes it sound "the same")
- Unit everywhere: **dB relative to the voice p90 10 ms RMS of the mid channel**. This makes the reference and our footage comparable even though the voices differ.
- `calib*.py` measures each sound class in fixed windows of the reference and of our mix (side or band-limited envelopes), prints `REF / MINE / adj`. Add `0.9 x adj` to `level*.json`, re-mix, re-measure. 3-4 rounds bring every class within ±0.5 dB.
- If a class cannot be measured (masked by the voice), measure prominence instead (v6 `tickprom.py`) or keep it faint and say so.

## Grammar learned so far (use as a starting guess, always confirm on the new reference)
- Graphic enters with motion -> whoosh/swoosh (low-heavy for big panels, airy for small).
- Box / label / pill pops -> short pop, tick or click, faint (−15 to −40 dB).
- Big reveal or world change -> sub boom or swell (often the loudest SFX, can be above the voice peak).
- Typed text -> one soft tick per word or grapheme cluster.
- Light flashes / bursts / leaks -> often **silent** (v7) or a bright noise burst just before (v9).
- Music bed when present is quiet: about −28 to −37 dB vs the voice.
- Beds (wind/water ambience) only under intro graphics, not the whole video.
