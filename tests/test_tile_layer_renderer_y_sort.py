"""
Tests for TileLayerRenderer y-sort.

Covers:
- y_sort read from parsed layer data
- y-major iteration when layer.y_sort=True
- Game-side object blitting after render (renderer is tile-only)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pygame
import pytest
from pygame import Surface

from tilemap_parser.parser.map_parse import (
    ParsedLayer,
    ParsedMeta,
    ParsedMap,
    _parse_layer,
)
from tilemap_parser.runtime.map_loader import TilemapData
from tilemap_parser.runtime.renderer import TileLayerRenderer


# ---------------------------------------------------------------------------
# ParsedLayer y_sort field
# ---------------------------------------------------------------------------


class TestParsedLayerYSort:
    def test_default_is_false(self):
        """y_sort defaults to False when not present in data."""
        d = {
            "name": "test",
            "type": "tile",
            "visible": True,
            "locked": False,
            "opacity": 1.0,
            "z_index": 0,
        }
        layer = _parse_layer(d, 0, "test")
        assert layer.y_sort is False

    def test_reads_true(self):
        d = {
            "name": "test",
            "type": "tile",
            "visible": True,
            "locked": False,
            "opacity": 1.0,
            "z_index": 0,
            "y_sort": True,
        }
        layer = _parse_layer(d, 0, "test")
        assert layer.y_sort is True

    def test_reads_false_explicit(self):
        d = {
            "name": "test",
            "type": "tile",
            "visible": True,
            "locked": False,
            "opacity": 1.0,
            "z_index": 0,
            "y_sort": False,
        }
        layer = _parse_layer(d, 0, "test")
        assert layer.y_sort is False

    def test_y_sort_origin_defaults_to_zero(self):
        d = {"name": "test", "type": "tile", "visible": True, "locked": False, "opacity": 1.0, "z_index": 0}
        layer = _parse_layer(d, 0, "test")
        assert layer.y_sort_origin == 0

    def test_y_sort_origin_reads_from_json(self):
        d = {"name": "test", "type": "tile", "visible": True, "locked": False, "opacity": 1.0, "z_index": 0, "y_sort_origin": 16}
        layer = _parse_layer(d, 0, "test")
        assert layer.y_sort_origin == 16


# ---------------------------------------------------------------------------
# Helpers — minimal map for renderer tests
# ---------------------------------------------------------------------------


def _dummy_tileset_surface(w=16, h=16) -> Surface:
    """Create a solid-colour surface to serve as a tileset cell."""
    surf = Surface((w, h))
    surf.fill((200, 100, 50))
    return surf


def _make_tile(pos, ttype=0, variant=0):
    from tilemap_parser.parser.map_parse import ParsedTile

    return ParsedTile(pos=pos, ttype=ttype, variant=variant, gid=None, properties=None)


def _make_map_data(layers, tile_size=(16, 16)) -> TilemapData:
    """Build a TilemapData from a list of ParsedLayer objects."""
    from pathlib import Path
    from tilemap_parser.parser.map_parse import ParsedTileset

    meta = ParsedMeta(
        tile_size=tile_size,
        map_size=(10, 10),
        initial_map_size=(10, 10),
        zoom_level=1.0,
        scroll=(0, 0),
        version="1.1",
        render_scale=1.0,
    )
    mock_map = object.__new__(ParsedMap)
    mock_map.meta = meta
    mock_map.layers = layers
    mock_map.tilesets = [ParsedTileset(path="dummy.png", type="tile")]
    tw, th = tile_size
    resolved_paths = [Path("dummy.png")]
    return TilemapData(mock_map, [_dummy_tileset_surface(tw, th)], resolved_paths, [])


# ---------------------------------------------------------------------------
# TileLayerRenderer — y_sort iteration
# ---------------------------------------------------------------------------


class _SpySurface(pygame.Surface):
    """Records (dest_x, dest_y) for each blit call."""

    def __init__(self, size):
        super().__init__(size)
        self.blit_calls: list[tuple[float, float]] = []

    def blit(self, source, dest, *args, **kwargs):
        if isinstance(dest, tuple):
            self.blit_calls.append((float(dest[0]), float(dest[1])))
        else:
            self.blit_calls.append((float(dest.x), float(dest.y)))
        return super().blit(source, dest, *args, **kwargs)


class TestLayerYSort:
    """Verify that y_sort changes iteration order within a chunk."""

    def make_map_data_two_tiles(self, y_sort: bool = True) -> TilemapData:
        """One layer with two tiles at different Y positions."""
        layer = ParsedLayer(
            id=0,
            name="Bushes",
            layer_type="tile",
            visible=True,
            locked=False,
            opacity=1.0,
            z_index=0,
            y_sort=y_sort,
        )
        layer.tiles[(0, 0)] = _make_tile((0, 0))
        layer.tiles[(0, 5)] = _make_tile((0, 5))
        return _make_map_data([layer])

    def test_y_sort_layer_does_not_crash(self):
        """Layer with y_sort=True renders without error."""
        data = self.make_map_data_two_tiles()
        renderer = TileLayerRenderer(data)
        target = Surface((200, 200))
        stats = renderer.render(target, (0, 0))
        assert stats.drawn_tiles == 2

    def test_y_major_order(self):
        """y-sort within a chunk produces y-major iteration."""
        data = self.make_map_data_two_tiles(y_sort=True)
        renderer = TileLayerRenderer(data)
        target = _SpySurface((200, 200))
        renderer.render(target, (0, 0))
        ys = [y for _, y in target.blit_calls]
        assert ys == sorted(ys)

    def test_no_ysort_preserves_input_order(self):
        """Without y-sort the chunk iteration is insertion order."""
        data = self.make_map_data_two_tiles(y_sort=False)
        renderer = TileLayerRenderer(data)
        target = _SpySurface((200, 200))
        renderer.render(target, (0, 0))
        ef = 16
        assert target.blit_calls == [(0.0, 0.0), (0.0, 5.0 * ef)]

    def test_y_sort_origin_shifts_sort_order(self):
        """y_sort_origin offsets the Y used for sorting."""
        layer = ParsedLayer(
            id=0, name="test", layer_type="tile", visible=True,
            locked=False, opacity=1.0, z_index=0,
            y_sort=True, y_sort_origin=32,
        )
        layer.tiles[(0, 0)] = _make_tile((0, 0))
        layer.tiles[(0, 1)] = _make_tile((0, 1))
        data = _make_map_data([layer])
        renderer = TileLayerRenderer(data)
        target = _SpySurface((200, 200))
        renderer.render(target, (0, 0))
        ef = 16
        assert target.blit_calls == [(0.0, 0.0), (0.0, 1.0 * ef)]


# ---------------------------------------------------------------------------
# Integration — y_sort tiles + game-side object blits (renderer is tile-only)
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_game_side_blits_after_render(self):
        """Objects blit in caller order after tiles (the extra_objects migration)."""
        layer = ParsedLayer(
            id=0,
            name="Bushes",
            layer_type="tile",
            visible=True,
            locked=False,
            opacity=1.0,
            z_index=0,
            y_sort=True,
        )
        layer.tiles[(0, 0)] = _make_tile((0, 0))
        layer.tiles[(0, 5)] = _make_tile((0, 5))
        data = _make_map_data([layer])
        renderer = TileLayerRenderer(data)
        target = _SpySurface((200, 200))
        ef = 16
        stats = renderer.render(target, (0, 0))
        assert stats.drawn_tiles == 2
        # Game side: blit object surfaces in caller order after render.
        for surf, x, y in [
            (_dummy_tileset_surface(), 5, 25),
            (_dummy_tileset_surface(), 5, 3),
        ]:
            target.blit(surf, (x, y))
        assert len(target.blit_calls) == 4
        assert target.blit_calls[0] == (0.0, 0.0)  # tile y=0
        assert target.blit_calls[1] == (0.0, 5.0 * ef)  # tile y=5
        assert target.blit_calls[2] == (5.0, 25.0)  # object in caller order
        assert target.blit_calls[3] == (5.0, 3.0)  # object in caller order
