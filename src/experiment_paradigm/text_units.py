"""Compatibility imports for relocated text-unit helpers."""

from .stimuli.text_units import (
    character_units,
    is_cjk_character,
    resolve_tts_unit,
    split_tts_units,
)

__all__ = [
    "character_units",
    "is_cjk_character",
    "resolve_tts_unit",
    "split_tts_units",
]
