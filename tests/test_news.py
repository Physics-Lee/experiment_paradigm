import hashlib
import json
import os
import tempfile
import unittest
import wave
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from experiment_paradigm.cli import parse_relaxing_news_args
from experiment_paradigm.news import read_news_items
from experiment_paradigm.paradigms import RelaxingNewsParadigm
from experiment_paradigm.tts import parse_news_args


def write_silent_wav(path: Path, duration_seconds: float = 0.02) -> None:
    sample_rate = 8000
    frame_count = round(sample_rate * duration_seconds)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frame_count)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NewsStimulusTests(unittest.TestCase):
    def test_markdown_table_extracts_only_news_title_column(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "news.md"
            path.write_text(
                "| # | 来源分类 | Top 1 标题（中文） | 评分 |\n"
                "|---|---|---|---|\n"
                "| 1 | 科技 | 第一条新闻。 | — |\n"
                "| 2 | 科学 | 第二条新闻。 | 42 |\n",
                encoding="utf-8",
            )

            self.assertEqual(
                read_news_items(path),
                ["第一条新闻。", "第二条新闻。"],
            )

    def test_plain_text_retains_one_nonempty_line_per_news_item(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "news.txt"
            path.write_text("第一条\n\n第二条\n", encoding="utf-8")

            self.assertEqual(read_news_items(path), ["第一条", "第二条"])

    def test_relaxing_news_cli_defaults_are_patient_friendly(self):
        args = parse_relaxing_news_args([])

        self.assertEqual(args.font_size, 40)
        self.assertEqual(args.square_size, 100)
        self.assertEqual(args.pre_audio_delay, 0.5)
        self.assertEqual(args.post_audio_hold, 1.0)
        self.assertEqual(args.rest_min, 5.0)
        self.assertEqual(args.rest_max, 6.0)

    def test_news_tts_defaults_to_whole_line_normal_speed(self):
        args = parse_news_args([])

        self.assertEqual(args.tts_unit, "line")
        self.assertEqual(args.voice, "zh-CN-XiaoxiaoNeural")
        self.assertEqual(args.rate, "+0%")

    def test_news_screen_keeps_small_square_red_and_rest_cross_gray(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            news_path = root / "news.txt"
            news_path.write_text("用于测试的新闻文字。\n", encoding="utf-8")
            audio_path = root / "news.wav"
            write_silent_wav(audio_path)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "complete": True,
                        "items": [
                            {
                                "id": "sentence_001",
                                "index": 1,
                                "text": "用于测试的新闻文字。",
                                "file": audio_path.name,
                                "sha256": sha256_file(audio_path),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            paradigm = RelaxingNewsParadigm(
                news_file=str(news_path),
                audio_manifest=str(manifest_path),
                font_size=40,
                square_size=100,
            )
            try:
                layout = paradigm._news_layout("用于测试的新闻文字。")
                paradigm._draw_news_state(layout)

                self.assertEqual(layout["square_size"], 100)
                self.assertEqual(
                    paradigm.screen.get_at(layout["square_rect"].center)[:3],
                    paradigm.RED,
                )

                paradigm._draw_rest_screen()
                screen_center = (
                    paradigm.width // 2,
                    paradigm.height // 2,
                )
                self.assertEqual(
                    paradigm.screen.get_at(screen_center)[:3],
                    paradigm.GRAY,
                )
            finally:
                paradigm.cleanup()


if __name__ == "__main__":
    unittest.main()
