# Programmatic video rendering frameworks and NLE automation (excluding Remotion, ffmpeg/ffprobe, HyperFrames)

Scope: options an AI coding agent could use to re-edit short vertical videos (Reels/TikTok/Shorts: talking head plus b-roll, Bengali captions, motion graphics, transitions, overlays, light leaks, a matted person composited over graphics) by writing code or JSON and rendering headlessly on a Linux server.

Research date: 2026-10-28. How the evidence was gathered:
- **Release dates and licenses** come from the npm registry and PyPI JSON APIs, queried directly on 2026-10-28. These are primary data.
- **GitHub READMEs** were read with WebFetch. The GitHub REST API was blocked in this session, so star counts and commit dates come from README page captures only.
- **Vendor pricing pages** (shotstack.io, creatomate.com, json2video.com, plainlyvideos.com, bannerbear.com, rendi.dev) could not be fetched because those hosts are outside this session's network allowlist. Pricing therefore comes from search snippets of official docs and third-party reviews. Each one is marked, and all should be re-checked on the vendor page.
- **Empirical Bengali shaping tests** were run in this session on Linux, using Noto Sans Bengali Bold and the string "ক্ষমা স্বাধীনতা কৃষ্ণ শ্রী", which contains the conjuncts ক্ষ, স্ব, ষ্ণ and শ্র. These are cited as "[Local test]" with the output file path. They are first-hand evidence, not web sources.

---

## Q1. Code-first JS/TS frameworks: Revideo, Motion Canvas, Etro, Diffusion Studio, Editly, FFCreator, Twick, VideoContext, WebCodecs renderers, Puppeteer/Playwright capture (timecut and similar), Theatre.js, GSAP

### Takeaway
Among the open-source JS options, only **Revideo** (MIT, Motion Canvas fork, maintained again with v0.11.0 in July 2026) and **Twick** (source-available SUL, active through May 2026, Puppeteer plus ffmpeg render server) combine headless Node rendering, audio and a JSON or code timeline.

Most of the others fall short for this use:
- **Browser-only:** Diffusion Studio, Etro, WebAV and VideoContext. Diffusion Studio also watermarks free output.
- **Stale:** Motion Canvas, Editly, FFCreator, timecut and Theatre.js.

Any Chromium-based renderer (Revideo, Twick, Puppeteer capture, GSAP pages) shapes Bengali correctly, because Chrome uses HarfBuzz. For headless canvas text, all three Node canvas libraries tested also shaped Bengali correctly.

### Cited Findings

