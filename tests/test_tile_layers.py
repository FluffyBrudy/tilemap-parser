"""Tile physics layer/mask filtering tests (Godot parity, battle-tested).

Rule (same as bodies via should_collide): mutual agreement — sprite and
tile must each accept the other.  Defaults (tile 1/all, sprite 1/all)
preserve historic collide-with-everything behaviour.
"""

import pytest

from tilemap_parser import (
    CollisionRunner,
    PhysicsWorld,
    TileCollisionData,
    CollisionPolygon,
    TilesetCollision,
    RectangleShape,
    parse_map_dict,
    parse_tileset_collision,
    rect_vs_tilemap,
)
from tilemap_parser.runtime.navigation.nav_grid import NavGrid

FULL = [(0.0, 0.0), (16.0, 0.0), (16.0, 16.0), (0.0, 16.0)]


class Sprite:
    def __init__(self, x=2, y=2, mask=1, layer=1):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.collision_shape = RectangleShape(width=8, height=8)
        self.collision_mask = mask
        self.collision_layer = layer


class BareSprite:
    """No layer/mask attrs at all — loud TypeError, never implicit."""

    def __init__(self):
        self.x = 2
        self.y = 2
        self.collision_shape = RectangleShape(width=8, height=8)


def tile_set(layer=1, mask=0xFFFFFFFF, gid=23):
    return TilesetCollision(tileset_name="t", tile_size=(16, 16), tiles={
        gid: TileCollisionData(tile_id=gid, shapes=[CollisionPolygon(vertices=list(FULL))],
                               collision_layer=layer, collision_mask=mask)})


def run(topdown=True):
    return CollisionRunner.from_game_type("topdown" if topdown else "platformer", tile_size=(16, 16))


class TestDefaultsPreserved:
    def test_default_tile_vs_default_sprite_collides(self):
        assert run()._collides_at(Sprite(), tile_set(), {(0, 0): ((23, 0),)}) is True

    def test_bare_sprite_without_attrs_raises(self):
        with pytest.raises(TypeError):
            run()._collides_at(BareSprite(), tile_set(), {(0, 0): ((23, 0),)})

    def test_parse_defaults(self):
        col = parse_tileset_collision({
            "tileset_name": "t", "tile_size": [16, 16],
            "tiles": {"5": {"tile_id": 5, "shapes": [
                {"type": "polygon", "vertices": [[0, 0], [16, 0], [16, 16], [0, 16]]}]}}})
        assert col.tiles[5].collision_layer == 1
        assert col.tiles[5].collision_mask == 0xFFFFFFFF


class TestMutualFiltering:
    def test_tile_layer_misses_sprite_mask_passes_through(self):
        assert run()._collides_at(Sprite(mask=1), tile_set(layer=2), {(0, 0): ((23, 0),)}) is False

    def test_matching_mask_collides(self):
        assert run()._collides_at(Sprite(mask=0b11), tile_set(layer=2), {(0, 0): ((23, 0),)}) is True

    def test_mutual_tile_mask_excludes_sprite_layer(self):
        ts = tile_set(layer=2, mask=0)  # tile accepts nobody back
        assert run()._collides_at(Sprite(mask=0b11, layer=1), ts, {(0, 0): ((23, 0),)}) is False

    def test_mutual_both_sides_agree(self):
        ts = tile_set(layer=2, mask=0b10)
        assert run()._collides_at(Sprite(mask=0b10, layer=0b10), ts, {(0, 0): ((23, 0),)}) is True

    def test_mixed_stack_filters_per_entry(self):
        ts = TilesetCollision(tileset_name="t", tile_size=(16, 16), tiles={
            10: TileCollisionData(tile_id=10, shapes=[CollisionPolygon(vertices=list(FULL))],
                                 collision_layer=1, collision_mask=0xFFFFFFFF),
            11: TileCollisionData(tile_id=11, shapes=[CollisionPolygon(vertices=list(FULL))],
                                 collision_layer=2, collision_mask=0xFFFFFFFF)})
        m = {(0, 0): ((10, 0), (11, 0))}
        assert run()._collides_at(Sprite(mask=1), ts, m) is True   # via gid 10
        assert run()._collides_at(Sprite(mask=2), ts, m) is True   # via gid 11
        ts2 = TilesetCollision(tileset_name="t", tile_size=(16, 16), tiles={
            11: TileCollisionData(tile_id=11, shapes=[CollisionPolygon(vertices=list(FULL))],
                                 collision_layer=2, collision_mask=0xFFFFFFFF)})
        assert run()._collides_at(Sprite(mask=1), ts2, {(0, 0): ((11, 0),)}) is False

    def test_platformer_respects_mask(self):
        ts = tile_set(layer=2)
        r = run(topdown=False)
        assert r._collides_at_platformer(Sprite(mask=1), ts, {(0, 0): ((23, 0),)}) is False
        assert r._collides_at_platformer(Sprite(mask=2), ts, {(0, 0): ((23, 0),)}) is True

    def test_first_hit_respects_mask(self):
        ts = tile_set(layer=2)
        r = run()
        assert r._first_colliding_shape(Sprite(mask=1), ts, {(0, 0): ((23, 0),)}) is None
        assert r._first_colliding_shape(Sprite(mask=2), ts, {(0, 0): ((23, 0),)}) is not None

    def test_parse_layer_mask_from_properties(self):
        col = parse_tileset_collision({
            "tileset_name": "t", "tile_size": [16, 16],
            "tiles": {"7": {"tile_id": 7, "properties": {"collision_layer": 2, "collision_mask": 4},
                            "shapes": [{"type": "polygon",
                                        "vertices": [[0, 0], [16, 0], [16, 16], [0, 16]]}]}}})
        assert col.tiles[7].collision_layer == 2
        assert col.tiles[7].collision_mask == 4

    def test_merge_carries_layer_mask(self):
        a = tile_set(layer=2, mask=4, gid=1)
        merged = TilesetCollision.merge([a], [100])
        assert merged.tiles[101].collision_layer == 2
        assert merged.tiles[101].collision_mask == 4


