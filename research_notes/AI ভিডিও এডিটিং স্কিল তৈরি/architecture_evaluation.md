# Architecture and Evaluation for "Copy This Reference Video's Edit Style" (style spec, auto-extraction, metrics, Bengali text, compute/cost)

Research date: 2026-10-28. Method: web search plus direct fetches of GitHub/primary repos. Note for the report writer: several primary sites were **not reachable from this research sandbox** (modal.com, support.google.com [YouTube encoding page], remotion.dev, shotstack.io, trac.ffmpeg.org), so some figures below come from search-result snippets of those pages or from third-party aggregators. Those are flagged where it matters.

---

## 1. Representation: which machine-readable format should an LLM write as the "style spec"?

### Takeaway
Use a **custom, schema-validated JSON "style spec"** (Zod/JSON-Schema) that an LLM writes, and that compiles to a **Remotion composition** (or similar JSON-to-video renderer). Use OpenTimelineIO only as an export/hand-off format to NLEs (Premiere/Resolve), not as the primary spec. OTIO only describes cuts and media references, and Remotion itself says a Remotion project cannot be exported to OTIO deterministically. Caption animation (per-word timing, easing, entry/exit) and SFX rules are not first-class in OTIO/EDL/FCPXML. Write them as your own typed fields.

### Cited Findings
**OpenTimelineIO (OTIO)**
- OTIO is "an interchange format and API for editorial cut information". It records the order and length of cuts and references to external media, and it is explicitly "not … a container format for media". The core is C++ with Python bindings and a plugin system. Native files are `.otio`, `.otioz` and `.otiod`. — [OTIO GitHub README](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)
- Adapters (Final Cut Pro XML, AAF, CMX 3600 EDL and others) were moved out of core. After v0.16 the main PyPI package ships only the core and native formats, and full adapter support needs the separate `OpenTimelineIO-Plugins` package. — [OTIO GitHub README](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)
- Remotion's docs say a Remotion project **cannot be deterministically exported to OTIO**. Remotion instead offers an *agent skill* that has an AI agent analyze the project and recreate an `.otio` file, and anything OTIO cannot represent is **prerendered** in Remotion. The docs say OTIO is a documented JSON format that DaVinci Resolve and Adobe Premiere 25.6+ can import. — [Remotion docs: export-opentimeline](https://www.remotion.dev/docs/export-opentimeline) (seen through a search snippet; the site could not be fetched directly)

