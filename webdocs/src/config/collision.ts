import type { ApiEntry, ClassEntry, ModuleEntry } from "./types";

export const collisionModules: ModuleEntry[] = [
  {
    name: "collision",
    description: "Collision data parsing and caching",
    items: [
      "parse_tileset_collision",
      "parse_character_collision",
      "load_tileset_collision",
      "load_character_collision",
      "CollisionCache",
      "TilesetCollision",
      "TileCollisionData",
      "CollisionPolygon",
      "RectangleShape",
      "CircleShape",
      "CapsuleShape",
      "CharacterCollision",
    ],
  },
  {
    name: "collision_runner",
    description: "Ready-to-use collision runners",
    items: ["CollisionRunner", "CollisionResult", "MovementMode", "ICollidableSprite"],
  },
];

export const collisionFunctions: ApiEntry[] = [
  {
    name: "parse_tileset_collision",
    signature: "parse_tileset_collision(data: dict) -> TilesetCollision",
    description: "Parse tileset collision data from a dictionary loaded from .collision.json file.",
    parameters: [
      { name: "data", type: "dict", description: "Dictionary with tileset collision data" },
    ],
    returns: "TilesetCollision",
  },
  {
    name: "parse_character_collision",
    signature: "parse_character_collision(data: dict) -> CharacterCollision",
    description: "Parse character collision data from a dictionary.",
    parameters: [
      { name: "data", type: "dict", description: "Dictionary with character collision data" },
    ],
    returns: "CharacterCollision",
  },
  {
    name: "load_tileset_collision",
    signature: "load_tileset_collision(tileset_path: PathLike) -> TilesetCollision | None",
    description: "Load tileset collision from a .collision.json file alongside the tileset image. Returns None if file doesn't exist.",
    parameters: [
      { name: "tileset_path", type: "PathLike", description: "Path to tileset image file" },
    ],
    returns: "TilesetCollision | None",
  },
  {
    name: "load_character_collision",
    signature: "load_character_collision(sprite_path: PathLike) -> CharacterCollision | None",
    description: "Load character collision from a .collision.json file alongside the sprite image. Returns None if file doesn't exist.",
    parameters: [
      { name: "sprite_path", type: "PathLike", description: "Path to character sprite image file" },
    ],
    returns: "CharacterCollision | None",
  },
  {
    name: "get_cached_tileset_collision",
    signature: "get_cached_tileset_collision(tileset_path: PathLike) -> TilesetCollision | None",
    description: "Get tileset collision using the global cache. Avoids repeated file I/O.",
    returns: "TilesetCollision | None",
  },
  {
    name: "get_cached_character_collision",
    signature: "get_cached_character_collision(sprite_path: PathLike) -> CharacterCollision | None",
    description: "Get character collision using the global cache. Avoids repeated file I/O.",
    returns: "CharacterCollision | None",
  },
  {
    name: "clear_collision_cache",
    signature: "clear_collision_cache()",
    description: "Clear the global collision cache. Call this when reloading assets.",
  },
];

