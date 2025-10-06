# Author: Ammar HADDAD - ammarhaddad@outlook.fr
# Description: A Tetris game featuring an AI opponent, database integration for high scores, and a user interface.

import pygame
import random
import sqlite3
import datetime
import numpy as np
import copy
import os

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BLOCK_SIZE = 30
GRID_COLUMNS = 10
GRID_ROWS = 20
GAME_WIDTH = GRID_COLUMNS * BLOCK_SIZE
GAME_HEIGHT = GRID_ROWS * BLOCK_SIZE
SPACING = 90  # Space between the two game grids
UI_HEIGHT = 100  # Space for score display

MUSIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music.mp3")

# Colors
BLACK = (20, 20, 20)
WHITE = (240, 240, 240)
GRAY = (100, 100, 100)
DARK_BLUE = (15, 30, 60)
DEEP_PURPLE = (50, 10, 70)
LIGHT_BLUE = (100, 149, 237)
LIGHT_GREEN = (50, 205, 50)
DARK_GRAY = (30, 30, 30)

# Tetromino Shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I-piece
    [[1, 1], [1, 1]],  # Square piece
    [[1, 1, 1], [0, 1, 0]],  # T-piece
    [[1, 1, 1], [1, 0, 0]],  # L-piece
    [[1, 1, 1], [0, 0, 1]],  # Reverse L-piece
    [[1, 1, 0], [0, 1, 1]],  # S-piece
    [[0, 1, 1], [1, 1, 0]]   # Z-piece
]

SHAPE_COLORS = [
    (0, 255, 255),    # Cyan for I-piece
    (255, 215, 0),    # Gold for Square
    (128, 0, 128),    # Purple for T-piece
    (255, 140, 0),    # Dark Orange for L-piece
    (30, 144, 255),   # Dodger Blue for Reverse L
    (50, 205, 50),    # Lime Green for S-piece
    (220, 20, 60)     # Crimson for Z-piece
]

class Tetromino:
    def __init__(self):
        self.shape = random.choice(SHAPES)
        self.color = SHAPE_COLORS[SHAPES.index(self.shape)]
        self.x = GAME_WIDTH // BLOCK_SIZE // 2 - len(self.shape[0]) // 2
        self.y = 0

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def rotate(self):
        # Rotate clockwise
        self.shape = list(zip(*self.shape[::-1]))

class TetrisPlayer:
    def __init__(self, x_offset=0, controls=None):
        self.x_offset = x_offset
        self.controls = controls or {}
        self.username = "Human Player"
        self.reset()
        
    def reset(self):
        """Reset player state for game restart"""
        self.grid = [[BLACK for _ in range(GRID_COLUMNS)] 
                     for _ in range(GRID_ROWS)]
        self.current_piece = Tetromino()
        self.game_over = False
        self.score = 0
        self.survival_time = 0

