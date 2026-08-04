"""Tests for Body + PhysicsWorld (the authoring surface)."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pygame
import pytest

from tilemap_parser.parser.collision import (
    CapsuleShape,
    CircleShape,
    CollisionPolygon,
    RectangleShape,
    TileCollisionData,
    TilesetCollision,
)
from tilemap_parser.runtime.body import Body
from tilemap_parser.runtime.collision import check_collision
from tilemap_parser.runtime.movement.runner import CollisionRunner
from tilemap_parser.runtime.world import PhysicsWorld


class Probe:
    """Minimal ICollidableObject stand-in."""

    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.collision_shape = shape


# ---------------------------------------------------------------------------
# Body construction
# ---------------------------------------------------------------------------


def test_body_accepts_primitives_only():
    poly = CollisionPolygon(vertices=[(0, 0), (10, 0), (10, 10)])
    with pytest.raises(TypeError, match="primitive shape"):
        Body(collision_shape=poly)


def test_body_rejects_unknown_mode():
    with pytest.raises(ValueError, match="mode"):
        Body(collision_shape=RectangleShape(width=10, height=10), mode="dynamic")


def test_body_defaults():
    body = Body(collision_shape=RectangleShape(width=32, height=32), x=5, y=6)
    assert body.x == 5
    assert body.y == 6
    assert body.vx == 0.0
    assert body.vy == 0.0
    assert body.mode == "static"
    assert body.collision_layer == 1
    assert body.collision_mask == 0xFFFFFFFF
    assert body.on_ground is False


# ---------------------------------------------------------------------------
# Body participates in collision detection (ICollidableObject contract)
# ---------------------------------------------------------------------------


def test_body_works_with_check_collision():
    body = Body(
        collision_shape=RectangleShape(width=32, height=32),
        x=100,
        y=200,
        collision_layer=3,
    )
    probe = Probe(110, 210, RectangleShape(width=8, height=8))

    hit = check_collision(body, probe)
    assert hit is not None
    assert hit.involves(body)
    assert hit.involves(probe)

    probe2 = Probe(500, 500, RectangleShape(width=8, height=8))
    assert check_collision(body, probe2) is None


def test_body_layer_filtering():
    body = Body(
        collision_shape=RectangleShape(width=32, height=32),
        x=100,
        y=200,
        collision_layer=2,
    )
    probe = Probe(110, 210, RectangleShape(width=8, height=8))
    probe.collision_mask = 0xFFFFFFFD  # all layers except layer 2
    assert check_collision(body, probe) is None

    probe.collision_mask = 0xFFFFFFFF
    assert check_collision(body, probe) is not None


# ---------------------------------------------------------------------------
# top_y_at
# ---------------------------------------------------------------------------


def test_top_y_at_rect():
    body = Body(
        collision_shape=RectangleShape(width=32, height=32),
        x=100,
        y=200,
    )
    assert body.top_y_at(100) == 200
    assert body.top_y_at(131) == 200
    assert body.top_y_at(132) == 200  # right edge inclusive
    assert body.top_y_at(133) is None
    assert body.top_y_at(99) is None


def test_top_y_at_rect_offset():
    body = Body(
        collision_shape=RectangleShape(width=32, height=32, offset=(4, 8)),
        x=100,
        y=200,
    )
    assert body.top_y_at(104) == 208
    assert body.top_y_at(135) == 208
    assert body.top_y_at(136) == 208  # right edge inclusive
    assert body.top_y_at(103) is None
    assert body.top_y_at(137) is None


def test_top_y_at_circle():
    body = Body(collision_shape=CircleShape(radius=10), x=100, y=200)
    assert body.top_y_at(100) == pytest.approx(190)  # apex
    assert body.top_y_at(110) == pytest.approx(200)  # right edge
    assert body.top_y_at(90) == pytest.approx(200)  # left edge
    assert body.top_y_at(111) is None
    # midpoint check: y = cy - sqrt(r^2 - dx^2)
    assert body.top_y_at(105) == pytest.approx(200 - math.sqrt(100 - 25))


def test_top_y_at_capsule():
    body = Body(collision_shape=CapsuleShape(radius=8, height=40), x=100, y=200)
    # top cap center at (100, 200); apex at 200 - 8
    assert body.top_y_at(100) == pytest.approx(192)
    assert body.top_y_at(108) == pytest.approx(200)
    assert body.top_y_at(92) == pytest.approx(200)
    assert body.top_y_at(109) is None


# ---------------------------------------------------------------------------
# as_polygon
# ---------------------------------------------------------------------------


def test_as_polygon_rect():
    body = Body(collision_shape=RectangleShape(width=32, height=16), x=100, y=200)
    poly = body.as_polygon()
    assert set(poly.vertices) == {
        (100, 200),
        (132, 200),
        (132, 216),
        (100, 216),
    }
    assert poly.one_way is False


def test_as_polygon_circle_bounds():
    body = Body(collision_shape=CircleShape(radius=10), x=100, y=200)
    poly = body.as_polygon()
    xs = [v[0] for v in poly.vertices]
    ys = [v[1] for v in poly.vertices]
    assert min(xs) == pytest.approx(90)
    assert max(xs) == pytest.approx(110)
    assert min(ys) == pytest.approx(190)
    assert max(ys) == pytest.approx(210)


def test_as_polygon_capsule_bounds():
    body = Body(collision_shape=CapsuleShape(radius=8, height=40), x=100, y=200)
    poly = body.as_polygon()
    xs = [v[0] for v in poly.vertices]
    ys = [v[1] for v in poly.vertices]
    assert min(xs) == pytest.approx(92)
    assert max(xs) == pytest.approx(108)
    assert min(ys) == pytest.approx(192)  # top cap apex
    assert max(ys) == pytest.approx(248)  # bottom cap apex: 200 + 40 + 8


# ---------------------------------------------------------------------------
# PhysicsWorld
# ---------------------------------------------------------------------------


def test_world_tile_map_defaults():
    world = PhysicsWorld()
    assert world.tile_map == {}
    assert world.tileset_collision is None
    assert world.bodies == []


def test_world_add_remove_duplicate():
    world = PhysicsWorld()
    body = Body(collision_shape=RectangleShape(width=10, height=10))
    world.add_body(body)
    world.add_body(body)  # idempotent
    assert len(world) == 1
    assert body in world

    world.remove_body(body)
    assert len(world) == 0

    with pytest.raises(ValueError, match="not in this world"):
        world.remove_body(body)


def test_world_clear_bodies():
    world = PhysicsWorld()
    world.add_body(Body(collision_shape=RectangleShape(width=10, height=10)))
    world.add_body(Body(collision_shape=CircleShape(radius=5)))
    world.clear_bodies()
    assert len(world) == 0

def test_world_from_map_builds_tile_layer():
    """from_map produces the same tile map the runner would get directly."""
    import json
    import tempfile

    from tilemap_parser.runtime.collision_cache import load_tileset_collision
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
        surf = pygame.Surface((32, 32))
        surf.fill((255, 0, 255))
        pygame.image.save(surf, str(png))

        collision_dir.joinpath("tileset.collision.json").write_text(
            json.dumps(
                {
                    "tileset_name": "tileset",
                    "tile_size": [16, 16],
                    "tiles": {
                        "1": {
                            "tile_id": 1,
                            "shapes": [
                                {
                                    "type": "polygon",
                                    "vertices": [[0.0, 0.0], [16.0, 0.0], [16.0, 16.0], [0.0, 16.0]],
                                    "one_way": False,
                                }
                            ],
                        }
                    },
                }
            )
        )

        map_path = data_dir / "map.json"
        map_path.write_text(
            json.dumps(
                {
                    "meta": {
                        "tile_size": "16;16",
                        "map_size": "2;2",
                        "initial_map_size": "2;2",
                        "render_scale": 1,
                        "scroll": "0;0",
                        "version": "1.1",
                    },
                    "resources": {
                        "tilesets": [
                            {
                                "path": "../assets/tileset.png",
                                "type": "tile",
                                "tile_count": 4,
                                "firstgid": 0,
                            }
                        ]
                    },
                    "project_state": {"rules": [], "groups": []},
                    "data": {
                        "layers": [
                            {
                                "name": "ground",
                                "type": "tile",
                                "visible": True,
                                "locked": False,
                                "opacity": 1.0,
                                "z_index": 0,
                                "tiles": {
                                    "0;0": {"pos": "0;0", "ttype": 0, "variant": 1},
                                    "1;0": {"pos": "1;0", "ttype": 0, "variant": 2},
                                    "0;1": {"pos": "0;1", "ttype": 0, "variant": 3},
                                    "1;1": {"pos": "1;1", "ttype": 0, "variant": 4},
                                },
                            },
                            {
                                "name": "skipme",
                                "type": "tile",
                                "visible": True,
                                "locked": False,
                                "opacity": 1.0,
                                "z_index": 0,
                                "tiles": {
                                    "0;0": {"pos": "0;0", "ttype": 0, "variant": 5},
                                    "1;0": {"pos": "1;0", "ttype": 0, "variant": 6},
                                    "0;1": {"pos": "0;1", "ttype": 0, "variant": 7},
                                    "1;1": {"pos": "1;1", "ttype": 0, "variant": 8},
                                },
                            },
                        ]
                    },
                }
            )
        )
        td = TilemapData.load(map_path)
        ts = load_tileset_collision(collision_dir / "tileset.collision.json")

        world = PhysicsWorld.from_map(td, ts)
        assert world.tileset_collision is ts
        assert world.tile_map == td.build_tile_map()

        world_excl = PhysicsWorld.from_map(td, ts, exclude_layers={"skipme"})
        assert world_excl.tile_map == td.build_tile_map(exclude_layers={"skipme"})


# ---------------------------------------------------------------------------
# Runner world attachment: attached world must resolve exactly like
# explicit per-call tile arguments (parity contract for Step 1).
# ---------------------------------------------------------------------------


def _ground_ts_and_map():
    shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
    ts = TilesetCollision(
        "ground", 16, {1: TileCollisionData(1, [shape]), 2: TileCollisionData(2, [shape])}
    )
    tile_map = {(0, 5): 1, (1, 5): 2, (2, 5): 1, (3, 5): 1}
    return ts, tile_map


def _ground_world():
    ts, tile_map = _ground_ts_and_map()
    world = PhysicsWorld(tile_map=tile_map, tileset_collision=ts, tile_size=(16, 16))
    return world, ts, tile_map


class Mover:
    """Minimal ICollidableSprite stand-in."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.width = 10
        self.height = 14
        self.on_ground = True
        self.collision_shape = RectangleShape(width=10, height=14)


