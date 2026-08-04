# Physics Authoring System — Migration Plan

Goal: reshape the runtime into a Godot-style physics authoring system.

One space (`PhysicsWorld`), bodies authored into it (`world.add_body(box)`),
tiles and bodies resolved uniformly by one movement resolver — without ever
rewriting the stable `move_platformer` / `move_platformer_with_slide`
algorithms or breaking the parser surface.

## Answer to the ordering question

- **Step 0 = module decomposition** (pure split, zero logic change) so the
  physics work lands in correctly-scoped files instead of making
  `tile_collision.py` (2157 lines) worse. DONE.
- **Steps 1+2 folded into one feature line** (per maintainer decision):
  the tile-source seam was a prerequisite of the bodies work, so it ships
  as one 5.0 feature, committed per stage, nothing released until every
  stage is done. No version bump — version stays at 4.2.8 until release.
- **Rigid dynamics (impulse solver, mass, friction) is NOT in scope** — that
  requires embedding a physics engine (Pymunk/Box2D). We provide the
  CharacterBody2D model: scripted velocity + collision resolution. True
  RigidBody2D behavior = deferred, possibly never.

## Locked design decisions

- One distribution, semver + deprecation cycle (Django-style: deprecate in N,
  remove in N+2).
- Parser surface never breaks. Top-level `tilemap_parser.__init__` exports are
  the public contract and never change. Module moves are internal; old module
  paths (`runtime.tile_collision`, `runtime.object_collision`) become
  re-export shims emitting `DeprecationWarning`, removed at 6.0.
- New modules: `runtime/world.py` (PhysicsWorld), `runtime/body.py` (Body).
  New top-level exports: `PhysicsWorld`, `Body`.
