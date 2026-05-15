# Object Collision System - IMPLEMENTATION READY
**Final Specification - Ready to Code**

**Version:** 1.1 (Detection Only - Quality Reviewed)  
**Date:** 2026-05-15  
**Status:** ✅ CANONICAL - This is the authoritative specification  
**Timeline:** 5 days  
**Risk Level:** LOW (Incremental, well-scoped)

---

## ⚠️ IMPORTANT: This is the CANONICAL specification

**All other planning documents are SUPERSEDED by this document.**

Superseded documents (for reference only):
- OBJECT_COLLISION_IMPLEMENTATION_PLAN.md (initial plan - too broad)
- POSSIBILITY_OBJ_COLLIISION.md (design corrections)
- REVISED_IMPLEMENTATION_PLAN.md (incorporated corrections)
- FINAL_REVISION_ON_TOP_OBJ_COLLISION.md (presentation format)
- OBJECT_COLLISION_SUMMARY.md (quick reference)

**If there are conflicts, THIS DOCUMENT is correct.**

---

## Quality Review Corrections

This specification incorporates critical fixes from quality review:

### 1. ✅ Layer Filtering Fixed
**Issue:** Original used `or` which created asymmetric filtering  
**Fix:** Now uses `and` for mutual agreement (standard behavior)

### 2. ✅ Touching Policy Documented
**Clarification:** Edge-touching counts as collision (prevents floating-point gaps)

### 3. ✅ Inside-Rectangle Depth Fixed
**Issue:** Depth calculation was incorrect when circle inside rect  
**Fix:** Now uses minimal translation distance (correct separation)

### 4. ✅ Polygon Type Clarified
**Clarification:** Uses `CollisionPolygon` for both tiles and objects (no separate type)

### 5. ✅ Spatial Grid Removed
**Cleanup:** Removed premature optimization flags (V1 is brute-force only)

### 6. ✅ Canonical Documentation
**Status:** This document is now the single source of truth

---

## Executive Summary

### What We're Building
A **collision detection library** for dynamic objects (enemies, projectiles, moving platforms).

### What We're NOT Building
- ❌ Physics engine
- ❌ Collision response solver
- ❌ Event system
- ❌ Game engine features

### Core Principle
> **Detection only. Game logic decides response.**

---

## Critical Success Factors

### ✅ Approved Scope
- Shape-vs-shape collision detection (rect, circle, polygon)
- Collision normal + penetration depth
- Layer-based filtering (mutual agreement)
- Multi-object management
- Brute-force collision (V1 - no spatial partitioning yet)

### ✅ Collision Semantics
**Important behavioral decisions:**
- **Edge-touching counts as collision** - Prevents floating-point gaps
- **Depth = minimal translation distance** - Consistent separation semantics
- **Layer filtering uses AND** - Both objects must agree to collide
- **Polygon type = CollisionPolygon** - Reused for both tiles and objects

### ✅ Approved Architecture
- **geometry.py** - Shared collision math (reusable)
- **object_collision.py** - Runtime detection (minimal)
- **collision.py** - Parser (unchanged)

### ✅ Approved Timeline
- **5 days total** (vs 11 days in original plan)
- Incremental delivery (each step works independently)

---

## Implementation Steps (Prioritized & Risk-Minimized)

### STEP 1: Extract Geometry Helpers (Day 1)
**Goal:** Create shared collision math foundation  
**Risk:** LOW - Extracting existing, proven code  
**File:** `src/tilemap_parser/geometry.py` (NEW)

#### What to Extract
From `collision_runner.py`, extract and generalize:
- AABB overlap test
- Circle distance test
- Point-in-polygon test (ray casting)
- Polygon AABB calculation

