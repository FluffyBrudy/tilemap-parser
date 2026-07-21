"""
Collision runner with ready-to-use movement modes for games.

Provides optimized collision detection and response for common game types:
- Slide: Smooth sliding along walls (top-down games)
- Platformer: Gravity-based movement with jump mechanics
- RPG: Grid-based or free movement with tile blocking

All runners work through a defined interface that any sprite class can implement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Protocol, Tuple, Union

from ..parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
    TilesetCollision,
)
from .protocols import ICollidable

Point = Tuple[float, float]
Vector2 = Tuple[float, float]


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


def point_in_polygon(point: Point, vertices: List[Point]) -> bool:
    """Check if point is inside polygon using ray casting (tile-local coordinates)."""
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

    # Vertex-in-rect
    for vx, vy in vertices:
        if rect_x <= vx <= rx2 and rect_y <= vy <= ry2:
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

    # Vertex-in-rect
    for vx, vy in vertices:
        wx, wy = vx * scale + ox, vy * scale + oy
        if rect_x <= wx <= rx2 and rect_y <= wy <= ry2:
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
    return False


class MovementMode(Enum):
    """Movement modes for collision runner"""

    SLIDE = "slide"
    PLATFORMER = "platformer"
    RPG = "rpg"


@dataclass
class CollisionResult:
    """Result of collision detection and resolution"""

    collided: bool = False
    final_x: float = 0.0
    final_y: float = 0.0
    hit_wall_x: bool = False
    hit_wall_y: bool = False
    hit_ceiling: bool = False
    on_ground: bool = False
    slide_vector: Optional[Vector2] = None


class CollisionRunner:
    """
    Ready-to-use collision runner with multiple movement modes.

    Handles collision detection and response for common game types.
    Works with any sprite class that implements ICollidableSprite interface.
    """

    def __init__(
        self,
        tile_size: Tuple[int, int] = (32, 32),
        mode: MovementMode = MovementMode.SLIDE,
        render_scale: float = 1.0,
    ):
        """
        Initialize collision runner.

        For most use cases, prefer using CollisionRunner.from_game_type() instead,
        which provides preset configurations for common game types.

        Args:
            tile_size: Size of tiles in pixels (width, height)
            mode: Movement mode (slide, platformer, rpg)
            render_scale: Visual scale factor for tile rendering (default 1.0)
        """
        self.tile_size = tile_size
        self.mode = mode
        if render_scale <= 0:
            raise ValueError(f"render_scale must be positive, got {render_scale}")
        self.render_scale = render_scale
        self._eff_tw = int(tile_size[0] * render_scale)
        self._eff_th = int(tile_size[1] * render_scale)

        self.gravity = 800.0
        self.max_fall_speed = 600.0
        self.jump_strength = -400.0
        self.horizontal_speed = 200.0

        self.ground_snap_tolerance = 2.0
        self.step_height = 4.0

        self.max_walk_angle = 60.0  # degrees from horizontal; steeper = wall

        self.slide_friction = 0.1

        self.rpg_snap_to_grid = False

        self._game_type: Optional[str] = None
        self._strict: bool = False

        # Reusable result object — reset fields before each use
        self._result = CollisionResult()

    def get_tile_at(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world position to tile coordinates"""
        tile_x = int(world_x // self._eff_tw)
        tile_y = int(world_y // self._eff_th)
        return (tile_x, tile_y)

    def get_tile_shapes(
        self,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        world_x: float,
        world_y: float,
    ) -> List[CollisionPolygon]:
        """Get collision shapes at world position"""
        tile_x, tile_y = self.get_tile_at(world_x, world_y)
        tile_id = tile_map.get((tile_x, tile_y))

        if tile_id is None or not tileset_collision.has_collision(tile_id):
            return []

        tile_world_x = tile_x * self._eff_tw
        tile_world_y = tile_y * self._eff_th

        return tileset_collision.get_world_shapes(
            tile_id, tile_world_x, tile_world_y, self.render_scale
        )

    def get_nearby_tile_shapes(
        self,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        sprite: ICollidable,
        margin: int = 1,
    ) -> List[CollisionPolygon]:
        """
        Get all world-space collision shapes near sprite.

        Returns transformed CollisionPolygon objects (world space).
        For internal movement use, the runner uses _collides_at() which avoids
        this allocation entirely.
        """
        left, top, right, bottom = get_shape_bounds(sprite)
        tw, th = self._eff_tw, self._eff_th

        min_tile_x = int(left // tw) - margin
        max_tile_x = int(right // tw) + margin
        min_tile_y = int(top // th) - margin
        max_tile_y = int(bottom // th) + margin

        shapes = []
        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile_id = tile_map.get((tile_x, tile_y))
                if tile_id is None:
                    continue
                tile_data = tileset_collision.tiles.get(tile_id)
                if tile_data is None:
                    continue
                tile_world_x = tile_x * tw
                tile_world_y = tile_y * th
                for poly in tile_data.shapes:
                    if poly.is_valid():
                        shapes.append(
                            poly.transform(
                                tile_world_x, tile_world_y, self.render_scale
                            )
                        )
        return shapes

    def _collides_at(
        self,
        sprite: ICollidable,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        margin: int = 1,
    ) -> bool:
        """
        Check if sprite collides with any tile at its current position.

        No allocation — iterates tiles and shapes directly, applies tile offset
        inline, exits immediately on first hit.
        """
        left, top, right, bottom = get_shape_bounds(sprite)
        tw, th = self._eff_tw, self._eff_th

        min_tile_x = int(left // tw) - margin
        max_tile_x = int(right // tw) + margin
        min_tile_y = int(top // th) - margin
        max_tile_y = int(bottom // th) + margin

        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile_id = tile_map.get((tile_x, tile_y))
                if tile_id is None:
                    continue
                tile_data = tileset_collision.tiles.get(tile_id)
                if tile_data is None:
                    continue
                ox = tile_x * tw
                oy = tile_y * th
                for poly in tile_data.shapes:
                    if poly.is_valid() and _check_sprite_polygon_offset(
                        sprite, poly, ox, oy, self.render_scale
                    ):
                        return True
        return False

    def _first_colliding_shape(
        self,
        sprite: ICollidable,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        margin: int = 1,
    ) -> Optional[Tuple[CollisionPolygon, float, float]]:
        """
        Return (polygon, tile_ox, tile_oy) for the first colliding shape, or None.
        Used by slope_slide to get the normal without allocating a full list.
        """
        left, top, right, bottom = get_shape_bounds(sprite)
        tw, th = self._eff_tw, self._eff_th

        min_tile_x = int(left // tw) - margin
        max_tile_x = int(right // tw) + margin
        min_tile_y = int(top // th) - margin
        max_tile_y = int(bottom // th) + margin

        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile_id = tile_map.get((tile_x, tile_y))
                if tile_id is None:
                    continue
                tile_data = tileset_collision.tiles.get(tile_id)
                if tile_data is None:
                    continue
                ox = tile_x * tw
                oy = tile_y * th
                for poly in tile_data.shapes:
                    if poly.is_valid() and _check_sprite_polygon_offset(
                        sprite, poly, ox, oy, self.render_scale
                    ):
                        return (poly, ox, oy)
        return None

    def move_and_slide(
        self,
        sprite: ICollidable,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        delta_x: float,
        delta_y: float,
        slope_slide: bool = False,
    ) -> CollisionResult:
        """
        Move sprite with sliding collision response.

        Best for top-down games where sprite should slide along walls.

        Args:
            sprite: Sprite to move (must implement ICollidableSprite)
            tileset_collision: Tileset collision data
            tile_map: Dictionary mapping (tile_x, tile_y) to tile_id
            delta_x: X movement amount
            delta_y: Y movement amount
            slope_slide: If True, allows sliding along slopes instead of blocking

        Returns:
            CollisionResult with final position and collision info
        """
        result = self._result
        result.collided = False
        result.hit_wall_x = False
        result.hit_wall_y = False
        result.hit_ceiling = False
        result.on_ground = False
        result.slide_vector = None
        result.final_x = sprite.x
        result.final_y = sprite.y

        if delta_x == 0 and delta_y == 0:
            return result

        old_x, old_y = sprite.x, sprite.y

        if slope_slide:
            max_slides = 4
            motion_x, motion_y = delta_x, delta_y

            for _ in range(max_slides):
                if abs(motion_x) < 0.01 and abs(motion_y) < 0.01:
                    break

                sprite.x = old_x + motion_x
                sprite.y = old_y + motion_y

                hit = self._first_colliding_shape(sprite, tileset_collision, tile_map)
                if hit is None:
                    result.final_x = sprite.x
                    result.final_y = sprite.y
                    return result

                sprite.x = old_x
                sprite.y = old_y
                result.collided = True

                poly, ox, oy = hit
                normal = self._get_collision_normal_from_motion(
                    sprite, poly, ox, oy, motion_x, motion_y, self.render_scale
                )
                if normal:
                    dot = motion_x * normal[0] + motion_y * normal[1]
                    if dot < 0:
                        motion_x -= normal[0] * dot
                        motion_y -= normal[1] * dot
                    else:
                        break
                else:
                    break

            result.final_x = sprite.x
            result.final_y = sprite.y
            return result

        # Non-slope: try full move first (fast path — no collision)
        sprite.x = old_x + delta_x
        sprite.y = old_y + delta_y
        if not self._collides_at(sprite, tileset_collision, tile_map):
            result.final_x = sprite.x
            result.final_y = sprite.y
            return result

        result.collided = True

        # X axis — spatially correct scan at the x-only position
        sprite.x = old_x + delta_x
        sprite.y = old_y
        x_collided = self._collides_at(sprite, tileset_collision, tile_map)
        if x_collided:
            sprite.x = old_x
            result.hit_wall_x = True

        # Y axis — spatially correct scan at the y-only position
        sprite.y = old_y + delta_y
        y_collided = self._collides_at(sprite, tileset_collision, tile_map)
        if y_collided:
            sprite.y = old_y
            result.hit_wall_y = True

        if not x_collided and not y_collided:
            if abs(delta_x) >= abs(delta_y):
                sprite.y = old_y
                y_collided = True
                result.hit_wall_y = True
                result.slide_vector = (delta_x, 0.0)
            else:
                sprite.x = old_x
                x_collided = True
                result.hit_wall_x = True
                result.slide_vector = (0.0, delta_y)

        result.final_x = sprite.x
        result.final_y = sprite.y

        if x_collided and not y_collided:
            result.slide_vector = (0.0, delta_y)
        elif y_collided and not x_collided:
            result.slide_vector = (delta_x, 0.0)

        return result

    def _get_collision_normal_from_motion(
        self,
        sprite: ICollidable,
        polygon: CollisionPolygon,
        ox: float,
        oy: float,
        motion_x: float,
        motion_y: float,
        scale: float = 1.0,
    ) -> Optional[Tuple[float, float]]:
        """
        Calculate the collision normal for a tile-local polygon at offset (ox, oy).
        Returns the outward normal of the edge most aligned against motion.
        """
        vertices = polygon.vertices
        n = len(vertices)
        if n < 2:
            return None

        # Compute polygon centroid, then translate to world space
        poly_cx = 0.0
        poly_cy = 0.0
        for vx, vy in vertices:
            poly_cx += vx * scale
            poly_cy += vy * scale
        poly_cx = ox + poly_cx / n
        poly_cy = oy + poly_cy / n

        best_edge = None
        best_alignment = -1.0

        for i in range(n):
            v1x, v1y = vertices[i][0] * scale + ox, vertices[i][1] * scale + oy
            v2x, v2y = (
                vertices[(i + 1) % n][0] * scale + ox,
                vertices[(i + 1) % n][1] * scale + oy,
            )

            edge_x = v2x - v1x
            edge_y = v2y - v1y
            edge_len = math.sqrt(edge_x * edge_x + edge_y * edge_y)
            if edge_len < 0.01:
                continue

            normal_x = -edge_y / edge_len
            normal_y = edge_x / edge_len

            edge_mid_x = (v1x + v2x) * 0.5
            edge_mid_y = (v1y + v2y) * 0.5
            to_outside_x = edge_mid_x - poly_cx
            to_outside_y = edge_mid_y - poly_cy

            if normal_x * to_outside_x + normal_y * to_outside_y < 0:
                normal_x = -normal_x
                normal_y = -normal_y

            alignment = -(motion_x * normal_x + motion_y * normal_y)
            if alignment > best_alignment and alignment > 0:
                best_alignment = alignment
                best_edge = (normal_x, normal_y)

        return best_edge

    def move_grounded(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        dt: float,
        velocity: Optional[Vector2] = None,
    ) -> CollisionResult:
        """
        Move sprite with basic grounded physics for simple entities.

        A lightweight alternative to ``move_platformer()`` and
        ``move_platformer_with_slide()`` for enemies and other
        entities that need tilemap collision without platformer
        features like jumping, one-way platforms, or slope walking.

        Key behaviours:

        * Applies gravity every frame when the sprite is not on the
          ground.
        * Resolves X collision (walls) by backing out the X axis and
          zeroing horizontal velocity.
        * Resolves Y collision via binary search so the sprite lands
          exactly on the polygon surface --- critical for **partial
          tiles** that only have collision in part of the tile (e.g.
          a 32x32 tile whose collision polygon only occupies the
          bottom 16 px).
        * Detects walk-off-ledge: when the sprite was on the ground
          and moves horizontally over empty space it is immediately
          set airborne.

        All collision uses the tile polygon shapes through the same
        zero-allocation ``_collides_at`` machinery as the other
        movement methods, so one-way platform polygons are treated
        as solid geometry (they block both X and Y movement).

        Args:
            sprite: Sprite to move. Must expose ``x``, ``y``, ``vx``,
                ``vy``, ``on_ground``, and ``collision_shape``.
            tileset_collision: Tileset collision data.
            tile_map: Dictionary mapping ``(tile_x, tile_y)`` to tile id.
            dt: Frame delta time in seconds.
            velocity: Optional explicit ``(vx, vy)``. When provided
                the method skips gravity and uses this velocity directly
                instead of reading from ``sprite.vx``/``sprite.vy``.
                Useful for custom controllers, knockback, or flying
                entities that should not receive gravity.

        Returns:
            :class:`CollisionResult` with final position and flags.
        """
        result = self._result
        result.collided = False
        result.hit_wall_x = False
        result.hit_wall_y = False
        result.hit_ceiling = False
        result.on_ground = False
        result.slide_vector = None
        result.final_x = sprite.x
        result.final_y = sprite.y

        old_x, old_y = sprite.x, sprite.y
        was_on_ground = getattr(sprite, "on_ground", False)

        # --- resolve velocity -----------------------------------------------
        if velocity is not None:
            sprite.vx = velocity[0]
            sprite.vy = velocity[1]
        else:
            if not was_on_ground:
                sprite.vy += self.gravity * dt
                if sprite.vy > self.max_fall_speed:
                    sprite.vy = self.max_fall_speed

        delta_x = sprite.vx * dt
        delta_y = sprite.vy * dt

        # --- X axis ---------------------------------------------------------
        if delta_x != 0.0:
            sprite.x = old_x + delta_x
            sprite.y = old_y

            if self._collides_at(sprite, tileset_collision, tile_map):
                sprite.x = old_x
                sprite.vx = 0.0
                result.hit_wall_x = True
                result.collided = True

        # --- ledge detection ------------------------------------------------
        # If the sprite was grounded and isn't actively falling, probe 1 px
        # downward at the *new* X position.  When nothing is underneath we
        # immediately leave the ground so gravity kicks in next frame.
        # Not applied when velocity is explicitly passed (caller controls Y).
        if velocity is None and was_on_ground and delta_y == 0.0:
            saved_y = sprite.y
            sprite.y += 1.0
            ground_below = self._collides_at(sprite, tileset_collision, tile_map)
            sprite.y = saved_y

            if not ground_below:
                sprite.on_ground = False
                was_on_ground = False

                # Begin falling immediately.
                sprite.vy += self.gravity * dt
                if sprite.vy > self.max_fall_speed:
                    sprite.vy = self.max_fall_speed

                delta_y = sprite.vy * dt

        # --- Y axis ---------------------------------------------------------
        sprite.y = sprite.y + delta_y

        collided_y = self._collides_at(sprite, tileset_collision, tile_map)

        if collided_y:
            result.collided = True

            if delta_y >= 0.0:
                # Falling -> binary search for ground surface
                sprite.y = old_y
                lo, hi = old_y, old_y + delta_y

                for _ in range(8):
                    mid = (lo + hi) * 0.5
                    sprite.y = mid

                    if self._collides_at(sprite, tileset_collision, tile_map):
                        hi = mid
                    else:
                        lo = mid

                sprite.y = lo
                sprite.vy = 0.0
                sprite.on_ground = True
                result.hit_wall_y = True
                result.on_ground = True

            else:
                # Rising -> binary search for ceiling
                sprite.y = old_y
                lo, hi = old_y + delta_y, old_y

                for _ in range(8):
                    mid = (lo + hi) * 0.5
                    sprite.y = mid

                    if self._collides_at(sprite, tileset_collision, tile_map):
                        lo = mid
                    else:
                        hi = mid

                sprite.y = hi
                sprite.vy = 0.0
                result.hit_ceiling = True

        elif delta_y > 0.0:
            sprite.on_ground = False

        result.final_x = sprite.x
        result.final_y = sprite.y
        result.on_ground = getattr(sprite, "on_ground", False)

        return result

    def move_platformer(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        dt: float,
        input_x: float = 0.0,
        jump_pressed: bool = False,
        velocity: Optional[Vector2] = None,
    ) -> CollisionResult:
        """
        Move sprite with platformer physics (gravity, jumping).

        Best for side-scrolling platformer games.

        Args:
            sprite: Sprite to move (must have vx, vy, on_ground attributes)
            tileset_collision: Tileset collision data
            tile_map: Dictionary mapping (tile_x, tile_y) to tile_id
            dt: Delta time in seconds
            input_x: Horizontal input (-1 to 1) for built-in movement
            jump_pressed: Whether jump button is pressed for built-in movement
            velocity: Optional explicit velocity (vx, vy). When provided, the
                runner skips built-in input/gravity/jump velocity calculation
                and only resolves collision for that velocity.

        Returns:
            CollisionResult with final position and collision info
        """
        result = self._result
        result.collided = False
        result.hit_wall_x = False
        result.hit_wall_y = False
        result.hit_ceiling = False
        result.on_ground = False
        result.slide_vector = None
        result.final_x = sprite.x
        result.final_y = sprite.y

        if velocity is not None:
            sprite.vx = velocity[0]
            sprite.vy = velocity[1]
        else:
            if not getattr(sprite, "on_ground", False):
                sprite.vy += self.gravity * dt
                if sprite.vy > self.max_fall_speed:
                    sprite.vy = self.max_fall_speed

            if jump_pressed and getattr(sprite, "on_ground", False):
                sprite.vy = self.jump_strength

            sprite.vx = input_x * self.horizontal_speed

        delta_x = sprite.vx * dt
        delta_y = sprite.vy * dt
        old_x, old_y = sprite.x, sprite.y
        _, _, _, old_bottom = get_shape_bounds(sprite)

        # X axis
        sprite.x = old_x + delta_x
        # Lift above ground snap overlap so ground doesn't block horizontal movement
        sprite.y = old_y - self.ground_snap_tolerance
        stepped_up = False
        if self._collides_at_platformer(
            sprite, tileset_collision, tile_map, include_one_way=False
        ):
            if delta_x != 0:
                # Try stepping up onto slope/stairs
                sprite.y = old_y - self.ground_snap_tolerance - self.step_height
                if not self._collides_at_platformer(
                    sprite, tileset_collision, tile_map, include_one_way=False
                ):
                    sprite.y = old_y - self.step_height
                    stepped_up = True
                else:
                    sprite.x = old_x
                    sprite.vx = 0.0
                    result.hit_wall_x = True
            else:
                sprite.x = old_x
                sprite.vx = 0.0
                result.hit_wall_x = True

        # Y axis — check one-way platforms
        if stepped_up:
            sprite.y = sprite.y + delta_y
        else:
            sprite.y = old_y + delta_y
        collided_y = False

        left, top, right, bottom = get_shape_bounds(sprite)
        tw, th = self._eff_tw, self._eff_th
        min_tile_x = int(left // tw) - 1
        max_tile_x = int(right // tw) + 1
        min_tile_y = int(top // th) - 1
        max_tile_y = int(bottom // th) + 1

        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile_id = tile_map.get((tile_x, tile_y))
                if tile_id is None:
                    continue
                tile_data = tileset_collision.tiles.get(tile_id)
                if tile_data is None:
                    continue
                ox = tile_x * tw
                oy = tile_y * th
                for poly in tile_data.shapes:
                    if not poly.is_valid():
                        continue
                    if not _check_sprite_polygon_offset(
                        sprite, poly, ox, oy, self.render_scale
                    ):
                        continue
                    if poly.one_way and sprite.vy > 0:
                        # one-way: only block if sprite was above the platform top
                        min_vy = (
                            min(v[1] for v in poly.vertices) * self.render_scale + oy
                        )
                        if old_y + (bottom - sprite.y) <= min_vy:
                            collided_y = True
                            break
                    elif not poly.one_way:
                        collided_y = True
                        break
                if collided_y:
                    break
            if collided_y:
                break

        if collided_y:
            if stepped_up:
                step_y = old_y - self.step_height
                lo, hi = step_y, old_y
                for _ in range(8):
                    mid = (lo + hi) * 0.5
                    sprite.y = mid
                    if self._collides_at_platformer(
                        sprite, tileset_collision, tile_map, include_one_way=False
                    ):
                        hi = mid
                    else:
                        lo = mid
                sprite.y = lo
                sprite.on_ground = True
                result.on_ground = True
            else:
                sprite.y = old_y
            if sprite.vy > 0:
                fall_y = sprite.vy * dt
                sprite.vy = 0.0
                sprite.on_ground = True
                result.on_ground = True
                lo, hi = old_y, old_y + fall_y
                for _ in range(8):
                    mid = (lo + hi) * 0.5
                    sprite.y = mid
                    if self._collides_at_platformer(
                        sprite,
                        tileset_collision,
                        tile_map,
                        include_one_way=True,
                        previous_bottom=old_bottom,
                    ):
                        hi = mid
                    else:
                        lo = mid
                sprite.y = lo
            elif sprite.vy < 0:
                sprite.vy = 0.0
                sprite.on_ground = False
                result.hit_ceiling = True
            else:
                sprite.on_ground = True
                result.on_ground = True
        else:
            sprite.on_ground = False

        downward_travel = max(0.0, sprite.vy) * dt
        if not sprite.on_ground and 0 <= downward_travel <= self.ground_snap_tolerance:
            if self._collides_at_platformer(
                sprite,
                tileset_collision,
                tile_map,
                include_one_way=True,
                previous_bottom=old_bottom,
            ):
                saved_y = sprite.y
                sprite.y = saved_y - self.ground_snap_tolerance
                if not self._collides_at_platformer(
                    sprite,
                    tileset_collision,
                    tile_map,
                    include_one_way=True,
                    previous_bottom=old_bottom,
                ):
                    lo, hi = sprite.y, saved_y
                    for _ in range(8):
                        mid = (lo + hi) * 0.5
                        sprite.y = mid
                        if self._collides_at_platformer(
                            sprite,
                            tileset_collision,
                            tile_map,
                            include_one_way=True,
                            previous_bottom=old_bottom,
                        ):
                            hi = mid
                        else:
                            lo = mid
                    sprite.y = lo
                else:
                    sprite.y = saved_y
                sprite.on_ground = True
                result.on_ground = True
                sprite.vy = 0.0
            else:
                saved_y = sprite.y
                sprite.y += self.ground_snap_tolerance
                if self._collides_at_platformer(
                    sprite,
                    tileset_collision,
                    tile_map,
                    include_one_way=True,
                    previous_bottom=old_bottom,
                ):
                    lo, hi = saved_y, sprite.y
                    for _ in range(8):
                        mid = (lo + hi) * 0.5
                        sprite.y = mid
                        if self._collides_at_platformer(
                            sprite,
                            tileset_collision,
                            tile_map,
                            include_one_way=True,
                            previous_bottom=old_bottom,
                        ):
                            hi = mid
                        else:
                            lo = mid
                    sprite.y = lo
                    sprite.on_ground = True
                    result.on_ground = True
                    sprite.vy = 0.0
                else:
                    sprite.y = saved_y

        result.final_x = sprite.x
        result.final_y = sprite.y
        result.collided = result.hit_wall_x or collided_y
        return result

    def _walkable_slope_at(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        motion_x: float,
        motion_y: float,
        walk_upness: float,
    ) -> Optional[float]:
        """Check if there is a walkable slope at the sprite's current position.
        Iterates all overlapping tiles and picks the best walkable edge.
        Returns the Y offset to apply, or None if not a walkable slope.
        """
        left, top, right, bottom = get_shape_bounds(sprite)
        tw, th = self._eff_tw, self._eff_th
        min_tile_x = int(left // tw) - 1
        max_tile_x = int(right // tw) + 1
        min_tile_y = int(top // th) - 1
        max_tile_y = int(bottom // th) + 1

        best_adj_y = None

        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile_id = tile_map.get((tile_x, tile_y))
                if tile_id is None:
                    continue
                tile_data = tileset_collision.tiles.get(tile_id)
                if tile_data is None:
                    continue
                ox = tile_x * tw
                oy = tile_y * th
                for poly in tile_data.shapes:
                    if not poly.is_valid():
                        continue
                    if self._is_full_rect(poly):
                        continue
                    if not _check_sprite_polygon_offset(
                        sprite, poly, ox, oy, self.render_scale
                    ):
                        continue

                    # Non-full-rect polygon overlapping the sprite — find the best edge.
                    verts = poly.vertices
                    n = len(verts)
                    cx = sum(verts[j][0] for j in range(n)) / n * self.render_scale + ox
                    cy = sum(verts[j][1] for j in range(n)) / n * self.render_scale + oy
                    for i in range(n):
                        v1x = verts[i][0] * self.render_scale + ox
                        v1y = verts[i][1] * self.render_scale + oy
                        v2x = verts[(i + 1) % n][0] * self.render_scale + ox
                        v2y = verts[(i + 1) % n][1] * self.render_scale + oy

                        ex = v2x - v1x
                        ey = v2y - v1y
                        e_len = math.sqrt(ex * ex + ey * ey)
                        if e_len < 0.01:
                            continue

                        # Two perpendicular normals
                        nx_a = -ey / e_len
                        ny_a = ex / e_len
                        nx_b = -nx_a
                        ny_b = -ny_a

                        # Pick the one pointing INTO the solid (toward polygon interior).
                        # Use the polygon centroid to determine which side is interior.
                        mx = (v1x + v2x) * 0.5
                        my = (v1y + v2y) * 0.5
                        to_centroid_x = cx - mx
                        to_centroid_y = cy - my
                        if nx_a * to_centroid_x + ny_a * to_centroid_y < 0:
                            nx_a = -nx_a
                            ny_a = -ny_a
                            nx_b = -nx_b
                            ny_b = -ny_b

                        # nx_a/ny_a now points away from centroid (outward).
                        # nx_b/ny_b points toward centroid (inward) = into the solid.

                        # For a walkable surface, the inward normal should push the
                        # player UP (negative screen y when inward is upward).
                        # Inward normal = (nx_b, ny_b) = (-nx_a, -ny_a).
                        # "Upward" in the inward sense means the y-component of
                        # inward normal is negative (pointing up on screen).
                        inward_up = -ny_b  # inward normal y component, negated
                        # Actually: for a floor, inward normal = (0, 1) pointing DOWN.
                        # -inward_y = -1, which is wrong.
                        # Better: just use the outward normal's upness.
                        # Outward normal = (nx_a, ny_a).
                        # For a floor, outward = (0, -1). upness = -(-1) = 1. ✓
                        # For this diagonal, outward = ? Let ny_a determine outward.

                        outward_ny = ny_a
                        upness = -outward_ny
                        if upness < walk_upness:
                            continue

                        # Check motion is INTO the surface (dot with outward normal < 0).
                        out_nx = nx_a
                        out_ny = ny_a
                        dot = motion_x * out_nx + motion_y * out_ny
                        if dot >= 0:
                            continue

                        # Project motion along the slope surface.
                        adj_x = motion_x - out_nx * dot
                        adj_y = motion_y - out_ny * dot
                        dy_off = adj_y - motion_y
                        if best_adj_y is None or dy_off > best_adj_y:
                            best_adj_y = dy_off

        if best_adj_y is not None:
            return best_adj_y
        return None

    def _is_full_rect(self, poly: CollisionPolygon) -> bool:
        """Check if a polygon is a full-tile rectangle."""
        if len(poly.vertices) != 4:
            return False
        verts = [
            (vx * self.render_scale, vy * self.render_scale) for vx, vy in poly.vertices
        ]
        min_x = min(v[0] for v in verts)
        max_x = max(v[0] for v in verts)
        min_y = min(v[1] for v in verts)
        max_y = max(v[1] for v in verts)
        return (
            abs(max_x - min_x - self._eff_tw) < 1.0
            and abs(max_y - min_y - self._eff_th) < 1.0
        )

    def _collides_at_platformer(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        include_one_way: bool = False,
        previous_bottom: Optional[float] = None,
    ) -> bool:
        """Collision query for platformers, with one-way platforms gated by approach."""
        left, top, right, bottom = get_shape_bounds(sprite)
        tw, th = self._eff_tw, self._eff_th

        min_tile_x = int(left // tw) - 1
        max_tile_x = int(right // tw) + 1
        min_tile_y = int(top // th) - 1
        max_tile_y = int(bottom // th) + 1

        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile_id = tile_map.get((tile_x, tile_y))
                if tile_id is None:
                    continue
                tile_data = tileset_collision.tiles.get(tile_id)
                if tile_data is None:
                    continue
                ox = tile_x * tw
                oy = tile_y * th
                for poly in tile_data.shapes:
                    if not poly.is_valid():
                        continue
                    if poly.one_way:
                        if not include_one_way:
                            continue
                        platform_y = (
                            min(v[1] for v in poly.vertices) * self.render_scale + oy
                        )
                        if (
                            previous_bottom is not None
                            and previous_bottom > platform_y + 0.5
                        ):
                            continue
                    if _check_sprite_polygon_offset(
                        sprite, poly, ox, oy, self.render_scale
                    ):
                        return True
        return False

    def _walkable_edge_y_at_x(
        self,
        poly: CollisionPolygon,
        ox: float,
        oy: float,
        world_x: float,
        edge_index: int,
        min_upness: float,
    ) -> Optional[float]:
        """Return the world Y for a walkable polygon edge at world_x."""
        verts = poly.vertices
        n = len(verts)
        v1x = verts[edge_index][0] * self.render_scale + ox
        v1y = verts[edge_index][1] * self.render_scale + oy
        v2x = verts[(edge_index + 1) % n][0] * self.render_scale + ox
        v2y = verts[(edge_index + 1) % n][1] * self.render_scale + oy

        min_x = min(v1x, v2x)
        max_x = max(v1x, v2x)
        if world_x < min_x - 0.01 or world_x > max_x + 0.01:
            return None

        edge_x = v2x - v1x
        edge_y = v2y - v1y
        edge_len = math.sqrt(edge_x * edge_x + edge_y * edge_y)
        if edge_len < 0.01:
            return None

        # Vertical faces are walls, never floors.
        if abs(edge_x) < 0.01:
            return None

        normal_x = -edge_y / edge_len
        normal_y = edge_x / edge_len

        cx = sum(v[0] for v in verts) / n * self.render_scale + ox
        cy = sum(v[1] for v in verts) / n * self.render_scale + oy
        mid_x = (v1x + v2x) * 0.5
        mid_y = (v1y + v2y) * 0.5

        # Flip to outward normal when the candidate points toward the centroid.
        if normal_x * (cx - mid_x) + normal_y * (cy - mid_y) > 0:
            normal_x = -normal_x
            normal_y = -normal_y

        upness = -normal_y
        if upness < min_upness:
            return None

        t = (world_x - v1x) / edge_x
        return v1y + (v2y - v1y) * t

    def _find_walkable_ground_y(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        max_up: float,
        max_down: float,
        include_one_way: bool = True,
        previous_bottom: Optional[float] = None,
    ) -> Optional[float]:
        """Find the nearest walkable floor surface under or just above the sprite."""
        left, top, right, bottom = get_shape_bounds(sprite)
        sample_xs = (left, (left + right) * 0.5, right)

        tw, th = self._eff_tw, self._eff_th
        min_tile_x = int((left - 1.0) // tw) - 1
        max_tile_x = int((right + 1.0) // tw) + 1
        min_tile_y = int((bottom - max_up - th) // th) - 1
        max_tile_y = int((bottom + max_down + th) // th) + 1
        min_upness = math.cos(math.radians(self.max_walk_angle))

        best_y: Optional[float] = None
        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile_id = tile_map.get((tile_x, tile_y))
                if tile_id is None:
                    continue
                tile_data = tileset_collision.tiles.get(tile_id)
                if tile_data is None:
                    continue
                ox = tile_x * tw
                oy = tile_y * th
                for poly in tile_data.shapes:
                    if not poly.is_valid():
                        continue
                    if poly.one_way and not include_one_way:
                        continue
                    for sample_x in sample_xs:
                        for i in range(len(poly.vertices)):
                            ground_y = self._walkable_edge_y_at_x(
                                poly, ox, oy, sample_x, i, min_upness
                            )
                            if ground_y is None:
                                continue
                            one_way_from_above = True
                            if poly.one_way and previous_bottom is not None:
                                one_way_from_above = previous_bottom <= ground_y + 0.5
                            if not one_way_from_above:
                                continue
                            if bottom - max_up <= ground_y <= bottom + max_down:
                                if best_y is None or ground_y < best_y:
                                    best_y = ground_y
        return best_y

    def move_platformer_with_slide(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        dt: float,
        input_x: float = 0.0,
        jump_pressed: bool = False,
        velocity: Optional[Vector2] = None,
    ) -> CollisionResult:
        """
        Slope-aware platformer movement.

        Supports:
        - gravity and jumping
        - one-way platforms
        - walkable slopes
        - stair stepping
        - smooth ground following

        Unlike move_platformer(), this mode follows polygon floor
        surfaces and prevents steep slopes from being treated as
        walkable terrain.

        Args:
            sprite:
                Sprite being simulated. Expected to provide position,
                velocity, and ground state attributes.

            tileset_collision:
                Collision definitions for tiles in the map.

            tile_map:
                Mapping of (tile_x, tile_y) coordinates to tile identifiers.

            dt:
                Frame delta time in seconds.

            input_x:
                Horizontal movement input, typically in the range [-1, 1].

            jump_pressed:
                True if jump was pressed during this frame.

            velocity:
                Optional explicit velocity (vx, vy). When provided, the runner
                skips built-in input/gravity/jump velocity calculation and only
                resolves collision for that velocity. This is the preferred
                path for dash, knockback, wind, moving-platform carry, or a
                custom controller.

        Returns:
            CollisionResult describing the resolved movement and collision
            state after simulation.
        """

        result = self._result
        result.collided = False
        result.hit_wall_x = False
        result.hit_wall_y = False
        result.hit_ceiling = False
        result.on_ground = False
        result.slide_vector = None
        result.final_x = sprite.x
        result.final_y = sprite.y

        skin = 0.01
        old_x, old_y = sprite.x, sprite.y
        _, _, _, old_bottom = get_shape_bounds(sprite)
        was_on_ground = getattr(sprite, "on_ground", False)
        jumped = False

        if velocity is not None:
            sprite.vx = velocity[0]
            sprite.vy = velocity[1]
            if sprite.vy < 0.0:
                sprite.on_ground = False
                jumped = True
        else:
            if jump_pressed and was_on_ground:
                sprite.vy = self.jump_strength
                sprite.on_ground = False
                jumped = True
            elif not was_on_ground:
                sprite.vy += self.gravity * dt
                if sprite.vy > self.max_fall_speed:
                    sprite.vy = self.max_fall_speed
            else:
                sprite.vy = min(sprite.vy, 0.0)

            sprite.vx = input_x * self.horizontal_speed
        delta_x = sprite.vx * dt
        delta_y = sprite.vy * dt
        bottom_offset = old_bottom - old_y

        slope_follow = abs(delta_x) * math.tan(math.radians(self.max_walk_angle))
        max_ground_up = max(self.step_height, slope_follow + skin)
        max_ground_down = max(self.ground_snap_tolerance, slope_follow + skin)

        # Horizontal movement first. Grounded sprites are allowed to follow
        # walkable floor contours, but only when a jump did not start this frame.
        if delta_x != 0.0:
            sprite.x = old_x + delta_x
            sprite.y = old_y

            followed_ground = False
            if was_on_ground and not jumped:
                ground_y = self._find_walkable_ground_y(
                    sprite,
                    tileset_collision,
                    tile_map,
                    max_up=max_ground_up,
                    max_down=max_ground_down,
                    include_one_way=True,
                    previous_bottom=old_bottom,
                )
                if ground_y is not None:
                    sprite.y = ground_y - bottom_offset - skin
                    followed_ground = True

            if self._collides_at_platformer(
                sprite, tileset_collision, tile_map, include_one_way=False
            ):
                sprite.x = old_x + delta_x
                sprite.y = old_y - self.step_height
                step_ground_y = self._find_walkable_ground_y(
                    sprite,
                    tileset_collision,
                    tile_map,
                    max_up=self.step_height + skin,
                    max_down=self.step_height + skin,
                    include_one_way=False,
                    previous_bottom=old_bottom,
                )
                if step_ground_y is not None:
                    sprite.y = step_ground_y - bottom_offset - skin
                if step_ground_y is None or self._collides_at_platformer(
                    sprite, tileset_collision, tile_map, include_one_way=False
                ):
                    sprite.x = old_x
                    sprite.y = old_y
                    sprite.vx = 0.0
                    result.collided = True
                    result.hit_wall_x = True
                else:
                    followed_ground = True

            if followed_ground:
                sprite.on_ground = True
                result.on_ground = True
        else:
            sprite.x = old_x
            sprite.y = old_y

        y_before_vertical = sprite.y
        _, _, _, previous_bottom = get_shape_bounds(sprite)

        if jumped or sprite.vy < 0.0:
            sprite.y = y_before_vertical + delta_y
            if self._collides_at_platformer(
                sprite, tileset_collision, tile_map, include_one_way=False
            ):
                lo = y_before_vertical + delta_y
                hi = y_before_vertical
                for _ in range(10):
                    mid = (lo + hi) * 0.5
                    sprite.y = mid
                    if self._collides_at_platformer(
                        sprite, tileset_collision, tile_map, include_one_way=False
                    ):
                        lo = mid
                    else:
                        hi = mid
                sprite.y = hi
                sprite.vy = 0.0
                sprite.on_ground = False
                result.collided = True
                result.hit_ceiling = True
            else:
                sprite.on_ground = False
        elif sprite.vy > 0.0:
            sprite.y = y_before_vertical + delta_y
            ground_y = self._find_walkable_ground_y(
                sprite,
                tileset_collision,
                tile_map,
                max_up=abs(delta_y) + max_ground_up,
                max_down=skin,
                include_one_way=True,
                previous_bottom=previous_bottom,
            )
            if ground_y is not None:
                sprite.y = ground_y - bottom_offset - skin
                sprite.vy = 0.0
                sprite.on_ground = True
                result.on_ground = True
                result.collided = True
                result.hit_wall_y = True
            elif self._collides_at_platformer(
                sprite,
                tileset_collision,
                tile_map,
                include_one_way=True,
                previous_bottom=previous_bottom,
            ):
                lo = y_before_vertical
                hi = y_before_vertical + delta_y
                for _ in range(10):
                    mid = (lo + hi) * 0.5
                    sprite.y = mid
                    if self._collides_at_platformer(
                        sprite,
                        tileset_collision,
                        tile_map,
                        include_one_way=True,
                        previous_bottom=previous_bottom,
                    ):
                        hi = mid
                    else:
                        lo = mid
                sprite.y = lo
                sprite.vy = 0.0
                sprite.on_ground = True
                result.on_ground = True
                result.collided = True
                result.hit_wall_y = True
            else:
                sprite.on_ground = False
        elif not jumped:
            ground_y = self._find_walkable_ground_y(
                sprite,
                tileset_collision,
                tile_map,
                max_up=max_ground_up,
                max_down=max_ground_down,
                include_one_way=True,
                previous_bottom=previous_bottom,
            )
            if ground_y is not None:
                sprite.y = ground_y - bottom_offset - skin
                sprite.vy = 0.0
                sprite.on_ground = True
                result.on_ground = True
            else:
                sprite.on_ground = False

        result.final_x = sprite.x
        result.final_y = sprite.y
        result.on_ground = getattr(sprite, "on_ground", False)
        return result

    def move_rpg(
        self,
        sprite: ICollidable,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        delta_x: float,
        delta_y: float,
    ) -> CollisionResult:
        """
        Move sprite with RPG-style blocking (no sliding).

        Best for grid-based RPG games where movement is blocked by walls.

        Args:
            sprite: Sprite to move
            tileset_collision: Tileset collision data
            tile_map: Dictionary mapping (tile_x, tile_y) to tile_id
            delta_x: X movement amount
            delta_y: Y movement amount

        Returns:
            CollisionResult with final position and collision info
        """
        result = self._result
        result.collided = False
        result.hit_wall_x = False
        result.hit_wall_y = False
        result.hit_ceiling = False
        result.on_ground = False
        result.slide_vector = None
        result.final_x = sprite.x
        result.final_y = sprite.y

        if delta_x == 0 and delta_y == 0:
            return result

        old_x, old_y = sprite.x, sprite.y
        sprite.x = old_x + delta_x
        sprite.y = old_y + delta_y

        if self._collides_at(sprite, tileset_collision, tile_map):
            sprite.x = old_x
            sprite.y = old_y
            result.collided = True

            x_blocked = False
            y_blocked = False
            if delta_x != 0:
                sprite.x = old_x + delta_x
                sprite.y = old_y
                x_blocked = self._collides_at(sprite, tileset_collision, tile_map)
            if delta_y != 0:
                sprite.x = old_x
                sprite.y = old_y + delta_y
                y_blocked = self._collides_at(sprite, tileset_collision, tile_map)
            sprite.x = old_x
            sprite.y = old_y

            if not x_blocked and not y_blocked:
                x_blocked = delta_x != 0
                y_blocked = delta_y != 0
            result.hit_wall_x = x_blocked
            result.hit_wall_y = y_blocked
        else:
            result.final_x = sprite.x
            result.final_y = sprite.y

        return result

    def move(
        self,
        sprite: ICollidable,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        delta_x: float = 0.0,
        delta_y: float = 0.0,
        dt: float = 0.016,
        **kwargs,
    ) -> CollisionResult:
        """
        Move sprite using configured movement mode.

        This is a convenience method that calls the appropriate movement function
        based on the runner's mode.

        Args:
            sprite: Sprite to move
            tileset_collision: Tileset collision data
            tile_map: Dictionary mapping (tile_x, tile_y) to tile_id
            delta_x: X movement amount (for slide/rpg modes)
            delta_y: Y movement amount (for slide/rpg modes)
            dt: Delta time in seconds (for platformer mode)
            **kwargs: Additional mode-specific arguments

        Returns:
            CollisionResult with final position and collision info
        """
        if self.mode == MovementMode.SLIDE:
            return self.move_and_slide(
                sprite, tileset_collision, tile_map, delta_x, delta_y
            )
        elif self.mode == MovementMode.PLATFORMER:
            return self.move_platformer(
                sprite,
                tileset_collision,
                tile_map,
                dt,
                input_x=kwargs.get("input_x", 0.0),
                jump_pressed=kwargs.get("jump_pressed", False),
                velocity=kwargs.get("velocity"),
            )
        elif self.mode == MovementMode.RPG:
            return self.move_rpg(sprite, tileset_collision, tile_map, delta_x, delta_y)

        return CollisionResult(final_x=sprite.x, final_y=sprite.y)

    @classmethod
    def from_game_type(
        cls,
        game_type: str,
        tile_size: Tuple[int, int] = (32, 32),
        strict: bool = False,
        render_scale: float = 1.0,
    ) -> "CollisionRunner":
        """
        Create a collision runner with preset configuration for a specific game type.

        This is the recommended way to create a collision runner for common game types.
        Provides sensible defaults that can be customized after creation.

        Game Types:
            'platformer': Side-scrolling platformer with gravity and jumping
                - Gravity: 800 px/s²
                - Max fall speed: 600 px/s
                - Jump strength: -400 px/s (negative = upward)
                - Mode: PLATFORMER
                - Requires sprite attributes: x, y, vx, vy, on_ground, collision_shape

            'topdown': Overhead view with free 8-directional movement
                - No gravity (gravity = 0)
                - Slides along walls smoothly
                - Mode: SLIDE
                - Requires sprite attributes: x, y, collision_shape

            'rpg': Grid-based or free movement with full blocking
                - No gravity (gravity = 0)
                - Stops at walls (no sliding)
                - Mode: RPG
                - Requires sprite attributes: x, y, collision_shape

        Args:
            game_type: Type of game ('platformer', 'topdown', or 'rpg')
            tile_size: Size of tiles in pixels (width, height)
            strict: If True, raises exceptions on warnings. If False, only warns.

        Returns:
            CollisionRunner configured for the specified game type

        Raises:
            ValueError: If game_type is not recognized

        Examples:
            >>>
            >>> runner = CollisionRunner.from_game_type('platformer', (32, 32))
            >>> result = runner.move(player, tileset, tile_map, dt=0.016)

            >>>
            >>> runner = CollisionRunner.from_game_type('topdown', (16, 16))
            >>> runner.slide_friction = 0.2
            >>> result = runner.move(player, tileset, tile_map, delta_x=dx, delta_y=dy)

            >>>
            >>> runner = CollisionRunner.from_game_type('rpg', (32, 32), strict=True)
            >>> runner.validate_config()
        """
        game_type = game_type.lower()

        if game_type == "platformer":
            runner = cls(
                tile_size, mode=MovementMode.PLATFORMER, render_scale=render_scale
            )
            runner.gravity = 800.0
            runner.max_fall_speed = 600.0
            runner.jump_strength = -400.0
            runner.horizontal_speed = 200.0
            runner.slide_friction = 0.1
            runner._game_type = "platformer"
            runner._strict = strict

        elif game_type == "topdown":
            runner = cls(tile_size, mode=MovementMode.SLIDE, render_scale=render_scale)
            runner.gravity = 0.0
            runner.max_fall_speed = 0.0
            runner.jump_strength = 0.0
            runner.slide_friction = 0.1
            runner._game_type = "topdown"
            runner._strict = strict

        elif game_type == "rpg":
            runner = cls(tile_size, mode=MovementMode.RPG, render_scale=render_scale)
            runner.gravity = 0.0
            runner.max_fall_speed = 0.0
            runner.jump_strength = 0.0
            runner.slide_friction = 0.0
            runner.rpg_snap_to_grid = False
            runner._game_type = "rpg"
            runner._strict = strict

        else:
            raise ValueError(
                f"Unknown game_type: '{game_type}'. "
                f"Valid options are: 'platformer', 'topdown', 'rpg'"
            )

        runner.validate_config()

        return runner

    def validate_config(self, strict: Optional[bool] = None) -> None:
        """
        Validate the current configuration for consistency and correctness.

        This method checks for common configuration mistakes and inconsistencies.
        Called automatically when using from_game_type(), but can also be called
        manually after changing configuration properties.

        Validation Rules:
            - Platformer mode requires gravity > 0
            - Top-down and RPG modes should have gravity = 0
            - Physics values must be in valid ranges
            - Mode must match game_type expectations

        Args:
            strict: If True, raises exceptions on warnings. If False, only warns.
                   If None, uses the strict setting from initialization.

        Raises:
            ValueError: If critical configuration errors are found
            Warning: If suspicious but valid configurations are detected (strict=False)

        Examples:
            >>> runner = CollisionRunner.from_game_type('platformer', cache, (32, 32))
            >>> runner.gravity = 0.0
            >>> runner.validate_config()

            >>> runner = CollisionRunner.from_game_type('topdown', cache, (32, 32))
            >>> runner.gravity = 800.0
            >>> runner.validate_config(strict=False)
        """
        import warnings

        if strict is None:
            strict = getattr(self, "_strict", False)

        game_type = getattr(self, "_game_type", None)
        errors = []
        warnings_list = []

        if self.gravity < 0:
            errors.append("gravity must be >= 0 (negative gravity not supported)")

        if self.max_fall_speed < 0:
            errors.append("max_fall_speed must be >= 0")

        if self.jump_strength > 0:
            warnings_list.append(
                "jump_strength is positive (upward force should be negative). "
                "Did you mean a negative value?"
            )

        if not (0.0 <= self.slide_friction <= 1.0):
            warnings_list.append(
                f"slide_friction={self.slide_friction} is outside typical range [0.0, 1.0]"
            )

        if self.mode == MovementMode.PLATFORMER:
            if self.gravity == 0:
                errors.append(
                    "PLATFORMER mode requires gravity > 0 for jumping mechanics.\n"
                    "  Fix: Set runner.gravity = 800.0 (or another positive value)\n"
                    "  Or: Use game_type='topdown' or 'rpg' instead"
                )

            if self.max_fall_speed == 0 and self.gravity > 0:
                warnings_list.append(
                    "PLATFORMER mode with gravity > 0 but max_fall_speed = 0. "
                    "Falling speed will be unlimited."
                )

        elif self.mode == MovementMode.SLIDE:
            if self.gravity > 0:
                warnings_list.append(
                    "SLIDE mode (top-down) typically uses gravity = 0. "
                    f"Current gravity = {self.gravity} will be ignored in move_and_slide()."
                )

        elif self.mode == MovementMode.RPG:
            if self.gravity > 0:
                errors.append(
                    "RPG mode should not use gravity (set gravity = 0).\n"
                    "  Fix: Set runner.gravity = 0.0\n"
                    "  Or: Use game_type='platformer' if you need gravity"
                )

        if game_type:
            if game_type == "platformer" and self.mode != MovementMode.PLATFORMER:
                warnings_list.append(
                    f"game_type='platformer' but mode={self.mode.value}. "
                    "This may cause unexpected behavior."
                )

            if game_type == "topdown" and self.mode != MovementMode.SLIDE:
                warnings_list.append(
                    f"game_type='topdown' but mode={self.mode.value}. "
                    "This may cause unexpected behavior."
                )

            if game_type == "rpg" and self.mode != MovementMode.RPG:
                warnings_list.append(
                    f"game_type='rpg' but mode={self.mode.value}. "
                    "This may cause unexpected behavior."
                )

            if game_type in ["topdown", "rpg"] and self.gravity > 0:
                warnings_list.append(
                    f"game_type='{game_type}' typically uses gravity=0, "
                    f"but current gravity={self.gravity}"
                )

        if errors:
            error_msg = "Configuration validation failed:\n\n"
            for i, err in enumerate(errors, 1):
                error_msg += f"{i}. {err}\n"

            if game_type:
                error_msg += f"\nCurrent configuration:\n"
                error_msg += f"  game_type: {game_type}\n"
                error_msg += f"  mode: {self.mode.value}\n"
                error_msg += f"  gravity: {self.gravity}\n"
                error_msg += f"  max_fall_speed: {self.max_fall_speed}\n"
                error_msg += f"  jump_strength: {self.jump_strength}\n"

            raise ValueError(error_msg)

        if warnings_list:
            warning_msg = "Configuration warnings detected:\n\n"
            for i, warn in enumerate(warnings_list, 1):
                warning_msg += f"{i}. {warn}\n"

            if game_type:
                warning_msg += f"\nCurrent configuration:\n"
                warning_msg += f"  game_type: {game_type}\n"
                warning_msg += f"  mode: {self.mode.value}\n"
                warning_msg += f"  gravity: {self.gravity}\n"

            if strict:
                raise ValueError(warning_msg)
            else:
                warnings.warn(warning_msg, UserWarning, stacklevel=2)


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
    tx0 = math.floor(left / tw)
    tx1 = math.floor((right - 1) / tw)
    ty0 = math.floor(top / th)
    ty1 = math.floor((bottom - 1) / th)
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
