"""
Tests for tilemap_parser.collision — covering the refactored API where
load_tileset_collision() and load_character_collision() accept a direct
path to the .collision.json file rather than deriving it from an image path.
"""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.collision import (
    # parsers
    parse_tileset_collision,
    parse_character_collision,
    parse_object_collision,
    # loaders
    load_tileset_collision,
    load_character_collision,
    load_object_collision,
    # cache
    CollisionCache,
    get_cached_tileset_collision,
    get_cached_character_collision,
    get_cached_object_collision,
    clear_collision_cache,
    # data classes
    TilesetCollision,
    CharacterCollision,
    RectangleShape,
    CircleShape,
    CapsuleShape,
    CollisionPolygon,
    CollisionParseError,
    ObjectCollisionData,
    ObjectCollisionRegionData,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent.parent / "examples" / "fixtures"
TILESET_COLLISION = FIXTURES / "collision" / "Terrain (32x32).collision.json"
CHARACTER_COLLISION = FIXTURES / "character_collision" / "hero.collision.json"

TILESET_DATA = {
    "tileset_name": "test_tileset",
    "tile_size": [32, 32],
    "tiles": {
        "0": {
            "tile_id": 0,
            "shapes": [
                {
                    "vertices": [[0.0, 0.0], [32.0, 0.0], [32.0, 32.0], [0.0, 32.0]],
                    "one_way": False,
                }
            ],
        },
        "1": {
            "tile_id": 1,
            "shapes": [
                {
                    "vertices": [[0.0, 16.0], [32.0, 16.0], [32.0, 32.0], [0.0, 32.0]],
                    "one_way": True,
                }
            ],
        },
    },
}

CHARACTER_RECT_DATA = {
    "name": "player",
    "shape": {"type": "rectangle", "width": 24.0, "height": 32.0, "offset": [4.0, 0.0]},
    "properties": {"speed": 150},
}

CHARACTER_CIRCLE_DATA = {
    "name": "ball",
    "shape": {"type": "circle", "radius": 16.0, "offset": [0.0, 0.0]},
    "properties": {},
}

CHARACTER_CAPSULE_DATA = {
    "name": "snake",
    "shape": {"type": "capsule", "radius": 8.0, "height": 48.0, "offset": [0.0, 0.0]},
    "properties": {},
}


# ===========================================================================
# parse_tileset_collision
# ===========================================================================

class TestParseTilesetCollision:
    def test_basic_parse(self):
        result = parse_tileset_collision(TILESET_DATA)
        assert isinstance(result, TilesetCollision)
        assert result.tileset_name == "test_tileset"
        assert result.tile_size == (32, 32)
        assert len(result.tiles) == 2

    def test_tile_has_collision(self):
        result = parse_tileset_collision(TILESET_DATA)
        assert result.has_collision(0)
        assert result.has_collision(1)
        assert not result.has_collision(99)

    def test_one_way_flag(self):
        result = parse_tileset_collision(TILESET_DATA)
        shapes = result.get_world_shapes(1, 0, 0)
        assert shapes[0].one_way is True

    def test_world_shapes_transform(self):
        result = parse_tileset_collision(TILESET_DATA)
        shapes = result.get_world_shapes(0, 100.0, 200.0)
        assert len(shapes) == 1
        # All vertices should be offset by (100, 200)
        for vx, vy in shapes[0].vertices:
            assert vx >= 100.0
            assert vy >= 200.0

    def test_world_shapes_missing_tile(self):
        result = parse_tileset_collision(TILESET_DATA)
        assert result.get_world_shapes(99, 0, 0) == []

    def test_missing_tileset_name_raises(self):
        bad = {k: v for k, v in TILESET_DATA.items() if k != "tileset_name"}
        with pytest.raises(CollisionParseError):
            parse_tileset_collision(bad)

    def test_missing_tile_size_raises(self):
        bad = {k: v for k, v in TILESET_DATA.items() if k != "tile_size"}
        with pytest.raises(CollisionParseError):
            parse_tileset_collision(bad)

    def test_empty_tiles(self):
        data = {"tileset_name": "empty", "tile_size": [16, 16], "tiles": {}}
        result = parse_tileset_collision(data)
        assert len(result.tiles) == 0


# ===========================================================================
# parse_character_collision
# ===========================================================================

class TestParseCharacterCollision:
    def test_rectangle(self):
        result = parse_character_collision(CHARACTER_RECT_DATA)
        assert isinstance(result, CharacterCollision)
        assert result.name == "player"
        assert isinstance(result.shape, RectangleShape)
        assert result.shape.width == 24.0
        assert result.shape.height == 32.0
        assert result.shape.offset == (4.0, 0.0)
        assert result.properties["speed"] == 150

    def test_circle(self):
        result = parse_character_collision(CHARACTER_CIRCLE_DATA)
        assert isinstance(result.shape, CircleShape)
        assert result.shape.radius == 16.0

    def test_capsule(self):
        result = parse_character_collision(CHARACTER_CAPSULE_DATA)
        assert isinstance(result.shape, CapsuleShape)
        assert result.shape.radius == 8.0
        assert result.shape.height == 48.0

    def test_unknown_shape_raises(self):
        bad = {
            "name": "x",
            "shape": {"type": "hexagon", "radius": 10.0},
            "properties": {},
        }
        with pytest.raises(CollisionParseError):
            parse_character_collision(bad)

    def test_missing_name_raises(self):
        bad = {k: v for k, v in CHARACTER_RECT_DATA.items() if k != "name"}
        with pytest.raises(CollisionParseError):
            parse_character_collision(bad)

    def test_properties_default_empty(self):
        data = {
            "name": "ghost",
            "shape": {"type": "circle", "radius": 10.0},
        }
        result = parse_character_collision(data)
        assert result.properties == {}


# ===========================================================================
# Shape helpers
# ===========================================================================

class TestShapeHelpers:
    def test_rectangle_get_bounds(self):
        shape = RectangleShape(width=24.0, height=32.0, offset=(4.0, 0.0))
        left, top, right, bottom = shape.get_bounds(100.0, 200.0)
        assert left == 104.0
        assert top == 200.0
        assert right == 128.0
        assert bottom == 232.0

    def test_circle_get_center(self):
        shape = CircleShape(radius=16.0, offset=(2.0, 3.0))
        cx, cy = shape.get_center(100.0, 200.0)
        assert cx == 102.0
        assert cy == 203.0

    def test_capsule_top_bottom(self):
        shape = CapsuleShape(radius=8.0, height=48.0, offset=(0.0, 0.0))
        top = shape.get_top_center(100.0, 200.0)
        bottom = shape.get_bottom_center(100.0, 200.0)
        assert top == (100.0, 200.0)
        assert bottom == (100.0, 248.0)

    def test_collision_polygon_is_valid(self):
        valid = CollisionPolygon(vertices=[(0, 0), (1, 0), (1, 1)])
        invalid = CollisionPolygon(vertices=[(0, 0), (1, 0)])
        assert valid.is_valid()
        assert not invalid.is_valid()

    def test_collision_polygon_transform(self):
        poly = CollisionPolygon(vertices=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)])
        transformed = poly.transform(5.0, 7.0)
        assert transformed.vertices[0] == (5.0, 7.0)
        assert transformed.vertices[1] == (15.0, 7.0)
        assert transformed.vertices[2] == (15.0, 17.0)


