from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def _resolve(name: str) -> Path:
    p = FIXTURES / name
    assert p.is_file(), f"Fixture not found: {p}"
    return p


class TestParseTsx:
    def test_basic_tsx(self):
        from tilemap_parser.parser.tmx_converter import parse_tsx_file

        data = parse_tsx_file(_resolve("test_tileset.tsx"))
        assert data["name"] == "test_tileset"
        assert data["tilewidth"] == 32
        assert data["tileheight"] == 32
        assert data["tilecount"] == 4
        assert data["columns"] == 2
        assert data["image"] == "tileset.png"
        assert "properties" not in data
        assert "tile_properties" in data
        tile0 = data["tile_properties"]["0"]
        assert tile0["grass"] is True
        tile1 = data["tile_properties"]["1"]
        assert tile1["hp"] == 10

    def test_tsx_file_not_found(self):
        from tilemap_parser.parser.tmx_converter import TmxParseError, parse_tsx_file

        with pytest.raises(TmxParseError, match="not found"):
            parse_tsx_file("/nonexistent/nope.tsx")

    def test_tsx_invalid_xml(self, tmp_path):
        from tilemap_parser.parser.tmx_converter import TmxParseError, parse_tsx_file

        bad = tmp_path / "bad.tsx"
        bad.write_text("not xml")
        with pytest.raises(TmxParseError, match="Invalid TSX"):
            parse_tsx_file(bad)


class TestParseTmxCsv:
    def test_load_via_parse_map_file(self):
        from tilemap_parser.parser.map_parse import parse_map_file

        parsed = parse_map_file(_resolve("test_map_csv.tmx"))

        assert parsed.meta.tile_size == (32, 32)
        assert parsed.meta.map_size == (3, 3)

        assert len(parsed.tilesets) == 1
        assert parsed.tilesets[0].path.endswith("tileset.png")

        assert len(parsed.layers) == 1
        layer = parsed.layers[0]
        assert layer.name == "Tile Layer 1"
        assert layer.layer_type == "tile"
        assert layer.visible is True
        assert layer.opacity == 1.0

        assert len(layer.tiles) == 4  # only GIDs 1-4 valid (tilecount=4)

        assert (0, 0) in layer.tiles
        assert layer.tiles[(0, 0)].ttype == 0
        assert layer.tiles[(0, 0)].variant == 0
        assert layer.tiles[(1, 0)].variant == 1
        assert layer.tiles[(2, 0)].variant == 2
        assert layer.tiles[(0, 1)].variant == 3

        assert (2, 2) not in layer.tiles  # GID 0 → empty

    def test_embedded_tileset(self):
        from tilemap_parser.parser.map_parse import parse_map_file

        parsed = parse_map_file(_resolve("test_map_embedded_tileset.tmx"))

        assert len(parsed.tilesets) == 1
        ts = parsed.tilesets[0]
        assert ts.path.endswith("builtin.png")
        assert ts.type == "tile"
        assert ts._tilecount == 4

        layer = parsed.layers[0]
        assert len(layer.tiles) == 4
        assert layer.tiles[(0, 0)].ttype == 0
        assert layer.tiles[(0, 0)].variant == 0
        assert layer.tiles[(1, 1)].variant == 3

    def test_empty_map(self):
        from tilemap_parser.parser.map_parse import parse_map_file

        parsed = parse_map_file(_resolve("test_map_empty.tmx"))

        assert parsed.meta.map_size == (10, 10)
        assert len(parsed.tilesets) == 0
        assert len(parsed.layers) == 1
        assert len(parsed.layers[0].tiles) == 0


