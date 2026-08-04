"""Movement types shared by the collision runner."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

Vector2 = tuple[float, float]

class MovementMode(Enum):
    """Movement modes for collision runner"""

    SLIDE = "slide"
    GROUNDED = "grounded"
    PLATFORMER = "platformer"
    RPG = "rpg"

@dataclass
class CollisionResult:
    """Result of collision detection and resolution"""

    collided: bool = False
    final_x: float = 0.0
    final_y: float = 0.0
    hit_wall_x: bool = False
    hit_wall_y: bool = False
    hit_ceiling: bool = False
    on_ground: bool = False
    slide_vector: Vector2 | None = None

