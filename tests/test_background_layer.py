import json
import tempfile
from pathlib import Path

import pygame
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.parser.map_parse import parse_map_dict
from tilemap_parser.runtime.map_loader import TilemapData


MINIMAL_MAP_META = {
    "tile_size": "16;16",
    "map_size": "10;10",
    "version": "1.1",
}


def _make_minimal_png(path: Path, size=(64, 64)):
    surf = pygame.Surface(size)
    surf.fill((123, 45, 67))
    pygame.image.save(surf, str(path))


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
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


def _make_map_with_background(data_dir, bg_image_path, bg_rect, layer_type="image"):
    payload = {
        "meta": {**MINIMAL_MAP_META},
        "resources": {"tilesets": []},
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
                    "tiles": {},
                },
                {
                    "name": "Background",
                    "type": layer_type,
                    "visible": True,
                    "locked": False,
                    "opacity": 1.0,
                    "z_index": -1,
                    "tiles": {},
                    "image_path": bg_image_path,
                    "image_rect": bg_rect,
                },
            ]
        },
    }
    mp = data_dir / "test_map.json"
    with open(mp, "w") as f:
        json.dump(payload, f, indent=2)
    return mp


class TestBackgroundLayerParsing:
    def test_parse_image_layer_dict(self):
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "5;5", "version": "1.1"},
            "resources": {"tilesets": []},
            "project_state": {"rules": [], "groups": []},
            "data": {
                "layers": [
                    {
                        "name": "Background",
                        "type": "image",
                        "visible": True,
                        "locked": False,
                        "opacity": 0.8,
                        "z_index": -1,
                        "tiles": {},
                        "image_path": "bg.png",
                        "image_rect": {"x": 0, "y": 0, "w": 160, "h": 160},
                    }
                ]
            },
        }
        parsed = parse_map_dict(payload)
        layer = parsed.layers[0]
        assert layer.layer_type == "image"
        assert layer.image_path == "bg.png"
        assert layer.image_rect == (0, 0, 160, 160)
        assert layer.opacity == 0.8

    def test_parse_background_layer_alias(self):
        for lt in ("background", "background_layer"):
            payload = {
                "meta": {"tile_size": "16;16", "map_size": "5;5", "version": "1.1"},
                "resources": {"tilesets": []},
                "project_state": {"rules": [], "groups": []},
                "data": {
                    "layers": [
                        {
                            "name": "BG",
                            "type": lt,
                            "visible": True,
                            "locked": False,
                            "opacity": 1.0,
                            "z_index": -1,
                            "tiles": {},
                            "image_path": "bg.png",
                            "image_rect": {"x": 10, "y": 20, "w": 30, "h": 40},
                        }
                    ]
                },
            }
            parsed = parse_map_dict(payload)
            assert parsed.layers[0].image_path == "bg.png"
            assert parsed.layers[0].image_rect == (10, 20, 30, 40)

    def test_no_image_rect(self):
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "5;5", "version": "1.1"},
            "resources": {"tilesets": []},
            "project_state": {"rules": [], "groups": []},
            "data": {
                "layers": [
                    {
                        "name": "BG",
                        "type": "image",
                        "visible": True,
                        "locked": False,
                        "opacity": 1.0,
                        "z_index": 0,
                        "tiles": {},
                        "image_path": "bg.png",
                    }
                ]
            },
        }
        parsed = parse_map_dict(payload)
        assert parsed.layers[0].image_path == "bg.png"
        assert parsed.layers[0].image_rect is None


class TestBackgroundLayerEagerLoad:
    def test_eager_load_background_surface(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        bg_path = "bg.png"
        _make_minimal_png(data_dir / bg_path, (64, 64))
        map_path = _make_map_with_background(
            data_dir, bg_path, {"x": 0, "y": 0, "w": 64, "h": 64}, layer_type="image"
        )
        data = TilemapData.load(map_path)
        assert data.background_layer is not None
        assert data.background_layer.image_path == bg_path
        assert data.background_layer.image_rect == (0, 0, 64, 64)
        assert data.background_layer.surface is not None
        assert data.background_layer.surface.get_size() == (64, 64)

    def test_background_layer_alias_eager(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        bg_path = "bg2.png"
        _make_minimal_png(data_dir / bg_path, (32, 32))
        map_path = _make_map_with_background(
            data_dir, bg_path, {"x": 0, "y": 0, "w": 32, "h": 32}, layer_type="background_layer"
        )
        data = TilemapData.load(map_path)
        assert data.background_layer is not None
        assert data.background_layer.surface is not None

    def test_missing_image_warns(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        map_path = _make_map_with_background(
            data_dir, "missing_bg.png", {"x": 0, "y": 0, "w": 10, "h": 10}
        )
        data = TilemapData.load(map_path)
        assert data.background_layer is not None
        assert data.background_layer.surface is None
        assert any("not found" in w for w in data.warnings)

    def test_no_background_layer(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        payload = {
            "meta": {**MINIMAL_MAP_META},
            "resources": {"tilesets": []},
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
                        "tiles": {},
                    }
                ]
            },
        }
        mp = data_dir / "test_map.json"
        with open(mp, "w") as f:
            json.dump(payload, f, indent=2)
        data = TilemapData.load(mp)
        assert data.background_layer is None
