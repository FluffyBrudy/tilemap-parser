import pygame
from tilemap_parser import load_character_collision
from tilemap_parser.runtime.collision_cache import CollisionCache
from tilemap_parser.runtime.tile_collision import CollisionRunner

from .entities.player import Player
from .settings import BASE_PATH_
from tilemap_parser.runtime.map_loader import TilemapData, load_map
from tilemap_parser.runtime.renderer import TileLayerRenderer


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.running = True

        map_data = load_map(BASE_PATH_ / "data" / "maps" / "1.json")
        self.renderer = TileLayerRenderer(map_data, include_hidden_layers=False)
        self.tilemap = self._build_tiles(map_data)

        self.collision_cache = CollisionCache()
        player_collision = self.collision_cache.get_character_collision(
            BASE_PATH_ / "data" / "character_collision" / "character.collision.json"
        )
        assert player_collision is not None
        self.player = Player(
            (400, 300),
            player_collision.shape,  # type: ignore
            BASE_PATH_ / "data" / "animations" / "player.animation.json",
        )
        self.collision_runner = CollisionRunner.from_game_type(
            "platformer", map_data.tile_size, True, map_data.render_scale
        )

    def _build_tiles(self, data: TilemapData):
        tile_map = {}
        for layer in data.parsed.layers:
            if layer.layer_type == "tile":
                for (tile_x, tile_y), tile in layer.tiles.items():
                    if isinstance(tile.ttype, int):
                        tile_map[(tile_x, tile_y)] = tile.variant
        return tile_map

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt: float):
        self.player.update(dt)
        self.collision_runner.move_platformer(
            self.player,
            self.collision_cache.get_tileset_collision(
                BASE_PATH_ / "data" / "collision" / "Pixel_Woods_Tileset.collision.json"  # type: ignore
            ),
            self.tilemap,
            dt,
            self.player.input_x,
            self.player.jump_pressed,
        )

    def render(self):
        self.screen.fill((0, 0, 0))
        self.renderer.render(self.screen)
        self.player.render(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.get_time() / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    Game().run()
