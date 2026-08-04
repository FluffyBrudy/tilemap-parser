# tilemap-parser

Standalone parser/loader for tilemap-editor JSON maps, sprite animations, and collision detection runtime.

## Features

- **Map parsing**: Load and query tilemaps, layers, objects, and autotile data from JSON
- **Chunked tile rendering**: Efficient visibility culling and chunk-based rendering with `TileLayerRenderer`
- **Camera system**: Centered/deadzone follow, lerp smoothing, screen-shake, and bounds clamping with `Camera`
- **Animation**: Frame-based sprite animation with `AnimationPlayer`
- **Particle system**: Configurable particle emitters with shapes, color transitions, alpha fades, gravity, and batch rendering with `ParticleSystem` + `SpriteBatchRenderer`
- **Collision (tile-based)**: Polygon collision detection for tilemaps with slide, platformer, and RPG movement modes via `CollisionRunner`
- **Collision (object-to-object)**: Spatial-grid mixed-shape collision detection (rect, circle, capsule, polygon) with layer filtering via `ObjectCollisionManager`
- **Capsule support**: Full capsule collision against all shape types
- **Hit helpers**: `CollisionHit.resolve()`, `involves()`, `other()` for ergonomic separation

## Quick Start

```python
from tilemap_parser import load_map, TileLayerRenderer, Camera

# Load map and set up renderer
game_data = load_map("path/to/map.json")
renderer = TileLayerRenderer(game_data)

# Set up camera
camera = Camera(800, 600, mode="centered")
camera.follow(player)
```

```python
from tilemap_parser import (
    CollisionRunner, CollisionCache,
    ObjectCollisionManager, CircleShape, RectangleShape,
    ParticleSystem, ParticleSystemConfig
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

# Particle system
particle_config = ParticleSystemConfig(
    particle_shape="circle",
    spawn_rate=10.0,
    max_particles=100,
    lifetime_min=0.5,
    lifetime_max=2.0,
    speed_min=50,
    speed_max=100,
    direction=270,
    spread=45,
    start_color_r=255, start_color_g=200, start_color_b=100, start_color_a=255,
    end_color_r=255, end_color_g=100, end_color_b=50, end_color_a=0,
    alpha_fade="fade_out",
    gravity_x=0,
    gravity_y=50,
)
particles = ParticleSystem(particle_config)
```

## Physics bodies

A `PhysicsWorld` is a single space holding the tile layer plus solid `Body` objects (static walls, kinematic crates). Attach a `CollisionRunner` to the world once and every move method resolves tiles and bodies through it — no per-call tile arguments.

> Full contract — object↔world↔`move_*`↔tiles↔rendering: see [docs/physics-world.md](docs/physics-world.md) and `examples/physics-crate/main.py`.

```python
from tilemap_parser import (
    Body, PhysicsWorld, CollisionRunner, RectangleShape,
    TilemapData, TilesetCollision, CollisionCache,
)

cache = CollisionCache()
tileset = cache.get_tileset_collision("data/collision/tileset.collision.json")
world = PhysicsWorld.from_map(game_data, tileset)   # adopts tile_size / render_scale

crate = Body(RectangleShape(width=16, height=16), x=320, y=480, mode="kinematic")
world.add_body(crate)

runner = CollisionRunner.from_world(world)          # or runner.attach(world)
```

Pushable crates are just kinematic bodies moved with an explicit velocity (gravity is skipped when `velocity=` is given):

```python
# player pressed against the crate -> hand the player's vx over
crate.vx = player.vx
result = runner.move_grounded(crate, None, None, dt, velocity=(crate.vx, 0))
if result.hit_wall_x:
    crate.vx = 0  # crate stopped against a tile wall or another body
```

`Body` accepts primitive shapes only (`RectangleShape`, `CircleShape`, `CapsuleShape`); use `MapObject` for polygon solids. Collision pairs honor both sides' `collision_layer` / `collision_mask`, and bodies are landing surfaces for platformer step-up (small crates are climbed, tall ones block like walls).

## Links

- **Docs**: [https://deepwiki.com/FluffyBrudy/tilemap-parser](https://deepwiki.com/FluffyBrudy/tilemap-parser)
- **Editor**: https://pypi.org/project/tilemap-editor/
- **Repository**: https://github.com/FluffyBrudy/tilemap-parser