# ===========================================================================
# load_tileset_collision — direct path API
# ===========================================================================

class TestLoadTilesetCollision:
    def test_loads_fixture(self):
        result = load_tileset_collision(TILESET_COLLISION)
        assert result is not None
        assert isinstance(result, TilesetCollision)
        assert result.tileset_name == "Terrain (32x32)"

    def test_returns_none_for_missing_file(self, tmp_path):
        result = load_tileset_collision(tmp_path / "nonexistent.collision.json")
        assert result is None

    def test_raises_on_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.collision.json"
        bad.write_text("not json", encoding="utf-8")
        with pytest.raises(CollisionParseError):
            load_tileset_collision(bad)

    def test_raises_on_wrong_schema(self, tmp_path):
        bad = tmp_path / "bad.collision.json"
        bad.write_text(json.dumps({"wrong": "schema"}), encoding="utf-8")
        with pytest.raises(CollisionParseError):
            load_tileset_collision(bad)

    def test_accepts_string_path(self):
        result = load_tileset_collision(str(TILESET_COLLISION))
        assert result is not None

    def test_fixture_tile_ids(self):
        result = load_tileset_collision(TILESET_COLLISION)
        assert result.has_collision(26)
        assert result.has_collision(8)
        assert not result.has_collision(0)

    def test_non_json_file_raises(self, tmp_path):
        # Passing a non-JSON file (e.g. an image) raises CollisionParseError,
        # not silently returns None — the file exists so we try to parse it.
        fake_image = tmp_path / "terrain.png"
        fake_image.write_bytes(b"\x89PNG\r\n")
        with pytest.raises(CollisionParseError):
            load_tileset_collision(fake_image)


