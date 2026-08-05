import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";
import FlowDiagram, {
  type FlowEdge,
  type FlowNode,
} from "../components/FlowDiagram";
import Toc from "../components/Toc";

const WIRING_NODES: FlowNode[] = [
  {
    id: "runner",
    x: 260,
    y: 0,
    w: 256,
    h: 80,
    title: "CollisionRunner",
    lines: ["from_game_type / from_world", "presets + tunables"],
    accent: "blue",
  },
  {
    id: "slide",
    x: 0,
    y: 208,
    w: 256,
    h: 80,
    title: "move_and_slide",
    lines: ["topdown · slide", "delta_x + delta_y"],
    accent: "teal",
  },
  {
    id: "platformer",
    x: 260,
    y: 208,
    w: 256,
    h: 80,
    title: "move_platformer",
    lines: ["platformer", "input_x + jump_pressed"],
    accent: "amber",
  },
  {
    id: "grounded",
    x: 520,
    y: 208,
    w: 256,
    h: 80,
    title: "move_grounded",
    lines: ["explicit velocity", "knockback, crates"],
    accent: "purple",
  },
];

const WIRING_EDGES: FlowEdge[] = [
  { from: "runner", to: "slide", fromOffset: 0.15 },
  { from: "runner", to: "platformer", fromOffset: 0.5 },
  { from: "runner", to: "grounded", fromOffset: 0.85 },
];

const TOC = [
  { id: "presets", label: "Game-type presets" },
  { id: "tunables", label: "Tunables" },
  { id: "attach", label: "Attach / detach / from_world" },
  { id: "result", label: "CollisionResult flags" },
  { id: "wiring", label: "Per-mode wiring" },
  { id: "validate", label: "validate_config & strict" },
];

const LOOP_TOP = `runner = CollisionRunner.from_game_type("topdown", tile_size=(32, 32))
# sprite needs only x, y, collision_shape

dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 160.0 * dt
dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 160.0 * dt
result = runner.move(player, tileset, tile_map, delta_x=dx, delta_y=dy)
if result.slide_vector:
    # move_and_slide kept a component you can build on
    pass`;

const LOOP_PLATFORM = `runner = CollisionRunner.from_game_type("platformer", tile_size=(32, 32))
# sprite needs x, y, collision_shape, vx, vy, on_ground

axis = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])          # -1 / 0 / 1
result = runner.move_platformer(
    player, tileset, tile_map, dt,
    input_x=float(axis), jump_pressed=keys[pygame.K_SPACE],
)
if result.on_ground:
    # step-up worked; you can jump next frame`;

