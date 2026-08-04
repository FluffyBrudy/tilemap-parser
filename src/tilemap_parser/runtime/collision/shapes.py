"""Shape-level collision primitives (narrowphase dispatch)."""

from __future__ import annotations

import warnings
from typing import List, Optional

from ...parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)
from ..protocols import ICollidableObject
from ...utils.geometry import (
    CollisionInfo,
    capsule_vs_capsule,
    capsule_vs_circle,
    capsule_vs_polygon,
    capsule_vs_rect,
    circle_vs_circle,
    get_shape_aabb,
    polygon_vs_circle,
    polygon_vs_polygon,
    polygon_vs_rect,
    rect_vs_circle,
    rect_vs_rect,
)


def _get_shapes(obj: ICollidableObject) -> List:
    """Return all collision shapes for an object.

    Objects with a :attr:`collision_shapes` attribute (e.g.
    :class:`MapObject`) may carry multiple polygons per region;
    single-shape objects return ``[obj.collision_shape]``.
    """
    shapes = getattr(obj, "collision_shapes", None)
    if shapes is not None and len(shapes) > 0:
        return list(shapes)
    return [obj.collision_shape]

def _combined_aabb(x: float, y: float, shapes: List) -> tuple[float, float, float, float]:
    """Union AABB across all shapes at position *(x, y)*."""
    left = top = float("inf")
    right = bottom = float("-inf")
    for shape in shapes:
        sx0, sy0, sx1, sy1 = get_shape_aabb(x, y, shape)
        if sx0 < left:
            left = sx0
        if sy0 < top:
            top = sy0
        if sx1 > right:
            right = sx1
        if sy1 > bottom:
            bottom = sy1
    return (left, top, right, bottom)

def _check_pair(
    obj_a: ICollidableObject,
    obj_b: ICollidableObject,
    shape_a,
    shape_b,
    aabb_a: tuple[float, float, float, float],
    aabb_b: tuple[float, float, float, float],
) -> Optional[CollisionInfo]:
    """Run narrowphase for a single shape pair."""
    if isinstance(shape_a, CircleShape) and isinstance(shape_b, CircleShape):
        ca = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        cb = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        return circle_vs_circle(ca, shape_a.radius, cb, shape_b.radius)

    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, RectangleShape):
        return rect_vs_rect(aabb_a, aabb_b)

    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, CircleShape):
        cb = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        return rect_vs_circle(aabb_a, cb, shape_b.radius)

    elif isinstance(shape_a, CircleShape) and isinstance(shape_b, RectangleShape):
        ca = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        return _flip_result(rect_vs_circle(aabb_b, ca, shape_a.radius))

    # Polygon vs Polygon
    elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, CollisionPolygon):
        verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
        verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
        return polygon_vs_polygon(verts_a, verts_b)

    # Polygon vs Circle
    elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, CircleShape):
        verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
        center_b = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        return polygon_vs_circle(verts_a, center_b, shape_b.radius)

    # Circle vs Polygon (flip normal)
    elif isinstance(shape_a, CircleShape) and isinstance(shape_b, CollisionPolygon):
        verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
        center_a = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        return _flip_result(polygon_vs_circle(verts_b, center_a, shape_a.radius))

    # Polygon vs Rect
    elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, RectangleShape):
        verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
        return polygon_vs_rect(verts_a, aabb_b)

    # Rect vs Polygon (flip normal)
    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, CollisionPolygon):
        verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
        return _flip_result(polygon_vs_rect(verts_b, aabb_a))

    # Capsule pairs
    elif isinstance(shape_a, CapsuleShape) and isinstance(shape_b, CapsuleShape):
        p1 = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        p2 = (p1[0], p1[1] + shape_a.height)
        q1 = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        q2 = (q1[0], q1[1] + shape_b.height)
        return capsule_vs_capsule(p1, p2, shape_a.radius, q1, q2, shape_b.radius)

    elif isinstance(shape_a, CapsuleShape) and isinstance(shape_b, CircleShape):
        p1 = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        p2 = (p1[0], p1[1] + shape_a.height)
        cb = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        return capsule_vs_circle(p1, p2, shape_a.radius, cb, shape_b.radius)

    elif isinstance(shape_a, CircleShape) and isinstance(shape_b, CapsuleShape):
        ca = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        q1 = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        q2 = (q1[0], q1[1] + shape_b.height)
        return _flip_result(capsule_vs_circle(q1, q2, shape_b.radius, ca, shape_a.radius))

    elif isinstance(shape_a, CapsuleShape) and isinstance(shape_b, RectangleShape):
        p1 = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        p2 = (p1[0], p1[1] + shape_a.height)
        return capsule_vs_rect(p1, p2, shape_a.radius, aabb_b)

    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, CapsuleShape):
        q1 = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        q2 = (q1[0], q1[1] + shape_b.height)
        return _flip_result(capsule_vs_rect(q1, q2, shape_b.radius, aabb_a))

    elif isinstance(shape_a, CapsuleShape) and isinstance(shape_b, CollisionPolygon):
        p1 = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        p2 = (p1[0], p1[1] + shape_a.height)
        verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
        return capsule_vs_polygon(p1, p2, shape_a.radius, verts_b)

    elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, CapsuleShape):
        verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
        q1 = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        q2 = (q1[0], q1[1] + shape_b.height)
        return _flip_result(capsule_vs_polygon(q1, q2, shape_b.radius, verts_a))

    else:
        warnings.warn(
            f"Unhandled collision shape pair: {type(shape_a).__name__} vs {type(shape_b).__name__}",
            UserWarning,
            stacklevel=3,
        )
        return None

def _flip_result(info: Optional[CollisionInfo]) -> Optional[CollisionInfo]:
    """Flip the normal of a :class:`CollisionInfo` in place."""
    if info is None:
        return None
    return CollisionInfo(
        normal=(-info.normal[0], -info.normal[1]),
        depth=info.depth,
    )