#### Deliverable
```python
# geometry.py

@dataclass(slots=True)
class CollisionInfo:
    """Low-level collision result"""
    normal: tuple[float, float]  # Separation direction
    depth: float                  # Penetration depth

def aabb_overlap(
    bounds1: tuple[float, float, float, float],  # (left, top, right, bottom)
    bounds2: tuple[float, float, float, float]
) -> bool:
    """
    Fast AABB overlap test (broadphase).
    
    Important: Edge-touching counts as collision.
    This is intentional to avoid floating-point gap issues.
    """
    l1, t1, r1, b1 = bounds1
    l2, t2, r2, b2 = bounds2
    return not (r1 < l2 or r2 < l1 or b1 < t2 or b2 < t1)

def get_shape_aabb(
    x: float,
    y: float,
    shape: Union[RectangleShape, CircleShape, CollisionPolygon]
) -> tuple[float, float, float, float]:
    """Get AABB for any shape type"""
    # Dispatch based on shape type
```

#### Tests
```python
# test_geometry.py
def test_aabb_overlap_separated()
def test_aabb_overlap_touching()
def test_aabb_overlap_overlapping()
def test_get_shape_aabb_rectangle()
def test_get_shape_aabb_circle()
def test_get_shape_aabb_polygon()
```

**Validation:** All tests pass, no regressions in existing code

---

### STEP 2: Add Circle & AABB Collision (Day 2)
**Goal:** Implement simplest shape-vs-shape collision  
**Risk:** LOW - Well-understood algorithms  
**File:** `src/tilemap_parser/geometry.py` (EXTEND)

#### Implement
```python
def circle_vs_circle(
    c1_center: tuple[float, float],
    c1_radius: float,
    c2_center: tuple[float, float],
    c2_radius: float
) -> Optional[CollisionInfo]:
    """
    Circle-circle collision detection.
    
    Returns:
        CollisionInfo with normal pointing from c1 to c2, or None
    
    Note: Touching circles (depth=0) count as collision per spec policy.
          This is consistent with aabb_overlap behavior.
    """
    dx = c2_center[0] - c1_center[0]
    dy = c2_center[1] - c1_center[1]
    dist_sq = dx * dx + dy * dy
    radius_sum = c1_radius + c2_radius
    
    # CRITICAL: Use > not >= to include touching (depth=0) as collision
    if dist_sq > radius_sum * radius_sum:
        return None  # Separated (no collision)
    
    dist = math.sqrt(dist_sq)
    if dist < 0.0001:  # Centers coincide
        return CollisionInfo(normal=(1.0, 0.0), depth=radius_sum)
    
    depth = radius_sum - dist
    normal = (dx / dist, dy / dist)
    return CollisionInfo(normal=normal, depth=depth)

def rect_vs_rect(
    r1_bounds: tuple[float, float, float, float],
    r2_bounds: tuple[float, float, float, float]
) -> Optional[CollisionInfo]:
    """
    AABB-AABB collision detection.
    
    Returns:
        CollisionInfo with normal pointing from r1 to r2, or None
    """
    if not aabb_overlap(r1_bounds, r2_bounds):
        return None
    
    # Calculate overlap on each axis
    l1, t1, r1, b1 = r1_bounds
    l2, t2, r2, b2 = r2_bounds
    
    overlap_x = min(r1, r2) - max(l1, l2)
    overlap_y = min(b1, b2) - max(t1, t2)
    
    # Choose axis with minimum penetration
    if overlap_x < overlap_y:
        # Separate on X axis
        normal = (1.0, 0.0) if (l1 + r1) < (l2 + r2) else (-1.0, 0.0)
        depth = overlap_x
    else:
        # Separate on Y axis
        normal = (0.0, 1.0) if (t1 + b1) < (t2 + b2) else (0.0, -1.0)
        depth = overlap_y
    
    return CollisionInfo(normal=normal, depth=depth)

def rect_vs_circle(
    rect_bounds: tuple[float, float, float, float],
    circle_center: tuple[float, float],
    circle_radius: float
) -> Optional[CollisionInfo]:
    """
    AABB-circle collision detection.
    
    Returns:
        CollisionInfo with normal pointing from rect to circle, or None
    """
    # Find closest point on rect to circle center
    l, t, r, b = rect_bounds
    cx, cy = circle_center
    
    closest_x = max(l, min(cx, r))
    closest_y = max(t, min(cy, b))
    
    # Check distance
    dx = cx - closest_x
    dy = cy - closest_y
    dist_sq = dx * dx + dy * dy
    
    if dist_sq >= circle_radius * circle_radius:
        return None  # No collision
    
    dist = math.sqrt(dist_sq)
    
    if dist < 0.0001:  # Circle center inside rect
        # Find closest edge and compute minimal separation
        dist_left = cx - l
        dist_right = r - cx
        dist_top = cy - t
        dist_bottom = b - cy
        
        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
        
        # CRITICAL: Depth is minimal translation distance
        # (not circle_radius + edge_dist which grows as circle moves deeper)
        if min_dist == dist_left:
            normal = (-1.0, 0.0)
            depth = circle_radius - dist_left  # Minimal separation
        elif min_dist == dist_right:
            normal = (1.0, 0.0)
            depth = circle_radius - dist_right
        elif min_dist == dist_top:
            normal = (0.0, -1.0)
            depth = circle_radius - dist_top
        else:
            normal = (0.0, 1.0)
            depth = circle_radius - dist_bottom
    else:
        depth = circle_radius - dist
        normal = (dx / dist, dy / dist)
    
    return CollisionInfo(normal=normal, depth=depth)
```

