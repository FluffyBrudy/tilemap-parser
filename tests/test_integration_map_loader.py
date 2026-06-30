from pathlib import Path

import pytest

from tilemap_parser import TilemapData, load_map

PROJECT_ROOT = Path(__file__).parent.parent
REAL_MAP_DIR = PROJECT_ROOT / "examples" / "platformer-with-slide" / "data" / "maps"
REAL_MAP_PATH = REAL_MAP_DIR / "map.json"
MAP_1_PATH = REAL_MAP_DIR / "1.json"


class TestLoadRealPlatformerWithSlideMap:
    def test_meta_fields(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert td.tile_size == (16, 16)
        assert td.map_size == (37, 20)
        assert td.render_scale == 3.0

    def test_layers_loaded(self):
        td = TilemapData.load(REAL_MAP_PATH)
        layers = td.get_layers()
        assert len(layers) == 2
        assert layers[0].name == "Layer 1"
        assert layers[0].layer_type == "tile"
        assert layers[0].z_index == 0
        assert layers[1].name == "Layer 2"
        assert layers[1].layer_type == "tile"
        assert layers[1].z_index == 1

    def test_tilesets_loaded(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert len(td.parsed.tilesets) == 1
        assert td.parsed.tilesets[0].type == "tile"

    def test_tileset_image_resolved(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert len(td.resolved_paths) == 1
        assert td.resolved_paths[0].is_file()
        assert td.resolved_paths[0].suffix == ".png"

    def test_tileset_surface_loaded(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert td.surfaces[0] is not None
        assert td.surfaces[0].get_width() > 0
        assert td.surfaces[0].get_height() > 0

    def test_build_tile_map_non_empty(self):
        td = TilemapData.load(REAL_MAP_PATH)
        tile_map = td.build_tile_map()
        assert len(tile_map) > 0

    def test_get_layer_by_id(self):
        td = TilemapData.load(REAL_MAP_PATH)
        layer = td.get_layer(0)
        assert layer is not None
        assert layer.name == "Layer 1"

    def test_get_layer_by_name(self):
        td = TilemapData.load(REAL_MAP_PATH)
        layer = td.get_layer("Layer 2")
        assert layer is not None
        assert layer.z_index == 1

    def test_get_layer_invalid_id_returns_none(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert td.get_layer(999) is None

    def test_get_layer_invalid_name_returns_none(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert td.get_layer("nonexistent") is None

    def test_no_missing_image_warnings(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert len(td.warnings) == 0

    def test_map_path_set(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert td.map_path == REAL_MAP_PATH.resolve()

    def test_nodes_auto_discovered_from_sibling_dir(self):
        td = TilemapData.load(REAL_MAP_PATH)
        assert len(td.particle_emitters) == 1
        pe = td.particle_emitters[0]
        assert pe.node_type == "particle_emitter"
        assert pe.name == "Emitter 1"
        assert len(td.area_nodes) == 0

    def test_get_tile_at_known_position(self):
        td = TilemapData.load(REAL_MAP_PATH)
        tile = td.get_tile_at(0, 0, 15)
        assert tile is not None
        assert tile.variant == 1

    def test_get_tile_at_empty_returns_none(self):
        td = TilemapData.load(REAL_MAP_PATH)
        tile = td.get_tile_at(0, 0, 0)
        assert tile is None

    def test_project_state_has_rules_and_groups(self):
        td = TilemapData.load(REAL_MAP_PATH)
        ps = td.parsed.project_state
        assert len(ps.rules) > 0
        assert len(ps.groups) > 0

    def test_no_warnings_with_load_map_function(self):
        td = load_map(REAL_MAP_PATH)
        assert len(td.warnings) == 0
        assert td.surfaces[0] is not None


class TestLoadSecondMap:
    def test_different_render_scale(self):
        td = TilemapData.load(MAP_1_PATH)
        assert td.render_scale == 4.0

    def test_different_map_size(self):
        td = TilemapData.load(MAP_1_PATH)
        assert td.map_size == (30, 20)

    def test_layers(self):
        td = TilemapData.load(MAP_1_PATH)
        layers = td.get_layers()
        assert len(layers) == 2
        assert layers[0].name == "decorations"
        assert layers[1].name == "Layer 1"

    def test_tileset_loaded(self):
        td = TilemapData.load(MAP_1_PATH)
        assert len(td.surfaces) == 1
        assert td.surfaces[0] is not None
        assert td.resolved_paths[0].is_file()

    def test_no_nodes_file(self):
        td = TilemapData.load(MAP_1_PATH)
        assert td.area_nodes == []
        assert td.particle_emitters == []


class TestMinimalMap:
    def test_load_minimal_map_no_tilesets(self):
        path = PROJECT_ROOT / "examples" / "particles" / "data" / "map.json"
        td = TilemapData.load(path)
        assert td.tile_size == (32, 32)
        assert td.map_size == (30, 20)
        assert len(td.surfaces) == 0
        assert len(td.resolved_paths) == 0
        assert len(td.get_layers()) == 1
