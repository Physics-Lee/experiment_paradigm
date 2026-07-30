"""Command line for the general sentence-audio paradigm."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..paradigms import SentenceParadigm
from .common import add_display_arguments


def parse_args(
    argv=None,
    *,
    default_sentences="stimuli/yan_jiangyi_v5.txt",
    default_manifest=(
        "assets/sentence_audio/yan_jiangyi_v5/"
        "zh-CN-YunxiaNeural/manifest.json"
    ),
    default_output_prefix="sentence_audio",
    default_prep_mode="square",
    default_prep_time_jitter=0.3,
    default_token_mode="character",
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="运行通用句子范式，使用离线预加载的句子音频。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_display_arguments(parser)
    files = parser.add_argument_group("刺激、音频与输出")
    files.add_argument(
        "--sentences",
        type=Path,
        default=Path(default_sentences),
        help="UTF-8 句子文件；每个非空行是一个 trial。",
    )
    files.add_argument(
        "--manifest",
        type=Path,
        default=Path(default_manifest),
        help="与句子文件的文字和顺序一致的音频 manifest.json。",
    )
    files.add_argument(
        "--output-prefix",
        default=default_output_prefix,
        help="timestamp/ 下 CSV/JSON 结果文件的文件名前缀。",
    )

    visual = parser.add_argument_group("文字分词与视觉提示")
    visual.add_argument(
        "--token-mode",
        choices=("word", "character"),
        default=default_token_mode,
        help="word=按空格分词；character=按字符分割。",
    )
    visual.add_argument(
        "--prep-mode",
        choices=("square", "dots"),
        default=default_prep_mode,
        help="视觉准备提示使用方块或逐渐减少的点。",
    )
    visual.add_argument(
        "--play-mode",
        choices=("green", "progress"),
        default="green",
        help="green=累积变绿；progress=背景进度条。",
    )
    visual.add_argument(
        "--char-speed",
        type=float,
        default=1.2,
        help="green 模式中相邻 token 变绿的间隔（秒）。",
    )
    visual.add_argument(
        "--dot-interval",
        type=float,
        default=0.6,
        help="dots 准备模式中每次减少点的间隔（秒）。",
    )
    visual.add_argument(
        "--progress-duration",
        type=float,
        default=1.2,
        help="progress 模式中单个 token 进度条填满的时间（秒）。",
    )
    visual.add_argument(
        "--progress-pause",
        type=float,
        default=0.5,
        help="progress 模式中相邻 token 进度条之间的停顿（秒）。",
    )

    timing = parser.add_argument_group("试次时序（全部为秒）")
    timing.add_argument(
        "--prep-time",
        type=float,
        default=1.5,
        help="准备阶段的中心时长。",
    )
    timing.add_argument(
        "--prep-time-jitter",
        type=float,
        default=default_prep_time_jitter,
        help="准备时长在 prep-time 两侧的均匀抖动半宽。",
    )
    timing.add_argument(
        "--jitter-mean",
        type=float,
        default=0.5,
        help="准备结束到文字动画开始的均匀延迟中心值。",
    )
    timing.add_argument(
        "--jitter-std",
        type=float,
        default=0.1,
        help="文字动画延迟在中心值两侧的均匀抖动半宽。",
    )
    timing.add_argument(
        "--inter-sentence-interval",
        type=float,
        default=2.0,
        help="相邻句子 trial 之间的间隔。",
    )

    audio = parser.add_argument_group("音频播放")
    audio.add_argument(
        "--pre-visual-gap",
        type=float,
        default=0.5,
        help="前置音频结束到视觉阶段开始的间隔（秒）。",
    )
    audio.add_argument(
        "--post-visual-gap",
        type=float,
        default=0.5,
        help="视觉阶段结束到后置音频开始的间隔（秒）。",
    )
    audio.add_argument(
        "--audio-screen",
        choices=("fixation", "black"),
        default="fixation",
        help="音频播放与音视间隔期间显示注视十字或纯黑屏。",
    )
    audio.add_argument(
        "--no-pre-audio",
        action="store_true",
        help="关闭视觉阶段之前的句子音频。",
    )
    audio.add_argument(
        "--no-post-audio",
        action="store_true",
        help="关闭视觉阶段之后的句子音频。",
    )
    return parser.parse_args(argv)


def main(
    argv=None,
    *,
    default_sentences="stimuli/yan_jiangyi_v5.txt",
    default_manifest=(
        "assets/sentence_audio/yan_jiangyi_v5/"
        "zh-CN-YunxiaNeural/manifest.json"
    ),
    default_output_prefix="sentence_audio",
    default_prep_mode="square",
    default_prep_time_jitter=0.3,
    default_token_mode="character",
) -> None:
    args = parse_args(
        argv,
        default_sentences=default_sentences,
        default_manifest=default_manifest,
        default_output_prefix=default_output_prefix,
        default_prep_mode=default_prep_mode,
        default_prep_time_jitter=default_prep_time_jitter,
        default_token_mode=default_token_mode,
    )
    paradigm = SentenceParadigm(
        sentences_file=str(args.sentences),
        char_speed=args.char_speed,
        prep_time=args.prep_time,
        prep_time_jitter=args.prep_time_jitter,
        jitter_mean=args.jitter_mean,
        jitter_std=args.jitter_std,
        dot_interval=args.dot_interval,
        prep_mode=args.prep_mode,
        play_mode=args.play_mode,
        progress_duration=args.progress_duration,
        progress_pause=args.progress_pause,
        inter_sentence_interval=args.inter_sentence_interval,
        output_prefix=args.output_prefix,
        audio_manifest=str(args.manifest),
        play_audio_before=not args.no_pre_audio,
        play_audio_after=not args.no_post_audio,
        pre_visual_gap=args.pre_visual_gap,
        post_visual_gap=args.post_visual_gap,
        audio_screen=args.audio_screen,
        token_mode=args.token_mode,
        display_mode=args.display_mode,
    )
    paradigm.run()
