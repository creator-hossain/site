# Styles already built (start from the closest one)

All outputs are in `video-pipeline/videos/`. Each folder has `compose_vN.py` (graphics), `sfx*.py` (synthesized sounds), `mix_vN.py`, `calib*.py`, `level*.json` (calibrated levels, dB vs voice p90).

| Folder | Look | Key techniques (function names in the script) | Sound |
|---|---|---|---|
| `full/`, `final/`, `v2/`, `v3/` | First caption + motion-graphics edits, Anek Bangla + Inter | libass `.ass` captions (`final/engine.py`), kinetic captions | none / music only |
| `v4/` | Punchy explainer: big captions, panels, counters, icons | caption pops, panel slides, count-up | the base SFX kit `sfx.py`: boom on cuts, riser before big cuts, swoosh on panels, chime on bullets, swish on big words, counter ticks, shimmer, thump on label pills, pop on icons |
| `v5/` | Pink stamped boxes, energy-burst transitions, bouncing logo card | stamp boxes, burst transition, bounce | harmonic blips on captions, stamp boom-boop, burst whoosh, bounce blips, sparkle on brand |
| `v6/` | Typewriter captions (Baloo Da 2) | per-grapheme-cluster typing | one soft tick per typed cluster, levels set by prominence (`tickprom.py`) |
| `v7/` | Airy cool grade, **giant pale words and a picture behind the person**, sky turns blue, gradient bar top-right, teal labels + diagonal shine, logo bug swap; 4:5 output | `flare_wipe`, `light_band`, `sky_tint`, `shine`, `burst`, `logo_bug`; person re-composited in front of graphics | wide wind/water ambience bed under the intro, swooshes on reveals, faint clicks on labels, light burst silent |
| `v8/` | Person **keyed onto an illustrated sky world** (BiRefNet mattes), glass wipe in/out, hue cycle on the person, big Poppins word + pill, 3D map / swatch / badge slide in, pale + navy caption boxes, orange light leak, glow-blur jump cut | `glass`, `hue_tint`, `world_layer`, `draw_box`, `leak`, `glow_blur` | C#m music bed, deep sub boom on world in/out, swell on element slide-in, tick on box pop, outro swell |
| `v9/` | Dark talk-show grade, **frosted glass list boxes** with line icons and typed techno caps (Exo 2), zoom-cut on every pop, pink-orange leak, falling objects (car keys), dip to black, design-tool selection lower third with cursor | `frosted`, `draw_list`, `punch`, `draw_rain`, `draw_lt`, `leak` | sub thump + click per box, bright burst before leak, hit on cut, key jingle during rain, whoosh into black, long boom + typing on lower third, dark music |
| `v10/` | **Podcast band layout** (sharp band + blurred fill), many pop-ins: title blur-in, speech bubble, highlighter bar + warning triangles, crown + glowing line, navy info card with gold stars and typed text, red-navy subtitle band with pills, counter with an icon digit, red-alert monochrome, icon tile row | `compose_base`, `title`, `bubble`, `highlighter`, `crown_seq`, `card`, `sub_band`, `counter`, `tiles` | bass-drop impact on red alert, swish on bubble, cartoon pops on labels/pills, bling on crown, low whoosh on card/band, swell on tiles, tick on cuts, count ticks, light E-D-A music |

## Reusable building blocks
- Person in front of graphics: draw graphics, then `img.alpha_composite(person)` where `person = frame with matte as alpha` (v7, v8).
- Bad matte fallback: if the face point is not in the matte, draw a soft body mask from the head track (v7 `render`, v10).
- Camera: `cam()` crops around the tracked head with slow drift; `punch()` (v9) for zoom cuts.
- Easing: `eo3` (ease-out cubic), `eback` (overshoot pop), `eio` (ease in-out). Durations are in seconds; measure them from 10-30 fps reference sheets.
- Captions timed to words: `wt("word", n)` = start time of the n-th occurrence in `words.json`.
