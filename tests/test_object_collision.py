"""
Tests for tilemap_parser.object_collision.

Covers:
- should_collide (layer filtering)
- check_collision (shape dispatch, layer filter, normal direction)
- CollisionHit helpers (resolve, involves, other)
- ObjectCollisionManager (add/remove, queries, duplicates, warnings)
"""

import warnings
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)
import tilemap_parser.runtime.object_collision as object_collision_runtime
from tilemap_parser.runtime.object_collision import (
    CollisionHit,
    ObjectCollisionManager,
    should_collide,
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
# should_collide
# ---------------------------------------------------------------------------

class TestShouldCollide:
    def test_default_layers_collide(self):
        a = _make_rect(0, 0, 10, 10)
        b = _make_rect(0, 0, 10, 10)
        assert should_collide(a, b) is True

    def test_mutual_agreement(self):
        a = _make_rect(0, 0, 10, 10, collision_layer=1, collision_mask=2)
        b = _make_rect(0, 0, 10, 10, collision_layer=2, collision_mask=1)
        assert should_collide(a, b) is True

    def test_one_disagrees_no_collision(self):
        a = _make_rect(0, 0, 10, 10, collision_layer=1, collision_mask=2)
        b = _make_rect(0, 0, 10, 10, collision_layer=2, collision_mask=0)
        assert should_collide(a, b) is False

    def test_both_disagree_no_collision(self):
        a = _make_rect(0, 0, 10, 10, collision_layer=1, collision_mask=4)
        b = _make_rect(0, 0, 10, 10, collision_layer=2, collision_mask=8)
        assert should_collide(a, b) is False

    def test_missing_attributes_use_defaults(self):
        class BareObject:
            x = 0.0
            y = 0.0
            collision_shape = RectangleShape(width=10, height=10)
        assert should_collide(BareObject(), BareObject()) is True


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

    def test_circle_fully_inside_rect_has_positive_depth(self):
        r = _make_rect(0, 0, 100, 100)
        c = _make_circle(50, 50, 5)

        hit = check_collision(r, c)

        assert hit is not None
        assert hit.depth == pytest.approx(55.0)
        assert hit.normal == (-1.0, 0.0)


class TestCheckCollisionCircleRect:
    def test_normal_flipped(self):
        """Circle vs Rect should have normal from circle to rect."""
        c = _make_circle(12, 5, 5)
        r = _make_rect(0, 0, 10, 10)
        hit = check_collision(c, r)
        assert hit is not None
        # Normal should point from circle toward rect (left, so negative X)
        assert hit.normal[0] == pytest.approx(-1.0)

    def test_rect_fully_contains_circle_has_positive_depth(self):
        c = _make_circle(50, 50, 5)
        r = _make_rect(0, 0, 100, 100)

        hit = check_collision(c, r)

        assert hit is not None
        assert hit.depth == pytest.approx(55.0)
        assert hit.normal == (1.0, -0.0)


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

    def test_add_value_equal_distinct_objects(self):
        class EqualObject(_DummyObject):
            def __eq__(self, other):
                return isinstance(other, EqualObject)

        mgr = ObjectCollisionManager()
        a = EqualObject(0, 0)
        b = EqualObject(20, 0)

        mgr.add_object(a)
        mgr.add_object(b)

        assert len(mgr.objects) == 2
        assert mgr.objects[0] is a
        assert mgr.objects[1] is b

    def test_remove_nonexistent_warns(self):
        mgr = ObjectCollisionManager()
        obj = _make_rect(0, 0, 10, 10)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mgr.remove_object(obj)
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "not" in str(w[0].message).lower()

    def test_remove_uses_identity_not_equality(self):
        class EqualObject(_DummyObject):
            def __eq__(self, other):
                return isinstance(other, EqualObject)

        mgr = ObjectCollisionManager()
        a = EqualObject(0, 0)
        b = EqualObject(20, 0)
        mgr.add_object(a)
        mgr.add_object(b)

        mgr.remove_object(b)

        assert len(mgr.objects) == 1
        assert mgr.objects[0] is a

    def test_construct_with_objects(self):
        a = _make_rect(0, 0, 10, 10)
        b = _make_rect(20, 0, 10, 10)

        mgr = ObjectCollisionManager([a, b])

        assert len(mgr) == 2
        objects = list(mgr)
        assert objects[0] is a
        assert objects[1] is b
        assert a in mgr
        assert b in mgr

    def test_clear(self):
        mgr = ObjectCollisionManager([_make_rect(0, 0, 10, 10)])

        mgr.clear()

        assert len(mgr) == 0
        assert mgr.objects == []


class TestManagerCheckAll:
    def test_invalid_cell_size_raises(self):
        with pytest.raises(ValueError, match="cell_size"):
            ObjectCollisionManager(cell_size=0)

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

    def test_spatial_broadphase_skips_distant_pairs(self, monkeypatch):
        mgr = ObjectCollisionManager(cell_size=16)
        a = _make_rect(0, 0, 10, 10)
        b = _make_rect(100, 0, 10, 10)
        mgr.add_object(a)
        mgr.add_object(b)
        calls = []

        def fake_check_collision(obj_a, obj_b):
            calls.append((obj_a, obj_b))
            return None

        monkeypatch.setattr(
            object_collision_runtime,
            "check_collision",
            fake_check_collision,
        )

        assert mgr.check_all_collisions() == []
        assert calls == []

    def test_large_object_spanning_cells_collides(self):
        mgr = ObjectCollisionManager(cell_size=16)
        large = _make_rect(0, 0, 64, 16)
        small = _make_rect(48, 0, 8, 8)
        mgr.add_object(large)
        mgr.add_object(small)

        hits = mgr.check_all_collisions()

        assert len(hits) == 1
        assert hits[0].object_a is large
        assert hits[0].object_b is small

    def test_moved_objects_are_reindexed_per_query(self):
        mgr = ObjectCollisionManager(cell_size=16)
        a = _make_rect(0, 0, 10, 10)
        b = _make_rect(100, 0, 10, 10)
        mgr.add_object(a)
        mgr.add_object(b)

        assert mgr.check_all_collisions() == []

        b.x = 8
        hits = mgr.check_all_collisions()

        assert len(hits) == 1
        assert hits[0].involves(a)
        assert hits[0].involves(b)


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

    def test_unmanaged_query_object(self):
        mgr = ObjectCollisionManager(cell_size=16)
        query = _make_rect(0, 0, 10, 10)
        managed = _make_rect(8, 0, 10, 10)
        far = _make_rect(100, 0, 10, 10)
        mgr.add_object(managed)
        mgr.add_object(far)

        hits = mgr.check_object(query)

        assert len(hits) == 1
        assert hits[0].object_a is query
        assert hits[0].object_b is managed


# ---------------------------------------------------------------------------
# CollisionHit helpers
# ---------------------------------------------------------------------------

class TestCollisionHitHelpers:
    def test_resolve_separates(self):
        a = _make_circle(0, 0, 10)
        b = _make_circle(15, 0, 10)
        hit = check_collision(a, b)
        assert hit is not None
        old_dx = abs(a.x - b.x)
        hit.resolve()
        assert abs(a.x - b.x) > old_dx

    def test_involves(self):
        a = _make_circle(0, 0, 10)
        b = _make_circle(15, 0, 10)
        c = _make_circle(100, 0, 10)
        hit = check_collision(a, b)
        assert hit is not None
        assert hit.involves(a) is True
        assert hit.involves(b) is True
        assert hit.involves(c) is False

    def test_other(self):
        a = _make_circle(0, 0, 10)
        b = _make_circle(15, 0, 10)
        hit = check_collision(a, b)
        assert hit is not None
        assert hit.other(a) is b
        assert hit.other(b) is a

    def test_other_raises(self):
        a = _make_circle(0, 0, 10)
        b = _make_circle(15, 0, 10)
        c = _make_circle(100, 0, 10)
        hit = check_collision(a, b)
        assert hit is not None
        with pytest.raises(ValueError, match="not part"):
            hit.other(c)

    # ------------------------------------------------------------------
    # slide_velocity
    # ------------------------------------------------------------------
    def test_slide_head_on(self):
        """Directly into surface → zero tangential motion."""
        hit = CollisionHit(
            object_a=None, object_b=None,
            normal=(1.0, 0.0), depth=5.0,
        )
        sx, sy = hit.slide_velocity(10.0, 0.0)
        assert sx == 0.0
        assert sy == 0.0

    def test_slide_angled(self):
        """Diagonal into surface → only perpendicular component removed."""
        hit = CollisionHit(
            object_a=None, object_b=None,
            normal=(1.0, 0.0), depth=5.0,
        )
        sx, sy = hit.slide_velocity(10.0, 5.0)
        assert sx == 0.0  # x component fully removed
        assert sy == 5.0  # y component preserved (tangential)

    def test_slide_parallel(self):
        """Velocity along the surface → unchanged."""
        hit = CollisionHit(
            object_a=None, object_b=None,
            normal=(0.0, 1.0), depth=5.0,
        )
        sx, sy = hit.slide_velocity(10.0, 0.0)
        assert sx == 10.0
        assert sy == 0.0

    def test_slide_away(self):
        """Velocity pointing away from surface → unchanged."""
        hit = CollisionHit(
            object_a=None, object_b=None,
            normal=(1.0, 0.0), depth=5.0,
        )
        sx, sy = hit.slide_velocity(-10.0, 0.0)
        assert sx == -10.0
        assert sy == 0.0

    def test_slide_zero(self):
        """Zero velocity → zero."""
        hit = CollisionHit(
            object_a=None, object_b=None,
            normal=(1.0, 0.0), depth=5.0,
        )
        sx, sy = hit.slide_velocity(0.0, 0.0)
        assert sx == 0.0
        assert sy == 0.0

    def test_slide_diagonal_normal(self):
        """Normal at 45°, velocity into surface → slide along surface."""
        import math
        n = (1.0 / math.sqrt(2), 1.0 / math.sqrt(2))
        hit = CollisionHit(
            object_a=None, object_b=None,
            normal=n, depth=5.0,
        )
        sx, sy = hit.slide_velocity(1.0, 0.0)
        # Dot = 1/sqrt(2) ≈ 0.707
        # slide = (1, 0) - (0.707, 0.707) * 0.707 = (1 - 0.5, -0.5)
        assert sx == pytest.approx(0.5)
        assert sy == pytest.approx(-0.5)


# ---------------------------------------------------------------------------
# Capsule collision
# ---------------------------------------------------------------------------

def _make_capsule(
    x: float = 0.0,
    y: float = 0.0,
    radius: float = 5.0,
    height: float = 20.0,
    ox: float = 0.0,
    oy: float = 0.0,
    collision_layer: int = 1,
    collision_mask: int = 0xFFFFFFFF,
) -> _DummyObject:
    return _DummyObject(
        x=x, y=y,
        shape=CapsuleShape(radius=radius, height=height, offset=(ox, oy)),
        collision_layer=collision_layer,
        collision_mask=collision_mask,
    )


class TestCapsuleCapsule:
    def test_colliding(self):
        a = _make_capsule(0, 0)
        b = _make_capsule(0, 10)
        hit = check_collision(a, b)
        assert hit is not None
        assert hit.depth > 0

    def test_separated(self):
        a = _make_capsule(0, 0)
        b = _make_capsule(50, 0)
        assert check_collision(a, b) is None


class TestCapsuleCircle:
    def test_colliding(self):
        a = _make_capsule(0, 0, radius=5, height=20)
        b = _make_circle(8, 10, 5)
        hit = check_collision(a, b)
        assert hit is not None
        assert hit.depth > 0

    def test_separated(self):
        a = _make_capsule(0, 0)
        b = _make_circle(100, 0, 5)
        assert check_collision(a, b) is None

    def test_circle_vs_capsule_normal_flipped(self):
        """Circle vs Capsule should produce same collision but flipped normal."""
        cap = _make_capsule(0, 0)
        cir = _make_circle(8, 10, 5)
        hit_cap_cir = check_collision(cap, cir)
        hit_cir_cap = check_collision(cir, cap)
        assert hit_cap_cir is not None
        assert hit_cir_cap is not None
        assert abs(hit_cap_cir.depth - hit_cir_cap.depth) < 0.001
        assert (hit_cap_cir.normal[0] + hit_cir_cap.normal[0]) < 0.001
        assert (hit_cap_cir.normal[1] + hit_cir_cap.normal[1]) < 0.001


class TestCapsuleRect:
    def test_colliding(self):
        a = _make_capsule(0, 0, radius=5, height=20)
        b = _make_rect(2, -5, 10, 30)
        hit = check_collision(a, b)
        assert hit is not None
        assert hit.depth > 0

    def test_separated(self):
        a = _make_capsule(0, 0)
        b = _make_rect(50, 0, 10, 10)
        assert check_collision(a, b) is None

    def test_rect_vs_capsule_normal_flipped(self):
        cap = _make_capsule(0, 0)
        rect = _make_rect(2, -5, 10, 30)
        hit_cap_rect = check_collision(cap, rect)
        hit_rect_cap = check_collision(rect, cap)
        assert hit_cap_rect is not None
        assert hit_rect_cap is not None
        assert abs(hit_cap_rect.depth - hit_rect_cap.depth) < 0.001
        assert (hit_cap_rect.normal[0] + hit_rect_cap.normal[0]) < 0.001
        assert (hit_cap_rect.normal[1] + hit_rect_cap.normal[1]) < 0.001


class TestCapsulePolygon:
    def test_colliding(self):
        a = _make_capsule(0, 0, radius=5, height=20)
        poly = CollisionPolygon(vertices=[(0, 0), (15, 0), (15, 10), (0, 10)])
        b = _DummyObject(x=0, y=5, shape=poly)
        hit = check_collision(a, b)
        assert hit is not None
        assert hit.depth > 0

    def test_separated(self):
        a = _make_capsule(0, 0)
        poly = CollisionPolygon(vertices=[(0, 0), (15, 0), (15, 10), (0, 10)])
        b = _DummyObject(x=100, y=0, shape=poly)
        assert check_collision(a, b) is None

    def test_poly_vs_capsule_normal_flipped(self):
        cap = _make_capsule(0, 0)
        poly = CollisionPolygon(vertices=[(0, 0), (15, 0), (15, 10), (0, 10)])
        poly_obj = _DummyObject(x=0, y=5, shape=poly)
        hit_cap_poly = check_collision(cap, poly_obj)
        hit_poly_cap = check_collision(poly_obj, cap)
        assert hit_cap_poly is not None
        assert hit_poly_cap is not None
        assert abs(hit_cap_poly.depth - hit_poly_cap.depth) < 0.001
        assert (hit_cap_poly.normal[0] + hit_poly_cap.normal[0]) < 0.001
        assert (hit_cap_poly.normal[1] + hit_poly_cap.normal[1]) < 0.001


class TestCapsuleManager:
    def test_manager_capsule_all_vs_all(self):
        mgr = ObjectCollisionManager()
        mgr.add_object(_make_capsule(0, 0))
        mgr.add_object(_make_capsule(0, 10))
        mgr.add_object(_make_capsule(50, 0))  # separated
        hits = mgr.check_all_collisions()
        assert len(hits) == 1  # only first two collide

    def test_manager_capsule_check_object(self):
        mgr = ObjectCollisionManager()
        cap0 = _make_capsule(0, 0)
        cap1 = _make_capsule(0, 10)
        cap2 = _make_capsule(50, 0)
        mgr.add_object(cap0)
        mgr.add_object(cap1)
        mgr.add_object(cap2)
        hits = mgr.check_object(cap0)
        assert len(hits) == 1
        assert hits[0].other(cap0) is cap1
