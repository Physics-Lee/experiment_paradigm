# Sentence Audio Guidance

The `en/` and `zh/` subdirectories contain ordered sentence MP3 assets and a
`manifest.json` for each language.

- Treat each manifest as the source of truth for sentence order, voice settings,
  duration, and SHA-256 checksum.
- Regenerate through `generate-sentence-audio`; do not hand-edit or recompress MP3
  files.
- Keep manifest text aligned with the corresponding file in `stimuli/`.
- Never load a manifest marked `"complete": false` in an experiment.
