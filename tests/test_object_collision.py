"""
Tests for tilemap_parser.object_collision.

Covers:
- _should_collide (layer filtering)
- check_collision (shape dispatch, layer filter, normal direction)
- ObjectCollisionManager (add/remove, queries, duplicates, warnings)
"""

import warnings
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.collision import CircleShape, CollisionPolygon, RectangleShape
from tilemap_parser.object_collision import (
    CollisionHit,
    ObjectCollisionManager,
    _should_collide,
    check_collision,
)


# ---------------------------------------------------------------------------
# Helpers — concrete objects implementing ICollidableObject
# ---------------------------------------------------------------------------

class _DummyObject:
    """Minimal collidable object for tests."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        shape=None,
        collision_layer: int = 1,
        collision_mask: int = 0xFFFFFFFF,
    ):
        self.x = x
        self.y = y
        self.collision_shape = shape or RectangleShape(width=10.0, height=10.0)
        self.collision_layer = collision_layer
        self.collision_mask = collision_mask


def _make_circle(x, y, radius, collision_layer=1, collision_mask=0xFFFFFFFF):
    return _DummyObject(x, y, CircleShape(radius=radius), collision_layer, collision_mask)


def _make_rect(x, y, w, h, collision_layer=1, collision_mask=0xFFFFFFFF):
    return _DummyObject(x, y, RectangleShape(width=w, height=h), collision_layer, collision_mask)


def _make_poly(x, y, vertices, collision_layer=1, collision_mask=0xFFFFFFFF):
    return _DummyObject(x, y, CollisionPolygon(vertices=vertices), collision_layer, collision_mask)


# ---------------------------------------------------------------------------
# _should_collide
# ---------------------------------------------------------------------------

class TestShouldCollide:
    def test_default_layers_collide(self):
        a = _make_rect(0, 0, 10, 10)
        b = _make_rect(0, 0, 10, 10)
        assert _should_collide(a, b) is True

    def test_mutual_agreement(self):
        a = _make_rect(0, 0, 10, 10, collision_layer=1, collision_mask=2)
        b = _make_rect(0, 0, 10, 10, collision_layer=2, collision_mask=1)
        assert _should_collide(a, b) is True

    def test_one_disagrees_no_collision(self):
        a = _make_rect(0, 0, 10, 10, collision_layer=1, collision_mask=2)
        b = _make_rect(0, 0, 10, 10, collision_layer=2, collision_mask=0)
        assert _should_collide(a, b) is False

    def test_both_disagree_no_collision(self):
        a = _make_rect(0, 0, 10, 10, collision_layer=1, collision_mask=4)
        b = _make_rect(0, 0, 10, 10, collision_layer=2, collision_mask=8)
        assert _should_collide(a, b) is False

    def test_missing_attributes_use_defaults(self):
        class BareObject:
            x = 0.0
            y = 0.0
            collision_shape = RectangleShape(width=10, height=10)
        assert _should_collide(BareObject(), BareObject()) is True


# ---------------------------------------------------------------------------
# check_collision
# ---------------------------------------------------------------------------

class TestCheckCollisionCircleCircle:
    def test_colliding(self):
        a = _make_circle(0, 0, 10)
        b = _make_circle(15, 0, 10)
        hit = check_collision(a, b)
        assert hit is not None
        assert hit.depth == pytest.approx(5.0)

    def test_separated(self):
        a = _make_circle(0, 0, 5)
        b = _make_circle(20, 0, 5)
        assert check_collision(a, b) is None


class TestCheckCollisionRectRect:
    def test_colliding(self):
        a = _make_rect(0, 0, 10, 10)
        b = _make_rect(5, 0, 10, 10)
        hit = check_collision(a, b)
        assert hit is not None
        assert hit.depth == pytest.approx(5.0)

    def test_separated(self):
        a = _make_rect(0, 0, 10, 10)
        b = _make_rect(20, 0, 10, 10)
        assert check_collision(a, b) is None


class TestCheckCollisionRectCircle:
    def test_colliding(self):
        r = _make_rect(0, 0, 10, 10)
        c = _make_circle(12, 5, 5)
        hit = check_collision(r, c)
        assert hit is not None
        assert hit.depth == pytest.approx(3.0)

    def test_separated(self):
        r = _make_rect(0, 0, 10, 10)
        c = _make_circle(30, 5, 5)
        assert check_collision(r, c) is None


class TestCheckCollisionCircleRect:
    def test_normal_flipped(self):
        """Circle vs Rect should have normal from circle to rect."""
        c = _make_circle(12, 5, 5)
        r = _make_rect(0, 0, 10, 10)
        hit = check_collision(c, r)
        assert hit is not None
        # Normal should point from circle toward rect (left, so negative X)
        assert hit.normal[0] == pytest.approx(-1.0)


class TestCheckCollisionLayerFiltering:
    def test_layer_blocks(self):
        a = _make_rect(0, 0, 10, 10, collision_layer=1, collision_mask=2)
        b = _make_rect(5, 0, 10, 10, collision_layer=2, collision_mask=0)
        # Geometrically overlapping, but layer filter blocks
        assert check_collision(a, b) is None


class TestCheckCollisionPolygon:
    def test_poly_vs_poly_colliding(self):
        p1 = _make_poly(0, 0, [(0, 0), (10, 0), (10, 10), (0, 10)])
        p2 = _make_poly(5, 0, [(0, 0), (10, 0), (10, 10), (0, 10)])
        hit = check_collision(p1, p2)
        assert hit is not None
        assert hit.depth > 0

    def test_poly_vs_circle_colliding(self):
        p = _make_poly(0, 0, [(0, 0), (10, 0), (10, 10), (0, 10)])
        c = _make_circle(12, 5, 5)
        hit = check_collision(p, c)
        assert hit is not None
        assert hit.depth > 0

    def test_circle_vs_poly_normal_flipped(self):
        """Circle vs Polygon — normal should point from circle toward polygon."""
        c = _make_circle(12, 5, 5)
        p = _make_poly(0, 0, [(0, 0), (10, 0), (10, 10), (0, 10)])
        hit = check_collision(c, p)
        assert hit is not None
        # Normal should point from circle toward polygon (left, negative X)
        assert hit.normal[0] < 0

    def test_poly_vs_rect_colliding(self):
        p = _make_poly(0, 0, [(0, 0), (10, 0), (10, 10), (0, 10)])
        r = _make_rect(5, 0, 10, 10)
        hit = check_collision(p, r)
        assert hit is not None
        assert hit.depth > 0

    def test_rect_vs_poly_normal_flipped(self):
        """Rect vs Polygon — normal should point from rect toward polygon."""
        r = _make_rect(5, 0, 10, 10)
        p = _make_poly(0, 0, [(0, 0), (10, 0), (10, 10), (0, 10)])
        hit = check_collision(r, p)
        assert hit is not None
        # Normal should point from rect toward polygon (left, negative X)
        assert hit.normal[0] < 0

    def test_manager_with_polygons(self):
        mgr = ObjectCollisionManager()
        p1 = _make_poly(0, 0, [(0, 0), (10, 0), (10, 10), (0, 10)])
        p2 = _make_poly(5, 0, [(0, 0), (10, 0), (10, 10), (0, 10)])
        mgr.add_object(p1)
        mgr.add_object(p2)
        hits = mgr.check_all_collisions()
        assert len(hits) == 1
        assert hits[0].depth > 0


# ---------------------------------------------------------------------------
# ObjectCollisionManager
# ---------------------------------------------------------------------------

class TestManagerAddRemove:
    def test_add_and_remove(self):
        mgr = ObjectCollisionManager()
        obj = _make_rect(0, 0, 10, 10)
        mgr.add_object(obj)
        assert len(mgr.objects) == 1
        mgr.remove_object(obj)
        assert len(mgr.objects) == 0

    def test_add_duplicate_warns(self):
        mgr = ObjectCollisionManager()
        obj = _make_rect(0, 0, 10, 10)
        mgr.add_object(obj)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mgr.add_object(obj)
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "already" in str(w[0].message).lower()
        assert len(mgr.objects) == 1

    def test_remove_nonexistent_warns(self):
        mgr = ObjectCollisionManager()
        obj = _make_rect(0, 0, 10, 10)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mgr.remove_object(obj)
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "not" in str(w[0].message).lower()


class TestManagerCheckAll:
    def test_no_duplicates(self):
        """Three overlapping circles — should produce exactly 3 pairs."""
        mgr = ObjectCollisionManager()
        for x in [0, 5, 10]:
            mgr.add_object(_make_circle(x, 0, 10))
        hits = mgr.check_all_collisions()
        assert len(hits) == 3

    def test_empty(self):
        mgr = ObjectCollisionManager()
        assert mgr.check_all_collisions() == []

    def test_single_object(self):
        mgr = ObjectCollisionManager()
        mgr.add_object(_make_rect(0, 0, 10, 10))
        assert mgr.check_all_collisions() == []


class TestManagerCheckObject:
    def test_returns_hits(self):
        mgr = ObjectCollisionManager()
        a = _make_circle(0, 0, 10)
        b = _make_circle(15, 0, 10)
        c = _make_circle(100, 0, 10)  # far away
        mgr.add_object(a)
        mgr.add_object(b)
        mgr.add_object(c)
        hits = mgr.check_object(a)
        assert len(hits) == 1
        assert hits[0].object_b is b

    def test_skips_self(self):
        mgr = ObjectCollisionManager()
        obj = _make_rect(0, 0, 10, 10)
        mgr.add_object(obj)
        hits = mgr.check_object(obj)
        assert hits == []

    def test_layer_filtering(self):
        mgr = ObjectCollisionManager()
        a = _make_rect(0, 0, 10, 10, collision_layer=1, collision_mask=0)
        b = _make_rect(5, 0, 10, 10, collision_layer=1, collision_mask=0)
        mgr.add_object(a)
        mgr.add_object(b)
        hits = mgr.check_object(a)
        assert hits == []
