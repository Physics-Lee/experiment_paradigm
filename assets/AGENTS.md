# Asset Guidance

This directory contains intentional, versioned experiment media.

- `listening_audio/` contains inputs discovered by `ListeningParadigm`.
- `sentence_audio/` contains versioned sentence neural-TTS sets such as
  `yan_jiangyi_v4_slow/`, each paired with its own manifest.
- `news_audio/` contains date-versioned whole-news TTS sets and manifests.
- `example_videos_v1/` and `example_videos_v2/` contain reference recordings.
- Moving or adding an asset requires updating code, documentation, and manifests
  that reference its path.
- Do not rename, recompress, normalize, or delete existing media without explicit
  experiment-design approval.
