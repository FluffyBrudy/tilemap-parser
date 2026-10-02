import json
import sys
import tempfile
from pathlib import Path

import pygame
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.parser.map_parse import MapParseError
from tilemap_parser.runtime.map_loader import TilemapData, load_map


def _png(path: Path, size, color):
    surf = pygame.Surface(size)
    surf.fill(color)
    pygame.image.save(surf, str(path))


@pytest.fixture
def proj():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        data_dir = tmp / "data"
        assets_dir = tmp / "assets"
        data_dir.mkdir()
        assets_dir.mkdir()
        _png(assets_dir / "tileset.png", (64, 64), (255, 0, 0))
        yield tmp, data_dir, assets_dir


def _write_map(data_dir: Path, render_scale=1.0, name="m.json", tileset="tileset.png", animation=None):
    ts_entry = {"path": f"../assets/{tileset}", "type": "tile"}
    if animation is not None:
        ts_entry["animation"] = animation
    payload = {
        "meta": {"tile_size": "16;16", "map_size": "4;4", "render_scale": render_scale, "version": "1.1"},
        "resources": {"tilesets": [ts_entry]},
        "project_state": {"rules": [], "groups": []},
        "data": {
            "layers": [
                {
                    "name": "L",
                    "type": "tile",
                    "visible": True,
                    "tiles": {
                        "0;0": {"pos": "0;0", "ttype": 0, "variant": 0},
                        "1;0": {"pos": "1;0", "ttype": 0, "variant": 3},
                    },
                }
            ]
        },
    }
    mp = data_dir / name
    with open(mp, "w") as f:
        json.dump(payload, f, indent=2)
    return mp


def _surf(size, color):
    s = pygame.Surface(size)
    s.fill(color)
    return s.convert_alpha()


def test_valid_swap_renders_replacement(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir)
    td = TilemapData.load(mp, tileset_surfaces={"tileset": _surf((64, 64), (0, 0, 255))})
    assert any("overridden" in w for w in td.warnings)
    assert td.get_tile_surface(0, 0).get_at((0, 0))[:3] == (0, 0, 255)


def test_index_key_and_load_map_passthrough(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir)
    td = load_map(mp, tileset_surfaces={0: _surf((64, 64), (0, 255, 0))})
    assert td.get_tile_surface(0, 0).get_at((0, 0))[:3] == (0, 255, 0)


def test_dim_mismatch_against_existing_file_fails(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir)
    with pytest.raises(MapParseError):
        TilemapData.load(mp, tileset_surfaces={"tileset": _surf((32, 32), (0, 0, 255))})


def test_missing_original_structural_check(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir, tileset="gone.png")
    with pytest.raises(MapParseError):
        TilemapData.load(mp, tileset_surfaces={"gone": _surf((20, 20), (0, 0, 255))})
    td = TilemapData.load(mp, tileset_surfaces={"gone": _surf((64, 64), (0, 0, 255))})
    assert td.get_tile_surface(0, 0).get_at((0, 0))[:3] == (0, 0, 255)


def test_out_of_range_variant_fails(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir, tileset="gone.png")
    with pytest.raises(MapParseError):
        TilemapData.load(mp, tileset_surfaces={"gone": _surf((16, 16), (0, 0, 255))})


def test_unknown_stem_ignored(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir)
    td = TilemapData.load(mp, tileset_surfaces={"nope": _surf((64, 64), (0, 0, 255))})
    assert td.get_tile_surface(0, 0).get_at((0, 0))[:3] == (255, 0, 0)


def test_odd_render_scale_no_false_failure(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir, render_scale=1.5)
    td = TilemapData.load(mp, tileset_surfaces={"tileset": _surf((64, 64), (0, 0, 255))})
    assert td.surfaces[0].get_size() == (64, 64)


_ANIM = {"frame_count": 3, "frame_duration_ms": 100, "frame_stride": 2}


def test_animated_frame_cells_rejected_when_short(proj):
    _, data_dir, _ = proj
    small = _surf((64, 16), (0, 0, 255))
    plain = _write_map(data_dir, name="plain.json", tileset="gone.png")
    td = TilemapData.load(plain, tileset_surfaces={"gone": small})
    assert td.get_tile_surface(0, 3) is not None
    anim_map = _write_map(data_dir, name="anim.json", tileset="gone.png", animation=_ANIM)
    with pytest.raises(MapParseError):
        TilemapData.load(anim_map, tileset_surfaces={"gone": _surf((64, 16), (0, 0, 255))})


def test_animated_frame_cells_accepted_when_covered(proj):
    _, data_dir, _ = proj
    mp = _write_map(data_dir, tileset="gone.png", animation=_ANIM)
    td = TilemapData.load(mp, tileset_surfaces={"gone": _surf((128, 16), (0, 0, 255))})
    assert td.get_tile_surface(0, 7) is not None
