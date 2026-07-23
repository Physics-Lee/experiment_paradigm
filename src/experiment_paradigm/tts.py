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

from .stimuli import read_news_items, read_nonempty_lines, split_tts_units


SCHEMA_VERSION = 2
DEFAULT_VOICE = "en-US-JennyNeural"


class DetailedHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Show defaults while preserving multi-line usage notes."""


def read_sentences(path: Path) -> list[str]:
    """Read non-empty UTF-8 stimulus lines without changing their order."""
    return read_nonempty_lines(path)


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


async def build_audio_set(
    args: argparse.Namespace,
    *,
    text_loader=read_sentences,
) -> dict[str, Any]:
    """Generate or reuse the full ordered sentence audio set."""
    sentences_path = args.sentences.resolve()
    output_dir = args.output_dir.resolve()
    manifest_path = output_dir / "manifest.json"
    sentences = text_loader(sentences_path)
    if not sentences:
        raise ValueError(f"No non-empty sentences found in {sentences_path}")

    segmented_sentences = [
        (text, *split_tts_units(text, args.tts_unit))
        for text in sentences
    ]

    existing_manifest = load_manifest(manifest_path)
    existing_segments: dict[str, dict[str, Any]] = {}
    if existing_manifest:
        for item in existing_manifest.get("items", []):
            if not isinstance(item, dict):
                continue
            segments = item.get("segments")
            if isinstance(segments, list):
                for segment in segments:
                    if isinstance(segment, dict):
                        existing_segments[segment.get("id")] = segment
            elif isinstance(item.get("id"), str):
                # Schema 1 stored one whole-line audio file directly on item.
                existing_segments[item["id"]] = item

    base_tts_settings = {
        "provider": "microsoft-edge-tts",
        "client": "edge-tts",
        "client_version": edge_tts.__version__,
        "voice": args.voice,
        "rate": args.rate,
        "volume": args.volume,
        "pitch": args.pitch,
        "format": "mp3",
    }
    requested_tts = {
        **base_tts_settings,
        "unit": args.tts_unit,
    }
    all_resolved_as_lines = all(
        resolved_unit == "line"
        for _, resolved_unit, _ in segmented_sentences
    )
    existing_tts = (
        existing_manifest.get("tts") if existing_manifest else None
    )
    settings_match = (
        existing_manifest is not None
        and (
            existing_tts == requested_tts
            or (
                existing_tts == base_tts_settings
                and all_resolved_as_lines
            )
        )
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
    for index, (text, resolved_unit, text_units) in enumerate(
        segmented_sentences,
        start=1,
    ):
        sentence_id = f"sentence_{index:03d}"
        segments: list[dict[str, Any]] = []

        for unit_index, unit_text in enumerate(text_units, start=1):
            if resolved_unit == "line":
                segment_id = sentence_id
                filename = f"{sentence_id}.mp3"
            else:
                segment_id = f"{sentence_id}_char_{unit_index:03d}"
                filename = f"{segment_id}.mp3"

            output_path = output_dir / filename
            existing_segment = existing_segments.get(segment_id)
            reusable = settings_match and can_reuse_audio(
                output_path,
                existing_segment,
                sentence_id=segment_id,
                text=unit_text,
            )
            if args.force or not reusable:
                if output_path.exists() and not args.force:
                    raise FileExistsError(
                        "Refusing to overwrite unmatched audio file: "
                        f"{output_path}. Use --force only after reviewing "
                        "the existing asset."
                    )
                print(f"Generating {segment_id}: {unit_text}")
                await generate_audio(
                    text=unit_text,
                    output_path=output_path,
                    voice=args.voice,
                    rate=args.rate,
                    volume=args.volume,
                    pitch=args.pitch,
                )
                generated_any = True
            else:
                print(f"Reusing {segment_id}: {output_path.name}")

            duration_ms, audio_hash = audio_metadata(output_path)
            segments.append(
                {
                    "id": segment_id,
                    "index": unit_index,
                    "text": unit_text,
                    "file": filename,
                    "duration_ms": duration_ms,
                    "sha256": audio_hash,
                }
            )

            current_item = {
                "id": sentence_id,
                "index": index,
                "text": text,
                "unit": resolved_unit,
                "duration_ms": sum(
                    segment["duration_ms"] for segment in segments
                ),
                "segments": segments,
            }

            # Persist after every segment so interrupted character generation
            # can resume without rewriting completed audio.
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
                        "items": [*items, current_item],
                    },
                )

        items.append(current_item)

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


def parse_args(argv=None):
    """Compatibility wrapper for the relocated sentence-TTS parser."""
    from .commands.tts import parse_args as command_parser

    return command_parser(argv)


def main(argv=None) -> None:
    """Compatibility wrapper for sentence TTS generation."""
    from .commands.tts import main as command_main

    command_main(argv)


def parse_news_args(argv=None):
    """Compatibility wrapper for the relocated news-TTS parser."""
    from .commands.tts import parse_news_args as command_parser

    return command_parser(argv)


def main_news(argv=None) -> None:
    """Compatibility wrapper for relaxing-news TTS generation."""
    from .commands.tts import main_news as command_main

    command_main(argv)


if __name__ == "__main__":
    main()
