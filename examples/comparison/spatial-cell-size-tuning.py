import math
import random
import sys
from typing import Dict, List, Set, Tuple

import pygame

from tilemap_parser.parser.collision import CircleShape
from tilemap_parser.runtime.collision import ObjectCollisionManager
from tilemap_parser.utils.geometry import aabb_overlap, get_shape_aabb

SCREEN_W, SCREEN_H = 1200, 700
FPS = 60
N_OBJECTS = 100
SPEED = 120
RADIUS = 10
MARGIN = 60

COLOR_BG = (20, 20, 30)
COLOR_DIVIDER = (60, 60, 80)
COLOR_OBJECT = (100, 180, 220)
COLOR_WHITE = (220, 220, 220)
BOUNDS = (MARGIN, MARGIN, SCREEN_W - MARGIN, SCREEN_H - MARGIN)

CELL_SIZES = [32, 128, 512]
COLORS = [(255, 140, 140), (140, 255, 140), (140, 200, 255)]


class Bouncer:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.collision_shape = CircleShape(radius=RADIUS)
        self.collision_layer = 1
        self.collision_mask = 0xFFFFFFFF


def count_checks(objects, cell_size):
    manager = ObjectCollisionManager(objects, cell_size=cell_size)
    obj_tuple, grid = manager._build_spatial_index()
    checked: Set[Tuple[int, int]] = set()
    for i, obj in enumerate(obj_tuple):
        for j in sorted(manager._candidate_indices(obj, grid)):
            if j <= i:
                continue
            pair = (i, j) if i < j else (j, i)
            if pair not in checked:
                checked.add(pair)
    candidates = 0
    for (i, j) in checked:
        aabb_i = get_shape_aabb(obj_tuple[i].x, obj_tuple[i].y, obj_tuple[i].collision_shape)
        aabb_j = get_shape_aabb(obj_tuple[j].x, obj_tuple[j].y, obj_tuple[j].collision_shape)
        if aabb_overlap(aabb_i, aabb_j):
            candidates += 1
    return len(checked), candidates


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Spatial Grid: Cell Size Tuning")
    font = pygame.font.SysFont("monospace", 13)
    clock = pygame.time.Clock()

    objects = []
    for _ in range(N_OBJECTS):
        x = random.uniform(MARGIN + RADIUS, SCREEN_W - MARGIN - RADIUS)
        y = random.uniform(MARGIN + RADIUS, SCREEN_H - MARGIN - RADIUS)
        angle = random.uniform(0, math.tau)
        s = random.uniform(0.5, 1.5) * SPEED
        objects.append(Bouncer(x, y, math.cos(angle) * s, math.sin(angle) * s))

    total_pairs = N_OBJECTS * (N_OBJECTS - 1) // 2
    panel_w = (SCREEN_W - 6) // 3
    panel_rects = [
        pygame.Rect(0, 0, panel_w, SCREEN_H),
        pygame.Rect(panel_w + 3, 0, panel_w, SCREEN_H),
        pygame.Rect((panel_w + 3) * 2, 0, panel_w, SCREEN_H),
    ]

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        l, t, r, b = BOUNDS
        for o in objects:
            o.x += o.vx * dt
            o.y += o.vy * dt
            if o.x - RADIUS < l:
                o.x = l + RADIUS; o.vx = abs(o.vx)
            elif o.x + RADIUS > r:
                o.x = r - RADIUS; o.vx = -abs(o.vx)
            if o.y - RADIUS < t:
                o.y = t + RADIUS; o.vy = abs(o.vy)
            elif o.y + RADIUS > b:
                o.y = b - RADIUS; o.vy = -abs(o.vy)

        screen.fill(COLOR_BG)
        old_clip = screen.get_clip()

        for idx, cell_size in enumerate(CELL_SIZES):
            checks, candidates = count_checks(objects, cell_size)
            rect = panel_rects[idx]
            screen.set_clip(rect)

            clip_surf = screen.subsurface(rect)
            clip_surf.fill(COLOR_BG)

            for o in objects:
                sx = int(o.x - rect.x)
                sy = int(o.y)
                pygame.draw.circle(clip_surf, COLOR_OBJECT, (sx, sy), RADIUS)

            pygame.draw.rect(clip_surf, (60, 60, 80), (0, 0, rect.w, SCREEN_H), 2)

            lines = [
                f"cell_size = {cell_size}",
                f"Objects: {N_OBJECTS}",
                f"Total pairs: {total_pairs}",
                f"Pairs checked: {checks}",
                f"AABB candidates: {candidates}",
                f"Checks avoided: {(1 - checks / max(total_pairs, 1)) * 100:.0f}%",
            ]
            pw, ph = 260, len(lines) * 18 + 8
            panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 170))
            clip_surf.blit(panel, (4, 4))
            y = 10
            for line in lines:
                c = COLORS[idx] if "checked" in line or "candidates" in line or "avoided" in line else (230, 230, 230)
                clip_surf.blit(font.render(line, True, c), (10, y))
                y += 18

        screen.set_clip(old_clip)
        for i in range(1, 3):
            pygame.draw.line(screen, COLOR_DIVIDER, (panel_w * i + 3 * i, 0), (panel_w * i + 3 * i, SCREEN_H), 3)

        lw, lh = 600, 22
        lpanel = pygame.Surface((lw, lh), pygame.SRCALPHA)
        lpanel.fill((0, 0, 0, 150))
        screen.blit(lpanel, (8, SCREEN_H - 26))
        legend = font.render(
            f"{N_OBJECTS} bouncing circles   |   cell 32 = too many cells   |   cell 512 = too few cells   |   ESC exit",
            True, (200, 200, 210),
        )
        screen.blit(legend, (14, SCREEN_H - 24))
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
