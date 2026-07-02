"""
Character shapes (rect / circle / capsule) vs a static polygon.

A character with 3 possible collision shapes moves against a pentagon.
Switch character shape with 1-2-3; arrow keys to move.
Shows how each shape type behaves against angled polygon edges.
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

CHAR_NAMES = ["Rect", "Circle", "Capsule"]

CHAR_DEFS: dict[str, object] = {
    "Rect": RectangleShape(width=36, height=56),
    "Circle": CircleShape(radius=24),
    "Capsule": CapsuleShape(radius=16, height=32),
}

# Regular pentagon pointing upward, radius ~65
_PENTA = [
    (0.0, -65.0),
    (61.8, -20.1),
    (38.2, 52.6),
    (-38.2, 52.6),
    (-61.8, -20.1),
]
POLYGON_WALL = CollisionPolygon(vertices=_PENTA)

COLOR_BG = (25, 25, 35)
COLOR_CHAR_IDLE = (70, 130, 220)
COLOR_WALL_IDLE = (160, 120, 180)
COLOR_COLLIDE = (60, 220, 100)
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


def draw_info(screen, font, hit, char_name):
    lines = [f"Character shape:  {char_name}"]
    lines.append(f"Target shape:     Polygon (pentagon)")
    if hit is None:
        lines.append("State:            separated")
    else:
        lines.append("State:            COLLIDING")
        lines.append(f"Depth:            {hit.depth:.3f} px")
        lines.append(f"Normal:           ({hit.normal[0]:.3f}, {hit.normal[1]:.3f})")
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, COLOR_WHITE), (12, 10 + i * 22))


def draw_controls(screen, font):
    x = 14
    y = SCREEN_H - 28
    items = [
        ("Arrows", "move character"),
        ("1-2-3", "Rect / Circle / Capsule"),
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
    pygame.display.set_caption("Character Shapes vs Polygon")
    font = pygame.font.SysFont("monospace", 15)
    clock = pygame.time.Clock()

    char = CollidableObject(250, 350, CHAR_DEFS["Rect"])
    char.shape_name = "Rect"

    wall = CollidableObject(650, 350, POLYGON_WALL)
    wall.shape_name = "Polygon"

    char_idx = 0  # 0=Rect, 1=Circle, 2=Capsule

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_3:
                    char_idx = event.key - pygame.K_1

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

        # ── Single collision check (character vs polygon) ──
        hit = check_collision(char, wall)

        # ── Render ──
        screen.fill(COLOR_BG)

        # Grid hint
        for gx in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, (35, 35, 48), (gx, 0), (gx, SCREEN_H), 1)
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.line(screen, (35, 35, 48), (0, gy), (SCREEN_W, gy), 1)

        # Wall (behind character)
        wc = COLOR_COLLIDE if hit else COLOR_WALL_IDLE
        draw_filled(screen, wall.collision_shape, wall.x, wall.y, wc)
        draw_outline(screen, wall.collision_shape, wall.x, wall.y, COLOR_WHITE)

        # Character
        cc = COLOR_COLLIDE if hit else COLOR_CHAR_IDLE
        draw_filled(screen, char.collision_shape, char.x, char.y, cc)
        draw_outline(screen, char.collision_shape, char.x, char.y, COLOR_WHITE)

        if hit is not None:
            draw_normal_arrow(screen, hit, char, wall)

        draw_info(screen, font, hit, CHAR_NAMES[char_idx])
        draw_controls(screen, font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
