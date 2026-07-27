# Sentence Audio Guidance

Each audio-set directory contains ordered sentence MP3 assets and one
`manifest.json`. The current locked-in sets use
`locked_in_v4/<full-voice-name>/`, paired with
`stimuli/yan_jiangyi_v4.txt`; `zh-CN-YunxiaNeural/` is the default.

- Treat each manifest as the source of truth for sentence order, voice settings,
  synthesis text, pronunciation aliases, duration, and SHA-256 checksum.
- Regenerate through `generate-sentence-audio`; do not hand-edit or recompress MP3
  files.
- Keep manifest text aligned with the corresponding file in `stimuli/`.
- Preserve the visible segment `text`; pronunciation substitutions such as
  `觉` → `叫` belong in the generated `tts_text` field.
- Never load a manifest marked `"complete": false` in an experiment.
- Keep alternative voices in separate directories. Never mix MP3 files from
  different voices or TTS settings in one audio set.
