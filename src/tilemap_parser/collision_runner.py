"""
Collision runner with ready-to-use movement modes for games.

Provides optimized collision detection and response for common game types:
- Slide: Smooth sliding along walls (top-down games)
- Platformer: Gravity-based movement with jump mechanics
- RPG: Grid-based or free movement with tile blocking

All runners work through a defined interface that any sprite class can implement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Protocol, Tuple, Union

from .collision import (
    CapsuleShape,
    CircleShape,
    CollisionCache,
    CollisionPolygon,
    RectangleShape,
    TilesetCollision,
)

Point = Tuple[float, float]
Vector2 = Tuple[float, float]


class ICollidableSprite(Protocol):
    """
    Interface that any sprite/character class must implement to use collision runners.

    Required attributes:
        x (float): World X position
        y (float): World Y position
        collision_shape (RectangleShape | CircleShape | CapsuleShape): Collision shape

    Optional attributes:
        vx (float): X velocity (for physics-based runners)
        vy (float): Y velocity (for physics-based runners)
        on_ground (bool): Whether sprite is on ground (for platformer)
    """

    x: float
    y: float
    collision_shape: Union[RectangleShape, CircleShape, CapsuleShape]

    vx: float
    vy: float
    on_ground: bool


def point_in_polygon(point: Point, vertices: List[Point]) -> bool:
    """Check if point is inside polygon using ray casting"""
    x, y = point
    n = len(vertices)
    inside = False

    p1x, p1y = vertices[0]
    for i in range(1, n + 1):
        p2x, p2y = vertices[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def rect_polygon_collision(
    rect_x: float, rect_y: float, rect_w: float, rect_h: float, vertices: List[Point]
) -> bool:
    """Check if rectangle collides with polygon"""

    corners = [
        (rect_x, rect_y),
        (rect_x + rect_w, rect_y),
        (rect_x, rect_y + rect_h),
        (rect_x + rect_w, rect_y + rect_h),
    ]

    for corner in corners:
        if point_in_polygon(corner, vertices):
            return True

    for vx, vy in vertices:
        if rect_x <= vx <= rect_x + rect_w and rect_y <= vy <= rect_y + rect_h:
            return True

    return False


def circle_polygon_collision(
    center: Point, radius: float, vertices: List[Point]
) -> bool:
    """Check if circle collides with polygon"""

    if point_in_polygon(center, vertices):
        return True

    cx, cy = center
    n = len(vertices)

    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]

        dx = x2 - x1
        dy = y2 - y1

        fx = cx - x1
        fy = cy - y1

        if dx == 0 and dy == 0:
            dist = math.sqrt((cx - x1) ** 2 + (cy - y1) ** 2)
        else:
            t = max(0, min(1, (fx * dx + fy * dy) / (dx * dx + dy * dy)))
            closest_x = x1 + t * dx
            closest_y = y1 + t * dy
            dist = math.sqrt((cx - closest_x) ** 2 + (cy - closest_y) ** 2)

        if dist <= radius:
            return True

    return False


def get_shape_bounds(sprite: ICollidableSprite) -> Tuple[float, float, float, float]:
    """Get AABB bounds for sprite (left, top, right, bottom)"""
    shape = sprite.collision_shape

    if isinstance(shape, RectangleShape):
        left = sprite.x + shape.offset[0]
        top = sprite.y + shape.offset[1]
        return (left, top, left + shape.width, top + shape.height)
    elif isinstance(shape, CircleShape):
        cx, cy = shape.get_center(sprite.x, sprite.y)
        r = shape.radius
        return (cx - r, cy - r, cx + r, cy + r)
    elif isinstance(shape, CapsuleShape):
        top_center = shape.get_top_center(sprite.x, sprite.y)
        r = shape.radius
        h = shape.height
        return (
            top_center[0] - r,
            top_center[1],
            top_center[0] + r,
            top_center[1] + h + r * 2,
        )

    return (sprite.x, sprite.y, sprite.x + 32, sprite.y + 32)


def check_sprite_polygon_collision(
    sprite: ICollidableSprite, polygon: CollisionPolygon
) -> bool:
    """Check if sprite collides with polygon"""
    shape = sprite.collision_shape

    if isinstance(shape, RectangleShape):
        left, top, right, bottom = get_shape_bounds(sprite)
        return rect_polygon_collision(
            left, top, right - left, bottom - top, polygon.vertices
        )
    elif isinstance(shape, CircleShape):
        center = shape.get_center(sprite.x, sprite.y)
        return circle_polygon_collision(center, shape.radius, polygon.vertices)
    elif isinstance(shape, CapsuleShape):

        left, top, right, bottom = get_shape_bounds(sprite)
        return rect_polygon_collision(
            left, top, right - left, bottom - top, polygon.vertices
        )

    return False


class MovementMode(Enum):
    """Movement modes for collision runner"""

    SLIDE = "slide"
    PLATFORMER = "platformer"
    RPG = "rpg"


@dataclass
class CollisionResult:
    """Result of collision detection and resolution"""

    collided: bool = False
    final_x: float = 0.0
    final_y: float = 0.0
    hit_wall_x: bool = False
    hit_wall_y: bool = False
    hit_ceiling: bool = False
    on_ground: bool = False
    slide_vector: Optional[Vector2] = None


class CollisionRunner:
    """
    Ready-to-use collision runner with multiple movement modes.

    Handles collision detection and response for common game types.
    Works with any sprite class that implements ICollidableSprite interface.
    """

    def __init__(
        self,
        collision_cache: CollisionCache,
        tile_size: Tuple[int, int] = (32, 32),
        mode: MovementMode = MovementMode.SLIDE,
    ):
        """
        Initialize collision runner.

        For most use cases, prefer using CollisionRunner.from_game_type() instead,
        which provides preset configurations for common game types.

        Args:
            collision_cache: Cache with preloaded collision data
            tile_size: Size of tiles in pixels (width, height)
            mode: Movement mode (slide, platformer, rpg)
        """
        self.cache = collision_cache
        self.tile_size = tile_size
        self.mode = mode

        self.gravity = 800.0
        self.max_fall_speed = 600.0
        self.jump_strength = -400.0

        self.slide_friction = 0.1

        self.rpg_snap_to_grid = False

        self._game_type: Optional[str] = None
        self._strict: bool = False

    def get_tile_at(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world position to tile coordinates"""
        tile_x = int(world_x // self.tile_size[0])
        tile_y = int(world_y // self.tile_size[1])
        return (tile_x, tile_y)

    def get_tile_shapes(
        self,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        world_x: float,
        world_y: float,
    ) -> List[CollisionPolygon]:
        """Get collision shapes at world position"""
        tile_x, tile_y = self.get_tile_at(world_x, world_y)
        tile_id = tile_map.get((tile_x, tile_y))

        if tile_id is None or not tileset_collision.has_collision(tile_id):
            return []

        tile_world_x = tile_x * self.tile_size[0]
        tile_world_y = tile_y * self.tile_size[1]

        return tileset_collision.get_world_shapes(tile_id, tile_world_x, tile_world_y)

    def get_nearby_tile_shapes(
        self,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        sprite: ICollidableSprite,
        margin: int = 1,
    ) -> List[CollisionPolygon]:
        """Get all collision shapes near sprite"""
        left, top, right, bottom = get_shape_bounds(sprite)

        min_tile_x = int(left // self.tile_size[0]) - margin
        max_tile_x = int(right // self.tile_size[0]) + margin
        min_tile_y = int(top // self.tile_size[1]) - margin
        max_tile_y = int(bottom // self.tile_size[1]) + margin

        shapes = []
        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                tile_id = tile_map.get((tile_x, tile_y))
                if tile_id is None or not tileset_collision.has_collision(tile_id):
                    continue

                tile_world_x = tile_x * self.tile_size[0]
                tile_world_y = tile_y * self.tile_size[1]

                tile_shapes = tileset_collision.get_world_shapes(
                    tile_id, tile_world_x, tile_world_y
                )
                shapes.extend(tile_shapes)

        return shapes

    def move_and_slide(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        delta_x: float,
        delta_y: float,
        slope_slide: bool = False,
    ) -> CollisionResult:
        """
        Move sprite with sliding collision response.

        Best for top-down games where sprite should slide along walls.

        Args:
            sprite: Sprite to move (must implement ICollidableSprite)
            tileset_collision: Tileset collision data
            tile_map: Dictionary mapping (tile_x, tile_y) to tile_id
            delta_x: X movement amount
            delta_y: Y movement amount
            slope_slide: If True, allows sliding along slopes instead of blocking

        Returns:
            CollisionResult with final position and collision info
        """
        result = CollisionResult(final_x=sprite.x, final_y=sprite.y)

        if delta_x == 0 and delta_y == 0:
            return result

        old_x, old_y = sprite.x, sprite.y

        if slope_slide:
            max_slides = 4
            motion_x, motion_y = delta_x, delta_y

            for i in range(max_slides):
                if abs(motion_x) < 0.01 and abs(motion_y) < 0.01:
                    break

                sprite.x = old_x + motion_x
                sprite.y = old_y + motion_y

                shapes = self.get_nearby_tile_shapes(
                    tileset_collision, tile_map, sprite
                )

                colliding_shape = None
                for shape in shapes:
                    if check_sprite_polygon_collision(sprite, shape):
                        colliding_shape = shape
                        break

                if not colliding_shape:

                    result.final_x = sprite.x
                    result.final_y = sprite.y
                    return result

                sprite.x = old_x
                sprite.y = old_y
                result.collided = True

                normal = self._get_collision_normal_from_motion(
                    sprite, colliding_shape, motion_x, motion_y
                )

                if normal:

                    dot = motion_x * normal[0] + motion_y * normal[1]

                    if dot < 0:
                        motion_x = motion_x - normal[0] * dot
                        motion_y = motion_y - normal[1] * dot
                    else:

                        break
                else:

                    break

            result.final_x = sprite.x
            result.final_y = sprite.y
            return result

        sprite.x += delta_x
        sprite.y += delta_y

        shapes = self.get_nearby_tile_shapes(tileset_collision, tile_map, sprite)

        collided = any(
            check_sprite_polygon_collision(sprite, shape) for shape in shapes
        )

        if not collided:
            result.final_x = sprite.x
            result.final_y = sprite.y
            return result

        result.collided = True

        sprite.x = old_x + delta_x
        sprite.y = old_y

        x_collided = any(
            check_sprite_polygon_collision(sprite, shape) for shape in shapes
        )

        if x_collided:
            sprite.x = old_x
            result.hit_wall_x = True

        sprite.x = old_x
        sprite.y = old_y + delta_y

        y_collided = any(
            check_sprite_polygon_collision(sprite, shape) for shape in shapes
        )

        if y_collided:
            sprite.y = old_y
            result.hit_wall_y = True

        if not x_collided:
            sprite.x = old_x + delta_x
        if not y_collided:
            sprite.y = old_y + delta_y

        result.final_x = sprite.x
        result.final_y = sprite.y

        if x_collided and not y_collided:
            result.slide_vector = (0, delta_y)
        elif y_collided and not x_collided:
            result.slide_vector = (delta_x, 0)

        return result

    def _get_collision_normal_from_motion(
        self,
        sprite: ICollidableSprite,
        polygon: CollisionPolygon,
        motion_x: float,
        motion_y: float,
    ) -> Optional[Tuple[float, float]]:
        """
        Calculate the collision normal from a polygon based on motion direction.
        Returns the normal of the edge that the sprite is moving into.
        """

        bounds = get_shape_bounds(sprite)
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2

        vertices = polygon.vertices
        if len(vertices) < 2:
            return None

        best_edge = None
        best_alignment = -1

        for i in range(len(vertices)):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % len(vertices)]

            edge_x = v2[0] - v1[0]
            edge_y = v2[1] - v1[1]
            edge_len = math.sqrt(edge_x * edge_x + edge_y * edge_y)

            if edge_len < 0.01:
                continue

            normal_x = -edge_y / edge_len
            normal_y = edge_x / edge_len

            poly_center_x = sum(v[0] for v in vertices) / len(vertices)
            poly_center_y = sum(v[1] for v in vertices) / len(vertices)
            edge_mid_x = (v1[0] + v2[0]) / 2
            edge_mid_y = (v1[1] + v2[1]) / 2

            to_outside_x = edge_mid_x - poly_center_x
            to_outside_y = edge_mid_y - poly_center_y

            if normal_x * to_outside_x + normal_y * to_outside_y < 0:
                normal_x = -normal_x
                normal_y = -normal_y

            alignment = -(motion_x * normal_x + motion_y * normal_y)

            if alignment > best_alignment and alignment > 0:
                best_alignment = alignment
                best_edge = (normal_x, normal_y)

        return best_edge

    def move_platformer(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        dt: float,
        input_x: float = 0.0,
        jump_pressed: bool = False,
    ) -> CollisionResult:
        """
        Move sprite with platformer physics (gravity, jumping).

        Best for side-scrolling platformer games.

        Args:
            sprite: Sprite to move (must have vx, vy, on_ground attributes)
            tileset_collision: Tileset collision data
            tile_map: Dictionary mapping (tile_x, tile_y) to tile_id
            dt: Delta time in seconds
            input_x: Horizontal input (-1 to 1)
            jump_pressed: Whether jump button is pressed

        Returns:
            CollisionResult with final position and collision info
        """
        result = CollisionResult(final_x=sprite.x, final_y=sprite.y)

        if not getattr(sprite, "on_ground", False):
            sprite.vy += self.gravity * dt
            sprite.vy = min(sprite.vy, self.max_fall_speed)

        if jump_pressed and getattr(sprite, "on_ground", False):
            sprite.vy = self.jump_strength

        sprite.vx = input_x * 200.0

        delta_x = sprite.vx * dt
        delta_y = sprite.vy * dt

        old_x, old_y = sprite.x, sprite.y

        sprite.x += delta_x
        shapes = self.get_nearby_tile_shapes(tileset_collision, tile_map, sprite)

        if any(check_sprite_polygon_collision(sprite, shape) for shape in shapes):
            sprite.x = old_x
            sprite.vx = 0
            result.hit_wall_x = True

        sprite.y += delta_y
        shapes = self.get_nearby_tile_shapes(tileset_collision, tile_map, sprite)

        collided_y = False

        for shape in shapes:
            if check_sprite_polygon_collision(sprite, shape):
                if shape.one_way and sprite.vy > 0:
                    if old_y + get_shape_bounds(sprite)[3] - old_y <= min(
                        v[1] for v in shape.vertices
                    ):
                        collided_y = True
                        break

        if collided_y:
            sprite.y = old_y

            if sprite.vy > 0:
                sprite.vy = 0
                sprite.on_ground = True
                result.on_ground = True
            elif sprite.vy < 0:
                sprite.vy = 0
                result.hit_ceiling = True
        else:
            sprite.on_ground = False

        result.final_x = sprite.x
        result.final_y = sprite.y
        result.collided = result.hit_wall_x or collided_y

        return result

    def move_rpg(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        delta_x: float,
        delta_y: float,
    ) -> CollisionResult:
        """
        Move sprite with RPG-style blocking (no sliding).

        Best for grid-based RPG games where movement is blocked by walls.

        Args:
            sprite: Sprite to move
            tileset_collision: Tileset collision data
            tile_map: Dictionary mapping (tile_x, tile_y) to tile_id
            delta_x: X movement amount
            delta_y: Y movement amount

        Returns:
            CollisionResult with final position and collision info
        """
        result = CollisionResult(final_x=sprite.x, final_y=sprite.y)

        if delta_x == 0 and delta_y == 0:
            return result

        old_x, old_y = sprite.x, sprite.y
        sprite.x += delta_x
        sprite.y += delta_y

        shapes = self.get_nearby_tile_shapes(tileset_collision, tile_map, sprite)

        collided = any(
            check_sprite_polygon_collision(sprite, shape) for shape in shapes
        )

        if collided:

            sprite.x = old_x
            sprite.y = old_y
            result.collided = True
            result.hit_wall_x = delta_x != 0
            result.hit_wall_y = delta_y != 0
        else:
            result.final_x = sprite.x
            result.final_y = sprite.y

        return result

    def move(
        self,
        sprite: ICollidableSprite,
        tileset_collision: TilesetCollision,
        tile_map: dict,
        delta_x: float = 0.0,
        delta_y: float = 0.0,
        dt: float = 0.016,
        **kwargs,
    ) -> CollisionResult:
        """
        Move sprite using configured movement mode.

        This is a convenience method that calls the appropriate movement function
        based on the runner's mode.

        Args:
            sprite: Sprite to move
            tileset_collision: Tileset collision data
            tile_map: Dictionary mapping (tile_x, tile_y) to tile_id
            delta_x: X movement amount (for slide/rpg modes)
            delta_y: Y movement amount (for slide/rpg modes)
            dt: Delta time in seconds (for platformer mode)
            **kwargs: Additional mode-specific arguments

        Returns:
            CollisionResult with final position and collision info
        """
        if self.mode == MovementMode.SLIDE:
            return self.move_and_slide(
                sprite, tileset_collision, tile_map, delta_x, delta_y
            )
        elif self.mode == MovementMode.PLATFORMER:
            return self.move_platformer(
                sprite,
                tileset_collision,
                tile_map,
                dt,
                input_x=kwargs.get("input_x", 0.0),
                jump_pressed=kwargs.get("jump_pressed", False),
            )
        elif self.mode == MovementMode.RPG:
            return self.move_rpg(sprite, tileset_collision, tile_map, delta_x, delta_y)

        return CollisionResult(final_x=sprite.x, final_y=sprite.y)

    @classmethod
    def from_game_type(
        cls,
        game_type: str,
        collision_cache: CollisionCache,
        tile_size: Tuple[int, int] = (32, 32),
        strict: bool = False,
    ) -> "CollisionRunner":
        """
        Create a collision runner with preset configuration for a specific game type.

        This is the recommended way to create a collision runner for common game types.
        Provides sensible defaults that can be customized after creation.

        Game Types:
            'platformer': Side-scrolling platformer with gravity and jumping
                - Gravity: 800 px/s²
                - Max fall speed: 600 px/s
                - Jump strength: -400 px/s (negative = upward)
                - Mode: PLATFORMER
                - Requires sprite attributes: x, y, vx, vy, on_ground, collision_shape

            'topdown': Overhead view with free 8-directional movement
                - No gravity (gravity = 0)
                - Slides along walls smoothly
                - Mode: SLIDE
                - Requires sprite attributes: x, y, collision_shape

            'rpg': Grid-based or free movement with full blocking
                - No gravity (gravity = 0)
                - Stops at walls (no sliding)
                - Mode: RPG
                - Requires sprite attributes: x, y, collision_shape

        Args:
            game_type: Type of game ('platformer', 'topdown', or 'rpg')
            collision_cache: Cache with preloaded collision data
            tile_size: Size of tiles in pixels (width, height)
            strict: If True, raises exceptions on warnings. If False, only warns.

        Returns:
            CollisionRunner configured for the specified game type

        Raises:
            ValueError: If game_type is not recognized

        Examples:
            >>>
            >>> runner = CollisionRunner.from_game_type('platformer', cache, (32, 32))
            >>> result = runner.move(player, tileset, tile_map, dt=0.016)

            >>>
            >>> runner = CollisionRunner.from_game_type('topdown', cache, (16, 16))
            >>> runner.slide_friction = 0.2
            >>> result = runner.move(player, tileset, tile_map, delta_x=dx, delta_y=dy)

            >>>
            >>> runner = CollisionRunner.from_game_type('rpg', cache, (32, 32), strict=True)
            >>> runner.validate_config()
        """
        game_type = game_type.lower()

        if game_type == "platformer":
            runner = cls(collision_cache, tile_size, mode=MovementMode.PLATFORMER)
            runner.gravity = 800.0
            runner.max_fall_speed = 600.0
            runner.jump_strength = -400.0
            runner.slide_friction = 0.1
            runner._game_type = "platformer"
            runner._strict = strict

        elif game_type == "topdown":
            runner = cls(collision_cache, tile_size, mode=MovementMode.SLIDE)
            runner.gravity = 0.0
            runner.max_fall_speed = 0.0
            runner.jump_strength = 0.0
            runner.slide_friction = 0.1
            runner._game_type = "topdown"
            runner._strict = strict

        elif game_type == "rpg":
            runner = cls(collision_cache, tile_size, mode=MovementMode.RPG)
            runner.gravity = 0.0
            runner.max_fall_speed = 0.0
            runner.jump_strength = 0.0
            runner.slide_friction = 0.0
            runner.rpg_snap_to_grid = False
            runner._game_type = "rpg"
            runner._strict = strict

        else:
            raise ValueError(
                f"Unknown game_type: '{game_type}'. "
                f"Valid options are: 'platformer', 'topdown', 'rpg'"
            )

        runner.validate_config()

        return runner

    def validate_config(self, strict: Optional[bool] = None) -> None:
        """
        Validate the current configuration for consistency and correctness.

        This method checks for common configuration mistakes and inconsistencies.
        Called automatically when using from_game_type(), but can also be called
        manually after changing configuration properties.

        Validation Rules:
            - Platformer mode requires gravity > 0
            - Top-down and RPG modes should have gravity = 0
            - Physics values must be in valid ranges
            - Mode must match game_type expectations

        Args:
            strict: If True, raises exceptions on warnings. If False, only warns.
                   If None, uses the strict setting from initialization.

        Raises:
            ValueError: If critical configuration errors are found
            Warning: If suspicious but valid configurations are detected (strict=False)

        Examples:
            >>> runner = CollisionRunner.from_game_type('platformer', cache, (32, 32))
            >>> runner.gravity = 0.0
            >>> runner.validate_config()

            >>> runner = CollisionRunner.from_game_type('topdown', cache, (32, 32))
            >>> runner.gravity = 800.0
            >>> runner.validate_config(strict=False)
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
                "jump_strength is positive (upward force should be negative). "
                "Did you mean a negative value?"
            )

        if not (0.0 <= self.slide_friction <= 1.0):
            warnings_list.append(
                f"slide_friction={self.slide_friction} is outside typical range [0.0, 1.0]"
            )

        if self.mode == MovementMode.PLATFORMER:
            if self.gravity == 0:
                errors.append(
                    "PLATFORMER mode requires gravity > 0 for jumping mechanics.\n"
                    "  Fix: Set runner.gravity = 800.0 (or another positive value)\n"
                    "  Or: Use game_type='topdown' or 'rpg' instead"
                )

            if self.max_fall_speed == 0 and self.gravity > 0:
                warnings_list.append(
                    "PLATFORMER mode with gravity > 0 but max_fall_speed = 0. "
                    "Falling speed will be unlimited."
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
                    f"game_type='platformer' but mode={self.mode.value}. "
                    "This may cause unexpected behavior."
                )

            if game_type == "topdown" and self.mode != MovementMode.SLIDE:
                warnings_list.append(
                    f"game_type='topdown' but mode={self.mode.value}. "
                    "This may cause unexpected behavior."
                )

            if game_type == "rpg" and self.mode != MovementMode.RPG:
                warnings_list.append(
                    f"game_type='rpg' but mode={self.mode.value}. "
                    "This may cause unexpected behavior."
                )

            if game_type in ["topdown", "rpg"] and self.gravity > 0:
                warnings_list.append(
                    f"game_type='{game_type}' typically uses gravity=0, "
                    f"but current gravity={self.gravity}"
                )

        if errors:
            error_msg = "Configuration validation failed:\n\n"
            for i, err in enumerate(errors, 1):
                error_msg += f"{i}. {err}\n"

            if game_type:
                error_msg += f"\nCurrent configuration:\n"
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
                warning_msg += f"\nCurrent configuration:\n"
                warning_msg += f"  game_type: {game_type}\n"
                warning_msg += f"  mode: {self.mode.value}\n"
                warning_msg += f"  gravity: {self.gravity}\n"

            if strict:
                raise ValueError(warning_msg)
            else:
                warnings.warn(warning_msg, UserWarning, stacklevel=2)