- Runner bound to a world (Godot's global-space model):
  `CollisionRunner.from_world(world, game_type)` / `runner.attach(world)`.
  Legacy `CollisionRunner(tile_size)` + per-call `(tileset_collision, tile_map)`
  API stays a warning-free tile-only adapter (no DeprecationWarning yet —
  deferred to Step 4 cleanup so the parity suite proves equivalence
  warning-free).
- Body primitives only: `RectangleShape` | `CircleShape` | `CapsuleShape`.
  Polygon shapes stay in `MapObject`'s lane (deferred unification).
- Bodies participate in solid blocking + ground landing (per-shape top-surface
  dispatcher), NOT slope walking (tile-only).
- Push transfer is a documented game-side recipe, matching Godot's own
  pattern (`CharacterBody2D` does not auto-push boxes):
  `hit_wall_x` -> `box.vx = player.vx` -> `move_grounded(box, dt, velocity=...)`.

## Module decomposition (Step 0)

Current state: `runtime/tile_collision.py` = 2157 lines (geometry primitives +
`CollisionResult` + 4 movement modes + slope queries + config validation),
`runtime/object_collision.py` = 504 lines (narrowphase + hits + manager),
`utils/geometry.py` = 757 (shape math, left as-is — coherent library).

Principles:

- **Split only what the physics work touches.** `tile_collision.py` and
  `object_collision.py` split; parser, particles, renderer, map_loader etc.
  stay (churning the stable parser surface is not justified by this work).
- **`CollisionRunner` stays ONE public class** — per-mode implementations split
  via composition: each mode module exposes a plain function taking `self`,
  and the runner assigns them as class attributes
  (`move_and_slide = slide.move_and_slide`), so `runner.move_platformer(...)`
  call sites never change.
- **The shared narrowphase is extracted once** — sprite-vs-body tests in the
  physics work and `ObjectCollisionManager` both consume it.
- Old module paths become silent-until-6.0 re-export shims
  (`DeprecationWarning`); in-repo tests/examples are updated to new paths in
  the same commit.
- Mechanical moves only: `git mv` code, zero logic edits. Full suite green =
  proof of parity before any physics work begins.

Target layout (runtime):

```
runtime/
├── world.py            NEW: PhysicsWorld (space) — the tile layer + bodies
├── body.py             NEW: Body + BodyMode + top_y_at / as_polygon
├── collision/          DONE (Step 0): split from object_collision.py
│   ├── shapes.py       narrowphase dispatch (CollisionInfo, _get_shapes,
│   │                   _combined_aabb, _check_pair, _flip_result)
│   ├── hit.py          CollisionHit, should_collide (+ _should_collide alias),
│   │                   check_collision
│   └── manager.py      ObjectCollisionManager (spatial grid)
├── movement/           DONE (Step 0): split from tile_collision.py
│   ├── types.py        CollisionResult, MovementMode, Vector2
│   ├── runner.py       CollisionRunner config / dispatch / from_game_type /
│   │                   validate / from_world / attach / detach
│   ├── queries.py      the seam — _collides_at*, _find_walkable_ground_y,
│   │                   _walkable_slope_at, _first_colliding_shape;
│   │                   body-aware via world.collides_with_body / top_y_at
│   ├── slide.py        move_and_slide
│   ├── grounded.py     move_grounded
│   ├── platformer.py   move_platformer + move_platformer_with_slide
│   │                   (the stable core)
│   └── rpg.py          move_rpg
├── polygon_query.py    DONE (Step 0): zero-alloc polygon-vs-shape primitives
├── protocols.py        DONE (Step 0): ICollidable, ICollidableObject,
│                       ICollidableSprite, ExtraObject, ShapeType/ShapePrimitive
├── tile_collision.py   SHIM: re-export (DeprecationWarning) until 6.0
├── object_collision.py SHIM: re-export (DeprecationWarning) until 6.0
└── ... unchanged: collision_cache, map_loader, map_object, renderer, camera,
    animation_player, particles, area_node
```

The planned `solids/` package (protocol + tile_layer + body_layer) was NOT
taken — the seam is implemented more cheaply: movement queries accept a
`world=None` kwarg and resolve tiles/bodies through the world when attached,
reusing `should_collide` + the shared narrowphase directly.

Result: no module over ~800 lines; the physics space/body code has a home;
`collision/shapes.py` is the single shared narrowphase for object manager AND
movement resolver.

## Maintainability note (deviations from the plan)

Three decisions deviate from the original plan.  Assessment of what they cost:

- **No `solids/` package — the seam is a `world=None` kwarg.**  No structural
  problem today; exactly two solid sources exist (tiles, bodies) and the world
  owns both.  `ICollisionSolidSource` would be indirection for a hypothetical
  third source (AGENTS: don't refactor for hypothetical flexibility).  Two
  named hotspots to watch:
  - The world-resolution block was copy-pasted in 5 mode-method sites
    (grounded, rpg, slide, platformer x2) — already extracted into
    `CollisionRunner._resolve_world(world)` (see commit for Step 1/2 notes).
  - The body-hook pattern ("after tile scan, check bodies") lives in 5 sites
    (4 query functions + `platformer.py`'s inline Y-scan, which is a separate
    codepath from the queries because it gates one-ways by `vy`/approach).
    Escape hatch if body resolution ever grows (broadphase for many bodies,
    kinematic rules): extract one `_collides_with_solids` query.
- **Legacy per-call API stays warning-free (deprecation deferred to Step 4).**
  The actual cost: every future movement feature must thread both paths —
  the folded Step 1+2 work paid this as a `world=None` kwarg on every query.
  Safe because the parity tests run both paths and assert identical results;
  the legacy path is a thin tile-only adapter by construction.  The
  deprecation surface (Step 4) enumerates the migration.
- **Vertex-in-rect is half-open in `polygon_query.py`.**  The old inclusive
  bounds (`<=`) treated resting contact as a collision: a crate sitting flush
  on a floor tile could not be pushed across a tile seam.  The check is now
  `rect_x <= vx < rx2 and rect_y <= vy < ry2` in both offset variants.  The
  object-manager contract (`rect_vs_rect` / `aabb_overlap` in
  `utils/geometry.py`) stays inclusive — depth-0 edge touching counts there —
  so body-vs-body blocking is unaffected.  Convention: both the right and
  bottom edges are exclusive (consistent with the ray-cast and segment
  tests, which are open at endpoints); a "wall" for a floor-level
  object must protrude above the floor line (a flush tile is floor
  continuation).  Also in this area: `PhysicsWorld.collides_with_body`
  excludes the queried sprite by identity (kinematic crates must not collide
  with themselves).
- **Version stays 4.2.8 until every step is done.**  Not a code concern; the
  property worth recording: `main` is untouched by this work (Step 0's commit
  was moved off it), so `main` stays releaseable at 4.2.8 at any point — the
  entire physics feature lives on `feat/physics-bodies` until release.

## Roadmap (with hour estimates)

### Step 0 — Module split (v4.3.x) — ~3-4 h — DONE

Mechanical, revertible, zero API change. Completed with an ast-based
extraction script (split_runtime.py, no logic edits): baseline 501 tests
green before and after; suite re-run with `-W error::DeprecationWarning` to
prove no shim is triggered internally.

- [x] 0.1 Extract `movement/types.py` + `polygon_query.py` from
      `tile_collision.py`. (~1 h)
- [x] 0.2 Split `object_collision.py` -> `collision/{shapes,hit,manager}.py`.
      (~1 h)
- [x] 0.3 Split `CollisionRunner` into per-mode modules:
      `movement/{runner,queries,slide,grounded,platformer,rpg}.py`,
      composed as class attributes on the single public class. (~1.5 h)
- [x] 0.4 Old modules become deprecated re-export shims; in-repo imports
      updated; top-level exports unchanged. (~0.5 h)
- [x] 0.5 Full suite green. (~0.5 h)

Notes:

- `ICollidable` / `ICollidableObject` / `ICollidableSprite` now live in
  `runtime/protocols.py`; `runtime/__init__.py` imports them from there.
- `_should_collide` kept as an alias in `collision/hit.py` for parity.
- The only test behavior change was `test_object_collision.py` monkeypatch:
  it now patches `collision.manager.check_collision` (where the name is
  resolved) instead of the old module attribute.

### Step 1 + Step 2 — The space and bodies (one 5.0 feature) — DONE

Folded per maintainer decision: the tile-source seam (Step 1) was a
prerequisite of the bodies work (Step 2) — one feature line, committed per
stage, no release until all stages are done.  Work landed on branch
`feat/physics-bodies` (Step 0's commit was moved off `main`).

- [x] 1.1 Coordinate space pinned: `test_loaded_object_position_consistency`
      (test_map_object.py) proves MapObject vertices are owner-local and the
      narrowphase applies `obj.x + vertex` once.  Bodies reuse the same
      contract — no new test needed. (covered in a4c5120)
- [x] 1.2/1.3 Tile-source seam via `world=None` kwarg on the movement queries;
      a runner attached to a world (`from_world` / `attach`) resolves tiles
      through the world.  No `solids/` package — smaller than planned.
      (62f1e1b)
- [x] 1.4 Parity proven: `test_runner_world_parity_*` (world-attached vs
      explicit per-call args) — identical results for platformer walk/jump,
      falling, wall hits, grounded mode; geometry adoption on attach.
      (62f1e1b)
- [x] 2.1 `Body`: primitive `collision_shape` (rect/circle/capsule; polygons
      rejected — MapObject lane), `x/y/vx/vy/on_ground`,
      `collision_layer/mask`, `mode: "static" | "kinematic"`.  Geometry
      helpers: `top_y_at(world_x)` (top-surface sampler) and
      `as_polygon()` (slide normals). (a4c5120)
- [x] 2.2 `PhysicsWorld`: `from_map(mapdata, tileset_collision)` (adopts the
      map's tile_size/render_scale), `add_body` / `remove_body` /
      `clear_bodies`, `collides_with_body(sprite)` via `should_collide` +
      the shared narrowphase. (a4c5120, 87cc5d3)
- [x] 2.3 `CollisionRunner.from_world()` / `attach()` / `detach()`; world
      overrides tile source and grid geometry.  Legacy per-call API stays
      warning-free (deprecation deferred to Step 4 — see locked decisions).
      (62f1e1b)
- [x] 2.4 Bodies block movement: `_collides_at`, `_collides_at_platformer`,
      the inline platformer Y-scan, and `_first_colliding_shape` (bodies
      surface as `as_polygon()` so slide-mode normals work); bodies are
      landing surfaces: `_find_walkable_ground_y` samples `body.top_y_at`
      (rect top, circle/capsule caps) — step-up onto small crates comes
      through the existing step logic for free. (87cc5d3, adffc64)
- [x] 2.5 Tests: land on box top / circle / capsule, blocked by box side,
      step-up small crate, too-tall crate blocks, layer filtering, world
      parity, attach geometry adoption. (a4c5120–adffc64)

### Step 3 — Bodies move in the space (v5.x) — ~3-4 h

- [x] 3.1 `move_grounded(box, world, dt, velocity=...)` path exercised against
      world: box slides, stops at tile walls and other bodies (body-vs-body
      via narrowphase). (~2 h)
- [x] 3.2 Push recipe documented in README/webdocs + example update
      (`examples/physics-crate` or extend platformer-with-slide). (~1 h)
      Done: README section + `examples/physics-crate/main.py` (3 crates:
      box blocks box, crate stops at tile wall, player stands on crates).
- [x] 3.3 Tests: box pushed by velocity stops at tile wall; box blocks another
      box; player stands on a box while it is static. (~1 h)

### Step 4 — Cleanup (v6.0) — ~1-2 h

- [ ] 4.1 Remove deprecated legacy runtime API (`CollisionRunner` legacy
      constructor + per-call methods — including the DeprecationWarning
      deferred from 2.3) and the two re-export shims. (~1 h)
- [ ] 4.2 CHANGELOG migration guide; examples migrated. (~0.5-1 h)

### Deprecation surface (Step 4 migration manifest)

`from_game_type` is NOT deprecated — only the per-call
`(tileset_collision, tile_map)` move arguments and the plain
`CollisionRunner(tile_size=...)` constructor are.  Migration order:

1. **Flip the parity tests first** (`tests/test_body.py`,
   `test_runner_world_parity_*` + the mode tests): they run world-attached
   vs legacy side-by-side today; converting the legacy side to
   world-attached while keeping the asserts proves equivalence before
   anything else moves.
2. **Migrate the legacy suites file by file**, each green before the next:
   - `tests/test_tile_collision.py` — 21 per-call sites
     (`from_game_type` + per-call args)
   - `tests/test_move_grounded.py` — 15 sites, incl. plain
     `CollisionRunner(tile_size=(32, 32))` at :76 (the legacy constructor)
   - `tests/test_integration_collision.py` — 9 sites
   - `tests/test_render_scale.py` — 7 plain-constructor sites (:261-334)
     + per-call moves
3. **Emit `DeprecationWarning`** on the legacy constructor + per-call args
   in a 5.x release (Django-style: deprecate in N, remove in N+2).
4. **Remove at 6.0**, then migrate the examples (plan 4.2):
   `examples/platformer/src/main.py`, `examples/platformer-with-slide/src/game.py`,
   `examples/tiny-quest/src/core/scene.py`,
   `examples/rpg-pathfinding/main.py`,
   `examples/comparison/collision-move-modes.py` — all `from_game_type`
   + per-call args today.

## Deferred (explicitly out of scope, revisit only on real use cases)

- Polygon shapes on `Body` (unify `MapObject` as a body).
- Multiple shapes per body (CollisionShape2D children plurality).
- `world.step(dt)` physics-engine integration (real RigidBody2D dynamics).
- Area2D-style detection-only bodies (sprite-vs-sprite stays in
  `ObjectCollisionManager`).
- Splitting `parser/map_parse.py` (527) / `tmx_converter.py` (448) /
  `runtime/particles.py` (587) — stable surface, not part of this work.

## Total estimate

~16-22 h across 5 steps. Steps 0-2 (incl. the folded 1+2 feature) = the risky
core — parity-verified at every stage; Steps 3 = ~3-4 h (the remaining
feature work); Step 4 = ~1-2 h (cleanup).
