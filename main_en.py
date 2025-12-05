import pygame
import sys
import time
import random

class SentenceParadigm:
    def __init__(self, sentences_file, char_speed=1.2, 
                 prep_time=1.5, prep_time_jitter=0.1, jitter_mean=0.5, jitter_std=0.1, prep_mode='square', 
                 dot_interval=0.5, play_mode='green', 
                 progress_duration=1.2, progress_pause=0.5, inter_sentence_interval=2.0):
        """
        Initialize the sentence paradigm display.
        
        Parameters:
        -----------
        sentences_file : str
            Path to the .txt file containing sentences (one per line)
        char_speed : float
            Time per character turning green (seconds per character)
            Only used when play_mode='green'
        prep_time : float
            Center time to display red square before sentence turns green (seconds)
            Only used when prep_mode='square'
        prep_time_jitter : float
            Half-width of uniform distribution for prep_time jitter (seconds)
            Only used when prep_mode='square'
        jitter_mean : float
            Center of uniform distribution for character jitter (seconds)
            Only used when play_mode='green'
        jitter_std : float
            Half-width of uniform distribution for character jitter (seconds)
            Only used when play_mode='green'
        prep_mode : str
            Preparation mode: 'square' for color-changing square, 'dots' for disappearing dots
        dot_interval : float
            Time between dot disappearances in dots mode (seconds)
        play_mode : str
            Play mode: 'green' for turning green one by one, 'progress' for progress bar
        progress_duration : float
            Duration for progress bar to complete on each character (seconds)
            Only used when play_mode='progress'
        progress_pause : float
            Pause duration between characters in progress mode (seconds)
            Only used when play_mode='progress'
        """
        self.sentences_file = sentences_file
        self.char_speed = char_speed  # seconds per character
        self.prep_time = prep_time    # seconds (center value)
        self.prep_time_jitter = prep_time_jitter  # half-width for prep_time uniform distribution
        self.jitter_mean = jitter_mean  # center of uniform distribution (seconds)
        self.jitter_std = jitter_std    # half-width of uniform distribution (seconds)
        self.prep_mode = prep_mode  # 'square' or 'dots'
        self.play_mode = play_mode  # 'green' or 'progress'
        self.progress_duration = progress_duration  # seconds for progress bar per character
        self.progress_pause = progress_pause  # seconds pause between characters
        self.inter_sentence_interval = inter_sentence_interval # total inter-sentence interval in seconds
        
        # Load sentences
        with open(sentences_file, 'r', encoding='utf-8') as f:
            self.sentences = [line.strip() for line in f if line.strip()]
        
        # Initialize pygame
        pygame.init()
        
        # Set up display (fullscreen)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("Sentence Paradigm")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.LIGHT_BROWN = (210, 180, 140)  # Light brown for progress bar
        
        # Font settings (larger for Chinese characters)
        self.font_size = 80
        self.char_spacing = 15  # Space between characters
        self.font = pygame.font.Font(None, self.font_size)
        
        # Try to load a Chinese font
        try:
            # Common Chinese fonts - Windows paths first
            chinese_fonts = [
                'C:/Windows/Fonts/msyh.ttc',     # Microsoft YaHei
                'C:/Windows/Fonts/simhei.ttf',   # SimHei
                'C:/Windows/Fonts/simsun.ttc',   # SimSun
                'C:/Windows/Fonts/msyhbd.ttc',   # Microsoft YaHei Bold
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            ]
            
            font_loaded = False
            for font_path in chinese_fonts:
                try:
                    self.font = pygame.font.Font(font_path, self.font_size)
                    print(f"Successfully loaded font: {font_path}")
                    font_loaded = True
                    break
                except Exception as e:
                    continue
            
            if not font_loaded:
                print("Warning: Could not load Chinese font. Using default font.")
                self.font = pygame.font.Font(None, self.font_size)
        except:
            print("Warning: Could not load Chinese font. Using default font.")
            self.font = pygame.font.Font(None, self.font_size)
        
        # Square settings
        self.square_size = 40
        
        # Dots settings
        self.dot_radius = 8
        self.dot_spacing = 40  # Space between dots (increased from 20)
        self.dot_interval = dot_interval  # Time between dot disappearances (seconds)
        
        # Progress bar settings
        self.progress_bar_height = 8  # Height of progress bar
        
        # Clock for timing
        self.clock = pygame.time.Clock()
        
    def draw_red_square(self, sentence_y):
        """Draw red square below the sentence."""
        square_x = self.width // 2 - self.square_size // 2
        square_y = sentence_y + 120  # Increased from 60 to 120
        pygame.draw.rect(self.screen, self.RED, 
                        (square_x, square_y, self.square_size, self.square_size))
    
    def draw_dots(self, sentence_y, char_widths, num_dots_left, num_dots_right):
        """Draw dots on both sides of the sentence."""
        # Calculate sentence boundaries
        total_width = sum(char_widths) + self.char_spacing * (len(char_widths) - 1)
        sentence_left = (self.width - total_width) // 2
        sentence_right = sentence_left + total_width
        # Center dots vertically with the sentence (sentence_y - 20 is the text baseline)
        # Add font_size // 2 to get to the vertical center of the text
        dot_y = sentence_y + 35 # 35 is fine-tuned for vertical alignment
        
        # Draw left dots
        for i in range(num_dots_left):
            dot_x = sentence_left - self.dot_spacing - (i * (self.dot_radius * 2 + self.dot_spacing))
            pygame.draw.circle(self.screen, self.WHITE, (dot_x, dot_y), self.dot_radius)
        
        # Draw right dots
        for i in range(num_dots_right):
            dot_x = sentence_right + self.dot_spacing + (i * (self.dot_radius * 2 + self.dot_spacing))
            pygame.draw.circle(self.screen, self.WHITE, (dot_x, dot_y), self.dot_radius)
        
    def display_sentence(self, sentence):
        """
        Display a single sentence with the paradigm:
        1. Preparation phase (square or dots mode)
        2. Words turn green one by one at char_speed (char_speed now means time per word)
        """
        # Calculate timing
        time_per_word = self.char_speed  # seconds per word (parameter name kept for compatibility)
        
        # Render the sentence to get position
        sentence_y = self.height // 2 - 40
        
        # Split into words
        words = sentence.split()
        word_spacing = self.char_spacing * 2  # Larger spacing between words
        
        # Calculate word widths
        word_widths = [self.font.render(word, True, self.WHITE).get_width() for word in words]
        
        # Phase 1: preparation phase
        if self.prep_mode == 'square':
            # Sample prep_time from uniform distribution
            actual_prep_time = random.uniform(self.prep_time - self.prep_time_jitter,
                                              self.prep_time + self.prep_time_jitter)
            
            # Phase 1: Preparation phase (white sentence + red square)
            start_time = time.time()
            while time.time() - start_time < actual_prep_time:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        print("Mouse clicked! Exiting...")
                        return False
                
                # Clear screen
                self.screen.fill(self.BLACK)
                
                # Calculate starting x position for centered text with spacing
                total_width = sum(word_widths) + word_spacing * (len(words) - 1)
                start_x = (self.width - total_width) // 2
                
                # Draw white sentence with spacing
                current_x = start_x
                for i, word in enumerate(words):
                    word_surface = self.font.render(word, True, self.WHITE)
                    self.screen.blit(word_surface, (current_x, sentence_y - 20))
                    current_x += word_widths[i] + word_spacing
                
                # Draw red square
                self.draw_red_square(sentence_y)
                
                pygame.display.flip()
                self.clock.tick(60)
    
        elif self.prep_mode == 'dots':
            # Phase 1: Dots disappearing phase
            total_dots = 3
            dots_left = total_dots
            dots_right = total_dots
            
            start_time = time.time()
            last_dot_time = start_time
            
            while dots_left > 0 or dots_right > 0:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        print("Mouse clicked! Exiting...")
                        return False
                
                # Check if it's time to remove a dot
                current_time = time.time()
                elapsed_since_last = current_time - last_dot_time
                
                if elapsed_since_last >= self.dot_interval:
                    # Remove dots simultaneously from both sides
                    if dots_left > 0:
                        dots_left -= 1
                    if dots_right > 0:
                        dots_right -= 1
                    last_dot_time = current_time
                
                # Clear screen
                self.screen.fill(self.BLACK)
                
                # Calculate starting x position for centered text with spacing
                total_width = sum(word_widths) + word_spacing * (len(words) - 1)
                start_x = (self.width - total_width) // 2
                
                # Draw white sentence with spacing
                current_x = start_x
                for i, word in enumerate(words):
                    word_surface = self.font.render(word, True, self.WHITE)
                    self.screen.blit(word_surface, (current_x, sentence_y - 20))
                    current_x += word_widths[i] + word_spacing
                
                # Draw remaining dots
                self.draw_dots(sentence_y, word_widths, dots_left, dots_right)
                
                pygame.display.flip()
                self.clock.tick(60)
    
        # Phase 2: Word display animation
        if self.play_mode == 'green':
            # Characters turn green one word at a time
            green_count = 0
            start_time = time.time()
            
            # Sample jitter from uniform distribution
            jitter = random.uniform(self.jitter_mean - self.jitter_std, 
                                    self.jitter_mean + self.jitter_std)
            
            while green_count <= len(words):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        print("Mouse clicked! Exiting...")
                        return False
                
                # Update green_count based on elapsed time
                elapsed = time.time() - start_time
                # First word turns green after jitter time
                if elapsed < jitter:
                    green_count = 0
                else:
                    green_count = int((elapsed - jitter) / self.char_speed) + 1
                
                if green_count > len(words):
                    green_count = len(words)
                
                # Clear screen
                self.screen.fill(self.BLACK)
                
                # Calculate starting x position for centered text
                total_width = sum(word_widths) + word_spacing * (len(words) - 1)
                start_x = (self.width - total_width) // 2
                
                # Draw each word with spacing
                current_x = start_x
                for i, word in enumerate(words):
                    color = self.GREEN if i < green_count else self.WHITE
                    word_surface = self.font.render(word, True, color)
                    self.screen.blit(word_surface, (current_x, sentence_y - 20))
                    current_x += word_widths[i] + word_spacing
                
                # Draw green square only in square mode
                if self.prep_mode == 'square':
                    square_x = self.width // 2 - self.square_size // 2
                    square_y = sentence_y + 120
                    pygame.draw.rect(self.screen, self.GREEN, 
                                   (square_x, square_y, self.square_size, self.square_size))
                
                pygame.display.flip()
                self.clock.tick(60)
                
                if green_count >= len(words):
                    break
        
        elif self.play_mode == 'progress':
            # New mode: Progress bar for each word
            total_width = sum(word_widths) + word_spacing * (len(words) - 1)
            start_x = (self.width - total_width) // 2
            
            # Track completed progress bars
            completed_bars = []
            
            for word_idx in range(len(words)):
                # Calculate current word position
                word_x = start_x + sum(word_widths[:word_idx]) + word_spacing * word_idx
                word_width = word_widths[word_idx]
                
                # Progress bar animation for this word
                start_time = time.time()
                while time.time() - start_time < self.progress_duration:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            return False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                return False
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            print("Mouse clicked! Exiting...")
                            return False
                    
                    # Calculate progress
                    elapsed = time.time() - start_time
                    progress = min(1.0, elapsed / self.progress_duration)
                    
                    # Clear screen
                    self.screen.fill(self.BLACK)

                    # position
                    progress_bar_y_temp = sentence_y - 20
                    
                    # Draw completed progress bars first (bottom layer)
                    for completed_idx, completed_x, completed_width in completed_bars:
                        progress_bar_y = progress_bar_y_temp
                        pygame.draw.rect(self.screen, self.LIGHT_BROWN,
                                       (completed_x, progress_bar_y, completed_width, int(self.font_size * 1.4)))
                    
                    # Draw current progress bar (bottom layer)
                    progress_bar_y = progress_bar_y_temp
                    progress_bar_width = int(word_width * 1.0 * progress)
                    pygame.draw.rect(self.screen, self.LIGHT_BROWN,
                                   (word_x, progress_bar_y, progress_bar_width, int(self.font_size * 1.4)))
                    
                    # Draw all words on top (top layer)
                    current_x = start_x
                    for i, word in enumerate(words):
                        word_surface = self.font.render(word, True, self.WHITE)
                        self.screen.blit(word_surface, (current_x, sentence_y - 20))
                        current_x += word_widths[i] + word_spacing

                    # Draw green square in square mode
                    if self.prep_mode == 'square':
                        square_x = self.width // 2 - self.square_size // 2
                        square_y = sentence_y + 120
                        pygame.draw.rect(self.screen, self.GREEN, 
                                    (square_x, square_y, self.square_size, self.square_size))
                    
                    pygame.display.flip()
                    self.clock.tick(60)
                
                # Add completed progress bar to the list
                completed_bars.append((word_idx, word_x, int(word_width * 0.99)))
                
                # Pause between words (except after last word)
                if word_idx < len(words) - 1:
                    pause_start = time.time()
                    while time.time() - pause_start < self.progress_pause:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                return False
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_ESCAPE:
                                    return False
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                print("Mouse clicked! Exiting...")
                                return False
                        self.clock.tick(60) # 60 FPS
    
        # Hold final state for 0.5 seconds
        hold_start = time.time()
        while time.time() - hold_start < 0.5:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    print("Mouse clicked! Exiting...")
                    return False
            self.clock.tick(60)

        return True
        
    def run(self):
        """Run the paradigm for all sentences."""
        print(f"Loaded {len(self.sentences)} sentences")
        print("Press ESC to quit")
        print(f"Character speed: {self.char_speed} s/char")
        print(f"Preparation time: {self.prep_time} s")
        
        try:
            for i, sentence in enumerate(self.sentences):
                print(f"Displaying sentence {i+1}/{len(self.sentences)}: {sentence}")
                
                if not self.display_sentence(sentence):
                    return  # Exit if display_sentence returns False
                
                # Inter-sentence interval with black screen then white cross
                # First 0.5s: black screen
                self.screen.fill(self.BLACK)
                pygame.display.flip()
                black_start = time.time()
                while time.time() - black_start < 0.5:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            return
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                return
                        # 添加鼠标点击退出
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            print("Mouse clicked! Exiting...")
                            return False
                    self.clock.tick(60)
                
                # Remaining time: white cross in center
                if self.inter_sentence_interval > 0.5:
                    cross_start = time.time()
                    while time.time() - cross_start < (self.inter_sentence_interval - 0.5):
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                return  # Just return, let finally handle quit
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_ESCAPE:
                                    return  # Just return, let finally handle quit
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                print("Mouse clicked! Exiting...")
                                return False
                        
                        self.screen.fill(self.BLACK)
                        
                        # Draw white cross in center
                        cross_size = 40  # Size of cross arms
                        cross_thickness = 10  # Thickness of cross lines
                        center_x = self.width // 2
                        center_y = self.height // 2
                        
                        # Horizontal line
                        pygame.draw.rect(self.screen, self.WHITE,
                                       (center_x - cross_size, center_y - cross_thickness // 2,
                                        cross_size * 2, cross_thickness))
                        # Vertical line
                        pygame.draw.rect(self.screen, self.WHITE,
                                       (center_x - cross_thickness // 2, center_y - cross_size,
                                        cross_thickness, cross_size * 2))
                        
                        pygame.display.flip()
                        self.clock.tick(60)
        
        finally: # Ensure pygame quits properly
            pygame.quit() # Quit pygame once at the end

# Example usage
if __name__ == "__main__":
    paradigm = SentenceParadigm(
        sentences_file="sentences_en.txt",
        char_speed = 1.2,
        prep_time = 1.8,
        prep_time_jitter = 0.3,
        jitter_mean = 0.5,
        jitter_std = 0.1, # in fact, this is half-width of uniform distribution
        dot_interval = 0.6,
        prep_mode = 'dots',  # 'square' or 'dots'
        play_mode = 'green',  # 'green' or 'progress'
        progress_duration = 1.2, 
        progress_pause = 0.5,
        inter_sentence_interval = 2.0 # total inter-sentence interval in seconds
    )

    paradigm.run()