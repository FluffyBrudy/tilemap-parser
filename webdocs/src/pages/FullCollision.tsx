import { Link } from "react-router-dom";
import CodeBlock from "../components/CodeBlock";
import { REPO } from "../nav";

import collisionPy from "../../../examples/full-collision/main.py?raw";

export default function FullCollision() {
  return (
    <div className="content">
      <h1>Full Collision</h1>
      <p>
        A copy-and-fill template: one file that wires every collision lane
        into one place, tiles, bodies, and a player moved by{" "}
        <code>move_platformer</code>. Replace the two FILL IN paths with your
        own map and collision data, then implement your movement in the two{" "}
        <code>implement your movement here</code> markers.
      </p>
      <p>
        It runs as-is on a small procedural world, so you can watch the wiring
        work before you replace anything. The bigger sibling is{" "}
        <Link to="/examples/full-physics-world" className="border-b-0 font-mono text-teal">
          Full Physics World
        </Link>
        : a multi-file runnable that teaches how the engine is assembled. This
        one is the quick start.
      </p>

      <CodeBlock title="main.py" code={collisionPy} />

      <p>
        <a
          href={`${REPO}/tree/main/examples/full-collision`}
          className="border-b-0 font-mono text-mute hover:bg-teal hover:text-ink"
        >
          [source]
        </a>
      </p>
    </div>
  );
}
