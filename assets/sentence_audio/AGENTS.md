# Sentence Audio Guidance

Each versioned subdirectory contains ordered sentence MP3 assets and one
`manifest.json`. The current primary locked-in set is
`yan_jiangyi_v4_slow/`, paired with `stimuli/yan_jiangyi_v4.txt`.

- Treat each manifest as the source of truth for sentence order, voice settings,
  synthesis text, pronunciation aliases, duration, and SHA-256 checksum.
- Regenerate through `generate-sentence-audio`; do not hand-edit or recompress MP3
  files.
- Keep manifest text aligned with the corresponding file in `stimuli/`.
- Preserve the visible segment `text`; pronunciation substitutions such as
  `觉` → `叫` belong in the generated `tts_text` field.
- Never load a manifest marked `"complete": false` in an experiment.
