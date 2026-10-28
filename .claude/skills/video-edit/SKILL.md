---
name: video-edit
description: Re-edits the user's Bengali talking-head + b-roll footage in the exact style of a reference Reels/TikTok/Shorts video - captions and their animation, motion graphics, transitions, background-keyed graphics, light leaks, SFX/ASMR placement, music and calibrated sound levels - using Python (Pillow + numpy) and ffmpeg only. Use when the user sends a reference video plus footage and asks to edit it "ei rokom", "same kore dao", "reference er moto", "same style", or asks for animated Bengali captions, motion graphics or sound design that should match a reference.
---

# Video edit in the style of a reference

The proven pipeline lives in `video-pipeline/` (repo root). Ten real edits were made with it (`video-pipeline/v3` … `v10`, results in `video-pipeline/videos/`). Never start from scratch: copy the closest version and adapt it.

## Hard rules
- **Never use Higgsfield tools** (the user forbade them). No AI video generators: everything is rendered with Python + ffmpeg.
- Bengali text must be shaped by HarfBuzz: Pillow with raqm (checked by `setup_check.py`). Animate per **word** or per grapheme cluster, never per code point.
- Always render **preview frames** first, look at them, fix, and only then render the full video.
- Match the reference's sound by **measuring** it (see `references/sound.md`); put no SFX where the reference has none.
- Talk to the user in Bengali; keep it short and say honestly what does not match yet.

## Commands (Windows: `python`; macOS/Linux: `python3`)
Run from the repo root. Paths with spaces need quotes.

## Workflow - copy this checklist and tick it off
```
- [ ] 0. Setup checked (first time on this computer)
- [ ] 1. Project folder created, inputs copied
- [ ] 2. Footage prepared (frames, mattes, track.json)
- [ ] 3. Word timings (words.json)
- [ ] 4. Reference analysed -> style.md
- [ ] 5. Graphics composed, previews approved, full render
- [ ] 6. Sound: cues, mix, calibrated against the reference
- [ ] 7. Muxed, overview made, delivered, style saved
```

**0. Setup.** `python .claude/skills/video-edit/scripts/setup_check.py` - installs missing pip packages, downloads the u2net model into `video-pipeline/models/`, checks ffmpeg and Bengali shaping. Fix every `FIX` line before going on (Windows help: `references/pitfalls.md`). Add `--birefnet` when hair/edge quality matters (graphics *behind* the person, like v8).

**1. Project.** Create `video-pipeline/<name>/` (same level as `v10/`, so all `../` paths of the templates keep working). Put `footage.mp4`, `ref.mp4` and any voice / SRT / transcript there. Big intermediates go in `video-pipeline/<name>/work/` (git-ignored).

**2. Prepare footage.**
`python .claude/skills/video-edit/scripts/prepare_footage.py video-pipeline/<name>/footage.mp4 video-pipeline/<name>/work`
-> `work/src/` frames (25 fps, 720x1280), `work/matte/` person mattes, `work/track.json` (head position per frame + shot list, `T` = talking head, `B` = b-roll). Check the printed shot list against the footage. ~0.7 s per frame on a 4-core CPU.

**3. Word timings** -> `work/words.json`, a list of `{"w": word, "t": start_s, "e": end_s}`.
- If the user gives a transcript / SRT / voice text: adapt `video-pipeline/full/aud/align.py` (trusted segment starts + pause detection; no ASR needed). This is the most accurate route for Bengali.
- Otherwise ASR: stock Whisper is poor on Bengali (~70 % WER); use a Bengali fine-tuned Whisper with `stable-ts` and ask the user to check the words.

**4. Analyse the reference.**
- `python .claude/skills/video-edit/scripts/ref_sheet.py video-pipeline/<name>/ref.mp4 video-pipeline/<name>/work/ref --fps 2 --window 30` (overview), then `--fps 10 --window 3` (or `--fps 30`) to study how each element enters/exits. Look at every sheet.
- `python .claude/skills/video-edit/scripts/ref_audio.py video-pipeline/<name>/ref.mp4 video-pipeline/<name>/work/refaud` - band table + spectrogram; mark every SFX (time, type, band, mid vs side).
- Measure colours (pixel sampling), font look (compare candidate fonts by rendering them next to a crop), timings in frames.
- Write `video-pipeline/<name>/style.md`: layout, fonts, colours, each animation (duration, easing, order), transitions, and the sound grammar (which event gets which sound). Then pick the closest template from `references/styles.md`.

**5. Compose.** Copy the template's `compose_vN.py` (+ `icons/` if it has one) into the project and rename it. Keep its helpers; replace the timeline tables (texts, times via `wt("word")`) with content that fits **this** footage's topic. Then:
`python compose_<name>.py work/src [work/matte] work/track.json work/words.json [extra args as in the template] out.mp4 --preview 1.0,4.2,8.8`
Look at the preview PNGs (make a grid with `video-pipeline/v10/sheet.py`), compare with the reference sheets, fix, repeat. Then render without `--preview` (writes `out.mp4` and `out_cues.json`).

**6. Sound.** Copy the template's `sfx*.py`, `mix_*.py`, `calib*.py`, `level*.json`. Synthesize the sounds the reference uses, emit cues from the compose script, mix, and run the calibration loop until every class is within ±0.5 dB of the reference (`references/sound.md`).

**7. Deliver.**
`ffmpeg -i out.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart final.mp4`
Make an overview grid of ~15 frames, check it, send `final.mp4` + grid, and summarise in Bengali: what was copied, the sound grammar learned, calibration numbers, and honest gaps. Keep `style.md` so the user can later say "use the <name> style again".

## References
- `references/styles.md` - the 8 styles already built, what each contains, which script to start from.
- `references/sound.md` - how to analyse a reference's sound, level units, the calibration loop, SFX grammar learned so far.
- `references/pitfalls.md` - Bengali text, mattes, compositing order, Windows notes, licences.
