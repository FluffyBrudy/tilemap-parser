"""Pushable crates — kinematic bodies moved through a PhysicsWorld.

Controls:  arrows / WASD to move,  Space to jump,  R to reset

The blue player is moved by a platformer runner attached to a
PhysicsWorld.  When the player walks into a kinematic crate, the crate
is pushed with an explicit velocity: ``move_grounded(crate, None, None,
dt, velocity=...)``.

See ``docs/physics-world.md`` for the full object contract (world ↔
move_* ↔ tiles ↔ rendering ↔ sprite-sprite interactions).

What to try:

1. Walk right into the first crate — it slides across the floor until
   it presses against the second crate (crates block each other).
2. Jump over the jammed pair and land between the second and third
   crates, then push the third crate right — it slides until it stops
   at the tile wall.
3. Jump onto a crate and stand on it — bodies are landing surfaces
   through the platformer step-up logic.
"""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pygame

from tilemap_parser import Body, CollisionRunner, PhysicsWorld, RectangleShape
from tilemap_parser.parser.collision import (
    CollisionPolygon,
    TileCollisionData,
    TilesetCollision,
)

TILE = 32
COLS, ROWS = 24, 14
SCREEN_W, SCREEN_H = COLS * TILE, ROWS * TILE
FPS = 60
PLAYER_W, PLAYER_H = 24, 28
PUSH_SPEED = 260.0
GRAVITY_GROUND_Y = 12 * TILE  # top of the ground row (the floor line)

FULL_TILE = [(0.0, 0.0), (float(TILE), 0.0), (float(TILE), float(TILE)), (0.0, float(TILE))]


def build_scene():
    """Ground rows + a wall column.  Returns the world and its crates."""
    tile_map: dict[tuple[int, int], int] = {}
    for x in range(COLS):
        for y in (12, 13):
            tile_map[(x, y)] = 0
    for y in range(8, 12):
        tile_map[(16, y)] = 0
    tileset = TilesetCollision(
        tileset_name="ground",
        tile_size=(TILE, TILE),
        tiles={0: TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=FULL_TILE)])},
    )
    world = PhysicsWorld(tile_map=tile_map, tileset_collision=tileset, tile_size=(TILE, TILE))

    crates = [
        Body(RectangleShape(width=TILE, height=TILE), x=8 * TILE, y=GRAVITY_GROUND_Y - TILE, mode="kinematic"),
        Body(RectangleShape(width=TILE, height=TILE), x=10 * TILE, y=GRAVITY_GROUND_Y - TILE, mode="kinematic"),
        Body(RectangleShape(width=TILE, height=TILE), x=13 * TILE, y=GRAVITY_GROUND_Y - TILE, mode="kinematic"),
    ]
    for crate in crates:
        world.add_body(crate)
    return world, crates


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.collision_shape = RectangleShape(width=PLAYER_W, height=PLAYER_H)


def body_ahead(world, sprite, axis, probe=8.0):
    """Find the body the sprite is pressed against.

    The runner stops a sprite just *short* of a body (sub-pixel skin
    gap), so the static ``collides_with_body`` check at the resting
    position can miss it.  Probe a few pixels into the push direction.
    """
    s = copy.copy(sprite)
    s.x = sprite.x + axis * probe
    return world.collides_with_body(s)


def draw_world(screen, world):
    for (tx, ty), tile_id in world.tile_map.items():
        rect = (tx * TILE, ty * TILE, TILE, TILE)
        pygame.draw.rect(screen, (70, 70, 90), rect)
        pygame.draw.rect(screen, (55, 55, 75), rect, 1)
    for body in world.bodies:
        pygame.draw.rect(
            screen,
            (230, 150, 60) if body.mode == "kinematic" else (140, 140, 160),
            (body.x, body.y, TILE, TILE),
        )
        pygame.draw.rect(screen, (40, 40, 40), (body.x, body.y, TILE, TILE), 2)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Physics crate demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 11)

    world, crates = build_scene()
    runner = CollisionRunner.from_world(world)
    player = Player(96, GRAVITY_GROUND_Y - PLAYER_H)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                world, crates = build_scene()
                runner = CollisionRunner.from_world(world)
                player = Player(96, GRAVITY_GROUND_Y - PLAYER_H)

        keys = pygame.key.get_pressed()
        axis = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        jump = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]

        result = runner.move_platformer(player, None, None, dt, input_x=float(axis), jump_pressed=jump)

        if result.hit_wall_x and axis != 0:
            block = world.collides_with_body(player)
            if block is None:
                block = body_ahead(world, player, axis)
            if block is not None and block.mode == "kinematic":
                block.vx = axis * PUSH_SPEED
        for crate in crates:
            if crate.vx:
                crate_result = runner.move_grounded(crate, None, None, dt, velocity=(crate.vx, 0.0))
                if crate_result.hit_wall_x:
                    crate.vx = 0.0
                else:
                    crate.vx *= 0.9
                    if abs(crate.vx) < 1.0:
                        crate.vx = 0.0

        screen.fill((35, 35, 45))
        draw_world(screen, world)
        pygame.draw.rect(screen, (100, 170, 255), (player.x, player.y, PLAYER_W, PLAYER_H))
        pygame.draw.rect(screen, (30, 30, 40), (player.x, player.y, PLAYER_W, PLAYER_H), 2)

        lines = [
            "Arrows/WASD: move  Space: jump  R: reset",
            "1. Push the first crate — it stops at the second crate.",
            "2. Jump over, then push the third crate into the tile wall.",
            "3. Jump on top of a crate to stand on it.",
        ]
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, (200, 200, 200)), (4, 4 + i * 13))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
