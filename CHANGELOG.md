# Changelog

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
