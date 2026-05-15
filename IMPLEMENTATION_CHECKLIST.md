# Object Collision Implementation - Checklist

**Use this checklist to track implementation progress**

---

## Pre-Implementation

- [ ] Read IMPLEMENTATION_READY.md completely
- [ ] Understand all 5 implementation steps
- [ ] Confirm 5-day timeline is acceptable
- [ ] Understand scope (detection only, no physics)
- [ ] Review quality fixes (layer filtering, depth calculation)
- [ ] Set up test environment

---

## Step 1: Extract Geometry Helpers (Day 1)

### Implementation
- [ ] Create `src/tilemap_parser/geometry.py`
- [ ] Add `CollisionInfo` dataclass
- [ ] Implement `aabb_overlap()` function
- [ ] Implement `get_shape_aabb()` function
- [ ] Extract AABB calculation logic from collision_runner.py
- [ ] Add proper docstrings

### Testing
- [ ] Create `tests/test_geometry.py`
- [ ] Test `aabb_overlap()` - separated cases
- [ ] Test `aabb_overlap()` - touching cases
- [ ] Test `aabb_overlap()` - overlapping cases
- [ ] Test `get_shape_aabb()` - RectangleShape
- [ ] Test `get_shape_aabb()` - CircleShape
- [ ] Test `get_shape_aabb()` - CollisionPolygon

### Validation
- [ ] All tests pass
- [ ] No regressions in existing code
- [ ] Code coverage ≥ 95%

---

## Step 2: Add Circle & AABB Collision (Day 2)

### Implementation
- [ ] Implement `circle_vs_circle()` in geometry.py
- [ ] Implement `rect_vs_rect()` in geometry.py
- [ ] Implement `rect_vs_circle()` in geometry.py
- [ ] Handle edge cases (coincident centers, inside rect)
- [ ] Ensure correct normal directions
- [ ] Ensure correct depth calculations (minimal separation)
- [ ] Add proper docstrings

### Testing
- [ ] Test `circle_vs_circle()` - separated
- [ ] Test `circle_vs_circle()` - touching
- [ ] Test `circle_vs_circle()` - overlapping
- [ ] Test `circle_vs_circle()` - coincident centers
- [ ] Test `rect_vs_rect()` - separated
- [ ] Test `rect_vs_rect()` - touching
- [ ] Test `rect_vs_rect()` - overlapping
- [ ] Test `rect_vs_circle()` - separated
- [ ] Test `rect_vs_circle()` - touching
- [ ] Test `rect_vs_circle()` - overlapping
- [ ] Test `rect_vs_circle()` - circle inside rect (critical!)

### Validation
- [ ] All tests pass
- [ ] Normals point in correct direction
- [ ] Depth represents minimal separation
- [ ] Edge-touching counts as collision
- [ ] Code coverage ≥ 95%

---

## Step 3: Add Object Collision Runtime (Day 3)

### Implementation
- [ ] Create `src/tilemap_parser/object_collision.py`
- [ ] Define `ICollidableObject` protocol
- [ ] Define `CollisionHit` dataclass
- [ ] Implement `_should_collide()` helper (use AND, not OR!)
- [ ] Implement `check_collision()` function
- [ ] Handle all shape-pair combinations (circle, rect)
- [ ] Implement `ObjectCollisionManager` class
- [ ] Implement `add_object()` method
- [ ] Implement `remove_object()` method
- [ ] Implement `check_all_collisions()` method (brute force)
- [ ] Implement `check_object()` method
- [ ] Add proper docstrings

### Testing
- [ ] Create `tests/test_object_collision.py`
- [ ] Test `check_collision()` - circle vs circle
- [ ] Test `check_collision()` - rect vs rect
- [ ] Test `check_collision()` - rect vs circle
- [ ] Test `check_collision()` - circle vs rect (flipped)
- [ ] Test layer filtering - both agree
- [ ] Test layer filtering - one disagrees (no collision)
- [ ] Test layer filtering - both disagree (no collision)
- [ ] Test `ObjectCollisionManager.add_object()`
- [ ] Test `ObjectCollisionManager.remove_object()`
- [ ] Test `ObjectCollisionManager.check_all_collisions()`
- [ ] Test `ObjectCollisionManager.check_object()`

