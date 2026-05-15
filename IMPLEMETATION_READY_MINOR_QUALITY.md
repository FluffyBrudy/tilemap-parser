# IMPLEMENTATION_READY - Potential Refactors Before Implementation

**⚠️ REFERENCE DOCUMENT - Quality Review**

**This document contains critical quality fixes that were incorporated into IMPLEMENTATION_READY.md v1.1**

**Status:** Reference only - explains specific bugs that were fixed  
**For implementation:** Use IMPLEMENTATION_READY.md (already includes these fixes)  
**Value:** Understanding what was corrected and why

**Critical fixes from this document:**
1. Layer filtering logic (AND not OR) - CRITICAL BUG
2. Touching policy clarification - Important behavior
3. Inside-rectangle depth calculation - CRITICAL BUG
4. Polygon type consistency - Clarification
5. Spatial grid cleanup - Removed premature optimization
6. Canonical documentation - Established single source of truth

**See:** DOCS_EVOLUTION.md for document timeline

---

**Status:** Optional cleanup before coding
**Goal:** Fix a few specification inconsistencies without expanding scope
**Important:** These are NOT architecture rewrites. The implementation remains detection-only.

---

# Purpose

During review, several small inconsistencies were identified in the implementation spec.

Most are minor, but fixing them now avoids:

* confusing behavior
* inconsistent collision semantics
* unnecessary implementation churn later

This document intentionally avoids adding new systems or complexity.

---

# 1. Collision Layer Filtering Semantics

## Current Spec

```python
return (a_mask & b_layer) != 0 or (b_mask & a_layer) != 0
```

## Problem

Using `or` means collision occurs if only ONE object wants collision.

Example:

* Player wants to collide with enemy
* Enemy explicitly ignores player

Collision still happens.

This creates asymmetric filtering behavior.

---

## Recommended Change

Use mutual agreement (`and`) instead:

```python
return (
    (a_mask & b_layer) != 0 and
    (b_mask & a_layer) != 0
)
```

## Why

This matches standard collision filtering behavior used in most engines and avoids surprising results.

---

# 2. Define "Touching" Collision Policy

## Current Spec

AABB overlap currently treats touching edges as overlap:

```python
return not (
    r1 < l2 or
    r2 < l1 or
    b1 < t2 or
    b2 < t1
)
```

## Important Clarification

This is NOT necessarily wrong.

The issue is simply that the behavior should be explicitly documented.

---

## Recommended Decision

Keep touching as collision.

Reason:

* simpler broadphase behavior
* common in tile/platform collision systems
* avoids tiny floating-point gaps

---

## Documentation Note

Explicitly state:

> "Edge-touching counts as collision throughout the collision system."

This keeps broadphase and narrowphase behavior consistent.

---

# 3. rect_vs_circle Inside-Rectangle Penetration Depth

## Current Spec

Inside-rectangle case:

```python
depth = circle_radius + dist_left
```

## Problem

This does not represent minimal separation distance.

Depth becomes larger as the circle moves deeper inside the rectangle.

That can produce incorrect separation later when collision response is added externally.

---

## Recommended Change

Compute minimal translation depth only.

Example logic:

```python
depth = circle_radius - min_dist_to_edge
```

(or equivalent minimal-separation formulation)

---

## Goal

Keep collision depth semantics consistent:

* depth = minimum distance required to separate shapes

---

# 4. Polygon Shape Type Consistency

## Current Situation

Some planning docs suggest:

* creating a separate `PolygonShape`

Other docs suggest:

* reusing `CollisionPolygon`

---

## Recommended Decision

Reuse `CollisionPolygon`.

Do NOT create:

* tile polygon type
* object polygon type
* PolygonShape duplicate

---

## Why

This keeps:

* API simpler
* tests simpler
* geometry helpers reusable
* fewer conversions required

---

# 5. Spatial Grid Expectations

## Current Situation

Spec includes:

```python
self._use_spatial_grid = len(self.objects) >= 50
```

But no actual grid implementation yet.

---

## Recommended Change

Keep brute-force implementation for V1.

Either:

* remove `_use_spatial_grid`
* OR clearly mark it as future optimization placeholder

---

## Important

Do NOT implement spatial partitioning yet.

Current scope is intentionally:

* simple
* incremental
* low-risk

---

# 6. Canonical Documentation

## Current Situation

Multiple planning documents now exist:

* OBJECT_COLLISION_IMPLEMENTATION_PLAN.md
* REVISED_IMPLEMENTATION_PLAN.md
* FINAL_REVISION_ON_TOP_OBJ_COLLISION.md
* IMPLEMENTATION_READY.md
* etc.

Some sections contradict each other.

---

## Recommended Change

Make:

```text
IMPLEMENTATION_READY.md
```

the single canonical specification.

Archive or mark older planning docs as superseded.

---

# Final Recommendation

These changes are intentionally small.

They:

* improve correctness
* reduce ambiguity
* avoid future rewrites

WITHOUT:

* adding physics
* adding engine architecture
* adding ECS patterns
* adding event systems
* expanding scope

Core implementation plan remains unchanged:

1. Extract geometry helpers
2. Add AABB/circle collision
3. Add object collision manager
4. Add SAT polygon support
5. Add docs/examples

Implementation remains:

* lightweight
* detection-only
* incremental
* low-risk
