# tilemap-parser

Standalone parser/loader for [tilemap-editor](https://pypi.org/project/tilemap-editor/) JSON maps, sprite animations, and a collision detection runtime.

## Install

```bash
pip install tilemap-parser
```

## Quick start

```python
from tilemap_parser import load_map, TileLayerRenderer, Camera, ParticleField, FOG_PROFILE

game_data = load_map("path/to/map.json")
renderer = TileLayerRenderer(game_data)

camera = Camera(800, 600, mode="centered")
camera.follow(player)

# Persistent fog: fill once, wrap forever — no particle churn
mist = ParticleField(
    area=(0, 0, 800, 600),
    profile=FOG_PROFILE,   # plain data — copy and tweak for your own moods
    color=(200, 50, 80),
    global_alpha=0.5,
)
```

## Features

- **Map parsing** — tilemaps, layers, objects, and autotile data from JSON
- **Collision** — tile-based (`CollisionRunner`) and object-to-object (`ObjectCollisionManager`) with rect, circle, capsule, and polygon shapes
- **Physics** — `PhysicsWorld` with static/kinematic `Body` solids and one-way platforms
- **Particles** — wrapped continuous fields (`ParticleField`, `FOG_PROFILE`), burst emitters, alpha fades, and batch rendering (`SpriteBatchRenderer`)
- **Pathfinding** — A* `Pathfinder` over eroded `NavGrid`s
- **Animation** — frame-based `AnimationPlayer`, plus a `Camera` with centered/deadzone follow
- **Rendering** — chunked `TileLayerRenderer` and `LayerRenderStats`

## Requirements

- Python 3.10+
- `pygame-ce>=2.5` (installed automatically)

## Links

- **Documentation**: https://tilemap-parser.vercel.app/
- **Repository**: https://github.com/FluffyBrudy/tilemap-parser