"""Grounded physics movement (move_grounded)."""

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
    Move sprite with basic grounded physics for simple entities.

    A lightweight alternative to ``move_platformer()`` and
    ``move_platformer_with_slide()`` for enemies and other
    entities that need tilemap collision without platformer
    features like jumping or slope walking.

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
    movement methods. With ``one_way="solid"`` (default) one-way
    platform polygons are treated as solid geometry (they block
    both X and Y movement). With ``one_way="directional"`` they
    behave platformer-style: horizontal movement passes through
    their sides, rising passes through from below, and falling
    lands only when approaching from above.

    Args:
        sprite: Sprite to move. Must expose ``x``, ``y``, ``vx``,
            ``vy``, ``on_ground``, and ``collision_shape``.
        tileset_collision: Tileset collision data. Optional when a world is
            attached (or passed as ``world=``) — resolved from it.
        tile_map: Dictionary mapping ``(tile_x, tile_y)`` to stacked
            ``((gid, flipbits), ...)`` entries (legacy integer and
            flat-tuple cells are normalized on the way in).
            Optional when a world is attached (or passed as ``world=``).
        dt: Frame delta time in seconds.
        velocity: Optional explicit ``(vx, vy)``. When provided
            the method skips gravity and uses this velocity directly
            instead of reading from ``sprite.vx``/``sprite.vy``.
            Useful for custom controllers, knockback, or flying
            entities that should not receive gravity.
        one_way: ``"solid"`` treats one-way polygons as solid walls
            and floors. ``"directional"`` lets horizontal and upward
            movement pass through them while falling still lands
            when approaching from above.

    Returns:
        :class:`CollisionResult` with final position and flags.
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

    # --- resolve velocity -----------------------------------------------
    if velocity is not None:
        sprite.vx = velocity[0]
        sprite.vy = velocity[1]
    else:
        if not was_on_ground:
            sprite.vy += self.gravity * dt
            sprite.vy = min(sprite.vy, self.max_fall_speed)

    delta_x = sprite.vx * dt
    delta_y = sprite.vy * dt

    # --- X axis ---------------------------------------------------------
    if delta_x != 0.0:
        sprite.x = old_x + delta_x
        sprite.y = old_y

        if self._collides_at(sprite, tileset_collision, tile_map, world=world, skip_one_way=directional):
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
        ground_below = self._collides_at(sprite, tileset_collision, tile_map, world=world)
        sprite.y = saved_y

        if not ground_below:
            sprite.on_ground = False
            was_on_ground = False

            # Begin falling immediately.
            sprite.vy += self.gravity * dt
            sprite.vy = min(sprite.vy, self.max_fall_speed)

            delta_y = sprite.vy * dt

    # --- Y axis ---------------------------------------------------------
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
            # Falling -> binary search for ground surface
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
            # Rising -> binary search for ceiling
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

