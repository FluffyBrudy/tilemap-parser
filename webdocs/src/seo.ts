export const SITE_URL = "https://tilemap-parser.vercel.app";

export const SITE_DESCRIPTION =
  "tilemap-parser docs: map parser + pygame collision runtime for game developers.";

export type Seo = { title: string; description: string };

export const SEO: Record<string, Seo> = {
  "/": {
    title: "tilemap-parser — docs",
    description:
      "tilemap-parser loads, renders and simulates tilemap-editor maps in pygame: tile layers, collision, a movement runner and pathfinding.",
  },
  "/install": {
    title: "Installation — tilemap-parser docs",
    description:
      "pip install tilemap-parser. Python 3.10+, pygame-ce is the only dependency. Tilemap editor companion for authoring maps and collision files.",
  },
  "/quick-start": {
    title: "Quick Start — tilemap-parser docs",
    description:
      "The smallest working example: load a map, move a sprite against tiles and draw it, with CollisionRunner presets for platformer or top-down.",
  },
  "/physics": {
    title: "Physics & Bodies — tilemap-parser docs",
    description:
      "How tilemap-parser splits collision into tiles, bodies and the movement runner: primitives, PhysicsWorld, layer/mask rules.",
  },
  "/runner": {
    title: "CollisionRunner — tilemap-parser docs",
    description:
      "Move modes and presets: move_and_slide, move_platformer, move_rpg, move_grounded — plus tunables and config validation.",
  },
  "/object-collision": {
    title: "Object Collision — tilemap-parser docs",
    description:
      "Sprite-vs-sprite contact detection separate from tile collision: ObjectCollisionManager, layers and masks.",
  },
  "/pipeline": {
    title: "The Pipeline — tilemap-parser docs",
    description:
      "The whole flow in one script: load map, build PhysicsWorld, attach CollisionRunner, move a player, push a crate, draw.",
  },
  "/map-parsing": {
    title: "Map Parsing & Rendering — tilemap-parser docs",
    description:
      "Load tilemap-editor JSON into TilemapData, render with TileLayerRenderer, and how layers, tilesets and scrapers work.",
  },
  "/animations": {
    title: "Animations — tilemap-parser docs",
    description:
      "Frame-based sprites: SpriteAnimationSet loads JSON + spritesheet, AnimationPlayer is the per-frame clock.",
  },
  "/camera": {
    title: "Camera — tilemap-parser docs",
    description:
      "Viewport offsets in pygame: centered or deadzone follow modes, lerp smoothing, bounds clamping and screen shake.",
  },
  "/particles": {
    title: "Particles — tilemap-parser docs",
    description:
      "Particle effects in pygame: one config per effect, one ParticleSystem per emitter; bursts, screen-wide snow, fog fields.",
  },
  "/pathfinding": {
    title: "Pathfinding — tilemap-parser docs",
    description:
      "Tile-grid A* over your collision layer: NavGrid, PathFinder and PathFollower for NPC movement.",
  },
  "/examples": {
    title: "Examples — tilemap-parser docs",
    description:
      "Standalone runnable examples: tiny quest, platformers, physics-world, collision, pathfinding, particles and comparisons.",
  },
  "/examples/full-physics-world": {
    title: "Full Physics World example — tilemap-parser docs",
    description:
      "Complete annotated physics world: bodies, kinematic crates, movement and drawing in one running example.",
  },
  "/examples/full-collision": {
    title: "Full Collision example — tilemap-parser docs",
    description:
      "Complete annotated collision demo: runner phases, movement modes and layers in one running example.",
  },
  "/examples/full-pathfinding": {
    title: "Full Pathfinding example — tilemap-parser docs",
    description:
      "Click-to-play maze: NavGrid, PathFinder and PathFollower wired into a running example.",
  },
  "/api": {
    title: "API Reference — tilemap-parser docs",
    description:
      "The practical index of tilemap-parser APIs, grouped by purpose: loading, tiles, collision, runner, world, rendering, particles.",
  },
  "/json": {
    title: "JSON Formats — tilemap-parser docs",
    description:
      "Real map, tileset, collision, node and particle JSON from the editor, and what the parser exposes from each.",
  },
  "/notes": {
    title: "Technical Notes — tilemap-parser docs",
    description:
      "Edge conventions, scale rules and performance facts of tilemap-parser, stated precisely.",
  },
};

export type SitemapRoute = { path: string; priority: string };

export const SITEMAP_ROUTES: SitemapRoute[] = [
  { path: "/", priority: "1.0" },
  { path: "/install", priority: "0.7" },
  { path: "/quick-start", priority: "0.9" },
  { path: "/physics", priority: "0.8" },
  { path: "/runner", priority: "0.8" },
  { path: "/object-collision", priority: "0.8" },
  { path: "/pipeline", priority: "0.6" },
  { path: "/map-parsing", priority: "0.8" },
  { path: "/animations", priority: "0.7" },
  { path: "/camera", priority: "0.7" },
  { path: "/particles", priority: "0.8" },
  { path: "/pathfinding", priority: "0.8" },
  { path: "/examples", priority: "0.7" },
  { path: "/examples/full-physics-world", priority: "0.5" },
  { path: "/examples/full-collision", priority: "0.5" },
  { path: "/examples/full-pathfinding", priority: "0.5" },
  { path: "/api", priority: "0.9" },
  { path: "/json", priority: "0.8" },
  { path: "/notes", priority: "0.6" },
];