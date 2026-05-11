import { motion } from "framer-motion";
import { useParams, useNavigate } from "react-router-dom";
import { CodeBlock } from "../components/CodeBlock";
import fullGameSource from "../../../examples/game-example/src/game.py?raw";

const examples = [
  {
    id: "full-game",
    title: "Complete pygame demo",
    description:
      "The full examples/game-example project: map loading, tile rendering, sprite animation, camera tracking, top-down movement, collision response, and debug overlay.",
    difficulty: "Advanced",
    projectPath: "examples/game-example",
    runCommand: "python src/game.py",
    highlights: [
      "Loads data/map.json and renders visible map tiles with TileLayerRenderer",
      "Loads player animation clips from the animation JSON file",
      "Builds a tile collision lookup from every tile layer in the map",
      "Moves a player shape with CollisionRunner.move_and_slide",
      "Centers the camera on the player and draws a small debug HUD",
    ],
    features: [
      "Complete pygame loop",
      "Camera-follow tile rendering",
      "Top-down collision response",
      "Animation clip switching",
      "Debug overlay and controls",
      "Downloadable project assets",
    ],
    code: fullGameSource,
    downloadUrl: "/examples/full-game-example.zip",
    sourceUrl:
      "https://github.com/FluffyBrudy/tilemap-parser/tree/main/examples/game-example",
  },
  {
    id: "animation",
    title: "Animation Example",
    description:
      "Learn how to load and play sprite animations without any game logic or collision detection. Perfect for understanding the animation system.",
    difficulty: "Beginner",
    projectPath: "examples/animation-example",
    runCommand: "python main.py",
    highlights: [
      "Loads a sprite animation JSON file",
      "Creates an AnimationPlayer with a starting clip",
      "Switches animation clips from keyboard input",
    ],
    features: [
      "SpriteAnimationSet loading",
      "AnimationPlayer usage",
      "Simple pygame loop",
      "Animation switching with keyboard",
      "Frame-by-frame control",
    ],
    code: `# Animation focused code
from tilemap_parser import SpriteAnimationSet, AnimationPlayer
import pygame

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Load animation set
anim_set = SpriteAnimationSet.load("data/RACCOONSPRITESHEET.anim.json")

# Create animation player
anim_player = AnimationPlayer(anim_set, "idledown")

# Game loop
running = True
while running:
    dt = clock.tick(60) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Switch animations
            if event.key == pygame.K_w:
                anim_player.play("walkup")
            elif event.key == pygame.K_s:
                anim_player.play("walkdown")
    
    # Update animation
    anim_player.update(dt * 1000)  # dt in milliseconds
    
    # Render
    screen.fill((0, 0, 0))
    frame = anim_player.get_current_image()
    screen.blit(frame, (400 - frame.get_width()//2, 300 - frame.get_height()//2))
    pygame.display.flip()`,
    downloadUrl: "/examples/animation-example.zip",
    sourceUrl:
      "https://github.com/FluffyBrudy/tilemap-parser/tree/main/examples/animation-example",
  },
  {
    id: "collision",
    title: "Collision Example",
    description:
      "Focus on the collision system alone. Learn how to implement collision detection and response without animations or complex rendering.",
    difficulty: "Intermediate",
    projectPath: "examples/collision-example",
    runCommand: "python main.py",
    highlights: [
      "Loads tileset collision data through CollisionCache",
      "Builds the tile map used by the collision runner",
      "Draws collision tiles for debugging while the player moves",
    ],
    features: [
      "CollisionCache and CollisionRunner",
      "Tile-based collision detection",
      "Slope sliding support",
      "Debug visualization of collision tiles",
      "Multiple collision shapes",
    ],
    code: `# Collision focused code
from tilemap_parser import (
    load_map, TileLayerRenderer, 
    CollisionRunner, CollisionCache, RectangleShape
)
import pygame

# Load map and collision data
game_data = load_map("data/map.json")
renderer = TileLayerRenderer(game_data)
collision_cache = CollisionCache()
tileset_collision = collision_cache.get_tileset_collision(
    "data/collision/HiddenJungle_PNG.collision.json"
)

# Setup collision runner
collision_runner = CollisionRunner.from_game_type(
    'topdown', collision_cache, game_data.tile_size
)

# Build tile map for collision detection
tile_map = {}
for layer in game_data.parsed.layers:
    if layer.layer_type == "tile":
        for (tile_x, tile_y), tile in layer.tiles.items():
            if isinstance(tile.ttype, int):
                tile_map[(tile_x, tile_y)] = tile.variant

# Create player
player = RectangleShape(x=100, y=100, width=32, height=32)

# Game loop
while running:
    dt = clock.tick(60) / 1000.0
    
    # Get input
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 200 * dt
    dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 200 * dt
    
    # Move with collision
    result = collision_runner.move_and_slide(
        player, tileset_collision, tile_map, dx, dy, slope_slide=True
    )
    
    # Debug: Draw collision tiles
    for (tx, ty) in tile_map:
        if tileset_collision.has_collision(tile_map[(tx, ty)]):
            pygame.draw.rect(screen, (255, 0, 0, 100), 
                           (tx * 32, ty * 32, 32, 32), 2)`,
    downloadUrl: "/examples/collision-example.zip",
    sourceUrl:
      "https://github.com/FluffyBrudy/tilemap-parser/tree/main/examples/collision-example",
  },
];