**Revideo**
- Revideo is described as "a rendering engine for creating videos in code". The repo is now `midrender/revideo` and the README calls it "the engine behind Midrender". — [GitHub midrender/revideo](https://github.com/midrender/revideo)
- It is MIT licensed.
- `renderVideo()` renders headlessly from Node or a CLI rendering endpoint, and runs "wherever Node and a headless browser run", including Google Cloud Run.
- It supports parallel rendering split across workers.
- `<Video/>` and `<Audio/>` components support audio export.
- A React `<Player/>` handles browser preview.
- It sends anonymous PostHog telemetry by default, which `DISABLE_TELEMETRY=true` turns off.
- npm release history for `@revideo/core` (MIT):
  - The latest is 0.11.0, published 2026-07-10, with repository field `midrender/revideo`.
  - Before that, canary builds stopped between 2025-04-20 and 2026-07-09, roughly a 15-month gap, then resumed. — [npm @revideo/core](https://www.npmjs.com/package/@revideo/core) (registry metadata pulled 2026-10-28)
- Origin and direction of the project:
  - Revideo forked Motion Canvas to add headless rendering, audio support and a library-first API.
  - Its core engine now powers Midrender, a YC company with the same founder that makes an AI motion-graphics editor.
  - The team "now primarily works on Midrender". — [Webfolio](https://www.webfolio.to/tools/revideo); [YC Midrender](https://www.ycombinator.com/companies/midrender)
  - One 2026 blog says the framework "is maintained but its roadmap follows a commercial product". This is unverified secondary commentary. — [Wireflow](https://www.wireflow.ai/blog/best-remotion-alternatives-in-2026)
- Revideo's `renderVideo` "uses a headless browser" and accepts variables plus FFmpeg settings. — [Revideo docs renderVideo](https://docs.re.video/api/renderer/renderVideo)

**Motion Canvas**
- License: MIT.
- The last stable npm release is 3.17.2 (2024-12-14). The last pre-release is 3.18.0-alpha.0 (2025-02-16), and npm shows nothing since. — [npm @motion-canvas/core](https://www.npmjs.com/package/@motion-canvas/core)
- According to Revideo's fork notes, Motion Canvas renders by pressing a button in the editor UI. Its maintainers considered library or headless use out of scope, which led to the fork. — [YC launch: Revideo](https://www.ycombinator.com/launches/Kq1-revideo-create-videos-with-code); [awesome.ecosyste.ms Revideo](https://awesome.ecosyste.ms/projects/github.com%2Fredotvideo%2Frevideo)
- Remotion's comparison describes Motion Canvas as an imperative, generator-based API that draws to a single canvas element. — [Remotion docs: compare Motion Canvas](https://www.remotion.dev/docs/compare/motion-canvas)

**Etro**
- Etro is a TypeScript library that composites video, audio, text and image layers with GLSL effects, and serializes a session to and from JSON.
- It runs in the browser only. Node use goes through a separate `etro-node` wrapper.
- `movie.record()` renders "in realtime", meaning at playback speed. Offline rendering is still listed as "coming soon".
- License: GPL-3.0. — [GitHub etro-js/etro](https://github.com/etro-js/etro)
- npm shows it is active again: 0.13.0 (2026-03-18), 0.14.0 (2026-06-06) and 0.14.1 (2026-08-12), after a gap from Feb 2024 to Mar 2026. — [npm etro](https://www.npmjs.com/package/etro)

**Diffusion Studio Core**
- It is a "browser based video compositing engine powered by WebCodecs", using Canvas 2D for painting and built on Mediabunny.
- **Server-side rendering is not supported.** The README says to use Remotion for that.
- It requires COOP and COEP headers.
- License is MPL-2.0. However, free use must keep a "Made with Diffusion Studio" watermark, and removing it needs a paid, one-time, non-expiring license key that is checked locally.
- Features include captions, rich text, keyframes, masks, a basic transition set including dissolve, audio ramps and silence removal. — [GitHub diffusionstudio/core](https://github.com/diffusionstudio/core)
- npm: v4.0.0 (2025-11-18) to 4.0.3 (2025-11-30), with no release since. — [npm @diffusionstudio/core](https://www.npmjs.com/package/@diffusionstudio/core)

**Editly**
- Editly is declarative, with a JSON5 spec for clips, layers and transitions. It runs on Node and ffmpeg and is MIT licensed.
- Layer types include title, subtitle, news-title, canvas, fabric and gl (GLSL shaders).
- Transitions are drawn from gl-transitions.
- Audio support covers audio tracks, crossfades, ducking via `audioNorm`, and keeping source audio.
- On Linux it needs headless-gl's system dependencies.
- It is "maintained by me alone" and is now ESM-only. — [GitHub mifi/editly](https://github.com/mifi/editly)
- npm: the last stable release is 0.14.2 (2022-12-23), and the `next` tag 0.15.0-rc.1 dates from 2025-01-19. — [npm editly](https://www.npmjs.com/package/editly)

**FFCreator**
- License: MIT. The last npm release is 7.5.8 (2024-07-27). — [npm ffcreator](https://www.npmjs.com/package/ffcreator)

**Twick**
- Twick is a React SDK for timeline video editors: a canvas timeline, AI captions, GL effects and MP4 export.
- License: **Sustainable Use License v1.0**. This is source-available, not OSI open source.
  - Commercial use and self-hosting are allowed.
  - Reselling or redistributing it as a standalone SDK, developer tool or SaaS needs a commercial license.
- It has two render paths:
  - `@twick/browser-render` uses WebCodecs plus ffmpeg.wasm and needs Chrome or Edge.
  - `@twick/render-server` uses **Node + Puppeteer + FFmpeg**. It is recommended for production, long videos and full audio.
  - `@twick/cloud-export-video` exports on AWS Lambda.
- AI captions use Google Vertex AI (Gemini).
- The JSON timeline holds `properties{width,height,fps}` and `tracks[] → elements[]`, each element with `type`, `s` and `e` times and `props`. — [GitHub ncounterspecialist/twick](https://github.com/ncounterspecialist/twick)
- npm: version 0.15.31 (2026-05-07), with frequent releases through spring 2026. — [npm @twick/render-server](https://www.npmjs.com/package/@twick/render-server)

**VideoContext (BBC)**
- License: Apache-2.0. The last npm release is 0.54.0 (2019-11-28), so it is effectively dormant. — [npm videocontext](https://www.npmjs.com/package/videocontext)

**WebCodecs-based SDKs**
- **WebAV:**
  - Built on WebCodecs. It runs in Chrome or Edge 102+ and Electron, and Node is not mentioned.
  - It is a sprite-and-combinator compositing model, and `Combinator.output()` returns an MP4 ReadableStream.
  - License: MIT. A paid "WebAV Pro" edition also exists. — [GitHub WebAV-Tech/WebAV](https://github.com/WebAV-Tech/WebAV)
  - npm `@webav/av-cliper` 1.2.8 is dated 2026-01-10. — [npm @webav/av-cliper](https://www.npmjs.com/package/@webav/av-cliper)
- **Mediabunny** (the muxing and demuxing layer under Diffusion Studio): MPL-2.0, version 1.62.1 (2026-10-22), very active. — [npm mediabunny](https://www.npmjs.com/package/mediabunny)

**Puppeteer and Playwright HTML-to-video capture**
- timecut and timesnap (BSD-3-Clause): last release 0.3.3 (2022-04-03), so stale. — [npm timecut](https://www.npmjs.com/package/timecut)
- puppeteer-capture (MIT): v1.58.0 (2026-08-07).
  - It uses Chrome's `HeadlessExperimental` CDP domain to capture each frame on demand, with a virtual clock.
  - Platform support is listed as Linux and Windows.
  - With Puppeteer v23+ it enforces the `chrome-headless-shell` binary, so `--headless=new` is unsupported. — [puppeteer-capture README](https://cdn.jsdelivr.net/npm/puppeteer-capture@1.58.0/README.md); [npm](https://www.npmjs.com/package/puppeteer-capture)
- HeyGen engineering notes on the beginFrame approach:
  - Deterministic beginFrame capture works on Linux with chrome-headless-shell.
  - With beginFrame control on, `requestAnimationFrame` does not fire.
  - Letting the browser play `<video>` during rendering is unreliable, so video frames must be supplied another way. — [HeyGen research: HTML-to-video](https://www.heygen.com/research/html-to-video)

**Theatre.js**
- `@theatre/core` is Apache-2.0 and `@theatre/studio` is AGPL-3.0-only.
- The last release is 0.7.2 (2024-05-19), so it is stalled. — [npm @theatre/core](https://www.npmjs.com/package/@theatre/core); [npm @theatre/studio](https://www.npmjs.com/package/@theatre/studio)

**GSAP**
- Version 3.15.0 (2026-04-13) is released under the "Standard 'no charge' license", which is not OSI. — [npm gsap](https://www.npmjs.com/package/gsap)
- Webflow made GSAP, including the former Club plugins such as SplitText, free for everyone, with commercial use permitted.
- The license **prohibits use in tools that let people build visual animations without code and compete with Webflow**. — [Webflow blog](https://webflow.com/blog/gsap-becomes-free); [GSAP standard license](https://gsap.com/community/standard-license/)

**Editframe** (newer HTML-to-video SDK)
- `@editframe/elements` 0.60.34 (2026-10-17) is source-available.
- It is free for individuals and organizations with 3 or fewer employees; larger organizations need a paid tier.
- Cloud rendering is listed at $0.02/min and needs the Cloud tier. — [Editframe SDK license](https://cdn.jsdelivr.net/npm/@editframe/api@0.54.0/LICENSE.md); [editframe.com/render](https://editframe.com/render); [npm](https://www.npmjs.com/package/@editframe/elements)

**Node canvas libraries** (for custom raster pipelines)
- `@napi-rs/canvas` 1.0.13 (2026-10-21, MIT), `skia-canvas` 4.0.0 (2026-10-12, MIT) and `canvas` (node-canvas) 3.2.3 (2026-03-31, MIT) are all current. — [npm @napi-rs/canvas](https://www.npmjs.com/package/@napi-rs/canvas); [npm skia-canvas](https://www.npmjs.com/package/skia-canvas); [npm canvas](https://www.npmjs.com/package/canvas)
- **[Local test]** All three rendered the Bengali test string with correct conjuncts using `fillText` and the Noto Sans Bengali font on Linux, with no special configuration. Output: `/tmp/claude-0/-home-user-site/b988b61d-5cda-5294-be82-80a85dc995ce/scratchpad/node_shape.png`

**Chromium-based renderers and Bengali**
- HarfBuzz is the shaping engine used in Chrome, Firefox, Android and GNOME. It has Indic shaping models covering Bengali. — [Wikipedia: HarfBuzz](https://en.wikipedia.org/wiki/HarfBuzz)

**Per-character caption animation**
- **[Local test]** In Node 22 (ICU 77.1, Unicode 16.0), `Intl.Segmenter('bn',{granularity:'grapheme'})` split the test string into 12 grapheme clusters: `ক্ষ, মা, স্বা, ধী, ন, তা, কৃ, ষ্ণ, শ্রী` and spaces. Every conjunct stayed whole. The string has 26 code points.
- So per-grapheme animation is safe with a modern ICU, but naive per-code-point splitting (`[...str]`) breaks conjuncts.
- Word segmentation returned the four words correctly.

**Speed and comparisons** (mostly secondary sources)
- One 2026 guide says a 60-second 1080p video typically takes 2–5 minutes to render locally with Remotion. It describes Motion Canvas and Revideo as frame-by-frame browser rendering. — [PkgPulse comparison](https://www.pkgpulse.com/guides/remotion-vs-motion-canvas-vs-revideo-programmatic-video-2026)
- HN and Reddit sentiment, as summarized by one comparison: "Remotion wins today: bigger ecosystem", and Revideo's plugin ecosystem is "smaller, younger". This is secondary. — [autoae.online Revideo vs Remotion](https://autoae.online/blog/revideo-vs-remotion-2026)

**Reference point (Remotion licensing, which the user already knows)**
- Free for individuals and companies of up to 3 people.
- The Company License "Automators" tier costs $0.01/render with a $100/month minimum. "Creators" costs $25 per seat per month. — [Remotion pricing docs](https://www.remotion.dev/docs/license/pricing)

### Inferences
- **Revideo** is the closest MIT-licensed analogue to Remotion. A generator-based TypeScript scene is easy for an LLM to write, and it has headless Node rendering and audio. The risk is bus factor: the 15-month release gap and the commercial pivot to Midrender. Pin the version and vendor-fork it.
- **Twick** fits best when the agent should emit a JSON timeline, not code, because the track and element format looks like a simple target. The SUL license is fine for internal or self-hosted use, but not for reselling a Twick-based SDK.
- **Etro, WebAV and Diffusion Studio** cannot be used as headless server renderers without wrapping them in headless Chrome yourself. WebCodecs in headless Linux Chrome brings its own codec and GPU caveats. Diffusion Studio's watermark and Etro's GPL-3.0 add licensing friction.
- **Editly** is still useful for simple JSON5 slideshow-style edits with gl-transitions. It is effectively frozen, though, and its title layers are basic, so they are not good for animated captions.
- **Bring-your-own HTML** (puppeteer-capture or a custom beginFrame loop plus GSAP or CSS, essentially what HyperFrames and Remotion do) gives the best text shaping and the largest LLM training corpus. Video must be fed as pre-decoded frames or through WebCodecs, not `<video>` playback. Check the GSAP license if the product is itself a no-code animation builder.
- **For Bengali karaoke or per-word captions**, animate at word or grapheme-cluster granularity using `Intl.Segmenter` with a recent ICU. Do not split per character with older SplitText-style code-point splitting.

### Gaps
- No independent, recent benchmark of Revideo against Remotion against Twick render speed (frames/sec on the same hardware) was found.
- Exact Motion Canvas v4 status is unknown: no release since the Feb 2025 alpha, and no official statement was found.
- It is unverified whether Twick's render-server is built on Revideo or Motion Canvas internals. The README excerpt did not say.
- FFCreator's current GitHub activity could not be checked because the GitHub API was blocked. Only npm (July 2024) was checked.
- Headless Chrome on Linux: whether VP9-alpha WebM (needed for a matted person layer) decodes reliably under chrome-headless-shell and beginFrame was not verified in this session.

---

## Q2. Python: MoviePy v2, PyAV, OpenCV, Manim, vidgear, Pillow/skia-python/pycairo frame pipelines, VapourSynth, GStreamer/GES, MLT, libopenshot — and Bengali shaping

### Takeaway
Bengali shaping in Python hinges on whether text goes through **HarfBuzz**:
- **Correct:** Pillow with RAQM (the default in current manylinux wheels when FriBiDi is present), and therefore MoviePy v2's `TextClip`. Pango-based paths (Manim/ManimPango, MLT's `pango` producer, GStreamer `textoverlay`, PangoCairo) and libass (VapourSynth subtext or assrender) should also be correct.
- **Broken:** Pillow's `BASIC` layout engine, OpenCV's core `putText`, and **Blender 5.2 VSE text strips**. The Pillow and Blender cases were verified in local tests in this session.

PyAV and vidgear are I/O layers only.

### Cited Findings

**Release and license status (PyPI, pulled 2026-10-28)**

| Package | Version | Date | License |
|---|---|---|---|
| moviepy | 2.2.1 | 2025-05-21 | MIT |
| av (PyAV) | 19.0.2 | 2026-10-21 | BSD-3 |
| opencv-python / contrib | 5.0.0.93 | 2026-07-02 | Apache-2.0 |
| manim | 0.22.1 | 2026-10-27 | MIT |
| manimpango | 0.7.1 | 2026-10-24 | MIT |
| vidgear | 0.3.6 | 2026-10-26 | Apache-2.0 |
| skia-python | 144.1 | 2026-10-20 | BSD |
| pycairo | 1.29.2 | 2026-10-04 | LGPL-2.1 / MPL-1.1 |
| PyGObject | 3.58.1 | — | LGPL |
| Pillow | 13.0.0 | 2026-10-16 | MIT-CMU |
| vapoursynth | R81 | 2026-10-04 | LGPL-2.1+ |
| bpy (Blender as a module) | 5.2.3 | 2026-10-22 | GPL-3.0 |
| movis | 0.7.1 | 2023-11-25 | MIT (stale) |
| vidpy (MLT wrapper) | 0.2.1 | 2023 | MIT (stale) |

Sources: [PyPI moviepy](https://pypi.org/project/moviepy/), [PyPI av](https://pypi.org/project/av/), [PyPI manim](https://pypi.org/project/manim/), [PyPI vidgear](https://pypi.org/project/vidgear/), [PyPI skia-python](https://pypi.org/project/skia-python/), [PyPI Pillow](https://pypi.org/project/Pillow/), [PyPI vapoursynth](https://pypi.org/project/vapoursynth/), [PyPI bpy](https://pypi.org/project/bpy/), [PyPI movis](https://pypi.org/project/movis/)

**Pillow and MoviePy**
- **[Local test]** The Pillow manylinux wheel installed by pip (pip resolved Pillow 11.3.0 together with moviepy 2.1.2 on Python 3.13) reports these features:
  - `raqm` True, version 0.10.1
  - `harfbuzz` True, version 11.2.1
  - `fribidi` True, version 1.0.13 (from system libfribidi)
- **[Local test]** Rendering the Bengali test string:
  - With `layout_engine=ImageFont.Layout.BASIC`, conjuncts are **broken**: hasanta is visible, and ক্ষ appears as ক্ + ষ.
  - With `Layout.RAQM` the output is **correct**.
  - **MoviePy 2.1.2's `TextClip`** is also correct. It calls `ImageFont.truetype(font, font_size)` without a `layout_engine`, so Pillow picks RAQM when available.
  - Output: `/tmp/claude-0/-home-user-site/b988b61d-5cda-5294-be82-80a85dc995ce/scratchpad/shape_test.png`
- Pillow docs (8.4.x era): wheels include optional libraries, but "Raqm support requires FriBiDi to be installed separately". Ensure `libfribidi0` is present in the Docker image. — [Pillow 8.4.x installation docs](https://git.akarpov.ru/python-pillow/Pillow/src/branch/8.4.x/docs/installation.rst)
- Raqm provides bidi (FriBiDi or SheenBidi), HarfBuzz shaping and script itemization. — [libraqm (ecosyste.ms)](https://awesome.ecosyste.ms/projects/github.com%2FHOST-Oman%2Flibraqm)
- MoviePy v2 dropped ImageMagick, PyGame, OpenCV and SciPy and consolidated on Pillow. If `font` is omitted, Pillow's default font cannot render non-Latin text. — [issoh.co.jp MoviePy v2 notes](https://www.issoh.co.jp/md/tech/6079)

**OpenCV**
- Core `putText` uses Hershey fonts.
- The `cv2.freetype` module in opencv_contrib "draw[s] UTF-8 strings with freetype/harfbuzz", using HarfBuzz for glyph IDs and FreeType for rasterization. — [OpenCV freetype docs](https://docs.opencv.org/4.x/d4/dfc/group__freetype.html); [opencv_contrib freetype README](https://github.com/opencv/opencv_contrib/blob/4.x/modules/freetype/README.md)

**Manim**
- Manim's `Text` switched to Pango rendering, keeping the older Cairo path as `CairoText`.
- The PR includes Hindi "नमस्ते" and Tamil examples. — [Manim PR #609](https://github.com/ManimCommunity/manim/pull/609/files)
- ManimPango renders text to images or SVG using Pango and can register fonts. — [ManimPango docs](https://manimpango.manim.community/)

**skia-python**
- Skia's Paragraph (skparagraph) was being added to skia-python in 2024 (PR #258) and is based on FreeType and HarfBuzz. — [cairo mailing list, Aug 2024](https://lists.freedesktop.org/archives/cairo/2024-August/029577.html)
- A separate helper, `skia-harfbuzz` (0.1.0, 2025-08), adds HarfBuzz-shaped drawing to skia-python. — [PyPI skia-harfbuzz](https://pypi.org/project/skia-harfbuzz/)
- **[Local test]** skia-python 144.1 failed to import on a minimal Linux container: `ImportError: libEGL.so.1`. The `libegl1` system package is needed even for CPU rendering.

**MLT (melt, used by Kdenlive and Shotcut)**
- The MLT `pango` producer is a title generator built on Pango international text layout plus FreeType2. It accepts Pango markup. Its font map loads once per process. — [MLT ProducerPango](https://mltframework.org/plugins/ProducerPango)
- Running headless:
  - The Qt module (`qtext`, `kdenlivetitle`, `qimage`, and the `qtblend` transition) needs X11, so use `xvfb-run`. — [KDE forum](https://forum.kde.org/viewtopic.php%3Ff=265&t=141279.html)
  - MLT developer Dan Dennedy says xvfb-run doesn't need a full desktop. Without the Qt module, text falls back to gdk-pixbuf and Pango. — [MLT mailing list](https://sourceforge.net/p/mlt/mailman/message/34199526/)
- Kdenlive projects can be rendered directly with `melt project.kdenlive -consumer avformat:out.mp4 vcodec=libx264 …`. The consumer is not embedded in the project file. — [Kdenlive-devel mailing list](https://mail.kde.org/pipermail/kdenlive/2012-December/007778.html)

**VapourSynth**
- The subtext (`sub`) plugin renders ASS, SRT and WebVTT and other formats via libass plus ffmpeg, either burned in or as separate bitmaps. — [PyPI vapoursynth-subtext](https://pypi.org/project/vapoursynth-subtext/)
- assrender uses libass and is described as "the fastest… and most correct ASS renderer for Vapoursynth". — [assrender (mirror)](https://gh.r-mj.com/AmusementClub/assrender)

**GStreamer GES**
- Pitivi, the GES-based editor, had its last mirror push on 2025-04-13, and its latest release is 2023.03. — [ecosyste.ms Pitivi](https://awesome.ecosyste.ms/projects/github.com%2Fgnome%2Fpitivi); [VideoHelp Pitivi](https://www.videohelp.com/software/PiTiVi)

**libopenshot**
- Debian and deb-multimedia ship python3-openshot 0.4.0. It still depends on the Qt5 GUI libraries. — [deb-multimedia python3-openshot](https://deb-multimedia.org/dists/stable/main/binary-amd64/package/python3-openshot); [Ubuntu python3-openshot](https://packages.ubuntu.com/sv/plucky/python3-openshot)

### Inferences
- **The best Python raster pipeline** for an agent is **PyAV** (decode and encode) plus **numpy** compositing plus **Pillow-RAQM**, **PangoCairo** or **skia-python Paragraph** for text. Alternatively, MoviePy v2 as a convenience layer:
  - Its `TextClip` gets Bengali right if RAQM is present.
  - It is a 2025 release with modest activity and is known to be slow, since it is per-frame numpy.
  - Advanced captions (per-word highlight, strokes, gradients) need custom Pillow, Pango or Skia drawing.
- **Manim** shapes text well through Pango, but it is built for math explainers. Using it for talking-head video re-edits would be awkward. At best, use it to pre-render title cards as alpha video.
- **MLT/melt** is the strongest open-source "XML timeline → headless render" engine. Kdenlive and Shotcut prove the feature set: transitions, keyframes, chroma and alpha compositing, LUTs, Pango text. It needs `xvfb-run` for the Qt services, and the XML is verbose for an LLM to author.
- **VapourSynth plus libass** is a strong fit for **ASS-based animated captions**: karaoke `\k` tags, transforms and per-word styling via libass, which uses HarfBuzz. The rest of the motion-graphics stack would then live elsewhere.
- **OpenCV's** core `putText` must never be used for Bengali.

### Gaps
- MoviePy 2.2.1 was not tested. pip resolved 2.1.2 because of the Pillow pin, but the `TextClip` code path is believed unchanged.
- The skia-python Paragraph/textlayout module was not verified because of the libEGL import failure in the test container.
- Pango producer output in MLT and GStreamer `textoverlay` with Bengali was not empirically tested here. Correctness is inferred from Pango using HarfBuzz.
- The current status of GES Python bindings for headless timeline rendering was not found. Neither was libopenshot's headless text behavior.

---

## Q3. Cloud JSON-to-video APIs: Shotstack, Creatomate, JSON2Video, Plainly, Bannerbear, Rendi and others — pricing, templates, Bengali fonts

### Takeaway
Cloud JSON APIs cost about **$0.20–$1.00 per rendered minute** at 1080p:

| Service | Rate | Template model |
|---|---|---|
| Shotstack | ~$0.20–0.30/min | JSON timeline |
| Creatomate | ~$0.25–1.00/min (pixel-based credits) | RenderScript JSON |
| JSON2Video | ~$0.20–0.25/min | JSON |
| Plainly | ~$1.08–1.38/min | After Effects templates |
| Rendi | billed by GB, not minutes | ffmpeg-as-a-service |

All accept custom TTF/OTF fonts. **None publicly documents Bengali or complex-script shaping**, so Bengali must be test-rendered before committing. Shotstack's HTML asset, being browser-based, is the most likely to shape correctly.

### Cited Findings

**Shotstack**
- Pricing (third-party data; the official page could not be fetched):
  - Pay-as-you-go: about $0.30/min, with credits bought in bundles starting at $75 for 250 credits, valid 1 year.
  - Subscriptions: about $0.20/min, from $39/month.
  - Usage is billed per second, so a 30-second video is 0.5 credit. Overage carries a 30% premium.
  - Custom pricing applies from 50,000 min/year.
  - Sources conflict on the free tier (10 free credits vs no free tier). — [SpotSaaS Shotstack pricing](https://www.spotsaas.com/product/shotstack/pricing); [Plainly blog list](https://www.plainlyvideos.com/blog/best-video-editing-api)
- Fonts and text:
  - The rich-text asset supports animations, gradients, shadows and custom fonts loaded from a TTF URL in the timeline `fonts` array. — [Shotstack rich-text docs](https://shotstack.io/docs/guide/architecting-an-application/rich-text)
  - Shotstack's own tutorial on international character sets uses the **HTML asset** with a downloaded font. — [Shotstack learn: international languages](https://shotstack.io/learn/international-language-character-sets-video/)

**Creatomate**
- Billing is pixel-based: 1 credit per 100 million pixels (width × height × fps × seconds), which is about 31 credits/min at 1080p25 and about 37 at 1080p30.
- Plans:
  - Essential: $54/month for 2,000 credits, about $0.84–1.00 per 1080p minute.
  - Growth 10K: $129/month, about $0.48/min.
  - Beyond 50K: $329/month, about $0.25/min. One source lists $249 instead.
- There is a one-time 50-credit trial.
- These figures come from competitor blogs. — [Wireflow Creatomate pricing](https://www.wireflow.ai/blog/creatomate-pricing); [JSON2Video comparison](https://json2video.com/how-to/creatomate-alternative/)
- More than 1,000 Google Fonts are included, plus custom WOFF, OTF and TTF fonts declared in a `fonts` array. — [Creatomate docs: custom font](https://creatomate.com/docs/json/quick-start/use-custom-font)

**JSON2Video**
- Plans (official docs):
  - Hobby: 3,000 credits, about 50 min of Full HD.
  - Professional: 12,000 credits, about 200 min.
  - Startup: 30,000 credits, about 500 min.
  - Enterprise: 78,000 credits, about 1,300 min. — [JSON2Video plans docs](https://json2video.com/docs/v2/pricing/plans)
- Prices: Professional $49.95/month and Startup $99.95/month. Third-party listings of other prices conflict. — [JSON2Video Bannerbear-comparison page](https://json2video.com/how-to/bannerbear-alternative/); [SpotSaaS](https://www.spotsaas.com/product/json2video/pricing)
- Free plan: 600 credits, about 10 min, 60 seconds max per video, watermarked. Prepaid packs that never expire are reportedly $49.95 for 120 min. These figures are from search snippets.

**Plainly** (After Effects template rendering)
- Billing is by output length, not render time, so a 30-second video is 0.5 min. Failed renders are refunded and draft renders are free. — [Plainly help: pricing](https://help.plainlyvideos.com/docs/basics/pricing-and-security)
- Plans: Starter $69/month for 50 min with API access. Others reported are Explorer about $134 for 100 min, Team $259 for 200 min, and Pro $649 for 600 min. These are third-party figures. — [Plainly pricing](https://www.plainlyvideos.com/pricing); [SoftwareAdvice](https://www.softwareadvice.com/product/525571-Plainly/)

**Bannerbear**
- V5 animated templates cost 1 base credit plus 2 credits per second, and 60 fps doubles the cost. — [Bannerbear help: API credits](https://www.bannerbear.com/v5/help/articles/545-what-are-api-credits/)
- Video length is capped at 300 seconds. — [Bannerbear help: video length](https://www.bannerbear.com/help/articles/95-how-long-can-videos-be/)
- Third-party plan figures: $49 for 1,000 credits, $149 for 10,000, $299 for 50,000. My own arithmetic puts this at about 120 credits per animated minute, so it is expensive for video.

**Rendi** (ffmpeg commands as a cloud API)
- Free tier: 4 vCPU, 50 GB processing per month, 1-minute command cap.
- Pro: $25/month, 100 GB per month (one review says 250 GB), with a 10-minute command cap.
- Billed by data volume, not duration. — [Rendi pricing](https://www.rendi.dev/pricing); [omidsaffari review](https://omidsaffari.com/blog/rendi-pricing); [DEV comparison](https://dev.to/javidjamae/best-ffmpeg-api-services-compared-2026-35p5)

**IMG.LY CE.SDK Renderer** (self-hosted commercial)
- It is a Docker container that runs the CreativeEngine server-side "without a browser" over HTTP.
- It encodes H.264/H.265 "with full patent coverage" and takes templates plus data to produce MP4.
- Pricing is quote-only, with a 30-day trial. — [IMG.LY server-side video rendering](https://img.ly/use-cases/server-side-video-rendering); [IMG.LY pricing](https://img.ly/pricing)
- CE.SDK claims automatic text shaping, bidi layout and script-specific rendering. — [IMG.LY language support](https://img.ly/docs/cesdk/js/text/language-support-a0f010/)

**Editframe**
- Cloud rendering costs $0.02/min, the cheapest listed. A Cloud-tier subscription is required. — [editframe.com/render](https://editframe.com/render)

### Inferences
- **For an agent-generated "style spec JSON"**, Shotstack and Creatomate are the closest drop-in renderers. They have timeline or RenderScript JSON, keyframes, transitions, text animations and custom fonts.
- **Cost:** at 60-second Reels, roughly $0.20–0.50 per video at mid tiers. That is acceptable for low volume but becomes the dominant cost at scale, compared with self-hosted rendering at near-zero marginal cost.
- **Bengali** is the biggest unknown for cloud APIs:
  - Shotstack's HTML asset probably uses a browser engine, which would mean HarfBuzz shaping.
  - Creatomate's own renderer is a black box.
  - Run a conjunct test (ক্ষ, স্ব, ষ্ণ, শ্র, plus reph and ি pre-base matra) before choosing.
- **Plainly and nexrender-style After Effects services** are only worth it if designers already produce AE templates.

### Gaps
- Official current pricing pages for every vendor could not be fetched. All prices above should be re-checked on vendor sites before being quoted.
- No vendor documentation or user report confirms correct Bengali or Indic shaping in Shotstack, Creatomate, JSON2Video, Plainly or Bannerbear.
- There is no data on render latency for these APIs (seconds per output minute).

---

## Q4. Vector and animation formats: Lottie (lottie-web, rlottie, Skottie, dotLottie/ThorVG, python-lottie) and Rive for animated stickers and titles, rendered headlessly

### Takeaway
Lottie is excellent for **non-text** animated stickers, shapes, light-leak-like overlays and transitions, and is headless-renderable in several ways: ThorVG/dotLottie (active, MIT), Skottie (Skia), lottie-web inside headless Chrome, and rlottie (now archived).

**Lottie text layers are a weak spot.** rlottie supports none. ThorVG's text support is still maturing. Skottie shapes through SkShaper and HarfBuzz. Bengali titles should be rendered by the main text engine, not inside Lottie.

Rive has no official headless or offscreen renderer. Its docs point to Revideo or Remotion for server-side rendering.

### Cited Findings

**Release and license status**
- lottie-web (MIT): last release 5.13.0 (2025-05-21), before which nothing since 2023. — [npm lottie-web](https://www.npmjs.com/package/lottie-web)
- `@lottiefiles/dotlottie-web` (MIT): 0.81.0 (2026-10-06). — [npm dotlottie-web](https://www.npmjs.com/package/@lottiefiles/dotlottie-web)
- `@thorvg/lottie-player` (MIT): 1.1.3 (2026-10-16). — [npm @thorvg/lottie-player](https://www.npmjs.com/package/@thorvg/lottie-player)
- `@rive-app/canvas` (MIT runtime): 2.48.0 (2026-10-27). — [npm @rive-app/canvas](https://www.npmjs.com/package/@rive-app/canvas)
- puppeteer-lottie: last release 2020, stale. — [npm puppeteer-lottie](https://www.npmjs.com/package/puppeteer-lottie)

**rlottie (Samsung)**
- The README says the project "has been archived and is no longer maintained".
- **Text layers are entirely unsupported**, as are expressions and layer effects.
- It renders offscreen into caller-supplied buffers through `renderSync()`. — [GitHub Samsung/rlottie](https://github.com/Samsung/rlottie)
- The Python binding `rlottie-python` 1.3.8 (2025-08-23) is LGPL. — [PyPI rlottie-python](https://pypi.org/project/rlottie-python/)

**ThorVG and dotLottie**
- LottieFiles' Lottie Creator uses ThorVG to render text layers, and "ThorVG requires us to load the font data ourselves". — [LottieFiles: Text layers in Lottie Creator](https://lottiefiles.com/blog/working-with-lottie-animations/text-layers-now-in-lottie-creator)
- ThorVG's roadmap still lists expanding text animations, shape modifiers, layer effects and expressions. — [LottieFiles: Introducing ThorVG](https://lottiefiles.com/blog/working-with-lottie-animations/introducing-thorvg-powerful-graphic-library-for-lottie-animations)

**Skottie (Skia)**
- Skottie's text shaper "implements After Effects text shaping behavior using SkShaper". — [SkottieShaper.h](https://skia.googlesource.com/skia/+/87e8850388938171691d8699f7921495acc5e5b1/modules/skottie/src/text/SkottieShaper.h)
- SkShaper shapes with HarfBuzz and falls back to plain glyph lookup when HarfBuzz is not compiled in. — [SkShaper.h](https://skia.googlesource.com/skia/+/3390cdf/tools/SkShaper.h)

**Lottie text from After Effects**
- Basic single-style text converts. Per-character animators are only partially supported. — [LottieFiles AE compatibility](https://docs.lottiefiles.com/en/integrations/after-effects/09_lottie-compatibility)

**python-lottie**
- Package `lottie` 0.7.2 (2025-05-01) is **AGPL-3.0+**.
- It converts Lottie and TGS to PNG, GIF, WebP, MP4 and WebM via cairosvg and OpenCV, and renders text as shapes through fonttools. — [PyPI lottie](https://pypi.org/project/lottie/); [python-lottie README (KDE mirror)](https://lxr.kde.org/source/graphics/glaxnimate/data/lib/python-lottie/README.md)

**Rive**
- Rendering to a bitmap is not supported directly in the React runtime. For offline or server rendering, the docs point to Revideo and Remotion, which both support Rive. — [Rive docs: rendering to a bitmap](https://rive.app/docs/runtimes/react/rendering-to-a-bitmap.md)
- Rive's editor Cloud Renderer exports H.264, GIF, PNG and SVG sequences and WebM on paid plans. — [Rive docs: exporting for video](https://rive.app/docs/editor/exporting/exporting-for-video-and-static-design.md)

### Inferences
- **Recommended pattern:** keep a library of Lottie or dotLottie assets (stickers, emoji bursts, arrows, light-leak or flash overlays, transition wipes). Render them headlessly with ThorVG/dotLottie or Skottie (for example via skia-python, CanvasKit, or `@lottiefiles/dotlottie-web` inside the HTML renderer) to RGBA frames or alpha WebM or ProRes. Then composite.
- The agent should only edit Lottie **colors and timing**, not text.
- Lottie JSON is very verbose, so LLMs should **select and parameterize** existing Lottie assets, not author them.
- **Avoid python-lottie for a closed-source SaaS** because of the AGPL.
- **Avoid rlottie** for new work because it is archived.
- **Rive** is only practical inside a headless-browser renderer such as Revideo, Remotion or a custom page. It has no first-party server renderer.

### Gaps
- No direct test or documentation was found of Bengali or Indic shaping inside Lottie text layers for ThorVG, Skottie or lottie-web.
- Whether lottie-web's per-character text animators break Indic clusters was not verified.
- Whether Rive's text engine supports Indic shaping was not found.

---

## Q5. Pro NLE automation: After Effects (ExtendScript, nexrender, aerender, MOGRT), Premiere (UXP/ExtendScript), DaVinci Resolve scripting (free vs Studio, Fusion), Blender VSE plus bpy, CapCut/JianYing drafts, FCPXML, OTIO

### Takeaway
None of the pro NLEs is a good headless-Linux render target for an agent:
- **After Effects and Premiere** have no Linux version. The nexrender worker is Windows and macOS only.
- **DaVinci Resolve 21.1 removed Python scripting from the free edition**, and network or headless rendering is Studio-only ($295 one-time).
- **Blender** runs headless on Linux via `pip install bpy`, but **its VSE text strips do not shape Bengali** (verified locally in Blender 5.2.3 LTS).
- **CapCut/JianYing draft generators** (pyJianYingDraft, VectCutAPI) produce drafts on Linux, but exporting needs the Windows desktop app. JianYing 6+ encrypts drafts.
- **OTIO and FCPXML** are interchange formats, not renderers.

### Cited Findings

**After Effects and nexrender**
- nexrender (MIT) drives AE's `aerender` CLI from a JSON job: `template{src,composition}`, `assets[]` (footage, data/expressions, JSX scripts) and `actions` (pre- and post-render steps).
- `nexrender-server` runs on Windows, macOS and Linux, but **`nexrender-worker` runs only on Windows and macOS** and needs a licensed or trial AE.
- MOGRT support comes only through a third-party action.
- The tested-with list stops at AE CC 2019. — [GitHub inlife/nexrender](https://github.com/inlife/nexrender)
- npm `@nexrender/core` 1.63.3 is dated 2026-02-25, so it is still maintained. — [npm @nexrender/core](https://www.npmjs.com/package/@nexrender/core)

**Premiere Pro**
- As of November 2025 Premiere moved to UXP-based extensibility. ExtendScript integrations stay supported through September 2026. — [Premiere scripting guide](https://premiere-scripting-guide.readthedocs.io/introduction/index.html)
- The UXP DOM covers sequences, tracks and clips, and can configure and trigger exports. — [Adobe UXP Premiere API](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/)
- Developers report inconsistent `EncoderManager.exportSequence()` behavior on 26.3.0. — [Adobe dev forum](https://forums.creativeclouddeveloper.com/t/encodermanager-exportsequence-no-preset-fallback-depends-on-opening-export-mode-then-queues-only-after-cancelling-a-0-dialog/12168)
- A March 2026 feature request says UXP still lacks full promise-based sequence automation. — [Adobe community request](https://community.adobe.com/feature-requests-730/modernize-premiere-pro-scripting-api-es6-and-promise-based-architecture-uxp-1555627)
- pymiere (GPL-3.0): last release 1.4.1 (2023-05-10). — [PyPI pymiere](https://pypi.org/project/pymiere/)

**DaVinci Resolve**
- Puget Systems quotes the 21.1 notes: "We have moved the ability to script in Python to the Studio version". It says scripting was entirely removed from the free edition in 21.1, with no simple workaround other than staying on Free 21.0. — [Puget Systems, Sept 2026](https://www.pugetsystems.com/blog/2026/09/10/how-davinci-resolve-free-v21-1-scripting-changes-affect-puget-bench/)
- Studio-only features include external scripting (JS, Lua, Python) and "network, remote and headless rendering". — [CineD comparison](https://www.cined.com/davinci-resolve-an-in-depth-comparison-between-the-free-and-studio-version/)
- On the free edition, `scriptapp("Resolve")` returns nil. — [davinci-resolve-mcp-free](https://github.com/emircbngl/davinci-resolve-mcp-free)
- Studio costs $295 one-time. Resolve runs on Windows, Mac and Linux. — [davinciresolve21.com](https://davinciresolve21.com/blog/free-vs-studio); [tryuncle comparison](https://tryuncle.com/learn/davinci-resolve/davinci-resolve-vs-pinnacle-studio)

**Blender**
- `bpy` 5.2.3 (GPL-3.0, 2026-10-22) is pip-installable as a Python module for cp313 manylinux; the wheel is about 402 MB. — [PyPI bpy](https://pypi.org/project/bpy/)
- **[Local test]** Blender 5.2.3 LTS run headless via `pip install bpy` with no display. A VSE scene was built in Python: a color strip, plus a TEXT strip using Noto Sans Bengali Bold with the test string. Rendering it with `bpy.ops.render.render(write_still=True)` took about 0.7 s.
  - **Result: conjuncts are not formed.** The output shows ক্‌ষ, স্‌ব, ষ্‌ণ and শ্‌র with visible hasanta, the same failure as Pillow's BASIC engine.
  - Output: `/tmp/claude-0/-home-user-site/b988b61d-5cda-5294-be82-80a85dc995ce/scratchpad/blender_vse_bn.png`
- The older VSEIndic add-on says "Blender cannot render Indic text… properly" and works around it by rendering text with pyvips into image strips. It was tested on Blender 2.82. — [GitHub VSEIndic](https://github.com/oormicreations/VSEIndic)

**CapCut and JianYing drafts**
- **pyJianYingDraft** (Apache-2.0, about 4.7k stars, PyPI 0.3.1 dated 2026-10-14):
  - It generates JianYing drafts with clips, speed, keyframes, masks, chroma key, blend modes, stickers, transitions, filters and effects. It also supports text styling with animations, bubble and flower-text effects, and **SRT import**.
  - Template mode replaces media or text in an existing draft.
  - On Linux and macOS it can generate drafts but **not export**: "generated drafts still need to be exported in Windows JianYing".
  - Automated export works only on JianYing ≤6. It uses UI automation and needs a VIP or subscription.
  - New 10.8 drafts are often not plain JSON. — [GitHub GuanYixuan/pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft); [PyPI](https://pypi.org/project/pyJianYingDraft/)
- **VectCutAPI**, formerly CapCutAPI (Apache-2.0):
  - It is an HTTP API plus an MCP server with 11 tools that writes CapCut or JianYing drafts, selected via `draft_profile` (`capcut_legacy`, `jianying_legacy`, `jianying_pro_10`).
  - The cloud rendering module is **not open-sourced**.
  - Requirements: Python 3.10+ and the CapCut or JianYing app. — [GitHub sun-guannan/CapCutAPI](https://github.com/sun-guannan/CapCutAPI)
- JianYing 6.0+ stores `draft_content.json` AES-encrypted. CapCut International drafts are reportedly not encrypted.
  - Community tools avoid decrypting, citing legal concerns.
  - CapCut rejects BOM-prefixed JSON. — [capcut-cli jianying-encryption doc](https://raw.githubusercontent.com/renezander030/capcut-cli/master/docs/jianying-encryption.md); [capcut-cli COMPATIBILITY](https://cdn.jsdelivr.net/npm/capcut-cli-david@2.5.0/COMPATIBILITY.md)

**OTIO and FCPXML**
- OpenTimelineIO (Apache-2.0) is at 0.18.1 (2025-11-09). — [PyPI OpenTimelineIO](https://pypi.org/project/OpenTimelineIO/)
- Adapters (per v0.15 docs):
  - FCP7 XML is the route into Premiere.
  - A kdenlive adapter exists.
  - FCPX XML moved to a separate `otio-fcp-adapter`. — [OTIO adapters docs](https://opentimelineio.readthedocs.io/en/v0.15/tutorials/adapters.html); [PyPI otio-fcp-adapter](https://pypi.org/project/otio-fcp-adapter)
- Premiere's native OTIO import and export was in beta from Oct 2024 and was not yet in release as of the Feb 2025 Adobe statement. — [Adobe community: OTIO beta](https://community.adobe.com/t5/premiere-pro-beta-discussions/now-in-beta-otio-import-and-export/m-p/14992671)

### Inferences
- **For a fully headless Linux agent, discard AE, Premiere and FCP as renderers.** They are only relevant if a Windows or macOS render node with Adobe licenses exists, or if existing AE or MOGRT templates must be reused via nexrender or Plainly.
- **Resolve Studio on Linux** is technically possible: Python API, Fusion, `-nogui`. But it needs a GPU, a $295 license per machine and a fragile GUI app in a container. Free 21.1+ is unusable for scripting.
- **Blender** is a credible free headless compositor for 3D or motion-graphics passes. For Bengali, text must come in as pre-rendered images or alpha video made by HarfBuzz-capable tools. Even then, Blender adds little over MLT or HTML for 2D Reels.
- **CapCut and JianYing draft JSON** is attractive because it gives access to CapCut's huge library of text animations, effects and transitions, and pyJianYingDraft and VectCutAPI already speak it. But it is **not a server render path**: it needs a desktop app (Windows for automated export), may need a paid account, and depends on an undocumented, encrypted, frequently changing format. Use it only for a "hand-off draft to a human editor" feature.
- **OTIO** is a sensible internal or interchange representation for cuts. It is weak at motion graphics or captions, so an agent could export OTIO for human finishing in Resolve, Premiere or Kdenlive.

### Gaps
- It is unverified whether Resolve Studio 21.x's `-nogui` and headless render mode works reliably in Docker on Linux without X. No source was found.
- AE text-engine Bengali shaping was not researched. AE has a South Asian and Middle Eastern text engine option, but no source was gathered here.
- Whether Blender's 3D Text object (as opposed to VSE strips) or any 5.x build has HarfBuzz shaping was not checked. Only the VSE text strip was tested.

---

## Q6. Which combination is best for an agent? Style-spec JSON → renderer; HTML/CSS vs Python raster vs NLE

### Takeaway
For Bengali short-form edits on a headless Linux server, the strongest architecture has three parts:
1. **An agent-authored, declarative style spec (JSON)** describing the cut list from transcript or OTIO-like timing, caption style, overlays and transitions.
2. **One browser-based renderer**, such as Revideo (MIT) or an in-house HTML page captured deterministically with chrome-headless-shell beginFrame, using GSAP or CSS. This gives HarfBuzz-correct Bengali, web fonts, CSS effects, Lottie/dotLottie and Rive players, and LLM-friendly code.
3. **ffmpeg** (already known) for pre-decoding, alpha matte compositing and final encode.

Python raster (PyAV plus Pillow-RAQM, Pango or Skia) is the fallback, and MLT/melt is the open-source NLE-grade alternative. Pro NLEs and CapCut drafts are hand-off formats, not render engines.

### Cited Findings

**Text-shaping correctness (verified or documented)**

| Engine | Bengali result | Basis |
|---|---|---|
| Chrome (HarfBuzz) | Correct | [HarfBuzz](https://en.wikipedia.org/wiki/HarfBuzz) |
| Node canvas: @napi-rs/canvas, skia-canvas, node-canvas | Correct | [Local test] |
| Pillow RAQM / MoviePy v2 TextClip | Correct | [Local test] |
| Pango (Manim, MLT pango) | Correct | [Manim PR](https://github.com/ManimCommunity/manim/pull/609/files); [MLT pango](https://mltframework.org/plugins/ProducerPango) |
| libass (VapourSynth subtext) | Correct | [vapoursynth-subtext](https://pypi.org/project/vapoursynth-subtext/) |
| OpenCV freetype module | Correct | [OpenCV docs](https://docs.opencv.org/4.x/d4/dfc/group__freetype.html) |
| Pillow BASIC | **Broken** | [Local test] |
| Blender 5.2 VSE text strip | **Broken** | [Local test] |
| rlottie text | **No text support at all** | [rlottie](https://github.com/Samsung/rlottie) |

**Determinism and video in browsers**
- Deterministic browser capture is best on Linux with chrome-headless-shell.
- `<video>` playback during capture is unreliable, so frames should be pre-extracted or decoded with WebCodecs. — [HeyGen research](https://www.heygen.com/research/html-to-video); [puppeteer-capture README](https://cdn.jsdelivr.net/npm/puppeteer-capture@1.58.0/README.md)

**Headless JSON-timeline engines that exist today**
- Twick: JSON tracks, then Puppeteer plus FFmpeg. — [Twick](https://github.com/ncounterspecialist/twick)
- Editly: JSON5. — [Editly](https://github.com/mifi/editly)
- MLT: XML, via `melt`. — [Kdenlive-devel](https://mail.kde.org/pipermail/kdenlive/2012-December/007778.html)
- Cloud APIs: Shotstack, Creatomate, JSON2Video. — see Q3

**Licensing summary for commercial SaaS**

*Free (OSI licenses):*
- MIT: Revideo, Motion Canvas, Editly, FFCreator, WebAV, lottie-web, dotLottie, ThorVG player, Rive runtime, MoviePy, Manim, the canvas libraries.
- Apache-2.0: OTIO, vidgear, OpenCV, pyJianYingDraft, VectCutAPI.
- BSD: PyAV, skia-python, timecut.
- MPL-2.0: Mediabunny.
- LGPL: MLT, VapourSynth, pycairo, PyGObject.

*Copyleft or restricted:*
- GPL-3.0: Etro, bpy (Blender).
- AGPL: python-lottie and Theatre.js Studio.
- Source-available or conditional: Twick (SUL), Editframe (free for 3 or fewer employees), Diffusion Studio (watermark unless paid), GSAP (free, but no competing no-code animation builders).

*Paid only:* Resolve Studio ($295), Adobe CC.

Sources are in Q1–Q5.

### Inferences

**Recommended stack**

*Spec layer.* An LLM emits a compact JSON "edit decision + style spec" with these sections:
- `cuts[]` from the transcript
- `captions{style, words[] with times}`
- `broll[]`
- `overlays[]`, referencing a Lottie or asset library by ID
- `transitions[]`
- `person_matte{src_alpha_video}`
- `bg_graphics`

A deterministic compiler, written by humans and tested, turns this spec into renderer code. The LLM should not hand-write the full renderer code each time. This gives validation, reproducibility and cheap retries.

*Primary renderer: an HTML/canvas renderer in headless Chromium.* Use Revideo for an MIT, Remotion-like DX, or an in-house page plus puppeteer-capture.
- Pros:
  - Correct Bengali shaping and line-breaking.
  - CSS blend modes for light leaks (`mix-blend-mode: screen`), filters, masks and SVG.
  - GSAP and Lottie in the same scene.
  - Huge LLM familiarity.
- Cons:
  - Slower than native, with per-frame screenshot cost.
  - Video decode inside the browser is tricky. Pre-extract frames, or composite the base video in ffmpeg and render only the overlay layer as alpha.

*Layered compositing pattern for a matted person in front of graphics.*
1. Background graphics or b-roll layer, rendered in HTML or Lottie.
2. Person layer: an alpha video from the matting model.
3. Foreground captions and stickers: HTML rendered with alpha.
4. ffmpeg `overlay` or blend in the order 1 → 2 → 3 (or Python/numpy).

This keeps the browser away from heavy video decode and makes each layer cacheable.

*Python fallback.* PyAV plus numpy plus Pillow-RAQM (ensure libfribidi and libraqm) or PangoCairo, or skia-python with libegl1, for simple caption burn-in at high throughput. Or VapourSynth plus libass if captions are expressed as ASS with karaoke tags.

*NLE-grade open-source alternative.* MLT/melt XML (Kdenlive or Shotcut feature set) plus `xvfb-run`. It is good for transitions, keyframes and compositing. Verbose XML is a cost for LLM authoring, but a compiler from the style spec hides it.

*Cloud APIs* (Shotstack, Creatomate) are for teams that want zero render infrastructure. Budget $0.20–$1 per minute and test Bengali conjuncts first.

*Avoid as primary renderers:*
- Blender VSE (Bengali text broken)
- Resolve free 21.1+ (no scripting)
- AE and Premiere (no Linux)
- CapCut drafts (desktop export only, encrypted format)
- rlottie (archived, no text)
- Etro, WebAV and Diffusion Studio (browser-only)
- Theatre.js and timecut (stale)

*Caption-animation detail for Bengali.* Split words with `Intl.Segmenter` (word granularity) and animate per word or per grapheme cluster. Never split per code point. Verify fonts (Noto Sans Bengali, Hind Siliguri, Anek Bangla, Baloo Da 2) have the needed conjunct coverage.

### Gaps
- No apples-to-apples benchmark exists of HTML capture against PyAV/Pillow against MLT for 1080×1920 30 fps short-form renders. Real throughput numbers would need in-house testing.
- Alpha-video interchange (VP9-alpha WebM vs ProRes 4444 vs PNG sequence) performance across these renderers was not researched here.
- No public case study was found of an AI agent driving MLT or Revideo for Bengali (or other Indic) short-form production.
