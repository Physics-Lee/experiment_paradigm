# Script Guidance

This directory contains compatibility entry points for repository-root workflows.

- Maintained implementations belong in `src/experiment_paradigm/`; scripts here
  should remain thin wrappers that bootstrap `src/`, import one package
  entry-point function, and call it under `if __name__ == "__main__"`.
- Do not define experiment defaults, instantiate paradigm classes, validate
  inputs, or re-export package APIs here.
- Resolve `src/` relative to the repository root so scripts work without relying
  on the caller's current `PYTHONPATH`.
- Prefer the installed console commands documented in `docs/readme.md`.
