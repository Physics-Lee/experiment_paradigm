# Source Guidance

`experiment_paradigm/` is the maintained Python package.

- Keep public paradigm imports exported from `experiment_paradigm.__init__`.
- Keep experiment behavior in one module per experiment under `paradigms/`.
- Keep shared lifecycle, audio, display, timing, and result behavior under
  `core/`.
- Keep command-line parsing and defaults under `commands/`; `cli.py` is a
  compatibility re-export only.
- Keep stimulus parsing under `stimuli/` and online neural audio generation in
  `tts.py`.
- Console entry functions must accept an optional argument list so they remain
  directly testable without launching a subprocess.
- Do not import repository `scripts/` from package code. Dependency direction
  is always `scripts/` → `src/experiment_paradigm/`.
- Preserve timestamp field names and measure all configured durations in seconds.
- Sentence audio must be fully validated and preloaded before trial playback.
- Keep network TTS generation separate from offline experiment execution.
- Run the repository test suite and AST syntax check after source changes.
