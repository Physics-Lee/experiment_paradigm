# Test Guidance

This directory contains non-interactive `unittest` coverage.

- Set SDL dummy video and audio drivers before importing Pygame.
- Use temporary files for mutation and never rewrite repository fixtures.
- Cover English word mode, Chinese character mode, manifest validation, timestamp
  ordering, and legacy no-audio behavior.
- Run with `python -m unittest discover -s tests -v`.
