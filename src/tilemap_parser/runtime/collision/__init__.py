"""Object-to-object collision package.

Shape-level narrowphase lives in :mod:`shapes`, hit results and pair
queries in :mod:`hit`, and the spatial-grid manager in :mod:`manager`.
"""

from .hit import CollisionHit, check_collision, should_collide
from .manager import ObjectCollisionManager

__all__ = ["CollisionHit", "ObjectCollisionManager", "check_collision", "should_collide"]
