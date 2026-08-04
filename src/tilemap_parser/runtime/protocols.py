"""Runtime collision protocols — the "interfaces" of the physics system."""

from __future__ import annotations

from typing import Protocol, Union

from pygame import Surface

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
    collision_shape: RectangleShape | CircleShape | CapsuleShape | CollisionPolygon

class ICollidableObject(ICollidable, Protocol):
    """
    Protocol for objects that can collide.

    All required attributes (x, y, collision_shape) are inherited from ICollidable.

    Optional attributes (with defaults):
        collision_layer: Layer this object is on (default: 1)
        collision_mask: Layers to collide with (default: 0xFFFFFFFF)
    """

class ICollidableSprite(ICollidable, Protocol):
    """
    Interface that any sprite/character class must implement to use collision runners.

    Required attributes:
        x (float): World X position
        y (float): World Y position
        collision_shape (RectangleShape | CircleShape | CapsuleShape): Collision shape

    Optional attributes:
        vx (float): X velocity (for physics-based runners)
        vy (float): Y velocity (for physics-based runners)
        on_ground (bool): Whether sprite is on ground (for platformer)
    """

    x: float
    y: float
    collision_shape: Union[RectangleShape, CircleShape, CapsuleShape]

    vx: float
    vy: float
    on_ground: bool
class ExtraObject(Protocol):
    surface: Surface | None
    x: float
    y: float

