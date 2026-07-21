from __future__ import annotations

from typing import Protocol, Union

from ..parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)


class ICollidable(Protocol):
    """Base protocol for anything with a world position and collision shape.

    This is the minimal interface for participating in collision detection.
    All collidable protocols (ICollidableSprite, ICollidableObject) extend this.

    Required attributes:
        x (float): World X position
        y (float): World Y position
        collision_shape: Shape used for collision detection
            (RectangleShape, CircleShape, CapsuleShape, or CollisionPolygon)
    """

    x: float
    y: float
    collision_shape: Union[RectangleShape, CircleShape, CapsuleShape, CollisionPolygon]