def _run_world(world, dt=0.1, input_x=1.0, jump=False, vx=0.0, vy=0.0):
    runner = CollisionRunner.from_world(world)
    sprite = Mover(5, 60)
    sprite.vx, sprite.vy = vx, vy
    result = runner.move_platformer(
        sprite, None, None, dt, input_x=input_x, jump_pressed=jump
    )
    return sprite, result


def _run_explicit(ts, tile_map, dt=0.1, input_x=1.0, jump=False, vx=0.0, vy=0.0):
    runner = CollisionRunner.from_game_type("platformer", tile_size=(16, 16))
    sprite = Mover(5, 60)
    sprite.vx, sprite.vy = vx, vy
    result = runner.move_platformer(
        sprite, ts, tile_map, dt, input_x=input_x, jump_pressed=jump
    )
    return sprite, result


def _assert_parity(a, b):
    sa, ra = a
    sb, rb = b
    for name in (
        "final_x",
        "final_y",
        "collided",
        "hit_wall_x",
        "hit_wall_y",
        "hit_ceiling",
        "on_ground",
    ):
        assert getattr(ra, name) == getattr(rb, name), f"{name} differs"
    assert (sa.x, sa.y) == (sb.x, sb.y)
    assert (sa.vx, sa.vy) == (sb.vx, sb.vy)


