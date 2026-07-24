import asyncio
import hashlib
import json
import os
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from experiment_paradigm import (
    LockedInSentenceReadingParadigm,
    SentenceParadigm,
)
from experiment_paradigm.tts import can_reuse_audio
from experiment_paradigm.tts import build_audio_set


def write_silent_wav(path, duration=0.04, sample_rate=44100):
    frame_count = int(duration * sample_rate)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack("<h", 0) * frame_count)


def sha256_file(path):
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


class SentenceAudioTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def build_fixture(self, root, *, manifest_text="Test sentence."):
        sentences_path = root / "sentences.txt"
        sentences_path.write_text("Test sentence.\n", encoding="utf-8")

        audio_path = root / "sentence_001.wav"
        write_silent_wav(audio_path)
        manifest_path = root / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "items": [
                        {
                            "id": "sentence_001",
                            "index": 1,
                            "text": manifest_text,
                            "file": audio_path.name,
                            "duration_ms": 40,
                            "sha256": sha256_file(audio_path),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return sentences_path, manifest_path

    def build_segmented_fixture(self, root):
        sentences_path = root / "sentences.txt"
        sentences_path.write_text("手机\n", encoding="utf-8")

        segments = []
        for index, character in enumerate("手机", start=1):
            segment_id = f"sentence_001_char_{index:03d}"
            audio_path = root / f"{segment_id}.wav"
            write_silent_wav(audio_path)
            segments.append(
                {
                    "id": segment_id,
                    "index": index,
                    "text": character,
                    "file": audio_path.name,
                    "duration_ms": 40,
                    "sha256": sha256_file(audio_path),
                }
            )

        manifest_path = root / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "complete": True,
                    "items": [
                        {
                            "id": "sentence_001",
                            "index": 1,
                            "text": "手机",
                            "unit": "character",
                            "duration_ms": 80,
                            "segments": segments,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return sentences_path, manifest_path

    def test_audio_wraps_visual_trial_and_timestamps_are_ordered(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(root)
            paradigm = SentenceParadigm(
                sentences_file=str(sentences_path),
                char_speed=0.001,
                prep_time=0.001,
                prep_time_jitter=0,
                jitter_mean=0,
                jitter_std=0,
                prep_mode="square",
                play_mode="green",
                inter_sentence_interval=0,
                audio_manifest=str(manifest_path),
                pre_visual_gap=0.001,
                post_visual_gap=0.001,
                audio_screen="black",
            )

            self.assertTrue(paradigm.display_sentence("Test sentence.", 1))
            self.assertEqual(len(paradigm.trials_data), 1)
            trial = paradigm.trials_data[0]

            self.assertEqual(trial["audio_id"], "sentence_001")
            self.assertEqual(trial["audio_file"], "sentence_001.wav")
            self.assertGreater(trial["audio_duration"], 0)
            self.assertLess(trial["pre_audio_onset"], trial["pre_audio_offset"])
            self.assertLess(trial["pre_audio_offset"], trial["prep_onset"])
            self.assertLess(trial["prep_onset"], trial["sentence_complete"])
            self.assertLess(
                trial["sentence_complete"],
                trial["post_audio_onset"],
            )
            self.assertLess(
                trial["post_audio_onset"],
                trial["post_audio_offset"],
            )
            self.assertLess(trial["post_audio_offset"], trial["trial_end"])

    def test_manifest_text_must_match_sentence_order(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(
                root,
                manifest_text="Wrong sentence.",
            )
            with self.assertRaisesRegex(ValueError, "text/order"):
                SentenceParadigm(
                    sentences_file=str(sentences_path),
                    audio_manifest=str(manifest_path),
                )

    def test_incomplete_manifest_is_rejected_before_playback(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["complete"] = False
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "incomplete"):
                SentenceParadigm(
                    sentences_file=str(sentences_path),
                    audio_manifest=str(manifest_path),
                )

    def test_no_manifest_preserves_legacy_no_audio_mode(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, _ = self.build_fixture(root)
            paradigm = SentenceParadigm(sentences_file=str(sentences_path))
            self.assertFalse(paradigm.play_audio_before)
            self.assertFalse(paradigm.play_audio_after)
            self.assertEqual(paradigm.sentence_audio, [])

    def test_character_mode_animates_chinese_by_character(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path = root / "sentences.txt"
            sentences_path.write_text("我教数学\n", encoding="utf-8")
            paradigm = SentenceParadigm(
                sentences_file=str(sentences_path),
                char_speed=0.001,
                prep_time=0.001,
                prep_time_jitter=0,
                jitter_mean=0,
                jitter_std=0,
                prep_mode="square",
                play_mode="green",
                token_mode="character",
            )

            self.assertTrue(paradigm.display_sentence("我教数学", 1))
            trial = paradigm.trials_data[0]
            self.assertEqual(trial["token_mode"], "character")
            self.assertEqual(trial["token_count"], 4)

    def test_locked_in_trial_records_synchronized_character_timestamps(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(
                root,
                manifest_text="我教数学",
            )
            sentences_path.write_text("我教数学\n", encoding="utf-8")
            paradigm = LockedInSentenceReadingParadigm(
                sentences_file=str(sentences_path),
                audio_manifest=str(manifest_path),
                char_speed=0.001,
                play_mode="green",
                baseline_min=0.001,
                baseline_max=0.001,
                pre_audio_delay_min=0.001,
                pre_audio_delay_max=0.001,
                silent_delay_min=0.001,
                silent_delay_max=0.001,
                final_hold=0.001,
                rest_min=0.001,
                rest_max=0.001,
            )

            self.assertTrue(paradigm.display_sentence("我教数学", 1))
            trial = paradigm.trials_data[0]
            onsets = trial["character_green_onsets"]

            self.assertEqual(trial["paradigm"], "locked_in_sentence_reading")
            self.assertEqual(len(onsets), 4)
            self.assertEqual(trial["square_green_onset"], onsets[0])
            self.assertEqual(trial["first_character_onset"], onsets[0])
            self.assertEqual(trial["cue_tone_onset"], onsets[0])
            self.assertEqual(
                trial["sentence_visible_onset"],
                trial["red_square_onset"],
            )
            self.assertLess(
                trial["sentence_visible_onset"],
                trial["target_audio_onset"],
            )
            self.assertEqual(trial["last_character_complete"], onsets[-1])
            self.assertLess(
                trial["target_audio_offset"],
                trial["square_green_onset"],
            )
            self.assertLess(
                trial["last_character_complete"],
                trial["trial_end"],
            )
            self.assertGreaterEqual(trial["actual_silent_delay"], 0.001)
            self.assertGreaterEqual(
                trial["actual_pre_audio_delay"],
                0.001,
            )
            self.assertGreaterEqual(trial["actual_final_hold"], 0.001)
            self.assertGreaterEqual(trial["actual_rest_duration"], 0.001)

    def test_locked_in_layout_uses_upper_and_lower_screen_halves(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(
                root,
                manifest_text="我教数学",
            )
            sentences_path.write_text("我教数学\n", encoding="utf-8")
            paradigm = LockedInSentenceReadingParadigm(
                sentences_file=str(sentences_path),
                audio_manifest=str(manifest_path),
                cue_tone=False,
            )

            layout = paradigm._sentence_layout("我教数学")
            lower_half_height = paradigm.height - paradigm.height // 2

            self.assertEqual(paradigm.play_mode, "progress")
            self.assertEqual(paradigm.progress_duration, 3.0)
            self.assertLess(layout["text_y"], paradigm.height // 2)
            self.assertEqual(
                layout["square_rect"].centery,
                paradigm.height // 2 + lower_half_height // 2,
            )
            self.assertAlmostEqual(
                layout["square_size"] / lower_half_height,
                0.60,
                places=2,
            )

    def test_locked_in_rest_screen_has_half_size_gray_center_cross(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(
                root,
                manifest_text="喝",
            )
            sentences_path.write_text("喝\n", encoding="utf-8")
            paradigm = LockedInSentenceReadingParadigm(
                sentences_file=str(sentences_path),
                audio_manifest=str(manifest_path),
                rest_cross=True,
                cue_tone=False,
            )

            paradigm._draw_rest_screen()
            center = (paradigm.width // 2, paradigm.height // 2)
            cross_inside = (
                center[0] + round(min(paradigm.width, paradigm.height) * 0.1),
                center[1],
            )
            cross_outside = (
                center[0] + round(min(paradigm.width, paradigm.height) * 0.12),
                center[1],
            )

            self.assertEqual(paradigm.screen.get_at(center)[:3], paradigm.GRAY)
            self.assertEqual(
                paradigm.screen.get_at(cross_inside)[:3],
                paradigm.GRAY,
            )
            self.assertEqual(
                paradigm.screen.get_at(cross_outside)[:3],
                paradigm.BLACK,
            )
            self.assertEqual(paradigm.screen.get_at((0, 0))[:3], paradigm.BLACK)

    def test_locked_in_rest_screen_is_black_by_default(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(
                root,
                manifest_text="喝",
            )
            sentences_path.write_text("喝\n", encoding="utf-8")
            paradigm = LockedInSentenceReadingParadigm(
                sentences_file=str(sentences_path),
                audio_manifest=str(manifest_path),
                cue_tone=False,
            )

            paradigm._draw_rest_screen()
            center = (paradigm.width // 2, paradigm.height // 2)

            self.assertFalse(paradigm.rest_cross_enabled)
            self.assertEqual(paradigm.screen.get_at(center)[:3], paradigm.BLACK)

    def test_locked_in_progress_mode_records_progress_events(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(
                root,
                manifest_text="手机",
            )
            sentences_path.write_text("手机\n", encoding="utf-8")
            paradigm = LockedInSentenceReadingParadigm(
                sentences_file=str(sentences_path),
                audio_manifest=str(manifest_path),
                play_mode="progress",
                progress_duration=0.001,
                progress_pause=0.001,
                baseline_min=0.001,
                baseline_max=0.001,
                pre_audio_delay_min=0.001,
                pre_audio_delay_max=0.001,
                silent_delay_min=0.001,
                silent_delay_max=0.001,
                final_hold=0.001,
                rest_min=0.001,
                rest_max=0.001,
                cue_tone=False,
            )

            self.assertTrue(paradigm.display_sentence("手机", 1))
            trial = paradigm.trials_data[0]
            events = trial["character_progress_events"]

            self.assertEqual(trial["play_mode"], "progress")
            self.assertEqual(trial["character_green_events"], [])
            self.assertEqual(len(events), 2)
            self.assertLess(events[0]["onset"], events[0]["completion"])
            self.assertLess(events[0]["completion"], events[1]["onset"])
            self.assertEqual(
                trial["last_character_complete"],
                events[-1]["completion"],
            )

    def test_character_audio_segments_play_in_order(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_segmented_fixture(root)
            paradigm = LockedInSentenceReadingParadigm(
                sentences_file=str(sentences_path),
                audio_manifest=str(manifest_path),
                progress_duration=0.001,
                progress_pause=0,
                baseline_min=0.001,
                baseline_max=0.001,
                pre_audio_delay_min=0.001,
                pre_audio_delay_max=0.001,
                silent_delay_min=0.001,
                silent_delay_max=0.001,
                final_hold=0.001,
                rest_min=0.001,
                rest_max=0.001,
                cue_tone=False,
            )

            self.assertTrue(
                paradigm.display_sentence(
                    "手机",
                    trial_id=2,
                    stimulus_index=1,
                    repetition=2,
                    repetition_trial=1,
                )
            )
            trial = paradigm.trials_data[0]
            segment_events = trial["target_audio_segments"]

            self.assertEqual(trial["trial_id"], 2)
            self.assertEqual(trial["stimulus_index"], 1)
            self.assertEqual(trial["repetition"], 2)
            self.assertEqual(trial["repetition_trial"], 1)
            self.assertEqual(trial["audio_segment_count"], 2)
            self.assertEqual(
                [event["text"] for event in segment_events],
                ["手", "机"],
            )
            self.assertLess(
                segment_events[0]["offset"],
                segment_events[1]["onset"],
            )

    def test_locked_in_schedule_reshuffles_each_repetition(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path, manifest_path = self.build_fixture(root)
            paradigm = LockedInSentenceReadingParadigm(
                sentences_file=str(sentences_path),
                audio_manifest=str(manifest_path),
                repetitions=2,
                shuffle=True,
                cue_tone=False,
            )
            paradigm.sentences = ["甲", "乙", "丙"]

            with patch(
                "experiment_paradigm.paradigms.random.shuffle",
                side_effect=lambda order: order.reverse(),
            ) as shuffle:
                schedule = paradigm._build_trial_schedule()

            self.assertEqual(shuffle.call_count, 2)
            self.assertEqual(
                [trial["stimulus_index"] for trial in schedule],
                [3, 2, 1, 3, 2, 1],
            )
            self.assertEqual(
                [trial["repetition"] for trial in schedule],
                [1, 1, 1, 2, 2, 2],
            )

    def test_existing_generated_audio_is_reused_only_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            audio_path = root / "sentence_001.mp3"
            audio_path.write_bytes(b"stable generated audio")
            item = {
                "id": "sentence_001",
                "text": "Test sentence.",
                "file": audio_path.name,
                "sha256": sha256_file(audio_path),
            }

            self.assertTrue(
                can_reuse_audio(
                    audio_path,
                    item,
                    sentence_id="sentence_001",
                    text="Test sentence.",
                )
            )
            audio_path.write_bytes(b"changed audio")
            self.assertFalse(
                can_reuse_audio(
                    audio_path,
                    item,
                    sentence_id="sentence_001",
                    text="Test sentence.",
                )
            )

    def test_tts_generator_sends_chinese_characters_separately(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path = root / "sentences.txt"
            sentences_path.write_text("手机\n", encoding="utf-8")
            output_dir = root / "audio"
            args = SimpleNamespace(
                sentences=sentences_path,
                output_dir=output_dir,
                tts_unit="auto",
                voice="zh-CN-XiaoxiaoNeural",
                rate="-50%",
                volume="+0%",
                pitch="+0Hz",
                force=False,
            )
            generated_texts = []

            async def fake_generate_audio(**kwargs):
                generated_texts.append(kwargs["text"])
                kwargs["output_path"].write_bytes(kwargs["text"].encode("utf-8"))

            def fake_audio_metadata(path):
                return 1000, sha256_file(path)

            with patch(
                "experiment_paradigm.tts.generate_audio",
                side_effect=fake_generate_audio,
            ), patch(
                "experiment_paradigm.tts.audio_metadata",
                side_effect=fake_audio_metadata,
            ):
                manifest = asyncio.run(build_audio_set(args))

            self.assertEqual(generated_texts, ["手", "机"])
            self.assertEqual(manifest["schema_version"], 2)
            self.assertEqual(manifest["items"][0]["unit"], "character")
            self.assertEqual(
                [
                    segment["text"]
                    for segment in manifest["items"][0]["segments"]
                ],
                ["手", "机"],
            )

    def test_character_tts_secretly_maps_jue_to_jiao_pronunciation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentences_path = root / "sentences.txt"
            sentences_path.write_text("睡觉\n", encoding="utf-8")
            output_dir = root / "audio"
            args = SimpleNamespace(
                sentences=sentences_path,
                output_dir=output_dir,
                tts_unit="character",
                voice="zh-CN-XiaoxiaoNeural",
                rate="-50%",
                volume="+0%",
                pitch="+0Hz",
                force=False,
            )
            generated_texts = []

            async def fake_generate_audio(**kwargs):
                generated_texts.append(kwargs["text"])
                kwargs["output_path"].write_bytes(
                    kwargs["text"].encode("utf-8")
                )

            def fake_audio_metadata(path):
                return 1000, sha256_file(path)

            with patch(
                "experiment_paradigm.tts.generate_audio",
                side_effect=fake_generate_audio,
            ), patch(
                "experiment_paradigm.tts.audio_metadata",
                side_effect=fake_audio_metadata,
            ):
                manifest = asyncio.run(build_audio_set(args))

            self.assertEqual(generated_texts, ["睡", "叫"])
            self.assertEqual(manifest["items"][0]["text"], "睡觉")
            self.assertEqual(
                [
                    segment["text"]
                    for segment in manifest["items"][0]["segments"]
                ],
                ["睡", "觉"],
            )
            self.assertEqual(
                [
                    segment["tts_text"]
                    for segment in manifest["items"][0]["segments"]
                ],
                ["睡", "叫"],
            )
            self.assertEqual(
                manifest["tts"]["character_pronunciation_aliases"],
                {"觉": "叫"},
            )

    def test_wrong_legacy_jue_audio_is_not_reused_after_alias_change(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            audio_path = Path(temporary_directory) / "jue.mp3"
            audio_path.write_bytes(b"old isolated jue audio")
            legacy_item = {
                "id": "sentence_001_char_002",
                "text": "觉",
                "file": audio_path.name,
                "sha256": sha256_file(audio_path),
            }

            self.assertFalse(
                can_reuse_audio(
                    audio_path,
                    legacy_item,
                    sentence_id="sentence_001_char_002",
                    text="觉",
                    tts_text="叫",
                )
            )


if __name__ == "__main__":
    unittest.main()
