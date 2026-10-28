# Project notes for Claude

- The user writes romanized Bangla; answer in Bengali (Bangla script), short and simple.
- Video editing: use the `video-edit` skill (`.claude/skills/video-edit/`) and the proven pipeline in `video-pipeline/`.
- Never use Higgsfield tools or AI video generators; edits are rendered with Python + ffmpeg.
- Show preview frames before a full render; match the reference's sound by measuring it.
- Large files (frames, mattes, model weights) stay out of git (see `.gitignore`); commit scripts, style notes and final videos.
