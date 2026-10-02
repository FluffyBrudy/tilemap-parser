"""Godot-parity layer union tests (aggressive).

Godot stacks TileMapLayers: every layer owns independent physics bodies,
so overlapping cells UNION — an upper deco tile never erases lower solid
ground.  Cells hold ``((gid, flipbits), ...)`` stacked entries.
"""

from pathlib import Path

import pygame
import pytest

from tilemap_parser import (
    CollisionRunner,
    PhysicsWorld,
    TilemapData,
    TilesetCollision,
    RectangleShape,
    TileCollisionData,
    CollisionPolygon,
    iter_cell_ids,
    parse_map_dict,
    rect_vs_tilemap,
)
from tilemap_parser.runtime.navigation.nav_grid import NavGrid

FULL = [(0.0, 0.0), (16.0, 0.0), (16.0, 16.0), (0.0, 16.0)]
LEFT_HALF = [(0.0, 0.0), (8.0, 0.0), (8.0, 16.0), (0.0, 16.0)]
RIGHT_HALF = [(8.0, 0.0), (16.0, 0.0), (16.0, 16.0), (8.0, 16.0)]


class Sprite:
    def __init__(self, x=0, y=0, w=8, h=8):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.collision_shape = RectangleShape(width=w, height=h)
        self.collision_mask = 1
        self.collision_layer = 1


def solid_set(*ids, one_way=False):
    tiles = {
        i: TileCollisionData(tile_id=i, shapes=[CollisionPolygon(vertices=list(FULL), one_way=one_way)])
        for i in ids
    }
    return TilesetCollision(tileset_name="t", tile_size=(16, 16), tiles=tiles)


def payload_two_layers(layer_defs, tilesets=None):
    """layer_defs: [(name, z, [(x, y, variant[, flip_dict])], extra_dict)]."""
    layers = []
    for spec in layer_defs:
        name, z, cells = spec[0], spec[1], spec[2]
        extra = spec[3] if len(spec) > 3 else {}
        tiles = {}
        for c in cells:
            x, y, v = c[0], c[1], c[2]
            flips = c[3] if len(c) > 3 else {}
            tiles[f"{x};{y}"] = {"pos": f"{x};{y}", "ttype": 0, "variant": v, **flips}
        layers.append({
            "name": name, "type": "tile", "visible": True, "locked": False,
            "opacity": 1.0, "z_index": z, "tiles": tiles, **extra,
        })
    return {
        "meta": {"tile_size": "16;16", "map_size": "10;10", "initial_map_size": "10;10",
                 "render_scale": 1, "scroll": "0;0", "version": "1.1"},
        "resources": {"tilesets": tilesets or [{"path": "a.png", "type": "tile", "tile_count": 200, "firstgid": 0}]},
        "project_state": {"rules": [], "groups": []},
        "data": {"layers": layers},
    }


def loader(payload):
    parsed = parse_map_dict(payload)
    return TilemapData(parsed, [None], [Path("a.png")], [])


# --- build_tile_map union -----------------------------------------------

