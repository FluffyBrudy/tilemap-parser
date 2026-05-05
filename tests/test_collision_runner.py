"""
Tests for tilemap_parser.collision_runner.

Covers:
- Geometry: point_in_polygon, rect_polygon_collision, circle_polygon_collision
- Runner: move_and_slide, move_platformer, move_rpg
- Edge cases: one-way platforms, slope sliding, corner collision
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.collision import (
    CollisionCache,
    CollisionPolygon,
    RectangleShape,
    CircleShape,
    CapsuleShape,
    TileCollisionData,
    TilesetCollision,
    load_tileset_collision,
)

from tilemap_parser.collision_runner import (
    CollisionRunner,
    MovementMode,
    point_in_polygon,
    rect_polygon_collision,
    circle_polygon_collision,
    get_shape_bounds,
    check_sprite_polygon_collision,
    _point_in_polygon_offset,
    _rect_polygon_collision_offset,
    _circle_polygon_collision_offset,
    _check_sprite_polygon_offset,
)


FIXTURES = Path(__file__).parent.parent / "examples" / "fixtures"
TILESET_COLLISION = FIXTURES / "collision" / "Terrain (32x32).collision.json"


FULL_TILE_POLY = [(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]
SLOPE_POLY = [(0.0, 32.0), (32.0, 0.0), (32.0, 32.0)]
HALF_TILE_POLY = [(0.0, 16.0), (32.0, 16.0), (32.0, 32.0), (0.0, 32.0)]


class MockSprite:
    def __init__(self, x=0, y=0, shape=None):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.collision_shape = shape or RectangleShape(width=24, height=32)


# ===========================================================================
# Geometry Tests: point_in_polygon
# ===========================================================================

class TestPointInPolygon:
    def test_point_outside_square(self):
        assert point_in_polygon((10, 10), FULL_TILE_POLY) is True
        assert point_in_polygon((-1, 10), FULL_TILE_POLY) is False
        assert point_in_polygon((10, -1), FULL_TILE_POLY) is False

    def test_point_on_edge(self):
        assert point_in_polygon((16, 0), FULL_TILE_POLY) is False

    def test_point_on_corner(self):
        assert point_in_polygon((0, 0), FULL_TILE_POLY) is False

    def test_triangle_slope(self):
        assert point_in_polygon((16, 24), SLOPE_POLY) is True
        assert point_in_polygon((8, 28), SLOPE_POLY) is True

    def test_offset_version(self):
        assert _point_in_polygon_offset(10, 10, FULL_TILE_POLY, 0, 0) is True
        assert _point_in_polygon_offset(10, 10, FULL_TILE_POLY, 100, 200) is False


# ===========================================================================
# Geometry Tests: rect_polygon_collision
# ===========================================================================

class TestRectPolygonCollision:
    def test_rect_inside_polygon(self):
        assert rect_polygon_collision(8, 8, 16, 16, FULL_TILE_POLY) is True

    def test_rect_outside_polygon(self):
        assert rect_polygon_collision(-10, -10, 8, 8, FULL_TILE_POLY) is False

    def test_rect_overlapping_edge(self):
        assert rect_polygon_collision(-8, 8, 16, 16, FULL_TILE_POLY) is True
        assert rect_polygon_collision(24, 8, 16, 16, FULL_TILE_POLY) is True

    def test_rect_with_offset(self):
        poly = [(100, 200), (132, 200), (132, 232), (100, 232)]
        assert rect_polygon_collision(108, 208, 16, 16, poly) is True


# ===========================================================================
# Geometry Tests: circle_polygon_collision
# ===========================================================================

class TestCirclePolygonCollision:
    def test_circle_center_inside(self):
        assert circle_polygon_collision((16, 16), 8, FULL_TILE_POLY) is True

    def test_circle_outside(self):
        assert circle_polygon_collision((-10, 16), 8, FULL_TILE_POLY) is False

    def test_circle_overlapping_edge(self):
        assert circle_polygon_collision((32, 16), 8, FULL_TILE_POLY) is True


# ===========================================================================
# Shape Bounds Tests
# ===========================================================================

class TestShapeBounds:
    def test_rectangle_bounds(self):
        sprite = MockSprite(x=100, y=200, shape=RectangleShape(width=24, height=32, offset=(4, 0)))
        left, top, right, bottom = get_shape_bounds(sprite)
        assert left == 104
        assert top == 200
        assert right == 128
        assert bottom == 232

    def test_circle_bounds(self):
        sprite = MockSprite(x=100, y=200, shape=CircleShape(radius=16, offset=(8, 4)))
        left, top, right, bottom = get_shape_bounds(sprite)
        assert left == 92
        assert top == 188
        assert right == 124
        assert bottom == 220

    def test_capsule_bounds(self):
        sprite = MockSprite(x=100, y=200, shape=CapsuleShape(radius=8, height=48, offset=(0, 0)))
        left, top, right, bottom = get_shape_bounds(sprite)
        assert left == 92
        assert top == 200
        assert right == 108
        assert bottom == 264


# ===========================================================================
# Runner: Setup Helpers
# ===========================================================================

def make_tileset_with_floor():
    tiles = {
        0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE_POLY)]),
        1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=HALF_TILE_POLY, one_way=True)]),
        2: TileCollisionData(tile_id=2, shapes=[CollisionPolygon(vertices=SLOPE_POLY)]),
    }
    return TilesetCollision(tileset_name="test", tile_size=(32, 32), tiles=tiles)


def make_tilemap_floor_only():
    tile_map = {}
    for x in range(10):
        for y in range(2):
            tile_map[(x, y)] = 0
    return tile_map


def make_tilemap_with_one_way():
    tile_map = {(5, 5): 1}
    return tile_map


# ===========================================================================
# Runner: move_and_slide Tests
# ===========================================================================

class TestMoveAndSlide:
    def setup_method(self):
        self.cache = CollisionCache()
        self.runner = CollisionRunner.from_game_type("topdown", self.cache, (32, 32))
        self.tileset = make_tileset_with_floor()

    def test_move_through_empty_space(self):
        tile_map = {}
        sprite = MockSprite(x=100, y=100)

        result = self.runner.move_and_slide(sprite, self.tileset, tile_map, 5, 5)

        assert result.final_x == 105
        assert result.final_y == 105

    def test_wall_block_x(self):
        tile_map = make_tilemap_floor_only()
        sprite = MockSprite(x=96, y=32)

        result = self.runner.move_and_slide(sprite, self.tileset, tile_map, 5, 0)

        assert result.final_x == 96

    def test_wall_block_y(self):
        tile_map = make_tilemap_floor_only()
        sprite = MockSprite(x=100, y=56)

        result = self.runner.move_and_slide(sprite, self.tileset, tile_map, 0, 5)

        assert result.final_y == 56


# ===========================================================================
# Runner: move_platformer Tests
# ===========================================================================

class TestMovePlatformer:
    def setup_method(self):
        self.cache = CollisionCache()
        self.runner = CollisionRunner.from_game_type("platformer", self.cache, (32, 32))
        self.tileset = make_tileset_with_floor()

    def test_gravity_applied(self):
        tile_map = {}
        sprite = MockSprite(x=100, y=100)
        sprite.vy = 0
        sprite.on_ground = False

        self.runner.move_platformer(sprite, self.tileset, tile_map, dt=0.016, input_x=0, jump_pressed=False)

        assert sprite.vy > 0


class TestMoveRpg:
    def setup_method(self):
        self.cache = CollisionCache()
        self.runner = CollisionRunner.from_game_type("rpg", self.cache, (32, 32))
        self.tileset = make_tileset_with_floor()

    def test_move_blocked_by_wall(self):
        tile_map = make_tilemap_floor_only()
        sprite = MockSprite(x=100, y=55)

        result = self.runner.move_rpg(sprite, self.tileset, tile_map, 5, 5)

        assert result.final_x == 100


# ===========================================================================
# Runner: One-Way Platforms
# ===========================================================================

class TestOneWayPlatforms:
    def setup_method(self):
        self.cache = CollisionCache()
        self.runner = CollisionRunner.from_game_type("platformer", self.cache, (32, 32))
        self.tileset = make_tileset_with_floor()

    def test_pass_through_from_below(self):
        tile_map = make_tilemap_with_one_way()
        sprite = MockSprite(x=150, y=140)
        sprite.vy = 100
        sprite.on_ground = False

        result = self.runner.move_platformer(sprite, self.tileset, tile_map, dt=0.016, input_x=0, jump_pressed=False)

        assert sprite.y > 140


class TestSlopeSlide:
    def setup_method(self):
        self.cache = CollisionCache()
        self.runner = CollisionRunner.from_game_type("topdown", self.cache, (32, 32))
        tiles = {2: TileCollisionData(tile_id=2, shapes=[CollisionPolygon(vertices=SLOPE_POLY)])}
        self.tileset = TilesetCollision(tileset_name="slope_test", tile_size=(32, 32), tiles=tiles)

    def test_slope_slide_works(self):
        tile_map = {(5, 5): 2}
        sprite = MockSprite(x=150, y=170)

        result = self.runner.move_and_slide(sprite, self.tileset, tile_map, 10, 10, slope_slide=True)

        assert result.collided is True


# ===========================================================================
# Integration: Realistic Map
# ===========================================================================

class TestRealisticMap:
    def setup_method(self):
        self.cache = CollisionCache()
        self.runner = CollisionRunner.from_game_type("topdown", self.cache, (32, 32))
        self.tileset = load_tileset_collision(TILESET_COLLISION)

    def test_load_fixture_tileset(self):
        assert self.tileset is not None
        assert self.tileset.tileset_name == "Terrain (32x32)"
        assert self.tileset.has_collision(26) is True
        assert self.tileset.has_collision(27) is True
        assert self.tileset.has_collision(8) is True

    def test_one_way_tile(self):
        assert self.tileset.has_collision(8) is True
        tile_data = self.tileset.tiles.get(8)
        assert tile_data is not None
        assert tile_data.shapes[0].one_way is True