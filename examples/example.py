import pygame
from pathlib import Path
from editor import Editor
from tilemap_parser.map_loader import load_map
from tilemap_parser.renderer import TileLayerRenderer


pygame.init()


def main():
    screen = pygame.display.set_mode((1200, 700))
    script_dir = Path(__file__).parent
    map_path = script_dir / "map.json"

    parser = load_map(str(map_path))
    renderer = TileLayerRenderer(parser)
    renderer.warm_cache()

    pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        renderer.render(screen)
        pygame.display.flip()

    pygame.quit()


main()
