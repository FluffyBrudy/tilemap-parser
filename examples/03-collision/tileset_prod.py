"""
Tileset Collision - Production Mode

USAGE: Run with tilemap-parser installed.

    pip install tilemap-parser
    python examples/03-collision/tileset_prod.py
"""

from pathlib import Path

from tilemap_parser import load_map
from tilemap_parser.collision import load_tileset_collision, CollisionCache


def main():
    # The editor stores tileset collision files at:
    #   <data_root>/collision/<tileset_stem>.collision.json
    #
    # In your game, data_root comes from settings.json.  Here we point at
    # the bundled example fixtures so the script is runnable out of the box.
    examples_dir = Path(__file__).parent.parent.parent / "examples"
    data_root = examples_dir / "fixtures"

    # Load map
    map_path = examples_dir / "map.json"
    if not map_path.exists():
        print(f"Map not found: {map_path}")
        return

    data = load_map(str(map_path))

    # Build tile map for collision checking
    # Key: (tile_x, tile_y), Value: tile_variant
    tile_map = {}
    for layer in data.get_layers(layer_type="tile"):
        for (x, y), tile in layer.tiles.items():
            if isinstance(tile.ttype, int):
                tile_map[(x, y)] = tile.variant

    print(f"Tile map: {len(tile_map)} tiles")

    # Load tileset collision using cache
    cache = CollisionCache()
    collision_path = data_root / "collision" / "Terrain (32x32).collision.json"
    tileset_collision = cache.get_tileset_collision(collision_path)

    if tileset_collision is None:
        print(f"No collision data at: {collision_path}")
        return

    # Check collision for a specific tile position
    tile_x, tile_y = 5, 3
    tile_id = tile_map.get((tile_x, tile_y))

    if tile_id and tileset_collision.has_collision(tile_id):
        print(f"\nTile ({tile_x}, {tile_y}) has collision (id={tile_id})")

        world_x = tile_x * data.tile_size[0]
        world_y = tile_y * data.tile_size[1]
        shapes = tileset_collision.get_world_shapes(tile_id, world_x, world_y)

        for i, shape in enumerate(shapes):
            print(f"  Shape {i}: {len(shape.vertices)}-vertex polygon")
            print(f"    One-way: {shape.one_way}")
    else:
        print(f"\nTile ({tile_x}, {tile_y}) has no collision")

    # Preload all tilesets at game startup
    print("\nPreloading collision data...")
    tileset_names = [
        "Terrain (32x32)",
        "objects",
        "structures",
    ]
    for name in tileset_names:
        path = data_root / "collision" / f"{name}.collision.json"
        cache.preload_tileset(path)
        print(f"  {path.name}: {'loaded' if path.exists() else 'not found'}")
    print("Done.")


if __name__ == "__main__":
    main()
