"""RPG grid blocking movement (move_rpg)."""

from __future__ import annotations

from ...parser.collision import TilesetCollision
from ..protocols import ICollidable
from ..world import PhysicsWorld
from .types import CollisionResult


def move_rpg(
    self,
    sprite: ICollidable,
    tileset_collision: TilesetCollision | None,
    tile_map: dict[tuple[int, int], int] | None,
    delta_x: float,
    delta_y: float,
    world: PhysicsWorld | None = None,
) -> CollisionResult:
    """
    Move sprite with RPG-style blocking (no sliding).

    Best for grid-based RPG games where movement is blocked by walls.

    Args:
        sprite: Sprite to move
        tileset_collision: Tileset collision data. Optional when a world is
            attached (or passed as ``world=``) — resolved from it.
        tile_map: Dictionary mapping (tile_x, tile_y) to tile_id. Optional
            when a world is attached (or passed as ``world=``).
        delta_x: X movement amount
        delta_y: Y movement amount

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

    if delta_x == 0 and delta_y == 0:
        return result

    old_x, old_y = sprite.x, sprite.y
    sprite.x = old_x + delta_x
    sprite.y = old_y + delta_y

    if self._collides_at(sprite, tileset_collision, tile_map, world=world):
        sprite.x = old_x
        sprite.y = old_y
        result.collided = True

        x_blocked = False
        y_blocked = False
        if delta_x != 0:
            sprite.x = old_x + delta_x
            sprite.y = old_y
            x_blocked = self._collides_at(sprite, tileset_collision, tile_map, world=world)
        if delta_y != 0:
            sprite.x = old_x
            sprite.y = old_y + delta_y
            y_blocked = self._collides_at(sprite, tileset_collision, tile_map, world=world)
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

