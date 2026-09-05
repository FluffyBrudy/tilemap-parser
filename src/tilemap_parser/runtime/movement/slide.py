"""Top-down sliding movement (move_and_slide)."""

from __future__ import annotations

import math

from ...parser.collision import CollisionPolygon, TilesetCollision
from ..protocols import ICollidable
from ..world import PhysicsWorld
from .types import CollisionResult


def move_and_slide(
    self,
    sprite: ICollidable,
    tileset_collision: TilesetCollision | None,
    tile_map: dict[tuple[int, int], int] | None,
    delta_x: float,
    delta_y: float,
    slope_slide: bool = False,
    world: PhysicsWorld | None = None,
) -> CollisionResult:
    """
    Move sprite with sliding collision response.

    Best for top-down games where sprite should slide along walls.

    Args:
        sprite: Sprite to move (must implement ICollidableSprite)
        tileset_collision: Tileset collision data. Optional when a world is
            attached (or passed as ``world=``) — resolved from it.
        tile_map: Dictionary mapping (tile_x, tile_y) to tile_id. Optional
            when a world is attached (or passed as ``world=``).
        delta_x: X movement amount
        delta_y: Y movement amount
        slope_slide: If True, allows sliding along slopes instead of blocking

    Returns:
        CollisionResult with final position and collision info
    """
    world = self._resolve_world(world)
    if world is not None:
        tileset_collision = world.tileset_collision
        tile_map = world.tile_map

    result = self._result
    result.collided = False
    result.hit_wall_x = False
    result.hit_wall_y = False
    result.hit_ceiling = False
    result.on_ground = False
    result.slide_vector = None
    result.ground_angle = None
    result.ground_normal = None
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

            hit = self._first_colliding_shape(sprite, tileset_collision, tile_map, world=world)
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
    if not self._collides_at(sprite, tileset_collision, tile_map, world=world):
        result.final_x = sprite.x
        result.final_y = sprite.y
        return result

    result.collided = True

    # X axis — spatially correct scan at the x-only position
    sprite.x = old_x + delta_x
    sprite.y = old_y
    x_collided = self._collides_at(sprite, tileset_collision, tile_map, world=world)
    if x_collided:
        sprite.x = old_x
        result.hit_wall_x = True

    # Y axis — spatially correct scan at the y-only position
    sprite.y = old_y + delta_y
    y_collided = self._collides_at(sprite, tileset_collision, tile_map, world=world)
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
) -> tuple[float, float] | None:
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

