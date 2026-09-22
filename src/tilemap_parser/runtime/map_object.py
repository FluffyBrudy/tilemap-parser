from __future__ import annotations

from pathlib import Path

import pygame
from pygame import Surface

from ..parser.collision import CollisionPolygon, ObjectCollisionData
from ..parser.collision_loader import load_object_collision
from .collision_cache import CollisionCache
from .map_loader import TilemapData



class MapObject:
    """
    Tilemap object with pre-scaled surface, position, and shapes in
    effective pixels; first shape doubles as collision_shape.
    """

    __slots__ = tuple(
        sorted(
            (
                "x",
                "y",
                "surface",
                "collision_shape",
                "collision_shapes",
                "collision_layer",
                "collision_mask",
                "y_sort_origin",
                "ttype",
            )
        )
    )

    def __init__(
        self,
        x: float,
        y: float,
        surface: Surface | None = None,
        collision_shape: CollisionPolygon | None = None,
        *,
        collision_shapes: list[CollisionPolygon] | None = None,
        collision_layer: int = 1,
        collision_mask: int = 0xFFFFFFFF,
        y_sort_origin: int | None = None,
        ttype: int = -1,
    ) -> None:
        self.x = x
        self.y = y
        self.surface = surface
        if collision_shapes is not None:
            self.collision_shapes = collision_shapes
            self.collision_shape = collision_shapes[0] if collision_shapes else None
        elif collision_shape is not None:
            self.collision_shapes = [collision_shape]
            self.collision_shape = collision_shape
        else:
            self.collision_shapes = []
            self.collision_shape = None
        self.collision_layer = collision_layer
        self.collision_mask = collision_mask
        self.y_sort_origin = y_sort_origin
        self.ttype = ttype

    @property
    def has_collision(self) -> bool:
        return len(self.collision_shapes) > 0


def _resolve_object_collision_filename(tileset_path: str | Path) -> str:
    return f"{Path(tileset_path).stem}.object_collision.json"


def load_map_objects(
    tilemap_data: TilemapData,
    collision_dir: str | Path,
    *,
    cache: CollisionCache | None = None,
    require_collision: bool = False,
) -> list[MapObject]:
    """Every object layer; pre-scaled; cached per tileset; require_collision
    drops visual-only objects (gate the rest on has_collision)."""
    collision_dir = Path(collision_dir)
    objects: list[MapObject] = []
    object_layers = tilemap_data.get_layers(layer_type="object")

    loaded_collision: dict[int, ObjectCollisionData | None] = {}

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
                collision_data = _load_collision_for_tileset(tilemap_data, ttype, collision_dir, cache)
                loaded_collision[ttype] = collision_data

            collision_data = loaded_collision[ttype]
            if collision_data is None:
                if require_collision:
                    continue
                game_obj = MapObject(
                    x=x,
                    y=y,
                    surface=surf,
                    collision_shape=None,
                    collision_shapes=[],
                    ttype=obj.ttype,
                )
                objects.append(game_obj)
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
                if require_collision:
                    continue
                game_obj = MapObject(
                    x=x,
                    y=y,
                    surface=surf,
                    collision_shape=None,
                    collision_shapes=[],
                    ttype=obj.ttype,
                )
                objects.append(game_obj)
                continue

            game_obj = MapObject(
                x=x,
                y=y,
                surface=surf,
                collision_shape=world_shapes[0],
                collision_shapes=world_shapes,
                collision_layer=region_layer,
                collision_mask=region_mask,
                ttype=obj.ttype,
            )
            objects.append(game_obj)

    return objects


def _load_collision_for_tileset(
    tilemap_data: TilemapData,
    ttype: int,
    collision_dir: Path,
    cache: CollisionCache | None,
) -> ObjectCollisionData | None:
    if ttype < 0 or ttype >= len(tilemap_data.parsed.tilesets):
        return None

    tileset_path = tilemap_data.parsed.tilesets[ttype].path
    coll_filename = _resolve_object_collision_filename(tileset_path)
    coll_path = collision_dir / coll_filename

    if cache is not None:
        return cache.get_object_collision(coll_path)
    return load_object_collision(coll_path)
