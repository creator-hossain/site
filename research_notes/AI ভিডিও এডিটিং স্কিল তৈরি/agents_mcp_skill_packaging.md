# Existing AI Video-Editing Projects/Agents/MCP Servers, and How to Package the Capability as a Claude Agent Skill

Research date: 2026-10-28. GitHub star counts, licenses (SPDX id as GitHub detects it) and "last push" dates come from the GitHub repository-search API, queried on 2026-10-28. Where only `updated_at` was available, that field also changes when a repo is starred, so it is not a reliable last-commit date; those rows say "updated". Network notes: arxiv.org, alphaxiv.org and remotion.dev could not be reached from this session (DNS blocked), so the paper findings rely on search-engine abstracts and secondary summaries (Emergent Mind, Hugging Face Papers, CVF/NeurIPS listings). Those findings are flagged where it matters.

## 1. Open-source AI video editors and agents: what exists, stack, license, activity

### Takeaway
The mature, actively maintained building blocks are: **auto-editor** (silence/motion cutting, exports NLE timelines), **MoviePy/FFmpeg**, **Remotion** and **HyperFrames** (code-to-video rendering), **pycaps** (CSS-animated captions), **FunClip/VideoLingo/NarratoAI** (ASR-driven clipping, subtitles, commentary), **OpenCut** (OSS CapCut alternative), plus agent frameworks such as **HKUDS VideoAgent**, **Director (VideoDB)** and **FireRed-OpenStoryline**. Several popular shorts generators (ShortGPT, ClipsAI, Reelsfy, captacity) are stale: no push in 18 months or more. Treat them as reference code only.

### Cited Findings

