"""
Naive AABB rect collision vs SAT polygon collision — why bounding boxes lie.

A diamond polygon is filled in purple; its AABB is overlaid as a faint
red rectangle. Move the character with arrow keys, switch shape with
1-2-3.  Watch the two collision indicators diverge when the character
enters the AABB corners but hasn't touched the actual polygon.

AABB uses get_shape_aabb + aabb_overlap (axis-aligned bounding box).
SAT uses check_collision (Separating Axis Theorem on the exact polygon).
"""

import math
import sys

import pygame

from tilemap_parser.parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)
from tilemap_parser.runtime.object_collision import check_collision
from tilemap_parser.utils.geometry import aabb_overlap, get_shape_aabb

# ── Config ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1000, 700
FPS = 60
MOVE_SPEED = 4

CHAR_NAMES = ["Rect", "Circle", "Capsule"]

CHAR_DEFS: dict[str, object] = {
    "Rect": RectangleShape(width=36, height=56),
    "Circle": CircleShape(radius=24),
    "Capsule": CapsuleShape(radius=16, height=32),
}

# Diamond (rotated square) — big gap between AABB and actual shape
_DIAMOND = [(0, -70), (70, 0), (0, 70), (-70, 0)]
POLYGON_TARGET = CollisionPolygon(vertices=_DIAMOND)

COLOR_BG = (25, 25, 35)
COLOR_CHAR_IDLE = (70, 130, 220)
COLOR_TARGET_IDLE = (160, 90, 200)
COLOR_AABB_FILL = (255, 100, 100, 35)
COLOR_AABB_LINE = (255, 120, 120)
COLOR_SAT_COLLIDE = (60, 220, 100)
COLOR_SAT_IDLE = (60, 160, 80)
COLOR_AABB_COLLIDE = (220, 60, 60)
COLOR_AABB_IDLE = (140, 70, 70)
COLOR_NORMAL = (255, 60, 60)
COLOR_WHITE = (220, 220, 220)
COLOR_DIM = (140, 140, 160)


class CollidableObject:
    def __init__(self, x: float, y: float, shape: object) -> None:
        self.x = x
        self.y = y
        self.shape_name = ""
        self.collision_shape = shape
        self.collision_layer = 1
        self.collision_mask = 0xFFFFFFFF


# ── Drawing helpers ─────────────────────────────────────────────────


def _offset(shape: object) -> tuple[float, float]:
    return shape.offset if hasattr(shape, "offset") else (0.0, 0.0)


def draw_filled(screen, shape, x, y, color):
    ox, oy = _offset(shape)
    if isinstance(shape, CircleShape):
        pygame.draw.circle(screen, color, (x + ox, y + oy), shape.radius)
    elif isinstance(shape, RectangleShape):
        pygame.draw.rect(screen, color, (x + ox, y + oy, shape.width, shape.height))
    elif isinstance(shape, CollisionPolygon):
        verts = [(x + vx, y + vy) for vx, vy in shape.vertices]
        pygame.draw.polygon(screen, color, verts)
    elif isinstance(shape, CapsuleShape):
        cx, cy = x + ox, y + oy
        pygame.draw.circle(screen, color, (cx, cy), shape.radius)
        pygame.draw.circle(screen, color, (cx, cy + shape.height), shape.radius)
        pygame.draw.rect(screen, color, (cx - shape.radius, cy, shape.radius * 2, shape.height))


def draw_outline(screen, shape, x, y, color, width=2):
    ox, oy = _offset(shape)
    if isinstance(shape, CircleShape):
        pygame.draw.circle(screen, color, (x + ox, y + oy), shape.radius, width)
    elif isinstance(shape, RectangleShape):
        pygame.draw.rect(screen, color, (x + ox, y + oy, shape.width, shape.height), width)
    elif isinstance(shape, CollisionPolygon):
        verts = [(x + vx, y + vy) for vx, vy in shape.vertices]
        pygame.draw.polygon(screen, color, verts, width)
    elif isinstance(shape, CapsuleShape):
        cx, cy = x + ox, y + oy
        pygame.draw.circle(screen, color, (cx, cy), shape.radius, width)
        pygame.draw.circle(screen, color, (cx, cy + shape.height), shape.radius, width)
        pygame.draw.rect(screen, color, (cx - shape.radius, cy, shape.radius * 2, shape.height), width)


def draw_normal_arrow(screen, hit, a, b):
    mx = (a.x + b.x) / 2
    my = (a.y + b.y) / 2
    length = hit.depth * 3 + 30
    ex = mx + hit.normal[0] * length
    ey = my + hit.normal[1] * length
    pygame.draw.line(screen, COLOR_NORMAL, (mx, my), (ex, ey), 3)
    angle = math.atan2(hit.normal[1], hit.normal[0])
    for sign in (-1, 1):
        px = ex - 10 * math.cos(angle + sign * 0.45)
        py = ey - 10 * math.sin(angle + sign * 0.45)
        pygame.draw.line(screen, COLOR_NORMAL, (ex, ey), (px, py), 3)


# ── Info overlay ────────────────────────────────────────────────────


