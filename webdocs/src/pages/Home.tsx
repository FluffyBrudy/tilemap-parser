import { Link } from "react-router-dom";
import FlowDiagram, { type FlowEdge, type FlowNode } from "../components/FlowDiagram";
import { HeroSprite } from "../components/PixelSprite";
import { REPO, VERSION } from "../nav";

const MAP_NODES: FlowNode[] = [
  {
    id: "parser",
    x: 0,
    y: 0,
    w: 256,
    h: 80,
    title: "tilemap_parser",
    lines: ["map, tileset, object", "loaders"],
    accent: "amber",
    link: "/map-parsing",
  },
  {
    id: "world",
    x: 260,
    y: 0,
    w: 256,
    h: 80,
    title: "PhysicsWorld",
    lines: ["tile_map + bodies", "collision layers"],
    accent: "teal",
    link: "/physics",
  },
  {
    id: "runner",
    x: 520,
    y: 0,
    w: 256,
    h: 80,
    title: "CollisionRunner",
    lines: ["five move modes", "presets + tunables"],
    accent: "blue",
    link: "/runner",
  },
  {
    id: "sprite",
    x: 520,
    y: 208,
    w: 256,
    h: 80,
    title: "Your Sprite",
    lines: ["x, y, collision_shape", "(+ vx, vy, on_ground)"],
    accent: "purple",
    link: "/physics",
  },
  {
    id: "nav",
    x: 260,
    y: 208,
    w: 256,
    h: 80,
    title: "NavGrid",
    lines: ["A* over walkability", "PathFollower steering"],
    accent: "red",
    link: "/pathfinding",
  },
];

const MAP_EDGES: FlowEdge[] = [
  { from: "parser", to: "world", fromSide: "right", toSide: "left" },
  { from: "world", to: "runner", fromSide: "right", toSide: "left" },
  { from: "runner", to: "sprite" },
  {
    from: "world",
    to: "nav",
    fromSide: "right",
    fromOffset: 0.85,
    toSide: "top",
    toOffset: 0.5,
  },
];

const FEATURES = [
  [
    "MAP PARSING",
    "Load and query tilemaps, layers, objects and autotiles from tilemap-editor JSON.",
  ],
  [
    "TILE COLLISION",
    "Slide, platformer and RPG movement modes resolved against tile polygons.",
  ],
  [
    "PHYSICS BODIES",
    "A PhysicsWorld: tiles + solid Body objects, kinematic crates you push around.",
  ],
  [
    "OBJECT COLLISION",
    "Sprite-vs-sprite lane: spatial-grid, mixed shapes, layer filtering.",
  ],
  [
    "CHUNKED RENDERING",
    "TileLayerRenderer culls to the viewport, chunk-by-chunk.",
  ],
  [
    "CAMERA + FX",
    "Centered/deadzone follow, lerp, screen-shake, bounds clamp.",
  ],
  [
    "ANIMATION",
    "Frame-based AnimationPlayer over tilemap-editor animation JSON.",
  ],
  [
    "PARTICLES",
    "ParticleSystem with shapes, color transitions, alpha fade, batch rendering.",
  ],
  ["PATHFINDING", "NavGrid, Pathfinder and PathFollower for RPG-style AI."],
  [
    "CAPSULES + HITS",
    "Capsule collision against every shape, and CollisionHit.resolve() helpers.",
  ],
];

export default function Home() {
  return (
    <div className="content">
      <section className="pixel-bands border-2 border-line-2 p-6 shadow-hard sm:p-8">
        <div className="flex items-center gap-2">
          <span className="font-pixel text-[9px] text-red">PRESS START</span>
          <span className="animate-blink text-[10px] text-red">▮</span>
        </div>
        <h1 className="mt-3 text-[#0d0b13]">
          <span className="block">tilemap-parser</span>
        </h1>
        <p className="font-retro text-[26px] leading-tight text-amber">
          standalone map parser + pygame collision runtime for game developers
        </p>
        <p className="text-mute">
          Python {">="} 3.10 · pygame-ce · version{" "}
          <span className="border-2 border-line-2 bg-raise px-1.5 py-0.5 font-pixel text-[8px] text-amber">
            v{VERSION}
          </span>
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/quick-start" className="btn-pixel" data-accent="amber">
            QUICK START ▸
          </Link>
          <Link to="/physics" className="btn-pixel">
            PHYSICS & BODIES
          </Link>
          <a href={REPO} className="btn-pixel">
            GITHUB
          </a>
        </div>
      </section>

      <div className="mt-6 flex justify-center border-2 border-line-2 bg-panel p-4 shadow-hard">
        <HeroSprite className="w-72 sm:w-80" />
        <div className="hidden self-end pb-2 font-pixel text-[8px] text-mute sm:block"></div>
      </div>

      <h2 id="what">WHAT YOU GET</h2>
      <p>
        Everything hangs off one spine: load data, build a world, resolve
        movement through the runner. The rooms below are the whole engine.
      </p>
      <FlowDiagram title="engine map" nodes={MAP_NODES} edges={MAP_EDGES} />
      <div className="grid gap-3 sm:grid-cols-2">
        {FEATURES.map(([title, body]) => (
          <div
            key={title}
            className="border-2 border-line-2 bg-panel p-4 hover:bg-panel-2"
          >
            <div className="font-pixel mb-2 text-[9px] text-teal">{title}</div>
            <p className="m-0 text-[14px] text-text">{body}</p>
          </div>
        ))}
      </div>

      <h2 id="jump">WHERE TO START</h2>
      <ul>
        <li>
          <Link to="/install">Installation</Link>: two pip commands and you're
          running.
        </li>
        <li>
          <Link to="/quick-start">Quick Start</Link>: the smallest playable
          program.
        </li>
        <li>
          <Link to="/physics">Physics & Bodies</Link>: collision, explained
          without the fog of war. Includes the sliding-box walkthrough.
        </li>
        <li>
          <Link to="/pipeline">The Pipeline</Link>: map → world → runner →
          player → crate → screen, one script.
        </li>
        <li>
          <Link to="/examples">Examples</Link>: nine working demos, from
          pushable crates to RPG pathfinding.
        </li>
      </ul>

      <p className="font-retro text-[24px] text-mute">
        Author maps and collision with the companion editor:{" "}
        <a
          href="https://pypi.org/project/tilemap-editor/"
          className="border-b-2"
        >
          tilemap-editor
        </a>
        .
      </p>
    </div>
  );
}