# ===========================================================================
# load_character_collision — direct path API
# ===========================================================================

class TestLoadCharacterCollision:
    def test_loads_fixture(self):
        result = load_character_collision(CHARACTER_COLLISION)
        assert result is not None
        assert isinstance(result, CharacterCollision)
        assert result.name == "hero"

    def test_returns_none_for_missing_file(self, tmp_path):
        result = load_character_collision(tmp_path / "ghost.collision.json")
        assert result is None

    def test_raises_on_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.collision.json"
        bad.write_text("{broken", encoding="utf-8")
        with pytest.raises(CollisionParseError):
            load_character_collision(bad)

    def test_accepts_string_path(self):
        result = load_character_collision(str(CHARACTER_COLLISION))
        assert result is not None

    def test_fixture_shape_type(self):
        result = load_character_collision(CHARACTER_COLLISION)
        assert isinstance(result.shape, RectangleShape)

    def test_non_json_file_raises(self, tmp_path):
        # Passing a non-JSON file (e.g. an image) raises CollisionParseError,
        # not silently returns None — the file exists so we try to parse it.
        fake_image = tmp_path / "hero.png"
        fake_image.write_bytes(b"\x89PNG\r\n")
        with pytest.raises(CollisionParseError):
            load_character_collision(fake_image)


# ===========================================================================
# CollisionCache
# ===========================================================================

class TestCollisionCache:
    def setup_method(self):
        self.cache = CollisionCache()

    def test_get_tileset_collision(self):
        result = self.cache.get_tileset_collision(TILESET_COLLISION)
        assert result is not None
        assert result.tileset_name == "Terrain (32x32)"

    def test_get_character_collision(self):
        result = self.cache.get_character_collision(CHARACTER_COLLISION)
        assert result is not None
        assert result.name == "hero"

    def test_missing_returns_none(self, tmp_path):
        result = self.cache.get_tileset_collision(tmp_path / "nope.collision.json")
        assert result is None

    def test_caches_result(self):
        r1 = self.cache.get_tileset_collision(TILESET_COLLISION)
        r2 = self.cache.get_tileset_collision(TILESET_COLLISION)
        assert r1 is r2  # same object — not re-parsed

    def test_clear_removes_cache(self):
        r1 = self.cache.get_tileset_collision(TILESET_COLLISION)
        self.cache.clear()
        r2 = self.cache.get_tileset_collision(TILESET_COLLISION)
        assert r1 is not r2  # re-parsed after clear

    def test_preload_tileset(self):
        self.cache.preload_tileset(TILESET_COLLISION)
        key = str(TILESET_COLLISION.resolve())
        assert key in self.cache._tileset_cache

    def test_preload_character(self):
        self.cache.preload_character(CHARACTER_COLLISION)
        key = str(CHARACTER_COLLISION.resolve())
        assert key in self.cache._character_cache

    def test_cache_key_is_resolved_path(self, tmp_path):
        # Two different Path objects pointing to the same file should share a cache entry
        link = tmp_path / "link.collision.json"
        import shutil
        shutil.copy(TILESET_COLLISION, link)
        r1 = self.cache.get_tileset_collision(link)
        r2 = self.cache.get_tileset_collision(link)
        assert r1 is r2


# ===========================================================================
# Global cache helpers
# ===========================================================================

class TestGlobalCacheHelpers:
    def setup_method(self):
        clear_collision_cache()

    def test_get_cached_tileset(self):
        result = get_cached_tileset_collision(TILESET_COLLISION)
        assert result is not None

    def test_get_cached_character(self):
        result = get_cached_character_collision(CHARACTER_COLLISION)
        assert result is not None

    def test_clear_collision_cache(self):
        get_cached_tileset_collision(TILESET_COLLISION)
        clear_collision_cache()
        # After clear, a fresh load still works
        result = get_cached_tileset_collision(TILESET_COLLISION)
        assert result is not None


# ===========================================================================
# Character collision — polygon shape
# ===========================================================================

