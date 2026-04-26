# Collision System - Slope Sliding Feature

## Overview
Added slope sliding physics to the collision system, allowing characters to slide along slopes instead of being blocked by them.

## Problem
The original collision system treated all polygons as solid walls, blocking movement completely. User had slope collision data (diagonal polygons) but characters couldn't slide along them.

## Solution
Added a `slope_slide` parameter to enable Godot-style sliding physics that:
- Detects collision with slopes
- Calculates surface normals
- Projects movement along the surface
- Prevents bypassing collision boundaries

## Changes to `src/tilemap_parser/collision_runner.py`

### 1. Modified `move_and_slide()` Method

**New Parameter:**
```python
def move_and_slide(
    self,
    sprite: ICollidableSprite,
    tileset_collision: TilesetCollision,
    tile_map: dict,
    delta_x: float,
    delta_y: float,
    slope_slide: bool = False  # NEW PARAMETER
) -> CollisionResult:
```

**Behavior:**
- `slope_slide=False` (default): Original blocking behavior - stops at walls
- `slope_slide=True`: Slides along surfaces using iterative collision resolution

**Algorithm (when slope_slide=True):**
1. Try to move with full motion vector
2. If collision detected:
   - Stay at old position (don't move into collision)
   - Calculate collision normal from the edge being hit
   - Project remaining motion along the surface (remove normal component)
   - Repeat up to 4 times for multiple collisions
3. Only slide if moving INTO surface (dot product < 0)

### 2. Added New Helper Method

**`_get_collision_normal_from_motion()`**
```python
def _get_collision_normal_from_motion(
    self,
    sprite: ICollidableSprite,
    polygon: CollisionPolygon,
    motion_x: float,
    motion_y: float
) -> Optional[Tuple[float, float]]:
```

**Purpose:**
- Calculates the collision normal based on motion direction
- Finds the edge that the sprite is moving INTO (not just closest edge)
- Returns outward-facing normal for proper sliding

**How it works:**
1. Iterates through all polygon edges
2. Calculates normal perpendicular to each edge
3. Ensures normal points outward from polygon center
4. Finds edge with best alignment to motion direction (negative dot product)
5. Returns normal of the edge being hit

## Usage Example

```python
# In your game loop
result = collision_runner.move_and_slide(
    player,
    tileset_collision,
    tile_map,
    delta_x,
    delta_y,
    slope_slide=True  # Enable slope sliding
)

# Check collision status
if result.collided:
    print("Hit a surface and slid along it")
```

## Test Implementation

Created `examples/example.py` with:
- Simple Player class with rectangular collision shape
- Keyboard controls (Arrow keys / WASD)
- Collision visualization (toggle with 'C' key)
- Visual feedback (player color changes on collision)
- Camera following player
- Uses `collision.json` as map and `collision_data.json` for collision shapes

## Key Differences from Original

| Feature | Original Behavior | With slope_slide=True |
|---------|------------------|----------------------|
| Hitting slopes | Blocks completely | Slides along surface |
| Multiple collisions | Stops at first | Handles up to 4 iterations |
| Motion projection | Axis-aligned only | Projects along surface normal |
| Collision bypass | N/A | Prevented by staying at old position |

## Technical Notes

- The algorithm is inspired by Godot's `move_and_slide()` function
- Uses dot product to determine if moving into or away from surface
- Iterative approach handles corner cases and multiple simultaneous collisions
- Normal calculation considers motion direction, not just proximity
- Prevents tunneling by not moving sprite into collision geometry

## Files Modified

1. `src/tilemap_parser/collision_runner.py`
   - Modified `move_and_slide()` method
   - Added `_get_collision_normal_from_motion()` helper method

2. `examples/example.py`
   - Created test scene with player character
   - Demonstrates slope sliding in action
   - Includes collision visualization

## Collision Data Format

The system works with existing collision data format:
```json
{
  "tileset_name": "Tileset",
  "tile_size": [16, 16],
  "tiles": {
    "26": {
      "tile_id": 26,
      "shapes": [
        {
          "type": "polygon",
          "vertices": [[x1, y1], [x2, y2], ...],
          "one_way": false
        }
      ]
    }
  }
}
```

Slopes are defined as polygons with diagonal edges. The sliding algorithm automatically detects and handles them.
