# রেফারেন্স-স্টাইল এডিটিংকে পুনর্ব্যবহারযোগ্য Claude Skill-এ রূপ দিন

এই কথোপকথনে যে পাইপলাইন কাজ করেছে, সেটিই Claude Code Skill-এর সবচেয়ে দ্রুত ও নির্ভরযোগ্য ভিত্তি। পাইপলাইনের অংশগুলো ছিল Pillow (RAQM text shaping) ও numpy দিয়ে per-frame compositing, multiprocessing, ffmpeg-এ pipe, u2net/BiRefNet ONNX matte, synthesized SFX kit, rule-based SFX cue list, রেফারেন্স অডিওর mid/side spectral analysis আর রেফারেন্সের বিপরীতে measure-and-adjust level calibration। নতুন renderer খোঁজার চেয়ে অনেক বেশি লাভ দুটি সংযোজনে। প্রথমটি রেফারেন্স থেকে স্বয়ংক্রিয়ভাবে বের করা একটি schema-validated **"style spec" JSON**, যাতে timestamp নয়, নিয়ম থাকবে। দ্বিতীয়টি একটি **scorecard লুপ**, যা render-এর পর একই extractor চালিয়ে ফলাফল রেফারেন্সের সাথে মেলায়। এটা জরুরি, কারণ 2026-এর Timeline-Bench-এ সেরা agent বাস্তব এডিটিং কাজের মাত্র **26.8%** সমাধান করেছে (গড় 14.0%), আর ব্যর্থতা এসেছে মূলত pacing, sound ও graphics-এর editorial মানে ([Emergent Mind](https://www.emergentmind.com/papers/2609.35143))। অর্থাৎ skill-এর আসল সম্পদ লিখে রাখা নিয়ম আর মাপার যন্ত্র, LLM-এর চোখের আন্দাজ নয়।

Remotion, ffmpeg ও HyperFrames-এর বাইরে প্রস্তাবিত স্ট্যাক এরকম: cut ধরতে TransNetV2, zoom ও easing মাপতে optical flow, ক্যাপশন পড়তে EasyOCR/Tesseract আর ফন্ট চিনতে Lipika, অডিওর জন্য audio-separator (BS-RoFormer), PANNs/LAION-CLAP ও pyloudnorm, আর label দিতে Gemini video বা Claude frame-grid। বাংলাই সবচেয়ে বড় ফাঁদ। Stock Whisper বাংলায় প্রায় **71–79% WER** দেয়, আর WhisperX-এ বাংলার কোনো default aligner নেই। এছাড়া Pillow BASIC, Blender VSE ও ভুল-কনফিগার করা libass যুক্তাক্ষর ভেঙে দেয়। তাই fine-tuned বাংলা ASR, CTC forced alignment এবং HarfBuzz-ভিত্তিক text rendering বাধ্যতামূলক। লাইসেন্স-নিরাপদ matting-এর জন্য BiRefNet (MIT), SAM 2.1 (Apache-2.0) ও temporal smoothing একসাথে ব্যবহার করুন। Skill-টি Claude Code plugin হিসেবে বানান, কারণ Claude API-এর skill sandbox-এ network বা runtime install নেই। বাইরের সার্ভিসের খরচ প্রতি 60-সেকেন্ডের Reel-এ মাত্র কয়েক সেন্ট।

## কোনো তৈরি টুল রেফারেন্সের স্টাইল হুবহু কপি করে না, তাই "নিয়ম" আর "টাইমলাইন" আলাদা রাখুন

রেফারেন্স ভিডিও দেখে তার এডিট-স্টাইল শিখে নতুন ফুটেজে বসানোর কোনো সাধারণ, end-to-end open-source সমাধান এখনো প্রকাশিত হয়নি। সবচেয়ে কাছের একাডেমিক কাজ, **Automatic Non-Linear Video Editing Transfer** (2021), প্রতিটি shot-এর শুধু framing, playback speed আর lighting তুলে এনে raw footage-এ প্রয়োগ করে ([arXiv](https://arxiv.org/pdf/2105.06988))। **V-Trans4Style** (NeurIPS 2025) শুধু স্টাইল অনুযায়ী transition-এর ক্রম সুপারিশ করে ([arXiv](https://arxiv.org/abs/2501.07983))। বাণিজ্যিক দিকে invideo-র agent রেফারেন্সের cut-এর timing ও ক্রম পড়ে আপনার ফুটেজ সাজায় ([invideo](https://invideo.io/editor/style-and-motion-reference/))। Sparki-র "copy style" ফিচার pacing, cut, transition ও text treatment ম্যাপ করে ([Sparki](https://sparki.io/features/copy-style))। কিন্তু দুটোই বন্ধ প্ল্যাটফর্ম, আর বাংলা টাইপোগ্রাফি, SFX placement বা অডিও-লেভেল ক্যালিব্রেশন নিয়ে কোনো দাবি করে না।

Open-source-এ সবচেয়ে কাছের উদাহরণ **FireRed-OpenStoryline** (Apache-2.0)। এর "Style Skills" একটি সম্পূর্ণ editing workflow-কে reusable Skill হিসেবে `.claude/skills`-এ সেভ করে, তারপর নতুন মিডিয়ায় প্রয়োগ করে ([GitHub](https://github.com/FireRedTeam/FireRed-OpenStoryline))। তবে সেই ফরম্যাটের কোনো ডকুমেন্টেশন নেই। এই কথোপকথনের পাইপলাইন রেফারেন্সের ক্যাপশন, motion, SFX আর লেভেল পর্যন্ত মিলিয়েছে, তাই এটি প্রকাশ্য OSS-এর চেয়ে ইতিমধ্যেই এগিয়ে। এখনকার কাজ হলো একবারের এই সাফল্যকে পুনরাবৃত্তিযোগ্য পদ্ধতিতে রূপ দেওয়া।

পদ্ধতিটা কেন "নিয়ম লিখে রাখা"-কেন্দ্রিক হওয়া উচিত, তার প্রমাণ দেয় 2026-এর benchmark-গুলো। **Timeline-Bench**-এ raw footage থেকে final cut পর্যন্ত 56টি বাস্তব কাজ আছে, আর এর quality test 43 জন এডিটরের 2,582টি blind judgment দিয়ে calibrated। সেখানে সেরা agent সমাধান করেছে মাত্র **26.8%** কাজ, গড় ছিল **14.0%**, আর pairwise তুলনায় **মানব এডিটর 83.5% ক্ষেত্রে জিতেছে** ([Emergent Mind](https://www.emergentmind.com/papers/2609.35143))। অনেক আউটপুট technical check পাস করেও story, pacing, sound ও graphics-এ ব্যর্থ হয়েছে। AgenticVBench-এর একটি leaderboard mirror-এ Claude Opus 4.7 + Claude Code-এর স্কোর 22.1% ([benchmarklist](https://benchmarklist.com/benchmarks/agenticvbench/))। আরও গুরুত্বপূর্ণ ফল এসেছে **VEU-Bench** থেকে: সেখানে 11টি Video-LLM cut type ও transition চিনতে হিমশিম খেয়েছে, কয়েকটি random অনুমানের চেয়েও খারাপ করেছে ([arXiv](https://arxiv.org/abs/2504.17828))। এর দুটি ব্যবহারিক মানে আছে। রেফারেন্সের cut, zoom, ক্যাপশন timing ও অডিও লেভেল মাপবে deterministic signal processing। আর "ভালো এডিট" বলতে কী বোঝায়, তা skill-এর ভেতরে সংখ্যায় লেখা থাকবে।

এজন্য স্থাপত্যটি দুই স্তরের। প্রথম স্তর **style spec**: রেফারেন্স থেকে বের করা একটি render-নিরপেক্ষ JSON। এতে absolute timestamp থাকবে না, থাকবে *নিয়ম*, যেমন "প্রতিটি hard cut-এর 80 ms আগে whoosh, −12 dB" বা "জোর দেওয়া শব্দে 250 ms-এর punch-in, scale 1.0→1.12"। দ্বিতীয় স্তর **timeline**: একটি deterministic compiler এই নিয়মগুলোকে নতুন ফুটেজের word timing, beat ও shot list-এর সাথে মিলিয়ে absolute-frame টাইমলাইন তৈরি করে।

শত শত timestamp লেখার চেয়ে ছোট, typed একটি schema পূরণে LLM অনেক বেশি নির্ভরযোগ্য। vercel-labs-এর `json-render` ঠিক এভাবে Zod-validated JSON থেকে composition বানায় ([tessl registry](https://tessl.io/registry/skills/github/vercel-labs/json-render/remotion))। একটি community prompt-to-video টেমপ্লেটও LLM-এর structured output Zod দিয়ে যাচাই করে ([webmonch](https://webmonch-blog.pages.dev/blog/building-prompt-to-video-remotion-template))। OpenTimelineIO-কে মূল ফরম্যাট বানাবেন না। এটি শুধু cut-এর ক্রম, দৈর্ঘ্য আর মিডিয়া রেফারেন্স রাখে ([OTIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)), ক্যাপশন অ্যানিমেশন বা SFX নিয়ম এর first-class অংশ নয়। তাই OTIO শুধু Premiere বা Resolve-এ hand-off-এর export হিসেবে রাখুন। Easing সংরক্ষণ করুন cubic-bezier control point হিসেবে, কারণ CSS, After Effects ও Lottie সবাই এই রূপ বোঝে। নিচের উদাহরণের মানগুলো শুধু দৃষ্টান্ত:

```json
{
  "spec_version": "1.0",
  "reference": {"file": "ref.mp4", "fps": 30, "duration_s": 42.3,
                "lufs_i": -13.2, "true_peak_db": -1.1, "side_to_mid_db": -9.5},
  "pacing": {"median_shot_s": 1.8, "p90_shot_s": 3.4, "broll_ratio": 0.35},
  "zoom_events": [{"trigger": "emphasis_word", "type": "punch_in",
                   "scale": [1.0, 1.12], "duration_ms": 250,
                   "easing_bezier": [0.22, 1.0, 0.36, 1.0]}],
  "captions": {"font": "Anek Bangla", "weight": 800, "size_pct_h": 6.5,
               "y_pct": 68, "max_words": 3, "unit": "word",
               "fill": "#FFFFFF", "active_word": "#FFD400",
               "stroke": {"color": "#000000", "px": 8},
               "enter": {"type": "pop", "from_scale": 0.8,
                         "overshoot": 1.12, "duration_ms": 180}},
  "matte": {"model": "birefnet-portrait", "temporal_ema": 0.6, "feather_px": 2},
  "overlays": [{"type": "light_leak", "blend": "screen",
                "opacity": 0.55, "on": "broll_in"}],
  "sfx_rules": [{"event": "hard_cut", "class": "whoosh", "offset_ms": -80, "gain_db": -12},
                {"event": "caption_group_enter", "class": "pop", "offset_ms": 0, "gain_db": -18}],
  "audio": {"target": "match_reference", "music_under_voice_db": -20,
            "duck": {"ratio": 6, "attack_ms": 150, "release_ms": 800}}
}
```

পুরো পাইপলাইন সাতটি ধাপে ভাগ হয়। প্রতিটি ধাপে Remotion/ffmpeg/HyperFrames-এর বাইরের কোন টুল কাজে আসবে, তা নিচের টেবিলে দেওয়া হলো। প্রতিটি টুলের বিস্তারিত পরের অংশগুলোতে আছে।

| ধাপ | কাজ | প্রস্তাবিত টুল | আউটপুট |
|---|---|---|---|
| 1. রেফারেন্স বিশ্লেষণ | cut, zoom, ক্যাপশন, রং, SFX, loudness মাপা | TransNetV2, OpenCV Farneback/RAFT, EasyOCR/Tesseract, Lipika, audio-separator, PANNs, LAION-CLAP, pyloudnorm, Gemini বা Claude frame-grid | `style_spec.json` |
| 2. নতুন ফুটেজের transcript | বাংলা word timing | fine-tuned বাংলা Whisper (stable-ts), ctc-forced-aligner, বা ElevenLabs Scribe/Deepgram | `words.json` |
| 3. Matte | talking head আলাদা করা | BiRefNet + SAM 2.1; CPU-তে RVM/MODNet | cached alpha |
| 4. Compile | নিয়ম + word/beat/shot থেকে absolute frame | নিজের Python compiler + JSON Schema validator | `timeline.json`, `sfx_cues.json` |
| 5. Render | layer compositing | Pillow-RAQM + numpy + ffmpeg (প্রমাণিত); বিকল্প Revideo, MLT, VapourSynth-libass | proxy ও final ভিডিও |
| 6. Audio mix | denoise, ducking, SFX, ক্যালিব্রেশন | DeepFilterNet, `sidechaincompress`, pyloudnorm | `mix.wav` |
| 7. QA | রেফারেন্সের বিপরীতে scorecard | একই extractor + librosa DTW + LPIPS | `score.json` |

শেষ ধাপটিই এই স্থাপত্যের প্রাণ। Adobe Research-এর EditDuet একটি Editor agent দিয়ে টাইমলাইন বানায় আর একটি Critic agent দিয়ে যাচাই করে ([Adobe Research](https://research.adobe.com/publication/editduet-a-multi-agent-system-for-video-non-linear-editing))। CutClaw-তে একটি Reviewer agent clip পরিমার্জন করে ([Hugging Face Papers](https://huggingface.co/papers/2603.29664))। আপনার Critic হবে সংখ্যাভিত্তিক। প্রথমে একটি low-res proxy (যেমন 540×960) render করুন। তারপর রেফারেন্সে যে extractor চালানো হয়েছিল, ঠিক সেগুলোই proxy-তে চালান, আর পার্থক্য structured diff হিসেবে ফেরত দিন, যেমন "zoom duration 420 ms বনাম ref 250 ms; LUFS −18 বনাম −13.2"। LUFS, color statistic বা zoom scale-এর মতো সংখ্যাসূচক প্যারামিটার script নিজেই ঠিক করবে। LLM শুধু discrete সিদ্ধান্ত নেবে: কোন অ্যানিমেশন টাইপ, কোন ফন্ট, কোন SFX। এই কথোপকথনের level-calibration লুপ অডিওর জন্য ঠিক এটাই করেছিল, আর skill-এ সেটিকে প্রতিটি মাত্রায় ছড়িয়ে দেওয়াই মূল উন্নতি।

Compositing-এ layer-এর ক্রম রাখুন background/b-roll, তারপর person alpha, তারপর ক্যাপশন, স্টিকার ও light leak। প্রতিটি layer cache করুন, যাতে matte একবারই হিসাব করতে হয়। Browser-ভিত্তিক renderer ব্যবহার করলে মনে রাখবেন, capture-এর সময় `<video>` playback অনির্ভরযোগ্য, তাই ফ্রেম আগে থেকে decode করে দিতে হয় ([HeyGen research](https://www.heygen.com/research/html-to-video))।

## রেফারেন্স বিশ্লেষণে মাপার কাজ deterministic টুলের, ব্যাখ্যার কাজ VLM-এর

### Cut ও jump cut শনাক্তকরণ

Cut detection-এ প্রথম পছন্দ **TransNetV2** (MIT)। NVIDIA-র Cosmos পেপারে একই ডেটাসেটগুলোতে দুটি টুলের F1 স্কোর তুলনা করা হয়েছে ([arXiv 2501.03575](https://arxiv.org/pdf/2501.03575)):

| ডেটাসেট | PySceneDetect | TransNetV2 |
|---|---|---|
| BBC | 0.889 | **0.967** |
| RAI | 0.831 | **0.919** |
| SHOT | 0.718 | **0.821** |
| ClipShots | 0.477 | **0.726** |

আরেকটি গবেষণায় 200টি ভিডিও হাতে যাচাই করে shot segmentation-এর নির্ভুলতা পাওয়া গেছে PySceneDetect-এর 65.5% আর TransNetV2-এর **87.0%** ([CineTrans](https://arxiv.org/pdf/2508.11484))। PyTorch port পাওয়া যায় `pip install transnetv2-pytorch` দিয়ে ([PyPI](https://pypi.org/project/transnetv2-pytorch/))। AutoShot short-video ডেটাসেটে TransNetV2-এর চেয়ে F1-এ 4.2% এগিয়ে ([arXiv](https://arxiv.org/pdf/2304.06116)), তবে এটি গবেষণা-কোড। PySceneDetect (`scenedetect`, CPU-only) সস্তা প্রথম পাস ও tuning-এর জন্য রাখুন। এর `adaptive` detector দ্রুত ক্যামেরা মুভমেন্টে ভুয়া cut কমায় ([PyPI](https://pypi.org/project/scenedetect/))।

Talking-head-এর **jump cut** কোনো তৈরি detector ধরে না, কারণ সাধারণ cut-এর চেয়ে এগুলো ধরা কঠিন ([OpenCV Q&A](https://answers.opencv.org/question/215834/help-detecting-where-a-video-has-been-cut-up-jump-cuts))। তাই নিজের signal বানান। Background histogram একই থাকল অথচ মুখের bounding box-এর অবস্থান হঠাৎ সরে গেল, তাহলে সেটা jump cut। আর box-এর scale হঠাৎ বদলালে সেটা "hard punch-in", অর্থাৎ একই shot-এর cropped copy-তে cut।

### Zoom ও easing curve

Zoom মাপার প্রমিত পদ্ধতি হলো আগে optical flow, তারপর homography বা affine, তারপর trajectory ([Codesota](https://www.codesota.com/building-blocks/optical-flow))। ধাপগুলো এরকম:

| ধাপ | কী করবেন |
|---|---|
| Flow | পরপর দুটি ফ্রেমের মধ্যে OpenCV Farneback (CPU, সস্তা) বা RAFT (GPU, নির্ভুল) চালান |
| Mask | মানুষ ও টেক্সটের অংশ mask করুন |
| Fit | RANSAC দিয়ে affine fit করুন, তারপর scale = √\|det(A)\| ধরুন |
| মসৃণ করা | Savitzky-Golay দিয়ে curve মসৃণ করে সময়-অক্ষ [0,1]-এ normalize করুন |
| Easing | least-squares দিয়ে cubic-bezier fit করুন, যা সরাসরি spec-এ বসে |

স্বাধীনভাবে চলমান বস্তু, যেমন বাতাসে উড়ন্ত পতাকা বা নড়তে থাকা হাত, এই হিসাব নষ্ট করে, তাই এগুলো বাদ দিতে হবে ([USPTO patent 8810708](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8810708))। সুবিধার দিক হলো Reels-এর zoom প্রায় সবসময় digital, আর এই পদ্ধতি digital zoom-এই সবচেয়ে নির্ভরযোগ্য। তবে easing curve পুনরুদ্ধারে RAFT বনাম Farneback-এর কোনো প্রকাশিত benchmark নেই, তাই tolerance নিজেকেই tune করতে হবে।

### ক্যাপশন OCR ও ফন্ট শনাক্তকরণ

ক্যাপশন বিশ্লেষণের জন্য 4–10 fps-এ ফ্রেম নিয়ে caption band-এ OCR চালান। টেক্সট region-এর diff থেকে প্রতিটি শব্দ-গুচ্ছের প্রথম ও শেষ ফ্রেম, bbox, প্রতি chunk-এ শব্দ সংখ্যা আর ফ্রেমের মধ্যে অবস্থান (শতাংশে) বের হয়ে আসে। প্রথম কয়েক ফ্রেমে box-এর scale যদি 0.8→1.1→1.0 হয়, তাহলে সেটা back-out easing-এর "pop" অ্যানিমেশন।

বাংলা OCR-এ প্রমাণিত baseline দুটি। 216টি বাংলা document image-এর একটি benchmark-এ **Tesseract**-এর character accuracy 88.54% (WER 20.01%) আর **EasyOCR**-এর 90.98% (WER 21.94%) ([BRAC University thesis](https://dspace.bracu.ac.bd/bitstreams/ba79fe28-fbb3-41bb-8f7b-53990b1f892d/download))। EasyOCR Apache-2.0 লাইসেন্সের, আর `gpu=False` দিলে CPU-তে চলে ([GitHub](https://github.com/JaidedAI/EasyOCR))। PaddleOCR PP-OCRv5-এ বাংলা যুক্ত হওয়ার দাবি এখনো শুধু একটি fork-এর README-তে আছে ([GitHub fork](https://github.com/Aariso0/PaddleOCR))। Surya-র weights cc-by-nc-sa লাইসেন্সের, ছোট প্রতিষ্ঠানের জন্য শর্তসাপেক্ষ ছাড় আছে ([GitHub](https://github.com/VikParuchuri/surya))। Stroke, shadow ও gradient-যুক্ত Reels ক্যাপশনে সব engine-ই দুর্বল। তাই আগে caption band crop করুন, k-means দিয়ে টেক্সট আর stroke-এর রং আলাদা করে binarise করুন, 2–3× upscale করুন, তারপর একই ক্যাপশনের 3–5টি ফ্রেমে temporal voting করুন।

ফন্ট শনাক্তকরণের মূলধারার টুল, যেমন WhatTheFont বা Adobe Match Font, মূলত Latin-কেন্দ্রিক। **Lipika** (open-source) বাংলাসহ 13টি ভারতীয় লিপির ফন্টের family, weight ও italic flag ফেরত দেয়। এর নিজস্ব দাবি অনুযায়ী validation-এ top-1 নির্ভুলতা 0.86 আর বাস্তব ছবিতে 0.90 ([PyPI](https://pypi.org/project/lipika/))। Lipika না মিললে render-and-compare করুন: OCR-করা টেক্সট shortlist-এর প্রতিটি ফন্টে Pillow-RAQM দিয়ে render করুন, তারপর binarise-করা crop-এর সাথে SSIM বা embedding similarity মিলিয়ে দেখুন।

### রং ও grade

`color-matcher` লাইব্রেরি Reinhard, MKL, MVGD ও `hm-mvgd-hm` পদ্ধতিতে রেফারেন্সের grade নতুন ফুটেজে স্থানান্তর করে। তবে এর তিনটি সীমাবদ্ধতা আছে: এটি **GPL-3.0**, এর LUT export ডকুমেন্টেড নয়, আর এটি ভিডিও ফাইলে নয়, ফ্রেম-ফোল্ডারে কাজ করে ([GitHub](https://github.com/hahnec/color-matcher))। Skill বিতরণের পরিকল্পনা থাকলে Lab-space-এ Reinhard পদ্ধতি নিজে লিখুন। এটা শুধু mean/std মেলানো, প্রায় 20 লাইনের কোড। পুনর্ব্যবহারের জন্য transfer-টি একটি 33³ identity HALD ছবিতে প্রয়োগ করে `.cube` LUT হিসেবে সেভ করুন, যাতে ffmpeg-এর `lut3d` বা যেকোনো renderer তা ব্যবহার করতে পারে। একটি সতর্কতা: ungraded original ছাড়া শুধু graded রেফারেন্স থেকে আসল LUT পুনরুদ্ধারের কোনো প্রকাশিত পদ্ধতি নেই। Statistic transfer শুধু একটি কাছাকাছি মান দেয়।

### VLM দিয়ে label দেওয়া

VLM-এর কাজ timestamp দেওয়া নয়, প্রতিটি segment-কে label করা: "এটি whip transition", "এখানে 3D emoji sticker ঢুকছে", "light leak কমলা-লাল"। প্রধান বিকল্পগুলোর তুলনা:

| বিকল্প | বৈশিষ্ট্য | খরচ/প্রয়োজন |
|---|---|---|
| **Gemini** | native video নেয়; default-এ প্রতি ফ্রেম 258 token, প্রতি সেকেন্ডে প্রায় 300 token, sampling **1 fps** ([Fora Soft](https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/video-vlms-frame-sampling-token-streaming-2026)) | 2.5 Flash-এ ইনপুট $0.30/1M token ([Fora Soft pricing](https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/real-cost-of-ai-in-video-products-gemini-openai-pricing)) |
| **Twelve Labs Pegasus 1.5** | ব্যবহারকারীর JSON schema অনুযায়ী timestamped metadata ফেরত দেয় ([MarTech Series](https://martechseries.com/video/twelvelabs-launches-pegasus-1-5-turning-raw-video-into-structured-queryable-data-at-scale/)) | প্রতি মিনিট প্রায় $0.029, 600 মিনিট ফ্রি ([pricing calculator](https://www.twelvelabs.io/pricing-calculator)) |
| **Qwen3-VL** (Apache-2.0) | text-timestamp alignment, video OCR, default 2 fps sampling ([GitHub](https://github.com/QwenLM/Qwen3-VL)) | self-host; GPU লাগে |
| **Claude** | native video নেই; প্রতি request-এ 100 (200k-context মডেলে) থেকে 600টি ছবি নেয় ([Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)) | skill-এর ভেতরেই চলে; আলাদা API লাগে না |

Gemini-র 1 fps sampling-এ 0.2–0.5 সেকেন্ডের caption pop বা flash graphics সহজেই বাদ পড়ে। তাই fps 2–5-এ তুলুন, অথবা OCR দেখে বাছাই করা ফ্রেম পাঠান। খরচের হিসাবে 60 সেকেন্ডের একটি Reel 1 fps-এ এক সেন্টেরও কম, আর 5 fps-এ মোটামুটি 2–3 সেন্ট। Video token-এ কোনো multiplier আছে কি না, তা নিয়ে উৎসগুলোর মধ্যে বিরোধ আছে, তাই অফিসিয়াল পাতায় যাচাই করুন।

Claude-এর জন্য সবচেয়ে কার্যকর কৌশল হলো 4–8 fps-এ ফ্রেম নিয়ে 3×3 বা 4×4 contact sheet বানানো, প্রতিটি ফ্রেমে `t=12.4s`-এর মতো লেবেল burn-in করে। শেষে VLM-এর দেওয়া timestamp-কে deterministic cut ও OCR timestamp-এর সাথে মিলিয়ে নিন।

| মাত্রা | প্রস্তাবিত টুল | লাইসেন্স | CPU-তে চলে? |
|---|---|---|---|
| Cut ও shot length | TransNetV2 (মূল), PySceneDetect (প্রথম পাস) | MIT / BSD | হ্যাঁ (TransNetV2 ধীর) |
| Zoom ও easing | OpenCV Farneback, RAFT | Apache-2.0 / BSD | Farneback হ্যাঁ |
| ক্যাপশন টেক্সট ও timing | EasyOCR + Tesseract `ben`, temporal vote | Apache-2.0 | হ্যাঁ |
| ফন্ট | Lipika, render-and-compare | open-source | হ্যাঁ |
| রং | নিজের Reinhard (GPL এড়াতে), `.cube` export | নিজস্ব | হ্যাঁ |
| Segment label | Gemini video বা Claude frame-grid | বাণিজ্যিক API | — |

## বাংলা ক্যাপশনে তিনটি ফাঁদ: ASR, word timing আর যুক্তাক্ষর shaping

### Stock Whisper বাংলায় অচল

প্রথম ফাঁদ হলো stock Whisper। Zero-shot Whisper large-v3-এর বাংলা CER FLEURS-এ **30.46** আর Common Voice 25-এ **37.31** ([BuzzASR model card](https://huggingface.co/BuzzASR/bengali))। Dolphin পেপারের নিজস্ব test set-এ large-v3-এর WER **71.0** ([arXiv](https://arxiv.org/pdf/2503.20212))। Mozilla.ai-র হিসাবে large-v3-turbo-র baseline normalized WER **78.843**। প্রায় 21,400টি Common Voice sample-এ fine-tune করার পর তা নেমে আসে **11.053**-এ ([model card](https://huggingface.co/mozilla-ai/whisper-large-v3-turbo-bn))। অর্থাৎ fine-tuned মডেল ছাড়া বাংলা ক্যাপশন কার্যত অচল।

2026-এর একটি long-form গবেষণায় WhisperX-এর মাধ্যমে চারটি বাংলা মডেল পরীক্ষা করা হয়েছিল। সেখানে tugstugi-র BengaliAI whisper-medium ধারাবাহিকভাবে সবচেয়ে কম WER দিয়েছে ([arXiv 2603.03158](https://arxiv.org/pdf/2603.03158))। আরেকটি দল Demucs দিয়ে কণ্ঠ আলাদা করে আর নীরবতার সীমানায় chunk করে private WER 0.377-এ পৌঁছেছে ([arXiv 2602.21741](https://arxiv.org/html/2602.21741v1))। আরও কয়েকটি বিকল্প:

| মডেল | ফলাফল | লাইসেন্স |
|---|---|---|
| AI4Bharat **IndicWhisper** | বাংলা গড় WER 20.1 ([vistaar](https://github.com/AI4Bharat/vistaar)) | MIT |
| **IndicConformer** বাংলা মডেল | CTC-RNNT hybrid ([HF card](https://huggingface.co/ai4bharat/indicconformer_stt_bn_hybrid_ctc_rnnt_large/raw/main/README.md)) | MIT |
| Meta **MMS** | — | **cc-by-nc-4.0**, অর্থাৎ বাণিজ্যিক নয় ([HF](https://huggingface.co/facebook/mms-1b-all)) |

### Cloud ASR বিকল্প

Cloud-এ বাংলা ও word timestamp দেয় এমন সার্ভিস:

| সার্ভিস | বাংলা সাপোর্ট | দাম ও সীমাবদ্ধতা |
|---|---|---|
| **ElevenLabs Scribe v2** | default-এ word-level timestamp দেয় | তৃতীয় পক্ষের তালিকায় প্রায় $0.22/ঘণ্টা ([Developers Digest](https://www.developersdigest.tech/models/speech/elevenlabs)) |
| **Deepgram Nova-3** | বাংলা তালিকাভুক্ত ([Deepgram](https://deepgram.com/learn/nova-3-adds-12-new-languages-across-europe-and-south-asia)) | প্রায় $0.0043/মিনিট ([convertaudiototext](https://convertaudiototext.com/blog/deepgram-nova-3-explained)) |
| **Google Chirp 3** | bn-BD এখনো Preview | word timestamp চালু করলে "transcription degradation" হতে পারে বলে নিজেরাই সতর্ক করে ([Google docs](https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3)) |
| **Amazon Transcribe** | শুধু bn-IN, শুধু batch | ([AWS](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html)) |

একটি ব্যবহারিক কৌশল: talking-head ভিডিওর script প্রায়ই আগে থেকে লেখা থাকে। সেক্ষেত্রে ASR-এর চেয়ে forced alignment বেশি নির্ভুল ও সস্তা।

### Word timing-এর জন্য forced alignment

দ্বিতীয় ফাঁদ alignment। **WhisperX**-এর default align-model তালিকায় hi, ur, te আছে, কিন্তু bn নেই। বাংলায় model না দিলে এটি `ValueError` ছুড়ে দেয়, তবে যেকোনো Hugging Face wav2vec2 CTC checkpoint হাতে দেওয়া যায় ([alignment.py](https://github.com/m-bain/whisperX/blob/main/whisperx/alignment.py))। অন্য বিকল্পগুলো:

| টুল | ব্যবহার | লাইসেন্স ও সতর্কতা |
|---|---|---|
| **ctc-forced-aligner** | `--language ben --romanize` দিয়ে বাংলা সমর্থন করে ([GitHub](https://github.com/MahmoudAshraf97/ctc-forced-aligner)) | কোড BSD-2, কিন্তু **default মডেল CC-BY-NC**; বাণিজ্যিক কাজে `--alignment_model` দিয়ে অনুমোদিত-লাইসেন্সের বাংলা CTC মডেল দিন |
| **stable-ts** | `align()` জানা টেক্সটকে যেকোনো Whisper checkpoint দিয়ে align করে (বাংলা fine-tune-সহ); `refine()` word-সীমানা আরও আঁটসাঁট করে; ASS `karaoke` export দেয় ([GitHub](https://github.com/jianfch/stable-ts)) | MIT |
| **whisper-timestamped** | — | AGPL-3.0; network service-এ ঝুঁকিপূর্ণ ([GitHub](https://github.com/linto-ai/whisper-timestamped)) |

torchaudio-র `forced_align` API 2.8-এ deprecated হয়ে 2.9-এ মুছে ফেলা হয়েছে ([PyTorch docs](https://docs.pytorch.org/audio/2.9.0/tutorials/ctc_forced_alignment_api_tutorial.html))। তাই এর ওপর কিছু বানাবেন না, অথবা version pin করুন।

প্রস্তাবিত প্রবাহ: ASR বা script থেকে টেক্সট নিন, Claude দিয়ে বানান ঠিক করান, তারপর align করে `words.json` বানান। Align-এর আগে normalization জরুরি: বাংলা বনাম Latin সংখ্যা, দাঁড়ি "।", আর যুক্তাক্ষরের ZWJ/ZWNJ এক নিয়মে আনুন।

### যুক্তাক্ষর shaping

তৃতীয় ফাঁদ হলো shaping। বাংলায় যুক্তাক্ষর, পূর্বস্থিত কার-চিহ্নের (ি ে ৈ) reordering আর রেফ সঠিকভাবে দেখাতে OpenType shaping লাগে। libraqm ছাড়া Pillow বাংলা ভুলভাবে render করে ([Stack Overflow mirror](https://kaweah.freedombox.rocks/kiwix/stackoverflow.com_en_all_2023-11/questions/67361964/blender-render-complex-fonts-as-rendered-with-python-pillow-libraqm))। তাই এই কথোপকথনে RAQM বেছে নেওয়াটা ঠিক সিদ্ধান্ত ছিল। Skill-এ একটি `check_env.py` রাখুন, যা `features.check("raqm")` assert করবে আর প্রতিটি `ImageFont.truetype`-এ `layout_engine=ImageFont.Layout.RAQM` বাধ্যতামূলক করবে। Docker image-এ `libfribidi`-ও রাখতে হবে।

Blender-এর VSE বাংলা ঠিকভাবে render করতে পারে না বলে VSEIndic add-on নিজেই স্বীকার করে ([GitHub](https://github.com/oormicreations/VSEIndic))। গবেষণা দলের Blender 5.2.3-এ স্থানীয় পরীক্ষাতেও একই ফল এসেছে: হসন্ত দৃশ্যমান থাকে, যুক্তাক্ষর তৈরি হয় না। FFmpeg-এর `subtitles` filter আগে `shaping` uninitialized রেখে "simple" shaper-এ আটকে যেত ([ffmpeg-devel patch](https://ffmpeg.org/pipermail/ffmpeg-devel/2021-March/277946.html))। তাই `ass` filter ব্যবহার করলে `shaping=complex` দিন ([FFmpeg docs](https://ayosec.github.io/ffmpeg-filters-docs/7.0/Filters/Video/ass.html))। Shonar Bangla ফন্টে ভুল render-এর একটি ticket এখনো আছে ([trac #10384](https://trac.ffmpeg.org/ticket/10384))। OpenCV-র core `putText` কখনো ব্যবহার করবেন না; `cv2.freetype` module HarfBuzz ব্যবহার করে বলে চলবে ([OpenCV docs](https://docs.opencv.org/4.x/d4/dfc/group__freetype.html))।

কিছু ভাঙন engine-এর নয়, ফন্টের। যেমন Lohit-Bengali-তে ত-এর পরে ি থাকলে যুক্তাক্ষর ভেঙে যায় ([Fedora fonts-bugs](https://lists.fedoraproject.org/archives/list/fonts-bugs@lists.fedoraproject.org/thread/ATQEAJQKDDUVBXC5NK6XPD23FG5MC53K))। তাই skill-এ একটি regression string রাখুন, যাতে ক্ষ, ত্র, ন্ত্র, র্, ি, ৌ আর ১ আছে, এবং প্রতিটি নতুন ফন্ট বা renderer-এ এটি render করে পরীক্ষা করুন। অ্যানিমেশন করুন শব্দ ধরে, বা আধুনিক Unicode grapheme নিয়মে পরীক্ষিত cluster ধরে। প্রতি code point আলাদা করে ভাঙলে যুক্তাক্ষর ভেঙে যাবে।

### বাংলা ফন্ট ও তাদের লাইসেন্স

নিরাপদ বাংলা ফন্টগুলো সব Google Fonts-এর **OFL** লাইসেন্সে পাওয়া যায়:

| ফন্ট | বৈশিষ্ট্য |
|---|---|
| **Hind Siliguri** | পরিষ্কার UI চেহারা; Regular, Medium ও SemiBold weight-এ "১" glyph বিকৃত বলে রিপোর্ট আছে ([Fontsource](https://fontsource.org/fonts/hind-siliguri/about); [bdeshi README](https://git.bdeshi.space/bdeshi/Hind-Siliguri/blame/branch/main/README.md)) |
| **Anek Bangla** | variable ফন্ট: `wdth` 75–125, `wght` 100–800; ক্যাপশনে weight বা width অ্যানিমেট করার জন্য আদর্শ ([METADATA](https://github.com/google/fonts/blob/main/ofl/anekbangla/METADATA.pb)) |
| **Baloo Da 2** | গোলাকার, প্লেফুল "Reels" চেহারা; `wght` 400–800 ([METADATA](https://github.com/google/fonts/blob/main/ofl/balooda2/METADATA.pb)) |
| **Noto Sans Bengali** | সবচেয়ে বিস্তৃত coverage ([Fontsource](https://fontsource.org/fonts/noto-sans-bengali/about)) |
| **Tiro Bangla** | serif, editorial চেহারা ([METADATA](https://github.com/google/fonts/blob/main/ofl/tirobangla/METADATA.pb)) |
| **Kalpurush** | SIL OFL ([GitHub](https://github.com/potasiyam/Kalpurush)) |

সমস্যা আছে কয়েকটি জনপ্রিয় ফন্টে। SolaimanLipi-র লাইসেন্স নিয়ে উৎসগুলো পরস্পরবিরোধী: কেউ বলে OFL কিন্তু বাণিজ্যিক কাজে আলাদা লাইসেন্স লাগবে, কেউ বলে GPL ([maateen](https://fonts.maateen.me/solaiman-lipi); [online-fonts](https://online-fonts.com/fonts/solaimanlipi))। Li Ador Noirrit-এর লাইসেন্স অংশ পরিবর্তন ও বিতরণ নিষিদ্ধ করে ([onlinewebfonts](https://www.onlinewebfonts.com/download/3565357604fee3776c402d09091028bb))। Shonar Bangla বাণিজ্যিক কাজে কেনা লাইসেন্স চায় ([freeforfonts](https://www.freeforfonts.com/fonts/shonar-bangla))। Lipika যদি রেফারেন্সে Li-সিরিজের মতো সীমাবদ্ধ ফন্ট পায়, skill-টি নিজে থেকেই সবচেয়ে কাছের OFL ফন্ট প্রস্তাব করবে।

### ক্যাপশন rendering-এর বিকল্প

Remotion-এর বাইরে ক্যাপশন rendering-এর বিকল্পগুলো:

| টুল | কীভাবে কাজ করে | লাইসেন্স |
|---|---|---|
| **pycaps** | CSS দিয়ে স্টাইল করে, `.word-being-narrated`-এর মতো state selector আছে; Playwright/Chromium দিয়ে render করে; `whisper_json`, SRT ও VTT import করে ([GitHub](https://github.com/francozanardi/pycaps)) | MIT, alpha পর্যায়ে |
| **VapourSynth + assrender** | libass দিয়ে ASS karaoke ক্যাপশন ([mirror](https://gh.r-mj.com/AmusementClub/assrender)) | LGPL |

তবে প্রধান renderer হিসেবে প্রমাণিত Pillow-RAQM পথই রাখুন। এটি pixel-level নিয়ন্ত্রণ দেয়, আর ইতিমধ্যে রেফারেন্সের সাথে মিলেছে। Gradient বা blur-এর মতো CSS-নির্ভর effect লাগলে তখন pycaps বা HTML পথ বিকল্প হিসেবে ব্যবহার করুন।

## লাইসেন্স-নিরাপদ matting-এ BiRefNet ও SAM 2.1, আর Remotion-এর বাইরে Revideo, MLT ও Lottie

### Matting মডেলগুলোর তুলনা

| মডেল | শক্তি | দুর্বলতা ও লাইসেন্স |
|---|---|---|
| **BiRefNet** | portrait, matting, HR-matting ও dynamic variant আছে; RTX 4090 FP16-এ 1024² ছবি প্রতি 57.7 ms ([GitHub](https://github.com/ZhengPeng7/BiRefNet)) | MIT (কোড ও weights); কোনো temporal model নেই, তাই দ্রুত নড়াচড়ায় ঝিলমিল করে ([Replicate](https://replicate.com/sprited/birefnet-video)) |
| **RVM** | recurrent temporal memory আছে; ONNX CPU ও CUDA-তে পরীক্ষিত; RTX 3090 FP16-এ HD-তে 172 fps (শুধু tensor throughput) ([GitHub](https://github.com/PeterL1n/RobustVideoMatting)) | **GPL-3.0**; CPU-র কোনো প্রকাশিত সংখ্যা নেই |
| **MatAnyone / MatAnyone 2** (CVPR 2026) | লেখকদের দাবি অনুযায়ী চুল ও কিনারায় সবচেয়ে স্থিতিশীল | S-Lab লাইসেন্স, শুধু non-commercial ([HF Space](https://peiqingyang-matanyone.hf.space/); [GitHub](https://github.com/pq-yang/MatAnyone2)) |
| **SAM 2.1** | tiny checkpoint A100-এ 91.2 FPS; weights `dl.fbaipublicfiles.com` থেকে সরাসরি নামে, Hugging Face লাগে না ([GitHub](https://github.com/facebookresearch/sam2)) | Apache-2.0 |
| **SAM 3** | "person" text prompt দিয়ে track করে | checkpoint Hugging Face-এ gated; SAM License বাণিজ্যিক ব্যবহার অনুমোদন করে, সামরিক ব্যবহারে নিষেধ ([GitHub](https://github.com/facebookresearch/sam3); [LICENSE](https://github.com/facebookresearch/sam3/blob/main/LICENSE)) |
| **RMBG-2.0** | — | non-commercial ([model card](https://huggingface.co/briaai/RMBG-2.0/blob/refs%2Fpr%2F6/README.md)) |
| **MODNet** | প্রায় 7M parameter, সবচেয়ে হালকা ([GitHub](https://github.com/ZHKKKe/MODNet)) | Apache-2.0 |
| **BackgroundMattingV2** | ফাঁকা background-এর একটি ছবি লাগে; RTX 2080 Ti-তে 4K 30fps ([GitHub](https://github.com/PeterL1n/BackgroundMattingV2)) | MIT |
| **Cutie** | mask propagation ([GitHub](https://github.com/hkchengrex/Cutie)) | MIT |
| **rembg** | u2net_human_seg, isnet ও birefnet-portrait-এর wrapper ([GitHub](https://github.com/danielgatis/rembg)) | MIT |

BiRefNet-এর একটি গুরুত্বপূর্ণ তথ্য আছে। লেখকের নিজের পরিমাপে RTX 4080S-এ steady-state গড় সময় PyTorch-এ 0.15 s, **ONNX-এ 4.43 s**, আর TensorRT-এ 0.11 s ([GitHub](https://github.com/ZhengPeng7/BiRefNet))। এই কথোপকথনে ONNX পথ কাজ করেছে, কিন্তু সেটিই সবচেয়ে ধীর পথ। তাই দীর্ঘ ভিডিও বা নিয়মিত ব্যবহারে GPU-তে PyTorch FP16 বা TensorRT-এ সরে যাওয়াই সবচেয়ে বড় গতি-লাভ।

BackgroundMattingV2-এর শর্তটাও কাজে লাগানো যায়। আপনি যদি tripod-এ শুট করেন, প্রতিটি শটের আগে 3 সেকেন্ডের ফাঁকা background রেকর্ড করলেই সেরা মানের matte পাবেন।

### প্রস্তাবিত matting stack

প্রস্তাবিত লাইসেন্স-নিরাপদ stack চারটি ধাপের:

| ধাপ | কাজ |
|---|---|
| 1 | SAM 2.1 দিয়ে keyframe mask বের করুন |
| 2 | প্রতিটি ফ্রেমে BiRefNet-portrait বা matting চালান |
| 3 | optical flow দেখে alpha-তে EMA smoothing দিন |
| 4 | কিনারায় হালকা feathering দিন |

CPU-তে বিকল্প RVM MobileNetV3 ONNX, `downsample_ratio` 0.25-এ চালালে। ব্যক্তিগত ব্যবহারে এর GPL লাইসেন্স সমস্যা নয়। শুধু ব্যক্তিগত কাজে সর্বোচ্চ মান চাইলে MatAnyone 2 ব্যবহার করতে পারেন। যে মডেলই ব্যবহার করুন, alpha একবার হিসাব করে cache করুন।

### Reframing, upscaling ও interpolation

16:9 ফুটেজকে 9:16 করতে দুটি পথ আছে। প্রথমটি MediaPipe (Apache-2.0) face landmarker-এর সাথে নিজের smoothing: একটি dead-zone রাখুন, one-euro filter দিন, আর cut-এর জায়গায় reset করুন ([GitHub](https://github.com/google-ai-edge/mediapipe))। দ্বিতীয়টি তৈরি সমাধান `pyautoflip` ([PyPI](https://pypi.org/project/pyautoflip/))। দুটি বিকল্প এড়িয়ে চলুন। Ultralytics YOLO SaaS-এর ক্ষেত্রেও AGPL শর্ত চাপায় ([Ultralytics](https://ultralytics.com/license))। InsightFace-এর pretrained মডেলগুলো non-commercial ([PyPI](https://pypi.org/project/insightface/))।

720p ফুটেজে punch-in দিলে ছবি নরম হয়ে যায়। শুধু zoom-করা অংশে Real-ESRGAN ncnn-vulkan (MIT) চালান ([mirror](https://gitee.com/DXFB/Real-ESRGAN-ncnn-vulkan))। Speed ramp-এর জন্য আছে RIFE (MIT), যা 2080 Ti-তে 720p-তে 2× interpolation 30+ FPS-এ করে ([GitHub](https://github.com/hzwer/Pratical-RIFE))। Video2X এই দুটোকে একসাথে প্যাকেজ করে দেয় ([GitHub](https://github.com/k4yt3x/video2x))।

### Remotion-এর বাইরের renderer

| Renderer | লাইসেন্স | বাংলা shaping | কখন ব্যবহার করবেন |
|---|---|---|---|
| Pillow-RAQM + numpy + PyAV (প্রমাণিত) | MIT-CMU / BSD-3 | সঠিক, যদি RAQM থাকে | default; pixel-level নিয়ন্ত্রণ |
| **Revideo** | MIT | সঠিক (Chromium) | Remotion-এর মতো TypeScript code, কোম্পানি-লাইসেন্স ছাড়াই |
| **Twick** render-server | Sustainable Use License | সঠিক (Puppeteer) | JSON tracks-ভিত্তিক টাইমলাইন |
| **MLT/melt** | LGPL | Pango ব্যবহার করে, তাই সঠিক হওয়ার কথা | NLE-মানের XML টাইমলাইন, Kdenlive-এর feature set |
| **VapourSynth + libass** | LGPL | সঠিক | ASS karaoke ক্যাপশন |
| **Manim** | MIT | Pango | title card-এর alpha video |
| Blender `bpy` VSE | GPL-3.0 | **ভাঙা** | বাংলা টেক্সটের জন্য নয় |

**Revideo** হলো Motion Canvas-এর fork। এটি `renderVideo()` দিয়ে headless Node-এ render করে, worker-দের মধ্যে ভাগ করে parallel rendering করে, আর audio export করে। এর 0.11.0 সংস্করণ এসেছে 2026-07-10-এ, প্রায় 15 মাসের বিরতির পর। এটি default-এ telemetry পাঠায়, যা `DISABLE_TELEMETRY=true` দিয়ে বন্ধ করা যায় ([GitHub](https://github.com/midrender/revideo); [npm](https://www.npmjs.com/package/@revideo/core))। দলটি এখন মূলত বাণিজ্যিক পণ্য Midrender নিয়ে কাজ করে, তাই version pin করুন।

**Twick**-এর timeline ফরম্যাট হলো `tracks[]` → `elements[]`, প্রতিটি element-এ `s`/`e` সময় থাকে। এর render-server Puppeteer ও FFmpeg ব্যবহার করে। নিজে host করা যায়, তবে SDK হিসেবে পুনরায় বিক্রি করা যায় না ([GitHub](https://github.com/ncounterspecialist/twick))।

নিজের HTML পাতা থেকে নিয়ন্ত্রিতভাবে ফ্রেম capture করতে চাইলে puppeteer-capture (MIT) কাজে লাগে ([README](https://cdn.jsdelivr.net/npm/puppeteer-capture@1.58.0/README.md))। GSAP এখন SplitText-সহ সবার জন্য ফ্রি। তবে এর লাইসেন্স Webflow-এর সাথে প্রতিযোগী no-code animation builder বানানো নিষিদ্ধ করে ([GSAP license](https://gsap.com/community/standard-license/))। MLT-এর `pango` producer Pango দিয়ে আন্তর্জাতিক টেক্সট layout করে ([MLT](https://mltframework.org/plugins/ProducerPango))। তবে এর Qt module-গুলোর জন্য `xvfb-run` লাগে ([KDE forum](https://forum.kde.org/viewtopic.php%3Ff=265&t=141279.html))।

### Overlay, light leak ও sticker

স্টিকার, emoji burst, তীরচিহ্ন, light-leak বা flash overlay আর wipe-এর জন্য Lottie সবচেয়ে উপযুক্ত। Headless rendering-এর বিকল্পগুলো:

| টুল | অবস্থা |
|---|---|
| ThorVG/dotLottie | MIT; সক্রিয়, `dotlottie-web` 0.81.0 এসেছে অক্টোবর 2026-এ ([npm](https://www.npmjs.com/package/@lottiefiles/dotlottie-web)) |
| Skottie | SkShaper দিয়ে HarfBuzz shaping করে ([Skia](https://skia.googlesource.com/skia/+/3390cdf/tools/SkShaper.h)) |
| rlottie | archived, টেক্সট-সাপোর্ট একেবারেই নেই ([GitHub](https://github.com/Samsung/rlottie)) |
| python-lottie | AGPL ([PyPI](https://pypi.org/project/lottie/)) |
| Rive | কোনো headless renderer নেই; তাদের docs Revideo বা Remotion ব্যবহার করতে বলে ([Rive docs](https://rive.app/docs/runtimes/react/rendering-to-a-bitmap.md)) |

Lottie JSON অনেক বড় ও জটিল। তাই LLM নতুন Lottie লিখবে না, শুধু library থেকে বেছে নিয়ে রং ও timing বদলাবে।

Light leak-এর জন্য লাইসেন্স-সহ ক্লিপের একটি ছোট library রাখুন, আর কথোপকথনে যেভাবে হয়েছে সেভাবে numpy-তে screen blend করুন। Generated sticker বানাতে Nano Banana প্রায় $0.039 প্রতি ছবি ([BenchLM](https://benchlm.ai/md/media-pricing/nano-banana.md)), তারপর BiRefNet বা rembg দিয়ে কেটে নিন। Veo 3.1 Lite 720p-এ $0.05 প্রতি সেকেন্ড ([BenchLM](https://benchlm.ai/md/media-pricing/veo.md)), তাই শুধু গুরুত্বপূর্ণ b-roll-এর জন্য ব্যবহার করুন। বাংলা টেক্সট ছবির ভেতরে generate করাবেন না; compositor-এ আলাদা overlay হিসেবে বসান।

### Cloud render API, NLE ও MCP server

Cloud JSON-to-video API-গুলোর খরচ:

| সার্ভিস | খরচ |
|---|---|
| Shotstack | প্রায় $0.20–0.30/মিনিট ([SpotSaaS](https://www.spotsaas.com/product/shotstack/pricing)) |
| Creatomate | pixel-ভিত্তিক credit, প্রায় $0.25–1.00/মিনিট ([Wireflow](https://www.wireflow.ai/blog/creatomate-pricing)) |
| JSON2Video | credit-ভিত্তিক plan ([docs](https://json2video.com/docs/v2/pricing/plans)) |
| Editframe | cloud rendering $0.02/মিনিট; 3 জন বা তার কম কর্মীর প্রতিষ্ঠানের জন্য ফ্রি ([Editframe](https://editframe.com/render)) |

এদের কেউই বাংলা shaping নথিভুক্ত করেনি। Shotstack নিজেই আন্তর্জাতিক লিপির জন্য HTML asset ব্যবহারের পরামর্শ দেয় ([Shotstack](https://shotstack.io/learn/international-language-character-sets-video/))। তাই যেকোনো সার্ভিস বেছে নেওয়ার আগে যুক্তাক্ষর পরীক্ষা করুন।

পেশাদার NLE-গুলো headless renderer হিসেবে কাজে আসে না:

| NLE বা টুল | সীমাবদ্ধতা |
|---|---|
| DaVinci Resolve | 21.1 থেকে Python scripting শুধু Studio-তে ([Puget Systems](https://www.pugetsystems.com/blog/2026/09/10/how-davinci-resolve-free-v21-1-scripting-changes-affect-puget-bench/)) |
| nexrender (After Effects) | worker শুধু Windows ও macOS-এ চলে ([GitHub](https://github.com/inlife/nexrender)) |
| pyJianYingDraft | draft বানায়, কিন্তু export করতে Windows-এর JianYing অ্যাপ লাগে ([GitHub](https://github.com/GuanYixuan/pyJianYingDraft)) |
| VectCutAPI | MCP দিয়ে CapCut draft লেখে ([GitHub](https://github.com/sun-guannan/VectCutAPI)) |

তাই CapCut draft শুধু "মানুষ এডিটরের কাছে হস্তান্তর" ফিচার হিসেবে রাখুন। কয়েকটি সহায়ক টুলও আছে। **auto-editor** (Unlicense) নীরবতা কাটার প্রথম পাস দেয় আর Premiere বা Resolve XML export করে ([GitHub](https://github.com/WyattBlue/auto-editor))। **kinocut** (Apache-2.0) একটি FFmpeg MCP server, যাতে 205টি typed tool আর guardrail আছে ([GitHub](https://github.com/KyaniteLabs/kinocut))। আপনার Resolve Studio থাকলে DaVinci Resolve MCP (MIT) ব্যবহার করা যায় ([GitHub](https://github.com/samuelgursky/davinci-resolve-mcp))।

## সাউন্ড ডিজাইনে লক্ষ্য platform-এর LUFS নয়, রেফারেন্সের মাপা প্রোফাইল

### রেফারেন্স অডিও ভাঙা

কথোপকথনের mid/side বিশ্লেষণ একটি সস্তা ও কার্যকর প্রথম ধাপ। কণ্ঠ সাধারণত মাঝখানে থাকে, আর SFX ও মিউজিক প্রায়ই চওড়া stereo-তে, তাই Side channel অনেক সময় কোনো ML ছাড়াই SFX আলাদা করে দেয়।

আরও গভীর বিশ্লেষণে **audio-separator** (MIT) ব্যবহার করুন। এর BS-RoFormer মডেল vocals-এ **12.9 dB SDR** আর instrumental-এ 17.0 dB দেয়, যেখানে `htdemucs_ft`-এর vocals 10.8 dB ([GitHub](https://github.com/nomadkaraoke/python-audio-separator))। Demucs 2025-এর 1 জানুয়ারি archived হয়েছে ([GitHub](https://github.com/facebookresearch/demucs))। এরপর residual stem-এ librosa দিয়ে onset বের করুন। প্রতিটি hit-এর 0.5–2 সেকেন্ডের window-তে দুটি জিনিস চালান। প্রথমটি PANNs: এর কোড MIT, এটি 527টি AudioSet class-এ frame-wise sound event detection করে, তবে checkpoint-এর লাইসেন্স উল্লেখ নেই ([GitHub](https://github.com/qiuqiangkong/audioset_tagging_cnn))। দ্বিতীয়টি LAION-CLAP: এর repo CC0, input 48 kHz হতে হবে ([GitHub](https://github.com/LAION-AI/CLAP))। CLAP-কে "whoosh transition", "cartoon pop", "keyboard typing ASMR", "riser"-এর মতো text prompt দিয়ে zero-shot classify করান।

এরপর SFX onset-গুলোকে cut-এর সময় ও ক্যাপশনের শব্দ-সময়ের সাথে মিলিয়ে দেখুন। তাহলে "cut-এর 80 ms আগে whoosh" ধরনের নিয়ম স্বয়ংক্রিয়ভাবে বের হয়ে আসবে। এই কথোপকথনের হাতে-লেখা rule-based cue list তখন রেফারেন্স থেকে শেখা নিয়মে রূপ নেবে। এমন কোনো প্রকাশিত সিস্টেম পাওয়া যায়নি, তাই এটি আপনার skill-এর একটি স্বতন্ত্র শক্তি হবে।

Beat-এর জন্য beat_this ব্যবহার করুন। একটি মাত্র মাধ্যমিক উৎস অনুযায়ী এর লাইসেন্স MIT ([HF](https://huggingface.co/cstr/beat-this-GGUF))। বিকল্প হিসেবে librosa আছে। madmom-এর pretrained মডেল (CC BY-NC-SA) ([PyPI](https://pypi.org/project/madmom/0.14/)) আর Essentia (AGPL) ([record](https://hdl.handle.net/10230/32252)) বাণিজ্যিক কাজে এড়িয়ে চলুন। রেফারেন্স ও render-এর সময়-অক্ষ মেলাতে librosa-র DTW উদাহরণ সরাসরি কাজে লাগে ([librosa](https://librosa.org/doc/main/auto_examples/plot_music_sync.html))।

### SFX সংগ্রহ

কথোপকথনের **synthesized SFX kit** লাইসেন্সের দিক থেকে সবচেয়ে পরিষ্কার উৎস: নিজের তৈরি, attribution লাগে না। তাই এটিকে ভিত্তি হিসেবে রাখুন। বাড়াতে চাইলে বাইরের উৎসগুলোর শর্ত এরকম:

| উৎস | শর্ত |
|---|---|
| Freesound | CC0 filter দিয়ে খুঁজুন; CC-BY হলে attribution list লাগবে ([Cinevva](https://app.cinevva.com/guides/free-sound-effects-music)) |
| Pixabay | attribution লাগে না, কিন্তু আলাদা ফাইল হিসেবে বিক্রি করা যায় না |
| Zapsplat | ফ্রি tier-এ credit দিতে হয়, premium-এ লাগে না ([Zapsplat](https://www.zapsplat.com/license-agreement)) |
| Sonniss GDC bundle | royalty-free, কিন্তু 2024 থেকে AI training নিষিদ্ধ, এমনকি CLAP fine-tune-ও ([GameFromScratch](https://gamefromscratch.com/sonniss-27-5gb-sound-effect-giveaway-at-gdc-2024/)) |
| Epidemic Sound API | prototype-এর জন্য ফ্রি key, production-এ paid; sublicensing, "find similar" আর video frame দিয়ে খোঁজার সুবিধা আছে ([Epidemic Sound](https://www.epidemicsound.com/blog/epidemic-sound-api/)) |
| BBC RemArc | non-commercial ([Freesound forum](https://freesound.org/forum/legal-help-and-attribution-questions/45079)) |

পুরো library-র CLAP embedding একটি FAISS index-এ রাখুন, প্রতিটি ফাইলের সাথে লাইসেন্সের একটি field-সহ। AES 2025-এর একটি গবেষণায় CLAP-ভিত্তিক SFX খোঁজা BBC library-র প্রচলিত workflow-কে উৎপাদনশীলতায় হারিয়েছে ([Surrey PDF](https://personalpages.surrey.ac.uk/w.wang/papers/Liu%20et%20al_AES_2025.pdf))।

Similarity কম হলে generation দিয়ে ঘাটতি পূরণ করা যায়:

| Generator | শর্ত |
|---|---|
| ElevenLabs SFX v2 API | duration সেট করলে সেকেন্ডপ্রতি 11 credit, সর্বোচ্চ 30 s ([ElevenLabs](https://elevenlabs.io/docs/help-center/product/content-production/sound-effects/how-much-does-it-cost-to-generate-sound-effects)) |
| Stable Audio Open | বার্ষিক আয় $1M-এর কম হলে বাণিজ্যিক ব্যবহার ফ্রি ([Stability AI](https://stability.ai/license)) |
| AudioGen / MusicGen | weights CC-BY-NC ([audiocraft](https://github.com/facebookresearch/audiocraft)) |
| MMAudio | checkpoint CC-BY-NC ([GitHub](https://github.com/hkchengrex/MMAudio)) |
| HunyuanVideo-Foley | EU, UK ও দক্ষিণ কোরিয়ায় লাইসেন্সপ্রাপ্ত নয় ([Creative AI News](https://www.creativeainews.com/articles/how-to-add-sound-effects-to-ai-video-2026/)) |

### মিউজিক

মিউজিকে সবচেয়ে কম ঝুঁকির পথ Epidemic Sound API। ACE-Step 1.5-এর কোড MIT; এটি 4 GB-এর কম VRAM-এ চলার দাবি করে, আর 10 সেকেন্ড থেকে 10 মিনিট পর্যন্ত মিউজিক বানায়। কিন্তু এর weights-এর লাইসেন্স যাচাই হয়নি, আর এটি নিজেই শৈলীগত মিলের কারণে copyright-এর ঝুঁকির কথা বলে ([GitHub](https://github.com/ace-step/ACE-Step-1.5))। YuE কোম্পানির ব্যবহারে আলাদা লাইসেন্স চায় ([GitHub](https://github.com/multimodal-art-projection/YuE))। Suno নভেম্বর 2025-এ WMG-র সাথে চুক্তির পর বর্তমান মডেলগুলো বাতিল করে 2026-এ লাইসেন্সপ্রাপ্ত নতুন মডেল আনবে, আর download-এর জন্য paid account লাগবে ([Music Business Worldwide](https://www.musicbusinessworldwide.com/warner-music-group-settles-with-suno-strikes-first-of-its-kind-deal-with-ai-song-generator/))। Udio একটি "walled garden"-এ রূপ নিচ্ছে, যেখানে export সীমিত ([Music Business Worldwide](https://www.musicbusinessworldwide.com/warner-music-settles-udio-lawsuit-strikes-licensing-deal-with-ai-platform/))। তাই এই দুটির ওপর পাইপলাইন বানাবেন না।

### Loudness লক্ষ্য ও mixing chain

Platform-এর loudness লক্ষ্য বিতর্কিত। সবচেয়ে বেশি উদ্ধৃত মান **−14 LUFS integrated ও −1 dBTP** ([loudfix](https://loudfix.pages.dev/blog/what-is-lufs/))। OpusClip বলে −10 থেকে −12 ([OpusClip](https://opus.pro/blog/best-loudness-normalizers))। 2026-এর একটি লেখা বলে platform-গুলো ফাইল বদলায় না, playback-এর সময় normalize করে ([Fora Soft](https://www.forasoft.com/learn/audio-for-video/articles-audio/lufs-targets-per-platform-2026))। Meta বা TikTok-এর কোনো অফিসিয়াল spec নেই। তাই এই skill-এর লক্ষ্য কোনো platform সংখ্যা নয়, বরং **রেফারেন্সের মাপা integrated LUFS, LRA, true peak আর mid/side ভারসাম্য**। এই কথোপকথনে ঠিক এটাই করা হয়েছিল, এবং এটাই সঠিক পদ্ধতি।

প্রস্তাবিত mixing chain:

| ধাপ | কাজ ও টুল |
|---|---|
| 1. Denoise | DeepFilterNet (Apache-2.0/MIT, 48 kHz, প্রায় 40 ms latency) ([LinuxLinks](https://www.linuxlinks.com/deepfilternet-low-complexity-speech-enhancement-framework/)); খুব খারাপ ফোন-অডিওতে Resemble Enhance (MIT) ([HF](https://huggingface.co/ResembleAI/resemble-enhance/blob/refs%2Fpr%2F3/README.md))। ASR-এর আগেও চালান |
| 2. কণ্ঠের লেভেল | কণ্ঠের stem-এর লেভেল ঠিক করুন |
| 3. Ducking | `sidechaincompress`: threshold 0.01–0.05, ratio 3–8, attack 100–300 ms, release 500–2000 ms ([FFmpeg Cookbook](https://ffmpeg-cookbook.pages.dev/en/articles/audio-ducking/)) |
| 4. SFX | নিয়ম অনুযায়ী SFX বসান |
| 5. Measure-and-adjust | pyloudnorm (ITU-R BS.1770-4, MIT) দিয়ে মাপুন ([GitHub](https://github.com/csteinmetz1/pyloudnorm)) |
| 6. চূড়ান্ত gain | দুই-পাস `loudnorm`; এক পাসে "pumping" হয় ([DEV](https://dev.to/masonwritescode/two-pass-loudness-normalization-with-ffmpeg-loudnorm-the-right-way-1nm3)) |

রেফারেন্সে মিউজিক স্পষ্ট না থাকলে fallback নিয়ম হিসেবে kmilo93sd-এর skill-এর মান ব্যবহার করুন: কণ্ঠের 18–25 dB নিচে মিউজিক ([GitHub](https://github.com/kmilo93sd/agent-video-editor))।

## 500 লাইনের SKILL.md, deterministic scripts আর evals: Claude Code plugin হিসেবে প্যাকেজিং

### Skill-এর গঠন ও context খরচ

একটি Agent Skill হলো একটি ফোল্ডার। এতে থাকে `SKILL.md` আর ঐচ্ছিক `scripts/`, `references/` ও `assets/`। Frontmatter-এর নিয়ম:

| Field | নিয়ম |
|---|---|
| `name` | সর্বোচ্চ 64 অক্ষর; ছোট হাতের অক্ষর, সংখ্যা ও hyphen; "anthropic" বা "claude" শব্দ নিষিদ্ধ |
| `description` | সর্বোচ্চ 1,024 অক্ষর; skill কী করে আর কখন ব্যবহার করতে হবে, দুটোই বলতে হবে |

Skill তিন স্তরে context-এ ঢোকে ([Claude Platform docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)):

| স্তর | কখন লোড হয় | খরচ |
|---|---|---|
| Metadata | সবসময় | প্রায় 100 token |
| `SKILL.md`-এর body | skill trigger হলে | 5k token-এর কম |
| বাকি ফাইল | প্রয়োজন হলে | না পড়া পর্যন্ত শূন্য; script bash-এ চলে, শুধু তার output context-এ ঢোকে |

শেষ নিয়মটাই আপনার জন্য সবচেয়ে গুরুত্বপূর্ণ। হাজার লাইনের compositing কোড কখনো Claude-এর context-এ ঢুকবে না, শুধু তার ফলাফল ঢুকবে। Skills ডিসেম্বর 2025-এ একটি open standard হয়েছে ([Anthropic Engineering](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills); [agentskills](https://github.com/agentskills/agentskills))।

### কোন surface-এ চালাবেন

সব surface-এ skill সমানভাবে চলে না:

| Surface | যা জানা দরকার |
|---|---|
| **Claude Code** | skill থাকে `~/.claude/skills`, `.claude/skills` বা কোনো plugin-এ; `${CLAUDE_SKILL_DIR}` substitution আছে; `` !`command` `` দিয়ে dynamic context দেওয়া যায় (ব্যর্থ হলে invocation বাতিল হয়, তাই শেষে `\|\| true` দিন); `context: fork` দিয়ে subagent-এ চালানো যায়; compaction-এর পর প্রতিটি skill-এর প্রথম 5,000 token থাকে, মোট 25,000 token বাজেটের মধ্যে ([Claude Code docs](https://code.claude.com/docs/en/skills)) |
| **claude.ai** | Settings > Features থেকে zip upload করতে হয়, প্রতি ব্যবহারকারী আলাদা; code execution লাগে; network সেটিং অনুযায়ী বদলায়; surface-গুলোর মধ্যে skill sync হয় না ([overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)) |
| **API** | প্রতি request-এ সর্বোচ্চ 20টি skill; `code_execution` tool লাগে; upload সর্বোচ্চ 30 MB; **network বা runtime install নেই** ([Skills guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide); [best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)) |

ONNX মডেল, onnxruntime আর বাংলা ASR weights 30 MB-তে ধরবে না। তাই পূর্ণ skill হবে Claude Code plugin। claude.ai-এর জন্য চাইলে একটি "lite" সংস্করণ রাখুন, যা শুধু রেফারেন্স বিশ্লেষণ করে style spec লিখবে।

### অনুসরণযোগ্য উদাহরণ

Anthropic-এর `anthropics/skills`-এ কোনো video skill নেই ([GitHub](https://github.com/anthropics/skills))। কাঠামোর জন্য সবচেয়ে ভালো উদাহরণ **kmilo93sd/agent-video-editor** ([GitHub](https://github.com/kmilo93sd/agent-video-editor))। এর গঠন: `SKILL.md`, `review-checklist.md`, প্রতিটি বিষয়ের আলাদা `references/`, প্রতিটি ভিডিও-ধরনের জন্য `recipes/`, search tool-সহ 128টি CC0 শব্দের `library/`, আর `evals/`। এতে নিয়মগুলো সংখ্যায় লেখা আছে, যেমন প্রতি লাইনে 42 অক্ষর, সর্বোচ্চ 2 লাইন, অন্তত 20 ফ্রেম; graphic যে শব্দে তার উল্লেখ, তার সর্বোচ্চ 0.5 s আগে ঢুকবে; zoom কখনো cut পার হবে না।

**kinocut** দেখায় guardrail কেমন হওয়া উচিত ([GitHub](https://github.com/KyaniteLabs/kinocut))। এতে default-এ 205টির মধ্যে বাছাই করা 20টি tool থাকে। Raw flag-এর বদলে typed tool, preflight check আর QA checkpoint আছে। Hash-সহ "Video Receipts" provenance রাখে, আর overwrite-এর আগে সম্মতি চায়। Distribution-এর উদাহরণ হিসেবে দেখুন remotion-dev/skills ([GitHub](https://github.com/remotion-dev/skills)) আর HyperFrames-এর plugin marketplace ([GitHub](https://github.com/heygen-com/hyperframes))।

প্রস্তাবিত ফোল্ডার কাঠামো:

```text
editing-reels-like-reference/
├── SKILL.md                     # router, workflow checklist, hard rules (<500 লাইন)
├── references/
│   ├── style-spec-schema.md     # প্রতিটি field-এর মানে ও বৈধ পরিসর
│   ├── analysis-recipe.md       # cut/zoom/OCR/color/SFX বিশ্লেষণ
│   ├── bengali-captions.md      # ASR, alignment, shaping, ফন্ট-তালিকা
│   ├── compositing-matting.md   # layer ক্রম, matte, light leak
│   ├── audio-sfx-loudness.md    # mid/side, ducking, calibration
│   ├── export-specs.md
│   └── licenses.md
├── scripts/
│   ├── check_env.py             # raqm, ffmpeg, onnxruntime, ফন্ট যাচাই
│   ├── setup_models.sh          # GitHub Releases/dl.fbaipublicfiles থেকে weights + sha256
│   ├── analyze_reference.py     # → style_spec.json + contact sheets
│   ├── transcribe_bn.py         # → words.json
│   ├── validate_spec.py         # JSON Schema; বিস্তারিত error
│   ├── compile_timeline.py      # → timeline.json, sfx_cues.json
│   ├── matte.py                 # cached alpha
│   ├── render.py                # --proxy / --final
│   ├── mix_audio.py             # রেফারেন্স-লক্ষ্যে calibration
│   └── score.py                 # scorecard → score.json
├── assets/
│   ├── fonts/                   # শুধু OFL
│   ├── sfx/                     # synthesized kit + CC0, licenses.csv
│   ├── overlays/                # light leak, Lottie
│   └── styles/                  # আগে বিশ্লেষিত রেফারেন্সের style_spec
└── evals/evals.json
```

### SKILL.md লেখার নিয়ম

`SKILL.md`-এ Anthropic-এর best-practice নিয়মগুলো মানুন ([best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)):

| নিয়ম | বিস্তারিত |
|---|---|
| আকার | body 500 লাইনের কম |
| Reference | `SKILL.md` থেকে মাত্র এক স্তর গভীরে; 100 লাইনের বেশি হলে শুরুতে সূচিপত্র |
| Workflow | কপি করা যায় এমন checklist আর feedback loop |
| Plan-validate-execute | `style_spec.json` ও `timeline.json` script দিয়ে যাচাই করে তারপর render; validator-এর error বার্তা বিস্তারিত |
| Script | "solve, don't punt": নিজেই error সামলাবে, "voodoo constant" এড়াবে; প্রতিটি script চালাতে হবে না পড়তে হবে, তা স্পষ্ট লিখুন |
| Default | অনেক বিকল্পের বদলে একটি default দিন |

skill-creator-এর পরামর্শও কাজে লাগে ([skill-creator](https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md))। নিয়মের পেছনের "কেন" ব্যাখ্যা করুন। সব-বড়-হাতের MUST বা NEVER একটি সতর্কসংকেত। Description একটু "pushy" রাখুন, যাতে skill কম trigger না হয়। আপনি বাংলায় কথা বলেন, তাই description-এ বাংলা trigger বাক্যও রাখুন:

```yaml
---
name: editing-reels-like-reference
description: Re-edits talking-head + b-roll footage (Bengali-first) to match a reference Reels/TikTok/Shorts video's style - captions and their animation, punch-in zooms, transitions, background removal and compositing, light leaks and overlays, SFX/ASMR placement, music and loudness. Analyses the reference into a validated style spec, renders a proxy, then measures and adjusts until it matches. Use when the user shares a reference video plus raw footage, or says "এই ভিডিওর মতো এডিট করো", "রিলস স্টাইলে এডিট", "same style as this", "copy this edit".
allowed-tools: Bash, Read, Write
---
```

### ধাপে ধাপে তৈরির পরিকল্পনা

| ধাপ | কী বানাবেন | মূল টুল | কখন শেষ ধরবেন |
|---|---|---|---|
| 1. প্রমাণিত কোড জমাট করা | কথোপকথনের compositing, matte, SFX kit ও calibration কোড `scripts/`-এ সরিয়ে CLI argument দিন; `check_env.py` বানান | Pillow-RAQM, numpy, ffmpeg, onnxruntime | একই ইনপুটে কথোপকথনের ফলাফল byte-কাছাকাছি পুনরুৎপন্ন হয় |
| 2. Schema | style spec-এর JSON Schema ও `validate_spec.py` | `jsonschema` বা pydantic | ভুল spec দিলে field-ধরে বিস্তারিত error আসে |
| 3. Analyzer | cut, zoom, OCR-ক্যাপশন, ফন্ট, রং, অডিও থেকে `style_spec.json`; সাথে Claude-এর পর্যালোচনার জন্য contact sheet | TransNetV2, Farneback, EasyOCR + Tesseract, Lipika, audio-separator, PANNs, CLAP, pyloudnorm | কথোপকথনের রেফারেন্স থেকে হাতে-বানানো spec-এর কাছাকাছি spec আসে |
| 4. বাংলা transcript | ASR বা script থেকে টেক্সট, তারপর alignment ও normalization | বাংলা fine-tuned Whisper + stable-ts বা ctc-forced-aligner; বিকল্প Scribe বা Deepgram | word-সীমানার ত্রুটি হাতে-চিহ্নিত নমুনায় গ্রহণযোগ্য |
| 5. Compiler | নিয়ম, শব্দ, beat ও shot থেকে `timeline.json` আর শেখা নিয়ম থেকে `sfx_cues.json` | নিজস্ব Python | একই ইনপুটে নির্ধারিত (deterministic) আউটপুট |
| 6. Renderer | `--proxy` ও `--final` মোড; layer cache | প্রমাণিত Pillow/numpy পাইপলাইন, ffmpeg | proxy এক মিনিটের মধ্যে; যুক্তাক্ষর regression পাস |
| 7. Audio | denoise, duck, SFX, রেফারেন্স-লক্ষ্যে calibration লুপ | DeepFilterNet, `sidechaincompress`, pyloudnorm | LUFS ও mid/side রেফারেন্সের ±0.5 dB-এর মধ্যে |
| 8. Scorecard লুপ | proxy-তে একই extractor, diff, স্বয়ংক্রিয় সংশোধন, সর্বোচ্চ N বার | `score.py`, librosa DTW, LPIPS | সব মাত্রা tolerance-এর মধ্যে আসে, অথবা কারণসহ রিপোর্ট দেয় |
| 9. SKILL.md ও references | router, checklist, নিয়ম, লাইসেন্স | skill-creator | Haiku, Sonnet ও Opus তিনটিতেই ঠিক পথ অনুসরণ করে |
| 10. Evals ও প্যাকেজিং | কমপক্ষে 3টি scenario, description optimisation, plugin ও marketplace | skill-creator, `claude plugin validate` | with-skill run baseline-কে স্পষ্টভাবে হারায় |

ধাপ 7-এর ±0.5 dB tolerance একটি প্রস্তাব, কোনো প্রকাশিত মান নয়। নিজের রেফারেন্সে পরীক্ষা করে ঠিক করুন।

### Evals ও scorecard

skill-creator-এর eval পদ্ধতি এরকম ([skill-creator](https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md)):

| ধাপ | কাজ |
|---|---|
| Test prompt | `evals/evals.json`-এ 2–3টি prompt রাখুন |
| তুলনা | with-skill আর baseline run সমান্তরালে চালান |
| মূল্যায়ন | grader দিয়ে `grading.json` বানান, তারপর `aggregate_benchmark` চালান |
| Description optimisation | 20টি query (8–10টি trigger করবে, 8–10টি প্রায়-মিল কিন্তু করবে না), 60/40 train/test ভাগ, প্রতিটি 3 বার চালানো; এর জন্য `claude -p` লাগে |
| প্যাকেজিং | `package_skill` দিয়ে `.skill` ফাইল বানান |

তিনটি eval scenario প্রস্তাব করা হলো। প্রথমটি এই কথোপকথনের রেফারেন্স ও ফুটেজ, যা golden regression হিসেবে কাজ করবে। দ্বিতীয়টি সম্পূর্ণ ভিন্ন স্টাইলের একটি রেফারেন্স, যেমন minimal ক্যাপশন আর SFX ছাড়া, যাতে skill শুধু একটি স্টাইলে overfit না হয়। তৃতীয়টি background মিউজিক ও শব্দদূষণ-যুক্ত, যুক্তাক্ষর-ভরা বাংলা ফুটেজ।

Scorecard-এর মাত্রাগুলো নিচে। এটি একটি নকশা, কোনো যাচাই-করা metric নয়; tolerance বাস্তব রেফারেন্সে tune করতে হবে।

| মাত্রা | দুই ভিডিও থেকে যা বের করবেন | তুলনা |
|---|---|---|
| Pacing | shot-দৈর্ঘ্যের বিন্যাস (TransNetV2) | KS বা Wasserstein দূরত্ব; প্রতি সেকেন্ডে cut-এর পার্থক্য |
| Zoom | প্রতি shot-এর scale curve | DTW দূরত্ব; bezier প্যারামিটারের L2 |
| ক্যাপশন timing | শব্দ শুরু থেকে ক্যাপশন দেখা দেওয়ার latency, স্ক্রিনে থাকার সময় | ms-এ গড় পরম ত্রুটি |
| ক্যাপশন চেহারা | একই টেক্সটের crop | LPIPS ([GitHub](https://github.com/richzhang/PerceptualSimilarity)); ফন্ট-ID মিল |
| রং | Lab mean/std, প্রতি shot-এর hue histogram | ΔE (CIEDE2000), EMD |
| Loudness | integrated LUFS, LRA, true peak, mid/side | LU-তে পার্থক্য |
| SFX | cut-এর তুলনায় onset offset, CLAP embedding | ms অফসেট; cosine similarity |

VMAF শুধু চূড়ান্ত encode-এর মান-হ্রাস ধরার জন্য রাখুন। এর v1 model set 2026-06-এ এসেছে, লাইসেন্স BSD+Patent ([GitHub](https://github.com/Netflix/vmaf))। FVD ব্যবহার করবেন না: এটি content-biased, আর একক ভিডিওর তুলনায় অচল ([arXiv 2404.12391](https://arxiv.org/pdf/2404.12391))।

### বিতরণ

বিতরণের জন্য একটি GitHub repo-তে `.claude-plugin/marketplace.json` রাখুন। তারপর ধাপগুলো ([Claude Code docs](https://code.claude.com/docs/en/plugin-marketplaces)):

```bash
claude plugin validate .
claude plugin marketplace add <owner>/<repo>
claude plugin install <plugin>@<marketplace>
```

অন্য agent-এর ব্যবহারকারীদের জন্য Vercel-এর `npx skills add <owner>/<repo>` 20টির বেশি agent-এ install করে। তবে এর directory skill-এর মান বা নিরাপত্তার নিশ্চয়তা দেয় না ([Vercel](https://vercel.com/changelog/introducing-skills-the-open-agent-skills-ecosystem))। Weights repo-তে রাখবেন না। `setup_models.sh` সেগুলো GitHub Releases থেকে নামাবে (BiRefNet-এর ONNX v1 release-এ আছে, RVM-এর v1.0.0-এ) আর SAM 2.1-এর `dl.fbaipublicfiles.com` থেকে, প্রতিটির sha256 যাচাই করে। কিছু sandbox-এ huggingface.co ব্লক থাকে, তাই Hugging Face-নির্ভর weights-এর বিকল্প উৎস রাখুন।

## লাইসেন্সের তিন স্তর আর প্রতি Reel-এ কয়েক সেন্টের খরচ

লাইসেন্স ঝুঁকি তিন স্তরে ভাগ করা যায়। নিচের ব্যাখ্যা আইনি পরামর্শ নয়।

| স্তর | টুল ও মডেল | ব্যবহারিক মানে |
|---|---|---|
| **নিরাপদ** (MIT, Apache, BSD, OFL, CC0) | BiRefNet, SAM 2.1, MODNet, BGMv2, Cutie, rembg, TransNetV2, EasyOCR, Qwen3-VL, IndicWhisper, IndicConformer, stable-ts, audio-separator, LAION-CLAP, pyloudnorm, DeepFilterNet, Resemble Enhance, MediaPipe, Real-ESRGAN-ncnn, RIFE, Revideo, PyAV, Pillow, OFL বাংলা ফন্ট, auto-editor | ব্যক্তিগত, বাণিজ্যিক ও বিতরণ, সব ক্ষেত্রেই সাধারণত চলে; attribution ও NOTICE ফাইল রাখুন |
| **Copyleft বা শর্তসাপেক্ষ** | RVM ও color-matcher (GPL-3.0), whisper-timestamped, Essentia, python-lottie ও Ultralytics (AGPL), MLT (LGPL), Remotion (3 জন কর্মী পর্যন্ত ফ্রি) ([LICENSE](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)), Twick (SUL), GSAP (প্রতিযোগী builder নিষিদ্ধ), Stable Audio Open (আয় $1M-এর কম), SAM 3 (সামরিক ব্যবহার নিষিদ্ধ), Sonniss (AI training নিষিদ্ধ), Zapsplat-এর ফ্রি tier (credit লাগে) | নিজের মেশিনে নিজের ভিডিওর জন্য চালানো সাধারণত ঠিক আছে; skill বিতরণ বা SaaS বানালে শর্ত সক্রিয় হয় |
| **Non-commercial** | MatAnyone 1/2, RMBG-2.0, VRMBG-3.0, Meta MMS, ctc-forced-aligner-এর default মডেল, madmom-এর মডেল, AudioGen, MusicGen ও MMAudio-র weights, BBC RemArc, InsightFace-এর মডেল, Surya (শর্তসাপেক্ষ) | monetised Reels-এ ব্যবহার করবেন না; কেবল পরীক্ষার জন্য রাখুন |

GPL মূলত বিতরণের সময় সক্রিয় হয়, আর AGPL network service চালালেও। তাই আপনি একা নিজের চ্যানেলের ভিডিও বানালে RVM বা color-matcher ব্যবহার সমস্যা নয়। কিন্তু skill-টি public repo-তে ছাড়লে বা অন্যদের সার্ভিস হিসেবে দিলে এগুলো আলাদা optional module-এ রাখুন, অথবা নিজে পুনরায় লিখুন, যেমন Reinhard। Hugging Face-এর বাংলা মডেলগুলোর (tugstugi, mozilla-ai, BuzzASR) লাইসেন্স গবেষণায় যাচাই করা যায়নি। বাণিজ্যিক ব্যবহারের আগে প্রতিটির model card দেখুন।

খরচের হিসাব 60 সেকেন্ডের একটি Reel ধরে করা:

| খাত | বিকল্প | আনুমানিক খরচ |
|---|---|---|
| রেফারেন্স VLM বিশ্লেষণ | Gemini 2.5 Flash, 1 fps / 5 fps | < $0.01 / প্রায় $0.02–0.03 (প্রতি রেফারেন্সে একবার) |
| | Twelve Labs Pegasus | প্রায় $0.03; 600 মিনিট ফ্রি ([calculator](https://www.twelvelabs.io/pricing-calculator)) |
| | Claude frame-grid | আলাদা খরচ নেই, session-এর ভেতরেই হয় |
| বাংলা ASR | ElevenLabs Scribe v2 / Deepgram Nova-3 | প্রায় $0.004 |
| | self-hosted fine-tuned Whisper | শুধু GPU সময় |
| Matting (GPU) | RunPod RTX 4090 pod, $0.34/ঘণ্টা থেকে ([RunPod](https://www.runpod.io/gpu-cloud/pricing)); BiRefNet প্রায় 17 FPS-এ 1,800 ফ্রেম প্রায় 2 মিনিটে | প্রায় $0.01 |
| | Modal L4, প্রায় $0.80/ঘণ্টা ([BudgetForge](https://www.budgetforge.dev/tools/modal-pricing-2026)) | কয়েক সেন্ট |
| Render | নিজের CPU-তে প্রমাণিত পাইপলাইন | প্রায় শূন্য |
| | Shotstack বা Creatomate | $0.20–1.00 |
| SFX generation (ঐচ্ছিক) | ElevenLabs SFX v2 | সেকেন্ডপ্রতি 11 credit |
| স্থির খরচ (প্রয়োজন হলে) | Remotion Automators: render-প্রতি $0.01, মাসে ন্যূনতম $100 ([Remotion pricing](https://www.remotion.dev/docs/license/pricing)); Resolve Studio $295 এককালীন | — |

Matting-এর হিসাবে 30 fps-এ 60 সেকেন্ড মানে 1,800 ফ্রেম। সব মিলিয়ে নিজের মেশিনে render করলে বাইরের খরচ প্রতি ভিডিওতে কয়েক সেন্ট। সবচেয়ে বড় খরচ তখন আপনার Claude subscription আর নিজের সময়। বাংলাদেশ থেকে Modal, RunPod বা AWS-এ কার্ড ও USD billing কতটা সহজ, তা এই গবেষণায় দেখা হয়নি। এটি একটি বাস্তব বাধা হতে পারে, আর সেক্ষেত্রে স্থানীয় GPU বা CPU-only পথই নিরাপদ।

Export-এর জন্য প্রস্তাবিত preset:

| প্যারামিটার | মান |
|---|---|
| রেজোলিউশন | 1080×1920 |
| Codec | H.264 High, yuv420p |
| Frame rate | 30 fps; রেফারেন্স 60 হলে 60 |
| অডিও | AAC 48 kHz, প্রায় 192 kbps |
| Container | MP4, `+faststart` |
| Bitrate | প্রায় 8–12 Mbps |

Instagram-এর bitrate নির্দেশনা উৎসভেদে 3.5 থেকে 15 Mbps পর্যন্ত পরস্পরবিরোধী ([SocialPilot](https://www.socialpilot.co/instagram-marketing/instagram-video-size); [argil](https://argil.ai/blog/instagram-reel-size-e350f)), তাই মাঝামাঝি মান নেওয়া হয়েছে। TikTok-ও 1080×1920 সুপারিশ করে, আর নিচের ও কিনারার UI এলাকায় গুরুত্বপূর্ণ জিনিস না রাখতে বলে ([Benly](https://benly.ai/learn/tiktok-ads/tiktok-video-specs))। ক্যাপশন নিচের প্রায় 20% আর ডান পাশের বোতাম-কলাম থেকে দূরে রাখুন।

## উপসংহার

এই গবেষণার সবচেয়ে বড় শিক্ষা হলো, প্রতিযোগিতার সুবিধা renderer-এ নেই। Remotion, Revideo, Pillow-RAQM বা MLT সবাই বাংলা ক্যাপশন ঠিকঠাক আঁকতে পারে। যা কেউ প্রকাশ করেনি, তা দুটি জিনিস। প্রথমটি রেফারেন্স থেকে নিয়মের স্বয়ংক্রিয় নিষ্কাশন, বিশেষ করে SFX onset, cut ও শব্দ-সময়ের পারস্পরিক সম্পর্ক থেকে শেখা SFX-placement নিয়ম। দ্বিতীয়টি দুই ভিন্ন-বিষয়ের ভিডিওর মধ্যে "style distance" মাপার একটি scorecard। এই কথোপকথন অডিওর জন্য দ্বিতীয়টির কঠিনতম অংশ, অর্থাৎ measure-and-adjust লুপ, ইতিমধ্যে বানিয়ে ফেলেছে। ভিজ্যুয়াল মাত্রাগুলোতে সেটি ছড়িয়ে দিলেই একবারের সাফল্য একটি পণ্য হয়ে ওঠে। প্রতিটি বিশ্লেষিত রেফারেন্স `assets/styles/`-এ একটি সংরক্ষিত spec হয়ে থাকবে। ফলে skill-টি সময়ের সাথে একটি স্টাইল-ক্যাটালগে পরিণত হবে, যা OpenStoryline-এর Style Skills-এর মতো, কিন্তু ডকুমেন্টেড ও বাংলা-প্রথম।

একই সাথে বাংলা এই কাজের সবচেয়ে বড় ঝুঁকি এবং সবচেয়ে বড় পার্থক্যকারী। কোনো cloud renderer বাংলা shaping নথিভুক্ত করেনি, WhisperX-এ বাংলা aligner নেই, আর মূলধারার ফন্ট-ID Latin-কেন্দ্রিক। তাই এই তিনটি সমাধান করা একটি skill সত্যিই বিরল। কিছু প্রশ্ন এখনো খোলা। Scorecard-এর tolerance বাস্তব রেফারেন্সে tune করতে হবে। বাংলা word-timing নির্ভুলতার কোনো প্রকাশিত benchmark নেই। Platform-এর loudness লক্ষ্য অনানুষ্ঠানিক। Gemini-র video-token মূল্য নিয়ে উৎসগুলোর মধ্যে বিরোধ আছে। এগুলো দুর্বলতা হলেও সুযোগও: যে নিজের রেফারেন্সে এই মাপগুলো জমা করবে, তার কাছেই থাকবে এমন একটি ডেটাসেট, যা আর কারও কাছে নেই।
