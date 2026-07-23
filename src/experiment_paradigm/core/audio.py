"""Manifest validation, preloading, and timestamped sentence playback."""

import hashlib
import json
from pathlib import Path

import pygame

from ..stimuli import split_tts_units


class SentenceAudioMixin:
    """Reusable sentence-audio behavior for visual paradigms."""

    @staticmethod
    def _sha256_file(path):
        """Return the SHA-256 digest for an audio asset."""
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _validate_sentence_audio_manifest(self, manifest_path, sentences):
        """Validate the ordered sentence/audio mapping before fullscreen starts."""
        manifest_path = Path(manifest_path).resolve()
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        schema_version = manifest.get("schema_version")
        if schema_version not in (1, 2):
            raise ValueError(
                f"Unsupported sentence audio manifest schema: "
                f"{manifest.get('schema_version')!r}"
            )
        if manifest.get("complete") is False:
            raise ValueError(
                f"Sentence audio manifest is incomplete: {manifest_path}"
            )

        items = manifest.get("items")
        if not isinstance(items, list) or len(items) != len(sentences):
            raise ValueError(
                "Sentence audio manifest must contain exactly one ordered item "
                f"per sentence ({len(sentences)} required)"
            )

        manifest_dir = manifest_path.parent
        validated_audio = []
        seen_item_ids = set()
        seen_segment_ids = set()
        for index, (sentence, item) in enumerate(
            zip(sentences, items),
            start=1,
        ):
            if not isinstance(item, dict):
                raise ValueError(f"Manifest item {index} must be an object")
            if item.get("index") != index or item.get("text") != sentence:
                raise ValueError(
                    f"Manifest item {index} does not match sentence text/order"
                )

            audio_id = item.get("id")
            if not isinstance(audio_id, str) or not audio_id:
                raise ValueError(f"Manifest item {index} has no valid id")
            if audio_id in seen_item_ids:
                raise ValueError(f"Duplicate sentence audio id: {audio_id}")
            seen_item_ids.add(audio_id)

            if schema_version == 1:
                unit_mode = "line"
                segment_items = [item]
                expected_text_units = [sentence]
            else:
                unit_mode = item.get("unit")
                if unit_mode not in ("line", "character"):
                    raise ValueError(
                        f"Manifest item {index} has no valid TTS unit"
                    )
                _, expected_text_units = split_tts_units(
                    sentence,
                    unit_mode,
                )
                segment_items = item.get("segments")
                if not isinstance(segment_items, list) or not segment_items:
                    raise ValueError(
                        f"Manifest item {index} has no audio segments"
                    )
                segment_texts = [
                    segment.get("text")
                    if isinstance(segment, dict)
                    else None
                    for segment in segment_items
                ]
                if segment_texts != expected_text_units:
                    raise ValueError(
                        f"Manifest item {index} segments do not match text"
                    )

            validated_segments = []
            for segment_index, segment in enumerate(segment_items, start=1):
                if not isinstance(segment, dict):
                    raise ValueError(
                        f"Manifest item {index} segment {segment_index} "
                        "must be an object"
                    )
                segment_id = segment.get("id")
                if not isinstance(segment_id, str) or not segment_id:
                    raise ValueError(
                        f"Manifest item {index} segment {segment_index} "
                        "has no valid id"
                    )
                if segment_id in seen_segment_ids:
                    raise ValueError(
                        f"Duplicate sentence audio segment id: {segment_id}"
                    )
                seen_segment_ids.add(segment_id)
                if schema_version == 2 and segment.get("index") != segment_index:
                    raise ValueError(
                        f"Manifest item {index} segment order is invalid"
                    )

                file_value = segment.get("file")
                if not isinstance(file_value, str) or not file_value:
                    raise ValueError(
                        f"Manifest item {index} segment {segment_index} "
                        "has no valid file"
                    )
                audio_path = (manifest_dir / file_value).resolve()
                if not audio_path.is_relative_to(manifest_dir):
                    raise ValueError(
                        "Manifest audio path escapes its directory: "
                        f"{file_value}"
                    )
                if not audio_path.is_file():
                    raise FileNotFoundError(
                        f"Sentence audio not found: {audio_path}"
                    )

                expected_hash = segment.get("sha256")
                if not isinstance(expected_hash, str) or (
                    self._sha256_file(audio_path) != expected_hash.lower()
                ):
                    raise ValueError(
                        "Sentence audio checksum mismatch: "
                        f"{audio_path.name}"
                    )
                validated_segments.append(
                    {
                        "id": segment_id,
                        "index": segment_index,
                        "text": expected_text_units[segment_index - 1],
                        "file": file_value,
                        "path": audio_path,
                    }
                )

            validated_audio.append(
                {
                    "id": audio_id,
                    "unit": unit_mode,
                    "segments": validated_segments,
                }
            )

        return manifest_path, validated_audio

    def _preload_sentence_audio(self, manifest_path, validated_audio):
        """Decode all validated sentence audio into mixer Sound objects."""
        loaded_audio = []
        for item in validated_audio:
            loaded_segments = []
            for segment in item["segments"]:
                audio_path = segment["path"]
                try:
                    sound = pygame.mixer.Sound(str(audio_path))
                except pygame.error as error:
                    raise ValueError(
                        f"Could not decode sentence audio: {audio_path}"
                    ) from error
                loaded_segments.append(
                    {
                        **segment,
                        "duration": sound.get_length(),
                        "sound": sound,
                    }
                )

            loaded_audio.append(
                {
                    "id": item["id"],
                    "unit": item["unit"],
                    "file": (
                        loaded_segments[0]["file"]
                        if len(loaded_segments) == 1
                        else None
                    ),
                    "files": [
                        segment["file"] for segment in loaded_segments
                    ],
                    "duration": sum(
                        segment["duration"] for segment in loaded_segments
                    ),
                    "segments": loaded_segments,
                }
            )

        print(
            f"Preloaded {len(loaded_audio)} trials / "
            f"{sum(len(item['segments']) for item in loaded_audio)} audio "
            "segments from "
            f"{manifest_path}"
        )
        return loaded_audio

    def _draw_audio_screen(self):
        """Draw the configured neutral screen for audio and audio/visual gaps."""
        self.screen.fill(self.BLACK)
        if self.audio_screen == "fixation":
            self.draw_fixation_cross()

    def _play_sentence_audio(
        self,
        audio_item,
        phase,
        trial_data,
        draw_frame=None,
    ):
        """Play one preloaded sentence sound and timestamp its command lifecycle."""
        if draw_frame is None:
            draw_frame = self._draw_audio_screen

        draw_frame()
        pygame.display.flip()

        overall_onset = self.get_timestamp()
        overall_onset_abs = self.get_absolute_time()
        trial_data[f"{phase}_audio_onset"] = overall_onset
        trial_data[f"{phase}_audio_onset_abs"] = overall_onset_abs
        segment_events = []
        for segment_index, segment in enumerate(
            audio_item["segments"],
            start=1,
        ):
            segment_onset = (
                overall_onset
                if segment_index == 1
                else self.get_timestamp()
            )
            segment_onset_abs = (
                overall_onset_abs
                if segment_index == 1
                else self.get_absolute_time()
            )
            channel = segment["sound"].play()
            if channel is None:
                raise RuntimeError(
                    f"No mixer channel available for {segment['file']}"
                )

            while channel.get_busy():
                if not self.check_exit_events():
                    channel.stop()
                    return False
                draw_frame()
                pygame.display.flip()
                self.clock.tick(60)

            segment_events.append(
                {
                    "index": segment_index,
                    "text": segment["text"],
                    "file": segment["file"],
                    "onset": segment_onset,
                    "onset_abs": segment_onset_abs,
                    "offset": self.get_timestamp(),
                    "offset_abs": self.get_absolute_time(),
                }
            )

        trial_data[f"{phase}_audio_offset"] = self.get_timestamp()
        trial_data[f"{phase}_audio_offset_abs"] = self.get_absolute_time()
        trial_data[f"{phase}_audio_segments"] = segment_events
        return True

    def _show_audio_visual_gap(self, duration):
        """Show the neutral audio screen for an exact configurable gap."""
        gap_start = self.get_timestamp()
        while self.get_timestamp() - gap_start < duration:
            if not self.check_exit_events():
                return False, self.get_timestamp() - gap_start
            self._draw_audio_screen()
            pygame.display.flip()
            self.clock.tick(60)
        return True, self.get_timestamp() - gap_start
