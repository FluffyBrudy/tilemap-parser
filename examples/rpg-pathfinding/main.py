import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pygame

from tilemap_parser.parser.collision import (
    CollisionPolygon,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.navigation import NavGrid, Pathfinder, PathFollower
from tilemap_parser.runtime.tile_collision import CollisionRunner

TILE_W, TILE_H = 32, 32
COLS, ROWS = 20, 15
SCREEN_W, SCREEN_H = COLS * TILE_W, ROWS * TILE_H
SPEED = 200
FPS = 60

FULL_TILE = [(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]


def build_maze():
    tile_map: dict[tuple[int, int], int] = {}
    walls = [
        [(2, y) for y in range(ROWS) if y < 2 or y > 7],
        [(6, y) for y in range(ROWS) if y < 4 or y > 10],
        [(11, y) for y in range(ROWS) if y < 2 or y > 6],
        [(15, y) for y in range(ROWS) if y < 5 or y > 11],
        [(x, 3) for x in range(3, 6)],
        [(x, 8) for x in range(8, 14)],
        [(x, 12) for x in range(4, 10)],
    ]
    for row in walls:
        for x, y in row:
            tile_map[(x, y)] = 0
    return tile_map, TilesetCollision(
        tileset_name="maze",
        tile_size=(TILE_W, TILE_H),
        tiles={0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE)])},
    )


class DummySprite:
    def __init__(self, x, y, w=20, h=20):
        self.x, self.y = float(x), float(y)
        self.w, self.h = w, h
        self.delta = pygame.Vector2(0, 0)
    @property
    def collision_shape(self):
        class R: offset = (0, 0); width = self.w; height = self.h
        return R()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 11)

    tile_map, tileset = build_maze()
    base = NavGrid(tile_map, tileset, (TILE_W, TILE_H), map_size=(COLS, ROWS))

    player = DummySprite(1 * TILE_W + 16, 1 * TILE_H + 16)
    runner = CollisionRunner.from_game_type("rpg", (TILE_W, TILE_H))
    follower = PathFollower((TILE_W, TILE_H))

    eroded = True
    erode_margin = 1.0
    saved_margin = 1.0
    wall_edit = False

    def sprite_size(margin):
        return max(int(margin * TILE_W * 2), 4)

    active_nav = base.erode(erode_margin)
    pathfinder = Pathfinder(active_nav)
    path: list[tuple[int, int]] = []
    waypoint_idx = 0
    enemy = DummySprite(
        1 * TILE_W + 16, 5 * TILE_H + 16,
        w=sprite_size(erode_margin), h=sprite_size(erode_margin),
    )

    def rebuild_nav():
        nonlocal active_nav, pathfinder, path, waypoint_idx, enemy
        active_nav = base.erode(erode_margin) if eroded else base
        pathfinder = Pathfinder(active_nav)
        path.clear()
        waypoint_idx = 0
        s = sprite_size(erode_margin)
        enemy.w, enemy.h = s, s

    def toggle_wall(tx, ty):
        key = (tx, ty)
        if key in tile_map:
            del tile_map[key]
        else:
            tile_map[key] = 0
        rebuild_nav()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    if eroded:
                        saved_margin = erode_margin
                        erode_margin = 0.0
                    else:
                        erode_margin = saved_margin
                    eroded = not eroded
                    rebuild_nav()
                elif event.key == pygame.K_w:
                    wall_edit = not wall_edit
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS) or event.unicode == '+':
                    if not eroded:
                        eroded = True
                        saved_margin = erode_margin
                    erode_margin = min(4.0, erode_margin + 0.25)
                    rebuild_nav()
                elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS) or event.unicode == '-':
                    if not eroded:
                        eroded = True
                        saved_margin = erode_margin
                    erode_margin = max(0.0, erode_margin - 0.25)
                    rebuild_nav()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                tx, ty = event.pos[0] // TILE_W, event.pos[1] // TILE_H
                if 0 <= tx < COLS and 0 <= ty < ROWS and event.button == 1:
                    if wall_edit:
                        toggle_wall(tx, ty)
                    else:
                        player.x = tx * TILE_W + TILE_W // 2
                        player.y = ty * TILE_H + TILE_H // 2
                        path.clear()
                        waypoint_idx = 0
                elif event.button == 3 and not wall_edit:
                    tx, ty = event.pos[0] // TILE_W, event.pos[1] // TILE_H
                    if 0 <= tx < COLS and 0 <= ty < ROWS and active_nav.is_walkable(tx, ty):
                        ex, ey = int(enemy.x // TILE_W), int(enemy.y // TILE_H)
                        path = pathfinder.find_path((ex, ey), (tx, ty)) or []
                        waypoint_idx = 0

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_DOWN]:  dy += 1
        if dx and dy:
            s = 0.7071
            dx *= s
            dy *= s
        runner.move_rpg(player, tileset, tile_map, dx * SPEED * dt, dy * SPEED * dt)

        if path:
            waypoint_idx, done, _, _ = follower.update_rpg(
                enemy, path, waypoint_idx, runner, tileset, tile_map,
                speed=SPEED, dt=dt,
            )
            if done:
                path.clear()
                waypoint_idx = 0

        screen.fill((30, 30, 30))
        for tx in range(COLS):
            for ty in range(ROWS):
                color = (60, 60, 60) if active_nav.is_solid(tx, ty) else (40, 40, 40)
                pygame.draw.rect(screen, color, (tx * TILE_W, ty * TILE_H, TILE_W, TILE_H))
                pygame.draw.rect(screen, (50, 50, 50), (tx * TILE_W, ty * TILE_H, TILE_W, TILE_H), 1)

        if path:
            for wx, wy in path:
                pygame.draw.circle(screen, (0, 200, 0),
                                   (wx * TILE_W + TILE_W // 2, wy * TILE_H + TILE_H // 2), 4)

        pw, ph = player.w, player.h
        ew, eh = enemy.w, enemy.h
        pygame.draw.rect(screen, (100, 100, 255), (player.x - pw // 2, player.y - ph // 2, pw, ph))
        pygame.draw.rect(screen, (255, 100, 100), (enemy.x - ew // 2, enemy.y - eh // 2, ew, eh))

        lines = [
            f"E: erosion {'ON' if eroded else 'OFF'}  margin={erode_margin:.2f}  (+/- adjust)",
            f"W: {'WALL EDIT' if wall_edit else 'play'} mode  |  LMB: {'toggle wall' if wall_edit else 'move player'}  |  RMB: enemy A* target",
        ]
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, (200, 200, 200)), (4, 4 + i * 13))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
