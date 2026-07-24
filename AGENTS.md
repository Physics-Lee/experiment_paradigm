# Repository Guidance

## Purpose and layout

This repository contains fullscreen Pygame paradigms for locked-in sentence
reading, relaxing news, general sentences, word reading, and audio listening.

- `src/experiment_paradigm/` contains the maintained package implementation.
  `paradigms/` contains one implementation module per experiment; `core/`
  contains shared runtime services; `commands/` owns argument parsing and
  defaults; `stimuli/` owns input parsing; and `tts.py` generates neural audio.
  `cli.py`, `news.py`, and `text_units.py` are compatibility re-exports.
- `scripts/` contains thin repository-checkout wrappers only. Maintained
  behavior, defaults, validation, and reusable imports belong in the package.
- `stimuli/` contains authoritative UTF-8 sentence/word lists and Markdown news
  tables.
- `assets/` contains intentional, versioned listening audio, sentence TTS assets,
  manifests, and example videos.
- `timestamp/` contains versioned example results and receives generated run
  output.
- `docs/` contains repository documentation.
- `reference/` contains local-only raw reference material and is not runtime
  input.

## Working conventions

- Run commands from the repository root because scripts use relative paths.
- Keep timing values in seconds and preserve the event/timestamp field names
  when changing experiment behavior.
- Do not launch the fullscreen entry points as an automated check. They require
  a display and user input; press Escape to exit an interactive run.
- `pyproject.toml` is the package and dependency source of truth;
  `requirements.txt` mirrors its pinned runtime dependencies for simple setup.
- Installed console commands are `run-sentence-audio`,
  `run-sentence-audio-zh`, `run-locked-in-sentence-reading`, `run-reading`,
  `run-listening`, `run-relaxing-news`, `generate-sentence-audio`, and
  `generate-news-audio`.
- The primary locked-in workflow defaults to
  `stimuli/yan_jiangyi_v4.txt` with
  `assets/sentence_audio/yan_jiangyi_v4_slow/manifest.json`. Each repetition
  is shuffled by default, and inter-trial rests show the centered gray cross by
  default. Preserve the explicit opt-outs `--no-shuffle` and
  `--no-rest-cross` when changing its CLI.
- The primary relaxation workflow is `scripts/run_relaxing_news.py`; its rest
  screen retains the current news by default and advances only after the
  minimum rest and an enabled button click.
- Use this non-interactive syntax check after Python edits:
  `python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('src').rglob('*.py')]"`

## Generated files and safety

- Treat newly created `timestamp/*.csv` and `timestamp/*.json` files as local
  run output unless a specific result is intentionally selected as a fixture.
- Treat `docs/generated/`, PDFs, caches, logs, and local environment files as
  generated or machine-local; they are ignored by Git.
- Existing tracked timestamp files and media are repository fixtures/assets.
  Do not remove, rewrite, recompress, or untrack them without explicit approval.
- Preserve unrelated working-tree changes, especially experiment data and
  stimulus edits.
