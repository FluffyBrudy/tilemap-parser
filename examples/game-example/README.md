# Tilemap-Parser Game Example

A complete game example demonstrating all major features of the tilemap-parser library.

## Features Demonstrated

- **Map Loading**: Load and parse tilemap data from JSON
- **Tile Rendering**: Efficient tile rendering with camera system using `TileLayerRenderer`
- **Collision Detection**: Polygon-based collision detection with `CollisionRunner`
- **Collision Response**: Smooth sliding movement along walls
- **Sprite Animation**: Frame-based sprite animation with `AnimationPlayer`
- **Player Movement**: Top-down 8-directional movement with collision

## Requirements

- Python 3.8+
- pygame
- tilemap-parser (this package)

## Installation

From the repository root:

```bash
# Install the package in development mode
pip install -e .

# Or install pygame separately if needed
pip install pygame
```

## Running the Game

From the `examples/game-example` directory:

```bash
python src/game.py
```

Or from the repository root:

```bash
python examples/game-example/src/game.py
```

## Controls

- **WASD** or **Arrow Keys**: Move the player
- **F1**: Toggle debug information
- **ESC**: Quit the game

## Project Structure

```
game-example/
├── src/
│   └── game.py           # Main game code
├── data/
│   ├── map.json          # Tilemap data
│   ├── collision/
│   │   └── HiddenJungle_PNG.collision.json  # Tile collision data
│   └── RACCOONSPRITESHEET.anim.json         # Player animations
├── assets/
│   ├── HiddenJungle_PNG.png                 # Tileset image
│   └── RACCOONSPRITESHEET.png               # Player sprite sheet
├── settings.json         # Game settings (paths, etc.)
└── README.md            # This file
```

## Code Overview

### Player Class

The `Player` class implements the `ICollidableSprite` protocol required by the collision system:

```python
class Player:
    x: float                    # World X position
    y: float                    # World Y position
    collision_shape: RectangleShape  # Collision shape
    vx: float                   # X velocity
    vy: float                   # Y velocity
    on_ground: bool            # Ground state (for platformers)
```

### Game Systems

1. **Map Loading**
   ```python
   game_data = load_map("data/map.json")
   ```

2. **Renderer Setup**
   ```python
   renderer = TileLayerRenderer(game_data)
   renderer.warm_cache()  # Preload tiles for performance
   ```

3. **Collision System**
   ```python
   collision_cache = CollisionCache()
   tileset_collision = collision_cache.get_tileset_collision(
       "data/collision/HiddenJungle_PNG.collision.json"
   )
   collision_runner = CollisionRunner.from_game_type(
       'topdown', collision_cache, tile_size
   )
   ```

4. **Movement with Collision**
   ```python
   result = collision_runner.move_and_slide(
       player, tileset_collision, tile_map,
       delta_x, delta_y, slope_slide=True
   )
   ```

5. **Rendering**
   ```python
   # Render tilemap
   renderer.render(screen, camera_xy=(camera_x, camera_y))
   
   # Render player
   player.render(screen, camera_x, camera_y)
   ```

## Customization

### Adjusting Player Speed

In `game.py`, modify the `speed` variable in the `update()` method:

```python
speed = 100.0  # pixels per second
```

### Changing Collision Shape

Modify the player's collision shape in the `Player.__init__()` method:

```python
# Rectangle: width, height, offset
self.collision_shape = RectangleShape(12, 12, offset=(-6, -6))

# Circle: radius, offset
self.collision_shape = CircleShape(6, offset=(0, 0))

# Capsule: radius, height, offset
self.collision_shape = CapsuleShape(6, 12, offset=(0, 0))
```

### Enabling/Disabling Slope Sliding

In the `move_and_slide()` call:

```python
# Smooth sliding along walls
result = collision_runner.move_and_slide(
    player, tileset_collision, tile_map,
    delta_x, delta_y, slope_slide=True
)

# Block at walls (no sliding)
result = collision_runner.move_and_slide(
    player, tileset_collision, tile_map,
    delta_x, delta_y, slope_slide=False
)
```

## Debug Information

Press **F1** to toggle debug overlay showing:

- FPS (frames per second)
- Player world position
- Player tile position
- Red collision box around player
- Control hints

## Troubleshooting

### "No module named 'tilemap_parser'"

Make sure you've installed the package:
```bash
pip install -e .
```

### "pygame.error: Couldn't open ..."

Make sure you're running the game from the correct directory. The game expects to find the `data/` and `assets/` folders relative to the current working directory.

### Player moves through walls

Check that:
1. Collision data is loaded correctly (check console output)
2. The tile_map is built correctly from your map data
3. The tile variant IDs in your map match the collision data

## Learning Resources

- [tilemap-parser Documentation](../../README.md)
- [Collision System Guide](../../docs/collision.md)
- [Animation System Guide](../../docs/animation.md)

## License

This example is part of the tilemap-parser project and is provided as-is for educational purposes.
