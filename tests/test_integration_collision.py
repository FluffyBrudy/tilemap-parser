from pathlib import Path

from tilemap_parser import (
    CollisionRunner,
    RectangleShape,
    CircleShape,
    load_tileset_collision,
    CollisionPolygon,
    TileCollisionData,
    TilesetCollision,
)

FIXTURES = Path(__file__).parent.parent / "examples" / "fixtures"
REAL_TILESET_COLLISION = FIXTURES / "collision" / "Terrain (32x32).collision.json"

FULL_TILE_POLY = [(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]
HALF_TILE_POLY = [(0.0, 16.0), (32.0, 16.0), (32.0, 32.0), (0.0, 32.0)]
SLOPE_POLY = [(0.0, 32.0), (32.0, 0.0), (32.0, 32.0)]


class SimpleSprite:
    def __init__(self, x=0, y=0, shape=None):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.collision_shape = shape or RectangleShape(width=24, height=32)


def make_tileset(tiles):
    return TilesetCollision(tileset_name="test", tile_size=(32, 32), tiles=tiles)


class TestFullPipelineCollision:
    def setup_method(self):
        self.runner = CollisionRunner.from_game_type("topdown", (32, 32))

    def test_move_through_empty_space(self):
        ts = make_tileset({0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE_POLY)])})
        tile_map = {(x, 0): 0 for x in range(10)}
        sprite = SimpleSprite(x=100, y=200)
        result = self.runner.move_and_slide(sprite, ts, tile_map, 5, 0)
        assert result.final_x == 105
        assert not result.collided

    def test_wall_blocks_movement(self):
        ts = make_tileset({0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE_POLY)])})
        tile_map = {(0, 0): 0}
        sprite = SimpleSprite(x=16, y=16)
        result = self.runner.move_and_slide(sprite, ts, tile_map, -10, 0)
        assert result.collided

    def test_platformer_gravity_and_ground(self):
        runner = CollisionRunner.from_game_type("platformer", (32, 32))
        ts = make_tileset({0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE_POLY)])})
        tile_map = {(0, 5): 0}
        sprite = SimpleSprite(x=4, y=127)
        result = runner.move_platformer(sprite, ts, tile_map, dt=0.016, input_x=0, jump_pressed=False)
        assert result.on_ground
        assert sprite.on_ground

    def test_one_way_platform_passes_upward(self):
        ts = make_tileset({1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=HALF_TILE_POLY, one_way=True)])})
        tile_map = {(5, 5): 1}
        sprite = SimpleSprite(x=160, y=130)
        result = self.runner.move_and_slide(sprite, ts, tile_map, 0, -10)
        assert not result.collided

    def test_one_way_platform_blocks_from_above(self):
        ts = make_tileset({1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=HALF_TILE_POLY, one_way=True)])})
        tile_map = {(5, 5): 1}
        sprite = SimpleSprite(x=160, y=144)
        result = self.runner.move_and_slide(sprite, ts, tile_map, 0, 10)
        assert result.collided

    def test_slope_collision(self):
        runner = CollisionRunner.from_game_type("topdown", (32, 32))
        ts = make_tileset({2: TileCollisionData(tile_id=2, shapes=[CollisionPolygon(vertices=SLOPE_POLY)])})
        tile_map = {(0, 0): 2}
        sprite = SimpleSprite(x=16, y=24)
        result = runner.move_and_slide(sprite, ts, tile_map, 5, 0, slope_slide=True)
        assert result.collided

    def test_rpg_mode_stops_at_wall(self):
        runner = CollisionRunner.from_game_type("rpg", (32, 32))
        ts = make_tileset({0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE_POLY)])})
        tile_map = {(0, 0): 0}
        sprite = SimpleSprite(x=20, y=16)
        result = runner.move_rpg(sprite, ts, tile_map, -10, 0)
        assert result.hit_wall_x

    def test_circle_shape_hits_wall(self):
        ts = make_tileset({0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE_POLY)])})
        tile_map = {(0, 0): 0}
        sprite = SimpleSprite(x=16, y=16, shape=CircleShape(radius=8))
        result = self.runner.move_and_slide(sprite, ts, tile_map, -10, 0)
        assert result.collided


class TestRealCollisionFixture:
    def test_load_real_tileset_collision(self):
        ts = load_tileset_collision(REAL_TILESET_COLLISION)
        assert ts is not None
        assert ts.tileset_name == "Terrain (32x32)"
        assert ts.tile_size == (32, 32)

    def test_real_collision_has_known_tiles(self):
        ts = load_tileset_collision(REAL_TILESET_COLLISION)
        assert ts.has_collision(26)
        assert ts.has_collision(27)
        assert ts.has_collision(8)

    def test_tile_8_is_one_way(self):
        ts = load_tileset_collision(REAL_TILESET_COLLISION)
        shapes = ts.get_world_shapes(8, 0, 0)
        assert len(shapes) == 1
        assert shapes[0].one_way is True

    def test_tile_26_is_full_block(self):
        ts = load_tileset_collision(REAL_TILESET_COLLISION)
        shapes = ts.get_world_shapes(26, 0, 0)
        assert len(shapes) == 1
        assert shapes[0].one_way is False

    def test_collision_with_real_fixture_data(self):
        ts = load_tileset_collision(REAL_TILESET_COLLISION)
        tile_map = {(5, 5): 26}
        sprite = SimpleSprite(x=160, y=160)
        runner = CollisionRunner.from_game_type("topdown", (32, 32))
        result = runner.move_and_slide(sprite, ts, tile_map, -1, 0)
        assert result.collided
