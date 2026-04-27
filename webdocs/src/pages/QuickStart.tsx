import { motion } from "framer-motion";
import { CodeBlock } from "../components/CodeBlock";

export function QuickStart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl space-y-12"
    >
      <section>
        <h2 className="text-2xl font-semibold text-zinc-100 mb-4">Quick Start</h2>
        <p className="text-zinc-400 mb-6">
          Load a tilemap and access its layers and tiles.
        </p>
        <CodeBlock code={`from tilemap_parser import load_map

data = load_map("assets/maps/level_1.json")

layers = data.get_layers(sort_by_zindex=True)
for layer in layers:
    print(layer.id, layer.name, layer.layer_type, layer.z_index)`} />
      </section>

      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3">Get tile surfaces</h3>
        <p className="text-zinc-400 mb-3">
          Extract individual tile images from a tileset for rendering.
        </p>
        <CodeBlock code={`# By variant index and tileset
tile_surface = data.get_image(variant=12, ttype=0)

# Same as above
tile_surface2 = data.get_tile_surface(0, 12)

# At specific grid position in a layer
cell_surface = data.get_tile_surface_at("Ground", 10, 4)`} />
      </section>

      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3">Animation playback</h3>
        <p className="text-zinc-400 mb-3">
          Load sprite animations and play them in your game loop.
        </p>
        <CodeBlock code={`from tilemap_parser import SpriteAnimationSet, AnimationPlayer

anim_set = SpriteAnimationSet.load("assets/anims/hero.anim.json")
player = AnimationPlayer(anim_set, "idle")

# In your game loop
player.update(16.67)  # delta time in ms
frame_surface = player.get_current_image()`} />
      </section>

      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3">Tile layer renderer</h3>
        <p className="text-zinc-400 mb-3">
          Render tile layers with automatic viewport culling.
        </p>
        <CodeBlock code={`import pygame
from tilemap_parser import TileLayerRenderer, load_map

data = load_map("assets/maps/level_1.json")
renderer = TileLayerRenderer(data)
renderer.warm_cache()

screen = pygame.display.set_mode((1280, 720))

# In game loop
stats = renderer.render(screen, camera_xy=(camera_x, camera_y))`} />
      </section>
    </motion.div>
  );
}