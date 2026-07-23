"""Shared validation and interruptible display timing."""

from __future__ import annotations

from collections.abc import Callable

import pygame


def validate_duration_range(name: str, minimum: float, maximum: float) -> None:
    """Validate a non-negative inclusive duration range."""
    if minimum < 0 or maximum < 0:
        raise ValueError(f"{name} durations must be non-negative")
    if minimum > maximum:
        raise ValueError(f"{name} minimum must not be greater than maximum")


def show_for_duration(
    *,
    duration: float,
    now: Callable[[], float],
    draw_frame: Callable[[], None],
    check_exit: Callable[[], bool],
    clock: pygame.time.Clock,
) -> tuple[bool, float]:
    """Draw a stable phase for a duration while remaining interruptible."""
    started_at = now()
    draw_frame()
    pygame.display.flip()
    while now() - started_at < duration:
        if not check_exit():
            return False, now() - started_at
        draw_frame()
        pygame.display.flip()
        clock.tick(60)
    return True, now() - started_at
