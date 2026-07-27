# Asset Guidance

This directory contains intentional, versioned experiment media.

- `listening_audio/` contains inputs discovered by `ListeningParadigm`.
- `sentence_audio/` stores maintained task sets as
  `<task-version>/<full-voice-name>/`, each paired with its own manifest.
- `news_audio/` stores whole-news TTS sets as
  `<news-date>/<full-voice-name>/`.
- `example_videos_v1/` and `example_videos_v2/` contain reference recordings.
- Moving or adding an asset requires updating code, documentation, and manifests
  that reference its path.
- Do not rename, recompress, normalize, or delete existing media without explicit
  experiment-design approval.
