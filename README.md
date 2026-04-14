# tilemap-parser

Standalone parser/loader package for map JSON produced by `tilemap-editor` plus sprite animation JSON.

## Install

```bash
pip install -e .
```

## Load map + inspect layers

```python
from tilemap_parser import load_map

data = load_map("assets/maps/level_1.json")

layers = data.get_layers(sort_by_zindex=True)
for layer in layers:
    print(layer.id, layer.name, layer.layer_type, layer.z_index, layer.properties)
```

## Tile image fetch API (variant + tileset)

```python
tile_surface = data.get_image(variant=12, ttype=0)
tile_surface2 = data.get_tile_surface(0, 12)
cell_surface = data.get_tile_surface_at("Ground", 10, 4)
```

## Raw payload access for debugging

```python
raw = data.get_raw()
```

`get_raw()` returns a deep-copied complete parsed root payload (including editor/project fields), so callers can inspect everything safely.

## Animation loading + playback helper

```python
from tilemap_parser import SpriteAnimationSet, AnimationPlayer

anim_set = SpriteAnimationSet.load("assets/anims/hero.anim.json")
player = AnimationPlayer(anim_set, "idle")

player.update(16.67)
frame_surface = player.get_current_image()
```

## Optional renderer for tile layers

```python
import pygame
from tilemap_parser import TileLayerRenderer, load_map

data = load_map("assets/maps/level_1.json")
renderer = TileLayerRenderer(data)
renderer.warm_cache()

screen = pygame.display.set_mode((1280, 720))
stats = renderer.render(screen, camera_xy=(camera_x, camera_y))
```

The renderer pre-indexes tile layers as `dict[layer_id, layer]`, sorts by `z_index`, ignores object layers, and caches `(tileset, variant)` cell surfaces to reduce repeated subsurface extraction.
