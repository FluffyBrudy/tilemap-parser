"""Tests for CollisionRunner.move_grounded().

Covers:
- Movement through empty space
- Wall blocking (X collision)
- Ground collision with full tiles
- Ground collision with partial tiles (half-height collision polygon)
- Ceiling collision
- Ledge detection (walk off edge while grounded)
- Explicit velocity mode (no gravity, flying enemies)
- Ground snap / binary search precision
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from tilemap_parser.parser.collision import (
    CollisionPolygon,
    RectangleShape,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.movement import CollisionRunner

FULL_TILE_POLY = [(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]
HALF_TILE_POLY = [(0.0, 16.0), (32.0, 16.0), (32.0, 32.0), (0.0, 32.0)]
SLOPE_POLY = [(0.0, 32.0), (32.0, 0.0), (32.0, 32.0)]


class MockSprite:
    def __init__(self, x=0, y=0, shape=None):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.collision_shape = shape or RectangleShape(width=24, height=32)


def make_tileset():
    tiles = {
        0: TileCollisionData(
            tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE_POLY)]
        ),
        1: TileCollisionData(
            tile_id=1, shapes=[CollisionPolygon(vertices=HALF_TILE_POLY)]
        ),
        2: TileCollisionData(
            tile_id=2, shapes=[CollisionPolygon(vertices=SLOPE_POLY)]
        ),
    }
    return TilesetCollision(tileset_name="test", tile_size=(32, 32), tiles=tiles)


def make_floor():
    tile_map = {}
    for x in range(10):
        for y in range(2):
            tile_map[(x, y)] = 0
    return tile_map


def make_wall():
    tile_map = {}
    for y in range(10):
        tile_map[(4, y)] = 0
    return tile_map


class TestMoveGrounded:
    def setup_method(self):
        self.runner = CollisionRunner(tile_size=(32, 32))
        self.runner.gravity = 800.0
        self.runner.max_fall_speed = 600.0
        self.tileset = make_tileset()

    # --- empty space ---------------------------------------------------------

    def test_moves_through_empty_space(self):
        """No tiles -> free movement with gravity."""
        sprite = MockSprite(x=100, y=100)
        sprite.vx = 50
        sprite.vy = 0
        sprite.on_ground = False

        result = self.runner.move_grounded(sprite, self.tileset, {}, dt=0.016)

        # gravity applied
        assert sprite.vy > 0
        assert result.final_x > 100
        assert result.final_y > 100
        assert result.collided is False
        assert result.on_ground is False

    def test_no_gravity_when_velocity_provided(self):
        """velocity=(vx,vy) skips gravity."""
        sprite = MockSprite(x=100, y=100)
        sprite.vx = 0
        sprite.vy = 0
        sprite.on_ground = False

        result = self.runner.move_grounded(
            sprite, self.tileset, {}, dt=0.016, velocity=(100.0, 0.0)
        )

        assert sprite.vy == 0.0  # no gravity applied
        assert result.final_x > 100
        assert result.final_y == 100  # no vertical movement

    # --- wall collision (X axis) ---------------------------------------------

    def test_wall_blocks_horizontal_movement(self):
        """Sprite moving into a tile wall is stopped and vx zeroed."""
        tile_map = {(4, 3): 0}
        sprite = MockSprite(x=128, y=65)
        sprite.vx = 50
        sprite.vy = 0
        sprite.on_ground = True

        result = self.runner.move_grounded(sprite, self.tileset, tile_map, dt=0.016)

        assert result.hit_wall_x is True
        assert result.collided is True
        assert sprite.vx == 0.0
        # Should still be at the wall edge (tile (4,3) starts at x=128)
        assert sprite.x < 129

    def test_wall_does_not_block_non_moving_sprite(self):
        """Stationary sprite touching a wall is not pushed away."""
        tile_map = {(4, 3): 0}
        sprite = MockSprite(x=126, y=64)
        sprite.vx = 0
        sprite.vy = 0
        sprite.on_ground = True

        result = self.runner.move_grounded(sprite, self.tileset, tile_map, dt=0.016)

        assert result.hit_wall_x is False
        assert sprite.x == 126

    # --- ground collision (Y axis, falling) ----------------------------------

    def test_falls_onto_ground_and_stops(self):
        """Falling sprite lands on tile surface, on_ground=True."""
        tile_map = {(0, 5): 0}
        sprite = MockSprite(x=4, y=64)
        sprite.vx = 0
        sprite.vy = 0
        sprite.on_ground = False

        self.runner.move_grounded(sprite, self.tileset, tile_map, dt=0.3)

        # Ground surface = tile (0,5) top = 5*32 = 160
        # Sprite bottom = sprite.y + shape.height + offset
        # shape = (0, 0, 24, 32) -> bottom = sprite.y + 32
        # Landed: bottom ~ 160 -> y ~ 128
        assert sprite.on_ground is True
        assert sprite.vy == 0.0
        assert abs(sprite.y - 128.0) < 1.0

    def test_partial_tile_ground_contact(self):
        """Sprite lands on a half-height tile (only bottom 16px solid)."""
        # Tile 1 has HALF_TILE_POLY: solid only from y=16 to y=32 (tile-local)
        # Surface is at y=16 in tile-local, so world y = 5*32 + 16 = 176
        tile_map = {(0, 5): 1}
        sprite = MockSprite(x=4, y=120)
        sprite.vx = 0
        sprite.vy = 0
        sprite.on_ground = False

        self.runner.move_grounded(sprite, self.tileset, tile_map, dt=0.2)

        # Sprite bottom should rest at y=176 (top of solid part)
        # bottom = y + 32 -> y ~ 144
        assert sprite.on_ground is True
        assert sprite.vy == 0.0
        assert abs(sprite.y - 144.0) < 1.0

    def test_stays_on_ground_when_stationary(self):
        """Sprite sitting on ground stays on_ground without sinking."""
        tile_map = {(0, 5): 0}
        sprite = MockSprite(x=4, y=128)  # bottom = 160 = ground surface
        sprite.vx = 0
        sprite.vy = 0
        sprite.on_ground = True

        result = self.runner.move_grounded(sprite, self.tileset, tile_map, dt=0.016)

        assert result.on_ground is True
        assert sprite.on_ground is True
        assert abs(sprite.y - 128.0) < 0.1

    # --- ceiling collision ---------------------------------------------------

    def test_hits_ceiling_and_stops(self):
        """Sprite moving upward into a tile is stopped, vy zeroed."""
        tile_map = {(0, 5): 0}
        sprite = MockSprite(x=4, y=200)
        sprite.vx = 0
        sprite.vy = -800  # moving up
        sprite.on_ground = False

        result = self.runner.move_grounded(sprite, self.tileset, tile_map, dt=0.016)

        # Ceiling = bottom of tile (0,5) = 5*32+32 = 192
        # Sprite top = sprite.y + shape.offset[1] = sprite.y
        # Hitting ceiling at y=192 - 0 (top of sprite) = 192
        assert result.hit_ceiling is True
        assert sprite.vy == 0.0

    # --- ledge detection -----------------------------------------------------

    def test_walks_off_ledge_and_starts_falling(self):
        """Grounded sprite walking over empty space leaves ground."""
        # One tile of ground at (0,5), nothing to the right
        tile_map = {(0, 5): 0}
        sprite = MockSprite(x=4, y=128)
        sprite.vx = 60
        sprite.vy = 0
        sprite.on_ground = True
    
        self.runner.move_grounded(sprite, self.tileset, tile_map, dt=0.5)
    
        # Moved far enough right that there's no ground below
        assert sprite.on_ground is False

    def test_remains_grounded_when_still_over_solid_ground(self):
        """Grounded sprite walking over more ground stays grounded."""
        tile_map = {}
        for x in range(0, 20):
            tile_map[(x, 5)] = 0
        sprite = MockSprite(x=4, y=128)
        sprite.vx = 50
        sprite.vy = 0
        sprite.on_ground = True

        self.runner.move_grounded(sprite, self.tileset, tile_map, dt=0.016)

        # Still has ground below -> stays grounded
        assert sprite.on_ground is True

    # --- explicit velocity mode ----------------------------------------------

    def test_explicit_velocity_no_gravity(self):
        """velocity=(200, 0) moves horizontally, no gravity applied."""
        sprite = MockSprite(x=100, y=100)
        sprite.vx = 0
        sprite.vy = 0
        sprite.on_ground = True

        result = self.runner.move_grounded(
            sprite, self.tileset, {}, dt=0.016, velocity=(200.0, 0.0)
        )

        assert result.final_x == pytest.approx(103.2)
        assert result.final_y == 100  # no vertical movement

    def test_explicit_velocity_with_knockback(self):
        """velocity can express knockback (negative vy up, positive vy down)."""
        tile_map = {}
        sprite = MockSprite(x=100, y=100)
        sprite.vx = 0
        sprite.vy = 0
        sprite.on_ground = False

        # Knockback: up and to the right
        result = self.runner.move_grounded(
            sprite, self.tileset, tile_map, dt=0.016, velocity=(-100.0, -200.0)
        )

        # No gravity applied, velocity is used directly
        assert sprite.vx == -100.0
        assert sprite.vy == -200.0
        assert result.final_x < 100
        assert result.final_y < 100

    # --- interaction with one-way polygons -----------------------------------

    def test_one_way_polygon_blocks_ground(self):
        """One-way polygons are treated as solid by move_grounded."""
        one_way_tileset = TilesetCollision(
            tileset_name="one_way",
            tile_size=(32, 32),
            tiles={
                0: TileCollisionData(
                    tile_id=0,
                    shapes=[
                        CollisionPolygon(vertices=FULL_TILE_POLY, one_way=True)
                    ],
                )
            },
        )
        tile_map = {(0, 5): 0}
        sprite = MockSprite(x=4, y=120)
        sprite.vx = 0
        sprite.vy = 0
        sprite.on_ground = False

        self.runner.move_grounded(sprite, one_way_tileset, tile_map, dt=0.2)

        # One-way tile from above -> land on it
        assert sprite.on_ground is True
        assert sprite.vy == 0.0
        assert abs(sprite.y - 128.0) < 1.0
