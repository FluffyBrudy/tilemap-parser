"""
Tests for render_scale support in the parser layer.

Covers:
- CollisionPolygon.transform with scale
- TilesetCollision.get_world_shapes with scale
- ParsedMeta.render_scale parsing
- TilemapData.render_scale property
- Inline offset functions with scale parameter
- CollisionRunner with effective_tile_size
"""

import json
import math
import pytest
from pathlib import Path
from typing import Any, Dict, List, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.parser.collision import CollisionPolygon, TilesetCollision, TileCollisionData, RectangleShape, CircleShape, CapsuleShape
from tilemap_parser.parser.map_parse import ParsedMeta, parse_map_dict
from tilemap_parser.runtime.tile_collision import (
    CollisionRunner,
    MovementMode,
    _point_in_polygon_offset,
    _rect_polygon_collision_offset,
    _circle_polygon_collision_offset,
    _check_sprite_polygon_offset,
    get_shape_bounds,
)


# ---------------------------------------------------------------------------
# Helpers — minimal sprite for collision tests
# ---------------------------------------------------------------------------

class DummySprite:
    def __init__(self, x=0, y=0, shape=None, vx=0, vy=0, on_ground=False):
        self.x = x
        self.y = y
        self.collision_shape = shape or RectangleShape(width=16, height=16)
        self.vx = vx
        self.vy = vy
        self.on_ground = on_ground


# ---------------------------------------------------------------------------
# CollisionPolygon.transform
# ---------------------------------------------------------------------------

class TestCollisionPolygonTransformScale:
    def test_no_scale_default(self):
        poly = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
        world = poly.transform(100, 200)
        assert world.vertices == [
            (100, 200), (116, 200), (116, 216), (100, 216)
        ]

    def test_scale_2x(self):
        poly = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
        world = poly.transform(100, 200, scale=2.0)
        # tile_x/y already in world space; vertices get multiplied by scale
        assert world.vertices == [
            (100, 200), (132, 200), (132, 232), (100, 232)
        ]

    def test_scale_half(self):
        poly = CollisionPolygon(vertices=[(10, 10), (20, 10), (20, 20)])
        world = poly.transform(50, 50, scale=0.5)
        # tile_x=50, tile_y=50; vertices: 10*0.5=5, 20*0.5=10
        # (50+5, 50+5) = (55, 55)
        # (50+10, 50+5) = (60, 55)
        # (50+10, 50+10) = (60, 60)
        assert world.vertices == [
            (55.0, 55.0), (60.0, 55.0), (60.0, 60.0)
        ]

    def test_scale_non_uniform_tile_offset(self):
        poly = CollisionPolygon(vertices=[(4, 8)])
        world = poly.transform(32, 64, scale=2.0)
        # 32 + 4*2 = 40, 64 + 8*2 = 80
        assert world.vertices == [(40, 80)]

    def test_scale_one_way_preserved(self):
        poly = CollisionPolygon(vertices=[(0, 0), (32, 0), (32, 32)], one_way=True)
        world = poly.transform(0, 0, scale=3.0)
        assert world.one_way is True


# ---------------------------------------------------------------------------
# TilesetCollision.get_world_shapes
# ---------------------------------------------------------------------------

class TestGetWorldShapesScale:
    @pytest.fixture
    def ts_coll(self):
        return TilesetCollision(
            tileset_name="test",
            tile_size=(32, 32),
            tiles={
                0: TileCollisionData(
                    tile_id=0,
                    shapes=[
                        CollisionPolygon(vertices=[(0, 0), (32, 0), (32, 32), (0, 32)]),
                    ],
                ),
            },
        )

    def test_default_scale(self, ts_coll):
        shapes = ts_coll.get_world_shapes(0, 64, 128)
        assert shapes[0].vertices == [(64, 128), (96, 128), (96, 160), (64, 160)]

    def test_custom_scale(self, ts_coll):
        shapes = ts_coll.get_world_shapes(0, 64, 128, scale=2.0)
        assert shapes[0].vertices == [(64, 128), (128, 128), (128, 192), (64, 192)]

    def test_missing_tile_returns_empty(self, ts_coll):
        assert ts_coll.get_world_shapes(999, 0, 0, scale=2.0) == []


# ---------------------------------------------------------------------------
# ParsedMeta.render_scale
# ---------------------------------------------------------------------------

