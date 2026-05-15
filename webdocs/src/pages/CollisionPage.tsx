import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { CodeBlock } from "../components/CodeBlock";

export function CollisionPage() {
  const { section } = useParams();

  useEffect(() => {
    if (section) {
      const el = document.getElementById(section);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [section]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-3xl space-y-12"
    >
      <section id="overview">
        <h2 className="text-2xl font-semibold text-zinc-100 mb-4">
          Collision Module
        </h2>
        <p className="text-zinc-400 mb-4">
          Parse and manage collision data from the tilemap editor. Supports
          tile-based polygon collision for environments and geometric shapes for
          characters.
        </p>
        <div className="grid grid-cols-2 gap-4 mt-6">
          <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
            <h4 className="text-sm font-medium text-zinc-200 mb-2">
              Tileset Collision
            </h4>
            <p className="text-xs text-zinc-500">
              Polygon-based collision shapes defined per tile in the editor
            </p>
          </div>
          <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
            <h4 className="text-sm font-medium text-zinc-200 mb-2">
              Character Collision
            </h4>
            <p className="text-xs text-zinc-500">
              Rectangle, circle, or capsule shapes for game characters
            </p>
          </div>
        </div>
      </section>

      <section id="functions">
        <h3 className="text-lg font-medium text-zinc-200 mb-4">Functions</h3>
        <div className="space-y-4">
          <FnCard
            name="load_tileset_collision"
            sig="load_tileset_collision(collision_path: PathLike) -> TilesetCollision | None"
            desc="Load collision data from a direct path to the .collision.json file. Editor stores these at <data_root>/collision/<stem>.collision.json. Returns None if file doesn't exist."
          />
          <FnCard
            name="load_character_collision"
            sig="load_character_collision(collision_path: PathLike) -> CharacterCollision | None"
            desc="Load character collision from a direct path to the .collision.json file. Editor stores these at <data_root>/character_collision/<name>.collision.json."
          />
          <FnCard
            name="parse_tileset_collision"
            sig="parse_tileset_collision(data: dict) -> TilesetCollision"
            desc="Parse tileset collision from a dictionary (from JSON)."
          />
          <FnCard
            name="parse_character_collision"
            sig="parse_character_collision(data: dict) -> CharacterCollision"
            desc="Parse character collision from a dictionary."
          />
          <FnCard
            name="get_cached_tileset_collision"
            sig="get_cached_tileset_collision(collision_path: PathLike) -> TilesetCollision | None"
            desc="Get tileset collision using global cache. Pass the direct path to the .collision.json file."
          />
          <FnCard
            name="get_cached_character_collision"
            sig="get_cached_character_collision(collision_path: PathLike) -> CharacterCollision | None"
            desc="Get character collision using global cache. Pass the direct path to the .collision.json file."
          />
          <FnCard
            name="clear_collision_cache"
            sig="clear_collision_cache()"
            desc="Clear the global collision cache."
          />
        </div>
      </section>

      <section id="data">
        <h3 className="text-lg font-medium text-zinc-200 mb-4">Data Classes</h3>
        <div className="space-y-6">
          <ClassCard
            name="TilesetCollision"
            desc="Complete collision data for a tileset"
            props={[
              "tileset_name: str",
              "tile_size: IntPoint",
              "tiles: Dict[int, TileCollisionData]",
            ]}
            methods={[
              "get_tile_collision(id)",
              "has_collision(id)",
              "get_world_shapes(id, x, y)",
            ]}
          />
          <ClassCard
            name="TileCollisionData"
            desc="Collision data for a single tile"
            props={["tile_id: int", "shapes: List[CollisionPolygon]"]}
            methods={["has_collision()"]}
          />
          <ClassCard
            name="CollisionPolygon"
            desc="Polygon collision shape for a tile"
            props={["vertices: List[Point]", "one_way: bool"]}
            methods={["transform(x, y)", "is_valid()"]}
          />
        </div>
      </section>

      <section id="shapes">
        <h3 className="text-lg font-medium text-zinc-200 mb-4">
          Character Shapes
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <ShapeCard
            name="RectangleShape"
            props={["width", "height", "offset"]}
            desc="Standard rectangle hitbox"
          />
          <ShapeCard
            name="CircleShape"
            props={["radius", "offset"]}
            desc="Circular hitbox"
          />
          <ShapeCard
            name="CapsuleShape"
            props={["radius", "height", "offset"]}
            desc="Vertical capsule shape"
          />
          <ShapeCard
            name="CharacterCollision"
            props={["name", "shape", "properties"]}
            desc="Character collision container"
          />
        </div>
      </section>

      <section id="cache">
        <h3 className="text-lg font-medium text-zinc-200 mb-4">
          CollisionCache
        </h3>
        <p className="text-zinc-400 mb-3">
          Caches collision data to avoid repeated file I/O. Create your own
          instance or use the global cache functions. All methods take the
          direct path to the .collision.json file.
        </p>
        <CodeBlock
          code={`from tilemap_parser import CollisionCache
from pathlib import Path

data_root = Path("data")  # from settings.json
cache = CollisionCache()

# Get tileset collision — pass the .collision.json path directly
tileset = cache.get_tileset_collision(data_root / "collision" / "terrain.collision.json")

# Get character collision
hero = cache.get_character_collision(data_root / "character_collision" / "hero.collision.json")

# Preload multiple at startup
for name in ["terrain", "objects"]:
    cache.preload_tileset(data_root / "collision" / f"{name}.collision.json")

# Clear when reloading assets
cache.clear()`}
        />
      </section>

      <section id="object-collision">
        <h3 className="text-lg font-medium text-zinc-200 mb-4">
          Object-to-Object Collision
        </h3>
        <p className="text-zinc-400 mb-4">
          Detect collisions between dynamic game objects (players, enemies, items)
          using mixed shapes with layer filtering. All 10 shape pairs supported
          (rect, circle, capsule, polygon vs everything).
        </p>

        <div className="space-y-6">
          <div className="border-l-2 border-zinc-800 pl-4">
            <code className="font-mono text-sm text-zinc-200">ICollidableObject</code>
            <p className="text-zinc-500 text-xs font-mono mt-1">Protocol</p>
            <p className="text-zinc-400 text-sm mt-1">
              Any object with <code className="text-amber-400 font-mono">x</code>, <code className="text-amber-400 font-mono">y</code>, and <code className="text-amber-400 font-mono">collision_shape</code> (RectangleShape, CircleShape, CapsuleShape, or CollisionPolygon). Optional <code className="text-amber-400 font-mono">collision_layer</code> and <code className="text-amber-400 font-mono">collision_mask</code> default to layer&nbsp;1 and collide-with-all.
            </p>
          </div>

          <FnCard
            name="should_collide"
            sig="should_collide(obj_a: ICollidableObject, obj_b: ICollidableObject) -> bool"
            desc="Check if two objects should collide based on layer/mask mutual agreement (AND logic)."
          />
          <FnCard
            name="check_collision"
            sig="check_collision(obj_a: ICollidableObject, obj_b: ICollidableObject) -> CollisionHit | None"
            desc="Full collision check: layer filter → broadphase AABB → narrowphase shape dispatch. Returns a CollisionHit or None."
          />
        </div>

        <h4 className="text-sm font-medium text-zinc-200 mt-6 mb-3">CollisionHit</h4>
        <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-6">
          <ResultProp name="object_a" type="ICollidableObject" />
          <ResultProp name="object_b" type="ICollidableObject" />
          <ResultProp name="normal" type="tuple[float, float]" />
          <ResultProp name="depth" type="float" />
          <ResultProp name="resolve()" type="None" />
          <ResultProp name="involves(obj)" type="bool" />
          <ResultProp name="other(obj)" type="ICollidableObject" />
        </div>

        <h4 className="text-sm font-medium text-zinc-200 mb-3">ObjectCollisionManager</h4>
        <p className="text-zinc-400 text-sm mb-3">
          Multi-object collision system with add/remove and all-vs-all queries.
        </p>
        <CodeBlock
          code={`from tilemap_parser import ObjectCollisionManager, CircleShape

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collision_shape = CircleShape(radius=16)

manager = ObjectCollisionManager()
ball_a = Ball(100, 100)
ball_b = Ball(130, 100)
manager.add_object(ball_a)
manager.add_object(ball_b)

# Game loop
for hit in manager.check_all_collisions():
    hit.resolve()  # separate both
    # hit.normal, hit.depth available for custom response`}
        />
      </section>
    </motion.div>
  );
}

function FnCard({
  name,
  sig,
  desc,
}: {
  name: string;
  sig: string;
  desc: string;
}) {
  return (
    <div
      className="border-l-2 border-zinc-800 pl-4 py-2 cursor-pointer hover:border-zinc-600 transition-colors"
      onClick={() => {}}
    >
      <code className="font-mono text-sm text-zinc-200">{name}</code>
      <p className="text-zinc-500 text-xs font-mono mt-1">{sig}</p>
      <p className="text-zinc-400 text-sm mt-1">{desc}</p>
    </div>
  );
}

function ClassCard({
  name,
  desc,
  props,
  methods,
}: {
  name: string;
  desc: string;
  props: string[];
  methods: string[];
}) {
  return (
    <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
      <code className="font-mono text-zinc-100">{name}</code>
      <p className="text-xs text-zinc-500 mt-1">{desc}</p>
      <div className="mt-3 space-y-2">
        <div>
          <span className="text-xs text-zinc-600 uppercase">Properties</span>
          <div className="text-xs font-mono text-zinc-400 mt-1">
            {props.join(", ")}
          </div>
        </div>
        <div>
          <span className="text-xs text-zinc-600 uppercase">Methods</span>
          <div className="text-xs font-mono text-zinc-400 mt-1">
            {methods.join(", ")}
          </div>
        </div>
      </div>
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

function ShapeCard({
  name,
  props,
  desc,
}: {
  name: string;
  props: string[];
  desc: string;
}) {
  return (
    <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
      <code className="font-mono text-sm text-zinc-200">{name}</code>
      <p className="text-xs text-zinc-500 mt-1">{desc}</p>
      <div className="text-xs font-mono text-zinc-600 mt-2">
        {props.join(", ")}
      </div>
    </div>
  );
}
