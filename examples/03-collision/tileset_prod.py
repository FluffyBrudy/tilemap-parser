"""
Tileset Collision - Production Mode

USAGE: Run with tilemap-parser installed.

    pip install tilemap-parser
    python examples/03-collision/tileset_prod.py
"""

from tilemap_parser import load_map
from tilemap_parser.collision import load_tileset_collision, CollisionCache


def main():
    # Load map
    data = load_map("assets/maps/level_1.json")
    
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
    tileset_collision = cache.get_tileset_collision("assets/terrain.png")
    
    if tileset_collision is None:
        print("No collision data (optional)")
        return
    
    # Check collision for a specific tile position
    tile_x, tile_y = 5, 3
    tile_id = tile_map.get((tile_x, tile_y))
    
    if tile_id and tileset_collision.has_collision(tile_id):
        print(f"\nTile ({tile_x}, {tile_y}) has collision (id={tile_id})")
        
        # Get collision shapes in world coordinates
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
    tileset_paths = [
        "assets/terrain.png",
        "assets/objects.png",
        "assets/structures.png",
    ]
    for path in tileset_paths:
        cache.preload_tileset(path)
    print("Done.")


if __name__ == "__main__":
    main()