"""world.py — the physics space: tiles, one-way platform, solid bodies.

This module owns the scene geometry: the tile layer, the tileset
collision data, and the solid bodies (pushable crates + a layer-2
pillar).  Nothing moves here — movement happens in main.py through a
CollisionRunner attached to the world.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tilemap_parser import Body, PhysicsWorld, RectangleShape
from tilemap_parser.parser.collision import (
    CollisionPolygon,
    TileCollisionData,
    TilesetCollision,
)

TILE = 32
COLS, ROWS = 26, 15
GRAVITY_GROUND_Y = 12 * TILE  # top of the ground row (the floor line)

FULL_TILE = [(0.0, 0.0), (float(TILE), 0.0), (float(TILE), float(TILE)), (0.0, float(TILE))]

# Collision layers: the player lives on layer 1 with a mask that excludes
# layer 2, so it walks through the pillar.  Crates keep the default mask
# (everything), so they stop at it.  Bodies only collide when both sides'
# layer/mask agree (see docs/physics-world.md).
PILLAR_LAYER = 2


def build_world():
    """Create the world: ground, walls, platforms, crates and the pillar."""
    tile_map: dict[tuple[int, int], int] = {}
    for x in range(COLS):
        for y in (12, 13):
            tile_map[(x, y)] = 0  # ground, solid
    for y in range(8, 12):
        tile_map[(20, y)] = 0  # right wall
    for x in range(12, 16):
        tile_map[(x, 9)] = 1  # one-way platform (tile id 1)

    tileset = TilesetCollision(
        tileset_name="ground",
        tile_size=(TILE, TILE),
        tiles={
            0: TileCollisionData(
                tile_id=0,
                shapes=[CollisionPolygon(vertices=FULL_TILE)],
            ),
            1: TileCollisionData(
                tile_id=1,
                shapes=[CollisionPolygon(vertices=FULL_TILE, one_way=True)],
            ),
        },
    )
    world = PhysicsWorld(
        tile_map=tile_map, tileset_collision=tileset, tile_size=(TILE, TILE)
    )

    for x in (8, 10, 13):
        world.add_body(
            Body(
                RectangleShape(width=TILE, height=TILE),
                x=x * TILE,
                y=GRAVITY_GROUND_Y - TILE,
                mode="kinematic",
                game_id="crate",
            )
        )
    world.add_body(
        Body(
            RectangleShape(width=TILE, height=6 * TILE),
            x=16 * TILE,
            y=6 * TILE,
            mode="static",
            collision_layer=PILLAR_LAYER,
            game_id="pillar",
        )
    )
    return world
