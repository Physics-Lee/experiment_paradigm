import csv
import hashlib
import json
import math
import os
import random
import struct
import time
from datetime import datetime
from pathlib import Path

import pygame


class BaseParadigm:
    """Base class for all experimental paradigms"""
    
    def __init__(self, caption="Paradigm", output_prefix="experiment"):
        """
        Initialize the base paradigm with common pygame setup.
        
        Parameters:
        -----------
        caption : str
            Window caption text
        output_prefix : str
            Prefix for output files (will generate {prefix}_timestamp.csv and .json)
        """
        # Initialize pygame
        pygame.init()
        
        # Set up display (fullscreen)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption(caption)
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.GRAY = (128, 128, 128)
        self.LIGHT_BROWN = (210, 180, 140)  # Light brown for progress bar
        
        # Font settings
        self.font_size = 80
        self.font = self._load_font()
        
        # Square settings
        self.square_size = 40
        self.square_offset_y = 120  # Distance below text
        
        # Clock for timing
        self.clock = pygame.time.Clock()
        
        # Fixation cross settings
        self.cross_size = 40
        self.cross_thickness = 10
        
        # Timestamp recording
        self.experiment_start_time = time.perf_counter()
        self.experiment_start_datetime = datetime.now()
        self.experiment_start_datetime_iso = self.experiment_start_datetime.isoformat()
        self.trials_data = []
        self.output_prefix = output_prefix
    
    def get_timestamp(self):
        """Get relative timestamp since experiment start."""
        return time.perf_counter() - self.experiment_start_time
    
    def get_absolute_time(self):
        """Get absolute timestamp (ISO format string)."""
        return datetime.now().isoformat()
    
    def save_data(self):
        """Save collected data to CSV and JSON files."""
        if not self.trials_data:
            print("No data to save.")
            return
        
        # Create timestamp directory if it doesn't exist
        timestamp_dir = "timestamp"
        if not os.path.exists(timestamp_dir):
            os.makedirs(timestamp_dir)
            print(f"Created directory: {timestamp_dir}/")
        
        # Generate filename with timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = os.path.join(timestamp_dir, f"{self.output_prefix}_{timestamp_str}.csv")
        json_filename = os.path.join(timestamp_dir, f"{self.output_prefix}_{timestamp_str}.json")
        
        # Save CSV
        self._save_csv(csv_filename)
        
        # Save JSON
        self._save_json(json_filename)
        
        print(f"\nData saved:")
        print(f"  CSV:  {csv_filename}")
        print(f"  JSON: {json_filename}")
    
    def _save_csv(self, filename):
        """Save data to CSV file."""
        if not self.trials_data:
            return
        
        # Get all keys from first trial
        fieldnames = list(self.trials_data[0].keys())
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.trials_data)
    
    def _save_json(self, filename):
        """Save data to JSON file."""
        data = {
            "experiment_start": self.experiment_start_datetime_iso,
            "total_trials": len(self.trials_data),
            "trials": self.trials_data
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
    
    def _load_font(self):
        """Load a suitable font for the paradigm."""
        # Try to load a Chinese/English font
        chinese_fonts = [
            'C:/Windows/Fonts/msyh.ttc',     # Microsoft YaHei
            'C:/Windows/Fonts/simhei.ttf',   # SimHei
            'C:/Windows/Fonts/simsun.ttc',   # SimSun
            'C:/Windows/Fonts/msyhbd.ttc',   # Microsoft YaHei Bold
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
        
        for font_path in chinese_fonts:
            try:
                font = pygame.font.Font(font_path, self.font_size)
                print(f"Successfully loaded font: {font_path}")
                return font
            except:
                continue
        
        print("Warning: Could not load system font. Using default font.")
        return pygame.font.Font(None, self.font_size)
    
    def draw_red_square(self, y_position):
        """Draw red square below the given y position."""
        square_x = self.width // 2 - self.square_size // 2
        square_y = y_position + self.square_offset_y
        pygame.draw.rect(self.screen, self.RED, 
                        (square_x, square_y, self.square_size, self.square_size))
    
    def draw_green_square(self, y_position):
        """Draw green square below the given y position."""
        square_x = self.width // 2 - self.square_size // 2
        square_y = y_position + self.square_offset_y
        pygame.draw.rect(self.screen, self.GREEN, 
                        (square_x, square_y, self.square_size, self.square_size))
    
    def draw_centered_red_square(self):
        """Draw red square in the center of screen."""
        square_x = self.width // 2 - self.square_size // 2
        square_y = self.height // 2 - self.square_size // 2
        pygame.draw.rect(self.screen, self.RED, 
                        (square_x, square_y, self.square_size, self.square_size))
    
    def draw_centered_green_square(self):
        """Draw green square in the center of screen."""
        square_x = self.width // 2 - self.square_size // 2
        square_y = self.height // 2 - self.square_size // 2
        pygame.draw.rect(self.screen, self.GREEN, 
                        (square_x, square_y, self.square_size, self.square_size))
    
    def draw_fixation_cross(self):
        """Draw white fixation cross in center of screen."""
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Horizontal line
        pygame.draw.rect(self.screen, self.WHITE,
                       (center_x - self.cross_size, center_y - self.cross_thickness // 2,
                        self.cross_size * 2, self.cross_thickness))
        # Vertical line
        pygame.draw.rect(self.screen, self.WHITE,
                       (center_x - self.cross_thickness // 2, center_y - self.cross_size,
                        self.cross_thickness, self.cross_size * 2))
    
    def check_exit_events(self):
        """Check for exit events (QUIT, ESC, mouse click)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                print("Mouse clicked! Exiting...")
                return False
        return True
    
    def show_interval(self, interval_duration):
        """Show inter-trial interval: black screen (0.5s) + fixation cross (remaining time)."""
        # First 0.5s: black screen
        self.screen.fill(self.BLACK)
        pygame.display.flip()
        black_start = time.time()
        while time.time() - black_start < 0.5:
            if not self.check_exit_events():
                return False
            self.clock.tick(60)
        
        # Remaining time: white cross in center
        if interval_duration > 0.5:
            cross_start = time.time()
            while time.time() - cross_start < (interval_duration - 0.5):
                if not self.check_exit_events():
                    return False
                
                self.screen.fill(self.BLACK)
                self.draw_fixation_cross()
                pygame.display.flip()
                self.clock.tick(60)
        
        return True
    
    def cleanup(self):
        """Clean up pygame resources."""
        pygame.quit()


class SentenceParadigm(BaseParadigm):
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
    ):
        """Initialize the sentence paradigm display."""
        with open(sentences_file, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f if line.strip()]

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

        if manifest.get("schema_version") != 1:
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
        seen_ids = set()
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
            if audio_id in seen_ids:
                raise ValueError(f"Duplicate sentence audio id: {audio_id}")
            seen_ids.add(audio_id)

            file_value = item.get("file")
            if not isinstance(file_value, str) or not file_value:
                raise ValueError(f"Manifest item {index} has no valid file")
            audio_path = (manifest_dir / file_value).resolve()
            if not audio_path.is_relative_to(manifest_dir):
                raise ValueError(
                    f"Manifest audio path escapes its directory: {file_value}"
                )
            if not audio_path.is_file():
                raise FileNotFoundError(f"Sentence audio not found: {audio_path}")

            expected_hash = item.get("sha256")
            if not isinstance(expected_hash, str) or (
                self._sha256_file(audio_path) != expected_hash.lower()
            ):
                raise ValueError(
                    f"Sentence audio checksum mismatch: {audio_path.name}"
                )

            validated_audio.append(
                {
                    "id": audio_id,
                    "file": file_value,
                    "path": audio_path,
                }
            )

        return manifest_path, validated_audio

    def _preload_sentence_audio(self, manifest_path, validated_audio):
        """Decode all validated sentence audio into mixer Sound objects."""
        loaded_audio = []
        for item in validated_audio:
            audio_path = item["path"]
            try:
                sound = pygame.mixer.Sound(str(audio_path))
            except pygame.error as error:
                raise ValueError(
                    f"Could not decode sentence audio: {audio_path}"
                ) from error

            loaded_audio.append(
                {
                    "id": item["id"],
                    "file": item["file"],
                    "path": audio_path,
                    "duration": sound.get_length(),
                    "sound": sound,
                }
            )

        print(
            f"Preloaded {len(loaded_audio)} sentence audio files from "
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

        trial_data[f"{phase}_audio_onset"] = self.get_timestamp()
        trial_data[f"{phase}_audio_onset_abs"] = self.get_absolute_time()
        channel = audio_item["sound"].play()
        if channel is None:
            raise RuntimeError(
                f"No mixer channel available for {audio_item['file']}"
            )

        while channel.get_busy():
            if not self.check_exit_events():
                channel.stop()
                return False
            draw_frame()
            pygame.display.flip()
            self.clock.tick(60)

        trial_data[f"{phase}_audio_offset"] = self.get_timestamp()
        trial_data[f"{phase}_audio_offset_abs"] = self.get_absolute_time()
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


class LockedInSentenceReadingParadigm(SentenceParadigm):
    """Character-paced sentence reading for patients with locked-in syndrome."""

    def __init__(
        self,
        sentences_file,
        audio_manifest,
        char_speed=1.2,
        play_mode="progress",
        progress_duration=3.0,
        progress_pause=0.5,
        baseline_min=1.5,
        baseline_max=2.5,
        pre_audio_delay_min=0.4,
        pre_audio_delay_max=0.6,
        silent_delay_min=2.0,
        silent_delay_max=3.0,
        final_hold=0.5,
        rest_min=5.0,
        rest_max=6.0,
        cue_tone=True,
        cue_frequency=1000,
        cue_duration=0.08,
        cue_volume=0.7,
        output_prefix="locked_in_sentence_reading",
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
        self.cue_tone_enabled = cue_tone
        self.cue_frequency = cue_frequency
        self.cue_duration = cue_duration
        self.cue_volume = cue_volume
        self.cue_sound = self._create_cue_sound() if cue_tone else None

    @staticmethod
    def _validate_duration_range(name, minimum, maximum):
        if minimum < 0 or maximum < 0:
            raise ValueError(f"{name} durations must be non-negative")
        if minimum > maximum:
            raise ValueError(
                f"{name} minimum must not be greater than maximum"
            )

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
        chinese_fonts = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
        for font_path in chinese_fonts:
            try:
                return pygame.font.Font(font_path, font_size)
            except (FileNotFoundError, OSError, pygame.error):
                continue
        return pygame.font.Font(None, font_size)

    def _sentence_layout(self, sentence):
        """Fit one centered character row into the upper half of the screen."""
        characters = self._characters(sentence)
        if not characters:
            raise ValueError("Sentence must contain at least one character")

        upper_height = self.height // 2
        maximum_width = round(self.width * 0.9)
        maximum_height = round(upper_height * 0.8)
        minimum_size = 12
        maximum_size = max(minimum_size, maximum_height)
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
        square_size = round((self.height - upper_height) * 0.75)
        square_rect = pygame.Rect(
            (self.width - square_size) // 2,
            upper_height + ((self.height - upper_height) - square_size) // 2,
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
        started_at = self.get_timestamp()
        draw_frame()
        pygame.display.flip()
        while self.get_timestamp() - started_at < duration:
            if not self.check_exit_events():
                return False, self.get_timestamp() - started_at
            self.clock.tick(60)
        return True, self.get_timestamp() - started_at

    def _draw_rest_screen(self):
        """Draw the large gray fixation cross used only between trials."""
        self.screen.fill(self.BLACK)
        center_x = self.width // 2
        center_y = self.height // 2
        arm_length = round(min(self.width, self.height) * 0.22)
        thickness = max(20, round(min(self.width, self.height) * 0.06))
        pygame.draw.rect(
            self.screen,
            self.GRAY,
            (
                center_x - arm_length,
                center_y - thickness // 2,
                arm_length * 2,
                thickness,
            ),
        )
        pygame.draw.rect(
            self.screen,
            self.GRAY,
            (
                center_x - thickness // 2,
                center_y - arm_length,
                thickness,
                arm_length * 2,
            ),
        )

    def display_sentence(self, sentence, trial_id):
        """Run one complete locked-in sentence-reading trial."""
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

        audio_item = self.sentence_audio[trial_id - 1]
        trial_data["audio_id"] = audio_item["id"]
        trial_data["audio_file"] = audio_item["file"]
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
        """Run the locked-in paradigm for all configured sentences."""
        print(f"Loaded {len(self.sentences)} sentences")
        print("Press ESC or click mouse to quit")
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

        try:
            for index, sentence in enumerate(self.sentences, start=1):
                print(
                    f"Displaying sentence {index}/{len(self.sentences)}: "
                    f"{sentence}"
                )
                if not self.display_sentence(sentence, trial_id=index):
                    break
        finally:
            self.save_data()
            self.cleanup()


class ReadingParadigm(BaseParadigm):
    def __init__(self, words_file, word_duration=0.3, prep_time=1.5, prep_time_jitter=0.1, 
                 word_jitter_mean=0.5, word_jitter_std=0.1, inter_word_interval=2.0,
                 output_prefix="reading"):
        """Initialize the reading paradigm display."""
        super().__init__(caption="Reading Paradigm", output_prefix=output_prefix)
        
        self.words_file = words_file
        self.word_duration = word_duration
        self.prep_time = prep_time
        self.prep_time_jitter = prep_time_jitter
        self.word_jitter_mean = word_jitter_mean
        self.word_jitter_std = word_jitter_std
        self.inter_word_interval = inter_word_interval
        
        # Load words
        with open(words_file, 'r', encoding='utf-8') as f:
            self.words = [line.strip() for line in f if line.strip()]
    
    def display_word(self, word, trial_id):
        """Display a single word with the paradigm."""
        # Initialize trial data
        trial_data = {
            'trial_id': trial_id,
            'paradigm': 'reading',
            'word': word,
            'trial_start': self.get_timestamp(),
            'trial_start_abs': self.get_absolute_time()  # 添加绝对时间
        }
        
        actual_prep_time = random.uniform(self.prep_time - self.prep_time_jitter,
                                          self.prep_time + self.prep_time_jitter)
        word_jitter = random.uniform(self.word_jitter_mean - self.word_jitter_std,
                                     self.word_jitter_mean + self.word_jitter_std)
        
        trial_data['actual_prep_time'] = actual_prep_time
        trial_data['actual_word_jitter'] = word_jitter
        
        # Phase 1: Red square in center
        trial_data['red_square_onset'] = self.get_timestamp()
        trial_data['red_square_onset_abs'] = self.get_absolute_time()
        
        start_time = time.time()
        while time.time() - start_time < actual_prep_time:
            if not self.check_exit_events():
                return False
            
            self.screen.fill(self.BLACK)
            self.draw_centered_red_square()
            pygame.display.flip()
            self.clock.tick(60)
        
        # Phase 2: Green square in center with jitter delay
        trial_data['green_square_onset'] = self.get_timestamp()
        trial_data['green_square_onset_abs'] = self.get_absolute_time()
        
        start_time = time.time()
        while time.time() - start_time < word_jitter:
            if not self.check_exit_events():
                return False
            
            self.screen.fill(self.BLACK)
            self.draw_centered_green_square()
            pygame.display.flip()
            self.clock.tick(60)
        
        # Phase 3: Word only (no square) in center
        trial_data['word_onset'] = self.get_timestamp()
        trial_data['word_onset_abs'] = self.get_absolute_time()
        
        start_time = time.time()
        while time.time() - start_time < self.word_duration:
            if not self.check_exit_events():
                return False
            
            self.screen.fill(self.BLACK)
            
            # Render and center the word
            word_surface = self.font.render(word, True, self.WHITE)
            word_rect = word_surface.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(word_surface, word_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        trial_data['word_offset'] = self.get_timestamp()
        trial_data['word_offset_abs'] = self.get_absolute_time()
        trial_data['trial_end'] = self.get_timestamp()
        trial_data['trial_end_abs'] = self.get_absolute_time()
        
        # Save trial data
        self.trials_data.append(trial_data)
        
        return True
    
    def run(self):
        """Run the paradigm for all words."""
        print(f"Loaded {len(self.words)} words")
        print("Press ESC or click mouse to quit")
        print(f"Word duration: {self.word_duration} s")
        print(f"Preparation time: {self.prep_time} s")
        
        try:
            for i, word in enumerate(self.words):
                print(f"Displaying word {i+1}/{len(self.words)}: {word}")
                
                if not self.display_word(word, trial_id=i+1):
                    break
                
                if not self.show_interval(self.inter_word_interval):
                    break
        
        finally:
            self.save_data()
            self.cleanup()


class ListeningParadigm(BaseParadigm):
    def __init__(self, audios_folder="assets/listening_audio", prep_time=1.5, prep_time_jitter=0.1, 
                 audio_jitter_mean=0.5, audio_jitter_std=0.1,
                 inter_audio_interval=2.0, repetitions=3,
                 output_prefix="listening"):
        """Initialize the listening paradigm display."""
        super().__init__(caption="Listening Paradigm", output_prefix=output_prefix)
        
        self.audios_folder = audios_folder
        self.prep_time = prep_time
        self.prep_time_jitter = prep_time_jitter
        self.audio_jitter_mean = audio_jitter_mean
        self.audio_jitter_std = audio_jitter_std
        self.inter_audio_interval = inter_audio_interval
        self.repetitions = repetitions
        
        # Initialize mixer
        pygame.mixer.init()
        
        # Load audio files
        import glob
        audio_extensions = ['*.mp3', '*.wav', '*.ogg']
        self.audio_files = []
        for ext in audio_extensions:
            self.audio_files.extend(glob.glob(os.path.join(audios_folder, ext)))
        
        if not self.audio_files:
            raise ValueError(f"No audio files found in {audios_folder}")
        
        audio_names = [os.path.basename(path) for path in self.audio_files]
        print(f"Found {len(self.audio_files)} audio files: {audio_names}")
        
        # Create randomized playlist
        self.playlist = []
        for audio_file in self.audio_files:
            self.playlist.extend([audio_file] * self.repetitions)
        
        random.shuffle(self.playlist)
        print(f"Created playlist with {len(self.playlist)} items (random order)")
    
    def play_audio(self, audio_file, trial_id):
        """Play a single audio file with the paradigm."""
        filename = os.path.basename(audio_file)
        
        # Initialize trial data
        trial_data = {
            'trial_id': trial_id,
            'paradigm': 'listening',
            'audio_filename': filename,
            'trial_start': self.get_timestamp(),
            'trial_start_abs': self.get_absolute_time()
        }
        
        actual_prep_time = random.uniform(self.prep_time - self.prep_time_jitter,
                                          self.prep_time + self.prep_time_jitter)
        audio_jitter = random.uniform(self.audio_jitter_mean - self.audio_jitter_std,
                                     self.audio_jitter_mean + self.audio_jitter_std)
        
        trial_data['actual_prep_time'] = actual_prep_time
        trial_data['actual_audio_jitter'] = audio_jitter
        
        # Phase 1: Red square in center
        trial_data['red_square_onset'] = self.get_timestamp()
        trial_data['red_square_onset_abs'] = self.get_absolute_time()
        
        start_time = time.time()
        while time.time() - start_time < actual_prep_time:
            if not self.check_exit_events():
                return False
            
            self.screen.fill(self.BLACK)
            self.draw_centered_red_square()  # 改用居中方块
            pygame.display.flip()
            self.clock.tick(60)
        
        # Phase 2: Green square in center with jitter delay
        trial_data['green_square_onset'] = self.get_timestamp()
        trial_data['green_square_onset_abs'] = self.get_absolute_time()
        
        start_time = time.time()
        while time.time() - start_time < audio_jitter:
            if not self.check_exit_events():
                return False
            
            self.screen.fill(self.BLACK)
            self.draw_centered_green_square()  # 改用居中方块
            pygame.display.flip()
            self.clock.tick(60)
        
        # Phase 3: Play audio with green square in center
        trial_data['audio_onset'] = self.get_timestamp()
        trial_data['audio_onset_abs'] = self.get_absolute_time()
        
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                if not self.check_exit_events():
                    pygame.mixer.music.stop()
                    return False
                
                self.screen.fill(self.BLACK)
                self.draw_centered_green_square()  # 改用居中方块
                pygame.display.flip()
                self.clock.tick(60)
            
            trial_data['audio_offset'] = self.get_timestamp()
            trial_data['audio_offset_abs'] = self.get_absolute_time()
    
        except Exception as e:
            print(f"Error playing audio {audio_file}: {e}")
            return False
        
        trial_data['trial_end'] = self.get_timestamp()
        trial_data['trial_end_abs'] = self.get_absolute_time()
        
        # Save trial data
        self.trials_data.append(trial_data)
        
        return True
    
    def run(self):
        """Run the paradigm for all audio files in the playlist."""
        print(f"Starting listening paradigm with {len(self.playlist)} audio presentations")
        print("Press ESC or click mouse to quit")
        print(f"Preparation time: {self.prep_time} s")
        
        try:
            for i, audio_file in enumerate(self.playlist):
                filename = os.path.basename(audio_file)
                print(f"Playing audio {i+1}/{len(self.playlist)}: {filename}")
                
                if not self.play_audio(audio_file, trial_id=i+1):
                    break
                
                if not self.show_interval(self.inter_audio_interval):
                    break
            
            print("Listening paradigm completed!")
        
        finally:
            pygame.mixer.quit()
            self.save_data()
            self.cleanup()
