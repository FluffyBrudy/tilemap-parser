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

    def test_default_scale_no_op(self, basic_map):
        """render_scale=1.0 (default) behaves identically to before."""
        td, collision_dir, _ = basic_map
        assert td.render_scale == 1.0
        objects = load_map_objects(td, collision_dir)
        assert len(objects) == 1
        obj = objects[0]
        # Positions are raw (no scaling)
        assert obj.x == 100
        assert obj.y == 200
        # Vertices are raw
        verts = obj.collision_shape.vertices
        assert verts[0] == (0, 0)
        assert verts[1] == (16, 0)
        assert verts[2] == (16, 16)
        assert verts[3] == (0, 16)

    def test_render_scale_3x(self):
        """render_scale=3.0 scales positions and polygon vertices."""
        from tilemap_parser.runtime.map_object import load_map_objects
        from tilemap_parser.runtime.map_loader import TilemapData

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

            collision_payload = {
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
                json.dump(collision_payload, f, indent=2)

            # Map with render_scale=3.0
            payload = {
                "meta": {
                    "tile_size": "16;16",
                    "map_size": "10;10",
                    "version": "1.1",
                    "render_scale": 3.0,
                },
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
            assert td.render_scale == 3.0
            objects = load_map_objects(td, collision_dir)
            assert len(objects) == 1
            obj = objects[0]

            # Position scaled by 3x
            assert obj.x == 300  # 100 * 3
            assert obj.y == 600  # 200 * 3

            # region_rect [5, 10] scaled by 3x → ox=15, oy=30
            # Vertices scaled by 3x: (0,0)→(0,0), (16,0)→(48,0), (16,16)→(48,48), (0,16)→(0,48)
            # World = ox + vx*rs: (15+0, 30+0) = (15, 30)
            #                     (15+48, 30+0) = (63, 30)
            #                     (15+48, 30+48) = (63, 78)
            #                     (15+0, 30+48) = (15, 78)
            verts = obj.collision_shape.vertices
            assert len(verts) == 4
            assert verts[0] == pytest.approx((15.0, 30.0))
            assert verts[1] == pytest.approx((63.0, 30.0))
            assert verts[2] == pytest.approx((63.0, 78.0))
            assert verts[3] == pytest.approx((15.0, 78.0))

            # Surface scaled by 3x: tileset is 32×16, variant 0 is 16×16
            assert obj.surface.get_size() == (48, 48)  # 16*3, 16*3

    def test_render_scale_surface_scaled(self):
        """Surface is scaled by render_scale in load_map_objects."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assets_dir = tmp / "assets"
            data_dir = tmp / "data"
            collision_dir = tmp / "data" / "collision"
            assets_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            collision_dir.mkdir(parents=True)

            png = assets_dir / "tileset.png"
            # Create a 64×32 tileset with 2 variants (16×16 each)
            surf = pygame.Surface((64, 32))
            surf.fill((255, 0, 255))
            pygame.image.save(surf, str(png))

            collision_payload = {
                "tileset_name": "tileset",
                "regions": {
                    "region_r": {
                        "region_id": "region_r",
                        "region_rect": [0, 0, 16, 16],
                        "name": "R",
                        "shapes": [{"type": "polygon", "vertices": [[0, 0], [16, 0], [16, 16], [0, 16]], "one_way": False}],
                        "properties": {},
                    },
                },
            }
            coll_path = collision_dir / "tileset.object_collision.json"
            with open(coll_path, "w") as f:
                json.dump(collision_payload, f, indent=2)

            for rs_val, expected_w, expected_h in [(1.0, 16, 16), (2.0, 32, 32), (3.0, 48, 48), (1.5, 24, 24)]:
                payload = {
                    "meta": {
                        "tile_size": "16;16",
                        "map_size": "10;10",
                        "version": "1.1",
                        "render_scale": rs_val,
                    },
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
                                        "area": {"x": 10, "y": 20, "w": 16, "h": 16},
                                        "ttype": 0,
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
                assert len(objects) == 1
                obj = objects[0]
                assert obj.surface.get_size() == (expected_w, expected_h), \
                    f"rs={rs_val}: expected ({expected_w},{expected_h}) got {obj.surface.get_size()}"
                assert obj.x == 10 * rs_val, f"rs={rs_val}: x={obj.x} != {10 * rs_val}"
                assert obj.y == 20 * rs_val, f"rs={rs_val}: y={obj.y} != {20 * rs_val}"

            # Fractional rs with odd dimensions to exercise surface truncation
            odd_png = assets_dir / "odd_tileset.png"
            odd_surf = pygame.Surface((17, 35))
            odd_surf.fill((0, 255, 0))
            pygame.image.save(odd_surf, str(odd_png))

            odd_collision = {
                "tileset_name": "odd_tileset",
                "regions": {
                    "region_r": {
                        "region_id": "region_r",
                        "region_rect": [0, 0, 17, 35],
                        "name": "R",
                        "shapes": [{"type": "polygon", "vertices": [[0, 0], [17, 0], [17, 35], [0, 35]], "one_way": False}],
                        "properties": {},
                    },
                },
            }
            odd_coll_path = collision_dir / "odd_tileset.object_collision.json"
            with open(odd_coll_path, "w") as f:
                json.dump(odd_collision, f, indent=2)

            payload_odd = {
                "meta": {
                    "tile_size": "16;16",
                    "map_size": "10;10",
                    "version": "1.1",
                    "render_scale": 1.5,
                },
                "resources": {"tilesets": [{"path": "../assets/odd_tileset.png", "type": "object"}]},
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
                                    "area": {"x": 11, "y": 21, "w": 17, "h": 35},
                                    "ttype": 0,
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
            odd_map_path = data_dir / "odd_test_map.json"
            with open(odd_map_path, "w") as f:
                json.dump(payload_odd, f, indent=2)

            td_odd = TilemapData.load(odd_map_path)
            objects_odd = load_map_objects(td_odd, collision_dir)
            assert len(objects_odd) == 1
            obj = objects_odd[0]
            assert obj.x == 11 * 1.5, f"fractional x: {obj.x} != {11 * 1.5}"
            assert obj.y == 21 * 1.5, f"fractional y: {obj.y} != {21 * 1.5}"
            assert obj.surface.get_size() == (25, 52), \
                f"truncated surface: {obj.surface.get_size()} != (25, 52)  [int(17*1.5)=25, int(35*1.5)=52]"

    def test_render_scale_collision_consistency(self):
        """At render_scale=3.0, a loaded object collides with a manually-placed
        probe object if and only if they overlap in effective (scaled) space."""
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

            # Collision region at (0,0) with a 16x16 square polygon
            collision_payload = {
                "tileset_name": "tileset",
                "regions": {
                    "region_r": {
                        "region_id": "region_r",
                        "region_rect": [0, 0, 16, 16],
                        "name": "R",
                        "shapes": [{"type": "polygon", "vertices": [[0, 0], [16, 0], [16, 16], [0, 16]], "one_way": False}],
                        "properties": {},
                    },
                },
            }
            coll_path = collision_dir / "tileset.object_collision.json"
            with open(coll_path, "w") as f:
                json.dump(collision_payload, f, indent=2)

            payload = {
                "meta": {
                    "tile_size": "16;16",
                    "map_size": "10;10",
                    "version": "1.1",
                    "render_scale": 3.0,
                },
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
            assert len(objects) == 1
            loaded = objects[0]

            # Loaded object position = (300, 600) in effective space
            # Collision polygon covers (300, 600) to (300+48, 600+48) = (348, 648)
            assert loaded.x == 300
            assert loaded.y == 600

            # Probe at (310, 610) with a 16x16 rect in effective space must collide
            probe_surf = pygame.Surface((16, 16))
            probe_shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
            probe = MapObject(x=310, y=610, surface=probe_surf, collision_shape=probe_shape)

            from tilemap_parser.runtime.object_collision import check_collision

            hit = check_collision(loaded, probe)
            assert hit is not None, "expected collision in effective space"

            # Probe far away must NOT collide
            probe_far = MapObject(x=1000, y=1000, surface=probe_surf, collision_shape=probe_shape)
            hit_far = check_collision(loaded, probe_far)
            assert hit_far is None, "no collision expected for far probe"

    def test_render_scale_region_offset_scaled(self):
        """Non-zero region_rect offset is scaled by render_scale."""
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

            # region_rect offset of (5,10), polygon at origin within that region
            collision_payload = {
                "tileset_name": "tileset",
                "regions": {
                    "region_r": {
                        "region_id": "region_r",
                        "region_rect": [5, 10, 16, 16],
                        "name": "R",
                        "shapes": [{"type": "polygon", "vertices": [[0, 0], [8, 0], [8, 8], [0, 8]], "one_way": False}],
                        "properties": {},
                    },
                },
            }
            coll_path = collision_dir / "tileset.object_collision.json"
            with open(coll_path, "w") as f:
                json.dump(collision_payload, f, indent=2)

            payload = {
                "meta": {
                    "tile_size": "16;16",
                    "map_size": "10;10",
                    "version": "1.1",
                    "render_scale": 3.0,
                },
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
            assert len(objects) == 1
            obj = objects[0]

            # Position scaled: (300, 600)
            # region_rect offset scaled: ox=15, oy=30
            # Vertices scaled: (0,0)→(0,0), (8,0)→(24,0), (8,8)→(24,24), (0,8)→(0,24)
            # World: (15, 30), (39, 30), (39, 54), (15, 54)
            verts = obj.collision_shape.vertices
            assert verts[0] == pytest.approx((15.0, 30.0))
            assert verts[1] == pytest.approx((39.0, 30.0))
            assert verts[2] == pytest.approx((39.0, 54.0))
            assert verts[3] == pytest.approx((15.0, 54.0))

            # Probe at object center must collide
            probe_surf = pygame.Surface((16, 16))
            probe_shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
            # Loaded world AABB: (300+15, 600+30) to (300+39, 600+54) = (315, 630) to (339, 654)
            probe = MapObject(x=315, y=630, surface=probe_surf, collision_shape=probe_shape)

            from tilemap_parser.runtime.object_collision import check_collision

            hit = check_collision(obj, probe)
            assert hit is not None, "expected collision with region offset"

    def test_render_scale_visual_collision_alignment(self):
        """At render_scale=N, collision AABB is fully inside visual rect
        and vertex positions are pixel-accurate for known values."""
        from tilemap_parser.runtime.map_object import load_map_objects
        from tilemap_parser.runtime.map_loader import TilemapData

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            assets_dir = tmp / "assets"
            data_dir = tmp / "data"
            collision_dir = tmp / "data" / "collision"
            assets_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            collision_dir.mkdir(parents=True)

            # Tileset: 64x96 with a known shape
            tileset_surf = pygame.Surface((64, 96))
            tileset_surf.fill((0, 255, 0))
            png = assets_dir / "tree.png"
            pygame.image.save(tileset_surf, str(png))

            # Collision: region_rect=[0,3,64,93] with polygon
            collision_payload = {
                "tileset_name": "tree",
                "regions": {
                    "region_r": {
                        "region_id": "region_r",
                        "region_rect": [0, 3, 64, 93],
                        "name": "R",
                        "shapes": [
                            {
                                "type": "polygon",
                                "vertices": [[32.0, 2.75], [8.0, 30.0], [10.5, 58.75],
                                             [22.5, 65.25], [20.0, 88.25], [33.5, 81.75],
                                             [47.5, 87.75], [41.5, 65.75], [58.5, 48.75],
                                             [52.0, 25.0]],
                                "one_way": False,
                            }
                        ],
                        "properties": {"collision_layer": 1, "collision_mask": 65535},
                    },
                },
            }
            coll_path = collision_dir / "tree.object_collision.json"
            with open(coll_path, "w") as f:
                json.dump(collision_payload, f, indent=2)

            for rs_val in [1.0, 2.0, 3.0, 4.0]:
                payload = {
                    "meta": {
                        "tile_size": "16;16",
                        "map_size": "10;10",
                        "version": "1.1",
                        "render_scale": rs_val,
                    },
                    "resources": {"tilesets": [{"path": "../assets/tree.png", "type": "object"}]},
                    "project_state": {"rules": [], "groups": []},
                    "data": {
                        "ongrid": {},
                        "layers": [
                            {
                                "name": "Objects",
                                "type": "object",
                                "visible": True,
                                "locked": False,
                                "opacity": 1.0,
                                "z_index": 0,
                                "properties": {},
                                "tiles": {},
                                "objects": {
                                    "1": {
                                        "area": {"x": 27, "y": 82, "w": 64, "h": 96},
                                        "ttype": 0,
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
                assert len(objects) == 1, f"rs={rs_val}: expected 1 object"
                obj = objects[0]

                # Verify surface size is pixel-accurate at integer render_scale
                expected_w = int(64 * rs_val)
                expected_h = int(96 * rs_val)
                assert obj.surface.get_size() == (expected_w, expected_h), \
                    f"rs={rs_val}: surface {obj.surface.get_size()} != ({expected_w},{expected_h})"

                # Verify position is pixel-accurate (float)
                assert obj.x == 27 * rs_val, f"rs={rs_val}: x={obj.x} != {27 * rs_val}"
                assert obj.y == 82 * rs_val, f"rs={rs_val}: y={obj.y} != {82 * rs_val}"

                # Verify every collision vertex is pixel-accurate for known values
                shape = obj.collision_shapes[0]
                # First vertex: (32.0, 2.75) + region_rect (0, 3) = world (32*rs, (3+2.75)*rs)
                expected_v0 = (32.0 * rs_val, (3.0 + 2.75) * rs_val)
                actual_v0 = shape.vertices[0]
                assert abs(actual_v0[0] - expected_v0[0]) < 0.001, \
                    f"rs={rs_val}: vertex[0].x {actual_v0[0]} != {expected_v0[0]}"
                assert abs(actual_v0[1] - expected_v0[1]) < 0.001, \
                    f"rs={rs_val}: vertex[0].y {actual_v0[1]} != {expected_v0[1]}"

                # Verify collision AABB is inside visual rect
                xs = [v[0] for v in shape.vertices]
                ys = [v[1] for v in shape.vertices]
                coll_min_x = obj.x + min(xs)
                coll_max_x = obj.x + max(xs)
                coll_min_y = obj.y + min(ys)
                coll_max_y = obj.y + max(ys)

                vis_left = obj.x
                vis_top = obj.y
                vis_right = obj.x + expected_w
                vis_bottom = obj.y + expected_h

                margin = -0.001  # allow 0px floating point tolerance
                assert coll_min_x >= vis_left + margin, \
                    f"rs={rs_val}: collision left {coll_min_x} < visual left {vis_left}"
                assert coll_min_y >= vis_top + margin, \
                    f"rs={rs_val}: collision top {coll_min_y} < visual top {vis_top}"
                assert coll_max_x <= vis_right - margin, \
                    f"rs={rs_val}: collision right {coll_max_x} > visual right {vis_right}"
                assert coll_max_y <= vis_bottom - margin, \
                    f"rs={rs_val}: collision bottom {coll_max_y} > visual bottom {vis_bottom}"

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