class TestParseTmxBase64:
    def test_base64_zlib(self):
        from tilemap_parser.parser.map_parse import parse_map_file

        parsed = parse_map_file(_resolve("test_map_base64.tmx"))

        assert len(parsed.layers) == 1
        layer = parsed.layers[0]
        assert len(layer.tiles) == 4

        assert layer.tiles[(0, 0)].ttype == 0
        assert layer.tiles[(0, 0)].variant == 0
        assert layer.tiles[(1, 0)].variant == 1
        assert (2, 2) not in layer.tiles  # GID 0 → empty

    def test_base64_raw_uncompressed(self):
        from tilemap_parser.parser.map_parse import parse_map_file

        parsed = parse_map_file(_resolve("test_map_base64_raw.tmx"))

        assert len(parsed.layers) == 1
        layer = parsed.layers[0]
        assert len(layer.tiles) == 4
        assert layer.tiles[(0, 0)].variant == 0
        assert layer.tiles[(2, 0)].variant == 2
        assert (1, 1) not in layer.tiles  # GID 5 is out of range


class TestFlipFlags:
    def test_flip_flags_preserved_on_parsed_tile(self):
        from tilemap_parser.parser.map_parse import parse_map_file

        parsed = parse_map_file(_resolve("test_map_flip.tmx"))

        layer = parsed.layers[0]
        assert len(layer.tiles) == 2

        tile_with_flag = layer.tiles[(0, 0)]
        assert tile_with_flag.variant == 0
        assert tile_with_flag.flip_h is True
        assert tile_with_flag.flip_v is False
        assert tile_with_flag.flip_d is False
        assert tile_with_flag.rotated_hex120 is False

        tile_no_flag = layer.tiles[(1, 0)]
        assert tile_no_flag.variant == 0
        assert tile_no_flag.flip_h is False
        assert tile_no_flag.flip_v is False
        assert tile_no_flag.flip_d is False
        assert tile_no_flag.rotated_hex120 is False

    def test_strip_flip_bits(self):
        from tilemap_parser.parser.tmx_converter import (
            TILE_FLIP_H,
            TILE_FLIP_V,
            TILE_FLIP_D,
            TILE_FLIP_HEX,
            TILE_FLIP_MASK,
            _decode_flip_flags,
        )

        assert _decode_flip_flags(1) == (1, False, False, False, False)
        assert _decode_flip_flags(TILE_FLIP_H | 5) == (5, True, False, False, False)
        assert _decode_flip_flags(TILE_FLIP_V | 3) == (3, False, True, False, False)
        assert _decode_flip_flags(TILE_FLIP_D | 7) == (7, False, False, True, False)
        assert _decode_flip_flags(TILE_FLIP_HEX | 11) == (11, False, False, False, True)
        assert _decode_flip_flags(TILE_FLIP_H | TILE_FLIP_V | 42) == (42, True, True, False, False)
        assert _decode_flip_flags(TILE_FLIP_H | TILE_FLIP_V | TILE_FLIP_D | 99) == (99, True, True, True, False)
        assert _decode_flip_flags(0) == (0, False, False, False, False)


class TestDecodeHelpers:
    def test_decode_csv(self):
        from tilemap_parser.parser.tmx_converter import _decode_csv

        result = _decode_csv("1,2,3\n4,5,6\n")
        assert result == [1, 2, 3, 4, 5, 6]

    def test_decode_csv_empty(self):
        from tilemap_parser.parser.tmx_converter import _decode_csv

        assert _decode_csv("") == []

    def test_decode_base64_zlib(self):
        import base64
        import struct
        import zlib

        from tilemap_parser.parser.tmx_converter import _decode_base64

        data = struct.pack("<4I", 10, 20, 30, 40)
        b64 = base64.b64encode(zlib.compress(data)).decode()
        result = _decode_base64(b64, "zlib")
        assert result == [10, 20, 30, 40]

    def test_decode_base64_uncompressed(self):
        import base64
        import struct

        from tilemap_parser.parser.tmx_converter import _decode_base64

        data = struct.pack("<3I", 7, 8, 9)
        b64 = base64.b64encode(data).decode()
        result = _decode_base64(b64, None)
        assert result == [7, 8, 9]

    def test_decode_base64_unsupported_compression(self):
        from tilemap_parser.parser.tmx_converter import TmxParseError, _decode_base64

        with pytest.raises(TmxParseError, match="Unsupported"):
            _decode_base64("AAAA", "lzma")


