from __future__ import annotations

from typing import Literal

from ...parser.collision import TilesetCollision
from ..polygon_query import get_shape_bounds
from ..protocols import ICollidableSprite
from ..world import PhysicsWorld
from .types import CollisionResult, Vector2


def move_grounded(
    self,
    sprite: ICollidableSprite,
    tileset_collision: TilesetCollision | None,
    tile_map: dict[tuple[int, int], object] | None,
    dt: float,
    velocity: Vector2 | None = None,
    world: PhysicsWorld | None = None,
    one_way: Literal["solid", "directional"] = "solid",
) -> CollisionResult:
    """
    Lightweight grounded physics: gravity, X walls, Y binary-search
    landing (exact on partial tiles), walk-off-ledge detection.
    ``one_way="solid"`` treats one-way polygons as solid walls and
    floors; ``"directional"`` passes horizontal/upward movement through
    them while falling lands from above. Explicit ``velocity=`` skips
    gravity and uses the given velocity directly.
    """
    world = self._resolve_world(world)
    if world is not None:
        tileset_collision = world.tileset_collision
        tile_map = world.tile_map
    if one_way not in ("solid", "directional"):
        raise ValueError(f"one_way must be 'solid' or 'directional', got {one_way!r}")
    directional = one_way == "directional"

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

    old_x, old_y = sprite.x, sprite.y
    was_on_ground = getattr(sprite, "on_ground", False)
    _, _, _, old_bottom = get_shape_bounds(sprite)

    if velocity is not None:
        sprite.vx = velocity[0]
        sprite.vy = velocity[1]
    else:
        if not was_on_ground:
            sprite.vy += self.gravity * dt
            sprite.vy = min(sprite.vy, self.max_fall_speed)

    delta_x = sprite.vx * dt
    delta_y = sprite.vy * dt

    if delta_x != 0.0:
        sprite.x = old_x + delta_x
        sprite.y = old_y

        if self._collides_at(sprite, tileset_collision, tile_map, world=world, skip_one_way=directional):
            sprite.x = old_x
            sprite.vx = 0.0
            result.hit_wall_x = True
            result.collided = True

    # Probe 1 px down at the new X when grounded and not falling; leaving
    # the ground makes gravity kick in next frame. Skipped with velocity=.
    if velocity is None and was_on_ground and delta_y == 0.0:
        saved_y = sprite.y
        sprite.y += 1.0
        ground_below = self._collides_at(sprite, tileset_collision, tile_map, world=world)
        sprite.y = saved_y

        if not ground_below:
            sprite.on_ground = False
            was_on_ground = False

            sprite.vy += self.gravity * dt
            sprite.vy = min(sprite.vy, self.max_fall_speed)

            delta_y = sprite.vy * dt

    sprite.y = sprite.y + delta_y

    if directional:
        if delta_y >= 0.0:
            collided_y = self._collides_at_platformer(
                sprite, tileset_collision, tile_map,
                include_one_way=True, previous_bottom=old_bottom, world=world,
            )
        else:
            collided_y = self._collides_at_platformer(
                sprite, tileset_collision, tile_map, include_one_way=False, world=world
            )
    else:
        collided_y = self._collides_at(sprite, tileset_collision, tile_map, world=world)

    if collided_y:
        result.collided = True

        if delta_y >= 0.0:
            sprite.y = old_y
            lo, hi = old_y, old_y + delta_y

            for _ in range(8):
                mid = (lo + hi) * 0.5
                sprite.y = mid

                if directional:
                    hit = self._collides_at_platformer(
                        sprite, tileset_collision, tile_map,
                        include_one_way=True, previous_bottom=old_bottom, world=world,
                    )
                else:
                    hit = self._collides_at(sprite, tileset_collision, tile_map, world=world)
                if hit:
                    hi = mid
                else:
                    lo = mid

            sprite.y = lo
            sprite.vy = 0.0
            sprite.on_ground = True
            result.hit_wall_y = True
            result.on_ground = True

        else:
            sprite.y = old_y
            lo, hi = old_y + delta_y, old_y

            for _ in range(8):
                mid = (lo + hi) * 0.5
                sprite.y = mid

                if directional:
                    hit = self._collides_at_platformer(
                        sprite, tileset_collision, tile_map, include_one_way=False, world=world
                    )
                else:
                    hit = self._collides_at(sprite, tileset_collision, tile_map, world=world)
                if hit:
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

