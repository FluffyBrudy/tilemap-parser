# Collision Only Example

This example demonstrates how to use the tilemap-parser collision system without any animations or complex game logic.

## Features
- Load a tilemap and collision data
- Create a simple player (rectangle) that can move with WASD/arrow keys
- Collision detection and response using CollisionRunner
- Debug rendering showing collision tiles and player collision box
- No animations or sprite rendering

## Requirements
- Python 3.10+
- pygame-ce
- tilemap-parser (install with `pip install tilemap-parser`)

## Files
- `collision.py`: Main script that sets up the collision demonstration
- `data/map.json`: Tilemap data (from game example)
- `data/collision/HiddenJungle_PNG.collision.json`: Collision data (from game example)
- `assets/HiddenJungle_PNG.png`: Tileset image (from game example)

## How to Run
1. Install requirements: `pip install -r requirements.txt`
2. Run the script: `python collision.py`

## Controls
- WASD or Arrow keys: Move the player (white rectangle)
- F1: Toggle debug information (shows FPS, position, tile coordinates)
- ESC: Quit

## Code Explanation
The script does the following:
1. Initializes pygame and loads the tilemap and collision data
2. Sets up a CollisionRunner for top-down movement
3. Creates a simple player rectangle at a starting position
4. In the game loop:
   - Handles input for movement
   - Updates player position with collision detection
   - Renders the tilemap, player, and debug information
5. The player is represented by a white rectangle, and its collision box is shown in red when debug is enabled
6. Collision tiles are highlighted in green when debug is enabled

This example focuses purely on the collision system, showing how to integrate tilemap-parser's collision detection into a simple pygame project.