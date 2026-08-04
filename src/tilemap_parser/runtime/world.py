"""PhysicsWorld — the single space bodies and tiles are resolved in.

Godot's global physics space, simplified: the world owns the tile layer
(the same ``{(col, row): tile_id}`` map the runner iterates) and the list
of :class:`~.body.Body` solids.  A :class:`~.movement.CollisionRunner`
attaches to a world (``CollisionRunner.from_world(world, game_type)``) and
resolves movement against the world's tiles AND bodies uniformly.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..parser.collision import TilesetCollision
from .body import Body
from .collision.hit import check_collision
from .map_loader import TilemapData
from .protocols import ICollidable


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
        return world

    # ------------------------------------------------------------------
    # Body management
    # ------------------------------------------------------------------

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
