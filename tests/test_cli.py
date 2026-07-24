import os
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from experiment_paradigm.cli import (
    parse_args as parse_sentence_args,
    parse_listening_args,
    parse_locked_in_args,
    parse_reading_args,
    parse_relaxing_news_args,
)
from experiment_paradigm.tts import parse_args as parse_tts_args
from experiment_paradigm.text_units import split_tts_units


class CommandLineDefaultsTests(unittest.TestCase):
    def test_all_paradigms_default_to_borderless_fullscreen(self):
        parsers = (
            parse_sentence_args,
            parse_locked_in_args,
            parse_reading_args,
            parse_listening_args,
            parse_relaxing_news_args,
        )

        for parser in parsers:
            with self.subTest(parser=parser.__name__):
                self.assertEqual(parser([]).display_mode, "borderless")

    def test_exclusive_fullscreen_can_be_selected(self):
        args = parse_locked_in_args(
            ["--display-mode", "exclusive"],
        )

        self.assertEqual(args.display_mode, "exclusive")

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

        self.assertEqual(
            args.sentences,
            Path("stimuli/yan_jiangyi_v4.txt"),
        )
        self.assertEqual(
            args.manifest,
            Path(
                "assets/sentence_audio/"
                "yan_jiangyi_v4_slow/manifest.json"
            ),
        )
        self.assertEqual(args.pre_audio_delay_min, 0.4)
        self.assertEqual(args.pre_audio_delay_max, 0.6)
        self.assertEqual(args.silent_delay_min, 1.5)
        self.assertEqual(args.silent_delay_max, 2.0)
        self.assertEqual(args.rest_min, 5.0)
        self.assertEqual(args.rest_max, 6.0)
        self.assertEqual(args.play_mode, "progress")
        self.assertEqual(args.progress_duration, 3.0)
        self.assertEqual(args.progress_pause, 0.5)
        self.assertEqual(args.cue_volume, 0.7)
        self.assertEqual(args.repetitions, 1)
        self.assertFalse(args.shuffle)
        self.assertFalse(args.show_rest_cross)

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
        self.assertIn("循环与顺序", help_text)
        self.assertIn("--repetitions", help_text)
        self.assertIn("--shuffle", help_text)
        self.assertIn("--show-rest-cross", help_text)
        self.assertIn("--cue-volume", help_text)
        self.assertIn("显示设置", help_text)
        self.assertIn("--display-mode", help_text)

    def test_locked_in_repetitions_and_shuffle_can_be_selected(self):
        args = parse_locked_in_args(["--repetitions", "4", "--shuffle"])

        self.assertEqual(args.repetitions, 4)
        self.assertTrue(args.shuffle)

    def test_locked_in_rest_cross_can_be_enabled(self):
        args = parse_locked_in_args(["--show-rest-cross"])

        self.assertTrue(args.show_rest_cross)

    def test_tts_help_is_described_and_grouped(self):
        output = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stdout(output):
            parse_tts_args(["--help"])

        help_text = output.getvalue()
        self.assertIn("输入与输出", help_text)
        self.assertIn("TTS 语音设置", help_text)
        self.assertIn("生成策略", help_text)
        self.assertIn("--force", help_text)
        self.assertIn("--tts-unit", help_text)

    def test_tts_auto_unit_splits_chinese_but_not_english(self):
        self.assertEqual(
            split_tts_units("手机。", "auto"),
            ("character", ["手", "机"]),
        )
        self.assertEqual(
            split_tts_units("mobile phone", "auto"),
            ("line", ["mobile phone"]),
        )


if __name__ == "__main__":
    unittest.main()
