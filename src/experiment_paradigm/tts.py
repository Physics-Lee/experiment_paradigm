"""Generate one neural TTS audio file per sentence and write a manifest."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import edge_tts
from mutagen.mp3 import MP3


SCHEMA_VERSION = 1
DEFAULT_VOICE = "en-US-JennyNeural"


def read_sentences(path: Path) -> list[str]:
    """Read non-empty UTF-8 stimulus lines without changing their order."""
    with path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any] | None:
    """Load an existing manifest if present."""
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_manifest_atomic(path: Path, manifest: dict[str, Any]) -> None:
    """Atomically replace a manifest without exposing partially written JSON."""
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".manifest_",
        suffix=".tmp.json",
        dir=path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        with temporary_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def can_reuse_audio(
    output_path: Path,
    existing_item: dict[str, Any] | None,
    *,
    sentence_id: str,
    text: str,
) -> bool:
    """Return whether an existing audio file exactly matches its manifest item."""
    if not output_path.exists() or existing_item is None:
        return False
    if (
        existing_item.get("id") != sentence_id
        or existing_item.get("text") != text
        or existing_item.get("file") != output_path.name
    ):
        return False
    expected_hash = existing_item.get("sha256")
    return isinstance(expected_hash, str) and sha256_file(output_path) == expected_hash


async def generate_audio(
    *,
    text: str,
    output_path: Path,
    voice: str,
    rate: str,
    volume: str,
    pitch: str,
) -> None:
    """Generate one MP3 atomically so interrupted requests leave no final file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}_",
        suffix=".tmp.mp3",
        dir=output_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)

    try:
        communicator = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch,
        )
        await communicator.save(str(temporary_path))
        if temporary_path.stat().st_size == 0:
            raise RuntimeError(f"TTS returned an empty file for {text!r}")
        temporary_path.replace(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def audio_metadata(path: Path) -> tuple[int, str]:
    """Return MP3 duration in milliseconds and its SHA-256 digest."""
    duration_ms = round(MP3(path).info.length * 1000)
    return duration_ms, sha256_file(path)


async def build_audio_set(args: argparse.Namespace) -> dict[str, Any]:
    """Generate or reuse the full ordered sentence audio set."""
    sentences_path = args.sentences.resolve()
    output_dir = args.output_dir.resolve()
    manifest_path = output_dir / "manifest.json"
    sentences = read_sentences(sentences_path)
    if not sentences:
        raise ValueError(f"No non-empty sentences found in {sentences_path}")

    existing_manifest = load_manifest(manifest_path)
    existing_items = {}
    if existing_manifest:
        existing_items = {
            item.get("id"): item
            for item in existing_manifest.get("items", [])
            if isinstance(item, dict)
        }

    requested_tts = {
        "provider": "microsoft-edge-tts",
        "client": "edge-tts",
        "client_version": edge_tts.__version__,
        "voice": args.voice,
        "rate": args.rate,
        "volume": args.volume,
        "pitch": args.pitch,
        "format": "mp3",
    }
    settings_match = (
        existing_manifest is not None
        and existing_manifest.get("tts") == requested_tts
    )
    generation_started_at = (
        existing_manifest.get("created_at")
        if settings_match and isinstance(existing_manifest.get("created_at"), str)
        else datetime.now(timezone.utc).isoformat()
    )
    sentences_file = os.path.relpath(sentences_path, output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    generated_any = False
    for index, text in enumerate(sentences, start=1):
        sentence_id = f"sentence_{index:03d}"
        output_path = output_dir / f"{sentence_id}.mp3"
        existing_item = existing_items.get(sentence_id)

        reusable = settings_match and can_reuse_audio(
            output_path,
            existing_item,
            sentence_id=sentence_id,
            text=text,
        )
        if args.force or not reusable:
            if output_path.exists() and not args.force:
                raise FileExistsError(
                    f"Refusing to overwrite unmatched audio file: {output_path}. "
                    "Use --force only after reviewing the existing asset."
                )
            print(f"Generating {sentence_id}: {text}")
            await generate_audio(
                text=text,
                output_path=output_path,
                voice=args.voice,
                rate=args.rate,
                volume=args.volume,
                pitch=args.pitch,
            )
            generated_any = True
        else:
            print(f"Reusing {sentence_id}: {output_path.name}")

        duration_ms, audio_hash = audio_metadata(output_path)
        items.append(
            {
                "id": sentence_id,
                "index": index,
                "text": text,
                "file": output_path.name,
                "duration_ms": duration_ms,
                "sha256": audio_hash,
            }
        )

        # Persist resumable progress after each completed audio item. Leave an
        # already complete, fully reusable manifest untouched.
        if generated_any or not (
            settings_match and existing_manifest.get("complete") is True
        ):
            write_manifest_atomic(
                manifest_path,
                {
                    "schema_version": SCHEMA_VERSION,
                    "complete": False,
                    "created_at": generation_started_at,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "sentences_file": sentences_file,
                    "tts": requested_tts,
                    "items": items,
                },
            )

    if (
        existing_manifest is not None
        and not generated_any
        and existing_manifest.get("schema_version") == SCHEMA_VERSION
        and existing_manifest.get("complete") is True
        and existing_manifest.get("sentences_file") == sentences_file
        and existing_manifest.get("items") == items
    ):
        print(f"Manifest unchanged: {manifest_path}")
        return existing_manifest

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "complete": True,
        "created_at": generation_started_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sentences_file": sentences_file,
        "tts": requested_tts,
        "items": items,
    }

    write_manifest_atomic(manifest_path, manifest)

    return manifest


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "为句子刺激文件逐行生成稳定的神经 TTS 音频，"
            "并建立文字—音频 manifest.json 对应清单。"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "示例: python scripts/generate_sentence_audio.py "
            "--sentences stimuli/yan_jiangyi.txt "
            "--output-dir assets/sentence_audio/yan_jiangyi "
            "--voice zh-CN-XiaoxiaoNeural"
        ),
    )
    files = parser.add_argument_group("输入与输出")
    files.add_argument(
        "--sentences",
        type=Path,
        default=Path("stimuli/sentences_en.txt"),
        help="UTF-8 刺激文件；每个非空行生成一个音频。",
    )
    files.add_argument(
        "--output-dir",
        type=Path,
        default=Path("assets/sentence_audio/en"),
        help="MP3 文件和 manifest.json 的输出目录。",
    )

    speech = parser.add_argument_group("TTS 语音设置")
    speech.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=(
            "Microsoft Edge TTS 语音名称；中文可使用 "
            "zh-CN-XiaoxiaoNeural。"
        ),
    )
    speech.add_argument(
        "--rate",
        default="+0%",
        help="语速相对调整，例如 -10%%、+20%%。",
    )
    speech.add_argument(
        "--volume",
        default="+0%",
        help="音量相对调整，例如 -10%%、+20%%。",
    )
    speech.add_argument(
        "--pitch",
        default="+0Hz",
        help="音调相对调整，例如 -10Hz、+20Hz。",
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


def main() -> None:
    args = parse_args()
    manifest = asyncio.run(build_audio_set(args))
    print(
        f"Wrote {len(manifest['items'])} audio files and manifest to "
        f"{args.output_dir.resolve()}"
    )


if __name__ == "__main__":
    main()
