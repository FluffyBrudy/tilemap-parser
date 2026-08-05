import { Link } from "react-router-dom";
import Callout from "../components/Callout";
import CodeBlock from "../components/CodeBlock";
import FlowDiagram, { type FlowEdge, type FlowNode } from "../components/FlowDiagram";
import Toc from "../components/Toc";
import { REPO } from "../nav";

import cratePy from "../../../examples/full-physics-world/crate.py?raw";
import mainPy from "../../../examples/full-physics-world/main.py?raw";
import playerPy from "../../../examples/full-physics-world/player.py?raw";
import worldPy from "../../../examples/full-physics-world/world.py?raw";

const TREE = `examples/full-physics-world/
├── main.py     the game loop: input, movement, rendering
├── world.py    the physics space: tiles, one-way platform, bodies
├── player.py   the animated player (procedural spritesheet)
└── crate.py    kinematic crate pushing through move_grounded`;

const DIAGRAM_NODES: FlowNode[] = [
  {
    id: "builder",
    x: 0,
    y: 0,
    w: 256,
    h: 80,
    title: "build_world()",
    lines: ["tile_map + tileset", "crates + pillar"],
    accent: "amber",
    link: "#world",
  },
  {
    id: "world",
    x: 260,
    y: 0,
    w: 256,
    h: 80,
    title: "PhysicsWorld",
    lines: ["owns the tile layer", "bodies + tile size"],
    accent: "teal",
    link: "#world",
  },
  {
    id: "runner",
    x: 520,
    y: 0,
    w: 256,
    h: 80,
    title: "CollisionRunner",
    lines: ["from_world(world)", "tiles and bodies resolve"],
    accent: "blue",
    link: "/runner",
  },
  {
    id: "player",
    x: 0,
    y: 208,
    w: 256,
    h: 80,
    title: "move_platformer",
    lines: ["player.py: input + jump", "gravity, step-up"],
    accent: "teal",
    link: "#player",
  },
  {
    id: "crate",
    x: 260,
    y: 208,
    w: 256,
    h: 80,
    title: "move_grounded",
    lines: ["crate.py: velocity only", "kinematic push"],
    accent: "amber",
    link: "#crate",
  },
  {
    id: "query",
    x: 520,
    y: 208,
    w: 256,
    h: 80,
    title: "collides_with_body",
    lines: ["push hook probe", "layer + mask check"],
    accent: "purple",
  },
];

const DIAGRAM_EDGES: FlowEdge[] = [
  { from: "builder", to: "world", fromSide: "right", toSide: "left" },
  { from: "world", to: "runner", fromSide: "right", toSide: "left" },
  { from: "runner", to: "player", fromOffset: 0.2, elbow: 168 },
  { from: "runner", to: "crate", fromOffset: 0.5, elbow: 144 },
  { from: "runner", to: "query", fromOffset: 0.8, elbow: 120 },
];

const FEATURES = [
  "Tile collision: solid ground and wall, plus a one-way platform",
  "PhysicsWorld assembly: tile_map, tileset collision, tile size",
  "Static bodies (the pillar) and kinematic bodies (the crates)",
  "A push loop through move_grounded with an explicit velocity",
  "A move_platformer player controller with runtime-generated animation",
  "Collision layers and masks: the pillar is on layer 2 and the player's mask excludes it",
  "Rendering: tiles, dashed one-way edges, hollow layer-2 bodies, animated sprite",
];

const READING_ORDER = [
  {
    to: "#main",
    label: "main.py",
    text: "the loop. This is where everything is wired: input, movement, the push hook, drawing.",
  },
  {
    to: "#world",
    label: "world.py",
    text: "the space. It owns the tile layer, the tileset collision data and the bodies; nothing moves here.",
  },
  {
    to: "#player",
    label: "player.py",
    text: "the sprite contract. A plain class with the attributes every movement function reads, plus procedural art.",
  },
  {
    to: "#crate",
    label: "crate.py",
    text: "kinematic bodies. How a push works, and why bodies never move themselves.",
  },
];

