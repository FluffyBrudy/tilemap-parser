"""
Camera with centered or deadzone follow, lerp smoothing, screen-shake, and bounds clamping.

Usage::

    camera = Camera(800, 600, mode="centered")
    camera.follow(player)

    # each frame:
    camera.update(dt)

    # render with camera.offset:
    tile_renderer.render(screen, camera.offset)
    player.render(screen, camera.offset)
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Optional, Tuple

import pygame

from ..utils.geometry import get_shape_aabb

if TYPE_CHECKING:
    from .map_loader import TilemapData


class Camera:
    __slots__ = (
        "x",
        "y",
        "viewport_w",
        "viewport_h",
        "mode",
        "target",
        "lerp_speed",
        "deadzone",
        "bounds",
        "_shake_timer",
        "_shake_intensity",
        "_shake_ox",
        "_shake_oy",
    )

    def __init__(
        self,
        viewport_width: int,
        viewport_height: int,
        mode: str = "centered",
    ):
        if mode not in ("centered", "deadzone"):
            raise ValueError(f"Camera mode must be 'centered' or 'deadzone', got {mode!r}")

        self.x = 0.0
        self.y = 0.0
        self.viewport_w = viewport_width
        self.viewport_h = viewport_height
        self.mode = mode
        self.target = None
        self.lerp_speed = 0.0
        self.bounds: tuple[float, float, float, float] | None = None

        if mode == "deadzone":
            dw = viewport_width * 0.5
            dh = viewport_height * 0.5
            self.deadzone = pygame.Rect(
                (viewport_width - dw) / 2,
                (viewport_height - dh) / 2,
                dw,
                dh,
            )
        else:
            self.deadzone = None

        self._shake_timer = 0.0
        self._shake_intensity = 0.0
        self._shake_ox = 0.0
        self._shake_oy = 0.0

    def follow(self, target) -> None:
        """Set the entity the camera should follow.

        *target* must have ``x``, ``y``, and ``collision_shape`` attributes
        (any sprite managed by the collision runner satisfies this).
        """
        self.target = target

    def set_bounds(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
    ) -> Camera:
        self.bounds = (min_x, min_y, max_x, max_y)
        return self

    def set_bounds_from_map(self, tilemap_data: TilemapData) -> Camera:
        tw, th = tilemap_data.tile_size
        mw, mh = tilemap_data.map_size
        rs = tilemap_data.render_scale
        return self.set_bounds(0.0, 0.0, float(mw * int(tw * rs)), float(mh * int(th * rs)))

    def shake(self, duration: float, intensity: float) -> None:
        """Trigger a screen-shake effect.

        Args:
            duration: Seconds the shake lasts.
            intensity: Maximum pixel offset applied each frame.
        """
        self._shake_timer = duration
        self._shake_intensity = intensity

    def update(self, dt: float) -> None:
        """Advance the camera by *dt* seconds.

        Computes the new position based on the follow mode, applies lerp,
        clamps to bounds, and updates the screen-shake.
        """
        if self.target is not None:
            l, t, r, b = get_shape_aabb(
                self.target.x,
                self.target.y,
                self.target.collision_shape,
            )
            cx = (l + r) * 0.5
            cy = (t + b) * 0.5

            if self.mode == "centered":
                self._move_toward(
                    cx - self.viewport_w / 2,
                    cy - self.viewport_h / 2,
                    dt,
                )
            elif self.mode == "deadzone" and self.deadzone is not None:
                self._follow_deadzone(cx, cy, dt)

        # Bounds clamp
        if self.bounds is not None:
            min_x, min_y, max_x, max_y = self.bounds
            if max_x - min_x < self.viewport_w:
                self.x = min_x - (self.viewport_w - (max_x - min_x)) / 2
            else:
                self.x = max(min_x, min(self.x, max_x - self.viewport_w))
            if max_y - min_y < self.viewport_h:
                self.y = min_y - (self.viewport_h - (max_y - min_y)) / 2
            else:
                self.y = max(min_y, min(self.y, max_y - self.viewport_h))

        # Shake
        if self._shake_timer > 0:
            self._shake_timer -= dt
            i = self._shake_intensity
            self._shake_ox = random.uniform(-i, i)
            self._shake_oy = random.uniform(-i, i)
            if self._shake_timer <= 0:
                self._shake_timer = 0.0
                self._shake_ox = 0.0
                self._shake_oy = 0.0

    @property
    def offset(self) -> Tuple[float, float]:
        """Camera offset including active screen-shake.

        Pass this directly to render calls::

            tile_renderer.render(screen, camera.offset)
            player.render(screen, camera.offset)
        """
        return (self.x + self._shake_ox, self.y + self._shake_oy)

    def _move_toward(self, target_x: float, target_y: float, dt: float) -> None:
        if self.lerp_speed > 0:
            t = 1.0 - math.exp(-self.lerp_speed * dt)
            self.x += (target_x - self.x) * t
            self.y += (target_y - self.y) * t
        else:
            self.x = target_x
            self.y = target_y

    def _follow_deadzone(self, cx: float, cy: float, dt: float) -> None:
        # Target position in screen space
        sx = cx - self.x
        sy = cy - self.y
        dz = self.deadzone
        dx = dy = 0.0

        if sx < dz.left:
            dx = sx - dz.left
        elif sx > dz.right:
            dx = sx - dz.right

        if sy < dz.top:
            dy = sy - dz.top
        elif sy > dz.bottom:
            dy = sy - dz.bottom

        self._move_toward(self.x + dx, self.y + dy, dt)
