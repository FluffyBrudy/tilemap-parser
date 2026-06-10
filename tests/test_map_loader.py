import json
import os
import tempfile
from pathlib import Path

import pygame
import pytest
from pygame import Rect

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


MINIMAL_NODES = {
    "nodes": [
        {
            "node_id": "area_1",
            "name": "Spawn Zone",
            "node_type": "area",
            "area": {"x": 64, "y": 128, "w": 96, "h": 48},
            "layer_name": "main",
            "properties": {"tag": "player_spawn"},
            "group": "",
        },
        {
            "node_id": "pe_1",
            "name": "Fire",
            "node_type": "particle_emitter",
            "area": {"x": 200, "y": 300, "w": 32, "h": 32},
            "layer_name": "fx",
            "properties": {
                "emission_shape": "point",
                "particle_shape": "circle",
                "spawn_rate": 10,
                "max_particles": 50,
                "lifetime_min": 1.0,
                "lifetime_max": 3.0,
            },
            "group": "",
        },
    ],
    "groups": [],
}


AREA_ONLY_NODES = {
    "nodes": [
        {
            "node_id": "area_1",
            "name": "Spawn Zone",
            "node_type": "area",
            "area": {"x": 64, "y": 128, "w": 96, "h": 48},
            "layer_name": "main",
            "properties": {"tag": "player_spawn"},
            "group": "",
        },
    ],
    "groups": [],
}


class TestNodeLoading:
    def test_area_nodes_populated(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        map_path = _make_map_json("../assets/tileset.png", data_dir)
        nodes_path = data_dir / "test_map.nodes.json"
        with open(nodes_path, "w") as f:
            json.dump(AREA_ONLY_NODES, f, indent=2)

        td = TilemapData.load(map_path)

        assert len(td.area_nodes) == 1
        an = td.area_nodes[0]
        assert an.node_id == "area_1"
        assert an.name == "Spawn Zone"
        assert an.node_type == "area"
        assert an.rect == Rect(64, 128, 96, 48)
        assert an.layer_name == "main"
        assert an.properties == {"tag": "player_spawn"}
        assert td.particle_emitters == []

    def test_particle_emitters_populated(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        map_path = _make_map_json("../assets/tileset.png", data_dir)
        nodes_path = data_dir / "test_map.nodes.json"
        with open(nodes_path, "w") as f:
            json.dump(MINIMAL_NODES, f, indent=2)

        td = TilemapData.load(map_path)

        assert len(td.particle_emitters) == 1
        pe = td.particle_emitters[0]
        assert pe.node_id == "pe_1"
        assert pe.name == "Fire"
        assert pe.node_type == "particle_emitter"
        assert pe.rect == Rect(200, 300, 32, 32)
        assert pe.layer_name == "fx"
        assert pe.group == ""
        assert pe.config.name == "Fire"
        assert pe.config.emission_shape == "point"
        assert pe.config.particle_shape == "circle"
        assert pe.config.spawn_rate == 10
        assert pe.config.max_particles == 50
        assert pe.config.lifetime_min == 1.0
        assert pe.config.lifetime_max == 3.0

    def test_no_nodes_file_handled_gracefully(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        map_path = _make_map_json("../assets/tileset.png", data_dir)

        td = TilemapData.load(map_path)

        assert td.area_nodes == []
        assert td.particle_emitters == []

    def test_nodes_dir_parameter_finds_nodes_in_custom_dir(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        map_path = _make_map_json("../assets/tileset.png", data_dir)
        custom_nodes_dir = tmp / "custom_nodes"
        custom_nodes_dir.mkdir()
        nodes_path = custom_nodes_dir / "test_map.nodes.json"
        with open(nodes_path, "w") as f:
            json.dump(AREA_ONLY_NODES, f, indent=2)

        td = TilemapData.load(map_path, nodes_dir=custom_nodes_dir)

        assert len(td.area_nodes) == 1
        assert td.area_nodes[0].node_id == "area_1"
        assert td.particle_emitters == []

    def test_emitter_config_defaults_for_missing_fields(self, map_data):
        tmp, data_dir, assets_dir, png = map_data
        map_path = _make_map_json("../assets/tileset.png", data_dir)
        minimal = {
            "nodes": [
                {
                    "node_id": "pe_min",
                    "name": "Minimal",
                    "node_type": "particle_emitter",
                    "area": {"x": 0, "y": 0, "w": 16, "h": 16},
                    "layer_name": "fx",
                    "properties": {},
                    "group": "",
                },
            ],
            "groups": [],
        }
        nodes_path = data_dir / "test_map.nodes.json"
        with open(nodes_path, "w") as f:
            json.dump(minimal, f, indent=2)

        td = TilemapData.load(map_path)

        assert len(td.particle_emitters) == 1
        pe = td.particle_emitters[0]
        assert pe.config.name == "Minimal"
        assert pe.config.emission_shape == "point"
        assert pe.config.particle_shape == "circle"
        assert pe.config.spawn_rate == 20
        assert pe.config.max_particles == 100
        assert pe.config.lifetime_min == 0.5
        assert pe.config.lifetime_max == 2.0
        assert pe.config.gravity_y == 30.0
