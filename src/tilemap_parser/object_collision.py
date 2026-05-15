"""
Object-to-object collision detection runtime.

Provides a protocol-based interface, shape dispatch, layer filtering,
and a multi-object manager.  Pure detection — no physics or response.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import List, Optional, Protocol, Union

from .collision import CircleShape, CollisionPolygon, RectangleShape
from .geometry import (
    CollisionInfo,
    aabb_overlap,
    circle_vs_circle,
    get_shape_aabb,
    polygon_vs_circle,
    polygon_vs_polygon,
    polygon_vs_rect,
    rect_vs_circle,
    rect_vs_rect,
)


class ICollidableObject(Protocol):
    """
    Protocol for objects that can collide.

    Required attributes:
        x: World X position
        y: World Y position
        collision_shape: Shape for collision
            (RectangleShape, CircleShape, or CollisionPolygon)

    Optional attributes (with defaults):
        collision_layer: Layer this object is on (default: 1)
        collision_mask: Layers to collide with (default: 0xFFFFFFFF)
    """

    x: float
    y: float
    collision_shape: Union[RectangleShape, CircleShape, CollisionPolygon]
    collision_layer: int
    collision_mask: int


@dataclass(slots=True)
class CollisionHit:
    """Result of a collision detection between two objects."""

    object_a: ICollidableObject
    object_b: ICollidableObject
    normal: tuple[float, float]  # Direction to separate (from A to B)
    depth: float  # Penetration depth


def _should_collide(
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

    All shape combinations are supported, including polygon-vs-anything.
    """
    # 1. Layer filter
    if not _should_collide(obj_a, obj_b):
        return None

    # 2. Broadphase
    aabb_a = get_shape_aabb(obj_a.x, obj_a.y, obj_a.collision_shape)
    aabb_b = get_shape_aabb(obj_b.x, obj_b.y, obj_b.collision_shape)
    if not aabb_overlap(aabb_a, aabb_b):
        return None

    # 3. Narrowphase dispatch
    shape_a = obj_a.collision_shape
    shape_b = obj_b.collision_shape

    info: Optional[CollisionInfo] = None

    if isinstance(shape_a, CircleShape) and isinstance(shape_b, CircleShape):
        ca = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        cb = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        info = circle_vs_circle(ca, shape_a.radius, cb, shape_b.radius)

    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, RectangleShape):
        info = rect_vs_rect(aabb_a, aabb_b)

    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, CircleShape):
        cb = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        info = rect_vs_circle(aabb_a, cb, shape_b.radius)

    elif isinstance(shape_a, CircleShape) and isinstance(shape_b, RectangleShape):
        ca = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        result = rect_vs_circle(aabb_b, ca, shape_a.radius)
        if result is not None:
            # Flip normal: was rect→circle, need circle→rect
            info = CollisionInfo(
                normal=(-result.normal[0], -result.normal[1]),
                depth=result.depth,
            )

    # Polygon vs Polygon
    elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, CollisionPolygon):
        verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
        verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
        info = polygon_vs_polygon(verts_a, verts_b)

    # Polygon vs Circle
    elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, CircleShape):
        verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
        center_b = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        info = polygon_vs_circle(verts_a, center_b, shape_b.radius)

    # Circle vs Polygon (flip normal)
    elif isinstance(shape_a, CircleShape) and isinstance(shape_b, CollisionPolygon):
        verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
        center_a = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        result = polygon_vs_circle(verts_b, center_a, shape_a.radius)
        if result is not None:
            info = CollisionInfo(
                normal=(-result.normal[0], -result.normal[1]),
                depth=result.depth,
            )

    # Polygon vs Rect
    elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, RectangleShape):
        verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
        info = polygon_vs_rect(verts_a, aabb_b)

    # Rect vs Polygon (flip normal)
    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, CollisionPolygon):
        verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
        result = polygon_vs_rect(verts_b, aabb_a)
        if result is not None:
            info = CollisionInfo(
                normal=(-result.normal[0], -result.normal[1]),
                depth=result.depth,
            )

    else:
        return None

    if info is None:
        return None

    return CollisionHit(
        object_a=obj_a,
        object_b=obj_b,
        normal=info.normal,
        depth=info.depth,
    )


class ObjectCollisionManager:
    """
    Manages collision detection for multiple objects.

    Features:
        - Add / remove objects
        - All-vs-all and one-vs-all queries
        - Layer filtering

    Note: This version uses brute-force O(n²) detection.
          Spatial partitioning is deferred to other version.
    """

    def __init__(self) -> None:
        self.objects: List[ICollidableObject] = []

    def add_object(self, obj: ICollidableObject) -> None:
        """Add an object to the collision system."""
        if obj in self.objects:
            warnings.warn(
                f"Object {obj} is already in the collision manager, skipping.",
                UserWarning,
                stacklevel=2,
            )
            return
        self.objects.append(obj)

    def remove_object(self, obj: ICollidableObject) -> None:
        """Remove an object from the collision system."""
        if obj not in self.objects:
            warnings.warn(
                f"Object {obj} is not in the collision manager, skipping.",
                UserWarning,
                stacklevel=2,
            )
            return
        self.objects.remove(obj)

    def check_all_collisions(self) -> List[CollisionHit]:
        """
        Check every unique pair (brute-force).

        Returns a list of CollisionHit for all colliding pairs.
        Each pair appears at most once (i, j) with j > i.
        """
        hits: List[CollisionHit] = []
        n = len(self.objects)
        for i in range(n):
            for j in range(i + 1, n):
                hit = check_collision(self.objects[i], self.objects[j])
                if hit is not None:
                    hits.append(hit)
        return hits

    def check_object(self, obj: ICollidableObject) -> List[CollisionHit]:
        """
        Check one object against all others.

        Skips comparison with itself.
        """
        hits: List[CollisionHit] = []
        for other in self.objects:
            if other is obj:
                continue
            hit = check_collision(obj, other)
            if hit is not None:
                hits.append(hit)
        return hits
