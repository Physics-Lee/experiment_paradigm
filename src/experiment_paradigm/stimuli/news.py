"""Load relaxing-news stimuli from plain text or a Markdown table."""

from __future__ import annotations

import re
from pathlib import Path


_MARKDOWN_SEPARATOR = re.compile(r"^:?-{3,}:?$")


def _markdown_cells(line: str) -> list[str]:
    """Return stripped cells from one pipe-delimited Markdown table row."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    """Return whether all cells form a Markdown alignment separator row."""
    return bool(cells) and all(
        _MARKDOWN_SEPARATOR.fullmatch(cell.replace(" ", ""))
        for cell in cells
    )


def read_news_items(path: Path) -> list[str]:
    """Read ordered news text from a Markdown title column or non-empty lines.

    A Markdown table is detected when its header contains a column whose name
    includes ``标题``. In that case only that column is returned, with table
    headers and separators omitted. Other files retain the ordinary one
    non-empty line per news item behavior.
    """
    lines = path.read_text(encoding="utf-8").splitlines()

    for header_index, line in enumerate(lines):
        cells = _markdown_cells(line)
        title_columns = [
            index for index, cell in enumerate(cells) if "标题" in cell
        ]
        if not title_columns:
            continue

        title_column = title_columns[0]
        items: list[str] = []
        for row in lines[header_index + 1 :]:
            row_cells = _markdown_cells(row)
            if not row_cells:
                if items:
                    break
                continue
            if _is_separator_row(row_cells):
                continue
            if title_column >= len(row_cells):
                continue
            title = row_cells[title_column].strip()
            if title:
                items.append(title)
        if items:
            return items

    return [line.strip() for line in lines if line.strip()]
