"""
Tests for tilemap_parser.runtime.map_object.

Covers:
- load_map_objects() — basic object loading with surface + collision
- Edge cases: missing collision file, missing region_id, no object layer
- MapObject satisfies ICollidableObject protocol
"""

import json
import tempfile
from pathlib import Path

import pygame
import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilemap_parser.parser.collision import CollisionPolygon
from tilemap_parser.runtime.map_loader import TilemapData
from tilemap_parser.runtime.map_object import MapObject, load_map_objects
from tilemap_parser.runtime.object_collision import ObjectCollisionManager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_MAP_META = {
    "tile_size": "16;16",
    "map_size": "10;10",
    "version": "1.1",
}


def _make_minimal_png(path: Path, size: tuple[int, int] = (32, 16)) -> None:
    surf = pygame.Surface(size)
    surf.fill((255, 0, 255))
    pygame.image.save(surf, str(path))


def _make_collision_json(collision_dir: Path, tileset_stem: str, region_id: str) -> Path:
    """Create a minimal object collision JSON with one rectangular region."""
    collision_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "tileset_name": tileset_stem,
        "regions": {
            region_id: {
                "region_id": region_id,
                "region_rect": [0, 0, 16, 16],
                "name": "Test Region",
                "shapes": [
                    {
                        "type": "polygon",
                        "vertices": [[0, 0], [16, 0], [16, 16], [0, 16]],
                        "one_way": False,
                    }
                ],
                "properties": {},
            },
        },
    }
    path = collision_dir / f"{tileset_stem}.object_collision.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


def _make_map_json_with_objects(
    tileset_path: str,
    data_dir: Path,
    *,
    region_id: str | None = None,
) -> Path:
    """Create a map JSON with a single object layer containing one object."""
    props = {}
    if region_id is not None:
        props["region_id"] = region_id

    payload = {
        "meta": {**MINIMAL_MAP_META},
        "resources": {"tilesets": [{"path": tileset_path, "type": "object"}]},
        "project_state": {"rules": [], "groups": []},
        "data": {
            "ongrid": {},
            "layers": [
                {
                    "name": "Object Layer",
                    "type": "object",
                    "visible": True,
                    "locked": False,
                    "opacity": 1.0,
                    "z_index": 0,
                    "properties": {},
                    "tiles": {},
                    "objects": {
                        "1": {
                            "area": {"x": 100, "y": 200, "w": 16, "h": 16},
                            "ttype": 0,
                            "tileset_type": "object",
                            "variant": 0,
                            "properties": props,
                        },
                    },
                    "next_object_id": 2,
                },
            ],
        },
    }
    map_path = data_dir / "test_map.json"
    with open(map_path, "w") as f:
        json.dump(payload, f, indent=2)
    return map_path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def basic_map():
    """Create a map with one object and a matching collision file."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        assets_dir = tmp / "assets"
        data_dir = tmp / "data"
        collision_dir = tmp / "data" / "collision"
        assets_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)

        png = assets_dir / "tileset.png"
        _make_minimal_png(png, (32, 16))

        _make_collision_json(collision_dir, "tileset", "region_1")
        map_path = _make_map_json_with_objects("../assets/tileset.png", data_dir)
        td = TilemapData.load(map_path)
        yield td, collision_dir, png


@pytest.fixture
def map_multi_shape():
    """Map with one object that has a region containing three disjoint polygons."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        assets_dir = tmp / "assets"
        data_dir = tmp / "data"
        collision_dir = tmp / "data" / "collision"
        assets_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)

        png = assets_dir / "tileset.png"
        _make_minimal_png(png, (32, 16))

        collision_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "tileset_name": "tileset",
            "regions": {
                "region_1": {
                    "region_id": "region_1",
                    "region_rect": [0, 0, 32, 32],
                    "name": "Multi-Shape Region",
                    "shapes": [
                        {
                            "type": "polygon",
                            "vertices": [[0, 0], [10, 0], [10, 10], [0, 10]],
                            "one_way": False,
                        },
                        {
                            "type": "polygon",
                            "vertices": [[20, 0], [32, 0], [32, 10], [20, 10]],
                            "one_way": False,
                        },
                        {
                            "type": "polygon",
                            "vertices": [[0, 20], [10, 20], [10, 32], [0, 32]],
                            "one_way": False,
                        },
                    ],
                    "properties": {},
                },
            },
        }
        path = collision_dir / "tileset.object_collision.json"
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

        map_path = _make_map_json_with_objects("../assets/tileset.png", data_dir)
        td = TilemapData.load(map_path)
        yield td, collision_dir


