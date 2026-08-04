"""Full pathfinding — a complete, self-contained example.

One AI entity walks an A* path (NavGrid → Pathfinder → PathFollower)
through a maze.  No external files: the maze is procedural and the
collision data is built in code.

Controls:
  LMB      move the player (the teal square)
  RMB      set the enemy's target — the green path is recomputed
  Space    toggle erosion (walls inflated by the enemy's size)
  W        toggle wall edit mode (LMB places / removes walls)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pygame

from tilemap_parser import RectangleShape
from tilemap_parser.parser.collision import (
    CollisionPolygon,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.movement import CollisionRunner
from tilemap_parser.runtime.navigation import NavGrid, Pathfinder, PathFollower

TILE = 32
COLS, ROWS = 20, 15
SCREEN_W, SCREEN_H = COLS * TILE, ROWS * TILE
SPEED = 200.0
FPS = 60

FULL_TILE = [(0.0, 0.0), (float(TILE), 0.0), (float(TILE), float(TILE)), (0.0, float(TILE))]


def build_maze():
    """A procedural maze: wall segments returned as (tile_map, tileset)."""
    tile_map: dict[tuple[int, int], int] = {}
    for x, y in [
        *[(2, y) for y in range(ROWS) if y < 2 or y > 7],
        *[(6, y) for y in range(ROWS) if y < 4 or y > 10],
        *[(11, y) for y in range(ROWS) if y < 2 or y > 6],
        *[(15, y) for y in range(ROWS) if y < 5 or y > 11],
        *[(x, 3) for x in range(3, 6)],
        *[(x, 8) for x in range(8, 14)],
        *[(x, 12) for x in range(4, 10)],
    ]:
        tile_map[(x, y)] = 0
    tileset = TilesetCollision(
        tileset_name="maze",
        tile_size=(TILE, TILE),
        tiles={0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE)])},
    )
    return tile_map, tileset


class Unit:
    """A moving square with the attributes CollisionRunner.move_rpg needs."""

    def __init__(self, x, y, size):
        self.x, self.y = float(x), float(y)
        self.w = self.h = size
        self.collision_shape = RectangleShape(width=size, height=size)

    def draw(self, screen, color):
        pygame.draw.rect(screen, color, (self.x, self.y, self.w, self.h))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 11)

    tile_map, tileset = build_maze()
    runner = CollisionRunner.from_game_type("rpg", (TILE, TILE))
    follower = PathFollower((TILE, TILE))

    erode_margin = 1.0
    eroded = True
    wall_edit = False
    path: list[tuple[int, int]] = []
    waypoint = 0

    player = Unit(1.5 * TILE, 1.5 * TILE, 20)
    enemy = Unit(1.5 * TILE, 5.5 * TILE, 20)

    def base():
        return NavGrid(tile_map, tileset, (TILE, TILE), map_size=(COLS, ROWS))

    grid = base()
    grid_eroded = grid.erode(erode_margin) if eroded else None

    def active_nav():
        return grid_eroded if eroded else grid

    def finder():
        return Pathfinder(active_nav())

    def reroute():
        nonlocal path, waypoint, grid, grid_eroded
        path = []
        waypoint = 0
        grid = base()
        grid_eroded = grid.erode(erode_margin) if eroded else None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    eroded = not eroded
                    reroute()
                elif event.key == pygame.K_w:
                    wall_edit = not wall_edit
            elif event.type == pygame.MOUSEBUTTONDOWN:
                tx, ty = event.pos[0] // TILE, event.pos[1] // TILE
                if not (0 <= tx < COLS and 0 <= ty < ROWS):
                    continue
                nav = active_nav()
                if wall_edit:
                    key = (tx, ty)
                    if key in tile_map:
                        del tile_map[key]
                    else:
                        tile_map[key] = 0
                    reroute()
                elif event.button == 1 and nav.is_walkable(tx, ty):
                    player.x = tx * TILE + TILE / 2
                    player.y = ty * TILE + TILE / 2
                    reroute()
                elif event.button == 3 and nav.is_walkable(tx, ty):
                    sx, sy = int(enemy.x // TILE), int(enemy.y // TILE)
                    path = finder().find_path((sx, sy), (tx, ty)) or []
                    waypoint = 0

        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - keys[pygame.K_UP]
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        runner.move_rpg(player, tileset, tile_map, dx * SPEED * dt, dy * SPEED * dt)

        if path:
            waypoint, done, _, _ = follower.update_rpg(
                enemy, path, waypoint, runner, tileset, tile_map, speed=SPEED, dt=dt
            )
            if done:
                reroute()

        screen.fill((30, 30, 30))
        nav = active_nav()
        for tx in range(COLS):
            for ty in range(ROWS):
                color = (60, 60, 60) if nav.is_solid(tx, ty) else (40, 40, 40)
                pygame.draw.rect(screen, color, (tx * TILE, ty * TILE, TILE, TILE))
                pygame.draw.rect(screen, (50, 50, 50), (tx * TILE, ty * TILE, TILE, TILE), 1)

        if path:
            for wx, wy in path:
                pygame.draw.circle(
                    screen,
                    (0, 200, 0),
                    (wx * TILE + TILE // 2, wy * TILE + TILE // 2),
                    4,
                )

        player.draw(screen, (100, 100, 255))
        enemy.draw(screen, (255, 100, 100))

        lines = [
            f"LMB: move player  |  RMB: enemy target (A*)  |  Space: erosion {'ON' if eroded else 'OFF'}  |  W: {'WALL EDIT' if wall_edit else 'play'}",
            "The enemy walks the green A* path through the eroded grid.",
        ]
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, (200, 200, 200)), (4, 4 + i * 13))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
