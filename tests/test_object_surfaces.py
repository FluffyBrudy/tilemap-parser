import json
import tempfile
from pathlib import Path

import pygame
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.runtime.map_loader import TilemapData
from tilemap_parser.parser.map_parse import ParsedObject, ParsedObjectArea


MINIMAL_MAP_META = {
    "tile_size": "16;16",
    "map_size": "10;10",
    "version": "1.1",
}


def _make_minimal_png(path: Path, size: tuple[int, int] = (32, 16)) -> None:
    surf = pygame.Surface(size)
    surf.fill((255, 0, 255))
    pygame.image.save(surf, str(path))


def _make_map_json_with_objects(tileset_path: str, data_dir: Path) -> Path:
    payload = {
        "meta": {**MINIMAL_MAP_META},
        "resources": {"tilesets": [{"path": tileset_path, "type": "tile"}]},
        "project_state": {"rules": [], "groups": []},
        "data": {
            "ongrid": {},
            "layers": [
                {
                    "name": "Object Layer 1",
                    "type": "object",
                    "visible": True,
                    "locked": False,
                    "opacity": 1.0,
                    "z_index": 1,
                    "properties": {},
                    "tiles": {},
                    "objects": {
                        "1": {
                            "area": {"x": 10, "y": 20, "w": 16, "h": 16},
                            "ttype": 0,
                            "tileset_type": "object",
                            "variant": 0,
                            "properties": {},
                        },
                        "2": {
                            "area": {"x": 50, "y": 60, "w": 32, "h": 32},
                            "ttype": 0,
                            "tileset_type": "object",
                            "variant": 1,
                            "properties": {"name": "foo"},
                        },
                    },
                    "next_object_id": 3,
                },
                {
                    "name": "Tile Layer",
                    "type": "tile",
                    "visible": True,
                    "locked": False,
                    "opacity": 1.0,
                    "z_index": 0,
                    "properties": {},
                    "tiles": {},
                    "objects": {},
                },
            ],
        },
    }
    map_path = data_dir / "test_map_objects.json"
    with open(map_path, "w") as f:
        json.dump(payload, f, indent=2)
    return map_path


@pytest.fixture
def map_data():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        data_dir = tmp / "data"
        assets_dir = tmp / "assets"
        data_dir.mkdir()
        assets_dir.mkdir()
        png = assets_dir / "tileset.png"
        _make_minimal_png(png)
        map_path = _make_map_json_with_objects("../assets/tileset.png", data_dir)
        td = TilemapData.load(map_path)
        yield td, data_dir, assets_dir, png


class TestObjectSurfaces:
    def test_get_object_surface_returns_surface(self, map_data):
        td, *_ = map_data
        obj = ParsedObject(
            area=ParsedObjectArea(x=10, y=20, w=16, h=16),
            ttype=0,
            tileset_type="object",
            variant=0,
        )
        surf = td.get_object_surface(obj)
        assert surf is not None
        assert isinstance(surf, pygame.Surface)
        assert surf.get_size() == (16, 16)

    def test_get_object_surface_from_parsed_object(self, map_data):
        td, *_ = map_data
        layer = td.get_layer("Object Layer 1")
        assert layer is not None
        obj = layer.objects.get(1)
        assert obj is not None
        surf = td.get_object_surface(obj)
        assert surf is not None
        assert isinstance(surf, pygame.Surface)

    def test_get_object_surface_by_id_returns_surface_xy(self, map_data):
        td, *_ = map_data
        result = td.get_object_surface_by_id("Object Layer 1", 1)
        assert result is not None
        surf, x, y = result
        assert isinstance(surf, pygame.Surface)
        assert x == 10
        assert y == 20

    def test_get_object_surface_by_id_second_object(self, map_data):
        td, *_ = map_data
        result = td.get_object_surface_by_id("Object Layer 1", 2)
        assert result is not None
        surf, x, y = result
        assert isinstance(surf, pygame.Surface)
        assert surf.get_size() == (16, 16)
        assert x == 50
        assert y == 60

    def test_get_object_surface_by_id_bad_layer_returns_none(self, map_data):
        td, *_ = map_data
        result = td.get_object_surface_by_id("Tile Layer", 1)
        assert result is None

    def test_get_object_surface_by_id_bad_layer_name(self, map_data):
        td, *_ = map_data
        result = td.get_object_surface_by_id("Nonexistent", 1)
        assert result is None

    def test_get_object_surface_by_id_bad_object_id(self, map_data):
        td, *_ = map_data
        result = td.get_object_surface_by_id("Object Layer 1", 999)
        assert result is None

    def test_get_object_surfaces_returns_all(self, map_data):
        td, *_ = map_data
        results = td.get_object_surfaces("Object Layer 1")
        assert len(results) == 2

        surf1, x1, y1, oid1 = results[0]
        assert isinstance(surf1, pygame.Surface)
        assert x1 == 10
        assert y1 == 20
        assert oid1 == 1

        surf2, x2, y2, oid2 = results[1]
        assert isinstance(surf2, pygame.Surface)
        assert x2 == 50
        assert y2 == 60
        assert oid2 == 2

    def test_get_object_surfaces_bad_layer(self, map_data):
        td, *_ = map_data
        results = td.get_object_surfaces("Tile Layer")
        assert results == []

    def test_get_object_surfaces_nonexistent_layer(self, map_data):
        td, *_ = map_data
        results = td.get_object_surfaces("Nonexistent")
        assert results == []

    def test_get_object_surface_with_out_of_range_ttype_returns_none(self, map_data):
        td, *_ = map_data
        obj = ParsedObject(
            area=ParsedObjectArea(x=0, y=0, w=16, h=16),
            ttype=999,
            tileset_type="object",
            variant=0,
        )
        surf = td.get_object_surface(obj)
        assert surf is None
