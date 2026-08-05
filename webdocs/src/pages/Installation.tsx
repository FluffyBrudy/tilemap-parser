import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";
import { Link } from "react-router-dom";
import { VERSION } from "../nav";

export default function Installation() {
  return (
    <div className="content">
      <h1>Installation</h1>

      <CodeBlock title="terminal" code={`pip install tilemap-parser`} />

      <p>
        Current release is <strong>v{VERSION}</strong>. The package needs{" "}
        <strong>Python {">="} 3.10</strong> and pulls in{" "}
        <code>pygame-ce {">="} 2.5</code> automatically, the only dependency.
      </p>

      <h2 id="editor">THE EDITOR COMPANION</h2>
      <p>
        Maps and collision files are authored in{" "}
        <a href="https://pypi.org/project/tilemap-editor/">tilemap-editor</a>;
        the parser reads its JSON directly.
      </p>
      <CodeBlock title="terminal" code={`pip install tilemap-editor`} />
      <p>
        You don't need the editor to <em>use</em> the parser. You can
        hand-write a <code>map.json</code> and a <code>.collision.json</code>,
        but the editor is how the JSON formats stay consistent. See{" "}
        <Link to="/json">JSON Formats</Link>.
      </p>

      <h2 id="verify">VERIFY IT WORKS</h2>
      <CodeBlock
        title="terminal"
        code={`python -c "import pygame; from tilemap_parser import load_map, PhysicsWorld, CollisionRunner; print('ok')"`}
      />

      <h2 id="venv">USE A VIRTUAL ENV</h2>
      <p>Game dev dependency roulette is real. Keep it isolated:</p>
      <CodeBlock
        title="terminal"
        code={`python -m venv .venv
source .venv/bin/activate      # Windows: .venv\\Scripts\\activate
pip install tilemap-parser`}
      />

      <h2 id="examples">RUN THE EXAMPLES</h2>
      <p>
        The examples live in the repository and import the source directly.
        Clone, install editable, run:
      </p>
      <CodeBlock
        title="terminal"
        code={`git clone https://github.com/FluffyBrudy/tilemap-parser
cd tilemap-parser
pip install -e .
cd examples/physics-crate
python main.py          # push some crates`}
      />

      <Callout kind="tip" title="PYGAME INIT">
        Runtime features that touch pygame surfaces (sprites, rendering,{" "}
        <code>SpriteAnimationSet.load</code>) need pygame initialized. Some
        entry points init it for you; when in doubt call{" "}
        <code>pygame.init()</code> first.
      </Callout>
    </div>
  );
}
