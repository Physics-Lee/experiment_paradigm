"""Shared command-line parsers and validators."""

import argparse


DISPLAY_MODES = ("borderless", "exclusive")


def add_display_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the shared fullscreen-mode selector to an experiment parser."""
    display = parser.add_argument_group("显示设置")
    display.add_argument(
        "--display-mode",
        choices=DISPLAY_MODES,
        default="borderless",
        help=(
            "borderless=无边框桌面全屏且不切换系统分辨率；"
            "exclusive=pygame 独占全屏，可能切换系统显示模式。"
        ),
    )


def positive_int(value: str) -> int:
    """Parse a strictly positive integer for repeat counts."""
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed
