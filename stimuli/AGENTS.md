# Stimulus Guidance

This directory contains authoritative experiment inputs.

- Keep text and Markdown files UTF-8 encoded.
- Line-oriented sentence files use one non-empty stimulus per trial.
- `yan_jiangyi_v5.txt` is the current primary locked-in stimulus and maps by
  line number to the selected
  `assets/sentence_audio/yan_jiangyi_v5/<full-voice-name>/` directory.
- `news/*.md` may use a Markdown table; the runtime extracts the column whose
  header contains `标题`.
- `words_reading.txt` is the reading-paradigm word list.
- After changing a sentence file, regenerate and review its audio manifest before
  running participant sessions.
- After changing a news file, generate a matching date-versioned directory
  under `assets/news_audio/`.
