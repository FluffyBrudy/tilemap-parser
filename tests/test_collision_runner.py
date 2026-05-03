"""
Tests for tilemap_parser.collision_runner — focusing on correctness of
geometric utilities, especially the xinters bug fix in point_in_polygon.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.collision_runner import point_in_polygon, CollisionRunner, MovementMode
from tilemap_parser.collision import CollisionCache, RectangleShape


# ===========================================================================
# point_in_polygon
# ===========================================================================

# Simple axis-aligned square: (0,0) -> (10,0) -> (10,10) -> (0,10)
SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]

# Triangle with a horizontal bottom edge — this is what triggered the xinters bug
# vertices: (0,0), (10,0), (5,10)
TRIANGLE_HORIZ_BASE = [(0.0, 0.0), (10.0, 0.0), (5.0, 10.0)]


class TestPointInPolygon:
    def test_inside_square(self):
        assert point_in_polygon((5.0, 5.0), SQUARE) is True

    def test_outside_square(self):
        assert point_in_polygon((15.0, 5.0), SQUARE) is False
        assert point_in_polygon((-1.0, 5.0), SQUARE) is False
        assert point_in_polygon((5.0, -1.0), SQUARE) is False
        assert point_in_polygon((5.0, 15.0), SQUARE) is False

    def test_inside_triangle(self):
        assert point_in_polygon((5.0, 5.0), TRIANGLE_HORIZ_BASE) is True

    def test_outside_triangle(self):
        assert point_in_polygon((0.5, 9.0), TRIANGLE_HORIZ_BASE) is False
        assert point_in_polygon((9.5, 9.0), TRIANGLE_HORIZ_BASE) is False

    # --- xinters bug regression tests ---
    # A polygon with a horizontal edge at y=0. When the ray is cast from a point
    # whose y equals the horizontal edge's y, the old code would read an
    # uninitialised / stale xinters and flip `inside` incorrectly.

    def test_horizontal_edge_does_not_use_stale_xinters(self):
        # Point well inside — must not be flipped by the horizontal base edge
        assert point_in_polygon((5.0, 5.0), TRIANGLE_HORIZ_BASE) is True

    def test_point_below_horizontal_edge(self):
        # y=-1 is outside regardless
        assert point_in_polygon((5.0, -1.0), TRIANGLE_HORIZ_BASE) is False

    def test_polygon_with_multiple_horizontal_edges(self):
        # Rectangle has horizontal top and bottom edges
        rect = [(0.0, 0.0), (20.0, 0.0), (20.0, 10.0), (0.0, 10.0)]
        assert point_in_polygon((10.0, 5.0), rect) is True
        assert point_in_polygon((10.0, 15.0), rect) is False
        assert point_in_polygon((-1.0, 5.0), rect) is False

    def test_first_iteration_no_unbound_xinters(self):
        # Polygon whose very first edge is horizontal — this is the case that
        # caused an UnboundLocalError before the fix (xinters never assigned
        # yet when the stale-read branch was reached on i=1).
        horiz_first = [(0.0, 5.0), (10.0, 5.0), (10.0, 0.0), (0.0, 0.0)]
        # Point inside
        assert point_in_polygon((5.0, 2.0), horiz_first) is True
        # Point outside
        assert point_in_polygon((5.0, 8.0), horiz_first) is False


# ===========================================================================
# CollisionRunner construction
# ===========================================================================

class TestCollisionRunnerConstruction:
    def test_from_game_type_platformer(self):
        cache = CollisionCache()
        runner = CollisionRunner.from_game_type("platformer", cache, (32, 32))
        assert runner.mode == MovementMode.PLATFORMER
        assert runner.gravity > 0

    def test_from_game_type_topdown(self):
        cache = CollisionCache()
        runner = CollisionRunner.from_game_type("topdown", cache, (32, 32))
        assert runner.mode == MovementMode.SLIDE
        assert runner.gravity == 0.0

    def test_from_game_type_rpg(self):
        cache = CollisionCache()
        runner = CollisionRunner.from_game_type("rpg", cache, (32, 32))
        assert runner.mode == MovementMode.RPG
        assert runner.gravity == 0.0

    def test_unknown_game_type_raises(self):
        cache = CollisionCache()
        with pytest.raises(ValueError):
            CollisionRunner.from_game_type("unknown", cache, (32, 32))

    def test_platformer_zero_gravity_raises(self):
        cache = CollisionCache()
        runner = CollisionRunner.from_game_type("platformer", cache, (32, 32))
        runner.gravity = 0.0
        with pytest.raises(ValueError):
            runner.validate_config()
