# Object Collision System – Design Corrections & Simplifications

**⚠️ REFERENCE DOCUMENT - Important Context**

**This document contains critical design corrections that shaped the final specification.**

**Status:** Reference only - explains WHY decisions were made  
**For implementation:** Use IMPLEMENTATION_READY.md  
**Value:** Understanding the reasoning behind scope reduction

**Key insights from this document:**
- Why we don't build a physics engine
- Why we keep the polygon paint system
- Why we use simple body types
- Why we avoid event systems
- Why we focus on detection only

**See:** DOCS_EVOLUTION.md for document timeline

---

**Goal:** Keep the system extensible enough for future engine features while avoiding premature complexity.

---

# 1. MOST IMPORTANT CORRECTION:

## Do NOT Turn This Into a Full Physics Engine Yet

Current plan mixes:

* collision detection
* collision response
* rigidbody physics
* movement systems
* event systems

These should NOT all arrive in v1.

## Recommended Scope

### V1 SHOULD ONLY DO:

* shape definitions
* shape-vs-shape detection
* broadphase filtering
* collision querying
* optional overlap info

### V1 SHOULD NOT DO:

* gravity
* velocity integration
* bounce physics
* friction solving
* impulse resolution
* physics stepping
* rigidbody simulation

Reason:
A proper physics engine becomes an entirely separate subsystem and will quickly dominate architecture decisions.

Current use cases:

* moving platforms
* bullets
* enemies
* bouncing objects

can already be handled by:

* user-controlled movement
* collision detection
* optional simple separation helpers

without full physics simulation.

---

# 2. KEEP POLYGON PAINT SYSTEM

## DO NOT REPLACE IT

Your current editor polygon paint system is GOOD.

This was the biggest architectural concern earlier.

## Correct Direction

Keep:

* grid tile polygon painting
* object tileset polygon painting

The runtime system simply consumes the same polygon data differently.

Meaning:

* editor workflow stays unified
* parser remains reusable
* users learn one collision authoring workflow

This is the correct balance between:

* flexibility
* usability
* maintainability

---

# 3. DO NOT CREATE SEPARATE TILE/OBJECT POLYGON TYPES YET

Current proposal:

* CollisionPolygon
* PolygonShape

This may be unnecessary duplication.

## Better Approach

Use ONE polygon class:

```python
@dataclass
class CollisionPolygon:
    vertices: List[Point]
    offset: Point = (0.0, 0.0)
    one_way: bool = False
```

Then:

* tiles use `one_way`
* objects ignore it

Reason:
The actual geometry is identical.

Creating:

* tile polygon
* object polygon
* dynamic polygon
* runtime polygon

too early creates maintenance burden.

Only split types later if behavior genuinely diverges.

---

# 4. BODY TYPES ARE SLIGHTLY OVERENGINEERED FOR V1

Current proposal copies Godot fully:

* AREA
* DYNAMIC
* KINEMATIC
* STATIC

This is probably too much initially.

## Recommended Simpler Model

Start with:

```python
class CollisionBodyType(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    SENSOR = "sensor"
```

Explanation:

* STATIC → map/platforms/walls
* DYNAMIC → moving collidable objects
* SENSOR → trigger-only

You can later expand into:

* kinematic
* rigidbody
* characterbody

without breaking architecture.

---

# 5. AVOID FULL EVENT BUS SYSTEM

Current proposal:

```python
manager.connect_collision(callback)
```

This is starting to become engine infrastructure.

## Simpler

Return collision results:

```python
collisions = manager.check_all_collisions()
```

or:

```python
for collision in manager.iter_collisions():
```

Let the game layer decide event handling.

This keeps parser/runtime decoupled.

---

# 6. DO NOT OVERCOMMIT TO ZERO ALLOCATIONS

This optimization target:

> “No allocations in hot paths”

is good philosophy but dangerous if applied too early.

## Better Rule

Optimize:

* broadphase
* polygon math
* repeated transforms

But do NOT:

