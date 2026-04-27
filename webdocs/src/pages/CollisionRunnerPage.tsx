import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { CodeBlock } from "../components/CodeBlock";

export function CollisionRunnerPage() {
  const { section } = useParams();

  useEffect(() => {
    if (section) {
      const el = document.getElementById(section);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [section]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-3xl space-y-12"
    >
      <section id="overview">
        <h2 className="text-2xl font-semibold text-zinc-100 mb-4">Collision Runner</h2>
        <p className="text-zinc-400 mb-4">
          Ready-to-use collision system for common game types. Handles detection and response for platformers, top-down, and RPG games.
        </p>
        <div className="grid grid-cols-3 gap-3 mt-4">
          <GameTypeCard type="platformer" desc="Gravity + jumping" icon="↓" />
          <GameTypeCard type="topdown" desc="Sliding walls" icon="↔" />
          <GameTypeCard type="rpg" desc="Grid blocking" icon="▦" />
        </div>
      </section>

      <section id="movement">
        <h3 className="text-lg font-medium text-zinc-200 mb-3">MovementMode Enum</h3>
        <div className="space-y-2">
          <EnumItem value="SLIDE" desc="Smooth sliding along walls (top-down games)" />
          <EnumItem value="PLATFORMER" desc="Gravity-based with jumping (platformer games)" />
          <EnumItem value="RPG" desc="Full blocking with no sliding (RPG games)" />
        </div>
      </section>

      <section id="result">
        <h3 className="text-lg font-medium text-zinc-200 mb-3">CollisionResult</h3>
        <p className="text-zinc-400 text-sm mb-3">Returned by all movement methods.</p>
        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <ResultProp name="collided" type="bool" />
          <ResultProp name="final_x" type="float" />
          <ResultProp name="final_y" type="float" />
          <ResultProp name="hit_wall_x" type="bool" />
          <ResultProp name="hit_wall_y" type="bool" />
          <ResultProp name="hit_ceiling" type="bool" />
          <ResultProp name="on_ground" type="bool" />
          <ResultProp name="slide_vector" type="Vector2" />
        </div>
      </section>

      <section id="runner">
        <h3 className="text-lg font-medium text-zinc-200 mb-3">CollisionRunner</h3>
        <p className="text-zinc-400 text-sm mb-3">
          Use <code className="text-amber-400 font-mono">from_game_type()</code> to create runners with sensible presets.
        </p>
        <div className="space-y-4">
          <MethodCard 
            name="from_game_type"
            sig="from_game_type(game_type, cache, tile_size?, strict?) -> CollisionRunner"
            desc="Factory method - recommended way to create runners. game_type: 'platformer', 'topdown', or 'rpg'"
          />
          <MethodCard 
            name="move"
            sig="move(sprite, tileset, tile_map, **kwargs) -> CollisionResult"
            desc="Main entry point - delegates to appropriate movement method based on mode"
          />
          <MethodCard 
            name="move_and_slide"
            sig="move_and_slide(sprite, tileset, tile_map, dx, dy, slope_slide?)"
            desc="Top-down sliding movement. Sprite slides along walls smoothly."
          />
          <MethodCard 
            name="move_platformer"
            sig="move_platformer(sprite, tileset, tile_map, dt, input_x?, jump_pressed?)"
            desc="Platformer physics with gravity, jumping, and one-way platforms."
          />
          <MethodCard 
            name="move_rpg"
            sig="move_rpg(sprite, tileset, tile_map, dx, dy)"
            desc="RPG blocking. Movement is blocked entirely by walls with no sliding."
          />
          <MethodCard 
            name="validate_config"
            sig="validate_config(strict?)"
            desc="Check configuration consistency. Warns or raises on issues."
          />
        </div>
      </section>

      <section id="setup">
        <h3 className="text-lg font-medium text-zinc-200 mb-3">Setup Examples</h3>
        
        <h4 className="text-sm text-zinc-300 mb-2">Platformer</h4>
        <CodeBlock code={`from tilemap_parser import CollisionRunner, CollisionCache, RectangleShape

cache = CollisionCache()
runner = CollisionRunner.from_game_type('platformer', cache, (32, 32))

# Sprite must have: x, y, vx, vy, on_ground, collision_shape
player.collision_shape = RectangleShape(width=24, height=32)

# Game loop
result = runner.move(
    player,
    tileset_collision,
    tile_map,
    dt=delta_time,
    input_x=input.get_axis("horizontal"),
    jump_pressed=input.pressed("jump")
)`} />

        <h4 className="text-sm text-zinc-300 mb-2 mt-6">Top-Down</h4>
        <CodeBlock code={`runner = CollisionRunner.from_game_type('topdown', cache, (32, 32))

# Game loop
result = runner.move(player, tileset_collision, tile_map, dx, dy)

if result.hit_wall_x:
    print("blocked horizontally")
if result.slide_vector:
    print(f"sliding: {result.slide_vector}")`} />

        <h4 className="text-sm text-zinc-300 mb-2 mt-6">RPG</h4>
        <CodeBlock code={`runner = CollisionRunner.from_game_type('rpg', cache, (32, 32))

# Grid-based movement
result = runner.move(player, tileset_collision, tile_map, dx, dy)

if result.collided:
    print("blocked by wall")`} />
      </section>
    </motion.div>
  );
}

function GameTypeCard({ type, desc, icon }: { type: string; desc: string; icon: string }) {
  return (
    <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800 text-center">
      <span className="text-2xl text-zinc-500">{icon}</span>
      <div className="mt-1">
        <code className="text-sm text-zinc-200">{type}</code>
        <p className="text-xs text-zinc-500">{desc}</p>
      </div>
    </div>
  );
}

function EnumItem({ value, desc }: { value: string; desc: string }) {
  return (
    <div className="flex gap-3 text-sm">
      <code className="font-mono text-blue-400 w-32">{value}</code>
      <span className="text-zinc-400">{desc}</span>
    </div>
  );
}

function ResultProp({ name, type }: { name: string; type: string }) {
  return (
    <div className="bg-zinc-900 rounded px-2 py-1.5 flex justify-between">
      <span className="text-zinc-300">{name}</span>
      <span className="text-zinc-500">{type}</span>
    </div>
  );
}

function MethodCard({ name, sig, desc }: { name: string; sig: string; desc: string }) {
  return (
    <div className="border-l-2 border-zinc-800 pl-4">
      <code className="font-mono text-sm text-zinc-200">{name}</code>
      <p className="text-zinc-500 text-xs font-mono mt-1">{sig}</p>
      <p className="text-zinc-400 text-sm mt-1">{desc}</p>
    </div>
  );
}