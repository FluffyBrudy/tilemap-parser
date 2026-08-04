"""Deprecated re-export shim.

The runtime collision modules were split into the :mod:`movement`,
:mod:`collision`, :mod:`polygon_query`, and :mod:`protocols` submodules.
This module keeps old import paths working until the removal in 6.0.

Deprecated since 5.0 — import from the new locations instead:
``tilemap_parser.runtime.movement``, ``tilemap_parser.runtime.collision``,
``tilemap_parser.runtime.polygon_query``.
"""

from __future__ import annotations

import warnings

from .movement.runner import CollisionRunner
from .movement.types import CollisionResult, MovementMode, Vector2
from .polygon_query import (
    Point,
    _check_sprite_polygon_offset,
    _circle_polygon_collision_offset,
    _point_in_polygon_offset,
    _rect_polygon_collision_offset,
    _segments_intersect,
    check_sprite_polygon_collision,
    circle_polygon_collision,
    get_shape_bounds,
    point_in_polygon,
    rect_polygon_collision,
    rect_vs_tilemap,
)
from .protocols import ICollidable, ICollidableObject, ICollidableSprite

__all__ = [
    "CollisionResult",
    "CollisionRunner",
    "ICollidable",
    "ICollidableObject",
    "ICollidableSprite",
    "MovementMode",
    "Point",
    "Vector2",
    "_check_sprite_polygon_offset",
    "_circle_polygon_collision_offset",
    "_point_in_polygon_offset",
    "_rect_polygon_collision_offset",
    "_segments_intersect",
    "check_sprite_polygon_collision",
    "circle_polygon_collision",
    "get_shape_bounds",
    "point_in_polygon",
    "rect_polygon_collision",
    "rect_vs_tilemap",
]

warnings.warn(
    "tilemap_parser.runtime.tile_collision is deprecated and will be removed "
    "in 6.0; import from tilemap_parser.runtime.movement / "
    "tilemap_parser.runtime.polygon_query instead.",
    DeprecationWarning,
    stacklevel=2,
)
