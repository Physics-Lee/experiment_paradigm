"""Command line for standalone audio listening."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..paradigms import ListeningParadigm
from .common import add_display_arguments


def parse_listening_args(argv=None) -> argparse.Namespace:
    """Parse the standalone listening command-line options."""
    parser = argparse.ArgumentParser(
        description="运行带时间戳的听力范式。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_display_arguments(parser)
    files = parser.add_argument_group("输入与输出")
    files.add_argument(
        "--audio-dir",
        type=Path,
        default=Path("assets/listening_audio"),
        help="包含 MP3/WAV/OGG 刺激音频的目录。",
    )
    files.add_argument(
        "--output-prefix",
        default="listening",
        help="timestamp/ 下 CSV/JSON 结果文件的文件名前缀。",
    )

    timing = parser.add_argument_group("试次时序（全部为秒）")
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
        "--audio-jitter-mean",
        type=float,
        default=0.5,
        help="绿方块出现到音频开始的均匀延迟中心值。",
    )
    timing.add_argument(
        "--audio-jitter-std",
        type=float,
        default=0.1,
        help="音频延迟在中心值两侧的均匀抖动半宽。",
    )
    timing.add_argument(
        "--inter-audio-interval",
        type=float,
        default=2.0,
        help="相邻听力 trial 之间的间隔。",
    )

    playlist = parser.add_argument_group("播放列表")
    playlist.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="每个音频加入随机播放列表的次数。",
    )
    return parser.parse_args(argv)


def main_listening(argv=None) -> None:
    """Run the standalone listening paradigm."""
    args = parse_listening_args(argv)
    paradigm = ListeningParadigm(
        audios_folder=str(args.audio_dir),
        prep_time=args.prep_time,
        prep_time_jitter=args.prep_time_jitter,
        audio_jitter_mean=args.audio_jitter_mean,
        audio_jitter_std=args.audio_jitter_std,
        inter_audio_interval=args.inter_audio_interval,
        repetitions=args.repetitions,
        output_prefix=args.output_prefix,
        display_mode=args.display_mode,
    )
    paradigm.run()
