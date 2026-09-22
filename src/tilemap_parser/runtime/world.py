"""Tile and body collision space: stacked union tile layer plus solids."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from ..parser.collision import CollisionPolygon, TileCollisionData, TilesetCollision
from .body import Body
from .collision.hit import check_collision
from .map_loader import TilemapData
from .protocols import ICollidable

if TYPE_CHECKING:  # pragma: no cover
    from ..parser.map_parse import ParsedTileset


FLIP_H = 1
FLIP_V = 2
FLIP_D = 4

StackEntry = Tuple[int, int]
TileCell = Tuple[StackEntry, ...]
TileMap = Dict[Tuple[int, int], TileCell]


def flip_flags(flip_h: bool = False, flip_v: bool = False, flip_d: bool = False) -> int:
    return (FLIP_H if flip_h else 0) | (FLIP_V if flip_v else 0) | (FLIP_D if flip_d else 0)


def flip_vertices(
    vertices: List[Tuple[float, float]],
    flags: int,
    tile_size: Tuple[float, float],
) -> List[Tuple[float, float]]:
    """Transpose-then-mirror per flags; extents swap on transpose,
    winding-independent so no re-winding."""
    if not flags:
        return list(vertices)
    tw, th = float(tile_size[0]), float(tile_size[1])
    w, h = (th, tw) if flags & FLIP_D else (tw, th)
    out: List[Tuple[float, float]] = []
    for x, y in vertices:
        if flags & FLIP_D:
            x, y = y, x
        if flags & FLIP_H:
            x = w - x
        if flags & FLIP_V:
            y = h - y
        out.append((x, y))
    return out


def flipped_data(
    base: TileCollisionData,
    flags: int,
    tile_size: Tuple[float, float],
) -> TileCollisionData:
    """Same object when flags == 0; preserves one_way/layer/mask."""
    if not flags:
        return base
    return TileCollisionData(
        tile_id=base.tile_id,
        shapes=[
            CollisionPolygon(
                vertices=flip_vertices(list(poly.vertices), flags, tile_size),
                one_way=poly.one_way,
            )
            for poly in base.shapes
        ],
        collision_layer=base.collision_layer,
        collision_mask=base.collision_mask,
    )


def _as_entry(value: object) -> Optional[StackEntry]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return (value, 0)
    if isinstance(value, (tuple, list)) and len(value) == 2:
        gid, flags = value
        if (
            isinstance(gid, int)
            and not isinstance(gid, bool)
            and isinstance(flags, int)
            and not isinstance(flags, bool)
        ):
            return (gid, flags)
    return None


def iter_cell_entries(cell: object) -> TileCell:
    """Normalize any cell shape to stacked entries; flat 2-tuples read as
    two legacy gids, deduped, first-seen order."""
    if cell is None:
        return ()
    if isinstance(cell, bool):
        return ()
    if isinstance(cell, int):
        return ((cell, 0),)
    if isinstance(cell, (tuple, list)):
        out: List[StackEntry] = []
        for v in cell:
            entry = _as_entry(v)
            if entry is None:
                if isinstance(v, int) and not isinstance(v, bool):
                    entry = (v, 0)
                else:
                    continue
            if entry not in out:
                out.append(entry)
        return tuple(out)
    return ()


def iter_cell_ids(cell: object) -> Tuple[int, ...]:
    return tuple(gid for gid, _flags in iter_cell_entries(cell))


def _normalize_tile_map(tile_map: Optional[Dict[Tuple[int, int], object]]) -> TileMap:
    normalized: TileMap = {}
    for pos, cell in dict(tile_map or {}).items():
        entries = iter_cell_entries(cell)
        if entries:
            normalized[tuple(pos)] = entries
    return normalized


class PhysicsWorld:
    def __init__(
        self,
        tile_map: Optional[Dict[Tuple[int, int], object]] = None,
        tileset_collision: Optional[TilesetCollision] = None,
        tile_size: Tuple[int, int] = (32, 32),
        render_scale: float = 1.0,
    ):
        """
        Legacy cells normalize to stacked entries; non-empty tile_map
        requires tileset_collision. tile_size doubles as flip extents.
        """
        self.tile_map: TileMap = _normalize_tile_map(tile_map)
        self.tileset_collision = tileset_collision
        self.tile_size = tuple(tile_size)
        self.render_scale = render_scale
        self.bodies: List[Body] = []
        self._flipped_cache: Dict[Tuple[int, int], TileCollisionData] = {}
        # GID routing ranges; empty means literal local lookups.
        self._grid_ranges: List[Tuple[int, int, str]] = []
        self._collision_owner_stem: Optional[str] = None
        if self.tile_map and self.tileset_collision is None:
            raise ValueError(
                "tile_map requires tileset_collision: a world with solid "
                "tiles cannot resolve movement without collision data"
            )

    @classmethod
    def from_map(
        cls,
        tilemap_data: TilemapData,
        tileset_collision: TilesetCollision,
        *,
        exclude_layers: Optional[set[str]] = None,
        use_gids: bool = False,
        collision_tileset: Optional[str] = None,
    ) -> "PhysicsWorld":
        """
        Unioned tile layers (overlap never erases); explicit
        ``collision_tileset=`` names the GID owner on multi-tileset maps.
        """
        world = cls(
            tile_size=(
                int(tilemap_data.parsed.meta.tile_size[0]),
                int(tilemap_data.parsed.meta.tile_size[1]),
            ),
            render_scale=tilemap_data.render_scale,
        )
        world.tile_map = tilemap_data.build_tile_map(
            exclude_layers=exclude_layers,
            use_gids=use_gids,
        )
        if world.tile_map and tileset_collision is None:
            raise ValueError(
                "tile_map requires tileset_collision: a world with solid "
                "tiles cannot resolve movement without collision data"
            )
        world.tileset_collision = tileset_collision
        if use_gids:
            world._capture_grid_ownership(tilemap_data, tileset_collision, collision_tileset)
        return world

    def _capture_grid_ownership(
        self,
        map_data: TilemapData,
        tileset_collision: TilesetCollision,
        collision_tileset: Optional[str] = None,
    ) -> None:
        grid: List[Tuple[int, int, str]] = []
        for ts in map_data.parsed.tilesets:
            if getattr(ts, "type", "tile") != "tile":
                continue
            grid.append((ts.firstgid, ts.tile_count, Path(ts.path).stem))
        if collision_tileset is not None:
            if any(stem == collision_tileset for _, _, stem in grid):
                self._grid_ranges = grid
                self._collision_owner_stem = collision_tileset
            else:
                warnings.warn(
                    f"collision_tileset={collision_tileset!r} matches no tile tileset in the map; "
                    "GID lookups fall back to literal ids",
                    UserWarning,
                    stacklevel=3,
                )
            return
        if len(grid) == 1:
            self._grid_ranges = grid
            self._collision_owner_stem = grid[0][2]
            return
        if self.tile_map and not any(
            tileset_collision.tiles.get(gid) is not None
            for cell in self.tile_map.values()
            for gid, _flags in iter_cell_entries(cell)
        ):
            warnings.warn(
                "no collision owner named: pass collision_tileset= with the map tileset "
                "stem that owns collision; GID lookups fall back to literal ids and "
                "no tile resolves",
                UserWarning,
                stacklevel=3,
            )

    def resolve_collision(self, tile_id: int) -> Optional[TileCollisionData]:
        """Routed (window owner → local key; deco never solid) or plain
        lookup when unrouted."""
        if self._grid_ranges and self.tileset_collision is not None:
            for firstgid, count, stem in self._grid_ranges:
                if firstgid <= tile_id < firstgid + count:
                    if stem != self._collision_owner_stem:
                        return None
                    return self.tileset_collision.tiles.get(tile_id - firstgid)
            return None
        if self.tileset_collision is None:
            return None
        return self.tileset_collision.tiles.get(tile_id)

    def has_collision_gid(self, tile_id: int) -> bool:
        data = self.resolve_collision(tile_id)
        return data is not None and data.has_collision()

    def tile_ids_at(self, pos: Tuple[int, int]) -> Tuple[int, ...]:
        return tuple(gid for gid, _flags in iter_cell_entries(self.tile_map.get(tuple(pos))))

    def tile_entries_at(self, pos: Tuple[int, int]) -> TileCell:
        return iter_cell_entries(self.tile_map.get(tuple(pos)))

    def resolve_stack_entry(self, entry: StackEntry) -> Optional[TileCollisionData]:
        """Flip-aware data per entry; cached per (gid, flags), shared when unflipped."""
        gid, flags = entry
        data = self.resolve_collision(gid)
        if data is None:
            return None
        if not flags:
            return data
        key = (gid, flags)
        cached = self._flipped_cache.get(key)
        if cached is None:
            tile_size = self.tile_size
            if self.tileset_collision is not None:
                tile_size = self.tileset_collision.tile_size
            cached = flipped_data(data, flags, tile_size)
            self._flipped_cache[key] = cached
        return cached

    def iter_cell_data(self, cell: object) -> "List[TileCollisionData]":
        # No layer/mask filter here; callers apply should_collide.
        datas: "List[TileCollisionData]" = []
        for entry in iter_cell_entries(cell):
            data = self.resolve_stack_entry(entry)
            if data is not None:
                datas.append(data)
        return datas

    def cell_has_collision(self, pos: Tuple[int, int]) -> bool:
        for data in self.iter_cell_data(self.tile_map.get(tuple(pos))):
            if data.has_collision():
                return True
        return False

    def add_body(self, body: Body) -> None:
        # Adding twice is a no-op.
        if body not in self.bodies:
            self.bodies.append(body)

    def remove_body(self, body: Body) -> None:
        try:
            self.bodies.remove(body)
        except ValueError:
            raise ValueError(f"{body!r} is not in this world") from None

    def clear_bodies(self) -> None:
        self.bodies.clear()

    def __contains__(self, body: object) -> bool:
        return body in self.bodies

    def __len__(self) -> int:
        return len(self.bodies)

    def collides_with_body(self, sprite: ICollidable) -> Optional[Body]:
        """
        First overlapping body in insertion order, else None. Mutual
        layer/mask agreement; bodies solid both ways; self excluded.
        """
        for body in self.bodies:
            if body is sprite:
                continue
            if check_collision(sprite, body) is not None:
                return body
        return None
