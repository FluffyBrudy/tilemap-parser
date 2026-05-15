# Object Collision System - FINAL Implementation Plan

**⚠️ SUPERSEDED - DO NOT USE FOR IMPLEMENTATION**

**This document is kept for historical reference only.**

**Use IMPLEMENTATION_READY.md instead** - it incorporates quality fixes.

**Issues with this document:**
- Presentation format (slide-style) not ideal for implementation
- Layer filtering logic incorrect
- Inside-rectangle depth calculation wrong
- Some implementation details incomplete

**See:** DOCS_EVOLUTION.md for document timeline

---

**Version:** 1.0 (Detection Only)  
**Date:** 2026-05-13  
**Status:** Ready for Implementation

---

# Core Philosophy

Build a **collision detection library**, not a game engine.

This system provides:

- Fast collision detection
- Clean separation from game logic
- Reusable geometry utilities
- Minimal and stable API

This system explicitly avoids:

- Physics simulation
- Event systems
- Engine-like abstractions

---

# Scope Definition

## V1 (Current Implementation)

### Collision Detection

Supports:

- Shape vs shape collision detection
- Collision normal calculation
- Penetration depth calculation

Supported shapes:

- Rectangle (AABB)
- Circle
- Polygon (convex only for runtime objects)

---

### Object Management

Features:

- Add/remove objects
- Query collisions:
  - all-vs-all
  - one-vs-all
- Internal broadphase optimization

---

### Layer Filtering

Supports:

- `collision_layer`
- `collision_mask`

---

### Existing System Reuse

Reuse existing:

- `collision.py`
- Polygon workflow
- Shape definitions
- Parsers

No duplicate geometry formats.

---

## V2 (Future / Optional)

Possible future additions:

- Capsule shapes
- Rotated shapes
- Swept collisions
- Contact manifolds
- Advanced spatial partitioning

---

# Explicitly Out of Scope

This system is **NOT**:

- A physics engine
- A rigidbody simulator
- A response solver
- An event dispatcher
- An ECS/runtime framework

Excluded features:

- Gravity
- Velocity integration
- Friction
- Bounce resolution
- Collision callbacks
- Object lifecycle systems

---

# High-Level Architecture

```text
Editor (Polygon Paint)
        ↓
collision.json
        ↓
collision.py (parser only)
        ↓
geometry.py (pure math)
        ↓
object_collision.py (runtime detection)
        ↓
game logic (user code)
```

---

# Design Principles

## Parser Stays Dumb

Responsibilities:

- Parse data
- Validate data
- Construct shape objects

No runtime logic.

---

## Geometry Is Shared Core

`geometry.py` becomes the shared collision math layer for:

- Tile collision
- Object collision
- Future systems

---

## Runtime Is Minimal

`object_collision.py` only:

- Stores objects
- Performs broadphase
- Performs narrowphase
- Returns collision results

No gameplay behavior.

---

## Game Logic Is External

Users decide:

- Movement
- Resolution
- Damage
- Events
- Triggers

The library only reports collisions.

---

# geometry.py (NEW)

Pure geometry + collision math module.

---

## CollisionInfo

```python
from dataclasses import dataclass

@dataclass(slots=True)
class CollisionInfo:
    normal: tuple[float, float]
    depth: float
```

---

## Responsibilities

Contains narrowphase collision functions:

```python
circle_vs_circle()
rect_vs_rect()
rect_vs_circle()

polygon_vs_polygon()
polygon_vs_circle()
polygon_vs_rect()
```

---

## Polygon Rules

Runtime object polygons:

- MUST be convex
- MUST be non-rotated
- MUST be static in local space

Tile polygons remain unchanged.

---

## Rotation Policy

Rotation is NOT supported in V1.

Excluded:

- Rotated rectangles
- Rotated polygons
- Transform matrices

All runtime shapes are axis-aligned/static.

---

# object_collision.py (NEW)

Runtime collision management layer.

---

# Object Interface

```python
class ICollidableObject:
    x: float
    y: float

    collision_shape: Shape

    collision_layer: int
    collision_mask: int
```

Minimal required runtime contract.

---

# CollisionHit

```python
from dataclasses import dataclass

@dataclass(slots=True)
class CollisionHit:
    object_a: object
    object_b: object

    normal: tuple[float, float]
    depth: float
```

---

# Core Collision Function

```python
def check_collision(obj_a, obj_b):
    """
    Returns CollisionHit or None.
    """
```

Pipeline:

1. Layer filtering
2. Broadphase AABB rejection
3. Narrowphase geometry test
4. Return collision result

---

# Collision Filtering

```python
(a.collision_mask & b.collision_layer) != 0
```

Applied BEFORE geometry checks.

---

# Collision Manager

Provides:

```python
add_object()
remove_object()

check_all_collisions()
check_object()
```

No event systems.

No automatic response solving.

---

# Broadphase Strategy

Internal implementation detail only.

Users never interact with it directly.

---

## Small Object Counts

```text
< 50 objects → brute force
```

Reason:

- Lower overhead
- Better cache behavior

---

## Large Object Counts

```text
≥ 50 objects → spatial hash grid
```

Reason:

- Reduces pair count
- Scales for larger scenes

---

# Runtime Pipeline

```text
Layer Filter
    ↓
AABB Early Reject
    ↓
Narrowphase Collision
    ↓
CollisionHit / None
```

---

# Performance Goals

Target performance:

| Object Count | Target Time |
|---|---|
| 100 objects | ~1ms |
| 1000 objects | ~5ms |

---

# Performance Rules

Critical constraints:

- No allocations in hot loops
- Early exits whenever possible
- Reuse geometry helpers
- Avoid unnecessary tuple creation
- Cache AABBs where possible

---

# collision.py (Existing)

Kept unchanged.

---

## Reused Types

```python
RectangleShape
CircleShape
CollisionPolygon
CharacterCollision
```

No new serialization formats.

No parser redesign.

---

# File Structure

```text
src/tilemap_parser/
├── collision.py
├── collision_runner.py
├── geometry.py
├── object_collision.py
└── __init__.py

tests/
├── test_geometry.py
├── test_object_collision.py
└── test_integration.py

examples/
└── object_collision_demo/
```

---

# Testing Strategy

## geometry.py

Test coverage:

- Every shape pair
- Edge overlaps
- Containment
- Touching edges
- Degenerate cases

---

## object_collision.py

Test coverage:

- Multi-object queries
- Layer filtering correctness
- Broadphase switching
- Stable collision outputs

---

## Integration Tests

Test coverage:

- Tile + object coexistence
- Parser interoperability
- Performance scaling

---

# Success Criteria

## Functional

Requirements:

- All shape pairs work
- Correct normals
- Correct penetration depth
- Correct filtering behavior

---

## Performance

Requirements:

- Real-time performance for 100 objects
- Acceptable scaling to 1000 objects

---

## Architecture Quality

Requirements:

- Clean module separation
- No physics leakage
- Minimal runtime API
- Extensible without redesign

---

# Key Design Wins

## Shared Geometry Core

Single reusable collision math layer.

---

## Minimal Runtime Layer

No unnecessary engine abstractions.

---

## Parser Isolation Preserved

Parsing remains independent from runtime logic.

---

## No Physics Engine Creep

Strict detection-only scope.

---

## Future-Proof Structure

Can extend later without architectural rewrite.

---

# Final V1 Philosophy

This system is intentionally:

- Small
- Fast
- Predictable
- Reusable
- Engine-agnostic

The goal is to provide a reliable collision foundation while avoiding unnecessary engine complexity.

---
