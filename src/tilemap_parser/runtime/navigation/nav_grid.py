from __future__ import annotations

from typing import Dict, List, Tuple

from ...parser.collision import TilesetCollision


class NavGrid:
    """Walkability grid derived from tile collision data.

    Classifies every tile position based on collision geometry and
    provides neighbor queries for pathfinding.

    The grid operates purely in tile coordinates (tx, ty) — no pixel
    math, no physics.  This keeps it decoupled from the movement system.
    """

    __slots__ = (
        "tile_map",
        "tileset_collision",
        "tile_size",
        "_eff_tw",
        "_eff_th",
    )

    def __init__(
        self,
        tile_map: Dict[Tuple[int, int], int],
        tileset_collision: TilesetCollision,
        tile_size: Tuple[int, int],
        render_scale: float = 1.0,
    ) -> None:
        self.tile_map = tile_map
        self.tileset_collision = tileset_collision
        self.tile_size = tile_size
        self._eff_tw = tile_size[0] * render_scale
        self._eff_th = tile_size[1] * render_scale

    def is_solid(self, tx: int, ty: int) -> bool:
        tile_id = self.tile_map.get((tx, ty))
        if tile_id is None:
            return False
        tile_data = self.tileset_collision.tiles.get(tile_id)
        if tile_data is None:
            return False
        for poly in tile_data.shapes:
            if poly.is_valid() and not poly.one_way:
                return True
        return False

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

    def is_walkable(self, tx: int, ty: int) -> bool:
        return not self.is_solid(tx, ty)

    def get_neighbors(
        self, tx: int, ty: int, *, diagonals: bool = False
    ) -> List[Tuple[int, int]]:
        neighbors: List[Tuple[int, int]] = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = tx + dx, ty + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        if diagonals:
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                nx, ny = tx + dx, ty + dy
                if self.is_walkable(nx, ny):
                    neighbors.append((nx, ny))
        return neighbors
