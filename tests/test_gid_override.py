import json
import sys
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.parser.collision import (
    CollisionPolygon,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.map_loader import load_map
from tilemap_parser.runtime.world import PhysicsWorld

FULL = [(0.0, 0.0), (8.0, 0.0), (8.0, 8.0), (0.0, 8.0)]


def _solid():
    return TileCollisionData(tile_id=0, shapes=[CollisionPolygon(vertices=list(FULL))])


def _write_map(tmp: Path, stem: str = "tileset_night", tiles=None, second: bool = True):
    (tmp / f"{stem}.png").write_bytes(b"x")
    (tmp / "cave.png").write_bytes(b"x")
    tilesets = [
        {"path": str(tmp / "cave.png"), "type": "tile", "tile_count": 10, "firstgid": 0},
        {"path": str(tmp / f"{stem}.png"), "type": "tile", "tile_count": 100, "firstgid": 90},
    ]
    if not second:
        tilesets = tilesets[1:]
    payload = {
        "meta": {"tile_size": "8;8", "map_size": "4;4", "version": "1.1"},
        "resources": {"tilesets": tilesets},
        "project_state": {"rules": []},
        "data": {
            "layers": [
                {
                    "name": "L",
                    "type": "tile",
                    "visible": True,
                    "tiles": tiles if tiles is not None else {"0;0": {"pos": "0;0", "ttype": 1, "variant": 5}},
                }
            ]
        },
    }
    mp = tmp / "m.json"
    mp.write_text(json.dumps(payload))
    return mp


def _col(name="tileset", local=None):
    tiles = {5: _solid()}
    tiles[5].tile_id = 5
    if local:
        tiles.update(local)
    return TilesetCollision(tileset_name=name, tile_size=(8, 8), tiles=tiles)


def _stem_warnings(rec):
    return [w for w in rec if "no collision owner named" in str(w.message) or "matches no tile tileset" in str(w.message)]


class TestRenamedSkinMiss:
    def test_total_miss_warns(self, tmp_path):
        map_data = load_map(_write_map(tmp_path))
        with pytest.warns(UserWarning, match="no collision owner named"):
            world = PhysicsWorld.from_map(map_data, _col(), use_gids=True)
        assert world._grid_ranges == []
        assert world.has_collision_gid(95) is False

    def test_partial_literal_hit_stays_silent(self, tmp_path):
        map_data = load_map(_write_map(tmp_path))
        col = _col()
        col.tiles[95] = _solid()
        col.tiles[95].tile_id = 95
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            world = PhysicsWorld.from_map(map_data, col, use_gids=True)
        assert _stem_warnings(rec) == []
        assert world.has_collision_gid(95) is True

    def test_empty_map_stays_silent(self, tmp_path):
        map_data = load_map(_write_map(tmp_path, tiles={}))
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            PhysicsWorld.from_map(map_data, _col(), use_gids=True)
        assert _stem_warnings(rec) == []


class TestCollisionTilesetOverride:
    def test_single_tileset_auto_routes_without_override(self, tmp_path):
        map_data = load_map(
            _write_map(tmp_path, second=False, tiles={"0;0": {"pos": "0;0", "ttype": 0, "variant": 5}})
        )
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            world = PhysicsWorld.from_map(map_data, _col(), use_gids=True)
        assert _stem_warnings(rec) == []
        assert world._collision_owner_stem == "tileset_night"
        assert world.has_collision_gid(95) is True

    def test_override_routes_renamed_map(self, tmp_path):
        map_data = load_map(_write_map(tmp_path))
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            world = PhysicsWorld.from_map(map_data, _col(), use_gids=True, collision_tileset="tileset_night")
        assert _stem_warnings(rec) == []
        assert world._collision_owner_stem == "tileset_night"
        assert world.has_collision_gid(95) is True
        assert world.cell_has_collision((0, 0)) is True

    def test_override_typo_warns(self, tmp_path):
        map_data = load_map(_write_map(tmp_path))
        with pytest.warns(UserWarning, match="matches no tile tileset"):
            world = PhysicsWorld.from_map(map_data, _col(), use_gids=True, collision_tileset="nope")
        assert world._grid_ranges == []
