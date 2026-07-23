"""Shared Pygame lifecycle and result persistence."""

import time
from datetime import datetime
from pathlib import Path

import pygame

from .display import draw_cross, draw_square, load_cjk_font
from .results import write_csv, write_json, write_run_results


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
        paths = write_run_results(
            trials=self.trials_data,
            output_prefix=self.output_prefix,
            experiment_start=self.experiment_start_datetime_iso,
        )
        if paths is None:
            return
        csv_filename, json_filename = paths
        print(f"\nData saved:")
        print(f"  CSV:  {csv_filename}")
        print(f"  JSON: {json_filename}")
    
    def _save_csv(self, filename):
        """Save data to CSV file."""
        write_csv(Path(filename), self.trials_data)
    
    def _save_json(self, filename):
        """Save data to JSON file."""
        write_json(
            Path(filename),
            experiment_start=self.experiment_start_datetime_iso,
            trials=self.trials_data,
        )
    
    def _load_font(self):
        """Load a suitable font for the paradigm."""
        return load_cjk_font(self.font_size)
    
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
        draw_square(
            self.screen,
            self.RED,
            center=(self.width // 2, self.height // 2),
            size=self.square_size,
        )
    
    def draw_centered_green_square(self):
        """Draw green square in the center of screen."""
        draw_square(
            self.screen,
            self.GREEN,
            center=(self.width // 2, self.height // 2),
            size=self.square_size,
        )
    
    def draw_fixation_cross(self):
        """Draw white fixation cross in center of screen."""
        draw_cross(
            self.screen,
            self.WHITE,
            center=(self.width // 2, self.height // 2),
            arm_length=self.cross_size,
            thickness=self.cross_thickness,
        )
    
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
