"""Reusable fonts and simple visual primitives."""

from __future__ import annotations

import pygame


CJK_FONT_PATHS = (
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)


def load_cjk_font(
    font_size: int,
    *,
    announce: bool = True,
) -> pygame.font.Font:
    """Load a CJK-capable font, falling back to Pygame's default."""
    for font_path in CJK_FONT_PATHS:
        try:
            font = pygame.font.Font(font_path, font_size)
            if announce:
                print(f"Successfully loaded font: {font_path}")
            return font
        except (FileNotFoundError, OSError, pygame.error):
            continue
    if announce:
        print("Warning: Could not load system font. Using default font.")
    return pygame.font.Font(None, font_size)


def draw_square(
    screen: pygame.Surface,
    color: tuple[int, int, int],
    *,
    center: tuple[int, int],
    size: int,
) -> pygame.Rect:
    """Draw and return a square centered on the requested point."""
    rect = pygame.Rect(0, 0, size, size)
    rect.center = center
    pygame.draw.rect(screen, color, rect)
    return rect


def draw_cross(
    screen: pygame.Surface,
    color: tuple[int, int, int],
    *,
    center: tuple[int, int],
    arm_length: int,
    thickness: int,
) -> None:
    """Draw a centered rectangular fixation cross."""
    center_x, center_y = center
    pygame.draw.rect(
        screen,
        color,
        (
            center_x - arm_length,
            center_y - thickness // 2,
            arm_length * 2,
            thickness,
        ),
    )
    pygame.draw.rect(
        screen,
        color,
        (
            center_x - thickness // 2,
            center_y - arm_length,
            thickness,
            arm_length * 2,
        ),
    )
