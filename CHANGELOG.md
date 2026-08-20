# Changelog

## 5.0.4 — 2026-08-20

### Updates
- `render_scale` support: `SpriteAnimationSet.load()` scales the spritesheet grid, and `parse_character_collision()` / `load_character_collision()` scale character shapes via `render_scale`

### Bug fixes
- Fixed atlas cell addressing with fractional `render_scale` and nonzero `grid_offset` in `SpriteAnimationSet`: the grid column/row counts are now pinned from the original sheet, and scales that produce zero-sized or non-fitting cells are rejected at load
- `parse_character_collision` now rejects non-finite (`nan`, `inf`) and invalid (`0`, negatives, non-numeric) `render_scale` values with `CollisionParseError`
- `CollisionCache._character_cache` is now typed for `(path, render_scale)` tuple keys

## 5.0.3 — 2026-08-06

### Updates
- New `wrap` particle mode for continuous media (mist, snow, rain, dust): particles never die; exiting the emission area toroidally re-enters on the opposite side with exact offset, velocity, alpha, and size preserved. Combine with `emit_field()` + `spawn_rate=0` for a persistent, birth/death-free field
- New field ergonomics: `ParticleSystem.emit_field(coverage, x, y, w, h)` fills an area once with density expressed as dimensionless coverage, backed by `ParticleSystemConfig.count_for_coverage()` and shape-aware `fill_area()` (circle emitters use their inscribed disc). Contract errors name the exact fields to set (`wrap`, `spawn_rate`)
- New `ParticleField` high-level helper: continuous-effect dials (`density`, `global_alpha` strength scale 0-1, `direction`/`speed`, `color`, `quality` budget, `ground_bias`) over wrapped fields, with `set_area`/`set_density`/`set_motion` refills; `set_color` and `global_alpha` restyle existing layers in place without rebuilding. Layer tuning ships as plain data — `FieldProfile`/`FieldLayerSpec` with the validated `FOG_PROFILE` constant (copy and tweak for your own moods; `fog()` factory removed)
- `ParticleField` gains a `blend` knob passing pygame blend flags to every particle draw: `pygame.BLEND_RGBA_ADD` gives additive (glowing) particles, `pygame.BLEND_PREMULTIPLIED` premultiplies the tinted sprites for cleaner overlap compositing. Default stays plain alpha blending. For scene glow, draw the field into a black RGB buffer and blit it with `pygame.BLEND_RGB_ADD` — fog adds light to the scene instead of occluding it
- String enums are now typed: `ParticleSystemConfig` fields use `Literal` types (`particle_shape`/`emission_shape`/`alpha_fade`) and `ParticleField` uses `quality: Literal['low','medium','high']` and `shape: Literal[...]`. The aliases `EmissionShape`, `ParticleShape`, `AlphaFadeMode`, `FieldQuality` are exported from `tilemap_parser` for type checkers; valid values still live in `EMISSION_SHAPES`, `PARTICLE_SHAPES`, `ALPHA_FADE_MODES`
- `ParticleField` accepts `direction="random"` for omnidirectional drift (every sheet picks a random angle), hiding the low-level `direction < 0` sentinel behind a readable value. `set_motion(direction="random")` works too; unknown strings raise
- `FieldProfile.with_alpha(factor, name=None)` derives a new immutable profile with every layer alpha scaled (clamped 0-255) — author named variants like `FOG_PROFILE.with_alpha(0.5, name="mist")` without ever mutating the source profile. `global_alpha` remains the live strength control
- New `fog` particle shape: flat soft-edged square that tiles into continuous haze (no bright core, unlike `smoke`)
- New optional `fade_peak_alpha` config field: `fade_both` can now follow a smooth `0 -> peak -> 0` bell curve (e.g. fog), instead of peaking at the max of start/end alpha
- `fade_both` no longer forces alpha to 255 at mid-life; it peaks at `max(start_a, end_a)` (or `fade_peak_alpha` when set)

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
