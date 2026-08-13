"""Self-contained speech + movement synchronization paradigm.

This module is intentionally standalone: it has no dependency on the
``experiment_paradigm`` package. A colleague only needs ``pygame`` plus the
files in this folder to run the paradigm.

Trial flow (all durations in seconds):

1. Baseline -- black screen, first trial only.
2. Preparation -- the Chinese numeral (left) and its gesture image (right)
   are shown with a RED go-cue bar at the bottom.
3. Go cue -- the bar turns GREEN (optionally with a short tone); the
   participant simultaneously says the numeral and performs the gesture.
4. Response window -- stimulus + green bar held for analysis.
5. Rest -- timed or an explicit "下一条/结束" button, like the locked-in
   paradigm.

Timestamps for every phase are written to ``timestamp/`` as paired CSV/JSON.
"""

from __future__ import annotations

import csv
import json
import math
import random
import struct
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pygame

# --------------------------------------------------------------------------
# Colors
# --------------------------------------------------------------------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)

# Default numeral set paired one-to-one with gestures/01.png..10.png.
DEFAULT_CHARACTERS = list("一二三四五六七八九十")

# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------
CJK_FONT_PATHS = (
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)


def load_cjk_font(font_size: int, *, announce: bool = True) -> pygame.font.Font:
    """Load a CJK-capable font, falling back to Pygame's default."""
    for font_path in CJK_FONT_PATHS:
        try:
            font = pygame.font.Font(font_path, font_size)
            if announce:
                print(f"Successfully loaded font: {font_path}")
            return font
        except (FileNotFoundError, OSError, pygame.error):
            continue
    if announce:
        print("Warning: Could not load system font. Using default font.")
    return pygame.font.Font(None, font_size)


# --------------------------------------------------------------------------
# Drawing / timing helpers
# --------------------------------------------------------------------------
def draw_cross(
    screen: pygame.Surface,
    color: tuple[int, int, int],
    *,
    center: tuple[int, int],
    arm_length: int,
    thickness: int,
) -> None:
    """Draw a centered rectangular fixation cross."""
    center_x, center_y = center
    pygame.draw.rect(
        screen,
        color,
        (
            center_x - arm_length,
            center_y - thickness // 2,
            arm_length * 2,
            thickness,
        ),
    )
    pygame.draw.rect(
        screen,
        color,
        (
            center_x - thickness // 2,
            center_y - arm_length,
            thickness,
            arm_length * 2,
        ),
    )


def validate_duration_range(name: str, minimum: float, maximum: float) -> None:
    """Validate a non-negative inclusive duration range."""
    if minimum < 0 or maximum < 0:
        raise ValueError(f"{name} durations must be non-negative")
    if minimum > maximum:
        raise ValueError(f"{name} minimum must not be greater than maximum")


def show_for_duration(
    *,
    duration: float,
    now: Callable[[], float],
    draw_frame: Callable[[], None],
    check_exit: Callable[[], bool],
    clock: pygame.time.Clock,
) -> tuple[bool, float]:
    """Draw a stable phase for a duration while remaining interruptible."""
    started_at = now()
    draw_frame()
    pygame.display.flip()
    while now() - started_at < duration:
        if not check_exit():
            return False, now() - started_at
        draw_frame()
        pygame.display.flip()
        clock.tick(60)
    return True, now() - started_at


# --------------------------------------------------------------------------
# Result persistence
# --------------------------------------------------------------------------
def write_csv(path: Path, trials: list[dict[str, Any]]) -> None:
    """Write trial rows using the first row's stable field order."""
    if not trials:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trials[0].keys()))
        writer.writeheader()
        writer.writerows(trials)


