"""Command line for the speech + movement synchronization paradigm."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from paradigm import SpeechMotorSyncParadigm


SCRIPT_DIR = Path(__file__).resolve().parent
DISPLAY_MODES = ("borderless", "exclusive")


def positive_int(value: str) -> int:
    """Parse a strictly positive integer for repeat counts."""
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def parse_args(argv=None) -> argparse.Namespace:
    """Parse the speech + movement synchronization command-line options."""
    parser = argparse.ArgumentParser(
        description=(
            "运行「说话与运动同步」范式：左侧汉字 + 右侧手势图同时呈现，"
            "底部红→绿长方形作为 go cue，受试者在变绿时同步说出该数字并做手势。"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "示例: python run.py --repetitions 3\n"
            "      python run.py --no-cue-tone --progress-duration 2.5"
        ),
    )

    display = parser.add_argument_group("显示设置")
    display.add_argument(
        "--display-mode",
        choices=DISPLAY_MODES,
        default="borderless",
        help=(
            "borderless=无边框桌面全屏且不切换系统分辨率；"
            "exclusive=pygame 独占全屏，可能切换系统显示模式。"
        ),
    )

    files = parser.add_argument_group("刺激、手势与输出")
    files.add_argument(
        "--stimuli",
        type=Path,
        default=SCRIPT_DIR / "stimuli.txt",
        help="UTF-8 刺激文件；每个非空行是一个数字刺激，第 i 行对应 gestures/0i.png。",
    )
    files.add_argument(
        "--gestures-dir",
        type=Path,
        default=SCRIPT_DIR / "gestures",
        help="手势图片目录；按 01.png..10.png 与刺激行一一对应。",
    )
    files.add_argument(
        "--audio-dir",
        type=Path,
        default=SCRIPT_DIR / "audio" / "normal",
        help=(
            "数字音频目录（与闭锁范式同款 zh-CN-YunxiaNeural TTS）；"
            "默认 audio/normal（正常语速）。要慢速用 audio/slow（-50%%）。"
        ),
    )
    files.add_argument(
        "--no-audio",
        dest="audio",
        action="store_false",
        default=True,
        help="关闭数字音频播放（仅视觉），跳过音频相关阶段。",
    )
    files.add_argument(
        "--output-prefix",
        default="speech_motor_sync",
        help="timestamp/ 下 CSV/JSON 结果文件的文件名前缀。",
    )
    files.add_argument(
        "--output-dir",
        type=Path,
        default=SCRIPT_DIR / "timestamp",
        help="结果 CSV/JSON 的输出目录。",
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

    visual = parser.add_argument_group("视觉与提示")
    visual.add_argument(
        "--font-size",
        type=int,
        default=300,
        help="左侧汉字字号上限；单字会在此上限与左半区空间内自适应放大。",
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
    continue_button_options = visual.add_mutually_exclusive_group()
    continue_button_options.add_argument(
        "--continue-button",
        dest="continue_button",
        action="store_true",
        default=True,
        help="trial 间休息达到最短时长后显示“下一条/结束”按钮，点击才继续；默认开启。",
    )
    continue_button_options.add_argument(
        "--no-continue-button",
        dest="continue_button",
        action="store_false",
        default=argparse.SUPPRESS,
        help="关闭“下一条”按钮，回到定时休息屏（休息到点自动继续）。",
    )
    countdown_options = visual.add_mutually_exclusive_group()
    countdown_options.add_argument(
        "--show-continue-countdown",
        dest="show_continue_countdown",
        action="store_true",
        default=True,
        help="在“下一条/结束”按钮上方显示剩余休息秒数倒计时；默认开启。",
    )
    countdown_options.add_argument(
        "--hide-continue-countdown",
        dest="show_continue_countdown",
        action="store_false",
        default=argparse.SUPPRESS,
        help="隐藏“下一条/结束”按钮上方的倒计时。",
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
        help="汉字+手势+红条出现到音频开始的随机延迟下限。",
    )
    timing.add_argument(
        "--pre-audio-delay-max",
        type=float,
        default=0.6,
        help="汉字+手势+红条出现到音频开始的随机延迟上限。",
    )
    timing.add_argument(
        "--silent-delay-min",
        type=float,
        default=1.5,
        help="音频结束到 go cue（条变绿/进度条开始）的随机延迟下限。",
    )
    timing.add_argument(
        "--silent-delay-max",
        type=float,
        default=2.0,
        help="音频结束到 go cue（条变绿/进度条开始）的随机延迟上限。",
    )
    timing.add_argument(
        "--progress-duration",
        type=float,
        default=1.2,
        help="go cue 变绿后，数字背后的浅棕色进度条填满的时长（即说话/动作反应窗）。",
    )
    timing.add_argument(
        "--final-hold",
        type=float,
        default=0.5,
        help="进度条填满后保持终末画面（绿条+满进度条）的时长，之后才进入十字休息屏。",
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
        help="关闭与 go cue（条变绿）同步的统一“滴”声。",
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


def main(argv=None) -> None:
    """Run the speech + movement synchronization paradigm."""
    args = parse_args(argv)
    paradigm = SpeechMotorSyncParadigm(
        stimuli_file=str(args.stimuli),
        gestures_dir=str(args.gestures_dir),
        audio=args.audio,
        audio_dir=str(args.audio_dir),
        baseline_min=args.baseline_min,
        baseline_max=args.baseline_max,
        pre_audio_delay_min=args.pre_audio_delay_min,
        pre_audio_delay_max=args.pre_audio_delay_max,
        silent_delay_min=args.silent_delay_min,
        silent_delay_max=args.silent_delay_max,
        progress_duration=args.progress_duration,
        final_hold=args.final_hold,
        rest_min=args.rest_min,
        rest_max=args.rest_max,
        rest_cross=args.show_rest_cross,
        cue_tone=not args.no_cue_tone,
        cue_frequency=args.cue_frequency,
        cue_duration=args.cue_duration,
        cue_volume=args.cue_volume,
        repetitions=args.repetitions,
        shuffle=args.shuffle,
        continue_button=args.continue_button,
        show_continue_countdown=args.show_continue_countdown,
        font_size=args.font_size,
        output_prefix=args.output_prefix,
        output_dir=args.output_dir,
        display_mode=args.display_mode,
    )
    paradigm.run()


if __name__ == "__main__":
    main(sys.argv[1:])
