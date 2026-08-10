"""Locked-in patient character-paced sentence-reading paradigm."""

import math
import random
import struct

import pygame

from ..core import (
    draw_cross,
    load_cjk_font,
    show_for_duration,
    validate_duration_range,
)
from .sentence import SentenceParadigm


class LockedInSentenceReadingParadigm(SentenceParadigm):
    """Character-paced sentence reading for patients with locked-in syndrome."""

    def __init__(
        self,
        sentences_file,
        audio_manifest,
        char_speed=1.2,
        play_mode="progress",
        progress_duration=2.0,
        progress_pause=0.5,
        rest_cross=False,
        baseline_min=1.5,
        baseline_max=2.5,
        pre_audio_delay_min=0.4,
        pre_audio_delay_max=0.6,
        silent_delay_min=1.5,
        silent_delay_max=2.0,
        final_hold=0.5,
        rest_min=5.0,
        rest_max=6.0,
        cue_tone=True,
        cue_frequency=1000,
        cue_duration=0.08,
        cue_volume=0.7,
        repetitions=1,
        shuffle=False,
        continue_button=True,
        output_prefix="locked_in_sentence_reading",
        display_mode="borderless",
        font_size=80,
    ):
        """Initialize the locked-in sentence-reading paradigm."""
        self._validate_duration_range(
            "baseline",
            baseline_min,
            baseline_max,
        )
        self._validate_duration_range(
            "pre-audio delay",
            pre_audio_delay_min,
            pre_audio_delay_max,
        )
        self._validate_duration_range(
            "silent delay",
            silent_delay_min,
            silent_delay_max,
        )
        self._validate_duration_range("rest", rest_min, rest_max)
        if char_speed <= 0:
            raise ValueError("char_speed must be positive")
        if play_mode not in ("green", "progress"):
            raise ValueError("play_mode must be 'green' or 'progress'")
        if progress_duration <= 0:
            raise ValueError("progress_duration must be positive")
        if progress_pause < 0:
            raise ValueError("progress_pause must be non-negative")
        if final_hold < 0:
            raise ValueError("final_hold must be non-negative")
        if cue_frequency <= 0:
            raise ValueError("cue_frequency must be positive")
        if cue_duration <= 0:
            raise ValueError("cue_duration must be positive")
        if not 0 < cue_volume <= 1:
            raise ValueError("cue_volume must be greater than 0 and at most 1")
        if font_size < 12:
            raise ValueError("font_size must be at least 12")
        if isinstance(repetitions, bool) or not isinstance(repetitions, int):
            raise ValueError("repetitions must be an integer")
        if repetitions < 1:
            raise ValueError("repetitions must be at least 1")

        super().__init__(
            sentences_file=sentences_file,
            char_speed=char_speed,
            prep_mode="square",
            play_mode=play_mode,
            progress_duration=progress_duration,
            progress_pause=progress_pause,
            inter_sentence_interval=0,
            output_prefix=output_prefix,
            audio_manifest=audio_manifest,
            play_audio_before=True,
            play_audio_after=False,
            audio_screen="black",
            token_mode="character",
            display_mode=display_mode,
        )

        self.baseline_min = baseline_min
        self.baseline_max = baseline_max
        self.pre_audio_delay_min = pre_audio_delay_min
        self.pre_audio_delay_max = pre_audio_delay_max
        self.silent_delay_min = silent_delay_min
        self.silent_delay_max = silent_delay_max
        self.final_hold = final_hold
        self.rest_min = rest_min
        self.rest_max = rest_max
        self.rest_cross_enabled = rest_cross
        self.cue_tone_enabled = cue_tone
        self.cue_frequency = cue_frequency
        self.cue_duration = cue_duration
        self.cue_volume = cue_volume
        self.repetitions = repetitions
        self.shuffle = shuffle
        self.continue_button_enabled = continue_button
        self.max_font_size = font_size
        self.cue_sound = self._create_cue_sound() if cue_tone else None
        button_font_size = max(18, min(32, round(self.height * 0.035)))
        self.continue_button_font = load_cjk_font(
            button_font_size,
            announce=False,
        )

    @staticmethod
    def _validate_duration_range(name, minimum, maximum):
        validate_duration_range(name, minimum, maximum)

    def _create_cue_sound(self):
        """Create the same short, category-neutral cue tone for every trial."""
        mixer_config = pygame.mixer.get_init()
        if mixer_config is None:
            raise RuntimeError("Pygame mixer is not initialized")

        sample_rate, sample_format, channels = mixer_config
        if abs(sample_format) != 16:
            raise RuntimeError(
                "Cue tone generation requires a 16-bit mixer format"
            )

        frame_count = max(1, round(sample_rate * self.cue_duration))
        fade_frames = max(1, min(frame_count // 2, round(sample_rate * 0.005)))
        pcm = bytearray()
        for frame_index in range(frame_count):
            fade_in = min(1.0, frame_index / fade_frames)
            fade_out = min(1.0, (frame_count - frame_index - 1) / fade_frames)
            envelope = min(fade_in, fade_out)
            sample = int(
                32767
                * self.cue_volume
                * envelope
                * math.sin(
                    2
                    * math.pi
                    * self.cue_frequency
                    * frame_index
                    / sample_rate
                )
            )
            encoded_sample = struct.pack("<h", sample)
            pcm.extend(encoded_sample * channels)

        return pygame.mixer.Sound(buffer=bytes(pcm))

    @staticmethod
    def _characters(sentence):
        """Return display characters while ignoring layout-only whitespace."""
        return [character for character in sentence if not character.isspace()]

    def _font_at_size(self, font_size):
        """Load the same CJK-capable font strategy at a requested size."""
        return load_cjk_font(font_size, announce=False)

    def _sentence_layout(self, sentence):
        """Fit one centered character row above a square centered on the midline."""
        characters = self._characters(sentence)
        if not characters:
            raise ValueError("Sentence must contain at least one character")

        upper_height = self.height // 2
        maximum_width = round(self.width * 0.9)
        maximum_height = round(upper_height * 0.8)
        minimum_size = 12
        maximum_size = max(minimum_size, min(self.max_font_size, maximum_height))
        best = None

        while minimum_size <= maximum_size:
            candidate_size = (minimum_size + maximum_size) // 2
            candidate_font = self._font_at_size(candidate_size)
            spacing = max(2, round(candidate_size * 0.08))
            widths = [
                candidate_font.render(character, True, self.WHITE).get_width()
                for character in characters
            ]
            total_width = sum(widths) + spacing * (len(characters) - 1)
            if (
                total_width <= maximum_width
                and candidate_font.get_height() <= maximum_height
            ):
                best = (
                    candidate_size,
                    candidate_font,
                    spacing,
                    widths,
                    total_width,
                )
                minimum_size = candidate_size + 1
            else:
                maximum_size = candidate_size - 1

        if best is None:
            candidate_font = self._font_at_size(12)
            widths = [
                candidate_font.render(character, True, self.WHITE).get_width()
                for character in characters
            ]
            best = (
                12,
                candidate_font,
                2,
                widths,
                sum(widths) + 2 * (len(characters) - 1),
            )

        font_size, font, spacing, widths, total_width = best
        text_y = (upper_height - font.get_height()) // 2
        start_x = (self.width - total_width) // 2
        square_size = round((self.height - upper_height) * 0.30)
        square_rect = pygame.Rect(
            (self.width - square_size) // 2,
            upper_height - square_size // 2,
            square_size,
            square_size,
        )
        return {
            "characters": characters,
            "font_size": font_size,
            "font": font,
            "spacing": spacing,
            "widths": widths,
            "start_x": start_x,
            "text_y": text_y,
            "square_size": square_size,
            "square_rect": square_rect,
        }

    def _draw_locked_in_state(
        self,
        layout,
        green_count,
        square_color,
        progress_index=None,
        progress_fraction=0.0,
    ):
        """Draw the large sentence row, optional progress, and lower square."""
        self.screen.fill(self.BLACK)

        if self.play_mode == "progress" and progress_index is not None:
            bar_height = layout["font"].get_height()
            bar_y = layout["text_y"]
            current_x = layout["start_x"]
            for index, width in enumerate(layout["widths"]):
                if index < progress_index:
                    fill_width = width
                elif index == progress_index:
                    fill_width = round(
                        width * max(0.0, min(1.0, progress_fraction))
                    )
                else:
                    fill_width = 0
                if fill_width > 0:
                    pygame.draw.rect(
                        self.screen,
                        self.LIGHT_BROWN,
                        (current_x, bar_y, fill_width, bar_height),
                    )
                current_x += width + layout["spacing"]

        current_x = layout["start_x"]
        for index, character in enumerate(layout["characters"]):
            color = (
                self.GREEN
                if self.play_mode == "green" and index < green_count
                else self.WHITE
            )
            surface = layout["font"].render(character, True, color)
            self.screen.blit(surface, (current_x, layout["text_y"]))
            current_x += layout["widths"][index] + layout["spacing"]
        pygame.draw.rect(self.screen, square_color, layout["square_rect"])

    def _show_for_duration(self, duration, draw_frame):
        """Show a stable phase and return its measured duration."""
        return show_for_duration(
            duration=duration,
            now=self.get_timestamp,
            draw_frame=draw_frame,
            check_exit=self.check_exit_events,
            clock=self.clock,
        )

    def _draw_rest_screen(self):
        """Draw the optional gray fixation cross used between trials."""
        self.screen.fill(self.BLACK)
        if not self.rest_cross_enabled:
            return
        arm_length = round(min(self.width, self.height) * 0.11)
        thickness = max(10, round(min(self.width, self.height) * 0.03))
        draw_cross(
            self.screen,
            self.GRAY,
            center=(self.width // 2, self.height // 2),
            arm_length=arm_length,
            thickness=thickness,
        )

    def check_exit_events(self):
        """Allow button interaction without treating every click as an exit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def _continue_button_rect(self):
        """Return the bottom-right continue-button rectangle."""
        button_width = max(150, min(260, round(self.width * 0.14)))
        button_height = max(54, min(76, round(self.height * 0.075)))
        margin_x = max(24, round(self.width * 0.04))
        margin_y = max(20, round(self.height * 0.04))
        return pygame.Rect(
            self.width - margin_x - button_width,
            self.height - margin_y - button_height,
            button_width,
            button_height,
        )

    def _draw_continue_state(
        self,
        button_rect,
        *,
        label,
        enabled,
        hovered,
        remaining,
    ):
        """Draw the rest background and the interactive continue button."""
        self._draw_rest_screen()

        if not enabled:
            fill_color = (58, 58, 58)
            border_color = (105, 105, 105)
        elif hovered:
            fill_color = (92, 132, 184)
            border_color = (205, 225, 250)
        else:
            fill_color = (65, 92, 128)
            border_color = (155, 180, 212)

        pygame.draw.rect(
            self.screen,
            fill_color,
            button_rect,
            border_radius=12,
        )
        pygame.draw.rect(
            self.screen,
            border_color,
            button_rect,
            width=3,
            border_radius=12,
        )
        label_surface = self.continue_button_font.render(
            label,
            True,
            self.WHITE if enabled else (150, 150, 150),
        )
        self.screen.blit(label_surface, label_surface.get_rect(center=button_rect.center))

        if enabled:
            status_text = "请点击按钮继续"
        else:
            status_text = f"休息 {remaining:.1f} 秒后可点击"
        status_surface = self.continue_button_font.render(
            status_text,
            True,
            (180, 180, 180),
        )
        status_rect = status_surface.get_rect(
            midbottom=(
                button_rect.centerx,
                button_rect.top - max(8, round(self.height * 0.012)),
            )
        )
        self.screen.blit(status_surface, status_rect)

    @staticmethod
    def _set_button_cursor(hovered):
        """Use a hand cursor over the enabled button when supported."""
        cursor = (
            pygame.SYSTEM_CURSOR_HAND
            if hovered
            else pygame.SYSTEM_CURSOR_ARROW
        )
        try:
            pygame.mouse.set_cursor(pygame.Cursor(cursor))
        except pygame.error:
            pass

    def _wait_for_continue(self, rest_duration, *, is_last):
        """Enforce the rest duration, then wait for an explicit button click."""
        rest_started = self.get_timestamp()
        rest_started_abs = self.get_absolute_time()
        button_rect = self._continue_button_rect()
        label = "结束" if is_last else "下一条"
        enabled_onset = None
        enabled_onset_abs = None

        while True:
            now = self.get_timestamp()
            elapsed = now - rest_started
            remaining = max(0.0, rest_duration - elapsed)
            enabled = remaining <= 0
            mouse_position = pygame.mouse.get_pos()
            hovered = enabled and button_rect.collidepoint(mouse_position)

            if enabled and enabled_onset is None:
                enabled_onset = now
                enabled_onset_abs = self.get_absolute_time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._set_button_cursor(False)
                    return False, None
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    self._set_button_cursor(False)
                    return False, None
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and enabled
                    and button_rect.collidepoint(event.pos)
                ):
                    clicked_at = self.get_timestamp()
                    clicked_at_abs = self.get_absolute_time()
                    self._set_button_cursor(False)
                    return True, {
                        "rest_onset": rest_started,
                        "rest_onset_abs": rest_started_abs,
                        "continue_button_enabled": enabled_onset,
                        "continue_button_enabled_abs": enabled_onset_abs,
                        "continue_button_click": clicked_at,
                        "continue_button_click_abs": clicked_at_abs,
                        "actual_rest_duration": clicked_at - rest_started,
                        "continue_wait_after_minimum": max(
                            0.0,
                            clicked_at - rest_started - rest_duration,
                        ),
                    }

            self._set_button_cursor(hovered)
            self._draw_continue_state(
                button_rect,
                label=label,
                enabled=enabled,
                hovered=hovered,
                remaining=remaining,
            )
            pygame.display.flip()
            self.clock.tick(60)

    def display_sentence(
        self,
        sentence,
        trial_id,
        stimulus_index=None,
        repetition=1,
        repetition_trial=None,
        is_last=False,
    ):
        """Run one complete locked-in sentence-reading trial."""
        if stimulus_index is None:
            stimulus_index = trial_id
        if repetition_trial is None:
            repetition_trial = trial_id
        layout = self._sentence_layout(sentence)
        characters = layout["characters"]
        baseline_duration = (
            random.uniform(self.baseline_min, self.baseline_max)
            if trial_id == 1
            else 0.0
        )
        pre_audio_delay = random.uniform(
            self.pre_audio_delay_min,
            self.pre_audio_delay_max,
        )
        silent_delay = random.uniform(
            self.silent_delay_min,
            self.silent_delay_max,
        )
        rest_duration = random.uniform(self.rest_min, self.rest_max)
        trial_data = {
            "trial_id": trial_id,
            "stimulus_index": stimulus_index,
            "repetition": repetition,
            "repetition_trial": repetition_trial,
            "paradigm": "locked_in_sentence_reading",
            "sentence": sentence,
            "prep_mode": "square",
            "play_mode": self.play_mode,
            "token_mode": "character",
            "trial_start": self.get_timestamp(),
            "trial_start_abs": self.get_absolute_time(),
            "planned_baseline_duration": baseline_duration,
            "actual_baseline_duration": None,
            "baseline_applied": trial_id == 1,
            "planned_pre_audio_delay": pre_audio_delay,
            "actual_pre_audio_delay": None,
            "planned_silent_delay": silent_delay,
            "actual_silent_delay": None,
            "planned_rest_duration": rest_duration,
            "actual_rest_duration": None,
            "rest_cross_enabled": self.rest_cross_enabled,
            "continue_required": self.continue_button_enabled,
            "continue_button_label": (
                "结束" if is_last else "下一条"
            )
            if self.continue_button_enabled
            else None,
            "rest_onset": None,
            "rest_onset_abs": None,
            "continue_button_enabled": None,
            "continue_button_enabled_abs": None,
            "continue_button_click": None,
            "continue_button_click_abs": None,
            "continue_wait_after_minimum": None,
            "cue_tone_enabled": self.cue_tone_enabled,
            "cue_volume": self.cue_volume,
            "cue_tone_onset": None,
            "cue_tone_onset_abs": None,
            "character_green_onsets": [],
            "character_green_events": [],
            "character_progress_onsets": [],
            "character_progress_events": [],
            "font_size": layout["font_size"],
            "square_size": layout["square_size"],
            "char_speed": self.char_speed,
            "progress_duration": self.progress_duration,
            "progress_pause": self.progress_pause,
            "final_hold": self.final_hold,
            "word_count": len(characters),
            "token_count": len(characters),
        }

        audio_item = self.sentence_audio[stimulus_index - 1]
        trial_data["audio_id"] = audio_item["id"]
        trial_data["audio_file"] = audio_item["file"]
        trial_data["audio_files"] = audio_item["files"]
        trial_data["audio_segment_count"] = len(audio_item["segments"])
        trial_data["audio_duration"] = audio_item["duration"]

        if baseline_duration > 0:
            baseline_ok, actual_baseline = self._show_for_duration(
                baseline_duration,
                lambda: self.screen.fill(self.BLACK),
            )
            trial_data["actual_baseline_duration"] = actual_baseline
            if not baseline_ok:
                return False
        else:
            trial_data["actual_baseline_duration"] = 0.0

        trial_data["sentence_visible_onset"] = self.get_timestamp()
        trial_data["sentence_visible_onset_abs"] = self.get_absolute_time()
        trial_data["red_square_onset"] = trial_data[
            "sentence_visible_onset"
        ]
        trial_data["red_square_onset_abs"] = trial_data[
            "sentence_visible_onset_abs"
        ]
        lead_ok, actual_pre_audio_delay = self._show_for_duration(
            pre_audio_delay,
            lambda: self._draw_locked_in_state(
                layout,
                green_count=0,
                square_color=self.RED,
            ),
        )
        trial_data["actual_pre_audio_delay"] = actual_pre_audio_delay
        if not lead_ok:
            return False

        if not self._play_sentence_audio(
            audio_item,
            "target",
            trial_data,
            draw_frame=lambda: self._draw_locked_in_state(
                layout,
                green_count=0,
                square_color=self.RED,
            ),
        ):
            return False
        trial_data["pre_audio_onset"] = trial_data["target_audio_onset"]
        trial_data["pre_audio_onset_abs"] = trial_data[
            "target_audio_onset_abs"
        ]
        trial_data["pre_audio_offset"] = trial_data["target_audio_offset"]
        trial_data["pre_audio_offset_abs"] = trial_data[
            "target_audio_offset_abs"
        ]

        trial_data["prep_onset"] = self.get_timestamp()
        trial_data["prep_onset_abs"] = self.get_absolute_time()
        delay_ok, actual_delay = self._show_for_duration(
            silent_delay,
            lambda: self._draw_locked_in_state(
                layout,
                green_count=0,
                square_color=self.RED,
            ),
        )
        trial_data["actual_silent_delay"] = actual_delay
        trial_data["actual_pre_visual_gap"] = actual_delay
        trial_data["prep_offset"] = self.get_timestamp()
        trial_data["prep_offset_abs"] = self.get_absolute_time()
        if not delay_ok:
            return False

        self._draw_locked_in_state(
            layout,
            green_count=1,
            square_color=self.GREEN,
            progress_index=0,
            progress_fraction=0.0,
        )
        cue_channel = None
        if self.cue_sound is not None:
            cue_channel = self.cue_sound.play()
            if cue_channel is None:
                raise RuntimeError("No mixer channel available for cue tone")
        pygame.display.flip()

        prompt_onset = self.get_timestamp()
        prompt_onset_abs = self.get_absolute_time()
        trial_data["square_green_onset"] = prompt_onset
        trial_data["square_green_onset_abs"] = prompt_onset_abs
        trial_data["sentence_onset"] = prompt_onset
        trial_data["sentence_onset_abs"] = prompt_onset_abs
        trial_data["first_character_onset"] = prompt_onset
        trial_data["first_character_onset_abs"] = prompt_onset_abs
        trial_data["first_word_onset"] = prompt_onset
        trial_data["first_word_onset_abs"] = prompt_onset_abs
        if cue_channel is not None:
            trial_data["cue_tone_onset"] = prompt_onset
            trial_data["cue_tone_onset_abs"] = prompt_onset_abs

        character_onsets = [prompt_onset]
        character_events = [
            {
                "index": 1,
                "character": characters[0],
                "onset": prompt_onset,
                "onset_abs": prompt_onset_abs,
            }
        ]

        if self.play_mode == "green":
            for character_index in range(1, len(characters)):
                target_onset = (
                    prompt_onset + character_index * self.char_speed
                )
                while self.get_timestamp() < target_onset:
                    if not self.check_exit_events():
                        return False
                    self.clock.tick(60)

                self._draw_locked_in_state(
                    layout,
                    green_count=character_index + 1,
                    square_color=self.GREEN,
                )
                pygame.display.flip()
                onset = self.get_timestamp()
                onset_abs = self.get_absolute_time()
                character_onsets.append(onset)
                character_events.append(
                    {
                        "index": character_index + 1,
                        "character": characters[character_index],
                        "onset": onset,
                        "onset_abs": onset_abs,
                    }
                )

            trial_data["character_green_onsets"] = character_onsets
            trial_data["character_green_events"] = character_events
            last_character_complete = character_onsets[-1]
            last_character_complete_abs = character_events[-1]["onset_abs"]
        else:
            progress_events = character_events
            for character_index in range(len(characters)):
                if character_index > 0:
                    onset = self.get_timestamp()
                    onset_abs = self.get_absolute_time()
                    character_onsets.append(onset)
                    progress_events.append(
                        {
                            "index": character_index + 1,
                            "character": characters[character_index],
                            "onset": onset,
                            "onset_abs": onset_abs,
                        }
                    )

                progress_started = character_onsets[-1]
                while (
                    self.get_timestamp() - progress_started
                    < self.progress_duration
                ):
                    if not self.check_exit_events():
                        return False
                    elapsed = self.get_timestamp() - progress_started
                    progress_fraction = min(
                        1.0,
                        elapsed / self.progress_duration,
                    )
                    self._draw_locked_in_state(
                        layout,
                        green_count=0,
                        square_color=self.GREEN,
                        progress_index=character_index,
                        progress_fraction=progress_fraction,
                    )
                    pygame.display.flip()
                    self.clock.tick(60)

                self._draw_locked_in_state(
                    layout,
                    green_count=0,
                    square_color=self.GREEN,
                    progress_index=character_index + 1,
                    progress_fraction=0.0,
                )
                pygame.display.flip()
                progress_events[-1]["completion"] = self.get_timestamp()
                progress_events[-1][
                    "completion_abs"
                ] = self.get_absolute_time()

                if (
                    character_index < len(characters) - 1
                    and self.progress_pause > 0
                ):
                    pause_started = self.get_timestamp()
                    while (
                        self.get_timestamp() - pause_started
                        < self.progress_pause
                    ):
                        if not self.check_exit_events():
                            return False
                        self.clock.tick(60)

            trial_data["character_progress_onsets"] = character_onsets
            trial_data["character_progress_events"] = progress_events
            last_character_complete = progress_events[-1]["completion"]
            last_character_complete_abs = progress_events[-1][
                "completion_abs"
            ]
        trial_data["last_character_complete"] = last_character_complete
        trial_data[
            "last_character_complete_abs"
        ] = last_character_complete_abs
        trial_data["sentence_complete"] = last_character_complete
        trial_data["sentence_complete_abs"] = last_character_complete_abs

        hold_ok, actual_hold = self._show_for_duration(
            self.final_hold,
            lambda: self._draw_locked_in_state(
                layout,
                green_count=(
                    len(characters) if self.play_mode == "green" else 0
                ),
                square_color=self.GREEN,
                progress_index=(
                    len(characters)
                    if self.play_mode == "progress"
                    else None
                ),
            ),
        )
        trial_data["actual_final_hold"] = actual_hold
        if not hold_ok:
            return False

        if self.continue_button_enabled:
            rest_ok, rest_events = self._wait_for_continue(
                rest_duration,
                is_last=is_last,
            )
            if not rest_ok:
                return False
            trial_data.update(rest_events)
        else:
            rest_ok, actual_rest = self._show_for_duration(
                rest_duration,
                self._draw_rest_screen,
            )
            trial_data["actual_rest_duration"] = actual_rest
            if not rest_ok:
                return False

        trial_data["trial_end"] = self.get_timestamp()
        trial_data["trial_end_abs"] = self.get_absolute_time()
        self.trials_data.append(trial_data)
        return True

    def _build_trial_schedule(self):
        """Build the presentation schedule, reshuffling each repetition."""
        schedule = []
        for repetition in range(1, self.repetitions + 1):
            stimulus_order = list(range(len(self.sentences)))
            if self.shuffle:
                random.shuffle(stimulus_order)
            for repetition_trial, zero_based_index in enumerate(
                stimulus_order,
                start=1,
            ):
                schedule.append(
                    {
                        "sentence": self.sentences[zero_based_index],
                        "stimulus_index": zero_based_index + 1,
                        "repetition": repetition,
                        "repetition_trial": repetition_trial,
                    }
                )
        return schedule

    def run(self):
        """Run the locked-in paradigm for all configured sentences."""
        schedule = self._build_trial_schedule()
        print(
            f"Loaded {len(self.sentences)} sentences; "
            f"{self.repetitions} repetition(s), {len(schedule)} trials"
        )
        print(f"Shuffle each repetition: {self.shuffle}")
        if self.continue_button_enabled:
            print("Press ESC or close window to quit (mouse clicks advance only via the button)")
        else:
            print("Press ESC, close window, or click mouse to quit")
        print(f"Character speed: {self.char_speed} s/character")
        print(f"Play mode: {self.play_mode}")
        if self.play_mode == "progress":
            print(
                "Progress timing: "
                f"{self.progress_duration} s/character, "
                f"{self.progress_pause} s pause"
            )
        print(
            "Baseline: "
            f"{self.baseline_min}-{self.baseline_max} s; "
            "pre-audio delay: "
            f"{self.pre_audio_delay_min}-{self.pre_audio_delay_max} s; "
            "silent delay: "
            f"{self.silent_delay_min}-{self.silent_delay_max} s; "
            f"rest: {self.rest_min}-{self.rest_max} s"
        )
        print(f"Unified cue tone: {self.cue_tone_enabled}")
        print(f"Gray cross during rest: {self.rest_cross_enabled}")
        print(f"Continue button between trials: {self.continue_button_enabled}")

        try:
            for trial_id, scheduled_trial in enumerate(schedule, start=1):
                print(
                    f"Displaying trial {trial_id}/{len(schedule)} "
                    f"(repetition {scheduled_trial['repetition']}, "
                    f"stimulus {scheduled_trial['stimulus_index']}): "
                    f"{scheduled_trial['sentence']}"
                )
                if not self.display_sentence(
                    scheduled_trial["sentence"],
                    trial_id=trial_id,
                    stimulus_index=scheduled_trial["stimulus_index"],
                    repetition=scheduled_trial["repetition"],
                    repetition_trial=scheduled_trial["repetition_trial"],
                    is_last=trial_id == len(schedule),
                ):
                    break
        finally:
            self.save_data()
            self.cleanup()
