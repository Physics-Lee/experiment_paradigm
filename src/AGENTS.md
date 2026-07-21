# Source Guidance

`experiment_paradigm/` is the maintained Python package.

- Keep public paradigm imports exported from `experiment_paradigm.__init__`.
- Keep experiment behavior and reusable classes in `paradigms.py`, offline
  command-line parsing and defaults in `cli.py`, and online neural audio
  generation in `tts.py`.
- Console entry functions must accept an optional argument list so they remain
  directly testable without launching a subprocess.
- Do not import repository `scripts/` from package code. Dependency direction
  is always `scripts/` → `src/experiment_paradigm/`.
- Preserve timestamp field names and measure all configured durations in seconds.
- Sentence audio must be fully validated and preloaded before trial playback.
- Keep network TTS generation separate from offline experiment execution.
- Run the repository test suite and AST syntax check after source changes.
