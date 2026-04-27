"""
Map Loading - Development Mode

USAGE: Run this script from the repository root with the local source.
This approach is useful when developing tilemap-parser itself or when
you want to use an unreleased version.

    python examples/01-map-loading/map_loading_dev.py

NOTE: This adds the src/ directory to sys.path to import the local package.
For production use, install tilemap-parser via pip and use map_loading_prod.py
"""

import sys
from pathlib import Path

# Add local source to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tilemap_parser import load_map


def main():
    # Get path to example map (adjust path as needed)
    script_dir = Path(__file__).parent
    map_path = script_dir.parent.parent / "examples" / "map.json"
    
    if not map_path.exists():
        print(f"Map file not found: {map_path}")
        print("Run from repository root or adjust the map_path above.")
        return
    
    # Load the map
    data = load_map(str(map_path))
    
    # Access map metadata
    print(f"Tile size: {data.tile_size}")
    print(f"Map size: {data.map_size}")
    
    # Get all layers
    layers = data.get_layers(sort_by_zindex=True)
    print(f"\nLayers ({len(layers)}):")
    for layer in layers:
        tile_count = len(layer.tiles)
        print(f"  {layer.name}: {layer.layer_type} ({tile_count} tiles)")
    
    # Get a specific layer by name
    terrain = data.get_layer("Terrain")
    if terrain:
        print(f"\nTerrain layer found with {len(terrain.tiles)} tiles")
    
    # Get tile at position
    tile = data.get_tile_at("Terrain", 5, 5)
    if tile:
        print(f"Tile at (5,5): variant={tile.variant}, ttype={tile.ttype}")
    
    # Get tile surface for rendering
    surface = data.get_tile_surface_at("Terrain", 5, 5)
    if surface:
        print(f"Tile surface: {surface.get_size()}")
    
    # Access raw data for debugging
    raw = data.get_raw()
    print(f"\nRaw map has {len(raw.get('data', {}).get('layers', []))} layers in data section")


if __name__ == "__main__":
    main()