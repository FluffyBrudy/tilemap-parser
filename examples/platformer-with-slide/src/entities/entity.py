from typing import Dict, List, Tuple

from src.ttypes.index import TCharacterShape

from pygame import Rect, Surface
import pygame

from tilemap_parser import (
    AnimationPlayer,
    ICollidableSprite,
    SpriteAnimationSet,
    get_shape_aabb,
)

from .fsm import BaseFsm


class Entity(ICollidableSprite):
    def __init__(
        self,
        x: float,
        y: float,
        collision_shape: TCharacterShape,
        animation_states: Dict[str, AnimationPlayer],
        states: Dict[str, BaseFsm],
        shape_bounds: Dict[str, Rect],
    ) -> None:
        """assumption: animation file have same exact keys"""
        if len(states) == 0:
            raise ValueError("required at least one state")

        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.collision_shape = collision_shape
        self.on_ground = True

        self.input_x = 0
        self.jump_pressed = False
        self.flipped = False

        self.animation_states = animation_states
        self.current_state = states[next(iter(states))]
        self.states = states

        self._shape_bounds = shape_bounds

    @classmethod
    def _load_shape_bound(cls, keys: List[str], animation_set: "SpriteAnimationSet"):
        bounds: Dict[str, Rect] = {}
        for name in keys:
            bound_rect = animation_set.get_content_bounds(name)
            if bound_rect is None:
                raise ValueError(
                    "Potential mismatch in animation state, unable to load bound"
                )
            bounds[name] = bound_rect
        return bounds

    def update(self, dt: float):
        self.manage_state()
        self.animation_states[self.current_state.name].update(dt * 1000)

    def transition_state(self, new_state):
        if self.current_state.name != new_state:
            self.current_state.exit(self)
            self.current_state = self.states[new_state]
            self.current_state.enter(self)
            self.animation_states[new_state].reset()

    def manage_state(self):
        next_state = self.current_state.get_next_state(self)
        if next_state is not None:
            self.transition_state(next_state)
        self.current_state.update(self)

    def render(self, surface: Surface, offset: Tuple[float | int, float | int]):
        current_frame = (
            self.animation_states[self.current_state.name]
            .get_current_image()
            .subsurface(self._shape_bounds[self.current_state.name])  # type: ignore
        )
        left, _, right, bottom = get_shape_aabb(self.x, self.y, self.collision_shape)
        pos = current_frame.get_rect(  # type: ignore
            midbottom=((left + right) * 0.5 - offset[0], bottom + 10 - offset[1])
        )
        if self.flipped:
            current_frame = pygame.transform.flip(current_frame, True, False)  # type: ignore
        surface.blit(current_frame, pos)  # type: ignore
