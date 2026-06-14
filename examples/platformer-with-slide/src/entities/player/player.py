from typing import Optional, Tuple

import pygame

from tilemap_parser import (
    AnimationPlayer,
    SpriteAnimationSet,
)
from tilemap_parser.runtime.collision_cache import _global_cache
from src.ttypes.index import TCharacterShape
from src.settings import *
from ..fsm import BaseFsm
from ..entity import Entity
from src.utils.debug import pgdebug


class Player(Entity):
    def __init__(
        self,
        x: float,
        y: float,
    ) -> None:
        character_info = _global_cache.get_character_collision(
            CHARACTER_COLLISION_PATH / "player-idle-character.collision.json"
        )
        animation_set = SpriteAnimationSet.load(ANIMATION_PATH / "player.anim.json")
        animation_keys = list(animation_set.library.animations.keys())
        shape_bounds = self._load_shape_bound(animation_keys, animation_set)
        animation_states = {
            k: AnimationPlayer(animation_set, k) for k in animation_keys
        }
        states = {
            "idle": IdleFsm("idle"),
            "run": RunFsm("run"),
            "jump": JumpFsm("jump"),
            "dash": DashFsm("dash"),
        }

        super().__init__(
            x, y, character_info.shape, animation_states, states, shape_bounds  # type: ignore
        )

        self.is_attacking = False
        self.dashing = False

        self.velocity_override: Optional[Tuple[float, float]] = None

    def handle_movemet(self):
        keys = pygame.key.get_pressed()
        if not self.dashing and keys[pygame.K_SPACE]:
            self.dashing = True
        else:
            if keys[pygame.K_UP]:
                self.jump_pressed = True
            if keys[pygame.K_LEFT]:
                self.input_x = -1
                self.flipped = True
            elif keys[pygame.K_RIGHT]:
                self.input_x = 1
                self.flipped = False
            else:
                self.input_x = 0

    def update(self, dt: float):
        self.handle_movemet()
        super().update(dt)
        pgdebug(f"{self.current_state.name}, ${self.input_x}")

    def can_jump(self):
        return self.jump_pressed and self.on_ground


class IdleFsm(BaseFsm):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def enter(self, entity: "Player") -> None:
        entity.vx = 0
        entity.vy = 0

    def get_next_state(self, entity: "Player") -> str | None:
        if entity.is_attacking:
            return "attack"
        if entity.dashing:
            return "dash"
        if abs(entity.vx) > 0.001:
            return "run"
        if entity.can_jump():
            return "jump"
        return None


class RunFsm(BaseFsm):
    def __init__(self, name: str):
        super().__init__(name)

    def get_next_state(self, entity: "Player") -> str | None:
        if entity.is_attacking:
            return "attack"
        if entity.dashing:
            return "dash"
        if abs(entity.vx) == 0:
            return "idle"
        if entity.can_jump():
            return "jump"
        return None


class JumpFsm(BaseFsm):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def enter(self, entity: "Player") -> None:
        entity.jump_pressed = False

    def get_next_state(self, entity: "Player") -> str | None:
        if entity.dashing:
            return "dash"
        if entity.on_ground:
            return "idle"
        return None


class DashFsm(BaseFsm):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def exit(self, entity: "Player"):
        entity.velocity_override = None
        entity.dashing = False

    def get_next_state(self, entity: "Player") -> str | None:
        if entity.animation_states[entity.current_state.name].finished:
            if entity.on_ground:
                return "idle"
            else:
                return "jump"
        return None

    def update(self, entity: "Player") -> None:
        direction = 1 - entity.flipped * 2
        entity.velocity_override = (direction * 1500, 0)