@pytest.fixture
def map_no_collision_file():
    """Map with no corresponding collision file on disk."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        assets_dir = tmp / "assets"
        data_dir = tmp / "data"
        collision_dir = tmp / "data" / "collision"
        assets_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        collision_dir.mkdir(parents=True)

        png = assets_dir / "tileset.png"
        _make_minimal_png(png, (32, 16))

        # Don't create any collision file
        map_path = _make_map_json_with_objects("../assets/tileset.png", data_dir)
        td = TilemapData.load(map_path)
        yield td, collision_dir


@pytest.fixture
def map_multiple_objects():
    """Map with two objects referencing the same collision region."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        assets_dir = tmp / "assets"
        data_dir = tmp / "data"
        collision_dir = tmp / "data" / "collision"
        assets_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)

        png = assets_dir / "tileset.png"
        _make_minimal_png(png, (32, 32))

        _make_collision_json(collision_dir, "tileset", "region_1")

        payload = {
            "meta": {**MINIMAL_MAP_META},
            "resources": {"tilesets": [{"path": "../assets/tileset.png", "type": "object"}]},
            "project_state": {"rules": [], "groups": []},
            "data": {
                "ongrid": {},
                "layers": [
                    {
                        "name": "Object Layer",
                        "type": "object",
                        "visible": True,
                        "locked": False,
                        "opacity": 1.0,
                        "z_index": 0,
                        "properties": {},
                        "tiles": {},
                        "objects": {
                            "1": {
                                "area": {"x": 100, "y": 200, "w": 16, "h": 16},
                                "ttype": 0,
                                "tileset_type": "object",
                                "variant": 0,
                            "properties": {},
                        },
                        "2": {
                            "area": {"x": 300, "y": 400, "w": 16, "h": 16},
                            "ttype": 0,
                            "tileset_type": "object",
                            "variant": 1,
                            "properties": {},
                            },
                        },
                        "next_object_id": 3,
                    },
                ],
            },
        }
        map_path = data_dir / "test_map.json"
        with open(map_path, "w") as f:
            json.dump(payload, f, indent=2)
        td = TilemapData.load(map_path)
        yield td, collision_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMapObject:
    def test_map_object_has_required_fields(self):
        """MapObject satisfies ICollidableObject protocol."""
        surf = pygame.Surface((16, 16))
        shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
        obj = MapObject(x=10, y=20, surface=surf, collision_shape=shape)
        assert obj.x == 10
        assert obj.y == 20
        assert obj.surface is surf
        assert obj.collision_shape is shape
        assert obj.collision_shapes == [shape]
        assert obj.collision_layer == 1
        assert obj.collision_mask == 0xFFFFFFFF

    def test_map_object_custom_layer_and_mask(self):
        surf = pygame.Surface((16, 16))
        shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
        obj = MapObject(x=0, y=0, surface=surf, collision_shape=shape, collision_layer=2, collision_mask=4)
        assert obj.collision_layer == 2
        assert obj.collision_mask == 4

    def test_map_object_can_be_added_to_collision_manager(self):
        """MapObject works with ObjectCollisionManager via ICollidableObject."""
        surf = pygame.Surface((16, 16))
        shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
        obj = MapObject(x=0, y=0, surface=surf, collision_shape=shape)

        mgr = ObjectCollisionManager()
        mgr.add_object(obj)
        assert obj in mgr
        assert len(mgr) == 1