class TestCharacterCollisionPolygon:
    def test_parse_polygon(self):
        data = parse_character_collision({
            "name": "test_poly",
            "shape": {
                "type": "polygon",
                "vertices": [[0, 0], [10, 0], [10, 10], [0, 10]],
                "one_way": False,
            },
            "properties": {},
        })
        assert data.name == "test_poly"
        assert isinstance(data.shape, CollisionPolygon)
        assert len(data.shape.vertices) == 4

    def test_parse_polygon_with_layer_mask(self):
        data = parse_character_collision({
            "name": "poly_char",
            "shape": {
                "type": "polygon",
                "vertices": [[0, 0], [5, 0], [5, 5], [0, 5]],
            },
            "properties": {
                "collision_layer": 4,
                "collision_mask": 15,
            },
        })
        assert data.collision_layer == 4
        assert data.collision_mask == 15

    def test_parse_polygon_missing_vertices_raises(self):
        with pytest.raises(CollisionParseError, match="missing"):
            parse_character_collision({
                "name": "bad",
                "shape": {"type": "polygon"},
            })

    def test_parse_polygon_too_few_vertices_raises(self):
        with pytest.raises(CollisionParseError, match="at least 3"):
            parse_character_collision({
                "name": "bad",
                "shape": {
                    "type": "polygon",
                    "vertices": [[0, 0], [10, 10]],
                },
            })


# ===========================================================================
# Character collision — typed layer/mask extraction
# ===========================================================================

class TestCharacterCollisionLayerMask:
    def test_defaults(self):
        data = parse_character_collision({
            "name": "test",
            "shape": {"type": "circle", "radius": 10},
        })
        assert data.collision_layer == 1
        assert data.collision_mask == 0xFFFFFFFF

    def test_from_properties(self):
        data = parse_character_collision({
            "name": "test",
            "shape": {"type": "circle", "radius": 10},
            "properties": {
                "collision_layer": 1024,
                "collision_mask": 65527,
            },
        })
        assert data.collision_layer == 1024
        assert data.collision_mask == 65527

    def test_string_coercion(self):
        """Editor may serialize numbers as strings."""
        data = parse_character_collision({
            "name": "test",
            "shape": {"type": "circle", "radius": 10},
            "properties": {
                "collision_layer": "2",
                "collision_mask": "65535",
            },
        })
        assert data.collision_layer == 2
        assert data.collision_mask == 65535

    def test_properties_dict_still_preserved(self):
        data = parse_character_collision({
            "name": "test",
            "shape": {"type": "circle", "radius": 10},
            "properties": {
                "collision_layer": 1,
                "collision_mask": 1,
                "custom_field": "value",
            },
        })
        assert data.properties["custom_field"] == "value"
        assert data.properties["collision_layer"] == 1


# ===========================================================================
# Object collision parsing
# ===========================================================================