**LLM → JSON timeline systems (existing examples)**
- `@json-render/remotion` (vercel-labs/json-render) turns a JSON spec into a Remotion composition. The timeline JSON holds composition metadata, enabled tracks, clip component names, props, `from` frame and `durationInFrames`. It ships standard components (TitleCard, LowerThird), lets you add custom clips with **Zod schemas**, and previews with `@remotion/player`. It is packaged as an agent "skill". — [tessl.io registry: json-render/remotion](https://tessl.io/registry/skills/github/vercel-labs/json-render/remotion); [skills.cat listing](https://skills.cat/skills/vercel-labs/json-render/json-render-remotion)
- A community prompt-to-video Remotion template has the LLM produce **structured output validated with Zod**. The timeline has four parallel tracks (background images, text, audio, short title), and transitions are limited to a small fixed set of types. — [webmonch blog: building prompt-to-video Remotion template](https://webmonch-blog.pages.dev/blog/building-prompt-to-video-remotion-template)
- Creatomate's JSON format, "RenderScript", is POSTed to `/v2/renders`, which returns a render ID, status and output URL. Its text animations are objects with `time`, `duration`, `easing`, `type` (e.g. `text-slide`), `scope`, `split` (e.g. `"line"`), `distance` and `direction`. — [Creatomate: generate videos from JSON via API](https://creatomate.com/blog/how-to-generate-videos-from-json-using-an-api); [Creatomate: JSON-to-video practical examples](https://creatomate.com/blog/json-to-video-practical-examples); [Creatomate quick start](https://creatomate.com/docs/api/quick-start/create-a-video-by-render-script)
- Creatomate has tutorials on auto-transcribing audio into **animated word-by-word captions**. I could not confirm that `split: "word"` exists. — [Creatomate JSON-to-video article](https://creatomate.com/blog/json-to-video-how-to-create-videos-from-json)
- ZapCap offers a separate hosted API for word-by-word animated captions. It is an alternative to building caption animation yourself. — [ZapCap animated captions API](https://zapcap.ai/api/animated-captions/)

**Lottie for motion/caption animation**
- The Lottie text model uses **text animators**. Each animator holds animated properties plus a list of **range selectors** that decide which subset of the text (characters/words) the values apply to. — [Skia Skottie TextAnimator.cpp](https://skia.googlesource.com/skia/+/4a281dc8ee8449040329747ade70dc0ab04b7d27/modules/skottie/src/text/TextAnimator.cpp); [lottie-docs: text](https://lottiefiles.github.io/lottie-docs/text)
- Player support for range selectors is uneven. lottie-android added only partial support (index-based ranges over characters, font-drawn text only, no easing/randomization/range shape, one range per layer). lottie-flutter 3.4.0 added range selectors for color, stroke, stroke width, tracking and opacity. — [lottie-android PR #2518](https://skia.googlesource.com/external/github.com/airbnb/lottie-android/+/71c1622ae3c145e5afaf6bbdd0a2edd274f49864); [lottie (Flutter) changelog](https://pub.dev/packages/lottie/changelog)
- LottieFiles' Lottie Creator added text layers. — [LottieFiles blog](https://lottiefiles.com/blog/working-with-lottie-animations/text-layers-now-in-lottie-creator)

### Inferences
- **Recommended layering** for a single developer working with an AI coding agent:
  1. **Style spec (LLM-authored, render-agnostic JSON)**. This describes *rules*, not absolute timestamps. Example fields:
     - `cut_rhythm`: median and percentile shot length, cut-on-beat probability
     - `zoom_events`: type `punch_in`/`ken_burns`, scale 1.0→1.15, duration_ms, easing as `cubic-bezier(x1,y1,x2,y2)`, trigger such as "on emphasized word"
     - `captions`: font family/weight, size as % of frame height, position (safe zone), max words per line, highlight color, `per_word` entry animation {type: pop/scale/slide, from_scale, duration_ms, easing, stagger_ms}, exit animation, active-word style
     - `color`: LUT path or statistics-transfer params
     - `sfx_rules`: e.g. "whoosh at every hard cut, offset -80 ms, gain -12 dB"; "pop at each caption word-group entry"; library tag or CLAP embedding of the reference SFX
     - `audio`: music ducking dB, target LUFS
  2. **Concrete timeline (deterministic compiler output)**. A script combines the style spec with the new footage's transcript (word timings), beats and shots to produce absolute-frame JSON for Remotion (`from`/`durationInFrames` per clip, as in json-render).
  3. **Export adapters**: OTIO for NLE hand-off (lossy, as Remotion documents), and FFmpeg/ASS as a fallback path.
- Keeping "rules" (style spec) separate from "instances" (timeline) is what lets one reference style transfer to new footage. LLMs are much more reliable at filling a small typed schema than at writing hundreds of absolute timestamps. That reliability claim is my inference, but it matches the Zod-validated designs above.
- Easing is best stored as **cubic-bezier control points** (the CSS/After Effects/Lottie convention), which Remotion's `interpolate`/`Easing.bezier` and Lottie keyframe tangents can both consume. This is an inference; the Remotion API was not verified in this session because remotion.dev was unreachable.
- Prefer Lottie only for *self-contained animated stickers/overlays*. For Bengali captions, keep text in the HTML/Chromium layer (see Section 4), because Lottie players' text-animator support is partial and their complex-script shaping is unverified.

### Gaps
- Could not fetch Shotstack's Edit API docs (shotstack.io unreachable), so its exact JSON schema is not verified here: timeline→tracks→clips with asset/start/length/transition/effect such as `zoomIn`, plus caption/word-timing support.
- No source found comparing FCPXML or MLT XML as LLM-authored formats. No evidence that either is a good LLM target. Both are verbose XML tied to a specific NLE/engine.
- Could not confirm Creatomate's exact per-word caption keyframe syntax.
- No source on how lottie-web specifically handles text range selectors or Bengali shaping.

---

## 2. Extracting the style from a reference automatically

### Takeaway
Use a stack of established tools:
- **Cuts**: TransNetV2, with PySceneDetect as a cheap baseline.
- **Zoom/punch-in and easing curves**: optical flow (RAFT/Farneback) with a robust affine fit per frame, then fit a bezier to the scale-over-time curve.
- **Color**: statistics/histogram transfer, e.g. the `color-matcher` library (GPL-3.0). Mind the license.
- **Typography**: OCR boxes over time for caption timing and position, plus a Bengali-capable font recognizer such as Lipika, since mainstream font-ID tools are Latin-centric.

### Cited Findings
**Cut / shot-boundary detection**
- NVIDIA's Cosmos paper (Table 1) compares the two directly. PySceneDetect scored F1 0.889 (BBC), 0.831 (RAI), 0.718 (SHOT), 0.477 (ClipShots). TransNetV2 scored 0.967, 0.919, 0.821, 0.726. The authors say "end-to-end learning-based approaches (e.g., TransNetV2 and AutoShot) perform much better than methods using hand-crafted features". PySceneDetect thresholds the temporal change of the HSV color histogram. — [Cosmos World Foundation Model Platform, arXiv 2501.03575](https://arxiv.org/pdf/2501.03575)
- TransNetV2 paper. — [arXiv 2008.04838](https://arxiv.org/pdf/2008.04838). A PyTorch port is on PyPI and reports F1 77.9 (ClipShots), 96.2 (BBC Planet Earth) and 93.9 (RAI). — [transnetv2-pytorch on PyPI](https://pypi.org/project/transnetv2-pytorch/)
- PySceneDetect's own benchmark uses TRECVID-SBD conventions. AdaptiveDetector leads its detectors (≈92 on BBC, ≈74 on AutoShot data), and HistogramDetector drops to ≈20 on ClipShots. These scores are not directly comparable with the TransNetV2 numbers. — [scenedetect.com benchmarks](https://www.scenedetect.com/benchmarks/)

**Zoom / punch-in / camera motion from optical flow**
- RAFT outputs a dense per-pixel displacement (u, v). — [MathWorks: dense 3D reconstruction using RAFT](https://jp.mathworks.com/help/vision/ug/dense-3d-reconstruction-from-two-views-using-RAFT-optical-flow.html)
- A standard pipeline is "compute flow → estimate homography/affine → smooth trajectory → warp". — [Codesota: optical flow building block](https://www.codesota.com/building-blocks/optical-flow)
- Patent literature describes estimating camera work from flow at corner points on static objects. Radial expansion about a point is a **zoom-in**, and affine parameters can be computed from those flows. Independently moving objects (e.g. a flag in the wind) corrupt the estimate, so they must be excluded. — [USPTO patent 8810708](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8810708)

**Color grading extraction / transfer**
- `color-matcher` (pip `color-matcher`, latest 0.4.x) provides color transfer "for automatic color-grading of photographs, paintings and film sequences". Methods: Reinhard et al., MKL (Monge-Kantorovich Linearization, Pitié et al.), MVGD (multivariate Gaussian) with histogram matching, and compounds `hm-mvgd-hm` and `hm-mkl-hm`. The authors claim HM-MVGD-HM "outperforms existing methods" (their own benchmark). API: `ColorMatcher().transfer(src=img, ref=ref_img, method='mkl')`. **License: GPL-3.0.** No LUT export is documented, and it works on images/frame folders, not video files. — [color-matcher GitHub](https://github.com/hahnec/color-matcher); [PyPI 0.4.1](https://pypi.org/project/color-matcher/0.4.1)
- The ComfyUI KJNodes "ColorMatch" node wraps the same library with the method list mkl (default), hm, reinhard, mvgd, hm-mvgd-hm and hm-mkl-hm. — [ComfyUI wiki: KJNodes ColorMatch](https://comfyui-wiki.com/en/custom-nodes/ComfyUI-KJNodes/nodes/color-match)

**Typography / font identification**
- Lipika (open-source, by Loopdesk) is an Indic font recognizer covering 13 Indic scripts, including Bengali. It returns font family, weight, an italic flag and a hosted WOFF2 link, and its self-reported accuracy is 0.86 top-1 (validation) and 0.90 on real photos. Its docs say WhatTheFont, Matcherator and Adobe Match Font rely mostly on Latin catalogs, and that conjuncts and matras change glyph shapes by context. — [lipika on PyPI](https://pypi.org/project/lipika/); [Lipika on Hugging Face](https://huggingface.co/loopdesk-ai/lipika)
- Academic Bangla font recognition: a CNN with 96% line-level accuracy across 10 fonts (2019), and VGG-16 transfer learning with 96.23% across 5 fonts. Both are small, controlled datasets. — [Springer 2019](https://link.springer.com/10.1007/978-981-13-7564-4_40); [IEEE 9850765](https://ieeexplore.ieee.org/document/9850765)

### Inferences
- **Practical extraction recipe** (my synthesis from the above):
  1. **Shots**: run TransNetV2, which gives the cut list and the shot-length distribution (the "pace").
  2. **Per-shot motion**:
     - Compute Farneback (cheap, OpenCV) or RAFT (accurate, GPU) flow between consecutive frames.
     - Mask out detected people/text, then RANSAC-fit a similarity/affine transform.
     - Scale = sqrt(|det(A)|). A cumulative scale curve rising from 1.0 to about 1.1–1.3 that is centred on the subject means a punch-in or Ken Burns.
     - A sudden scale jump at a cut with no flow continuity means a "hard punch-in" (a cut to a cropped copy).
     - Normalize the scale curve over its duration to [0,1] and fit a cubic-bezier with least squares. This gives easing parameters that can go straight into the spec.
  3. **Animation timing of overlays**: per-frame absolute difference within the OCR box region finds when captions appear/disappear and how long entry animations last. Running OCR (e.g. PaddleOCR/Tesseract with Bengali data) per frame gives text content, box size and position over time, which yields words per caption chunk, line count and position as a % of frame. Box scale over the first N frames of each word reveals "pop" animations, e.g. 0.8→1.1→1.0 overshoot = back-out easing.
  4. **Color**: estimate per-shot statistics (Lab mean/std, or a 3D histogram) from the reference.
     - Apply them to new footage with `color-matcher`'s `hm-mvgd-hm` or `reinhard`.
     - For a reusable LUT, apply the transfer to a 33³ identity "HALD" image and save the result as a `.cube` file. This is my inference; the library does not document LUT export.
     - **GPL-3.0** means that if you distribute the tool (not just run it as a service), your code may need to be GPL. Consider re-implementing Reinhard (~20 lines) to avoid the GPL.
  5. **Font**: crop caption frames and run Lipika for Bengali. Fall back to manually comparing against a shortlist of the OFL Bengali fonts in Section 4.
- Flow-based easing extraction is only reliable on synthetic (digital) zooms. Real camera moves and subject motion add noise, so smooth the curve (Savitzky-Golay) before fitting.

### Gaps
- No published benchmark of RAFT vs Farneback specifically for *digital zoom/easing curve recovery*. The approach is standard but unvalidated.
- No source found for automatic **LUT estimation** from a single graded reference without a matching ungraded original. Statistics transfer approximates it, but it is not a true LUT recovery.
- No Bengali-specific OCR accuracy figures were gathered for stylized caption fonts (PaddleOCR/Tesseract/EasyOCR Bengali models).
- No tool found that detects SFX *placement* in a reference automatically. Onset detection plus CLAP tagging (Section 3) is a plausible route but unverified.

---

## 3. Evaluation: measuring how close a render is to the reference, and the render → compare → adjust loop

### Takeaway
A render of *new footage* will never match the reference pixel for pixel, so full-reference metrics (SSIM/LPIPS/VMAF) are mainly useful for **regression checks** (render vs. a previously approved render) and for comparing **style-isolated layers**: caption crops, color statistics and motion curves. For style similarity itself, compare **extracted feature curves** (cut-rhythm histogram, zoom-scale curves, caption timing, color stats, loudness, onset density, CLAP timbre embeddings), aligned with DTW. FVD is not suitable for single-video comparisons.

### Cited Findings
**Image/video perceptual metrics**
- **LPIPS**: `pip install lpips`; `lpips.LPIPS(net='alex')`. Inputs are RGB tensors in [-1, 1]. `alex` gives the "best forward scores" as a metric, and `vgg` is preferred as an optimization loss. BSD-2-Clause. — [richzhang/PerceptualSimilarity](https://github.com/richzhang/PerceptualSimilarity)
- **DISTS** is built to tolerate texture resampling while staying sensitive to structure (VGG features). LPIPS has VGG/AlexNet variants. — [Video compression dataset and benchmark of learning-based VQ metrics, arXiv 2211.12109](https://arxiv.org/pdf/2211.12109). One survey reports DISTS ≈0.86 vs LPIPS ≈0.85 correlation with human scores on its data. — [Generative face video coding survey, arXiv 2506.07369](https://arxiv.org/pdf/2506.07369)
- Image metrics have no temporal term, and the common practice is to **average per-frame scores**. — [ColorVideoVDP, arXiv 2401.11485](https://arxiv.org/pdf/2401.11485); [Perceptual metric for frame interpolation, arXiv 2210.01879](https://arxiv.org/pdf/2210.01879)
- **VMAF** fuses VIF and DLM spatial features with a mean absolute difference between consecutive frames, and maps them through SVR. — [ColorVideoVDP, arXiv 2401.11485](https://arxiv.org/pdf/2401.11485). A videoconferencing study notes that VMAF is the only one of the standard metrics with a temporal component, yet it still misses freezes, skips and frame-rate variation. — [arXiv 2303.12761](https://arxiv.org/pdf/2303.12761v1.pdf)
- A codec-comparison study found VMAF correlated with subjective quality better than PSNR, SSIM, MS-SSIM and VIF. — [CEUR-WS Vol-3027 paper19](https://ceur-ws.org/Vol-3027/paper19.pdf)
- **VMAF repo status (as of Oct 2026)**: a new **v1 model set was released 2026-06** (guidance in `models_v1.md`) and an **HDR version in 2026-10**. v0 models are documented in `models_v0.md`. There is a "NEG" mode that disables enhancement gain for codec evaluation. `libvmaf` also computes PSNR, PSNR-HVS, SSIM, MS-SSIM and CIEDE2000. To use it in FFmpeg, build with `--enable-libvmaf`. The license is **BSD+Patent** (changed from Apache 2.0 in Feb 2020). — [Netflix/vmaf GitHub](https://github.com/Netflix/vmaf)
- **FVD problems**:
  - Ge et al. (CVPR 2024) show FVD is **content-biased** toward per-frame quality over temporal realism. Sampling static videos can lower FVD without any temporal improvement, and FVD rises only slightly under large temporal corruption. Features from self-supervised video models reduce the bias. — [On the Content Bias in FVD, arXiv 2404.12391](https://arxiv.org/pdf/2404.12391)
  - "Beyond FVD" lists non-Gaussian I3D features, insensitivity to temporal distortion and **impractically large sample sizes**, and concludes that FVD falls short as a standalone metric. — [Luo et al., arXiv 2410.05203](https://arxiv.org/html/2410.05203v1)

**Temporal alignment**
- librosa's official DTW example aligns two recordings of the same piece at different tempos. It computes chroma for each, calls `librosa.sequence.dtw(X=chroma1, Y=chroma2, metric="cosine")` to get a cost matrix and warping path (returned in reverse, so flip it), and converts frames to seconds with `librosa.frames_to_time`. — [librosa: Music synchronization with DTW](https://librosa.org/doc/main/auto_examples/plot_music_sync.html)
- An onset-strength peak approach (strong peaks used as anchor points) can fix offsets between a recording and a reference. — [Aligning audio files in Python (blog)](https://write.as/hammertoe/aligning-audio-files-in-python)

**Audio loudness**
- `pyloudnorm` implements **ITU-R BS.1770-4** (the measurement underlying EBU R128) with adjustable gating and filters. Usage: `pyln.Meter(rate).integrated_loudness(data)` and `pyln.normalize.loudness(data, measured, target)`. MIT license. — [pyloudnorm GitHub](https://github.com/csteinmetz1/pyloudnorm)
- FFmpeg `loudnorm` is best used **two-pass**: pass 1 runs with `print_format=json` and measures `input_i`, `input_tp`, `input_lra` and `input_thresh`, and pass 2 applies a linear gain. A single pass "pumps". — [DEV: two-pass loudnorm the right way](https://dev.to/masonwritescode/two-pass-loudness-normalization-with-ffmpeg-loudnorm-the-right-way-1nm3). `ffmpeg-normalize` automates this, defaulting to −23 LUFS (EBU broadcast) with a 7 LU LRA target. — [ffmpeg-normalize](https://github.com/em-synth/ffmpeg-normalize)
- **Platform loudness targets are disputed** (no official TikTok/Meta source found):
  - The most commonly cited target is **−14 LUFS integrated, −1 dBTP**. — [loudfix: what is LUFS](https://loudfix.pages.dev/blog/what-is-lufs/); [Reels audio guide](https://dj-master-web.vercel.app/en/blog/instagram-reels-audio-en)
  - One source says TikTok/Instagram **do not normalize**, so the audio plays as uploaded. — [loudfix](https://loudfix.pages.dev/blog/what-is-lufs/)
  - Another source says they normalize to about −14. — [cnapsstudio Notion](https://cnapsstudio.notion.site/Tool-Video-Editing-Audio-Finish-3aaf00afbadf805a931fdea750df9a44)
  - OpusClip claims −10 to −12 LUFS. — [OpusClip blog](https://opus.pro/blog/best-loudness-normalizers)
  - A 2026 article says platforms typically apply normalization at playback rather than rewriting the file. — [Fora Soft: LUFS targets per platform 2026](https://www.forasoft.com/learn/audio-for-video/articles-audio/lufs-targets-per-platform-2026)

**SFX timbre similarity (CLAP)**
- LAION-CLAP: `pip install laion-clap`. The audio embedding API is `get_audio_embedding_from_filelist(x=[...])` or `get_audio_embedding_from_data(x=waveforms)`, and `get_text_embedding(texts)` embeds text. **Audio must be 48 kHz.** Checkpoints:
  - `630k-audioset-best.pt` for general audio under 10 s
  - `630k-audioset-fusion-best.pt` for variable length
  - `music_speech_audioset_epoch_15_esc_89.98.pt` (HTSAT-base) for speech, music and general audio
  - The repo license is listed as CC0-1.0. — [LAION-AI/CLAP GitHub](https://github.com/LAION-AI/CLAP)
- CLAP embeddings are 512-d and compared with cosine similarity, per secondary descriptions. — [Mixpeek audio extractor docs](https://mixpeek.com/docs/processing/extractors/audio-fingerprint); [axinc-ai CLAP article](https://medium.com/axinc-ai/clap-feature-extraction-model-for-searching-audio-from-text-dcfd4c93756e)
- Audio Atlas does sound-effect search by embedding SFX with CLAP's audio encoder and comparing them to the query embedding. — [Audio Atlas about](https://audio-atlas.github.io/audio-atlas-frontend/about). A Surrey study (AES 2025) found a CLAP-based SFX search beat the BBC Sound Effects Library workflow on productivity and frustration. — [Liu et al., AES 2025 (PDF)](https://personalpages.surrey.ac.uk/w.wang/papers/Liu%20et%20al_AES_2025.pdf)

### Inferences
- **Proposed "style distance" scorecard.** Each metric is computed on features, so the reference and the new render need not share content.

  | Dimension | Feature extracted from both videos | Comparison |
  |---|---|---|
  | Pace | shot-length distribution (TransNetV2) | Wasserstein/KS distance; cuts/sec difference |
  | Zoom/motion | per-shot scale curves (flow+affine), normalized to [0,1] time | DTW distance between curves; bezier-param L2 |
  | Caption timing | word-onset → caption-appear latency, on-screen duration, words/chunk | mean abs error in ms |
  | Caption look | crop of a caption frame (same text rendered both ways if possible) | LPIPS/DISTS on crops; font-ID match |
  | Color | Lab mean/std, hue histogram per shot | ΔE (CIEDE2000) of means; histogram EMD |
  | Loudness | integrated LUFS, LRA, true peak (pyloudnorm/ffmpeg) | absolute diff in LU |
  | Rhythm/SFX | onset density, SFX-onset offset vs cuts | DTW / mean offset ms |
  | SFX timbre | CLAP embedding of each SFX hit | cosine similarity |

- **Render → compare → adjust loop**:
  1. The LLM writes the style spec.
  2. The compiler produces the timeline.
  3. Render a fast **low-res proxy** (e.g. 540×960, 30 fps).
  4. Run the same extractors on the proxy as on the reference.
  5. Compute the scorecard.
  6. Feed the LLM a structured diff, e.g. "zoom duration 420 ms vs ref 250 ms; caption pop overshoot 1.05 vs 1.12; LUFS −18 vs −14".
  7. The LLM patches only the spec fields involved.
  8. Repeat until every metric is within tolerance or N iterations is reached, then do the final full-res render.

  Because the extractors are deterministic, many parameters (LUFS, color stats, zoom scale) can be fixed numerically without the LLM. Reserve the LLM for discrete choices (animation type, font, SFX choice).
- Use VMAF/SSIM only to make sure the **final encode** has not degraded quality vs the master (same content, same resolution). Here VMAF is the right tool, and the new v1 models are worth trying.
- Do not use FVD: it needs large sample sets and is content-biased.

### Gaps
- No published metric or benchmark exists for "edit-style similarity" between two short-form videos with different content. The scorecard above is a design, not a validated metric, and tolerances must be tuned on real references.
- No official TikTok or Meta loudness documentation found. The −14 LUFS figure is industry convention, not a confirmed platform spec.
- Did not verify FFmpeg's `ebur128` filter syntax or the `libvmaf` CUDA build from primary docs (ffmpeg.org was partly unreachable).
- No source evaluated CLAP specifically on short UI-style SFX (whoosh/pop/ding) similarity.

---

## 4. Complex-script (Bengali) text rendering pitfalls and fonts

### Takeaway
Bengali needs **OpenType shaping (HarfBuzz)** for conjuncts (যুক্তাক্ষর), reordering of pre-base vowel signs (ি ে ৈ) and reph. The safest renderer is **Chromium (HarfBuzz via Skia)**, i.e. Remotion/HTML captions. Pillow works only when built with **libraqm** and `layout_engine=RAQM`. FFmpeg/libass can silently fall back to "simple" shaping, so force `shaping=complex`. Use **OFL fonts from Google Fonts**: Hind Siliguri, Noto Sans/Serif Bengali, Baloo Da 2, Anek Bangla, Tiro Bangla. Treat Li-series fonts and Shonar Bangla as **restricted**, and check the SolaimanLipi license file yourself because sources conflict.

### Cited Findings
**Renderers**
- **Pillow**:
  - Bengali renders **incorrectly without libraqm and correctly with it**. Setup is "not straightforward like English text". — [Stack Overflow (mirror): Pillow + libraqm Bengali](https://kaweah.freedombox.rocks/kiwix/stackoverflow.com_en_all_2023-11/questions/67361964/blender-render-complex-fonts-as-rendered-with-python-pillow-libraqm)
  - Pillow needs complex-text support enabled at build time (FreeType + HarfBuzz + FriBiDi via libraqm). — [Arch Linux bug FS#55226](https://bugs.archlinux.org/task/55226.html)
  - A Khmer clipping bug in Pillow+raqm was fixed by PR #3787, which shows edge cases exist. — [Pillow issue #3235](https://github-redirect.dependabot.com/python-pillow/Pillow/issues/3235)
- **Some breakage is the font, not the engine**: Lohit-Bengali failed to form conjuncts where the second consonant is ত followed by ি. — [Fedora fonts-bugs thread](https://lists.fedoraproject.org/archives/list/fonts-bugs@lists.fedoraproject.org/thread/ATQEAJQKDDUVBXC5NK6XPD23FG5MC53K)
- **FFmpeg/libass**:
  - An FFmpeg ticket reports Bengali rendering wrong in the `subtitles` filter with the Shonar Bangla font, even though the libass log showed HarfBuzz-ng 7.3.0 (COMPLEX) available. — [FFmpeg trac #10384](https://trac.ffmpeg.org/ticket/10384) (seen through a search snippet)
  - A 2021 FFmpeg patch explains that the `subtitles` filter left `shaping` uninitialized, which **forced the "simple" shaper**, and that Indic scripts needing complex shaping "are not rendered correctly". The patch moves the option into common subtitle options. — [ffmpeg-devel patch, Mar 2021](https://ffmpeg.org/pipermail/ffmpeg-devel/2021-March/277946.html)
  - The `ass` filter's `shaping` option: `auto` (default, best available), `simple` (substitutions only) and `complex` (OpenType substitutions **and** positioning). — [FFmpeg 7.0 ass filter docs](https://ayosec.github.io/ffmpeg-filters-docs/7.0/Filters/Video/ass.html)
- **Browsers/Skia**:
  - HarfBuzz's Indic shaping model covers Bengali. — [HarfBuzz docs mirror](https://rocketleaguechatp.duckdns.org/tarball_dev/usr/share/gtk-doc/html/harfbuzz/what-does-harfbuzz-do.html)
  - Skia's HarfBuzz copy includes Bengali shaping tests. — [Skia third_party/harfbuzz shaper-indic tests](https://skia.googlesource.com/third_party/harfbuzz/+/410731d3fb678365c07a4d1745b72b6bb3142b70/test/shaping/texts/in-house/shaper-indic)
  - Early (2011–12) WebKit/Chromium bugs show Indic rendering problems that were fixed by upstream HarfBuzz updates. — [WebKit bug 67933](https://bugs.webkit.org/show_bug.cgi?id=67933)

**Fonts and licenses**
- **Hind Siliguri** is five Bengali weights from Indian Type Foundry's open-source Hind multi-script project, licensed **SIL OFL 1.1**. — [Fontsource: Hind Siliguri](https://fontsource.org/fonts/hind-siliguri/about); [Adobe Fonts listing](https://fonts.adobe.com/fonts/hind-siliguri)
  - **Known defect**: a community repo reports malformed glyphs for Bengali digit one "১" in the Regular, Medium and SemiBold weights. — [bdeshi/Hind-Siliguri README](https://git.bdeshi.space/bdeshi/Hind-Siliguri/blame/branch/main/README.md)
- **Noto Sans Bengali**: **OFL-1.1**. — [Fontsource: Noto Sans Bengali](https://fontsource.org/fonts/noto-sans-bengali/about)
- **Anek Bangla**: Google Fonts `license: "OFL"`, designer Ek Type. It is variable, with axes `wdth` 75–125 and `wght` 100–800, which makes it useful for animated weight/width captions. — [google/fonts anekbangla METADATA.pb](https://github.com/google/fonts/blob/main/ofl/anekbangla/METADATA.pb)
- **Baloo Da 2**: `license: "OFL"`, designer Ek Type, variable `wght` 400–800. — [google/fonts balooda2 METADATA.pb](https://github.com/google/fonts/blob/main/ofl/balooda2/METADATA.pb)
- **Tiro Bangla**: `license: "OFL"`, designers Tiro Typeworks, John Hudson, Fiona Ross and Neelakash Kshetrimayum. Regular and Italic only. — [google/fonts tirobangla METADATA.pb](https://github.com/google/fonts/blob/main/ofl/tirobangla/METADATA.pb)
- **Kalpurush**: SIL OFL 1.0 (Avro Free Bangla Font Project, designer Tanbin Islam Siyam, distributed by OmicronLab). Its Latin glyphs come from Gentium. — [potasiyam/Kalpurush GitHub](https://github.com/potasiyam/Kalpurush); [OmicronLab Bangla fonts](https://omicronlab.com/bangla-fonts.html)
- **SolaimanLipi**: sources conflict.
  - One mirror says SIL OFL 1.0 but "free for personal use… needs a proper license for commercial applications", which is internally inconsistent with OFL. — [fonts.maateen.me: SolaimanLipi](https://fonts.maateen.me/solaiman-lipi)
  - Another says GPL v2+ with a font-embedding exception. — [online-fonts.com: SolaimanLipi](https://online-fonts.com/fonts/solaimanlipi)
  - A 2009 XeTeX list post describes it as OFL. — [XeTeX list 2009](https://tug.org/pipermail/xetex/2009-May/013162.html)
- **Li Ador Noirrit** (Lipighor Font Foundry; Nurul Alom Ador and Niladri Shekhar Bala): the license excerpt **bans modifying, distributing or selling** and requires credit. Commercial-use terms are unclear and the source is a third-party mirror. — [onlinewebfonts: Li Ador Noirrit](https://www.onlinewebfonts.com/download/3565357604fee3776c402d09091028bb)
- **Shonar Bangla** (Windows system font) requires a purchased license for commercial use. — [freeforfonts: Shonar Bangla](https://www.freeforfonts.com/fonts/shonar-bangla)

**Identifying the font in a reference video**
- See Section 2: Lipika for Indic font ID. Mainstream tools (WhatTheFont, Matcherator, Adobe Match Font) are Latin-centric. — [Lipika HF](https://huggingface.co/loopdesk-ai/lipika)

### Inferences
- **Recommendation**: render all Bengali captions in **Chromium via Remotion (HTML/CSS)**.
  - Chromium uses HarfBuzz through Skia, word-level `<span>` animation is trivial in CSS/React, and fonts load as WOFF2 from Google Fonts/Fontsource.
  - Avoid splitting Bengali text **per character** for animation, because that breaks conjunct shaping across spans. Animate at the **word** (or grapheme-cluster) level only. This follows from how shaping works on contiguous runs; I found no source that tests this explicitly.
- If you use the FFmpeg/ASS path: always set `shaping=complex` (ass filter), check libass's log for "COMPLEX", and test a regression string containing ক্ষ, ত্র, ন্ত্র, র্, ি, ৌ and the digit ১.
- If you use Pillow: assert `features.check("raqm")` is True and pass `layout_engine=ImageFont.Layout.RAQM`. On Windows, Pillow wheels need `fribidi.dll` separately. That Windows detail comes from training knowledge, not verified this session.
- Default font shortlist for Bangladeshi short-form captions, all commercially safe under OFL:
  - Hind Siliguri: clean UI look, but avoid "১" in the affected weights or use the community-fixed fork
  - Anek Bangla: variable, bold display
  - Baloo Da 2: rounded, playful, the typical "Reels" look
  - Noto Sans Bengali: widest coverage
  - Tiro Bangla: serif/editorial
- OFL allows commercial use and embedding in videos. Rendered pixels in a video are not a "font distribution", so the main obligations apply only if you redistribute the font files (e.g. bundled in an app). This is an inference from the OFL summary in the search results, not legal advice.

### Gaps
- Could not confirm the current status of FFmpeg ticket #10384 (trac.ffmpeg.org unreachable), i.e. whether `shaping=complex` fixes Bengali in current builds.
- Noto Serif Bengali's license was not individually verified. It is almost certainly OFL like the rest of Noto, but no source was fetched.
- Official Lipighor and SolaimanLipi license texts were not found. These need checking against the files shipped with the fonts.
- No benchmark of Bengali shaping correctness across Chromium vs libass vs Pillow+raqm vs Skia/Skottie.

---

## 5. Compute, cost, encoding and platform specs

### Takeaway
For a single developer, **CPU rendering is usually sufficient** for 30–60 s Reels.
- Remotion's own figures show Lambda (no GPU) rendering 80 s of video in about 15 s for about $0.01/min (simple compositions). Local multi-core rendering with tuned concurrency also works.
- GPUs matter for the **analysis models** (RAFT, TransNetV2, CLAP, OCR, WhisperX) and for WebGL/heavy CSS effects. Rent them per second: Modal L4 ≈ $0.80/h, A10 ≈ $1.10/h; RunPod 4090 pods from ≈ $0.34/h.
- Encode to **1080×1920 H.264 + AAC MP4, 30 fps (60 for fast motion)**. Platform bitrate guidance is inconsistent across sources; ~8–12 Mbps is a safe middle ground.

### Cited Findings
**Rendering (Remotion)**
- Remotion Lambda's marketing figures: an 80-second video in 15 s, a 2-hour video in 12 min, about **$0.01 per minute of video**. Assumes ARM64 Lambda, 2048 MB RAM, warm, us-east-1, excluding S3/egress. — [remotion.dev/lambda](https://remotion.dev/lambda)
- The HelloWorld cost example is about $0.001 per render (7.56 s warm, 11.02 s cold). A 1-minute render pulling a remote 4K video was about $0.10–0.11, and resolution increases "significantly increase" render time and cost. — [Remotion Lambda cost example](https://www.remotion.dev/docs/lambda/cost-example); [mirror](https://convert.remotion.dev/docs/lambda/cost-example)
- Concurrency can help or hurt. Remotion defaults to half the system's threads, and recommends `npx remotion benchmark` (default 3 runs) to find the best concurrency. — [Remotion performance docs](https://remotion.dev/docs/performance); [Remotion CLI benchmark](https://www.remotion.dev/docs/cli/benchmark)
- GPU:
  - Chromium **disables the GPU in headless mode**, which can significantly slow WebGL/canvas/shadows/gradients/blur/transforms. Enable it with the `--gl` flag.
  - "**AWS Lambda instances have no GPU**."
  - On Linux, use `chrome-for-testing` mode to take advantage of GPU drivers.
  - Sources: [Remotion docs gpu.mdx (GitHub)](https://github.com/remotion-dev/remotion/blob/main/packages/docs/docs/gpu.mdx); [Remotion performance docs](https://remotion.dev/docs/performance)

**Cloud GPU pricing (late 2026, from secondary sources; verify on vendor pages)**
- **Modal**:
  - H100 ≈ $0.001097/s (~$3.95/h). One source says the headline rate assumes no region pinning or preemption changes. — [Spheron: Modal pricing 2026](https://www.spheron.network/blog/modal-gpu-pricing-2026-per-second-billing/)
  - A10 ≈ $0.000306/s (~$1.10/h) and L4 ≈ $0.000222/s (~$0.80/h), citing modal.com/pricing as of July 2026. — [BudgetForge: Modal pricing 2026](https://www.budgetforge.dev/tools/modal-pricing-2026)
  - An outlier tutorial lists L4 at $0.0011/s (Apr 2026), likely wrong. — [theneuralbase](https://theneuralbase.com/modal/learn/beginner/gpu-l4-for-cheaper/)
- **RunPod**:
  - Serverless is billed per second, rounded up, from worker start to full stop. Flex workers scale to zero, and active (always-on) workers are cheaper. The 16 GB tier (A4000/A4500/RTX 4000) costs **$0.00016/s flex, $0.00011/s active**. — [RunPod serverless pricing docs](https://docs.runpod.io/serverless/pricing)
  - Pods: RTX 4090 24 GB from **$0.34/h** (pricing page, July 2026). — [RunPod pricing](https://www.runpod.io/gpu-cloud/pricing)
  - Third-party range for the 4090: $0.34–0.69/h, Community vs Secure Cloud (June 2026). — [Hivenet RunPod guide](https://www.hivenet.com/post/runpod-pricing-complete-guide-to-gpu-cloud-costs)
  - An older blog lists 4090 serverless flex at $0.00044/s, which is probably outdated. — [RunPod blog](https://blog.runpod.io/runpod-serverless-pricing-update)
- **Replicate**:
  - L40S $0.000975/s (~$3.51/h), A100 80GB $0.0014/s (~$5.04/h), H100 $0.001525/s (~$5.49/h). — [replicate.com/pricing](https://replicate.com/pricing)
  - The A100 40GB tier is retired (blog correction dated 2026-10-24). — [apicostcalc](https://apicostcalc.com/blog/replicate-h100-cheaper-a100-40gb-gone.html)
  - An aggregator's lower numbers appear stale. — [pricegpu](https://pricegpu.pages.dev/provider/replicate)
- **Lambda** (sources conflict):
  - A10 is about $0.75–0.86/h. — [lambdalabs.com/cloud snapshot](https://lambdalabs.com/cloud); [DeployBase, Mar 2026](https://deploybase.ai/articles/lambda-cloud-gpu-pricing)
  - H100 PCIe is about $2.49–3.29/h and H100 SXM about $2.99–3.99/h per GPU (SXM only in 8-GPU nodes). — [Spheron, May 2026](https://www.spheron.network/blog/lambda-cloud-h100-pricing-2026/); [DeployBase](https://deploybase.ai/articles/lambda-cloud-gpu-pricing)

**Encoding / upload specs**
- **Instagram Reels** (third-party guides; no Meta page retrieved):
  - 1080×1920 at 9:16 is the standard. Instagram downsizes to 1080p, so 4K brings no visible benefit. MP4 with H.264 plus AAC (≥128 kbps) is the usual recommendation. 30 fps is the default, with 60 for fast motion. Max file size is 4 GB.
  - HEVC is **contested**: one guide says it may be re-encoded on upload and another lists it as acceptable.
  - Bitrate advice ranges from ~3.5 Mbps to 5–8, 8–12 and 10–15 Mbps. One guide says anything above ~12 Mbps is downsampled.
  - Length limits are reported inconsistently (3 min in-app recording vs 15 min upload).
  - Sources: [argil.ai 2026 spec sheet](https://argil.ai/blog/instagram-reel-size-e350f); [SocialPilot 2026](https://www.socialpilot.co/instagram-marketing/instagram-video-size); [Mallary dev guide 2026](https://www.mallary.ai/blog/instagram-reel-resolution); [ContentStudio](https://contentstudio.io/blog/instagram-reel-size)
- **TikTok** (third-party; no official TikTok page retrieved):
  - 9:16. In-Feed minimum is 540×960 and **1080×1920 is recommended**. MP4/MOV, under 500 MB for ads.
  - Bitrate floor ≥516 kbps, with ≥2,500 kbps recommended for some ad types.
  - Keep key elements out of the bottom/edge UI zones.
  - Sources: [Benly: TikTok video specs](https://benly.ai/learn/tiktok-ads/tiktok-video-specs); [Sovran: TikTok ad specs 2026](https://sovran.ai/blog/tiktok-video-ad-specs); [RelevantAudience](https://www.relevantaudience.com/tiktok-ads/tiktok-video-size-ad-specs/)

### Inferences
- **Workload math**: a 45 s Reel at 60 fps is 2,700 frames, and at 30 fps it is 1,350.
  - If Remotion's "80 s in 15 s on Lambda" applies to simple caption/zoom compositions, a 45 s Reel costs well under $0.01 and renders in seconds on Lambda.
  - Locally, an 8-core laptop at a few frames per second per Chrome tab would take a few minutes. This is unverified; run `npx remotion benchmark` on your own composition.
- **Suggested architecture for a Bangladesh-based solo developer**:
  - Render the timeline **locally or on a cheap CPU VPS** with Remotion (no GPU needed for HTML captions/zooms).
  - Run the **GPU analysis jobs** (TransNetV2, RAFT, OCR, CLAP, WhisperX for Bengali word timings) as per-second serverless functions on Modal or RunPod. A few minutes of L4 time per reference costs a few US cents at ~$0.80/h (~$0.013/min).
  - Cache the extracted reference style spec, so analysis runs once per reference and not once per render.
- **Parallel frame rendering**: Remotion Lambda already splits renders into chunks across many Lambdas. With FFmpeg you can split by shot, render the segments in parallel, and concat with the concat demuxer (stream copy) if all segments share codec parameters. This is general FFmpeg practice, not sourced this session.
- **Suggested export preset** (synthesis of the conflicting third-party guidance):
  - 1080×1920, 30 fps (or 60 if the reference is 60), H.264 High profile, yuv420p, CRF ~18–20 or VBR ~10 Mbps (max 12)
  - AAC 48 kHz ~192 kbps, −14 LUFS integrated / −1 dBTP via two-pass loudnorm
  - MP4 with `+faststart`
  - Keep captions inside the central safe zone, away from the bottom ~20% and the right-side button column

### Gaps
- No published CPU-vs-GPU benchmark for **1080×1920 @ 60 fps** Remotion renders, and none with Bengali text. Must be measured locally.
- Primary pricing pages for Modal and RunPod 4090/L4 serverless could not be fetched. Modal's free monthly credit amount was not verified. All prices are point-in-time (mid–late 2026) from secondary sources.
- No official Meta/Instagram or TikTok organic-upload spec page was retrieved, and bitrate guidance conflicts widely. YouTube's official "recommended upload encoding settings" page (support.google.com) was unreachable.
- Not researched: payment-method availability from Bangladesh for Modal/RunPod/Replicate/AWS (card/USD billing), which may be a practical blocker.
- Not researched: hardware-encoder (NVENC) vs x264 quality trade-offs for final export.
