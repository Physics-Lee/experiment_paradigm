"""Compatibility imports for command-line entry points.

Maintained parsers now live under :mod:`experiment_paradigm.commands`.
"""

from .commands import (
    main,
    main_listening,
    main_locked_in,
    main_reading,
    main_relaxing_news,
    main_zh,
    parse_args,
    parse_listening_args,
    parse_locked_in_args,
    parse_reading_args,
    parse_relaxing_news_args,
    positive_int,
)

__all__ = [
    "positive_int",
    "parse_args",
    "main",
    "parse_locked_in_args",
    "main_locked_in",
    "main_zh",
    "parse_relaxing_news_args",
    "main_relaxing_news",
    "parse_reading_args",
    "main_reading",
    "parse_listening_args",
    "main_listening",
]

if __name__ == "__main__":
    main()
