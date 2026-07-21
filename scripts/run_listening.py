"""Compatibility entry point for the listening paradigm."""

from pathlib import Path
import sys


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from experiment_paradigm.cli import main_listening


if __name__ == "__main__":
    main_listening()