export default function FullPhysicsWorld() {
  return (
    <div className="content">
      <h1>Full Physics World</h1>
      <p>
        The engine assembled end to end in one runnable mini game: a player,
        pushable crates, a one-way platform, and a body filtered by collision
        layer. Four small files, each with one job. This is{" "}
        <code>docs/physics-world.md</code> made runnable.
      </p>

      <Callout kind="warn" title="THIS ONE IS BIGGER THAN THE GUIDES">
        This example is intentionally larger than the guide snippets. If you
        are new here, do the <Link to="/physics">Physics &amp; Bodies</Link>{" "}
        and <Link to="/runner">CollisionRunner</Link> guides first, then come
        back and read this page top to bottom.
      </Callout>

      <p>
        Assets are generated at runtime, so this example has no external asset
        dependencies: the first run draws a tiny spritesheet and its animation
        JSON into <code>generated/</code> inside the example folder.
      </p>

      <Toc
        items={[
          { id: "features", label: "Features" },
          { id: "structure", label: "Project structure" },
          { id: "running", label: "Running" },
          { id: "architecture", label: "Architecture" },
          { id: "source", label: "Source" },
          { id: "order", label: "Reading order" },
        ]}
      />

      <h2 id="features">FEATURES</h2>
      <ul>
        {FEATURES.map((f) => (
          <li key={f}>{f}</li>
        ))}
      </ul>

      <h2 id="structure">PROJECT STRUCTURE</h2>
      <CodeBlock language="text" title="tree" code={TREE} />

      <h2 id="running">RUNNING</h2>
      <CodeBlock
        title="terminal"
        language="bash"
        code={`pip install -e .
cd examples/full-physics-world
python main.py`}
      />

      <h2 id="architecture">ARCHITECTURE</h2>
      <p>
        Everything flows through the world. The runner is attached to it with{" "}
        <code>CollisionRunner.from_world(world)</code>, so tiles and bodies
        resolve together in every movement call.
      </p>
      <FlowDiagram
        title="data flow"
        nodes={DIAGRAM_NODES}
        edges={DIAGRAM_EDGES}
      />

      <h2 id="source">SOURCE</h2>

      <h3 id="main">main.py: the game loop</h3>
      <p>
        Input, one <code>move_platformer</code> call, the push hook, crate
        physics, then drawing. The only file with a <code>while</code> loop.
      </p>
      <CodeBlock title="main.py" code={mainPy} />

      <h3 id="world">world.py: the physics space</h3>
      <p>
        The scene: ground, a wall, a one-way platform, three crates and the
        layer-2 pillar. Returns a ready <code>PhysicsWorld</code>.
      </p>
      <CodeBlock title="world.py" code={worldPy} />

      <h3 id="player">player.py: the sprite and its art</h3>
      <p>
        The player is a plain class with the attributes every movement
        function reads. The spritesheet and animation JSON are generated here.
      </p>
      <CodeBlock title="player.py" code={playerPy} />

      <h3 id="crate">crate.py: kinematic bodies</h3>
      <p>
        Bodies never move themselves. A kinematic body is moved with an
        explicit velocity through <code>move_grounded</code>, resolved by the
        same collision lane as the player.
      </p>
      <CodeBlock title="crate.py" code={cratePy} />

      <h2 id="order">READING ORDER</h2>
      <ol>
        {READING_ORDER.map((r) => (
          <li key={r.label}>
            <a href={r.to} className="border-b-0 font-mono text-teal">
              {r.label}
            </a>{" "}
            {r.text}
          </li>
        ))}
      </ol>
      <p>
        Then the two guides this example builds on:{" "}
        <Link to="/physics">Physics &amp; Bodies</Link> for the object
        contract and <Link to="/runner">CollisionRunner</Link> for the
        movement presets. The{" "}
        <a
          href={`${REPO}/tree/main/examples/full-physics-world`}
          className="border-b-0 font-mono text-mute hover:bg-teal hover:text-ink"
        >
          [source]
        </a>{" "}
        lives in the repo.
      </p>
    </div>
  );
}
