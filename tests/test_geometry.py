"""
Tests for tilemap_parser.geometry.

Covers:
- CollisionInfo dataclass
- aabb_overlap (separated, touching, overlapping)
- get_shape_aabb (RectangleShape, CircleShape, CollisionPolygon)
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.geometry import (
    CollisionInfo,
    aabb_overlap,
    circle_vs_circle,
    get_shape_aabb,
    polygon_vs_circle,
    polygon_vs_polygon,
    polygon_vs_rect,
    rect_vs_circle,
    rect_vs_rect,
)
from tilemap_parser.collision import RectangleShape, CircleShape, CollisionPolygon


# ---------------------------------------------------------------------------
# CollisionInfo
# ---------------------------------------------------------------------------

class TestCollisionInfo:
    def test_fields(self):
        info = CollisionInfo(normal=(1.0, 0.0), depth=5.0)
        assert info.normal == (1.0, 0.0)
        assert info.depth == 5.0

    def test_slots(self):
        """CollisionInfo uses __slots__ — no __dict__."""
        info = CollisionInfo(normal=(0.0, 1.0), depth=3.0)
        assert not hasattr(info, "__dict__")


# ---------------------------------------------------------------------------
# aabb_overlap
# ---------------------------------------------------------------------------

class TestAabbOverlap:
    def test_separated_horizontal(self):
        b1 = (0.0, 0.0, 10.0, 10.0)
        b2 = (20.0, 0.0, 30.0, 10.0)
        assert aabb_overlap(b1, b2) is False

    def test_separated_vertical(self):
        b1 = (0.0, 0.0, 10.0, 10.0)
        b2 = (0.0, 20.0, 10.0, 30.0)
        assert aabb_overlap(b1, b2) is False

    def test_separated_diagonal(self):
        b1 = (0.0, 0.0, 10.0, 10.0)
        b2 = (15.0, 15.0, 25.0, 25.0)
        assert aabb_overlap(b1, b2) is False

    def test_touching_right_edge(self):
        """Edge-touching counts as collision (per spec)."""
        b1 = (0.0, 0.0, 10.0, 10.0)
        b2 = (10.0, 0.0, 20.0, 10.0)
        assert aabb_overlap(b1, b2) is True

    def test_touching_left_edge(self):
        b1 = (10.0, 0.0, 20.0, 10.0)
        b2 = (0.0, 0.0, 10.0, 10.0)
        assert aabb_overlap(b1, b2) is True

    def test_touching_bottom_edge(self):
        b1 = (0.0, 0.0, 10.0, 10.0)
        b2 = (0.0, 10.0, 10.0, 20.0)
        assert aabb_overlap(b1, b2) is True

    def test_touching_top_edge(self):
        b1 = (0.0, 10.0, 10.0, 20.0)
        b2 = (0.0, 0.0, 10.0, 10.0)
        assert aabb_overlap(b1, b2) is True

    def test_touching_corner(self):
        """Corner-touching (single point) counts as collision."""
        b1 = (0.0, 0.0, 10.0, 10.0)
        b2 = (10.0, 10.0, 20.0, 20.0)
        assert aabb_overlap(b1, b2) is True

    def test_overlapping_partial(self):
        b1 = (0.0, 0.0, 20.0, 20.0)
        b2 = (10.0, 10.0, 30.0, 30.0)
        assert aabb_overlap(b1, b2) is True

    def test_overlapping_full_containment(self):
        b1 = (0.0, 0.0, 30.0, 30.0)
        b2 = (5.0, 5.0, 15.0, 15.0)
        assert aabb_overlap(b1, b2) is True

    def test_identical_bounds(self):
        b = (0.0, 0.0, 10.0, 10.0)
        assert aabb_overlap(b, b) is True

    def test_negative_coordinates(self):
        b1 = (-20.0, -20.0, -10.0, -10.0)
        b2 = (-15.0, -15.0, -5.0, -5.0)
        assert aabb_overlap(b1, b2) is True

    def test_negative_coordinates_separated(self):
        b1 = (-20.0, -20.0, -10.0, -10.0)
        b2 = (5.0, 5.0, 15.0, 15.0)
        assert aabb_overlap(b1, b2) is False


# ---------------------------------------------------------------------------
# get_shape_aabb
# ---------------------------------------------------------------------------

class TestGetShapeAabbRectangle:
    def test_zero_offset(self):
        shape = RectangleShape(width=32.0, height=32.0, offset=(0.0, 0.0))
        result = get_shape_aabb(100.0, 50.0, shape)
        assert result == (100.0, 50.0, 132.0, 82.0)

    def test_positive_offset(self):
        shape = RectangleShape(width=20.0, height=10.0, offset=(5.0, 3.0))
        result = get_shape_aabb(10.0, 10.0, shape)
        assert result == (15.0, 13.0, 35.0, 23.0)

    def test_negative_offset(self):
        shape = RectangleShape(width=16.0, height=16.0, offset=(-8.0, -8.0))
        result = get_shape_aabb(0.0, 0.0, shape)
        assert result == (-8.0, -8.0, 8.0, 8.0)

    def test_at_origin(self):
        shape = RectangleShape(width=10.0, height=20.0, offset=(0.0, 0.0))
        result = get_shape_aabb(0.0, 0.0, shape)
        assert result == (0.0, 0.0, 10.0, 20.0)


class TestGetShapeAabbCircle:
    def test_zero_offset(self):
        shape = CircleShape(radius=10.0, offset=(0.0, 0.0))
        result = get_shape_aabb(100.0, 50.0, shape)
        assert result == (90.0, 40.0, 110.0, 60.0)

    def test_positive_offset(self):
        shape = CircleShape(radius=5.0, offset=(3.0, 4.0))
        result = get_shape_aabb(0.0, 0.0, shape)
        assert result == (-2.0, -1.0, 8.0, 9.0)

    def test_negative_offset(self):
        shape = CircleShape(radius=8.0, offset=(-2.0, -3.0))
        result = get_shape_aabb(10.0, 10.0, shape)
        assert result == (0.0, -1.0, 16.0, 15.0)

    def test_at_origin(self):
        shape = CircleShape(radius=16.0, offset=(0.0, 0.0))
        result = get_shape_aabb(0.0, 0.0, shape)
        assert result == (-16.0, -16.0, 16.0, 16.0)


class TestGetShapeAabbPolygon:
    def test_unit_square_at_origin(self):
        shape = CollisionPolygon(vertices=[(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)])
        result = get_shape_aabb(0.0, 0.0, shape)
        assert result == (0.0, 0.0, 32.0, 32.0)

    def test_offset_position(self):
        shape = CollisionPolygon(vertices=[(0.0, 0.0), (10.0, 0.0), (10.0, 20.0), (0.0, 20.0)])
        result = get_shape_aabb(100.0, 50.0, shape)
        assert result == (100.0, 50.0, 110.0, 70.0)

    def test_negative_vertices(self):
        shape = CollisionPolygon(vertices=[(-5.0, -3.0), (5.0, -3.0), (5.0, 3.0), (-5.0, 3.0)])
        result = get_shape_aabb(0.0, 0.0, shape)
        assert result == (-5.0, -3.0, 5.0, 3.0)

    def test_triangle(self):
        shape = CollisionPolygon(vertices=[(0.0, 0.0), (10.0, 20.0), (20.0, 0.0)])
        result = get_shape_aabb(5.0, 5.0, shape)
        assert result == (5.0, 5.0, 25.0, 25.0)

    def test_polygon_with_offset_on_shape(self):
        """Shape has its own offset field — this is NOT applied by get_shape_aabb
        (CollisionPolygon.offset does not exist in the current dataclass; vertices
        are already in local space).  The world offset comes from x, y params."""
        shape = CollisionPolygon(vertices=[(0.0, 0.0), (10.0, 10.0)])
        result = get_shape_aabb(100.0, 100.0, shape)
        assert result == (100.0, 100.0, 110.0, 110.0)

    def test_single_vertex_degenerate(self):
        """Edge case: polygon with 1 vertex — still returns a valid AABB."""
        shape = CollisionPolygon(vertices=[(5.0, 7.0)])
        result = get_shape_aabb(0.0, 0.0, shape)
        assert result == (5.0, 7.0, 5.0, 7.0)

    def test_two_vertices_line(self):
        shape = CollisionPolygon(vertices=[(0.0, 0.0), (10.0, 20.0)])
        result = get_shape_aabb(1.0, 2.0, shape)
        assert result == (1.0, 2.0, 11.0, 22.0)


class TestGetShapeAabbUnsupported:
    def test_raises_on_unknown_shape(self):
        class FakeShape:
            pass
        with pytest.raises(TypeError, match="Unsupported shape type"):
            get_shape_aabb(0.0, 0.0, FakeShape())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# circle_vs_circle
# ---------------------------------------------------------------------------

class TestCircleVsCircle:
    def test_separated(self):
        c1 = (0.0, 0.0)
        c2 = (30.0, 0.0)
        result = circle_vs_circle(c1, 10.0, c2, 10.0)
        assert result is None

    def test_touching(self):
        """Touching circles count as collision — depth should be 0."""
        c1 = (0.0, 0.0)
        c2 = (20.0, 0.0)
        result = circle_vs_circle(c1, 10.0, c2, 10.0)
        assert result is not None
        assert result.depth == pytest.approx(0.0, abs=1e-9)
        assert result.normal == (1.0, 0.0)

    def test_overlapping(self):
        c1 = (0.0, 0.0)
        c2 = (15.0, 0.0)
        result = circle_vs_circle(c1, 10.0, c2, 10.0)
        assert result is not None
        assert result.depth == pytest.approx(5.0)
        assert result.normal == (1.0, 0.0)

    def test_coincident_centers(self):
        """Same center — normal defaults to (1, 0), depth = sum of radii."""
        c = (5.0, 5.0)
        result = circle_vs_circle(c, 10.0, c, 10.0)
        assert result is not None
        assert result.normal == (1.0, 0.0)
        assert result.depth == pytest.approx(20.0)

    def test_diagonal_overlap(self):
        c1 = (0.0, 0.0)
        c2 = (10.0, 10.0)
        result = circle_vs_circle(c1, 10.0, c2, 10.0)
        assert result is not None
        expected_dist = (10.0**2 + 10.0**2) ** 0.5
        expected_depth = 20.0 - expected_dist
        assert result.depth == pytest.approx(expected_depth)
        expected_normal = (10.0 / expected_dist, 10.0 / expected_dist)
        assert result.normal[0] == pytest.approx(expected_normal[0])
        assert result.normal[1] == pytest.approx(expected_normal[1])

    def test_different_radii(self):
        c1 = (0.0, 0.0)
        c2 = (8.0, 0.0)
        result = circle_vs_circle(c1, 5.0, c2, 3.0)
        assert result is not None
        assert result.depth == pytest.approx(0.0)  # touching: 5+3=8, dist=8


# ---------------------------------------------------------------------------
# rect_vs_rect
# ---------------------------------------------------------------------------

class TestRectVsRect:
    def test_separated(self):
        r1 = (0.0, 0.0, 10.0, 10.0)
        r2 = (20.0, 0.0, 30.0, 10.0)
        assert rect_vs_rect(r1, r2) is None

    def test_touching(self):
        """Touching rects count as collision — depth should be 0."""
        r1 = (0.0, 0.0, 10.0, 10.0)
        r2 = (10.0, 0.0, 20.0, 10.0)
        result = rect_vs_rect(r1, r2)
        assert result is not None
        assert result.depth == pytest.approx(0.0, abs=1e-9)
        assert result.normal == (1.0, 0.0)

    def test_overlapping_x_axis(self):
        """Overlap is smaller on X axis — normal should be on X."""
        r1 = (0.0, 0.0, 20.0, 20.0)
        r2 = (15.0, 0.0, 35.0, 20.0)
        result = rect_vs_rect(r1, r2)
        assert result is not None
        assert result.depth == pytest.approx(5.0)
        assert result.normal == (1.0, 0.0)

    def test_overlapping_y_axis(self):
        """Overlap is smaller on Y axis — normal should be on Y."""
        r1 = (0.0, 0.0, 20.0, 20.0)
        r2 = (0.0, 15.0, 20.0, 35.0)
        result = rect_vs_rect(r1, r2)
        assert result is not None
        assert result.depth == pytest.approx(5.0)
        assert result.normal == (0.0, 1.0)

    def test_overlap_equal_axes(self):
        """When overlap_x == overlap_y, Y axis is chosen (strict < in if, else branch)."""
        r1 = (0.0, 0.0, 10.0, 10.0)
        r2 = (5.0, 5.0, 15.0, 15.0)
        result = rect_vs_rect(r1, r2)
        assert result is not None
        assert result.depth == pytest.approx(5.0)
        assert result.normal == (0.0, 1.0)

    def test_r2_left_of_r1(self):
        r1 = (10.0, 0.0, 20.0, 10.0)
        r2 = (0.0, 0.0, 15.0, 10.0)
        result = rect_vs_rect(r1, r2)
        assert result is not None
        assert result.normal == (-1.0, 0.0)

    def test_r2_above_r1(self):
        r1 = (0.0, 10.0, 10.0, 20.0)
        r2 = (0.0, 0.0, 10.0, 15.0)
        result = rect_vs_rect(r1, r2)
        assert result is not None
        assert result.normal == (0.0, -1.0)


# ---------------------------------------------------------------------------
# rect_vs_circle
# ---------------------------------------------------------------------------

class TestRectVsCircle:
    def test_separated(self):
        rect = (0.0, 0.0, 10.0, 10.0)
        center = (30.0, 5.0)
        assert rect_vs_circle(rect, center, 5.0) is None

    def test_touching_edge(self):
        """Circle touching rect edge — depth should be 0."""
        rect = (0.0, 0.0, 10.0, 10.0)
        center = (15.0, 5.0)
        result = rect_vs_circle(rect, center, 5.0)
        assert result is not None
        assert result.depth == pytest.approx(0.0, abs=1e-9)
        assert result.normal == (1.0, 0.0)

    def test_touching_corner(self):
        """Circle touching rect corner — slight overlap to avoid FP edge case."""
        import math
        rect = (0.0, 0.0, 10.0, 10.0)
        offset = 5.0 / math.sqrt(2) - 0.001
        center = (10.0 + offset, 10.0 + offset)
        result = rect_vs_circle(rect, center, 5.0)
        assert result is not None
        # Depth = 0.001 * sqrt(2) because offset reduction is along diagonal
        expected_depth = 0.001 * math.sqrt(2)
        assert result.depth == pytest.approx(expected_depth, abs=1e-9)
        expected_normal = (1.0 / math.sqrt(2), 1.0 / math.sqrt(2))
        assert result.normal[0] == pytest.approx(expected_normal[0])
        assert result.normal[1] == pytest.approx(expected_normal[1])

    def test_overlapping_side(self):
        rect = (0.0, 0.0, 10.0, 10.0)
        center = (12.0, 5.0)
        result = rect_vs_circle(rect, center, 5.0)
        assert result is not None
        assert result.depth == pytest.approx(3.0)
        assert result.normal == (1.0, 0.0)

    def test_overlapping_corner(self):
        rect = (0.0, 0.0, 10.0, 10.0)
        center = (13.0, 13.0)
        result = rect_vs_circle(rect, center, 5.0)
        assert result is not None
        expected_dist = (3.0**2 + 3.0**2) ** 0.5
        expected_depth = 5.0 - expected_dist
        assert result.depth == pytest.approx(expected_depth)
        expected_normal = (3.0 / expected_dist, 3.0 / expected_dist)
        assert result.normal[0] == pytest.approx(expected_normal[0])
        assert result.normal[1] == pytest.approx(expected_normal[1])

    def test_circle_inside_rect(self):
        """Circle center inside rect — minimal translation distance."""
        rect = (0.0, 0.0, 20.0, 20.0)
        center = (5.0, 10.0)
        result = rect_vs_circle(rect, center, 8.0)
        assert result is not None
        # Closest edge is left (dist_left = 5.0), so normal = (-1, 0)
        # depth = radius - dist_left = 8 - 5 = 3
        assert result.normal == (-1.0, 0.0)
        assert result.depth == pytest.approx(3.0)

    def test_circle_inside_rect_closest_top(self):
        rect = (0.0, 0.0, 20.0, 20.0)
        center = (10.0, 3.0)
        result = rect_vs_circle(rect, center, 8.0)
        assert result is not None
        # Closest edge is top (dist_top = 3.0)
        assert result.normal == (0.0, -1.0)
        assert result.depth == pytest.approx(5.0)

    def test_circle_inside_rect_closest_bottom(self):
        rect = (0.0, 0.0, 20.0, 20.0)
        center = (10.0, 17.0)
        result = rect_vs_circle(rect, center, 8.0)
        assert result is not None
        # Closest edge is bottom (dist_bottom = 3.0)
        assert result.normal == (0.0, 1.0)
        assert result.depth == pytest.approx(5.0)

    def test_circle_center_on_edge(self):
        """Circle center exactly on rect edge."""
        rect = (0.0, 0.0, 10.0, 10.0)
        center = (10.0, 5.0)
        result = rect_vs_circle(rect, center, 5.0)
        assert result is not None
        assert result.depth == pytest.approx(5.0)
        assert result.normal == (1.0, 0.0)

    def test_circle_center_at_corner(self):
        """Circle center exactly on rect corner."""
        rect = (0.0, 0.0, 10.0, 10.0)
        center = (10.0, 10.0)
        result = rect_vs_circle(rect, center, 5.0)
        assert result is not None
        assert result.depth == pytest.approx(5.0)
        assert result.normal == (1.0, 0.0)


# ---------------------------------------------------------------------------
# polygon_vs_polygon (SAT)
# ---------------------------------------------------------------------------

class TestPolygonVsPolygon:
    def test_separated(self):
        p1 = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        p2 = [(20.0, 0.0), (30.0, 0.0), (30.0, 10.0), (20.0, 10.0)]
        assert polygon_vs_polygon(p1, p2) is None

    def test_touching(self):
        """Edge-touching counts as collision — depth should be 0."""
        p1 = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        p2 = [(10.0, 0.0), (20.0, 0.0), (20.0, 10.0), (10.0, 10.0)]
        result = polygon_vs_polygon(p1, p2)
        assert result is not None
        assert result.depth == pytest.approx(0.0, abs=1e-9)

    def test_overlapping(self):
        p1 = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        p2 = [(5.0, 0.0), (15.0, 0.0), (15.0, 10.0), (5.0, 10.0)]
        result = polygon_vs_polygon(p1, p2)
        assert result is not None
        assert result.depth == pytest.approx(5.0)

    def test_full_containment(self):
        p1 = [(0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)]
        p2 = [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0), (5.0, 15.0)]
        result = polygon_vs_polygon(p1, p2)
        assert result is not None
        assert result.depth > 0

    def test_diamond_vs_square(self):
        """Diamond (rotated square) vs axis-aligned square."""
        diamond = [(5.0, 0.0), (10.0, 5.0), (5.0, 10.0), (0.0, 5.0)]
        square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        result = polygon_vs_polygon(diamond, square)
        assert result is not None
        assert result.depth > 0

    def test_triangle_vs_square(self):
        tri = [(0.0, 0.0), (10.0, 0.0), (5.0, 10.0)]
        sq = [(3.0, 5.0), (8.0, 5.0), (8.0, 12.0), (3.0, 12.0)]
        result = polygon_vs_polygon(tri, sq)
        assert result is not None
        assert result.depth > 0

    def test_normal_points_from_p1_to_p2(self):
        """Verify normal direction: p1 is left, p2 is right → normal should be (+, 0)."""
        p1 = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        p2 = [(5.0, 0.0), (15.0, 0.0), (15.0, 10.0), (5.0, 10.0)]
        result = polygon_vs_polygon(p1, p2)
        assert result is not None
        # p2 center is to the right of p1 center → normal X should be positive
        assert result.normal[0] > 0


# ---------------------------------------------------------------------------
# polygon_vs_circle
# ---------------------------------------------------------------------------

class TestPolygonVsCircle:
    def test_separated(self):
        poly = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        center = (30.0, 5.0)
        assert polygon_vs_circle(poly, center, 5.0) is None

    def test_touching_edge(self):
        poly = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        center = (15.0, 5.0)
        result = polygon_vs_circle(poly, center, 5.0)
        assert result is not None
        assert result.depth == pytest.approx(0.0, abs=1e-9)

    def test_overlapping(self):
        poly = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        center = (12.0, 5.0)
        result = polygon_vs_circle(poly, center, 5.0)
        assert result is not None
        assert result.depth == pytest.approx(3.0)
        assert result.normal[0] > 0  # pointing toward circle (right)

    def test_circle_center_inside(self):
        poly = [(0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)]
        center = (10.0, 10.0)
        result = polygon_vs_circle(poly, center, 5.0)
        assert result is not None
        # depth = radius + distance_to_closest_edge = 5 + 10 = 15
        assert result.depth == pytest.approx(15.0)

    def test_circle_near_vertex(self):
        """Circle near a polygon vertex (corner)."""
        poly = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        center = (13.0, 13.0)
        result = polygon_vs_circle(poly, center, 5.0)
        assert result is not None
        # Distance from (13,13) to corner (10,10) = sqrt(18) ≈ 4.24 < 5
        expected_dist = (3.0**2 + 3.0**2) ** 0.5
        assert result.depth == pytest.approx(5.0 - expected_dist)


# ---------------------------------------------------------------------------
# polygon_vs_rect
# ---------------------------------------------------------------------------

class TestPolygonVsRect:
    def test_separated(self):
        poly = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        rect = (20.0, 0.0, 30.0, 10.0)
        assert polygon_vs_rect(poly, rect) is None

    def test_touching(self):
        poly = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        rect = (10.0, 0.0, 20.0, 10.0)
        result = polygon_vs_rect(poly, rect)
        assert result is not None
        assert result.depth == pytest.approx(0.0, abs=1e-9)

    def test_overlapping(self):
        poly = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        rect = (5.0, 0.0, 15.0, 10.0)
        result = polygon_vs_rect(poly, rect)
        assert result is not None
        assert result.depth == pytest.approx(5.0)

    def test_polygon_inside_rect(self):
        poly = [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0), (5.0, 15.0)]
        rect = (0.0, 0.0, 20.0, 20.0)
        result = polygon_vs_rect(poly, rect)
        assert result is not None
        assert result.depth > 0

    def test_triangle_vs_rect(self):
        tri = [(0.0, 0.0), (10.0, 0.0), (5.0, 10.0)]
        rect = (3.0, 5.0, 8.0, 12.0)
        result = polygon_vs_rect(tri, rect)
        assert result is not None
        assert result.depth > 0
