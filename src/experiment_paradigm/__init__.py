"""Fullscreen Pygame paradigms and neural sentence-audio tooling."""

from .paradigms import (
    BaseParadigm,
    ListeningParadigm,
    LockedInSentenceReadingParadigm,
    ReadingParadigm,
    SentenceParadigm,
)

__all__ = [
    "BaseParadigm",
    "SentenceParadigm",
    "LockedInSentenceReadingParadigm",
    "ReadingParadigm",
    "ListeningParadigm",
]
