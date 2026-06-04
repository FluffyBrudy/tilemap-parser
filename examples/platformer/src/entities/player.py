from pathlib import Path
from typing import TYPE_CHECKING, Tuple

from pygame import Surface
from tilemap_parser import AnimationPlayer

from tilemap_parser.runtime.animation_player import SpriteAnimationSet

if TYPE_CHECKING:
    from tilemap_parser.parser.collision import CharacterShapeType


class Player:
    def __init__(
        self,
        pos: Tuple[float, float],
        shape: "CharacterShapeType",
        animation_path: Path,
    ) -> None:
        self.vx = self.vy = 0.0
        self.x = pos[0]
        self.y = pos[1]
        self.collision_shape = shape
        self.on_ground = False

        animation_lib = SpriteAnimationSet.load(animation_path)

        self.current_state = "idle"
        self.animation_states = {
            "idle": AnimationPlayer(animation_lib, "idle"),
            "run": AnimationPlayer(animation_lib, "idle"),
        }

    def render(self, surface: Surface):
        frame = self.animation_states[self.current_state].get_current_image()
        surface.blit(frame, (self.x, self.y))  # type: ignore