def test_runner_world_parity_walk_and_jump():
    """Attached world resolves identically to explicit per-call tile args."""
    world, ts, tile_map = _ground_world()
    _assert_parity(_run_world(world), _run_explicit(ts, tile_map))
    _assert_parity(_run_world(world, jump=True), _run_explicit(ts, tile_map, jump=True))


def test_runner_world_parity_falling_and_collision():
    """Vertical motion and wall hits stay identical through the world."""
    world, ts, tile_map = _ground_world()
    _assert_parity(
        _run_world(world, vy=120.0), _run_explicit(ts, tile_map, vy=120.0)
    )
    _assert_parity(
        _run_world(world, input_x=0.0, vx=200.0),
        _run_explicit(ts, tile_map, input_x=0.0, vx=200.0),
    )


def test_runner_world_parity_grounded_mode():
    """Other modes resolve through the world too."""
    world, ts, tile_map = _ground_world()

    def run_grounded(use_world):
        runner = CollisionRunner(mode="grounded", tile_size=(16, 16))
        if use_world:
            runner.attach(world)
        sprite = Mover(5, 60)
        sprite.vx = 0.0
        sprite.vy = 0.0
        args = (sprite, None, None, 0.1) if use_world else (sprite, ts, tile_map, 0.1)
        result = runner.move_grounded(*args, velocity=(40.0, 80.0))
        return sprite, result

    _assert_parity(run_grounded(True), run_grounded(False))


