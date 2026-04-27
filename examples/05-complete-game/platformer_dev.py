"""
Complete Platformer - Development Mode

A complete example showing map loading, collision, and rendering together.
This demonstrates a working platformer game loop.

USAGE: Run from repository root with local source.

    python examples/05-complete-game/platformer_dev.py
"""

import sys
from pathlib import Path

# Add local source to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pygame
from tilemap_parser import load_map
from tilemap_parser.collision import (
    CollisionCache, RectangleShape,
    TilesetCollision, parse_tileset_collision
)
from tilemap_parser.collision_runner import CollisionRunner, MovementMode


class Player:
    """Simple player with collision shape for CollisionRunner"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.collision_shape = RectangleShape(width=24, height=32)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.speed = 200
        self.color = (100, 200, 255)


def main():
    pygame.init()
    
    script_dir = Path(__file__).parent.parent.parent / "examples"
    map_path = script_dir / "map.json"
    
    if not map_path.exists():
        print(f"Map not found: {map_path}")
        return
    
    # Load map
    data = load_map(str(map_path))
    print(f"Map loaded: {data.tile_size}, {data.map_size}")
    
    # Build tile map (tile_id by position)
    tile_map = {}
    for layer in data.get_layers(layer_type="tile"):
        for (x, y), tile in layer.tiles.items():
            if isinstance(tile.ttype, int):
                tile_map[(x, y)] = tile.variant
    
    print(f"Tile map: {len(tile_map)} tiles")
    
    # Load collision data
    collision_path = script_dir / "collision_data.json"
    tileset_collision = None
    if collision_path.exists():
        import json
        with open(collision_path) as f:
            collision_data = json.load(f)
        tileset_collision = parse_tileset_collision(collision_data)
        print(f"Collision loaded: {len(tileset_collision.tiles)} tiles")
    
    # Create collision runner
    cache = CollisionCache()
    runner = CollisionRunner.from_game_type("platformer", cache, data.tile_size)
    
    # Create player
    player = Player(100, 100)
    
    # Setup rendering
    from tilemap_parser.renderer import TileLayerRenderer
    renderer = TileLayerRenderer(data)
    renderer.warm_cache()
    
    # Display
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    
    print("\nControls: Arrow keys/WASD to move, Space to jump, ESC to quit")
    
    camera_x, camera_y = 0, 0
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Input
        keys = pygame.key.get_pressed()
        input_x = 0.0
        jump_pressed = False
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            input_x = -1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            input_x = 1.0
        if keys[pygame.K_SPACE]:
            jump_pressed = True
        
        # Move with collision
        if tileset_collision:
            result = runner.move(
                player,
                tileset_collision,
                tile_map,
                dt=dt,
                input_x=input_x,
                jump_pressed=jump_pressed
            )
            
            # Color feedback
            if player.on_ground:
                player.color = (100, 255, 100)
            else:
                player.color = (100, 200, 255)
        else:
            # No collision - just move
            player.x += input_x * player.speed * dt
            player.y += player.vy * dt
            player.vy = min(player.vy + runner.gravity * dt, runner.max_fall_speed)
        
        # Camera follow
        camera_x = player.x - 400
        camera_y = player.y - 300
        
        # Render
        screen.fill((30, 30, 50))
        renderer.render(screen, camera_xy=(camera_x, camera_y))
        
        # Draw player
        px = player.x - camera_x
        py = player.y - camera_y
        w = player.collision_shape.width
        h = player.collision_shape.height
        pygame.draw.rect(screen, player.color, (px, py, w, h), 2)
        
        # HUD
        font = pygame.font.Font(None, 24)
        texts = [
            f"Position: ({player.x:.0f}, {player.y:.0f})",
            f"On ground: {player.on_ground}",
            f"VY: {player.vy:.0f}",
        ]
        for i, text in enumerate(texts):
            surf = font.render(text, True, (255, 255, 255))
            screen.blit(surf, (10, 10 + i * 25))
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()