class TestParseObjectCollision:
    def test_basic_parse(self):
        data = parse_object_collision({
            "tileset_name": "BaseSet",
            "regions": {
                "r1": {
                    "region_id": "r1",
                    "region_rect": [0, 0, 100, 100],
                    "name": "Test",
                    "shapes": [{
                        "type": "polygon",
                        "vertices": [[0, 0], [10, 0], [10, 10]],
                        "one_way": False,
                    }],
                    "properties": {
                        "collision_layer": 16,
                        "collision_mask": 65535,
                    },
                },
            },
        })
        assert isinstance(data, ObjectCollisionData)
        assert data.tileset_name == "BaseSet"
        assert len(data.regions) == 1
        r = data.get_region("r1")
        assert r is not None
        assert r.name == "Test"
        assert r.region_rect == (0, 0, 100, 100)
        assert len(r.shapes) == 1
        assert r.collision_layer == 16
        assert r.collision_mask == 65535

    def test_empty_regions(self):
        data = parse_object_collision({
            "tileset_name": "Empty",
            "regions": {},
        })
        assert data.tileset_name == "Empty"
        assert len(data.regions) == 0

    def test_has_collision(self):
        data = parse_object_collision({
            "tileset_name": "Test",
            "regions": {
                "r1": {
                    "region_id": "r1",
                    "region_rect": [0, 0, 10, 10],
                    "name": "Has",
                    "shapes": [{"type": "polygon", "vertices": [[0,0],[1,0],[1,1]], "one_way": False}],
                    "properties": {},
                },
                "r2": {
                    "region_id": "r2",
                    "region_rect": [0, 0, 10, 10],
                    "name": "Empty",
                    "shapes": [],
                    "properties": {},
                },
            },
        })
        assert data.has_collision("r1") is True
        assert data.has_collision("r2") is False
        assert data.has_collision("missing") is False

    def test_get_world_shapes(self):
        data = parse_object_collision({
            "tileset_name": "Test",
            "regions": {
                "r1": {
                    "region_id": "r1",
                    "region_rect": [100, 200, 50, 50],
                    "name": "Test",
                    "shapes": [{"type": "polygon", "vertices": [[0,0],[10,0],[10,10]], "one_way": False}],
                    "properties": {},
                },
            },
        })
        r = data.get_region("r1")
        world_shapes = r.get_world_shapes(0, 0)
        assert len(world_shapes) == 1
        # Vertices should be offset by region_rect
        assert world_shapes[0].vertices[0] == (100.0, 200.0)

    def test_string_layer_mask_coercion(self):
        data = parse_object_collision({
            "tileset_name": "Test",
            "regions": {
                "r1": {
                    "region_id": "r1",
                    "region_rect": [0, 0, 10, 10],
                    "name": "Test",
                    "shapes": [],
                    "properties": {
                        "collision_layer": "16",
                        "collision_mask": "65535",
                    },
                },
            },
        })
        r = data.get_region("r1")
        assert r.collision_layer == 16
        assert r.collision_mask == 65535

    def test_missing_tileset_name_raises(self):
        with pytest.raises(CollisionParseError):
            parse_object_collision({"regions": {}})


# ===========================================================================
# Object collision loading
# ===========================================================================

class TestLoadObjectCollision:
    def test_returns_none_for_missing_file(self):
        result = load_object_collision("nonexistent.object_collision.json")
        assert result is None

    def test_raises_on_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.object_collision.json"
        bad_file.write_text("not json")
        with pytest.raises(CollisionParseError):
            load_object_collision(bad_file)

    def test_loads_valid_file(self, tmp_path):
        valid_file = tmp_path / "test.object_collision.json"
        valid_file.write_text(json.dumps({
            "tileset_name": "TestSet",
            "regions": {
                "r1": {
                    "region_id": "r1",
                    "region_rect": [0, 0, 10, 10],
                    "name": "Test",
                    "shapes": [],
                    "properties": {},
                },
            },
        }))
        result = load_object_collision(valid_file)
        assert result is not None
        assert result.tileset_name == "TestSet"


# ===========================================================================
# Object collision caching
# ===========================================================================

class TestObjectCollisionCache:
    def setup_method(self):
        self.cache = CollisionCache()
        self.tmp = Path(__file__).parent.parent / "examples" / "game-example" / "data" / "collision"

    def test_get_object_collision(self):
        result = self.cache.get_object_collision(self.tmp / "RACCOONSPRITESHEET.object_collision.json")
        assert result is not None
        assert result.tileset_name == "RACCOONSPRITESHEET"

    def test_caches_result(self, tmp_path):
        f = tmp_path / "test.object_collision.json"
        f.write_text(json.dumps({
            "tileset_name": "Test",
            "regions": {},
        }))
        r1 = self.cache.get_object_collision(f)
        r2 = self.cache.get_object_collision(f)
        assert r1 is r2

    def test_clear_removes_cache(self, tmp_path):
        f = tmp_path / "test.object_collision.json"
        f.write_text(json.dumps({
            "tileset_name": "Test",
            "regions": {},
        }))
        r1 = self.cache.get_object_collision(f)
        self.cache.clear()
        r2 = self.cache.get_object_collision(f)
        assert r1 is not r2

    def test_preload_object(self, tmp_path):
        f = tmp_path / "test.object_collision.json"
        f.write_text(json.dumps({
            "tileset_name": "Test",
            "regions": {},
        }))
        self.cache.preload_object(f)
        assert f.resolve().as_posix() in str(self.cache._object_cache)


class TestGlobalObjectCacheHelper:
    def setup_method(self):
        clear_collision_cache()

    def test_get_cached_object(self, tmp_path):
        f = tmp_path / "test.object_collision.json"
        f.write_text(json.dumps({
            "tileset_name": "Test",
            "regions": {},
        }))
        result = get_cached_object_collision(f)
        assert result is not None
        assert result.tileset_name == "Test"
