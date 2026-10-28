# Visual AI Models & Tools for an Automated Short-Form (Reels/TikTok) Editing Pipeline

Research date: 2026-10-28. The scope is visual sub-tasks for talking-head + b-roll editing on a headless Linux server (CPU-only and GPU).

Access note for the writer: in this research sandbox, `huggingface.co`, `arxiv.org`, `ai.google.dev`, `scenedetect.com`, `paddleocr.ai` and `docs.twelvelabs.io` could not be reached (DNS blocked). `github.com` pages could be fetched, but the GitHub API (`gh api`) was refused for repos not attached to the session. So several official pages (Gemini pricing/docs, HF model cards, arXiv abstracts) are cited via search-engine snippets or secondary sources, and each such case is flagged. A production sandbox with the same restrictions should pull weights from **GitHub Releases, `dl.fbaipublicfiles.com`, Google Drive or pip wheels** rather than Hugging Face. Per-model alternatives are listed below.

---

## 1. Person/video matting & background removal with temporal stability

### Takeaway
For talking-head video, the best quality is a **temporal video-matting model seeded by a segmentation mask**: MatAnyone / MatAnyone 2 (best hair/edge stability, but S-Lab licence is likely non-commercial), or SAM 2.1 (Apache-2.0) for masks plus RVM (GPL-3.0) for alpha. **RobustVideoMatting** is still the most practical CPU/ONNX option with built-in recurrent temporal memory. **BiRefNet** (MIT) gives the cleanest per-frame edges, but it has no temporal model and flickers on motion. RMBG-2.0 and BRIA's temporal VRMBG-3.0 need a commercial agreement. For a commercial product, the cleanest-licensed GPU stack is **SAM 2.1 (Apache-2.0) + BiRefNet-matting/portrait (MIT) + temporal smoothing**, or BackgroundMattingV2 (MIT) if a clean background plate can be shot.

### Cited Findings

