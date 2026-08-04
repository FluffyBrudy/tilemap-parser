"""Full physics world — every collision lane wired into one runnable demo.

This is the "how the engine is intended to be assembled" example:

  world.py    builds the PhysicsWorld: tiles, one-way platform, bodies
  player.py   the animated player controller (procedural spritesheet)
  crate.py    kinematic crate pushing through move_grounded
  main.py     the game loop: input, movement, rendering

Controls:  arrows / WASD to move,  Space to jump,  R to reset

Assets are generated at runtime into ``./generated``, so this example
has no external asset dependencies.

What to try:

1. Push a crate right — crates block each other, so a pushed crate
   stops at the next one, the pillar, or the wall.
2. Walk through the hollow pillar: it is on layer 2 and the player's
   collision_mask excludes layer 2, so the player passes while crates
   stop.
3. Jump up through the dashed one-way platform from below, then land
   on top of it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pygame

from tilemap_parser import CollisionRunner

from crate import PUSH_SPEED, body_ahead, push
from player import PLAYER_H, Player
from world import COLS, GRAVITY_GROUND_Y, ROWS, TILE, build_world

SCREEN_W, SCREEN_H = COLS * TILE, ROWS * TILE
FPS = 60
ASSET_DIR = Path(__file__).resolve().parent / "generated"


def draw_tiles(screen, world):
    for (tx, ty), tile_id in world.tile_map.items():
        x, y = tx * TILE, ty * TILE
        pygame.draw.rect(screen, (70, 70, 90), (x, y, TILE, TILE))
        pygame.draw.rect(screen, (55, 55, 75), (x, y, TILE, TILE), 1)
        if world.tileset_collision.tiles[tile_id].shapes[0].one_way:
            # dashed top edge: you can jump up through this platform
            for gx in range(x, x + TILE, 8):
                pygame.draw.line(screen, (240, 220, 120), (gx, y), (gx + 4, y))


def draw_bodies(screen, world):
    for body in world.bodies:
        shape = body.collision_shape
        rect = (
            body.x + shape.offset[0],
            body.y + shape.offset[1],
            shape.width,
            shape.height,
        )
        if body.mode == "kinematic":
            pygame.draw.rect(screen, (230, 150, 60), rect)
            pygame.draw.rect(screen, (40, 40, 40), rect, 2)
        else:
            # layer-2 pillar, drawn hollow: the player walks through it
            x, y, w, h = (int(v) for v in rect)
            for gx in range(x, x + w, 8):
                pygame.draw.line(screen, (150, 150, 180), (gx, y), (gx + 4, y))
                pygame.draw.line(screen, (150, 150, 180), (gx, y + h), (gx + 4, y + h))
            for gy in range(y, y + h, 8):
                pygame.draw.line(screen, (150, 150, 180), (x, gy), (x, gy + 4))
                pygame.draw.line(screen, (150, 150, 180), (x + w, gy), (x + w, gy + 4))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Full physics world")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 11)

    world = build_world()
    runner = CollisionRunner.from_world(world)
    player = Player(96, GRAVITY_GROUND_Y - PLAYER_H, ASSET_DIR)

    def reset():
        nonlocal world, runner, player
        world = build_world()
        runner = CollisionRunner.from_world(world)
        player = Player(96, GRAVITY_GROUND_Y - PLAYER_H, ASSET_DIR)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset()

        keys = pygame.key.get_pressed()
        axis = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )
        jump = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        if axis:
            player.facing = 1 if axis > 0 else -1

        result = runner.move_platformer(
            player, None, None, dt, input_x=float(axis), jump_pressed=jump
        )

        if result.hit_wall_x and axis != 0:
            block = world.collides_with_body(player)
            if block is None:
                block = body_ahead(world, player, axis)
            if block is not None and block.mode == "kinematic":
                block.vx = axis * PUSH_SPEED

        push(runner, world, dt)
        player.update_animation(dt)

        screen.fill((35, 35, 45))
        draw_tiles(screen, world)
        draw_bodies(screen, world)
        player.draw(screen)

        lines = [
            "Arrows/WASD: move  Space: jump  R: reset",
            "Push a crate right: it stops at another crate, the pillar, or the wall.",
            "The hollow pillar is layer 2: you pass, crates stop.",
            "Jump up through the dashed one-way platform, then land on it.",
        ]
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, (200, 200, 200)), (4, 4 + i * 13))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
