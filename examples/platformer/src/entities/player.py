from typing import TYPE_CHECKING, Tuple, Dict
from pathlib import Path
from pygame import Surface, key, transform
from pygame.constants import K_SPACE, K_UP, K_LEFT, K_RIGHT

from ..debug import pgdebug
from ..fsm.base import FsmBase
from tilemap_parser import AnimationPlayer

from tilemap_parser.runtime.animation_player import SpriteAnimationSet
from tilemap_parser.utils.geometry import get_shape_aabb

if TYPE_CHECKING:
    from tilemap_parser.parser.collision import (
        CapsuleShape,
        CircleShape,
        RectangleShape,
    )


class Player:
    def __init__(
        self,
        pos: Tuple[float | int, float | int],
        shape: "RectangleShape | CircleShape | CapsuleShape",
        animation_path: Path,
    ) -> None:
        self.vx = self.vy = 0.0
        self.x = pos[0]
        self.y = pos[1]
        self.collision_shape = shape
        self.on_ground = False

        self.input_x = 0
        self.jump_pressed = False
        self.facing = False
        self.is_attacking = False

        states: Dict[str, FsmBase] = {
            "idle": IdleFsm("idle"),
            "walk": WalkFsm("walk"),
            "jump": JumpFsm("jump"),
            "attack": AttackFsm("attack"),
        }
        default_state = "idle"
        self.current_state = states[default_state]
        self.states = states
        animation_lib = SpriteAnimationSet.load(animation_path)
        self.animation_states = {
            "jump": AnimationPlayer(animation_lib, "jump"),
            "idle": AnimationPlayer(animation_lib, "idle"),
            "walk": AnimationPlayer(animation_lib, "walk"),
            "attack": AnimationPlayer(animation_lib, "attack"),
            "dash": AnimationPlayer(animation_lib, "dash"),
            "hurt": AnimationPlayer(animation_lib, "hurt"),
            "death": AnimationPlayer(animation_lib, "hurt"),
        }
        self._shape_bound = self._load_shape_bound(animation_lib)

    def _load_shape_bound(self, animation_set):
        states = {}
        for name in self.animation_states:
            states[name] = animation_set.get_content_bounds(name)
        return states

    def update(self, dt: float):
        self.handle_input()
        self.manage_state()
        self.animation_states[self.current_state.name].update(dt * 1000)

    def transition_state(self, state_key: str):
        if self.current_state.name != state_key:
            self.current_state.exit(self)
            self.current_state = self.states[state_key]
            self.current_state.enter(self)
            self.animation_states[state_key].reset()

    def manage_state(self):
        next_state = self.current_state.get_next_state(self)
        if next_state is not None:
            self.transition_state(next_state)
        self.current_state.update(self)

    def handle_input(self):
        pressed_key = key.get_pressed()
        if pressed_key[K_UP]:
            self.jump_pressed = True
        if pressed_key[K_SPACE]:
            self.is_attacking = True
        if pressed_key[K_LEFT]:
            self.input_x = -1
            self.facing = True
        elif pressed_key[K_RIGHT]:
            self.input_x = 1
            self.facing = False
        else:
            self.input_x = 0

    def render(self, surface: Surface, offset: Tuple[float, float]):
        pgdebug(
            f"velocity=({round(self.vx), round(self.vy)}), state=${self.current_state.name}"
        )
        frame = (
            self.animation_states[self.current_state.name]
            .get_current_image()
            .subsurface(self._shape_bound[self.current_state.name])  # type: ignore
        )
        left, _, right, bottom = get_shape_aabb(self.x, self.y, self.collision_shape)
        frame_rect = frame.get_rect(midbottom=((left + right) * 0.5 - offset[0], bottom - offset[1]))  # type: ignore
        if self.facing:
            frame = transform.flip(frame, True, False)

        surface.blit(frame, frame_rect)  # type: ignore


class IdleFsm(FsmBase["Player"]):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def get_next_state(self, entity: Player, /, **kwargs) -> None | str:
        if entity.is_attacking:
            return "attack"
        if entity.jump_pressed and entity.on_ground:
            return "jump"
        if abs(entity.vx) > 0:
            return "walk"

        return None


class WalkFsm(FsmBase["Player"]):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def get_next_state(self, entity: Player, /, **kwargs) -> None | str:
        if entity.is_attacking:
            return "attack"
        if abs(entity.vx) == 0:
            return "idle"
        if not entity.on_ground:
            return "jump"

        return None


class JumpFsm(FsmBase["Player"]):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def get_next_state(self, entity: Player, /, **kwargs) -> None | str:
        if entity.is_attacking:
            return "attack"
        if entity.on_ground:
            return "idle"

        return None

    def exit(self, entity: Player) -> None:
        entity.jump_pressed = False


class AttackFsm(FsmBase["Player"]):
    def enter(self, entity: Player) -> None:
        entity.animation_states[self.name].reset()

    def get_next_state(self, entity: Player, /, **kwargs) -> None | str:
        if entity.animation_states[self.name].finished:
            entity.is_attacking = False
            if not entity.on_ground:
                return "jump"
            else:
                return "idle"

    def update(self, entity: Player) -> None:
        entity.vx = 0
        entity.input_x = 0
