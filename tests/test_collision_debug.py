import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser import (
    PhysicsWorld,
    describe_character_collision,
    describe_shape,
    describe_sprite,
    describe_tile_cell,
    describe_tile_collision,
    describe_tile_layer,
    describe_tileset_collision,
    shape_to_points,
)
from tilemap_parser.parser.collision import (
    CapsuleShape,
    CharacterCollision,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
    TileCollisionData,
    TilesetCollision,
)


def test_rect_points_and_draw_args():
    d = describe_shape(RectangleShape(width=10, height=20, offset=(5, 7)), 100, 200, 2.0)
    assert d["draw_kind"] == "rect"
    assert d["rect"] == (110.0, 214.0, 20.0, 40.0)
    assert d["points"] == [(110.0, 214.0), (130.0, 214.0), (130.0, 254.0), (110.0, 254.0)]
    assert d["valid"] is True


def test_circle_points_and_draw_args():
    d = describe_shape(CircleShape(radius=5, offset=(2, 3)), 10, 20, 2.0)
    assert d["draw_kind"] == "circle"
    assert d["center"] == (14.0, 26.0)
    assert d["radius"] == 10.0
    assert len(d["points"]) == 16


def test_capsule_points_and_draw_args():
    d = describe_shape(CapsuleShape(radius=4, height=10, offset=(1, 2)), 0, 0, 1.0)
    assert d["draw_kind"] == "capsule"
    assert d["segment"] == ((1.0, 2.0), (1.0, 12.0))
    assert d["radius"] == 4.0
    assert len(d["points"]) == 10


def test_polygon_points_passthrough():
    d = describe_shape(CollisionPolygon(vertices=[(0, 0), (8, 0), (8, 6)], one_way=True), 4, 6, 2.0)
    assert d["draw_kind"] == "polygon"
    assert d["points"] == [(4.0, 6.0), (20.0, 6.0), (20.0, 18.0)]
    assert d["one_way"] is True
    assert shape_to_points(CollisionPolygon(vertices=[(1, 2)]), 3, 4, 2.0) == [(5.0, 8.0)]


def test_tileset_reports_individual_tiles():
    ts = TilesetCollision(
        tileset_name="t",
        tile_size=(16, 16),
        tiles={
            1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=[(0, 0), (8, 0), (8, 8)])]),
            2: TileCollisionData(tile_id=2, shapes=[CollisionPolygon(vertices=[(0, 0), (4, 0), (4, 4)])]),
        },
    )
    out = describe_tileset_collision(ts)
    assert set(out) == {1, 2}
    assert out[1]["shapes"][0]["points"] != out[2]["shapes"][0]["points"]
    assert describe_tile_collision(None) == {"has_collision": False, "shapes": []}


def test_character_all_kinds():
    for shape in [
        RectangleShape(width=6, height=8),
        CircleShape(radius=5),
        CapsuleShape(radius=3, height=9),
        CollisionPolygon(vertices=[(0, 0), (5, 0), (5, 5)]),
    ]:
        d = describe_character_collision(CharacterCollision(name="c", shape=shape))
        assert d["shape"]["valid"] is True
        assert len(d["shape"]["points"]) >= 3


def test_cell_lists_stacked_entries_separately():
    ts = TilesetCollision(
        tileset_name="t",
        tile_size=(16, 16),
        tiles={
            1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=[(0, 0), (8, 0), (8, 8)])]),
            2: TileCollisionData(tile_id=2, shapes=[CollisionPolygon(vertices=[(0, 0), (4, 0), (4, 4)])]),
        },
    )
    cell = ((1, 0), (2, 0))
    out = describe_tile_cell(cell, tileset=ts)
    assert [e["gid"] for e in out] == [1, 2]
    assert out[0]["shapes"][0]["points"] != out[1]["shapes"][0]["points"]
    assert describe_tile_cell(None, tileset=ts) == []


class _LiveSprite:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.collision_shape = shape
        self.collision_layer = 1
        self.collision_mask = 0xFFFFFFFF


