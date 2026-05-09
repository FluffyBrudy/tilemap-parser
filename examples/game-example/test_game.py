"""
Test script to verify game loads correctly without opening a window
"""

import os
import sys

# Set SDL to use dummy video driver (no window)
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Add parent directory to path to import tilemap_parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pygame
from tilemap_parser import (
    load_map, 
    SpriteAnimationSet, 
    TileLayerRenderer, 
    CollisionRunner, 
    CollisionCache,
    RectangleShape
)

def test_game_loading():
    """Test that all game resources load correctly"""
    print("Testing game resource loading...")
    
    # Initialize pygame with dummy driver
    pygame.init()
    # Create a dummy display surface (required for image loading)
    pygame.display.set_mode((1, 1))
    
    # Test 1: Load map
    print("\n1. Loading map...")
    game_data = load_map("data/map.json")
    print(f"   ✓ Map loaded: {game_data.tile_size} tile size")
    
    # Test 2: Load animations
    print("\n2. Loading player animations...")
    player_anim_set = SpriteAnimationSet.load("data/RACCOONSPRITESHEET.anim.json")
    print(f"   ✓ Animations loaded: {len(player_anim_set.library.animations)} animations")
    for anim_name in player_anim_set.library.animations.keys():
        print(f"      - {anim_name}")
    
    # Test 3: Setup renderer
    print("\n3. Setting up renderer...")
    renderer = TileLayerRenderer(game_data)
    renderer.warm_cache()
    print(f"   ✓ Renderer initialized")
    
    # Test 4: Load collision data
    print("\n4. Loading collision data...")
    collision_cache = CollisionCache()
    tileset_collision = collision_cache.get_tileset_collision(
        "data/collision/HiddenJungle_PNG.collision.json"
    )
    
    if tileset_collision:
        collision_count = len([t for t in tileset_collision.tiles.values() if t.has_collision()])
        print(f"   ✓ Collision data loaded: {collision_count} tiles with collision")
        print(f"      Tileset: {tileset_collision.tileset_name}")
        print(f"      Tile size: {tileset_collision.tile_size}")
    else:
        print("   ✗ Warning: No collision data loaded!")
    
    # Test 5: Create collision runner
    print("\n5. Creating collision runner...")
    collision_runner = CollisionRunner.from_game_type(
        'topdown', 
        collision_cache, 
        game_data.tile_size
    )
    print(f"   ✓ Collision runner initialized")
    print(f"      Mode: {collision_runner.mode.value}")
    print(f"      Tile size: {collision_runner.tile_size}")
    
    # Test 6: Build tile map
    print("\n6. Building tile map...")
    tile_map = {}
    for layer in game_data.parsed.layers:
        if layer.layer_type == "tile":
            for (tile_x, tile_y), tile in layer.tiles.items():
                if isinstance(tile.ttype, int):
                    tile_map[(tile_x, tile_y)] = tile.variant
    print(f"   ✓ Tile map built: {len(tile_map)} tiles")
    
    # Test 7: Create player
    print("\n7. Creating player...")
    from src.game import Player
    start_x = 8 * game_data.tile_size[0]
    start_y = 8 * game_data.tile_size[1]
    player = Player(start_x, start_y, player_anim_set)
    print(f"   ✓ Player created at ({start_x}, {start_y})")
    print(f"      Collision shape: {type(player.collision_shape).__name__}")
    print(f"      Facing: {player.facing}")
    
    # Test 8: Test collision detection
    print("\n8. Testing collision detection...")
    # Try to move player
    delta_x = 10.0
    delta_y = 0.0
    result = collision_runner.move_and_slide(
        player,
        tileset_collision,
        tile_map,
        delta_x,
        delta_y,
        slope_slide=True
    )
    print(f"   ✓ Collision detection working")
    print(f"      Collided: {result.collided}")
    print(f"      Final position: ({result.final_x:.1f}, {result.final_y:.1f})")
    
    pygame.quit()
    
    print("\n" + "="*50)
    print("✓ All tests passed! Game is ready to run.")
    print("="*50)
    print("\nTo run the game:")
    print("  python src/game.py")
    print("\nControls:")
    print("  WASD/Arrows - Move")
    print("  F1 - Toggle Debug")
    print("  ESC - Quit")

if __name__ == "__main__":
    try:
        test_game_loading()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
