import os
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from experiment_paradigm.cli import (
    parse_listening_args,
    parse_locked_in_args,
    parse_reading_args,
)
from experiment_paradigm.tts import parse_args as parse_tts_args


class CommandLineDefaultsTests(unittest.TestCase):
    def test_reading_defaults_live_in_package_cli(self):
        args = parse_reading_args([])

        self.assertEqual(args.words, Path("stimuli/words_reading.txt"))
        self.assertEqual(args.word_duration, 0.2)
        self.assertEqual(args.output_prefix, "reading")

    def test_listening_defaults_live_in_package_cli(self):
        args = parse_listening_args([])

        self.assertEqual(args.audio_dir, Path("assets/listening_audio"))
        self.assertEqual(args.repetitions, 3)
        self.assertEqual(args.output_prefix, "listening")

    def test_locked_in_defaults_live_in_package_cli(self):
        args = parse_locked_in_args([])

        self.assertEqual(args.sentences, Path("stimuli/sentences.txt"))
        self.assertEqual(args.pre_audio_delay_min, 0.4)
        self.assertEqual(args.pre_audio_delay_max, 0.6)
        self.assertEqual(args.silent_delay_min, 2.0)
        self.assertEqual(args.silent_delay_max, 3.0)
        self.assertEqual(args.rest_min, 5.0)
        self.assertEqual(args.rest_max, 6.0)
        self.assertEqual(args.play_mode, "progress")
        self.assertEqual(args.progress_duration, 3.0)
        self.assertEqual(args.progress_pause, 0.5)
        self.assertEqual(args.cue_volume, 0.7)

    def test_locked_in_progress_mode_can_be_selected(self):
        args = parse_locked_in_args(["--play-mode", "progress"])

        self.assertEqual(args.play_mode, "progress")

    def test_locked_in_help_is_described_and_grouped(self):
        output = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stdout(output):
            parse_locked_in_args(["--help"])

        help_text = output.getvalue()
        self.assertIn("刺激、音频与输出", help_text)
        self.assertIn("视觉提示与速度", help_text)
        self.assertIn("试次时序", help_text)
        self.assertIn("统一提示音", help_text)
        self.assertIn("--cue-volume", help_text)

    def test_tts_help_is_described_and_grouped(self):
        output = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stdout(output):
            parse_tts_args(["--help"])

        help_text = output.getvalue()
        self.assertIn("输入与输出", help_text)
        self.assertIn("TTS 语音设置", help_text)
        self.assertIn("生成策略", help_text)
        self.assertIn("--force", help_text)


if __name__ == "__main__":
    unittest.main()
