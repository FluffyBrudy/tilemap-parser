"""World solids: primitive shapes only (polygons stay in MapObject). Static
never moves; kinematic is moved explicitly by the game; neither simulates.
"""

from __future__ import annotations

import math

from ..parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)

BodyMode = str

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
        Polygons rejected (use MapObject); mode static/kinematic only.
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

    def top_y_at(self, world_x: float) -> float | None:
        """Top surface only; bodies are never one-way."""
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

        px = self.x + shape.offset[0]
        py = self.y + shape.offset[1]
        return _circle_top_y(px, py, shape.radius, world_x)

    def as_polygon(self) -> CollisionPolygon:
        """Slide-mode normals only; enough edges to read exact."""
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
        verts: list[tuple[float, float]] = []
        for k in range(steps + 1):
            a = math.pi + (math.pi * k / steps)
            verts.append((px + r * math.cos(a), py + r * math.sin(a)))
        for k in range(steps + 1):
            a = math.pi * k / steps
            verts.append((bx + r * math.cos(a), by + r * math.sin(a)))
        return CollisionPolygon(vertices=verts)


def _circle_top_y(cx: float, cy: float, radius: float, world_x: float) -> float | None:
    dx = world_x - cx
    if abs(dx) > radius:
        return None
    return cy - math.sqrt(radius * radius - dx * dx)


def _ngon(cx: float, cy: float, radius: float, edges: int) -> list[tuple[float, float]]:
    return [
        (
            cx + radius * math.cos(2 * math.pi * i / edges),
            cy + radius * math.sin(2 * math.pi * i / edges),
        )
        for i in range(edges)
    ]
