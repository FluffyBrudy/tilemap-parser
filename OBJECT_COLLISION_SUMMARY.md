# Object Collision System - Quick Reference

**⚠️ SUPERSEDED - DO NOT USE FOR IMPLEMENTATION**

**This document is kept for historical reference only.**

**Use IMPLEMENTATION_READY.md instead** - it incorporates all corrections and is the canonical specification.

**Issues with this document:**
- Based on overly broad initial plan
- Contains outdated scope decisions
- Timeline and phases superseded

**See:** DOCS_EVOLUTION.md for document timeline

---

# Object Collision System - Quick Reference

## 🎯 Goal
Add dynamic object-to-object collision detection for moving/animated objects (bouncing balls, projectiles, enemies, etc.)

---

## ✅ What We Have (Ready to Use)

### Shape Classes
- ✅ `RectangleShape` - Complete with `get_bounds()`
- ✅ `CircleShape` - Complete with `get_center()`
- ✅ `CapsuleShape` - Complete with `get_top_center()`, `get_bottom_center()`
- ⚠️ `CollisionPolygon` - Exists for tiles, can adapt for objects

### Parsing System
- ✅ `CharacterCollision` - Data class with `name`, `shape`, `properties`
- ✅ `parse_character_collision()` - Parses rect/circle/capsule from JSON
- ✅ `load_character_collision()` - Loads from file
- ✅ `CollisionCache` - Caching system ready

### JSON Format
```json
{
  "name": "bouncing_ball",
  "shape": {"type": "circle", "radius": 16, "offset": [0, 0]},
  "properties": {
    "body_type": "dynamic",
    "mass": 1.0,
    "restitution": 0.8
  }
}
```

---

## ❌ What's Missing

### 1. Polygon Support for Objects
- Need `PolygonShape` class
- Need polygon parsing in `parse_character_collision()`

### 2. Shape-to-Shape Collision Math
- `circle_circle_collision()`
- `rect_rect_collision()`
- `polygon_polygon_collision()`
- All shape-pair combinations

### 3. Object Collision Manager
- Runtime system to manage multiple objects
- Collision detection (all-vs-all, one-vs-all)
- Layer filtering
- Spatial partitioning

### 4. Protocol for Objects
- `ICollidableObject` interface
- Like `ICollidableSprite` but for dynamic objects

---

## 📋 Implementation Order

### Phase 1: Core Detection (Simple Shapes) - 2-3 days
**Priority:** HIGH  
**Goal:** Basic collision with rect/circle/capsule

1. Define `ICollidableObject` protocol
2. Implement shape-to-shape collision functions
3. Create `ObjectCollisionManager` (basic)
4. Write tests

**Deliverable:** Working collision for simple shapes

---

### Phase 2: Polygon Support - 1-2 days
**Priority:** HIGH  
**Goal:** Add polygon collision

1. Add `PolygonShape` to `collision.py`
2. Extend `parse_character_collision()` for polygons
3. Implement polygon collision functions
4. Write tests

**Deliverable:** Full shape support

---

### Phase 3: Layer System - 1 day
**Priority:** MEDIUM  
**Goal:** Collision filtering

1. Add `CollisionBodyType` enum
2. Implement layer/mask filtering
3. Integrate with manager

**Deliverable:** Efficient filtering

---

### Phase 4: Spatial Partitioning - 1-2 days
**Priority:** MEDIUM  
**Goal:** Optimize for many objects

1. Implement spatial hash grid
2. Adaptive strategy (brute force vs grid)
3. Benchmark performance

**Deliverable:** Scalable collision

---

### Phase 5: Physics (Optional) - 2 days
**Priority:** LOW  
**Goal:** Automatic physics

1. Add physics properties to protocol
2. Implement gravity/velocity integration
3. Implement collision response
4. Add event callbacks

**Deliverable:** Full physics system

---

### Phase 6: Documentation - 1 day
**Priority:** HIGH  
**Goal:** Complete docs

1. API reference
2. User guide
3. Example project
4. Migration guide