def test_runner_attach_adopts_world_geometry():
    """attach() switches grid geometry to the world's tile size/scale."""
    world = PhysicsWorld(tile_size=(8, 16), render_scale=2.0)
    runner = CollisionRunner.from_game_type("platformer", tile_size=(16, 16))
    assert runner._eff_tw == 16
    runner.attach(world)
    assert runner.tile_size == (8, 16)
    assert runner.render_scale == 2.0
    assert runner._eff_tw == 16
    assert runner._eff_th == 32
    runner.detach()
    assert runner._world is None


# ---------------------------------------------------------------------------
# Bodies block movement (Step 2: bodies are solids in the world)
# ---------------------------------------------------------------------------


def _wall_world():
    """Ground tiles plus a 16x200 static wall at x=100 rising from the floor."""
    ts, _ = _ground_ts_and_map()
    tile_map = {(x, 5): 1 for x in range(16)}
    world = PhysicsWorld(tile_map=tile_map, tileset_collision=ts, tile_size=(16, 16))
    wall = Body(collision_shape=RectangleShape(width=16, height=200), x=100, y=0)
    world.add_body(wall)
    return world, wall


def test_world_collides_with_body_first_in_order():
    world, _ = _wall_world()
    world.clear_bodies()
    b1 = Body(collision_shape=RectangleShape(width=10, height=10), x=0, y=0)
    b2 = Body(collision_shape=RectangleShape(width=10, height=10), x=0, y=0)
    world.add_body(b1)
    world.add_body(b2)
    sprite = Mover(0, 0)
    assert world.collides_with_body(sprite) is b1


def test_body_blocks_platformer_walk():
    """Walking into a static body stops the sprite (hit_wall_x)."""
    world, _ = _wall_world()
    runner = CollisionRunner.from_world(world)
    sprite = Mover(85, 40)
    sprite.on_ground = True
    for _ in range(5):
        result = runner.move_platformer(
            sprite, None, None, 0.05, velocity=(200.0, 0.0)
        )
    assert result.hit_wall_x
    assert sprite.x < 100


