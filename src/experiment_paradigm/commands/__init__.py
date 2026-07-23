"""Public command-line entry points grouped by paradigm."""

from .common import positive_int
from .listening import main_listening, parse_listening_args
from .locked_in_reading import (
    main_locked_in,
    main_zh,
    parse_locked_in_args,
)
from .reading import main_reading, parse_reading_args
from .relaxing_news import main_relaxing_news, parse_relaxing_news_args
from .sentence import main, parse_args

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

