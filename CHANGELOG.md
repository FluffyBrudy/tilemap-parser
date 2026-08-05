# Changelog

## 5.0.1 — 2026-08-05

### Major Features Added
- **Physics world and bodies**: `PhysicsWorld` (tile layer + bodies + one-way platforms), `Body` (static/kinematic modes, shape + collision layer/mask), world-bound movement via `CollisionRunner.attach()` / `from_world()`, `collides_with_body()`, `move_grounded()` and `MovementMode.GROUNDED`
- **Pathfinding**: `NavGrid`, `Pathfinder` (A*), `PathFollower`, and grid erosion for inflated walls
- **TMX/TSX tileset support** with a Tiled-format converter
- **Global id (gid) system** with flip flags aligned to the Tiled spec
- **Y-sort rendering**: depth-based draw order with `extra_objects`
- **Linear-scan one-vs-all collision queries** in `ObjectCollisionManager`

### Updates
- Object collision bridge: `load_map_objects()` with per-region layer/mask, object scaling, and non-collidable objects
- Collision protocols unified under `ICollidable`
- Track referenced tilesets per object layer
- Webdocs revamp: new site UI plus physics, pathfinding, and particle guides

### Bug fixes
- Tile rendering bound check in edge chunks
- Strict gid validation, multiline properties, Tiled flip-flag alignment
- Capsule polygon duplicate vertices, polygon-shaped sprite collision (`get_shape_bounds`), crate friction in examples, dead code removal

### Examples
- `full-physics-world`, `physics-crate`, `full-collision`, `full-pathfinding`

## 4.0.0 — 2026-07-11

### Major Features Added
- **Camera system**: New `Camera` class with centered or deadzone follow modes, lerp smoothing, screen-shake effects, and bounds clamping
- **Particle system**: Full particle system with configurable emitters, 8 particle shapes, color transitions, alpha fading, gravity, rotation, and batch rendering with `ParticleSystem`, `ParticleEmitter`, `ParticleRenderer`, and `SpriteBatchRenderer`
- **Chunked tile rendering**: `TileLayerRenderer` now uses chunk-based culling for efficient rendering of large maps
- **Render stats**: `LayerRenderStats` provides drawn/skipped tile counts and visible layer info for debugging

### New Utilities
- `clear_texture_caches()` to clear internal particle texture caches
- `parse_particle_file()` and `parse_particle_dict()` to load particle configs

### Updates
- Updated docs link from deepwiki to vercel

## 3.0.0 — 2026-05-18

### Major restructuring
- Reorganized flat package into subpackages: `parser/`, `runtime/`, `utils/`
- Broke up mixed modules: `animation.py` → parser + runtime, `collision.py` → parser + runtime
- Renamed `collision_runner.py` → `tile_collision.py`
- Moved collision loader functions into `parser/collision_loader.py` (cleaner I/O separation)

### New features
- **Capsule collision**: Full support across all shape pairs (capsule-vs-circle, capsule-vs-capsule, capsule-vs-rect, capsule-vs-polygon)
- **CollisionHit helpers**: `resolve()`, `involves(obj)`, `other(obj)` for ergonomic separation and queries
- **`should_collide()`** made public (aliased as `_should_collide` for backward compat)

### Bug fix
- Fixed `CollisionRunner._get_collision_normal_from_motion()` polygon centroid calculation: tile offset (`ox`/`oy`) was incorrectly divided by vertex count, causing all slide normals to be wrong and `slope_slide=True` to fully block instead of sliding

### API changes
- `ICollidableObject` protocol: `collision_layer` and `collision_mask` are now optional (accessed via `getattr` with defaults)
- `ObjectCollisionManager.check_object()`: more robust identity checks
- `check_collision()` now warns on unhandled shape pairs

### Internal
- Decoupled `CollisionRunner` from `CollisionCache` (cache removal was dead code)
- Geometry utilities now include AABB for `CapsuleShape`
- All geometry functions re-exported through `utils/__init__`

### Testing
- 15 new capsule collision tests
- 4 new CollisionHit helper tests
- All existing tests preserved (177 → 190 passing)

## 2.0.4 — earlier

### Fixes & improvements
- Added missing geometry functions to package `__all__` exports
- Improved documentation and webdocs
