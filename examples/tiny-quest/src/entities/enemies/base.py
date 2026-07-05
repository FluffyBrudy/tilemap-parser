from typing import TYPE_CHECKING, List, Optional, Tuple, cast

import pygame
from pygame import Surface
from tilemap_parser import ObjectCollisionManager, get_shape_aabb

from src.entities.enemies.arial import ArialEnemyBase
from src.entities.enemies.devilkin2 import Devilkin2

if TYPE_CHECKING:
    from src.entities.entity import Entity


class EnemyManager:
    manager = ObjectCollisionManager()

    @classmethod
    def spawn(cls, enemy_cls, x: float, y: float, target: "Entity"):
        enemy = enemy_cls(x, y)
        enemy.set_target(target)
        cls.manager.add_object(enemy)
        return enemy

    @classmethod
    def add(cls, obj: "Entity"):
        cls.manager.add_object(obj)

    @classmethod
    def remove(cls, obj: "Entity"):
        cls.manager.remove_object(obj)

    @classmethod
    def update(cls, dt: float):
        removable_enemies = []

        enemies = cast(List["Entity"], cls.manager.objects)
        for enemy in enemies:
            enemy.update(dt)
            if isinstance(enemy, (ArialEnemyBase, Devilkin2)):
                if enemy.can_kill():
                    removable_enemies.append(enemy)

        cls.remove_enemies(removable_enemies)

    @classmethod
    def render(cls, surface: Surface, offset=(0, 0), player_pos: Optional[Tuple[float, float]] = None):
        enemies = cast(List["Entity"], cls.manager.objects)
        for enemy in enemies:
            if player_pos is not None and hasattr(enemy, "detection_range"):
                pcx, pcy = player_pos
                edx = pcx - enemy.x
                edy = pcy - enemy.y
                if (edx * edx + edy * edy) ** 0.5 <= enemy.detection_range * 2:
                    l, t, r, b = get_shape_aabb(enemy.x, enemy.y, enemy.collision_shape)
                    cx = int((l + r) * 0.5 - offset[0])
                    cy = int((t + b) * 0.5 - offset[1])
                    radius = int(enemy.detection_range)
                    ring = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring, (255, 30, 30, 30), (radius, radius), radius)
                    pygame.draw.circle(ring, (255, 80, 80, 120), (radius, radius), radius, 2)
                    surface.blit(ring, (cx - radius, cy - radius))
            enemy.render(surface, offset)

    @classmethod
    def get_enemies(cls):
        return cls.manager.objects

    @classmethod
    def remove_enemies(cls, enemies: List["Entity"]):
        for enemy in enemies:
            cls.manager.remove_object(enemy)
