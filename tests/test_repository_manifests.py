import os
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from experiment_paradigm import SentenceParadigm


ROOT = Path(__file__).resolve().parents[1]


class RepositoryManifestTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_english_and_chinese_manifests_match_their_stimulus_lists(self):
        cases = (
            (
                "stimuli/sentences_en.txt",
                "assets/sentence_audio/en/manifest.json",
                3,
                "word",
            ),
            (
                "stimuli/sentences.txt",
                "assets/sentence_audio/zh/manifest.json",
                5,
                "character",
            ),
        )
        for sentences, manifest, expected_count, token_mode in cases:
            with self.subTest(manifest=manifest):
                paradigm = SentenceParadigm(
                    sentences_file=str(ROOT / sentences),
                    audio_manifest=str(ROOT / manifest),
                    token_mode=token_mode,
                )
                self.assertEqual(len(paradigm.sentences), expected_count)
                self.assertEqual(len(paradigm.sentence_audio), expected_count)
                self.assertTrue(paradigm.play_audio_before)
                self.assertTrue(paradigm.play_audio_after)
                pygame.quit()


if __name__ == "__main__":
    unittest.main()
