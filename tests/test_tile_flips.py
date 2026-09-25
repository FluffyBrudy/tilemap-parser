"""Tile flip-transform tests (Godot parity, battle-tested).

Convention (documented, Tiled transpose-first): diagonal transpose, then
horizontal / vertical mirrors in tile-local space.  Winding flips are
harmless — the narrowphase is winding-independent.
"""

import pygame
import pytest

from tilemap_parser import (
    FLIP_D,
    FLIP_H,
    FLIP_V,
    CollisionRunner,
    PhysicsWorld,
    TileCollisionData,
    CollisionPolygon,
    TilesetCollision,
    RectangleShape,
    flip_flags,
    flip_vertices,
    flipped_data,
)
from tilemap_parser.runtime.renderer import _apply_tile_flip, _tile_flip_flags

TSZ = (16, 16)

# bottom-left right triangle (x <= y): blocks left-bottom, open right-top
TRI_BL = [(0.0, 0.0), (0.0, 16.0), (16.0, 16.0)]
LEFT_HALF = [(0.0, 0.0), (8.0, 0.0), (8.0, 16.0), (0.0, 16.0)]
FULL = [(0.0, 0.0), (16.0, 0.0), (16.0, 16.0), (0.0, 16.0)]


class Sprite:
    def __init__(self, x=0, y=0, w=4, h=4):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.collision_shape = RectangleShape(width=w, height=h)
        self.collision_mask = 1
        self.collision_layer = 1


def tri_set(gid=10):
    return TilesetCollision(tileset_name="t", tile_size=TSZ, tiles={
        gid: TileCollisionData(tile_id=gid, shapes=[CollisionPolygon(vertices=list(TRI_BL))])})


def probe(ts, tile_map, x, y):
    runner = CollisionRunner.from_game_type("topdown", tile_size=TSZ)
    return bool(runner._collides_at(Sprite(x=x, y=y), ts, tile_map))


class TestFlipConvention:
    def test_flags_encode(self):
        assert flip_flags(True, False, False) == FLIP_H == 1
        assert flip_flags(False, True, False) == FLIP_V == 2
        assert flip_flags(False, False, True) == FLIP_D == 4
        assert flip_flags(True, True, True) == 7
        assert flip_flags() == 0

    def test_identity(self):
        assert flip_vertices(TRI_BL, 0, TSZ) == list(TRI_BL)

    def test_flip_h_mirrors_x(self):
        assert flip_vertices([(0.0, 4.0)], FLIP_H, TSZ) == [(16.0, 4.0)]

    def test_flip_v_mirrors_y(self):
        assert flip_vertices([(3.0, 0.0)], FLIP_V, TSZ) == [(3.0, 16.0)]

    def test_transpose_swaps_axes(self):
        assert flip_vertices([(2.0, 5.0)], FLIP_D, TSZ) == [(5.0, 2.0)]

    def test_combo_h_v_d_on_left_half_is_bottom_half(self):
        got = flip_vertices(LEFT_HALF, FLIP_H | FLIP_V | FLIP_D, TSZ)
        # D: left half -> full-width top half; H: full-width mirror (no-op);
        # V: top -> full-width bottom half
        assert sorted(got) == sorted([(0.0, 8.0), (16.0, 8.0), (16.0, 16.0), (0.0, 16.0)])

    def test_transpose_swaps_extents_on_non_square(self):
        size = (32, 16)
        left_q = [(0.0, 0.0), (8.0, 0.0), (8.0, 16.0), (0.0, 16.0)]
        got = flip_vertices(left_q, FLIP_D, size)
        # transpose -> full-width top strip; grid cell itself unchanged
        assert sorted(got) == sorted([(0.0, 0.0), (0.0, 8.0), (16.0, 8.0), (16.0, 0.0)])

    def test_transposed_non_square_collides_top_strip(self):
        size = (32, 16)
        ts = TilesetCollision(tileset_name="t", tile_size=size, tiles={
            9: TileCollisionData(tile_id=9, shapes=[CollisionPolygon(
                vertices=[(0.0, 0.0), (8.0, 0.0), (8.0, 16.0), (0.0, 16.0)])])})
        runner = CollisionRunner.from_game_type("topdown", tile_size=size)
        m = {(0, 0): ((9, FLIP_D),)}
        # transposed shape covers x[0,16] y[0,8] of the 32x16 cell
        assert bool(runner._collides_at(Sprite(x=4, y=2), ts, m)) is True
        assert bool(runner._collides_at(Sprite(x=4, y=10), ts, m)) is False

    def test_flipped_data_preserves_metadata(self):
        base = TileCollisionData(tile_id=9, shapes=[CollisionPolygon(vertices=list(TRI_BL), one_way=True)],
                                 collision_layer=2, collision_mask=4)
        out = flipped_data(base, FLIP_H, TSZ)
        assert out.tile_id == 9
        assert out.collision_layer == 2 and out.collision_mask == 4
        assert out.shapes[0].one_way is True

    def test_flipped_data_identity_returns_base(self):
        base = TileCollisionData(tile_id=9, shapes=[CollisionPolygon(vertices=list(TRI_BL))])
        assert flipped_data(base, 0, TSZ) is base