class TestLoadMapObjects:
    def test_basic_load(self, basic_map):
        td, collision_dir, _ = basic_map
        objects = load_map_objects(td, collision_dir)
        assert len(objects) == 1

        obj = objects[0]
        assert isinstance(obj, MapObject)
        assert isinstance(obj.surface, pygame.Surface)
        assert isinstance(obj.collision_shape, CollisionPolygon)
        assert obj.x == 100
        assert obj.y == 200
        assert obj.collision_layer == 1
        assert obj.collision_mask == 0xFFFFFFFF

    def test_object_surface_size(self, basic_map):
        td, collision_dir, _ = basic_map
        objects = load_map_objects(td, collision_dir)
        obj = objects[0]
        # Tileset is 32x16 with tile_size 16x16 → variant 0 at (0,0) → 16x16
        assert obj.surface.get_size() == (16, 16)

    def test_collision_shape_vertices(self, basic_map):
        td, collision_dir, _ = basic_map
        objects = load_map_objects(td, collision_dir)
        obj = objects[0]
        # region_rect is [0, 0, 16, 16]; vertices are owner-local
        # narrowphase applies obj.x (100) + obj.y (200) to get world space
        verts = obj.collision_shape.vertices
        assert len(verts) == 4
        assert verts[0] == (0, 0)
        assert verts[1] == (16, 0)
        assert verts[2] == (16, 16)
        assert verts[3] == (0, 16)

    def test_multiple_objects(self, map_multiple_objects):
        td, collision_dir = map_multiple_objects
        objects = load_map_objects(td, collision_dir)
        assert len(objects) == 2

        obj0, obj1 = objects
        assert obj0.x == 100
        assert obj0.y == 200
        assert obj1.x == 300
        assert obj1.y == 400

    def test_multiple_objects_distinct_surfaces(self, map_multiple_objects):
        td, collision_dir = map_multiple_objects
        objects = load_map_objects(td, collision_dir)
        assert objects[0].surface is not objects[1].surface

    def test_missing_collision_file(self, map_no_collision_file):
        td, collision_dir = map_no_collision_file
        objects = load_map_objects(td, collision_dir)
        assert objects == []

    def test_no_object_layers(self):
        """Map with no object layers at all returns empty list."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assets_dir = tmp / "assets"
            data_dir = tmp / "data"
            assets_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)

            png = assets_dir / "tileset.png"
            _make_minimal_png(png)

            payload = {
                "meta": {**MINIMAL_MAP_META},
                "resources": {"tilesets": [{"path": "../assets/tileset.png", "type": "tile"}]},
                "project_state": {"rules": [], "groups": []},
                "data": {
                    "ongrid": {},
                    "layers": [
                        {
                            "name": "Tile Layer",
                            "type": "tile",
                            "visible": True,
                            "locked": False,
                            "opacity": 1.0,
                            "z_index": 0,
                            "properties": {},
                            "tiles": {},
                            "objects": {},
                        },
                    ],
                },
            }
            map_path = data_dir / "test_map.json"
            with open(map_path, "w") as f:
                json.dump(payload, f, indent=2)
            td = TilemapData.load(map_path)
            objects = load_map_objects(td, data_dir / "collision")
            assert objects == []

    def test_collision_per_tileset_cached(self, map_multiple_objects, monkeypatch):
        """Collision data is cached per tileset index — not reloaded for each object."""
        td, collision_dir = map_multiple_objects
        call_count = 0

        def tracking_load(path):
            nonlocal call_count
            call_count += 1
            from tilemap_parser.parser.collision_loader import load_object_collision
            return load_object_collision(path)

        monkeypatch.setattr(
            "tilemap_parser.runtime.map_object.load_object_collision",
            tracking_load,
        )
        objects = load_map_objects(td, collision_dir)
        assert len(objects) == 2
        # Both objects share the same tileset (index 0); the collision
        # file should be loaded exactly once.
        assert call_count == 1

    def test_with_collision_cache(self, basic_map, monkeypatch):
        """CollisionCache prevents redundant file loads across calls."""
        from tilemap_parser.runtime.collision_cache import CollisionCache

        td, collision_dir, _ = basic_map
        call_count = 0

        def tracking_load(path):
            nonlocal call_count
            call_count += 1
            from tilemap_parser.parser.collision_loader import load_object_collision
            return load_object_collision(path)

        # CollisionCache.get_object_collision calls its own module-level
        # load_object_collision; patch at the cache module.
        monkeypatch.setattr(
            "tilemap_parser.runtime.collision_cache.load_object_collision",
            tracking_load,
        )

        cache = CollisionCache()
        objects1 = load_map_objects(td, collision_dir, cache=cache)
        assert len(objects1) == 1
        assert call_count == 1

        objects2 = load_map_objects(td, collision_dir, cache=cache)
        assert len(objects2) == 1
        # Second call should hit cache — no additional file load.
        assert call_count == 1

    def test_multi_shape_region(self, map_multi_shape):
        """A region with N disjoint polygons stores all shapes in collision_shapes."""
        td, collision_dir = map_multi_shape
        objects = load_map_objects(td, collision_dir)
        assert len(objects) == 1

        obj = objects[0]
        assert isinstance(obj, MapObject)
        assert isinstance(obj.surface, pygame.Surface)
        assert obj.x == 100
        assert obj.y == 200
        assert obj.collision_layer == 1

        # All three shapes preserved
        assert len(obj.collision_shapes) == 3

        # First shape is also collision_shape (protocol compat)
        assert obj.collision_shape is obj.collision_shapes[0]

        # Each shape is a distinct polygon
        assert obj.collision_shapes[0] is not obj.collision_shapes[1]
        assert obj.collision_shapes[1] is not obj.collision_shapes[2]

        # Verify each has different vertices
        verts = [s.vertices for s in obj.collision_shapes]
        assert len(set(tuple(v[0]) for v in verts)) == 3

    def test_all_regions_applied(self):
        """Multiple collision regions: each contributes its shapes to the object."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assets_dir = tmp / "assets"
            data_dir = tmp / "data"
            collision_dir = tmp / "data" / "collision"
            assets_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            collision_dir.mkdir(parents=True)

            png = assets_dir / "tileset.png"
            _make_minimal_png(png, (32, 32))

            # 3 separate regions, each with 1 shape
            payload = {
                "tileset_name": "tileset",
                "regions": {
                    "region_top": {
                        "region_id": "region_top",
                        "region_rect": [0, 0, 32, 16],
                        "name": "Top",
                        "shapes": [{"type": "polygon", "vertices": [[0, 0], [32, 0], [32, 16], [0, 16]], "one_way": False}],
                        "properties": {},
                    },
                    "region_bot": {
                        "region_id": "region_bot",
                        "region_rect": [0, 16, 32, 16],
                        "name": "Bottom",
                        "shapes": [{"type": "polygon", "vertices": [[0, 0], [32, 0], [32, 16], [0, 16]], "one_way": False}],
                        "properties": {},
                    },
                    "region_extra": {
                        "region_id": "region_extra",
                        "region_rect": [0, 0, 16, 32],
                        "name": "Extra",
                        "shapes": [{"type": "polygon", "vertices": [[0, 0], [16, 0], [16, 32], [0, 32]], "one_way": False}],
                        "properties": {},
                    },
                },
            }
            coll_path = collision_dir / "tileset.object_collision.json"
            with open(coll_path, "w") as f:
                json.dump(payload, f, indent=2)

            map_path = _make_map_json_with_objects("../assets/tileset.png", data_dir)
            td = TilemapData.load(map_path)
            objects = load_map_objects(td, collision_dir)

            assert len(objects) == 1
            obj = objects[0]
            # 3 regions × 1 shape each → 3 collision_shapes
            assert len(obj.collision_shapes) == 3
            assert obj.collision_shape is obj.collision_shapes[0]
            assert obj.collision_shapes[0] is not obj.collision_shapes[1]
            assert obj.collision_shapes[1] is not obj.collision_shapes[2]

    def test_multi_shape_collision(self):
        """Two multi-shape objects collide when any of their shapes overlap."""
        surf = pygame.Surface((16, 16))
        # shape_a: 0-10, 0-10
        shape_a = CollisionPolygon(vertices=[(0, 0), (10, 0), (10, 10), (0, 10)])
        # shape_b: 20-30, 0-10  
        shape_b = CollisionPolygon(vertices=[(20, 0), (30, 0), (30, 10), (20, 10)])

        obj1 = MapObject(x=0, y=0, surface=surf, collision_shape=shape_a, collision_shapes=[shape_a, shape_b])
        # Second object with one shape at (25,0)-(35,0)-(35,10)-(25,10)
        # Overlaps with obj1's shape_b (20,0)-(30,0)-(30,10)-(20,10)
        shape_c = CollisionPolygon(vertices=[(0, 0), (10, 0), (10, 10), (0, 10)])
        obj2 = MapObject(x=25, y=0, surface=surf, collision_shape=shape_c)

        from tilemap_parser.runtime.object_collision import check_collision

        hit = check_collision(obj1, obj2)
        # obj1.shape_b (world 20,0-30,10) overlaps with obj2.shape_c (world 25,0-35,10)
        assert hit is not None, "expected shape_b-vs-shape_c overlap"
        assert hit.involves(obj1)
        assert hit.involves(obj2)

    def test_multi_shape_no_collision(self):
        """Two multi-shape objects with no overlapping shapes return None."""
        surf = pygame.Surface((16, 16))
        shape_a = CollisionPolygon(vertices=[(0, 0), (10, 0), (10, 10), (0, 10)])
        shape_b = CollisionPolygon(vertices=[(20, 0), (30, 0), (30, 10), (20, 10)])

        obj1 = MapObject(x=0, y=0, surface=surf, collision_shape=shape_a, collision_shapes=[shape_a, shape_b])
        obj2 = MapObject(x=100, y=100, surface=surf, collision_shape=shape_a)

        from tilemap_parser.runtime.object_collision import check_collision

        hit = check_collision(obj1, obj2)
        assert hit is None

    def test_objects_work_with_collision_manager(self, map_multi_shape):
        """Multi-shape loaded object + probe: exercises combined-AABB + narrowphase."""
        td, collision_dir = map_multi_shape
        objects = load_map_objects(td, collision_dir)
        assert len(objects) == 1
        loaded = objects[0]

        # Probe at (125, 205) — overlaps only shape[1] (world 120,200–132,210),
        # not shape[0] (100,200–110,210) nor shape[2] (100,220–110,232).
        probe_surf = pygame.Surface((10, 10))
        probe_shape = CollisionPolygon(vertices=[(0, 0), (10, 0), (10, 10), (0, 10)])
        probe = MapObject(x=125, y=205, surface=probe_surf, collision_shape=probe_shape)

        mgr = ObjectCollisionManager()
        mgr.add_object(loaded)
        mgr.add_object(probe)
        assert len(mgr) == 2

        hits = mgr.check_all_collisions()
        assert len(hits) == 1
        hit = hits[0]
        assert hit.involves(loaded)
        assert hit.involves(probe)

    def test_loaded_object_position_consistency(self):
        """Loaded MapObject vertices are owner-local; narrowphase applies obj.x/y once.

        Uses a non-zero region_rect offset to verify position is not double-applied.
        """
        from tilemap_parser.runtime.object_collision import check_collision

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assets_dir = tmp / "assets"
            data_dir = tmp / "data"
            collision_dir = tmp / "data" / "collision"
            assets_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            collision_dir.mkdir(parents=True)

            png = assets_dir / "tileset.png"
            _make_minimal_png(png, (48, 48))

            payload = {
                "tileset_name": "tileset",
                "regions": {
                    "region_r": {
                        "region_id": "region_r",
                        "region_rect": [5, 10, 16, 16],
                        "name": "R",
                        "shapes": [{"type": "polygon", "vertices": [[0, 0], [16, 0], [16, 16], [0, 16]], "one_way": False}],
                        "properties": {},
                    },
                },
            }
            coll_path = collision_dir / "tileset.object_collision.json"
            with open(coll_path, "w") as f:
                json.dump(payload, f, indent=2)

            map_path = _make_map_json_with_objects("../assets/tileset.png", data_dir)
            td = TilemapData.load(map_path)
            objects = load_map_objects(td, collision_dir)
            assert len(objects) == 1
            loaded = objects[0]

            # Manual object at the same world position the loaded object occupies
            # region_rect [5,10] + obj(100,200) → world origin at (105, 210)
            surf = pygame.Surface((16, 16))
            shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
            manual = MapObject(x=105, y=210, surface=surf, collision_shape=shape)

            # Same world AABB → must collide
            hit = check_collision(loaded, manual)
            assert hit is not None, "loaded and manual object at same world pos should collide"

    def test_invalid_tileset_index_skipped(self):
        """Object with ttype out of range is skipped."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assets_dir = tmp / "assets"
            data_dir = tmp / "data"
            collision_dir = tmp / "data" / "collision"
            assets_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)

            png = assets_dir / "tileset.png"
            _make_minimal_png(png)

            _make_collision_json(collision_dir, "tileset", "region_1")

            payload = {
                "meta": {**MINIMAL_MAP_META},
                "resources": {"tilesets": [{"path": "../assets/tileset.png", "type": "object"}]},
                "project_state": {"rules": [], "groups": []},
                "data": {
                    "ongrid": {},
                    "layers": [
                        {
                            "name": "Object Layer",
                            "type": "object",
                            "visible": True,
                            "locked": False,
                            "opacity": 1.0,
                            "z_index": 0,
                            "properties": {},
                            "tiles": {},
                            "objects": {
                                "1": {
                                    "area": {"x": 0, "y": 0, "w": 16, "h": 16},
                                    "ttype": 999,
                                    "tileset_type": "object",
                                    "variant": 0,
                                    "properties": {},
                                },
                            },
                            "next_object_id": 2,
                        },
                    ],
                },
            }
            map_path = data_dir / "test_map.json"
            with open(map_path, "w") as f:
                json.dump(payload, f, indent=2)
            td = TilemapData.load(map_path)
            objects = load_map_objects(td, collision_dir)
            assert objects == []


