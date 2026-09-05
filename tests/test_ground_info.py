"""Ground supporting-surface info for move_platformer_with_slide.

Covers the conservative contract:
- ground geometry comes from the already-selected walkable polygon edge
  (edge -> normal -> angle), not tile identity / bounding box.
- CollisionResult.ground_angle / ground_normal are post-move state.
- World-X velocity preserved: no cos() scaling.
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.parser.collision import (
    CollisionPolygon,
    RectangleShape,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.body import Body
from tilemap_parser.runtime.movement import CollisionRunner
from tilemap_parser.runtime.world import PhysicsWorld

FULL = [(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]
SLOPE_UP = [(0.0, 32.0), (32.0, 0.0), (32.0, 32.0)]  # rises toward +X
SLOPE_DOWN = [(0.0, 0.0), (32.0, 32.0), (0.0, 32.0)]  # falls toward +X
# Nearly rectangular, but the supporting TOP edge is tilted ~5.36 deg.
TILTED_TOP = [(0.0, 3.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]
# Steep hypotenuse ~76 deg from horizontal -> not walkable with 60 deg max.
STEEP = [(0.0, 32.0), (8.0, 0.0), (8.0, 32.0)]
ONE_WAY_TOP = [(0.0, 8.0), (32.0, 8.0), (32.0, 16.0), (0.0, 16.0)]


class MockSprite:
    def __init__(self, x=0, y=0, w=24, h=32):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.collision_shape = RectangleShape(width=w, height=h)


def make_tileset():
    return TilesetCollision(
        tileset_name="ground_test",
        tile_size=(32, 32),
        tiles={
            0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL)]),
            2: TileCollisionData(
                tile_id=2, shapes=[CollisionPolygon(vertices=SLOPE_UP)]
            ),
            3: TileCollisionData(
                tile_id=3, shapes=[CollisionPolygon(vertices=SLOPE_DOWN)]
            ),
            4: TileCollisionData(
                tile_id=4, shapes=[CollisionPolygon(vertices=TILTED_TOP)]
            ),
            5: TileCollisionData(tile_id=5, shapes=[CollisionPolygon(vertices=STEEP)]),
            6: TileCollisionData(
                tile_id=6,
                shapes=[CollisionPolygon(vertices=ONE_WAY_TOP, one_way=True)],
            ),
        },
    )


def test_flat_reports_zero():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    s = MockSprite(x=160, y=160 - 32 - 0.01)
    s.on_ground = True
    res = r.move_platformer_with_slide(s, ts, {(5, 5): 0}, dt=0.016, input_x=0)
    assert res.on_ground is True
    assert res.ground_angle == 0.0
    assert res.ground_normal == (0.0, -1.0)


def test_slope_up_reports_positive_45():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    s = MockSprite(x=160, y=169.99, w=8, h=16)
    s.on_ground = True
    res = r.move_platformer_with_slide(s, ts, {(5, 5): 2}, dt=0.016, input_x=1)
    assert res.on_ground is True
    assert res.ground_angle == 45.0
    assert res.ground_normal[0] == pytest.approx(-(2**0.5) / 2)
    assert res.ground_normal[1] == pytest.approx(-(2**0.5) / 2)


def test_slope_down_reports_negative():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    info = r._find_walkable_ground_info(
        MockSprite(x=16, y=0 - 32, w=24, h=32),
        ts,
        {(0, 0): 3},
        max_up=40.0,
        max_down=40.0,
    )
    assert info is not None
    assert info.angle == -45.0
    assert info.normal[0] > 0
    assert info.normal[1] < 0


def test_nearly_rect_reports_actual_tilted_edge():
    # Guards against tile-type / bbox slope classification.
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    s = MockSprite(x=8, y=1.5 - 32 - 0.01)
    s.on_ground = True
    res = r.move_platformer_with_slide(s, ts, {(0, 0): 4}, dt=0.016, input_x=0)
    assert res.on_ground is True
    assert res.ground_angle == math.degrees(math.atan2(3.0, 32.0))
    assert abs(res.ground_angle - 5.36) < 0.01


def test_steep_edge_is_not_walkable():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    info = r._find_walkable_ground_info(
        MockSprite(x=4, y=0 - 32, w=8, h=16),
        ts,
        {(0, 0): 5},
        max_up=40.0,
        max_down=40.0,
    )
    assert info is None


def test_vertical_edge_rejected():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    poly = CollisionPolygon(vertices=FULL)
    minu = math.cos(math.radians(r.max_walk_angle))
    # Edge 1 of FULL is (32,0)->(32,32): vertical wall.
    assert r._walkable_edge_info_at_x(poly, 0, 0, 32.0, 1, minu) is None
    # Edge 0 is the flat top.
    assert r._walkable_edge_info_at_x(poly, 0, 0, 16.0, 0, minu) is not None


def test_airborne_reports_none():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    s = MockSprite(x=100, y=100)
    s.on_ground = False
    res = r.move_platformer_with_slide(s, ts, {}, dt=0.016, input_x=0)
    assert res.on_ground is False
    assert res.ground_angle is None
    assert res.ground_normal is None


def test_jump_reports_none():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    s = MockSprite(x=160, y=160 - 32 - 0.01)
    s.on_ground = True
    res = r.move_platformer_with_slide(
        s, ts, {(5, 5): 0}, dt=0.016, input_x=0, jump_pressed=True
    )
    assert res.on_ground is False
    assert res.ground_angle is None
    assert res.ground_normal is None


def test_ledge_walkoff_clears_result():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    # Stand at right edge of a single flat tile, then step past it.
    s = MockSprite(x=160 + 32 - 24, y=160 - 32 - 0.01)
    s.on_ground = True
    first = r.move_platformer_with_slide(s, ts, {(5, 5): 0}, dt=0.016, input_x=0)
    assert first.on_ground is True
    assert first.ground_angle == 0.0
    s.on_ground = True
    res = r.move_platformer_with_slide(s, ts, {(5, 5): 0}, dt=0.5, input_x=1)
    assert res.on_ground is False
    assert res.ground_angle is None
    assert res.ground_normal is None


def test_one_way_from_above_reports_flat():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    # Tile (0,0) one-way top at y=8; stand on it.
    s = MockSprite(x=4, y=8 - 32 - 0.01)
    s.on_ground = True
    res = r.move_platformer_with_slide(s, ts, {(0, 0): 6}, dt=0.016, input_x=0)
    assert res.on_ground is True
    assert res.ground_angle == 0.0


def test_explicit_velocity_participates_in_slope_follow():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    s = MockSprite(x=160, y=169.99, w=8, h=16)
    s.on_ground = True
    res = r.move_platformer_with_slide(
        s, ts, {(5, 5): 2}, dt=0.016, input_x=0, velocity=(200.0, 0.0)
    )
    assert res.on_ground is True
    assert res.ground_angle == 45.0
    assert s.x > 160
    assert s.y < 169.99


def test_world_x_preserved_flat_vs_slope():
    # World-X semantics: same input gives same X displacement; slope adds Y.
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    flat = MockSprite(x=160, y=160 - 32 - 0.01)
    flat.on_ground = True
    r.move_platformer_with_slide(flat, ts, {(5, 5): 0}, dt=0.016, input_x=1)
    sloped = MockSprite(x=160, y=169.99, w=8, h=16)
    sloped.on_ground = True
    r.move_platformer_with_slide(sloped, ts, {(5, 5): 2}, dt=0.016, input_x=1)
    assert sloped.x == flat.x
    assert sloped.y < 169.99


def test_body_ground_stays_flat_conservative():
    world = PhysicsWorld(tile_map={}, tileset_collision=None, tile_size=(32, 32))
    world.add_body(
        Body(collision_shape=RectangleShape(width=200, height=16), x=0, y=80)
    )
    runner = CollisionRunner.from_world(world, game_type="platformer")
    s = MockSprite(x=50, y=80 - 32 - 0.01)
    s.on_ground = True
    res = runner.move_platformer_with_slide(s, None, None, dt=0.016, input_x=0)
    assert res.on_ground is True
    assert res.ground_angle == 0.0
    assert res.ground_normal == (0.0, -1.0)


def test_y_query_delegates_to_info_query():
    r = CollisionRunner.from_game_type("platformer", (32, 32))
    ts = make_tileset()
    s = MockSprite(x=160, y=160 - 32 - 5)
    y = r._find_walkable_ground_y(s, ts, {(5, 5): 0}, max_up=10.0, max_down=10.0)
    info = r._find_walkable_ground_info(s, ts, {(5, 5): 0}, max_up=10.0, max_down=10.0)
    assert y is not None and info is not None
    assert y == info.y
