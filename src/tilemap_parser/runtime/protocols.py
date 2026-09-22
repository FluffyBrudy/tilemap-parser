from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)


@runtime_checkable
class ICollidable(Protocol):
    """All members required; missing layer/mask raises TypeError at first use."""

    x: float
    y: float
    collision_shape: RectangleShape | CircleShape | CapsuleShape | CollisionPolygon
    collision_layer: int
    collision_mask: int


@runtime_checkable
class ICollidableSprite(ICollidable, Protocol):
    """ICollidable plus motion state; passes anywhere ICollidable does."""

    vx: float
    vy: float
    on_ground: bool


ICollidableObject = ICollidable
