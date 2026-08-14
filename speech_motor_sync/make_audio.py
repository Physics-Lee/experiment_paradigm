"""Generate spoken-numeral TTS audio for 一二三四五六七八九十.

Produces two parallel sets under ``audio/``, using the same voice as the
locked-in paradigm default (``zh-CN-YunxiaNeural``):

  audio/slow/01.mp3 .. 10.mp3    -- rate -50%  (slow; the locked-in default)
  audio/normal/01.mp3 .. 10.mp3  -- rate +0%   (normal speed)

File naming matches ``gestures/`` (``01``..``10``), so stimulus i pairs with
``audio/<set>/0i.mp3``. Generation requires internet + ``edge-tts``; the
paradigm itself plays offline.

    pip install edge-tts
    python make_audio.py           # generate both sets (reuses existing)
    python make_audio.py --force   # regenerate and overwrite
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile
from pathlib import Path

import edge_tts

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paradigm import DEFAULT_CHARACTERS  # noqa: E402

VOICE = "zh-CN-YunxiaNeural"          # same as locked-in default
SETS = {"slow": "-50%", "normal": "+0%"}
BASE_DIR = Path(__file__).resolve().parent / "audio"


async def generate_one(text, output_path, voice, rate):
    """Generate one MP3 atomically so a failed request leaves no final file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}_",
        suffix=".tmp.mp3",
        dir=output_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        communicate = edge_tts.Communicate(
            text=text, voice=voice, rate=rate
        )
        await communicate.save(str(temporary_path))
        if temporary_path.stat().st_size == 0:
            raise RuntimeError(f"TTS returned an empty file for {text!r}")
        temporary_path.replace(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


async def build_set(name, rate, force, voice):
    """Generate one full slow/normal set for every numeral."""
    out_dir = BASE_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, char in enumerate(DEFAULT_CHARACTERS, start=1):
        path = out_dir / f"{index:02d}.mp3"
        if path.exists() and not force:
            print(f"Reusing {name}/{path.name} ({char})")
            continue
        print(f"Generating {name}/{path.name} ({char}, rate={rate})")
        await generate_one(char, path, voice, rate)
    print(f"Set '{name}' complete -> {out_dir}")


async def main_async(force, voice):
    for name, rate in SETS.items():
        await build_set(name, rate, force, voice)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="生成一二三四五六七八九十的神经 TTS 音频（慢速 -50% 与正常两套）。"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成并覆盖已有音频。",
    )
    parser.add_argument(
        "--voice",
        default=VOICE,
        help="Edge TTS 语音名称；默认与闭锁范式一致 zh-CN-YunxiaNeural。",
    )
    args = parser.parse_args()
    asyncio.run(main_async(args.force, args.voice))


if __name__ == "__main__":
    main()
