# Object Collision System - REVISED Implementation Plan
**Based on Design Corrections from POSSIBILITY_OBJ_COLLIISION.md**

**⚠️ SUPERSEDED - DO NOT USE FOR IMPLEMENTATION**

**This document is kept for historical reference only.**

**Use IMPLEMENTATION_READY.md instead** - it incorporates additional quality fixes.

**Issues with this document:**
- Layer filtering logic incorrect (uses OR instead of AND)
- Inside-rectangle depth calculation wrong
- Spatial grid references not removed
- Some inconsistencies remain

**See:** DOCS_EVOLUTION.md for document timeline

---

**Date:** 2026-05-13  
**Status:** Planning Phase (Revised)  
**Goal:** Implement focused, practical object-to-object collision **detection** system

---

## Executive Summary

### What Changed
- ❌ **Removed:** Full physics engine, event bus, complex body types, capsules
- ✅ **Kept:** Detection only, shared geometry, simple API, existing polygon workflow
- 🎯 **Result:** 5 days instead of 11 days, cleaner architecture, focused scope

### Core Principle
> **Build "a very good collision system", NOT "a mini game engine"**

---

## Table of Contents
1. [Scope Definition](#scope-definition)
2. [Architecture Overview](#architecture-overview)
3. [What We're Building](#what-were-building)
4. [What We're NOT Building](#what-were-not-building)
5. [Implementation Phases](#implementation-phases)
6. [File Structure](#file-structure)
7. [API Reference](#api-reference)
8. [Testing Strategy](#testing-strategy)
9. [Timeline](#timeline)

---

## Scope Definition

### V1 Goals (This Implementation)
✅ **Collision Detection**
- Detect when objects overlap
- Return collision information (normal, depth)
- Support rect/circle/polygon shapes
- Layer-based filtering

✅ **Object Management**
- Add/remove objects from collision system
- Query collisions (all-vs-all, one-vs-all)
- Automatic broadphase optimization (internal)

✅ **Reuse Existing**
- Existing shape classes
- Existing polygon paint workflow
- Existing parser infrastructure

### V2 Goals (Future)
⏭️ **If Needed Later**
- Capsule shapes
- Collision response helpers (simple pushback)
- Swept collision detection
- Trigger callbacks
- Simple physics helpers

### NOT Goals (Ever in This Library)
❌ **Out of Scope**
- Full physics engine
- Rigidbody simulation
- Gravity/velocity integration
- Friction/restitution solving
- Impulse resolution
- Physics stepping
- Event bus system

**Reason:** These belong in a game engine, not a tilemap parser library.

---

## Architecture Overview

### Clean Layer Separation

```
┌─────────────────────────────────────┐
│         Editor (External)           │
│   - Polygon paint tool              │
│   - Collision shape editor          │
└──────────────┬──────────────────────┘
               │ JSON files
               ↓
┌─────────────────────────────────────┐
│      Parser (collision.py)          │
│   - Parse JSON                      │
│   - Validate data                   │
│   - Cache results                   │
└──────────────┬──────────────────────┘
               │ Data structures
               ↓
┌─────────────────────────────────────┐
│   Geometry (geometry.py) - NEW      │
│   - Low-level collision math        │
│   - Shape-vs-shape tests            │
│   - SAT, distance checks            │
└──────────────┬──────────────────────┘
               │ Collision functions
               ↓
┌─────────────────────────────────────┐
│  Runtime (object_collision.py)      │
│   - Object management               │
│   - Collision queries               │
│   - Broadphase optimization         │
└──────────────┬──────────────────────┘
               │ Collision results
               ↓
┌─────────────────────────────────────┐
│       Game Logic (User Code)        │
│   - Handle collisions               │
│   - Apply responses                 │
│   - Game-specific behavior          │
└─────────────────────────────────────┘
```

### Key Architectural Decisions

1. **Parser stays dumb** - Only parse/validate/cache
2. **Geometry is shared** - Both tile and object collision use same math
3. **Runtime is focused** - Detection only, no physics
4. **Game logic is separate** - Users handle responses

---

## What We're Building

### 1. Shared Geometry Module (`geometry.py`)

**Purpose:** Low-level collision math shared by tile and object systems

```python
# Core collision tests
def circle_vs_circle(
    c1_center: Point, c1_radius: float,
    c2_center: Point, c2_radius: float
) -> Optional[CollisionInfo]

def rect_vs_rect(
    r1_bounds: Tuple[float, float, float, float],
    r2_bounds: Tuple[float, float, float, float]
) -> Optional[CollisionInfo]

def polygon_vs_polygon(
    p1_vertices: List[Point],
    p2_vertices: List[Point]
) -> Optional[CollisionInfo]

def rect_vs_circle(
    rect_bounds: Tuple[float, float, float, float],
    circle_center: Point,
    circle_radius: float
) -> Optional[CollisionInfo]

def polygon_vs_circle(
    poly_vertices: List[Point],
    circle_center: Point,
    circle_radius: float
) -> Optional[CollisionInfo]

def polygon_vs_rect(
    poly_vertices: List[Point],
    rect_bounds: Tuple[float, float, float, float]
) -> Optional[CollisionInfo]

# Helper data
@dataclass
class CollisionInfo:
    """Low-level collision result"""
    normal: Tuple[float, float]
    depth: float
```

**Why separate file:**
- Prevents code duplication
- Single source of truth for collision math
- Can be tested independently
- Reusable by both tile and object systems

---

### 2. Object Collision Module (`object_collision.py`)

**Purpose:** Manage dynamic object collision detection

#### Protocol
```python
class ICollidableObject(Protocol):
    """
    Interface for objects that can collide.
    
    Required attributes:
        x (float): World X position
        y (float): World Y position
        collision_shape: Shape for collision
    
    Optional attributes:
        body_type (CollisionBodyType): Type of body (default: DYNAMIC)
        collision_layer (int): Layer this object is on (default: 1)
        collision_mask (int): Layers this object collides with (default: 0xFFFFFFFF)
    """
    x: float
    y: float
    collision_shape: Union[RectangleShape, CircleShape, CollisionPolygon]
```

#### Body Types (Simplified)
```python
class CollisionBodyType(Enum):
    """Body type for collision filtering"""
    STATIC = "static"    # Non-moving (walls, platforms)
    DYNAMIC = "dynamic"  # Moving objects (enemies, projectiles)
    SENSOR = "sensor"    # Trigger-only (no collision response)
```

#### Collision Result
```python
@dataclass
class CollisionHit:
    """Result of a collision detection"""
    object_a: ICollidableObject
    object_b: ICollidableObject
    normal: Tuple[float, float]  # Direction to separate (from A to B)
    depth: float                  # Penetration depth
```

#### Detection Function
```python
def check_collision(
    obj_a: ICollidableObject,
    obj_b: ICollidableObject
) -> Optional[CollisionHit]:
    """
    Check if two objects collide.
    
    Returns:
        CollisionHit if colliding, None otherwise
    """
```

#### Manager
```python
class ObjectCollisionManager:
    """
    Manages collision detection for multiple objects.
    
    Features:
    - Add/remove objects
    - Query collisions
    - Layer filtering
    - Automatic broadphase optimization (internal)
    """
    
    def __init__(self):
        """Initialize collision manager"""
        self.objects: List[ICollidableObject] = []
        self._spatial_grid = None  # Internal, adaptive
    
    def add_object(self, obj: ICollidableObject):
        """Add object to collision system"""
    
    def remove_object(self, obj: ICollidableObject):
        """Remove object from collision system"""
    
    def check_all_collisions(self) -> List[CollisionHit]:
        """
        Check all objects against each other.
        
        Returns:
            List of collision hits
        
        Note:
            Automatically uses spatial grid for >50 objects
        """
    
    def check_object(self, obj: ICollidableObject) -> List[CollisionHit]:
        """
        Check one object against all others.
        
        Args:
            obj: Object to check
        
        Returns:
            List of objects it collides with
        """
```

---

### 3. Parser Extensions (Minimal)

**File:** `collision.py`

**Changes:** MINIMAL - Only if needed for polygon offset support

```python
# Existing CollisionPolygon already works!
@dataclass
class CollisionPolygon:
    vertices: List[Point]
    one_way: bool = False  # Objects ignore this, tiles use it
    
    # May add if needed:
    # offset: Point = (0.0, 0.0)
```

**Why minimal:**
- Existing `CollisionPolygon` works for both tiles and objects
- `one_way` is simply ignored by objects
- No need for separate `PolygonShape` class
- Keeps parser simple

---

## What We're NOT Building

### ❌ Physics Engine
```python
# NOT IMPLEMENTING:
class RigidBody:
    velocity: Vector2
    mass: float
    
    def apply_force(self, force: Vector2):
        """NO - This is physics engine territory"""
    
    def integrate(self, dt: float):
        """NO - This is physics engine territory"""
```

**Why not:** Physics engines are complex subsystems that dominate architecture. Users can implement simple physics in their game logic if needed.

---

### ❌ Collision Response
```python
# NOT IMPLEMENTING:
def resolve_collision_elastic(hit: CollisionHit, restitution: float):
    """NO - This is game logic territory"""

def resolve_collision_friction(hit: CollisionHit, friction: float):
    """NO - This is game logic territory"""
```

**Why not:** Response depends on game-specific behavior. We provide `normal` and `depth` - users decide what to do with it.

---

### ❌ Event Bus System
```python
# NOT IMPLEMENTING:
manager.connect_collision(callback)
manager.on_collision_enter(callback)
manager.emit_collision_event(event)
```

**Why not:** Event systems are engine infrastructure. Users can build their own event handling around collision results.

---

### ❌ Complex Body Types
```python
# NOT IMPLEMENTING (in V1):
class CollisionBodyType(Enum):
    AREA = "area"
    RIGIDBODY = "rigidbody"
    KINEMATIC = "kinematic"
    CHARACTER = "character"
    STATIC = "static"
```

**Why not:** Godot's 4 types serve full engine needs. We only need 3 for collision detection.

---

### ❌ Capsule Shapes (V1)
```python
# NOT IMPLEMENTING (in V1):
CapsuleShape
```

**Why not:** Polygons can approximate capsules temporarily. Can add in V2 if needed.

---

## Implementation Phases

### Phase 1: Shared Geometry (1 day)
**Goal:** Extract and generalize collision math  
**File:** `src/tilemap_parser/geometry.py` (NEW)

#### Tasks:
1. **Create geometry.py**
   ```python
   # Low-level collision functions
   def circle_vs_circle(...) -> Optional[CollisionInfo]
   def rect_vs_rect(...) -> Optional[CollisionInfo]
   def polygon_vs_polygon(...) -> Optional[CollisionInfo]
   def rect_vs_circle(...) -> Optional[CollisionInfo]
   def polygon_vs_circle(...) -> Optional[CollisionInfo]
   def polygon_vs_rect(...) -> Optional[CollisionInfo]
   ```

2. **Extract math from collision_runner.py**
   - Adapt existing polygon collision code
   - Generalize for reuse
   - Keep optimizations (inline calculations, early exits)

3. **Add CollisionInfo dataclass**
   ```python
   @dataclass
   class CollisionInfo:
       normal: Tuple[float, float]
       depth: float
   ```

4. **Write unit tests**
   - Test each shape-pair combination
   - Test edge cases (touching, overlapping, separated)
   - Test degenerate cases (zero-size, invalid)

**Deliverable:** Reusable collision math library

---

### Phase 2: Core Detection (2 days)
**Goal:** Object collision detection  
**File:** `src/tilemap_parser/object_collision.py` (NEW)

#### Tasks:
1. **Define protocol**
   ```python
   class ICollidableObject(Protocol):
       x: float
       y: float
       collision_shape: Union[RectangleShape, CircleShape, CollisionPolygon]
       body_type: CollisionBodyType = CollisionBodyType.DYNAMIC
       collision_layer: int = 1
       collision_mask: int = 0xFFFFFFFF
   ```

2. **Define body types**
   ```python
   class CollisionBodyType(Enum):
       STATIC = "static"
       DYNAMIC = "dynamic"
       SENSOR = "sensor"
   ```

3. **Define collision result**
   ```python
   @dataclass
   class CollisionHit:
       object_a: ICollidableObject
       object_b: ICollidableObject
       normal: Tuple[float, float]
       depth: float
   ```

4. **Implement check_collision()**
   ```python
   def check_collision(obj_a, obj_b) -> Optional[CollisionHit]:
       # 1. Check layer filtering
       # 2. Get world-space bounds/shapes
       # 3. Dispatch to geometry.py functions
       # 4. Return CollisionHit or None
   ```

5. **Write unit tests**
   - Test all shape combinations
   - Test layer filtering
   - Test body type filtering

**Deliverable:** Working collision detection function

---

### Phase 3: Manager (1 day)
**Goal:** Multi-object collision management  
**File:** `src/tilemap_parser/object_collision.py` (EXTEND)

#### Tasks:
1. **Implement ObjectCollisionManager**
   ```python
   class ObjectCollisionManager:
       def __init__(self)
       def add_object(obj)
       def remove_object(obj)
       def check_all_collisions() -> List[CollisionHit]
       def check_object(obj) -> List[CollisionHit]
   ```

2. **Implement broadphase optimization**
   ```python
   # Internal, adaptive
   if len(self.objects) < 50:
       # Brute force O(n²)
   else:
       # Spatial hash grid O(n)
   ```

3. **Implement layer filtering**
   ```python
   def _should_collide(obj_a, obj_b) -> bool:
       # Check collision_layer & collision_mask
   ```

4. **Write integration tests**
   - Test with multiple objects
   - Test layer filtering
   - Test broadphase switching
   - Benchmark performance (10, 100, 1000 objects)

**Deliverable:** Complete collision manager

---

### Phase 4: Documentation & Examples (1 day)
**Goal:** Complete documentation and working example  
**Files:** `docs/`, `examples/object-collision-example/`

#### Tasks:
1. **API Documentation**
   - Protocol documentation
   - Manager API reference
   - Function signatures
   - Usage examples

2. **User Guide**
   - Quick start
   - JSON format (reuse existing character collision)
   - Integration with tile collision
   - Layer filtering guide

3. **Example Project**
   ```
   examples/object-collision-example/
   ├── bouncing_balls.py
   ├── data/
   │   ├── ball.collision.json
   │   └── platform.collision.json
   └── README.md
   ```

4. **Code Example**
   ```python
   # Simple bouncing balls example
   from tilemap_parser import (
       ObjectCollisionManager,
       load_character_collision,
       CircleShape,
   )
   
   class Ball:
       def __init__(self, x, y):
           self.x = x
           self.y = y
           self.collision_shape = CircleShape(radius=16)
           self.vx = 100.0
           self.vy = 0.0
   
   manager = ObjectCollisionManager()
   ball1 = Ball(100, 100)
   ball2 = Ball(200, 100)
   manager.add_object(ball1)
   manager.add_object(ball2)
   
   # Game loop
   while running:
       dt = clock.tick(60) / 1000.0
       
       # Update positions (user code)
       ball1.x += ball1.vx * dt
       ball2.x += ball2.vx * dt
       
       # Check collisions
       hits = manager.check_all_collisions()
       for hit in hits:
           # Handle collision (user code)
           # Simple bounce example:
           hit.object_a.vx *= -1
           hit.object_b.vx *= -1
   ```

**Deliverable:** Complete documentation and working example

---

## File Structure

```
src/tilemap_parser/
├── collision.py              # MINIMAL/NO CHANGES
│   ├── CollisionPolygon      # Reused for objects!
│   ├── RectangleShape        # Reused for objects!
│   ├── CircleShape           # Reused for objects!
│   ├── CharacterCollision    # Reused for objects!
│   └── parse_character_collision()  # Already works!
│
├── collision_runner.py       # NO CHANGES
│   └── (tile collision system)
│
├── geometry.py               # NEW - Shared collision math
│   ├── CollisionInfo
│   ├── circle_vs_circle()
│   ├── rect_vs_rect()
│   ├── polygon_vs_polygon()
│   ├── rect_vs_circle()
│   ├── polygon_vs_circle()
│   └── polygon_vs_rect()
│
├── object_collision.py       # NEW - Object collision
│   ├── ICollidableObject (protocol)
│   ├── CollisionBodyType (enum)
│   ├── CollisionHit (dataclass)
│   ├── check_collision()
│   └── ObjectCollisionManager
│
└── __init__.py              # UPDATE - Export new APIs
    └── Export: geometry, object_collision APIs

tests/
├── test_collision.py         # NO CHANGES (existing tests)
├── test_collision_runner.py  # NO CHANGES (existing tests)
├── test_geometry.py          # NEW - Geometry tests
├── test_object_collision.py  # NEW - Object collision tests
└── test_object_collision_integration.py  # NEW - Integration tests

examples/
├── animation-example/        # Existing
├── collision-example/        # Existing
├── game-example/             # Existing
└── object-collision-example/ # NEW
    ├── bouncing_balls.py
    ├── data/
    │   ├── ball.collision.json
    │   └── platform.collision.json
    └── README.md

docs/
└── object_collision.md       # NEW - User guide
```

---

## API Reference

### geometry.py

```python
@dataclass
class CollisionInfo:
    """Low-level collision information"""
    normal: Tuple[float, float]  # Separation direction
    depth: float                  # Penetration depth

def circle_vs_circle(
    c1_center: Point,
    c1_radius: float,
    c2_center: Point,
    c2_radius: float
) -> Optional[CollisionInfo]:
    """Check circle-circle collision"""

def rect_vs_rect(
    r1_bounds: Tuple[float, float, float, float],  # (left, top, right, bottom)
    r2_bounds: Tuple[float, float, float, float]
) -> Optional[CollisionInfo]:
    """Check rectangle-rectangle collision (AABB)"""

def polygon_vs_polygon(
    p1_vertices: List[Point],
    p2_vertices: List[Point]
) -> Optional[CollisionInfo]:
    """Check polygon-polygon collision (SAT)"""

def rect_vs_circle(
    rect_bounds: Tuple[float, float, float, float],
    circle_center: Point,
    circle_radius: float
) -> Optional[CollisionInfo]:
    """Check rectangle-circle collision"""

def polygon_vs_circle(
    poly_vertices: List[Point],
    circle_center: Point,
    circle_radius: float
) -> Optional[CollisionInfo]:
    """Check polygon-circle collision"""

def polygon_vs_rect(
    poly_vertices: List[Point],
    rect_bounds: Tuple[float, float, float, float]
) -> Optional[CollisionInfo]:
    """Check polygon-rectangle collision"""
```

---

### object_collision.py

```python
class ICollidableObject(Protocol):
    """
    Protocol for objects that can collide.
    
    Required:
        x: World X position
        y: World Y position
        collision_shape: Shape for collision
    
    Optional:
        body_type: Type of body (default: DYNAMIC)
        collision_layer: Layer this object is on (default: 1)
        collision_mask: Layers to collide with (default: 0xFFFFFFFF)
    """
    x: float
    y: float
    collision_shape: Union[RectangleShape, CircleShape, CollisionPolygon]
    body_type: CollisionBodyType = CollisionBodyType.DYNAMIC
    collision_layer: int = 1
    collision_mask: int = 0xFFFFFFFF

class CollisionBodyType(Enum):
    """Body type for collision filtering"""
    STATIC = "static"    # Non-moving objects
    DYNAMIC = "dynamic"  # Moving objects
    SENSOR = "sensor"    # Trigger-only (no response)

@dataclass
class CollisionHit:
    """Result of collision detection"""
    object_a: ICollidableObject
    object_b: ICollidableObject
    normal: Tuple[float, float]  # Direction to separate (from A to B)
    depth: float                  # Penetration depth

def check_collision(
    obj_a: ICollidableObject,
    obj_b: ICollidableObject
) -> Optional[CollisionHit]:
    """
    Check if two objects collide.
    
    Args:
        obj_a: First object
        obj_b: Second object
    
    Returns:
        CollisionHit if colliding, None otherwise
    
    Note:
        Respects collision_layer and collision_mask
    """

class ObjectCollisionManager:
    """
    Manages collision detection for multiple objects.
    
    Features:
    - Add/remove objects
    - Query collisions
    - Layer filtering
    - Automatic broadphase optimization
    """
    
    def __init__(self):
        """Initialize collision manager"""
    
    def add_object(self, obj: ICollidableObject):
        """
        Add object to collision system.
        
        Args:
            obj: Object to add
        """
    
    def remove_object(self, obj: ICollidableObject):
        """
        Remove object from collision system.
        
        Args:
            obj: Object to remove
        """
    
    def check_all_collisions(self) -> List[CollisionHit]:
        """
        Check all objects against each other.
        
        Returns:
            List of collision hits
        
        Note:
            Automatically uses spatial grid for >50 objects.
            Respects collision layers and masks.
        """
    
    def check_object(self, obj: ICollidableObject) -> List[CollisionHit]:
        """
        Check one object against all others.
        
        Args:
            obj: Object to check
        
        Returns:
            List of collision hits involving this object
        """
```

---

## Testing Strategy

### Unit Tests

#### test_geometry.py
```python
def test_circle_circle_collision():
    # Test overlapping circles
    # Test touching circles
    # Test separated circles
    # Test edge cases

def test_rect_rect_collision():
    # Test overlapping rects
    # Test touching rects
    # Test separated rects
    # Test edge cases

def test_polygon_polygon_collision():
    # Test overlapping polygons
    # Test touching polygons
    # Test separated polygons
    # Test concave polygons
    # Test edge cases

# ... etc for all shape pairs
```

#### test_object_collision.py
```python
def test_check_collision_circle_circle():
    # Test with ICollidableObject instances

def test_check_collision_layer_filtering():
    # Test layer/mask filtering

def test_manager_add_remove():
    # Test object management

def test_manager_check_all():
    # Test collision queries

def test_manager_broadphase():
    # Test spatial grid activation
```

---

### Integration Tests

#### test_object_collision_integration.py
```python
def test_bouncing_balls():
    # Simulate bouncing balls
    # Verify collisions detected
    # Verify no false positives

def test_with_tile_collision():
    # Test objects + tiles together
    # Verify both systems work independently

def test_layer_filtering_complex():
    # Test complex layer scenarios
    # Multiple layers, multiple masks

def test_performance():
    # Benchmark with 10, 100, 1000 objects
    # Verify < 1ms for 100 objects
    # Verify < 5ms for 1000 objects
```

---

### Coverage Target
- **95%+ code coverage**
- All shape-pair combinations tested
- All edge cases covered
- Performance benchmarks included

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Shared Geometry | 1 day | Reusable collision math |
| Phase 2: Core Detection | 2 days | Working collision detection |
| Phase 3: Manager | 1 day | Complete collision manager |
| Phase 4: Docs & Examples | 1 day | Documentation + example |

**Total: 5 days**

---

## Success Criteria

### Functional Requirements
- ✅ Detect collisions between rect/circle/polygon
- ✅ Support layer/mask filtering
- ✅ Return collision normal and depth
- ✅ Manage multiple objects
- ✅ Automatic broadphase optimization

### Performance Requirements
- ✅ < 1ms for 100 objects
- ✅ < 5ms for 1000 objects (with spatial grid)
- ✅ No unnecessary allocations

### Quality Requirements
- ✅ 95%+ test coverage
- ✅ Complete API documentation
- ✅ Working example project
- ✅ Backward compatible
- ✅ Consistent with existing code

### Architecture Requirements
- ✅ Clean layer separation
- ✅ Shared geometry (no duplication)
- ✅ Parser stays dumb
- ✅ No physics engine
- ✅ No event bus

---

## Key Design Principles

### 1. Focused Scope
**Build:** Collision detection  
**Don't build:** Physics engine, event system, game engine

### 2. Reuse Existing
**Reuse:** Shapes, parser, polygon workflow  
**Don't duplicate:** Collision math, polygon types

### 3. Clean Boundaries
**Separate:** Parser, geometry, runtime, game logic  
**Don't blur:** Layer responsibilities

### 4. Pragmatic Optimization
**Optimize:** Algorithms, broadphase, caching  
**Don't over-optimize:** Micro-optimizations, premature pooling

### 5. Extensible Design
**Allow:** Future additions (capsules, physics helpers)  
**Don't commit:** To full engine features

---

## Migration from Original Plan

### What Was Removed
- ❌ Full physics engine (gravity, velocity, forces)
- ❌ Collision response (bounce, friction, impulse)
- ❌ Event bus system (callbacks, signals)
- ❌ Complex body types (4 types → 3 types)
- ❌ Capsule shapes (delayed to V2)
- ❌ Separate polygon types (reuse existing)
- ❌ Exposed spatial grid API (internal only)

### What Was Kept
- ✅ Collision detection (core feature)
- ✅ Layer filtering (essential)
- ✅ Shared geometry (prevents duplication)
- ✅ Protocol-based design (clean API)
- ✅ Existing polygon workflow (reuse)
- ✅ Backward compatibility (no breaking changes)

### What Was Simplified
- Body types: 4 → 3
- Timeline: 11 days → 5 days
- Files: 6 → 3 new files
- API surface: Smaller, focused
- Scope: Detection only

---

## Next Steps

1. ✅ **Review this plan** - Confirm revised approach
2. 🚀 **Start Phase 1** - Implement shared geometry
3. 🔄 **Iterate** - Test, optimize, refine
4. 📦 **Deliver** - Complete, tested, documented system

---

## Notes

- **Philosophy:** Focused, practical, maintainable
- **Priority:** Correctness > Performance > Features
- **Approach:** Incremental - each phase delivers value
- **Testing:** Test-driven - write tests alongside code
- **Documentation:** Document as you go

---

**End of Revised Implementation Plan**

*This plan reflects the design corrections from POSSIBILITY_OBJ_COLLIISION.md and focuses on building a very good collision detection system, not a mini game engine.*
