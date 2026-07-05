from typing import Optional, Tuple

import pygame
from tilemap_parser import CollisionHit, ICollidableSprite, get_shape_aabb
from tilemap_parser.runtime.collision_cache import _global_cache

from src.settings import *
from src.utils.pgdebug import pgdebug
from src.utils.shape import get_sprite_center

from ..entity import Entity
from ..fsm import BaseFsm
from ..projectiles.bullet import Bullet


class Player(Entity, ICollidableSprite):
    def __init__(self, x: float, y: float) -> None:
        collision = _global_cache.get_character_collision(
            CHARACTER_COLLISION_PATH / "player.collision.json",
        )
        if collision is None:
            raise ValueError("Unable to load player collision")

        super().__init__(
            x,
            y,
            collision,
            ANIMATION_PATH / "player.anim.json",
            {
                "idle": IdleFsm("idle"),
                "run": RunFsm("run"),
                "jump": JumpFsm("jump"),
                "hurt": HurtFsm("hurt"),
            },
        )
        self.on_ground = True
        self.input_x = 0
        self.jump_pressed = False
        self.velocity_override: Optional[Tuple[float, float]] = None
        self.hit_result: Optional[CollisionHit] = None

        self.is_shooting = False
        self.is_hitted = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and self.on_ground:
            self.jump_pressed = True
        if keys[pygame.K_LEFT]:
            self.input_x = -1
            self.flipped = True
        elif keys[pygame.K_RIGHT]:
            self.input_x = 1
            self.flipped = False
        else:
            self.input_x = 0

    def shoot_bullet(self):
        bullet_x, bullet_y = get_sprite_center(self)
        direction = -1 if self.flipped else 1
        Bullet.add_bullet(Bullet(bullet_x, bullet_y, (300 + abs(self.vx)) * direction))

    def update(self, dt: float):
        pgdebug(f"{self.current_state.name}, is_hit={self.is_hitted}")
        self.handle_input()
        super().update(dt)

    def render(self, surface: pygame.Surface, offset: Tuple[float | int, float | int]):
        Bullet.render(surface, offset)
        return super().render(surface, offset)


class IdleFsm(BaseFsm):
    def get_next_state(self, entity: Player) -> str | None:
        if entity.is_hitted:
            return "hurt"
        if abs(entity.vx) > 0.001:
            return "run"
        if entity.jump_pressed or entity.vy > 0.001:
            return "jump"

        return None


class RunFsm(BaseFsm):
    def get_next_state(self, entity: Player) -> str | None:
        if entity.is_hitted:
            return "hurt"
        if abs(entity.vx) <= 0.001:
            return "idle"
        if entity.jump_pressed:
            return "jump"

        return None


class JumpFsm(BaseFsm):
    def enter(self, entity: Player) -> None:
        entity.jump_pressed = False

    def get_next_state(self, entity: Player) -> str | None:
        if entity.is_hitted:
            return "hurt"
        if entity.on_ground:
            return "idle"
        return None


class HurtFsm(BaseFsm):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.start_time = 0
        self.cooldown_reached = False
        self.cooldown_timer = 1000

    def enter(self, entity: Player, /) -> None:
        self.start_time = pygame.time.get_ticks()
        self.cooldown_reached = False

        if entity.hit_result is not None:
            dx, dy = entity.hit_result.normal
            entity.velocity_override = -dx * SPEED_NORMAL, dy

    def get_next_state(self, entity: Player, /) -> str | None:
        if not self.cooldown_reached:
            return None

        return "idle"

    def update(self, entity: Player, /) -> None:
        current = pygame.time.get_ticks()
        if (current - self.start_time) >= self.cooldown_timer:
            self.cooldown_reached = True

    def exit(self, entity: Player, /) -> None:
        entity.velocity_override = None
        entity.hit_result = None
        entity.is_hitted = False
