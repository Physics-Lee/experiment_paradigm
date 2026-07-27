import os
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from experiment_paradigm import (
    LockedInSentenceReadingParadigm,
    RelaxingNewsParadigm,
)


ROOT = Path(__file__).resolve().parents[1]


class RepositoryManifestTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_primary_patient_manifests_match_their_stimulus_lists(self):
        locked_in = LockedInSentenceReadingParadigm(
            sentences_file=str(ROOT / "stimuli/yan_jiangyi_v4.txt"),
            audio_manifest=str(
                ROOT
                / "assets/sentence_audio/yan_jiangyi_v4/"
                "zh-CN-YunxiaNeural/manifest.json"
            ),
            cue_tone=False,
        )
        self.assertEqual(len(locked_in.sentences), 5)
        self.assertEqual(len(locked_in.sentence_audio), 5)
        pygame.quit()

        relaxing_news = RelaxingNewsParadigm(
            news_file=str(ROOT / "stimuli/news/2026_07_23.md"),
            audio_manifest=str(
                ROOT
                / "assets/news_audio/2026_07_23/"
                "zh-CN-YunyangNeural/manifest.json"
            ),
        )
        self.assertEqual(len(relaxing_news.sentences), 6)
        self.assertEqual(len(relaxing_news.sentence_audio), 6)


if __name__ == "__main__":
    unittest.main()
