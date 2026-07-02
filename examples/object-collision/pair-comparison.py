"""
Object Collision Visual Demo — see every shape pair in action.

Move the active (blue) object with arrow keys.
Change shapes with 1-4 (active) and Q/R/T/Y (target).
Only the specific narrowphase check for the current pair runs.
On collision: green tint, depth readout, normal arrow.
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

# ── Config ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1000, 700
FPS = 60
MOVE_SPEED = 4

SHAPE_NAMES = ["Circle", "Rect", "Polygon", "Capsule"]

SHAPE_DEFS: dict[str, object] = {
    "Circle": CircleShape(radius=30),
    "Rect": RectangleShape(width=60, height=60),
    "Polygon": CollisionPolygon(vertices=[(-30, -30), (30, -30), (0, 30)]),
    "Capsule": CapsuleShape(radius=20, height=40),
}

COLOR_BG = (25, 25, 35)
COLOR_IDLE_A = (70, 130, 220)
COLOR_IDLE_B = (220, 160, 60)
COLOR_COLLIDE = (60, 220, 100)
COLOR_NORMAL = (255, 60, 60)
COLOR_WHITE = (220, 220, 220)
COLOR_DIM = (140, 140, 160)


class CollidableObject:
    """Minimal object satisfying ICollidableObject protocol."""

    def __init__(self, x: float, y: float, shape_name: str) -> None:
        self.x = x
        self.y = y
        self.shape_name = shape_name
        self.collision_shape = SHAPE_DEFS[shape_name]
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
    length = hit.depth * 3 + 40
    ex = mx + hit.normal[0] * length
    ey = my + hit.normal[1] * length
    pygame.draw.line(screen, COLOR_NORMAL, (mx, my), (ex, ey), 3)
    angle = math.atan2(hit.normal[1], hit.normal[0])
    for sign in (-1, 1):
        px = ex - 10 * math.cos(angle + sign * 0.45)
        py = ey - 10 * math.sin(angle + sign * 0.45)
        pygame.draw.line(screen, COLOR_NORMAL, (ex, ey), (px, py), 3)


# ── Info overlay ────────────────────────────────────────────────────


def draw_info(screen, font, hit, a_name, b_name):
    lines = [f"Pair:  {a_name} vs {b_name}"]
    if hit is None:
        lines.append("State:  separated")
    else:
        lines.append("State:  COLLIDING")
        lines.append(f"Depth:  {hit.depth:.3f} px")
        lines.append(f"Normal: ({hit.normal[0]:.3f}, {hit.normal[1]:.3f})")
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, COLOR_WHITE), (12, 10 + i * 22))


def draw_controls(screen, font):
    x = 14
    y = SCREEN_H - 28
    items = [
        ("Arrows", "move active"),
        ("1-4", "active shape"),
        ("Q/R/T/Y", "target shape"),
    ]
    for label, desc in items:
        lbl = font.render(label, True, (255, 200, 100))
        dsc = font.render(f"  {desc}", True, COLOR_DIM)
        screen.blit(lbl, (x, y))
        screen.blit(dsc, (x + lbl.get_width(), y))
        x += lbl.get_width() + dsc.get_width() + 30


# ── Main ────────────────────────────────────────────────────────────


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Object Collision Visual Demo")
    font = pygame.font.SysFont("monospace", 15)
    clock = pygame.time.Clock()

    active = CollidableObject(300, 350, "Rect")
    target = CollidableObject(650, 350, "Circle")

    # active_idx maps: 0=Circle, 1=Rect, 2=Polygon, 3=Capsule
    # target_idx maps: 0=Circle, 1=Rect, 2=Polygon, 3=Capsule
    active_idx, target_idx = 1, 0

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # Active shapes: 1-4
                if pygame.K_1 <= event.key <= pygame.K_4:
                    active_idx = event.key - pygame.K_1
                # Target shapes: Q/R/T/Y
                elif event.key == pygame.K_q:
                    target_idx = 0
                elif event.key == pygame.K_r:
                    target_idx = 1
                elif event.key == pygame.K_t:
                    target_idx = 2
                elif event.key == pygame.K_y:
                    target_idx = 3

        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        active.x += dx * MOVE_SPEED
        active.y += dy * MOVE_SPEED

        # Clamp
        active.x = max(40, min(SCREEN_W - 40, active.x))
        active.y = max(60, min(SCREEN_H - 60, active.y))

        # Apply shape changes
        for obj, idx in ((active, active_idx), (target, target_idx)):
            name = SHAPE_NAMES[idx]
            if obj.shape_name != name:
                obj.shape_name = name
                obj.collision_shape = SHAPE_DEFS[name]

        # ── Single collision check (only this pair) ──
        hit = check_collision(active, target)

        # ── Render ──
        screen.fill(COLOR_BG)

        # Draw grid hint
        for gx in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, (35, 35, 48), (gx, 0), (gx, SCREEN_H), 1)
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.line(screen, (35, 35, 48), (0, gy), (SCREEN_W, gy), 1)

        # Target (drawn first so active appears on top)
        tc = COLOR_COLLIDE if hit else COLOR_IDLE_B
        draw_filled(screen, target.collision_shape, target.x, target.y, tc)
        draw_outline(screen, target.collision_shape, target.x, target.y, COLOR_WHITE)

        # Active
        ac = COLOR_COLLIDE if hit else COLOR_IDLE_A
        draw_filled(screen, active.collision_shape, active.x, active.y, ac)
        draw_outline(screen, active.collision_shape, active.x, active.y, COLOR_WHITE)

        if hit is not None:
            draw_normal_arrow(screen, hit, active, target)

        draw_info(screen, font, hit, SHAPE_NAMES[active_idx], SHAPE_NAMES[target_idx])
        draw_controls(screen, font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
