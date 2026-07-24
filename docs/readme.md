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

- `src/experiment_paradigm/paradigms/` contains one maintained Pygame
  implementation module per experiment type.
- `src/experiment_paradigm/core/` contains shared audio, display, timing,
  lifecycle, and result-persistence services.
- `src/experiment_paradigm/commands/` contains argument parsing, defaults, and
  installed experiment entry points. `cli.py` remains a compatibility import.
- `src/experiment_paradigm/tts.py` contains resumable neural TTS generation.
- `stimuli/` contains the authoritative sentence and word lists.
- `assets/` contains listening audio, sentence TTS assets, and example videos.
- `scripts/` contains thin compatibility entry points for running directly from
  a repository checkout. It contains no experiment behavior or defaults.

In short, `src/` is the product code and the only implementation source of
truth. `scripts/` is a convenience adapter: it adds `src/` to the import path
and calls a package entry point.

## Display mode

All runnable paradigms default to borderless desktop fullscreen. This fills the
current desktop without asking Windows to switch display resolution, so other
application windows are not resized or moved when an experiment starts or
ends.

Every experiment command accepts the same selector:

```powershell
# Recommended default: borderless desktop fullscreen
run-sentence-audio-zh --display-mode borderless

# Optional legacy Pygame exclusive fullscreen
run-sentence-audio-zh --display-mode exclusive
```

`exclusive` uses `pygame.FULLSCREEN` and may switch the system display mode on
some Windows, DPI-scaling, or multi-monitor configurations. Use `borderless`
for OBS recording unless the target experiment computer has been tested with
exclusive fullscreen.

## Generate sentence audio

The generator uses Microsoft Edge online neural TTS to produce one stable MP3
per non-empty stimulus line. Generation requires network access; experiment
playback does not.

The primary locked-in v4 set uses character-by-character Chinese TTS:

```powershell
conda activate experiment_paradigm
generate-sentence-audio `
  --sentences stimuli/yan_jiangyi_v4.txt `
  --output-dir assets/sentence_audio/yan_jiangyi_v4_slow `
  --voice zh-CN-XiaoxiaoNeural `
  --rate=-50% `
  --tts-unit character
```

The output directory contains a `manifest.json` recording the ordered sentence
mapping, TTS settings, duration, and SHA-256 checksum. Matching files are
reused. An existing unmatched file is never overwritten unless `--force` is
explicitly supplied after review.

The generator defaults to `--tts-unit auto`: stimuli containing only Chinese
ideographs are sent to TTS one character at a time, while English and other
text remain one TTS request per line. For example, `手机` produces two audio
segments (`手`, then `机`) under one trial item in the manifest. Use
`--tts-unit line` to force the former whole-line behavior or
`--tts-unit character` to force character segmentation. Playback preloads all
segments, plays them consecutively, and records every segment's onset and
offset.

`--rate` controls relative Edge TTS speaking speed, not an exact output
duration. For example, PowerShell requires `--rate=-50%` for a negative rate.
Different characters and phrases do not scale to an identical duration per
character, so exact targets such as 3.0 seconds per Chinese character require a
separate pitch-preserving time-stretching step that is not built into this
generator. Use `edge-tts --list-voices` to inspect available voice names and
`python scripts/generate_sentence_audio.py -h` for generation/reuse details.

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
4. after the audio ends, a randomized 1.5–2.0-second silent delay that keeps
   the same sentence and red square visible;
5. one synchronized onset for the green square, first character progress bar,
   and category-neutral cue tone;
6. character-by-character progress bars, taking 3.0 seconds per character by
   default;
7. a 0.5-second final-state hold and randomized 5.0–6.0-second black rest,
   optionally showing a centered gray cross, followed directly by the next trial
   without an extra black transition.

The sentence is automatically fitted as a single centered row in the upper
half of the screen. The square occupies 60% of the lower-half height and is
centered in that half. Character transitions remain green so the current
progress stays visible.

Press Escape or click the mouse to stop. Completed trials are saved as paired
CSV and JSON files under `timestamp/`. The output includes audio identifiers,
runtime duration, audio command onset and offset timestamps, randomized planned
and actual phase durations, square/cue onset, every character's green onset,
last-character completion, and trial end.

Use `--repetitions N` to run the full stimulus list N times. Each repetition
is independently shuffled by default; use `--no-shuffle` for file order.
Output rows retain the
original `stimulus_index` and add `repetition` plus `repetition_trial`, so the
actual randomized presentation order is recoverable from the timestamps.

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
run-sentence-audio-zh --no-rest-cross
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

## Run the relaxing news paradigm

The separate news paradigm is intended for passive patient relaxation. It
accepts either a plain UTF-8 file with one news item per non-empty line or a
Markdown table. For a Markdown table it automatically extracts the column whose
header contains `标题`, so table headers, categories, and scores are not read
aloud.

Generate today's six news recordings once using the normal Microsoft neural
voice speed:

```powershell
python scripts/generate_news_audio.py
```

Then run the fullscreen paradigm using the local generated audio:

```powershell
python scripts/run_relaxing_news.py
```

Each news item appears as wrapped white text at a maximum 40-pixel font size
with a centered 100-pixel red square. The square remains red throughout the
news presentation; there is no reading progress, green state, or cue tone.
Audio starts 0.5 seconds after the text appears at the generated `+0%` normal
speed. The final news screen remains for 1.0 second after audio completion,
then begins a randomized 5.0–6.0-second minimum rest while retaining the news
page by default. When the minimum rest ends, the patient must click the
hover-responsive `下一条` button to continue. Use `--rest-screen cross` to show
the small gray cross instead; both rest screens require the button click. Use
`python scripts/run_relaxing_news.py -h` to change these display and timing
values.

See [`relaxing_news_paradigm.md`](relaxing_news_paradigm.md) for the complete
news input, generation, playback, and replacement workflow.

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