class TestProjectState:
    def test_project_state_empty(self):
        from tilemap_parser.parser.map_parse import parse_map_file

        parsed = parse_map_file(_resolve("test_map_csv.tmx"))

        assert len(parsed.project_state.rules) == 0
        assert len(parsed.project_state.groups) == 0
        assert parsed.project_state.automap_rules is None


class TestXmlEncoding:
    def test_xml_tile_encoding(self, tmp_path):
        from tilemap_parser.parser.tmx_converter import parse_tmx_file

        tmx = tmp_path / "xml_encoded.tmx"
        tmx.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down" width="2" height="2" tilewidth="16" tileheight="16" infinite="0">
 <tileset firstgid="1" name="a" tilewidth="16" tileheight="16" tilecount="4" columns="2">
  <image source="a.png" width="32" height="32"/>
 </tileset>
 <layer id="1" name="Tile Layer 1" width="2" height="2">
  <data>
   <tile gid="1"/>
   <tile gid="2"/>
   <tile gid="3"/>
   <tile gid="4"/>
  </data>
 </layer>
</map>""")
        parsed = parse_tmx_file(tmx)
        assert len(parsed.layers[0].tiles) == 4
        assert parsed.layers[0].tiles[(0, 0)].variant == 0
        assert parsed.layers[0].tiles[(1, 1)].variant == 3

    def test_xml_with_empty_tiles(self, tmp_path):
        from tilemap_parser.parser.tmx_converter import parse_tmx_file

        tmx = tmp_path / "xml_empty.tmx"
        tmx.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down" width="2" height="2" tilewidth="16" tileheight="16" infinite="0">
 <tileset firstgid="1" name="a" tilewidth="16" tileheight="16" tilecount="4" columns="2">
  <image source="a.png" width="32" height="32"/>
 </tileset>
 <layer id="1" name="Empty" width="2" height="2">
  <data>
   <tile gid="0"/>
   <tile gid="0"/>
   <tile gid="0"/>
   <tile gid="1"/>
  </data>
 </layer>
</map>""")
        parsed = parse_tmx_file(tmx)
        assert len(parsed.layers[0].tiles) == 1
        assert (1, 1) in parsed.layers[0].tiles


class TestLayerProperties:
    def test_layer_visibility_and_opacity(self, tmp_path):
        from tilemap_parser.parser.tmx_converter import parse_tmx_file

        tmx = tmp_path / "props.tmx"
        tmx.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down" width="1" height="1" tilewidth="16" tileheight="16" infinite="0">
 <layer id="1" name="Hidden" width="1" height="1" visible="0" opacity="0.5">
  <data encoding="csv">0</data>
 </layer>
</map>""")
        parsed = parse_tmx_file(tmx)
        layer = parsed.layers[0]
        assert layer.visible is False
        assert layer.opacity == 0.5
        assert layer.name == "Hidden"


class TestMultipleLayers:
    def test_two_layers(self, tmp_path):
        from tilemap_parser.parser.tmx_converter import parse_tmx_file

        tmx = tmp_path / "two_layers.tmx"
        tmx.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down" width="2" height="2" tilewidth="16" tileheight="16" infinite="0">
 <tileset firstgid="1" name="a" tilewidth="16" tileheight="16" tilecount="4" columns="2">
  <image source="a.png" width="32" height="32"/>
 </tileset>
 <layer id="1" name="Ground" width="2" height="2">
  <data encoding="csv">1,1,1,1</data>
 </layer>
 <layer id="2" name="Overlay" width="2" height="2">
  <data encoding="csv">0,2,0,0</data>
 </layer>
</map>""")
        parsed = parse_tmx_file(tmx)
        assert len(parsed.layers) == 2
        assert parsed.layers[0].name == "Ground"
        assert parsed.layers[0].z_index == 0
        assert len(parsed.layers[0].tiles) == 4
        assert parsed.layers[1].name == "Overlay"
        assert parsed.layers[1].z_index == 1
        assert len(parsed.layers[1].tiles) == 1


