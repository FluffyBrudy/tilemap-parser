from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from ...parser.collision import TileCollisionData, TilesetCollision


class NavGrid:
    """Walkability grid derived from tile collision data.

    The base grid is a pure representation of the world — no entity size
    or clearance baked in.  Entity-specific clearance is layered on via
    ``erode(margin)`` which returns a derived grid with walls inflated.
    """

    __slots__ = (
        "_eff_th",
        "_eff_tw",
        "_gid_resolver",
        "_height",
        "_walkable",
        "_width",
        "collision_mask",
        "tile_map",
        "tile_size",
        "tileset_collision",
    )

    def __init__(
        self,
        tile_map: Dict[Tuple[int, int], object],
        tileset_collision: TilesetCollision,
        tile_size: Tuple[int, int],
        render_scale: float = 1.0,
        map_size: Optional[Tuple[int, int]] = None,
        gid_resolver=None,
        collision_mask: int = 0xFFFFFFFF,
    ) -> None:
        self.tile_map = tile_map
        self.tileset_collision = tileset_collision
        # Optional callable (int) -> TileCollisionData | None.  Pass
        # ``physics_world.resolve_collision`` for GID-routed maps so ids from
        # non-collidable grid tilesets resolve to None instead of aliasing.
        self._gid_resolver = gid_resolver
        self.collision_mask = collision_mask
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

    def _resolve(self, tile_id):
        if tile_id is None:
            return None
        if self._gid_resolver is not None:
            return self._gid_resolver(tile_id)
        return self.tileset_collision.tiles.get(tile_id)

    def _iter_datas(self, cell: object):
        from ..world import flipped_data, iter_cell_entries

        for gid, flags in iter_cell_entries(cell):
            data = self._resolve(gid)
            if data is None:
                continue
            if flags:
                data = flipped_data(data, flags, self.tile_size)
            if not (self.collision_mask & data.collision_layer):
                continue
            yield data

    def _is_tile_walkable(self, tx: int, ty: int) -> bool:
        for tile_data in self._iter_datas(self.tile_map.get((tx, ty))):
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
        has_one_way = False
        for tile_data in self._iter_datas(self.tile_map.get((tx, ty))):
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
        # _gid_resolver lives in __slots__: dropping it here made every
        # derived grid raise AttributeError once _resolve() ran (e.g. via
        # is_one_way), and silently lost GID routing before that.
        new._gid_resolver = self._gid_resolver
        new.collision_mask = self.collision_mask
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
        tile_map: Dict[Tuple[int, int], object],
        tileset_collision: TilesetCollision,
        tile_size: Tuple[int, int],
        sprite_width: float,
        sprite_height: Optional[float] = None,
        render_scale: float = 1.0,
        map_size: Optional[Tuple[int, int]] = None,
        cache: Optional[dict[tuple, NavGrid]] = None,
        gid_resolver=None,
        collision_mask: int = 0xFFFFFFFF,
    ) -> NavGrid:
        """Build (or fetch from *cache*) an eroded grid for one entity size.

        The cache is scoped to a single map/routing context and is keyed by
        ``(margin, resolver_is_literal, collision_mask)`` so literal,
        GID-routed, and mask-filtered grids can never cross-contaminate
        through a shared cache dict.
        """
        tw = tile_size[0] * render_scale
        size = max(sprite_width, sprite_height if sprite_height is not None else sprite_width)
        margin = (size / 2.0) / tw
        key = (margin, gid_resolver is None, collision_mask)
        if cache is not None and key in cache:
            return cache[key]
        nav = cls(
            tile_map,
            tileset_collision,
            tile_size,
            render_scale,
            map_size,
            gid_resolver=gid_resolver,
            collision_mask=collision_mask,
        ).erode(margin)
        if cache is not None:
            cache[key] = nav
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
