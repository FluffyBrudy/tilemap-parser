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
class GroundInfo:
    """Walkable supporting surface selected by the ground query.

    Single source of truth derived from the actual supporting polygon
    edge (``edge -> normal -> angle``). The normal is authoritative;
    ``angle`` is derived from it.

    Attributes:
        y: World Y of the supporting surface at the sampled foot X.
        normal: Outward unit normal ``(nx, ny)`` of the supporting edge.
            For tile edges this is the polygon outward normal; for
            bodies the existing conservative ``(0.0, -1.0)`` is used
            (no new circle/capsule slope semantics).
        angle: Raw geometric angle in degrees. ``0.0`` = flat,
            positive = surface rises toward ``+X``, negative = falls
            toward ``+X`` (screen coords, ``+Y`` down). No flat
            threshold is applied — consumers classify.
    """

    y: float = 0.0
    normal: Vector2 = (0.0, -1.0)
    angle: float = 0.0


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
    ground_angle: float | None = None
    ground_normal: Vector2 | None = None
