"""
Tests for Camera.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import math
import random

import pytest

from tilemap_parser.parser.collision import RectangleShape
from tilemap_parser.runtime.camera import Camera
from tilemap_parser.runtime.map_loader import TilemapData


class MockTarget:
    def __init__(self, x=0.0, y=0.0, shape=None):
        self.x = x
        self.y = y
        self.collision_shape = shape or RectangleShape(width=24, height=32)


# ------------------------------------------------------------------
# Centered mode
# ------------------------------------------------------------------


class TestCameraCentered:
    def test_follow_centers_on_target(self):
        """Camera centers on the target's world position."""
        cam = Camera(800, 600, mode="centered")
        target = MockTarget(x=400, y=300)
        cam.follow(target)
        cam.update(0.016)

        # Target center = (400 + 12, 300 + 16) = (412, 316) — shape offset is (0,0)
        # Center: (400+424)/2 = 412, (300+332)/2 = 316
        # Camera position = center - viewport/2
        assert cam.x == pytest.approx(412 - 400)
        assert cam.y == pytest.approx(316 - 300)

    def test_follow_updates_each_frame(self):
        """Camera re-positions when target moves."""
        cam = Camera(800, 600, mode="centered")
        target = MockTarget(x=0, y=0)
        cam.follow(target)
        cam.update(0.016)

        target.x = 800
        target.y = 600
        cam.update(0.016)

        # New target center: (800, 600) + center of shape
        cx = 800 + 12
        cy = 600 + 16
        assert cam.x == pytest.approx(cx - 400)
        assert cam.y == pytest.approx(cy - 300)

    def test_no_target_does_not_move(self):
        """Camera stays at origin when no target is set."""
        cam = Camera(800, 600, mode="centered")
        cam.update(0.016)
        assert cam.x == 0.0
        assert cam.y == 0.0

    def test_offset_reflects_position(self):
        """offset property matches camera position without shake."""
        cam = Camera(800, 600, mode="centered")
        target = MockTarget(x=400, y=300)
        cam.follow(target)
        cam.update(0.016)

        ox, oy = cam.offset
        assert ox == cam.x
        assert oy == cam.y


# ------------------------------------------------------------------
# Deadzone mode
# ------------------------------------------------------------------


class TestCameraDeadzone:
    def test_no_movement_inside_deadzone(self):
        """Camera does not move when target stays within deadzone."""
        cam = Camera(800, 600, mode="deadzone")
        # Default deadzone is 50% viewport → 400x300 centered
        # Camera starts at (0, 0). Target screen center should be within deadzone.
        target = MockTarget(x=400, y=300)
        cam.follow(target)
        cam.update(0.016)

        x_before = cam.x
        y_before = cam.y

        # Small target movement within deadzone
        target.x = 410
        target.y = 310
        cam.update(0.016)

        assert cam.x == x_before
        assert cam.y == y_before

    def test_moves_when_target_exits_deadzone_right(self):
        """Camera follows when target exits deadzone to the right."""
        cam = Camera(800, 600, mode="deadzone")
        target = MockTarget(x=0, y=0)
        cam.follow(target)
        cam.update(0.016)

        # Deadzone right edge = viewport/2 + deadzone_w/2 = 400 + 200 = 600
        # Move target far right so it exits deadzone
        target.x = 2000
        cam.update(0.016)

        # Camera should have moved right (positive x)
        assert cam.x > 0

    def test_moves_when_target_exits_deadzone_bottom(self):
        """Camera follows when target exits deadzone downward."""
        cam = Camera(800, 600, mode="deadzone")
        target = MockTarget(x=0, y=0)
        cam.follow(target)
        cam.update(0.016)

        target.y = 2000
        cam.update(0.016)

        assert cam.y > 0

    def test_stops_when_target_returns_to_deadzone(self):
        """Camera stops once target re-enters the deadzone."""
        cam = Camera(800, 600, mode="deadzone")
        target = MockTarget(x=0, y=0)
        cam.follow(target)
        cam.update(0.016)

        # Push target outside to the right
        target.x = 2000
        cam.update(0.016)
        x_after_first = cam.x

        # Don't move target — camera should stay
        cam.update(0.016)
        assert cam.x == x_after_first


