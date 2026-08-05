import { Link } from "react-router-dom";
import CodeBlock from "../components/CodeBlock";
import { REPO } from "../nav";

import pathfindingPy from "../../../examples/full-pathfinding/main.py?raw";

export default function FullPathfinding() {
  return (
    <div className="content">
      <h1>Full Pathfinding</h1>
      <p>
        A complete, self-contained pathfinding demo in one file:{" "}
        <code>NavGrid</code>, <code>Pathfinder</code> and{" "}
        <code>PathFollower</code> wired into a click-to-play maze. No external
        data; the maze and collision data are procedural.
      </p>
      <p>
        Intentionally minimal: the{" "}
        <Link to="/pathfinding" className="border-b-0 font-mono text-teal">
          Pathfinding guide
        </Link>{" "}
        covers the API in depth. This is the whole thing running.
      </p>

      <CodeBlock title="main.py" code={pathfindingPy} />

      <p>
        <a
          href={`${REPO}/tree/main/examples/full-pathfinding`}
          className="border-b-0 font-mono text-mute hover:bg-teal hover:text-ink"
        >
          [source]
        </a>
      </p>
    </div>
  );
}
