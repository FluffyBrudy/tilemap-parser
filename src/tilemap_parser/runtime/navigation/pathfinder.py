from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Set, Tuple

from .nav_grid import NavGrid


class Pathfinder:
    __slots__ = ("nav_grid",)

    def __init__(self, nav_grid: NavGrid) -> None:
        self.nav_grid = nav_grid

    def find_path(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        max_steps: int = 2000,
    ) -> Optional[List[Tuple[int, int]]]:
        sx, sy = start
        ex, ey = end

        if not self.nav_grid.is_walkable(ex, ey):
            return None

        open_set: List[Tuple[float, int, int]] = [(0.0, sx, sy)]
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0.0}
        f_score: Dict[Tuple[int, int], float] = {
            start: _manhattan(sx, sy, ex, ey)
        }

        closed: Set[Tuple[int, int]] = set()
        steps = 0
        while open_set and steps < max_steps:
            _, cx, cy = heapq.heappop(open_set)
            current = (cx, cy)

            if current in closed:
                continue
            closed.add(current)
            steps += 1

            if current == end:
                return _reconstruct_path(came_from, current)

            for neighbor in self.nav_grid.get_neighbors(cx, cy):
                tentative = g_score[current] + 1.0
                if tentative < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    f = tentative + _manhattan(
                        neighbor[0], neighbor[1], ex, ey
                    )
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, neighbor[0], neighbor[1]))

        return None


def _manhattan(ax: int, ay: int, bx: int, by: int) -> float:
    return float(abs(ax - bx) + abs(ay - by))


def _reconstruct_path(
    came_from: Dict[Tuple[int, int], Tuple[int, int]],
    current: Tuple[int, int],
) -> List[Tuple[int, int]]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path
