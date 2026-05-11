# Animation Only Example

This example demonstrates how to load and play sprite animations using tilemap-parser without any game logic or collision detection.

## Features
- Load sprite animations from JSON
- Play animations using AnimationPlayer
- Simple pygame loop to display animation
- No collision or game mechanics

## Requirements
- Python 3.10+
- pygame-ce
- tilemap-parser (install with `pip install tilemap-parser`)

## Files
- `animation.py`: Main script that loads and plays the animation
- `data/RACCOONSPRITESHEET.anim.json`: Animation definition
- `assets/RACCOONSPRITESHEET.png`: Sprite sheet image

## How to Run
1. Install requirements: `pip install -r requirements.txt`
2. Run the script: `python animation.py`

## Controls
- Close the window to exit

## Code Explanation
The script does the following:
1. Initializes pygame
2. Loads the sprite animation set from JSON
3. Creates an AnimationPlayer for the "idledown" animation
4. In the game loop:
   - Updates the animation with delta time
   - Renders the current frame centered on screen
   - Handles quit events

This is the minimal setup needed to use tilemap-parser's animation system.