export const collisionClasses: ClassEntry[] = [
  {
    name: "CollisionParseError",
    signature: "class CollisionParseError(Exception)",
    description: "Raised when collision data cannot be parsed due to invalid format.",
  },
  {
    name: "CollisionPolygon",
    signature: "class CollisionPolygon",
    description: "Polygon collision shape for a tile.",
    properties: [
      { name: "vertices", type: "List[Point]", description: "List of (x, y) vertex coordinates" },
      { name: "one_way", type: "bool", description: "If True, only collides when sprite is above (platforms)" },
    ],
    methods: [
      { name: "transform", signature: "transform(tile_x: float, tile_y: float) -> CollisionPolygon", description: "Transform polygon to world space coordinates" },
      { name: "is_valid", signature: "is_valid() -> bool", description: "Check if polygon has at least 3 vertices" },
    ],
  },
  {
    name: "TileCollisionData",
    signature: "class TileCollisionData",
    description: "Collision data for a single tile.",
    properties: [
      { name: "tile_id", type: "int", description: "Tile variant index" },
      { name: "shapes", type: "List[CollisionPolygon]", description: "All collision shapes for this tile" },
    ],
    methods: [
      { name: "has_collision", signature: "has_collision() -> bool", description: "Check if tile has any valid collision shapes" },
    ],
  },
  {
    name: "TilesetCollision",
    signature: "class TilesetCollision",
    description: "Complete collision data for a tileset.",
    properties: [
      { name: "tileset_name", type: "str", description: "Name of the tileset" },
      { name: "tile_size", type: "IntPoint", description: "(width, height) of each tile" },
      { name: "tiles", type: "Dict[int, TileCollisionData]", description: "Collision data keyed by tile_id" },
    ],
    methods: [
      { name: "get_tile_collision", signature: "get_tile_collision(tile_id: int) -> TileCollisionData | None", description: "Get collision data for a specific tile" },
      { name: "has_collision", signature: "has_collision(tile_id: int) -> bool", description: "Check if tile has collision data" },
      { name: "get_world_shapes", signature: "get_world_shapes(tile_id: int, tile_x: float, tile_y: float) -> List[CollisionPolygon]", description: "Get collision shapes transformed to world space" },
    ],
  },
  {
    name: "RectangleShape",
    signature: "class RectangleShape",
    description: "Rectangle collision shape for character collision.",
    properties: [
      { name: "width", type: "float", description: "Width of rectangle" },
      { name: "height", type: "float", description: "Height of rectangle" },
      { name: "offset", type: "Point", description: "Offset from sprite position (default: (0, 0))" },
    ],
    methods: [
      { name: "get_bounds", signature: "get_bounds(x: float, y: float) -> Tuple[float, float, float, float]", description: "Get AABB bounds in world space (left, top, right, bottom)" },
    ],
  },
  {
    name: "CircleShape",
    signature: "class CircleShape",
    description: "Circle collision shape for character collision.",
    properties: [
      { name: "radius", type: "float", description: "Radius of circle" },
      { name: "offset", type: "Point", description: "Offset from sprite position (default: (0, 0))" },
    ],
    methods: [
      { name: "get_center", signature: "get_center(x: float, y: float) -> Point", description: "Get center position in world space" },
    ],
  },
  {
    name: "CapsuleShape",
    signature: "class CapsuleShape",
    description: "Capsule collision shape (vertical orientation) for character collision.",
    properties: [
      { name: "radius", type: "float", description: "Radius of the capsule" },
      { name: "height", type: "float", description: "Total height including hemispheres" },
      { name: "offset", type: "Point", description: "Offset from sprite position (default: (0, 0))" },
    ],
    methods: [
      { name: "get_top_center", signature: "get_top_center(x: float, y: float) -> Point", description: "Get top circle center in world space" },
      { name: "get_bottom_center", signature: "get_bottom_center(x: float, y: float) -> Point", description: "Get bottom circle center in world space" },
    ],
  },
  {
    name: "CharacterCollision",
    signature: "class CharacterCollision",
    description: "Complete collision data for a character sprite.",
    properties: [
      { name: "name", type: "str", description: "Character name" },
      { name: "shape", type: "CharacterShapeType", description: "RectangleShape, CircleShape, or CapsuleShape" },
      { name: "properties", type: "Dict[str, Any]", description: "Custom properties from editor" },
    ],
  },
  {
    name: "CollisionCache",
    signature: "class CollisionCache",
    description: "Optimized collision data cache with fast lookups. Caches parsed collision data to avoid repeated file I/O.",
    methods: [
      { name: "get_tileset_collision", signature: "get_tileset_collision(tileset_path: PathLike) -> TilesetCollision | None", description: "Get tileset collision data (cached)" },
      { name: "get_character_collision", signature: "get_character_collision(sprite_path: PathLike) -> CharacterCollision | None", description: "Get character collision data (cached)" },
      { name: "clear", signature: "clear()", description: "Clear all cached collision data" },
      { name: "preload_tileset", signature: "preload_tileset(tileset_path: PathLike)", description: "Preload tileset collision data into cache" },
      { name: "preload_character", signature: "preload_character(sprite_path: PathLike)", description: "Preload character collision data into cache" },
    ],
  },
];

