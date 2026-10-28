# Corolla Cross ভিডিও এডিটিং পাইপলাইন

এই কথোপকথনে reference ভিডিও দেখে Corolla Cross ভিডিও যেভাবে এডিট করা হয়েছে, তার সব script, ডেটা, font, icon আর final ভিডিও এই folder-এ আছে। সবকিছু ffmpeg আর Python (Pillow + numpy) দিয়ে করা, কোনো AI ভিডিও জেনারেটর ব্যবহার করা হয়নি।

## কোন folder-এ কী আছে

| Folder | কী আছে |
|---|---|
| `videos/` | যে ভিডিওগুলো আপনাকে পাঠানো হয়েছিল, সেগুলোর final কপি (`corolla_v3.mp4` … `corolla_v10.mp4` এবং শুরুর দিকের ভার্সন) |
| `source/` | আপনার নিজের ফুটেজ (`corolla_source.mp4`), voice (`voice.mp3`) আর transcript (`voice_transcript.pdf`) |
| `full/` | শুরুর পাইপলাইন: `compose_full.py`, মাথার tracking ডেটা `track.json`, শব্দের সময় `aud/words.json` আর alignment script `aud/align.py` |
| `v4/` … `v10/` | প্রতিটা reference-এর জন্য আলাদা ভার্সন (নিচের টেবিল দেখুন) |
| `v2/`, `v3/`, `final/`, `r2/`, `scene/`, `work/`, `cmp/` | শুরুর দিকের ভার্সন, caption-এর `.ass` ফাইল আর পরীক্ষার script |
| `seg/scripts/`, `scene/scripts/` | background removal (matte) আর গাড়ির cutout বানানোর script |
| `fonts/bnx/`, `fonts8/` | ব্যবহার করা font (Anek Bangla, Baloo Da 2, Hind Siliguri, Poppins, Exo 2, Kalpurush ইত্যাদি, সবগুলো OFL) |
| `v9/icons/`, `v10/icons/` | Lucide icon থেকে বানানো PNG (ISC license) |
| `v5/car/` | ফুটেজ থেকে কেটে নেওয়া গাড়ির ছবি (graphic-এ ব্যবহৃত) |

## প্রতিটা ভার্সনের ফাইল

প্রতিটা `vN/` folder-এ সাধারণত এই ফাইলগুলো থাকে:

| ফাইল | কাজ |
|---|---|
| `compose_vN.py` | প্রতিটা frame আঁকে (লেখা, graphic, transition) আর ffmpeg-এ পাঠায়; সাথে sound cue-র তালিকা (`*_cues.json`) বানায় |
| `sfx*.py` | সব SFX (whoosh, pop, boom, tick ইত্যাদি) Python দিয়ে synthesize করে |
| `mix_vN.py` | voice-এর সাথে SFX আর music মেশায় |
| `calib*.py` | reference-এর sound লেভেল মেপে আমার mix-এর সাথে মেলায় |
| `level*.json` | calibration শেষে ঠিক হওয়া লেভেল (voice-এর তুলনায় dB) |

| ভার্সন | Reference-এর স্টাইল |
|---|---|
| v3 | প্রথম দিকের motion-graphics স্টাইল |
| v4 | SFX/ASMR সহ প্রথম ভার্সন |
| v5 | harmonic blip, stamp, bounce SFX |
| v6 | typewriter caption, প্রতি অক্ষরে tick |
| v7 | হালকা নীল আকাশ, মানুষের পিছনে বড় লেখা |
| v8 | sky "world", 3D ম্যাপ, glass wipe (BiRefNet matte) |
| v9 | অন্ধকার talk-show, glass box তালিকা, চাবির বৃষ্টি |
| v10 | podcast band layout, bubble, info card, icon tile |

## আবার চালাতে যা লাগবে

1. **Software:** `ffmpeg`, Python 3, আর `pip install pillow numpy scipy soundfile onnxruntime cairosvg fonttools`। Pillow-এ `libraqm` থাকতে হবে, নাহলে বাংলা যুক্তাক্ষর ভেঙে যায় (`python3 -c "from PIL import features; print(features.check('raqm'))"` দিয়ে দেখে নিন)।
2. **Font:** কিছু script font খোঁজে `/usr/share/fonts/truetype/bnx/` থেকে। তাই `fonts/bnx/`-এর ফাইলগুলো সেখানে কপি করুন।
3. **Frame বের করা:** ফুটেজ থেকে 25fps-এ frame:
   ```bash
   mkdir -p full/src && ffmpeg -i source/corolla_source.mp4 -vf fps=25 full/src/f_%04d.png
   ```
4. **Matte (background removal):** model ফাইল repo-তে নেই (GitHub-এর 100MB সীমার বেশি), এখান থেকে নামাতে হবে:
   - `u2net_human_seg.onnx`: https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx
   - BiRefNet: https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx

   তারপর `seg/scripts/` বা `scene/scripts/batch_matte.py` দিয়ে `full/matte/` বানান। v8-এর জন্য `v8/birefmatte.py` দিয়ে `v8/bm/` বানান।
5. **Render উদাহরণ (v10):**
   ```bash
   cd v10
   python3 -I compose_v10.py ../full/src ../full/track.json ../full/aud/words.json video_v10.mp4
   python3 -I mix_v10.py $PWD ../source/corolla_source.mp4 video_v10_cues.json mix_v10.wav level10.json
   ffmpeg -i video_v10.mp4 -i mix_v10.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest corolla_v10.mp4
   ```
   শুধু কয়েকটা frame দেখতে চাইলে শেষে `--preview 2.4,8.2,30.0` দিন।

## যা এখানে রাখা হয়নি, আর কেন

- **Frame আর matte ফোল্ডার** (প্রায় 1.5GB+): ফুটেজ থেকে আবার বানানো যায় (উপরের ধাপ 3–4)।
- **AI model ফাইল** (`.onnx`, 100–230MB): GitHub-এ 100MB-এর বড় ফাইল রাখা যায় না; নামানোর link উপরে আছে।
- **মাঝের ফাইল** (`video_vN.mp4`, `mix_vN.wav`, preview ছবি): final ভিডিওতেই সব আছে, আর script দিয়ে আবার বানানো যায়।
- **Reference ভিডিওগুলো** (WhatsApp থেকে পাঠানো `VID-2026…` ফাইল): এগুলো অন্যের বানানো ভিডিও, তাই GitHub-এ তোলা হয়নি। এগুলো আপনার ফোনেই আছে।

গবেষণার পূর্ণ report আছে `../reports/` folder-এ।