class TestParsedMetaRenderScale:
    def test_default_render_scale(self):
        meta = ParsedMeta(
            tile_size=(16, 16),
            map_size=(10, 10),
            initial_map_size=(10, 10),
            zoom_level=1.0,
            scroll=(0, 0),
            version="1.1",
        )
        assert meta.render_scale == 1.0

    def test_custom_render_scale(self):
        meta = ParsedMeta(
            tile_size=(16, 16),
            map_size=(10, 10),
            initial_map_size=(10, 10),
            zoom_level=1.0,
            scroll=(0, 0),
            version="1.1",
            render_scale=3.0,
        )
        assert meta.render_scale == 3.0

    def test_parsed_from_map_dict(self):
        """render_scale is read from meta dict by parse_map_dict"""
        root = {
            "meta": {
                "tile_size": "16,16",
                "map_size": "10,10",
                "zoom_level": 1.0,
                "scroll": "0,0",
                "version": "1.1",
                "render_scale": 2.5,
            },
            "data": {"layers": []},
            "project_state": {"rules": [], "groups": []},
        }
        parsed = parse_map_dict(root)
        assert parsed.meta.render_scale == 2.5

    def test_parsed_defaults_to_1_0_when_missing(self):
        root = {
            "meta": {
                "tile_size": "16,16",
                "map_size": "10,10",
                "zoom_level": 1.0,
                "scroll": "0,0",
                "version": "1.1",
            },
            "data": {"layers": []},
            "project_state": {"rules": [], "groups": []},
        }
        parsed = parse_map_dict(root)
        assert parsed.meta.render_scale == 1.0

    def test_parsed_rejects_non_numeric(self):
        root = {
            "meta": {
                "tile_size": "16,16",
                "map_size": "10,10",
                "zoom_level": 1.0,
                "scroll": "0,0",
                "version": "1.1",
                "render_scale": "not-a-number",
            },
            "data": {"layers": []},
            "project_state": {"rules": [], "groups": []},
        }
        with pytest.raises(Exception):
            parse_map_dict(root)


# ---------------------------------------------------------------------------
# Inline offset functions with scale parameter
# ---------------------------------------------------------------------------

class TestInlineOffsetScale:
    """_point_in_polygon_offset, _rect_polygon_collision_offset,
    _circle_polygon_collision_offset, _check_sprite_polygon_offset with scale."""

    def test_point_offset_scale(self):
        """_point_in_polygon_offset scales vertices before offset"""
        verts = [(0, 0), (10, 0), (10, 10), (0, 10)]
        # ox=100, oy=200, scale=2 → world vertices: [(100,200), (120,200), (120,220), (100,220)]
        # point (90, 190) is outside (below and left)
        assert _point_in_polygon_offset(90, 190, verts, 100, 200, scale=2.0) is False
        # center of scaled polygon: (10,10)*2 + (100,200) = (120, 220)
        assert _point_in_polygon_offset(120, 220, verts, 100, 200, scale=2.0) is True

    def test_rect_offset_scale(self):
        """_rect_polygon_collision_offset scales vertices"""
        verts = [(0, 0), (10, 0), (10, 10), (0, 10)]
        # scale=2, ox=0, oy=0 → polygon covers (0,0) to (20,20)
        # rect at (5, 5, 10, 10) should collide
        assert _rect_polygon_collision_offset(5, 5, 10, 10, verts, 0, 0, scale=2.0) is True
        # rect at (25, 25, 5, 5) should not
        assert _rect_polygon_collision_offset(25, 25, 5, 5, verts, 0, 0, scale=2.0) is False

    def test_circle_offset_scale(self):
        """_circle_polygon_collision_offset scales vertices"""
        verts = [(0, 0), (10, 0), (10, 10), (0, 10)]
        # scale=2, ox=0, oy=0 → polygon covers (0,0) to (20,20)
        # circle at center (10, 10) radius 5 should collide
        assert _circle_polygon_collision_offset(10, 10, 5, verts, 0, 0, scale=2.0) is True
        # far away should not
        assert _circle_polygon_collision_offset(100, 100, 5, verts, 0, 0, scale=2.0) is False

    def test_rect_collision_scale_defaults_to_1(self):
        """scale=1.0 should give same result as no scale"""
        verts = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _rect_polygon_collision_offset(2, 2, 5, 5, verts, 5, 5, scale=1.0) == \
               _rect_polygon_collision_offset(2, 2, 5, 5, verts, 5, 5)

    def test_check_sprite_polygon_offset_scale(self):
        """_check_sprite_polygon_offset passes scale through"""
        verts = [(0, 0), (16, 0), (16, 16), (0, 16)]
        poly = CollisionPolygon(vertices=verts)
        sprite = DummySprite(x=100, y=100, shape=RectangleShape(width=16, height=16))
        # ox=0, oy=0, scale=2 → polygon covers (0,0) to (32,32)
        # sprite at (100,100) out of range
        assert _check_sprite_polygon_offset(sprite, poly, 0, 0, scale=2.0) is False
        # sprite at (0,0) should intersect
        sprite.x = 0
        sprite.y = 0
        assert _check_sprite_polygon_offset(sprite, poly, 0, 0, scale=2.0) is True