**RobustVideoMatting (RVM)**
- License: **GPL-3.0** ("Code is re-released under GPL-3.0 license", Sep 2021). — [RVM GitHub](https://github.com/PeterL1n/RobustVideoMatting)
- Exports: ONNX (MobileNetV3 & ResNet50, FP32/FP16, opset 12, "tested on ONNX Runtime with CPU and CUDA backends"), TorchScript, TF SavedModel, TF.js (MobileNetV3 INT8) and CoreML (fixed resolution only). MobileNetV3 is the recommended variant, and ResNet50 gives "small performance improvements". — [RVM GitHub](https://github.com/PeterL1n/RobustVideoMatting)
- GPU speed (tensor throughput only; the repo's video conversion script is "much slower"): RTX 3090 FP16 172 fps at HD / 154 fps at 4K; RTX 2060 Super FP16 134 / 108; GTX 1080 Ti FP32 104 / 74. Recommended `downsample_ratio` is 0.25 for HD and 0.125 for 4K. **No CPU numbers are published.** — [RVM GitHub](https://github.com/PeterL1n/RobustVideoMatting)
- How to call: `torch.hub.load("PeterL1n/RobustVideoMatting", "mobilenetv3")` plus `torch.hub.load(..., "converter")` (`convert_video` accepts a CPU or CUDA model). Weights are on **GitHub Releases v1.0.0**, with mirrors on Google Drive and Baidu Pan. — [RVM GitHub](https://github.com/PeterL1n/RobustVideoMatting)

**MatAnyone (v1) and MatAnyone 2**
- MatAnyone licence: **NTU S-Lab License 1.0**. It needs a **first-frame mask**, which "could be obtained from interactive segmentation models such as SAM2". Install with `pip install git+https://github.com/pq-yang/MatAnyone` and call `InferenceCore("PeiqingYang/MatAnyone")`. Weights `matanyone.pth` are on **GitHub release v1.0.0** (auto-downloaded) or on HF. `--max_size` downsamples. No VRAM or speed figures are given. — [MatAnyone GitHub](https://github.com/pq-yang/MatAnyone)
- Quality claim: "stable performance in both semantics of core regions and fine-grained boundary details". On a harmonized-composite example from their YouTubeMatte benchmark, RVM was confused while MatAnyone "still yields robust performance" (authors' own claim). — [MatAnyone GitHub](https://github.com/pq-yang/MatAnyone)
- The HF demo page describes the S-Lab licence as covering "redistribution and use for **non-commercial purposes**". — [MatAnyone HF Space](https://peiqingyang-matanyone.hf.space/) (via search snippet; HF was not reachable directly)
- MatAnyone 2: repo created Dec 2025, inference code + Gradio demo released Mar 2026, CVPR 2026 (arXiv 2512.11782). It is still S-Lab License 1.0 and is described as preserving fine detail "by avoiding segmentation-like boundaries", with a learned quality evaluator. Install with `uv add matanyone2@git+https://github.com/pq-yang/MatAnyone2.git`. It ships a CLI `matanyone2`, and weights `matanyone2.pth` are on GitHub release v1.0.0 or `MatAnyone2.from_pretrained("PeiqingYang/MatAnyone2")`. No speed or VRAM figures are given. A third-party CoreML port (MatAnyone2Kit, 2026.06) claims real-time on Apple. — [MatAnyone2 GitHub](https://github.com/pq-yang/MatAnyone2)

**BiRefNet (incl. lite / portrait / matting / HR variants)**
- License: **MIT** (code and weights). — [BiRefNet GitHub](https://github.com/ZhengPeng7/BiRefNet)
- Variants: BiRefNet_lite (Swin-T backbone), BiRefNet_lite-2K (2560×1440 input, Sep 2024), BiRefNet-matting (trimap-free general matting, Oct 2024), portrait (P3M-10k + humans, Swin-L), BiRefNet_HR (2048², Feb 2025), BiRefNet_HR-matting (Feb 12 2025), BiRefNet_dynamic (256–2304 px, Mar 31 2025). — [BiRefNet GitHub](https://github.com/ZhengPeng7/BiRefNet)
- GPU speed: A100 FP16 69.4 ms, RTX 4090 FP16 57.7 ms, V100 FP16 152 ms per 1024² image. Another statement gives "17 FPS" at 1024² with 3.45 GB on an RTX 4090 FP16. Inference memory is 4.8 GB FP32 / 3.5 GB FP16. — [BiRefNet GitHub](https://github.com/ZhengPeng7/BiRefNet)
- ONNX: 1024×1024 default. Through ONNX, Swin-L is ~165 ms on A100 (~90% slower than PyTorch) and Swin-T ~93.8 ms. On an RTX 4080S, the steady-state averages were 0.15 s (PyTorch), **4.43 s (ONNX)** and 0.11 s (TensorRT). **ONNX files are in the GitHub v1 release**, and other weights are on Google Drive. A video-inference notebook is `tutorials/BiRefNet_inference_video.ipynb`. — [BiRefNet GitHub](https://github.com/ZhengPeng7/BiRefNet)
- Community ONNX exports exist (e.g., `onnx-community/BiRefNet_lite-ONNX` and MIT-labelled matting/HR-matting exports). — [onnx-community/BiRefNet_lite-ONNX](https://huggingface.co/onnx-community/BiRefNet_lite-ONNX/blame/main/README.md); [PinkPixel/birefnet-hr-matting-onnx](https://huggingface.co/PinkPixel/birefnet-hr-matting-onnx); [BiRefNet-portrait card](https://huggingface.co/ZhengPeng7/BiRefNet-portrait)
- **Temporal weakness:** "BiRefNet has no temporal model, so fast motion can shimmer slightly between frames." — [Replicate sprited/birefnet-video](https://replicate.com/sprited/birefnet-video)

**BRIA RMBG-2.0 / VRMBG-3.0**
- RMBG-2.0 is "source-available ... for non-commercial use". Mirrors list it as CC BY-NC 4.0, and commercial use requires a BRIA agreement. — [RMBG-2.0 model card](https://huggingface.co/briaai/RMBG-2.0/blob/refs%2Fpr%2F6/README.md); [camenduru mirror](https://huggingface.co/camenduru/rmbg-2.0)
- An unofficial mirror says BRIA's hosted API includes a commercial licence while self-hosted weights require an agreement. — [Taha812 RMBG-2.0 weights](https://huggingface.co/datasets/Taha812/RMBG-2.0-weights) (unofficial; verify on bria.ai)
- VRMBG-3.0 (BRIA video model) "consumes the current frame together with the previous frame's predicted alpha" for temporal stability. Its weights are gated: "commercial use requires a BRIA AI agreement; academic access granted upon request". — [VRMBG-3.0 mirror page](https://cloudfare-proxy.pages.dev/briaai/VRMBG-3.0) (mirror via search snippet; release date not found)

**SAM 2.1 (video propagation)**
- License: **Apache 2.0** (checkpoints + code). — [SAM 2 GitHub](https://github.com/facebookresearch/sam2)
- SAM 2.1 checkpoints (A100, torch 2.5.1): hiera_tiny 38.9M params / 91.2 FPS; small 46M / 84.8; base_plus 80.8M / 64.1; large 224.4M / 39.5 FPS (SA-V J&F 76.5→79.5). — [SAM 2 GitHub](https://github.com/facebookresearch/sam2)
- Video API: `build_sam2_video_predictor` → `init_state` → `add_new_points_or_box` → `propagate_in_video`. Dec 2024 update added independent per-object inference, and `vos_optimized=True` enables `torch.compile`. Installation says "on a GPU machine". **CPU support is not documented.** — [SAM 2 GitHub](https://github.com/facebookresearch/sam2)
- Weights download: **direct links on `dl.fbaipublicfiles.com`** (e.g., `.../092824/sam2.1_hiera_tiny.pt`) or `checkpoints/download_ckpts.sh`, which needs no HF. — [SAM 2 GitHub](https://github.com/facebookresearch/sam2)

**SAM 3 / SAM 3.1**
- SAM 3 was released Nov 19, 2025. It detects, segments and **tracks** all instances matching a text/noun-phrase or exemplar prompt in images and video. — [Roboflow: What is SAM 3](https://blog.roboflow.com/what-is-sam3/)
- 848M params. Requires a CUDA GPU (CUDA ≥12.6, Python ≥3.12, PyTorch ≥2.7). Video predictor accepts text prompts. **Checkpoints are gated on Hugging Face** (request access + `hf auth login`). SAM 3.1 "Object Multiplex" (03/27/2026) does shared-memory multi-object tracking and is "significantly faster". — [SAM 3 GitHub](https://github.com/facebookresearch/sam3)
- The "SAM License" grants a worldwide, royalty-free licence to use, modify and distribute. It has **no non-commercial clause** but restricts military/ITAR/weapons uses and requires redistributing the same licence. — [SAM 3 LICENSE](https://github.com/facebookresearch/sam3/blob/main/LICENSE)

**MODNet, BackgroundMattingV2, rembg, Cutie/XMem**
- MODNet: **Apache-2.0** (code, models, demos). It is trimap-free portrait matting with ONNX and TorchScript conversion scripts and a separate TensorRT repo. The online-app model is "about 7M" and handles 2K images quickly on common PCs. It has webcam/custom-video demos. No temporal-consistency module is described in the README. — [MODNet GitHub](https://github.com/ZHKKKe/MODNet)
- BackgroundMattingV2: **MIT** ("permits commercial use"). It **requires a captured clean background image**. Reported speed is 4K 30fps / HD 60fps on an RTX 2080 Ti, with ONNX and TorchScript export scripts. — [BGMv2 GitHub](https://github.com/PeterL1n/BackgroundMattingV2)
- rembg: MIT-licensed library. Its model list includes `u2net_human_seg`, `isnet-general-use`, `sam` and `birefnet-portrait`. Weight licences follow upstream projects. — [rembg GitHub](https://github.com/danielgatis/rembg)
- Cutie (XMem successor, mask-propagation VOS): **MIT**. The bundled RITM GUI code follows RITM's licence. It is also on PyPI as `rf-cutie`. — [Cutie GitHub](https://github.com/hkchengrex/Cutie); [rf-cutie PyPI](https://pypi.org/project/rf-cutie/)

### Inferences
- **Ranking for hair/edge quality + low flicker, GPU:** (1) MatAnyone 2 → (2) MatAnyone → (3) SAM 2.1/SAM 3 mask + BiRefNet-matting alpha with temporal EMA smoothing → (4) RVM ResNet50 → (5) BGMv2 (only with a clean plate, where it is excellent) → (6) MODNet → (7) rembg u2net/isnet. MatAnyone is first because it is purpose-built (memory propagation) and is evaluated against RVM by its authors. Independent third-party benchmarks were not found, so this ranking is a judgment, not a measured result.
- **Commercial-safe ranking:** BiRefNet (MIT), SAM 2.1 (Apache-2.0), BGMv2 (MIT), MODNet (Apache-2.0), Cutie (MIT) and SAM 3 (SAM License, commercial OK with restrictions) are usable. RVM is GPL-3.0, which is fine for server-side internal use but copyleft if distributed. MatAnyone 1/2 (S-Lab, likely non-commercial), RMBG-2.0 and VRMBG-3.0 (BRIA agreement) are not usable commercially without a licence.
- **CPU-only:** RVM MobileNetV3 ONNX at `downsample_ratio` 0.25 is the realistic CPU choice, and MODNet ONNX (~7M params) is the lightest. BiRefNet at 1024² on CPU will be seconds per frame (it is 4.4 s/frame even with ONNX on a GPU per the author), so it is impractical for full video on CPU. SAM 2/3 and MatAnyone are effectively GPU-only.
- **Practical recipe for talking-head Reels:** run SAM 2.1 tiny/small (or SAM 3 with the text prompt "person") to get the first-frame/keyframe mask, then MatAnyone (non-commercial) or RVM (GPL) for alpha. For a fully permissive stack, run BiRefNet-portrait per frame, then temporal smoothing (EMA on alpha guided by optical flow) and edge feathering.
- **Environment note (not web-verified):** this agent environment also exposes a Higgsfield MCP `remove_background` tool (and `reframe`, `upscale_video`), which is a paid, hosted alternative.

### Gaps
- No independent, same-dataset benchmark comparing MatAnyone 2 vs RVM vs BiRefNet vs SAM 3 on hair quality/flicker was found. The ice-ice-bear 2026-04 "matting library landscape" blog could not be fetched (host blocked).
- **No published CPU fps** for RVM, BiRefNet, MatAnyone or MODNet. These must be benchmarked locally.
- MatAnyone/MatAnyone 2 VRAM and fps are not stated. The exact commercial terms of the S-Lab License 1.0 text were not read directly.
- VRMBG-3.0 release date and pricing were not found. The BRIA API price was not verified.
- XMem licence was not checked (Cutie is its maintained successor).

---

## 2. Shot/scene boundary detection & jump-cut detection

### Takeaway
Use **TransNetV2** (MIT, PyTorch port on PyPI) as the default neural detector. AutoShot is slightly more accurate on short-form video specifically. Keep **PySceneDetect** (CPU-only, fast, pip `scenedetect`) as a cheap first pass and for tuning. Neither reliably flags *jump cuts* in static talking-head footage. Jump cuts need a custom signal (face bounding-box/landmark discontinuity + low-threshold content score + audio-gap alignment).

### Cited Findings
- TransNetV2: **MIT**. F1 77.9 (ClipShots), 96.2 (BBC Planet Earth), 93.9 (RAI). A PyTorch inference version ships in `inference-pytorch`. No speed numbers are in the README. — [TransNetV2 GitHub](https://github.com/soCzech/TransNetV2)
- A PyPI port, `transnetv2-pytorch`, exists, and its maintainer re-evaluation reproduces the 77.9 / 96.2 / 93.9 F1 scores. — [transnetv2-pytorch PyPI](https://pypi.org/project/transnetv2-pytorch/1.0.2/)
- AutoShot (CVPRW 2023) introduces a **short-video SBD dataset (SHOT)**. It reports F1 +4.2% over TransNetV2 on SHOT and +1.1 / +0.9 / +1.2 points on ClipShots / BBC / RAI. — [AutoShot arXiv 2304.06116](https://arxiv.org/pdf/2304.06116)
- In NVIDIA's Cosmos paper, PySceneDetect (HSV histogram change thresholding), Panda70M, TransNetV2 and AutoShot were evaluated on ShotBench. The neural ones predict per-frame transition probability over a 100-frame window. — [Cosmos arXiv 2501.03575](https://arxiv.org/pdf/2501.03575)
- In a manual check of 200 videos, PySceneDetect had 65.5% shot segmentation accuracy vs **TransNetV2 87.0%**. PySceneDetect "operates exclusively on the CPU, offering greater processing efficiency". — [CineTrans arXiv 2508.11484](https://arxiv.org/pdf/2508.11484)
- PySceneDetect's own benchmark (strict frame-exact hard cuts): AdaptiveDetector leads on BBC (F1 92) and on the AutoShot dataset (74), and HistogramDetector falls to 20 on ClipShots. — [PySceneDetect benchmarks](https://www.scenedetect.com/benchmarks/) (via search snippet; page blocked in sandbox; vendor-reported)
- PySceneDetect usage: `content` detector with a "good value to start with" of `--threshold 27` (HSV + optional edge weights). `adaptive` compares against a rolling average to suppress false cuts in fast camera motion. A stats file gives per-frame scores for tuning. pip package: `scenedetect`. — [scenedetect PyPI](https://pypi.org/project/scenedetect/)
- Jump-cut detection in one's own talking-head footage was discussed on the OpenCV forum. Normal cuts/blank frames are easier to detect than jump cuts. — [OpenCV Q&A](https://answers.opencv.org/question/215834/help-detecting-where-a-video-has-been-cut-up-jump-cuts)
- AutoFlip uses colour-histogram comparison for shot changes before reframing. — [Google Research blog: AutoFlip](https://www.research.google/blog/autoflip-an-open-source-framework-for-intelligent-video-reframing/)

### Inferences
- **Ranking (accuracy):** AutoShot ≈ TransNetV2 > PySceneDetect Adaptive > Content > Histogram. **Ranking (ease/CPU):** PySceneDetect > TransNetV2 (small CNN; runs on CPU, slower) > AutoShot (research code).
- **Jump-cut recipe for reference analysis:** compute per-frame face bbox centre/scale (MediaPipe/YuNet) and flag frames where the bbox jumps by more than X% while the background histogram stays similar. Combine with a PySceneDetect `content` score at a lowered threshold (~10–15) and audio-silence boundaries from the transcript. A sudden *scale* change with the same background = punch-in zoom cut. A sudden position change = jump cut. This is a design suggestion, not from a source.
- For reference-video style extraction, the cut list (timestamps + shot lengths) gives **average shot length / cuts per second**, a key pacing metric.

### Gaps
- No published CPU throughput for TransNetV2/AutoShot was found.
- AutoShot code/licence status was not verified (GitHub not fetched).
- No dedicated open-source "jump-cut detector" model was found.

---

## 3. Face/person tracking for auto-reframing 16:9 → 9:16

### Takeaway
For a commercial pipeline, use **MediaPipe Tasks face detector/landmarker (Apache-2.0)** or **OpenCV YuNet (Apache-2.0)** for face boxes, plus a smoothed crop path (moving average / Kalman, with hard re-centre at shot boundaries). `pyautoflip` is the ready-made pip option. Avoid Ultralytics YOLO (AGPL-3.0 even for SaaS) and InsightFace model packs (non-commercial) unless licensed.

### Cited Findings
- Google AutoFlip (2020) is built on MediaPipe. It uses face/object detection (TFLite on CPU), histogram-based shot detection, and per-object importance weights to pick the crop. — [Google Research blog](https://www.research.google/blog/autoflip-an-open-source-framework-for-intelligent-video-reframing/); [Google Open Source blog](https://opensource.googleblog.com/2020/02/autoflip-open-source-framework-for.html)
- "The original MediaPipe AutoFlip solution is no longer actively supported." `pyautoflip` is a Python re-implementation: `pip install pyautoflip`; `pyautoflip reframe -i in.mp4 -o out.mp4` (9:16 default); `--method saliency` (UNISAL + face detection); Python `reframe_video(input, output, target_aspect_ratio="9:16")`. — [pyautoflip PyPI](https://pypi.org/project/pyautoflip/)
- MediaPipe repo licence: **Apache-2.0**. — [MediaPipe GitHub](https://github.com/google-ai-edge/mediapipe)
- A talking-head reframing skill (wjs-reframing-video) tracks the active speaker using MediaPipe face landmarks + mouth-aspect-ratio variance. It uses hard cuts between speakers by default, with smooth panning opt-in. — [ClawHub wjs-reframing-video](https://clawhub.ai/jianshuo/wjs-reframing-video)
- DIY baseline from a practitioner thread: face centre per frame → 9:16 crop window → moving-average smoothing to avoid jitter. — [Reddit snapshot](https://reddit.sentinel-team.org/posts/1qa5ira/snapshots/2026-01-12T03%3A21%3A30.45965Z)
- Ultralytics YOLO: use requires releasing the entire project under AGPL-3.0 *or* buying an Enterprise License, "even if you train your own model from scratch or deploy it privately, such as via SaaS". Pricing is unpublished. — [Ultralytics licence page](https://ultralytics.com/license); [Ultralytics request licence](https://www.ultralytics.com/request-license)
- InsightFace: the code is MIT, but pretrained models (buffalo_l, antelopev2, etc.) are "for non-commercial research purposes only". Commercial licences are sold separately. — [insightface PyPI](https://pypi.org/project/insightface/); [InsightFace licensing](https://www.insightface.ai/solutions/face-recognition-licensing)
- A suggested commercial-friendly alternative is YuNet detector + SFace recognizer, Apache-2.0. — [mudler/face-detect-gguf](https://huggingface.co/mudler/face-detect-gguf) (secondary)
- Commercial API option: OpusClip offers an auto-resize/reframe API for 9:16 / 16:9 / 1:1. — [OpusClip blog](https://www.opus.pro/blog/auto-resize-video-api)

### Inferences
- **Ranking (talking-head, commercial-safe):** (1) MediaPipe face landmarker + custom smoothing (Apache-2.0, fast on CPU, also gives mouth landmarks for active-speaker detection) → (2) `pyautoflip` (fastest to adopt; check its licence) → (3) OpenCV YuNet (Apache-2.0, tiny ONNX in OpenCV Zoo) → (4) SAM 2/3 person mask centroid on GPU (robust when the face turns away) → (5) YOLO/InsightFace only if licensed.
- Everything here runs on CPU in real time or better for 720p/1080p detection at reduced resolution. A GPU is not needed for reframing.
- Smoothing design: dead-zone (don't move the crop unless the face leaves the central ~20%), critically-damped spring or one-euro filter, and reset at TransNetV2 cut points. Clamp to frame bounds. For punch-in zooms, scale the crop window rather than upscaling the output when the source is 1080p+.
- Environment note: a hosted Higgsfield `reframe` MCP tool is available in this agent environment (not web-verified, paid).

### Gaps
- `pyautoflip`'s licence and maintenance cadence were not verified.
- MediaPipe's current pip package name/versions and the legacy-vs-Tasks status of the Face Detection solution were not confirmed from the fetched page. The model download host (storage.googleapis.com) was not verified.
- No benchmark comparing open-source reframers was found.

---

## 4. Upscaling / frame interpolation / denoise (for punch-in zooms on 720p)

### Takeaway
For 720p punch-ins (e.g., 1.5–2× crop), **Real-ESRGAN (ncnn-vulkan or PyTorch, MIT/BSD)** on cropped frames is the pragmatic choice. It works on CPU but slowly, and it can over-sharpen faces, so use it only for the zoomed segment. **RealBasicVSR** (Apache-2.0) is temporally better but needs an old mmediting stack and a GPU. For interpolation (slow-mo or smoothing speed ramps), **Practical-RIFE / rife-ncnn-vulkan (MIT)** is fast. **FILM** (Apache-2.0, TF2, archived) handles large motion but is slow. ffmpeg `minterpolate` is a CPU-only fallback with artefacts.

### Cited Findings
- Real-ESRGAN-ncnn-vulkan: **MIT**. — [Real-ESRGAN-ncnn-vulkan mirror](https://gitee.com/DXFB/Real-ESRGAN-ncnn-vulkan)
- An FAQ mirror says the ncnn implementation is the faster route for CPU inference (no numbers). — [Real-ESRGAN FAQ (mintlify mirror)](https://mintlify.com/xinntao/Real-ESRGAN/resources/faq)
- Practical-RIFE: **MIT**. 30+ FPS for 2× 720p interpolation on a 2080 Ti. — [Practical-RIFE GitHub](https://github.com/hzwer/Pratical-RIFE); [RIFE HF mirror](https://huggingface.co/daydreamlive/RIFE/blob/main/README.md)
- rife-ncnn-vulkan is MIT and ncnn is BSD-3 (per Video2X's dependency table). Video2X 6.x bundles these upscalers/interpolators. — [Video2X GitHub](https://github.com/k4yt3x/video2x)
- REAL Video Enhancer is another packaged GUI/CLI around RIFE/ESRGAN-type models. — [REAL-Video-Enhancer GitHub](https://github.com/TNTwise/REAL-Video-Enhancer)
- VapourSynth `vs-mlrt` supports CUDA/Vulkan and pure-CPU backends for these models. — [Doom9 forum](https://forum.doom9.org/archive/index.php/t-184386.html)
- RealBasicVSR: **Apache-2.0**. 4× model for real-world video SR. Depends on mmcv-full + mmedit (example pinned to PyTorch 1.7.1 / CUDA 10.1). Weights are on Dropbox/Google Drive/OneDrive (not HF). Saving to video adds compression, so save PNG sequences. No speed/VRAM given. — [RealBasicVSR GitHub](https://github.com/ckkelvinchan/RealBasicVSR)
- FILM: **Apache-2.0**, TensorFlow 2, **archived/read-only**. Designed for large motion. Supports `--block_height/--block_width` patching for high-res. Weights are on Google Drive. — [FILM GitHub](https://github.com/google-research/frame-interpolation)

### Inferences
- **When useful:** a 2× digital zoom on 720p yields a 360p-equivalent crop, which is visibly soft on a 1080×1920 canvas. Real-ESRGAN (x2/x4 "general" or anime-free models) applied only to the zoomed section helps. For 1080p sources a 1.3–1.5× punch-in usually needs no AI upscaling (Lanczos is enough). This is an editor-judgment heuristic, not sourced.
- **Ranking for punch-in upscaling:** (1) Real-ESRGAN x2/x4 (GPU; ncnn-vulkan also on CPU, slowly) → (2) RealBasicVSR (GPU, better temporal consistency, dependency pain) → (3) Lanczos/`zscale` in ffmpeg (CPU, instant) as the default. Watch for "plastic skin" on faces; a face restorer (GFPGAN/CodeFormer) is a further option, but its licences were not checked.
- **Interpolation ranking:** RIFE (fast, MIT) > FILM (quality on big motion, slow, TF2) > ffmpeg `minterpolate=mi_mode=mci` (CPU, ghosting). Interpolation is rarely needed for Reels except speed ramps or slow-mo of b-roll.
- **Denoise:** ffmpeg `hqdn3d`/`nlmeans` on CPU are adequate for talking heads (not sourced in this session).

### Gaps
- No measured CPU throughput for Real-ESRGAN, RealBasicVSR, RIFE or FILM was found. These need local benchmarking.
- Real-ESRGAN main-repo licence (BSD-3 per prior knowledge) and GFPGAN/CodeFormer licences were not verified this session.
- ffmpeg `minterpolate` documentation was not fetched.

---

## 5. Video understanding to analyse a reference edit (graphics, text, colours, transitions, timing)

### Takeaway
**Gemini (2.5/3.x Flash or Pro) with native video input** is the cheapest and most capable single call for "watch this reference Reel and return timestamped JSON": ~300 tokens/s at default resolution, so a 60 s Reel is ~18k tokens, i.e. fractions of a cent on Flash. However, the default **1 fps sampling misses fast cuts/graphics**, so raise fps or clip sections. **Twelve Labs Pegasus 1.5+** offers schema-driven, timestamped metadata extraction as a product. **Qwen3-VL (Apache-2.0)** is the best open model with explicit timestamp alignment (vLLM/transformers on GPU). **Claude/GPT** need frames extracted by the agent, e.g. contact-sheet grids with burned-in timestamps. The most robust approach is **hybrid**: deterministic tools (SBD, OCR, colour clustering, audio/ASR) produce the timeline, and a VLM labels each segment.

### Cited Findings

**Gemini**
- Video tokenisation: 258 tokens/frame at default media resolution, 66 at low resolution, +~32 tokens/s audio, so ~300 tokens/s default and ~100 tokens/s low. Sampling is 1 frame per second by default. — [Fora Soft, 2026-05-31](https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/video-vlms-frame-sampling-token-streaming-2026) (secondary; ai.google.dev blocked in sandbox)
- Pricing (secondary): Gemini 2.5 Flash $0.30 in / $2.50 out per 1M tokens; 2.5 Pro $1.25 / $10 (≤200k). Batch halves the price, and context caching cuts cached input by 90%. One hour of video at default resolution is ~1.08M tokens ≈ $0.33 on Flash. — [Fora Soft pricing, 2026-05-23](https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/real-cost-of-ai-in-video-products-gemini-openai-pricing)
- Gemini 3 Pro Preview (Nov 2025): $2.00 in / $12.00 out ≤200k, $4 / $18 above. — [Apidog](https://apidog.com/blog/gemini-3-0-api-cost/). Gemini 3 Flash: $0.50 in / $3.00 out. — [MorphLLM](https://www.morphllm.com/gemini-api-pricing); [Puter](https://developer.puter.com/tutorials/gemini-api-pricing/)
- Google's pricing page lists Gemini 3.1 Flash-Lite at $0.25 per 1M for text/image/video input ($0.50 audio). — [ai.google.dev/pricing](https://ai.google.dev/pricing) (search snippet only)
- **Conflict:** Gemini 3.1 Pro is listed at $2.40 / $14.40 by one aggregator vs $2.00 / $12.00 elsewhere. — [CloudPrice](https://cloudprice.net/models/google-gemini-3-1-pro). There is also a conflict over whether video tokens carry a 1.5× multiplier. — see the two Fora Soft/tkmxai summaries above. Verify on the official page.
- A 2026 report says Gemini added "agentic" video processing that picks which parts of a video to watch (newer Flash models). Unverified. — [HowAIWorks](https://howaiworks.ai/blog/google-gemini-agentic-video-2026)

**Twelve Labs**
- Official calculator: Marengo indexing $0.042/min + $0.0015/min infrastructure, search $4 per 1K queries. Pegasus analysis $0.0292–0.0294 per minute of input video + $0.0075 per 1K output tokens. Free tier is 600 min. — [Twelve Labs pricing calculator](https://www.twelvelabs.io/pricing-calculator); [usagepricing.com](https://usagepricing.com/blueprint/twelve-labs)
- **Conflict:** the "pricing-2" page lists Marengo/Pegasus visual indexing at $0.033/min and different token rates. — [Twelve Labs pricing-2](https://www.twelvelabs.io/pricing-2)
- Pegasus 1.5 "Time Based Metadata Extraction" takes a user-defined JSON schema and returns structured, **timestamped** results across a video of up to two hours. — [MarTech Series](https://martechseries.com/video/twelvelabs-launches-pegasus-1-5-turning-raw-video-into-structured-queryable-data-at-scale/); [TwelveLabs structured responses docs](https://docs.twelvelabs.io/docs/guides/analyze-videos/structured-responses)
- Pegasus 1.2 on Amazon Bedrock accepts a JSON-Schema response format. — [AWS Bedrock Pegasus docs](https://docs.aws.amazon.com/es_es/bedrock/latest/userguide/model-parameters-pegasus.html). A Pegasus 1.6 listing also exists. — [Toolradar](https://toolradar.com/tools/pegasus-1-6-by-twelvelabs)

**Open VLMs**
- Qwen3-VL: **Apache-2.0**. Dense 2B/4B/8B/32B and MoE 30B-A3B/235B-A22B (Instruct + Thinking, FP8 variants), released Sep–Oct 2025. Features "text–timestamp alignment" for "timestamp-grounded event localization", video grounding, video OCR, 256K context (expandable to 1M), default **2 fps** sampling, OCR in **32 languages**. Runs on vLLM ≥0.11 and transformers ≥4.57. FP8 requires H100+. — [Qwen3-VL GitHub](https://github.com/QwenLM/Qwen3-VL)
- Qwen3-VL fine-tunes for temporal grounding: TimeLens2-8B (MCG-NJU, Jul 2026, Apache-2.0, returns start/end seconds for each described event; 2B/4B siblings) and TimePLE-8B (KlingTeam, Apache-2.0). — [Mixpeek TimeLens2](https://mixpeek.com/model/MCG-NJU/TimeLens2-8B); [TimePLE listing](https://app.alphaneural.io/models/KlingTeam/TimePLE)
- Qwen3-VL GGUF runs in llama.cpp/Ollama on CPU **for images**. llama.cpp lacks native video input, so pass sampled frames. A `llama-video` package adds temporal handling (targets Qwen3.5). — [Qwen3-VL-2B-Thinking-GGUF](https://huggingface.co/Qwen/Qwen3-VL-2B-Thinking-GGUF); [ComfyUI Qwen3-VL-gguf](https://github.com/KLL535/ComfyUI_Simple_Qwen3-VL-gguf); [llama-video PyPI](https://pypi.org/project/llama-video/)

**Claude / OpenAI (frame-based)**
- Claude vision: an image costs ⌈w/28⌉×⌈h/28⌉ tokens. Limits are 100 images/request (200k-context models) or 600 (others). With >20 images, each must be ≤2000 px. Max is 8000×8000 and 10 MB. Newer models accept up to 2576 px on the long edge (up to ~4784 tokens/image). **No native video**, so extract frames. — [Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)
- OpenAI: aggregator lists gpt-5 at $1.25 in / $10 out per 1M tokens. No source on video-frame pricing was found. — [BetOnAI OpenAI pricing 2026](https://betonai.net/?p=1814) (aggregator)

### Inferences
- **Ranking for "analyse a reference Reel → timestamped JSON":** (1) Gemini 3/3.1 Flash or 2.5 Flash with video upload, `fps` raised to 2–5 for 30–90 s clips, `responseSchema` JSON (cheapest, native audio + video). (2) Twelve Labs Pegasus 1.5+ (schema-driven timestamped metadata; ~$0.03/min; good for batches of references). (3) Gemini Pro / Claude / GPT-5 on **frame grids** (e.g., 3×3 or 4×4 contact sheets at 4–8 fps with burned-in `t=12.4s` labels) for fine-grained graphic/text-overlay description; Claude handles up to 100–600 images/request. (4) Qwen3-VL-8B/32B self-hosted on GPU (Apache-2.0, timestamp tokens; 8B needs a ~24 GB GPU in BF16 by rule of thumb, not sourced). (5) Qwen3-VL-2B/4B GGUF on CPU, frame-by-frame only and slow. InternVL and LLaVA-Video were not researched in depth.
- **Agent recipe to extract an editing style (hybrid, deterministic first):**
  1. `ffprobe` → fps, resolution, duration. Then ASR (separate research) → word timings.
  2. TransNetV2/PySceneDetect → cut list, shot-length histogram, cuts/sec. Plus face-bbox scale tracking → punch-in zoom events and their zoom factor/duration.
  3. Sample frames at 4–10 fps. Run OCR (PaddleOCR) on each and diff text regions over time → on-screen caption timeline (text, bbox, first/last frame, font size ratio, position = top/centre/bottom). Caption style = words per caption, highlight colour per word.
  4. Colour: k-means on caption-region pixels (text vs stroke vs box), whole-frame palette per shot, LUT/grade estimate (mean saturation/contrast).
  5. Transitions: frame-difference profile around cuts (hard cut vs whip/zoom blur vs fade) plus a VLM label on the 5 frames around each cut.
  6. VLM pass (Gemini video or Claude frame grids) with a strict JSON schema: `{segments:[{t_start,t_end,shot_type,graphics:[{type,text,position,animation}],broll:bool,transition_in,sfx_hint}]}`. Then reconcile VLM timestamps against deterministic cut/OCR timestamps, since VLMs at 1–2 fps are imprecise at sub-second level.
- Because Gemini samples at 1 fps by default, 0.2–0.5 s caption pops and flash graphics are likely missed unless fps is raised or OCR-driven frame sampling is used.

### Gaps
- Official Gemini docs/pricing pages (ai.google.dev) were blocked. Exact current per-model video rates, the custom-fps parameter name (`videoMetadata.fps`, from prior knowledge, unverified) and max video length were not confirmed.
- OpenAI's current GPT-5.x/4.1 vision pricing and video handling were not confirmed from an official page.
- InternVL3/3.5 and LLaVA-Video licences/benchmarks were not researched (budget).
- No head-to-head benchmark of these VLMs on *edit-style* extraction (graphics/transitions timing) exists in the sources found.
- Twelve Labs pricing conflict ($0.033 vs $0.042/min) is unresolved.

---

## 6. OCR for on-screen Bengali text, font identification, colour palette extraction

### Takeaway
For Bengali caption OCR: **PaddleOCR 3.x (PP-OCRv5 multilingual, Apache-2.0)** appears to have added Bengali in v3.4 (unconfirmed officially). **EasyOCR** (Apache-2.0, pip, CPU OK) and **Tesseract `ben`** are proven baselines (~89–91% char accuracy on Bengali documents). **Google Cloud Vision** is the commercial accuracy fallback. Stylised Reel captions (stroke, shadow, gradient) degrade all engines, so pre-process (crop caption band, binarise, upscale 2×) and cross-check with a VLM (Gemini). Font ID for Bengali has **no off-the-shelf model**. Use a render-and-compare approach against a candidate set of Bengali fonts.

### Cited Findings
- PaddleOCR PP-OCRv5 multilingual: 37 languages in v3.1.1 docs → "109 languages" in v3.3.0 (adds Cyrillic, Arabic, Devanagari, Tamil, Telugu) → "111 languages (including … Tibetan script and **Bengali**)" in v3.4.0 per a GitHub fork's README. Bengali is only explicitly confirmed by the fork. — [PaddleOCR docs v3.1.1](https://www.paddleocr.ai/v3.1.1/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html); [paddleocr 3.3.0 release](https://newreleases.io/project/pypi/paddleocr/release/3.3.0); [PaddleOCR fork README](https://github.com/Aariso0/PaddleOCR); [PaddleOCR 3.0 tech report](https://arxiv.org/pdf/2507.05595)
- Bengali document OCR benchmark (216 images, 9 categories): **Tesseract** CLA 88.54% / WER 20.01%; **EasyOCR** CLA 90.98% / WER 21.94%. A hybrid with Google Vision API scored best. — [BRAC University thesis](https://dspace.bracu.ac.bd/bitstreams/ba79fe28-fbb3-41bb-8f7b-53990b1f892d/download)
- The Bharat Scene Text (2025) benchmark compares Tesseract, PaddleOCR, EasyOCR, SuryaOCR, Google OCR and GPT-4 on Indian-language scene text (Bengali numbers not retrieved). — [arXiv 2511.23071](https://arxiv.org/pdf/2511.23071)
- EasyOCR: **Apache-2.0**, 80+ languages, `gpu=False` for CPU, latest v1.7.2 (24 Sep 2024). Weights auto-download from the jaided.ai model hub (`~/.EasyOCR/model`), not GitHub. — [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR)
- Surya OCR: 90+ languages. Weights are **cc-by-nc-sa-4.0**, waived for orgs under $5M revenue AND under $5M funding, and the user must not compete with the Datalab API. — [Surya GitHub](https://github.com/VikParuchuri/surya); [surya-ocr PyPI](https://pypi.org/project/surya-ocr/0.4.7)
- Qwen3-VL OCR covers 32 languages (Bengali not confirmed). — [Qwen3-VL GitHub](https://github.com/QwenLM/Qwen3-VL)
- Font recognition open-source: **storia-ai/font-classify** classifies ~3,000 Google Fonts and ships an ONNX checkpoint (outputs font filenames). **fontina** is MIT, DeepFont-like, with training data generation (PyPI 0.0.1 yanked, so use GitHub). YuzuMarker.FontDetection is CJK-only. deep_font is small with weights included. Most derive from Adobe's DeepFont (2015). — [font-classify](https://awesome.ecosyste.ms/projects/github.com%2Fstoria-ai%2Ffont-classify); [fontina](https://awesome.ecosyste.ms/projects/github.com%2Fdexterp37%2Ffontina); [YuzuMarker](https://docsearch.algolia.com/mcp/docs/repo/jeffersonqin/yuzumarker.fontdetection); [deep_font](https://github.com/larksq/deep_font); [arXiv 2602.13889](https://www.arxiv.org/pdf/2602.13889)

### Inferences
- **OCR ranking for Bengali Reel captions:** (1) Google Cloud Vision / Gemini Flash (as an OCR-capable VLM; it also reads stylised text and context), commercial → (2) PaddleOCR PP-OCRv5 multilingual (if Bengali confirmed; fast on CPU; pip `paddleocr`) → (3) EasyOCR `['bn','en']` (Apache-2.0, CPU-capable) → (4) Tesseract `ben` (Apache-2.0, `tessdata_best` on GitHub, CPU; best on clean, high-contrast binarised crops) → (5) Surya (licence-restricted). The rank is a judgment. Run two engines and vote, since no Bengali *scene/caption* benchmark numbers were retrieved.
- **Bengali specifics:** conjuncts (যুক্তাক্ষর) and vowel signs (কার) split by stylised strokes are the main failure mode. Upscale caption crops 2–3× and binarise text vs stroke colour (k-means on the caption box) before Tesseract/EasyOCR. Use temporal voting across 3–5 frames of the same caption.
- **Font identification approach (Bengali):** WhatTheFont/Adobe-style services and storia font-classify target Latin fonts, so Bengali support is unlikely (not verified). Practical method: (a) build a candidate list of popular Bengali fonts (e.g., Hind Siliguri, Noto Sans/Serif Bengali, Baloo Da 2, Tiro Bangla, Galada, Anek Bangla, Atma, Mina from Google Fonts, plus commercial Li/Ekushey/SolaimanLipi families); (b) render the OCR'd string in each with PIL/HarfBuzz (Raqm layout needed for Bengali shaping); (c) compare against the binarised crop via SSIM / CLIP-image / DINOv2 embedding similarity or a fine-tuned fontina model trained on synthetic Bengali renders; (d) a VLM can shortlist "rounded / bold / handwritten / serif" style. Also estimate stroke width, stroke colour, shadow and box colours from pixel clustering.
- **Colour palette extraction:** k-means (OpenCV `cv2.kmeans` / scikit-learn) or `colorthief`/`Pylette` on (a) caption text/stroke/box pixels, (b) graphic overlay regions, (c) whole frames per shot. Convert to CIELAB for clustering and report hex + coverage %. These are standard techniques; no source was fetched this session.

### Gaps
- An official PaddleOCR changelog confirming Bengali (`bn`) recognition, and its accuracy, could not be retrieved (paddleocr.ai blocked).
- EasyOCR's Bengali support was not confirmed from the README (the language list is on jaided.ai). Bengali is believed supported from prior knowledge, unverified.
- No Bengali scene-text/caption accuracy numbers for PaddleOCR/EasyOCR/Google Vision were retrieved. The Bharat Scene Text paper table was not accessible.
- Google Cloud Vision OCR pricing and WhatTheFont's API availability/Bengali coverage were not researched.
- No open-source Bengali font-identification model was found.

---

## 7. Generative helpers (b-roll, stickers, 3D icons, backgrounds), with cost

### Takeaway
Use cheap image models for icons/stickers/backgrounds: **Gemini 2.5 Flash Image ("Nano Banana") ~$0.039/image** (half in batch), **gpt-image-1.5 ~$0.009–0.133/image** by quality, **Imagen 4 ~$0.04**. Generated video b-roll is costly: **Veo 3.1 $0.40/s (1080p), Fast $0.10–0.12/s, Lite $0.05–0.08/s**, so 5 s of Lite 720p ≈ $0.25. Prefer stock b-roll plus generated stills with Ken-Burns motion for budget pipelines. Remove backgrounds from generated stickers with BiRefNet/rembg.

### Cited Findings
- Nano Banana (gemini-2.5-flash-image): **$0.039/image** standard, **$0.0195** batch/flex (page dated Sep 2026). A reseller (PiAPI) offers $0.03. — [BenchLM Nano Banana pricing](https://benchlm.ai/md/media-pricing/nano-banana.md); [PiAPI](https://piapi.ai/blogs/free-nano-banana-api-pricing-and-key-access-2025-google-gemini-2-5-flash-via-piapi)
- gpt-image-1.5 at 1024×1024: ~$0.009 (low) / $0.034 (medium) / $0.133 (high). gpt-image-1 reportedly retires Oct 23 2026 (unconfirmed by OpenAI). — [PricePerToken GPT Image](https://pricepertoken.com/gpt-image-pricing); [Aireiter](https://aireiter.com/blog/gpt-image-1-5-api-pricing)
- Imagen 4: $0.04 per generation (scraped GCP table, weak source). — [CloudPriceCheck](https://cloudpricecheck-com.pages.dev/gcp/gemini-api-pricing)
- Veo 3.1 via Gemini API: $0.40/s (720p/1080p), $0.60/s (4K). Veo 3.1 Fast $0.10 / $0.12 / $0.30. Veo 3.1 Lite $0.05 (720p) / $0.08 (1080p), launched Mar 31 2026. No free tier. — [BenchLM Veo pricing](https://benchlm.ai/md/media-pricing/veo.md); [vo3ai blog](https://www.vo3ai.com/blog/veo-31-lite-pricing-explained-is-googles-005second-ai-video-the-cheapest-api-opt-2026-04-01)

### Inferences
- **Ranking for Reels graphics:** (1) Nano Banana / gpt-image-1.5 low-medium for emoji-style stickers and "3D icon" renders (prompt: "3D clay icon, isolated on plain background"), then BiRefNet → transparent PNG → (2) Imagen 4 / Flux (Flux pricing not found) for photoreal backgrounds → (3) Veo 3.1 Lite/Fast only for hero b-roll shots. Self-hosted open image models (FLUX.1-schnell Apache-2.0, SDXL) need a ≥12–24 GB GPU (prior knowledge, unverified this session).
- Text rendering in Bengali inside generated images is unreliable for most image models (unverified). Overlay Bengali text in the compositor (ffmpeg/Remotion/MoviePy with proper shaping) rather than generating it.
- Environment note: this agent environment exposes Higgsfield MCP tools (`generate_image`, `generate_video`, `generate_3d`, `remove_background`, `upscale_video`, `reframe`, `video_analysis_create`, `virality_predictor`). These are a credit-billed hosted alternative (pricing not checked).

### Gaps
- Official Google/OpenAI pricing pages could not be fetched. All generative prices above come from aggregators and should be re-verified.
- Flux (Black Forest Labs) API pricing, Ideogram/Recraft (strong for icons/vector) pricing, and Kling/Runway/Seedance video pricing were not researched.
- Higgsfield credit costs were not checked.
