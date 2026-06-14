from typing import cast

import pygame
from tilemap_parser import (
    CollisionRunner,
    TileLayerRenderer,
    TilesetCollision,
    load_map,
)
from tilemap_parser.runtime.collision_cache import _global_cache
from .settings import *
from .entities import Player
from .utils.debug import Debug, pgdebug

MAP_PATH = BASE_PATH / "data" / "maps"


class Game:
    __slots__ = (
        "screen",
        "clock",
        "running",
        "collision_runner",
        "collision_tileset",
        "tile_renderer",
        "player",
        "tilemap",
    )

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Platformer")

        self.clock = pygame.time.Clock()
        self.running = True

        self._preload()

    def _preload(self):
        mapdata = load_map(MAP_PATH / "1.json")
        self.collision_tileset = cast(
            TilesetCollision,
            _global_cache.get_tileset_collision(
                COLLISION_TILESET_PATH
                / "Foozle_2DT0008_GreenValley_Tileset_Pixel_Art.collision.json"
            ),
        )
        self.tile_renderer = TileLayerRenderer(data=mapdata)
        self.collision_runner = CollisionRunner.from_game_type(
            "platformer",
            mapdata.tile_size,
            strict=True,
            render_scale=mapdata.render_scale,
        )
        self.collision_runner.jump_strength = -550
        self.player = Player(300, HEIGHT // 2)
        self.tilemap = mapdata.build_tile_map()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt):
        self.player.update(dt)
        self.collision_runner.move_platformer_with_slide(
            self.player,
            self.collision_tileset,
            self.tilemap,
            dt,
            self.player.input_x,
            self.player.jump_pressed,
            self.player.velocity_override,
        )

    def draw(self):
        camera = (
            (self.player.x - WIDTH // 2),
            (self.player.y - HEIGHT // 2),
        )
        self.screen.fill(BLACK)
        self.tile_renderer.render(self.screen, camera)
        self.player.render(self.screen, camera)
        Debug.draw_all(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    Game().run()
