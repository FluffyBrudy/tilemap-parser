"""Zero-allocation polygon-vs-shape query primitives.

Pure math: sprite shape vs tile polygon tests with the tile offset applied
inline during computation. Shared by the movement resolver and tile queries.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from ..parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
    TilesetCollision,
)
from .protocols import ICollidable

Point = Tuple[float, float]

def point_in_polygon(point: Point, vertices: List[Point]) -> bool:
    """Check if point is inside polygon using ray casting (tile-local coordinates)."""
    if not vertices:
        return False
    x, y = point
    n = len(vertices)
    inside = False
    p1x, p1y = vertices[0]
    for i in range(1, n + 1):
        p2x, p2y = vertices[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def _point_in_polygon_offset(
    px: float,
    py: float,
    vertices: List[Point],
    ox: float,
    oy: float,
    scale: float = 1.0,
) -> bool:
    """Ray-cast with tile offset applied inline — no allocation."""
    if not vertices:
        return False
    n = len(vertices)
    inside = False
    p1x, p1y = vertices[0][0] * scale + ox, vertices[0][1] * scale + oy
    for i in range(1, n + 1):
        vx, vy = vertices[i % n]
        p2x, p2y = vx * scale + ox, vy * scale + oy
        if py > min(p1y, p2y):
            if py <= max(p1y, p2y):
                if px <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or px <= xinters:
                            inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def _segments_intersect(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    cx: float,
    cy: float,
    dx: float,
    dy: float,
) -> bool:
    """Check if segment AB intersects CD (open — ignores collinear/endpoint)."""
    o1 = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    o2 = (bx - ax) * (dy - ay) - (by - ay) * (dx - ax)
    o3 = (dx - cx) * (ay - cy) - (dy - cy) * (ax - cx)
    o4 = (dx - cx) * (by - cy) - (dy - cy) * (bx - cx)
    if (o1 > 0 and o2 < 0) or (o1 < 0 and o2 > 0):
        if (o3 > 0 and o4 < 0) or (o3 < 0 and o4 > 0):
            return True
    return False

def rect_polygon_collision(
    rect_x: float, rect_y: float, rect_w: float, rect_h: float, vertices: List[Point]
) -> bool:
    """Check if rectangle collides with polygon (world-space vertices)."""
    if not vertices:
        return False
    # AABB pre-reject
    n = len(vertices)
    min_vx = max_vx = vertices[0][0]
    min_vy = max_vy = vertices[0][1]
    for i in range(1, n):
        vx, vy = vertices[i]
        if vx < min_vx:
            min_vx = vx
        elif vx > max_vx:
            max_vx = vx
        if vy < min_vy:
            min_vy = vy
        elif vy > max_vy:
            max_vy = vy
    rx2 = rect_x + rect_w
    ry2 = rect_y + rect_h
    if rect_x > max_vx or rx2 < min_vx or rect_y > max_vy or ry2 < min_vy:
        return False

    # Corner tests — no tuple allocation
    if point_in_polygon((rect_x, rect_y), vertices):
        return True
    if point_in_polygon((rx2, rect_y), vertices):
        return True
    if point_in_polygon((rect_x, ry2), vertices):
        return True
    if point_in_polygon((rx2, ry2), vertices):
        return True

    # Vertex-in-rect — half-open right/bottom edges: a vertex sitting exactly
    # on the rect's bottom/right edge is resting contact, not an overlap
    # (consistent with the ray-cast and segment tests, which are exclusive).
    for vx, vy in vertices:
        if rect_x <= vx < rx2 and rect_y <= vy < ry2:
            return True

    # Edge-edge intersection (catches triangle-vs-rectangle cases)
    rect_edges = (
        (rect_x, rect_y, rx2, rect_y),
        (rx2, rect_y, rx2, ry2),
        (rx2, ry2, rect_x, ry2),
        (rect_x, ry2, rect_x, rect_y),
    )
    for rax, ray, rbx, rby in rect_edges:
        for i in range(n):
            p1x, p1y = vertices[i]
            p2x, p2y = vertices[(i + 1) % n]
            if _segments_intersect(rax, ray, rbx, rby, p1x, p1y, p2x, p2y):
                return True
    return False

def _rect_polygon_collision_offset(
    rect_x: float,
    rect_y: float,
    rect_w: float,
    rect_h: float,
    vertices: List[Point],
    ox: float,
    oy: float,
    scale: float = 1.0,
) -> bool:
    """Rectangle vs polygon with tile offset applied inline — no allocation."""
    if not vertices:
        return False
    # AABB pre-reject with offset
    n = len(vertices)
    v0x, v0y = vertices[0][0] * scale + ox, vertices[0][1] * scale + oy
    min_vx = max_vx = v0x
    min_vy = max_vy = v0y
    for i in range(1, n):
        wx, wy = vertices[i][0] * scale + ox, vertices[i][1] * scale + oy
        if wx < min_vx:
            min_vx = wx
        elif wx > max_vx:
            max_vx = wx
        if wy < min_vy:
            min_vy = wy
        elif wy > max_vy:
            max_vy = wy
    if (
        rect_x > max_vx
        or rect_x + rect_w < min_vx
        or rect_y > max_vy
        or rect_y + rect_h < min_vy
    ):
        return False

    # Corner tests
    rx2, ry2 = rect_x + rect_w, rect_y + rect_h
    if _point_in_polygon_offset(rect_x, rect_y, vertices, ox, oy, scale):
        return True
    if _point_in_polygon_offset(rx2, rect_y, vertices, ox, oy, scale):
        return True
    if _point_in_polygon_offset(rect_x, ry2, vertices, ox, oy, scale):
        return True
    if _point_in_polygon_offset(rx2, ry2, vertices, ox, oy, scale):
        return True

    # Vertex-in-rect — half-open right/bottom edges (resting contact, see above)
    for vx, vy in vertices:
        wx, wy = vx * scale + ox, vy * scale + oy
        if rect_x <= wx < rx2 and rect_y <= wy < ry2:
            return True

    # Edge-edge intersection (catches triangle-vs-rectangle cases)
    for i in range(n):
        p1x = vertices[i][0] * scale + ox
        p1y = vertices[i][1] * scale + oy
        p2x = vertices[(i + 1) % n][0] * scale + ox
        p2y = vertices[(i + 1) % n][1] * scale + oy
        if _segments_intersect(rect_x, rect_y, rx2, rect_y, p1x, p1y, p2x, p2y):
            return True
        if _segments_intersect(rx2, rect_y, rx2, ry2, p1x, p1y, p2x, p2y):
            return True
        if _segments_intersect(rx2, ry2, rect_x, ry2, p1x, p1y, p2x, p2y):
            return True
        if _segments_intersect(rect_x, ry2, rect_x, rect_y, p1x, p1y, p2x, p2y):
            return True
    return False

def circle_polygon_collision(
    center: Point, radius: float, vertices: List[Point]
) -> bool:
    """Check if circle collides with polygon (world-space vertices)."""
    if point_in_polygon(center, vertices):
        return True

    cx, cy = center
    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        dx = x2 - x1
        dy = y2 - y1
        fx = cx - x1
        fy = cy - y1
        if dx == 0 and dy == 0:
            dist = math.sqrt((cx - x1) ** 2 + (cy - y1) ** 2)
        else:
            t = max(0.0, min(1.0, (fx * dx + fy * dy) / (dx * dx + dy * dy)))
            closest_x = x1 + t * dx
            closest_y = y1 + t * dy
            dist = math.sqrt((cx - closest_x) ** 2 + (cy - closest_y) ** 2)
        if dist <= radius:
            return True
    return False

def _circle_polygon_collision_offset(
    cx: float,
    cy: float,
    radius: float,
    vertices: List[Point],
    ox: float,
    oy: float,
    scale: float = 1.0,
) -> bool:
    """Circle vs polygon with tile offset applied inline — no allocation."""
    if _point_in_polygon_offset(cx, cy, vertices, ox, oy, scale):
        return True
    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i][0] * scale + ox, vertices[i][1] * scale + oy
        x2, y2 = (
            vertices[(i + 1) % n][0] * scale + ox,
            vertices[(i + 1) % n][1] * scale + oy,
        )
        dx = x2 - x1
        dy = y2 - y1
        fx = cx - x1
        fy = cy - y1
        if dx == 0 and dy == 0:
            dist = math.sqrt((cx - x1) ** 2 + (cy - y1) ** 2)
        else:
            t = max(0.0, min(1.0, (fx * dx + fy * dy) / (dx * dx + dy * dy)))
            closest_x = x1 + t * dx
            closest_y = y1 + t * dy
            dist = math.sqrt((cx - closest_x) ** 2 + (cy - closest_y) ** 2)
        if dist <= radius:
            return True
    return False

def get_shape_bounds(sprite: ICollidable) -> Tuple[float, float, float, float]:
    """Get AABB bounds for sprite (left, top, right, bottom)"""
    shape = sprite.collision_shape
    if isinstance(shape, RectangleShape):
        left = sprite.x + shape.offset[0]
        top = sprite.y + shape.offset[1]
        return (left, top, left + shape.width, top + shape.height)
    elif isinstance(shape, CircleShape):
        cx, cy = shape.get_center(sprite.x, sprite.y)
        r = shape.radius
        return (cx - r, cy - r, cx + r, cy + r)
    elif isinstance(shape, CapsuleShape):
        top_center = shape.get_top_center(sprite.x, sprite.y)
        r = shape.radius
        h = shape.height
        return (
            top_center[0] - r,
            top_center[1] - r,
            top_center[0] + r,
            top_center[1] + h + r,
        )
    elif isinstance(shape, CollisionPolygon):
        verts = shape.vertices
        if not verts:
            return (sprite.x, sprite.y, sprite.x, sprite.y)
        min_x = min(v[0] for v in verts)
        max_x = max(v[0] for v in verts)
        min_y = min(v[1] for v in verts)
        max_y = max(v[1] for v in verts)
        return (sprite.x + min_x, sprite.y + min_y, sprite.x + max_x, sprite.y + max_y)
    return (sprite.x, sprite.y, sprite.x + 32, sprite.y + 32)

def check_sprite_polygon_collision(
    sprite: ICollidable, polygon: CollisionPolygon
) -> bool:
    """Check if sprite collides with a world-space polygon (legacy / public API)."""
    shape = sprite.collision_shape
    if isinstance(shape, RectangleShape):
        left, top, right, bottom = get_shape_bounds(sprite)
        return rect_polygon_collision(
            left, top, right - left, bottom - top, polygon.vertices
        )
    elif isinstance(shape, CircleShape):
        center = shape.get_center(sprite.x, sprite.y)
        return circle_polygon_collision(center, shape.radius, polygon.vertices)
    elif isinstance(shape, CapsuleShape):
        left, top, right, bottom = get_shape_bounds(sprite)
        return rect_polygon_collision(
            left, top, right - left, bottom - top, polygon.vertices
        )
    return False

def _check_sprite_polygon_offset(
    sprite: ICollidable,
    polygon: CollisionPolygon,
    ox: float,
    oy: float,
    scale: float = 1.0,
) -> bool:
    """
    Check if sprite collides with a tile-local polygon at world offset (ox, oy).
    No allocation — offset is applied inline during math.
    """
    shape = sprite.collision_shape
    if isinstance(shape, RectangleShape):
        left = sprite.x + shape.offset[0]
        top = sprite.y + shape.offset[1]
        return _rect_polygon_collision_offset(
            left, top, shape.width, shape.height, polygon.vertices, ox, oy, scale
        )
    elif isinstance(shape, CircleShape):
        cx = sprite.x + shape.offset[0]
        cy = sprite.y + shape.offset[1]
        return _circle_polygon_collision_offset(
            cx, cy, shape.radius, polygon.vertices, ox, oy, scale
        )
    elif isinstance(shape, CapsuleShape):
        left = sprite.x + shape.offset[0] - shape.radius
        top = sprite.y + shape.offset[1] - shape.radius
        w = shape.radius * 2
        h = shape.height + shape.radius * 2
        return _rect_polygon_collision_offset(
            left, top, w, h, polygon.vertices, ox, oy, scale
        )
    elif isinstance(shape, CollisionPolygon):
        return _polygon_polygon_collision_offset(
            shape.vertices, polygon.vertices, sprite.x, sprite.y, ox, oy, scale
        )
    return False

def _polygon_polygon_collision_offset(
    verts_a: list[Point],
    verts_b: list[Point],
    ax: float,
    ay: float,
    ox: float,
    oy: float,
    scale: float = 1.0,
) -> bool:
    """Polygon vs polygon with offsets applied inline — no allocation.

    *verts_a* is sprite-local (translated by the sprite origin *ax*, *ay*);
    *verts_b* is tile-local (translated by the tile offset *ox*, *oy* and
    scaled by *scale*).
    """
    if not verts_a or not verts_b:
        return False

    a0x = ax + verts_a[0][0]
    a0y = ay + verts_a[0][1]
    a_min_x = a_max_x = a0x
    a_min_y = a_max_y = a0y
    for vx, vy in verts_a[1:]:
        wx, wy = ax + vx, ay + vy
        if wx < a_min_x:
            a_min_x = wx
        elif wx > a_max_x:
            a_max_x = wx
        if wy < a_min_y:
            a_min_y = wy
        elif wy > a_max_y:
            a_max_y = wy

    b0x = ox + verts_b[0][0] * scale
    b0y = oy + verts_b[0][1] * scale
    b_min_x = b_max_x = b0x
    b_min_y = b_max_y = b0y
    for vx, vy in verts_b[1:]:
        wx, wy = ox + vx * scale, oy + vy * scale
        if wx < b_min_x:
            b_min_x = wx
        elif wx > b_max_x:
            b_max_x = wx
        if wy < b_min_y:
            b_min_y = wy
        elif wy > b_max_y:
            b_max_y = wy

    if a_min_x > b_max_x or a_max_x < b_min_x or a_min_y > b_max_y or a_max_y < b_min_y:
        return False

    # Vertex-in-polygon (either polygon containing a vertex of the other)
    for vx, vy in verts_a:
        if _point_in_polygon_offset(ax + vx, ay + vy, verts_b, ox, oy, scale):
            return True
    for vx, vy in verts_b:
        if _point_in_polygon_offset(ox + vx * scale, oy + vy * scale, verts_a, ax, ay, 1.0):
            return True

    # Edge-edge intersection
    n_a, n_b = len(verts_a), len(verts_b)
    for i in range(n_a):
        a1x, a1y = ax + verts_a[i][0], ay + verts_a[i][1]
        a2x, a2y = ax + verts_a[(i + 1) % n_a][0], ay + verts_a[(i + 1) % n_a][1]
        for j in range(n_b):
            b1x, b1y = ox + verts_b[j][0] * scale, oy + verts_b[j][1] * scale
            b2x, b2y = ox + verts_b[(j + 1) % n_b][0] * scale, oy + verts_b[(j + 1) % n_b][1] * scale
            if _segments_intersect(a1x, a1y, a2x, a2y, b1x, b1y, b2x, b2y):
                return True
    return False

def rect_vs_tilemap(
    left: float,
    top: float,
    right: float,
    bottom: float,
    tile_map: Dict[Tuple[int, int], int],
    tileset_collision: TilesetCollision,
    tile_size: Tuple[int, int],
    render_scale: float = 1.0,
) -> bool:
    """Check if an AABB collides with any collision tile in a tile map.

    Iterates overlapping tiles, transforms each tile's collision polygons to
    world space, and tests for intersection with the given rectangle.

    Args:
        left, top, right, bottom: World-space AABB of the query rect.
        tile_map: Dict mapping (col, row) -> tile_variant_id.
        tileset_collision: TilesetCollision with per-tile polygon shapes.
        tile_size: Raw tile size as (width, height) from map data.
        render_scale: Multiplier from tile-local to world pixels.

    Returns:
        True if the rect overlaps any tile collision polygon.
    """
    tw = tile_size[0] * render_scale
    th = tile_size[1] * render_scale
    # Half-open rect [left, right): visit every tile the rect overlaps, including
    # a tile the right/bottom edge intrudes into by less than a pixel (a whole-
    # pixel subtraction would skip it for sub-pixel query rects).
    tx0 = math.floor(left / tw)
    tx1 = math.floor((right - 1e-9) / tw)
    ty0 = math.floor(top / th)
    ty1 = math.floor((bottom - 1e-9) / th)
    rw = right - left
    rh = bottom - top

    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            tile_id = tile_map.get((tx, ty))
            if tile_id is None:
                continue
            tile_data = tileset_collision.tiles.get(tile_id)
            if tile_data is None:
                continue
            ox = tx * tw
            oy = ty * th
            for poly in tile_data.shapes:
                if not poly.is_valid():
                    continue
                if _rect_polygon_collision_offset(left, top, rw, rh, poly.vertices, ox, oy, render_scale):
                    return True
    return False
