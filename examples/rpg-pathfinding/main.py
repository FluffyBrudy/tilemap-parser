from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import pygame

from tilemap_parser.parser.collision import (
    CollisionPolygon,
    RectangleShape,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.navigation import NavGrid, Pathfinder, PathFollower
from tilemap_parser.runtime.tile_collision import CollisionRunner

TILE_SIZE = 32
FULL_TILE = [(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]

ROWS, COLS = 11, 15
W, H = COLS * TILE_SIZE, ROWS * TILE_SIZE

MAP_GRID = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,1,0,0,0,0,0,0,1],
    [1,0,1,1,0,0,0,1,0,0,0,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,0,0,1,1,1,0,0,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,0,1,0,0,0,1,0,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,1,1,0,0,1,1,1,1,0,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

SPRITE_W, SPRITE_H = 16, 20


class Entity:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.collision_shape = RectangleShape(
            width=SPRITE_W, height=SPRITE_H, offset=(-SPRITE_W // 2, -SPRITE_H // 2),
        )
        self.surface = pygame.Surface((SPRITE_W, SPRITE_H))
        self.surface.fill((50, 120, 220))


def make_tile_map() -> dict:
    return {(c, r): 0 for r in range(ROWS) for c in range(COLS) if MAP_GRID[r][c] == 1}


def make_tileset() -> TilesetCollision:
    return TilesetCollision(
        tileset_name="demo",
        tile_size=(TILE_SIZE, TILE_SIZE),
        tiles={0: TileCollisionData(0, [CollisionPolygon(FULL_TILE)])},
    )


def tile_at(px: int, py: int) -> tuple:
    return (px // TILE_SIZE, py // TILE_SIZE)


def build_nav(grid, tileset):
    return NavGrid(
        {(c, r): 0 for r in range(ROWS) for c in range(COLS) if grid[r][c] == 1},
        tileset, (TILE_SIZE, TILE_SIZE),
    )


def find_path(grid, start, goal):
    tileset = make_tileset()
    nav = build_nav(grid, tileset)
    return Pathfinder(nav).find_path(start, goal)


def main():
    pygame.display.init()
    pygame.font.init()

    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("RPG Pathfinding Demo — LMB:start  RMB:goal  MMB:wall  SPACE:follow  arrows:move")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 12)

    grid = [row[:] for row in MAP_GRID]
    tileset = make_tileset()
    tile_map = make_tile_map()
    runner = CollisionRunner.from_game_type("rpg", (TILE_SIZE, TILE_SIZE))
    follower = PathFollower((TILE_SIZE, TILE_SIZE))

    start = (2, 7)
    goal = (12, 3)
    path = find_path(grid, start, goal)

    entity = Entity(
        start[0] * TILE_SIZE + TILE_SIZE // 2,
        start[1] * TILE_SIZE + TILE_SIZE // 2,
    )

    following = False
    waypoint_idx = 0
    arrived = False
    running = True

    COLOR_WALL = (60, 60, 60)
    COLOR_FLOOR = (200, 200, 200)
    COLOR_PATH = (100, 200, 100)
    COLOR_PATH_LINE = (80, 160, 80)
    COLOR_WP_ACTIVE = (255, 255, 0)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    entity.x = start[0] * TILE_SIZE + TILE_SIZE // 2
                    entity.y = start[1] * TILE_SIZE + TILE_SIZE // 2
                    waypoint_idx = 0
                    arrived = False
                    following = False
                elif event.key == pygame.K_SPACE:
                    if not path:
                        continue
                    following = not following
                    if following:
                        waypoint_idx = 0
                        arrived = False
                        entity.x = start[0] * TILE_SIZE + TILE_SIZE // 2
                        entity.y = start[1] * TILE_SIZE + TILE_SIZE // 2

            elif event.type == pygame.MOUSEBUTTONDOWN:
                tx, ty = tile_at(event.pos[0], event.pos[1])
                if not (0 <= tx < COLS and 0 <= ty < ROWS):
                    continue

                if event.button == 1:
                    start = (tx, ty)
                    entity.x = start[0] * TILE_SIZE + TILE_SIZE // 2
                    entity.y = start[1] * TILE_SIZE + TILE_SIZE // 2
                    waypoint_idx = 0
                    arrived = False
                    following = False
                    path = find_path(grid, start, goal)

                elif event.button == 3:
                    goal = (tx, ty)
                    path = find_path(grid, start, goal)
                    waypoint_idx = 0
                    arrived = False
                    following = False

                elif event.button == 2:
                    grid[ty][tx] = 1 if grid[ty][tx] == 0 else 0
                    tile_map = make_tile_map()
                    if (tx, ty) == start or (tx, ty) == goal:
                        continue
                    path = find_path(grid, start, goal)
                    waypoint_idx = 0
                    arrived = False
                    following = False

        dt = clock.tick(60) / 1000.0

        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        if dx or dy:
            if dx and dy:
                dx = int(dx * 0.7071)
                dy = int(dy * 0.7071)
            runner.move_rpg(entity, tileset, tile_map, dx * 150.0 * dt, dy * 150.0 * dt)
            following = False

        if following and path and not arrived:
            waypoint_idx, arrived = follower.update_rpg(
                entity, path, waypoint_idx, runner, tileset, tile_map,
                speed=150.0, dt=min(dt, 0.033),
            )
            if arrived:
                following = False

        screen.fill((0, 0, 0))
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if grid[r][c] == 1:
                    pygame.draw.rect(screen, COLOR_WALL, rect)
                else:
                    pygame.draw.rect(screen, COLOR_FLOOR, rect)
                pygame.draw.rect(screen, (100, 100, 100), rect, 1)

        if path:
            for i, (px, py) in enumerate(path):
                cx = px * TILE_SIZE + TILE_SIZE // 2
                cy = py * TILE_SIZE + TILE_SIZE // 2
                color = COLOR_WP_ACTIVE if i == waypoint_idx else COLOR_PATH
                pygame.draw.circle(screen, color, (cx, cy), 3)
                if i < len(path) - 1:
                    nx = path[i + 1][0] * TILE_SIZE + TILE_SIZE // 2
                    ny = path[i + 1][1] * TILE_SIZE + TILE_SIZE // 2
                    pygame.draw.line(screen, COLOR_PATH_LINE, (cx, cy), (nx, ny), 2)

        screen.blit(entity.surface, (entity.x - SPRITE_W // 2, entity.y - SPRITE_H // 2))

        sx, sy = start[0] * TILE_SIZE + TILE_SIZE // 2, start[1] * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, (0, 220, 0), (sx, sy), 6)
        screen.blit(font.render("S", True, (0, 0, 0)), (sx - 4, sy - 8))

        gx, gy = goal[0] * TILE_SIZE + TILE_SIZE // 2, goal[1] * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, (220, 40, 40), (gx, gy), 6)
        screen.blit(font.render("G", True, (0, 0, 0)), (gx - 4, gy - 8))

        status = "MANUAL" if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN] else "IDLE" if not following else "FOLLOW"
        if arrived:
            status = "ARRIVED!"

        info = [
            f"[{status}]  WP: {waypoint_idx}/{len(path) - 1 if path else '-'}",
            f"Pos: ({entity.x:.0f}, {entity.y:.0f})  Tile: {tile_at(int(entity.x), int(entity.y))}",
            f"Path: {len(path) if path else 0} tiles",
            f"Start: {start}  Goal: {goal}",
        ]
        for i, line in enumerate(info):
            screen.blit(font.render(line, True, (240, 240, 240)), (4, 4 + i * 14))

        help_lines = [
            "LMB: set start",
            "RMB: set goal",
            "MMB: toggle wall",
            "SPACE: auto-follow",
            "Arrows: manual move",
            "ESC: quit",
        ]
        for i, line in enumerate(help_lines):
            screen.blit(font.render(line, True, (200, 200, 200)), (W - 160, 4 + i * 14))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
