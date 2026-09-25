"""Object-to-object collision package.

Shape-level narrowphase lives in :mod:`shapes`, hit results and pair
queries in :mod:`hit`, and the spatial-grid manager in :mod:`manager`.
"""

from .hit import CollisionHit, check_collision, should_collide
from .manager import ObjectCollisionManager
from .shapes import (
    describe_character_collision,
    describe_shape,
    describe_sprite,
    describe_tile_cell,
    describe_tile_collision,
    describe_tileset_collision,
    shape_to_points,
)

__all__ = [
    "CollisionHit",
    "ObjectCollisionManager",
    "check_collision",
    "describe_character_collision",
    "describe_shape",
    "describe_sprite",
    "describe_tile_cell",
    "describe_tile_collision",
    "describe_tileset_collision",
    "shape_to_points",
    "should_collide",
]