#### Tests
```python
# test_geometry.py
def test_circle_vs_circle_separated()
def test_circle_vs_circle_touching()
def test_circle_vs_circle_overlapping()
def test_circle_vs_circle_coincident()

def test_rect_vs_rect_separated()
def test_rect_vs_rect_touching()
def test_rect_vs_rect_overlapping()

def test_rect_vs_circle_separated()
def test_rect_vs_circle_touching()
def test_rect_vs_circle_overlapping()
def test_rect_vs_circle_inside()
```

**Validation:** All shape pairs work correctly with proper normals/depth

---

### STEP 3: Add Object Collision Runtime (Day 3)
**Goal:** Create object management and collision queries  
**Risk:** LOW - Simple wrapper around geometry functions  
**File:** `src/tilemap_parser/object_collision.py` (NEW)

#### Implement
```python
# object_collision.py

from typing import Protocol, Union, Optional, List
from dataclasses import dataclass
from .collision import RectangleShape, CircleShape, CollisionPolygon
from .geometry import (
    CollisionInfo,
    get_shape_aabb,
    aabb_overlap,
    circle_vs_circle,
    rect_vs_rect,
    rect_vs_circle,
)

class ICollidableObject(Protocol):
    """
    Protocol for objects that can collide.
    
    Required attributes:
        x: World X position
        y: World Y position
        collision_shape: Shape for collision (RectangleShape, CircleShape, or CollisionPolygon)
        collision_layer: Layer this object is on (default: 1)
        collision_mask: Layers to collide with (default: 0xFFFFFFFF)
    
    Note: Uses CollisionPolygon (not a separate PolygonShape type).
          The existing CollisionPolygon works for both tiles and objects.
    """
    x: float
    y: float
    collision_shape: Union[RectangleShape, CircleShape, CollisionPolygon]
    collision_layer: int
    collision_mask: int

@dataclass(slots=True)
class CollisionHit:
    """Result of collision detection"""
    object_a: ICollidableObject
    object_b: ICollidableObject
    normal: tuple[float, float]  # Direction to separate (from A to B)
    depth: float                  # Penetration depth

def _should_collide(obj_a: ICollidableObject, obj_b: ICollidableObject) -> bool:
    """
    Check if two objects should collide based on layers.
    
    Uses mutual agreement: BOTH objects must want to collide.
    This prevents asymmetric filtering issues.
    
    Example:
        - Player (layer=1, mask=2) wants to collide with Enemy (layer=2)
        - Enemy (layer=2, mask=0) ignores everything
        - Result: NO collision (mutual agreement required)
    """
    a_layer = getattr(obj_a, 'collision_layer', 1)
    a_mask = getattr(obj_a, 'collision_mask', 0xFFFFFFFF)
    b_layer = getattr(obj_b, 'collision_layer', 1)
    b_mask = getattr(obj_b, 'collision_mask', 0xFFFFFFFF)
    
    # CRITICAL: Use AND for mutual agreement (not OR)
    return (a_mask & b_layer) != 0 and (b_mask & a_layer) != 0

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
    """
    # Layer filtering
    if not _should_collide(obj_a, obj_b):
        return None
    
    # Get AABBs for broadphase
    aabb_a = get_shape_aabb(obj_a.x, obj_a.y, obj_a.collision_shape)
    aabb_b = get_shape_aabb(obj_b.x, obj_b.y, obj_b.collision_shape)
    
    # Broadphase rejection
    if not aabb_overlap(aabb_a, aabb_b):
        return None
    
    # Narrowphase - dispatch based on shape types
    shape_a = obj_a.collision_shape
    shape_b = obj_b.collision_shape
    
    collision_info = None
    
    # Circle vs Circle
    if isinstance(shape_a, CircleShape) and isinstance(shape_b, CircleShape):
        center_a = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        center_b = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        collision_info = circle_vs_circle(center_a, shape_a.radius, center_b, shape_b.radius)
    
    # Rect vs Rect
    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, RectangleShape):
        collision_info = rect_vs_rect(aabb_a, aabb_b)
    
    # Rect vs Circle (or Circle vs Rect)
    elif isinstance(shape_a, RectangleShape) and isinstance(shape_b, CircleShape):
        center_b = (obj_b.x + shape_b.offset[0], obj_b.y + shape_b.offset[1])
        collision_info = rect_vs_circle(aabb_a, center_b, shape_b.radius)
    
    elif isinstance(shape_a, CircleShape) and isinstance(shape_b, RectangleShape):
        center_a = (obj_a.x + shape_a.offset[0], obj_a.y + shape_a.offset[1])
        info = rect_vs_circle(aabb_b, center_a, shape_a.radius)
        if info:
            # Flip normal (was from rect to circle, need from circle to rect)
            collision_info = CollisionInfo(
                normal=(-info.normal[0], -info.normal[1]),
                depth=info.depth
            )
    
    # Polygon support comes in STEP 4
    else:
        return None  # Unsupported shape combination (for now)
    
    if collision_info is None:
        return None
    
    return CollisionHit(
        object_a=obj_a,
        object_b=obj_b,
        normal=collision_info.normal,
        depth=collision_info.depth
    )

class ObjectCollisionManager:
    """
    Manages collision detection for multiple objects.
    
    Features:
    - Add/remove objects
    - Query collisions
    - Layer filtering
    
    Note: V1 uses brute-force collision detection.
          Spatial partitioning is a future optimization (V2).
    """
    
    def __init__(self):
        """Initialize collision manager"""
        self.objects: List[ICollidableObject] = []
    
    def add_object(self, obj: ICollidableObject):
        """Add object to collision system"""
        if obj not in self.objects:
            self.objects.append(obj)
    
    def remove_object(self, obj: ICollidableObject):
        """Remove object from collision system"""
        if obj in self.objects:
            self.objects.remove(obj)
    
    def check_all_collisions(self) -> List[CollisionHit]:
        """
        Check all objects against each other (brute force).
        
        Returns:
            List of collision hits
        
        Performance: O(n²) - acceptable for <100 objects
        """
        hits = []
        n = len(self.objects)
        
        for i in range(n):
            for j in range(i + 1, n):
                hit = check_collision(self.objects[i], self.objects[j])
                if hit:
                    hits.append(hit)
        
        return hits
    
    def check_object(self, obj: ICollidableObject) -> List[CollisionHit]:
        """
        Check one object against all others.
        
        Args:
            obj: Object to check
        
        Returns:
            List of collision hits involving this object
        """
        hits = []
        
        for other in self.objects:
            if other is obj:
                continue
            
            hit = check_collision(obj, other)
            if hit:
                hits.append(hit)
        
        return hits
```

