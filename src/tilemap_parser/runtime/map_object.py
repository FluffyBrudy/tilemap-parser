"""
Runtime map object loading and representation.

Bridges the gap between parsed map objects, collision data, and
the collision manager.  Provides a ready-to-use :class:`MapObject`
that implements :class:`ICollidableObject` and carries a pygame
:class:`~pygame.Surface` for rendering.

Usage::

    objects = load_map_objects(tilemap_data, MAPS_PATH / "collision")
    for obj in objects:
        collision_manager.add_object(obj)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union

import pygame
from pygame import Surface

from ..parser.collision import CollisionPolygon, ObjectCollisionData
from ..parser.collision_loader import load_object_collision
from .collision_cache import CollisionCache
from .map_loader import TilemapData


class MapObject:
    """
    A game object loaded from a tilemap, carrying a surface for
    rendering and collision data for physics.

    All spatial data (``x``, ``y``, ``surface`` size, and collision
    polygon vertices) is pre-scaled by the map's ``render_scale``.
    Units are in *effective* pixels (``render_scale × tile_size``).
    The object is ready for direct use in a game loop that runs in
    effective-pixel space — no additional scaling needed.

    Satisfies the :class:`ICollidableObject` protocol so it can be
    added directly to an :class:`ObjectCollisionManager`.

    When a region contains multiple disjoint polygons, *all* shapes
    are stored in :attr:`collision_shapes` and the first shape is
    used as :attr:`collision_shape` for protocol compatibility.
    The collision system (:func:`check_collision`) iterates all
    shape pairs when either object has multiple shapes.
    """

    __slots__ = (
        "x",
        "y",
        "surface",
        "collision_shape",
        "collision_shapes",
        "collision_layer",
        "collision_mask",
        "y_sort_origin",
    )

    def __init__(
        self,
        x: float,
        y: float,
        surface: Surface,
        collision_shape: CollisionPolygon,
        *,
        collision_shapes: Optional[List[CollisionPolygon]] = None,
        collision_layer: int = 1,
        collision_mask: int = 0xFFFFFFFF,
        y_sort_origin: Optional[int] = None,
    ) -> None:
        self.x = x
        self.y = y
        self.surface = surface
        self.collision_shapes = collision_shapes or [collision_shape]
        self.collision_shape = self.collision_shapes[0]
        self.collision_layer = collision_layer
        self.collision_mask = collision_mask
        self.y_sort_origin = y_sort_origin


def _resolve_object_collision_filename(tileset_path: Union[str, Path]) -> str:
    """Extract the object collision filename for a given tileset path.

    Example: ``"building7.png"`` → ``"building7.object_collision.json"``
    """
    return f"{Path(tileset_path).stem}.object_collision.json"


def load_map_objects(
    tilemap_data: TilemapData,
    collision_dir: Union[str, Path],
    *,
    cache: Optional[CollisionCache] = None,
) -> List[MapObject]:
    """Load all collidable objects from a tilemap.

    Iterates every object layer in *tilemap_data*, resolves the
    corresponding ``.object_collision.json`` from *collision_dir*, and
    builds :class:`MapObject` instances with pre-scaled surfaces,
    positions, and collision shapes.

    **render_scale transparency**

    All spatial data is automatically scaled by the map's
    ``render_scale`` (from ``tilemap_data.render_scale``):

    * ``MapObject.x`` / ``MapObject.y`` — raw map coords × ``rs``
      (stored as ``float``; fractional pixel positions are preserved).
    * ``MapObject.surface`` — surface is scaled by ``rs`` via
      :func:`pygame.transform.scale` (no-op when ``rs == 1.0``).
      Raster dimensions are truncated to integers via ``int()``
      to satisfy :func:`pygame.transform.scale` requirements.
    * Collision polygon vertices and ``region_rect`` offsets are
      multiplied by ``rs`` via :meth:`CollisionPolygon.transform`.

    The returned objects are ready for a game loop that runs in
    effective-pixel space (``render_scale × tile_size``).  No
    additional scaling is required by the caller.

    Collision data is cached per tileset index so the same file is
    never loaded twice.

    Args:
        tilemap_data: Loaded tilemap data (surfaces, tilesets, layers).
        collision_dir: Directory containing ``*.object_collision.json``
            files (typically ``<map_path>/collision/``).
        cache: Optional :class:`CollisionCache` for caching parsed
            collision data across calls.

    Returns:
        List of :class:`MapObject` instances, one per map object that
        has both a valid surface and a matching collision region.
        When a region contains multiple collision polygons, all shapes
        are preserved in :attr:`MapObject.collision_shapes` and the
        collision system checks each shape pair during narrowphase.
    """
    collision_dir = Path(collision_dir)
    objects: List[MapObject] = []
    object_layers = tilemap_data.get_layers(layer_type="object")

    loaded_collision: Dict[int, Optional[ObjectCollisionData]] = {}

    for layer in object_layers:
        for obj_id, obj in layer.objects.items():
            surf_x_y = tilemap_data.get_object_surface_by_id(layer.id, obj_id)
            if surf_x_y is None:
                continue

            surf, x, y = surf_x_y
            rs = tilemap_data.render_scale
            x = x * rs
            y = y * rs

            if rs != 1.0 and surf is not None:
                w, h = surf.get_size()
                surf = pygame.transform.scale(surf, (int(w * rs), int(h * rs)))

            ttype = obj.ttype
            if ttype not in loaded_collision:
                collision_data = _load_collision_for_tileset(
                    tilemap_data, ttype, collision_dir, cache
                )
                loaded_collision[ttype] = collision_data

            collision_data = loaded_collision[ttype]
            if collision_data is None:
                continue

            world_shapes = []
            region_layer = 1
            region_mask = 0xFFFFFFFF
            for region in collision_data.regions.values():
                if not world_shapes:
                    region_layer = region.collision_layer
                    region_mask = region.collision_mask
                ox = region.region_rect[0] * rs
                oy = region.region_rect[1] * rs
                world_shapes.extend(shape.transform(ox, oy, rs) for shape in region.shapes)
            if not world_shapes:
                continue

            game_obj = MapObject(
                x=x,
                y=y,
                surface=surf,
                collision_shape=world_shapes[0],
                collision_shapes=world_shapes,
                collision_layer=region_layer,
                collision_mask=region_mask,
            )
            objects.append(game_obj)

    return objects


def _load_collision_for_tileset(
    tilemap_data: TilemapData,
    ttype: int,
    collision_dir: Path,
    cache: Optional[CollisionCache],
) -> Optional[ObjectCollisionData]:
    """Load (or retrieve from cache) collision data for a tileset index."""
    if ttype < 0 or ttype >= len(tilemap_data.parsed.tilesets):
        return None

    tileset_path = tilemap_data.parsed.tilesets[ttype].path
    coll_filename = _resolve_object_collision_filename(tileset_path)
    coll_path = collision_dir / coll_filename

    if cache is not None:
        return cache.get_object_collision(coll_path)
    return load_object_collision(coll_path)
