"""Full collision — copy-and-fill template.

One file that wires every collision lane into one place: tiles, bodies,
and a player moved by ``CollisionRunner.move_platformer``.

Copy it into your project, fill in the two FILL IN paths, then implement
your movement in the two "implement your movement here" markers.  It
runs as-is against a mini procedural world, so you can watch the wiring
work before you replace anything.

See ``docs/physics-world.md`` for the object contract and
``examples/full-physics-world`` for the full multi-file version.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pygame

from tilemap_parser import (
    Body,
    CollisionRunner,
    PhysicsWorld,
    RectangleShape,
    TilemapData,
    load_tileset_collision,
)
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

# ── FILL IN: paths to your own map and collision data ───────────────
MAP_PATH = Path("your/map.json")
COLLISION_PATH = Path("your/collision.json")
# ─────────────────────────────────────────────────────────────────────

FULL_TILE = [(0.0, 0.0), (float(TILE), 0.0), (float(TILE), float(TILE)), (0.0, float(TILE))]


def build_world():
    """Load your map + collision data and wrap them in a PhysicsWorld.

    Point MAP_PATH and COLLISION_PATH at your tilemap-editor exports and
    this branch is the only code you need.  The fallback below keeps the
    template runnable before you fill anything in.
    """
    if MAP_PATH.is_file() and COLLISION_PATH.is_file():
        tileset = load_tileset_collision(COLLISION_PATH)
        return PhysicsWorld.from_map(TilemapData.load(MAP_PATH), tileset)

    # Fallback mini world: ground + a wall, one static and one kinematic body.
    tile_map = {}
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
    world.add_body(
        Body(RectangleShape(width=TILE, height=TILE), x=8 * TILE, y=11 * TILE, mode="static", game_id="block")
    )
    world.add_body(
        Body(RectangleShape(width=TILE, height=TILE), x=10 * TILE, y=11 * TILE, mode="kinematic", game_id="crate")
    )
    return world


class Player:
    """The sprite the runner moves.

    Keeps the attributes every movement function reads: ``x``, ``y``,
    ``vx``, ``vy``, ``on_ground`` and ``collision_shape``.  Add
    ``collision_layer`` / ``collision_mask`` if you want bodies filtered
    by layer.
    """

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.collision_shape = RectangleShape(width=PLAYER_W, height=PLAYER_H)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    world = build_world()
    runner = CollisionRunner.from_world(world)
    player = Player(PLAYER_W, 12 * TILE - PLAYER_H)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        axis = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )
        jump = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]

        # ── implement your movement here ────────────────────────────────
        # One call, all lanes: tiles AND bodies resolve together, because
        # the runner is attached to the world.
        result = runner.move_platformer(
            player, None, None, dt, input_x=float(axis), jump_pressed=jump
        )

        # Optional push hook, like examples/physics-crate: a kinematic
        # body the player walks into slides away.
        # if result.hit_wall_x and axis:
        #     body = world.collides_with_body(player)
        #     if body is not None and body.mode == "kinematic":
        #         body.vx = axis * 260.0
        # ── implement your movement here ────────────────────────────────

        screen.fill((35, 35, 45))
        for (tx, ty), tile_id in world.tile_map.items():
            x, y = tx * TILE, ty * TILE
            pygame.draw.rect(screen, (70, 70, 90), (x, y, TILE, TILE))
            pygame.draw.rect(screen, (55, 55, 75), (x, y, TILE, TILE), 1)
        for body in world.bodies:
            shape = body.collision_shape
            color = (230, 150, 60) if body.mode == "kinematic" else (140, 140, 160)
            pygame.draw.rect(screen, color, (body.x, body.y, shape.width, shape.height))
        pygame.draw.rect(screen, (100, 170, 255), (player.x, player.y, PLAYER_W, PLAYER_H))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
