"""Command lines for Microsoft neural TTS asset generation."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from ..stimuli import read_news_items
from ..tts import (
    DEFAULT_VOICE,
    DetailedHelpFormatter,
    build_audio_set,
)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "为句子刺激文件逐行生成稳定的神经 TTS 音频，"
            "并建立文字—音频 manifest.json 对应清单。"
        ),
        formatter_class=DetailedHelpFormatter,
        epilog=(
            "时长说明:\n"
            "  --rate 只调整相对语速，不能保证精确的目标时长或"
            "每字时长。\n"
            "  负语速在 PowerShell 中请使用等号，例如 "
            "--rate=-50%。\n"
            "  若需精确到 3.0 秒/汉字，需要 TTS 后的保调时间"
            "拉伸工具；当前生成器未内置该处理。\n\n"
            "网络与复用规则:\n"
            "  生成阶段需要联网；范式播放阶段完全离线。\n"
            "  文字、TTS 设置和 SHA-256 全部匹配时会复用已有"
            "音频。\n"
            "  不匹配的已有文件不会被自动覆盖；审核后才"
            "使用 --force。\n\n"
            "查询可用语音:\n"
            "  edge-tts --list-voices\n\n"
            "中文生成示例:\n"
            "  python scripts/generate_sentence_audio.py --sentences "
            "stimuli/yan_jiangyi.txt --output-dir "
            "assets/sentence_audio/yan_jiangyi --voice "
            "zh-CN-XiaoxiaoNeural --rate=-50%\n\n"
            "实验运行参数（进度条、延迟、休息、提示音等）:\n"
            "  python scripts/run_sentence_audio_zh.py -h"
        ),
    )
    files = parser.add_argument_group("输入与输出")
    files.add_argument(
        "--sentences",
        type=Path,
        default=Path("stimuli/sentences_en.txt"),
        help=(
            "UTF-8 刺激文件；每个非空行是一个 trial，可生成"
            "一个或多个音频片段。"
        ),
    )
    files.add_argument(
        "--output-dir",
        type=Path,
        default=Path("assets/sentence_audio/en"),
        help="MP3 文件和 manifest.json 的输出目录。",
    )

    speech = parser.add_argument_group("TTS 语音设置")
    speech.add_argument(
        "--tts-unit",
        choices=("auto", "line", "character"),
        default="auto",
        help=(
            "auto=纯中文按汉字、其他文本按整行；line=始终按整行；"
            "character=始终按非空白/非标点字符。"
        ),
    )
    speech.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=(
            "Microsoft Edge TTS 语音名称；中文可使用 "
            "zh-CN-XiaoxiaoNeural。使用 edge-tts --list-voices "
            "查看全部可用语音。"
        ),
    )
    speech.add_argument(
        "--rate",
        default="+0%",
        help=(
            "相对语速，不是目标时长。例如 --rate=-50%% "
            "放慢、--rate=+20%% 加快。"
        ),
    )
    speech.add_argument(
        "--volume",
        default="+0%",
        help="TTS 合成音量的相对调整，例如 --volume=+20%%。",
    )
    speech.add_argument(
        "--pitch",
        default="+0Hz",
        help="TTS 合成音调的相对调整，例如 --pitch=-10Hz。",
    )

    generation = parser.add_argument_group("生成策略")
    generation.add_argument(
        "--force",
        action="store_true",
        help=(
            "强制重新生成并替换已有音频；仅在确认需要"
            "覆盖后使用。"
        ),
    )
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    manifest = asyncio.run(build_audio_set(args))
    segment_count = sum(
        len(item.get("segments", [item])) for item in manifest["items"]
    )
    print(
        f"Prepared {segment_count} audio segments for "
        f"{len(manifest['items'])} trials and wrote the manifest to "
        f"{args.output_dir.resolve()}"
    )


def parse_news_args(argv=None) -> argparse.Namespace:
    """Parse normal-speed Microsoft TTS options for relaxing news."""
    parser = argparse.ArgumentParser(
        description=(
            "从纯文本新闻或 Markdown 表格的“标题”列生成放松新闻范式音频。"
        ),
        formatter_class=DetailedHelpFormatter,
        epilog=(
            "说明:\n"
            "  每条新闻整句发送给 Microsoft Edge TTS，不进行逐字切分。\n"
            "  默认 +0% 为正常语速。生成需要联网，播放范式不需要联网。\n"
            "  Markdown 表格会自动跳过表头，并提取名称含“标题”的列。\n\n"
            "示例:\n"
            "  python scripts/generate_news_audio.py"
        ),
    )
    files = parser.add_argument_group("输入与输出")
    files.add_argument(
        "--news",
        dest="sentences",
        type=Path,
        default=Path("stimuli/news/2026_07_23.md"),
        help=(
            "UTF-8 新闻文件；支持每个非空行一条新闻，或包含“标题”列的 "
            "Markdown 表格。"
        ),
    )
    files.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "assets/news_audio/2026_07_23/zh-CN-YunyangNeural"
        ),
        help="新闻 MP3 文件和 manifest.json 的输出目录。",
    )

    speech = parser.add_argument_group("Microsoft AI 语音设置")
    speech.add_argument(
        "--voice",
        default="zh-CN-YunyangNeural",
        help="Microsoft Edge TTS 中文神经语音名称。",
    )
    speech.add_argument(
        "--rate",
        default="+0%",
        help="相对语速；+0%% 为正常语速。",
    )
    speech.add_argument(
        "--volume",
        default="+0%",
        help="相对音量，例如 --volume=+20%%。",
    )
    speech.add_argument(
        "--pitch",
        default="+0Hz",
        help="相对音调，例如 --pitch=-10Hz。",
    )
    generation = parser.add_argument_group("生成策略")
    generation.add_argument(
        "--force",
        action="store_true",
        help="审核后强制替换不匹配的已有音频。",
    )
    parser.set_defaults(tts_unit="line")
    return parser.parse_args(argv)


def main_news(argv=None) -> None:
    """Generate whole-news audio for the relaxation paradigm."""
    args = parse_news_args(argv)
    manifest = asyncio.run(
        build_audio_set(args, text_loader=read_news_items)
    )
    print(
        f"Prepared {len(manifest['items'])} news audio files and wrote "
        f"{args.output_dir.resolve() / 'manifest.json'}"
    )
