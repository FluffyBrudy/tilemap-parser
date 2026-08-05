import { Link } from "react-router-dom";
import CodeBlock from "../components/CodeBlock";
import { REPO } from "../nav";

type Card = {
  name: string;
  path: string;
  blurb: string;
  files: string[];
  run?: string;
};

const CARDS: Card[] = [
  {
    name: "physics-crate",
    path: "examples/physics-crate",
    blurb:
      "The canonical physics demo. Push kinematic crates across the floor; they block each other and the tile wall, and you can stand on them. This is the sliding box from the Physics guide.",
    files: ["main.py"],
    run: "python main.py",
  },
  {
    name: "platformer",
    path: "examples/platformer",
    blurb:
      "Full side-scroller: gravity, jump, player state machine, enemies, parallax-ready assets. Uses move_platformer with step-up and one-way platforms.",
    files: ["src/main.py", "src/entities/", "src/fsm/"],
  },
  {
    name: "platformer-with-slide",
    path: "examples/platformer-with-slide",
    blurb:
      "Slope-aware platformer built on move_platformer_with_slide: walks polygon floor surfaces, respects max_walk_angle, real tilemap-editor map + collision data.",
    files: ["src/game.py", "data/maps/map.json", "data/collision/"],
  },
  {
    name: "tiny-quest",
    path: "examples/tiny-quest",
    blurb:
      "A compact quest game: player entity, enemies, waterfalls, spikes, sounds. Shows character collision files wired to runtime sprites.",
    files: ["src/game.py", "src/entities/", "data/character_collision/"],
  },
  {
    name: "rpg-pathfinding",
    path: "examples/rpg-pathfinding",
    blurb:
      "RPG movement plus NavGrid / Pathfinder / PathFollower: an AI entity walks a computed path through the tile grid.",
    files: ["main.py"],
  },
  {
    name: "object-collision",
    path: "examples/object-collision",
    blurb:
      "The sprite-vs-sprite lane: character-vs-polygon and pair-comparison scripts over ObjectCollisionManager.",
    files: ["character-vs-polygon.py", "pair-comparison.py"],
  },
  {
    name: "particles",
    path: "examples/particles",
    blurb:
      "Particle system playground: emitters with shapes, color transitions, alpha fade, gravity, batch rendering. The full config lives in code.",
    files: ["src/main.py", "src/full.py", "data/map.json"],
  },
  {
    name: "game-example",
    path: "examples/game-example",
    blurb:
      "Minimal game shell with its own collision data, a clean base to fork.",
    files: ["data/collision/"],
  },
  {
    name: "comparison",
    path: "examples/comparison",
    blurb:
      "Benchmarks and honest trade-offs: broadphase naive-vs-spatial, AABB-vs-SAT, movement modes, culled-vs-chunked rendering, particle caching, spatial cell-size tuning.",
    files: [
      "collision-move-modes.py",
      "collision-aabb-vs-sat.py",
      "broadphase-naive-vs-spatial.py",
      "spatial-cell-size-tuning.py",
      "rendering-naive-vs-culled.py",
      "rendering-culled-vs-chunked.py",
      "particle-naive-vs-cached.py",
      "movement-naive-vs-parser.py",
    ],
  },
];

export default function Examples() {
  return (
    <div className="content">
      <h1>Examples</h1>
      <p>
        Every directory under <code>examples/</code> runs standalone. All wiring
        below is tested and correct; these are the source of truth for the
        guide pages.
      </p>

      <CodeBlock
        title="terminal"
        language="bash"
        code={`git clone https://github.com/FluffyBrudy/tilemap-parser
cd tilemap-parser
pip install -e .
cd examples/physics-crate
python main.py`}
      />

      <h2 id="full">FULL USE CASES</h2>
      <p>
        Three read-the-source examples that wire whole lanes end to end. Their
        pages show every file inline, so they double as the docs.
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        <Link
          to="/examples/full-physics-world"
          className="panel flex flex-col p-4 hover:border-teal"
        >
          <h3 className="m-0">full-physics-world</h3>
          <p className="m-0 mt-2 flex-1 text-[14px]">
            The engine assembled: a runnable mini game with an animated player,
            pushable crates, a one-way platform and a layer-2 body. Four files,
            one job each.
          </p>
          <div className="mt-3 border-t-2 border-line pt-2">
            <div className="font-pixel mb-1 text-[8px] text-mute">FILES</div>
            <code className="block text-[12px] text-mute">
              main.py  world.py  player.py  crate.py
            </code>
            <div className="mt-2 font-mono text-[12px] text-amber">
              {">"} python main.py
            </div>
          </div>
        </Link>
        <Link
          to="/examples/full-collision"
          className="panel flex flex-col p-4 hover:border-teal"
        >
          <h3 className="m-0">full-collision</h3>
          <p className="m-0 mt-2 flex-1 text-[14px]">
            A copy-and-fill template: tiles, bodies and a move_platformer
            player in one file. Runs as-is on a mini world before you fill in
            your paths.
          </p>
          <div className="mt-3 border-t-2 border-line pt-2">
            <div className="font-pixel mb-1 text-[8px] text-mute">FILES</div>
            <code className="block text-[12px] text-mute">main.py</code>
            <div className="mt-2 font-mono text-[12px] text-amber">
              {">"} python main.py
            </div>
          </div>
        </Link>
        <Link
          to="/examples/full-pathfinding"
          className="panel flex flex-col p-4 hover:border-teal"
        >
          <h3 className="m-0">full-pathfinding</h3>
          <p className="m-0 mt-2 flex-1 text-[14px]">
            NavGrid, Pathfinder and PathFollower in one self-contained maze:
            click a target and the enemy walks the A* path.
          </p>
          <div className="mt-3 border-t-2 border-line pt-2">
            <div className="font-pixel mb-1 text-[8px] text-mute">FILES</div>
            <code className="block text-[12px] text-mute">main.py</code>
            <div className="mt-2 font-mono text-[12px] text-amber">
              {">"} python main.py
            </div>
          </div>
        </Link>
      </div>

      <h2 id="grid">THE CARDS</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {CARDS.map((c) => (
          <div key={c.name} className="panel flex flex-col p-4">
            <div className="flex items-baseline justify-between gap-2">
              <h3 className="m-0">{c.name}</h3>
              <a
                href={`${REPO}/tree/main/${c.path}`}
                className="border-b-0 font-mono text-[11px] text-mute hover:bg-teal hover:text-ink"
              >
                [source]
              </a>
            </div>
            <p className="m-0 mt-2 flex-1 text-[14px]">{c.blurb}</p>
            <div className="mt-3 border-t-2 border-line pt-2">
              <div className="font-pixel mb-1 text-[8px] text-mute">FILES</div>
              <code className="block text-[12px] text-mute">
                {c.files.join("  ")}
              </code>
              {c.run && (
                <div className="mt-2 font-mono text-[12px] text-amber">
                  {">"} {c.run}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <h2 id="order">A SENSIBLE READING ORDER</h2>
      <ol>
        <li>
          <strong>physics-crate</strong>: bodies, attach, the push loop, the
          sub-pixel probe.
        </li>
        <li>
          <strong>platformer-with-slide</strong>: slope walking, real map data.
        </li>
        <li>
          <strong>rpg-pathfinding</strong>: movement + AI on a grid.
        </li>
        <li>
          <strong>object-collision</strong> and <strong>particles</strong>: the
          non-physics lanes.
        </li>
        <li>
          <strong>comparison</strong>: when you start caring about frame time.
        </li>
      </ol>
    </div>
  );
}
