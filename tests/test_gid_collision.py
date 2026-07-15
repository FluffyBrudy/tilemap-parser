"""Tests for GID-based collision resolution (firstgid, merge, build_tile_map)."""

from pathlib import Path

from tilemap_parser.parser.collision import (
    parse_tileset_collision,
    TilesetCollision,
    TileCollisionData,
    CollisionPolygon,
)
from tilemap_parser.parser.map_parse import parse_map_dict
from tilemap_parser.runtime.map_loader import TilemapData


class TestParseTileGid:
    def test_parse_tile_with_gid(self):
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "4;4", "initial_map_size": "4;4",
                     "render_scale": 1, "scroll": "0;0", "version": "1.1"},
            "resources": {"tilesets": [{"path": "ts.png", "type": "tile", "tile_count": 100, "firstgid": 0}]},
            "project_state": {"rules": [], "groups": []},
            "data": {
                "layers": [{
                    "name": "Terrain", "type": "tile", "visible": True, "locked": False,
                    "opacity": 1.0, "z_index": 0, "tiles": {
                        "0;0": {"pos": "0;0", "ttype": 0, "variant": 5, "gid": 105},
                    },
                }],
            },
        }
        parsed = parse_map_dict(payload)
        tile = parsed.layers[0].tiles[(0, 0)]
        assert tile.gid == 105
        assert tile.variant == 5
        assert tile.ttype == 0

    def test_parse_tile_without_gid(self):
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "4;4", "initial_map_size": "4;4",
                     "render_scale": 1, "scroll": "0;0", "version": "1.1"},
            "resources": {"tilesets": [{"path": "ts.png", "type": "tile"}]},
            "project_state": {"rules": [], "groups": []},
            "data": {
                "layers": [{
                    "name": "Terrain", "type": "tile", "visible": True, "locked": False,
                    "opacity": 1.0, "z_index": 0, "tiles": {
                        "0;0": {"pos": "0;0", "ttype": 0, "variant": 5},
                    },
                }],
            },
        }
        parsed = parse_map_dict(payload)
        tile = parsed.layers[0].tiles[(0, 0)]
        assert tile.gid is None
        assert tile.variant == 5


class TestParseTilesetFirstgid:
    def test_parse_tile_count_and_firstgid(self):
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "4;4", "initial_map_size": "4;4",
                     "render_scale": 1, "scroll": "0;0", "version": "1.1"},
            "resources": {"tilesets": [
                {"path": "a.png", "type": "tile", "tile_count": 64, "firstgid": 0},
                {"path": "b.png", "type": "tile", "tile_count": 128, "firstgid": 64},
            ]},
            "project_state": {"rules": [], "groups": []},
            "data": {"layers": [{
                "name": "L", "type": "tile", "visible": True, "locked": False,
                "opacity": 1.0, "z_index": 0, "tiles": {},
            }]},
        }
        parsed = parse_map_dict(payload)
        assert len(parsed.tilesets) == 2
        assert parsed.tilesets[0].tile_count == 64
        assert parsed.tilesets[0].firstgid == 0
        assert parsed.tilesets[1].tile_count == 128
        assert parsed.tilesets[1].firstgid == 64

    def test_missing_firstgid_defaults_zero(self):
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "4;4", "initial_map_size": "4;4",
                     "render_scale": 1, "scroll": "0;0", "version": "1.1"},
            "resources": {"tilesets": [
                {"path": "a.png", "type": "tile"},
            ]},
            "project_state": {"rules": [], "groups": []},
            "data": {"layers": [{
                "name": "L", "type": "tile", "visible": True, "locked": False,
                "opacity": 1.0, "z_index": 0, "tiles": {},
            }]},
        }
        parsed = parse_map_dict(payload)
        assert parsed.tilesets[0].tile_count == 0
        assert parsed.tilesets[0].firstgid == 0


class TestParseTilesetCollisionNoFirstgid:
    def test_collision_file_firstgid_not_present(self):
        data = {
            "tileset_name": "test",
            "tile_size": [32, 32],
            "tiles": {
                "5": {"tile_id": 5, "shapes": [
                    {"vertices": [[0, 0], [32, 0], [32, 32], [0, 32]], "one_way": False},
                ]},
            },
        }
        result = parse_tileset_collision(data)
        assert not hasattr(result, "firstgid")
        assert 5 in result.tiles

    def test_collision_file_extra_firstgid_ignored(self):
        data = {
            "tileset_name": "test",
            "tile_size": [32, 32],
            "firstgid": 100,
            "tiles": {},
        }
        result = parse_tileset_collision(data)
        assert not hasattr(result, "firstgid")

    def test_empty_tiles(self):
        data = {
            "tileset_name": "test",
            "tile_size": [32, 32],
            "tiles": {},
        }
        result = parse_tileset_collision(data)
        assert not hasattr(result, "firstgid")


