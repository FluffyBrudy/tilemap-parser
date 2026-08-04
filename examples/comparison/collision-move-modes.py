import sys
from typing import Dict, List, Tuple

import pygame

from tilemap_parser.parser.collision import (
    CollisionPolygon,
    RectangleShape,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.movement import CollisionRunner

SCREEN_W, SCREEN_H = 900, 700
FPS = 60
TS = 32

COLOR_BG = (20, 20, 30)
COLOR_WALL = (70, 50, 50)
COLOR_FLOOR = (50, 60, 70)
COLOR_SLOPE = (60, 70, 90)
COLOR_STEP = (80, 60, 50)

LEVEL_W, LEVEL_H = 14, 14
LEVEL_DATA = [
    "XXXXXXXXXXXXXX",
    "X............X",
    "X../....\\....X",
    "X./......\\...X",
    "X..........S.X",
    "X..........S.X",
    "X....XX....S.X",
    "X..........X.X",
    "X..\\...../...X",
    "X...\\.../....X",
    "X............X",
    "X....SS......X",
    "X............X",
    "XXXXXXXXXXXXXX",
]

SHAPE_MAP = {
    "X": CollisionPolygon(vertices=[(0, 0), (TS, 0), (TS, TS), (0, TS)]),
    "/": CollisionPolygon(vertices=[(0, TS), (TS, 0), (TS, TS)]),
    "\\": CollisionPolygon(vertices=[(0, 0), (TS, TS), (0, TS)]),
    "S": CollisionPolygon(vertices=[(0, TS * 0.5), (TS, TS * 0.5), (TS, TS), (0, TS)]),
}


class Sprite:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.collision_shape = RectangleShape(width=TS - 8, height=TS - 8, offset=(4, 4))


def build_collision_data():
    tiles_by_id: Dict[int, List[CollisionPolygon]] = {}
    tile_map: Dict[Tuple[int, int], int] = {}
    next_id = 0
    for row in range(LEVEL_H):
        for col in range(LEVEL_W):
            ch = LEVEL_DATA[row][col]
            if ch in SHAPE_MAP:
                poly = SHAPE_MAP[ch]
                tid = None
                for existing_id, existing_polys in tiles_by_id.items():
                    if len(existing_polys) == 1 and existing_polys[0].vertices == poly.vertices:
                        tid = existing_id
                        break
                if tid is None:
                    tid = next_id
                    next_id += 1
                    tiles_by_id[tid] = [poly]
                tile_map[(col, row)] = tid
    tiles = {tid: TileCollisionData(tile_id=tid, shapes=shapes) for tid, shapes in tiles_by_id.items()}
    tileset = TilesetCollision(tileset_name="shapes", tile_size=(TS, TS), tiles=tiles)
    return tileset, tile_map


def draw_level(screen, offset_x, offset_y):
    for row in range(LEVEL_H):
        for col in range(LEVEL_W):
            ch = LEVEL_DATA[row][col]
            x = col * TS - offset_x
            y = row * TS - offset_y
            if ch == "X":
                color = COLOR_WALL if row < LEVEL_H - 1 else COLOR_FLOOR
                pygame.draw.rect(screen, color, (x, y, TS, TS))
                pygame.draw.rect(screen, (40, 40, 50), (x, y, TS, TS), 1)
            elif ch == "/":
                pts = [(x, y + TS), (x + TS, y), (x + TS, y + TS)]
                pygame.draw.polygon(screen, COLOR_SLOPE, pts)
                pygame.draw.polygon(screen, (40, 40, 50), pts, 1)
            elif ch == "\\":
                pts = [(x, y), (x + TS, y + TS), (x, y + TS)]
                pygame.draw.polygon(screen, COLOR_SLOPE, pts)
                pygame.draw.polygon(screen, (40, 40, 50), pts, 1)
            elif ch == "S":
                pygame.draw.rect(screen, COLOR_STEP, (x, y + TS * 0.5, TS, TS * 0.5))
                pygame.draw.rect(screen, (40, 40, 50), (x, y + TS * 0.5, TS, TS * 0.5), 1)


MODES: List[Tuple[str, str, Tuple[int, int, int], dict]] = [
    ("SLIDE", "topdown", (255, 140, 140), {}),
    ("PLATFORMER", "platformer", (140, 255, 140), {}),
    ("PLATFORMER+SLIDE", "platformer", (140, 220, 255), {"with_slide": True}),
    ("RPG", "rpg", (255, 200, 140), {}),
]


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Collision: movement mode comparison — TAB to switch")
    font = pygame.font.SysFont("monospace", 14)
    clock = pygame.time.Clock()

    tileset, tile_map = build_collision_data()

    runners = []
    for _, game_type, _, opts in MODES:
        runner = CollisionRunner.from_game_type(game_type, tile_size=(TS, TS))
        if game_type == "topdown":
            runner.slide_friction = 0.15
        runners.append(runner)

    mode_idx = 0
    char = Sprite(TS * 2, TS * 2)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    mode_idx = (mode_idx + 1) % len(MODES)
                    char.x = TS * 2
                    char.y = TS * 2
                    char.vx = 0
                    char.vy = 0
                    char.on_ground = False

        keys = pygame.key.get_pressed()
        name, game_type, color, opts = MODES[mode_idx]
        runner = runners[mode_idx]

        if opts.get("with_slide"):
            input_x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
            jump = keys[pygame.K_UP]
            runner.move_platformer_with_slide(char, tileset, tile_map, dt, input_x, jump)
        elif game_type == "platformer":
            input_x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
            jump = keys[pygame.K_UP]
            runner.move_platformer(char, tileset, tile_map, dt, input_x, jump)
        elif game_type == "topdown":
            dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 250 * dt
            dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 250 * dt
            runner.move_and_slide(char, tileset, tile_map, dx, dy, slope_slide=True)
        else:
            dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 250 * dt
            dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 250 * dt
            runner.move_rpg(char, tileset, tile_map, dx, dy)

        cam_x = max(0, min(char.x - SCREEN_W // 2, LEVEL_W * TS - SCREEN_W))
        cam_y = max(0, min(char.y - SCREEN_H // 2, LEVEL_H * TS - SCREEN_H))

        screen.fill(COLOR_BG)
        draw_level(screen, cam_x, cam_y)

        cx = int(char.x - cam_x)
        cy = int(char.y - cam_y)
        shape = char.collision_shape
        pygame.draw.rect(screen, (255, 255, 255), (cx + 4, cy + 4, shape.width, shape.height), 2)
        inner = pygame.Surface((shape.width, shape.height), pygame.SRCALPHA)
        inner.fill((*color[:3], 100))
        screen.blit(inner, (cx + 4, cy + 4))

        in_air = not char.on_ground if hasattr(char, "on_ground") else False
        status = "AIR" if in_air else "GROUND"
        lines = [
            f"Mode: {name}",
            f"X: {char.x:.0f}  Y: {char.y:.0f}",
            f"State: {status}",
        ]
        pw, ph = 260, len(lines) * 20 + 10
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))
        screen.blit(panel, (8, 8))
        y = 14
        for line in lines:
            c = color if "Mode" in line else (230, 230, 230)
            screen.blit(font.render(line, True, c), (14, y))
            y += 20

        controls_texts = []
        if game_type == "platformer":
            controls_texts = ["Arrows move", "UP jump", "TAB switch mode"]
        elif game_type == "topdown":
            controls_texts = ["Arrows move (any dir)", "TAB switch mode"]
        else:
            controls_texts = ["Arrows move (any dir)", "TAB switch mode"]
        controls_str = "   |   ".join(controls_texts)

        lw, lh = 580, 22
        lpanel = pygame.Surface((lw, lh), pygame.SRCALPHA)
        lpanel.fill((0, 0, 0, 150))
        screen.blit(lpanel, (8, SCREEN_H - 26))
        screen.blit(font.render(controls_str, True, (200, 200, 210)), (14, SCREEN_H - 24))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