export const collisionRunnerClasses: ClassEntry[] = [
  {
    name: "MovementMode",
    signature: "class MovementMode(Enum)",
    description: "Movement modes for collision runner.",
    properties: [
      { name: "SLIDE", type: "MovementMode", description: "Smooth sliding along walls (top-down games)" },
      { name: "PLATFORMER", type: "MovementMode", description: "Gravity-based movement with jumping (platformer games)" },
      { name: "RPG", type: "MovementMode", description: "Full blocking with no sliding (RPG games)" },
    ],
  },
  {
    name: "CollisionResult",
    signature: "class CollisionResult",
    description: "Result of collision detection and resolution.",
    properties: [
      { name: "collided", type: "bool", description: "Whether any collision occurred" },
      { name: "final_x", type: "float", description: "Final X position after collision resolution" },
      { name: "final_y", type: "float", description: "Final Y position after collision resolution" },
      { name: "hit_wall_x", type: "bool", description: "Whether sprite hit a vertical wall" },
      { name: "hit_wall_y", type: "bool", description: "Whether sprite hit a horizontal wall" },
      { name: "hit_ceiling", type: "bool", description: "Whether sprite hit a ceiling" },
      { name: "on_ground", type: "bool", description: "Whether sprite is on ground (platformer)" },
      { name: "slide_vector", type: "Vector2 | None", description: "Slide direction if sliding" },
    ],
  },
  {
    name: "CollisionRunner",
    signature: "class CollisionRunner",
    description: "Ready-to-use collision runner with multiple movement modes. Handles collision detection and response for common game types.",
    properties: [
      { name: "cache", type: "CollisionCache", description: "Collision data cache" },
      { name: "tile_size", type: "IntPoint", description: "(width, height) of tiles in pixels" },
      { name: "mode", type: "MovementMode", description: "Current movement mode" },
      { name: "gravity", type: "float", description: "Gravity acceleration (px/s²)" },
      { name: "max_fall_speed", type: "float", description: "Maximum falling speed (px/s)" },
      { name: "jump_strength", type: "float", description: "Jump velocity (negative = upward)" },
      { name: "slide_friction", type: "float", description: "Friction coefficient for sliding" },
    ],
    methods: [
      {
        name: "__init__",
        signature: "__init__(collision_cache: CollisionCache, tile_size?: tuple, mode?: MovementMode)",
        description: "Initialize collision runner.",
      },
      {
        name: "from_game_type",
        signature: "from_game_type(game_type: str, collision_cache: CollisionCache, tile_size?: tuple, strict?: bool) -> CollisionRunner",
        description: "Factory method to create a preset collision runner. Recommended way to create runners.",
        parameters: [
          { name: "game_type", type: "str", description: "'platformer', 'topdown', or 'rpg'" },
        ],
      },
      {
        name: "move",
        signature: "move(sprite, tileset_collision, tile_map, delta_x?, delta_y?, dt?, **kwargs) -> CollisionResult",
        description: "Move sprite using configured movement mode. Delegates to move_and_slide, move_platformer, or move_rpg.",
      },
      {
        name: "move_and_slide",
        signature: "move_and_slide(sprite, tileset_collision, tile_map, delta_x, delta_y, slope_slide?) -> CollisionResult",
        description: "Move with sliding collision response. Best for top-down games.",
      },
      {
        name: "move_platformer",
        signature: "move_platformer(sprite, tileset_collision, tile_map, dt, input_x?, jump_pressed?) -> CollisionResult",
        description: "Move with platformer physics (gravity, jumping). Best for side-scrollers.",
      },
      {
        name: "move_rpg",
        signature: "move_rpg(sprite, tileset_collision, tile_map, delta_x, delta_y) -> CollisionResult",
        description: "Move with RPG-style blocking (no sliding). Best for grid-based RPGs.",
      },
      {
        name: "validate_config",
        signature: "validate_config(strict?: bool)",
        description: "Validate current configuration for consistency. Raises errors/warnings for issues.",
      },
      {
        name: "get_tile_at",
        signature: "get_tile_at(world_x: float, world_y: float) -> IntPoint",
        description: "Convert world position to tile coordinates.",
      },
      {
        name: "get_nearby_tile_shapes",
        signature: "get_nearby_tile_shapes(tileset_collision, tile_map, sprite, margin?) -> List[CollisionPolygon]",
        description: "Get all collision shapes near sprite for efficient collision checking.",
      },
    ],
    examples: [
      {
        code: `from tilemap_parser import CollisionRunner, CollisionCache

# Create cache and runner
cache = CollisionCache()
runner = CollisionRunner.from_game_type('platformer', cache, (32, 32))

# In game loop
result = runner.move(
    player,
    tileset_collision,
    tile_map,
    dt=delta_time,
    input_x=input_x,
    jump_pressed=jump_pressed
)`,
        description: "Basic platformer setup",
      },
      {
        code: `from tilemap_parser import CollisionRunner, CollisionCache

cache = CollisionCache()
runner = CollisionRunner.from_game_type('topdown', cache, (32, 32))

# In game loop
result = runner.move(player, tileset_collision, tile_map, dx, dy)`,
        description: "Top-down movement",
      },
    ],
  },
];