"""Fullscreen Pygame paradigms and neural sentence-audio tooling."""

import os


os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from .paradigms import (
    BaseParadigm,
    ListeningParadigm,
    LockedInSentenceReadingParadigm,
    ReadingParadigm,
    RelaxingNewsParadigm,
    SentenceParadigm,
)

__all__ = [
    "BaseParadigm",
    "SentenceParadigm",
    "LockedInSentenceReadingParadigm",
    "RelaxingNewsParadigm",
    "ReadingParadigm",
    "ListeningParadigm",
]
