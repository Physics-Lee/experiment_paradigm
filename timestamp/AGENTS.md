# Timestamp Data Guidance

This directory contains CSV and JSON experiment results written by
`BaseParadigm.save_data()` in
`src/experiment_paradigm/core/base.py`, using the writers in
`src/experiment_paradigm/core/results.py`.

- Existing tracked 2025 files are historical repository fixtures. Preserve them
  unless a data-retention change is explicitly requested.
- New timestamped CSV/JSON files are generated run output and are ignored by
  default. Add one deliberately only when it is meant to become a stable
  example or test fixture.
- CSV and JSON counterparts with the same prefix and datetime represent the
  same run; keep pairs together.
- Do not hand-edit timing measurements. If transformation is needed, write a
  reproducible script and retain the original data.
- Treat absolute timestamps as potentially sensitive participant/session
  metadata and inspect results before sharing.