# ---------------------------------------------------------------------------
# CollisionRunner
# ---------------------------------------------------------------------------

class TestCollisionRunnerRenderScale:
    def test_default_render_scale(self):
        runner = CollisionRunner(tile_size=(32, 32))
        assert runner.render_scale == 1.0
        assert runner._eff_tw == 32
        assert runner._eff_th == 32

    def test_custom_scale_effective_size(self):
        runner = CollisionRunner(tile_size=(32, 32), render_scale=2.0)
        assert runner.render_scale == 2.0
        assert runner._eff_tw == 64
        assert runner._eff_th == 64

    def test_non_integer_scale(self):
        runner = CollisionRunner(tile_size=(16, 16), render_scale=1.5)
        assert runner._eff_tw == 24  # int(16 * 1.5)
        assert runner._eff_th == 24

    def test_get_tile_at_with_scale(self):
        runner = CollisionRunner(tile_size=(32, 32), render_scale=2.0)
        # world pos at (63, 63) → tile 0 (since eff_tw=64)
        assert runner.get_tile_at(63, 63) == (0, 0)
        # world pos at (64, 64) → tile 1
        assert runner.get_tile_at(64, 64) == (1, 1)

    def test_get_tile_at_no_scale(self):
        runner = CollisionRunner(tile_size=(32, 32))
        # world pos at (31, 31) → tile 0
        assert runner.get_tile_at(31, 31) == (0, 0)
        # world pos at (32, 32) → tile 1
        assert runner.get_tile_at(32, 32) == (1, 1)

    def test_scale_affects_collision_query(self):
        """With render_scale=2, the effective grid is 64x64, affecting which
        tiles are checked for collision at a given world position."""
        runner = CollisionRunner(tile_size=(32, 32), render_scale=2.0)
        eff_tw = runner._eff_tw  # 64
        # A tile_map with a single tile at (0,0)
        tile_map = {(0, 0): 0}
        ts_coll = TilesetCollision(
            tileset_name="test",
            tile_size=(32, 32),
            tiles={
                0: TileCollisionData(
                    tile_id=0,
                    shapes=[CollisionPolygon(vertices=[(0, 0), (32, 0), (32, 32), (0, 32)])],
                ),
            },
        )

        # sprite at (10, 10) with 16x16 rect shape should collide with tile (0, 0)
        sprite = DummySprite(x=10, y=10, shape=RectangleShape(width=16, height=16))
        # _collides_at internally checks tiles using eff_tw/eff_th and passes self.render_scale
        assert runner._collides_at(sprite, ts_coll, tile_map) is True

        # sprite far to the right at (128, 10) should NOT collide (tile (0,0) world is 0..64)
        sprite2 = DummySprite(x=128, y=10, shape=RectangleShape(width=16, height=16))
        # sprite at (128, 10) with 16 wide → bounds 128..144, tile_x = 128//64 = 2 → no tile at (2,0)
        assert runner._collides_at(sprite2, ts_coll, tile_map) is False

    def test_from_game_type_passes_scale(self):
        runner = CollisionRunner.from_game_type("platformer", tile_size=(16, 16), render_scale=3.0)
        assert runner.render_scale == 3.0
        assert runner._eff_tw == 48
        assert runner._eff_th == 48

    def test_from_game_type_default_scale(self):
        runner = CollisionRunner.from_game_type("topdown", tile_size=(16, 16))
        assert runner.render_scale == 1.0
        assert runner._eff_tw == 16
        assert runner._eff_th == 16

    def test_collides_at_inline_offset_pass_scale(self):
        """Verify _collides_at passes scale down to _check_sprite_polygon_offset
        by checking edge-case with scaled vertices."""
        runner = CollisionRunner(tile_size=(8, 8), render_scale=2.0)
        # eff_tw = 16, eff_th = 16
        # A triangle polygon that only fills bottom-right corner of tile
        verts = [(0, 0), (8, 0), (4, 8)]
        ts_coll = TilesetCollision(
            tileset_name="test",
            tile_size=(8, 8),
            tiles={0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=verts)])},
        )
        tile_map = {(0, 0): 0}
        # sprite at (8, 12) with 4x4 rect
        # With scale=2, vertices become (0,0)*2=0, (8,0)*2=16, (4,8)*2=8+16=24 in world:
        # (16,0), (0,0), (8,16). ox=0, oy=0.
        # Wait, ox = tile_x * eff_tw = 0*16 = 0
        # Vertices are tile-local: [(0,0), (8,0), (4,8)]
        # Scaled: [(0,0), (16,0), (8,16)]
        # + offset (0,0) → world: [(0,0), (16,0), (8,16)]
        # Sprite bounds: x=8, y=12, w=4, h=4 → (8..12, 12..16)
        # Scaled triangle: [(0,0), (16,0), (8,16)] — at y=12 the triangle spans x=6..10,
        # which overlaps the sprite rect (8..12, 12..16). So collision IS expected.
        sprite = DummySprite(x=8, y=12, shape=RectangleShape(width=4, height=4))
        assert runner._collides_at(sprite, ts_coll, tile_map) is True