class TestRuntimeIntegration:
    def test_tmx_loads_via_tilemap_data(self, tmp_path):
        import pygame

        from tilemap_parser.runtime.map_loader import TilemapData

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        png = assets_dir / "tileset.png"
        surf = pygame.Surface((64, 64))
        surf.fill((255, 0, 255))
        pygame.image.save(surf, str(png))

        tmx = data_dir / "test.tmx"
        tmx.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down" width="2" height="2" tilewidth="32" tileheight="32" infinite="0">
 <tileset firstgid="1" name="test" tilewidth="32" tileheight="32" tilecount="4" columns="2">
  <image source="../assets/tileset.png" width="64" height="64"/>
 </tileset>
 <layer id="1" name="Ground" width="2" height="2">
  <data encoding="csv">1,2,3,4</data>
 </layer>
</map>""")

        td = TilemapData.load(tmx, skip_missing_images=False)
        assert len(td.warnings) == 0
        assert len(td.surfaces) == 1
        assert td.surfaces[0] is not None
        assert len(td.parsed.layers) == 1
        layer_data = td.get_layer("Ground")
        assert layer_data is not None
        assert len(layer_data.tiles) == 4

    def test_tmx_missing_tileset_warns(self, tmp_path):
        import pygame

        from tilemap_parser.runtime.map_loader import TilemapData

        tmx = tmp_path / "missing.tmx"
        tmx.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down" width="2" height="2" tilewidth="32" tileheight="32" infinite="0">
 <tileset firstgid="1" source="nonexistent.tsx"/>
 <layer id="1" name="Ground" width="2" height="2">
  <data encoding="csv">0,0,0,0</data>
 </layer>
</map>""")

        td = TilemapData.load(tmx, extra_search_base=tmp_path)
        assert len(td.warnings) >= 1

    def test_real_sewers_map_from_tiled_examples(self):
        import pygame

        from tilemap_parser.runtime.map_loader import TilemapData
        from tilemap_parser.parser.map_parse import parse_map_file

        tmx_path = _resolve("sewers.tmx")
        png_path = _resolve("sewer_tileset.png")
        assert png_path.is_file()

        parsed = parse_map_file(tmx_path)

        assert parsed.meta.tile_size == (24, 24)
        assert parsed.meta.map_size == (50, 50)

        assert len(parsed.tilesets) == 1
        ts = parsed.tilesets[0]
        assert ts.path.endswith("sewer_tileset.png")
        assert ts.type == "tile"

        assert len(parsed.layers) == 2
        bottom = parsed.layers[0]
        top = parsed.layers[1]

        assert bottom.name == "Bottom"
        assert bottom.layer_type == "tile"
        assert bottom.opacity == 1.0
        assert len(bottom.tiles) > 0

        assert top.name == "Top"
        assert top.layer_type == "tile"
        assert top.opacity == 0.49
        assert len(top.tiles) > 0

        all_ttypes = {t.ttype for t in bottom.tiles.values()}
        assert all_ttypes == {0}

        all_variants = {t.variant for t in bottom.tiles.values()}
        max_variant = max(all_variants)
        min_variant = min(all_variants)
        assert min_variant >= 0
        assert max_variant < 72  # 8 cols * 9 rows

        td = TilemapData.load(tmx_path, skip_missing_images=False)
        assert len(td.warnings) == 0
        assert len(td.surfaces) == 1
        assert td.surfaces[0] is not None
        assert td.surfaces[0].get_size() == (192, 217)

        assert len(td.parsed.layers) == 2

        assert td.get_layer("Bottom") is not None
        assert td.get_layer("Top") is not None


class TestErrorCases:
    def test_nonexistent_file(self):
        from tilemap_parser.parser.map_parse import parse_map_file

        with pytest.raises(Exception, match="Not a file"):
            parse_map_file("/nonexistent/map.tmx")

    def test_wrong_extension_raises_error(self, tmp_path):
        from tilemap_parser.parser.map_parse import parse_map_file

        f = tmp_path / "test.py"
        f.write_text("not a map")
        with pytest.raises(Exception, match=r"\.json.*\.tmx"):
            parse_map_file(f)
