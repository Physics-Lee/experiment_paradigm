import os
import unittest
from unittest.mock import Mock, patch


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from experiment_paradigm.core import BaseParadigm


class DisplayModeTests(unittest.TestCase):
    def _build_with_mocked_display(self, display_mode):
        screen = Mock()
        screen.get_size.return_value = (1920, 1080)
        patches = (
            patch(
                "experiment_paradigm.core.base.pygame.display"
                ".get_desktop_sizes",
                return_value=[(1920, 1080)],
            ),
            patch(
                "experiment_paradigm.core.base.pygame.display.set_mode",
                return_value=screen,
            ),
            patch(
                "experiment_paradigm.core.base.pygame.display.set_caption",
            ),
            patch.object(
                BaseParadigm,
                "_load_font",
                return_value=Mock(),
            ),
        )
        with patches[0], patches[1] as set_mode, patches[2], patches[3]:
            paradigm = BaseParadigm(display_mode=display_mode)
        return paradigm, set_mode

    def test_borderless_mode_uses_desktop_size_without_exclusive_flag(self):
        paradigm, set_mode = self._build_with_mocked_display("borderless")

        set_mode.assert_called_once_with((1920, 1080), pygame.NOFRAME)
        self.assertEqual(paradigm.display_mode, "borderless")

    def test_exclusive_mode_retains_the_original_pygame_fullscreen_call(self):
        paradigm, set_mode = self._build_with_mocked_display("exclusive")

        set_mode.assert_called_once_with((0, 0), pygame.FULLSCREEN)
        self.assertEqual(paradigm.display_mode, "exclusive")

    def test_unknown_display_mode_is_rejected_before_pygame_starts(self):
        with patch(
            "experiment_paradigm.core.base.pygame.init",
        ) as pygame_init:
            with self.assertRaisesRegex(ValueError, "display_mode"):
                BaseParadigm(display_mode="unknown")

        pygame_init.assert_not_called()


if __name__ == "__main__":
    unittest.main()