#### Tests
```python
# test_object_collision.py
def test_check_collision_circle_circle()
def test_check_collision_rect_rect()
def test_check_collision_rect_circle()
def test_check_collision_layer_filtering()

def test_manager_add_remove()
def test_manager_check_all()
def test_manager_check_object()
def test_manager_layer_filtering()
```

**Validation:** Object management works, collisions detected correctly

---

### STEP 4: Add Polygon Support (Day 4)
**Goal:** Add polygon collision (SAT algorithm)  
**Risk:** MEDIUM - More complex algorithm, but well-documented  
**File:** `src/tilemap_parser/geometry.py` (EXTEND)

#### Implement
```python
# geometry.py

def polygon_vs_polygon(
    p1_vertices: List[tuple[float, float]],
    p2_vertices: List[tuple[float, float]]
) -> Optional[CollisionInfo]:
    """
    Polygon-polygon collision using SAT (Separating Axis Theorem).
    
    Note: Polygons must be convex.
    
    Returns:
        CollisionInfo with normal and depth, or None
    """
    # SAT implementation
    # Test all edge normals from both polygons
    # Find minimum penetration axis
    # Return normal and depth
    pass  # Implementation details

def polygon_vs_circle(
    poly_vertices: List[tuple[float, float]],
    circle_center: tuple[float, float],
    circle_radius: float
) -> Optional[CollisionInfo]:
    """
    Polygon-circle collision.
    
    Returns:
        CollisionInfo with normal and depth, or None
    """
    # Check if circle center inside polygon
    # Check distance to each edge
    # Return closest collision
    pass  # Implementation details

def polygon_vs_rect(
    poly_vertices: List[tuple[float, float]],
    rect_bounds: tuple[float, float, float, float]
) -> Optional[CollisionInfo]:
    """
    Polygon-rectangle collision.
    
    Returns:
        CollisionInfo with normal and depth, or None
    """
    # Convert rect to polygon (4 vertices)
    # Use polygon_vs_polygon
    pass  # Implementation details
```

