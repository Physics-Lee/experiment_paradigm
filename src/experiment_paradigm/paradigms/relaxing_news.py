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
    """Read news aloud with stable text, a red square, and gray-cross rests."""

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
        output_prefix="relaxing_news",
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
        )
        pygame.display.set_caption("Relaxing News")
        self.news_file = str(news_path)
        self.news_font_size = font_size
        self.news_square_size = square_size
        self.pre_audio_delay = pre_audio_delay
        self.post_audio_hold = post_audio_hold
        self.rest_min = rest_min
        self.rest_max = rest_max

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

    def _show_for_duration(self, duration, draw_frame):
        """Display one stable phase while checking for an early exit."""
        return show_for_duration(
            duration=duration,
            now=self.get_timestamp,
            draw_frame=draw_frame,
            check_exit=self.check_exit_events,
            clock=self.clock,
        )

    def display_news(self, text, trial_id):
        """Present and read one news item, then show the gray-cross rest."""
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
            "rest_cross_enabled": True,
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

    def run(self):
        """Run the ordered relaxing-news playlist once."""
        print(f"Loaded {len(self.sentences)} news items")
        print("Press ESC or click mouse to quit")
        print(
            f"Text size: {self.news_font_size}px; "
            f"red square: {self.news_square_size}px"
        )
        print(
            f"Pre-audio delay: {self.pre_audio_delay}s; "
            f"post-audio hold: {self.post_audio_hold}s; "
            f"gray-cross rest: {self.rest_min}-{self.rest_max}s"
        )

        try:
            for trial_id, text in enumerate(self.sentences, start=1):
                print(
                    f"Presenting news {trial_id}/{len(self.sentences)}: {text}"
                )
                if not self.display_news(text, trial_id):
                    break
            print("Relaxing news paradigm completed!")
        finally:
            pygame.mixer.quit()
            self.save_data()
            self.cleanup()
