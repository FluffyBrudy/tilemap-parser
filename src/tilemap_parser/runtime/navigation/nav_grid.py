from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from ...parser.collision import TilesetCollision


class NavGrid:
    """Walkability grid derived from tile collision data.

    The base grid is a pure representation of the world — no entity size
    or clearance baked in.  Entity-specific clearance is layered on via
    ``erode(margin)`` which returns a derived grid with walls inflated.
    """

    __slots__ = (
        "tile_map",
        "tileset_collision",
        "tile_size",
        "_eff_tw",
        "_eff_th",
        "_width",
        "_height",
        "_walkable",
    )

    def __init__(
        self,
        tile_map: Dict[Tuple[int, int], int],
        tileset_collision: TilesetCollision,
        tile_size: Tuple[int, int],
        render_scale: float = 1.0,
        map_size: Optional[Tuple[int, int]] = None,
    ) -> None:
        self.tile_map = tile_map
        self.tileset_collision = tileset_collision
        self.tile_size = tile_size
        self._eff_tw = tile_size[0] * render_scale
        self._eff_th = tile_size[1] * render_scale

        if map_size is not None:
            self._width, self._height = map_size
        else:
            self._width = 0
            self._height = 0
            for tx, ty in tile_map:
                if tx >= self._width:
                    self._width = tx + 1
                if ty >= self._height:
                    self._height = ty + 1

        self._walkable = [[self._is_tile_walkable(x, y) for x in range(self._width)] for y in range(self._height)]

    def _is_tile_walkable(self, tx: int, ty: int) -> bool:
        tile_id = self.tile_map.get((tx, ty))
        if tile_id is None:
            return True
        tile_data = self.tileset_collision.tiles.get(tile_id)
        if tile_data is None:
            return True
        for poly in tile_data.shapes:
            if poly.is_valid() and not poly.one_way:
                return False
        return True

    def _in_bounds(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self._width and 0 <= ty < self._height

    def is_solid(self, tx: int, ty: int) -> bool:
        if not self._in_bounds(tx, ty):
            return True
        return not self._walkable[ty][tx]

    def is_walkable(self, tx: int, ty: int) -> bool:
        if not self._in_bounds(tx, ty):
            return False
        return self._walkable[ty][tx]

    def is_one_way(self, tx: int, ty: int) -> bool:
        tile_id = self.tile_map.get((tx, ty))
        if tile_id is None:
            return False
        tile_data = self.tileset_collision.tiles.get(tile_id)
        if tile_data is None:
            return False
        has_one_way = False
        for poly in tile_data.shapes:
            if not poly.is_valid():
                continue
            if poly.one_way:
                has_one_way = True
            else:
                return False
        return has_one_way

    def copy(self) -> NavGrid:
        new = NavGrid.__new__(NavGrid)
        new.tile_map = self.tile_map
        new.tileset_collision = self.tileset_collision
        new.tile_size = self.tile_size
        new._eff_tw = self._eff_tw
        new._eff_th = self._eff_th
        new._width = self._width
        new._height = self._height
        new._walkable = [row[:] for row in self._walkable]
        return new

    def erode(self, margin: float) -> NavGrid:
        new = self.copy()
        new._erode_in_place(margin)
        return new

    def _erode_in_place(self, margin: float) -> None:
        original = [row[:] for row in self._walkable]
        r = int(math.ceil(margin + 0.5))

        for sy in range(self._height):
            for sx in range(self._width):
                if not original[sy][sx]:
                    continue
                min_tx = max(0, sx - r)
                max_tx = min(self._width - 1, sx + r)
                min_ty = max(0, sy - r)
                max_ty = min(self._height - 1, sy + r)
                for ty in range(min_ty, max_ty + 1):
                    for tx in range(min_tx, max_tx + 1):
                        if original[ty][tx]:
                            continue
                        dx = abs(tx - sx)
                        dy = abs(ty - sy)
                        dist_x = max(0.0, dx - 0.5)
                        dist_y = max(0.0, dy - 0.5)
                        if dist_x == 0 and dist_y == 0:
                            dist = 0.0
                        elif dist_x == 0:
                            dist = dist_y
                        elif dist_y == 0:
                            dist = dist_x
                        else:
                            dist = math.hypot(dist_x, dist_y)
                        if dist <= margin:
                            self._walkable[sy][sx] = False
                            break
                    if not self._walkable[sy][sx]:
                        break

    @classmethod
    def for_entity(
        cls,
        tile_map: Dict[Tuple[int, int], int],
        tileset_collision: TilesetCollision,
        tile_size: Tuple[int, int],
        sprite_width: float,
        sprite_height: Optional[float] = None,
        render_scale: float = 1.0,
        map_size: Optional[Tuple[int, int]] = None,
        cache: Optional[Dict[float, NavGrid]] = None,
    ) -> NavGrid:
        tw = tile_size[0] * render_scale
        size = max(sprite_width, sprite_height if sprite_height is not None else sprite_width)
        margin = (size / 2.0) / tw
        if cache is not None and margin in cache:
            return cache[margin]
        nav = cls(tile_map, tileset_collision, tile_size, render_scale, map_size).erode(margin)
        if cache is not None:
            cache[margin] = nav
        return nav

    def get_neighbors(self, tx: int, ty: int, *, diagonals: bool = False) -> List[Tuple[int, int]]:
        neighbors: List[Tuple[int, int]] = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = tx + dx, ty + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        if diagonals:
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                nx, ny = tx + dx, ty + dy
                if not self.is_walkable(nx, ny):
                    continue
                if not self.is_walkable(tx + dx, ty) or not self.is_walkable(tx, ty + dy):
                    continue
                neighbors.append((nx, ny))
        return neighbors