# ------------------------------------------------------------------
# Lerp
# ------------------------------------------------------------------


class TestCameraLerp:
    def test_lerp_smooths_movement(self):
        """With lerp_speed > 0, camera lags behind target."""
        cam = Camera(800, 600, mode="centered")
        cam.lerp_speed = 5.0
        target = MockTarget(x=0, y=0)
        cam.follow(target)
        cam.update(0.016)

        # Move target far away
        target.x = 1000
        target.y = 1000
        cam.update(0.016)

        # Camera has moved some but not all the way
        cx = 1012  # center at x=1000 + 12
        target_x = cx - 400
        assert cam.x != target_x
        assert cam.x > 0

    def test_lerp_zero_is_instant(self):
        """With lerp_speed = 0, camera snaps instantly."""
        cam = Camera(800, 600, mode="centered")
        cam.lerp_speed = 0.0
        target = MockTarget(x=0, y=0)
        cam.follow(target)
        cam.update(0.016)

        target.x = 1000
        target.y = 1000
        cam.update(0.016)

        cx = 1012
        cy = 1016
        assert cam.x == pytest.approx(cx - 400)
        assert cam.y == pytest.approx(cy - 300)

    def test_higher_lerp_follows_faster(self):
        """Higher lerp_speed values converge more quickly."""
        cam_slow = Camera(800, 600, mode="centered")
        cam_fast = Camera(800, 600, mode="centered")
        cam_slow.lerp_speed = 2.0
        cam_fast.lerp_speed = 10.0

        # Start both cameras already converged on the target
        target_slow = MockTarget(x=500, y=300)
        target_fast = MockTarget(x=500, y=300)
        cam_slow.follow(target_slow)
        cam_fast.follow(target_fast)
        cam_slow.update(0.016)
        cam_fast.update(0.016)

        # Teleport target — fast cam should converge faster
        target_slow.x = 1000
        target_fast.x = 1000
        cam_slow.update(0.016)
        cam_fast.update(0.016)

        fast_dist = abs(cam_fast.x - (1012 - 400))
        slow_dist = abs(cam_slow.x - (1012 - 400))
        assert fast_dist < slow_dist


# ------------------------------------------------------------------
# Shake
# ------------------------------------------------------------------


class TestCameraShake:
    def test_shake_creates_offset(self):
        """shake() produces nonzero shake offset."""
        cam = Camera(800, 600, mode="centered")
        cam.shake(1.0, 10.0)

        cam.update(0.016)
        ox, oy = cam.offset

        # Shake should move offset away from raw camera position
        assert abs(ox - cam.x) > 0 or abs(oy - cam.y) > 0

    def test_shake_decays(self):
        """Shake offset returns to zero after timer expires."""
        cam = Camera(800, 600, mode="centered")
        cam.shake(0.03, 10.0)

        # Advance past the shake duration
        cam.update(0.02)
        cam.update(0.02)

        ox, oy = cam.offset
        assert ox == cam.x
        assert oy == cam.y

    def test_shake_does_not_affect_camera_position(self):
        """Camera x, y stay the same during shake; only offset changes."""
        cam = Camera(800, 600, mode="centered")
        target = MockTarget(x=400, y=300)
        cam.follow(target)
        cam.update(0.016)

        x_before = cam.x
        y_before = cam.y

        cam.shake(1.0, 20.0)
        cam.update(0.016)

        assert cam.x == x_before
        assert cam.y == y_before


# ------------------------------------------------------------------
# Bounds
# ------------------------------------------------------------------


