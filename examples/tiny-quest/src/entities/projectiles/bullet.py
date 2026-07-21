from typing import Callable, List, Optional, Set, TypedDict, Unpack

import pygame
from tilemap_parser import (
    ICollidable,
    RectangleShape,
    check_collision,
)


class BulletType(TypedDict, total=False):
    width: int
    height: int
    speed: float


class Bullet:
    WIDTH = 8
    HEIGHT = 8
    MAX_RANGE = 200
    bullet_group: Set["Bullet"] = set()

    def __init__(self, x: float, y: float, vx: float, **override: Unpack[BulletType]) -> None:
        size = (
            override.get("width") or Bullet.WIDTH,
            override.get("height") or Bullet.HEIGHT,
        )

        self.collision_shape = RectangleShape(*size)
        self.x, self.y = x, y
        self.vx = vx

        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        self.surface.fill((255, 255, 255))
        self.range = Bullet.MAX_RANGE

    def __hash__(self) -> int:
        return id(self)

    @classmethod
    def check_collision_with(cls, obj: ICollidable):
        surviving_bullets = set()

        for bullet in cls.bullet_group:
            if not check_collision(bullet, obj):
                surviving_bullets.add(bullet)

        cls.bullet_group = surviving_bullets

    @classmethod
    def add_bullet(cls, object: "Bullet"):
        cls.bullet_group.add(object)

    @classmethod
    def update(cls, dt: float, is_solid_cb: Callable[[float, float, float, float], bool] | None = None):
        surviving_bullets = set()

        for bullet in cls.bullet_group:
            bullet.x += bullet.vx * dt
            bullet.range -= abs(bullet.vx * dt)
            alpha = Bullet.get_alpha_by_range(bullet.range, Bullet.MAX_RANGE)
            bullet.surface.set_alpha(alpha)
            if bullet.range >= 0:
                if is_solid_cb is None:
                    surviving_bullets.add(bullet)
                else:
                    left = bullet.x
                    top = bullet.y
                    right = left + bullet.collision_shape.width
                    bottom = top + bullet.collision_shape.height
                    if not is_solid_cb(left, top, right, bottom):
                        surviving_bullets.add(bullet)

        cls.bullet_group = surviving_bullets

    @classmethod
    def render(cls, surface: pygame.Surface, offset=(0, 0)):
        for bullet in cls.bullet_group:
            surface.blit(
                bullet.surface,
                (
                    bullet.x - offset[0],
                    bullet.y - offset[1],
                ),
            )

    @staticmethod
    def get_alpha_by_range(a: float, b: float):
        if a < 0 or a > b:
            return 0
        norm = (b - a) / b
        return int((1 - norm) * 255)
