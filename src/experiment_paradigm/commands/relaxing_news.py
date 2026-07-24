"""Command line for passive relaxing-news playback."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..paradigms import RelaxingNewsParadigm
from .common import add_display_arguments


def parse_relaxing_news_args(argv=None) -> argparse.Namespace:
    """Parse the patient relaxation news-paradigm options."""
    parser = argparse.ArgumentParser(
        description=(
            "运行患者放松新闻范式：显示较小白字和小红方块，"
            "以正常语速朗读新闻，休息结束后点击按钮进入下一条。"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "请先运行 python scripts/generate_news_audio.py 生成音频；"
            "正式播放全程使用本地音频，不需要联网。"
        ),
    )
    add_display_arguments(parser)
    files = parser.add_argument_group("新闻、音频与输出")
    files.add_argument(
        "--news",
        type=Path,
        default=Path("stimuli/news/2026_07_23.md"),
        help=(
            "UTF-8 新闻文件；支持每个非空行一条新闻，或包含“标题”列的 "
            "Markdown 表格。"
        ),
    )
    files.add_argument(
        "--manifest",
        type=Path,
        default=Path("assets/news_audio/2026_07_23/manifest.json"),
        help="与新闻文字和顺序严格匹配的音频 manifest.json。",
    )
    files.add_argument(
        "--output-prefix",
        default="relaxing_news",
        help="timestamp/ 下 CSV/JSON 结果文件的文件名前缀。",
    )

    visual = parser.add_argument_group("视觉设置")
    visual.add_argument(
        "--font-size",
        type=int,
        default=40,
        help="新闻文字的最大字号；过长新闻会自动继续缩小并换行。",
    )
    visual.add_argument(
        "--square-size",
        type=int,
        default=100,
        help="始终保持红色的正方形边长（像素）。",
    )
    visual.add_argument(
        "--rest-screen",
        choices=("news", "cross"),
        default="news",
        help=(
            "休息阶段的背景：news=保留刚才的新闻页面；"
            "cross=黑底灰色十字。两种模式都显示继续按钮。"
        ),
    )

    timing = parser.add_argument_group("时序（全部为秒）")
    timing.add_argument(
        "--pre-audio-delay",
        type=float,
        default=0.5,
        help="新闻文字和红方块出现后，到音频开始的固定延迟。",
    )
    timing.add_argument(
        "--post-audio-hold",
        type=float,
        default=1.0,
        help="音频结束后继续保持新闻文字和红方块的时间。",
    )
    timing.add_argument(
        "--rest-min",
        type=float,
        default=5.0,
        help="继续按钮启用前的随机最短休息时长下限。",
    )
    timing.add_argument(
        "--rest-max",
        type=float,
        default=6.0,
        help="继续按钮启用前的随机最短休息时长上限。",
    )
    return parser.parse_args(argv)


def main_relaxing_news(argv=None) -> None:
    """Run the patient relaxation news paradigm."""
    args = parse_relaxing_news_args(argv)
    paradigm = RelaxingNewsParadigm(
        news_file=str(args.news),
        audio_manifest=str(args.manifest),
        font_size=args.font_size,
        square_size=args.square_size,
        pre_audio_delay=args.pre_audio_delay,
        post_audio_hold=args.post_audio_hold,
        rest_min=args.rest_min,
        rest_max=args.rest_max,
        rest_screen=args.rest_screen,
        output_prefix=args.output_prefix,
        display_mode=args.display_mode,
    )
    paradigm.run()
