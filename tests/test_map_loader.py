import json
import os
import tempfile
from pathlib import Path

import pygame
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.runtime.map_loader import TilemapData, _resolve_resource_path


MINIMAL_MAP_META = {
    "tile_size": "16;16",
    "map_size": "10;10",
    "version": "1.1",
}


def _make_minimal_png(path: Path, size: tuple[int, int] = (16, 16)) -> None:
    surf = pygame.Surface(size)
    surf.fill((255, 0, 255))
    pygame.image.save(surf, str(path))


def _make_map_json(tileset_path: str, data_dir: Path) -> Path:
    payload = {
        "meta": {**MINIMAL_MAP_META},
        "resources": {"tilesets": [{"path": tileset_path, "type": "tile"}]},
        "project_state": {"rules": [], "groups": []},
        "data": {"ongrid": {}},
    }
    map_path = data_dir / "test_map.json"
    with open(map_path, "w") as f:
        json.dump(payload, f, indent=2)
    return map_path


@pytest.fixture(autouse=True)
def pygame_init():
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def tmp_project():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        data_dir = tmp / "data"
        assets_dir = tmp / "assets"
        data_dir.mkdir()
        assets_dir.mkdir()
        yield tmp, data_dir, assets_dir


@pytest.fixture
def map_data(tmp_project):
    tmp, data_dir, assets_dir = tmp_project
    png = assets_dir / "tileset.png"
    _make_minimal_png(png)
    return tmp, data_dir, assets_dir, png


class TestResolveResourcePath:
    def test_relative_goes_up_to_assets(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        result = _resolve_resource_path("../assets/tileset.png", data_dir, None)
        assert result == png.resolve()

    def test_relative_within_data_fails(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        result = _resolve_resource_path("assets/tileset.png", data_dir, None)
        assert not result.is_file()

    def test_extra_search_base_fallback(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        result = _resolve_resource_path("assets/tileset.png", data_dir, extra_search_base=tmp)
        assert result == png.resolve()

    def test_absolute_path(self, tmp_project):
        tmp, data_dir, assets_dir = tmp_project
        png = tmp / "tileset.png"
        _make_minimal_png(png)
        result = _resolve_resource_path(str(png), tmp, None)
        assert result == png
        assert result.resolve() == png.resolve()


class TestTilemapDataLoad:
    def test_load_with_valid_map_relative_path(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        map_path = _make_map_json("../assets/tileset.png", data_dir)

        td = TilemapData.load(map_path)

        assert len(td.resolved_paths) == 1
        assert td.resolved_paths[0] == png.resolve()
        assert td.surfaces[0] is not None
        assert len(td.warnings) == 0

    def test_load_with_invalid_path_generates_warning(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        map_path = _make_map_json("assets/tileset.png", data_dir)

        td = TilemapData.load(map_path)

        assert len(td.warnings) >= 1
        assert "missing" in td.warnings[0].lower()
        assert td.surfaces[0] is None

    def test_load_with_extra_search_base(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        map_path = _make_map_json("assets/tileset.png", data_dir)

        td = TilemapData.load(map_path, extra_search_base=tmp)

        assert td.resolved_paths[0] == png.resolve()
        assert td.surfaces[0] is not None