class _MultiSprite(_LiveSprite):
    def __init__(self, x, y, shapes):
        super().__init__(x, y, shapes[0])
        self.collision_shapes = shapes


def test_sprite_tracks_live_position():
    s = _LiveSprite(10.0, 20.0, RectangleShape(width=8, height=6, offset=(1, 2)))
    before = describe_sprite(s, 2.0)[0]["points"]
    s.x += 5.0
    s.y -= 4.0
    after = describe_sprite(s, 2.0)[0]["points"]
    assert [(ax - bx, ay - by) for (ax, ay), (bx, by) in zip(after, before)] == [(5.0, -4.0)] * 4


def test_sprite_multi_and_shapeless():
    s = _MultiSprite(
        0.0,
        0.0,
        [
            CircleShape(radius=4),
            None,
            CollisionPolygon(vertices=[(0, 0), (6, 0), (6, 6)]),
        ],
    )
    out = describe_sprite(s, 1.0)
    assert [d["draw_kind"] for d in out] == ["circle", "polygon"]
    s.collision_shapes = []
    s.collision_shape = None
    assert describe_sprite(s, 1.0) == []


def _layer_tileset():
    return TilesetCollision(
        tileset_name="t",
        tile_size=(16, 16),
        tiles={
            1: TileCollisionData(
                tile_id=1,
                shapes=[CollisionPolygon(vertices=[(0, 0), (8, 0), (8, 8)])],
            ),
            2: TileCollisionData(
                tile_id=2,
                shapes=[CollisionPolygon(vertices=[(0, 0), (4, 0), (4, 4)], one_way=True)],
            ),
        },
    )


def test_describe_tile_layer_world_positioned():
    ts = _layer_tileset()
    tile_map = {(2, 1): ((1, 0),), (0, 0): ((2, 0), (1, 0))}
    out = describe_tile_layer(tile_map, tileset=ts, scale=2.0)
    assert [e["tile"] for e in out] == [(2, 1), (0, 0), (0, 0)]
    assert out[0]["points"] == [(64.0, 32.0), (80.0, 32.0), (80.0, 48.0)]
    assert [e["gid"] for e in out if e["tile"] == (0, 0)] == [2, 1]
    assert out[1]["one_way"] is True
    assert out[2]["one_way"] is False


def test_describe_tile_layer_world_defaults():
    ts = _layer_tileset()
    tile_map = {(1, 0): ((1, 0),), (3, 3): 99}
    world = PhysicsWorld(tile_map=tile_map, tileset_collision=ts, tile_size=(16, 16), render_scale=2.0)
    out = describe_tile_layer(tile_map, world=world)
    assert out[0]["points"] == [(32.0, 0.0), (48.0, 0.0), (48.0, 16.0)]
    assert [e["tile"] for e in out] == [(1, 0)]


def test_describe_tile_layer_needs_resolver():
    with pytest.raises(TypeError):
        describe_tile_layer({(0, 0): 1})


def test_describe_tile_layer_skips_invalid():
    ts = TilesetCollision(
        tileset_name="t",
        tile_size=(16, 16),
        tiles={1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=[(0, 0), (1, 1)])])},
    )
    assert describe_tile_layer({(0, 0): ((1, 0),)}, tileset=ts) == []


def test_describe_empty_polygon_returns_invalid():
    d = describe_shape(CollisionPolygon(vertices=[]), 4.0, 6.0)
    assert d["kind"] == "polygon"
    assert d["valid"] is False
    assert d["points"] == []
    assert d["aabb"] == (4.0, 6.0, 4.0, 6.0)
    ts = TilesetCollision(
        tileset_name="t",
        tile_size=(16, 16),
        tiles={8: TileCollisionData(tile_id=8, shapes=[CollisionPolygon(vertices=[])])},
    )
    out = describe_tile_cell(((8, 0),), tileset=ts)
    assert len(out) == 1
    assert out[0]["has_collision"] is False
    assert out[0]["shapes"][0]["valid"] is False
