"""Command line for standalone word reading."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..paradigms import ReadingParadigm
from .common import add_display_arguments


def parse_reading_args(argv=None) -> argparse.Namespace:
    """Parse the standalone word-reading command-line options."""
    parser = argparse.ArgumentParser(
        description="运行带时间戳的单词阅读范式。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_display_arguments(parser)
    files = parser.add_argument_group("输入与输出")
    files.add_argument(
        "--words",
        type=Path,
        default=Path("stimuli/words_reading.txt"),
        help="UTF-8 单词文件；每个非空行是一个 trial。",
    )
    files.add_argument(
        "--output-prefix",
        default="reading",
        help="timestamp/ 下 CSV/JSON 结果文件的文件名前缀。",
    )

    timing = parser.add_argument_group("试次时序（全部为秒）")
    timing.add_argument(
        "--word-duration",
        type=float,
        default=0.2,
        help="单词在屏幕中央显示的时长。",
    )
    timing.add_argument(
        "--prep-time",
        type=float,
        default=1.5,
        help="红色准备方块的中心时长。",
    )
    timing.add_argument(
        "--prep-time-jitter",
        type=float,
        default=0.1,
        help="准备时长在 prep-time 两侧的均匀抖动半宽。",
    )
    timing.add_argument(
        "--word-jitter-mean",
        type=float,
        default=0.5,
        help="绿方块出现到单词出现的均匀延迟中心值。",
    )
    timing.add_argument(
        "--word-jitter-std",
        type=float,
        default=0.1,
        help="单词延迟在中心值两侧的均匀抖动半宽。",
    )
    timing.add_argument(
        "--inter-word-interval",
        type=float,
        default=2.0,
        help="相邻单词 trial 之间的间隔。",
    )
    return parser.parse_args(argv)


def main_reading(argv=None) -> None:
    """Run the standalone word-reading paradigm."""
    args = parse_reading_args(argv)
    paradigm = ReadingParadigm(
        words_file=str(args.words),
        word_duration=args.word_duration,
        prep_time=args.prep_time,
        prep_time_jitter=args.prep_time_jitter,
        word_jitter_mean=args.word_jitter_mean,
        word_jitter_std=args.word_jitter_std,
        inter_word_interval=args.inter_word_interval,
        output_prefix=args.output_prefix,
        display_mode=args.display_mode,
    )
    paradigm.run()
