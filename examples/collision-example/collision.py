"""
Collision Only Example
Demonstrate collision detection using tilemap-parser without animations
"""

import pygame
import sys
from pathlib import Path
from tilemap_parser import (
    load_map, 
    SpriteAnimationSet,  # Not used but imported for completeness
    TileLayerRenderer, 
    CollisionRunner, 
    CollisionCache,
    RectangleShape
)

# We don't need animations for this example, but we'll keep the import structure similar

def main():
    # Initialize pygame
    pygame.init()
    
    # Screen setup
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("tilemap-parser - Collision Example")
    clock = pygame.time.Clock()
    target_fps = 60
    
    # Load game data (map)
    game_data = load_map("data/map.json")
    print(f"Map loaded: {game_data.tile_size} tile size")
    
    # Setup renderer (we'll render the tilemap but no sprites)
    renderer = TileLayerRenderer(game_data)
    # Note: We don't warm_cache because it's not necessary for this example and might break in some contexts
    # The renderer will cache tiles on-demand during rendering.
    
    # Setup collision system
    collision_cache = CollisionCache()
    tileset_collision = collision_cache.get_tileset_collision(
        "data/collision/HiddenJungle_PNG.collision.json"
    )
    
    if tileset_collision:
        collision_count = len([t for t in tileset_collision.tiles.values() if t.has_collision()])
        print(f"Collision data loaded: {collision_count} tiles with collision")
    else:
        print("Warning: No collision data loaded!")
        return
    
    # Create collision runner for top-down movement
    collision_runner = CollisionRunner.from_game_type(
        'topdown', 
        collision_cache, 
        game_data.tile_size
    )
    print("Collision runner initialized for top-down movement")
    
    # Build tile map for collision detection (we need this for the collision runner)
    tile_map = {}
    for layer in game_data.parsed.layers:
        if layer.layer_type == "tile":
            for (tile_x, tile_y), tile in layer.tiles.items():
                if isinstance(tile.ttype, int):
                    tile_map[(tile_x, tile_y)] = tile.variant
    
    print(f"Tile map built: {len(tile_map)} tiles")
    
    # Create a simple player (rectangle) at a starting position without collision
    # We'll use a RectangleShape for collision, but render as a simple rectangle
    start_x = 5.5 * game_data.tile_size[0]  # Center of tile (5,5) approximately
    start_y = 5.5 * game_data.tile_size[1]
    player = RectangleShape(12, 12, offset=(-6, -6))  # 12x12 rectangle centered
    player_x = float(start_x)
    player_y = float(start_y)
    
    # Game state
    running = True
    show_debug = True  # Toggle with F1
    
    # Main loop
    while running:
        # Calculate delta time
        dt = clock.tick(target_fps) / 1000.0  # seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F1:
                    show_debug = not show_debug
        
        # Get input for movement
        keys = pygame.key.get_pressed()
        input_x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        input_y = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        
        # Normalize diagonal movement
        if input_x != 0 and input_y != 0:
            input_x *= 0.7071  # 1/sqrt(2)
            input_y *= 0.7071
        
        # Apply movement with collision
        speed = 100.0  # pixels per second
        delta_x = input_x * speed * dt
        delta_y = input_y * speed * dt
        
        if delta_x != 0 or delta_y != 0:
            # We need to create a temporary object that has the required attributes for CollisionRunner
            # The CollisionRunner expects an object with x, y, collision_shape, vx, vy, on_ground
            class MovableRect:
                def __init__(self, x, y, shape):
                    self.x = x
                    self.y = y
                    self.collision_shape = shape
                    self.vx = 0.0
                    self.vy = 0.0
                
                @property
                def on_ground(self):
                    return False  # Not used in top-down mode
            
            movable_player = MovableRect(player_x, player_y, player)
            
            # Move with collision detection
            result = collision_runner.move_and_slide(
                movable_player,
                tileset_collision,
                tile_map,
                delta_x,
                delta_y,
                slope_slide=True
            )
            
            # Update player position
            player_x = result.final_x
            player_y = result.final_y
        
        # Clear screen
        screen.fill((50, 50, 80))  # Dark blue background
        
        # Calculate camera position (center on player)
        camera_x = player_x - screen_width // 2
        camera_y = player_y - screen_height // 2
        
        # Render tilemap
        renderer.render(screen, camera_xy=(camera_x, camera_y))
        
        # Render player (as a white rectangle)
        player_rect = pygame.Rect(
            player_x - 6 - camera_x,  # x - offset - camera
            player_y - 6 - camera_y,  # y - offset - camera
            12,  # width
            12   # height
        )
        pygame.draw.rect(screen, (255, 255, 255), player_rect)
        
        # Render debug info
        if show_debug:
            # Draw collision boxes for tiles that have collision (for debugging)
            # We'll sample a few tiles around the player to avoid drawing too many
            tile_size = game_data.tile_size
            player_tile_x = int(player_x // tile_size[0])
            player_tile_y = int(player_y // tile_size[1])
            
            # Draw a 10x10 grid of tiles around the player
            for tx in range(player_tile_x - 5, player_tile_x + 6):
                for ty in range(player_tile_y - 5, player_tile_y + 6):
                    if (tx, ty) in tile_map:
                        tile_variant = tile_map[(tx, ty)]
                        # Check if this tile has collision in our collision data
                        if tx < tileset_collision.tileset_width and ty < tileset_collision.tileset_height:
                            tile_data = tileset_collision.tiles.get((tx, ty))
                            if tile_data and tile_data.has_collision():
                                # Draw a green box for collision tiles
                                debug_rect = pygame.Rect(
                                    tx * tile_size[0] - camera_x,
                                    ty * tile_size[1] - camera_y,
                                    tile_size[0],
                                    tile_size[1]
                                )
                                pygame.draw.rect(screen, (0, 255, 0), debug_rect, 1)
            
            # Draw player collision box (red)
            bounds = player.get_bounds(player_x, player_y)
            debug_rect = pygame.Rect(
                bounds[0] - camera_x,
                bounds[1] - camera_y,
                bounds[2] - bounds[0],
                bounds[3] - bounds[1]
            )
            pygame.draw.rect(screen, (255, 0, 0), debug_rect, 1)
            
            # Draw text debug info
            font = pygame.font.Font(None, 24)
            small_font = pygame.font.Font(None, 18)
            
            # FPS
            fps = int(clock.get_fps())
            fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
            screen.blit(fps_text, (10, 10))
            
            # Player position
            pos_text = small_font.render(
                f"Position: ({int(player_x)}, {int(player_y)})", 
                True, (255, 255, 255)
            )
            screen.blit(pos_text, (10, 35))
            
            # Tile position
            tile_x = int(player_x // game_data.tile_size[0])
            tile_y = int(player_y // game_data.tile_size[1])
            tile_text = small_font.render(
                f"Tile: ({tile_x}, {tile_y})", 
                True, (255, 255, 255)
            )
            screen.blit(tile_text, (10, 55))
            
            # Controls
            controls = [
                "Controls:",
                "WASD/Arrows - Move",
                "F1 - Toggle Debug",
                "ESC - Quit"
            ]
            y_offset = screen_height - 90
            for line in controls:
                text = small_font.render(line, True, (200, 200, 200))
                screen.blit(text, (10, y_offset))
                y_offset += 20
        
        # Update display
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()