class TestTilesetCollisionMerge:
    def test_merge_offsets_keys_by_firstgid(self):
        ts0 = TilesetCollision(
            tileset_name="grass", tile_size=(16, 16),
            tiles={5: TileCollisionData(tile_id=5), 10: TileCollisionData(tile_id=10)},
        )
        ts1 = TilesetCollision(
            tileset_name="water", tile_size=(16, 16),
            tiles={0: TileCollisionData(tile_id=0), 5: TileCollisionData(tile_id=5)},
        )
        merged = TilesetCollision.merge([ts0, ts1], [0, 200])
        assert merged.tileset_name == "merged"
        assert merged.tile_size == (16, 16)
        assert 5 in merged.tiles
        assert 10 in merged.tiles
        assert 200 in merged.tiles
        assert 205 in merged.tiles
        assert len(merged.tiles) == 4

    def test_merge_empty(self):
        merged = TilesetCollision.merge([], [])
        assert merged.tileset_name == "merged"
        assert merged.tiles == {}

    def test_merge_single_identity(self):
        ts = TilesetCollision(
            tileset_name="single", tile_size=(16, 16),
            tiles={3: TileCollisionData(tile_id=3)},
        )
        merged = TilesetCollision.merge([ts], [0])
        assert merged.tiles == ts.tiles

    def test_merge_same_variant_different_tilesets(self):
        ts0 = TilesetCollision(
            tileset_name="a", tile_size=(16, 16),
            tiles={52: TileCollisionData(tile_id=52, shapes=[
                CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)]),
            ])},
        )
        ts1 = TilesetCollision(
            tileset_name="b", tile_size=(16, 16),
            tiles={52: TileCollisionData(tile_id=52)},
        )
        merged = TilesetCollision.merge([ts0, ts1], [0, 500])
        assert 52 in merged.tiles
        assert 552 in merged.tiles
        assert merged.tiles[52].tile_id == 52
        assert merged.tiles[552].tile_id == 552
        assert len(merged.tiles) == 2


class TestBuildTileMapWithGids:
    def make_payload(self, tilesets, layer_tiles):
        layers = []
        for name, tiles in layer_tiles:
            layers.append({
                "name": name, "type": "tile", "visible": True, "locked": False,
                "opacity": 1.0, "z_index": 0, "tiles": {
                    f"{x};{y}": {"pos": f"{x};{y}", "ttype": ttype, "variant": v}
                    for (x, y, ttype, v) in tiles
                },
            })
        return {
            "meta": {"tile_size": "16;16", "map_size": "10;10", "initial_map_size": "10;10",
                     "render_scale": 1, "scroll": "0;0", "version": "1.1"},
            "resources": {"tilesets": tilesets},
            "project_state": {"rules": [], "groups": []},
            "data": {"layers": layers},
        }

    def test_build_tile_map_with_gids_uses_firstgid(self):
        payload = self.make_payload(
            tilesets=[
                {"path": "a.png", "type": "tile", "tile_count": 100, "firstgid": 0},
                {"path": "b.png", "type": "tile", "tile_count": 200, "firstgid": 100},
            ],
            layer_tiles=[
                ("L1", [(0, 0, 0, 5), (1, 0, 0, 10), (0, 1, 1, 0), (1, 1, 1, 52)]),
            ],
        )
        parsed = parse_map_dict(payload)
        loader = TilemapData(parsed, [None, None], [Path("a.png"), Path("b.png")], [])
        tile_map = loader.build_tile_map(use_gids=True)
        assert tile_map == {
            (0, 0): 5,      # ttype 0, variant 5  → firstgid[0]=0,  gid=0+5=5
            (1, 0): 10,     # ttype 0, variant 10 → firstgid[0]=0,  gid=0+10=10
            (0, 1): 100,    # ttype 1, variant 0  → firstgid[1]=100, gid=100+0=100
            (1, 1): 152,    # ttype 1, variant 52 → firstgid[1]=100, gid=100+52=152
        }

    def test_build_tile_map_no_gids_backward_compat(self):
        payload = self.make_payload(
            tilesets=[{"path": "a.png", "type": "tile", "tile_count": 100, "firstgid": 0}],
            layer_tiles=[("L1", [(0, 0, 0, 5), (1, 0, 0, 10)])],
        )
        parsed = parse_map_dict(payload)
        loader = TilemapData(parsed, [None], [Path("a.png")], [])
        tile_map = loader.build_tile_map(use_gids=False)
        assert tile_map == {(0, 0): 5, (1, 0): 10}

    def test_build_tile_map_falls_back_when_no_firstgid(self):
        payload = self.make_payload(
            tilesets=[{"path": "a.png", "type": "tile"}],
            layer_tiles=[("L1", [(0, 0, 0, 5)])],
        )
        parsed = parse_map_dict(payload)
        loader = TilemapData(parsed, [None], [Path("a.png")], [])
        tile_map = loader.build_tile_map(use_gids=True)
        assert tile_map == {(0, 0): 5}

    def test_build_tile_map_uses_gid_field_when_present(self):
        """When a tile has an explicit gid, it takes priority over firstgid+var."""
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "10;10", "initial_map_size": "10;10",
                     "render_scale": 1, "scroll": "0;0", "version": "1.1"},
            "resources": {"tilesets": [{"path": "a.png", "type": "tile", "tile_count": 100, "firstgid": 0}]},
            "project_state": {"rules": [], "groups": []},
            "data": {"layers": [{
                "name": "L", "type": "tile", "visible": True, "locked": False,
                "opacity": 1.0, "z_index": 0, "tiles": {
                    "0;0": {"pos": "0;0", "ttype": 0, "variant": 5, "gid": 999},
                },
            }]},
        }
        parsed = parse_map_dict(payload)
        loader = TilemapData(parsed, [None], [Path("a.png")], [])
        tile_map = loader.build_tile_map(use_gids=True)
        assert tile_map == {(0, 0): 999}