def test_body_blocks_grounded_movement():
    world, _ = _wall_world()
    runner = CollisionRunner(mode="grounded", tile_size=(16, 16))
    runner.attach(world)
    sprite = Mover(30, 60)
    for _ in range(10):
        result = runner.move_grounded(sprite, None, None, 0.1, velocity=(200.0, 0.0))
    assert result.hit_wall_x
    assert sprite.x < 100


def test_body_blocks_slide_mode():
    """move_and_slide treats a body as a solid wall (slides along it)."""
    world, _ = _wall_world()
    runner = CollisionRunner(mode="slide", tile_size=(16, 16))
    runner.attach(world)
    sprite = Mover(30, 60)
    for _ in range(10):
        result = runner.move_and_slide(sprite, None, None, 20.0, 0.0)
    assert result.hit_wall_x
    assert sprite.x < 100
    assert result.slide_vector == (0.0, 0.0)


def test_body_first_colliding_shape_world_space_offset():
    """_first_colliding_shape surfaces a body as a WORLD-space polygon with a
    zero offset.

    Regression: the body polygon from ``as_polygon()`` is already in world
    space, but it was paired with a ``(body.x, body.y)`` offset.  The slide
    normal code applies ``v * scale + ox`` to tile-local polygons, so the
    offset must be zero — otherwise the polygon's centroid is displaced by
    the body position and the offset contract is violated.
    """
    world, _ = _wall_world()
    runner = CollisionRunner(mode="slide", tile_size=(16, 16))
    runner.attach(world)
    sprite = Mover(95, 60)
    hit = runner._first_colliding_shape(
        sprite, world.tileset_collision, world.tile_map, world=world
    )
    assert hit is not None
    poly, ox, oy = hit
    assert ox == 0.0
    assert oy == 0.0
    assert poly.vertices[0] == (100.0, 0.0)  # world space, not body-local


def test_body_slide_normal_from_polygon():
    """Diagonal motion into a body's left face yields the face normal."""
    world, _ = _wall_world()
    runner = CollisionRunner(mode="slide", tile_size=(16, 16))
    runner.attach(world)
    sprite = Mover(95, 60)
    hit = runner._first_colliding_shape(
        sprite, world.tileset_collision, world.tile_map, world=world
    )
    poly, ox, oy = hit
    normal = runner._get_collision_normal_from_motion(
        sprite, poly, ox, oy, 40.0, 10.0, runner.render_scale
    )
    assert normal == (-1.0, 0.0)


def test_body_blocked_by_layer_mask():
    """A body on a layer the sprite's mask excludes does not block."""
    world, wall = _wall_world()
    wall.collision_layer = 2
    runner = CollisionRunner.from_world(world)
    sprite = Mover(30, 66)
    sprite.on_ground = True
    sprite.collision_mask = 1  # only layer 1
    for _ in range(30):
        result = runner.move_platformer(sprite, None, None, 0.05, input_x=1.0)
    assert not result.hit_wall_x
    assert sprite.x > 100  # walked straight through


def test_body_removal_unblocks_movement():
    world, wall = _wall_world()
    world.remove_body(wall)
    runner = CollisionRunner.from_world(world)
    sprite = Mover(30, 66)
    sprite.on_ground = True
    for _ in range(30):
        result = runner.move_platformer(sprite, None, None, 0.05, input_x=1.0)
    assert not result.hit_wall_x
    assert sprite.x > 100


# ---------------------------------------------------------------------------
# Bodies are ground: landing on body tops via top_y_at (Step 2 landing)
# ---------------------------------------------------------------------------


def _empty_world():
    """A world with no tiles — only bodies are solid."""
    return PhysicsWorld(tile_map={}, tileset_collision=None, tile_size=(16, 16))


