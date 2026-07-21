# Audio Asset Guidance

This directory contains the MP3 stimuli loaded by `ListeningParadigm` in
`src/experiment_paradigm/paradigms.py`. The class discovers `.mp3`, `.wav`, and
`.ogg` files and shuffles the resulting playlist.

- Audio files are intentional, versioned experiment inputs; do not edit,
  normalize, rename, or recompress them unless the experiment design requires
  it.
- Preserve stimulus basenames because timestamp output records each basename as
  the presented audio file.
- When adding a stimulus, confirm that its format is supported by Pygame and
  account for the configured repetition count in the resulting trial count.
- Keep generated recordings and audio-editing project files outside this
  directory.
