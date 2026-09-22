from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from ..parser.collision import (
    CharacterCollision,
    ObjectCollisionData,
    TilesetCollision,
)
from ..parser.collision_loader import (
    load_character_collision,
    load_object_collision,
    load_tileset_collision,
)


class CollisionCache:
    """
    Per-path parsed collision data. Typical editor paths:
    collision/<stem>.collision.json, character_collision/<name>.collision.json.
    """

    def __init__(self):
        self._tileset_cache: Dict[str, Optional[TilesetCollision]] = {}
        self._character_cache: Dict[Tuple[str, float], Optional[CharacterCollision]] = {}
        self._object_cache: Dict[str, Optional[ObjectCollisionData]] = {}

    def get_tileset_collision(
        self, collision_path: Union[str, Path]
    ) -> Optional[TilesetCollision]:
        key = str(Path(collision_path).resolve())

        if key not in self._tileset_cache:
            self._tileset_cache[key] = load_tileset_collision(collision_path)

        return self._tileset_cache[key]

    def get_character_collision(
        self, collision_path: Union[str, Path], render_scale: float = 1.0
    ) -> Optional[CharacterCollision]:
        key = (str(Path(collision_path).resolve()), render_scale)

        if key not in self._character_cache:
            self._character_cache[key] = load_character_collision(
                collision_path, render_scale=render_scale
            )

        return self._character_cache[key]

    def get_object_collision(
        self, collision_path: Union[str, Path]
    ) -> Optional[ObjectCollisionData]:
        key = str(Path(collision_path).resolve())

        if key not in self._object_cache:
            self._object_cache[key] = load_object_collision(collision_path)

        return self._object_cache[key]

    def clear(self):
        self._tileset_cache.clear()
        self._character_cache.clear()
        self._object_cache.clear()

    def preload_tileset(self, collision_path: Union[str, Path]):
        self.get_tileset_collision(collision_path)

    def preload_character(self, collision_path: Union[str, Path]):
        self.get_character_collision(collision_path)

    def preload_object(self, collision_path: Union[str, Path]):
        self.get_object_collision(collision_path)


_global_cache = CollisionCache()


def get_cached_tileset_collision(
    collision_path: Union[str, Path],
) -> Optional[TilesetCollision]:
    return _global_cache.get_tileset_collision(collision_path)


def get_cached_character_collision(
    collision_path: Union[str, Path],
    render_scale: float = 1.0,
) -> Optional[CharacterCollision]:
    return _global_cache.get_character_collision(collision_path, render_scale=render_scale)


def get_cached_object_collision(
    collision_path: Union[str, Path],
) -> Optional[ObjectCollisionData]:
    return _global_cache.get_object_collision(collision_path)


def clear_collision_cache():
    _global_cache.clear()