def _drop_runner(world):
    runner = CollisionRunner.from_world(world)
    sprite = Mover(20, 10)
    sprite.vx = 0.0
    sprite.vy = 0.0
    sprite.on_ground = False
    for _ in range(60):
        result = runner.move_platformer(sprite, None, None, 0.05, input_x=0.0)
    return sprite, result


def test_platformer_lands_on_body_top():
    """A body floor catches a falling sprite like a tile floor."""
    world = _empty_world()
    floor = Body(collision_shape=RectangleShape(width=200, height=16), x=0, y=80)
    world.add_body(floor)
    sprite, result = _drop_runner(world)
    assert result.on_ground
    assert abs(sprite.y + 14 - 80) < 0.5  # bottom flush with the body top


def test_platformer_lands_on_circle_body():
    """Landing works on curved body tops (circle top surface)."""
    world = _empty_world()
    bump = Body(collision_shape=CircleShape(radius=16), x=24, y=80)
    world.add_body(bump)
    sprite, result = _drop_runner(world)
    assert result.on_ground
    top = bump.top_y_at(sprite.x + 5)
    assert abs(sprite.y + 14 - top) < 0.5


def test_platformer_lands_on_capsule_body():
    """Capsule top surfaces are landable too."""
    world = _empty_world()
    pillar = Body(collision_shape=CapsuleShape(radius=8, height=32), x=24, y=48)
    world.add_body(pillar)
    sprite, result = _drop_runner(world)
    assert result.on_ground
    top = pillar.top_y_at(sprite.x + 5)
    assert abs(sprite.y + 14 - top) < 0.5


def test_landing_respects_layer_mask():
    """A sprite whose mask excludes a body's layer falls through it."""
    world = _empty_world()
    floor = Body(collision_shape=RectangleShape(width=200, height=16), x=0, y=80)
    floor.collision_layer = 2
    world.add_body(floor)
    sprite = Mover(20, 10)
    sprite.vx = 0.0
    sprite.vy = 0.0
    sprite.collision_mask = 1  # only layer 1
    sprite.on_ground = False
    for _ in range(60):
        result = CollisionRunner.from_world(world).move_platformer(
            sprite, None, None, 0.05, input_x=0.0
        )
    assert not result.on_ground
    assert sprite.y + 14 > 80  # fell through the body


def _step_world(crate_height):
    """Floor plus a crate of *crate_height* px sitting on it at x=100..116."""
    world = _empty_world()
    world.add_body(
        Body(collision_shape=RectangleShape(width=200, height=16), x=0, y=80)
    )
    world.add_body(
        Body(
            collision_shape=RectangleShape(width=16, height=crate_height),
            x=100,
            y=80 - crate_height,
        )
    )
    return world


def test_body_step_up_small_crate():
    """A crate shorter than step_height is climbed, not blocked."""
    world = _step_world(crate_height=4)
    runner = CollisionRunner.from_world(world)
    sprite = Mover(85, 66)  # standing on the floor (bottom = 80)
    sprite.on_ground = True
    result = runner.move_platformer(
        sprite, None, None, 0.05, velocity=(200.0, 0.0)
    )
    assert not result.hit_wall_x
    assert abs(sprite.y + 14 - 76) < 0.5  # now standing on the crate top


def test_body_too_tall_blocks_step_up():
    """A crate taller than step_height stops the sprite like a wall."""
    world = _step_world(crate_height=16)
    runner = CollisionRunner.from_world(world)
    sprite = Mover(85, 66)
    sprite.on_ground = True
    result = runner.move_platformer(
        sprite, None, None, 0.05, velocity=(200.0, 0.0)
    )
    assert result.hit_wall_x
    assert sprite.x < 100


# ---------------------------------------------------------------------------
# Step 3: bodies move in the space (kinematic crates pushed via move_grounded)
# ---------------------------------------------------------------------------


