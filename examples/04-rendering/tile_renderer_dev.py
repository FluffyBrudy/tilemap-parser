"""
Tile Rendering - Development Mode

USAGE: Run from repository root with local source.

    python examples/04-rendering/tile_renderer_dev.py
"""

import sys
from pathlib import Path

# Add local source to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pygame
from tilemap_parser import load_map
from tilemap_parser.renderer import TileLayerRenderer


def main():
    pygame.init()
    
    script_dir = Path(__file__).parent.parent.parent / "examples"
    map_path = script_dir / "map.json"
    
    if not map_path.exists():
        print(f"Map not found: {map_path}")
        return
    
    # Load map data
    data = load_map(str(map_path))
    
    # Create renderer
    renderer = TileLayerRenderer(data)
    
    # Pre-load all tile surfaces for better performance
    print("Warming cache...")
    renderer.warm_cache()
    print("Cache warmed.")
    
    # Create display
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    
    # Simple camera
    camera_x, camera_y = 0, 0
    running = True
    
    print("\nControls: Arrow keys to move, ESC to quit")
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_LEFT:
                    camera_x -= 100 * dt
                elif event.key == pygame.K_RIGHT:
                    camera_x += 100 * dt
                elif event.key == pygame.K_UP:
                    camera_y -= 100 * dt
                elif event.key == pygame.K_DOWN:
                    camera_y += 100 * dt
        
        # Render
        screen.fill((30, 30, 40))
        
        stats = renderer.render(
            screen,
            camera_xy=(camera_x, camera_y),
            viewport_size=(800, 600)
        )
        
        # Draw stats
        font = pygame.font.Font(None, 24)
        info = [
            f"FPS: {clock.get_fps():.0f}",
            f"Camera: ({camera_x:.0f}, {camera_y:.0f})",
            f"Drawn: {stats.drawn_tiles}, Skipped: {stats.skipped_tiles}",
        ]
        for i, text in enumerate(info):
            surf = font.render(text, True, (255, 255, 255))
            screen.blit(surf, (10, 10 + i * 25))
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()