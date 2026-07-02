"""
Broadphase: naive O(n²) vs spatial hashing.

N bouncing objects (default 100) inside a visible wall boundary.
Left panel checks every (i, j) pair; right panel uses
ObjectCollisionManager's uniform grid.  Shows the candidate-pair
count for each method — the gap widens with N.
"""

import math
import random
import sys

import pygame

from tilemap_parser.parser.collision import CircleShape
from tilemap_parser.runtime.object_collision import ObjectCollisionManager
from tilemap_parser.utils.geometry import aabb_overlap, get_shape_aabb

# ── Config ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1200, 700
FPS = 60
N_OBJECTS = 100
SPEED = 120
RADIUS = 10
MARGIN = 60  # wall boundary inset from screen edge

COLOR_BG = (20, 20, 30)
COLOR_DIVIDER = (60, 60, 80)
COLOR_OBJECT = (100, 180, 220)
COLOR_CANDIDATE_NAIVE = (200, 100, 100)
COLOR_CANDIDATE_SPATIAL = (100, 200, 100)
COLOR_BOUNDARY = (60, 60, 80)
COLOR_WHITE = (220, 220, 220)
COLOR_DIM = (140, 140, 160)

BOUNDS = (MARGIN, MARGIN, SCREEN_W - MARGIN, SCREEN_H - MARGIN)


class Bouncer:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.collision_shape = CircleShape(radius=RADIUS)
        self.collision_layer = 1
        self.collision_mask = 0xFFFFFFFF


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Broadphase: O(n²) vs Spatial Hashing")
    font = pygame.font.SysFont("monospace", 14)
    clock = pygame.time.Clock()

    mid = SCREEN_W // 2

    objects = []
    for _ in range(N_OBJECTS):
        x = random.uniform(MARGIN + RADIUS, SCREEN_W - MARGIN - RADIUS)
        y = random.uniform(MARGIN + RADIUS, SCREEN_H - MARGIN - RADIUS)
        angle = random.uniform(0, math.tau)
        s = random.uniform(0.5, 1.5) * SPEED
        objects.append(Bouncer(x, y, math.cos(angle) * s, math.sin(angle) * s))

    manager = ObjectCollisionManager(objects, cell_size=128.0)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ── Move with wall bounce ──
        l, t, r, b = BOUNDS
        for o in objects:
            o.x += o.vx * dt
            o.y += o.vy * dt
            if o.x - RADIUS < l:
                o.x = l + RADIUS
                o.vx = abs(o.vx)
            elif o.x + RADIUS > r:
                o.x = r - RADIUS
                o.vx = -abs(o.vx)
            if o.y - RADIUS < t:
                o.y = t + RADIUS
                o.vy = abs(o.vy)
            elif o.y + RADIUS > b:
                o.y = b - RADIUS
                o.vy = -abs(o.vy)

        # ── Naive broadphase ──
        naive_candidates = 0
        for i in range(N_OBJECTS):
            aabb_i = get_shape_aabb(objects[i].x, objects[i].y, objects[i].collision_shape)
            for j in range(i + 1, N_OBJECTS):
                aabb_j = get_shape_aabb(objects[j].x, objects[j].y, objects[j].collision_shape)
                if aabb_overlap(aabb_i, aabb_j):
                    naive_candidates += 1

        # ── Spatial broadphase ──
        spatial_candidates = 0
        obj_tuple, grid = manager._build_spatial_index()
        checked_pairs = set()
        for i, obj in enumerate(obj_tuple):
            for j in sorted(manager._candidate_indices(obj, grid)):
                if j <= i:
                    continue
                pair = (i, j) if i < j else (j, i)
                if pair not in checked_pairs:
                    checked_pairs.add(pair)
                    aabb_i = get_shape_aabb(
                        obj_tuple[pair[0]].x, obj_tuple[pair[0]].y,
                        obj_tuple[pair[0]].collision_shape,
                    )
                    aabb_j = get_shape_aabb(
                        obj_tuple[pair[1]].x, obj_tuple[pair[1]].y,
                        obj_tuple[pair[1]].collision_shape,
                    )
                    if aabb_overlap(aabb_i, aabb_j):
                        spatial_candidates += 1

        total_pairs = N_OBJECTS * (N_OBJECTS - 1) // 2

        # ── Render ──
        screen.fill(COLOR_BG)

        # Wall boundary
        pygame.draw.rect(screen, COLOR_BOUNDARY, (l, t, r - l, b - t), 2)

        # Divider
        pygame.draw.line(screen, COLOR_DIVIDER, (mid, 0), (mid, SCREEN_H), 3)

        # Objects
        for o in objects:
            pygame.draw.circle(screen, COLOR_OBJECT, (o.x, o.y), RADIUS)

        # Panel headers (dark panel for readability)
        for px, panel_label, cand_count, color in [
            (10, "Naive O(n²)", naive_candidates, COLOR_CANDIDATE_NAIVE),
            (mid + 10, "Spatial Hashing", spatial_candidates, COLOR_CANDIDATE_SPATIAL),
        ]:
            lines = [
                panel_label,
                f"Objects: {N_OBJECTS}",
                f"Total pairs: {total_pairs}",
                f"AABB candidates: {cand_count}",
                f"Reduction: {((1 - cand_count / max(total_pairs, 1)) * 100):.0f}%",
            ]
            pw, ph = 220, len(lines) * 20 + 10
            panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 160))
            screen.blit(panel, (px, 6))
            y = 14
            for line in lines:
                c = color if "candidates" in line or "Reduction" in line else (230, 230, 230)
                screen.blit(font.render(line, True, c), (px + 6, y))
                y += 20

        # Legend
        lw, lh = 580, 22
        lpanel = pygame.Surface((lw, lh), pygame.SRCALPHA)
        lpanel.fill((0, 0, 0, 150))
        screen.blit(lpanel, (8, SCREEN_H - 26))
        legend = font.render(
            "AABB candidates (green) = pairs that pass broadphase & enter narrowphase   |   ESC exit",
            True, (200, 200, 210),
        )
        screen.blit(legend, (14, SCREEN_H - 24))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
