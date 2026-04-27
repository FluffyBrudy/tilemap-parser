import { motion } from "framer-motion";

export function TechnicalPage() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-4xl space-y-12"
    >
      <div>
        <h2 className="text-2xl font-semibold text-zinc-100 mb-2">Technical Documentation</h2>
        <p className="text-zinc-400">
          Internal architecture, performance considerations, and error handling patterns for power users.
        </p>
      </div>

      <DataFlowSection />
      <PerformanceSection />
      <ErrorHandlingSection />
      <ArchitectureSection />
    </motion.div>
  );
}

function DataFlowSection() {
  return (
    <section>
      <h3 className="text-lg font-medium text-zinc-200 mb-4">Data Flow</h3>
      <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
        <FlowDiagram />
        <div className="mt-6 space-y-4">
          <FlowStep step="1" title="Editor Export" desc="tilemap-editor saves JSON files (maps, animations, collision data) to disk." />
          <FlowStep step="2" title="Parser Load" desc="tilemap-parser reads JSON via parse_map_file(), parse_animation_file(), load_tileset_collision() etc." />
          <FlowStep step="3" title="Data Parsing" desc="JSON is validated and converted to typed Python dataclasses (ParsedMap, AnimationLibrary, TilesetCollision)." />
          <FlowStep step="4" title="Image Loading" desc="Tileset/spritesheet images are loaded via pygame and converted to surfaces." />
          <FlowStep step="5" title="Runtime Use" desc="Game engine uses TilemapData, SpriteAnimationSet, CollisionRunner for gameplay." />
        </div>
      </div>
    </section>
  );
}

function FlowDiagram() {
  return (
    <div className="flex items-center justify-center gap-2 flex-wrap">
      <Box label="Editor" sub="tilemap-editor" />
      <Arrow />
      <Box label="JSON Files" sub=".json, .anim.json, .collision.json" />
      <Arrow />
      <Box label="Parser" sub="tilemap-parser" />
      <Arrow />
      <Box label="Python Objects" sub="Typed dataclasses" />
      <Arrow />
      <Box label="Game Engine" sub="Pygame runtime" />
    </div>
  );
}

function Box({ label, sub }: { label: string; sub: string }) {
  return (
    <div className="bg-zinc-800 rounded-lg px-4 py-2 text-center border border-zinc-700">
      <div className="text-sm text-zinc-100 font-medium">{label}</div>
      <div className="text-xs text-zinc-500">{sub}</div>
    </div>
  );
}

function Arrow() {
  return <span className="text-zinc-600 text-xl">→</span>;
}

function FlowStep({ step, title, desc }: { step: string; title: string; desc: string }) {
  return (
    <div className="flex gap-3">
      <div className="w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center shrink-0">
        <span className="text-xs text-zinc-400">{step}</span>
      </div>
      <div>
        <div className="text-sm font-medium text-zinc-200">{title}</div>
        <div className="text-xs text-zinc-500">{desc}</div>
      </div>
    </div>
  );
}

function PerformanceSection() {
  return (
    <section>
      <h3 className="text-lg font-medium text-zinc-200 mb-4">Performance Considerations</h3>
      <div className="space-y-4">
        <PerformanceCard
          title="warm_cache()"
          desc="Pre-loads all tile surfaces into memory before rendering."
          benefit="Eliminates per-frame subsurface extraction, reducing CPU overhead."
          code={`renderer = TileLayerRenderer(data)
renderer.warm_cache()  # Call once at startup

# Now render() is faster
stats = renderer.render(screen, camera_xy=(x, y))`}
        />

        <PerformanceCard
          title="CollisionCache"
          desc="Caches parsed collision data to avoid repeated file I/O and parsing."
          benefit="First access parses JSON; subsequent accesses return cached data instantly."
          code={`cache = CollisionCache()

# First call - reads and parses file
collision = cache.get_tileset_collision("terrain.collision.json")

# All subsequent calls - returns cached data
collision = cache.get_tileset_collision("terrain.collision.json")  # instant

# Preload multiple tilesets at startup
for path in tileset_paths:
    cache.preload_tileset(path)`}
        />

        <PerformanceCard
          title="Viewport Culling"
          desc="TileLayerRenderer only draws tiles within the visible viewport."
          benefit="Reduces draw calls significantly for large maps."
          code={`# render() automatically culls tiles outside viewport
stats = renderer.render(
    screen,
    camera_xy=(cam_x, cam_y),
    viewport_size=(800, 600)  # Optional override
)

# stats.drawn_tiles shows tiles rendered
# stats.skipped_tiles shows tiles skipped`}
        />

        <PerformanceCard
          title="Lazy Loading"
          desc="load_map() supports skipping missing images for faster startup."
          benefit="Allows the game to run even if some tilesets are missing."
          code={`# Default: skip missing tileset images with warning
data = load_map("map.json")

# Strict mode: raise error if any tileset is missing
data = load_map("map.json", skip_missing_images=False)`}
        />
      </div>
    </section>
  );
}

function PerformanceCard({ title, desc, benefit, code }: { title: string; desc: string; benefit: string; code: string }) {
  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden">
      <div className="p-4">
        <code className="text-amber-400 font-mono">{title}()</code>
        <p className="text-sm text-zinc-400 mt-1">{desc}</p>
        <p className="text-sm text-zinc-500 mt-1"><span className="text-green-400">Benefit:</span> {benefit}</p>
      </div>
      <pre className="bg-zinc-950 px-4 py-3 text-xs font-mono text-zinc-300 overflow-x-auto border-t border-zinc-800">
        {code}
      </pre>
    </div>
  );
}

