"""Launch the sentence paradigm with matching pre/post sentence audio."""

from __future__ import annotations

import argparse
from pathlib import Path

from .paradigms import (
    ListeningParadigm,
    LockedInSentenceReadingParadigm,
    ReadingParadigm,
    SentenceParadigm,
)


def parse_args(
    argv=None,
    *,
    default_sentences="stimuli/sentences_en.txt",
    default_manifest="assets/sentence_audio/en/manifest.json",
    default_output_prefix="sentence_audio",
    default_prep_mode="square",
    default_prep_time_jitter=0.3,
    default_token_mode="word",
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="运行通用句子范式，使用离线预加载的句子音频。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
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
    default_sentences="stimuli/sentences_en.txt",
    default_manifest="assets/sentence_audio/en/manifest.json",
    default_output_prefix="sentence_audio",
    default_prep_mode="square",
    default_prep_time_jitter=0.3,
    default_token_mode="word",
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
    )
    paradigm.run()


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
            "--sentences stimuli/yan_jiangyi.txt "
            "--manifest assets/sentence_audio/yan_jiangyi/manifest.json"
        ),
    )

    files = parser.add_argument_group("刺激、音频与输出")
    files.add_argument(
        "--sentences",
        type=Path,
        default=Path("stimuli/sentences.txt"),
        help="UTF-8 刺激文件；每个非空行是一个 trial。",
    )
    files.add_argument(
        "--manifest",
        type=Path,
        default=Path("assets/sentence_audio/zh/manifest.json"),
        help=(
            "与刺激文件逐行对应的 manifest.json；启动前会校验"
            "文字、顺序、音频文件和 SHA-256。"
        ),
    )
    files.add_argument(
        "--output-prefix",
        default="locked_in_sentence_reading",
        help="timestamp/ 下 CSV/JSON 结果文件的文件名前缀。",
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
        default=3.0,
        help="progress 模式中单个汉字进度条填满的时间（秒）。",
    )
    visual.add_argument(
        "--progress-pause",
        type=float,
        default=0.5,
        help="progress 模式中前一字填满后到下一字开始的停顿（秒）。",
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
        default=2.0,
        help="音频结束到方块变绿/视觉进度开始的随机延迟下限。",
    )
    timing.add_argument(
        "--silent-delay-max",
        type=float,
        default=3.0,
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
        help="trial 间大号灰色十字休息的随机下限。",
    )
    timing.add_argument(
        "--rest-max",
        type=float,
        default=6.0,
        help="trial 间大号灰色十字休息的随机上限。",
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
    paradigm = LockedInSentenceReadingParadigm(
        sentences_file=str(args.sentences),
        audio_manifest=str(args.manifest),
        char_speed=args.char_speed,
        play_mode=args.play_mode,
        progress_duration=args.progress_duration,
        progress_pause=args.progress_pause,
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
        output_prefix=args.output_prefix,
    )
    paradigm.run()


def parse_reading_args(argv=None) -> argparse.Namespace:
    """Parse the standalone word-reading command-line options."""
    parser = argparse.ArgumentParser(
        description="运行带时间戳的单词阅读范式。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
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
    )
    paradigm.run()


def parse_listening_args(argv=None) -> argparse.Namespace:
    """Parse the standalone listening command-line options."""
    parser = argparse.ArgumentParser(
        description="运行带时间戳的听力范式。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
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
    )
    paradigm.run()


def main_zh(argv=None) -> None:
    """Compatibility alias for the locked-in Chinese paradigm."""
    main_locked_in(argv)


if __name__ == "__main__":
    main()
