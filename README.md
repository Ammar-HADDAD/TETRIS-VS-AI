# eTetris

A modern Tetris game implementation featuring single-player mode against an AI opponent, complete with score tracking, game history, and a polished user interface.

## Author

**Ammar HADDAD**  
Contact: ammarhaddad@outlook.fr

## Overview

eTetris is a Python-based Tetris game that pits human players against an intelligent AI opponent. The game features a sleek, full-screen interface with real-time scoring, persistent data storage, and dynamic difficulty scaling.

## Features

### Core Gameplay
- Classic Tetris mechanics with seven standard tetromino shapes
- Simultaneous human vs AI gameplay with separate grids
- Progressive difficulty system with increasing fall speeds
- Real-time score tracking and display

### AI Opponent
- Heuristic-based decision making
- Evaluates board state using multiple metrics (height, holes, bumpiness)
- Adaptive piece placement and rotation strategies

### User Interface
- Full-screen display optimized for 1920x1080 resolution
- Clean, modern design with custom color schemes
- Intuitive navigation and controls
- Pause and restart functionality
- Background music with mute controls

### Data Persistence
- SQLite database integration for score storage
- Leaderboard displaying top 10 players
- Complete game history tracking
- Records include player names, scores, survival time, and timestamps

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Required Dependencies

```bash
pip install pygame numpy
```

### Additional Requirements
- Place a music file named `music.mp3` in the `src/` directory (optional)
- Ensure sufficient disk space for database storage

## Project Structure

```
eTetris/
├── main.py                    # Main game file
├── src/
│   ├── music.mp3             # Background music (optional)
│   └── tetris_database.db    # SQLite database (auto-generated)
└── README.md
```

## Controls

### Gameplay
- **Arrow Left**: Move piece left
- **Arrow Right**: Move piece right
- **Arrow Down**: Soft drop (increase fall speed)
- **Arrow Up**: Rotate piece clockwise

### System Controls
- **ESC**: Exit game or return to menu
- **SPACE**: Mute/unmute background music
- **P**: Pause/unpause game
- **R**: Restart current game (with confirmation)
- **M**: Return to main menu (from game over screen)

### Menu Navigation
- **Arrow Left/Right**: Navigate between menu options
- **ENTER**: Confirm selection or start game

## Game Modes

### Main Menu Options

1. **Play**: Start a new game against the AI
   - Enter username (up to 12 characters)
   - Compete for high scores

2. **Leaderboard**: View top 10 high scores
   - Displays rank, username, score, survival time, and date
   - Excludes AI scores for fair competition

3. **Game History**: Review recent game sessions
   - Shows last 10 games with rankings
   - Includes both human and AI performance data

## Scoring System

Points are awarded based on lines cleared simultaneously:

- 1 line: 40 points
- 2 lines: 100 points
- 3 lines: 300 points
- 4 lines (Tetris): 1200 points

## AI Algorithm

The AI opponent uses a heuristic evaluation system that considers:

- **Board Height**: Minimizes the maximum column height
- **Holes**: Counts empty cells below filled cells
- **Bumpiness**: Measures height variation between adjacent columns

The AI simulates all possible piece placements and rotations, selecting the move that minimizes the weighted sum of these metrics.

## Database Schema

### Scores Table
```sql
CREATE TABLE scores (
    id INTEGER PRIMARY KEY,
    username TEXT,
    score INTEGER,
    survival_time REAL,
    date TEXT
)
```

### Game History Table
```sql
CREATE TABLE game_history (
    id INTEGER PRIMARY KEY,
    username TEXT,
    winner TEXT,
    human_score INTEGER,
    ai_score INTEGER,
    survival_time REAL,
    date TEXT
)
```

## Technical Details

### Performance Specifications
- Target frame rate: 60 FPS
- Grid size: 10 columns x 20 rows
- Block size: 30 pixels
- Initial fall speed: 0.3 seconds per row
- Speed increase: 10% reduction every 10 seconds

### Color Scheme
- I-piece: Cyan
- Square: Gold
- T-piece: Purple
- L-piece: Dark Orange
- Reverse L: Dodger Blue
- S-piece: Lime Green
- Z-piece: Crimson

## Known Limitations

- Fixed screen resolution (1920x1080 fullscreen)
- Single AI difficulty level
- Music file must be manually provided
- Database stored locally only

## Future Enhancements

Potential improvements for future versions:

- Multiple difficulty levels for AI opponent
- Online leaderboards and multiplayer
- Customizable controls and themes
- Mobile device support
- Achievement system
- Replay functionality

## Troubleshooting

### Music Not Playing
Ensure `music.mp3` exists in the `src/` directory. The game will continue without music if the file is missing.

### Database Errors
The game automatically creates the database file. If issues persist, delete `tetris_database.db` to regenerate it.

### Display Issues
The game is optimized for 1920x1080 resolution. Lower resolutions may cause visual overlap or truncation.

## License

This project is provided as-is for educational and entertainment purposes.

## Contributing

For bug reports, feature requests, or contributions, please contact the author directly.

---

**Version**: 1.0  
**Last Updated**: 2025  
**Python Version**: 3.7+