### Validation
- [ ] All tests pass
- [ ] Layer filtering uses AND (mutual agreement)
- [ ] Manager handles multiple objects correctly
- [ ] No duplicate collision reports
- [ ] Code coverage ≥ 95%

---

## Step 4: Add Polygon Support (Day 4)

### Implementation
- [ ] Implement `polygon_vs_polygon()` in geometry.py (SAT)
- [ ] Implement `polygon_vs_circle()` in geometry.py
- [ ] Implement `polygon_vs_rect()` in geometry.py
- [ ] Update `check_collision()` to handle polygon cases
- [ ] Handle CollisionPolygon with offset
- [ ] Add proper docstrings

### Testing
- [ ] Test `polygon_vs_polygon()` - separated
- [ ] Test `polygon_vs_polygon()` - touching
- [ ] Test `polygon_vs_polygon()` - overlapping
- [ ] Test `polygon_vs_circle()` - separated
- [ ] Test `polygon_vs_circle()` - overlapping
- [ ] Test `polygon_vs_circle()` - circle inside polygon
- [ ] Test `polygon_vs_rect()` - separated
- [ ] Test `polygon_vs_rect()` - overlapping
- [ ] Test polygon collision in manager

### Validation
- [ ] All tests pass
- [ ] Polygon collisions work correctly
- [ ] Normals and depth correct
- [ ] Code coverage ≥ 95%

---

## Step 5: Documentation & Example (Day 5)

### Documentation
- [ ] Write API reference for geometry.py
- [ ] Write API reference for object_collision.py
- [ ] Write user guide (quick start)
- [ ] Document collision semantics (touching, depth, layers)
- [ ] Document integration with tile collision
- [ ] Document performance characteristics
- [ ] Add code examples to docstrings

### Example Project
- [ ] Create `examples/object-collision-example/`
- [ ] Create `bouncing_balls.py` example
- [ ] Create example collision JSON files
- [ ] Create README.md for example
- [ ] Test example runs correctly
- [ ] Add comments explaining key concepts

### Integration
- [ ] Update `src/tilemap_parser/__init__.py` to export new APIs
- [ ] Verify no breaking changes to existing APIs
- [ ] Run all existing tests (collision.py, collision_runner.py)
- [ ] Create integration test (tiles + objects together)

### Validation
- [ ] Example runs without errors
- [ ] Documentation is complete and clear
- [ ] All tests pass (new and existing)
- [ ] Code coverage ≥ 95% overall
- [ ] No breaking changes

---

## Final Validation

### Functional Requirements
- [ ] Circle-circle collision works
- [ ] Rect-rect collision works
- [ ] Rect-circle collision works
- [ ] Polygon collision works
- [ ] Layer filtering works (mutual agreement)
- [ ] Correct normals returned
- [ ] Correct depth returned
- [ ] Multi-object queries work

### Performance Requirements
- [ ] Benchmark with 100 objects < 1ms
- [ ] Benchmark with 1000 objects < 5ms
- [ ] No unnecessary allocations in hot paths

### Quality Requirements
- [ ] 95%+ test coverage
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Example works
- [ ] No breaking changes

### Architecture Requirements
- [ ] Clean module separation
- [ ] No physics engine features
- [ ] Parser unchanged
- [ ] Reusable geometry
- [ ] Uses CollisionPolygon (not separate type)

---

## Post-Implementation

- [ ] Code review
- [ ] Performance profiling
- [ ] Update main README.md
- [ ] Tag release (if applicable)
- [ ] Archive planning documents

---

## Notes

**Critical reminders:**
- Layer filtering uses AND (not OR)
- Depth = minimal translation distance
- Edge-touching counts as collision
- Use CollisionPolygon (not separate type)
- V1 is brute-force (no spatial grid)
- Detection only (no physics)

**If stuck:**
- Re-read IMPLEMENTATION_READY.md
- Check DOCS_EVOLUTION.md for context
- Ask questions - don't guess

---

**Status:** Ready to begin  
**Estimated Time:** 5 days  
**Risk Level:** LOW

Good luck! 🚀