export function Examples() {
  const { exampleId } = useParams();
  const navigate = useNavigate();
  const selectedExample = examples.find((ex) => ex.id === exampleId);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Beginner":
        return "text-green-400 bg-green-400/10 border-green-400/20";
      case "Intermediate":
        return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
      case "Advanced":
        return "text-red-400 bg-red-400/10 border-red-400/20";
      default:
        return "text-zinc-400 bg-zinc-400/10 border-zinc-400/20";
    }
  };

  if (selectedExample) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-5xl"
      >
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-zinc-500 mb-6">
          <button
            onClick={() => navigate("/examples")}
            className="hover:text-zinc-300 transition-colors"
          >
            Examples
          </button>
          <span>/</span>
          <span className="text-zinc-300">{selectedExample.title}</span>
        </div>

        <div className="mb-8">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold text-zinc-100">
              {selectedExample.title}
            </h1>
            <span
              className={`rounded-full border px-3 py-1 text-xs font-medium ${getDifficultyColor(selectedExample.difficulty)}`}
            >
              {selectedExample.difficulty}
            </span>
          </div>
          <p className="max-w-3xl text-lg leading-8 text-zinc-400">
            {selectedExample.description}
          </p>
        </div>

        <div className="mb-8 grid gap-4 rounded-lg border border-zinc-800 bg-zinc-950 p-5 md:grid-cols-3">
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
              Project
            </div>
            <div className="mt-2 font-mono text-sm text-zinc-200">
              {selectedExample.projectPath}
            </div>
          </div>
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
              Run
            </div>
            <div className="mt-2 font-mono text-sm text-zinc-200">
              {selectedExample.runCommand}
            </div>
          </div>
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
              Includes
            </div>
            <div className="mt-2 text-sm text-zinc-300">
              Source, JSON data, and image assets
            </div>
          </div>
        </div>

        <div className="mb-8 flex flex-wrap gap-3">
          <a
            href={selectedExample.downloadUrl}
            className="flex items-center gap-2 rounded-lg bg-cyan-500 px-5 py-2.5 font-medium text-zinc-950 shadow-lg shadow-cyan-500/10 transition-colors hover:bg-cyan-400"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            Download Example
          </a>
          <a
            href={selectedExample.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 px-5 py-2.5 font-medium text-zinc-100 transition-colors hover:bg-zinc-700"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            View on GitHub
          </a>
        </div>

        <div className="mb-8 rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
          <h2 className="mb-4 text-xl font-semibold text-zinc-100">
            What this demonstrates
          </h2>
          <div className="grid gap-3 md:grid-cols-2">
            {selectedExample.highlights.map((feature, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <svg
                  className="mt-0.5 h-5 w-5 flex-shrink-0 text-cyan-300"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <span className="text-zinc-300">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="mb-8">
          <h2 className="mb-4 text-xl font-semibold text-zinc-100">
            {selectedExample.id === "full-game" ? "Full game.py" : "Code preview"}
          </h2>
          <CodeBlock
            code={selectedExample.code}
            title={selectedExample.id === "full-game" ? "examples/game-example/src/game.py" : undefined}
          />
        </div>

        <div className="flex justify-between items-center pt-8 border-t border-zinc-800">
          <button
            onClick={() => navigate("/examples")}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Examples
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-6xl"
    >
      <section className="mb-12">
        <p className="mb-3 text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Learn by running code
        </p>
        <h1 className="mb-4 text-4xl font-semibold text-zinc-100">Examples</h1>
        <p className="max-w-3xl text-lg leading-8 text-zinc-400">
          Start with a focused sample when you need one system, or open the
          complete pygame demo to see map loading, rendering, animation, camera
          movement, and collision working together.
        </p>
      </section>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {examples.map((example, idx) => (
          <motion.div
            key={example.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            onClick={() => navigate(`/examples/${example.id}`)}
            className="group cursor-pointer rounded-lg border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-cyan-700/60 hover:bg-zinc-900"
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-semibold text-zinc-100 transition-colors group-hover:text-cyan-300">
                {example.title}
              </h3>
              <span
                className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getDifficultyColor(example.difficulty)}`}
              >
                {example.difficulty}
              </span>
            </div>

            <p className="text-zinc-400 text-sm mb-4 line-clamp-3">
              {example.description}
            </p>

            <div className="mb-6 space-y-2">
              {example.features.slice(0, 3).map((feature, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-sm text-zinc-500"
                >
                  <svg
                    className="w-4 h-4 text-zinc-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>{feature}</span>
                </div>
              ))}
              {example.features.length > 3 && (
                <div className="text-xs text-zinc-600 ml-6">
                  +{example.features.length - 3} more features
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 text-sm font-medium text-cyan-300 group-hover:text-cyan-200">
              <span>View Example</span>
              <svg
                className="w-4 h-4 group-hover:translate-x-1 transition-transform"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </motion.div>
        ))}
      </div>

      <section className="mt-16 rounded-lg border border-zinc-800 bg-zinc-950 p-8">
        <h2 className="mb-4 text-2xl font-semibold text-zinc-100">
          Run an example locally
        </h2>
        <div className="space-y-4 text-zinc-300">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-zinc-950">
              1
            </div>
            <div>
              <h3 className="font-medium mb-1">Download an Example</h3>
              <p className="text-sm text-zinc-400">
                Click on any example card to view details and download the
                complete source code.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-zinc-950">
              2
            </div>
            <div>
              <h3 className="font-medium mb-1">Install Dependencies</h3>
              <p className="text-sm text-zinc-400">
                Run{" "}
                <code className="px-2 py-0.5 bg-zinc-800 rounded text-blue-300">
                  pip install tilemap-parser pygame-ce
                </code>{" "}
                in your terminal.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-zinc-950">
              3
            </div>
            <div>
              <h3 className="font-medium mb-1">Run the Example</h3>
              <p className="text-sm text-zinc-400">
                Extract the zip file and run{" "}
                <code className="px-2 py-0.5 bg-zinc-800 rounded text-blue-300">
                  python src/game.py
                </code>{" "}
                for the full demo, or follow the README in the focused examples.
              </p>
            </div>
          </div>
        </div>
      </section>
    </motion.div>
  );
}
