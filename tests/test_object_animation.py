import json
import os
import tempfile
from pathlib import Path

import pygame
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.parser.map_parse import (
    MapParseError,
    ObjectAnimation,
    ParsedObject,
    ParsedObjectArea,
    parse_map_dict,
)
from tilemap_parser.runtime.map_loader import TilemapData


MINIMAL_MAP_META = {
    "tile_size": "16;16",
    "map_size": "10;10",
    "version": "1.1",
}


def _make_minimal_png(path: Path, size: tuple[int, int] = (64, 16)) -> None:
    surf = pygame.Surface(size)
    surf.fill((255, 0, 255))
    pygame.image.save(surf, str(path))


def _make_object_map(data_dir: Path, tileset_path: str, animation: dict | None = None) -> Path:
    obj: dict = {
        "area": {"x": 32, "y": 64, "w": 16, "h": 16},
        "ttype": 0,
        "tileset_type": "object",
        "variant": 0,
    }
    if animation is not None:
        obj["animation"] = animation
    payload = {
        "meta": {**MINIMAL_MAP_META},
        "resources": {"tilesets": [{"path": tileset_path, "type": "object"}]},
        "project_state": {"rules": [], "groups": []},
        "data": {
            "layers": [
                {
                    "name": "Objects",
                    "type": "object",
                    "visible": True,
                    "locked": False,
                    "opacity": 1.0,
                    "z_index": 0,
                    "tiles": {},
                    "objects": {"1": obj},
                    "next_object_id": 2,
                }
            ]
        },
    }
    map_path = data_dir / "test_map.json"
    with open(map_path, "w") as f:
        json.dump(payload, f, indent=2)
    return map_path


@pytest.fixture
def tmp_project():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        data_dir = tmp / "data"
        assets_dir = tmp / "assets"
        data_dir.mkdir()
        assets_dir.mkdir()
        yield tmp, data_dir, assets_dir


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


class TestObjectAnimationParsing:
    def test_parse_valid_animation(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={
                "frame_count": 4,
                "frame_duration_ms": 150,
                "speed": 1.5,
                "loop": True,
                "animation_mode": "random_start_times",
                "random_phase": True,
                "frames": [0, 1, 2, 3],
            },
        )
        data = TilemapData.load(map_path)
        layer = data.get_layer("Objects")
        assert layer is not None
        obj = layer.objects[1]
        assert obj.animation is not None
        assert obj.animation.frame_count == 4
        assert obj.animation.frame_duration_ms == 150.0
        assert obj.animation.speed == 1.5
        assert obj.animation.loop is True
        assert obj.animation.animation_mode == "random_start_times"
        assert obj.animation.random_phase is True
        assert obj.animation.frames == [0, 1, 2, 3]

    def test_parse_animation_defaults(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 2, "frame_duration_ms": 100},
        )
        data = TilemapData.load(map_path)
        obj = data.get_layer("Objects").objects[1]
        anim = obj.animation
        assert anim is not None
        assert anim.speed == 1.0
        assert anim.loop is True
        assert anim.animation_mode == "default"
        assert anim.random_phase is False
        assert anim.frames == []

    def test_no_animation(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(data_dir, ts_path, animation=None)
        data = TilemapData.load(map_path)
        obj = data.get_layer("Objects").objects[1]
        assert obj.animation is None

    def test_missing_frame_count_fails(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_duration_ms": 100},
        )
        with pytest.raises(MapParseError, match="frame_count"):
            TilemapData.load(map_path)

    def test_missing_frame_duration_fails(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 4},
        )
        with pytest.raises(MapParseError, match="frame_duration_ms"):
            TilemapData.load(map_path)

    def test_zero_frame_count_fails(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 0, "frame_duration_ms": 100},
        )
        with pytest.raises(MapParseError, match="frame_count.*must be >= 1"):
            TilemapData.load(map_path)

    def test_negative_duration_fails(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 4, "frame_duration_ms": -50},
        )
        with pytest.raises(MapParseError, match="frame_duration_ms.*must be > 0"):
            TilemapData.load(map_path)

    def test_frames_length_mismatch_fails(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 4, "frame_duration_ms": 100, "frames": [0, 1]},
        )
        with pytest.raises(MapParseError, match="frames.*must contain exactly 4 entries"):
            TilemapData.load(map_path)

    def test_frames_too_many_fails(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 2, "frame_duration_ms": 100, "frames": [0, 1, 2, 3]},
        )
        with pytest.raises(MapParseError, match="frames.*must contain exactly 2 entries"):
            TilemapData.load(map_path)

    def test_frames_negative_index_fails(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 4, "frame_duration_ms": 100, "frames": [0, -1, 2, 3]},
        )
        with pytest.raises(MapParseError, match="frames.*must be non-negative"):
            TilemapData.load(map_path)


