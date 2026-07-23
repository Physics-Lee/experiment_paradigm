"""General sentence presentation with optional preloaded audio."""

import hashlib
import json
import random
import time
from pathlib import Path

import pygame

from ..core import BaseParadigm
from ..core.audio import SentenceAudioMixin
from ..stimuli import read_nonempty_lines


class SentenceParadigm(SentenceAudioMixin, BaseParadigm):
    def __init__(
        self,
        sentences_file,
        char_speed=1.2,
        prep_time=1.5,
        prep_time_jitter=0.1,
        jitter_mean=0.5,
        jitter_std=0.1,
        prep_mode="square",
        dot_interval=0.5,
        play_mode="green",
        progress_duration=1.2,
        progress_pause=0.5,
        inter_sentence_interval=2.0,
        output_prefix="sentence",
        audio_manifest=None,
        play_audio_before=None,
        play_audio_after=None,
        pre_visual_gap=0.5,
        post_visual_gap=0.5,
        audio_screen="fixation",
        token_mode="word",
        sentences=None,
    ):
        """Initialize the sentence paradigm display."""
        if sentences is None:
            sentences = read_nonempty_lines(Path(sentences_file))
        else:
            sentences = list(sentences)
        if not sentences:
            raise ValueError("Sentence stimulus file contains no usable text")

        audio_before_enabled = (
            audio_manifest is not None
            if play_audio_before is None
            else play_audio_before
        )
        audio_after_enabled = (
            audio_manifest is not None
            if play_audio_after is None
            else play_audio_after
        )
        if pre_visual_gap < 0 or post_visual_gap < 0:
            raise ValueError("Audio/visual gaps must be non-negative")
        if audio_screen not in ("fixation", "black"):
            raise ValueError("audio_screen must be 'fixation' or 'black'")
        if token_mode not in ("word", "character"):
            raise ValueError("token_mode must be 'word' or 'character'")
        if (audio_before_enabled or audio_after_enabled) and not audio_manifest:
            raise ValueError(
                "audio_manifest is required when sentence audio playback is enabled"
            )

        validated_audio = []
        resolved_manifest = None
        if audio_before_enabled or audio_after_enabled:
            resolved_manifest, validated_audio = (
                self._validate_sentence_audio_manifest(
                    audio_manifest,
                    sentences,
                )
            )

        # Only create the fullscreen window after all paths, text mappings, and
        # checksums have passed validation.
        super().__init__(caption="Sentence Paradigm", output_prefix=output_prefix)

        self.sentences_file = sentences_file
        self.sentences = sentences
        self.char_speed = char_speed
        self.prep_time = prep_time
        self.prep_time_jitter = prep_time_jitter
        self.jitter_mean = jitter_mean
        self.jitter_std = jitter_std
        self.prep_mode = prep_mode
        self.play_mode = play_mode
        self.progress_duration = progress_duration
        self.progress_pause = progress_pause
        self.inter_sentence_interval = inter_sentence_interval
        
        # Optional sentence audio settings. Supplying a manifest enables both
        # audio phases by default while preserving legacy no-audio behavior.
        self.audio_manifest = resolved_manifest
        self.play_audio_before = audio_before_enabled
        self.play_audio_after = audio_after_enabled
        self.pre_visual_gap = pre_visual_gap
        self.post_visual_gap = post_visual_gap
        self.audio_screen = audio_screen
        self.token_mode = token_mode
        self.sentence_audio = []

        if self.play_audio_before or self.play_audio_after:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=44100,
                    size=-16,
                    channels=2,
                    buffer=512,
                )
            self.sentence_audio = self._preload_sentence_audio(
                resolved_manifest,
                validated_audio,
            )
        
        # Spacing settings
        self.char_spacing = 15
        
        # Dots settings
        self.dot_radius = 8
        self.dot_spacing = 40
        self.dot_interval = dot_interval

    def draw_dots(self, sentence_y, char_widths, num_dots_left, num_dots_right):
        """Draw dots on both sides of the sentence."""
        spacing = (
            self.char_spacing
            if self.token_mode == "character"
            else self.char_spacing * 2
        )
        total_width = sum(char_widths) + spacing * (len(char_widths) - 1)
        sentence_left = (self.width - total_width) // 2
        sentence_right = sentence_left + total_width
        dot_y = sentence_y + 35
        
        # Draw left dots
        for i in range(num_dots_left):
            dot_x = sentence_left - self.dot_spacing - (
                i * (self.dot_radius * 2 + self.dot_spacing)
            )
            pygame.draw.circle(self.screen, self.WHITE, (dot_x, dot_y), self.dot_radius)
        
        # Draw right dots
        for i in range(num_dots_right):
            dot_x = sentence_right + self.dot_spacing + (
                i * (self.dot_radius * 2 + self.dot_spacing)
            )
            pygame.draw.circle(self.screen, self.WHITE, (dot_x, dot_y), self.dot_radius)
    
    def display_sentence(self, sentence, trial_id):
        """Display a single sentence with the paradigm."""
        # Initialize trial data
        trial_data = {
            'trial_id': trial_id,
            'paradigm': 'sentence',
            'sentence': sentence,
            'prep_mode': self.prep_mode,
            'play_mode': self.play_mode,
            'token_mode': self.token_mode,
            'trial_start': self.get_timestamp(),
            'trial_start_abs': self.get_absolute_time()
        }

        audio_item = None
        if self.sentence_audio:
            audio_item = self.sentence_audio[trial_id - 1]
            trial_data["audio_id"] = audio_item["id"]
            trial_data["audio_file"] = audio_item["file"]
            trial_data["audio_files"] = audio_item["files"]
            trial_data["audio_segment_count"] = len(
                audio_item["segments"]
            )
            trial_data["audio_duration"] = audio_item["duration"]

        # Phase 0: Play the matching sentence audio before visual presentation.
        if self.play_audio_before:
            if not self._play_sentence_audio(
                audio_item,
                "pre",
                trial_data,
            ):
                return False
            gap_ok, actual_gap = self._show_audio_visual_gap(
                self.pre_visual_gap
            )
            trial_data["actual_pre_visual_gap"] = actual_gap
            if not gap_ok:
                return False
        
        sentence_y = self.height // 2 - 40
        if self.token_mode == "character":
            words = list(sentence)
            word_spacing = self.char_spacing
        else:
            words = sentence.split()
            word_spacing = self.char_spacing * 2
        word_widths = [self.font.render(word, True, self.WHITE).get_width() for word in words]
        
        # Phase 1: Preparation phase
        trial_data['prep_onset'] = self.get_timestamp()
        trial_data['prep_onset_abs'] = self.get_absolute_time()
        
        if self.prep_mode == 'square':
            actual_prep_time = random.uniform(self.prep_time - self.prep_time_jitter,
                                              self.prep_time + self.prep_time_jitter)
            trial_data['actual_prep_time'] = actual_prep_time
            
            start_time = time.time()
            while time.time() - start_time < actual_prep_time:
                if not self.check_exit_events():
                    return False
                
                self.screen.fill(self.BLACK)
                
                # Draw white sentence
                total_width = sum(word_widths) + word_spacing * (len(words) - 1)
                start_x = (self.width - total_width) // 2
                current_x = start_x
                for i, word in enumerate(words):
                    word_surface = self.font.render(word, True, self.WHITE)
                    self.screen.blit(word_surface, (current_x, sentence_y - 20))
                    current_x += word_widths[i] + word_spacing
                
                self.draw_red_square(sentence_y)
                pygame.display.flip()
                self.clock.tick(60)
        
        elif self.prep_mode == 'dots':
            total_dots = 3
            dots_left = total_dots
            dots_right = total_dots
            start_time = time.time()
            last_dot_time = start_time
            
            while dots_left > 0 or dots_right > 0:
                if not self.check_exit_events():
                    return False
                
                current_time = time.time()
                if current_time - last_dot_time >= self.dot_interval:
                    if dots_left > 0:
                        dots_left -= 1
                    if dots_right > 0:
                        dots_right -= 1
                    last_dot_time = current_time
                
                self.screen.fill(self.BLACK)
                
                # Draw white sentence
                total_width = sum(word_widths) + word_spacing * (len(words) - 1)
                start_x = (self.width - total_width) // 2
                current_x = start_x
                for i, word in enumerate(words):
                    word_surface = self.font.render(word, True, self.WHITE)
                    self.screen.blit(word_surface, (current_x, sentence_y - 20))
                    current_x += word_widths[i] + word_spacing
                
                self.draw_dots(sentence_y, word_widths, dots_left, dots_right)
                pygame.display.flip()
                self.clock.tick(60)
        
        trial_data['prep_offset'] = self.get_timestamp()
        trial_data['prep_offset_abs'] = self.get_absolute_time()
        
        # Phase 2: Word display animation
        trial_data['first_word_onset'] = self.get_timestamp()
        trial_data['first_word_onset_abs'] = self.get_absolute_time()
        
        if self.play_mode == 'green':
            green_count = 0
            start_time = time.time()
            jitter = random.uniform(self.jitter_mean - self.jitter_std, 
                                    self.jitter_mean + self.jitter_std)
            trial_data['actual_jitter'] = jitter
            
            while green_count <= len(words):
                if not self.check_exit_events():
                    return False
                
                elapsed = time.time() - start_time
                if elapsed < jitter:
                    green_count = 0
                else:
                    green_count = int((elapsed - jitter) / self.char_speed) + 1
                
                if green_count > len(words):
                    green_count = len(words)
                
                self.screen.fill(self.BLACK)
                
                total_width = sum(word_widths) + word_spacing * (len(words) - 1)
                start_x = (self.width - total_width) // 2
                current_x = start_x
                for i, word in enumerate(words):
                    color = self.GREEN if i < green_count else self.WHITE
                    word_surface = self.font.render(word, True, color)
                    self.screen.blit(word_surface, (current_x, sentence_y - 20))
                    current_x += word_widths[i] + word_spacing
                
                if self.prep_mode == 'square':
                    self.draw_green_square(sentence_y)
                
                pygame.display.flip()
                self.clock.tick(60)
                
                if green_count >= len(words):
                    break
        
        elif self.play_mode == 'progress':
            total_width = sum(word_widths) + word_spacing * (len(words) - 1)
            start_x = (self.width - total_width) // 2
            completed_bars = []
            
            for word_idx in range(len(words)):
                word_x = start_x + sum(word_widths[:word_idx]) + word_spacing * word_idx
                word_width = word_widths[word_idx]
                
                start_time = time.time()
                while time.time() - start_time < self.progress_duration:
                    if not self.check_exit_events():
                        return False
                    
                    elapsed = time.time() - start_time
                    progress = min(1.0, elapsed / self.progress_duration)
                    
                    self.screen.fill(self.BLACK)
                    progress_bar_y = sentence_y - 20
                    
                    # Draw completed progress bars
                    for _, completed_x, completed_width in completed_bars:
                        pygame.draw.rect(
                            self.screen,
                            self.LIGHT_BROWN,
                            (
                                completed_x,
                                progress_bar_y,
                                completed_width,
                                int(self.font_size * 1.4),
                            ),
                        )
                    
                    # Draw current progress bar
                    progress_bar_width = int(word_width * progress)
                    pygame.draw.rect(
                        self.screen,
                        self.LIGHT_BROWN,
                        (
                            word_x,
                            progress_bar_y,
                            progress_bar_width,
                            int(self.font_size * 1.4),
                        ),
                    )
                    
                    # Draw all words on top
                    current_x = start_x
                    for i, word in enumerate(words):
                        word_surface = self.font.render(word, True, self.WHITE)
                        self.screen.blit(word_surface, (current_x, sentence_y - 20))
                        current_x += word_widths[i] + word_spacing
                    
                    if self.prep_mode == 'square':
                        self.draw_green_square(sentence_y)
                    
                    pygame.display.flip()
                    self.clock.tick(60)
                
                completed_bars.append((word_idx, word_x, int(word_width * 0.99)))
                
                # Pause between words
                if word_idx < len(words) - 1:
                    pause_start = time.time()
                    while time.time() - pause_start < self.progress_pause:
                        if not self.check_exit_events():
                            return False
                        self.clock.tick(60)
        
        trial_data['sentence_complete'] = self.get_timestamp()
        trial_data['sentence_complete_abs'] = self.get_absolute_time()
        
        # Hold final state
        hold_start = time.time()
        while time.time() - hold_start < 0.5:
            if not self.check_exit_events():
                return False
            self.clock.tick(60)
        
        # Phase 3: Play the same matching audio after visual presentation.
        if self.play_audio_after:
            gap_ok, actual_gap = self._show_audio_visual_gap(
                self.post_visual_gap
            )
            trial_data["actual_post_visual_gap"] = actual_gap
            if not gap_ok:
                return False
            if not self._play_sentence_audio(
                audio_item,
                "post",
                trial_data,
            ):
                return False

        trial_data['trial_end'] = self.get_timestamp()
        trial_data['trial_end_abs'] = self.get_absolute_time()
        trial_data['word_count'] = len(words)
        trial_data['token_count'] = len(words)
        
        # Save trial data
        self.trials_data.append(trial_data)
        
        return True
    
    def run(self):
        """Run the paradigm for all sentences."""
        print(f"Loaded {len(self.sentences)} sentences")
        print("Press ESC or click mouse to quit")
        print(f"Character speed: {self.char_speed} s/char")
        print(f"Preparation time: {self.prep_time} s")
        print(f"Token mode: {self.token_mode}")
        if self.play_audio_before or self.play_audio_after:
            print(
                "Sentence audio: "
                f"before={self.play_audio_before}, "
                f"after={self.play_audio_after}"
            )
        
        try:
            for i, sentence in enumerate(self.sentences):
                print(f"Displaying sentence {i+1}/{len(self.sentences)}: {sentence}")
                
                if not self.display_sentence(sentence, trial_id=i+1):
                    break
                
                if not self.show_interval(self.inter_sentence_interval):
                    break
        
        finally:
            self.save_data()
            self.cleanup()

