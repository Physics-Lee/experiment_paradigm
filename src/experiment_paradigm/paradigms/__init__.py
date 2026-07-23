"""Public paradigm classes, split by experiment type."""

import random

from ..core import BaseParadigm
from .listening import ListeningParadigm
from .locked_in_reading import LockedInSentenceReadingParadigm
from .reading import ReadingParadigm
from .relaxing_news import RelaxingNewsParadigm
from .sentence import SentenceParadigm

__all__ = [
    "BaseParadigm",
    "SentenceParadigm",
    "LockedInSentenceReadingParadigm",
    "ReadingParadigm",
    "ListeningParadigm",
    "RelaxingNewsParadigm",
]

