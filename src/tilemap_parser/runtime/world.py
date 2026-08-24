"""PhysicsWorld — the single space bodies and tiles are resolved in.

Godot's global physics space, simplified: the world owns the tile layer
(the same ``{(col, row): tile_id}`` map the runner iterates) and the list
of :class:`~.body.Body` solids.  A :class:`~.movement.CollisionRunner`
attaches to a world (``CollisionRunner.from_world(world, game_type)``) and
resolves movement against the world's tiles AND bodies uniformly.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from ..parser.collision import TileCollisionData, TilesetCollision
from .body import Body
from .collision.hit import check_collision
from .map_loader import TilemapData
from .protocols import ICollidable

if TYPE_CHECKING:  # pragma: no cover
    from ..parser.map_parse import ParsedTileset


class PhysicsWorld:
    """A space containing a tile layer and solid bodies."""

    def __init__(
        self,
        tile_map: Optional[Dict[Tuple[int, int], int]] = None,
        tileset_collision: Optional[TilesetCollision] = None,
        tile_size: Tuple[int, int] = (32, 32),
        render_scale: float = 1.0,
    ):
        """
        Create an empty world.

        Args:
            tile_map: ``{(col, row): tile_id}`` tile layer (see
                :meth:`TilemapData.build_tile_map`).  Defaults to empty.
            tileset_collision: Collision data for the tiles in *tile_map*.
            tile_size: Tile dimensions in pixels ``(width, height)`` —
                the space's grid, adopted by a runner on attach.
            render_scale: Effective-pixel scale of the space (see
                :attr:`TilemapData.render_scale`).
        """
        self.tile_map: Dict[Tuple[int, int], int] = dict(tile_map or {})
        self.tileset_collision = tileset_collision
        self.tile_size = tuple(tile_size)
        self.render_scale = render_scale
        self.bodies: List[Body] = []
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

 
    def _capture_grid_ownership(
        self, map_data: TilemapData, tileset_collision: TilesetCollision
    ) -> None:
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
            raise ValueError(
                f"{body!r} is not in this world"
            ) from None

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
