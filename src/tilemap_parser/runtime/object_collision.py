"""Deprecated re-export shim.

The runtime collision modules were split into the :mod:`movement`,
:mod:`collision`, :mod:`polygon_query`, and :mod:`protocols` submodules.
This module keeps old import paths working until the removal in 6.0.

Deprecated since 5.0 — import from the new locations instead:
``tilemap_parser.runtime.collision``.
"""

from __future__ import annotations

import warnings

from .collision.hit import (
    CollisionHit,
    _should_collide,
    check_collision,
    should_collide,
)
from .collision.manager import ObjectCollisionManager
from .protocols import ICollidableObject

__all__ = [
    "CollisionHit",
    "ICollidableObject",
    "ObjectCollisionManager",
    "_should_collide",
    "check_collision",
    "should_collide",
]

warnings.warn(
    "tilemap_parser.runtime.object_collision is deprecated and will be "
    "removed in 6.0; import from tilemap_parser.runtime.collision instead.",
    DeprecationWarning,
    stacklevel=2,
)
