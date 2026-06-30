"""
Object-to-object collision detection runtime.

Provides a protocol-based interface, shape dispatch, layer filtering,
a multi-object manager, and collision hit helpers for separation/resolve/slide.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from math import floor, isfinite
from typing import Dict, Iterable, Iterator, List, Optional, Protocol, Set, Tuple, Union

from ..parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)
from ..utils.geometry import (
    CollisionInfo,
    aabb_overlap,
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


class ICollidableObject(Protocol):
    """
    Protocol for objects that can collide.

    Required attributes:
        x: World X position
        y: World Y position
        collision_shape: Shape for collision
            (RectangleShape, CircleShape, CapsuleShape, or CollisionPolygon)

    Optional attributes (with defaults):
        collision_layer: Layer this object is on (default: 1)
        collision_mask: Layers to collide with (default: 0xFFFFFFFF)
    """

    x: float
    y: float
    collision_shape: Union[RectangleShape, CircleShape, CapsuleShape, CollisionPolygon]


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

    All shape combinations are supported, including polygon-vs-anything.
    """
    # 1. Layer filter
    if not should_collide(obj_a, obj_b):
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

    # Capsule pairs
    elif isinstance(shape_a, CapsuleShape) and isinstance(shape_b, CapsuleShape):
        p1 = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        p2 = (p1[0], p1[1] + shape_a.height)
        q1 = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        q2 = (q1[0], q1[1] + shape_b.height)
        info = capsule_vs_capsule(p1, p2, shape_a.radius, q1, q2, shape_b.radius)

    elif isinstance(shape_a, CapsuleShape) and isinstance(shape_b, CircleShape):
        p1 = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        p2 = (p1[0], p1[1] + shape_a.height)
        cb = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        info = capsule_vs_circle(p1, p2, shape_a.radius, cb, shape_b.radius)

    elif isinstance(shape_a, CircleShape) and isinstance(shape_b, CapsuleShape):
        ca = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        q1 = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        q2 = (q1[0], q1[1] + shape_b.height)
        result = capsule_vs_circle(q1, q2, shape_b.radius, ca, shape_a.radius)
        if result is not None:
            info = CollisionInfo(
                normal=(-result.normal[0], -result.normal[1]),
                depth=result.depth,
            )

    elif isinstance(shape_a, CapsuleShape) and isinstance(shape_b, RectangleShape):
        p1 = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        p2 = (p1[0], p1[1] + shape_a.height)
        info = capsule_vs_rect(p1, p2, shape_a.radius, aabb_b)

    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, CapsuleShape):
        q1 = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        q2 = (q1[0], q1[1] + shape_b.height)
        result = capsule_vs_rect(q1, q2, shape_b.radius, aabb_a)
        if result is not None:
            info = CollisionInfo(
                normal=(-result.normal[0], -result.normal[1]),
                depth=result.depth,
            )

    elif isinstance(shape_a, CapsuleShape) and isinstance(shape_b, CollisionPolygon):
        p1 = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        p2 = (p1[0], p1[1] + shape_a.height)
        verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
        info = capsule_vs_polygon(p1, p2, shape_a.radius, verts_b)

    elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, CapsuleShape):
        verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
        q1 = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        q2 = (q1[0], q1[1] + shape_b.height)
        result = capsule_vs_polygon(q1, q2, shape_b.radius, verts_a)
        if result is not None:
            info = CollisionInfo(
                normal=(-result.normal[0], -result.normal[1]),
                depth=result.depth,
            )

    else:
        warnings.warn(
            f"Unhandled collision shape pair: {type(shape_a).__name__} vs {type(shape_b).__name__}",
            UserWarning,
            stacklevel=2,
        )
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

    Uses a uniform-grid spatial broadphase and exact shape narrowphase.
    The grid is rebuilt for each query so moved objects are always indexed
    at their current world positions.
    """

    def __init__(
        self,
        objects: Optional[Iterable[ICollidableObject]] = None,
        *,
        cell_size: float = 128.0,
    ) -> None:
        if not isfinite(cell_size) or cell_size <= 0:
            raise ValueError("cell_size must be a finite positive number")

        self.objects: List[ICollidableObject] = []
        self.cell_size = float(cell_size)
        if objects is not None:
            for obj in objects:
                self.add_object(obj)

    def __len__(self) -> int:
        """Return the number of objects currently managed."""
        return len(self.objects)

    def __iter__(self) -> Iterator[ICollidableObject]:
        """Iterate over managed objects in insertion order."""
        return iter(self.objects)

    def __contains__(self, obj: object) -> bool:
        """Return True if the exact object instance is managed."""
        return any(existing is obj for existing in self.objects)

    def _find_object_index(self, obj: ICollidableObject) -> int:
        for index, existing in enumerate(self.objects):
            if existing is obj:
                return index
        return -1

    def add_object(self, obj: ICollidableObject) -> None:
        """Add an object to the collision system."""
        if self._find_object_index(obj) != -1:
            warnings.warn(
                f"Object {obj} is already in the collision manager, skipping.",
                UserWarning,
                stacklevel=2,
            )
            return
        self.objects.append(obj)

    def remove_object(self, obj: ICollidableObject) -> None:
        """Remove an object from the collision system."""
        index = self._find_object_index(obj)
        if index == -1:
            warnings.warn(
                f"Object {obj} is not in the collision manager, skipping.",
                UserWarning,
                stacklevel=2,
            )
            return
        del self.objects[index]

    def clear(self) -> None:
        """Remove all objects from the collision system."""
        self.objects.clear()

    def _cells_for_aabb(
        self,
        aabb: tuple[float, float, float, float],
    ) -> Iterator[Tuple[int, int]]:
        left, top, right, bottom = aabb
        min_cell_x = floor(left / self.cell_size)
        max_cell_x = floor(right / self.cell_size)
        min_cell_y = floor(top / self.cell_size)
        max_cell_y = floor(bottom / self.cell_size)

        for cell_y in range(min_cell_y, max_cell_y + 1):
            for cell_x in range(min_cell_x, max_cell_x + 1):
                yield (cell_x, cell_y)

    def _object_aabb(
        self,
        obj: ICollidableObject,
    ) -> tuple[float, float, float, float]:
        return get_shape_aabb(obj.x, obj.y, obj.collision_shape)

    def _build_spatial_index(
        self,
    ) -> tuple[Tuple[ICollidableObject, ...], Dict[Tuple[int, int], List[int]]]:
        objects = tuple(self.objects)
        grid: Dict[Tuple[int, int], List[int]] = {}

        for index, obj in enumerate(objects):
            for cell in self._cells_for_aabb(self._object_aabb(obj)):
                grid.setdefault(cell, []).append(index)

        return objects, grid

    def _candidate_indices(
        self,
        obj: ICollidableObject,
        grid: Dict[Tuple[int, int], List[int]],
    ) -> Set[int]:
        candidates: Set[int] = set()
        for cell in self._cells_for_aabb(self._object_aabb(obj)):
            candidates.update(grid.get(cell, ()))
        return candidates

    def check_all_collisions(self) -> List[CollisionHit]:
        """
        Check every potentially colliding pair.

        Returns a list of CollisionHit for all colliding pairs.
        Each pair appears at most once (i, j) with j > i.
        """
        objects, grid = self._build_spatial_index()
        hits: List[CollisionHit] = []

        for i, obj in enumerate(objects):
            candidate_indices = self._candidate_indices(obj, grid)
            for j in sorted(candidate_indices):
                if j <= i:
                    continue
                hit = check_collision(objects[i], objects[j])
                if hit is not None:
                    hits.append(hit)
        return hits

    def check_object(self, obj: ICollidableObject) -> List[CollisionHit]:
        """
        Check one object against all others.

        The queried object does not need to be managed. If it is managed,
        comparison with itself is skipped by identity.
        """
        objects, grid = self._build_spatial_index()
        hits: List[CollisionHit] = []
        for index in sorted(self._candidate_indices(obj, grid)):
            other = objects[index]
            if other is obj:
                continue
            hit = check_collision(obj, other)
            if hit is not None:
                hits.append(hit)
        return hits

    def check_object_first(self, obj: ICollidableObject) -> Optional[CollisionHit]:
        """
        Check one object against all others and return the first collision hit.

        The queried object does not need to be managed. If it is managed,
        comparison with itself is skipped by identity.

        Candidate iteration follows insertion order among the spatially relevant
        managed objects.
        """
        objects, grid = self._build_spatial_index()
        for index in sorted(self._candidate_indices(obj, grid)):
            other = objects[index]
            if other is obj:
                continue
            hit = check_collision(obj, other)
            if hit is not None:
                return hit
        return None
