"""
Shared collision geometry utilities.

Pure math layer used by both tile collision (tile_collision.py) and
object collision (object_collision.py).  No runtime state — only
deterministic functions and data types.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Union

from ..parser.collision import CapsuleShape, CircleShape, CollisionPolygon, RectangleShape


@dataclass(slots=True)
class CollisionInfo:
    """Low-level collision result from a narrow-phase test."""

    normal: tuple[float, float]  # Separation direction
    depth: float  # Penetration depth


def aabb_overlap(
    bounds1: tuple[float, float, float, float],
    bounds2: tuple[float, float, float, float],
) -> bool:
    """
    Fast AABB overlap test (broadphase).

    Bounds are (left, top, right, bottom).

    Important: edge-touching counts as collision.  This is intentional
    to avoid floating-point gap issues and keeps broadphase / narrowphase
    semantics consistent.
    """
    l1, t1, r1, b1 = bounds1
    l2, t2, r2, b2 = bounds2
    return not (r1 < l2 or r2 < l1 or b1 < t2 or b2 < t1)


def get_shape_aabb(
    x: float,
    y: float,
    shape: Union[RectangleShape, CircleShape, CollisionPolygon, CapsuleShape],
) -> tuple[float, float, float, float]:
    """
    Return AABB (left, top, right, bottom) for any supported shape.

    Parameters
    ----------
    x, y : float
        World-space origin of the shape's owner.
    shape : RectangleShape | CircleShape | CollisionPolygon | CapsuleShape
        The collision shape to compute bounds for.
    """
    if isinstance(shape, RectangleShape):
        left = x + shape.offset[0]
        top = y + shape.offset[1]
        return (left, top, left + shape.width, top + shape.height)

    if isinstance(shape, CircleShape):
        cx = x + shape.offset[0]
        cy = y + shape.offset[1]
        r = shape.radius
        return (cx - r, cy - r, cx + r, cy + r)

    if isinstance(shape, CapsuleShape):
        ox = x + shape.offset[0]
        oy = y + shape.offset[1]
        r = shape.radius
        return (ox - r, oy - r, ox + r, oy + shape.height + r)

    # CollisionPolygon — min / max over all vertices
    if isinstance(shape, CollisionPolygon):
        ox = x
        oy = y
        verts = shape.vertices
        min_x = max_x = verts[0][0] + ox
        min_y = max_y = verts[0][1] + oy
        for vx, vy in verts[1:]:
            wx = vx + ox
            wy = vy + oy
            if wx < min_x:
                min_x = wx
            elif wx > max_x:
                max_x = wx
            if wy < min_y:
                min_y = wy
            elif wy > max_y:
                max_y = wy
        return (min_x, min_y, max_x, max_y)

    raise TypeError(f"Unsupported shape type: {type(shape).__name__}")


def circle_vs_circle(
    c1_center: tuple[float, float],
    c1_radius: float,
    c2_center: tuple[float, float],
    c2_radius: float,
) -> Optional[CollisionInfo]:
    """
    Circle-circle collision detection.

    Returns CollisionInfo with normal pointing from c1 to c2, or None.
    Edge-touching counts as collision (depth=0).
    """
    dx = c2_center[0] - c1_center[0]
    dy = c2_center[1] - c1_center[1]
    dist_sq = dx * dx + dy * dy
    radius_sum = c1_radius + c2_radius

    if dist_sq > radius_sum * radius_sum:
        return None  # separated

    dist = math.sqrt(dist_sq)
    if dist < 0.0001:
        return CollisionInfo(normal=(1.0, 0.0), depth=radius_sum)

    depth = radius_sum - dist
    normal = (dx / dist, dy / dist)
    return CollisionInfo(normal=normal, depth=depth)


def rect_vs_rect(
    r1_bounds: tuple[float, float, float, float],
    r2_bounds: tuple[float, float, float, float],
) -> Optional[CollisionInfo]:
    """
    AABB-AABB collision detection.

    Returns CollisionInfo with normal pointing from r1 to r2, or None.
    Chooses the axis with minimum penetration for separation.
    Edge-touching counts as collision (depth=0).
    """
    if not aabb_overlap(r1_bounds, r2_bounds):
        return None

    l1, t1, r1, b1 = r1_bounds
    l2, t2, r2, b2 = r2_bounds

    overlap_x = min(r1, r2) - max(l1, l2)
    overlap_y = min(b1, b2) - max(t1, t2)

    if overlap_x < overlap_y:
        normal = (1.0, 0.0) if (l1 + r1) < (l2 + r2) else (-1.0, 0.0)
        depth = overlap_x
    else:
        normal = (0.0, 1.0) if (t1 + b1) < (t2 + b2) else (0.0, -1.0)
        depth = overlap_y

    return CollisionInfo(normal=normal, depth=depth)


def rect_vs_circle(
    rect_bounds: tuple[float, float, float, float],
    circle_center: tuple[float, float],
    circle_radius: float,
) -> Optional[CollisionInfo]:
    """
    AABB-circle collision detection.

    Returns CollisionInfo with normal pointing from rect to circle, or None.
    Handles circle-center-inside-rect using minimal translation distance.
    Edge-touching counts as collision (depth=0).
    """
    l, t, r, b = rect_bounds
    cx, cy = circle_center

    closest_x = max(l, min(cx, r))
    closest_y = max(t, min(cy, b))

    dx = cx - closest_x
    dy = cy - closest_y
    dist_sq = dx * dx + dy * dy

    if dist_sq > circle_radius * circle_radius:
        return None  # no collision

    dist = math.sqrt(dist_sq)

    if dist < 0.0001:
        # Circle center inside rect — minimal translation distance
        dist_left = cx - l
        dist_right = r - cx
        dist_top = cy - t
        dist_bottom = b - cy

        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

        if min_dist == dist_left:
            normal = (-1.0, 0.0)
            depth = circle_radius + dist_left
        elif min_dist == dist_right:
            normal = (1.0, 0.0)
            depth = circle_radius + dist_right
        elif min_dist == dist_top:
            normal = (0.0, -1.0)
            depth = circle_radius + dist_top
        else:
            normal = (0.0, 1.0)
            depth = circle_radius + dist_bottom
    else:
        depth = circle_radius - dist
        normal = (dx / dist, dy / dist)

    return CollisionInfo(normal=normal, depth=depth)


# ---------------------------------------------------------------------------
# Polygon collision (SAT-based)
# ---------------------------------------------------------------------------

def _project_polygon(
    vertices: List[tuple[float, float]],
    axis: tuple[float, float],
) -> tuple[float, float]:
    """Project all vertices onto an axis, return (min, max)."""
    ax, ay = axis
    dot = vertices[0][0] * ax + vertices[0][1] * ay
    proj_min = proj_max = dot
    for i in range(1, len(vertices)):
        dot = vertices[i][0] * ax + vertices[i][1] * ay
        if dot < proj_min:
            proj_min = dot
        elif dot > proj_max:
            proj_max = dot
    return proj_min, proj_max


def _polygon_center(
    vertices: List[tuple[float, float]],
) -> tuple[float, float]:
    """Compute centroid of a polygon."""
    n = len(vertices)
    cx = sum(v[0] for v in vertices) / n
    cy = sum(v[1] for v in vertices) / n
    return cx, cy


def polygon_vs_polygon(
    p1_vertices: List[tuple[float, float]],
    p2_vertices: List[tuple[float, float]],
) -> Optional[CollisionInfo]:
    """
    Convex polygon-polygon collision using the Separating Axis Theorem (SAT).

    Note: Polygons must be convex.  No validation is performed — the caller
    (editor) guarantees convexity.

    Returns CollisionInfo with normal pointing from p1 toward p2, or None.
    Edge-touching counts as collision (depth=0).
    """
    n1 = len(p1_vertices)
    n2 = len(p2_vertices)

    # Compute centers once for normal orientation
    c1x = sum(v[0] for v in p1_vertices) / n1
    c1y = sum(v[1] for v in p1_vertices) / n1
    c2x = sum(v[0] for v in p2_vertices) / n2
    c2y = sum(v[1] for v in p2_vertices) / n2
    to_c2_x = c2x - c1x
    to_c2_y = c2y - c1y

    min_overlap = float("inf")
    best_axis: Optional[tuple[float, float]] = None

    # Test edge normals from p1
    for i in range(n1):
        j = (i + 1) % n1
        ex = p1_vertices[j][0] - p1_vertices[i][0]
        ey = p1_vertices[j][1] - p1_vertices[i][1]
        edge_len = math.sqrt(ex * ex + ey * ey)
        if edge_len < 0.0001:
            continue

        # Perpendicular axis (outward)
        ax = -ey / edge_len
        ay = ex / edge_len

        min1, max1 = _project_polygon(p1_vertices, (ax, ay))
        min2, max2 = _project_polygon(p2_vertices, (ax, ay))

        # Check overlap (touching counts)
        if max1 < min2 or max2 < min1:
            return None  # separating axis found

        overlap = min(max1, max2) - max(min1, min2)
        if overlap < min_overlap:
            min_overlap = overlap
            best_axis = (ax, ay)

    # Test edge normals from p2
    for i in range(n2):
        j = (i + 1) % n2
        ex = p2_vertices[j][0] - p2_vertices[i][0]
        ey = p2_vertices[j][1] - p2_vertices[i][1]
        edge_len = math.sqrt(ex * ex + ey * ey)
        if edge_len < 0.0001:
            continue

        ax = -ey / edge_len
        ay = ex / edge_len

        min1, max1 = _project_polygon(p1_vertices, (ax, ay))
        min2, max2 = _project_polygon(p2_vertices, (ax, ay))

        if max1 < min2 or max2 < min1:
            return None

        overlap = min(max1, max2) - max(min1, min2)
        if overlap < min_overlap:
            min_overlap = overlap
            best_axis = (ax, ay)

    if best_axis is None:
        # Degenerate case: all edges too short, treat as collision
        return CollisionInfo(normal=(1.0, 0.0), depth=0.0)

    # Ensure normal points from p1 toward p2
    ax, ay = best_axis
    if ax * to_c2_x + ay * to_c2_y < 0:
        ax = -ax
        ay = -ay

    return CollisionInfo(normal=(ax, ay), depth=min_overlap)


def _point_in_polygon(
    px: float, py: float, vertices: List[tuple[float, float]]
) -> bool:
    """Ray-casting point-in-polygon test."""
    n = len(vertices)
    inside = False
    j = n - 1
    for i in range(n):
        vi = vertices[i]
        vj = vertices[j]
        if ((vi[1] > py) != (vj[1] > py)) and (
            px < (vj[0] - vi[0]) * (py - vi[1]) / (vj[1] - vi[1]) + vi[0]
        ):
            inside = not inside
        j = i
    return inside


def _closest_point_on_segment(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float,
) -> tuple[float, float]:
    """Find closest point on segment AB to point P."""
    abx = bx - ax
    aby = by - ay
    ab_len_sq = abx * abx + aby * aby
    if ab_len_sq < 0.0001:
        return ax, ay
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / ab_len_sq))
    return ax + t * abx, ay + t * aby


def polygon_vs_circle(
    poly_vertices: List[tuple[float, float]],
    circle_center: tuple[float, float],
    circle_radius: float,
) -> Optional[CollisionInfo]:
    """
    Convex polygon-circle collision.

    Note: Polygon must be convex.

    Returns CollisionInfo with normal pointing from polygon toward circle,
    or None.  Edge-touching counts as collision (depth=0).
    """
    cx, cy = circle_center
    r = circle_radius

    inside = _point_in_polygon(cx, cy, poly_vertices)

    min_dist_sq = float("inf")
    best_closest_x = 0.0
    best_closest_y = 0.0
    best_normal_x = 0.0
    best_normal_y = 0.0

    n = len(poly_vertices)
    for i in range(n):
        ax, ay = poly_vertices[i]
        bx, by = poly_vertices[(i + 1) % n]

        closest_x, closest_y = _closest_point_on_segment(cx, cy, ax, ay, bx, by)
        dx = cx - closest_x
        dy = cy - closest_y
        dist_sq = dx * dx + dy * dy

        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            best_closest_x = closest_x
            best_closest_y = closest_y
            dist = math.sqrt(dist_sq) if dist_sq > 0.0 else 0.0
            if dist > 0.0001:
                best_normal_x = dx / dist
                best_normal_y = dy / dist
            else:
                # Degenerate: circle center on edge — use edge normal
                ex = bx - ax
                ey = by - ay
                edge_len = math.sqrt(ex * ex + ey * ey)
                if edge_len > 0.0001:
                    best_normal_x = -ey / edge_len
                    best_normal_y = ex / edge_len
                else:
                    best_normal_x = 1.0
                    best_normal_y = 0.0

    if inside:
        # Circle center inside polygon — depth = radius + distance to edge
        depth = r + math.sqrt(min_dist_sq)
    else:
        if min_dist_sq > r * r:
            return None
        depth = r - math.sqrt(min_dist_sq)

    return CollisionInfo(
        normal=(best_normal_x, best_normal_y),
        depth=depth,
    )


def polygon_vs_rect(
    poly_vertices: List[tuple[float, float]],
    rect_bounds: tuple[float, float, float, float],
) -> Optional[CollisionInfo]:
    """
    Convex polygon-rectangle (AABB) collision.

    Converts rect to a 4-vertex polygon and delegates to polygon_vs_polygon.
    Normal points from polygon toward rect.
    """
    l, t, r, b = rect_bounds
    rect_verts: List[tuple[float, float]] = [(l, t), (r, t), (r, b), (l, b)]
    return polygon_vs_polygon(poly_vertices, rect_verts)


# ---------------------------------------------------------------------------
# Capsule collision
# ---------------------------------------------------------------------------

def _segment_closest_point_to_point(
    ax: float, ay: float,
    bx: float, by: float,
    px: float, py: float,
) -> tuple[float, float]:
    """Closest point on segment AB to point P."""
    abx = bx - ax
    aby = by - ay
    ab_len_sq = abx * abx + aby * aby
    if ab_len_sq < 0.0001:
        return ax, ay
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / ab_len_sq))
    return ax + t * abx, ay + t * aby


def _segment_closest_point_to_aabb(
    ax: float, ay: float,
    bx: float, by: float,
    l: float, t: float, r: float, b: float,
) -> tuple[float, float, float]:
    """
    Closest point on segment AB to AABB (l,t,r,b).

    Returns (closest_x, closest_y, distance_squared).
    """
    abx = bx - ax
    aby = by - ay
    ab_len_sq = abx * abx + aby * aby

    best_dsq = float("inf")
    best_x = ax
    best_y = ay

    def _try(px: float, py: float) -> None:
        nonlocal best_dsq, best_x, best_y
        cpx = max(l, min(px, r))
        cpy = max(t, min(py, b))
        dx = px - cpx
        dy = py - cpy
        dsq = dx * dx + dy * dy
        if dsq < best_dsq:
            best_dsq = dsq
            best_x = px
            best_y = py

    _try(ax, ay)
    _try(bx, by)

    if ab_len_sq > 0.0001:
        for cx, cy in [(l, t), (r, t), (r, b), (l, b)]:
            t_proj = ((cx - ax) * abx + (cy - ay) * aby) / ab_len_sq
            t_clamped = max(0.0, min(1.0, t_proj))
            _try(ax + t_clamped * abx, ay + t_clamped * aby)

    return best_x, best_y, best_dsq


def _segments_closest_points(
    a1x: float, a1y: float, a2x: float, a2y: float,
    b1x: float, b1y: float, b2x: float, b2y: float,
) -> tuple[tuple[float, float], tuple[float, float], float]:
    """
    Closest points between two segments and distance² between them.

    Returns ((pa_x, pa_y), (pb_x, pb_y), dist_sq).
    """
    d1x = a2x - a1x
    d1y = a2y - a1y
    d2x = b2x - b1x
    d2y = b2y - b1y

    d1_len_sq = d1x * d1x + d1y * d1y
    d2_len_sq = d2x * d2x + d2y * d2y

    # Both degenerate — closest points are the segment starts
    if d1_len_sq < 0.0001 and d2_len_sq < 0.0001:
        dx = b1x - a1x
        dy = b1y - a1y
        return (a1x, a1y), (b1x, b1y), dx * dx + dy * dy

    # First degenerate (point)
    if d1_len_sq < 0.0001:
        px, py = _segment_closest_point_to_point(b1x, b1y, b2x, b2y, a1x, a1y)
        dx = px - a1x
        dy = py - a1y
        return (a1x, a1y), (px, py), dx * dx + dy * dy

    # Second degenerate (point)
    if d2_len_sq < 0.0001:
        px, py = _segment_closest_point_to_point(a1x, a1y, a2x, a2y, b1x, b1y)
        dx = px - b1x
        dy = py - b1y
        return (px, py), (b1x, b1y), dx * dx + dy * dy

    # Both are segments — solve analytically
    rx = a1x - b1x
    ry = a1y - b1y
    a = d1_len_sq
    b = d1x * d2x + d1y * d2y
    c = d2_len_sq
    d = d1x * rx + d1y * ry
    e = d2x * rx + d2y * ry

    det = a * c - b * b
    if det < 0.0001:
        # Parallel — check all endpoint-edge combinations
        best_dsq = float("inf")
        best_p = (a1x, a1y)
        best_q = (b1x, b1y)
        for pa, pb in [
            ((a1x, a1y), _segment_closest_point_to_point(b1x, b1y, b2x, b2y, a1x, a1y)),
            ((a2x, a2y), _segment_closest_point_to_point(b1x, b1y, b2x, b2y, a2x, a2y)),
            ((b1x, b1y), _segment_closest_point_to_point(a1x, a1y, a2x, a2y, b1x, b1y)),
            ((b2x, b2y), _segment_closest_point_to_point(a1x, a1y, a2x, a2y, b2x, b2y)),
        ]:
            dx = pb[0] - pa[0]
            dy = pb[1] - pa[1]
            dsq = dx * dx + dy * dy
            if dsq < best_dsq:
                best_dsq = dsq
                best_p = pa
                best_q = pb
        return best_p, best_q, best_dsq

    s = (b * e - c * d) / det
    t = (a * e - b * d) / det
    s = max(0.0, min(1.0, s))
    t = max(0.0, min(1.0, t))

    pa_x = a1x + s * d1x
    pa_y = a1y + s * d1y
    pb_x = b1x + t * d2x
    pb_y = b1y + t * d2y

    dx = pb_x - pa_x
    dy = pb_y - pa_y
    return (pa_x, pa_y), (pb_x, pb_y), dx * dx + dy * dy


def capsule_vs_circle(
    cap_p1: tuple[float, float],
    cap_p2: tuple[float, float],
    cap_radius: float,
    circle_center: tuple[float, float],
    circle_radius: float,
) -> Optional[CollisionInfo]:
    """
    Capsule-circle collision.

    Normal points from capsule toward circle.
    """
    px, py = _segment_closest_point_to_point(
        cap_p1[0], cap_p1[1], cap_p2[0], cap_p2[1],
        circle_center[0], circle_center[1],
    )
    return circle_vs_circle(
        (px, py), cap_radius,
        circle_center, circle_radius,
    )


def capsule_vs_capsule(
    p1: tuple[float, float],
    p2: tuple[float, float],
    r1: float,
    q1: tuple[float, float],
    q2: tuple[float, float],
    r2: float,
) -> Optional[CollisionInfo]:
    """
    Capsule-capsule collision.

    Normal points from capsule A (p1-p2) toward capsule B (q1-q2).
    """
    (pa_x, pa_y), (pb_x, pb_y), _ = _segments_closest_points(
        p1[0], p1[1], p2[0], p2[1],
        q1[0], q1[1], q2[0], q2[1],
    )
    return circle_vs_circle(
        (pa_x, pa_y), r1,
        (pb_x, pb_y), r2,
    )


def capsule_vs_rect(
    cap_p1: tuple[float, float],
    cap_p2: tuple[float, float],
    cap_radius: float,
    rect_bounds: tuple[float, float, float, float],
) -> Optional[CollisionInfo]:
    """
    Capsule-rectangle (AABB) collision.

    Finds closest point on capsule segment to rect, then delegates to
    rect_vs_circle.  Normal points from capsule toward rect (flipped
    from rect_vs_circle output).
    """
    px, py, _ = _segment_closest_point_to_aabb(
        cap_p1[0], cap_p1[1], cap_p2[0], cap_p2[1],
        rect_bounds[0], rect_bounds[1], rect_bounds[2], rect_bounds[3],
    )
    result = rect_vs_circle(rect_bounds, (px, py), cap_radius)
    if result is None:
        return None
    return CollisionInfo(
        normal=(-result.normal[0], -result.normal[1]),
        depth=result.depth,
    )


def _segment_closest_point_to_polygon(
    ax: float, ay: float,
    bx: float, by: float,
    vertices: List[tuple[float, float]],
) -> tuple[float, float, float]:
    """
    Closest point on segment AB to convex polygon and distance squared.

    Checks segment endpoints, projected polygon vertices, and
    segment-to-edge pairs.  O(n²) but polygons are small.
    """
    abx = bx - ax
    aby = by - ay
    ab_len_sq = abx * abx + aby * aby
    n = len(vertices)

    best_dsq = float("inf")
    best_x = ax
    best_y = ay

    def _dist_to_poly_sq(px: float, py: float) -> float:
        """Minimum distance² from point to any polygon edge (0 if inside)."""
        inside = True
        min_dsq = float("inf")
        for i in range(n):
            vax, vay = vertices[i]
            vbx, vby = vertices[(i + 1) % n]
            # Edge normal direction check for inside test
            ex = vbx - vax
            ey = vby - vay
            nx = -ey
            ny = ex
            dx = px - vax
            dy = py - vay
            if nx * dx + ny * dy < 0:
                inside = False
            cx, cy = _closest_point_on_segment(px, py, vax, vay, vbx, vby)
            ddx = px - cx
            ddy = py - cy
            dsq = ddx * ddx + ddy * ddy
            if dsq < min_dsq:
                min_dsq = dsq
        return 0.0 if inside else min_dsq

    def _try(px: float, py: float) -> None:
        nonlocal best_dsq, best_x, best_y
        dsq = _dist_to_poly_sq(px, py)
        if dsq < best_dsq:
            best_dsq = dsq
            best_x = px
            best_y = py

    _try(ax, ay)
    _try(bx, by)

    if ab_len_sq > 0.0001:
        for vx, vy in vertices:
            t_proj = ((vx - ax) * abx + (vy - ay) * aby) / ab_len_sq
            t_clamped = max(0.0, min(1.0, t_proj))
            _try(ax + t_clamped * abx, ay + t_clamped * aby)

    for i in range(n):
        vax, vay = vertices[i]
        vbx, vby = vertices[(i + 1) % n]
        (pa_x, pa_y), _, _ = _segments_closest_points(
            ax, ay, bx, by, vax, vay, vbx, vby,
        )
        _try(pa_x, pa_y)

    return best_x, best_y, best_dsq


def capsule_vs_polygon(
    cap_p1: tuple[float, float],
    cap_p2: tuple[float, float],
    cap_radius: float,
    poly_vertices: List[tuple[float, float]],
) -> Optional[CollisionInfo]:
    """
    Capsule-convex-polygon collision.

    Finds closest point on capsule segment to polygon, then delegates to
    polygon_vs_circle.  Normal points from capsule toward polygon
    (flipped from polygon_vs_circle output).
    """
    px, py, _ = _segment_closest_point_to_polygon(
        cap_p1[0], cap_p1[1], cap_p2[0], cap_p2[1],
        poly_vertices,
    )
    result = polygon_vs_circle(poly_vertices, (px, py), cap_radius)
    if result is None:
        return None
    return CollisionInfo(
        normal=(-result.normal[0], -result.normal[1]),
        depth=result.depth,
    )