class TestBuildUnion:
    def test_overlap_unions_not_overwrites(self):
        td = loader(payload_two_layers([
            ("ground", 0, [(1, 1, 23)]),
            ("deco", 1, [(1, 1, 107)]),
        ]))
        assert td.build_tile_map() == {(1, 1): ((23, 0), (107, 0))}

    def test_union_order_is_z_order(self):
        td = loader(payload_two_layers([
            ("top", 5, [(0, 0, 7)]),
            ("bottom", 0, [(0, 0, 3)]),
        ]))
        assert td.build_tile_map() == {(0, 0): ((3, 0), (7, 0))}

    def test_same_gid_deduped(self):
        td = loader(payload_two_layers([
            ("a", 0, [(0, 0, 5)]),
            ("b", 1, [(0, 0, 5)]),
        ]))
        assert td.build_tile_map() == {(0, 0): ((5, 0),)}

    def test_same_gid_different_flips_kept(self):
        td = loader(payload_two_layers([
            ("a", 0, [(0, 0, 5)]),
            ("b", 1, [(0, 0, 5, {"flip_h": True})]),
        ]))
        assert td.build_tile_map() == {(0, 0): ((5, 0), (5, 1))}

    def test_flip_flags_encoded(self):
        td = loader(payload_two_layers([
            ("a", 0, [(0, 0, 5, {"flip_h": True, "flip_v": True, "flip_d": True})]),
        ]))
        assert td.build_tile_map() == {(0, 0): ((5, 7),)}

    def test_disjoint_cells_untouched(self):
        td = loader(payload_two_layers([
            ("a", 0, [(0, 0, 1)]),
            ("b", 1, [(1, 1, 2)]),
        ]))
        assert td.build_tile_map() == {(0, 0): ((1, 0),), (1, 1): ((2, 0),)}

    def test_three_layers_stack(self):
        td = loader(payload_two_layers([
            ("a", 0, [(0, 0, 1)]),
            ("b", 1, [(0, 0, 2)]),
            ("c", 2, [(0, 0, 3)]),
        ]))
        assert td.build_tile_map() == {(0, 0): ((1, 0), (2, 0), (3, 0))}

    def test_exclude_layers_still_skips(self):
        td = loader(payload_two_layers([
            ("ground", 0, [(0, 0, 23)]),
            ("deco", 1, [(0, 0, 107)]),
        ]))
        assert td.build_tile_map(exclude_layers={"deco"}) == {(0, 0): ((23, 0),)}

    def test_collision_disabled_layer_skipped_direct_key(self):
        td = loader(payload_two_layers([
            ("ground", 0, [(0, 0, 23)]),
            ("deco", 1, [(0, 0, 107)], {"collision_enabled": False}),
        ]))
        assert td.build_tile_map() == {(0, 0): ((23, 0),)}
        assert td.parsed.layers[1].collision_enabled is False

    def test_collision_disabled_layer_skipped_via_properties(self):
        td = loader(payload_two_layers([
            ("ground", 0, [(0, 0, 23)]),
            ("deco", 1, [(0, 0, 107)], {"properties": {"collision_enabled": False}}),
        ]))
        assert td.build_tile_map() == {(0, 0): ((23, 0),)}

    def test_collision_enabled_defaults_true(self):
        td = loader(payload_two_layers([("g", 0, [(0, 0, 1)])]))
        assert td.parsed.layers[0].collision_enabled is True

    def test_object_layers_never_included(self):
        p = payload_two_layers([("g", 0, [(0, 0, 1)])])
        p["data"]["layers"].append({
            "name": "objects", "type": "object", "visible": True, "locked": False,
            "opacity": 1.0, "z_index": 9, "tiles": {},
            "objects": {"1": {"area": {"x": 0, "y": 0, "w": 16, "h": 16},
                                    "ttype": 0, "tileset_type": "tile", "variant": 0}},
        })
        assert loader(p).build_tile_map() == {(0, 0): ((1, 0),)}


# --- union collision behavior --------------------------------------------

