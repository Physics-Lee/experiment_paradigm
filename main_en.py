import pygame
import sys
import time
import random
import csv
import json
from datetime import datetime
import os

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
    def __init__(self, sentences_file, char_speed=1.2, 
                 prep_time=1.5, prep_time_jitter=0.1, jitter_mean=0.5, jitter_std=0.1, prep_mode='square', 
                 dot_interval=0.5, play_mode='green', 
                 progress_duration=1.2, progress_pause=0.5, inter_sentence_interval=2.0,
                 output_prefix="sentence"):
        """Initialize the sentence paradigm display."""
        super().__init__(caption="Sentence Paradigm", output_prefix=output_prefix)
        
        self.sentences_file = sentences_file
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
        
        # Load sentences
        with open(sentences_file, 'r', encoding='utf-8') as f:
            self.sentences = [line.strip() for line in f if line.strip()]
        
        # Spacing settings
        self.char_spacing = 15
        
        # Dots settings
        self.dot_radius = 8
        self.dot_spacing = 40
        self.dot_interval = dot_interval
    
    def draw_dots(self, sentence_y, char_widths, num_dots_left, num_dots_right):
        """Draw dots on both sides of the sentence."""
        total_width = sum(char_widths) + self.char_spacing * 2 * (len(char_widths) - 1)
        sentence_left = (self.width - total_width) // 2
        sentence_right = sentence_left + total_width
        dot_y = sentence_y + 35
        
        # Draw left dots
        for i in range(num_dots_left):
            dot_x = sentence_left - self.dot_spacing - (i * (self.dot_radius * 2 + self.dot_spacing))
            pygame.draw.circle(self.screen, self.WHITE, (dot_x, dot_y), self.dot_radius)
        
        # Draw right dots
        for i in range(num_dots_right):
            dot_x = sentence_right + self.dot_spacing + (i * (self.dot_radius * 2 + self.dot_spacing))
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
            'trial_start': self.get_timestamp(),
            'trial_start_abs': self.get_absolute_time()
        }
        
        sentence_y = self.height // 2 - 40
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
                        pygame.draw.rect(self.screen, self.LIGHT_BROWN,
                                       (completed_x, progress_bar_y, completed_width, int(self.font_size * 1.4)))
                    
                    # Draw current progress bar
                    progress_bar_width = int(word_width * progress)
                    pygame.draw.rect(self.screen, self.LIGHT_BROWN,
                                   (word_x, progress_bar_y, progress_bar_width, int(self.font_size * 1.4)))
                    
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
        
        trial_data['trial_end'] = self.get_timestamp()
        trial_data['trial_end_abs'] = self.get_absolute_time()
        trial_data['word_count'] = len(words)
        
        # Save trial data
        self.trials_data.append(trial_data)
        
        return True
    
    def run(self):
        """Run the paradigm for all sentences."""
        print(f"Loaded {len(self.sentences)} sentences")
        print("Press ESC or click mouse to quit")
        print(f"Character speed: {self.char_speed} s/char")
        print(f"Preparation time: {self.prep_time} s")
        
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
    def __init__(self, audios_folder="audios", prep_time=1.5, prep_time_jitter=0.1, 
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
        
        print(f"Found {len(self.audio_files)} audio files: {[os.path.basename(f) for f in self.audio_files]}")
        
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


# Example usage
if __name__ == "__main__":
    # paradigm = SentenceParadigm(
    #     sentences_file="sentences_en.txt",
    #     char_speed=1.2,
    #     prep_time=1.5,
    #     prep_time_jitter=0.3,
    #     jitter_mean=0.5,
    #     jitter_std=0.1,
    #     dot_interval=0.6,
    #     prep_mode='square',
    #     play_mode='green',
    #     progress_duration=1.2,
    #     progress_pause=0.5,
    #     inter_sentence_interval=2.0,
    #     output_prefix="sentence"
    # )
    # paradigm.run()

    reading = ReadingParadigm(
        words_file="words_reading.txt",
        word_duration=0.2,
        prep_time=1.5,
        prep_time_jitter=0.1,
        inter_word_interval=2.0,
        word_jitter_mean=0.5,
        word_jitter_std=0.1,
        output_prefix="reading"
    )
    reading.run()

    # listening = ListeningParadigm(
    #     audios_folder="audios",
    #     prep_time=1.5,
    #     prep_time_jitter=0.1,
    #     inter_audio_interval=2.0,
    #     audio_jitter_mean=0.5,
    #     audio_jitter_std=0.1,
    #     repetitions=3,
    #     output_prefix="listening"
    # )
    # listening.run()