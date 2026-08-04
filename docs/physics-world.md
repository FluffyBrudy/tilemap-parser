# PhysicsWorld — the object contract

How objects connect to the physics world, the `move_*` methods, tiles,
rendering, and each other.  Read this together with
`examples/physics-crate/main.py`, which implements the full loop.

## One space, one runner

`PhysicsWorld` is the single space everything resolves in.  It owns
exactly three things:

| Owned by the world | What it is |
|---|---|
| `tile_map` | The collision tile layer — `{(col, row): tile_id}` |
| `tileset_collision` | Tile geometry — `TilesetCollision` (polygon per tile id) |
| `bodies` | Solid `Body` objects — static walls, kinematic crates |

plus the space's grid geometry: `tile_size` and `render_scale`.

A `CollisionRunner` **attaches** to the world once and every `move_*`
call then resolves against the world's tiles *and* bodies uniformly —
you pass `None, None` for the tile arguments:

```python
world = PhysicsWorld.from_map(game_data, tileset_collision)   # adopts tile_size + render_scale
runner = CollisionRunner.from_world(world, game_type="platformer")
# legacy alternative: runner = CollisionRunner(...); runner.attach(world)

result = runner.move_platformer(player, None, None, dt, input_x=1.0, jump_pressed=False)
```

Rules of attachment:

- Attaching **overrides the tile source and grid geometry**; detach
  (`runner.detach()`) falls back to per-call tile arguments.
- The tile source is locked at attach: if your game has several maps,
  build one world per map and re-attach, or pass `world=other_world`
  as the last argument of any move call for a one-off override.
- Per-call `(tileset_collision, tile_map)` args still work — the world
  is optional, not required.

## The object contract (what a sprite must expose)

Anything you move through the runner must implement
`ICollidableSprite` — a plain attribute interface, no base class:

```python
class Player:
    def __init__(self, x, y):
        self.x = float(x)          # world position
        self.y = float(y)
        self.vx = 0.0              # velocity (physics modes)
        self.vy = 0.0
        self.on_ground = True      # grounded state (platformer)
        self.collision_shape = RectangleShape(width=24, height=28)
        self.collision_layer = 1   # optional, defaults
        self.collision_mask = 0xFFFFFFFF
```

| Attribute | Required | Used by |
|---|---|---|
| `x`, `y` | yes | position (shape origin — top-left for `RectangleShape`, center for `CircleShape`/`CapsuleShape`) |
| `collision_shape` | yes | `RectangleShape`, `CircleShape`, or `CapsuleShape` (primitives only — polygon objects use `MapObject`) |
| `vx`, `vy` | physics modes | `move_platformer`, `move_platformer_with_slide`, `move_grounded` |
| `on_ground` | platformer | grounded state, step-up, jump |
| `collision_layer` / `collision_mask` | optional | body filtering — both sides must agree (`should_collide`) |

`Body` is the same contract plus a `mode` ("static" / "kinematic") and
`game_id`; it is the authoring surface for *solids*, not sprites.  Draw
your sprites at `(x, y)` with the shape's size — the collision box and
the visual box are the same rectangle.

## Connectivity with `move_*`

All five movement methods share one shape —
`move(sprite, tileset_collision, tile_map, ...)` with `world=None` last
— and all five resolve **bodies as solids** (blocking, landing,
step-up):

| Method | Input model | Bodies as… |
|---|---|---|
| `move_platformer` | built-in gravity/jump + `input_x`, or explicit `velocity=` | walls + landing surfaces + step-up |
| `move_platformer_with_slide` | same, plus slopes | walls + landing surfaces + step-up |
| `move_grounded` | built-in gravity (no jump), or explicit `velocity=` | walls + landing surfaces |
| `move_and_slide` | per-frame displacement `delta_x, delta_y` (you supply velocity × dt) | walls + slide normals |
| `move_rpg` | per-frame displacement `delta_x, delta_y` | walls (full blocking) |