#### Update object_collision.py
```python
# Add polygon cases to check_collision()
elif isinstance(shape_a, CollisionPolygon) and isinstance(shape_b, CollisionPolygon):
    verts_a = [(obj_a.x + v[0], obj_a.y + v[1]) for v in shape_a.vertices]
    verts_b = [(obj_b.x + v[0], obj_b.y + v[1]) for v in shape_b.vertices]
    collision_info = polygon_vs_polygon(verts_a, verts_b)

# ... other polygon combinations
```

#### Tests
```python
# test_geometry.py
def test_polygon_vs_polygon_separated()
def test_polygon_vs_polygon_overlapping()
def test_polygon_vs_circle()
def test_polygon_vs_rect()
```

**Validation:** Polygon collisions work correctly

---

### STEP 5: Documentation & Example (Day 5)
**Goal:** Complete documentation and working example  
**Risk:** LOW - Documentation task  
**Files:** `docs/`, `examples/object-collision-example/`

#### Create Example
```python
# examples/object-collision-example/bouncing_balls.py

import pygame
from tilemap_parser import ObjectCollisionManager, CircleShape

class Ball:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.collision_shape = CircleShape(radius=16, offset=(0, 0))
        self.collision_layer = 1
        self.collision_mask = 1

# Initialize
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

manager = ObjectCollisionManager()

# Create balls
balls = [
    Ball(100, 100, 100, 50),
    Ball(200, 150, -80, 30),
    Ball(300, 200, 60, -40),
]

for ball in balls:
    manager.add_object(ball)

# Game loop
running = True
while running:
    dt = clock.tick(60) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update positions
    for ball in balls:
        ball.x += ball.vx * dt
        ball.y += ball.vy * dt
        
        # Bounce off walls
        if ball.x < 16 or ball.x > 784:
            ball.vx *= -1
        if ball.y < 16 or ball.y > 584:
            ball.vy *= -1
    
    # Check collisions
    hits = manager.check_all_collisions()
    for hit in hits:
        # Simple bounce response
        hit.object_a.vx *= -1
        hit.object_a.vy *= -1
        hit.object_b.vx *= -1
        hit.object_b.vy *= -1
        
        # Separate objects
        sep_x = hit.normal[0] * hit.depth * 0.5
        sep_y = hit.normal[1] * hit.depth * 0.5
        hit.object_a.x -= sep_x
        hit.object_a.y -= sep_y
        hit.object_b.x += sep_x
        hit.object_b.y += sep_y
    
    # Render
    screen.fill((0, 0, 0))
    for ball in balls:
        pygame.draw.circle(screen, (255, 255, 255), (int(ball.x), int(ball.y)), 16)
    pygame.display.flip()

pygame.quit()
```

