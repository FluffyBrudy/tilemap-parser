# Object Collision System - Implementation Plan

**⚠️ SUPERSEDED - DO NOT USE FOR IMPLEMENTATION**

**This document is kept for historical reference only.**

**Use IMPLEMENTATION_READY.md instead** - it incorporates all corrections and is the canonical specification.

**Issues with this document:**
- Scope too broad (included physics engine)
- Timeline too long (11 days vs 5 days)
- Unnecessary complexity (event bus, complex body types)

**See:** DOCS_EVOLUTION.md for document timeline

---

# Object Collision System - Implementation Plan

**Date:** 2026-05-13  
**Status:** Planning Phase  
**Goal:** Implement dynamic object-to-object collision detection system for moving/animated objects

---

## Table of Contents
1. [Background & Context](#background--context)
2. [Current System Analysis](#current-system-analysis)
3. [What Exists (Usable)](#what-exists-usable)
4. [What's Missing](#whats-missing)
5. [Design Decisions](#design-decisions)
6. [Implementation Plan](#implementation-plan)
7. [Critical Focus Areas](#critical-focus-areas)

---

## Background & Context

### Problem Statement
The current collision system (`collision.py` + `collision_runner.py`) handles:
- ✅ **Static tile collision** (grid-based, polygon shapes)
- ✅ **Character vs tiles** (player/sprite moving through tilemap)
- ❌ **Object vs object** (dynamic objects colliding with each other)

### Use Case
Support moving/animated objects with collision:
- Bouncing balls (oscillating, physics-based)
- Moving platforms
- Projectiles
- Enemies colliding with each other
- Any dynamic object that needs collision detection

### Inspiration: Godot Engine Approach
Godot supports **both simple shapes AND polygons** for all body types:
- **CollisionShape2D**: Rectangle, Circle, Capsule (fast, recommended for dynamic)
- **CollisionPolygon2D**: Custom painted polygons (slower, but works for dynamic)
- **Body Types**: Area2D (detection only), RigidBody2D (physics), CharacterBody2D (manual), StaticBody2D (static)
- **Layer System**: 32-bit masks for collision filtering

---

## Current System Analysis

### Existing Architecture (Well-Designed)

#### 1. `collision.py` - Data Structures & Parsing
**Purpose:** Parse collision data from JSON, provide shape classes

**Components:**
- Shape classes: `RectangleShape`, `CircleShape`, `CapsuleShape`, `CollisionPolygon`
- Parsers: `parse_tileset_collision()`, `parse_character_collision()`
- Loaders: `load_tileset_collision()`, `load_character_collision()`
- Cache: `CollisionCache` for performance

**Design Quality:** ⭐⭐⭐⭐⭐
- Clean separation of concerns
- Dataclass-based (immutable, type-safe)
- Extensible `properties` dict
- Caching built-in

#### 2. `collision_runner.py` - Runtime Collision System
**Purpose:** Handle sprite movement with tile collision response

**Components:**
- Movement modes: Slide, Platformer, RPG
- Collision detection: Sprite vs tile polygons
- Physics: Gravity, jumping, sliding
- Optimizations: Spatial queries, inline offset calculations

**Design Quality:** ⭐⭐⭐⭐⭐
- Protocol-based (`ICollidableSprite`)
- Multiple movement modes
- Highly optimized (no allocations in hot paths)
- Reusable result objects

**Key Insight:** The system is **carefully optimized** - we must match this quality!

---

## What Exists (Usable)

### ✅ Shape Classes (Ready for Objects)

#### RectangleShape
```python
@dataclass
class RectangleShape:
    width: float
    height: float
    offset: Point = (0.0, 0.0)
    
    def get_bounds(x, y) -> (left, top, right, bottom)
```
**Status:** ✅ Complete, world-space bounds calculation included

#### CircleShape
```python
@dataclass
class CircleShape:
    radius: float
    offset: Point = (0.0, 0.0)
    
    def get_center(x, y) -> Point
```
**Status:** ✅ Complete, world-space center calculation included

#### CapsuleShape
```python
@dataclass
class CapsuleShape:
    radius: float
    height: float
    offset: Point = (0.0, 0.0)
    
    def get_top_center(x, y) -> Point
    def get_bottom_center(x, y) -> Point
```
**Status:** ✅ Complete, world-space calculations included

#### CollisionPolygon
```python
@dataclass
class CollisionPolygon:
    vertices: List[Point]
    one_way: bool = False
    
    def transform(tile_x, tile_y) -> CollisionPolygon
    def is_valid() -> bool
```
**Status:** ⚠️ Exists for tiles, can be adapted for objects

---

### ✅ Character Collision System (Ready for Objects)

#### CharacterCollision
```python
@dataclass
class CharacterCollision:
    name: str
    shape: Union[RectangleShape, CircleShape, CapsuleShape]
    properties: Dict[str, Any]  # ← Extensible for physics metadata!
```

#### Parser
```python
def parse_character_collision(data: JsonDict) -> CharacterCollision
def load_character_collision(path) -> Optional[CharacterCollision]
```
**Supports:** rectangle, circle, capsule  
**Missing:** polygon type

#### JSON Format
```json
{
  "name": "bouncing_ball",
  "shape": {
    "type": "circle",
    "radius": 16,
    "offset": [0, 0]
  },
  "properties": {
    "body_type": "dynamic",
    "mass": 1.0,
    "restitution": 0.8,
    "friction": 0.3
  }
}
```
**Status:** ✅ Format ready, `properties` can hold physics data

---

### ✅ Collision Cache (Ready for Objects)
```python
class CollisionCache:
    def get_character_collision(path) -> Optional[CharacterCollision]
    def preload_character(path)
    def clear()
```
**Status:** ✅ Complete, can cache object collision data

---

## What's Missing

### ❌ 1. Polygon Support for Objects

**Current:** `parse_character_collision()` only handles rectangle/circle/capsule  
**Need:** Add polygon parsing

```python
# In parse_character_collision():
elif shape_type == "polygon":
    vertices = [tuple(v) for v in shape_data["vertices"]]
    offset = tuple(shape_data.get("offset", (0.0, 0.0)))
    shape = PolygonShape(vertices=vertices, offset=offset)
```

**Decision:** Create `PolygonShape` class (separate from `CollisionPolygon`)
- `CollisionPolygon` is for tiles (has `one_way`, `transform()`)
- `PolygonShape` is for objects (has `offset`, consistent with other shapes)

---

### ❌ 2. Shape-to-Shape Collision Detection

**Current:** Only sprite-to-tile-polygon collision exists  
**Need:** All shape-pair combinations

| Shape A | Shape B | Status | Priority |
|---------|---------|--------|----------|
| Circle | Circle | ❌ Missing | HIGH |
| Rect | Rect | ❌ Missing | HIGH |
| Rect | Circle | ⚠️ Exists (for polygons) | ADAPT |
| Circle | Capsule | ❌ Missing | MEDIUM |
| Rect | Capsule | ❌ Missing | MEDIUM |
| Capsule | Capsule | ❌ Missing | LOW |
| Polygon | Polygon | ⚠️ Exists (for tiles) | ADAPT |
| Polygon | Circle | ⚠️ Exists (for tiles) | ADAPT |
| Polygon | Rect | ⚠️ Exists (for tiles) | ADAPT |
| Polygon | Capsule | ❌ Missing | LOW |

**Optimization Note:** Reuse existing polygon collision math from `collision_runner.py`

---

### ❌ 3. Object Collision Manager

**Need:** Runtime system to manage multiple dynamic objects

```python
class ObjectCollisionManager:
    """
    Manages collision detection between dynamic objects.
    
    Features:
    - Add/remove objects
    - Check collisions (all-vs-all or one-vs-all)
    - Layer/mask filtering
    - Spatial partitioning (for many objects)
    - Optional physics integration
    """
```

**Critical:** Must match optimization quality of `collision_runner.py`

---

### ❌ 4. Protocol for Dynamic Objects

**Need:** Interface that objects must implement

```python
class ICollidableObject(Protocol):
    """
    Protocol for dynamic objects (like ICollidableSprite but for objects).
    
    Required:
        x, y: Position
        collision_shape: Shape (rect/circle/capsule/polygon)
    
    Optional (for physics):
        vx, vy: Velocity
        mass, restitution, friction: Physics properties
        collision_layer, collision_mask: Layer filtering
    """
```

---

### ❌ 5. Physics Integration (Optional)

**Need:** Automatic physics for dynamic bodies

- Gravity application
- Velocity integration
- Collision response (bounce, push)
- Friction/damping

**Decision:** Make this **optional** - some users only want detection

---

## Design Decisions

### Decision 1: Polygon Shape for Objects
**Question:** Reuse `CollisionPolygon` or create `PolygonShape`?

**Answer:** Create separate `PolygonShape`
- **Reason:** `CollisionPolygon` has tile-specific features (`one_way`, `transform()`)
- **Benefit:** Clean separation, consistent API with other shapes

```python
@dataclass
class PolygonShape:
    """Polygon collision shape for dynamic objects"""
    vertices: List[Point]
    offset: Point = (0.0, 0.0)
    
    def get_bounds(x, y) -> (left, top, right, bottom)
    def get_world_vertices(x, y) -> List[Point]
```

---

### Decision 2: Properties Dict for Physics Metadata
**Question:** Store physics data in `properties` dict or top-level fields?

**Answer:** Use `properties` dict
- **Reason:** No breaking changes, backward compatible
- **Benefit:** Editor already supports it, extensible

```json
{
  "properties": {
    "body_type": "dynamic|kinematic|area|static",
    "mass": 1.0,
    "restitution": 0.8,
    "friction": 0.3,
    "gravity_scale": 1.0,
    "collision_layer": 1,
    "collision_mask": 0xFFFFFFFF
  }
}
```

**Defaults:** If missing, use sensible defaults (kinematic, mass=1.0, etc.)

---

### Decision 3: Body Types (Like Godot)
**Question:** Support different body types?

**Answer:** YES, use enum

```python
class CollisionBodyType(Enum):
    AREA = "area"           # Detection only, no physics
    DYNAMIC = "dynamic"     # Full physics (like RigidBody2D)
    KINEMATIC = "kinematic" # Manual control (like CharacterBody2D)
    STATIC = "static"       # Non-moving (like StaticBody2D)
```

**Default:** `kinematic` (most common for game objects)

---

### Decision 4: Layer System
**Question:** Implement collision layers/masks?

**Answer:** YES, 32-bit bitmask system (like Godot)

```python
def _should_collide(obj_a, obj_b) -> bool:
    """Check if two objects should collide based on layers"""
    a_layer = getattr(obj_a, 'collision_layer', 1)
    a_mask = getattr(obj_a, 'collision_mask', 0xFFFFFFFF)
    b_layer = getattr(obj_b, 'collision_layer', 1)
    b_mask = getattr(obj_b, 'collision_mask', 0xFFFFFFFF)
    
    return (a_mask & b_layer) != 0 or (b_mask & a_layer) != 0
```

**Benefit:** Powerful filtering without checking every pair

---

### Decision 5: Spatial Partitioning
**Question:** Always use spatial grid?

**Answer:** Adaptive approach
- **< 50 objects:** Brute force (O(n²) but simple)
- **≥ 50 objects:** Spatial hash grid (O(n) but overhead)

**Reason:** Match `collision_runner.py` philosophy - optimize when needed

---

### Decision 6: Separation of Concerns
**Question:** Modify existing files or create new module?

**Answer:** Create `object_collision.py` (NEW FILE)
- **Reason:** Don't touch carefully designed `collision.py` / `collision_runner.py`
- **Exception:** Minimal extension to `collision.py` for polygon parsing

**Philosophy:** Composition over modification

---

## Implementation Plan

### Phase 1: Core Detection (Simple Shapes Only)
**Goal:** Basic object-to-object collision with rect/circle/capsule  
**Duration:** 2-3 days  
**Files:** `src/tilemap_parser/object_collision.py` (NEW)

#### Tasks:
1. **Protocol Definition**
   ```python
   class ICollidableObject(Protocol):
       x: float
       y: float
       collision_shape: Union[RectangleShape, CircleShape, CapsuleShape]
   ```

2. **Shape-to-Shape Collision (High Priority)**
   ```python
   def circle_circle_collision(c1, c2) -> bool
   def rect_rect_collision(r1, r2) -> bool
   def rect_circle_collision(r, c) -> bool
   ```
   **Optimization:** Inline calculations, no allocations

3. **Collision Dispatcher**
   ```python
   def check_collision(obj_a, obj_b) -> bool:
       """Dispatch to appropriate shape-pair function"""
   ```

4. **Basic Manager**
   ```python
   class ObjectCollisionManager:
       def add_object(obj)
       def remove_object(obj)
       def check_object_collisions(obj) -> List[ICollidableObject]
       def check_all_collisions() -> List[Tuple[obj_a, obj_b]]
   ```

5. **Tests**
   - Unit tests for each shape-pair
   - Integration test with manager
   - Performance benchmark (1000 objects)

**Deliverable:** Working collision detection for simple shapes

---

### Phase 2: Polygon Support
**Goal:** Add polygon collision for complex objects  
**Duration:** 1-2 days  
**Files:** `collision.py` (EXTEND), `object_collision.py` (EXTEND)

#### Tasks:
1. **Add PolygonShape to collision.py**
   ```python
   @dataclass
   class PolygonShape:
       vertices: List[Point]
       offset: Point = (0.0, 0.0)
       
       def get_bounds(x, y) -> Tuple[float, float, float, float]
       def get_world_vertices(x, y) -> List[Point]
   ```

2. **Extend Parser**
   ```python
   # In parse_character_collision():
   elif shape_type == "polygon":
       shape = PolygonShape(vertices=..., offset=...)
   ```

3. **Update Type Union**
   ```python
   CharacterShapeType = Union[RectangleShape, CircleShape, CapsuleShape, PolygonShape]
   ```

4. **Polygon Collision Detection**
   - Adapt existing polygon math from `collision_runner.py`
   - `polygon_polygon_collision()`
   - `polygon_circle_collision()`
   - `polygon_rect_collision()`

5. **Tests**
   - Polygon parsing tests
   - Polygon collision tests
   - Complex shape integration test

**Deliverable:** Full shape support including polygons

---

### Phase 3: Layer System & Filtering
**Goal:** Efficient collision filtering  
**Duration:** 1 day  
**Files:** `object_collision.py` (EXTEND)

#### Tasks:
1. **Body Type Enum**
   ```python
   class CollisionBodyType(Enum):
       AREA = "area"
       DYNAMIC = "dynamic"
       KINEMATIC = "kinematic"
       STATIC = "static"
   ```

2. **Layer Filtering**
   ```python
   def _should_collide(obj_a, obj_b) -> bool
   ```

3. **Update Protocol**
   ```python
   class ICollidableObject(Protocol):
       # ... existing ...
       body_type: CollisionBodyType = CollisionBodyType.KINEMATIC
       collision_layer: int = 1
       collision_mask: int = 0xFFFFFFFF
   ```

4. **Integrate with Manager**
   - Filter checks in `check_all_collisions()`
   - Skip checks based on layers

5. **Tests**
   - Layer filtering tests
   - Body type tests

**Deliverable:** Efficient collision filtering

---

### Phase 4: Spatial Partitioning
**Goal:** Optimize for many objects  
**Duration:** 1-2 days  
**Files:** `object_collision.py` (EXTEND)

#### Tasks:
1. **Spatial Hash Grid**
   ```python
   class _SpatialGrid:
       def __init__(self, cell_size: int)
       def insert(obj, bounds)
       def query(bounds) -> List[obj]
       def clear()
   ```

2. **Adaptive Strategy**
   ```python
   # In ObjectCollisionManager:
   if len(self.objects) < 50:
       # Brute force
   else:
       # Use spatial grid
   ```

3. **Benchmark**
   - Test with 10, 100, 1000, 10000 objects
   - Compare brute force vs spatial grid
   - Document performance characteristics

**Deliverable:** Scalable collision detection

---

### Phase 5: Physics Integration (Optional)
**Goal:** Automatic physics for dynamic bodies  
**Duration:** 2 days  
**Files:** `object_collision.py` (EXTEND)

#### Tasks:
1. **Physics Properties**
   ```python
   class ICollidableObject(Protocol):
       # ... existing ...
       vx: float = 0.0
       vy: float = 0.0
       mass: float = 1.0
       restitution: float = 0.5
       friction: float = 0.3
   ```

2. **Physics Update**
   ```python
   def _update_physics(self, dt: float):
       """Apply gravity, integrate velocity"""
   ```

3. **Collision Response**
   ```python
   def _apply_collision_response(self, event: CollisionEvent):
       """Elastic collision, push separation"""
   ```

4. **Event System**
   ```python
   @dataclass
   class CollisionEvent:
       obj_a: ICollidableObject
       obj_b: ICollidableObject
       penetration: float
       normal: Tuple[float, float]
   
   # Callbacks
   manager.connect_collision(callback)
   ```

5. **Tests**
   - Physics integration tests
   - Collision response tests
   - Event callback tests

**Deliverable:** Full physics system (optional)

---

### Phase 6: Documentation & Examples
**Goal:** Complete documentation and examples  
**Duration:** 1 day  
**Files:** `docs/`, `examples/object-collision-example/`

#### Tasks:
1. **API Documentation**
   - Protocol documentation
   - Manager API reference
   - Function signatures
   - Performance characteristics

2. **User Guide**
   - Quick start
   - JSON format guide
   - Integration with tile collision
   - Performance tips

3. **Example Project**
   ```
   examples/object-collision-example/
   ├── bouncing_balls.py
   ├── data/
   │   ├── ball.collision.json
   │   └── platform.collision.json
   └── README.md
   ```

4. **Migration Guide**
   - For users of `CharacterCollision`
   - JSON format examples
   - Code examples

**Deliverable:** Complete documentation

---

## Critical Focus Areas

### 1. Performance Optimization (CRITICAL)
**Why:** `collision_runner.py` is highly optimized - we must match this quality

**Strategies:**
- **No allocations in hot paths**
  - Reuse result objects
  - Inline calculations
  - Avoid temporary lists/tuples

- **Early exits**
  - AABB pre-rejection
  - Layer filtering before shape checks
  - Spatial grid for broad phase

- **Efficient algorithms**
  - SAT (Separating Axis Theorem) for polygons
  - Distance checks for circles
  - AABB for rectangles

**Benchmark Targets:**
- 100 objects: < 1ms per frame
- 1000 objects: < 5ms per frame (with spatial grid)

---

### 2. API Consistency (CRITICAL)
**Why:** Must feel like part of the existing system

**Guidelines:**
- **Match naming conventions**
  - `ICollidableObject` (like `ICollidableSprite`)
  - `check_collision()` (like `check_sprite_polygon_collision()`)
  - `ObjectCollisionManager` (like `CollisionRunner`)

- **Match patterns**
  - Protocol-based interfaces
  - Dataclass for data structures
  - Optional parameters with defaults
  - Type hints everywhere

- **Match documentation style**
  - Docstrings with Args/Returns/Raises
  - Usage examples in docstrings
  - Clear parameter descriptions

---

### 3. Backward Compatibility (CRITICAL)
**Why:** Don't break existing code

**Rules:**
- **No modifications to existing APIs**
  - `collision.py` - only ADD, don't change
  - `collision_runner.py` - don't touch
  - Existing JSON format - still works

- **Graceful degradation**
  - Missing `properties` → use defaults
  - Unknown shape type → raise clear error
  - Invalid data → helpful error messages

---

### 4. Testing (CRITICAL)
**Why:** Collision bugs are hard to debug

**Coverage:**
- **Unit tests** (each function)
  - All shape-pair combinations
  - Edge cases (overlapping, touching, separated)
  - Degenerate cases (zero-size, invalid)

- **Integration tests** (system)
  - Manager with multiple objects
  - Layer filtering
  - Physics integration

- **Performance tests** (benchmarks)
  - Scaling with object count
  - Spatial grid effectiveness
  - Memory usage

**Target:** 95%+ code coverage

---

### 5. Documentation (HIGH)
**Why:** Complex system needs clear docs

**Requirements:**
- **API reference** (complete)
- **User guide** (practical)
- **Examples** (working code)
- **Performance guide** (optimization tips)

---

## File Structure

```
src/tilemap_parser/
├── collision.py              # EXTEND (add PolygonShape, update parser)
├── collision_runner.py       # NO CHANGES
├── object_collision.py       # NEW (main implementation)
└── __init__.py              # UPDATE (export new APIs)

tests/
├── test_collision.py         # EXTEND (polygon parsing tests)
├── test_object_collision.py  # NEW (unit tests)
└── test_object_collision_integration.py  # NEW (integration tests)

examples/
└── object-collision-example/  # NEW
    ├── bouncing_balls.py
    ├── data/
    │   ├── ball.collision.json
    │   └── platform.collision.json
    └── README.md

docs/
└── object_collision.md       # NEW (user guide)
```

---

## Success Criteria

### Functional Requirements
- ✅ Detect collisions between all shape types
- ✅ Support simple shapes (rect/circle/capsule)
- ✅ Support polygon shapes
- ✅ Layer/mask filtering
- ✅ Optional physics integration
- ✅ Event callbacks

### Performance Requirements
- ✅ < 1ms for 100 objects
- ✅ < 5ms for 1000 objects (with spatial grid)
- ✅ No allocations in hot paths
- ✅ Memory efficient

### Quality Requirements
- ✅ 95%+ test coverage
- ✅ Complete documentation
- ✅ Working examples
- ✅ Backward compatible
- ✅ Consistent with existing code

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Core Detection | 2-3 days | 3 days |
| Phase 2: Polygon Support | 1-2 days | 5 days |
| Phase 3: Layer System | 1 day | 6 days |
| Phase 4: Spatial Partitioning | 1-2 days | 8 days |
| Phase 5: Physics (Optional) | 2 days | 10 days |
| Phase 6: Documentation | 1 day | 11 days |

**Total: ~11 days** (with physics)  
**Minimum: ~6 days** (without physics)

---

## Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Start Phase 1** - Implement core detection with simple shapes
3. **Iterate** - Test, optimize, refine
4. **Extend** - Add polygon support, layers, spatial grid
5. **Polish** - Documentation, examples, final optimizations

---

## Notes

- **Philosophy:** Match the quality and design of existing system
- **Priority:** Correctness > Performance > Features
- **Approach:** Incremental - each phase delivers working functionality
- **Testing:** Test-driven - write tests alongside implementation
- **Documentation:** Document as you go - don't leave it for the end

---

**End of Implementation Plan**
