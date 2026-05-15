"""
Collision data loading utilities.

Provides file I/O functions that read collision JSON files from disk
and dispatch to the appropriate parser functions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from .collision import (
    CharacterCollision,
    CollisionParseError,
    ObjectCollisionData,
    TilesetCollision,
    parse_character_collision,
    parse_object_collision,
    parse_tileset_collision,
)


def load_tileset_collision(
    collision_path: Union[str, Path],
) -> TilesetCollision | None:
    """
    Load tileset collision data from a collision JSON file.

    The editor stores tileset collision files at:
        <data_root>/collision/<tileset_stem>.collision.json

    Args:
        collision_path: Direct path to the .collision.json file.

    Returns:
        TilesetCollision object, or None if the file does not exist.

    Raises:
        CollisionParseError: If the file exists but cannot be parsed.
    """
    collision_path = Path(collision_path)

    if not collision_path.exists():
        return None

    try:
        with open(collision_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_tileset_collision(data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise CollisionParseError(f"Cannot load {collision_path}: {e}") from e


def load_character_collision(
    collision_path: Union[str, Path],
) -> CharacterCollision | None:
    """
    Load character collision data from a collision JSON file.

    The editor stores character collision files at:
        <data_root>/character_collision/<character_name>.collision.json

    Args:
        collision_path: Direct path to the .collision.json file.

    Returns:
        CharacterCollision object, or None if the file does not exist.

    Raises:
        CollisionParseError: If the file exists but cannot be parsed.
    """
    collision_path = Path(collision_path)

    if not collision_path.exists():
        return None

    try:
        with open(collision_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_character_collision(data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise CollisionParseError(f"Cannot load {collision_path}: {e}") from e


def load_object_collision(
    collision_path: Union[str, Path],
) -> ObjectCollisionData | None:
    """
    Load object collision data from a collision JSON file.

    File format: ``<tileset_name>.object_collision.json``
    Typical path: ``<data_root>/collision/<tileset_name>.object_collision.json``

    Args:
        collision_path: Direct path to the .object_collision.json file.

    Returns:
        ObjectCollisionData object, or None if the file does not exist.

    Raises:
        CollisionParseError: If the file exists but cannot be parsed.
    """
    collision_path = Path(collision_path)

    if not collision_path.exists():
        return None

    try:
        with open(collision_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_object_collision(data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise CollisionParseError(f"Cannot load {collision_path}: {e}") from e