class TestFlipCollision:
    def test_unflipped_triangle_sides(self):
        ts = tri_set()
        assert probe(ts, {(0, 0): ((10, 0),)}, 1, 11) is True    # left-bottom inside
        assert probe(ts, {(0, 0): ((10, 0),)}, 11, 2) is False   # right-top outside

    def test_flip_h_moves_block_to_right(self):
        ts = tri_set()
        assert probe(ts, {(0, 0): ((10, FLIP_H),)}, 11, 11) is True
        assert probe(ts, {(0, 0): ((10, FLIP_H),)}, 0, 0) is False

    def test_flip_v_moves_block_to_top(self):
        ts = tri_set()
        assert probe(ts, {(0, 0): ((10, FLIP_V),)}, 1, 1) is True
        assert probe(ts, {(0, 0): ((10, FLIP_V),)}, 11, 11) is False

    def test_flip_d_transposes_block(self):
        ts = tri_set()
        # x<=y becomes y<=x: bottom-right triangle
        assert probe(ts, {(0, 0): ((10, FLIP_D),)}, 11, 2) is True
        assert probe(ts, {(0, 0): ((10, FLIP_D),)}, 2, 11) is False

    def test_full_block_invariant_under_all_flags(self):
        ts = TilesetCollision(tileset_name="t", tile_size=TSZ, tiles={
            1: TileCollisionData(tile_id=1, shapes=[CollisionPolygon(vertices=list(FULL))])})
        runner = CollisionRunner.from_game_type("topdown", tile_size=TSZ)
        pts = [(x, y) for x in (0, 4, 8, 12) for y in (0, 4, 8, 12)]
        base = [bool(runner._collides_at(Sprite(x=x, y=y), ts, {(0, 0): ((1, 0),)})) for x, y in pts]
        for flags in range(1, 8):
            got = [bool(runner._collides_at(Sprite(x=x, y=y), ts, {(0, 0): ((1, flags),)})) for x, y in pts]
            assert got == base, f"full block changed under flags={flags}"

    def test_mixed_flips_same_cell_union(self):
        """Left-half unflipped + left-half flipped-h (= right half): both sides."""
        ts = TilesetCollision(tileset_name="t", tile_size=TSZ, tiles={
            10: TileCollisionData(tile_id=10, shapes=[CollisionPolygon(vertices=list(LEFT_HALF))])})
        m = {(0, 0): ((10, 0), (10, FLIP_H))}
        assert probe(ts, m, 1, 4) is True
        assert probe(ts, m, 11, 4) is True

    def test_world_cache_identity(self):
        ts = tri_set()
        world = PhysicsWorld(tile_map={(0, 0): ((10, FLIP_H),)}, tileset_collision=ts)
        a = world.resolve_stack_entry((10, FLIP_H))
        b = world.resolve_stack_entry((10, FLIP_H))
        assert a is b
        assert world.resolve_stack_entry((10, 0)) is ts.tiles[10]

    def test_one_way_top_edge_relocates_under_flip_v(self):
        ts = TilesetCollision(tileset_name="t", tile_size=TSZ, tiles={
            3: TileCollisionData(tile_id=3, shapes=[CollisionPolygon(
                vertices=[(0.0, 0.0), (16.0, 0.0), (16.0, 4.0), (0.0, 4.0)], one_way=True)])})
        world = PhysicsWorld(tile_map={(0, 0): ((3, FLIP_V),)}, tileset_collision=ts, tile_size=TSZ)
        data = world.resolve_stack_entry((3, FLIP_V))
        assert min(v[1] for v in data.shapes[0].vertices) == 12.0

    def test_platformer_lands_on_flipped_slope(self):
        ts = TilesetCollision(tileset_name="t", tile_size=TSZ, tiles={
            10: TileCollisionData(tile_id=10, shapes=[CollisionPolygon(vertices=list(LEFT_HALF))])})
        world = PhysicsWorld(tile_map={(0, 1): ((10, FLIP_H),)}, tileset_collision=ts, tile_size=TSZ)
        runner = CollisionRunner.from_world(world)
        # flipped-h left half = right half: sprite over right side collides...
        assert runner._collides_at_platformer(Sprite(x=10, y=13), ts, world.tile_map, world=world) is True
        # ...sprite over left side does not
        assert runner._collides_at_platformer(Sprite(x=0, y=13), ts, world.tile_map, world=world) is False


class TestRendererFlip:
    def _pattern(self):
        pygame.init()
        surf = pygame.Surface((4, 4))
        cols = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
        for i, c in enumerate(cols):
            surf.set_at((i, 0), c)
            surf.set_at((0, i), c)
        return surf

    def test_flip_h_pixels(self):
        s = _apply_tile_flip(self._pattern(), FLIP_H)
        # row0 was R,G,B,W left->right; flipped-h must read W,B,G,R
        assert [self._pattern().get_at((3 - i, 0))[:3] for i in range(4)] == \
               [s.get_at((i, 0))[:3] for i in range(4)]

    def test_flip_v_pixels(self):
        p, s = self._pattern(), _apply_tile_flip(self._pattern(), FLIP_V)
        assert [p.get_at((0, 3 - i))[:3] for i in range(4)] == \
               [s.get_at((0, i))[:3] for i in range(4)]

    def test_transpose_pixels(self):
        p, s = self._pattern(), _apply_tile_flip(self._pattern(), FLIP_D)
        assert [p.get_at((0, i))[:3] for i in range(4)] == \
               [s.get_at((i, 0))[:3] for i in range(4)]

    def test_flags_from_tile(self):
        class T:
            flip_h = True
            flip_v = False
            flip_d = True
        assert _tile_flip_flags(T()) == FLIP_H | FLIP_D
        assert _tile_flip_flags(object()) == 0


class TestFlipConstantParity:
    """Renderer mirrors world.FLIP_* by value (dependency-light); pin it."""

    def test_renderer_mirrors_world_flags(self):
        from tilemap_parser.runtime import renderer as renderer_mod
        from tilemap_parser.runtime.world import FLIP_D as W_D
        from tilemap_parser.runtime.world import FLIP_H as W_H
        from tilemap_parser.runtime.world import FLIP_V as W_V

        assert (renderer_mod._FLIP_H, renderer_mod._FLIP_V, renderer_mod._FLIP_D) == (
            W_H,
            W_V,
            W_D,
        )
