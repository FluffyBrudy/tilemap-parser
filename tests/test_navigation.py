from __future__ import annotations

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from tilemap_parser.parser.collision import (
    CollisionPolygon,
    RectangleShape,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.navigation import NavGrid, Pathfinder, PathFollower
from tilemap_parser.runtime.movement import CollisionRunner

TILE_SIZE = 32
FULL_TILE = [(0.0, 0.0), (32.0, 0.0), (32.0, 32.0), (0.0, 32.0)]

MAP = [
    [1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1],
]

ROWS = len(MAP)
COLS = len(MAP[0])

START_TILE = (1, 2)
GOAL_TILE = (4, 4)


class MockSprite:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.collision_shape = RectangleShape(width=18, height=26, offset=(-9, -13))


def build_tile_map() -> dict:
    tile_map = {}
    for r in range(ROWS):
        for c in range(COLS):
            if MAP[r][c] == 1:
                tile_map[(c, r)] = 0
    return tile_map


def build_tileset() -> TilesetCollision:
    return TilesetCollision(
        tileset_name="test",
        tile_size=(TILE_SIZE, TILE_SIZE),
        tiles={
            0: TileCollisionData(
                tile_id=0,
                shapes=[CollisionPolygon(vertices=FULL_TILE)],
            ),
        },
    )


class TestNavigation:
    def setup_method(self):
        self.tile_map = build_tile_map()
        self.tileset = build_tileset()
        self.runner = CollisionRunner.from_game_type("rpg", (TILE_SIZE, TILE_SIZE))
        self.nav_grid = NavGrid(self.tile_map, self.tileset, (TILE_SIZE, TILE_SIZE))
        self.pathfinder = Pathfinder(self.nav_grid)
        self.follower = PathFollower((TILE_SIZE, TILE_SIZE))

    def test_path_exists_around_wall(self):
        path = self.pathfinder.find_path(START_TILE, GOAL_TILE)
        assert path is not None, "A* should find a path"
        assert path[0] == START_TILE
        assert path[-1] == GOAL_TILE
        assert len(path) >= 3

    def test_no_path_into_solid_wall(self):
        path = self.pathfinder.find_path(START_TILE, (2, 2))
        assert path is None

    def test_no_path_outside_map(self):
        path = self.pathfinder.find_path(START_TILE, (-1, -1))
        assert path is None

    def test_path_avoids_wall_tiles(self):
        path = self.pathfinder.find_path(START_TILE, GOAL_TILE)
        for tx, ty in path[1:-1]:
            assert MAP[ty][tx] == 0, f"path goes through wall at ({tx}, {ty})"

    def test_path_same_start_and_goal(self):
        path = self.pathfinder.find_path((1, 1), (1, 1))
        assert path == [(1, 1)]

    def test_follower_reaches_goal(self):
        path = self.pathfinder.find_path(START_TILE, GOAL_TILE)
        assert path is not None

        cx = START_TILE[0] * TILE_SIZE + TILE_SIZE * 0.5
        cy = START_TILE[1] * TILE_SIZE + TILE_SIZE * 0.5
        sprite = MockSprite(x=cx, y=cy)

        waypoint_idx = 0
        max_steps = 300
        arrived = False

        for _ in range(max_steps):
            waypoint_idx, arrived, _, _ = self.follower.update_rpg(
                sprite, path, waypoint_idx, self.runner,
                self.tileset, self.tile_map, speed=150.0, dt=0.016,
            )
            if arrived:
                break

        assert arrived, (
            f"sprite stuck at ({sprite.x:.1f}, {sprite.y:.1f}) "
            f"waypoint {waypoint_idx}/{len(path)}"
        )

        gx = GOAL_TILE[0] * TILE_SIZE + TILE_SIZE * 0.5
        gy = GOAL_TILE[1] * TILE_SIZE + TILE_SIZE * 0.5
        dx = gx - sprite.x
        dy = gy - sprite.y
        assert (dx * dx + dy * dy) ** 0.5 < TILE_SIZE * 0.5, "sprite should be near goal tile"

    def test_follower_stops_at_end_of_path(self):
        path = self.pathfinder.find_path(START_TILE, GOAL_TILE)
        assert path is not None

        cx = START_TILE[0] * TILE_SIZE + TILE_SIZE * 0.5
        cy = START_TILE[1] * TILE_SIZE + TILE_SIZE * 0.5
        sprite = MockSprite(x=cx, y=cy)

        _, arrived, _, _ = self.follower.update_rpg(
            sprite, [], 0, self.runner,
            self.tileset, self.tile_map,
        )
        assert arrived is True

        _, arrived, _, _ = self.follower.update_rpg(
            sprite, path, len(path), self.runner,
            self.tileset, self.tile_map,
        )
        assert arrived is True

    def test_nav_grid_walkable_tiles(self):
        assert self.nav_grid.is_walkable(1, 1) is True
        assert self.nav_grid.is_walkable(0, 0) is False
        assert self.nav_grid.is_walkable(2, 2) is False
        assert self.nav_grid.is_walkable(4, 4) is True

    def test_nav_grid_solid(self):
        assert self.nav_grid.is_solid(0, 0) is True
        assert self.nav_grid.is_solid(1, 1) is False

    def test_out_of_bounds_not_walkable(self):
        assert self.nav_grid.is_walkable(-1, 0) is False
        assert self.nav_grid.is_walkable(100, 100) is False

    def test_out_of_bounds_solid(self):
        assert self.nav_grid.is_solid(-1, 0) is True
        assert self.nav_grid.is_solid(100, 100) is True

    def test_get_neighbors_no_diagonals(self):
        neighbors = self.nav_grid.get_neighbors(3, 3)
        expected = {(3, 2), (3, 4), (2, 3), (4, 3)}
        assert set(neighbors) == expected

    def test_get_neighbors_with_diagonals(self):
        neighbors = self.nav_grid.get_neighbors(3, 3, diagonals=True)
        for nx, ny in neighbors:
            assert self.nav_grid.is_walkable(nx, ny), f"({nx}, {ny}) not walkable"
        assert (2, 2) not in neighbors
        assert (3, 2) in neighbors
        assert (4, 3) in neighbors

    def test_neighbor_near_wall_excludes_wall(self):
        neighbors = self.nav_grid.get_neighbors(2, 1)
        for nx, ny in neighbors:
            assert self.nav_grid.is_walkable(nx, ny), f"neighbor ({nx}, {ny}) is wall"


class TestNavGridErosion:
    def setup_method(self):
        self.tile_map = build_tile_map()
        self.tileset = build_tileset()
        self.base = NavGrid(self.tile_map, self.tileset, (TILE_SIZE, TILE_SIZE))

    def test_erosion_blocks_adjacent(self):
        eroded = self.base.erode(1.0)
        assert eroded.is_solid(0, 0) is True
        assert eroded.is_solid(1, 1) is True
        assert eroded.is_solid(1, 2) is True
        assert eroded.is_solid(2, 1) is True

    def test_erosion_does_not_affect_base(self):
        self.base.erode(1.0)
        assert self.base.is_walkable(1, 1) is True

    def test_erosion_margin_half(self):
        eroded = self.base.erode(0.5)
        assert eroded.is_walkable(1, 1) is False
        assert eroded.is_walkable(3, 3) is True

    def test_copy_is_independent(self):
        copy = self.base.copy()
        assert copy.is_walkable(1, 1) is True
        eroded = copy.erode(1.0)
        assert copy.is_walkable(1, 1) is True
        assert eroded.is_walkable(1, 1) is False

    def test_for_entity_small_vs_large(self):
        small = NavGrid.for_entity(
            self.tile_map, self.tileset, (TILE_SIZE, TILE_SIZE), sprite_width=16
        )
        large = NavGrid.for_entity(
            self.tile_map, self.tileset, (TILE_SIZE, TILE_SIZE), sprite_width=64
        )
        assert small.is_walkable(3, 3) is True
        assert large.is_walkable(3, 3) is False

    def test_for_entity_caching(self):
        cache: dict = {}
        a = NavGrid.for_entity(
            self.tile_map, self.tileset, (TILE_SIZE, TILE_SIZE),
            sprite_width=32, cache=cache,
        )
        b = NavGrid.for_entity(
            self.tile_map, self.tileset, (TILE_SIZE, TILE_SIZE),
            sprite_width=32, cache=cache,
        )
        assert a is b

    def test_erosion_blocks_narrow_gap_no_alternate(self):
        w, h = 6, 6
        tight_map: dict[tuple[int, int], int] = {}
        for x in range(w):
            for y in range(h):
                if x == 0 or x == w - 1 or y == 0 or y == h - 1:
                    continue
                if x == 3 and y != 3:
                    tight_map[(x, y)] = 0
        ts = TilesetCollision(
            tileset_name="test",
            tile_size=(TILE_SIZE, TILE_SIZE),
            tiles={
                0: TileCollisionData(
                    tile_id=0,
                    shapes=[CollisionPolygon(vertices=FULL_TILE)],
                ),
            },
        )
        base = NavGrid(tight_map, ts, (TILE_SIZE, TILE_SIZE), map_size=(w, h))
        pf = Pathfinder(base)
        path = pf.find_path((1, 1), (4, 4))
        assert path is not None
        assert (3, 3) in path

        eroded = base.erode(1.0)
        pf_eroded = Pathfinder(eroded)
        path_eroded = pf_eroded.find_path((1, 1), (4, 4))
        assert path_eroded is None


class TestPathfinderClosedSet:
    def setup_method(self):
        self.tile_map = build_tile_map()
        self.tileset = build_tileset()
        self.nav_grid = NavGrid(self.tile_map, self.tileset, (TILE_SIZE, TILE_SIZE))
        self.pathfinder = Pathfinder(self.nav_grid)

    def test_path_found_with_closed_set(self):
        path = self.pathfinder.find_path(START_TILE, GOAL_TILE)
        assert path is not None
        assert path[0] == START_TILE
        assert path[-1] == GOAL_TILE

    def test_no_path_with_closed_set(self):
        path = self.pathfinder.find_path(START_TILE, (2, 2))
        assert path is None


class TestPathFollowerStalling:
    def setup_method(self):
        self.tile_map = build_tile_map()
        self.tileset = build_tileset()
        self.runner = CollisionRunner.from_game_type("rpg", (TILE_SIZE, TILE_SIZE))
        self.follower = PathFollower((TILE_SIZE, TILE_SIZE))

    def test_update_rpg_returns_stall_info(self):
        path = [(2, 2)]
        sprite = MockSprite(x=5 * TILE_SIZE, y=5 * TILE_SIZE)
        idx, done, hwx, hwy = self.follower.update_rpg(
            sprite, path, 0, self.runner,
            self.tileset, self.tile_map, speed=150.0, dt=0.016,
        )
        assert isinstance(hwx, bool)
        assert isinstance(hwy, bool)

    def test_update_rpg_arrived_has_no_stall(self):
        path = [(2, 2)]
        sprite = MockSprite(
            x=2 * TILE_SIZE + TILE_SIZE * 0.5,
            y=2 * TILE_SIZE + TILE_SIZE * 0.5,
        )
        _, done, hwx, hwy = self.follower.update_rpg(
            sprite, path, 0, self.runner,
            self.tileset, self.tile_map, speed=150.0, dt=0.016,
        )
        assert done is True
        assert hwx is False
        assert hwy is False
