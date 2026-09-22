import json
import sys
import tempfile
from pathlib import Path

import pygame
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.runtime.map_loader import TilemapData, load_map


def _png(path: Path, size=(16, 16)):
    surf = pygame.Surface(size)
    surf.fill((10, 200, 120))
    pygame.image.save(surf, str(path))


@pytest.fixture
def proj():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        data_dir = tmp / "data"
        assets_dir = tmp / "assets"
        data_dir.mkdir()
        assets_dir.mkdir()
        _png(assets_dir / "tileset.png")
        _png(assets_dir / "bg.png", (64, 64))
        yield tmp, data_dir, assets_dir


def _write_map(data_dir: Path, name="test_map.json"):
    payload = {
        "meta": {
            "tile_size": "16;16",
            "map_size": "4;4",
            "initial_map_size": "4;4",
            "render_scale": 2.0,
            "scroll": "0;0",
            "version": "1.1",
        },
        "resources": {"tilesets": [{"path": "../assets/tileset.png", "type": "tile"}]},
        "project_state": {"rules": [], "groups": []},
        "data": {
            "layers": [
                {
                    "name": "Terrain",
                    "type": "tile",
                    "visible": True,
                    "locked": False,
                    "opacity": 1.0,
                    "z_index": 0,
                    "tiles": {
                        "0;0": {"pos": "0;0", "ttype": 0, "variant": 1},
                        "1;0": {"pos": "1;0", "ttype": 0, "variant": 2},
                    },
                },
                {
                    "name": "Objs",
                    "type": "object",
                    "visible": True,
                    "locked": False,
                    "opacity": 1.0,
                    "z_index": 1,
                    "tiles": {},
                    "objects": {
                        "1": {
                            "area": {"x": 32, "y": 0, "w": 16, "h": 16},
                            "ttype": 0,
                            "tileset_type": "object",
                            "variant": 0,
                        }
                    },
                },
                {
                    "name": "Sky",
                    "type": "image",
                    "visible": True,
                    "locked": False,
                    "opacity": 1.0,
                    "z_index": -1,
                    "tiles": {},
                    "image_path": "../assets/bg.png",
                    "image_rect": {"x": 16, "y": 0, "w": 64, "h": 64},
                    "image_placements": [
                        {"pid": 1, "x": 80, "y": 0, "w": 32, "h": 32, "mode": "stretch"},
                    ],
                },
            ]
        },
    }
    mp = data_dir / name
    with open(mp, "w") as f:
        json.dump(payload, f, indent=2)
    with open(data_dir / (mp.stem + ".nodes.json"), "w") as f:
        json.dump(
            {
                "nodes": [
                    {
                        "node_id": "a1",
                        "name": "Zone",
                        "node_type": "area",
                        "area": {"x": 0, "y": 32, "w": 16, "h": 16},
                        "layer_name": "main",
                        "properties": {},
                        "group": "",
                    }
                ],
                "groups": [],
            },
            f,
            indent=2,
        )
    return mp


def test_default_zero(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir)
    td = TilemapData.load(mp)
    assert td.tile_offset == (0, 0)
    assert td.origin_offset == (0, 0)
    assert td.get_tile_at("Terrain", 0, 0).variant == 1
    assert td.map_size == (4, 4)


def test_offset_tiles_shifts_everything(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir)
    td = TilemapData.load(mp, offset_tiles=(2, 1))
    assert td.tile_offset == (2, 1)
    assert td.origin_offset == (64, 32)
    assert td.map_size == (6, 5)
    assert td.get_tile_at("Terrain", 0, 0) is None
    assert td.get_tile_at("Terrain", 2, 1).variant == 1
    assert td.get_tile_at("Terrain", 3, 1).variant == 2
    tm = td.build_tile_map()
    assert (2, 1) in tm and (3, 1) in tm
    assert (0, 0) not in tm
    obj = td.get_layer("Objs").objects[1]
    assert (obj.area.x, obj.area.y) == (64, 16)
    sky = td.get_layer("Sky")
    assert sky.image_rect == (48, 16, 64, 64)
    assert [(p.x, p.y) for p in sky.image_placements] == [(112, 16)]
    assert td.background_layer.image_rect == (48, 16, 64, 64)
    assert td.area_nodes[0].rect.topleft == (64, 96)
    assert td.parsed.meta.scroll == (64, 32)


def test_offset_xy_aliases_and_load_map(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir)
    a = TilemapData.load(mp, offset_x=1, offset_y=2)
    b = load_map(mp, offset_tiles=(1, 2))
    assert a.tile_offset == (1, 2) == b.tile_offset
    assert a.origin_offset == b.origin_offset == (32, 64)
    assert a.get_tile_at("Terrain", 1, 2).variant == 1


def test_offset_rejects_negative(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir)
    with pytest.raises(ValueError):
        TilemapData.load(mp, offset_tiles=(-1, 0))
    with pytest.raises(ValueError):
        load_map(mp, offset_x=-2)