class TestUnionCollides:
    def test_deco_over_solid_still_collides(self):
        ts = solid_set(23)
        world = PhysicsWorld(tile_map={(0, 0): ((107, 0), (23, 0))}, tileset_collision=ts)
        assert world.cell_has_collision((0, 0)) is True
        assert world.tile_ids_at((0, 0)) == (107, 23)

    def test_solid_over_deco_still_collides(self):
        ts = solid_set(23)
        world = PhysicsWorld(tile_map={(0, 0): ((23, 0), (107, 0))}, tileset_collision=ts)
        assert world.cell_has_collision((0, 0)) is True

    def test_deco_only_no_collision(self):
        ts = solid_set(23)
        world = PhysicsWorld(tile_map={(0, 0): ((107, 0),)}, tileset_collision=ts)
        assert world.cell_has_collision((0, 0)) is False

    def test_empty_cell_no_collision(self):
        ts = solid_set(23)
        world = PhysicsWorld(tile_map={}, tileset_collision=ts)
        assert world.cell_has_collision((5, 5)) is False
        assert world.tile_ids_at((5, 5)) == ()

    def test_partial_shapes_union_both_tested(self):
        """Left-half + right-half stacked: both halves block (Godot union)."""
        ts = TilesetCollision(tileset_name="t", tile_size=(16, 16), tiles={
            10: TileCollisionData(tile_id=10, shapes=[CollisionPolygon(vertices=list(LEFT_HALF))]),
            11: TileCollisionData(tile_id=11, shapes=[CollisionPolygon(vertices=list(RIGHT_HALF))]),
        })
        runner = CollisionRunner.from_game_type("topdown", tile_size=(16, 16))
        tile_map = {(0, 0): ((10, 0), (11, 0))}
        left = Sprite(x=1, y=4, w=5)    # [1,6]: strictly inside left half
        right = Sprite(x=10, y=4, w=5)  # [10,15]: strictly inside right half
        assert runner._collides_at(left, ts, tile_map) is True
        assert runner._collides_at(right, ts, tile_map) is True
        # either half alone covers only its side
        assert runner._collides_at(left, ts, {(0, 0): ((11, 0),)}) is False
        assert runner._collides_at(right, ts, {(0, 0): ((10, 0),)}) is False

    def test_first_colliding_shape_sees_second_gid(self):
        ts = solid_set(23)
        runner = CollisionRunner.from_game_type("topdown", tile_size=(16, 16))
        sprite = Sprite(x=2, y=2)
        hit = runner._first_colliding_shape(sprite, ts, {(0, 0): ((107, 0), (23, 0))})
        assert hit is not None

    def test_get_tile_shapes_unions(self):
        ts = TilesetCollision(tileset_name="t", tile_size=(16, 16), tiles={
            10: TileCollisionData(tile_id=10, shapes=[CollisionPolygon(vertices=list(LEFT_HALF))]),
            11: TileCollisionData(tile_id=11, shapes=[CollisionPolygon(vertices=list(RIGHT_HALF))]),
        })
        runner = CollisionRunner.from_game_type("topdown", tile_size=(16, 16))
        assert len(runner.get_tile_shapes(ts, {(0, 0): ((10, 0), (11, 0))}, 4, 4)) == 2
        assert len(runner.get_nearby_tile_shapes(ts, {(0, 0): ((10, 0), (11, 0))}, Sprite(x=2, y=2))) == 2

    def test_rect_vs_tilemap_union(self):
        ts = solid_set(23)
        assert rect_vs_tilemap(0, 0, 16, 16, {(0, 0): ((107, 0), (23, 0))}, ts, (16, 16)) is True
        assert rect_vs_tilemap(0, 0, 16, 16, {(0, 0): ((107, 0),)}, ts, (16, 16)) is False

    def test_legacy_cells_still_work(self):
        ts = solid_set(23)
        runner = CollisionRunner.from_game_type("topdown", tile_size=(16, 16))
        assert runner._collides_at(Sprite(x=2, y=2), ts, {(0, 0): 23}) is True
        assert runner._collides_at(Sprite(x=2, y=2), ts, {(0, 0): (23,)}) is True
        assert rect_vs_tilemap(0, 0, 16, 16, {(0, 0): 23}, ts, (16, 16)) is True
        world = PhysicsWorld(tile_map={(0, 0): 23}, tileset_collision=ts)
        assert world.tile_map == {(0, 0): ((23, 0),)}
        assert world.cell_has_collision((0, 0)) is True

    def test_iter_cell_ids_tolerant(self):
        assert iter_cell_ids(None) == ()
        assert iter_cell_ids(5) == (5,)
        assert iter_cell_ids((5, 7)) == (5, 7)
        assert iter_cell_ids(((5, 1), (7, 0))) == (5, 7)
        assert iter_cell_ids([5, 7]) == (5, 7)
        assert iter_cell_ids(True) == ()

    def test_flat_int_pair_is_two_legacy_tiles(self):
        """(23, 1) reads as gids 23 and 1 — never 'gid 23 + FLIP_H'.
        A single flipped tile must nest: ((23, 1),)."""
        from tilemap_parser import iter_cell_entries
        assert iter_cell_entries((23, 1)) == ((23, 0), (1, 0))
        assert iter_cell_entries(((23, 1),)) == ((23, 1),)
        assert iter_cell_entries(23) == ((23, 0),)


