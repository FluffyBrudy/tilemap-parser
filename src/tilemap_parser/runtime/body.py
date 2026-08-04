"""Physics bodies authored into a :class:`~.world.PhysicsWorld`.

A :class:`Body` is the authoring surface for a solid in the world.  It owns
a single primitive collision shape (rectangle, circle, or capsule — polygon
shapes stay in the ``MapObject`` lane) plus its position and velocity, and
participates in collision detection through the same
``ICollidableObject`` contract as :class:`~.map_object.MapObject`
(owner-local shape, ``obj.x + vertex`` applied once by the narrowphase).

Bodies are NOT self-moving.  ``mode == "kinematic"`` marks a body the game
moves explicitly each frame (e.g. a crate pushed with ``move_grounded``);
``mode == "static"`` marks a body that never moves (e.g. scenery, furniture).
Neither mode implies physics-engine dynamics — velocity is scripted, Godot
``StaticBody2D`` / ``CharacterBody2D`` style.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

from ..parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)

BodyMode = str  # "static" | "kinematic"

BODY_MODES = ("static", "kinematic")

BodyShape = RectangleShape | CircleShape | CapsuleShape


class Body:
    """A solid body with a single primitive collision shape."""

    __slots__ = (
        "collision_layer",
        "collision_mask",
        "collision_shape",
        "game_id",
        "mode",
        "on_ground",
        "vx",
        "vy",
        "x",
        "y",
    )

    def __init__(
        self,
        collision_shape: BodyShape,
        x: float = 0.0,
        y: float = 0.0,
        *,
        vx: float = 0.0,
        vy: float = 0.0,
        mode: BodyMode = "static",
        collision_layer: int = 1,
        collision_mask: int = 0xFFFFFFFF,
        game_id: str = "",
    ):
        """
        Create a body.

        Args:
            collision_shape: Primitive shape (RectangleShape, CircleShape,
                or CapsuleShape).  Polygon shapes are not supported on
                bodies — use :class:`MapObject` for polygon solids.
            x: World X position of the shape origin (top-left / center
                per shape offset semantics).
            y: World Y position.
            vx: X velocity (for kinematic bodies).
            vy: Y velocity (for kinematic bodies).
            mode: ``"static"`` (never moves) or ``"kinematic"`` (moved
                explicitly by the game).
            collision_layer: Layer this body is on (default 1).
            collision_mask: Layers this body collides with (default all).
            game_id: Optional label for debugging.
        """
        if not isinstance(collision_shape, (RectangleShape, CircleShape, CapsuleShape)):
            raise TypeError(
                "Body requires a primitive shape (RectangleShape, CircleShape, "
                f"or CapsuleShape), got {type(collision_shape).__name__}"
            )
        if mode not in BODY_MODES:
            raise ValueError(
                f"mode must be one of {BODY_MODES}, got {mode!r}"
            )
        self.collision_shape = collision_shape
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.mode = mode
        self.collision_layer = collision_layer
        self.collision_mask = collision_mask
        self.game_id = game_id
        self.on_ground = False

    def __repr__(self) -> str:
        return (
            f"Body(shape={type(self.collision_shape).__name__}, x={self.x}, "
            f"y={self.y}, mode={self.mode!r}, game_id={self.game_id!r})"
        )

    # ------------------------------------------------------------------
    # Geometry helpers used by the movement resolver
    # ------------------------------------------------------------------

    def top_y_at(self, world_x: float) -> Optional[float]:
        """Return the top-surface world Y of this body at *world_x*, or None.

        Only the top surface is sampled — bodies are never one-way, but the
        resolver only needs the topmost surface for ground landing.
        """
        shape = self.collision_shape
        if isinstance(shape, RectangleShape):
            left = self.x + shape.offset[0]
            if left <= world_x <= left + shape.width:
                return self.y + shape.offset[1]
            return None

        if isinstance(shape, CircleShape):
            cx = self.x + shape.offset[0]
            cy = self.y + shape.offset[1]
            return _circle_top_y(cx, cy, shape.radius, world_x)

        # CapsuleShape — vertical segment (top cap center, radius, height)
        px = self.x + shape.offset[0]
        py = self.y + shape.offset[1]
        return _circle_top_y(px, py, shape.radius, world_x)

    def as_polygon(self) -> CollisionPolygon:
        """World-space polygon approximation of this body's shape.

        Used only by slide-mode normal computation (the tile resolver works
        on polygon edges).  Circles/capsules are approximated with enough
        edges that the closest-edge normal is visually exact.
        """
        shape = self.collision_shape
        if isinstance(shape, RectangleShape):
            left = self.x + shape.offset[0]
            top = self.y + shape.offset[1]
            return CollisionPolygon(
                vertices=[
                    (left, top),
                    (left + shape.width, top),
                    (left + shape.width, top + shape.height),
                    (left, top + shape.height),
                ]
            )

        if isinstance(shape, CircleShape):
            cx = self.x + shape.offset[0]
            cy = self.y + shape.offset[1]
            return CollisionPolygon(
                vertices=_ngon(cx, cy, shape.radius, 16)
            )

        # Capsule — top cap semicircle, implicit side edges, bottom cap
        px = self.x + shape.offset[0]
        py = self.y + shape.offset[1]
        bx = px
        by = py + shape.height
        r = shape.radius
        steps = 4
        verts: list[Tuple[float, float]] = []
        # Top cap — left (pi) to right (0) through the top (3pi/2 = up)
        for k in range(steps + 1):
            a = math.pi + (math.pi * k / steps)
            verts.append((px + r * math.cos(a), py + r * math.sin(a)))
        # Bottom cap — right (0) to left (pi) through the bottom (pi/2 = down)
        for k in range(steps + 1):
            a = math.pi * k / steps
            verts.append((bx + r * math.cos(a), by + r * math.sin(a)))
        return CollisionPolygon(vertices=verts)


def _circle_top_y(cx: float, cy: float, radius: float, world_x: float) -> Optional[float]:
    """Top-surface Y of a circle at *world_x* (upper semicircle), or None."""
    dx = world_x - cx
    if abs(dx) > radius:
        return None
    return cy - math.sqrt(radius * radius - dx * dx)


def _ngon(cx: float, cy: float, radius: float, edges: int) -> list[Tuple[float, float]]:
    """Vertices of a regular polygon approximating a circle."""
    return [
        (
            cx + radius * math.cos(2 * math.pi * i / edges),
            cy + radius * math.sin(2 * math.pi * i / edges),
        )
        for i in range(edges)
    ]
