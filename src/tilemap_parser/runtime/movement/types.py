from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

Vector2 = tuple[float, float]


class MovementMode(Enum):

    SLIDE = "slide"
    GROUNDED = "grounded"
    PLATFORMER = "platformer"
    RPG = "rpg"


@dataclass
class GroundInfo:
    """Supporting-surface Y, outward normal, derived angle.

    Normal wins; ``angle`` follows it: ``0.0`` = flat, positive rises
    toward ``+X`` (screen coords, ``+Y`` down). Bodies read flat
    ``(0.0, -1.0)`` / ``0.0``.
    """

    y: float = 0.0
    normal: Vector2 = (0.0, -1.0)
    angle: float = 0.0


@dataclass
class CollisionResult:

    collided: bool = False
    final_x: float = 0.0
    final_y: float = 0.0
    hit_wall_x: bool = False
    hit_wall_y: bool = False
    hit_ceiling: bool = False
    on_ground: bool = False
    slide_vector: Vector2 | None = None
    ground_angle: float | None = None
    ground_normal: Vector2 | None = None
