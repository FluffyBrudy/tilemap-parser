"""Facing-flip tests for flip_character_shape (player/bullet turns).

Convention: sprite-local coords, origin = sprite top-left. Horizontal
flip maps x -> W - x, vertical maps y -> H - y. Rectangle offsets are
top-left (size-aware); circle/capsule offsets are centers; polygons
mirror per-vertex (same convention as tile flip_vertices).
"""

import math

import pytest

from tilemap_parser import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
    flip_character_shape,
    get_shape_aabb,
)


def _aabb_center(shape, w, h):
    l, t, r, b = get_shape_aabb(0, 0, shape)
    return ((l + r) / 2, (t + b) / 2)


class TestRectangleFlip:
    def test_flip_h_exact(self):
        s = RectangleShape(width=15.0, height=40.0, offset=(19.0, 10.0))
        out = flip_character_shape(s, (48.0, 48.0))
        assert out.offset == (48.0 - (19.0 + 15.0), 10.0)
        assert (out.width, out.height) == (15.0, 40.0)

    def test_flip_v_exact(self):
        s = RectangleShape(width=15.0, height=40.0, offset=(19.0, 10.0))
        out = flip_character_shape(s, (48.0, 48.0), flip_h=False, flip_v=True)
        assert out.offset == (19.0, 48.0 - (10.0 + 40.0))

    def test_flip_both(self):
        s = RectangleShape(width=10.0, height=20.0, offset=(5.0, 6.0))
        out = flip_character_shape(s, (50.0, 60.0), flip_h=True, flip_v=True)
        assert out.offset == (50.0 - 15.0, 60.0 - 26.0)

    def test_no_flip_returns_equal_copy(self):
        s = RectangleShape(width=10.0, height=20.0, offset=(5.0, 6.0))
        out = flip_character_shape(s, (50.0, 60.0), flip_h=False, flip_v=False)
        assert out == s and out is not s


class TestCircleFlip:
    def test_center_mirrors(self):
        s = CircleShape(radius=8.0, offset=(10.0, 20.0))
        out = flip_character_shape(s, (48.0, 64.0))
        assert out.offset == (38.0, 20.0)
        assert out.radius == 8.0

    def test_flip_v(self):
        s = CircleShape(radius=8.0, offset=(10.0, 20.0))
        out = flip_character_shape(s, (48.0, 64.0), flip_h=False, flip_v=True)
        assert out.offset == (10.0, 44.0)

    def test_centered_circle_is_fixed_point(self):
        s = CircleShape(radius=8.0, offset=(24.0, 24.0))
        out = flip_character_shape(s, (48.0, 48.0))
        assert out.offset == (24.0, 24.0)


class TestCapsuleFlip:
    def test_flip_h(self):
        s = CapsuleShape(radius=8.0, height=16.0, offset=(10.0, 4.0))
        out = flip_character_shape(s, (48.0, 48.0))
        assert out.offset == (38.0, 4.0)
        assert (out.radius, out.height) == (8.0, 16.0)

    def test_flip_v_moves_top_to_mirrored_bottom(self):
        s = CapsuleShape(radius=8.0, height=16.0, offset=(10.0, 4.0))
        out = flip_character_shape(s, (48.0, 48.0), flip_h=False, flip_v=True)
        assert out.offset == (10.0, 48.0 - (4.0 + 16.0))


class TestPolygonFlip:
    def test_matches_tile_flip_vertices(self):
        from tilemap_parser import FLIP_H, FLIP_V, flip_vertices

        verts = [(0.0, 0.0), (16.0, 0.0), (16.0, 16.0), (0.0, 16.0)]
        assert flip_character_shape(
            CollisionPolygon(vertices=list(verts)), (16.0, 16.0), flip_h=True
        ).vertices == flip_vertices(list(verts), FLIP_H, (16.0, 16.0))
        assert flip_character_shape(
            CollisionPolygon(vertices=list(verts)), (16.0, 16.0), flip_h=False, flip_v=True
        ).vertices == flip_vertices(list(verts), FLIP_V, (16.0, 16.0))
        assert flip_character_shape(
            CollisionPolygon(vertices=list(verts)), (16.0, 16.0), flip_h=True, flip_v=True
        ).vertices == flip_vertices(list(verts), FLIP_H | FLIP_V, (16.0, 16.0))

    def test_one_way_preserved(self):
        s = CollisionPolygon(vertices=[(0.0, 0.0), (8.0, 0.0), (8.0, 8.0)], one_way=True)
        out = flip_character_shape(s, (16.0, 16.0))
        assert out.one_way is True


class TestInvariants:
    SHAPES = [
        RectangleShape(width=15.0, height=40.0, offset=(19.0, 10.0)),
        CircleShape(radius=8.0, offset=(10.0, 20.0)),
        CapsuleShape(radius=8.0, height=16.0, offset=(10.0, 4.0)),
        CollisionPolygon(vertices=[(2.0, 3.0), (14.0, 3.0), (14.0, 20.0), (2.0, 20.0)]),
    ]

    @pytest.mark.parametrize("flip_h,flip_v", [(True, False), (False, True), (True, True)])
    def test_double_flip_is_identity(self, flip_h, flip_v):
        for s in self.SHAPES:
            once = flip_character_shape(s, (48.0, 64.0), flip_h=flip_h, flip_v=flip_v)
            twice = flip_character_shape(once, (48.0, 64.0), flip_h=flip_h, flip_v=flip_v)
            assert twice == s

    @pytest.mark.parametrize("flip_h,flip_v", [(True, False), (False, True), (True, True)])
    def test_aabb_center_mirrors(self, flip_h, flip_v):
        w, h = 48.0, 64.0
        for s in self.SHAPES:
            cx, cy = _aabb_center(s, w, h)
            out = flip_character_shape(s, (w, h), flip_h=flip_h, flip_v=flip_v)
            ocx, ocy = _aabb_center(out, w, h)
            assert ocx == pytest.approx(w - cx if flip_h else cx)
            assert ocy == pytest.approx(h - cy if flip_v else cy)

    def test_input_never_mutated(self):
        import copy

        for s in self.SHAPES:
            before = copy.deepcopy(s)
            flip_character_shape(s, (48.0, 64.0), flip_h=True, flip_v=True)
            assert s == before

    def test_aabb_size_preserved(self):
        for s in self.SHAPES:
            l, t, r, b = get_shape_aabb(0, 0, s)
            out = flip_character_shape(s, (48.0, 64.0))
            ol, ot, orr, ob = get_shape_aabb(0, 0, out)
            assert (orr - ol, ob - ot) == pytest.approx((r - l, b - t))


class TestInvalid:
    def test_zero_size(self):
        with pytest.raises(ValueError):
            flip_character_shape(RectangleShape(width=1, height=1), (0.0, 10.0))

    def test_negative_size(self):
        with pytest.raises(ValueError):
            flip_character_shape(RectangleShape(width=1, height=1), (10.0, -5.0))

    def test_nan_size(self):
        with pytest.raises(ValueError):
            flip_character_shape(RectangleShape(width=1, height=1), (math.nan, 10.0))

    def test_unknown_shape(self):
        with pytest.raises(TypeError):
            flip_character_shape(object(), (10.0, 10.0))  # pyright: ignore
