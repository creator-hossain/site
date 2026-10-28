# -*- coding: utf-8 -*-
"""One-time setup + health check for the video-edit skill (Windows, macOS, Linux).

  python .claude/skills/video-edit/scripts/setup_check.py            # check, install missing pip packages, download u2net
  python .claude/skills/video-edit/scripts/setup_check.py --birefnet # also download BiRefNet (224 MB, cleaner hair edges)

Prints OK / FIX lines. Every FIX line says what to do.
"""
import sys, os, shutil, subprocess, importlib.util, urllib.request, platform

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
MODELS = os.path.join(ROOT, "video-pipeline", "models")
PKGS = {"PIL": "pillow", "numpy": "numpy", "scipy": "scipy", "soundfile": "soundfile", "onnxruntime": "onnxruntime"}
URLS = {"u2net_human_seg.onnx": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx",
        "birefnet-lite.onnx": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx"}
bad = 0
def ok(msg): print("OK  ", msg)
def fix(msg):
    global bad; bad += 1; print("FIX ", msg)

print(f"python {platform.python_version()} on {platform.system()}  |  repo: {ROOT}")
if sys.version_info < (3, 9): fix("Python 3.9+ needed (python.org, tick 'Add python.exe to PATH').")

missing = [p for m, p in PKGS.items() if importlib.util.find_spec(m) is None]
if missing:
    print("installing:", " ".join(missing))
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", *missing])
for m, p in PKGS.items():
    (ok if importlib.util.find_spec(m) else fix)(f"python package {p}" + ("" if importlib.util.find_spec(m) else " - run: python -m pip install " + p))

for tool in ("ffmpeg", "ffprobe"):
    (ok if shutil.which(tool) else fix)(f"{tool} on PATH" + ("" if shutil.which(tool) else
        " - Windows: winget install Gyan.FFmpeg (then open a NEW terminal) | macOS: brew install ffmpeg | Linux: apt install ffmpeg"))

try:
    from PIL import features
    if features.check("raqm"): ok("Pillow can shape Bengali (raqm)")
    else:
        fix("Pillow has NO raqm -> Bengali conjuncts will break. "
            + ("Windows: Pillow needs FriBiDi as fribidi.dll in a PATH folder (see references/pitfalls.md); "
               "if that fails, run the skill inside WSL Ubuntu." if platform.system() == "Windows"
               else "macOS: brew install fribidi | Linux: apt install libfribidi0 libraqm0, then reinstall pillow."))
except Exception as e:
    fix(f"Pillow import failed: {e}")

fonts = os.path.join(ROOT, "video-pipeline", "fonts", "bnx", "BalooDa2-BN-ExtraBold.ttf")
(ok if os.path.exists(fonts) else fix)("repo fonts present" + ("" if os.path.exists(fonts) else " - is the repo fully cloned?"))

os.makedirs(MODELS, exist_ok=True)
want = ["u2net_human_seg.onnx"] + (["birefnet-lite.onnx"] if "--birefnet" in sys.argv else [])
for name in want:
    dst = os.path.join(MODELS, name)
    if not os.path.exists(dst) or os.path.getsize(dst) < 10_000_000:
        print(f"downloading {name} ...", flush=True)
        try: urllib.request.urlretrieve(URLS[name], dst + ".part"); os.replace(dst + ".part", dst)
        except Exception as e: fix(f"download {name} failed ({e}) - download it in a browser from {URLS[name]} into {MODELS}"); continue
    ok(f"model {name} ({os.path.getsize(dst) // 1_000_000} MB)")

print("\nALL GOOD - ready to edit." if not bad else f"\n{bad} thing(s) to fix (see FIX lines).")
