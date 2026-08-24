"""GID range-routing tests: single grid collision file, multi-tileset maps.

Regression ground: with ``use_gids=True`` and a collision file whose
``firstgid != 0``, literal lookups silently missed (e.g. only 1 of many
collidable tiles resolved).  Naive per-lookup offset subtraction also aliases:
a decoration grid whose GID window lands inside the owner's *local*
key space (e.g. gid ``1813 - 90 = 1723``) would become falsely solid
the moment the owner gains that local key.

Routing must therefore resolve ownership against the map's grid
resource table BEFORE translating.
"""

import json
from pathlib import Path

import pytest

from tilemap_parser.parser.collision import (
    CollisionPolygon,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.navigation.nav_grid import NavGrid
from tilemap_parser.runtime.world import PhysicsWorld

# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------

def solid(x=8.0, y=8.0):
    return CollisionPolygon(vertices=[(0, 0), (x, 0), (x, y), (0, y)])


def make_col(name: str, keys: dict[int, list]) -> TilesetCollision:
    return TilesetCollision(
        tileset_name=name,
        tile_size=(8, 8),
        tiles={k: TileCollisionData(tile_id=k, shapes=v) for k, v in keys.items()},
    )


def stamp(world: PhysicsWorld, ranges, owner_stem: str | None) -> None:
    """Simulate what from_map captures from map_data.parsed.tilesets."""
    world._grid_ranges = list(ranges)
    world._collision_owner_stem = owner_stem



RANGES = [
    (0, 90, "cave"),          # decoration grid
    (90, 1750, "tileset"),    # collision owner
    (1840, 56, "cave_hole"),  # decoration grid
    (1896, 1296, "bg"),       # decoration grid
]
COL_KEYS = {1: [solid()], 2: [solid()], 575: [solid()], 981: [solid()]}


@pytest.fixture()
def routed_world() -> PhysicsWorld:
    w = PhysicsWorld(
        tile_map={(0, 6): 92, (3, 6): 1813},
        tileset_collision=make_col("tileset", COL_KEYS),
        tile_size=(8, 8),
        render_scale=3.0,
    )
    stamp(w, RANGES, "tileset")
    return w


class TestRoutingMatrix:
    def test_owner_gid_translates_to_local(self, routed_world):
        assert routed_world.resolve_collision(92) is not None      # local 2
        assert routed_world.has_collision_gid(92) is True

    def test_decoration_grid_never_solids__alias_regression(self, routed_world):
        # gid 1813 belongs to cave_hole; naive `gid-90` would hit local 1723.
        assert routed_world.resolve_collision(1813) is None
        assert routed_world.has_collision_gid(1813) is False

    def test_other_owner_windows_rejected(self, routed_world):
        assert routed_world.resolve_collision(5) is None           # cave window
        assert routed_world.resolve_collision(1900) is None        # bg window
        assert routed_world.resolve_collision(1840 + 4) is None    # hole window

    def test_unmapped_gap_is_none(self, routed_world):
        # 90+1750+56+1296 == 3192: first id past every grid window
        assert routed_world.resolve_collision(3192) is None
        assert routed_world.resolve_collision(5000) is None

    def test_owner_local_keys_without_collision_shapes(self, routed_world):
        # owner-local 50 exists as a gid but has no entry -> None, not crash
        assert routed_world.resolve_collision(90 + 50) is None

    def test_boundary_edges(self, routed_world):
        assert routed_world.resolve_collision(89) is None           # last cave gid
        # inclusive owner lower edge: local 0 exists in the window but has no
        # collision entry -> None (must not fall through to another range)
        assert routed_world.resolve_collision(90) is None
        assert routed_world.resolve_collision(90 + 1749) is None    # last owner gid, keyless


class TestLiteralFallback:
    def test_no_routing_keeps_literal_lookup(self):
        w = PhysicsWorld(
            tile_map={(0, 0): 2},
            tileset_collision=make_col("tileset", COL_KEYS),
            tile_size=(8, 8),
        )
        assert w._grid_ranges == []
        assert w.resolve_collision(2) is not None
        assert w.has_collision_gid(2) is True

    def test_merged_gid_keyed_file_stays_literal(self):
        # merge() output: keys ARE gids, no stem match possible
        merged = make_col("merged", {92: [solid()]})
        w = PhysicsWorld(
            tile_map={(0, 6): 92}, tileset_collision=merged, tile_size=(8, 8)
        )
        stamp(w, [], None)
        assert w.resolve_collision(92) is not None


class TestFromMapCapture:
    def _payload(self, tmp: Path):
        (tmp / "a.png").write_bytes(b"x")  # existence not required (skip_missing_images)
        (tmp / "b.png").write_bytes(b"x")
        return {
            "meta": {
                "tile_size": "8;8",
                "map_size": "4;4",
                "offset": "0;0",
                "render_scale": 1.0,
                "version": "1.1",
            },
            "resources": {
                "tilesets": [
                    {"path": str(tmp / "a.png"), "type": "tile", "tile_count": 4, "firstgid": 0},
                    {"path": str(tmp / "b.png"), "type": "tile", "tile_count": 4, "firstgid": 4},
                    {"path": str(tmp / "c.png"), "type": "object", "tile_count": 2, "firstgid": 8},
                ]
            },
            "project_state": {"rules": []},
            "data": {
                "layers": [
                    {
                        "name": "L", "type": "tile", "visible": True,
                        "tiles": {
                            "0;0": {"pos": "0;0", "ttype": 1, "variant": 0, "gid": 4},
                            "1;0": {"pos": "1;0", "ttype": 0, "variant": 1, "gid": 1},
                        },
                    }
                ]
            },
        }

    def test_from_map_auto_captures_owner_and_routes(self, tmp_path):
        from tilemap_parser.runtime.map_loader import load_map

        payload_path = tmp_path / "m.json"
        payload_path.write_text(json.dumps(self._payload(tmp_path)))

        map_data = load_map(payload_path)
        col = make_col("b", {0: [solid()]})  # local-keyed file for resource b

        world = PhysicsWorld.from_map(map_data, col, use_gids=True)

        # gid 4 -> owner b -> local 0 -> solid; gid 1 -> owner a -> decor
        assert world.has_collision_gid(4) is True
        assert world.has_collision_gid(1) is False
        # object resource c never participates even though its window follows
        assert world.resolve_collision(8) is None

    def test_from_map_literal_mode_untouched(self, tmp_path):
        from tilemap_parser.runtime.map_loader import load_map

        payload_path = tmp_path / "m.json"
        payload_path.write_text(json.dumps(self._payload(tmp_path)))
        map_data = load_map(payload_path)
        col = make_col("b", {0: [solid(), solid()]})

        world = PhysicsWorld.from_map(map_data, col, use_gids=False)
        assert world._grid_ranges == []
        assert world.resolve_collision(0) is not None  # literal local id


# ---------------------------------------------------------------------------
# NavGrid resolver propagation (copy / erode / for_entity)
# ---------------------------------------------------------------------------

class TestNavGridResolverPropagation:
    def _world(self):
        world = PhysicsWorld(
            tile_map={(0, 6): 92, (3, 6): 1813},
            tileset_collision=make_col("tileset", COL_KEYS),
            tile_size=(8, 8),
        )
        stamp(world, RANGES, "tileset")
        return world

    def test_copy_preserves_resolver_and_does_not_crash(self):
        w = self._world()
        base = NavGrid(w.tile_map, w.tileset_collision, w.tile_size, gid_resolver=w.resolve_collision)

        derived = base.copy()  # used to lack the slot entirely
        assert derived._gid_resolver is not None

        # is_one_way hits _resolve(): raised AttributeError on copies before
        derived.is_one_way(0, 6)
        # routed semantics survive the copy: owner solid, decoration not
        assert derived.is_solid(0, 6) is True    # gid 92 -> owner local 2
        assert derived.is_solid(3, 6) is False   # gid 1813 -> other grid resource

        eroded = base.erode(1.0)
        eroded.is_one_way(0, 6)
        assert eroded._gid_resolver is not None

    def test_literal_grid_unchanged_without_resolver(self):
        grid = NavGrid({(0, 0): 2}, make_col("t", COL_KEYS), (8, 8))
        assert grid.copy()._gid_resolver is None
        assert grid.is_solid(0, 0) is True       # literal local key 2
        grid.is_one_way(0, 0)                    # must not raise

    def test_cache_keys_separate_resolver_modes(self):
        w = self._world()
        cache: dict = {}

        literal = NavGrid.for_entity(
            w.tile_map, w.tileset_collision, w.tile_size,
            sprite_width=10.0, sprite_height=10.0, cache=cache,
        )
        routed = NavGrid.for_entity(
            w.tile_map, w.tileset_collision, w.tile_size,
            sprite_width=10.0, sprite_height=10.0, cache=cache,
            gid_resolver=w.resolve_collision,
        )

        assert len(cache) == 2, "modes must occupy distinct cache slots"
        assert literal is not routed
        assert literal._gid_resolver is None
        assert routed._gid_resolver is not None
        # same inputs, different semantics: owner tile solid only when routed
        assert literal.is_solid(0, 6) is False   # literal lookup of gid 92 misses
        assert routed.is_solid(0, 6) is True     # routed resolves to local 2

    def test_cache_reuses_entry_within_same_mode(self):
        w = self._world()
        cache: dict = {}
        a = NavGrid.for_entity(
            w.tile_map, w.tileset_collision, w.tile_size,
            sprite_width=16.0, cache=cache, gid_resolver=w.resolve_collision,
        )
        b = NavGrid.for_entity(
            w.tile_map, w.tileset_collision, w.tile_size,
            sprite_width=16.0, cache=cache, gid_resolver=w.resolve_collision,
        )
        assert a is b, "same margin + same mode must hit the cached grid"

        lit_a = NavGrid.for_entity(
            w.tile_map, w.tileset_collision, w.tile_size,
            sprite_width=16.0, cache=cache,
        )
        lit_b = NavGrid.for_entity(
            w.tile_map, w.tileset_collision, w.tile_size,
            sprite_width=16.0, cache=cache,
        )
        assert lit_a is lit_b and lit_a is not a
        assert len(cache) == 2

    def test_for_entity_forwards_resolver(self):
        w = self._world()
        grid = NavGrid.for_entity(
            w.tile_map,
            w.tileset_collision,
            w.tile_size,
            sprite_width=10.0,
            sprite_height=10.0,
            gid_resolver=w.resolve_collision,
        )
        assert grid._gid_resolver is not None
        # owner tile stays solid under entity clearance; decoration never was
        assert grid.is_solid(0, 6) is True
        assert grid.is_solid(3, 6) is False

        # parity: identical construction without a resolver would alias the
        # decoration gid into local 1723 (keyless today, so also False) --
        # assert via direct literal probe that routing, not luck, decides.
        literal = NavGrid.for_entity(
            w.tile_map, w.tileset_collision, w.tile_size, sprite_width=10.0
        )
        assert literal._gid_resolver is None
        assert literal.is_solid(0, 6) is False   # literal lookup of gid 92 misses
        assert grid.is_solid(0, 6) is True       # routed lookup resolves it
