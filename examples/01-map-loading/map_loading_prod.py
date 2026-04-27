"""
Map Loading - Production Mode

USAGE: Run this script with tilemap-parser installed from PyPI.
This is the recommended approach for production games.

    pip install tilemap-parser
    python examples/01-map-loading/map_loading_prod.py

NOTE: No sys.path manipulation needed. The package is installed system-wide.
"""

from tilemap_parser import load_map


def main():
    # Load a map file (adjust path as needed)
    map_path = "assets/maps/level_1.json"
    
    # Load the map with default settings
    # - Skips missing tileset images with warnings
    # - Searches relative to map file for tileset images
    data = load_map(map_path)
    
    # Access map metadata
    print(f"Tile size: {data.tile_size}")
    print(f"Map size: {data.map_size}")
    
    # Get all tile layers sorted by z_index
    tile_layers = data.get_layers(layer_type="tile", sort_by_zindex=True)
    print(f"\nTile layers ({len(tile_layers)}):")
    for layer in tile_layers:
        print(f"  {layer.name}: z_index={layer.z_index}, visible={layer.visible}")
    
    # Filter by visibility
    visible_layers = data.get_layers(include_hidden=False)
    print(f"\nVisible layers: {len(visible_layers)}")
    
    # Get layer by ID or name
    layer_by_name = data.get_layer("Terrain")
    layer_by_id = data.get_layer(0)
    
    # Build a tile lookup for collision systems
    tile_map = {}
    for layer in data.get_layers(layer_type="tile"):
        for (x, y), tile in layer.tiles.items():
            if isinstance(tile.ttype, int):
                tile_map[(x, y)] = tile.variant
    
    print(f"\nTile map has {len(tile_map)} tiles")
    
    # Get raw JSON for inspection/debugging
    raw = data.get_raw()
    print(f"\nMap version: {raw.get('meta', {}).get('version', 'unknown')}")


if __name__ == "__main__":
    main()