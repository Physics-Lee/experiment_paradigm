"""Command line for locked-in patient sentence reading."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..paradigms import LockedInSentenceReadingParadigm
from .common import add_display_arguments, positive_int


DEFAULT_LOCKED_IN_AUDIO_DIR = Path(
    "assets/sentence_audio/yan_jiangyi_v5/zh-CN-YunxiaNeural"
)


def resolve_locked_in_manifest(args: argparse.Namespace) -> Path:
    """Resolve either an audio-set directory or a direct manifest override."""
    if args.manifest is not None:
        return args.manifest
    return args.audio_dir / "manifest.json"


def parse_locked_in_args(argv=None) -> argparse.Namespace:
    """Parse the locked-in sentence-reading command-line options."""
    parser = argparse.ArgumentParser(
        description=(
            "运行闭锁患者中文句子朗读范式：白字/红方块先出现，"
            "延迟后播放预加载目标音频，音频后再启动视觉进度。"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "示例: python scripts/run_sentence_audio_zh.py "
            "--repetitions 3"
        ),
    )
    add_display_arguments(parser)

    files = parser.add_argument_group("刺激、音频与输出")
    files.add_argument(
        "--sentences",
        type=Path,
        default=Path("stimuli/yan_jiangyi_v5.txt"),
        help="UTF-8 刺激文件；每个非空行是一个 trial。",
    )
    audio_input = files.add_mutually_exclusive_group()
    audio_input.add_argument(
        "--audio-dir",
        type=Path,
        default=DEFAULT_LOCKED_IN_AUDIO_DIR,
        help=(
            "任务音频集目录；目录内必须包含 manifest.json 和其引用的 "
            "MP3。切换语音时优先使用此参数。"
        ),
    )
    audio_input.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=(
            "直接指定 manifest.json，供旧目录或特殊音频集兼容使用；"
            "不能与 --audio-dir 同时使用。"
        ),
    )
    files.add_argument(
        "--output-prefix",
        default="locked_in_sentence_reading",
        help="timestamp/ 下 CSV/JSON 结果文件的文件名前缀。",
    )

    order = parser.add_argument_group("循环与顺序")
    order.add_argument(
        "--repetitions",
        type=positive_int,
        default=1,
        help="完整刺激列表的循环次数；每轮中的每个刺激呈现一次。",
    )
    shuffle_options = order.add_mutually_exclusive_group()
    shuffle_options.add_argument(
        "--shuffle",
        dest="shuffle",
        action="store_true",
        default=True,
        help="每轮开始前独立随机打乱刺激顺序；默认开启。",
    )
    shuffle_options.add_argument(
        "--no-shuffle",
        dest="shuffle",
        action="store_false",
        default=argparse.SUPPRESS,
        help="关闭随机打乱，每轮都按刺激文件中的顺序呈现。",
    )

    visual = parser.add_argument_group("视觉提示与速度")
    visual.add_argument(
        "--play-mode",
        choices=("green", "progress"),
        default="progress",
        help="progress=逐字背景进度条；green=汉字累积变绿。",
    )
    visual.add_argument(
        "--char-speed",
        type=float,
        default=1.2,
        help="green 模式中相邻汉字变绿的间隔（秒/字）。",
    )
    visual.add_argument(
        "--progress-duration",
        type=float,
        default=2.0,
        help="progress 模式中单个汉字进度条填满的时间（秒）。",
    )
    visual.add_argument(
        "--progress-pause",
        type=float,
        default=0.5,
        help="progress 模式中前一字填满后到下一字开始的停顿（秒）。",
    )
    rest_cross_options = visual.add_mutually_exclusive_group()
    rest_cross_options.add_argument(
        "--show-rest-cross",
        dest="show_rest_cross",
        action="store_true",
        default=True,
        help="trial 间休息时在黑屏中央显示灰色十字；默认开启。",
    )
    rest_cross_options.add_argument(
        "--no-rest-cross",
        dest="show_rest_cross",
        action="store_false",
        default=argparse.SUPPRESS,
        help="关闭灰色十字，trial 间休息时使用纯黑屏。",
    )

    timing = parser.add_argument_group("试次时序（全部为秒）")
    timing.add_argument(
        "--baseline-min",
        type=float,
        default=1.5,
        help="实验开始、第一个 trial 前黑屏静息基线的随机下限。",
    )
    timing.add_argument(
        "--baseline-max",
        type=float,
        default=2.5,
        help="实验开始、第一个 trial 前黑屏静息基线的随机上限。",
    )
    timing.add_argument(
        "--pre-audio-delay-min",
        type=float,
        default=0.4,
        help="白字/红方块出现到音频开始的随机延迟下限。",
    )
    timing.add_argument(
        "--pre-audio-delay-max",
        type=float,
        default=0.6,
        help="白字/红方块出现到音频开始的随机延迟上限。",
    )
    timing.add_argument(
        "--silent-delay-min",
        type=float,
        default=1.5,
        help="音频结束到方块变绿/视觉进度开始的随机延迟下限。",
    )
    timing.add_argument(
        "--silent-delay-max",
        type=float,
        default=2.0,
        help="音频结束到方块变绿/视觉进度开始的随机延迟上限。",
    )
    timing.add_argument(
        "--final-hold",
        type=float,
        default=0.5,
        help="最后一字完成后保持最终画面的时间。",
    )
    timing.add_argument(
        "--rest-min",
        type=float,
        default=5.0,
        help="trial 间休息时长的随机下限。",
    )
    timing.add_argument(
        "--rest-max",
        type=float,
        default=6.0,
        help="trial 间休息时长的随机上限。",
    )

    cue = parser.add_argument_group("统一提示音")
    cue.add_argument(
        "--no-cue-tone",
        action="store_true",
        help="关闭与绿方块/第一字同步的统一“滴”声。",
    )
    cue.add_argument(
        "--cue-frequency",
        type=int,
        default=1000,
        help="统一提示音的频率（Hz）。",
    )
    cue.add_argument(
        "--cue-duration",
        type=float,
        default=0.08,
        help="统一提示音的时长（秒）。",
    )
    cue.add_argument(
        "--cue-volume",
        type=float,
        default=0.7,
        help="统一提示音的音量，取值范围 (0, 1]。",
    )
    return parser.parse_args(argv)


def main_locked_in(argv=None) -> None:
    """Run the locked-in Chinese sentence-reading paradigm."""
    args = parse_locked_in_args(argv)
    audio_manifest = resolve_locked_in_manifest(args)
    paradigm = LockedInSentenceReadingParadigm(
        sentences_file=str(args.sentences),
        audio_manifest=str(audio_manifest),
        char_speed=args.char_speed,
        play_mode=args.play_mode,
        progress_duration=args.progress_duration,
        progress_pause=args.progress_pause,
        rest_cross=args.show_rest_cross,
        baseline_min=args.baseline_min,
        baseline_max=args.baseline_max,
        pre_audio_delay_min=args.pre_audio_delay_min,
        pre_audio_delay_max=args.pre_audio_delay_max,
        silent_delay_min=args.silent_delay_min,
        silent_delay_max=args.silent_delay_max,
        final_hold=args.final_hold,
        rest_min=args.rest_min,
        rest_max=args.rest_max,
        cue_tone=not args.no_cue_tone,
        cue_frequency=args.cue_frequency,
        cue_duration=args.cue_duration,
        cue_volume=args.cue_volume,
        repetitions=args.repetitions,
        shuffle=args.shuffle,
        output_prefix=args.output_prefix,
        display_mode=args.display_mode,
    )
    paradigm.run()


def main_zh(argv=None) -> None:
    """Compatibility alias for the locked-in Chinese paradigm."""
    main_locked_in(argv)
