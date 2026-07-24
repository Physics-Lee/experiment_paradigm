# Test Guidance

This directory contains non-interactive `unittest` coverage.

- Set SDL dummy video and audio drivers before importing Pygame.
- Use temporary files for mutation and never rewrite repository fixtures.
- Cover display modes, Chinese character mode, pronunciation aliases, news
  parsing/manual continuation, manifest validation, timestamp ordering, public
  compatibility imports, and legacy no-audio behavior.
- Run with `python -m unittest discover -s tests -v`.