class TestObjectAnimationFrames:
    def test_get_frames_with_explicit_frames(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path, (64, 16))
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 4, "frame_duration_ms": 100, "frames": [3, 2, 1, 0]},
        )
        data = TilemapData.load(map_path)
        obj = data.get_layer("Objects").objects[1]
        anim_data = data.get_object_animation(obj)
        assert anim_data is not None
        frames = anim_data["frames"]
        assert len(frames) == 4
        for f in frames:
            assert f.get_size() == (16, 16)

    def test_get_frames_with_default_range(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path, (64, 16))
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 4, "frame_duration_ms": 100},
        )
        data = TilemapData.load(map_path)
        obj = data.get_layer("Objects").objects[1]
        anim_data = data.get_object_animation(obj)
        assert anim_data is not None
        frames = anim_data["frames"]
        assert len(frames) == 4

    def test_get_frames_none_when_no_animation(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(data_dir, ts_path, animation=None)
        data = TilemapData.load(map_path)
        obj = data.get_layer("Objects").objects[1]
        assert data.get_object_animation(obj) is None

    def test_get_object_animation_helper(self, tmp_project):
        _, data_dir, assets_dir = tmp_project
        ts_path = "sheet.png"
        _make_minimal_png(data_dir / ts_path)
        map_path = _make_object_map(
            data_dir,
            ts_path,
            animation={"frame_count": 2, "frame_duration_ms": 200},
        )
        data = TilemapData.load(map_path)
        obj = data.get_layer("Objects").objects[1]
        anim = data.get_object_animation(obj)
        assert anim is not None
        assert len(anim["frames"]) == 2
        assert anim["frame_duration_ms"] == 200.0


class TestObjectAnimationParseMapDict:
    def test_parse_map_dict_directly(self):
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "5;5", "version": "1.1"},
            "resources": {"tilesets": []},
            "project_state": {"rules": [], "groups": []},
            "data": {
                "layers": [
                    {
                        "name": "Entities",
                        "type": "object",
                        "visible": True,
                        "locked": False,
                        "opacity": 1.0,
                        "z_index": 0,
                        "tiles": {},
                        "objects": {
                            "1": {
                                "area": {"x": 0, "y": 0, "w": 16, "h": 16},
                                "ttype": 0,
                                "tileset_type": "object",
                                "variant": 0,
                                "animation": {
                                    "frame_count": 3,
                                    "frame_duration_ms": 80,
                                    "loop": False,
                                    "frames": [0, 1, 2],
                                },
                            }
                        },
                    }
                ]
            },
        }
        parsed = parse_map_dict(payload)
        obj = parsed.layers[0].objects[1]
        assert obj.animation is not None
        assert obj.animation.frame_count == 3
        assert obj.animation.loop is False
        assert obj.animation.frames == [0, 1, 2]

    def test_parse_map_dict_no_animation(self):
        payload = {
            "meta": {"tile_size": "16;16", "map_size": "5;5", "version": "1.1"},
            "resources": {"tilesets": []},
            "project_state": {"rules": [], "groups": []},
            "data": {
                "layers": [
                    {
                        "name": "Entities",
                        "type": "object",
                        "visible": True,
                        "locked": False,
                        "opacity": 1.0,
                        "z_index": 0,
                        "tiles": {},
                        "objects": {
                            "1": {
                                "area": {"x": 0, "y": 0, "w": 16, "h": 16},
                                "ttype": 0,
                                "tileset_type": "object",
                                "variant": 0,
                            }
                        },
                    }
                ]
            },
        }
        parsed = parse_map_dict(payload)
        obj = parsed.layers[0].objects[1]
        assert obj.animation is None
