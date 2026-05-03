export interface ApiParameter {
  name: string;
  type: string;
  optional?: boolean;
  description: string;
}

export interface ApiExample {
  title?: string;
  code: string;
  description?: string;
}

export interface ApiEntry {
  name: string;
  signature: string;
  description: string;
  parameters?: ApiParameter[];
  returns?: string;
  examples?: ApiExample[];
  notes?: string[];
}

export interface ClassMethod {
  name: string;
  signature: string;
  description: string;
  parameters?: ApiParameter[];
  returns?: string;
}

export interface ClassEntry {
  name: string;
  signature: string;
  description: string;
  properties?: { name: string; type: string; description: string }[];
  methods?: ClassMethod[];
  examples?: ApiExample[];
}

export interface ModuleEntry {
  name: string;
  description: string;
  items: string[];
}

export interface ApiConfig {
  packageName: string;
  version: string;
  description: string;
  modules: ModuleEntry[];
  functions: ApiEntry[];
  classes: ClassEntry[];
}

export const apiConfig: ApiConfig = {
  packageName: "tilemap-parser",
  version: "2.0.0",
  description:
    "Standalone parser/loader for tilemap-editor JSON maps and sprite animation JSON",
  modules: [
    {
      name: "tilemap_parser",
      description: "Main module with all public exports",
      items: [
        "load_map",
        "TilemapData",
        "parse_map_dict",
        "parse_map_file",
        "parse_map_json",
        "SpriteAnimationSet",
        "AnimationPlayer",
        "TileLayerRenderer",
      ],
    },
  ],
  functions: [
    {
      name: "load_map",
      signature:
        "load_map(path: PathLike, *, extra_search_base?: Path, skip_missing_images?: bool) -> TilemapData",
      description:
        "Load and parse a tilemap JSON file from disk. Returns a TilemapData object with access to layers, tilesets, and tile images.",
      parameters: [
        {
          name: "path",
          type: "PathLike",
          description: "Path to the JSON map file",
        },
        {
          name: "extra_search_base",
          type: "Path | None",
          optional: true,
          description: "Additional directory to search for tileset images",
        },
        {
          name: "skip_missing_images",
          type: "bool",
          optional: true,
          description:
            "Continue loading even if tileset images are missing (default: True)",
        },
      ],
      returns: "TilemapData",
      examples: [
        {
          code: 'from tilemap_parser import load_map\n\ndata = load_map("assets/maps/level_1.json")',
          description: "Load a tilemap file",
        },
      ],
    },
    {
      name: "parse_map_dict",
      signature: "parse_map_dict(root: dict) -> ParsedMap",
      description:
        "Parse a tilemap from a Python dict. Returns a ParsedMap with all map data but no loaded images.",
      returns: "ParsedMap",
    },
    {
      name: "parse_map_json",
      signature: "parse_map_json(text: str) -> ParsedMap",
      description: "Parse a tilemap from a JSON string.",
      returns: "ParsedMap",
    },
    {
      name: "parse_map_file",
      signature: "parse_map_file(path: PathLike) -> ParsedMap",
      description:
        "Parse a tilemap JSON file into a ParsedMap. Does not load any tile images.",
      returns: "ParsedMap",
    },
    {
      name: "parse_animation_dict",
      signature: "parse_animation_dict(data: dict) -> AnimationLibrary",
      description: "Parse sprite animation data from a Python dict.",
      returns: "AnimationLibrary",
    },
    {
      name: "parse_animation_json",
      signature: "parse_animation_json(text: str) -> AnimationLibrary",
      description: "Parse sprite animation data from a JSON string.",
      returns: "AnimationLibrary",
    },
    {
      name: "parse_animation_file",
      signature: "parse_animation_file(path: PathLike) -> AnimationLibrary",
      description: "Parse sprite animation data from a JSON file.",
      returns: "AnimationLibrary",
    },
  ],
  classes: [
    {
      name: "TilemapData",
      signature: "class TilemapData",
      description:
        "Main class for accessing loaded tilemap data. Provides methods to query layers, tiles, and retrieve tile surfaces for rendering.",
      properties: [
        {
          name: "tile_size",
          type: "Tuple[int, int]",
          description: "Width and height of each tile in pixels",
        },
        {
          name: "map_size",
          type: "Tuple[int, int]",
          description: "Width and height of the map in tiles",
        },
        {
          name: "map_path",
          type: "Path | None",
          description: "Path to the loaded map file",
        },
      ],
      methods: [
        {
          name: "get_layers",
          signature:
            "get_layers(*, include_hidden?: bool, layer_type?: str, sort_by_zindex?: bool) -> List[ParsedLayer]",
          description:
            "Get all layers, optionally filtered by type or visibility. Sorted by z_index by default.",
          parameters: [
            {
              name: "include_hidden",
              type: "bool",
              optional: true,
              description: "Include hidden layers (default: True)",
            },
            {
              name: "layer_type",
              type: "str | None",
              optional: true,
              description: "Filter by 'tile' or 'object'",
            },
            {
              name: "sort_by_zindex",
              type: "bool",
              optional: true,
              description: "Sort by z_index (default: True)",
            },
          ],
          returns: "List[ParsedLayer]",
        },
        {
          name: "get_layer",
          signature:
            "get_layer(layer_id_or_name: int | str) -> ParsedLayer | None",
          description: "Get a layer by its ID or name.",
          returns: "ParsedLayer | None",
        },
        {
          name: "get_tile_layers_dict",
          signature:
            "get_tile_layers_dict(*, include_hidden?: bool) -> Dict[int, ParsedLayer]",
          description: "Get all tile layers as a dictionary keyed by layer ID.",
        },
        {
          name: "get_raw",
          signature: "get_raw() -> dict",
          description:
            "Get the complete raw map data as a dict. Returns a deep copy for safe inspection.",
        },
        {
          name: "get_image",
          signature:
            "get_image(variant: int, ttype?: int, *, copy_surface?: bool) -> Surface | None",
          description:
            "Extract a single tile surface by variant index and tileset.",
          parameters: [
            {
              name: "variant",
              type: "int",
              description: "Tile variant index within the tileset",
            },
            {
              name: "ttype",
              type: "int",
              optional: true,
              description: "Tileset index (default: 0)",
            },
          ],
        },
        {
          name: "get_tile_surface",
          signature:
            "get_tile_surface(ttype: int, variant: int, *, copy_surface?: bool) -> Surface | None",
          description:
            "Extract a tile surface. Alias for get_image() with swapped argument order.",
        },
        {
          name: "get_tile_at",
          signature:
            "get_tile_at(layer_id_or_name: int | str, x: int, y: int) -> ParsedTile | None",
          description: "Get the tile at a specific grid position in a layer.",
        },
        {
          name: "get_tile_surface_at",
          signature:
            "get_tile_surface_at(layer_id_or_name: int | str, x: int, y: int) -> Surface | None",
          description: "Get the tile surface at a specific grid position.",
        },
      ],
      examples: [
        {
          code: `from tilemap_parser import load_map

data = load_map("level_1.json")

# Get all layers sorted by z_index
layers = data.get_layers(sort_by_zindex=True)
for layer in layers:
    print(f"{layer.name}: {layer.layer_type}")

# Get a specific layer by name
terrain = data.get_layer("Ground")
if terrain:
    tile = terrain.tiles.get((5, 3))
    
# Get tile surface for rendering
surface = data.get_tile_surface_at("Ground", 5, 3)`,
        },
      ],
    },
    {
      name: "ParsedMap",
      signature: "class ParsedMap",
      description:
        "Pure data class containing parsed tilemap data without loaded images.",
      properties: [
        {
          name: "meta",
          type: "ParsedMeta",
          description: "Map metadata (tile size, map size, etc.)",
        },
        {
          name: "layers",
          type: "List[ParsedLayer]",
          description: "All parsed layers",
        },
        {
          name: "tilesets",
          type: "List[ParsedTileset]",
          description: "All tileset definitions",
        },
        {
          name: "project_state",
          type: "ParsedProjectState",
          description: "Autotile rules and groups",
        },
        { name: "raw", type: "dict", description: "Complete raw JSON data" },
      ],
    },
    {
      name: "ParsedLayer",
      signature: "class ParsedLayer",
      description: "Represents a single layer in the tilemap.",
      properties: [
        { name: "id", type: "int", description: "Unique layer identifier" },
        { name: "name", type: "str", description: "Layer name" },
        { name: "layer_type", type: "str", description: "'tile' or 'object'" },
        {
          name: "visible",
          type: "bool",
          description: "Whether layer is visible",
        },
        {
          name: "locked",
          type: "bool",
          description: "Whether layer is locked",
        },
        {
          name: "opacity",
          type: "float",
          description: "Layer opacity (0.0 to 1.0)",
        },
        { name: "z_index", type: "int", description: "Render order" },
        { name: "properties", type: "dict", description: "Custom properties" },
        {
          name: "tiles",
          type: "Dict[Point, ParsedTile]",
          description: "Tiles keyed by (x, y) position",
        },
        {
          name: "objects",
          type: "Dict[int, ParsedObject]",
          description: "Objects keyed by ID (object layers only)",
        },
      ],
    },
    {
      name: "ParsedTile",
      signature: "class ParsedTile",
      description: "Represents a single tile in a layer.",
      properties: [
        { name: "pos", type: "Point", description: "(x, y) grid position" },
        {
          name: "ttype",
          type: "TilesetRef",
          description: "Tileset index or path reference",
        },
        { name: "variant", type: "int", description: "Tile variant index" },
        {
          name: "properties",
          type: "dict | None",
          description: "Custom tile properties",
        },
      ],
    },
    {
      name: "ParsedTileset",
      signature: "class ParsedTileset",
      description: "Tileset definition with path and properties.",
      properties: [
        { name: "path", type: "str", description: "Path to the tileset image" },
        {
          name: "type",
          type: "str",
          description: "Tileset type (usually 'tile')",
        },
        {
          name: "properties",
          type: "dict",
          description: "Tileset-level properties",
        },
        {
          name: "tile_properties",
          type: "dict",
          description: "Per-tile properties keyed by variant",
        },
      ],
    },
    {
      name: "ParsedMeta",
      signature: "class ParsedMeta",
      description: "Map metadata.",
      properties: [
        {
          name: "tile_size",
          type: "Point",
          description: "(width, height) of each tile",
        },
        {
          name: "map_size",
          type: "Point",
          description: "(width, height) of map in tiles",
        },
        {
          name: "initial_map_size",
          type: "Point",
          description: "Initial map size when created",
        },
        { name: "zoom_level", type: "float", description: "Editor zoom level" },
        {
          name: "scroll",
          type: "Point",
          description: "Editor scroll position",
        },
        { name: "version", type: "str", description: "Map format version" },
      ],
    },
    {
      name: "SpriteAnimationSet",
      signature: "class SpriteAnimationSet",
      description:
        "Loaded sprite animation with spritesheet surface. Provides methods to extract animation frames.",
      properties: [
        {
          name: "library",
          type: "AnimationLibrary",
          description: "Animation definitions",
        },
        {
          name: "surface",
          type: "Surface",
          description: "Loaded spritesheet surface",
        },
        {
          name: "warnings",
          type: "List[str]",
          description: "Warnings during loading",
        },
      ],
      methods: [
        {
          name: "load",
          signature:
            "load(json_path: PathLike, *, spritesheet_path?: PathLike, extra_search_base?: Path) -> SpriteAnimationSet",
          description:
            "Factory method to load an animation set from JSON and spritesheet.",
          parameters: [
            {
              name: "json_path",
              type: "PathLike",
              description: "Path to animation JSON file",
            },
            {
              name: "spritesheet_path",
              type: "PathLike | None",
              optional: true,
              description: "Override spritesheet path",
            },
            {
              name: "extra_search_base",
              type: "Path | None",
              optional: true,
              description: "Additional search directory",
            },
          ],
          returns: "SpriteAnimationSet",
        },
        {
          name: "get_image",
          signature:
            "get_image(variant_id: int, *, copy_surface?: bool) -> Surface | None",
          description: "Extract a frame from the spritesheet by variant ID.",
        },
      ],
      examples: [
        {
          code: `from tilemap_parser import SpriteAnimationSet

anim_set = SpriteAnimationSet.load("hero.anim.json")
frame = anim_set.get_image(0)  # Get first frame`,
        },
      ],
    },
    {
      name: "AnimationPlayer",
      signature: "class AnimationPlayer",
      description:
        "Plays sprite animations with frame timing and looping support.",
      properties: [
        {
          name: "clip",
          type: "AnimationClip | None",
          description: "Current animation clip",
        },
        {
          name: "finished",
          type: "bool",
          description: "Whether animation has finished (non-looping)",
        },
        {
          name: "frame_index",
          type: "int",
          description: "Current frame index",
        },
      ],
      methods: [
        {
          name: "__init__",
          signature:
            "__init__(animation_set: SpriteAnimationSet, animation_name: str)",
          description: "Create a player for a named animation.",
        },
        {
          name: "reset",
          signature: "reset()",
          description: "Reset playback to frame 0.",
        },
        {
          name: "update",
          signature: "update(dt_ms: float)",
          description: "Advance playback by delta time in milliseconds.",
        },
        {
          name: "get_current_image",
          signature: "get_current_image() -> Surface | None",
          description: "Get the current frame surface for rendering.",
        },
      ],
      examples: [
        {
          code: `from tilemap_parser import SpriteAnimationSet, AnimationPlayer

anim_set = SpriteAnimationSet.load("hero.anim.json")
player = AnimationPlayer(anim_set, "idle")

# In game loop
player.update(16.67)  # ~60fps
frame_surface = player.get_current_image()`,
        },
      ],
    },
    {
      name: "AnimationClip",
      signature: "class AnimationClip",
      description: "A single animation sequence with frames and metadata.",
      properties: [
        { name: "name", type: "str", description: "Animation name" },
        {
          name: "frames",
          type: "List[AnimationFrame]",
          description: "Frame data",
        },
        { name: "loop", type: "bool", description: "Whether animation loops" },
        { name: "fps", type: "float", description: "Target frames per second" },
        { name: "metadata", type: "dict", description: "Custom metadata" },
        {
          name: "markers",
          type: "List[AnimationMarker]",
          description: "Frame markers",
        },
      ],
      methods: [
        {
          name: "frame_count",
          signature: "frame_count() -> int",
          description: "Total number of frames",
        },
        {
          name: "total_duration_ms",
          signature: "total_duration_ms() -> float",
          description: "Total duration in milliseconds",
        },
      ],
    },
    {
      name: "AnimationLibrary",
      signature: "class AnimationLibrary",
      description: "Container for all animations in a spritesheet.",
      properties: [
        {
          name: "animations",
          type: "Dict[str, AnimationClip]",
          description: "Animations keyed by name",
        },
        {
          name: "spritesheet_path",
          type: "str | None",
          description: "Path to spritesheet",
        },
        {
          name: "tile_size",
          type: "Tuple[int, int]",
          description: "Frame size",
        },
      ],
      methods: [
        {
          name: "get",
          signature: "get(name: str) -> AnimationClip | None",
          description: "Get animation by name",
        },
      ],
    },
    {
      name: "TileLayerRenderer",
      signature: "class TileLayerRenderer",
      description:
        "Pygame renderer for tile layers with camera support and caching.",
      methods: [
        {
          name: "__init__",
          signature:
            "__init__(data: TilemapData, *, include_hidden_layers?: bool)",
          description: "Initialize renderer with tilemap data.",
        },
        {
          name: "warm_cache",
          signature: "warm_cache()",
          description:
            "Pre-load all tile surfaces into cache for faster rendering.",
        },
        {
          name: "render",
          signature:
            "render(target: Surface, camera_xy?: tuple, viewport_size?: tuple) -> LayerRenderStats",
          description:
            "Render visible tile layers. Only tiles within viewport + buffer are drawn.",
          parameters: [
            {
              name: "target",
              type: "Surface",
              description: "Pygame surface to render onto",
            },
            {
              name: "camera_xy",
              type: "tuple",
              optional: true,
              description: "Camera position (x, y)",
            },
            {
              name: "viewport_size",
              type: "tuple | None",
              optional: true,
              description: "Viewport size override",
            },
          ],
          returns: "LayerRenderStats",
        },
      ],
      examples: [
        {
          code: `import pygame
from tilemap_parser import TileLayerRenderer, load_map

pygame.init()
screen = pygame.display.set_mode((1280, 720))

data = load_map("level_1.json")
renderer = TileLayerRenderer(data)
renderer.warm_cache()

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill((0, 0, 0))
    stats = renderer.render(screen, camera_xy=(cam_x, cam_y))
    pygame.display.flip()`,
        },
      ],
    },
    {
      name: "LayerRenderStats",
      signature: "class LayerRenderStats",
      description: "Statistics from a render operation.",
      properties: [
        {
          name: "drawn_tiles",
          type: "int",
          description: "Tiles actually drawn",
        },
        {
          name: "skipped_tiles",
          type: "int",
          description: "Tiles skipped (out of viewport)",
        },
        {
          name: "visible_layers",
          type: "int",
          description: "Number of visible layers rendered",
        },
      ],
    },
    {
      name: "MapParseError",
      signature: "class MapParseError(Exception)",
      description: "Raised when tilemap JSON parsing fails.",
    },
    {
      name: "AnimationParseError",
      signature: "class AnimationParseError(Exception)",
      description: "Raised when animation JSON parsing fails.",
    },
  ],
};