# --- from_map end-to-end (the reported bug) ------------------------------

class TestFromMapUnion:
    def test_entry_repro_deco_either_order_stays_solid(self):
        """tiles gids 23/24 + tileprops 107/108 at same cells, both orders."""
        ts = solid_set(23, 24)
        td = loader(payload_two_layers([
            ("tiles", 3, [(13, 17, 23), (14, 17, 24)]),
            ("tileprops", 2, [(13, 17, 107), (14, 17, 108)]),
        ]))
        world = PhysicsWorld.from_map(td, ts, use_gids=True)
        assert world.tile_map[(13, 17)] == ((107, 0), (23, 0))
        assert world.cell_has_collision((13, 17)) is True
        assert world.cell_has_collision((14, 17)) is True

        td = loader(payload_two_layers([
            ("tileprops", 5, [(13, 17, 107), (14, 17, 108)]),
            ("tiles", 0, [(13, 17, 23), (14, 17, 24)]),
        ]))
        world = PhysicsWorld.from_map(td, ts, use_gids=True)
        assert world.tile_map[(13, 17)] == ((23, 0), (107, 0))
        assert world.cell_has_collision((13, 17)) is True
        assert world.cell_has_collision((14, 17)) is True

    def test_platformer_lands_on_stacked_cell(self):
        ts = solid_set(23)
        td = loader(payload_two_layers([
            ("tiles", 0, [(0, 1, 23)]),
            ("tileprops", 1, [(0, 1, 107)]),
        ]))
        world = PhysicsWorld.from_map(td, ts, use_gids=True)
        runner = CollisionRunner.from_world(world)
        assert world.cell_has_collision((0, 1)) is True
        assert runner._collides_at_platformer(Sprite(x=2, y=10), ts, world.tile_map, world=world) is True

    def test_exclude_layers_flows_through_from_map(self):
        ts = solid_set(23)
        td = loader(payload_two_layers([
            ("tiles", 0, [(0, 0, 23)]),
            ("deco", 1, [(0, 0, 107), (5, 5, 108)]),
        ]))
        world = PhysicsWorld.from_map(td, ts, exclude_layers={"deco"}, use_gids=True)
        assert world.tile_map == {(0, 0): ((23, 0),)}


# --- nav grid union -------------------------------------------------------

class TestNavUnion:
    def test_solid_plus_deco_is_solid(self):
        grid = NavGrid({(0, 0): ((107, 0), (23, 0))}, solid_set(23), (16, 16), map_size=(1, 1))
        assert grid.is_solid(0, 0) is True
        assert grid.is_walkable(0, 0) is False

    def test_deco_only_walkable(self):
        grid = NavGrid({(0, 0): ((107, 0),)}, solid_set(23), (16, 16), map_size=(1, 1))
        assert grid.is_walkable(0, 0) is True

    def test_one_way_union_rules(self):
        ts = TilesetCollision(tileset_name="t", tile_size=(16, 16), tiles={
            1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=list(FULL), one_way=True)]),
            2: TileCollisionData(tile_id=2, shapes=[CollisionPolygon(vertices=list(FULL))]),
        })
        both = NavGrid({(0, 0): ((1, 0), (2, 0))}, ts, (16, 16), map_size=(1, 1))
        assert both.is_solid(0, 0) is True
        assert both.is_one_way(0, 0) is False
        one = NavGrid({(0, 0): ((1, 0),)}, ts, (16, 16), map_size=(1, 1))
        assert one.is_one_way(0, 0) is True
