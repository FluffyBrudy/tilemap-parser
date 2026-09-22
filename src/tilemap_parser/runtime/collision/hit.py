from __future__ import annotations

import warnings
from dataclasses import dataclass

from ..protocols import ICollidable
from ...utils.geometry import CollisionInfo, aabb_overlap, get_shape_aabb
from .shapes import _check_pair, _combined_aabb, _get_shapes


@dataclass(slots=True)
class CollisionHit:
    object_a: ICollidable
    object_b: ICollidable
    normal: tuple[float, float]
    depth: float

    def resolve(self) -> None:
        sep_x = self.normal[0] * self.depth * 0.5
        sep_y = self.normal[1] * self.depth * 0.5
        self.object_a.x -= sep_x
        self.object_a.y -= sep_y
        self.object_b.x += sep_x
        self.object_b.y += sep_y

    def slide_velocity(self, vx: float, vy: float) -> tuple[float, float]:
        """Strips approach, keeps tangential; unchanged if parallel or leaving."""
        dot = vx * self.normal[0] + vy * self.normal[1]
        if dot > 0:
            return (vx - self.normal[0] * dot, vy - self.normal[1] * dot)
        return (vx, vy)

    def involves(self, obj: ICollidable) -> bool:
        return self.object_a is obj or self.object_b is obj

    def other(self, obj: ICollidable) -> ICollidable:
        """Raises ValueError for non-members."""
        if self.object_a is obj:
            return self.object_b
        if self.object_b is obj:
            return self.object_a
        raise ValueError("Object is not part of this collision hit")

def _layer_mask(obj: ICollidable) -> tuple[int, int]:
    # Missing members raise; never default silently.
    try:
        return obj.collision_layer, obj.collision_mask
    except AttributeError as e:
        raise TypeError(
            f"{type(obj).__name__} is missing required collision members: "
            f"set collision_layer and collision_mask explicitly "
            f"(no implicit defaults)."
        ) from e


def should_collide(
    obj_a: ICollidable,
    obj_b: ICollidable,
) -> bool:
    """
    Both sides must agree (AND, not OR).
    """
    a_layer, a_mask = _layer_mask(obj_a)
    b_layer, b_mask = _layer_mask(obj_b)

    # CRITICAL: AND for mutual agreement (not OR)
    return (a_mask & b_layer) != 0 and (b_mask & a_layer) != 0


_should_collide = should_collide

def check_collision(
    obj_a: ICollidable,
    obj_b: ICollidable,
) -> CollisionHit | None:
    """
    Multi-shape objects supported; identical when both single.
    """
    if not should_collide(obj_a, obj_b):
        return None

    # Shapeless warns and skips; never implicit.
    shapes_a = _get_shapes(obj_a)
    shapes_b = _get_shapes(obj_b)

    if not shapes_a or not shapes_b:
        warnings.warn(
            f"Skipping collision query for shapeless "
            f"{type(obj_a).__name__ if not shapes_a else type(obj_b).__name__}: "
            f"no collision shapes (gate on has_collision before querying).",
            UserWarning,
            stacklevel=2,
        )
        return None

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

    deepest: CollisionInfo | None = None

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

