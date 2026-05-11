import { motion } from "framer-motion";
import { useParams, useNavigate } from "react-router-dom";
import { CodeBlock } from "../components/CodeBlock";

const examples = [
  {
    id: "full-game",
    title: "Full Game Example",
    description:
      "A complete game demonstrating all features of tilemap-parser including map loading, sprite animations, collision detection, and rendering.",
    difficulty: "Advanced",
    features: [
      "Player movement with collision",
      "Sprite animation system",
      "Tile layer rendering",
      "Debug visualization",
      "Camera system",
      "Input handling",
    ],
    code: `# Main game file
from tilemap_parser import (
    load_map, SpriteAnimationSet, AnimationPlayer,
    TileLayerRenderer, CollisionRunner, CollisionCache
)

# Load all game resources
game_data = load_map("data/map.json")
anim_set = SpriteAnimationSet.load("data/RACCOONSPRITESHEET.anim.json")
renderer = TileLayerRenderer(game_data)
collision_cache = CollisionCache()
tileset_collision = collision_cache.get_tileset_collision(
    "data/collision/HiddenJungle_PNG.collision.json"
)
collision_runner = CollisionRunner.from_game_type(
    'topdown', collision_cache, game_data.tile_size
)

# Game loop
while running:
    dt = clock.tick(60) / 1000.0
    
    # Handle input
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * speed * dt
    dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed * dt
    
    # Update animation
    anim_player.update(dt * 1000)
    
    # Move with collision
    result = collision_runner.move_and_slide(
        player, tileset_collision, tile_map, dx, dy, slope_slide=True
    )
    
    # Render
    renderer.render(screen, camera_offset)
    screen.blit(anim_player.get_current_image(), player.position)`,
    downloadUrl: "/examples/full-game-example.zip",
    sourceUrl:
      "https://github.com/FluffyBrudy/tilemap-parser/tree/main/examples/full-game-example",
  },
  {
    id: "animation",
    title: "Animation Example",
    description:
      "Learn how to load and play sprite animations without any game logic or collision detection. Perfect for understanding the animation system.",
    difficulty: "Beginner",
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

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h1 className="text-3xl font-bold text-zinc-100">
              {selectedExample.title}
            </h1>
            <span
              className={`px-3 py-1 text-xs font-medium rounded-full border ${getDifficultyColor(selectedExample.difficulty)}`}
            >
              {selectedExample.difficulty}
            </span>
          </div>
          <p className="text-lg text-zinc-400">{selectedExample.description}</p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 mb-8">
          <a
            href={selectedExample.downloadUrl}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-600/20"
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
            className="flex items-center gap-2 px-5 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg font-medium transition-colors"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            View on GitHub
          </a>
        </div>

        {/* Features */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-zinc-100 mb-4">
            What You'll Learn
          </h2>
          <div className="grid md:grid-cols-2 gap-3">
            {selectedExample.features.map((feature, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <svg
                  className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0"
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

        {/* Code Preview */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-zinc-100 mb-4">
            Code Preview
          </h2>
          <CodeBlock code={selectedExample.code} />
        </div>

        {/* Navigation */}
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
      {/* Header */}
      <section className="mb-12">
        <h1 className="text-4xl font-bold text-zinc-100 mb-4">Examples</h1>
        <p className="text-lg text-zinc-400">
          Explore practical examples to learn tilemap-parser. Each example is
          self-contained and focuses on specific features, from basic animations
          to complete games.
        </p>
      </section>

      {/* Examples Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {examples.map((example, idx) => (
          <motion.div
            key={example.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            onClick={() => navigate(`/examples/${example.id}`)}
            className="group bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 rounded-xl p-6 cursor-pointer transition-all hover:shadow-xl hover:shadow-blue-500/5"
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-semibold text-zinc-100 group-hover:text-blue-400 transition-colors">
                {example.title}
              </h3>
              <span
                className={`px-2.5 py-1 text-xs font-medium rounded-full border ${getDifficultyColor(example.difficulty)}`}
              >
                {example.difficulty}
              </span>
            </div>

            <p className="text-zinc-400 text-sm mb-4 line-clamp-3">
              {example.description}
            </p>

            <div className="space-y-2 mb-6">
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

            <div className="flex items-center gap-2 text-sm text-blue-400 group-hover:text-blue-300 font-medium">
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

      {/* Getting Started Section */}
      <section className="mt-16 bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-blue-800/30 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-zinc-100 mb-4">
          Getting Started with Examples
        </h2>
        <div className="space-y-4 text-zinc-300">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
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
            <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
              2
            </div>
            <div>
              <h3 className="font-medium mb-1">Install Dependencies</h3>
              <p className="text-sm text-zinc-400">
                Run{" "}
                <code className="px-2 py-0.5 bg-zinc-800 rounded text-blue-300">
                  pip install tilemap-parser pygame
                </code>{" "}
                in your terminal.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
              3
            </div>
            <div>
              <h3 className="font-medium mb-1">Run the Example</h3>
              <p className="text-sm text-zinc-400">
                Extract the zip file and run{" "}
                <code className="px-2 py-0.5 bg-zinc-800 rounded text-blue-300">
                  python main.py
                </code>{" "}
                to see it in action.
              </p>
            </div>
          </div>
        </div>
      </section>
    </motion.div>
  );
}
