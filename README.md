# tilemap-parser

Standalone parser/loader for tilemap-editor JSON maps, sprite animations, and collision detection runtime.

## Features

- **Map parsing**: Load and query tilemaps, layers, objects, and autotile data from JSON
- **Animation**: Frame-based sprite animation with `AnimationPlayer`
- **Collision (tile-based)**: Polygon collision detection for tilemaps with slide, platformer, and RPG movement modes via `CollisionRunner`
- **Collision (object-to-object)**: Spatial-grid mixed-shape collision detection (rect, circle, capsule, polygon) with layer filtering via `ObjectCollisionManager`
- **Capsule support**: Full capsule collision against all shape types
- **Hit helpers**: `CollisionHit.resolve()`, `involves()`, `other()` for ergonomic separation

## Quick Start

```python
from tilemap_parser import load_map, TileLayerRenderer

game_data = load_map("path/to/map.json")
renderer = TileLayerRenderer(game_data)
```

```python
from tilemap_parser import (
    CollisionRunner, CollisionCache,
    ObjectCollisionManager, CircleShape, RectangleShape,
)

# Tile-based collision
cache = CollisionCache()
tileset = cache.get_tileset_collision("data/collision/tileset.collision.json")
runner = CollisionRunner.from_game_type("topdown", tile_size=(32, 32))

# Object-to-object collision
manager = ObjectCollisionManager()
manager.add_object(player)
for hit in manager.check_all_collisions():
    hit.resolve()  # separate both objects
```

## Links

- **Docs**: https://tilemap-parser.vercel.app/
- **Editor**: https://pypi.org/project/tilemap-editor/
- **Repository**: https://github.com/FluffyBrudy/tilemap-parser
