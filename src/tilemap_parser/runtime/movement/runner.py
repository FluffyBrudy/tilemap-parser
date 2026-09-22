from __future__ import annotations

from ...parser.collision import CollisionPolygon, TilesetCollision
from ..polygon_query import get_shape_bounds
from ..protocols import ICollidable
from ..world import PhysicsWorld
from . import grounded, platformer, queries, rpg, slide
from .types import CollisionResult, MovementMode


class CollisionRunner:
    """Collision runner with movement modes composed from sibling modules."""

    move_and_slide = slide.move_and_slide
    _get_collision_normal_from_motion = slide._get_collision_normal_from_motion
    move_grounded = grounded.move_grounded
    move_platformer = platformer.move_platformer
    move_platformer_with_slide = platformer.move_platformer_with_slide
    move_rpg = rpg.move_rpg
    _collides_at = queries._collides_at
    _first_colliding_shape = queries._first_colliding_shape
    _collides_at_platformer = queries._collides_at_platformer
    _walkable_edge_y_at_x = queries._walkable_edge_y_at_x
    _walkable_edge_info_at_x = queries._walkable_edge_info_at_x
    _find_walkable_ground_y = queries._find_walkable_ground_y
    _find_walkable_ground_info = queries._find_walkable_ground_info

    def __init__(
        self,
        tile_size: tuple[int, int] = (32, 32),
        mode: MovementMode = MovementMode.SLIDE,
        render_scale: float = 1.0,
    ):
        """
        Prefer CollisionRunner.from_game_type() for common game types.
        """
        self.tile_size = tile_size
        self.mode = MovementMode(mode) if isinstance(mode, str) else mode
        if render_scale <= 0:
            raise ValueError(f"render_scale must be positive, got {render_scale}")
        self.render_scale = render_scale
        self._eff_tw = max(1, int(tile_size[0] * render_scale))
        self._eff_th = max(1, int(tile_size[1] * render_scale))

        self.gravity = 800.0
        self.max_fall_speed = 600.0
        self.jump_strength = -400.0
        self.horizontal_speed = 200.0

        self.ground_snap_tolerance = 2.0
        self.step_height = 4.0

        self.max_walk_angle = 60.0  # degrees from horizontal; steeper = wall

        self.slide_friction = 0.1

        self.rpg_snap_to_grid = False

        self._game_type: str | None = None
        self._strict: bool = False
        self._world: PhysicsWorld | None = None

        # Reusable result object — reset fields before each use
        self._result = CollisionResult()

    def attach(self, world: PhysicsWorld | None) -> None:
        """Adopts tile_size/render_scale; None detaches to per-call args."""
        self._world = world
        if world is not None:
            self.tile_size = tuple(world.tile_size)
            self.render_scale = world.render_scale
            self._eff_tw = max(1, int(self.tile_size[0] * self.render_scale))
            self._eff_th = max(1, int(self.tile_size[1] * self.render_scale))

    def detach(self) -> None:
        self._world = None

    def _resolve_world(self, world: PhysicsWorld | None) -> PhysicsWorld | None:
        return self._world if world is None else world

    @classmethod
    def from_world(
        cls,
        world: PhysicsWorld,
        game_type: str = "platformer",
        strict: bool = False,
    ) -> CollisionRunner:
        """
        Bound to a world: movement resolves against its tiles and bodies.
        """
        runner = cls.from_game_type(
            game_type,
            tile_size=tuple(world.tile_size),
            strict=strict,
            render_scale=world.render_scale,
        )
        runner.attach(world)
        return runner

    def get_tile_at(self, world_x: float, world_y: float) -> tuple[int, int]:
        tile_x = int(world_x // self._eff_tw)
        tile_y = int(world_y // self._eff_th)
        return (tile_x, tile_y)

    def get_tile_shapes(
        self,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        world_x: float,
        world_y: float,
    ) -> list[CollisionPolygon]:
        """World-space shapes at a position; union of stacked entries."""
        from .queries import _iter_tile_datas

        tile_x, tile_y = self.get_tile_at(world_x, world_y)
        cell = tile_map.get((tile_x, tile_y))

        world = self._resolve_world(None)
        shapes: list[CollisionPolygon] = []
        for tile_data in _iter_tile_datas(world, tileset_collision, cell):
            tile_world_x = tile_x * self._eff_tw
            tile_world_y = tile_y * self._eff_th
            shapes.extend(
                shape.transform(tile_world_x, tile_world_y, self.render_scale)
                for shape in tile_data.shapes
                if shape.is_valid()
            )
        return shapes

    def get_nearby_tile_shapes(
        self,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        sprite: ICollidable,
        margin: int = 1,
    ) -> list[CollisionPolygon]:
        """
        World-space shapes near a sprite. Internal movement uses
        _collides_at(), which avoids this allocation.
        """
        left, top, right, bottom = get_shape_bounds(sprite)
        tw, th = self._eff_tw, self._eff_th

        min_tile_x = int(left // tw) - margin
        max_tile_x = int(right // tw) + margin
        min_tile_y = int(top // th) - margin
        max_tile_y = int(bottom // th) + margin

        shapes = []
        world = self._resolve_world(None)
        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                cell = tile_map.get((tile_x, tile_y))
                if cell is None:
                    continue
                for tile_data in queries._iter_tile_datas(world, tileset_collision, cell):
                    tile_world_x = tile_x * tw
                    tile_world_y = tile_y * th
                    for poly in tile_data.shapes:
                        if poly.is_valid():
                            shapes.append(poly.transform(tile_world_x, tile_world_y, self.render_scale))
        return shapes

    def move(
        self,
        sprite: ICollidable,
        tileset_collision: TilesetCollision | None,
        tile_map: dict | None,
        delta_x: float = 0.0,
        delta_y: float = 0.0,
        dt: float = 0.016,
        **kwargs,
    ) -> CollisionResult:
        """
        Dispatches on mode; world-attached calls may pass None tile args.
        """
        if self.mode == MovementMode.SLIDE:
            return self.move_and_slide(
                sprite, tileset_collision, tile_map, delta_x, delta_y,
                slope_slide=kwargs.get("slope_slide", False),
                world=kwargs.get("world"),
            )
        elif self.mode == MovementMode.PLATFORMER:
            return self.move_platformer(
                sprite,
                tileset_collision,
                tile_map,
                dt,
                input_x=kwargs.get("input_x", 0.0),
                jump_pressed=kwargs.get("jump_pressed", False),
                velocity=kwargs.get("velocity"),
                world=kwargs.get("world"),
            )
        elif self.mode == MovementMode.GROUNDED:
            return self.move_grounded(
                sprite, tileset_collision, tile_map, dt,
                velocity=kwargs.get("velocity"),
                world=kwargs.get("world"),
                one_way=kwargs.get("one_way", "solid"),
            )
        elif self.mode == MovementMode.RPG:
            return self.move_rpg(
                sprite, tileset_collision, tile_map, delta_x, delta_y,
                world=kwargs.get("world"),
            )

        return CollisionResult(final_x=sprite.x, final_y=sprite.y)

    @classmethod
    def from_game_type(
        cls,
        game_type: str,
        tile_size: tuple[int, int] = (32, 32),
        strict: bool = False,
        render_scale: float = 1.0,
    ) -> CollisionRunner:
        """
        Presets: platformer (gravity+jump), topdown (slide, no gravity),
        rpg (blocking, no gravity). Raises ValueError on unknown game_type.
        """
        game_type = game_type.lower()

        if game_type == "platformer":
            runner = cls(tile_size, mode=MovementMode.PLATFORMER, render_scale=render_scale)
            runner.gravity = 800.0
            runner.max_fall_speed = 600.0
            runner.jump_strength = -400.0
            runner.horizontal_speed = 200.0
            runner.slide_friction = 0.1
            runner._game_type = "platformer"
            runner._strict = strict

        elif game_type == "topdown":
            runner = cls(tile_size, mode=MovementMode.SLIDE, render_scale=render_scale)
            runner.gravity = 0.0
            runner.max_fall_speed = 0.0
            runner.jump_strength = 0.0
            runner.slide_friction = 0.1
            runner._game_type = "topdown"
            runner._strict = strict

        elif game_type == "rpg":
            runner = cls(tile_size, mode=MovementMode.RPG, render_scale=render_scale)
            runner.gravity = 0.0
            runner.max_fall_speed = 0.0
            runner.jump_strength = 0.0
            runner.slide_friction = 0.0
            runner.rpg_snap_to_grid = False
            runner._game_type = "rpg"
            runner._strict = strict

        else:
            raise ValueError(f"Unknown game_type: '{game_type}'. Valid options are: 'platformer', 'topdown', 'rpg'")

        runner.validate_config()

        return runner

    def validate_config(self, strict: bool | None = None) -> None:
        """
        Validation rules: platformer needs gravity > 0; slide/rpg need
        gravity = 0; physics values must be in range; mode must match
        game_type. Raises ValueError on errors (or warnings when strict).
        """
        import warnings

        if strict is None:
            strict = getattr(self, "_strict", False)

        game_type = getattr(self, "_game_type", None)
        errors = []
        warnings_list = []

        if self.gravity < 0:
            errors.append("gravity must be >= 0 (negative gravity not supported)")

        if self.max_fall_speed < 0:
            errors.append("max_fall_speed must be >= 0")

        if self.jump_strength > 0:
            warnings_list.append(
                "jump_strength is positive (upward force should be negative). Did you mean a negative value?"
            )

        if not (0.0 <= self.slide_friction <= 1.0):
            warnings_list.append(f"slide_friction={self.slide_friction} is outside typical range [0.0, 1.0]")

        if self.mode == MovementMode.PLATFORMER:
            if self.gravity == 0:
                errors.append(
                    "PLATFORMER mode requires gravity > 0 for jumping mechanics.\n"
                    "  Fix: Set runner.gravity = 800.0 (or another positive value)\n"
                    "  Or: Use game_type='topdown' or 'rpg' instead"
                )

            if self.max_fall_speed == 0 and self.gravity > 0:
                warnings_list.append(
                    "PLATFORMER mode with gravity > 0 but max_fall_speed = 0. Falling speed will be unlimited."
                )

        elif self.mode == MovementMode.SLIDE:
            if self.gravity > 0:
                warnings_list.append(
                    "SLIDE mode (top-down) typically uses gravity = 0. "
                    f"Current gravity = {self.gravity} will be ignored in move_and_slide()."
                )

        elif self.mode == MovementMode.RPG:
            if self.gravity > 0:
                errors.append(
                    "RPG mode should not use gravity (set gravity = 0).\n"
                    "  Fix: Set runner.gravity = 0.0\n"
                    "  Or: Use game_type='platformer' if you need gravity"
                )

        if game_type:
            if game_type == "platformer" and self.mode != MovementMode.PLATFORMER:
                warnings_list.append(
                    f"game_type='platformer' but mode={self.mode.value}. This may cause unexpected behavior."
                )

            if game_type == "topdown" and self.mode != MovementMode.SLIDE:
                warnings_list.append(
                    f"game_type='topdown' but mode={self.mode.value}. This may cause unexpected behavior."
                )

            if game_type == "rpg" and self.mode != MovementMode.RPG:
                warnings_list.append(f"game_type='rpg' but mode={self.mode.value}. This may cause unexpected behavior.")

            if game_type in ["topdown", "rpg"] and self.gravity > 0:
                warnings_list.append(
                    f"game_type='{game_type}' typically uses gravity=0, but current gravity={self.gravity}"
                )

        if errors:
            error_msg = "Configuration validation failed:\n\n"
            for i, err in enumerate(errors, 1):
                error_msg += f"{i}. {err}\n"

            if game_type:
                error_msg += "\nCurrent configuration:\n"
                error_msg += f"  game_type: {game_type}\n"
                error_msg += f"  mode: {self.mode.value}\n"
                error_msg += f"  gravity: {self.gravity}\n"
                error_msg += f"  max_fall_speed: {self.max_fall_speed}\n"
                error_msg += f"  jump_strength: {self.jump_strength}\n"

            raise ValueError(error_msg)

        if warnings_list:
            warning_msg = "Configuration warnings detected:\n\n"
            for i, warn in enumerate(warnings_list, 1):
                warning_msg += f"{i}. {warn}\n"

            if game_type:
                warning_msg += "\nCurrent configuration:\n"
                warning_msg += f"  game_type: {game_type}\n"
                warning_msg += f"  mode: {self.mode.value}\n"
                warning_msg += f"  gravity: {self.gravity}\n"

            if strict:
                raise ValueError(warning_msg)
            else:
                warnings.warn(warning_msg, UserWarning, stacklevel=2)