class AIPlayer(TetrisPlayer):
    def calculate_board_height(self, grid):
        for y in range(len(grid)):
            if any(cell != BLACK for cell in grid[y]):
                return len(grid) - y
        return 0

    def calculate_holes(self, grid):
        holes = 0
        for x in range(len(grid[0])):
            found_block = False
            for y in range(len(grid)):
                if grid[y][x] != BLACK:
                    found_block = True
                elif found_block:
                    holes += 1
        return holes

    def calculate_bumpiness(self, grid):
        column_heights = [self.get_column_height(grid, x) for x in range(len(grid[0]))]
        return sum(abs(column_heights[i] - column_heights[i+1]) for i in range(len(column_heights)-1))

    def get_column_height(self, grid, column):
        for y in range(len(grid)):
            if grid[y][column] != BLACK:
                return len(grid) - y
        return 0

    def make_move(self, game):
        best_score = float('inf')
        best_move = {
            'rotation': 0,
            'x': self.current_piece.x
        }

        for rotation in range(4):
            test_piece = Tetromino()
            test_piece.shape = copy.deepcopy(self.current_piece.shape)
            test_piece.color = self.current_piece.color
            test_piece.x = self.current_piece.x
            test_piece.y = self.current_piece.y

            # Rotate piece
            for _ in range(rotation):
                test_piece.rotate()

            # Try different horizontal positions
            for dx in range(-5, 6):
                # Reset piece position and create a deep copy of the grid
                test_piece.x = self.current_piece.x + dx
                test_piece.y = self.current_piece.y
                grid_copy = [row.copy() for row in self.grid]

                # Simulate dropping the piece
                temp_piece = copy.deepcopy(test_piece)
                while game.is_valid_move(temp_piece, 0, 1, grid_copy):
                    temp_piece.y += 1

                # Check if the final position is valid and doesn't overwrite existing pieces
                if game.is_valid_move(temp_piece, 0, 0, grid_copy):
                    # Assess the board state without actually modifying the grid
                    test_grid = [row.copy() for row in grid_copy]
                    for y, row in enumerate(temp_piece.shape):
                        for x, cell in enumerate(row):
                            if cell:
                                grid_x = temp_piece.x + x
                                grid_y = temp_piece.y + y
                                if 0 <= grid_y < len(test_grid):
                                    test_grid[grid_y][grid_x] = temp_piece.color

                    # Evaluate board state
                    height = self.calculate_board_height(test_grid)
                    holes = self.calculate_holes(test_grid)
                    bumpiness = self.calculate_bumpiness(test_grid)

                    # Scoring function (lower is better)
                    score = height * 2 + holes * 3 + bumpiness

                    if score < best_score:
                        best_score = score
                        best_move = {
                            'rotation': rotation,
                            'x': temp_piece.x
                        }

        # Apply best move
        for _ in range(best_move['rotation']):
            self.current_piece.rotate()
        self.current_piece.x = best_move['x']

class TetrisGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        pygame.mixer.music.load(MUSIC_PATH) 
        pygame.mixer.music.play(-1)  # -1 makes it loop indefinitely

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen.get_size()
        pygame.display.set_caption('eTetris')
        self.clock = pygame.time.Clock()

        # Load custom fonts
        self.title_font = pygame.font.SysFont('tetris', 80)
        self.font = pygame.font.SysFont('OCR A Extended', 36)
        self.small_font = pygame.font.SysFont('OCR A Extended', 24)
        
        # Calculate player grid positions
        self.human_x = (SCREEN_WIDTH - (2 * GAME_WIDTH + SPACING)) // 2
        self.ai_x = self.human_x + GAME_WIDTH + SPACING
        
        human_controls = {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
                          'down': pygame.K_DOWN, 'rotate': pygame.K_UP}
        self.human_player = TetrisPlayer(x_offset=self.human_x, controls=human_controls)
        self.ai_player = AIPlayer(x_offset=self.ai_x)
        
        self.game_over = False
        self.start_time = None
        self.init_database()
        
        if not self.show_start_screen():
            pygame.quit()

    def reset(self):
        self.human_player.reset()
        self.ai_player.reset()
        self.game_over = False
        self.start_time = pygame.time.get_ticks()

    def init_database(self):
        # Ensure database directory exists
        os.makedirs('data', exist_ok=True)
        
        # Create SQLite database for high scores and game history
        self.conn = sqlite3.connect('src/tetris_database.db')
        cursor = self.conn.cursor()
        
        # Scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY,
                username TEXT,
                score INTEGER,
                survival_time REAL,
                date TEXT
            )
        ''')
        
        # Game history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY,
                username TEXT,
                winner TEXT,
                human_score INTEGER,
                ai_score INTEGER,
                survival_time REAL,
                date TEXT
            )
        ''')
        
        self.conn.commit()
        
    def show_start_screen(self):
        start_screen = True
        human_player_name = ""
        selected_menu = "Play"
        music_paused = False
        music_pause_toggled = False

        while start_screen:
            self.screen.fill(DEEP_PURPLE)  # Deep purple background
            
            screen_rect = self.screen.get_rect()  # Get the screen rect for easy centering
            
            # Title
            title = self.title_font.render('eTetris', True, WHITE)
            title_rect = title.get_rect(center=(screen_rect.centerx, screen_rect.top + 80))
            self.screen.blit(title, title_rect)
            
            # Menu options 
            menu_options = ["Play", "Leaderboard", "Game History"]
            
            # Centered menu navigation
            menu_y = title_rect.bottom + 50
            menu_spacing = 300
            for i, option in enumerate(menu_options):
                color = LIGHT_BLUE if option == selected_menu else WHITE
                menu_text = self.font.render(option, True, color)
                menu_rect = menu_text.get_rect(center=(screen_rect.centerx + (i - 1) * menu_spacing, menu_y))
                self.screen.blit(menu_text, menu_rect)
            
            if selected_menu == "Play":
                # Centered input box
                input_box = pygame.Rect(0, 0, 300, 50)
                input_box.center = (screen_rect.centerx, menu_y + SCREEN_HEIGHT//5)
                pygame.draw.rect(self.screen, LIGHT_BLUE, input_box, 3)  # Blue border
                
                # Player name input text
                txt_surface = self.font.render(human_player_name, True, WHITE)
                txt_rect = txt_surface.get_rect(center=input_box.center)
                self.screen.blit(txt_surface, txt_rect)
                
                # Centered instruction text
                name_prompt = self.font.render('Enter your username', True, WHITE)
                prompt_rect = name_prompt.get_rect(center=(screen_rect.centerx, input_box.top - 40))
                self.screen.blit(name_prompt, prompt_rect)
                
                # Centered start button
                start_button = pygame.Rect(0, 0, 200, 50)
                start_button.center = (screen_rect.centerx, input_box.bottom + 60)
                start_text = self.font.render('START', True, BLACK)
                start_text_rect = start_text.get_rect(center=start_button.center)
                
                # Button color changes based on username input
                button_color = LIGHT_GREEN if human_player_name else GRAY
                pygame.draw.rect(self.screen, button_color, start_button)
                self.screen.blit(start_text, start_text_rect)

            elif selected_menu == "Leaderboard":
                self.show_leaderboard()

            elif selected_menu == "Game History":
                self.show_game_history()

            # Centered bottom instructions
            instructions = self.small_font.render("ESC: Exit | SPACE: Mute | ARROWS: Navigate", True, WHITE)
            instructions_rect = instructions.get_rect(center=(screen_rect.centerx, screen_rect.bottom - 50))
            self.screen.blit(instructions, instructions_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        confirm = self.show_confirmation_dialog("Exit Game?", "Are you sure you want to exit?")
                        if confirm:
                            return False
                    elif event.key == pygame.K_SPACE:
                        music_pause_toggled = True
                    elif event.key == pygame.K_LEFT:
                        selected_menu = menu_options[(menu_options.index(selected_menu) - 1) % len(menu_options)]
                    elif event.key == pygame.K_RIGHT:
                        selected_menu = menu_options[(menu_options.index(selected_menu) + 1) % len(menu_options)]
                    
                    if selected_menu == "Play":
                        if event.key == pygame.K_RETURN and human_player_name:
                            self.human_player.username = human_player_name
                            return True
                        elif event.key == pygame.K_BACKSPACE:
                            human_player_name = human_player_name[:-1]
                        else:
                            if len(human_player_name) < 12 and event.unicode.isprintable():
                                human_player_name += event.unicode
                
                if music_pause_toggled:
                    human_player_name = human_player_name[:-1] if human_player_name else human_player_name
                    music_pause_toggled = False
                    music_paused = not music_paused

                    if music_paused:
                        pygame.mixer.music.pause() 
                    else:
                        pygame.mixer.music.unpause()

            human_player_name = human_player_name[:12]

        return False

    def show_confirmation_dialog(self, title, message):
        dialog_width = 500
        dialog_height = 200
        dialog_x = (SCREEN_WIDTH - dialog_width) // 3 - 100
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 3
        
        # Darken background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        
        # Draw dialog box
        pygame.draw.rect(self.screen, DARK_BLUE, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, WHITE, (dialog_x, dialog_y, dialog_width, dialog_height), 2)
        
        # Title
        title_text = self.font.render(title, True, WHITE)
        self.screen.blit(title_text, (dialog_x + 20, dialog_y + 20))
        
        # Message
        msg_text = self.small_font.render(message, True, WHITE)
        self.screen.blit(msg_text, (dialog_x + 20, dialog_y + 70))
        
        # Buttons
        yes_button = pygame.Rect(dialog_x + 150, dialog_y + 140, 80, 40)
        no_button = pygame.Rect(dialog_x + 270, dialog_y + 140, 80, 40)
        
        pygame.draw.rect(self.screen, (220, 20, 60), yes_button)
        pygame.draw.rect(self.screen, LIGHT_GREEN, no_button)
        
        yes_text = self.small_font.render("[Y]", True, WHITE)
        no_text = self.small_font.render("[N]", True, BLACK)
        
        self.screen.blit(yes_text, (yes_button.x + 20, yes_button.y + 10))
        self.screen.blit(no_text, (no_button.x + 20, no_button.y + 10))
        
        pygame.display.flip()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        return True
                    elif event.key == pygame.K_n:
                        return False

    def show_leaderboard(self):
        # Fetch top 10 scores
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT username, score, survival_time, date 
            FROM scores 
            WHERE username != 'AI'
            ORDER BY score DESC 
            LIMIT 10
        ''')
        scores = cursor.fetchall()

        # Render leaderboard
        y_offset = SCREEN_HEIGHT // 5


        # Table setup
        table_width = 600
        table_x = (SCREEN_WIDTH - table_width) // 3 - 150

        header_text = self.small_font.render('Rank', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x, y_offset + 40))
        header_text = self.small_font.render('Name', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x + 100, y_offset + 40))
        header_text = self.small_font.render('Score', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x + 400, y_offset + 40))
        header_text = self.small_font.render('Time', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x + 500, y_offset + 40))
        header_text = self.small_font.render('Date', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x + 600, y_offset + 40))



        for i, (username, score, survival_time, date) in enumerate(scores, 1):
            row_y = y_offset + 80 + i * 30
            
            rank_text = self.small_font.render(str(i), True, WHITE)
            name_text = self.small_font.render(username[:12], True, WHITE)  # Limit name length
            score_text = self.small_font.render(str(score), True, WHITE)
            time_text = self.small_font.render(f'{survival_time // 60:.0f}min', True, WHITE)
            date_text = self.small_font.render(date.split()[0], True, WHITE)

            self.screen.blit(rank_text, (table_x, row_y))
            self.screen.blit(name_text, (table_x + 100, row_y))
            self.screen.blit(score_text, (table_x + 400, row_y))
            self.screen.blit(time_text, (table_x + 500, row_y))
            self.screen.blit(date_text, (table_x + 600, row_y))



    def show_game_history(self):
        cursor = self.conn.cursor()
        
        # First, fetch all scores and their ranks based on score
        cursor.execute('''
            SELECT username, score, survival_time, date,
                (SELECT COUNT(*) + 1 FROM scores s2 WHERE s2.score > s1.score AND s2.username != 'AI') AS rank
            FROM scores s1
            WHERE username != 'AI'
            ORDER BY date DESC
            LIMIT 10
        ''')
        scores = cursor.fetchall()
        
        # Render leaderboard
        y_offset = SCREEN_HEIGHT // 5

        # Table setup
        table_width = 600
        table_x = (SCREEN_WIDTH - table_width) // 3 - 150
        header_text = self.small_font.render('Rank', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x, y_offset + 40))
        header_text = self.small_font.render('Name', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x + 100, y_offset + 40))
        header_text = self.small_font.render('Score', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x + 400, y_offset + 40))
        header_text = self.small_font.render('Time', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x + 500, y_offset + 40))
        header_text = self.small_font.render('Date', True, LIGHT_BLUE)
        self.screen.blit(header_text, (table_x + 600, y_offset + 40))
        
        # Display scores with their actual rank by score
        for i, (username, score, survival_time, date, rank) in enumerate(scores, 1):
            row_y = y_offset + 80 + i * 30
            
            rank_text = self.small_font.render(str(rank), True, WHITE)
            name_text = self.small_font.render(username[:12], True, WHITE)  # Limit name length
            score_text = self.small_font.render(str(score), True, WHITE)
            time_text = self.small_font.render(f'{survival_time // 60:.0f}min', True, WHITE)
            date_text = self.small_font.render(date.split()[0], True, WHITE)
            self.screen.blit(rank_text, (table_x, row_y))
            self.screen.blit(name_text, (table_x + 100, row_y))
            self.screen.blit(score_text, (table_x + 400, row_y))
            self.screen.blit(time_text, (table_x + 500, row_y))
            self.screen.blit(date_text, (table_x + 600, row_y))


    def draw_grid(self, player):
        # Draw vertical lines
        for x in range(GRID_COLUMNS + 1):
            start_pos = (player.x_offset + x * BLOCK_SIZE, 0)
            end_pos = (player.x_offset + x * BLOCK_SIZE, GAME_HEIGHT)
            pygame.draw.line(self.screen, GRAY, start_pos, end_pos, 1)
        # Draw horizontal lines
        for y in range(GRID_ROWS + 1):
            start_pos = (player.x_offset, y * BLOCK_SIZE)
            end_pos = (player.x_offset + GAME_WIDTH, y * BLOCK_SIZE)
            pygame.draw.line(self.screen, GRAY, start_pos, end_pos, 1)

    def draw_piece(self, piece, x_offset_pixels):
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    rect = [
                        x_offset_pixels + (piece.x + x) * BLOCK_SIZE,
                        (piece.y + y) * BLOCK_SIZE,
                        BLOCK_SIZE - 1,
                        BLOCK_SIZE - 1
                    ]
                    pygame.draw.rect(self.screen, piece.color, rect)

    def is_valid_move(self, piece, dx=0, dy=0, grid=None):
        if grid is None:
            # Default to human grid if piece is human's current piece, else AI's
            grid = self.human_player.grid if piece == self.human_player.current_piece else self.ai_player.grid
        
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece.x + x + dx
                    new_y = piece.y + y + dy
                    
                    # Check grid boundaries
                    if (new_x < 0 or new_x >= len(grid[0]) or new_y >= len(grid)):
                        return False
                    
                    # Check collision with existing blocks
                    if new_y >= 0 and grid[new_y][new_x] != BLACK:
                        return False
        return True

    def save_scores(self):
        cursor = self.conn.cursor()
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine winner
        winner = "AI" if self.human_player.game_over else "Human"
        
        # Save game history
        cursor.execute('''
            INSERT INTO game_history 
            (username, winner, human_score, ai_score, survival_time, date) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.human_player.username, winner, 
            self.human_player.score, self.ai_player.score, 
            min(self.human_player.survival_time, self.ai_player.survival_time), 
            current_date))

        # Save individual player scores
        if hasattr(self.human_player, 'username'):
            cursor.execute('''
                INSERT INTO scores 
                (username, score, survival_time, date) 
                VALUES (?, ?, ?, ?)
            ''', (self.human_player.username, self.human_player.score, 
                self.human_player.survival_time, current_date))
        
        # Save AI score
        cursor.execute('''
            INSERT INTO scores 
            (username, score, survival_time, date) 
            VALUES (?, ?, ?, ?)
        ''', ('AI', self.ai_player.score, 
            self.ai_player.survival_time, current_date))
        
        self.conn.commit()


    def run(self):
        # Start timing
        self.start_time = pygame.time.get_ticks()
        
        fall_speed = 0.3  # seconds
        update_interval = 10  # Increment speed every interval seconds
        last_fall_time = pygame.time.get_ticks()
        
        # Track time for updating speed
        speed_level = 1

        paused = False
        music_paused = False

        while not self.game_over:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        confirm = self.show_confirmation_dialog("Exit Game?", "Are you sure you want to quit?")
                        if confirm:
                            self.game_over = True
                            return
                    elif event.key == pygame.K_SPACE:
                        music_paused = not music_paused
                        pygame.mixer.music.pause() if music_paused else pygame.mixer.music.unpause()
                    elif event.key == pygame.K_p:
                        paused = not paused
                        pygame.mixer.music.pause() if paused else pygame.mixer.music.unpause()
                    elif event.key == pygame.K_r:
                        if self.show_confirmation_dialog("Restart game?", "Are you sure you want to restart? All the results of this game will be lost"):
                            self.reset()
                    
                    if not paused:
                        if event.key == self.human_player.controls['left']:
                            if self.is_valid_move(self.human_player.current_piece, dx=-1):
                                self.human_player.current_piece.move(-1, 0)
                        
                        if event.key == self.human_player.controls['right']:
                            if self.is_valid_move(self.human_player.current_piece, dx=1):
                                self.human_player.current_piece.move(1, 0)
                        
                        if event.key == self.human_player.controls['down']:
                            if self.is_valid_move(self.human_player.current_piece, dy=1):
                                self.human_player.current_piece.move(0, 1)
                        
                        if event.key == self.human_player.controls['rotate']:
                            rotated_piece = Tetromino()
                            rotated_piece.shape = [row[:] for row in self.human_player.current_piece.shape]
                            for _ in range(1):  # Rotate once (clockwise)
                                rotated_piece.shape = list(zip(*rotated_piece.shape[::-1]))
                            rotated_piece.x = self.human_player.current_piece.x
                            rotated_piece.y = self.human_player.current_piece.y
                            rotated_piece.color = self.human_player.current_piece.color
                            
                            if self.is_valid_move(rotated_piece, grid=self.human_player.grid):
                                self.human_player.current_piece.rotate()

            if paused:
                pause_text = self.font.render("PAUSED - Press P to resume", True, WHITE)
                text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(pause_text, text_rect)
                pygame.display.flip()
                continue
            
            if isinstance(self.ai_player, AIPlayer):
                self.ai_player.make_move(self)

            current_time = pygame.time.get_ticks()
            
            # Check if it's time to increase speed
            elapsed_seconds = (current_time - self.start_time) / 1000
            if elapsed_seconds >= speed_level * update_interval:
                fall_speed = max(0.1, fall_speed * 0.9)  # Reduce fall time by 10%, but not below 0.1 seconds
                speed_level += 1
            
            if current_time - last_fall_time > fall_speed * 1000:
                if self.is_valid_move(self.human_player.current_piece, dy=1):
                    self.human_player.current_piece.move(0, 1)
                else:
                    self.lock_piece(self.human_player)
                    self.human_player.current_piece = Tetromino()
                    
                    if not self.is_valid_move(self.human_player.current_piece):
                        self.human_player.game_over = True

                if self.is_valid_move(self.ai_player.current_piece, dy=1):
                    self.ai_player.current_piece.move(0, 1)
                else:
                    self.lock_piece(self.ai_player)
                    self.ai_player.current_piece = Tetromino()
                    
                    if not self.is_valid_move(self.ai_player.current_piece):
                        self.ai_player.game_over = True
                
                last_fall_time = current_time

                self.human_player.survival_time = (current_time - self.start_time) / 1000
                self.ai_player.survival_time = (current_time - self.start_time) / 1000

            if self.human_player.game_over or self.ai_player.game_over:
                self.game_over = True

            self.screen.fill(BLACK)
            
            self.draw_grid(self.human_player)
            self.draw_grid(self.ai_player)
            
            self.draw_piece(self.human_player.current_piece, self.human_player.x_offset)
            self.draw_piece(self.ai_player.current_piece, self.ai_player.x_offset)
            
            for y, row in enumerate(self.human_player.grid):
                for x, color in enumerate(row):
                    if color != BLACK:
                        pygame.draw.rect(
                            self.screen, color,
                            (self.human_player.x_offset + x * BLOCK_SIZE,
                            y * BLOCK_SIZE,
                            BLOCK_SIZE - 1, BLOCK_SIZE - 1)
                        )
            
            for y, row in enumerate(self.ai_player.grid):
                for x, color in enumerate(row):
                    if color != BLACK:
                        pygame.draw.rect(
                            self.screen, color,
                            (self.ai_player.x_offset + x * BLOCK_SIZE,
                            y * BLOCK_SIZE,
                            BLOCK_SIZE - 1, BLOCK_SIZE - 1)
                        )

            p1_text = self.font.render(f'Human: {self.human_player.score}', True, LIGHT_BLUE)
            p2_text = self.font.render(f'AI: {self.ai_player.score}', True, LIGHT_GREEN)
            self.screen.blit(p1_text, (self.human_x, GAME_HEIGHT + 10))
            self.screen.blit(p2_text, (self.ai_x, GAME_HEIGHT + 10))

            speed_text = self.font.render(f"SPEED: x{0.5/fall_speed:.2f}", True, GRAY)
            self.screen.blit(speed_text, (20,20))

            # Update the instructions to show current speed level
            instructions = self.small_font.render("ESC: Exit Game | SPACE: Mute/Unmute | P: Pause/Unpause | R: Restart", True, GRAY)
            self.screen.blit(instructions, (20, GAME_HEIGHT + 70))

            pygame.display.flip()
            self.clock.tick(60)

        self.save_scores()
        self.show_game_over_screen()


    def show_game_over_screen(self):
        game_over = True
        while game_over:
            self.screen.fill(BLACK)
            
            winner = "Human Player" if self.ai_player.game_over else "AI"
            
            game_over_text = self.font.render('GAME OVER', True, WHITE)
            winner_text = self.font.render(f'Winner: {winner}', True, WHITE)
            p1_score_text = self.font.render(f'Human Player Score: {self.human_player.score}', True, LIGHT_BLUE)
            p2_score_text = self.font.render(f'AI Score: {self.ai_player.score}', True, LIGHT_GREEN)
            game_duration_text = self.font.render(f'Game duration: {min(self.human_player.survival_time, self.ai_player.survival_time):.2f}s', True, LIGHT_BLUE)
            

            instructions = self.small_font.render("ESC: Exit Game | SPACE: Mute/Unmute | P: Pause/Unpause | M: Main menu", True, GRAY)
            self.screen.blit(instructions, (20, SCREEN_HEIGHT//2 + 100))

            self.screen.blit(game_over_text, (SCREEN_WIDTH // 3 - 100, SCREEN_HEIGHT // 2 - 300))
            self.screen.blit(winner_text, (SCREEN_WIDTH // 3 - 100, SCREEN_HEIGHT // 2 - 250))
            self.screen.blit(p1_score_text, (SCREEN_WIDTH // 3 - 200, SCREEN_HEIGHT // 2 - 200))
            self.screen.blit(p2_score_text, (SCREEN_WIDTH // 3 - 200, SCREEN_HEIGHT // 2 - 150))
            self.screen.blit(game_duration_text, (SCREEN_WIDTH // 3 - 200, SCREEN_HEIGHT // 2 - 100))
        
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                
                if event.type == pygame.KEYDOWN:
                    
                    if event.key == pygame.K_m:
                        game_over = False
                        self.show_start_screen()

    def lock_piece(self, player):
        for y, row in enumerate(player.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = player.current_piece.x + x
                    grid_y = player.current_piece.y + y
                    if 0 <= grid_y < len(player.grid):
                        player.grid[grid_y][grid_x] = player.current_piece.color

        lines_cleared = 0
        for i, row in enumerate(player.grid[:]):
            if all(cell != BLACK for cell in row):
                del player.grid[i]
                player.grid.insert(0, [BLACK for _ in range(len(row))])
                lines_cleared += 1

        if lines_cleared > 0:
            player.score += [40, 100, 300, 1200][lines_cleared - 1]
    
def main():
    game = TetrisGame()
    if not game.run():
        pygame.quit()

if __name__ == "__main__":
    main()