function ErrorHandlingSection() {
  return (
    <section>
      <h3 className="text-lg font-medium text-zinc-200 mb-4">Error Handling Patterns</h3>
      <div className="space-y-4">
        <ErrorCard
          error="MapParseError"
          desc="Raised when tilemap JSON parsing fails"
          causes={["Invalid JSON syntax", "Missing required fields", "Invalid data types", "Non-existent tileset paths"]}
          handling={`try:
    data = load_map("map.json")
except MapParseError as e:
    print(f"Failed to load map: {e}")
    # Handle gracefully - show error screen, load fallback map, etc.`}
        />

        <ErrorCard
          error="AnimationParseError"
          desc="Raised when animation JSON parsing fails"
          causes={["Invalid animation structure", "Unknown shape type", "Invalid frame data", "Missing spritesheet"]}
          handling={`try:
    anim = SpriteAnimationSet.load("hero.anim.json")
except AnimationParseError as e:
    print(f"Failed to load animation: {e}")
    # Fall back to static sprite`}
        />

        <ErrorCard
          error="CollisionParseError"
          desc="Raised when collision data parsing fails"
          causes={["Invalid polygon vertices", "Unknown character shape type", "Invalid collision file format"]}
          handling={`try:
    collision = load_tileset_collision("tileset.png")
    if collision is None:
        # File doesn't exist - optional collision data
        collision = None
except CollisionParseError as e:
    print(f"Invalid collision file: {e}")
    collision = None  # Continue without collision`}
        />

        <ErrorCard
          error="pygame.error"
          desc="Raised when image loading fails"
          causes={["Unsupported image format", "Corrupt image file", "File permissions"]}
          handling={`try:
    surface = pygame.image.load("tileset.png")
except pygame.error as e:
    print(f"Image load failed: {e}")
    # Use placeholder or disable rendering for this tileset`}
        />
      </div>
    </section>
  );
}

function ErrorCard({ error, desc, causes, handling }: { error: string; desc: string; causes: string[]; handling: string }) {
  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden">
      <div className="p-4 border-b border-zinc-800">
        <code className="text-red-400 font-mono">{error}</code>
        <p className="text-sm text-zinc-400 mt-1">{desc}</p>
      </div>
      <div className="p-4 border-b border-zinc-800">
        <h4 className="text-xs text-zinc-500 uppercase mb-2">Common Causes</h4>
        <ul className="text-xs text-zinc-400 space-y-1">
          {causes.map(cause => <li>• {cause}</li>)}
        </ul>
      </div>
      <div className="p-4">
        <h4 className="text-xs text-zinc-500 uppercase mb-2">Handling Pattern</h4>
        <pre className="text-xs font-mono text-zinc-300 whitespace-pre-wrap">{handling}</pre>
      </div>
    </div>
  );
}

function ArchitectureSection() {
  return (
    <section>
      <h3 className="text-lg font-medium text-zinc-200 mb-4">Internal Architecture</h3>
      <div className="grid grid-cols-2 gap-4">
        <ArchitectureCard
          title="Map Parsing Pipeline"
          items={[
            "parse_map_file() → reads JSON file",
            "parse_map_json() → parses string",
            "parse_map_dict() → validates and converts",
            "Returns ParsedMap with all data",
            "load_map() wraps with pygame image loading",
          ]}
        />
        <ArchitectureCard
          title="Animation Pipeline"
          items={[
            "parse_animation_file() → reads .anim.json",
            "SpriteAnimationSet.load() → loads spritesheet",
            "AnimationLibrary → stores all clips",
            "AnimationPlayer → manages playback state",
          ]}
        />
        <ArchitectureCard
          title="Collision Pipeline"
          items={[
            "load_tileset_collision() → sidecar .collision.json",
            "CollisionCache → global singleton cache",
            "get_cached_tileset_collision() → cached access",
            "CollisionRunner → movement + collision",
          ]}
        />
        <ArchitectureCard
          title="Rendering Pipeline"
          items={[
            "TileLayerRenderer → wraps TilemapData",
            "get_tile_layers_dict() → indexes layers",
            "warm_cache() → pre-extracts surfaces",
            "render() → viewport culling + blit",
          ]}
        />
      </div>

      <div className="mt-6 bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h4 className="text-sm font-medium text-zinc-200 mb-3">Key Class Relationships</h4>
        <pre className="text-xs font-mono text-zinc-400">{`TilemapData
├── ParsedMap (parsed.meta, parsed.layers, parsed.tilesets)
├── surfaces[] (pygame.Surface for each tileset)
└── methods: get_layers(), get_tile_surface(), etc.

TileLayerRenderer
├── TilemapData (data)
├── tile_layers{} (dict of ParsedLayer)
├── _variant_cache{} (cached tile surfaces)
└── methods: warm_cache(), render()

SpriteAnimationSet
├── AnimationLibrary (animations{})
├── surface (pygame.Surface spritesheet)
└── methods: get_image(variant_id)

CollisionRunner
├── CollisionCache (cache)
├── MovementMode (SLIDE, PLATFORMER, RPG)
└── methods: move(), move_and_slide(), move_platformer()`}</pre>
      </div>
    </section>
  );
}

function ArchitectureCard({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
      <h4 className="text-sm font-medium text-zinc-200 mb-3">{title}</h4>
      <ul className="text-xs text-zinc-400 space-y-1">
        {items.map((item, i) => <li key={i}>• {item}</li>)}
      </ul>
    </div>
  );
}