"""Collision hit results and pair queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..protocols import ICollidableObject
from ...utils.geometry import CollisionInfo, aabb_overlap, get_shape_aabb
from .shapes import _check_pair, _combined_aabb, _get_shapes


@dataclass(slots=True)
class CollisionHit:
    """Result of a collision detection between two objects."""

    object_a: ICollidableObject
    object_b: ICollidableObject
    normal: tuple[float, float]  # Direction to separate (from A to B)
    depth: float  # Penetration depth

    def resolve(self) -> None:
        """Separate both objects by half the depth along the collision normal."""
        sep_x = self.normal[0] * self.depth * 0.5
        sep_y = self.normal[1] * self.depth * 0.5
        self.object_a.x -= sep_x
        self.object_a.y -= sep_y
        self.object_b.x += sep_x
        self.object_b.y += sep_y

    def slide_velocity(self, vx: float, vy: float) -> tuple[float, float]:
        """Project velocity along the collision surface (slide response).

        Removes the component of (vx, vy) that is along *self.normal*,
        leaving only the tangential component.  Intended for the moving
        object passed as *object_a* — when that object moves into
        *object_b* the approach component is stripped so the object slides
        along the surface instead of penetrating.

        If the velocity is already parallel to the surface or points away
        from *object_b* the original velocity is returned unchanged.

        Args:
            vx: X component of velocity (object_a's velocity)
            vy: Y component of velocity

        Returns:
            (slide_x, slide_y) — velocity projected onto the surface
        """
        dot = vx * self.normal[0] + vy * self.normal[1]
        if dot > 0:
            return (vx - self.normal[0] * dot, vy - self.normal[1] * dot)
        return (vx, vy)

    def involves(self, obj: ICollidableObject) -> bool:
        """Check if this hit involves the given object."""
        return self.object_a is obj or self.object_b is obj

    def other(self, obj: ICollidableObject) -> ICollidableObject:
        """Get the other object in this hit pair. Raises ValueError if obj is not part of the hit."""
        if self.object_a is obj:
            return self.object_b
        if self.object_b is obj:
            return self.object_a
        raise ValueError("Object is not part of this collision hit")

def should_collide(
    obj_a: ICollidableObject,
    obj_b: ICollidableObject,
) -> bool:
    """
    Check if two objects should collide based on layers.

    Uses mutual agreement: BOTH objects must want to collide.
    This prevents asymmetric filtering issues.
    """
    a_layer = getattr(obj_a, "collision_layer", 1)
    a_mask = getattr(obj_a, "collision_mask", 0xFFFFFFFF)
    b_layer = getattr(obj_b, "collision_layer", 1)
    b_mask = getattr(obj_b, "collision_mask", 0xFFFFFFFF)

    # CRITICAL: AND for mutual agreement (not OR)
    return (a_mask & b_layer) != 0 and (b_mask & a_layer) != 0


# Backward compat alias
_should_collide = should_collide

def check_collision(
    obj_a: ICollidableObject,
    obj_b: ICollidableObject,
) -> Optional[CollisionHit]:
    """
    Check if two objects collide.

    Pipeline:
        1. Layer filtering
        2. Broadphase AABB rejection
        3. Narrowphase geometry dispatch
        4. Return CollisionHit or None

    Supports multi-shape objects (those with a ``collision_shapes``
    attribute).  When both objects have a single shape the behaviour
    is identical to previous versions.
    """
    # 1. Layer filter
    if not should_collide(obj_a, obj_b):
        return None

    # 2. Broadphase — use combined AABB when an object has multiple shapes
    shapes_a = _get_shapes(obj_a)
    shapes_b = _get_shapes(obj_b)

    if len(shapes_a) == 1:
        aabb_a = get_shape_aabb(obj_a.x, obj_a.y, shapes_a[0])
    else:
        aabb_a = _combined_aabb(obj_a.x, obj_a.y, shapes_a)

    if len(shapes_b) == 1:
        aabb_b = get_shape_aabb(obj_b.x, obj_b.y, shapes_b[0])
    else:
        aabb_b = _combined_aabb(obj_b.x, obj_b.y, shapes_b)

    if not aabb_overlap(aabb_a, aabb_b):
        return None

    # 3. Narrowphase — iterate all shape pairs, keep the deepest
    deepest: Optional[CollisionInfo] = None

    for shape_a in shapes_a:
        for shape_b in shapes_b:
            pair_aabb_a = get_shape_aabb(obj_a.x, obj_a.y, shape_a)
            pair_aabb_b = get_shape_aabb(obj_b.x, obj_b.y, shape_b)
            if not aabb_overlap(pair_aabb_a, pair_aabb_b):
                continue

            info = _check_pair(obj_a, obj_b, shape_a, shape_b, pair_aabb_a, pair_aabb_b)
            if info is not None and (deepest is None or info.depth > deepest.depth):
                deepest = info

    if deepest is None:
        return None

    return CollisionHit(
        object_a=obj_a,
        object_b=obj_b,
        normal=deepest.normal,
        depth=deepest.depth,
    )

