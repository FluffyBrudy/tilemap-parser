"""
Collision data caching utilities.

Provides a cache layer on top of the collision loaders to avoid
repeated file I/O during runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Union

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
    Optimized collision data cache with fast lookups.

    Caches parsed collision data to avoid repeated file I/O and parsing.
    Useful for runtime performance in game engines.

    All methods accept the direct path to the .collision.json file.

    Typical paths produced by the editor:
        Tileset:   <data_root>/collision/<stem>.collision.json
        Character: <data_root>/character_collision/<name>.collision.json
        Object:    <data_root>/collision/<tileset_name>.object_collision.json
    """

    def __init__(self):
        self._tileset_cache: Dict[str, Optional[TilesetCollision]] = {}
        self._character_cache: Dict[str, Optional[CharacterCollision]] = {}
        self._object_cache: Dict[str, Optional[ObjectCollisionData]] = {}

    def get_tileset_collision(
        self, collision_path: Union[str, Path]
    ) -> Optional[TilesetCollision]:
        """Get tileset collision data (cached).

        Args:
            collision_path: Direct path to the .collision.json file.
        """
        key = str(Path(collision_path).resolve())

        if key not in self._tileset_cache:
            self._tileset_cache[key] = load_tileset_collision(collision_path)

        return self._tileset_cache[key]

    def get_character_collision(
        self, collision_path: Union[str, Path]
    ) -> Optional[CharacterCollision]:
        """Get character collision data (cached).

        Args:
            collision_path: Direct path to the .collision.json file.
        """
        key = str(Path(collision_path).resolve())

        if key not in self._character_cache:
            self._character_cache[key] = load_character_collision(collision_path)

        return self._character_cache[key]

    def get_object_collision(
        self, collision_path: Union[str, Path]
    ) -> Optional[ObjectCollisionData]:
        """Get object collision data (cached).

        Args:
            collision_path: Direct path to the .object_collision.json file.
        """
        key = str(Path(collision_path).resolve())

        if key not in self._object_cache:
            self._object_cache[key] = load_object_collision(collision_path)

        return self._object_cache[key]

    def clear(self):
        """Clear all cached collision data"""
        self._tileset_cache.clear()
        self._character_cache.clear()
        self._object_cache.clear()

    def preload_tileset(self, collision_path: Union[str, Path]):
        """Preload tileset collision data into cache.

        Args:
            collision_path: Direct path to the .collision.json file.
        """
        self.get_tileset_collision(collision_path)

    def preload_character(self, collision_path: Union[str, Path]):
        """Preload character collision data into cache.

        Args:
            collision_path: Direct path to the .collision.json file.
        """
        self.get_character_collision(collision_path)

    def preload_object(self, collision_path: Union[str, Path]):
        """Preload object collision data into cache.

        Args:
            collision_path: Direct path to the .object_collision.json file.
        """
        self.get_object_collision(collision_path)


_global_cache = CollisionCache()


def get_cached_tileset_collision(
    collision_path: Union[str, Path],
) -> Optional[TilesetCollision]:
    """Get tileset collision using global cache.

    Args:
        collision_path: Direct path to the .collision.json file.
    """
    return _global_cache.get_tileset_collision(collision_path)


def get_cached_character_collision(
    collision_path: Union[str, Path],
) -> Optional[CharacterCollision]:
    """Get character collision using global cache.

    Args:
        collision_path: Direct path to the .collision.json file.
    """
    return _global_cache.get_character_collision(collision_path)


def get_cached_object_collision(
    collision_path: Union[str, Path],
) -> Optional[ObjectCollisionData]:
    """Get object collision using global cache.

    Args:
        collision_path: Direct path to the .object_collision.json file.
    """
    return _global_cache.get_object_collision(collision_path)


def clear_collision_cache():
    """Clear global collision cache"""
    _global_cache.clear()