class TestSpriteLessQueries:
    def test_rect_default_unfiltered(self):
        assert rect_vs_tilemap(0, 0, 16, 16, {(0, 0): ((23, 0),)}, tile_set(layer=2), (16, 16)) is True

    def test_rect_mask_filters_tile_side(self):
        ts = tile_set(layer=2)
        assert rect_vs_tilemap(0, 0, 16, 16, {(0, 0): ((23, 0),)}, ts, (16, 16), collision_mask=1) is False
        assert rect_vs_tilemap(0, 0, 16, 16, {(0, 0): ((23, 0),)}, ts, (16, 16), collision_mask=2) is True

    def test_nav_default_solid(self):
        g = NavGrid({(0, 0): ((23, 0),)}, tile_set(layer=2), (16, 16), map_size=(1, 1))
        assert g.is_solid(0, 0) is True

    def test_nav_mask_filters(self):
        ts = tile_set(layer=2)
        g = NavGrid({(0, 0): ((23, 0),)}, ts, (16, 16), map_size=(1, 1), collision_mask=1)
        assert g.is_walkable(0, 0) is True
        g2 = NavGrid({(0, 0): ((23, 0),)}, ts, (16, 16), map_size=(1, 1), collision_mask=2)
        assert g2.is_solid(0, 0) is True

    def test_shape_getters_stay_unfiltered(self):
        """Shape getters are introspection (no sprite): union of shapes, no mask."""
        ts = tile_set(layer=2)
        r = run()
        assert len(r.get_tile_shapes(ts, {(0, 0): ((23, 0),)}, 4, 4)) == 1


class TestMixedOneWaySolid:
    """Solid + one-way stacked in one cell: solid dominates (Godot-consistent)."""

    def _stack(self):
        return TilesetCollision(tileset_name="t", tile_size=(16, 16), tiles={
            1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=list(FULL), one_way=True)]),
            2: TileCollisionData(tile_id=2, shapes=[CollisionPolygon(vertices=list(FULL))])})

    def test_platformer_blocked_from_below_by_solid(self):
        ts = self._stack()
        r = run(topdown=False)
        s = Sprite(y=10)  # overlapping the cell
        # one-way alone never blocks in the default pass ...
        assert r._collides_at_platformer(s, ts, {(0, 0): ((1, 0),)}) is False
        # ... but stacked solid blocks unconditionally ...
        assert r._collides_at_platformer(s, ts, {(0, 0): ((1, 0), (2, 0))}) is True
        # ... even when the one-way gate explicitly excuses below-approach
        assert r._collides_at_platformer(
            s, ts, {(0, 0): ((1, 0), (2, 0))},
            include_one_way=True, previous_bottom=30.0) is True

    def test_nav_not_one_way_when_solid_present(self):
        ts = self._stack()
        g = NavGrid({(0, 0): ((1, 0), (2, 0))}, ts, (16, 16), map_size=(1, 1))
        assert g.is_solid(0, 0) is True
        assert g.is_one_way(0, 0) is False