# ---------------------------------------------------------------------------
# CollisionRunner.get_tile_shapes and get_nearby_tile_shapes
# ---------------------------------------------------------------------------

class TestRunnerTileShapeMethodsScale:
    @pytest.fixture
    def ts_coll(self):
        return TilesetCollision(
            tileset_name="test",
            tile_size=(32, 32),
            tiles={
                0: TileCollisionData(
                    tile_id=0,
                    shapes=[CollisionPolygon(vertices=[(0, 0), (32, 0), (32, 32), (0, 32)])],
                ),
            },
        )

    def test_get_tile_shapes_with_scale(self, ts_coll):
        runner = CollisionRunner(tile_size=(32, 32), render_scale=2.0)
        tile_map = {(0, 0): 0, (1, 0): 0}
        # world pos (10, 10) → tile (0, 0) → tile world = (0*64, 0*64) = (0,0)
        # vertices scaled by 2.0: [(0,0), (64,0), (64,64), (0,64)]
        # + offset (0,0) → same
        shapes = runner.get_tile_shapes(ts_coll, tile_map, 10, 10)
        assert len(shapes) == 1
        assert shapes[0].vertices == [(0, 0), (64, 0), (64, 64), (0, 64)]

    def test_get_nearby_tile_shapes_with_scale(self, ts_coll):
        runner = CollisionRunner(tile_size=(32, 32), render_scale=2.0)
        tile_map = {(0, 0): 0, (1, 0): 0}
        sprite = DummySprite(x=10, y=10, shape=RectangleShape(width=16, height=16))
        shapes = runner.get_nearby_tile_shapes(ts_coll, tile_map, sprite, margin=0)
        assert len(shapes) == 1


# ---------------------------------------------------------------------------
# TilemapData.render_scale (integration with map_loader)
# ---------------------------------------------------------------------------

class TestTilemapDataRenderScale:
    def test_render_scale_property_exists(self):
        """Verify TilemapData has a render_scale property read from parsed meta"""
        from tilemap_parser.runtime.map_loader import TilemapData

        class MockParsedMap:
            pass

        meta = ParsedMeta(
            tile_size=(16, 16),
            map_size=(10, 10),
            initial_map_size=(10, 10),
            zoom_level=1.0,
            scroll=(0, 0),
            version="1.1",
            render_scale=2.0,
        )
        mock = MockParsedMap()
        mock.meta = meta
        mock.layers = []
        mock.tilesets = []
        mock.project_state = None
        mock.raw = {}
        import pygame
        data = TilemapData(mock, [], [], [])
        assert data.render_scale == 2.0