The **velocity contract** (physics modes): when you pass `velocity=
(vx, vy)` the runner skips gravity, input, and jump — it only resolves
collision for that velocity and adopts it onto the sprite.  You own the
velocity; the runner zeroes `vx` on wall hit and `vy` on landing.

```python
# gravity at game level (for a crate that falls, or a custom controller):
crate.vy += 800.0 * dt
result = runner.move_grounded(crate, None, None, dt, velocity=(crate.vx, crate.vy))
if result.hit_wall_x:
    crate.vx = 0.0
```

## Tiles: draw vs collide

The world holds the *collision* tile layer.  Rendering is a separate
lane — the renderer draws the map, the runner resolves it:

```python
renderer = TileLayerRenderer(game_data)          # draws the visible layers
world = PhysicsWorld.from_map(game_data, tileset)  # collision layer + grid geometry
```

If you draw `world.tile_map` yourself, tile `(col, row)` occupies the
pixel rect `(col * tile_w, row * tile_h, tile_w, tile_h)`.  Your sprites
are drawn in the same pixel space — that is the only coordinate system;
`render_scale` (from the map's `TilemapData.render_scale`) is adopted
by both the world and the runner on attach.

## The update loop — connecting the dots

```python
# --- setup -----------------------------------------------------------
game_data = load_map("map.json")
tileset = CollisionCache().get_tileset_collision("map.collision.json")

world = PhysicsWorld.from_map(game_data, tileset)
runner = CollisionRunner.from_world(world, game_type="platformer")
player = Player(96, 356)
crate = Body(RectangleShape(width=32, height=32), x=256, y=352, mode="kinematic")
world.add_body(crate)

manager = ObjectCollisionManager()               # sprite-vs-sprite lane
manager.add_object(another_npc)

# --- per frame -------------------------------------------------------
dt = clock.tick(60) / 1000.0
axis = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])   # -1 / 0 / 1

# 1. player vs tiles + bodies
result = runner.move_platformer(player, None, None, dt, input_x=float(axis), jump_pressed=jump)

# 2. player vs player / npc (separate lane, unchanged)
for hit in manager.check_all_collisions():
    hit.resolve()

# 3. pushable bodies: hand the velocity over, then move them
if result.hit_wall_x and axis != 0:
    block = world.collides_with_body(player)     # may miss by ~1px — probe (see example)
    if block is not None and block.mode == "kinematic":
        block.vx = axis * PUSH_SPEED
for body in world.bodies:
    if body.vx:
        r = runner.move_grounded(body, None, None, dt, velocity=(body.vx, body.vy))
        if r.hit_wall_x:
            body.vx = 0.0

# 4. draw — tiles, then sprites/bodies at (x, y)
```

## Object/player interaction

| Pair | Mechanism |
|---|---|
| sprite ↔ tiles | the runner's collision queries (all `move_*`) |
| sprite ↔ body | the runner (bodies block and support movement) + `world.collides_with_body(sprite)` for hit-testing |
| body ↔ body | `move_grounded(body, ..., velocity=...)` — bodies block each other |
| sprite ↔ sprite | **not** the world — use `ObjectCollisionManager` (spatial grid, layer filtering) |

The world is not a physics engine: it resolves movement against tiles
and bodies, but it does not simulate sprite-vs-sprite contact — that is
`ObjectCollisionManager`'s lane.  Sprites collide with tiles and bodies
(bodies block and support them); bodies collide with sprites, tiles,
and each other, all during movement resolution.

## What unifies everything

```
renderer ──draws──> tiles (visual)          sprites (visual)
                        │                          │
tile_map + tileset_collision ──┐      ICollidableSprite (x, y, collision_shape, ...)
                               ▼                    │
                        PhysicsWorld                │
                        (tiles + bodies + grid) ◄───┘
                               ▲
                        CollisionRunner (attached)  move_* resolves
```

The world is the unifier: tiles and bodies are solids in the same space,
the runner is the resolver, and `ICollidableSprite` is the only contract
an object must meet to participate.  If you can draw it, you can move
it; if you can move it, it can be pushed.
