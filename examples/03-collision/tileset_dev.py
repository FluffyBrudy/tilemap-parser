"""
Tileset Collision - Development Mode

USAGE: Run from repository root with local source.

    python examples/03-collision/tileset_dev.py
"""

import sys
from pathlib import Path
import json

# Add local source to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tilemap_parser import load_map
from tilemap_parser.collision import parse_tileset_collision, load_tileset_collision


def main():
    script_dir = Path(__file__).parent.parent.parent / "examples"
    
    # Load map to get tileset info
    map_path = script_dir / "map.json"
    if not map_path.exists():
        print(f"Map not found: {map_path}")
        return
    
    data = load_map(str(map_path))
    print(f"Map: {data.map_size}, tile size: {data.tile_size}")
    
    # Method 1: Load collision from sidecar file
    # The collision file should be at: tileset.png -> tileset.collision.json
    tileset_path = script_dir / "terrain.png"
    collision = load_tileset_collision(str(tileset_path))
    
    if collision is None:
        print("No collision file found (this is optional)")
        return
    
    print(f"\nTileset: {collision.tileset_name}")
    print(f"Tile size: {collision.tile_size}")
    print(f"Tiles with collision: {len(collision.tiles)}")
    
    # Check which tiles have collision
    tiles_with_collision = [tile_id for tile_id in collision.tiles if collision.has_collision(tile_id)]
    print(f"Tiles with collision: {tiles_with_collision[:10]}...")
    
    # Get world-space collision shapes for a specific tile
    tile_id = 0
    world_x, world_y = 5 * data.tile_size[0], 3 * data.tile_size[1]
    shapes = collision.get_world_shapes(tile_id, world_x, world_y)
    
    print(f"\nTile {tile_id} at world ({world_x}, {world_y}):")
    print(f"  Collision shapes: {len(shapes)}")
    for i, shape in enumerate(shapes):
        print(f"  Shape {i}: {len(shape.vertices)} vertices, one_way={shape.one_way}")
    
    # Method 2: Parse from dict (for custom loading)
    collision_data = {
        "tileset_name": "custom_tileset",
        "tile_size": [32, 32],
        "tiles": {
            "0": {
                "tile_id": 0,
                "shapes": [
                    {
                        "vertices": [[1.0, 10.0], [30.0, 10.0], [30.0, 31.0], [1.0, 31.0]],
                        "one_way": False
                    }
                ]
            }
        }
    }
    custom_collision = parse_tileset_collision(collision_data)
    print(f"\nCustom collision: {custom_collision.tileset_name}")
    
    # Build tile map for collision checking
    tile_map = {}
    for layer in data.get_layers(layer_type="tile"):
        for (x, y), tile in layer.tiles.items():
            if isinstance(tile.ttype, int):
                tile_map[(x, y)] = tile.variant
    
    print(f"\nTile map: {len(tile_map)} tiles indexed")


if __name__ == "__main__":
    main()