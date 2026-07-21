from typing import Tuple

from tilemap_parser import ICollidable, get_shape_aabb

TShapeSprite = ICollidable


def get_sprite_center(sprite: TShapeSprite):
    left, top, right, bottom = get_shape_aabb(sprite.x, sprite.y, sprite.collision_shape)
    return (left + right) * 0.5, (top + bottom) * 0.5


def is_close_to(entity: TShapeSprite, point: Tuple[int | float, int | float], tolerance: float = 0.001):
    ecx, ecy = get_sprite_center(entity)
    dx = point[0] - ecx
    dy = point[1] - ecy
    length = (dx * dx + dy * dy) ** 0.5

    norm_x, norm_y = 0, 0
    if length > 0:
        norm_x = dx / length
        norm_y = dy / length

    if length > tolerance:
        return (False, (norm_x, norm_y))
    return True, (norm_x, norm_y)
