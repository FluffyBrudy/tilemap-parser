"""Runtime collision protocols — the "interfaces" of the physics system."""

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
    """Structural contract for anything in the collision space.

    Duck-typed: any object satisfying these members works with
    :class:`ObjectCollisionManager`, :func:`check_collision`, and the
    movement runners. All members are required — no implicit defaults.
    Forgetting ``collision_layer`` / ``collision_mask`` raises a loud
    ``TypeError`` at first use instead of silently colliding (or not)
    with everything.
    """

    x: float
    y: float
    collision_shape: RectangleShape | CircleShape | CapsuleShape | CollisionPolygon
    collision_layer: int
    collision_mask: int


@runtime_checkable
class ICollidableSprite(ICollidable, Protocol):
    """A collidable with motion state for the movement runners.

    Extends :class:`ICollidable`, so sprites pass anywhere a plain
    collidable is expected (e.g. ``ObjectCollisionManager``). Motion
    state is the sole distinction — no parallel hierarchy.
    """

    vx: float
    vy: float
    on_ground: bool


ICollidableObject = ICollidable