def _crate_world(crate_x=20, wall_x=100):
    """Floor (tiles x=0..11, row 5) plus a kinematic crate and a static wall."""
    shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
    ts = TilesetCollision("ground", 16, {1: TileCollisionData(1, [shape])})
    tile_map = {(x, 5): 1 for x in range(12)}
    world = PhysicsWorld(tile_map=tile_map, tileset_collision=ts, tile_size=(16, 16))
    crate = Body(
        collision_shape=RectangleShape(width=16, height=16),
        x=crate_x,
        y=64,
        mode="kinematic",
    )
    world.add_body(crate)
    wall = Body(collision_shape=RectangleShape(width=16, height=16), x=wall_x, y=64)
    world.add_body(wall)
    return world, crate, wall


def _push_crate(world, crate, steps=30, dt=0.1, speed=100.0):
    runner = CollisionRunner(mode="grounded", tile_size=(16, 16))
    runner.attach(world)
    result = None
    for _ in range(steps):
        result = runner.move_grounded(
            crate, None, None, dt, velocity=(speed, 0.0)
        )
    return result


def test_crate_pushed_slides_on_floor():
    """A crate resting flush on the floor can be pushed (regression: the
    inclusive vertex-in-rect check used to treat resting contact as a
    collision, blocking flush-placed crates from moving at all)."""
    world, crate, _ = _crate_world()
    result = _push_crate(world, crate, steps=1)
    assert not result.hit_wall_x
    assert crate.x > 20


def test_crate_pushed_stops_at_tile_wall():
    """A pushed crate stops at a solid tile wall (the wall protrudes above
    the floor line, like the wall tiles in the existing movement tests)."""
    shape = CollisionPolygon(vertices=[(0, 0), (16, 0), (16, 16), (0, 16)])
    ts = TilesetCollision("ground", 16, {1: TileCollisionData(1, [shape])})
    tile_map = {(x, 5): 1 for x in range(12)}
    tile_map[(12, 4)] = 1  # wall column at x=192, protruding from y=64..80
    world = PhysicsWorld(tile_map=tile_map, tileset_collision=ts, tile_size=(16, 16))
    crate = Body(
        collision_shape=RectangleShape(width=16, height=16),
        x=20,
        y=64,
        mode="kinematic",
    )
    world.add_body(crate)
    result = _push_crate(world, crate)
    assert result.hit_wall_x
    assert crate.x + 16 <= 192  # stopped at the wall face (tile 12 left edge)
    assert crate.x > 160  # did slide most of the way


def test_crate_pushed_stops_at_other_body():
    """A pushed crate stops at a static body (body-vs-body blocking)."""
    world, crate, wall = _crate_world()
    result = _push_crate(world, crate)
    assert result.hit_wall_x
    assert crate.x + 16 <= wall.x  # never penetrates the wall body
    assert crate.x > 60  # did slide most of the way


def test_crate_cannot_pass_through_other_body():
    """Even a high-speed push never tunnels through a body."""
    world, crate, wall = _crate_world()
    _push_crate(world, crate, steps=3, dt=0.1, speed=900.0)
    assert crate.x + 16 <= wall.x


def test_player_pushes_crate_recipe():
    """The push recipe: player hits crate (hit_wall_x) -> crate.vx = player.vx
    -> move_grounded(crate, velocity=...) slides the crate until it stops."""
    world, crate, wall = _crate_world(crate_x=48)
    runner = CollisionRunner.from_world(world)

    player = Mover(30, 66)
    player.on_ground = True
    result = runner.move_platformer(
        player, None, None, 0.05, velocity=(200.0, 0.0)
    )
    assert result.hit_wall_x  # player pressed against the crate
    assert player.x + 10 <= crate.x

    crate.vx = player.vx if player.vx > 0 else 200.0
    result = _push_crate(world, crate)
    assert result.hit_wall_x
    assert crate.x + 16 <= wall.x
    assert crate.x > 48  # the push actually moved it
