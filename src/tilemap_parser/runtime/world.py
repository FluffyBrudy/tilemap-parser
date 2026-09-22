"""PhysicsWorld — the single space bodies and tiles are resolved in.

Godot's global physics space, simplified: the world owns the tile layer
(the same ``{(col, row): ((gid, flipbits), ...)}`` union map the runner iterates)
and the list of :class:`~.body.Body` solids.  A :class:`~.movement.CollisionRunner`
attaches to a world (``CollisionRunner.from_world(world, game_type)``) and
resolves movement against the world's tiles AND bodies uniformly.
"""

from __future__ import annotations

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

StackEntry = Tuple[int, int]  # (gid, flipbits)
TileCell = Tuple[StackEntry, ...]
TileMap = Dict[Tuple[int, int], TileCell]


def flip_flags(flip_h: bool = False, flip_v: bool = False, flip_d: bool = False) -> int:
    """Encode tile flip bools (ParsedTile / TMX) to a stack-entry bitmask."""
    return (FLIP_H if flip_h else 0) | (FLIP_V if flip_v else 0) | (FLIP_D if flip_d else 0)


def flip_vertices(
    vertices: List[Tuple[float, float]],
    flags: int,
    tile_size: Tuple[float, float],
) -> List[Tuple[float, float]]:
    """Mirror/transpose tile-local vertices per flip flags (Tiled order).

    Diagonal transpose first (axes swap, so the mirror extents swap too),
    then horizontal / vertical mirrors.  Identity when ``flags == 0``.
    For non-square tiles the transpose swaps the mirror extents
    ``(w, h) -> (h, w)`` while the grid cell itself is unchanged (standard
    2D-engine behavior for transposed non-square tiles).
    Winding may flip (CW<->CCW); the narrowphase is winding-independent
    (ray-cast containment, orientation-agnostic segments, centroid-tested
    outward normals), so no re-winding is needed.
    """
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
    """Return *base* with every shape's vertices flip-transformed.

    Identity (same object) when ``flags == 0``.  Preserves ``one_way``,
    ``collision_layer`` and ``collision_mask``.
    """
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
    """Normalize one tile_map cell to ``((gid, flipbits), ...)``.

    Accepts ``None``, legacy ``int``, legacy flat ``(gid, ...)`` tuples /
    lists (flags default 0), and the canonical nested form.  Dedups
    identical entries, preserving first-seen (z-)order.

    Convention (ambiguous by necessity, pinned here): a flat 2-tuple of
    ints is ALWAYS two legacy tiles — ``(23, 1)`` means gids 23 and 1,
    never "gid 23 with FLIP_H".  A single flipped tile must be nested:
    ``((23, 1),)``.  ``build_tile_map()`` only ever emits the nested form.
    """
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
    """Gids stacked in one cell (legacy-int tolerant, order-preserving)."""
    return tuple(gid for gid, _flags in iter_cell_entries(cell))


def _normalize_tile_map(tile_map: Optional[Dict[Tuple[int, int], object]]) -> TileMap:
    normalized: TileMap = {}
    for pos, cell in dict(tile_map or {}).items():
        entries = iter_cell_entries(cell)
        if entries:
            normalized[tuple(pos)] = entries
    return normalized


