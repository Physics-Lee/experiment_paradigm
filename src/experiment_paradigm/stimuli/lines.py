"""Plain UTF-8 line-oriented stimulus loading."""

from __future__ import annotations

from pathlib import Path


def read_nonempty_lines(path: Path) -> list[str]:
    """Return stripped non-empty UTF-8 lines without changing their order."""
    with path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]
