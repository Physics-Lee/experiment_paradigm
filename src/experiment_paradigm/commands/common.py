"""Shared command-line parsers and validators."""

import argparse


def positive_int(value: str) -> int:
    """Parse a strictly positive integer for repeat counts."""
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed

