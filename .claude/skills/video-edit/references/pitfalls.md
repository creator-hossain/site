# Pitfalls

## Bengali text
- Pillow must report `features.check("raqm") == True`, otherwise conjuncts (ক্ষ, স্ব, শ্র) and pre-base vowel signs (ি ে ৈ) render wrong. Pillow BASIC layout, Blender's video editor and libass with "simple" shaping all break Bengali.
- Animate per word, or per grapheme cluster (`regex` module `\X`, or the cluster logic in `v6/compose_v6.py`); never split a word into code points.
- Mixed Bengali + Latin lines: render each run with a font that has its glyphs (see `tmask` in `v10`, `hind_mask` in `v8`).
- Fonts in `video-pipeline/fonts/` and `fonts8/` are OFL (free for commercial use). Hind Siliguri has a slightly odd "১" in some weights.

## Mattes and compositing
- u2net (default) is fast; BiRefNet (`--birefnet`, `v8/birefmatte.py`) gives cleaner hair but is slower (~10 s/frame on CPU via ONNX). Never average mattes across a cut.
- If the matte grabs a car or loses the face, fall back to a soft body mask from the head track.
- Order: background / graphics behind -> person (matte as alpha) -> captions, stickers, light leaks on top.

## Windows notes
- Use `python`, not `python3`. After installing ffmpeg with winget, open a **new** terminal so PATH updates.
- Pillow on Windows needs the FriBiDi library for raqm: a `fribidi.dll` must be in a folder on PATH (Pillow docs). One way: get the MSYS2 package `mingw-w64-x86_64-fribidi` (from repo.msys2.org), take `libfribidi-0.dll`, copy it as `fribidi.dll` next to `python.exe`, re-run `setup_check.py`. If raqm still fails, run the whole skill inside **WSL Ubuntu** (`wsl --install`), where `apt install libfribidi0` makes it work - this exact Linux setup produced all videos.
- `multiprocessing.Pool` works on Windows because the compose scripts create the pool under `if __name__ == "__main__":`; keep it that way in new scripts.
- Quote paths that contain spaces or Bengali characters.

## Licences (commercial videos)
- Safe: BiRefNet (MIT), u2net/rembg (MIT/Apache), SAM 2.1 (Apache), OFL fonts, Lucide icons (ISC), synthesized SFX (ours), CC0 sounds (Freesound with CC0 filter, Pixabay).
- Avoid for monetised videos: MatAnyone, RMBG-2.0 (BRIA), MusicGen / AudioGen / MMAudio weights, Meta MMS - non-commercial.
- Never use the Higgsfield tools for this user.
