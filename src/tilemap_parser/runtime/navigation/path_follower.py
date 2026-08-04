from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ...parser.collision import TilesetCollision
from ..protocols import ICollidable
from ..movement import CollisionRunner


class PathFollower:
    __slots__ = ("_eff_tw", "_eff_th", "arrival_distance")

    def __init__(
        self,
        effective_tile_size: Tuple[float, float],
        *,
        arrival_distance: Optional[float] = None,
    ) -> None:
        self._eff_tw, self._eff_th = effective_tile_size
        self.arrival_distance = (
            arrival_distance
            if arrival_distance is not None
            else math.hypot(self._eff_tw, self._eff_th) * 0.2
        )

    def update_rpg(
        self,
        sprite: ICollidable,
        path: List[Tuple[int, int]],
        waypoint_index: int,
        collision_runner: CollisionRunner,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        speed: float = 200.0,
        dt: float = 0.016,
    ) -> Tuple[int, bool, bool, bool]:
        if not path or waypoint_index >= len(path):
            return waypoint_index, True, False, False

        while waypoint_index < len(path):
            wx, wy = path[waypoint_index]
            tx = wx * self._eff_tw + self._eff_tw * 0.5
            ty = wy * self._eff_th + self._eff_th * 0.5
            if math.hypot(tx - sprite.x, ty - sprite.y) < self.arrival_distance:
                waypoint_index += 1
            else:
                break

        if waypoint_index >= len(path):
            return waypoint_index, True, False, False

        wx, wy = path[waypoint_index]
        tx = wx * self._eff_tw + self._eff_tw * 0.5
        ty = wy * self._eff_th + self._eff_th * 0.5

        dx = tx - sprite.x
        dy = ty - sprite.y
        dist = math.hypot(dx, dy)

        if dist < 0.01:
            delta_x = 0.0
            delta_y = 0.0
        else:
            step = min(speed * dt, dist)
            delta_x = (dx / dist) * step
            delta_y = (dy / dist) * step

        result = collision_runner.move_rpg(
            sprite, tileset_collision, tile_map, delta_x, delta_y
        )

        if math.hypot(tx - sprite.x, ty - sprite.y) < self.arrival_distance:
            waypoint_index += 1

        return waypoint_index, waypoint_index >= len(path), result.hit_wall_x, result.hit_wall_y
