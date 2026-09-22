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
    """Missing file gives None; unparsable file raises."""
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
    render_scale: float = 1.0,
) -> CharacterCollision | None:
    """Missing file gives None; unparsable file raises."""
    collision_path = Path(collision_path)

    if not collision_path.exists():
        return None

    try:
        with open(collision_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_character_collision(data, render_scale=render_scale)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise CollisionParseError(f"Cannot load {collision_path}: {e}") from e


def load_object_collision(
    collision_path: Union[str, Path],
) -> ObjectCollisionData | None:
    """Missing file gives None; unparsable file raises."""
    collision_path = Path(collision_path)

    if not collision_path.exists():
        return None

    try:
        with open(collision_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_object_collision(data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise CollisionParseError(f"Cannot load {collision_path}: {e}") from e