* ruin readability
* create object pools everywhere
* micro-optimize prematurely

Especially because:
Python itself allocates constantly.

Focus on:

* avoiding unnecessary list creation
* avoiding repeated polygon transforms
* caching bounds

NOT:

* trying to mimic C++ ECS engines.

---

# 7. SPATIAL GRID SHOULD BE OPTIONAL & INTERNAL

Good idea:

* brute force for small counts
* spatial hash for larger counts

But:
DO NOT expose this in API.

## Bad

```python
manager = ObjectCollisionManager(use_spatial_grid=True)
```

## Better

Internal automatic optimization:

```python
manager = ObjectCollisionManager()
```

The manager decides internally.

Cleaner API.
Less future maintenance.

---

# 8. COLLISION RESPONSE SHOULD STAY MINIMAL

This part risks spiraling:

```python
penetration
normal
restitution
friction
```

## Recommended

V1 collision result:

```python
@dataclass
class CollisionHit:
    object_a
    object_b
    normal
    depth
```

Enough for:

* pushback
* simple bouncing
* platform collision
* triggers

You can build proper physics later on top.

---

# 9. CAPSULE SUPPORT MAY BE PREMATURE

Current priorities:

* rect
* circle
* capsule
* polygon

Realistically:
capsules are mainly useful for:

* character controllers

If timeline matters:

## Recommended Order

### V1

* rectangle
* circle
* polygon

### V2

* capsule

Reason:
Polygon already solves most capsule use cases temporarily.

---

# 10. DO NOT DUPLICATE TILE COLLISION LOGIC

Very important.

Current danger:

* tile collision code
* object collision code
* duplicated SAT/math

## Better

Create shared low-level geometry helpers:

```python
geometry.py
```

Example:

```python
polygon_vs_polygon()
circle_vs_circle()
rect_vs_circle()
sat_test()
```

Then:

* tile collision uses them
* object collision uses them

This prevents future desync bugs.

---

# 11. KEEP PARSER DUMB

Critical architectural point.

Parser should ONLY:

* parse data
* validate data
* cache data

Parser should NOT:

* know physics
* know movement
* know runtime behavior
* know broadphase
* know collision response

Good architecture boundary:

```text
Editor
  ↓
Parser
  ↓
Collision Runtime
  ↓
Game Logic
```

Do not blur these layers.

---

# 12. AVOID GODOT FEATURE PARITY THINKING

This is extremely important.

You are inspired by Godot.
Good.

But:
you are NOT building Godot.

Avoid:

* reproducing every body type
* reproducing every physics behavior
* reproducing every node abstraction

Instead:
identify your actual game/runtime needs.

Current needs are much smaller and clearer.

That is GOOD.

---

# 13. RECOMMENDED FINAL V1 SCOPE

## KEEP

### Shapes

* rectangle
* circle
* polygon

### Runtime

* object-vs-object detection
* broadphase
* collision querying
* layer filtering

### Editor

* existing polygon painter

### Parser

* extend existing parser minimally

---

# 14. RECOMMENDED V2 SCOPE

After real-world usage:

Add only if needed:

* capsules
* collision response helpers
* spatial partition tuning
* trigger callbacks
* simple physics helpers
* swept collision
* continuous collision detection

---

# 15. BEST ARCHITECTURAL DECISION IN CURRENT PLAN

This one is VERY correct:

> Create object_collision.py instead of modifying collision_runner.py heavily

Keep this decision.

It preserves:

* stability
* maintainability
* backward compatibility

Very good call.

---

# 16. FINAL RECOMMENDATION SUMMARY

## Strongly Keep

* existing polygon paint workflow
* parser/runtime separation
* separate object collision module
* layer filtering
* adaptive broadphase
* protocol-based design

## Simplify

* body types
* event system
* physics integration
* polygon type duplication
* optimization targets

## Delay

* full physics
* capsules
* advanced response
* engine-style abstractions

## Most Important Principle

Build:
“a very good collision system”

NOT:
“a mini game engine”