class PhysicsWorld:
    """A space containing a tile layer and solid bodies."""

    def __init__(
        self,
        tile_map: Optional[Dict[Tuple[int, int], object]] = None,
        tileset_collision: Optional[TilesetCollision] = None,
        tile_size: Tuple[int, int] = (32, 32),
        render_scale: float = 1.0,
    ):
        """
        Create an empty world.

        Args:
            tile_map: ``{(col, row): ((gid, flipbits), ...)}`` tile layer
                (see :meth:`TilemapData.build_tile_map`).  Legacy
                ``{(col, row): tile_id}`` and flat ``(gid, ...)`` cells
                normalize to stacked entries with zero flips.  Defaults
                to empty.
            tileset_collision: Collision data for the tiles in *tile_map*.
            tile_size: Tile dimensions in pixels ``(width, height)`` —
                the space's grid, adopted by a runner on attach.  Also the
                mirror extents for flip transforms.
            render_scale: Effective-pixel scale of the space (see
                :attr:`TilemapData.render_scale`).
        """
        self.tile_map: TileMap = _normalize_tile_map(tile_map)
        self.tileset_collision = tileset_collision
        self.tile_size = tuple(tile_size)
        self.render_scale = render_scale
        self.bodies: List[Body] = []
        self._flipped_cache: Dict[Tuple[int, int], TileCollisionData] = {}
        # GID routing (see `resolve_collision`): (firstgid, tile_count, stem)
        # for every *grid* resource of the source map, plus the stem that the
        # single collision file belongs to.  Empty => literal local lookups.
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
    ) -> "PhysicsWorld":
        """
        Build a world from loaded map data.

        Tile layers are unioned Godot-style: overlapping cells keep every
        layer's gid, so deco layers can never erase solid ground.  Layers
        with ``collision_enabled=False`` and *exclude_layers* are skipped.

        Args:
            tilemap_data: Loaded tilemap (see :func:`~.runtime.load_map`).
            tileset_collision: Collision data for the map's tiles.
            exclude_layers: Tile layers to skip (see
                :meth:`TilemapData.build_tile_map`).
            use_gids: Whether tile ids are global ids (see
                :meth:`TilemapData.build_tile_map`).

        Returns:
            A world whose tile layer and grid geometry match the map.
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
            world._capture_grid_ownership(tilemap_data, tileset_collision)
        return world

    def _capture_grid_ownership(self, map_data: TilemapData, tileset_collision: TilesetCollision) -> None:
        """Record every grid resource's GID range and the collision owner.

        Only ``type=="tile"`` resources participate; object tilesets are
        never part of the physics grid.  Routing activates only when the
        collision file's ``tileset_name`` stem-matches one of them —
        otherwise lookups stay literal (legacy / pre-merged files).
        """
        owner = tileset_collision.tileset_name
        ranges: List[Tuple[int, int, str]] = []
        matched: Optional[str] = None
        for ts in map_data.parsed.tilesets:
            if getattr(ts, "type", "tile") != "tile":
                continue
            stem = Path(ts.path).stem
            ranges.append((ts.firstgid, ts.tile_count, stem))
            if stem == owner and matched is None:
                matched = stem
        if matched is not None:
            self._grid_ranges = ranges
            self._collision_owner_stem = matched

    def resolve_collision(self, tile_id: int) -> Optional[TileCollisionData]:
        """Resolve a possibly-global tile id to its collision data.

        With GID routing active (``from_map(..., use_gids=True)`` plus a
        stem-matched collision file):

        1. find the grid resource whose ``[firstgid, firstgid+count)``
           window contains *tile_id*;
        2. if that resource is **not** the collision owner → ``None``
           (decoration grids are never solid, no cross-set aliasing);
        3. else translate ``tile_id - firstgid`` to the local key.

        Without routing (literal mode, or a pre-merged GID-keyed
        collision), falls back to a plain dictionary lookup — identical
        to historic behaviour.
        """
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
        """Convenience boolean form of :meth:`resolve_collision`."""
        data = self.resolve_collision(tile_id)
        return data is not None and data.has_collision()

    def tile_ids_at(self, pos: Tuple[int, int]) -> Tuple[int, ...]:
        """Gids stacked at *pos* (legacy tolerant, ``()`` when empty)."""
        return tuple(gid for gid, _flags in iter_cell_entries(self.tile_map.get(tuple(pos))))

    def tile_entries_at(self, pos: Tuple[int, int]) -> TileCell:
        """``((gid, flipbits), ...)`` stacked at *pos* (``()`` when empty)."""
        return iter_cell_entries(self.tile_map.get(tuple(pos)))

    def resolve_stack_entry(self, entry: StackEntry) -> Optional[TileCollisionData]:
        """Resolve one ``(gid, flipbits)`` entry to flip-aware collision data.

        GID routing matches :meth:`resolve_collision`; flipped geometry is
        transformed once and cached per ``(gid, flipbits)``.  ``flags == 0``
        returns the shared base object (no copy).
        """
        gid, flags = entry
        data = self.resolve_collision(gid)
        if data is None:
            return None
        if not flags:
            return data
        key = (gid, flags)
        cached = self._flipped_cache.get(key)
        if cached is None:
            cached = flipped_data(data, flags, self.tile_size)
            self._flipped_cache[key] = cached
        return cached

    def iter_cell_data(self, cell: object) -> "List[TileCollisionData]":
        """Flip-aware collision datas for every entry in one cell (union).

        Skips entries with no data.  Does NOT layer/mask-filter — callers
        with a sprite apply ``should_collide`` (see movement queries).
        """
        datas: "List[TileCollisionData]" = []
        for entry in iter_cell_entries(cell):
            data = self.resolve_stack_entry(entry)
            if data is not None:
                datas.append(data)
        return datas

    def cell_has_collision(self, pos: Tuple[int, int]) -> bool:
        """True when any stacked gid at *pos* has collision shapes."""
        for data in self.iter_cell_data(self.tile_map.get(tuple(pos))):
            if data.has_collision():
                return True
        return False

    # body
    def add_body(self, body: Body) -> None:
        """Add a body to the world.  Adding the same body twice is a no-op."""
        if body not in self.bodies:
            self.bodies.append(body)

    def remove_body(self, body: Body) -> None:
        """Remove a body from the world.  Raises ValueError if absent."""
        try:
            self.bodies.remove(body)
        except ValueError:
            raise ValueError(f"{body!r} is not in this world") from None

    def clear_bodies(self) -> None:
        """Remove all bodies from the world."""
        self.bodies.clear()

    def __contains__(self, body: object) -> bool:
        return body in self.bodies

    def __len__(self) -> int:
        return len(self.bodies)

    def collides_with_body(self, sprite: ICollidable) -> Optional[Body]:
        """
        Return the first body *sprite* overlaps, or None.

        Body collisions honor both sides' ``collision_layer`` /
        ``collision_mask`` (mutual agreement, like
        :func:`~.runtime.collision.hit.should_collide`).  Bodies are
        always solid both ways — there is no one-way flag.

        Args:
            sprite: The moving object (``x``, ``y``, ``collision_shape``).
                If it is itself a body managed by this world, it is
                excluded by identity (a body never blocks itself).

        Returns:
            The first blocking body in insertion order, or ``None``.
        """
        for body in self.bodies:
            if body is sprite:
                continue
            if check_collision(sprite, body) is not None:
                return body
        return None
