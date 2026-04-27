"""
Complete Platformer - Production Mode

A complete example showing map loading, collision, and rendering together.
This demonstrates a working platformer game loop.

USAGE: Run with tilemap-parser installed.

    pip install tilemap-parser
    python examples/05-complete-game/platformer_prod.py
"""

import pygame
from tilemap_parser import load_map
from tilemap_parser.collision import load_tileset_collision, RectangleShape
from tilemap_parser.collision_runner import CollisionRunner
from tilemap_parser.renderer import TileLayerRenderer


class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.collision_shape = RectangleShape(width=24, height=32)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False


def main():
    pygame.init()
    
    # Load map
    data = load_map("assets/maps/level_1.json")
    
    # Build tile map for collision
    tile_map = {}
    for layer in data.get_layers(layer_type="tile"):
        for (x, y), tile in layer.tiles.items():
            if isinstance(tile.ttype, int):
                tile_map[(x, y)] = tile.variant
    
    # Load collision
    tileset_collision = load_tileset_collision("assets/terrain.png")
    
    # Setup collision runner for platformer
    cache = load_tileset_collision  # Just use the function
    runner = CollisionRunner.from_game_type("platformer", None, data.tile_size)
    
    # Setup renderer
    renderer = TileLayerRenderer(data)
    renderer.warm_cache()
    
    # Player
    player = Player(100, 100)
    
    # Display
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
        
        # Input
        keys = pygame.key.get_pressed()
        input_x = 0.0
        jump = keys[pygame.K_SPACE]
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            input_x = -1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            input_x = 1.0
        
        # Move
        if tileset_collision:
            result = runner.move(
                player,
                tileset_collision,
                tile_map,
                dt=dt,
                input_x=input_x * player.speed,
                jump_pressed=jump
            )
        else:
            player.x += input_x * 200 * dt
            player.vy = min(player.vy + 800 * dt, 600)
            player.y += player.vy * dt
        
        # Camera
        cam_x = player.x - 640
        cam_y = player.y - 360
        
        # Render
        screen.fill((20, 20, 30))
        renderer.render(screen, camera_xy=(cam_x, cam_y))
        
        # Player debug
        pygame.draw.rect(
            screen, (100, 200, 255),
            (player.x - cam_x, player.y - cam_y, 24, 32), 2
        )
        
        # FPS
        font = pygame.font.Font(None, 20)
        screen.blit(font.render(f"FPS: {clock.get_fps():.0f}", True, (200, 200, 200)), (10, 10))
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()