**Deliverable:** Complete documentation

---

## 🎯 Critical Focus Areas

### 1. Performance (CRITICAL)
- No allocations in hot paths
- Early exits (AABB, layers)
- Efficient algorithms
- **Target:** < 1ms for 100 objects

### 2. API Consistency (CRITICAL)
- Match existing naming conventions
- Match existing patterns
- Match existing documentation style

### 3. Backward Compatibility (CRITICAL)
- No breaking changes to existing APIs
- Graceful degradation
- Clear error messages

### 4. Testing (CRITICAL)
- Unit tests for all functions
- Integration tests for system
- Performance benchmarks
- **Target:** 95%+ coverage

---

## 📁 Files to Create/Modify

### NEW Files
- `src/tilemap_parser/object_collision.py` - Main implementation
- `tests/test_object_collision.py` - Unit tests
- `tests/test_object_collision_integration.py` - Integration tests
- `examples/object-collision-example/` - Example project

### EXTEND Files
- `src/tilemap_parser/collision.py` - Add `PolygonShape`, extend parser
- `src/tilemap_parser/__init__.py` - Export new APIs
- `tests/test_collision.py` - Add polygon parsing tests

### NO CHANGES
- `src/tilemap_parser/collision_runner.py` - Don't touch!

---

## 🚀 Quick Start (After Implementation)

```python
from tilemap_parser import (
    ObjectCollisionManager,
    load_character_collision,
    CircleShape,
)

# Load collision data
ball_data = load_character_collision("data/ball.collision.json")

# Create objects
class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collision_shape = CircleShape(radius=16)
        self.vx = 100.0
        self.vy = 0.0

# Setup manager
manager = ObjectCollisionManager()
ball1 = Ball(100, 100)
ball2 = Ball(200, 100)
manager.add_object(ball1)
manager.add_object(ball2)

# Game loop
while running:
    dt = clock.tick(60) / 1000.0
    
    # Update positions
    ball1.x += ball1.vx * dt
    ball2.x += ball2.vx * dt
    
    # Check collisions
    collisions = manager.check_all_collisions()
    for obj_a, obj_b in collisions:
        handle_collision(obj_a, obj_b)
```

---

## 📊 Timeline

| Phase | Duration | Features |
|-------|----------|----------|
| Phase 1 | 2-3 days | Simple shapes collision |
| Phase 2 | 1-2 days | Polygon support |
| Phase 3 | 1 day | Layer filtering |
| Phase 4 | 1-2 days | Spatial partitioning |
| Phase 5 | 2 days | Physics (optional) |
| Phase 6 | 1 day | Documentation |

**Total:** ~11 days (with physics) or ~6 days (without physics)

---

## ✅ Success Criteria

- [ ] Detect collisions between all shape types
- [ ] Support rect/circle/capsule/polygon
- [ ] Layer/mask filtering works
- [ ] < 1ms for 100 objects
- [ ] < 5ms for 1000 objects
- [ ] 95%+ test coverage
- [ ] Complete documentation
- [ ] Working examples
- [ ] Backward compatible

---

## 📝 Design Decisions Summary

1. **Polygon Shape:** Create separate `PolygonShape` (not reuse `CollisionPolygon`)
2. **Physics Metadata:** Store in `properties` dict (backward compatible)
3. **Body Types:** Use enum (area/dynamic/kinematic/static)
4. **Layer System:** 32-bit bitmask (like Godot)
5. **Spatial Grid:** Adaptive (< 50 objects = brute force, ≥ 50 = grid)
6. **New Module:** Create `object_collision.py` (don't modify existing)

---

## 🔗 Related Documents

- **Full Plan:** `OBJECT_COLLISION_IMPLEMENTATION_PLAN.md`
- **Existing Code:** `src/tilemap_parser/collision.py`, `collision_runner.py`
- **Tests:** `tests/test_collision.py`, `test_collision_runner.py`

---

**Status:** Planning Complete ✅  
**Next Step:** Begin Phase 1 Implementation