def write_json(
    path: Path,
    *,
    experiment_start: str,
    trials: list[dict[str, Any]],
) -> None:
    """Write the paired structured result file."""
    payload = {
        "experiment_start": experiment_start,
        "total_trials": len(trials),
        "trials": trials,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def write_run_results(
    *,
    trials: list[dict[str, Any]],
    output_prefix: str,
    experiment_start: str,
    output_dir: Path,
) -> tuple[Path, Path] | None:
    """Write paired timestamped CSV/JSON results and return their paths."""
    if not trials:
        print("No data to save.")
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"{output_prefix}_{stamp}.csv"
    json_path = output_dir / f"{output_prefix}_{stamp}.json"
    write_csv(csv_path, trials)
    write_json(json_path, experiment_start=experiment_start, trials=trials)
    return csv_path, json_path


# --------------------------------------------------------------------------
# Base pygame lifecycle
# --------------------------------------------------------------------------
class _ParadigmBase:
    """Minimal fullscreen lifecycle shared by the standalone paradigm."""

    def __init__(
        self,
        caption="Paradigm",
        output_prefix="speech_motor_sync",
        output_dir=None,
        display_mode="borderless",
    ):
        if display_mode not in ("borderless", "exclusive"):
            raise ValueError("display_mode must be 'borderless' or 'exclusive'")

        pygame.init()
        if display_mode == "borderless":
            desktop_size = pygame.display.get_desktop_sizes()[0]
            self.screen = pygame.display.set_mode(desktop_size, pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        self.display_mode = display_mode
        pygame.display.set_caption(caption)

        self.clock = pygame.time.Clock()

        self.experiment_start_time = time.perf_counter()
        self.experiment_start_datetime = datetime.now()
        self.experiment_start_datetime_iso = (
            self.experiment_start_datetime.isoformat()
        )
        self.trials_data: list[dict[str, Any]] = []
        self.output_prefix = output_prefix
        self.output_dir = Path(output_dir) if output_dir else (
            Path(__file__).resolve().parent / "timestamp"
        )

    # -- timing -----------------------------------------------------------
    def get_timestamp(self) -> float:
        return time.perf_counter() - self.experiment_start_time

    def get_absolute_time(self) -> str:
        return datetime.now().isoformat()

    # -- persistence ------------------------------------------------------
    def save_data(self) -> None:
        paths = write_run_results(
            trials=self.trials_data,
            output_prefix=self.output_prefix,
            experiment_start=self.experiment_start_datetime_iso,
            output_dir=self.output_dir,
        )
        if paths is None:
            return
        csv_filename, json_filename = paths
        print("\nData saved:")
        print(f"  CSV:  {csv_filename}")
        print(f"  JSON: {json_filename}")

    # -- events -----------------------------------------------------------
    def check_exit_events(self) -> bool:
        """ESC / window-close exit; mouse clicks advance only via the button."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def cleanup(self) -> None:
        pygame.quit()


# --------------------------------------------------------------------------
# Speech + movement synchronization paradigm
# --------------------------------------------------------------------------
class SpeechMotorSyncParadigm(_ParadigmBase):
    """Present a numeral + gesture, then a red-to-green go-cue bar."""

    def __init__(
        self,
        stimuli_file=None,
        characters=None,
        gestures_dir="gestures",
        baseline_min=1.5,
        baseline_max=2.5,
        prep_min=1.5,
        prep_max=2.0,
        response_duration=2.0,
        rest_min=5.0,
        rest_max=6.0,
        rest_cross=True,
        cue_tone=True,
        cue_frequency=1000,
        cue_duration=0.08,
        cue_volume=0.7,
        repetitions=1,
        shuffle=True,
        continue_button=True,
        show_continue_countdown=False,
        font_size=300,
        output_prefix="speech_motor_sync",
        output_dir=None,
        display_mode="borderless",
    ):
        """Initialize the speech + movement synchronization paradigm."""
        validate_duration_range("baseline", baseline_min, baseline_max)
        validate_duration_range("prep", prep_min, prep_max)
        validate_duration_range("rest", rest_min, rest_max)
        if response_duration < 0:
            raise ValueError("response_duration must be non-negative")
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

        if characters is None:
            characters = self._read_stimuli(stimuli_file)
        else:
            characters = list(characters)
        if not characters:
            raise ValueError("No stimulus characters available")

        super().__init__(
            caption="Speech + Movement Sync Paradigm",
            output_prefix=output_prefix,
            output_dir=output_dir,
            display_mode=display_mode,
        )

        self.characters = characters
        self.gestures_dir = Path(gestures_dir)
        self.baseline_min = baseline_min
        self.baseline_max = baseline_max
        self.prep_min = prep_min
        self.prep_max = prep_max
        self.response_duration = response_duration
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
        self.show_continue_countdown = show_continue_countdown
        self.max_font_size = font_size

        self._compute_layout()
        self._char_cache: dict[str, tuple[pygame.Surface, int]] = {}
        self.gestures = self._load_gestures(len(self.characters))

        if self.cue_tone_enabled:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=44100, size=-16, channels=2, buffer=512
                )
            self.cue_sound = self._create_cue_sound()
        else:
            self.cue_sound = None

        button_font_size = max(18, min(32, round(self.height * 0.035)))
        self.continue_button_font = load_cjk_font(
            button_font_size, announce=False
        )

    # -- stimuli ----------------------------------------------------------
    @staticmethod
    def _read_stimuli(stimuli_file):
        if stimuli_file is None:
            return list(DEFAULT_CHARACTERS)
        with Path(stimuli_file).open("r", encoding="utf-8") as handle:
            return [
                line.strip()
                for line in handle
                if line.strip()
            ]

    # -- layout -----------------------------------------------------------
    def _compute_layout(self):
        """Precompute the on-screen regions for text, gesture, and go-cue bar."""
        self.bar_height = max(60, round(self.height * 0.07))
        bar_margin_x = round(self.width * 0.10)
        bar_margin_bottom = round(self.height * 0.05)
        self.bar_rect = pygame.Rect(
            bar_margin_x,
            self.height - bar_margin_bottom - self.bar_height,
            self.width - 2 * bar_margin_x,
            self.bar_height,
        )
        self.bar_radius = max(6, round(self.bar_height * 0.18))

        content_top = round(self.height * 0.08)
        content_bottom = self.bar_rect.top - round(self.height * 0.04)
        self.content_center_y = (content_top + content_bottom) // 2
        content_height = max(120, content_bottom - content_top)

        self.left_center_x = round(self.width * 0.28)
        self.right_center_x = round(self.width * 0.72)
        self.left_box = (round(self.width * 0.40), content_height)
        self.gesture_box = (round(self.width * 0.40), content_height)

    def _fit_font(self, text, max_w, max_h, cap):
        """Binary-search the largest font size that fits one glyph in a box."""
        lo, hi = 12, max(12, cap)
        best_font = None
        best_size = 12
        while lo <= hi:
            mid = (lo + hi) // 2
            font = load_cjk_font(mid, announce=False)
            surface = font.render(text, True, WHITE)
            if (
                surface.get_width() <= max_w
                and surface.get_height() <= max_h
            ):
                best_font, best_size = font, mid
                lo = mid + 1
            else:
                hi = mid - 1
        if best_font is None:
            best_font = load_cjk_font(12, announce=False)
            best_size = 12
        return best_font, best_size

    def _char_surface(self, char):
        """Return a cached rendered numeral surface and its font size."""
        cached = self._char_cache.get(char)
        if cached is not None:
            return cached
        font, size = self._fit_font(
            char, self.left_box[0], self.left_box[1], self.max_font_size
        )
        surface = font.render(char, True, WHITE)
        self._char_cache[char] = (surface, size)
        return surface, size

    # -- gesture images ---------------------------------------------------
    def _scale_to_box(self, surface):
        """Scale an image to fit the gesture box, preserving aspect ratio."""
        w, h = surface.get_size()
        max_w, max_h = self.gesture_box
        scale = min(max_w / w, max_h / h)
        if abs(scale - 1.0) > 1e-3:
            surface = pygame.transform.smoothscale(
                surface,
                (max(1, round(w * scale)), max(1, round(h * scale))),
            )
        return surface

    def _make_placeholder_surface(self, index):
        """Draw an on-the-fly placeholder card when no gesture image exists."""
        w, h = self.gesture_box
        surface = pygame.Surface((w, h))
        surface.fill((238, 240, 246))
        pygame.draw.rect(
            surface,
            (80, 110, 170),
            surface.get_rect(),
            width=max(4, round(min(w, h) * 0.02)),
            border_radius=round(min(w, h) * 0.05),
        )
        big = load_cjk_font(round(min(w, h) * 0.34), announce=False)
        digit = load_cjk_font(round(min(w, h) * 0.16), announce=False)
        label = load_cjk_font(round(min(w, h) * 0.07), announce=False)
        cn = DEFAULT_CHARACTERS[index - 1]
        cn_surf = big.render(cn, True, (40, 60, 110))
        surface.blit(
            cn_surf, cn_surf.get_rect(center=(w // 2, round(h * 0.40)))
        )
        dig_surf = digit.render(str(index), True, (90, 90, 90))
        surface.blit(
            dig_surf, dig_surf.get_rect(center=(w // 2, round(h * 0.66)))
        )
        label_surf = label.render(
            f"手势占位图 {index:02d} · 替换为真实照片",
            True,
            (120, 120, 120),
        )
        surface.blit(
            label_surf,
            label_surf.get_rect(center=(w // 2, round(h * 0.85))),
        )
        return surface.convert()

    def _find_gesture_file(self, index):
        """Return the gesture image path for ``index``, or None.

        Accepts ``.jpg``/``.jpeg``/``.png`` (any case). Real photos (jpg/jpeg)
        are preferred over generated ``.png`` icons when both exist; the
        zero-padded name (``01``) is preferred over the bare number (``1``).
        """
        stems = (f"{index:02d}", str(index))
        for ext in ("jpg", "jpeg", "png"):
            for stem in stems:
                for name in (f"{stem}.{ext}", f"{stem}.{ext.upper()}"):
                    candidate = self.gestures_dir / name
                    if candidate.is_file():
                        return candidate
        return None

    def _load_gestures(self, count):
        """Preload one gesture image per stimulus, with placeholder fallback."""
        items = {}
        for index in range(1, count + 1):
            path = self._find_gesture_file(index)
            if path is None:
                items[index] = {
                    "surface": self._make_placeholder_surface(index),
                    "file": None,
                    "placeholder": True,
                }
                print(
                    f"Gesture {index:02d}: image missing, "
                    "using on-the-fly placeholder"
                )
            else:
                try:
                    raw = pygame.image.load(str(path)).convert_alpha()
                except pygame.error as error:
                    raise ValueError(
                        f"Could not decode gesture image: {path}"
                    ) from error
                items[index] = {
                    "surface": self._scale_to_box(raw),
                    "file": path.name,
                    "placeholder": False,
                }
                print(f"Gesture {index:02d}: loaded {path.name}")
        return items

    # -- cue tone ---------------------------------------------------------
    def _create_cue_sound(self):
        """Create the short, category-neutral go-cue tone."""
        mixer_config = pygame.mixer.get_init()
        if mixer_config is None:
            raise RuntimeError("Pygame mixer is not initialized")

        sample_rate, sample_format, channels = mixer_config
        if abs(sample_format) != 16:
            raise RuntimeError("Cue tone generation requires a 16-bit mixer")

        frame_count = max(1, round(sample_rate * self.cue_duration))
        fade_frames = max(
            1, min(frame_count // 2, round(sample_rate * 0.005))
        )
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
            encoded = struct.pack("<h", sample)
            pcm.extend(encoded * channels)
        return pygame.mixer.Sound(buffer=bytes(pcm))

    # -- drawing ----------------------------------------------------------
    def _draw_trial_state(self, char_surface, gesture_surface, bar_color):
        """Draw numeral (left), gesture (right), and the go-cue bar (bottom)."""
        self.screen.fill(BLACK)
        self.screen.blit(
            char_surface,
            char_surface.get_rect(
                center=(self.left_center_x, self.content_center_y)
            ),
        )
        self.screen.blit(
            gesture_surface,
            gesture_surface.get_rect(
                center=(self.right_center_x, self.content_center_y)
            ),
        )
        pygame.draw.rect(
            self.screen, bar_color, self.bar_rect, border_radius=self.bar_radius
        )

    def _draw_rest_screen(self):
        """Draw the optional gray fixation cross used between trials."""
        self.screen.fill(BLACK)
        if not self.rest_cross_enabled:
            return
        arm_length = round(min(self.width, self.height) * 0.11)
        thickness = max(10, round(min(self.width, self.height) * 0.03))
        draw_cross(
            self.screen,
            GRAY,
            center=(self.width // 2, self.height // 2),
            arm_length=arm_length,
            thickness=thickness,
        )

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
        self, button_rect, *, label, enabled, hovered, remaining
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
            self.screen, fill_color, button_rect, border_radius=12
        )
        pygame.draw.rect(
            self.screen,
            border_color,
            button_rect,
            width=3,
            border_radius=12,
        )
        label_surface = self.continue_button_font.render(
            label, True, WHITE if enabled else (150, 150, 150)
        )
        self.screen.blit(
            label_surface,
            label_surface.get_rect(center=button_rect.center),
        )

        if self.show_continue_countdown:
            status = "请点击按钮继续" if enabled else f"休息 {remaining:.1f} 秒后可点击"
            status_surface = self.continue_button_font.render(
                status, True, (180, 180, 180)
            )
            self.screen.blit(
                status_surface,
                status_surface.get_rect(
                    midbottom=(
                        button_rect.centerx,
                        button_rect.top
                        - max(8, round(self.height * 0.012)),
                    )
                ),
            )

    @staticmethod
    def _set_button_cursor(hovered):
        """Use a hand cursor over the enabled button when supported."""
        cursor = (
            pygame.SYSTEM_CURSOR_HAND if hovered else pygame.SYSTEM_CURSOR_ARROW
        )
        try:
            pygame.mouse.set_cursor(pygame.Cursor(cursor))
        except pygame.error:
            pass

    # -- rest handling ----------------------------------------------------
    def _show_for_duration(self, duration, draw_frame):
        """Show a stable phase and return its measured duration."""
        return show_for_duration(
            duration=duration,
            now=self.get_timestamp,
            draw_frame=draw_frame,
            check_exit=self.check_exit_events,
            clock=self.clock,
        )

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
                            0.0, clicked_at - rest_started - rest_duration
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

    # -- schedule ---------------------------------------------------------
    def _build_trial_schedule(self):
        """Build the presentation schedule, reshuffling each repetition."""
        schedule = []
        for repetition in range(1, self.repetitions + 1):
            order = list(range(len(self.characters)))
            if self.shuffle:
                random.shuffle(order)
            for repetition_trial, zero_based in enumerate(order, start=1):
                schedule.append(
                    {
                        "character": self.characters[zero_based],
                        "stimulus_index": zero_based + 1,
                        "repetition": repetition,
                        "repetition_trial": repetition_trial,
                    }
                )
        return schedule

    # -- one trial --------------------------------------------------------
    def display_trial(
        self,
        character,
        stimulus_index,
        trial_id,
        repetition,
        repetition_trial,
        is_first,
        is_last,
    ):
        """Run one complete speech + movement synchronization trial."""
        char_surface, font_size = self._char_surface(character)
        gesture = self.gestures[stimulus_index]
        gesture_surface = gesture["surface"]

        baseline_duration = (
            random.uniform(self.baseline_min, self.baseline_max)
            if is_first
            else 0.0
        )
        prep_duration = random.uniform(self.prep_min, self.prep_max)
        rest_duration = random.uniform(self.rest_min, self.rest_max)

        trial_data = {
            "trial_id": trial_id,
            "stimulus_index": stimulus_index,
            "repetition": repetition,
            "repetition_trial": repetition_trial,
            "paradigm": "speech_motor_sync",
            "character": character,
            "gesture_file": gesture["file"],
            "gesture_placeholder": gesture["placeholder"],
            "trial_start": self.get_timestamp(),
            "trial_start_abs": self.get_absolute_time(),
            "planned_baseline_duration": baseline_duration,
            "actual_baseline_duration": None,
            "baseline_applied": is_first,
            "planned_prep_duration": prep_duration,
            "actual_prep_duration": None,
            "prep_onset": None,
            "prep_onset_abs": None,
            "prep_offset": None,
            "prep_offset_abs": None,
            "response_duration_planned": self.response_duration,
            "actual_response_duration": None,
            "go_onset": None,
            "go_onset_abs": None,
            "response_offset": None,
            "response_offset_abs": None,
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
            "font_size": font_size,
            "bar_x": self.bar_rect.x,
            "bar_y": self.bar_rect.y,
            "bar_width": self.bar_rect.width,
            "bar_height": self.bar_rect.height,
            "display_width": self.width,
            "display_height": self.height,
        }

        # 1. Baseline (first trial only): black screen.
        if baseline_duration > 0:
            baseline_ok, actual_baseline = self._show_for_duration(
                baseline_duration, lambda: self.screen.fill(BLACK)
            )
            trial_data["actual_baseline_duration"] = actual_baseline
            if not baseline_ok:
                return False
        else:
            trial_data["actual_baseline_duration"] = 0.0

        # 2. Preparation: numeral + gesture + RED bar.
        trial_data["prep_onset"] = self.get_timestamp()
        trial_data["prep_onset_abs"] = self.get_absolute_time()
        prep_ok, actual_prep = self._show_for_duration(
            prep_duration,
            lambda: self._draw_trial_state(
                char_surface, gesture_surface, RED
            ),
        )
        trial_data["actual_prep_duration"] = actual_prep
        trial_data["prep_offset"] = self.get_timestamp()
        trial_data["prep_offset_abs"] = self.get_absolute_time()
        if not prep_ok:
            return False

        # 3. Go cue: bar turns GREEN (+ optional tone). Speech + movement
        #    onset is read off this timestamp by downstream analysis.
        self._draw_trial_state(char_surface, gesture_surface, GREEN)
        cue_channel = None
        if self.cue_sound is not None:
            cue_channel = self.cue_sound.play()
            if cue_channel is None:
                raise RuntimeError("No mixer channel available for cue tone")
        pygame.display.flip()

        go_onset = self.get_timestamp()
        go_onset_abs = self.get_absolute_time()
        trial_data["go_onset"] = go_onset
        trial_data["go_onset_abs"] = go_onset_abs
        if cue_channel is not None:
            trial_data["cue_tone_onset"] = go_onset
            trial_data["cue_tone_onset_abs"] = go_onset_abs

        # 4. Response window: hold stimulus + GREEN bar.
        response_ok, actual_response = self._show_for_duration(
            self.response_duration,
            lambda: self._draw_trial_state(
                char_surface, gesture_surface, GREEN
            ),
        )
        trial_data["actual_response_duration"] = actual_response
        trial_data["response_offset"] = self.get_timestamp()
        trial_data["response_offset_abs"] = self.get_absolute_time()
        if not response_ok:
            return False

        # 5. Rest: explicit continue button or timed black/fixation screen.
        if self.continue_button_enabled:
            rest_ok, rest_events = self._wait_for_continue(
                rest_duration, is_last=is_last
            )
            if not rest_ok:
                return False
            trial_data.update(rest_events)
        else:
            rest_ok, actual_rest = self._show_for_duration(
                rest_duration, self._draw_rest_screen
            )
            trial_data["actual_rest_duration"] = actual_rest
            if not rest_ok:
                return False

        trial_data["trial_end"] = self.get_timestamp()
        trial_data["trial_end_abs"] = self.get_absolute_time()
        self.trials_data.append(trial_data)
        return True

    # -- run --------------------------------------------------------------
    def run(self):
        """Run the paradigm for all configured stimuli and repetitions."""
        schedule = self._build_trial_schedule()
        print(
            f"Loaded {len(self.characters)} stimuli; "
            f"{self.repetitions} repetition(s), {len(schedule)} trials"
        )
        print(f"Shuffle each repetition: {self.shuffle}")
        if self.continue_button_enabled:
            print(
                "Press ESC or close window to quit "
                "(mouse clicks advance only via the button)"
            )
        else:
            print("Press ESC or close window to quit")
        print(
            "Prep: "
            f"{self.prep_min}-{self.prep_max} s; "
            f"response: {self.response_duration} s; "
            f"rest: {self.rest_min}-{self.rest_max} s"
        )
        print(f"Go-cue tone: {self.cue_tone_enabled}")
        print(f"Gray cross during rest: {self.rest_cross_enabled}")
        print(f"Continue button between trials: {self.continue_button_enabled}")

        try:
            for trial_id, scheduled in enumerate(schedule, start=1):
                print(
                    f"Displaying trial {trial_id}/{len(schedule)} "
                    f"(repetition {scheduled['repetition']}, "
                    f"stimulus {scheduled['stimulus_index']}): "
                    f"{scheduled['character']}"
                )
                if not self.display_trial(
                    scheduled["character"],
                    stimulus_index=scheduled["stimulus_index"],
                    trial_id=trial_id,
                    repetition=scheduled["repetition"],
                    repetition_trial=scheduled["repetition_trial"],
                    is_first=trial_id == 1,
                    is_last=trial_id == len(schedule),
                ):
                    break
        finally:
            self.save_data()
            self.cleanup()
