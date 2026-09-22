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


class TestHiddenImageLayers:
    def _map_with_hidden_bg(self, data_dir, bg_image_path):
        payload = {
            "meta": {**MINIMAL_MAP_META},
            "resources": {"tilesets": []},
            "project_state": {"rules": [], "groups": []},
            "data": {
                "layers": [
                    {
                        "name": "HiddenBG",
                        "type": "image",
                        "visible": False,
                        "locked": False,
                        "opacity": 1.0,
                        "z_index": -1,
                        "tiles": {},
                        "image_path": bg_image_path,
                        "image_rect": {"x": 0, "y": 0, "w": 64, "h": 64},
                    },
                ]
            },
        }
        mp = data_dir / "test_hidden.json"
        with open(mp, "w") as f:
            json.dump(payload, f, indent=2)
        return mp

    def test_hidden_bg_skipped_eager(self, tmp_project):
        _, data_dir, _ = tmp_project
        _make_minimal_png(data_dir / "bg.png", (64, 64))
        data = TilemapData.load(self._map_with_hidden_bg(data_dir, "bg.png"))
        assert data.background_layer is None

    def test_image_surfaces_skip_hidden_by_default(self, tmp_project):
        _, data_dir, _ = tmp_project
        _make_minimal_png(data_dir / "bg.png", (64, 64))
        data = TilemapData.load(self._map_with_hidden_bg(data_dir, "bg.png"))
        assert data.get_image_layer_surfaces() == []
        assert len(data.get_image_layer_surfaces(include_hidden=True)) == 1

    def test_single_image_surface_hidden_opt_in(self, tmp_project):
        _, data_dir, _ = tmp_project
        _make_minimal_png(data_dir / "bg.png", (64, 64))
        data = TilemapData.load(self._map_with_hidden_bg(data_dir, "bg.png"))
        assert data.get_image_layer_surface("HiddenBG") is None
        assert data.get_image_layer_surface("HiddenBG", include_hidden=True) is not None


def _bg_layer_dict(**over):
    d = {
        "name": "Background",
        "type": "image",
        "visible": True,
        "locked": False,
        "opacity": 1.0,
        "z_index": -1,
        "tiles": {},
        "image_path": "bg.png",
        "image_rect": {"x": 0, "y": 0, "w": 64, "h": 64},
    }
    d.update(over)
    return d


def _parse_layers(layers):
    payload = {
        "meta": {"tile_size": "16;16", "map_size": "5;5", "version": "1.1"},
        "resources": {"tilesets": []},
        "project_state": {"rules": [], "groups": []},
        "data": {"layers": layers},
    }
    return parse_map_dict(payload).layers


class TestImagePlacementsParsing:
    def test_absent_means_empty_and_no_counter(self):
        (layer,) = _parse_layers([_bg_layer_dict()])
        assert layer.image_placements == []
        assert layer.next_placement_id is None

    def test_valid_placements_and_counter_bump(self):
        (layer,) = _parse_layers([_bg_layer_dict(
            image_placements=[
                {"pid": 1, "x": 0, "y": 0, "w": 64, "h": 64},
                {"pid": 5, "x": 64, "y": 0, "w": 64, "h": 64, "mode": "repeat"},
            ],
            next_placement_id=6,
        )])
        assert [(p.pid, p.mode) for p in layer.image_placements] == [(1, "stretch"), (5, "repeat")]
        assert layer.next_placement_id == 6

    def test_counter_derived_when_missing_and_bad_entries_dropped(self):
        (layer,) = _parse_layers([_bg_layer_dict(
            image_placements=[
                {"pid": 4, "x": 0, "y": 0, "w": 8, "h": 8},
                {"pid": "x", "x": 0, "y": 0, "w": 8, "h": 8},
                {"x": 0, "y": 0, "w": 8, "h": 8},
                {"pid": 2, "x": 0, "y": 0, "w": 8, "h": 8, "mode": "weird"},
            ],
        )])
        assert [p.pid for p in layer.image_placements] == [4, 2]
        assert layer.image_placements[1].mode == "stretch"
        assert layer.next_placement_id == 5

    def test_garbage_counter_falls_back(self):
        (layer,) = _parse_layers([_bg_layer_dict(next_placement_id="nope")])
        assert layer.image_placements == []
        assert layer.next_placement_id == 1


class TestPlacedImageLayerSurface:
    def _map(self, tmp_project, layers):
        _, data_dir, assets_dir = tmp_project
        _make_minimal_png(data_dir / "bg.png", size=(16, 16))
        payload = {
            "meta": {**MINIMAL_MAP_META},
            "resources": {"tilesets": []},
            "project_state": {"rules": [], "groups": []},
            "data": {"layers": layers},
        }
        mp = data_dir / "m.json"
        mp.write_text(json.dumps(payload))
        return TilemapData.load(mp)

    def test_legacy_single_rect_composes(self, tmp_project):
        data = self._map(tmp_project, [_bg_layer_dict(
            image_path="bg.png", image_rect={"x": 0, "y": 0, "w": 16, "h": 16})])
        surf = data.get_placed_image_layer_surface("Background")
        assert surf is not None and surf.get_size() == (16, 16)

    def test_union_of_base_and_duplicates(self, tmp_project):
        data = self._map(tmp_project, [_bg_layer_dict(
            image_path="bg.png",
            image_rect={"x": 0, "y": 0, "w": 16, "h": 16},
            image_placements=[{"pid": 1, "x": 16, "y": 0, "w": 16, "h": 16}],
            next_placement_id=2,
        )])
        surf = data.get_placed_image_layer_surface("Background")
        assert surf is not None and surf.get_size() == (32, 16)

    def test_render_scale_and_repeat(self, tmp_project):
        data = self._map(tmp_project, [_bg_layer_dict(
            image_path="bg.png",
            image_rect={"x": 0, "y": 0, "w": 16, "h": 16},
            image_placements=[{"pid": 1, "x": 0, "y": 16, "w": 40, "h": 16, "mode": "repeat"}],
            next_placement_id=2,
        )])
        surf = data.get_placed_image_layer_surface("Background", render_scale=2.0)
        assert surf is not None and surf.get_size() == (80, 64)

    def test_none_cases_and_bad_scale(self, tmp_project):
        data = self._map(tmp_project, [_bg_layer_dict(image_path="bg.png")])
        assert data.get_placed_image_layer_surface("nope") is None
        assert data.get_placed_image_layer_surface("Background", include_hidden=False) is not None
        with pytest.raises(ValueError):
            data.get_placed_image_layer_surface("Background", render_scale=0)
