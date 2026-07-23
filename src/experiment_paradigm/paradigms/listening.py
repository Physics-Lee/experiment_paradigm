"""Standalone audio-listening paradigm."""

import os
import random
import time

import pygame

from ..core import BaseParadigm


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

