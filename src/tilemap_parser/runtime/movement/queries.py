"""Tile solid queries composed into the collision runner."""

from __future__ import annotations

import math

from ...parser.collision import CollisionPolygon, TilesetCollision
from ..collision.hit import should_collide
from ..polygon_query import _check_sprite_polygon_offset, get_shape_bounds
from ..protocols import ICollidable, ICollidableSprite


def _collides_at(
    self,
    sprite: ICollidable,
    tileset_collision: TilesetCollision,
    tile_map: dict,
    margin: int = 1,
    world=None,
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
    return world is not None and world.collides_with_body(sprite) is not None

def _first_colliding_shape(
    self,
    sprite: ICollidable,
    tileset_collision: TilesetCollision,
    tile_map: dict,
    margin: int = 1,
    world=None,
) -> tuple[CollisionPolygon, float, float] | None:
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
    if world is not None:
        body = world.collides_with_body(sprite)
        if body is not None:
            # as_polygon() is already world-space; the caller applies
            # `v * scale + ox` to tile-local polygons, so offset is zero.
            return (body.as_polygon(), 0.0, 0.0)
    return None

def _collides_at_platformer(
    self,
    sprite: ICollidableSprite,
    tileset_collision: TilesetCollision,
    tile_map: dict,
    include_one_way: bool = False,
    previous_bottom: float | None = None,
    world=None,
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
    return world is not None and world.collides_with_body(sprite) is not None

def _walkable_edge_y_at_x(
    self,
    poly: CollisionPolygon,
    ox: float,
    oy: float,
    world_x: float,
    edge_index: int,
    min_upness: float,
) -> float | None:
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
    previous_bottom: float | None = None,
    world=None,
) -> float | None:
    """Find the nearest walkable floor surface under or just above the sprite."""
    left, _, right, bottom = get_shape_bounds(sprite)
    sample_xs = (left, (left + right) * 0.5, right)

    tw, th = self._eff_tw, self._eff_th
    min_tile_x = int((left - 1.0) // tw) - 1
    max_tile_x = int((right + 1.0) // tw) + 1
    min_tile_y = int((bottom - max_up - th) // th) - 1
    max_tile_y = int((bottom + max_down + th) // th) + 1
    min_upness = math.cos(math.radians(self.max_walk_angle))

    best_y: float | None = None
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
                        if (bottom - max_up <= ground_y <= bottom + max_down) and (
                            best_y is None or ground_y < best_y
                        ):
                            best_y = ground_y
    if world is not None:
        for body in world.bodies:
            if body is sprite:
                continue
            if not should_collide(sprite, body):
                continue
            for sample_x in sample_xs:
                ground_y = body.top_y_at(sample_x)
                if ground_y is None:
                    continue
                if not bottom - max_up <= ground_y <= bottom + max_down:
                    continue
                if best_y is None or ground_y < best_y:
                    best_y = ground_y
    return best_y

