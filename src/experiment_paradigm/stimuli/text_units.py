"""Text segmentation rules shared by TTS generation and playback validation."""

from __future__ import annotations

import unicodedata


def is_cjk_character(character: str) -> bool:
    """Return whether one character belongs to a common CJK ideograph block."""
    codepoint = ord(character)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def character_units(text: str) -> list[str]:
    """Split text into spoken characters, excluding whitespace/punctuation."""
    return [
        character
        for character in text
        if not character.isspace()
        and not unicodedata.category(character).startswith("P")
    ]


def resolve_tts_unit(text: str, requested_unit: str) -> str:
    """Resolve auto mode to character only for all-CJK spoken content."""
    if requested_unit not in ("auto", "line", "character"):
        raise ValueError("tts_unit must be 'auto', 'line', or 'character'")
    if requested_unit != "auto":
        return requested_unit

    units = character_units(text)
    if units and all(is_cjk_character(character) for character in units):
        return "character"
    return "line"


def split_tts_units(text: str, requested_unit: str) -> tuple[str, list[str]]:
    """Return the resolved unit mode and ordered text sent to each TTS call."""
    resolved_unit = resolve_tts_unit(text, requested_unit)
    units = character_units(text) if resolved_unit == "character" else [text]
    if not units:
        raise ValueError(f"No speakable text units found in {text!r}")
    return resolved_unit, units
