"""Movement resolution package.

The public :class:`CollisionRunner` composes its movement implementations
from the sibling modules (slide, grounded, platformer, rpg, queries) —
the runner remains the single public surface.
"""

from .runner import CollisionRunner
from .types import CollisionResult, GroundInfo, MovementMode

__all__ = ["CollisionResult", "CollisionRunner", "GroundInfo", "MovementMode"]
