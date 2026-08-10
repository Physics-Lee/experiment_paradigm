"""Passive patient relaxation paradigm with spoken news."""

import random
from pathlib import Path

import pygame

from ..core import (
    draw_cross,
    load_cjk_font,
    show_for_duration,
    validate_duration_range,
)
from ..stimuli import read_news_items
from .sentence import SentenceParadigm


class RelaxingNewsParadigm(SentenceParadigm):
    """Read news aloud with stable text and manually advanced rests."""

    def __init__(
        self,
        news_file,
        audio_manifest,
        font_size=40,
        square_size=100,
        pre_audio_delay=0.5,
        post_audio_hold=1.0,
        rest_min=5.0,
        rest_max=6.0,
        rest_screen="news",
        gesture_hint=False,
        output_prefix="relaxing_news",
        display_mode="borderless",
    ):
        """Initialize the news relaxation paradigm."""
        if font_size < 12:
            raise ValueError("font_size must be at least 12")
        if square_size < 1:
            raise ValueError("square_size must be positive")
        if pre_audio_delay < 0:
            raise ValueError("pre_audio_delay must be non-negative")
        if post_audio_hold < 0:
            raise ValueError("post_audio_hold must be non-negative")
        if rest_screen not in ("news", "cross"):
            raise ValueError("rest_screen must be 'news' or 'cross'")
        self._validate_duration_range("rest", rest_min, rest_max)

        news_path = Path(news_file)
        news_items = read_news_items(news_path)
        if not news_items:
            raise ValueError(f"No news items found in {news_path}")

        super().__init__(
            sentences_file=str(news_path),
            audio_manifest=audio_manifest,
            play_audio_before=True,
            play_audio_after=False,
            audio_screen="black",
            token_mode="character",
            output_prefix=output_prefix,
            sentences=news_items,
            display_mode=display_mode,
        )
        pygame.display.set_caption("Relaxing News")
        self.news_file = str(news_path)
        self.news_font_size = font_size
        self.news_square_size = square_size
        self.pre_audio_delay = pre_audio_delay
        self.post_audio_hold = post_audio_hold
        self.rest_min = rest_min
        self.rest_max = rest_max
        self.rest_screen = rest_screen
        self.gesture_hint = gesture_hint
        self.gesture_hint_font = load_cjk_font(60, announce=False)
        button_font_size = max(18, min(32, round(self.height * 0.035)))
        self.continue_button_font = load_cjk_font(
            button_font_size,
            announce=False,
        )

    @staticmethod
    def _validate_duration_range(name, minimum, maximum):
        validate_duration_range(name, minimum, maximum)

    def _font_at_size(self, font_size):
        """Load a CJK-capable regular font at the requested size."""
        return load_cjk_font(font_size, announce=False)

    @staticmethod
    def _wrap_text(text, font, maximum_width):
        """Wrap mixed Chinese/Latin text without changing displayed content."""
        lines = []
        current = ""
        for character in text:
            if character == "\n":
                lines.append(current)
                current = ""
                continue
            candidate = current + character
            if current and font.size(candidate)[0] > maximum_width:
                lines.append(current)
                current = character
            else:
                current = candidate
        if current or not lines:
            lines.append(current)
        return lines

    def _news_layout(self, text):
        """Fit wrapped news text above a compact lower red square."""
        maximum_width = round(self.width * 0.82)
        maximum_text_height = round(self.height * 0.56)
        font_size = self.news_font_size

        while font_size >= 12:
            font = self._font_at_size(font_size)
            lines = self._wrap_text(text, font, maximum_width)
            line_gap = max(4, round(font_size * 0.35))
            total_height = (
                len(lines) * font.get_height()
                + max(0, len(lines) - 1) * line_gap
            )
            if total_height <= maximum_text_height:
                break
            font_size -= 1
        else:
            raise ValueError("News text cannot fit on screen")

        rendered_lines = [font.render(line, True, self.WHITE) for line in lines]
        text_top = max(
            round(self.height * 0.08),
            round(self.height * 0.36 - total_height / 2),
        )
        square_size = min(
            self.news_square_size,
            round(min(self.width, self.height) * 0.18),
        )
        square_rect = pygame.Rect(
            (self.width - square_size) // 2,
            round(self.height * 0.76 - square_size / 2),
            square_size,
            square_size,
        )
        return {
            "font_size": font_size,
            "font": font,
            "lines": lines,
            "rendered_lines": rendered_lines,
            "line_gap": line_gap,
            "text_top": text_top,
            "text_height": total_height,
            "square_size": square_size,
            "square_rect": square_rect,
        }

    def _draw_news_state(self, layout):
        """Draw white wrapped news text and the always-red square."""
        self.screen.fill(self.BLACK)
        y_position = layout["text_top"]
        for surface in layout["rendered_lines"]:
            self.screen.blit(
                surface,
                ((self.width - surface.get_width()) // 2, y_position),
            )
            y_position += surface.get_height() + layout["line_gap"]
        pygame.draw.rect(self.screen, self.RED, layout["square_rect"])

        if self.gesture_hint:
            hint_text = "左手握拳-是，摇头-否，左手张开-跳过"
            hint_surface = self.gesture_hint_font.render(
                hint_text,
                True,
                self.WHITE,
            )
            self.screen.blit(
                hint_surface,
                hint_surface.get_rect(
                    midtop=(
                        self.width // 2,
                        layout["square_rect"].bottom
                        + max(12, round(self.height * 0.02)),
                    )
                ),
            )

    def _draw_rest_screen(self):
        """Draw the centered small gray cross directly between news items."""
        self.screen.fill(self.BLACK)
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
        layout,
        button_rect,
        *,
        label,
        enabled,
        hovered,
        remaining,
    ):
        """Draw the selected rest background and interactive button."""
        if self.rest_screen == "news":
            self._draw_news_state(layout)
        else:
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

    def _wait_for_continue(self, layout, rest_duration, *, is_last):
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
                layout,
                button_rect,
                label=label,
                enabled=enabled,
                hovered=hovered,
                remaining=remaining,
            )
            pygame.display.flip()
            self.clock.tick(60)

    def _show_for_duration(self, duration, draw_frame):
        """Display one stable phase while checking for an early exit."""
        return show_for_duration(
            duration=duration,
            now=self.get_timestamp,
            draw_frame=draw_frame,
            check_exit=self.check_exit_events,
            clock=self.clock,
        )

    def display_news(self, text, trial_id, *, is_last=False):
        """Present and read one news item, then require manual continuation."""
        layout = self._news_layout(text)
        rest_duration = random.uniform(self.rest_min, self.rest_max)
        trial_data = {
            "trial_id": trial_id,
            "paradigm": "relaxing_news",
            "news_text": text,
            "trial_start": self.get_timestamp(),
            "trial_start_abs": self.get_absolute_time(),
            "font_size": layout["font_size"],
            "square_size": layout["square_size"],
            "square_color": "red",
            "planned_pre_audio_delay": self.pre_audio_delay,
            "actual_pre_audio_delay": None,
            "planned_post_audio_hold": self.post_audio_hold,
            "actual_post_audio_hold": None,
            "planned_rest_duration": rest_duration,
            "actual_rest_duration": None,
            "rest_screen": self.rest_screen,
            "rest_cross_enabled": self.rest_screen == "cross",
            "continue_required": True,
            "continue_button_label": "结束" if is_last else "下一条",
            "rest_onset": None,
            "rest_onset_abs": None,
            "continue_button_enabled": None,
            "continue_button_enabled_abs": None,
            "continue_button_click": None,
            "continue_button_click_abs": None,
            "continue_wait_after_minimum": None,
        }

        audio_item = self.sentence_audio[trial_id - 1]
        trial_data["audio_id"] = audio_item["id"]
        trial_data["audio_file"] = audio_item["file"]
        trial_data["audio_files"] = audio_item["files"]
        trial_data["audio_segment_count"] = len(audio_item["segments"])
        trial_data["audio_duration"] = audio_item["duration"]

        trial_data["news_visible_onset"] = self.get_timestamp()
        trial_data["news_visible_onset_abs"] = self.get_absolute_time()
        trial_data["red_square_onset"] = trial_data["news_visible_onset"]
        trial_data["red_square_onset_abs"] = trial_data[
            "news_visible_onset_abs"
        ]
        delay_ok, actual_delay = self._show_for_duration(
            self.pre_audio_delay,
            lambda: self._draw_news_state(layout),
        )
        trial_data["actual_pre_audio_delay"] = actual_delay
        if not delay_ok:
            return False

        if not self._play_sentence_audio(
            audio_item,
            "news",
            trial_data,
            draw_frame=lambda: self._draw_news_state(layout),
        ):
            return False

        hold_ok, actual_hold = self._show_for_duration(
            self.post_audio_hold,
            lambda: self._draw_news_state(layout),
        )
        trial_data["actual_post_audio_hold"] = actual_hold
        if not hold_ok:
            return False

        rest_ok, rest_events = self._wait_for_continue(
            layout,
            rest_duration,
            is_last=is_last,
        )
        if not rest_ok:
            return False
        trial_data.update(rest_events)

        trial_data["trial_end"] = self.get_timestamp()
        trial_data["trial_end_abs"] = self.get_absolute_time()
        self.trials_data.append(trial_data)
        return True

    def run(self):
        """Run the ordered relaxing-news playlist once."""
        print(f"Loaded {len(self.sentences)} news items")
        print("Press ESC to quit; click the continue button between news items")
        print(
            f"Text size: {self.news_font_size}px; "
            f"red square: {self.news_square_size}px"
        )
        print(
            f"Pre-audio delay: {self.pre_audio_delay}s; "
            f"post-audio hold: {self.post_audio_hold}s; "
            f"rest: {self.rest_min}-{self.rest_max}s; "
            f"rest screen: {self.rest_screen}; manual continue: True"
        )

        try:
            for trial_id, text in enumerate(self.sentences, start=1):
                print(
                    f"Presenting news {trial_id}/{len(self.sentences)}: {text}"
                )
                if not self.display_news(
                    text,
                    trial_id,
                    is_last=trial_id == len(self.sentences),
                ):
                    break
            print("Relaxing news paradigm completed!")
        finally:
            pygame.mixer.quit()
            self.save_data()
            self.cleanup()
