"""Shape-level collision primitives (narrowphase dispatch)."""

from __future__ import annotations

import math
import warnings
from typing import TYPE_CHECKING

from ...parser.collision import (
    CapsuleShape,
    CharacterShapeType,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)
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
from ..protocols import ICollidable

if TYPE_CHECKING:
    from ...parser.collision import (
        CharacterCollision,
        TileCollisionData,
        TilesetCollision,
    )
    from ..world import PhysicsWorld


def _get_shapes(obj: ICollidable) -> list:
    """Return all collision shapes for an object.

    Objects with a :attr:`collision_shapes` attribute (e.g.
    :class:`MapObject`) may carry multiple polygons per region;
    single-shape objects return ``[obj.collision_shape]``.
    Shapeless objects return ``[]`` (never ``[None]``) — callers
    warn and skip instead of crashing in AABB computation.
    """
    shapes = getattr(obj, "collision_shapes", None)
    if shapes is not None and len(shapes) > 0:
        return list(shapes)
    shape = getattr(obj, "collision_shape", None)
    if shape is None:
        return []
    return [shape]

def _combined_aabb(x: float, y: float, shapes: list) -> tuple[float, float, float, float]:
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
    obj_a: ICollidable,
    obj_b: ICollidable,
    shape_a,
    shape_b,
    aabb_a: tuple[float, float, float, float],
    aabb_b: tuple[float, float, float, float],
) -> CollisionInfo | None:
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

def _flip_result(info: CollisionInfo | None) -> CollisionInfo | None:
    """Flip the normal of a :class:`CollisionInfo` in place."""
    if info is None:
        return None
    return CollisionInfo(
        normal=(-info.normal[0], -info.normal[1]),
        depth=info.depth,
    )


def shape_to_points(
    shape: CharacterShapeType, x: float = 0.0, y: float = 0.0, scale: float = 1.0
) -> list[tuple[float, float]]:
    if isinstance(shape, RectangleShape):
        left = x + shape.offset[0] * scale
        top = y + shape.offset[1] * scale
        w = shape.width * scale
        h = shape.height * scale
        return [(left, top), (left + w, top), (left + w, top + h), (left, top + h)]
    if isinstance(shape, CircleShape):
        cx = x + shape.offset[0] * scale
        cy = y + shape.offset[1] * scale
        r = shape.radius * scale
        return [(cx + r * math.cos(2 * math.pi * i / 16), cy + r * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    if isinstance(shape, CapsuleShape):
        px = x + shape.offset[0] * scale
        py = y + shape.offset[1] * scale
        r = shape.radius * scale
        bx = px
        by = py + shape.height * scale
        verts: list[tuple[float, float]] = []
        for k in range(5):
            a = math.pi + (math.pi * k / 4)
            verts.append((px + r * math.cos(a), py + r * math.sin(a)))
        for k in range(5):
            a = math.pi * k / 4
            verts.append((bx + r * math.cos(a), by + r * math.sin(a)))
        return verts
    if isinstance(shape, CollisionPolygon):
        return [(x + vx * scale, y + vy * scale) for vx, vy in shape.vertices]
    raise TypeError(f"Unsupported shape type: {type(shape).__name__}")


def describe_shape(shape: CharacterShapeType, x: float = 0.0, y: float = 0.0, scale: float = 1.0) -> dict[str, object]:
    scaled = shape.scaled(scale)
    aabb = get_shape_aabb(x, y, scaled)
    if isinstance(shape, RectangleShape):
        return {
            "kind": "rect",
            "draw_kind": "rect",
            "valid": bool(shape.width > 0 and shape.height > 0),
            "aabb": aabb,
            "rect": (aabb[0], aabb[1], aabb[2] - aabb[0], aabb[3] - aabb[1]),
            "points": shape_to_points(shape, x, y, scale),
        }
    if isinstance(shape, CircleShape):
        center = (x + scaled.offset[0], y + scaled.offset[1])
        return {
            "kind": "circle",
            "draw_kind": "circle",
            "valid": bool(shape.radius > 0),
            "aabb": aabb,
            "center": center,
            "radius": scaled.radius,
            "points": shape_to_points(shape, x, y, scale),
        }
    if isinstance(shape, CapsuleShape):
        top = (x + scaled.offset[0], y + scaled.offset[1])
        bottom = (top[0], top[1] + scaled.height)
        return {
            "kind": "capsule",
            "draw_kind": "capsule",
            "valid": bool(shape.radius > 0 and shape.height >= 0),
            "aabb": aabb,
            "segment": (top, bottom),
            "radius": scaled.radius,
            "points": shape_to_points(shape, x, y, scale),
        }
    if isinstance(shape, CollisionPolygon):
        return {
            "kind": "polygon",
            "draw_kind": "polygon",
            "valid": bool(shape.is_valid()),
            "aabb": aabb,
            "one_way": bool(shape.one_way),
            "points": shape_to_points(shape, x, y, scale),
        }
    raise TypeError(f"Unsupported shape type: {type(shape).__name__}")


def describe_tile_collision(data: TileCollisionData | None, scale: float = 1.0) -> dict[str, object]:
    if data is None:
        return {"has_collision": False, "shapes": []}
    return {
        "tile_id": data.tile_id,
        "has_collision": bool(data.has_collision()),
        "collision_layer": data.collision_layer,
        "collision_mask": data.collision_mask,
        "shapes": [describe_shape(s, 0.0, 0.0, scale) for s in data.shapes],
    }


def describe_tileset_collision(
    tileset: TilesetCollision,
    tile_ids: list[int] | tuple[int, ...] | set[int] | None = None,
    scale: float = 1.0,
) -> dict[int, dict[str, object]]:
    ids = sorted(tileset.tiles.keys()) if tile_ids is None else list(tile_ids)
    return {tid: describe_tile_collision(tileset.tiles.get(tid), scale) for tid in ids}


def describe_character_collision(char: CharacterCollision, scale: float = 1.0) -> dict[str, object]:
    return {
        "name": char.name,
        "collision_layer": char.collision_layer,
        "collision_mask": char.collision_mask,
        "shape": describe_shape(char.shape, 0.0, 0.0, scale),
    }


def describe_sprite(sprite: ICollidable, scale: float = 1.0) -> list[dict[str, object]]:
    return [
        describe_shape(shape, sprite.x, sprite.y, scale)
        for shape in _get_shapes(sprite)
        if shape is not None
    ]


def describe_tile_cell(
    cell: object,
    *,
    world: PhysicsWorld | None = None,
    tileset: TilesetCollision | None = None,
    scale: float | None = None,
) -> list[dict[str, object]]:
    from ..world import flipped_data, iter_cell_entries

    if scale is None:
        scale = world.render_scale if world is not None else 1.0
    out: list[dict[str, object]] = []
    for gid, flags in iter_cell_entries(cell):
        data = None
        if world is not None:
            data = world.resolve_stack_entry((gid, flags))
        elif tileset is not None:
            base = tileset.tiles.get(gid)
            if base is not None:
                data = base if not flags else flipped_data(base, flags, tileset.tile_size)
        if data is None:
            out.append({"gid": gid, "flipbits": flags, "has_collision": False, "shapes": []})
        else:
            out.append(
                {
                    "gid": gid,
                    "flipbits": flags,
                    "has_collision": bool(data.has_collision()),
                    "shapes": [describe_shape(s, 0.0, 0.0, scale) for s in data.shapes],
                }
            )
    return out

