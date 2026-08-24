"""Platformer movement (the stable core)."""

from __future__ import annotations

import math

from ...parser.collision import TilesetCollision
from ..polygon_query import _check_sprite_polygon_offset, get_shape_bounds
from ..protocols import ICollidableSprite
from ..world import PhysicsWorld
from .queries import _resolve_tile_data
from .types import CollisionResult, Vector2


def move_platformer(
    self,
    sprite: ICollidableSprite,
    tileset_collision: TilesetCollision | None,
    tile_map: dict[tuple[int, int], int] | None,
    dt: float,
    input_x: float = 0.0,
    jump_pressed: bool = False,
    velocity: Vector2 | None = None,
    world: PhysicsWorld | None = None,
) -> CollisionResult:
    """
    Move sprite with platformer physics (gravity, jumping).

    Best for side-scrolling platformer games.

    Args:
        sprite: Sprite to move (must have vx, vy, on_ground attributes)
        tileset_collision: Tileset collision data. Optional when a world is
            attached (or passed as ``world=``) — resolved from it.
        tile_map: Dictionary mapping (tile_x, tile_y) to tile_id. Optional
            when a world is attached (or passed as ``world=``).
        dt: Delta time in seconds
        input_x: Horizontal input (-1 to 1) for built-in movement
        jump_pressed: Whether jump button is pressed for built-in movement
        velocity: Optional explicit velocity (vx, vy). When provided, the
            runner skips built-in input/gravity/jump velocity calculation
            and only resolves collision for that velocity.

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
    result.final_x = sprite.x
    result.final_y = sprite.y

    if velocity is not None:
        sprite.vx = velocity[0]
        sprite.vy = velocity[1]
    else:
        if not getattr(sprite, "on_ground", False):
            sprite.vy += self.gravity * dt
            sprite.vy = min(sprite.vy, self.max_fall_speed)

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
        sprite, tileset_collision, tile_map, include_one_way=False, world=world
    ):
        if delta_x != 0:
            # Try stepping up onto slope/stairs
            sprite.y = old_y - self.ground_snap_tolerance - self.step_height
            if not self._collides_at_platformer(
                sprite, tileset_collision, tile_map, include_one_way=False, world=world
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
            tile_data = _resolve_tile_data(world, tileset_collision, tile_id)
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

    if not collided_y and world is not None and world.collides_with_body(sprite):
        collided_y = True

    if collided_y:
        if stepped_up:
            step_y = old_y - self.step_height
            lo, hi = step_y, old_y
            for _ in range(8):
                mid = (lo + hi) * 0.5
                sprite.y = mid
                if self._collides_at_platformer(
                    sprite, tileset_collision, tile_map, include_one_way=False, world=world
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
                    previous_bottom=old_bottom, world=world
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
            previous_bottom=old_bottom, world=world
        ):
            saved_y = sprite.y
            sprite.y = saved_y - self.ground_snap_tolerance
            if not self._collides_at_platformer(
                sprite,
                tileset_collision,
                tile_map,
                include_one_way=True,
                previous_bottom=old_bottom, world=world
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
                        previous_bottom=old_bottom, world=world
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
                previous_bottom=old_bottom, world=world
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
                        previous_bottom=old_bottom, world=world
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

def move_platformer_with_slide(
    self,
    sprite: ICollidableSprite,
    tileset_collision: TilesetCollision | None,
    tile_map: dict[tuple[int, int], int] | None,
    dt: float,
    input_x: float = 0.0,
    jump_pressed: bool = False,
    velocity: Vector2 | None = None,
    world: PhysicsWorld | None = None,
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
            Collision definitions for tiles in the map. Optional when a
            world is attached (or passed as ``world=``) — resolved from it.

        tile_map:
            Mapping of (tile_x, tile_y) coordinates to tile identifiers.
            Optional when a world is attached (or passed as ``world=``).

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
            sprite.vy = min(sprite.vy, self.max_fall_speed)
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
                previous_bottom=old_bottom, world=world
            )
            if ground_y is not None:
                sprite.y = ground_y - bottom_offset - skin
                followed_ground = True

        if self._collides_at_platformer(
            sprite, tileset_collision, tile_map, include_one_way=False, world=world
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
                previous_bottom=old_bottom, world=world
            )
            if step_ground_y is not None:
                sprite.y = step_ground_y - bottom_offset - skin
            if step_ground_y is None or self._collides_at_platformer(
                sprite, tileset_collision, tile_map, include_one_way=False, world=world
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
            sprite, tileset_collision, tile_map, include_one_way=False, world=world
        ):
            lo = y_before_vertical + delta_y
            hi = y_before_vertical
            for _ in range(10):
                mid = (lo + hi) * 0.5
                sprite.y = mid
                if self._collides_at_platformer(
                    sprite, tileset_collision, tile_map, include_one_way=False, world=world
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
            previous_bottom=previous_bottom, world=world
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
            previous_bottom=previous_bottom, world=world
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
                    previous_bottom=previous_bottom, world=world
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
            previous_bottom=previous_bottom, world=world
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