class TestCameraBounds:
    def test_clamps_to_left_top(self):
        """Camera does not show area outside world bounds (top-left)."""
        cam = Camera(800, 600, mode="centered")
        cam.bounds = (0, 0, 1600, 1200)
        target = MockTarget(x=0, y=0)
        cam.follow(target)
        cam.update(0.016)

        assert cam.x == 0.0
        assert cam.y == 0.0

    def test_clamps_to_right_bottom(self):
        """Camera does not show area outside world bounds (bottom-right)."""
        cam = Camera(800, 600, mode="centered")
        cam.bounds = (0, 0, 1600, 1200)
        target = MockTarget(x=1600, y=1200)
        cam.follow(target)
        cam.update(0.016)

        # Camera right edge should not exceed world right
        assert cam.x == pytest.approx(1600 - 800)
        assert cam.y == pytest.approx(1200 - 600)

    def test_within_bounds_free_movement(self):
        """Camera moves freely when target is inside bounds."""
        cam = Camera(800, 600, mode="centered")
        cam.bounds = (0, 0, 1600, 1200)
        target = MockTarget(x=400, y=300)
        cam.follow(target)
        cam.update(0.016)

        assert cam.x == pytest.approx(412 - 400)
        assert cam.y == pytest.approx(316 - 300)


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------


class TestCameraEdgeCases:
    def test_invalid_mode_raises(self):
        """Unknown mode string raises ValueError."""
        with pytest.raises(ValueError):
            Camera(800, 600, mode="invalid")

    def test_offset_tuple(self):
        """offset returns a (float, float) tuple."""
        cam = Camera(800, 600, mode="centered")
        assert isinstance(cam.offset, tuple)
        assert len(cam.offset) == 2

    def test_default_deadzone_size(self):
        """Deadzone defaults to 50% viewport when mode='deadzone'."""
        cam = Camera(800, 600, mode="deadzone")
        assert cam.deadzone is not None
        assert cam.deadzone.width == 400
        assert cam.deadzone.height == 300

    def test_no_deadzone_in_centered_mode(self):
        """Centered mode has no deadzone rect."""
        cam = Camera(800, 600, mode="centered")
        assert cam.deadzone is None


# ------------------------------------------------------------------
# Bounds helpers
# ------------------------------------------------------------------


def _write_map(data_dir: Path, name: str = "test_map.json"):
    payload = {
        "meta": {
            "tile_size": "32;32",
            "map_size": "10;8",
            "initial_map_size": "10;8",
            "render_scale": 1.0,
            "scroll": "0;0",
            "version": "1.1",
        },
        "resources": {"tilesets": []},
        "project_state": {"rules": [], "groups": []},
        "data": {"layers": []},
    }
    mp = data_dir / name
    with open(mp, "w") as f:
        json.dump(payload, f, indent=2)
    return mp


class TestCameraSetBounds:
    def test_set_bounds_returns_self(self):
        cam = Camera(800, 600, mode="centered")
        assert cam.set_bounds(0, 0, 1600, 1200) is cam
        assert cam.bounds == (0, 0, 1600, 1200)

    def test_set_bounds_from_map(self, tmp_path):
        mp = _write_map(tmp_path)
        td = TilemapData.load(mp)
        cam = Camera(800, 600, mode="centered")
        assert cam.set_bounds_from_map(td) is cam
        assert cam.bounds == (0.0, 0.0, 320.0, 256.0)

    def test_set_bounds_from_map_with_offset(self, tmp_path):
        mp = _write_map(tmp_path)
        td = TilemapData.load(mp, offset_tiles=(0, 5))
        cam = Camera(800, 600, mode="centered")
        cam.set_bounds_from_map(td)
        assert cam.bounds == (0.0, 0.0, 320.0, 416.0)
        target = MockTarget(x=160, y=400)
        cam.follow(target)
        cam.update(0.016)
        assert cam.x == pytest.approx(0 - (800 - 320) / 2)
        assert cam.y == pytest.approx(0 - (600 - 416) / 2)

    def test_small_map_centers(self):
        cam = Camera(800, 600, mode="centered")
        cam.set_bounds(0, 0, 320, 256)
        target = MockTarget(x=160, y=128)
        cam.follow(target)
        cam.update(0.016)
        assert cam.x == pytest.approx(0 - (800 - 320) / 2)
        assert cam.y == pytest.approx(0 - (600 - 256) / 2)
