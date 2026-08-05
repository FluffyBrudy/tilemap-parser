import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";
import FlowDiagram, { type FlowEdge, type FlowNode } from "../components/FlowDiagram";

const CHAIN_NODES: FlowNode[] = [
  {
    id: "grid",
    x: 0,
    y: 0,
    w: 256,
    h: 80,
    title: "NavGrid",
    lines: ["tile_map + tileset", "walkability grid"],
    accent: "amber",
  },
  {
    id: "finder",
    x: 260,
    y: 0,
    w: 256,
    h: 80,
    title: "Pathfinder",
    lines: ["A* over the grid", "find_path(start, end)"],
    accent: "teal",
  },
  {
    id: "follower",
    x: 520,
    y: 0,
    w: 256,
    h: 80,
    title: "PathFollower",
    lines: ["waypoint steering", "update_rpg(...)"],
    accent: "blue",
  },
  {
    id: "runner",
    x: 260,
    y: 208,
    w: 256,
    h: 80,
    title: "CollisionRunner",
    lines: ["move_rpg resolves", "every step"],
    accent: "purple",
    link: "/runner",
  },
];

const CHAIN_EDGES: FlowEdge[] = [
  { from: "grid", to: "finder", fromSide: "right", toSide: "left" },
  { from: "finder", to: "follower", fromSide: "right", toSide: "left" },
  { from: "follower", to: "runner" },
];

const PATH = `from tilemap_parser import load_map, load_tileset_collision
from tilemap_parser.runtime.navigation import NavGrid, Pathfinder

game_data = load_map("data/map.json")
tile_map = game_data.build_tile_map()           # {(col, row): tile_id}
tileset  = load_tileset_collision("data/map.collision.json")

base = NavGrid(tile_map, tileset, (32, 32), map_size=(24, 14))
nav  = base.erode(1.0)                          # inflate walls 1 tile

pathfinder = Pathfinder(nav)
path = pathfinder.find_path((1, 1), (20, 5))    # [(tx, ty), ...] | None`;

const FOLLOW = `from tilemap_parser import CollisionRunner
from tilemap_parser.runtime.navigation import PathFollower

follower = PathFollower((32, 32))            # effective tile size

runner = CollisionRunner.from_game_type("rpg", (32, 32))

# In your game loop:
waypoint_idx, arrived, hit_x, hit_y = follower.update_rpg(
    enemy, path, waypoint_idx,
    runner, tileset, tile_map,
    speed=200.0, dt=dt,
)
if arrived:
    path = None   # or pick a new destination`;

export default function Pathfinding() {
  return (
    <div className="content">
      <h1>Pathfinding: tile-grid A*</h1>
      <p>
        Three classes, one flow: <code>NavGrid</code> turns the collision
        layer into a walkability grid, <code>Pathfinder</code> runs A* over
        it, and <code>PathFollower</code> steers a sprite along the result
        with the runner resolving actual movement. The canonical demo is{" "}
        <code>examples/rpg-pathfinding/main.py</code>.
      </p>

      <FlowDiagram title="the chain" nodes={CHAIN_NODES} edges={CHAIN_EDGES} />

      <h2 id="grid">THE GRID</h2>
      <p>
        A <code>NavGrid</code> is built from the same data the physics world
        uses: the flat tile map and its <code>TilesetCollision</code>. Tiles
        with solid polygons are walls; one-way tiles are still walkable
        surfaces.
      </p>
      <CodeBlock title="nav.py" code={PATH} />
      <ul>
        <li>
          <code>find_path(start_tile, end_tile, max_steps=2000)</code> returns{" "}
          <code>None</code> when the destination is unwalkable or unreachable.
          Path tiles are grid coordinates; multiply by the effective tile
          size to get world pixels (the follower does this for you).
        </li>
        <li>
          <code>erode(margin)</code> returns a derived grid with walls
          inflated by <em>margin tiles</em>, so entities keep a corridor from
          hugging walls. The example uses <code>erode(1.0)</code>.
        </li>
        <li>
          <code>NavGrid.for_entity(...)</code> derives the margin from a
          sprite size automatically:{" "}
          <code>margin = (max(w, h) / 2) / tile_w</code>.
        </li>
      </ul>

      <h2 id="follower">FOLLOWING THE PATH</h2>
      <p>
        <code>PathFollower</code> walks the waypoints; each{" "}
        <code>update_rpg()</code> call moves the sprite toward the current
        waypoint's center at <code>speed</code>, resolving the move through
        the runner's <code>move_rpg</code>, and advances the waypoint on
        arrival (default arrival distance: 20% of a tile diagonal).
      </p>
      <CodeBlock title="loop.py" code={FOLLOW} />
      <ul>
        <li>
          The returned tuple is{" "}
          <code>(new_waypoint_index, arrived, hit_wall_x, hit_wall_y)</code>;
          branch on <code>arrived</code> to pick the next destination.
        </li>
        <li>
          <code>update_rpg</code> resolves collision against{" "}
          <code>tile_map</code>/<code>tileset_collision</code> via{" "}
          <code>move_rpg</code>, so the follower never walks through walls; it
          just gets stopped and you read <code>hit_wall_x/y</code>.
        </li>
      </ul>
      <Callout kind="warn" title="REBUILD WHEN THE MAP CHANGES">
        <code>NavGrid</code> snapshots walkability at construction. If your
        game edits tiles (destroyed walls, opened doors), rebuild the grid
        and re-run <code>find_path</code>; stale grids lead into walls.
      </Callout>

      <h2 id="when">WHEN NOT TO USE IT</h2>
      <p>
        This is tile-grid pathfinding: good for rooms, mazes and dungeon
        layouts. It does not reason about height differences, slopes, or
        dynamic bodies; anything that moves should be handled by your game's
        steering on top of the path. And for simple "chase the player" AI,
        steering the sprite at the target each frame is cheaper than a path.
      </p>
    </div>
  );
}
