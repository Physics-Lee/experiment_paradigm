"""Standalone word-reading paradigm."""

import random
import time

import pygame

from ..core import BaseParadigm


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