**Silence / first-pass cutting**
- **auto-editor** (WyattBlue/auto-editor): 5,642★, **Unlicense** (public domain), last push 2026-10-27; written in **Nim**. It cuts silence or inactivity using audio loudness by default, or motion (`--edit motion:threshold=0.02`, boolean combos such as `"(or audio:0.03 motion:0.06)"`, dB thresholds like `audio:-19dB`). `--margin` defaults to 0.2s and can be asymmetric (`--margin 0.3s,1.5sec`). Label/action system: `--edit:2 audio:-12dB --when:2 speed:1.5`. It **exports timelines** to Premiere XML (`--export premiere`), DaVinci Resolve (`resolve`), Final Cut Pro (`final-cut-pro`), ShotCut, Kdenlive and `clip-sequence`, and ships an agent skill (`npx skills add WyattBlue/auto-editor`) — [GitHub](https://github.com/WyattBlue/auto-editor)

**Agentic editing frameworks**
- **HKUDS/VideoAgent**: 1,975★, MIT, last push 2026-07-22. "All-in-One Agentic Framework for Video Understanding and Editing, and Remaking". The README lists it as an EMNLP 2026 paper, arXiv 2606.23327. Architecture: intent analysis (explicit/implicit sub-intents), a graph-powered workflow whose nodes are tool capabilities, two-step self-evaluation and a Storyboard Agent. Tasks include meme remakes, crosstalk, commentary, video overviews, **beat-synced edits**, music videos and cross-lingual adaptation. Stack: **Claude powers the "Agentic Graph Router" and is required**; DeepSeek/GPT/Gemini handle other functions; CosyVoice, fish-speech, seed-vc, DiffSinger, Whisper large-v3-turbo, ImageBind; Python 3.10 with ffmpeg; about 8 GB GPU — [GitHub](https://github.com/HKUDS/VideoAgent)
- The VideoAgent paper's rhythm-analysis agent uses **librosa and scipy for beat detection** and syncs cuts to beats, retrieving scenes from shot-level descriptions — [arXiv HTML 2606.23327v2 via search](https://arxiv.org/html/2606.23327v2)
- **Director by VideoDB** (video-db/Director): 1,565★, MIT, last push 2026-01-23. A "ChatGPT for videos" framework: a reasoning engine orchestrates 20+ prebuilt agents (summarize, search, clip, dub, subtitle, text-to-movie, highlight creator). Python 3.9+ backend, Node 22 frontend. It is built on VideoDB's cloud "video-as-data" infrastructure, with a hosted version at chat.videodb.io. New agents are added by copying `sample_agent.py` and registering it in `handler.py` — [GitHub](https://github.com/video-db/Director)
- **FireRed-OpenStoryline**: about 3,573★ (updated 2026-10-27), Apache-2.0, open-sourced 2026-02-10. A natural-language editing agent: LLM planning plus tool orchestration through an MCP server (`src/open_storyline/mcp/`), built on LangChain, MoviePy and FFmpeg. Features: media search and segmentation, script generation with **few-shot style transfer from reference text**, beat-synced music, ASR rough cut that removes fillers and repeats (added 2026-03-22), and AI-generated transition shots (added 2026-04-02; uses paid third-party video generation). Notably, **"Style Skills" save a complete editing workflow as a reusable Skill** that can be applied to new media, stored under `.storyline/skills` / `.claude/skills`. It ships Claude Code skills `/openstoryline-install` and `/openstoryline-use` — [GitHub](https://github.com/FireRedTeam/FireRed-OpenStoryline)
- **diffusionstudio/agent** ("The agentic video editing framework"): 296★, MIT, **last push 2025-02-10 (stale)**. Its engine **diffusionstudio/core** (browser WebCodecs compositing): 1,249★, MPL-2.0, last push 2025-11-18 — [agent](https://github.com/diffusionstudio/agent), [core](https://github.com/diffusionstudio/core)

**Descript-like / transcript-based editing**
- **OpenCut** ("The open-source CapCut alternative"): 96,540★, MIT, created 2025-06-22, last push 2026-09-24 — [GitHub](https://github.com/OpenCut-app/OpenCut)
- **audapolis** (an editor for spoken-word audio with automatic transcription, Descript-style): 1,901★, **AGPL-3.0**, last push 2026-06-24 — [GitHub](https://github.com/bugbakery/audapolis)
- **LosslessCut**: 45,330★, GPL-2.0, last push 2026-10-27. A lossless trim/cut tool, not AI — [GitHub](https://github.com/mifi/lossless-cut)
- Small newer talking-head tools: timkulbaev/ai-video-editor (removes silences, filler words and restart phrases with Silero VAD and faster-whisper, includes an MCP server, 14★), and marvtub/takes-public (macOS teleprompter/recorder whose agent cuts the edit through a "takes" MCP server, 38★, created 2026-10-04) — [ai-video-editor](https://github.com/timkulbaev/ai-video-editor), [takes-public](https://github.com/marvtub/takes-public)

**Shorts / OpusClip-style generators**
- **MoneyPrinterTurbo**: GitHub API reports 135,890★, MIT, last push 2026-10-28. Generates HD short videos from a topic or keyword (script, stock footage, TTS, subtitles) — [GitHub](https://github.com/harry0703/MoneyPrinterTurbo). The star count is far higher than my training-era knowledge (tens of thousands), but it is what the API returned.
- **AI-Youtube-Shorts-Generator**: now at **Anil-matcha/AI-Youtube-Shorts-Generator**, 5,631★ (updated 2026-10-28). An "open-source alternative to Opus Clip, Vidyo.ai, Klap & SubMagic": LLM highlight detection, Whisper transcription, automatic 9:16 vertical crop. The original SamurAIGPT path did not resolve, and the move is inferred. License not captured — [GitHub](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator)
- **FunClip** (Alibaba ModelScope): 6,465★, MIT, last push 2026-10-08. FunASR-powered transcription, subtitles and **LLM-assisted clipping** with a local Gradio UI — [GitHub](https://github.com/modelscope/FunClip)
- **NarratoAI**: 11,578★, MIT, last push 2026-10-24. One-click AI commentary ("解说") plus editing — [GitHub](https://github.com/linyqh/NarratoAI)
- **VideoLingo**: 18,963★, Apache-2.0, last push 2026-09-30. Subtitle segmentation, translation, alignment and dubbing — [GitHub](https://github.com/Huanshere/VideoLingo)
- **ShortGPT**: 8,079★, MIT, **last push 2025-02-10 (stale)** — [GitHub](https://github.com/RayVentura/ShortGPT)
- **ClipsAI** (Python library that converts long videos into clips): 558★, MIT, **last push 2024-01-17 (stale)** — [GitHub](https://github.com/ClipsAI/clipsai)
- **reels-clips-automator / Reelsfy**: 232★, MIT, **last push 2023-09-23 (stale)** — [GitHub](https://github.com/eddieoz/reels-clips-automator)

**Captions / subtitle animation**
- **pycaps**: 230★, MIT, last push 2026-09-30, **alpha** (not on PyPI). Subtitles are styled with CSS, with state selectors such as `.word-being-narrated`. Word-level timing comes from Whisper or faster-whisper, or from imported `whisper_json`/`srt`/`vtt`. Includes templates (`minimalist`, `default`), regex/wordlist/AI tagging, and effects (pop, slide, typewriter, emoji, SFX). Rendering uses Playwright and Chromium (`CssSubtitleRenderer`) or the lighter `PictexSubtitleRenderer`. CLI example: `pycaps render --input my_video.mp4 --template minimalist`; Python API: `CapsPipelineBuilder` — [GitHub](https://github.com/francozanardi/pycaps)
- **captacity** ("Add Automatic Captions to YouTube Shorts with AI"): 139★, MIT, **last push 2024-06-07 (stale)** — [GitHub](https://github.com/unconv/captacity)
- **Remotion template-tiktok**: 294★, last push 2026-10-16. TikTok-style captions with Whisper.cpp; the `medium.en` model (about 1.5 GB) is downloaded by default and configured in `whisper-config.mjs`. Run `node sub.mjs [file|folder]`, then `npx remotion render`. "For some entities a company license is needed" — [GitHub](https://github.com/remotion-dev/template-tiktok)

**Programmatic rendering engines**
- **Remotion**: 68,315★, last push 2026-10-27. Its license is not OSI (GitHub reports NOASSERTION): free for individuals, non-profits and **for-profit organizations with up to 3 employees**; others need a company license. Selling or relicensing derivatives of Remotion is prohibited. The page notes the license will change slightly in Remotion 5.0 — [GitHub](https://github.com/remotion-dev/remotion), [LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)
- **HyperFrames** (HeyGen): 74,047★, **Apache-2.0**, created 2026-03-10, last push 2026-10-28. "Write HTML. Render video. Built for agents." An HTML composition with data attributes is seeked frame by frame in headless Chrome and encoded with FFmpeg, which makes it deterministic. No build step; needs Node 22+ and FFmpeg. Supports GSAP, CSS, Lottie, Three.js, Anime.js and WAAPI, shader transitions, kinetic caption blocks and a registry of about 450 blocks — [GitHub](https://github.com/heygen-com/hyperframes)
- **MoviePy**: 15,046★, MIT, last push 2026-08-26 — [GitHub](https://github.com/Zulko/moviepy)
- **editly** ("Slick, declarative command line video editing & API"): 5,559★, MIT, last push 2025-05-12 — [GitHub](https://github.com/mifi/editly)

### Inferences
- For a Claude skill, the most reusable components are permissively licensed and active: auto-editor (Unlicense) for the first-pass silence cut, which also gives free NLE-XML export; FFmpeg and MoviePy for assembly; pycaps (MIT, alpha) or HyperFrames (Apache-2.0) for animated captions and motion graphics; FunClip/faster-whisper for ASR. Use Remotion only if the user's organization qualifies for the free tier or holds a company license.
- HKUDS VideoAgent and FireRed-OpenStoryline are the closest architectural precedents for a "plan, then call tools, then self-check" editing agent, and OpenStoryline's "Style Skills" is the closest OSS precedent for storing an editing style as a Skill.
- Stale shorts generators (ShortGPT, ClipsAI, Reelsfy, captacity) are useful mainly as reference implementations of highlight detection and 9:16 auto-reframe heuristics.

### Gaps
- The exact license of Anil-matcha/AI-Youtube-Shorts-Generator and the true last-commit dates of repos returned with `updated_at` only (OpenStoryline, AI-Youtube-Shorts-Generator) were not captured.
- No dedicated search was run for "open source Descript alternative" beyond audapolis, OpenCut and the transcript-cut tools above.
- Whether LAVE, ExpressEdit and EditDuet released code was not checked.

## 2. MCP servers for video editing: which are maintained and what they expose

### Takeaway
Maintained, high-signal servers include the **DaVinci Resolve MCP** (samuelgursky, MIT, very active, 37 compound or 390 granular tools), **Premiere Pro MCPs** (hetpatel-11 and leancoderkavy, CEP/ExtendScript bridges), **After Effects MCP** (Dakkshin, MIT), **VectCutAPI** (CapCut/JianYing draft generator with MCP, Apache-2.0), **Blender MCP** (now `ahujasid/mcp-for-blender`, 32.5k★), the **Shotstack** official MCP (beta, cloud), the **VideoDB** `videodb-director-mcp`, and FFmpeg-based servers. Among FFmpeg servers, **kinocut** (Apache-2.0, 205 tools, guardrails) is the most developed. The early ffmpeg MCPs (egoist, misbahsy) are stale.

### Cited Findings
- **DaVinci Resolve MCP** (samuelgursky/davinci-resolve-mcp): 3,809★, MIT, last push 2026-10-27, README badge v4.15.5. Three servers:
  - a **compound server with 37 tools** (examples: `resolve_control`, `setup`, `media_analysis`, `analyze_media`; "136 guarded workflow actions across 9 tools")
  - a **granular server with 390 tools**, one per API method
  - an optional Node **offline server with 18 tools** (`drp`, `drt`, `drx`, `project_db`, `pipeline`, `conform`, `fusion`) that edits project files without Resolve running

  Tool categories: project, media pool, timeline and conform, color, Fusion, Fairlight, render. **External scripting requires Resolve Studio.** An in-app bridge works on the free edition, but Resolve 21.1 moved Python scripting to Studio. Needs Resolve 18.5+ and Python 3.10+. It bundles `docs/SKILL.md` ("Operational context for AI assistants"), AGENTS.md and CLAUDE.md — [GitHub](https://github.com/samuelgursky/davinci-resolve-mcp)
- Alternative Resolve servers: lordhoell/davinci-resolve-mcp ("MCP server + Claude Code skill exposing the complete DaVinci Resolve scripting API (440+ tools)", 23★) and guycochran/resolve-mcp-server (53 tools, 13★) — [lordhoell](https://github.com/lordhoell/davinci-resolve-mcp), [guycochran](https://github.com/guycochran/resolve-mcp-server)
- **Premiere Pro MCPs**:
  - hetpatel-11/Adobe_Premiere_Pro_MCP: 771★, TypeScript, created 2025-07-07, CEP/ExtendScript/UXP
  - leancoderkavy/premiere-pro-mcp: 448★, "local-first … through a local CEP bridge", created 2026-02-27
  - ayushozha/AdobePremiereProMCP: 129★, Go/Rust/Python/TS
  - antipaster/Adobe-Premiere-Pro-MCP: "170+ editing tools", 40★
  - sylphiette269/premiere-mcp-editor-cn: rough cut driven by documents, **reference videos**, prompts and footage folders, 8★

  All updated in Oct 2026 — [GitHub search results](https://github.com/hetpatel-11/Adobe_Premiere_Pro_MCP), [leancoderkavy](https://github.com/leancoderkavy/premiere-pro-mcp), [ayushozha](https://github.com/ayushozha/AdobePremiereProMCP), [antipaster](https://github.com/antipaster/Adobe-Premiere-Pro-MCP), [sylphiette269](https://github.com/sylphiette269/premiere-mcp-editor-cn)
- **After Effects MCP** (Dakkshin/after-effects-mcp): 807★, MIT, last push 2026-04-01. Remote control of compositions, text, shapes, solids and properties via an ExtendScript bridge — [GitHub](https://github.com/Dakkshin/after-effects-mcp)
- **VectCutAPI** (sun-guannan/VectCutAPI; page links still say "CapCutAPI", so it appears to be a rename): 2,337★, Apache-2.0, last push 2026-10-24. Generates **CapCut/JianYing draft folders** (`dfd_…`) that you copy into the app's drafts directory, with profiles `capcut_legacy`, `jianying_legacy` and `jianying_pro_10`. MCP over stdio (`mcp_server.py`; test output mentions 11 tools, including `create_draft`, `add_video`, `add_text`, `add_video_keyframe`, `save_draft`). HTTP server `capcut_server.py` runs on port 9001. Features: subtitles (SRT import and styling), filters and transitions, stickers, keyframes. Caveats: needs the desktop app to view or render, and the cloud rendering, web client and "MCP Editing Agent" code are **not open-sourced** — [GitHub](https://github.com/sun-guannan/VectCutAPI)
- Other CapCut/NLE MCPs: MigueDuque/capcut-mcp-server-extended (12★); AISEO-VirtualabDigital/mcp-video-editor (CapCut and OpenCut, 50 tools, dry-run, created 2026-10-26, 51★); AMMIROSOH/Kdenlive-mcp (headless Kdenlive, 12★) — [capcut-ext](https://github.com/MigueDuque/capcut-mcp-server-extended), [mcp-video-editor](https://github.com/AISEO-VirtualabDigital/mcp-video-editor), [Kdenlive-mcp](https://github.com/AMMIROSOH/Kdenlive-mcp)
- **Blender MCP**: the ahujasid repo now appears as **ahujasid/mcp-for-blender**, 32,532★, Python, created 2025-03-07, updated 2026-10-28 ("Community plugin to control Blender 3D with any LLM … Not affiliated with the official Blender Foundation") — [GitHub](https://github.com/ahujasid/mcp-for-blender)
- **Shotstack MCP** (official, **beta**): npm `@shotstack/shotstack-mcp-server` runs via npx and supports remote HTTP (Claude.ai, ChatGPT) and local stdio. It works **only with production API keys**. Key tools are `studio` (an interactive editing canvas in chat), `render_video` (returns a render ID) and `get_render_status`. Third-party listings give 12 or 23 tools, so the full official list is unconfirmed — [Shotstack docs](https://shotstack.io/docs/guide/mcp-integration/mcp-overview), [Shotstack blog](https://shotstack.io/learn/connect-shotstack-to-ai-tools-with-mcp/), [npm via ecosyste.ms](https://packages.ecosyste.ms/registries/npmjs.org/packages/@shotstack%2Fshotstack-mcp-server/versions/1.0.3)
- **VideoDB MCP**: `uvx videodb-director-mcp --api-key=VIDEODB_API_KEY` connects to the Director backend and offers "a single tool for many workflows". The toolkit also publishes `llms.txt` and `llms-full.txt`. Repo video-db/agent-toolkit: 49★, last push 2026-03-26, no license detected — [GitHub](https://github.com/video-db/agent-toolkit)
- **FFmpeg MCPs**:
  - **kinocut** (KyaniteLabs, formerly `mcp-video`): Apache-2.0, v1.16.5 released 2026-10-27, 223★. Serves **20 curated tools by default; `KINOCUT_TOOLS=all` exposes 205 MCP tools and 177 CLI commands**. Categories include core editing (32), Hyperframes (18), AI-assisted media (11; transcription, scene detection, upscaling, stem separation) and transitions (3). Guardrails: typed tools instead of free-form ffmpeg flags, preflight checks, structured results with "Video Receipts" (hashes and provenance), QA checkpoints, explicit consent before overwriting. Bundles `skills/kinocut/SKILL.md` and `kinocut-repurpose`. Install: `claude mcp add kinocut -- uvx --from kinocut kino --mcp` — [GitHub](https://github.com/KyaniteLabs/kinocut)
  - video-creator/ffmpeg-mcp: 153★, MIT, last push 2026-05-20 — [GitHub](https://github.com/video-creator/ffmpeg-mcp)
  - egoist/ffmpeg-mcp: 122★, **no license**, last push 2025-03-29 (stale) — [GitHub](https://github.com/egoist/ffmpeg-mcp)
  - misbahsy/video-audio-mcp: 89★, MIT, last push 2025-05-24 (stale) — [GitHub](https://github.com/misbahsy/video-audio-mcp)
- Other agent-native editors with MCP:
  - Cassette-Editor/oh-my-cassette: "AI video editing plugin & MCP server for Claude Code, Codex…", 126★, created 2026-06-10
  - AH64-dll/OpenEdit: ingest, transcribe, edit graph, MLT/ffmpeg render, QC; 53★
  - artokun/comfyui-mcp: 178 tools and 36 AI skills for ComfyUI image/video generation; 872★

  [oh-my-cassette](https://github.com/Cassette-Editor/oh-my-cassette), [OpenEdit](https://github.com/AH64-dll/OpenEdit), [comfyui-mcp](https://github.com/artokun/comfyui-mcp)

### Inferences
- There are two styles of NLE MCP: those that drive a running app (Resolve, Premiere, AE through scripting bridges, which needs a paid app or Studio license and a desktop GUI) and those that write project or draft files offline (VectCutAPI drafts, Resolve offline `drp/drt`, auto-editor XML). For a portable Claude skill, the file-writing approach (a timeline JSON compiled to FFmpeg, or exported as FCPXML/Premiere XML/CapCut draft) avoids GUI dependencies and works in Claude Code and headless containers.
- kinocut's design choices (curated default tool subset, typed tools instead of raw flags, preflight and QA gates, provenance receipts) are directly applicable to a skill's bundled scripts and match Anthropic's "plan-validate-execute" guidance (Section 4).

### Gaps
- Remotion's own MCP server (if any) could not be verified because remotion.dev was blocked. The remotion-dev/skills `/remotion-docs` skill (docs search) was verified instead (Section 3).
- The official Shotstack tool list and full VectCutAPI tool names beyond five were not retrieved. Tool lists for the Premiere and AE MCPs were taken from repo descriptions, not READMEs.
- Last-commit dates for the repos from minimal search output (Premiere MCPs, Blender MCP) are `updated_at` values, not commit dates.

## 3. Existing Agent Skills related to video: what exists and how they are structured

### Takeaway
Anthropic's official `anthropics/skills` repo has **no video skill**. Its media-adjacent skills are creative/design and document skills. The richest video skills come from vendors: **Remotion** (`remotion-dev/skills`, 12 skills) and **HyperFrames** (7 skills, also a Claude Code plugin marketplace). Other video-related skills are bundled with MCP servers (Resolve MCP, kinocut, OpenStoryline, auto-editor), and a growing set of community ffmpeg/editing skills is installable through `npx skills add` (skills.sh) or `/plugin marketplace add`.

### Cited Findings
- **anthropics/skills**: about 184k★, last push 2026-10-09. Layout: `.claude-plugin/` (marketplace config), `skills/`, `spec/`, `template/`, `THIRD_PARTY_NOTICES.md`. Categories: Creative & Design, Development & Technical (including MCP server generation), Enterprise & Communication, and Document Skills. `docx/pdf/pptx/xlsx` are **source-available, not open source**; many others are Apache-2.0. Install: `/plugin marketplace add anthropics/skills`, then `/plugin install document-skills@anthropic-agent-skills` or `example-skills@anthropic-agent-skills`. The README does not mention video skills — [GitHub](https://github.com/anthropics/skills)
- **Template SKILL.md** in anthropics/skills: frontmatter with `name` (lowercase, hyphens) and `description`, then a body with Instructions, Examples and Guidelines sections — [GitHub](https://github.com/anthropics/skills)
- **remotion-dev/skills**: 5,794★, last push 2026-10-26, no license detected. Skills: `/remotion-best-practices` (umbrella), `/remotion-create`, `/remotion-markup` (compositions, animation, layout, typography, media, effects, audio, fonts, timing), `/remotion-studio`, `/remotion-render`, `/remotion-maps`, **`/remotion-captions`**, `/remotion-saas`, `/remotion-interactivity`, `/remotion-docs` (searches docs and fetches pages as Markdown), `/remotion-upgrade`, `/remotion-multimedia` (Mediabunny). Install: `npx skills add remotion-dev/skills` or `gh skill install remotion-dev/skills`; `bun create video` also offers them — [GitHub](https://github.com/remotion-dev/skills)
- **HyperFrames skills**: 7 skills. The core set is `/hyperframes` (entry point), `/hyperframes-cli`, `/hyperframes-registry` (about 450 blocks) and `/media-use` (music, images, voiceover); on demand are `/figma`, `/slideshow` and `/remotion-to-hyperframes`. Install as a Claude Code plugin with `claude plugin marketplace add heygen-com/hyperframes` then `claude plugin install hyperframes@hyperframes`, or standalone with `npx skills add heygen-com/hyperframes`; update with `npx hyperframes skills update` — [GitHub](https://github.com/heygen-com/hyperframes)
- **Skills bundled with tools**: auto-editor (`npx skills add WyattBlue/auto-editor`) — [GitHub](https://github.com/WyattBlue/auto-editor); DaVinci Resolve MCP `docs/SKILL.md` — [GitHub](https://github.com/samuelgursky/davinci-resolve-mcp); kinocut `skills/kinocut/SKILL.md` and `kinocut-repurpose` — [GitHub](https://github.com/KyaniteLabs/kinocut); OpenStoryline `/openstoryline-install` and `/openstoryline-use`, plus user-saved "Style Skills" — [GitHub](https://github.com/FireRedTeam/FireRed-OpenStoryline)
- **kmilo93sd/agent-video-editor** is a structural exemplar of an "editing judgment" skill, despite having only 6★. Layout under `skills/editing-videos/`:
  - `SKILL.md` (process, core rules, recipe index) and `review-checklist.md`
  - `references/` (pacing and cuts, hooks and retention, graphics and captions, audio, color, thumbnails, licenses, tools)
  - `recipes/` (one per video type, loaded on demand)
  - `library/` (128 CC0 sounds/music with a search tool)
  - `graphics/` (26 CC0 HyperFrames graphics)
  - `memes/` (rights reference)
  - `evals/`

  Encoded rules include:
  - music 18–25 dB under the voice, with ducking
  - loudness: **-14 LUFS / -1 dBTP for YouTube**, -16 LKFS for podcasts
  - captions at **42 characters per line, 2 lines, 20 frames minimum**
  - graphics enter at most 0.5 s before the word that names them
  - zooms only when motivated and never across a cut

  Licenses: code MIT, assets CC0. Install via `npx skills add` or `/plugin marketplace add kmilo93sd/agent-video-editor` — [GitHub](https://github.com/kmilo93sd/agent-video-editor)
- **Community ffmpeg/editing skills** (from search snippets; not individually verified):
  - mhnadali/mh-video-editor-skill: "beat-synced short-form video editing with FFmpeg (EDL-based, cached renders, QA gate)"
  - 6missedcalls/video-editing-skill: trim, jump cut, captions in Hormozi/standard/minimal styles; pure Bash + FFmpeg + Whisper
  - kajisho5/ffmpeg-skill: 42 FFmpeg tools with a machine-readable contract and an MCP server
  - ychoi-kr/claude-ffmpeg-skill: notes that Claude already knows ffmpeg well

  [mh-video-editor-skill](https://github.com/mhnadali/mh-video-editor-skill), [video-editing-skill](https://github.com/6missedcalls/video-editing-skill), [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill), [ychoi-kr/claude-ffmpeg-skill](https://github.com/ychoi-kr/claude-ffmpeg-skill)
- **Marketplaces and directories**:
  - **anthropics/claude-plugins-official** ("Official, Anthropic-managed directory of high quality Claude Code Plugins"): 44,977★, Apache-2.0, created 2025-11-20. The name `claude-plugins-official` is reserved — [GitHub](https://github.com/anthropics/claude-plugins-official), [Claude Code docs](https://code.claude.com/docs/en/plugin-marketplaces)
  - **skills.sh and the `skills` CLI** (Vercel, launched 2026-01-20): `npx skills add <owner/repo>` installs from git repos into 20+ agents, and skills.sh is a directory and leaderboard. Its docs say it cannot guarantee skill quality or security — [Vercel changelog](https://vercel.com/changelog/introducing-skills-the-open-agent-skills-ecosystem), [Vercel blog](https://vercel.com/blog/introducing-skills)
  - Leaderboard figures (for example, find-skills at 3.3M installs on 2026-09-11) differ between secondary sources — [qaskills.sh](https://qaskills.sh/blog/skills-sh-agent-skills-directory-guide); contradicted by [webreactiva](https://www.webreactiva.com/blog/skills-sh)

### Inferences
- The dominant structural pattern in video skills is: a short SKILL.md entry point and router; `references/` split by topic (pacing, captions, audio, color); `recipes/` per output type (Shorts, talking head, podcast clip); `scripts/` for deterministic FFmpeg/ASR steps; `assets/` (fonts, LUTs, SFX, caption templates); `evals/`; and a QA or review checklist gate before final render.
- Distributing as both a Claude Code plugin (marketplace.json, which can also bundle an `.mcp.json`) and an Agent Skills-standard folder (`npx skills add`) maximises reach, as Remotion, HyperFrames and kmilo93sd do.

### Gaps
- The full anthropics/skills skill inventory (individual names) was not listed on the README page fetched. Whether any Anthropic skill covers audio or video is unconfirmed, beyond the README making no mention of it.
- The internal file layout of remotion-dev/skills (for example, a `rules/` folder) could not be confirmed from the README.

## 4. Claude Agent Skills documentation: format, progressive disclosure, size, installation, evaluation

### Takeaway
A skill is a folder with `SKILL.md` (YAML frontmatter with `name` ≤64 characters [lowercase letters, digits, hyphens; no "anthropic" or "claude"] and `description` ≤1,024 characters) plus optional `scripts/`, `references/` and `assets/`. Claude loads it in three levels: metadata (about 100 tokens) is always present, the body loads on trigger (keep it under 500 lines / under 5k tokens), and files load only on demand, with scripts executed rather than read. Installation differs per surface: Claude Code reads the filesystem or plugins, claude.ai takes a zip upload per user, and the API uses `/v1/skills` with a workspace-wide `container.skills` that requires code execution and has no network. Anthropic recommends evaluation-first development (three or more evals, Claude A/B iteration), and skill-creator automates evals and description optimisation.

### Cited Findings

**Concept and history**
- Agent Skills were introduced 2025-10-16 as "organized folders of instructions, scripts, and resources that agents can discover and load dynamically". A 2025-12-18 update released Skills as an **open standard**. Security guidance: install only from trusted sources and audit scripts and external network calls — [Anthropic Engineering](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- The open standard lives in **agentskills/agentskills** (26,711★, Apache-2.0, created 2025-12-16). Conventions: required `SKILL.md`; optional `scripts/`, `references/`, `assets/`; a `skills-ref` directory; full spec at agentskills.io/specification — [GitHub](https://github.com/agentskills/agentskills)

**Progressive disclosure**
- Level 1 metadata loads "always (at startup), ~100 tokens per Skill". Level 2 SKILL.md body loads "when Skill is triggered, under 5k tokens". Level 3+ resources cost "none until accessed": "Scripts run through bash, and only their output enters context" — [Claude Platform docs: overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

**Frontmatter rules (API and platform)**
- `name`: maximum 64 characters, lowercase letters/numbers/hyphens, no XML tags, no reserved words `anthropic` or `claude`. `description`: non-empty, maximum 1,024 characters, no XML tags, must say what the skill does and when to use it — [overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

**Best practices** — [Best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- "Claude is already very smart": add only context it lacks.
- Match degrees of freedom to fragility (high: text heuristics; medium: parameterised scripts; low: exact scripts, the "narrow bridge").
- Test with Haiku, Sonnet and Opus.
- Write descriptions in third person with what plus when (for example, "Use when … or when the user mentions …"). Claude picks among "potentially 100+ available Skills" from the description.
- Gerund names (`processing-pdfs`); avoid `helper`/`utils`.
- **SKILL.md body under 500 lines.** Keep references **one level deep** from SKILL.md, because Claude may `head -100` nested files. Give reference files over **100 lines** a table of contents.
- Use workflows with **copyable checklists** and **feedback loops** ("run validator → fix errors → repeat").
- **Plan-validate-execute** with a verifiable intermediate file (for example, `changes.json`): validate it with a script before applying, for batch, destructive or high-stakes operations. Make validation errors verbose.
- Scripts should "solve, don't punt": handle errors and avoid "voodoo constants". State whether a script is to be **run** or **read**.
- Avoid time-sensitive information (use an "old patterns" `<details>` block), keep terminology consistent, use forward-slash paths, and give one default rather than many options.
- Refer to MCP tools by fully qualified name, **`ServerName:tool_name`**.
- List required packages explicitly. claude.ai can install from npm/PyPI; the **API has no network and no runtime installs**.
- Checklist: three or more evaluations, testing on all three models, real-usage testing.

**Evaluation-driven development** — [Best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- Process: identify gaps without the skill → build **three scenarios** → measure a baseline → write minimal instructions → iterate. The eval JSON shape is `{skills, query, files, expected_behavior[]}`. "There is not currently a built-in way to run these evaluations."
- Iterate with "Claude A" (author) and "Claude B" (tester); observe navigation for unexpected paths, missed links and ignored files.

**skill-creator (anthropics/skills)** — [skill-creator SKILL.md](https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md)
- Workflow: capture intent → interview → write SKILL.md → 2–3 test prompts in `evals/evals.json` → spawn **with-skill and baseline runs** in parallel → `timing.json` → grade with `agents/grader.md` into `grading.json` (fields `text`, `passed`, `evidence`) → `python -m scripts.aggregate_benchmark` → analyse → `eval-viewer/generate_review.py` → iterate.
- Description optimisation: **20 queries (8–10 should-trigger, 8–10 near-miss should-not)**, `python -m scripts.run_loop --max-iterations 5`, **60/40 train/test split, each query run 3×**. Needs `claude -p`, so skip it on claude.ai.
- Style: explain the why, treat ALL-CAPS MUST/NEVER as a warning sign, make descriptions somewhat "pushy" to avoid under-triggering.
- Anatomy: `scripts/`, `references/`, `assets/`; body under 500 lines; reference files **over 300 lines** need a TOC; split variants into per-domain files (for example `aws.md` / `gcp.md`).
- Packaging: `python -m scripts.package_skill <folder>` produces a `.skill` file.

**Claude Code specifics** — [Claude Code docs: Skills](https://code.claude.com/docs/en/skills)
- Locations: enterprise managed; personal `~/.claude/skills/<name>/SKILL.md`; project `.claude/skills/<name>/SKILL.md` (commit to share); nested `<subdir>/.claude/skills`; `--add-dir`; plugin `<plugin>/skills/<name>/SKILL.md`, invoked as `/plugin-name:skill-name`. Precedence: enterprise > personal > project. Skills replace `.claude/commands/*.md`, which still work.
- Frontmatter fields: `name`, `description`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context: fork` (run in a subagent), `agent`, `background`, `hooks`, `paths` (glob-limited activation), `shell`; spec fields `metadata`/`license`/`compatibility` are accepted but ignored. Only `description` is recommended. **description + when_to_use is truncated at 1,536 characters** in the listing.
- Substitutions: `$ARGUMENTS`, `$0`/`$1`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_SESSION_ID}`.
- `` !`command` `` dynamic context injection runs before Claude sees the skill. A failing command aborts the invocation; append `|| true`.
- Size: keep SKILL.md under 500 lines. After compaction, each skill keeps its first **5,000 tokens**, within a combined **25,000-token** budget.
- Live reload for skill edits; `/reload-skills` for new top-level directories. Diagnostics: `/doctor` and `/skill-doctor`, which reports per-skill context cost.

**Plugins and marketplaces** — [Claude Code docs: marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- A marketplace is a repo with `.claude-plugin/marketplace.json` (`name`, `owner`, `plugins[]` with `name` and `source`). Sources can be a relative path, `github`, `git-subdir`, `url`, `archive`, `npm` or `command`.
- Commands: `claude plugin validate ./my-marketplace`; `claude plugin marketplace add <owner>/<repo>`; `claude plugin install <plugin>@<marketplace>`; skills run as `/<plugin>:<skill>`.
- The entry name must equal the `plugin.json` name. Official names such as `claude-plugins-official` are reserved.
- Plugins can be submitted to Anthropic's directory.

**claude.ai** — [overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- Upload custom skills as a **zip via Settings > Features** on Pro, Max, Team and Enterprise with code execution enabled. Skills are **per-user only**, with no org-wide admin distribution. Network access varies by settings.
- Custom skills **do not sync across surfaces** (claude.ai, API and Claude Code are separate). Agent Skills are **not covered by ZDR**.

**API** — [Claude Platform docs: Skills guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
- Skills are passed in `container.skills` as `{type: "anthropic"|"custom", skill_id, version}`, **up to 20 skills per request**, and need the tool `{"type": "code_execution_20250825", "name": "code_execution"}`.
- Upload with `POST /v1/skills` (multipart `files[]`, SKILL.md at the root or a single top folder), total **under 30 MB uncompressed**. New versions (`POST /v1/skills/{id}/versions`) are full snapshots.
- Skills mount at `/skills/{skill-name}/`. Generated files come back as `file_id`s, downloaded through the Files API.
- Long operations return the stop reason **`pause_turn`**: resend with the same `container.id` to continue.
- Custom skills are workspace-scoped; use one workspace per tenant.
- The page fetched does not mention beta headers. Older material referenced `skills-2025-10-02` and others, so check the API reference.

### Inferences
- For a video-editing skill, the documented guidance points to this layout: a lean SKILL.md (router, workflow checklist, hard rules) of no more than about 300–500 lines; `references/` per concern (edit-style analysis, captions, audio loudness, color, export specs per platform) with TOCs; `scripts/` for deterministic steps (probe, ASR, silence detection, scene/beat detection, timeline-JSON validator, FFmpeg renderer, QC checker); and `assets/` (fonts, LUTs, caption CSS templates). Use the **plan-validate-execute** pattern with an `edit_plan.json` or timeline JSON validated before rendering.
- Because the API sandbox has no network or runtime installs and heavy binaries such as Whisper models are impractical, the full-featured version should target **Claude Code**, where there is full network access and local installs. A plugin can bundle the skill with an MCP server (for example kinocut or a Resolve MCP) through `.mcp.json`.
- The description limits differ by surface (1,024 characters by the platform spec, versus a 1,536-character combined listing truncation in Claude Code). Keep the description within 1,024 characters for portability.

### Gaps
- The second half of the Skills API guide (beyond 100k characters) and the troubleshooting section of the Claude Code skills page were not read.
- Whether `skills-2025-10-02` or other beta headers are still required in late 2026 could not be confirmed from the fetched page.
- The full agentskills.io specification field list (`license`, `compatibility`, `metadata`, `allowed-tools`) was not fetched directly. Claude Code's docs confirm only that it accepts `metadata`, `license` and `compatibility`.

## 5. Research: edit style transfer from a reference video, and LLM agents that plan edits (timeline/EDL)

### Takeaway
No single paper end-to-end "learns a reference video's editing style and re-applies it to new footage" in a general way. The closest are **Automatic Non-Linear Video Editing Transfer** (2021; per-shot framing, speed and lighting), **V-Trans4Style** (NeurIPS 2025; style-conditioned transition recommendation), **Write-A-Video** (2019; idiom-constrained montage) and the reference-replication features in commercial tools (invideo, Sparki). On the agent side, a 2024–2026 line of work covers LAVE, ExpressEdit, RAVA, EditDuet, Prompt-Driven Agentic Editing, CutClaw, VideoAgent, Aurora and Unified Agentic Editing. New 2026 benchmarks (AgenticVBench, Timeline-Bench, TimelineBench) show current coding agents, Claude Code included, solve only about 14–31% of realistic editing tasks, and fall short most on **editorial quality** (pacing, story, sound).

### Cited Findings

**Style and reference transfer**
- **Automatic Non-Linear Video Editing Transfer** (arXiv 2105.06988, 2021): extracts editing styles from a source video (framing, playback speed and lighting per shot) and applies them to raw footage — [arXiv via search](https://arxiv.org/pdf/2105.06988), [ar5iv](https://ar5iv.labs.arxiv.org/html/2105.06988)
- **V-Trans4Style** (Guhan et al., arXiv 2501.07983, NeurIPS 2025): a transformer encoder-decoder recommends transition sequences, and a style-conditioning module (activation maximisation at inference) adapts them to styles from "cinematic to vlog" without retraining. It introduces **AutoTransition++** (6k videos labelled by production style), built on AutoTransition (35k videos annotated with transitions). Reported gains: up to 80% in transition recall/ranking, 12% in style similarity; user study with 102 participants — [arXiv](https://arxiv.org/abs/2501.07983), [NeurIPS 2025](https://neurips.cc/virtual/2025/133898)
- **RefVFX** (arXiv 2601.07833, 2026): "Tuning-free Visual Effect Transfer across Videos" transfers time-varying effects from a reference video. It handles effects, not cut rhythm — [arXiv](https://arxiv.org/pdf/2601.07833)
- **Write-A-Video** (Wang, Yang, Hu, Yau, Shamir; SIGGRAPH Asia 2019 / ACM TOG): themed text plus a video repository becomes a montage. Visual-semantic matching (keywords and embeddings), then assembly as a hybrid optimisation over a shot graph using cinematography metrics (camera movement, tone) and **user-specified editing idioms** — [paper PDF](https://faculty.runi.ac.il/arik/site/includes/papers/WriteAVideo.pdf), [SIGGRAPH Asia press](https://pressroom.asia.siggraph.org/blog/lights-camera-and-text-novel-video-editing-tool-for-user-friendly)
- **AutoCut** (CVPR 2026): end-to-end advertisement editing via multimodal discretisation. It notes that commercial templates fix shot order, transition types and pacing — [CVF](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhou_AutoCut_End-to-end_advertisement_video_editing_based_on_multimodal_discretization_and_CVPR_2026_paper.pdf)
- **VEU-Bench** (arXiv 2504.17828, CVPR 2025): 19 fine-grained editing-understanding tasks (recognition, reasoning, judging) covering shot size, cut types and transitions. 11 Video-LLMs struggled, some below random. The fine-tuned "Oscars" model gained over 28.3% accuracy. This matters because analysing a reference video's style requires exactly these perception skills — [arXiv](https://arxiv.org/abs/2504.17828), [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Li_VEU-Bench_Towards_Comprehensive_Understanding_of_Video_Editing_CVPR_2025_paper.html)
- Commercial reference-style replication: invideo's agent "studies the timing and sequence of [the reference's] cuts, then trims and arranges your footage" — [invideo](https://invideo.io/editor/style-and-motion-reference/). Sparki's "copy style" maps the reference's pacing, cuts, transitions and text treatment onto the user's footage — [Sparki](https://sparki.io/features/copy-style)

**LLM agents that plan edits**
- **LAVE** (arXiv 2402.10294, 2024): auto-generates text descriptions of footage so an LLM agent can plan. The timeline supports clip sequencing and trimming. User study with 8 participants — [arXiv](https://arxiv.org/html/2402.10294)
- **ExpressEdit** (arXiv 2403.17693, IUI 2024): natural-language plus sketch editing commands, with an LLM and vision models interpreting temporal, spatial and operational references. Formative study of 176 commands from 10 editors; user study with 10 novices — [arXiv](https://arxiv.org/abs/2403.17693v1)
- **Reframe Anything / RAVA** (arXiv 2403.06070, 2024): an LLM agent for reframing (for example, landscape to vertical) with perception, planning and execution stages — [arXiv](https://arxiv.org/pdf/2403.06070)
- **EditDuet** (arXiv 2509.10761; Adobe Research, SIGGRAPH 2025): two agents, an **Editor** that builds sequences on a NLE timeline and a **Critic** that gives feedback or approves, with learned communication. A secondary summary reports 86.9% human preference for generated B-roll sequences and an 8.2% failure rate on EditStock; not verified against the paper — [Adobe Research](https://research.adobe.com/publication/editduet-a-multi-agent-system-for-video-non-linear-editing), [arXiv](https://arxiv.org/abs/2509.10761v1)
- **Prompt-Driven Agentic Video Editing System** (arXiv 2509.16811, Sept 2025): builds a semantic index of multi-hour footage. Its output is a **timestamped trace in structured JSON**, with interpretable intermediate edit plans and storyboards — [arXiv](https://arxiv.org/abs/2509.16811)
- **CutClaw** (arXiv 2603.29664, Mar 2026; Beijing Jiaotong University, Great Bay University GVC Lab, Tencent ARC): a multi-agent system that turns hours-long footage into music-synchronised shorts. A **Playwriter** plans the narrative tied to musical shifts; **Editor** and **Reviewer** agents select and refine clips. Code at GVCLab/CutClaw; paper licensed CC BY-NC-SA 4.0 — [Hugging Face Papers](https://huggingface.co/papers/2603.29664), [arXiv](https://arxiv.org/abs/2603.29664)
- **Unified Agentic Video Editing Across Levels of Complexity and Creativity** (arXiv 2609.12769; Bertelsmann AI Hub): one **hierarchical data structure** organising source footage supports scene previews, summaries and cinematic trailers in a real production setting — [arXiv](https://arxiv.org/pdf/2609.12769)
- **Aurora** (arXiv 2605.18748, May 2026): a VLM agent turns a request into a **structured edit plan**, which a unified video diffusion transformer then executes. Introduces AgentEdit-Bench. Weights: Qwen3-VL-8B LoRA planner and a fine-tuned WAN2.2-TI2V-5B. This is generative, pixel-level editing rather than NLE cutting — [arXiv](https://arxiv.org/abs/2605.18748), [HF weights](https://huggingface.co/yeates/aurora-weights)

**Benchmarks (2026)**
- **AgenticVBench** (arXiv 2605.27705): 100 tasks in 4 families (assembly, repair, sequencing, repurposing), designed with 20 industry experts. The best agent stack "barely crosses 30%". A leaderboard mirror lists GPT-5.5 + Codex at about 31.0% and **Claude Opus 4.7 + Claude Code at 22.1%** (secondary source; sources disagree on some details) — [Emergent Mind](https://www.emergentmind.com/papers/2605.27705), [benchmarklist](https://benchmarklist.com/benchmarks/agenticvbench/)
- **Timeline-Bench** (arXiv 2609.35143, Sept 2026): 56 real tasks from raw footage to final cut (dialog take selection, interview story shaping, commercials from product shots, voiceover and graphics). Each task has a brief, assets, a container and tests covering delivery format, content and brief requirements. The quality test was calibrated on 2,582 blind judgments from 43 editors. 16 agents were evaluated, with harnesses including Codex and Claude Code. Best agent: 26.8% resolved, average 14.0%. Many outputs pass technical checks but fail on story, pacing, sound and graphics, and **human editors won 83.5% of pairwise comparisons**. This comes from search summaries; the paper was not read directly — [Emergent Mind](https://www.emergentmind.com/papers/2609.35143), [arXiv](https://arxiv.org/abs/2609.35143v1)
- **TimelineBench** (NeurIPS 2026, a different benchmark): 100 tasks for computer-use agents in an open-source editor, scored by deterministic project-state diffs. Best configuration 49.0%; no open-weight configuration exceeded 10.0% — [NeurIPS 2026](https://neurips.cc/virtual/2026/166886)
- Titles seen but abstracts not retrieved: Crayotter (arXiv 2608.02694, long-horizon editing agents trained with group-relative preference backpropagation), LumiVideo (arXiv 2604.02409, agentic color grading), UniVA (arXiv 2511.08521) — [Crayotter](https://arxiv.org/pdf/2608.02694), [LumiVideo](https://arxiv.org/pdf/2604.02409), [UniVA](https://arxiv.org/html/2511.08521v1)

### Inferences
- A practical "learn style from a reference video" skill would combine methods from this literature:
  1. Analyse the reference: shot detection, then a shot-length distribution or cuts-per-minute; transition-type classification (VEU-Bench / AutoTransition taxonomy); speed changes; framing and zoom; caption style; loudness/music-ducking profile; beat alignment (librosa, as in VideoAgent).
  2. Store the result as a structured **style profile JSON**, the idea behind OpenStoryline's "Style Skills" and Write-A-Video's idioms.
  3. Have the agent generate a **timeline/EDL JSON** constrained by that profile (Prompt-Driven Agentic Editing; EditDuet's timeline).
  4. Validate and render deterministically.
  5. Run a Critic/Reviewer pass (EditDuet, CutClaw) against the profile.
- The 2026 benchmarks suggest the bottleneck is editorial judgment rather than tool calling. That argues for encoding concrete pacing, caption and loudness rules in `references/` (as kmilo93sd's skill does) and for a review-checklist gate.
- VEU-Bench's finding that general Video-LLMs are weak at recognising cut and transition types implies style extraction should rely on deterministic signal processing (PySceneDetect-style cut detection, audio analysis) wherever possible, with the LLM used for higher-level interpretation.

### Gaps
- arxiv.org was unreachable, so abstracts for Timeline-Bench, AgenticVBench, EditDuet metrics, Unified Agentic Editing, CutClaw results and Automatic NLE Editing Transfer (authors, venue) were taken from search snippets or secondary summaries and should be verified.
- The 2026 arXiv IDs (2603–2609) are later than the model's training knowledge and could not be cross-checked against the primary pages.
- No paper was found that specifically does end-to-end "edit style transfer from a reference video to new footage" with an LLM agent. This looks like an open gap, filled so far only by commercial features (invideo, Sparki) and OpenStoryline's Style Skills, whose format is undocumented.
- Not covered: "Learning to Cut by Watching Movies", MovieCuts, Netflix match-cutting, TeaserGen and similar cut-prediction work; no searches were run for them.
