"""
Tile Rendering - Production Mode

USAGE: Run with tilemap-parser installed.

    pip install tilemap-parser
    python examples/04-rendering/tile_renderer_prod.py
"""

import pygame
from tilemap_parser import load_map
from tilemap_parser.renderer import TileLayerRenderer


def main():
    pygame.init()
    
    # Load map from assets
    data = load_map("assets/maps/level_1.json")
    
    # Create renderer
    renderer = TileLayerRenderer(data)
    renderer.warm_cache()  # Call once at startup
    
    # Display setup
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    
    # Game camera
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
        
        # Movement
        keys = pygame.key.get_pressed()
        speed = 300
        if keys[pygame.K_LEFT]: camera_x -= speed * dt
        if keys[pygame.K_RIGHT]: camera_x += speed * dt
        if keys[pygame.K_UP]: camera_y -= speed * dt
        if keys[pygame.K_DOWN]: camera_y += speed * dt
        
        # Render
        screen.fill((20, 20, 30))
        
        stats = renderer.render(
            screen,
            camera_xy=(camera_x, camera_y),
            viewport_size=(1280, 720)
        )
        
        # Performance stats
        font = pygame.font.Font(None, 20)
        fps_text = font.render(f"FPS: {clock.get_fps():.0f}", True, (200, 200, 200))
        stats_text = font.render(
            f"Drawn: {stats.drawn_tiles} | Visible layers: {stats.visible_layers}",
            True, (150, 150, 150)
        )
        screen.blit(fps_text, (10, 10))
        screen.blit(stats_text, (10, 30))
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()