#### Write Documentation
- API reference for all functions
- Usage guide
- Integration examples
- Performance tips

**Validation:** Example runs, documentation complete

---

## Risk Mitigation

### Why This Approach is Low-Risk

1. **Incremental Steps** - Each step delivers working functionality
2. **Existing Code Reuse** - Extracting proven collision math
3. **Simple Algorithms** - Circle/AABB are well-understood
4. **Polygon Last** - Most complex part comes after foundation is solid
5. **No Physics** - Avoiding complex scope creep

### Rollback Strategy

If any step fails:
- **Step 1 fails:** No impact, nothing changed yet
- **Step 2 fails:** geometry.py still has AABB helpers (useful)
- **Step 3 fails:** geometry.py still reusable
- **Step 4 fails:** Circle/rect collision still works
- **Step 5 fails:** Code still works, just undocumented

---

## Performance Targets

| Metric | Target | Validation |
|--------|--------|------------|
| 100 objects | < 1ms | Benchmark test |
| 1000 objects | < 5ms | Benchmark test |
| Memory overhead | Minimal | No object pools needed |
| Allocations | Minimal | Reuse result objects |

---

## Success Criteria

### Functional
- ✅ Circle-circle collision works
- ✅ Rect-rect collision works
- ✅ Rect-circle collision works
- ✅ Polygon collision works (Step 4)
- ✅ Layer filtering works
- ✅ Correct normals and depth

### Performance
- ✅ Meets performance targets
- ✅ No unnecessary allocations
- ✅ Early exits work

### Quality
- ✅ 95%+ test coverage
- ✅ All tests pass
- ✅ Documentation complete
- ✅ Example works

### Architecture
- ✅ Clean module separation
- ✅ No physics leakage
- ✅ Parser unchanged
- ✅ Reusable geometry

---

## Final Checklist Before Starting

- [ ] Read this document completely
- [ ] Understand each step's goal
- [ ] Have test strategy ready
- [ ] Know rollback plan
- [ ] Confirm 5-day timeline acceptable
- [ ] Confirm scope (detection only)
- [ ] Confirm no physics engine
- [ ] Ready to start Step 1

---

## Post-Implementation

### V2 Considerations (Future)
If needed later:
- Capsule shapes
- Rotated shapes
- Swept collision
- Spatial grid optimization
- Contact manifolds

### What NOT to Add
Never add to this library:
- Physics simulation
- Rigidbody dynamics
- Event systems
- Game engine features

---

## Summary

This implementation plan is:
- ✅ **Focused** - Detection only
- ✅ **Incremental** - 5 clear steps
- ✅ **Low-risk** - Each step validates before next
- ✅ **Practical** - Reuses existing code
- ✅ **Complete** - Includes tests and docs
- ✅ **Timeline-conscious** - 5 days total

**Status: READY TO IMPLEMENT** 🚀

---

**Next Action:** Begin Step 1 - Extract geometry helpers from collision_runner.py
