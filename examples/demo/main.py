"""
tilemap-parser demo — single-file showcase of all major features.

Requirements:
    pip install tilemap-parser pygame-ce

Run:
    python main.py

Controls:
    WASD / Arrow keys  — move player
    ESC                — quit

What this demonstrates:
  - Inline map data  → parse_map_dict() → TilemapData
  - Inline collision data → parse_tileset_collision()
  - Tile rendering   → TileLayerRenderer with programmatic spritesheet
  - Tile collision   → CollisionRunner.move_and_slide()
  - Irregular polygon tile shapes (7-vertex rock)
  - Object collision → ObjectCollisionManager with mixed shapes/layers
  - Animation        → AnimationLibrary + SpriteAnimationSet + AnimationPlayer
  - Shape drawing    → pygame.draw for debug visualisation (circle, capsule, rect, polygon)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Union

import pygame

from tilemap_parser import (
    aabb_overlap,
    AnimationClip,
    AnimationFrame,
    AnimationLibrary,
    AnimationPlayer,
    CapsuleShape,
    CircleShape,
    CollisionHit,
    CollisionResult,
    CollisionRunner,
    get_shape_aabb,
    ObjectCollisionManager,
    RectangleShape,
    SpriteAnimationSet,
    TileLayerRenderer,
    TilemapData,
    parse_map_dict,
    parse_tileset_collision,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TILE_W, TILE_H = 32, 32
MAP_W, MAP_H = 20, 15
SCREEN_W, SCREEN_H = 800, 600
PLAYER_SPEED = 160  # px / s


# ---------------------------------------------------------------------------
# Inline data helpers
# ---------------------------------------------------------------------------
def _tile(variant: int) -> dict:
    return {"variant": variant, "ttype": 0}


def build_map_dict() -> dict:
    """20×15 tile map with border walls, interior pillars, and polygon tiles."""
    tiles: dict[str, dict] = {}
    for x in range(MAP_W):
        for y in range(MAP_H):
            key = f"{x}_{y}"
            is_border = x == 0 or x == MAP_W - 1 or y == 0 or y == MAP_H - 1
            pillar_a = x == 5 and 3 <= y <= 5
            pillar_b = x == 14 and 9 <= y <= 11
            # Polygon-shaped tiles (irregular rock / ramp)
            is_poly_rock = (x, y) in ((7, 7), (11, 4), (10, 11))
            is_poly_ramp = (x, y) in ((9, 4), (7, 11))
            if is_border or pillar_a or pillar_b:
                variant = 1
            elif is_poly_rock or is_poly_ramp:
                variant = 2
            else:
                variant = 0
            t = _tile(variant)
            t["pos"] = f"{x};{y}"
            tiles[key] = t

    return {
        "meta": {
            "tile_size": f"{TILE_W};{TILE_H}",
            "map_size": f"{MAP_W};{MAP_H}",
            "version": "1.1",
        },
        "data": {
            "layers": [
                {
                    "name": "Ground",
                    "type": "tile",
                    "visible": True,
                    "z_index": 0,
                    "tiles": tiles,
                }
            ]
        },
        "resources": {"tilesets": [{"path": "demo.png", "type": "tile"}]},
        "project_state": {"rules": [], "groups": []},
    }


TILESET_COLLISION_DATA: dict = {
    "tileset_name": "demo",
    "tile_size": [TILE_W, TILE_H],
    "tiles": {
        "1": {
            "shapes": [
                {
                    "vertices": [
                        [0.0, 0.0],
                        [float(TILE_W), 0.0],
                        [float(TILE_W), float(TILE_H)],
                        [0.0, float(TILE_H)],
                    ]
                }
            ]
        },
        "2": {
            "shapes": [
                {
                    "vertices": [
                        [5.0, 0.0], [27.0, 2.0], [32.0, 12.0],
                        [28.0, 28.0], [18.0, 32.0], [8.0, 30.0], [0.0, 22.0],
                    ]
                }
            ]
        },
    },
}


# ---------------------------------------------------------------------------
# Player  — satisfies both ICollidableSprite and ICollidableObject
# ---------------------------------------------------------------------------
class Player:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.collision_shape = CircleShape(radius=12)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False


# ---------------------------------------------------------------------------
# NPC — supports collision layers and optional horizontal patrol
# ---------------------------------------------------------------------------
class Npc:
    def __init__(
        self,
        x: float,
        y: float,
        shape: Union[RectangleShape, CircleShape, CapsuleShape],
        color: tuple[int, int, int],
        collision_layer: int = 1,
        collision_mask: int = 0xFFFFFFFF,
        patrol_range: float = 0.0,
    ) -> None:
        self.x = x
        self.y = y
        self.collision_shape = shape
        self.collision_layer = collision_layer
        self.collision_mask = collision_mask
        self.color = color
        self._origin_x = x
        self._dir = 1
        self._patrol_range = patrol_range

    def update(self, dt: float) -> None:
        if self._patrol_range > 0:
            self.x += self._dir * 40.0 * dt
            if abs(self.x - self._origin_x) > self._patrol_range:
                self._dir *= -1


# ---------------------------------------------------------------------------
# Programmatic spritesheets (no external files needed)
# ---------------------------------------------------------------------------
def make_tile_sheet() -> pygame.Surface:
    """3-column sheet: col 0 = floor, col 1 = wall, col 2 = polygon rock."""
    surf = pygame.Surface((TILE_W * 3, TILE_H))
    surf.fill((50, 55, 60), rect=(0, 0, TILE_W, TILE_H))
    pygame.draw.rect(surf, (58, 63, 68), (0, 0, TILE_W, TILE_H), 1)
    surf.fill((80, 60, 40), rect=(TILE_W, 0, TILE_W, TILE_H))
    pygame.draw.rect(surf, (100, 75, 50), (TILE_W, 0, TILE_W, TILE_H), 1)
    surf.fill((65, 60, 50), rect=(TILE_W * 2, 0, TILE_W, TILE_H))
    pygame.draw.rect(surf, (85, 75, 60), (TILE_W * 2, 0, TILE_W, TILE_H), 1)
    return surf


def make_anim_sheet() -> pygame.Surface:
    """2-frame spritesheet for the player (blue circle)."""
    surf = pygame.Surface((TILE_W * 2, TILE_H), pygame.SRCALPHA)
    # frame 0
    pygame.draw.circle(surf, (60, 150, 220), (TILE_W // 2, TILE_H // 2), 12)
    pygame.draw.circle(surf, (100, 190, 240), (TILE_W // 2, TILE_H // 2), 10)
    # frame 1
    cx = TILE_W + TILE_W // 2
    pygame.draw.circle(surf, (80, 180, 240), (cx, TILE_H // 2), 13)
    pygame.draw.circle(surf, (120, 220, 255), (cx, TILE_H // 2), 11)
    return surf


# ---------------------------------------------------------------------------
# Debug drawing helpers
# ---------------------------------------------------------------------------
def draw_shape(surf: pygame.Surface, obj: object, cam_x: float, cam_y: float) -> None:
    shape = getattr(obj, "collision_shape", None)
    color = getattr(obj, "color", (200, 200, 200))
    if shape is None:
        return

    if isinstance(shape, CircleShape):
        cx, cy = shape.get_center(getattr(obj, "x"), getattr(obj, "y"))
        pygame.draw.circle(surf, color, (int(cx - cam_x), int(cy - cam_y)), int(shape.radius), 2)

    elif isinstance(shape, CapsuleShape):
        top = shape.get_top_center(getattr(obj, "x"), getattr(obj, "y"))
        bot = shape.get_bottom_center(getattr(obj, "x"), getattr(obj, "y"))
        tx, ty = int(top[0] - cam_x), int(top[1] - cam_y)
        bx, by = int(bot[0] - cam_x), int(bot[1] - cam_y)
        r, h = int(shape.radius), int(shape.height)
        pygame.draw.rect(surf, color, (tx - r, ty, r * 2, h), 2)
        pygame.draw.circle(surf, color, (tx, ty), r, 2)
        pygame.draw.circle(surf, color, (bx, by), r, 2)

    elif isinstance(shape, RectangleShape):
        left, top, _, _ = shape.get_bounds(getattr(obj, "x"), getattr(obj, "y"))
        pygame.draw.rect(
            surf,
            color,
            (int(left - cam_x), int(top - cam_y), int(shape.width), int(shape.height)),
            2,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("tilemap-parser demo")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)

    # 1. Tilemap parsing + rendering -----------------------------------------
    parsed = parse_map_dict(build_map_dict())
    data = TilemapData(parsed, [make_tile_sheet()], [Path("demo.png")], [])
    renderer = TileLayerRenderer(data)
    renderer.warm_cache()

    # 2. Tile collision setup -------------------------------------------------
    ts_collision = parse_tileset_collision(TILESET_COLLISION_DATA)
    runner = CollisionRunner.from_game_type("topdown", data.tile_size)

    tile_map: dict[tuple[int, int], int] = {}
    for layer in data.parsed.layers:
        if layer.layer_type == "tile":
            for pos, tile in layer.tiles.items():
                tile_map[pos] = tile.variant

    # 3. Object collision setup -----------------------------------------------
    mgr = ObjectCollisionManager()

    player = Player(TILE_W * 3.0, TILE_H * 3.0)
    mgr.add_object(player)

    npcs: list[Npc] = [
        Npc(
            TILE_W * 6.0, TILE_H * 4.0,
            CapsuleShape(radius=8, height=16), (255, 180, 80),
            collision_layer=2, patrol_range=60.0,
        ),
        Npc(
            TILE_W * 12.0, TILE_H * 3.0,
            RectangleShape(width=24, height=24), (180, 255, 120),
            collision_layer=3,
        ),
        Npc(
            TILE_W * 8.0, TILE_H * 10.0,
            CircleShape(radius=14), (255, 100, 100),
            collision_layer=2,
        ),
    ]
    for n in npcs:
        mgr.add_object(n)

    # 4. Animation setup ------------------------------------------------------
    anim_lib = AnimationLibrary(
        spritesheet_path=None,
        tile_size=(TILE_W, TILE_H),
        animations={
            "idle": AnimationClip(
                name="idle", loop=True, fps=4,
                frames=[AnimationFrame(0, 250), AnimationFrame(1, 250)],
            ),
        },
    )
    anim_set = SpriteAnimationSet(library=anim_lib, surface=make_anim_sheet(), warnings=[])
    anim_player = AnimationPlayer(anim_set, "idle")

    # 5. Game loop ------------------------------------------------------------
    running = True
    collision_tiles: set[tuple[int, int]] = set()
    hits: list[CollisionHit] = []
    result = CollisionResult()

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        dx = dy = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1.0
        length = (dx * dx + dy * dy) ** 0.5
        if length:
            dx = dx / length * PLAYER_SPEED * dt
            dy = dy / length * PLAYER_SPEED * dt

        # Tile collision
        result = runner.move_and_slide(player, ts_collision, tile_map, dx, dy, slope_slide=True)

        # Expand player AABB by 2px so tiles the player collided with (pushed just
        # outside) still get highlighted.
        margin = 2.0 if result.collided else 0.0
        pa = get_shape_aabb(player.x, player.y, player.collision_shape)
        player_aabb = (pa[0] - margin, pa[1] - margin, pa[2] + margin, pa[3] + margin)
        collision_tiles.clear()
        px, py = int(player.x // TILE_W), int(player.y // TILE_H)
        for ox in range(-1, 2):
            for oy in range(-1, 2):
                tx, ty = px + ox, py + oy
                tid = tile_map.get((tx, ty))
                if tid is not None and ts_collision.has_collision(tid):
                    tile_aabb = (tx * TILE_W, ty * TILE_H, (tx + 1) * TILE_W, (ty + 1) * TILE_H)
                    if aabb_overlap(player_aabb, tile_aabb):
                        collision_tiles.add((tx, ty))

        # NPCs
        for n in npcs:
            n.update(dt)

        # Object-vs-object
        hits = mgr.check_all_collisions()
        for h in hits:
            h.resolve()

        # Animation
        anim_player.update(dt * 1000)

        # Camera
        cam_x = player.x - SCREEN_W // 2
        cam_y = player.y - SCREEN_H // 2

        # Render ---------------------------------------------------------------
        screen.fill((18, 18, 22))

        renderer.render(screen, camera_xy=(cam_x, cam_y))

        for tx, ty in collision_tiles:
            rect = (tx * TILE_W - cam_x, ty * TILE_H - cam_y, TILE_W, TILE_H)
            pygame.draw.rect(screen, (255, 60, 60), rect, 2)
            # Draw polygon shapes inside the tile
            tid = tile_map.get((tx, ty))
            if tid is not None:
                world_shapes = ts_collision.get_world_shapes(tid, tx * TILE_W, ty * TILE_H)
                for poly in world_shapes:
                    pts = [(int(v[0] - cam_x), int(v[1] - cam_y)) for v in poly.vertices]
                    if len(pts) >= 3:
                        pygame.draw.polygon(screen, (255, 200, 60), pts, 1)

        for n in npcs:
            draw_shape(screen, n, cam_x, cam_y)

        draw_shape(screen, player, cam_x, cam_y)

        frame = anim_player.get_current_image()
        if frame is not None:
            screen.blit(frame, (player.x - cam_x - TILE_W // 2, player.y - cam_y - TILE_H // 2))

        for h in hits:
            mx = (h.object_a.x + h.object_b.x) / 2 - cam_x
            my = (h.object_a.y + h.object_b.y) / 2 - cam_y
            pygame.draw.circle(screen, (255, 50, 50), (int(mx), int(my)), 5)

        # HUD ------------------------------------------------------------------
        lines = [
            f"FPS: {clock.get_fps():.0f}",
            f"Player: ({player.x:.0f}, {player.y:.0f})",
            f"Tile collision: {'yes' if result.collided else 'no'}",
            f"Object hits: {len(hits)}",
            f"Polygon tiles nearby: {sum(1 for t in collision_tiles if tile_map.get(t) == 2)}",
        ]
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, (200, 200, 200)), (10, 10 + i * 20))

        screen.blit(
            font.render("WASD/arrows move  |  ESC quit", True, (140, 140, 150)),
            (10, SCREEN_H - 28),
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
