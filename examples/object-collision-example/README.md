# Object Collision Example — Mixed-Shape Bouncing Objects

Demonstrates the **object-to-object collision detection** system in `tilemap-parser` with **mixed shape types**.

## What It Demonstrates

- **Loading collision shapes from JSON** — ball shape loaded via `load_character_collision()`
- **Layer/mask from properties** — `collision_layer` and `collision_mask` read from JSON `properties` dict
- **Mixed shape collision** — all three shape types colliding with each other:
  - **CircleShape** — bouncing balls (loaded from JSON)
  - **RectangleShape** — bouncing blocks (created programmatically)
  - **CollisionPolygon** — bouncing triangles (created programmatically, convex)
- **ObjectCollisionManager** — managing multiple dynamic objects, add/remove
- **All-vs-all collision** — `check_all_collisions()` with brute-force O(n²) detection
- **Layer filtering** — a "ghost" ball on layer 2 that passes through layer 1 objects (mutual agreement via AND)
- **Simple bounce response** — velocity reflection using collision normal + depth-based separation
- **Debug visualization** — collision normals drawn as green lines

## Prerequisites

```bash
pip install pygame
```

## How to Run

```bash
cd examples/object-collision-example/src
python bouncing_balls.py
```

## Controls

| Key | Action |
|-----|--------|
| `ESC` | Quit |
| `R` | Reset all objects to random positions |
| `G` | Toggle ghost ball (layer 2, no collisions) |
| `F1` | Toggle debug overlay (collision normals, shape counts) |

## Scene Composition

On each reset, the example creates:

| Shape | Class | Count | Collision Type |
|-------|-------|-------|----------------|
| Circle | `Ball` | 3 | `CircleShape` |
| Rectangle | `Block` | 2 | `RectangleShape` |
| Triangle | `Diamond` | 2 | `CollisionPolygon` |
| Ghost Ball | `Ball` | 1 | `CircleShape` (layer 2, mask=0) |
| Walls | `Wall` | 4 | `RectangleShape` (static boundaries) |

All dynamic objects (circles, rectangles, triangles) collide with each other. The ghost ball passes through everything.

## Key Code Pattern

This is the core pattern users will copy into their own projects:

```python
from tilemap_parser import (
    load_character_collision,
    ObjectCollisionManager,
    CircleShape,
    RectangleShape,
    CollisionPolygon,
)

# 1. Load collision shape from JSON
ball_data = load_character_collision("data/ball.collision.json")

# 2. Create objects implementing ICollidableObject
class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collision_shape = ball_data.shape
        self.collision_layer = ball_data.properties.get("collision_layer", 1)
        self.collision_mask = ball_data.properties.get("collision_mask", 0xFFFFFFFF)

# 3. Setup manager
manager = ObjectCollisionManager()
manager.add_object(ball1)
manager.add_object(block1)
manager.add_object(diamond1)

# 4. In game loop
hits = manager.check_all_collisions()
for hit in hits:
    # hit.normal  → direction to separate (from A to B)
    # hit.depth   → penetration depth
    # Apply your own response logic here
```

## File Structure

```
object-collision-example/
├── src/
│   └── bouncing_balls.py      # Main demo with mixed shapes
├── data/
│   ├── ball.collision.json     # CircleShape definition
│   └── wall.collision.json     # RectangleShape reference
└── README.md
```

## Collision JSON Format

The ball shape is defined in `data/ball.collision.json`:

```json
{
  "name": "bouncing_ball",
  "shape": {
    "type": "circle",
    "radius": 16,
    "offset": [0, 0]
  },
  "properties": {
    "collision_layer": 1,
    "collision_mask": 1
  }
}
```

Supported shape types in the parser: `rectangle`, `circle`, `capsule`.

**Note:** `CollisionPolygon` for dynamic objects is supported by the collision system but cannot be loaded from JSON in V1 (parser extension planned for V2). Polygons must be created programmatically.

## Layer Filtering

The collision system uses **mutual agreement** (AND logic):

```python
# Both objects must want to collide
(a_mask & b_layer) != 0 and (b_mask & a_layer) != 0
```

In this example:
- Normal objects: layer=1, mask=1 → collide with each other
- Ghost ball: layer=2, mask=0 → collides with nothing
- Walls: layer=2, mask=1 → dynamic objects collide with walls, walls don't collide with each other

## Shape Support Matrix

| Shape A | Shape B | Supported |
|---------|---------|-----------|
| Circle | Circle | Yes |
| Rect | Rect | Yes |
| Rect | Circle | Yes |
| Polygon | Polygon | Yes (SAT) |
| Polygon | Circle | Yes |
| Polygon | Rect | Yes |

All 6 shape-pair combinations are fully supported.

## Links

- Main docs: https://tilemap-parser.vercel.app/
- Editor: https://pypi.org/project/tilemap-editor/
- Game example: `../game-example/`
- Collision example (tile-based): `../collision-example/`