export default function RunnerGuide() {
  return (
    <div className="content">
      <h1>CollisionRunner guide</h1>
      <p>
        The runner is the single public surface for movement. It composes five
        movement implementations behind one object: configure it once, call a{" "}
        <code>move_*</code> every frame, read the result. Everything below is
        the runner's actual behavior from <code>runtime/movement/</code>.
      </p>
      <Toc items={TOC} />

      <h2 id="presets">GAME-TYPE PRESETS</h2>
      <p>
        <code>
          CollisionRunner.from_game_type(name, tile_size=(32, 32), strict=False,
          render_scale=1.0)
        </code>{" "}
        is the recommended constructor. Presets:
      </p>
      <table>
        <thead>
          <tr>
            <th>game_type</th>
            <th>Mode</th>
            <th>Gravity</th>
            <th>Jump</th>
            <th>Sprite needs</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>platformer</code>
            </td>
            <td>
              <code>PLATFORMER</code>
            </td>
            <td>800 px/s²</td>
            <td>-400 px/s</td>
            <td>
              <code>x, y, collision_shape, vx, vy, on_ground</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>topdown</code>
            </td>
            <td>
              <code>SLIDE</code>
            </td>
            <td>0</td>
            <td>0</td>
            <td>
              <code>x, y, collision_shape</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>rpg</code>
            </td>
            <td>
              <code>RPG</code>
            </td>
            <td>0</td>
            <td>0</td>
            <td>
              <code>x, y, collision_shape</code>
            </td>
          </tr>
        </tbody>
      </table>
      <p>
        Unknown names raise <code>ValueError</code>. Everything the presets set
        is just attributes; tweak after construction. The generic{" "}
        <code>CollisionRunner(tile_size, mode, render_scale)</code> constructor
        also exists;
        <code>
          runner.move(sprite, tileset, tile_map, delta_x, delta_y, dt, ...)
        </code>{" "}
        dispatches on the configured mode (slide → <code>move_and_slide</code>,
        platformer → <code>move_platformer</code>, rpg → <code>move_rpg</code>).
      </p>

      <h2 id="tunables">TUNABLES</h2>
      <table>
        <thead>
          <tr>
            <th>Attribute</th>
            <th>Default</th>
            <th>What it does</th>
            <th>Change it when…</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>gravity</code>
            </td>
            <td>
              <code>800.0</code>
            </td>
            <td>
              px/s² applied to airborne sprites each frame (physics modes)
            </td>
            <td>your jump arcs feel floaty or stiff</td>
          </tr>
          <tr>
            <td>
              <code>max_fall_speed</code>
            </td>
            <td>
              <code>600.0</code>
            </td>
            <td>terminal velocity cap on falling</td>
            <td>sprites punch through thin floors at high fall speed</td>
          </tr>
          <tr>
            <td>
              <code>jump_strength</code>
            </td>
            <td>
              <code>-400.0</code>
            </td>
            <td>negative vy applied on jump (negative = up)</td>
            <td>tuning jump height</td>
          </tr>
          <tr>
            <td>
              <code>horizontal_speed</code>
            </td>
            <td>
              <code>200.0</code>
            </td>
            <td>
              built-in <code>input_x * horizontal_speed</code> sets{" "}
              <code>vx</code>
            </td>
            <td>walk/run speed feels wrong</td>
          </tr>
          <tr>
            <td>
              <code>step_height</code>
            </td>
            <td>
              <code>4.0</code>
            </td>
            <td>max stair/step height a grounded sprite climbs (px)</td>
            <td>you want to hop small ledges (raise) or not (lower)</td>
          </tr>
          <tr>
            <td>
              <code>ground_snap_tolerance</code>
            </td>
            <td>
              <code>2.0</code>
            </td>
            <td>how far the runner snaps a sprite onto ground</td>
            <td>sprites slide off 1px lips</td>
          </tr>
          <tr>
            <td>
              <code>max_walk_angle</code>
            </td>
            <td>
              <code>60.0</code>
            </td>
            <td>
              degrees from horizontal; steeper slopes are walls in{" "}
              <code>move_platformer_with_slide</code>
            </td>
            <td>slopes feel too climbable / not climbable enough</td>
          </tr>
          <tr>
            <td>
              <code>slide_friction</code>
            </td>
            <td>
              <code>0.1</code>
            </td>
            <td>validated config value (must be in [0, 1])</td>
            <td>—</td>
          </tr>
          <tr>
            <td>
              <code>rpg_snap_to_grid</code>
            </td>
            <td>
              <code>False</code>
            </td>
            <td>RPG-mode config flag (kept false; movement stays free)</td>
            <td>—</td>
          </tr>
        </tbody>
      </table>
      <Callout kind="warn" title="READ THE DEFAULTS BEFORE YOU TUNE">
        The presets exist so you don't have to guess. Change one value at a time
        and re-test the feeling; the runner validates ranges for you (see{" "}
        <code>validate_config</code> below).
      </Callout>

      <h2 id="attach">ATTACH / DETACH / FROM_WORLD</h2>
      <p>
        Without an attached world the runner resolves against whatever{" "}
        <code>(tileset_collision, tile_map)</code> you pass per call. Attach a{" "}
        <code>PhysicsWorld</code> and it resolves against the world's tiles{" "}
        <em>and</em> bodies uniformly; you pass <code>None, None</code>:
      </p>
      <CodeBlock
        title="attachment rules"
        code={`runner = CollisionRunner.from_world(world, game_type="platformer")   # preset + attach
# or the legacy two-step:
runner = CollisionRunner()
runner.attach(world)         # adopts world.tile_size + render_scale
runner.detach()              # back to per-call tile arguments

# one-off override of an attached world (does not change the attachment):
result = runner.move_platformer(player, None, None, dt, input_x=1.0, world=other_world)`}
      />
      <ul>
        <li>
          Attaching overrides the tile source and grid geometry;{" "}
          <code>detach()</code> falls back to per-call args.
        </li>
        <li>
          Multiple maps → one world per map, re-attach (or the per-call{" "}
          <code>world=</code> override).
        </li>
        <li>
          The runner also offers <code>get_tile_at(world_x, world_y)</code> and{" "}
          <code>get_nearby_tile_shapes(...)</code> for queries outside movement.
        </li>
      </ul>

      <h2 id="result">COLLISIONRESULT FLAGS</h2>
      <p>
        One dataclass, reset before each call: <code>collided</code>,{" "}
        <code>final_x</code>, <code>final_y</code>, <code>hit_wall_x</code>,{" "}
        <code>hit_wall_y</code>, <code>hit_ceiling</code>,{" "}
        <code>on_ground</code>, <code>slide_vector</code>. Full semantics on the{" "}
        <a href="/physics#result">Physics &amp; Bodies</a> page; the short
        version: branch on <code>hit_wall_x</code> for walls,{" "}
        <code>on_ground</code> for landing, and read <code>slide_vector</code>{" "}
        in slide mode.
      </p>
      <Callout kind="note" title="ONE RESULT OBJECT, REUSED">
        The runner keeps a single reusable <code>CollisionResult</code> and
        resets its fields before each call. Don't stash a reference across{" "}
        <code>move_*</code> calls; read what you need from the returned object
        in the same frame.
      </Callout>

      <h2 id="wiring">PER-MODE WIRING</h2>
      <FlowDiagram
        title="move modes"
        nodes={WIRING_NODES}
        edges={WIRING_EDGES}
      />
      <h3>Top-down (slide)</h3>
      <CodeBlock title="game loop" code={LOOP_TOP} />
      <h3>Platformer</h3>
      <CodeBlock title="game loop" code={LOOP_PLATFORM} />
      <h3>Explicit velocity (knockback, crates, custom controllers)</h3>
      <CodeBlock
        title="velocity contract"
        code={`# velocity= skips gravity, input and jump; adopts (vx, vy) onto the sprite
result = runner.move_grounded(enemy, None, None, dt, velocity=(enemy.vx, enemy.vy))
if result.hit_wall_x:
    enemy.vx = 0.0      # runner zeroed vy on landing for you`}
      />

      <h2 id="validate">VALIDATE_CONFIG & STRICT</h2>
      <p>
        Presets call <code>validate_config()</code> automatically. Manual rules
        worth knowing:
      </p>
      <ul>
        <li>
          <code>PLATFORMER</code> mode requires <code>gravity &gt; 0</code>;
          zero gravity is a <code>ValueError</code>.
        </li>
        <li>
          <code>RPG</code> mode with <code>gravity &gt; 0</code> is a{" "}
          <code>ValueError</code>; top-down with gravity just warns (it's
          ignored in <code>move_and_slide</code>).
        </li>
        <li>
          <code>gravity &lt; 0</code> and <code>max_fall_speed &lt; 0</code> are
          errors; positive <code>jump_strength</code> warns.
        </li>
        <li>
          <code>strict=True</code> turns warnings into raised{" "}
          <code>ValueError</code>.
        </li>
      </ul>
    </div>
  );
}
