"""
Movement: naive (add velocity, no collision) vs parser (check + revert).

Two characters, same arrow-key input, same gravity.
Red (naive): position += velocity — clips through walls and falls through floor.
Green (parser): checks collision per axis — blocked by walls, stands on floor.

Uses check_collision per-axis (like the parser's move_and_slide) so the green
character slides along walls naturally.  All self-contained — no tilemap assets.
"""

import math
import sys

import pygame

from tilemap_parser.parser.collision import (
    CircleShape,
    CollisionPolygon,
    RectangleShape,
)
from tilemap_parser.runtime.object_collision import check_collision

# ── Config ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1000, 700
FPS = 60
MOVE_SPEED = 200
GRAVITY = 800
JUMP_VEL = -420

COLOR_BG = (20, 20, 30)
COLOR_NAIVE = (220, 80, 80)
COLOR_NAIVE_DIM = (100, 50, 50)
COLOR_PARSER = (80, 200, 100)
COLOR_PARSER_DIM = (50, 100, 60)
COLOR_WALL = (120, 100, 160)
COLOR_FLOOR = (100, 120, 140)
COLOR_WHITE = (220, 220, 220)
COLOR_DIM = (140, 140, 160)
COLOR_COLLIDE = (255, 200, 80)


class Char:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.collision_shape = RectangleShape(width=28, height=44)
        self.collision_layer = 1
        self.collision_mask = 0xFFFFFFFF


# ── Scene geometry (floor + wall) ──────────────────────────────────
# Floor: a wide rectangle across the bottom
FLOOR_POLY = CollisionPolygon(vertices=[
    (-500, 0), (500, 0), (500, 40), (-500, 40),
])

# Wall: a block sitting on the floor
WALL_POLY = CollisionPolygon(vertices=[
    (0, -120), (48, -120), (48, 0), (0, 0),
])


class StaticObj:
    def __init__(self, x: float, y: float, shape: object):
        self.x = x
        self.y = y
        self.collision_shape = shape
        self.collision_layer = 1
        self.collision_mask = 0xFFFFFFFF


# ── Drawing helpers ─────────────────────────────────────────────────


def draw_poly(screen, poly, x, y, color):
    verts = [(x + vx, y + vy) for vx, vy in poly.vertices]
    pygame.draw.polygon(screen, color, verts)


def draw_poly_outline(screen, poly, x, y, color, width=2):
    verts = [(x + vx, y + vy) for vx, vy in poly.vertices]
    pygame.draw.polygon(screen, color, verts, width)


def draw_char(screen, obj, color, label):
    s = obj.collision_shape
    ox, oy = (s.offset[0] if hasattr(s, "offset") else 0,
              s.offset[1] if hasattr(s, "offset") else 0)
    rect = pygame.Rect(obj.x + ox, obj.y + oy, s.width, s.height)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, COLOR_WHITE, rect, 2)


# ── Main ────────────────────────────────────────────────────────────


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Movement: Naive vs Parser")
    font = pygame.font.SysFont("monospace", 14)
    clock = pygame.time.Clock()

    naive = Char(150, 100)
    parser = Char(150, 100)

    floor = StaticObj(SCREEN_W // 2, SCREEN_H - 20, FLOOR_POLY)
    wall = StaticObj(500, SCREEN_H - 60, WALL_POLY)
    obstacles = [floor, wall]

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        input_x = (pygame.key.get_pressed()[pygame.K_RIGHT] -
                   pygame.key.get_pressed()[pygame.K_LEFT])
        jump = pygame.key.get_pressed()[pygame.K_SPACE]

        # ── Naive movement (no collision) ──
        naive.vx = input_x * MOVE_SPEED
        naive.vy += GRAVITY * dt
        if jump and naive.on_ground:
            naive.vy = JUMP_VEL
            naive.on_ground = False
        naive.x += naive.vx * dt
        naive.y += naive.vy * dt
        naive.on_ground = False

        # ── Parser movement (per-axis check) ──
        parser.vx = input_x * MOVE_SPEED
        parser.vy += GRAVITY * dt
        if jump and parser.on_ground:
            parser.vy = JUMP_VEL
            parser.on_ground = False
        parser.on_ground = False

        # X-axis
        parser.x += parser.vx * dt
        for obs in obstacles:
            hit = check_collision(parser, obs)
            if hit is not None:
                parser.x -= parser.vx * dt
                parser.vx = 0
                break

        # Y-axis
        parser.y += parser.vy * dt
        for obs in obstacles:
            hit = check_collision(parser, obs)
            if hit is not None:
                parser.y -= parser.vy * dt
                if parser.vy > 0:
                    parser.on_ground = True
                parser.vy = 0
                break

        # ── Render ──
        screen.fill(COLOR_BG)

        # Grid hint
        for gx in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, (30, 30, 42), (gx, 0), (gx, SCREEN_H), 1)
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.line(screen, (30, 30, 42), (0, gy), (SCREEN_W, gy), 1)

        # Scene
        draw_poly(screen, FLOOR_POLY, floor.x, floor.y, COLOR_FLOOR)
        draw_poly_outline(screen, FLOOR_POLY, floor.x, floor.y, COLOR_WHITE)
        draw_poly(screen, WALL_POLY, wall.x, wall.y, COLOR_WALL)
        draw_poly_outline(screen, WALL_POLY, wall.x, wall.y, COLOR_WHITE)

        # Characters
        draw_char(screen, naive, COLOR_NAIVE, "NAIVE")
        draw_char(screen, parser, COLOR_PARSER, "PARSER")

        # State indicators above characters (with dark shadow)
        for obj, color, name in [(naive, COLOR_NAIVE, "NAIVE"),
                                  (parser, COLOR_PARSER, "PARSER")]:
            label = font.render(name, True, color)
            shadow = font.render(name, True, (0, 0, 0))
            lx = obj.x - label.get_width() // 2
            ly = obj.y - 56
            for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                screen.blit(shadow, (lx + dx, ly + dy))
            screen.blit(label, (lx, ly))

        # Info panel (dark background)
        lines = [
            ("Movement Comparison", (230, 230, 230)),
            ("", (230, 230, 230)),
            (f"Naive:  x={naive.x:.0f}  y={naive.y:.0f}  vx={naive.vx:.0f}  vy={naive.vy:.0f}", (255, 160, 160)),
            (f"Parser: x={parser.x:.0f}  y={parser.y:.0f}  vx={parser.vx:.0f}  vy={parser.vy:.0f}", (160, 255, 160)),
        ]
        pw, ph = 350, len(lines) * 20 + 10
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 160))
        screen.blit(panel, (8, 6))
        y = 14
        for text, color in lines:
            screen.blit(font.render(text, True, color), (14, y))
            y += 20

        # Controls
        cw, ch = 610, 22
        cpanel = pygame.Surface((cw, ch), pygame.SRCALPHA)
        cpanel.fill((0, 0, 0, 150))
        screen.blit(cpanel, (8, SCREEN_H - 26))
        ctrl = font.render(
            "Arrows move  |  SPACE jump  |  Red walks through walls — Green respects collision",
            True, (200, 200, 210),
        )
        screen.blit(ctrl, (14, SCREEN_H - 24))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
