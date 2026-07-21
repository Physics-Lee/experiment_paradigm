# Experiment Paradigms

Fullscreen Pygame paradigms for sentence speaking, word reading, and audio
listening experiments. Run commands from the repository root because stimulus
and output paths are relative to it.

## Environment

The repository includes a pinned Python dependency list:

```powershell
conda create -n experiment_paradigm python=3.12 pip -y
conda activate experiment_paradigm
python -m pip install -e .
```

## Source layout

- `src/experiment_paradigm/paradigms.py` contains the maintained, reusable
  Pygame implementations.
- `src/experiment_paradigm/cli.py` contains argument parsing, defaults, and
  installed experiment entry points.
- `src/experiment_paradigm/tts.py` contains resumable neural TTS generation.
- `stimuli/` contains the authoritative sentence and word lists.
- `assets/` contains listening audio, sentence TTS assets, and example videos.
- `scripts/` contains thin compatibility entry points for running directly from
  a repository checkout. It contains no experiment behavior or defaults.

In short, `src/` is the product code and the only implementation source of
truth. `scripts/` is a convenience adapter: it adds `src/` to the import path
and calls a package entry point.

## Generate sentence audio

The generator uses Microsoft Edge online neural TTS to produce one stable MP3
per non-empty stimulus line. Generation requires network access; experiment
playback does not.

```powershell
conda activate experiment_paradigm

# English
generate-sentence-audio `
  --sentences stimuli/sentences_en.txt `
  --output-dir assets/sentence_audio/en `
  --voice en-US-JennyNeural

# Chinese
generate-sentence-audio `
  --sentences stimuli/sentences.txt `
  --output-dir assets/sentence_audio/zh `
  --voice zh-CN-XiaoxiaoNeural
```

Each output directory contains a `manifest.json` recording the ordered sentence
mapping, TTS settings, duration, and SHA-256 checksum. Matching files are
reused. An existing unmatched file is never overwritten unless `--force` is
explicitly supplied after review.

## Run the sentence paradigm with audio

```powershell
conda activate experiment_paradigm

# English: word-by-word visual progression
run-sentence-audio

# Chinese: locked-in patient sentence-reading flow
run-sentence-audio-zh

# Explicit equivalent command
run-locked-in-sentence-reading
```

Compatibility wrappers remain under `scripts/`:
`python scripts/run_sentence_audio_en.py` runs English and
`python scripts/run_sentence_audio_zh.py` runs Chinese.

The English command retains the general sentence-audio sequence:

1. matching sentence audio on a fixation screen;
2. a 0.5-second pre-visual gap;
3. the existing preparation and sentence animation;
4. a 0.5-second post-visual gap;
5. the same matching sentence audio;
6. the existing inter-sentence interval.

The Chinese commands implement
[`locked_in_sentence_reading_paradigm.md`](locked_in_sentence_reading_paradigm.md).
Every trial uses:

1. a randomized 1.5–2.5-second black resting baseline before the first trial
   only;
2. the large white sentence and red square appearing first;
3. after a randomized 0.4–0.6-second visual lead, the matching target audio
   playing while the sentence and red square remain visible;
4. after the audio ends, a randomized 2.0–3.0-second silent delay that keeps
   the same sentence and red square visible;
5. one synchronized onset for the green square, first character progress bar,
   and category-neutral cue tone;
6. character-by-character progress bars, taking 3.0 seconds per character by
   default;
7. a 0.5-second final-state hold and randomized 5.0–6.0-second rest with a
   large gray cross centered on black, followed directly by the next trial
   without an extra black transition.

The sentence is automatically fitted as a single centered row in the upper
half of the screen. The square occupies 75% of the lower-half height and is
centered in that half. Character transitions remain green so the current
progress stays visible.

Press Escape or click the mouse to stop. Completed trials are saved as paired
CSV and JSON files under `timestamp/`. The output includes audio identifiers,
runtime duration, audio command onset and offset timestamps, randomized planned
and actual phase durations, square/cue onset, every character's green onset,
last-character completion, and trial end.

Useful options:

```powershell
run-sentence-audio --help
run-sentence-audio --audio-screen black
run-sentence-audio --pre-visual-gap 0.75 --post-visual-gap 0.75
run-sentence-audio --no-post-audio
run-sentence-audio-zh --char-speed 1.0
run-sentence-audio-zh --play-mode progress `
  --progress-duration 3.0 --progress-pause 0.5
run-sentence-audio-zh --no-cue-tone
run-sentence-audio-zh --cue-volume 0.9
run-locked-in-sentence-reading --baseline-min 1.5 --baseline-max 2.5
```

The recorded audio timestamps describe mixer playback commands and completion,
not the exact physical onset at the speaker. Calibrate audio latency on the
target experiment computer before participant data collection.

## Run the reading and listening paradigms

Installed commands:

```powershell
run-reading
run-listening
```

Equivalent repository-checkout wrappers:

```powershell
python scripts/run_reading.py
python scripts/run_listening.py
```

Use `--help` on either installed command to inspect its package-owned defaults.

## Tests

The automated test suite uses SDL dummy video and audio drivers and does not
launch an interactive fullscreen session:

```powershell
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
python -m unittest discover -s tests -v
```

Example videos and the original audio assets are from
[Sound of Text](https://soundoftext.com/). Special thanks.