def draw_panel(screen, font, char_name, aabb_result, sat_result, match):
    lines = [
        ("Collision Detection Comparison", (230, 230, 230)),
        ("", (230, 230, 230)),
        (
            f"AABB (naive):     {'COLLIDING' if aabb_result else 'separated'}",
            (255, 140, 140) if aabb_result else (160, 110, 110),
        ),
        (
            f"SAT  (polygon):   {'COLLIDING' if sat_result else 'separated'}",
            (140, 255, 140) if sat_result else (110, 160, 110),
        ),
        ("", (230, 230, 230)),
        (f"Match:             {'YES' if match else 'MISMATCH'}  {'✓' if match else '✗ — naive is wrong!'}", (230, 230, 230) if match else (255, 140, 140)),
        ("", (230, 230, 230)),
        (f"Character shape:   {char_name}", (230, 230, 230)),
        ("Target shape:     Polygon (diamond)", (230, 230, 230)),
    ]

    pw = 320
    ph = len(lines) * 20 + 10
    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 170))
    screen.blit(panel, (8, 6))
    y = 14
    for text, color in lines:
        screen.blit(font.render(text, True, color), (14, y))
        y += 20

    # Explanation panel
    if not match:
        exp_lines = [
            "Naive AABB says COLLIDE because the",
            "character's box overlaps the polygon's",
            "bounding box.  But the actual diamond",
            "shape has empty corners — SAT correctly",
            "reports no contact.",
        ]
        ew = 310
        eh = len(exp_lines) * 18 + 10
        epanel = pygame.Surface((ew, eh), pygame.SRCALPHA)
        epanel.fill((0, 0, 0, 170))
        screen.blit(epanel, (8, y - 4))
        for text in exp_lines:
            rendered = font.render(text, True, (180, 180, 190))
            screen.blit(rendered, (14, y))
            y += 18


def draw_controls(screen, font):
    cw, ch = 520, 22
    cpanel = pygame.Surface((cw, ch), pygame.SRCALPHA)
    cpanel.fill((0, 0, 0, 150))
    screen.blit(cpanel, (8, SCREEN_H - 26))
    x = 14
    y = SCREEN_H - 24
    items = [
        ("Arrows", "move character"),
        ("1-2-3", "Rect / Circle / Capsule"),
        ("R", "reset position"),
    ]
    for label, desc in items:
        lbl = font.render(label, True, (255, 200, 100))
        dsc = font.render(f"  {desc}", True, (180, 180, 190))
        screen.blit(lbl, (x, y))
        screen.blit(dsc, (x + lbl.get_width(), y))
        x += lbl.get_width() + dsc.get_width() + 30


# ── Main ────────────────────────────────────────────────────────────


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Naive AABB vs SAT Polygon — Comparison")
    font = pygame.font.SysFont("monospace", 15)
    clock = pygame.time.Clock()

    char = CollidableObject(200, 350, CHAR_DEFS["Rect"])
    char.shape_name = "Rect"
    char_reset = (200.0, 350.0)

    target = CollidableObject(650, 350, POLYGON_TARGET)
    target.shape_name = "Polygon"

    char_idx = 0

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_3:
                    char_idx = event.key - pygame.K_1
                elif event.key == pygame.K_r:
                    char.x, char.y = char_reset

        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        char.x += dx * MOVE_SPEED
        char.y += dy * MOVE_SPEED
        char.x = max(40, min(SCREEN_W - 40, char.x))
        char.y = max(60, min(SCREEN_H - 60, char.y))

        # Apply shape change
        name = CHAR_NAMES[char_idx]
        if char.shape_name != name:
            char.shape_name = name
            char.collision_shape = CHAR_DEFS[name]

        # ── Two collision checks ──
        char_aabb = get_shape_aabb(char.x, char.y, char.collision_shape)
        poly_aabb = get_shape_aabb(target.x, target.y, target.collision_shape)
        aabb_result = aabb_overlap(char_aabb, poly_aabb)

        sat_hit = check_collision(char, target)
        sat_result = sat_hit is not None

        match = aabb_result == sat_result

        # ── Render ──
        screen.fill(COLOR_BG)

        # Grid
        for gx in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, (35, 35, 48), (gx, 0), (gx, SCREEN_H), 1)
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.line(screen, (35, 35, 48), (0, gy), (SCREEN_W, gy), 1)

        # ── Polygon AABB overlay (faint red) ──
        left, top, right, bottom = poly_aabb
        bw, bh = right - left, bottom - top
        aabb_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        aabb_surf.fill(COLOR_AABB_FILL)
        screen.blit(aabb_surf, (left, top))
        pygame.draw.rect(screen, COLOR_AABB_LINE, (left, top, bw, bh), 2)

        # ── Target polygon ──
        draw_filled(screen, target.collision_shape, target.x, target.y, COLOR_TARGET_IDLE)
        draw_outline(screen, target.collision_shape, target.x, target.y, COLOR_WHITE)

        # ── Character ──
        cc = COLOR_SAT_COLLIDE if sat_result else COLOR_CHAR_IDLE
        draw_filled(screen, char.collision_shape, char.x, char.y, cc)
        draw_outline(screen, char.collision_shape, char.x, char.y, COLOR_WHITE)

        # Highlight AABB false-positive region
        if aabb_result and not sat_result:
            overlap_left = max(char_aabb[0], poly_aabb[0])
            overlap_top = max(char_aabb[1], poly_aabb[1])
            overlap_right = min(char_aabb[2], poly_aabb[2])
            overlap_bottom = min(char_aabb[3], poly_aabb[3])
            ow = overlap_right - overlap_left
            oh = overlap_bottom - overlap_top
            if ow > 0 and oh > 0:
                warn = pygame.Surface((ow, oh), pygame.SRCALPHA)
                warn.fill((255, 0, 0, 50))
                screen.blit(warn, (overlap_left, overlap_top))
                pygame.draw.rect(screen, (255, 60, 60), (overlap_left, overlap_top, ow, oh), 2)

        if sat_hit is not None:
            draw_normal_arrow(screen, sat_hit, char, target)

        draw_panel(screen, font, CHAR_NAMES[char_idx], aabb_result, sat_result, match)
        draw_controls(screen, font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
