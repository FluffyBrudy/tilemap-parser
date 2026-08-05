import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";
import Toc from "../components/Toc";
import { Link } from "react-router-dom";

const TOC = [
  { id: "three-jobs", label: "Three jobs, three owners" },
  { id: "wiring", label: "The two-minute wiring" },
  { id: "contract", label: "The object contract" },
  { id: "five-methods", label: "The five move methods" },
  { id: "velocity-contract", label: "The velocity contract" },
  { id: "sliding-box", label: "The sliding box" },
  { id: "result", label: "Reading CollisionResult" },
  { id: "layers", label: "Layers & masks" },
  { id: "coords", label: "Coordinate space" },
  { id: "traps", label: "Traps, ranked" },
];

const WRING = `from tilemap_parser import (
    CollisionRunner, PhysicsWorld, Body, RectangleShape,
    load_map, load_tileset_collision,
)

game_data = load_map("map.json")
tileset   = load_tileset_collision("map.collision.json")

world  = PhysicsWorld.from_map(game_data, tileset)   # adopts tile_size + render_scale
runner = CollisionRunner.from_world(world, game_type="platformer")

result = runner.move_platformer(player, None, None, dt, input_x=1.0, jump_pressed=False)`;

const CONTRACT = `class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.collision_shape = RectangleShape(width=24, height=28)
        self.collision_layer = 1          # optional, defaults
        self.collision_mask = 0xFFFFFFFF`;

const PUSH = `# 1. player moves against everything
result = runner.move_platformer(player, None, None, dt, input_x=float(axis), jump_pressed=jump)

# 2. pressed against a wall? find what is in the way
if result.hit_wall_x and axis != 0:
    block = world.collides_with_body(player)
    if block is None:
        block = body_ahead(world, player, axis)   # probe a few px into the wall
    if block is not None and block.mode == "kinematic":
        block.vx = axis * PUSH_SPEED              # hand the crate a velocity

# 3. drive every body that has a velocity
for crate in world.bodies:
    if crate.vx:
        crate_result = runner.move_grounded(crate, None, None, dt, velocity=(crate.vx, crate.vy))
        if crate_result.hit_wall_x:
            crate.vx = 0.0                        # crate meets crate/tile wall -> stop
        else:
            crate.vx *= 0.9                       # friction: sliding crates slow down
            if abs(crate.vx) < 1.0:
                crate.vx = 0.0`;

const PROBE = `def body_ahead(world, sprite, axis, probe=8.0):
    s = copy.copy(sprite)
    s.x = sprite.x + axis * probe
    return world.collides_with_body(s)`;

export default function PhysicsBodies() {
  return (
    <div className="content">
      <h1>Collision, without the fog of war</h1>
      <Toc items={TOC} />

      <h2 id="three-jobs">THREE JOBS, THREE OWNERS</h2>
      <p>
        Collision is three jobs, and the library splits them on purpose. Learn
        the split and nothing else surprises you.
      </p>
      <table>
        <thead>
          <tr>
            <th>Job</th>
            <th>Who does it</th>
            <th>Owns</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Where solids live</td>
            <td>
              <code>PhysicsWorld</code>
            </td>
            <td>
              the collision tile layer, the <code>TilesetCollision</code>{" "}
              geometry, the list of <code>Body</code> solids, and the grid (
              <code>tile_size</code>, <code>render_scale</code>)
            </td>
          </tr>
          <tr>
            <td>How things move</td>
            <td>
              <code>CollisionRunner</code>
            </td>
            <td>
              the five <code>move_*</code> methods, gravity, tunables,{" "}
              <code>CollisionResult</code>
            </td>
          </tr>
          <tr>
            <td>What can be moved</td>
            <td>your sprite</td>
            <td>
              <code>x</code>, <code>y</code>, <code>collision_shape</code>; that
              is the whole contract
            </td>
          </tr>
        </tbody>
      </table>
      <p>
        Tiles and bodies are <em>both</em> just solids in the world. The runner
        never cares which one it hit; it resolves movement against the union of
        them. If you can draw it, you can collide with it.
      </p>

      <h2 id="wiring">THE TWO-MINUTE WIRING</h2>
      <CodeBlock title="wiring.py" code={WRING} />
      <p>
        Note the <code>from_world</code> constructor: it applies the game-type
        preset <em>and</em> attaches the world in one step. From then on every{" "}
        <code>move_*</code> call resolves against the world's tiles <em>and</em>{" "}
        bodies, so you pass <code>None, None</code> for the tile arguments. The
        legacy spelling{" "}
        <code>runner = CollisionRunner(); runner.attach(world)</code> still
        works.
      </p>
      <ul>
        <li>
          Attaching <strong>overrides the tile source and grid geometry</strong>
          ; <code>runner.detach()</code> falls back to per-call tile arguments.
        </li>
        <li>
          The tile source is <strong>locked at attach</strong>. Multiple maps?
          One world per map, re-attach, or pass <code>world=other_world</code>{" "}
          as the last argument of any move call for a one-off override.
        </li>
        <li>
          Per-call <code>(tileset_collision, tile_map)</code> still works; the
          world is optional, not required.
        </li>
      </ul>

      <h2 id="contract">THE OBJECT CONTRACT</h2>
      <CodeBlock title="player.py" code={CONTRACT} />
      <table>
        <thead>
          <tr>
            <th>Attribute</th>
            <th>Required</th>
            <th>Used by</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>x</code>, <code>y</code>
            </td>
            <td>yes</td>
            <td>
              position; shape origin: top-left for <code>RectangleShape</code>,
              center for <code>CircleShape</code>, top cap center for{" "}
              <code>CapsuleShape</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>collision_shape</code>
            </td>
            <td>yes</td>
            <td>
              primitives only; polygon shapes use <code>MapObject</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>vx</code>, <code>vy</code>
            </td>
            <td>physics modes</td>
            <td>
              <code>move_platformer</code>,{" "}
              <code>move_platformer_with_slide</code>,{" "}
              <code>move_grounded</code>
            </td>
          </tr>
          <tr>
            <td>
              <code>on_ground</code>
            </td>
            <td>platformer</td>
            <td>grounded state, step-up, jump</td>
          </tr>
          <tr>
            <td>
              <code>collision_layer</code> / <code>collision_mask</code>
            </td>
            <td>optional</td>
            <td>body filtering; both sides must agree</td>
          </tr>
        </tbody>
      </table>
      <p>
        <code>Body</code> is the same contract plus a <code>mode</code> (
        <code>"static"</code> / <code>"kinematic"</code>) and{" "}
        <code>game_id</code>. It is the authoring surface for <em>solids</em>,
        not sprites.
      </p>
      <Callout kind="warn" title="POSITION + SHAPE IS INERT DATA">
        A sprite only collides with anything once it goes through the runner.{" "}
        <code>world.collides_with_body(sprite)</code> can <em>test</em> it, but
        nothing <em>resolves</em> it until a <code>move_*</code> call runs.
      </Callout>

      <h2 id="five-methods">THE FIVE MOVE METHODS: PICK BY INPUT MODEL</h2>
      <table>
        <thead>
          <tr>
            <th>Method</th>
            <th>You feed it</th>
            <th>Gravity?</th>
            <th>Wall response</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>move_and_slide</code>
            </td>
            <td>
              displacement <code>delta_x, delta_y</code>
            </td>
            <td>no</td>
            <td>
              slide along the wall; <code>slide_vector</code> reports what's
              left
            </td>
          </tr>
          <tr>
            <td>
              <code>move_rpg</code>
            </td>
            <td>displacement</td>
            <td>no</td>
            <td>full block; a diagonal into a corner stops you dead</td>
          </tr>
          <tr>
            <td>
              <code>move_grounded</code>
            </td>
            <td>
              nothing; reads <code>sprite.vx/vy</code>, applies gravity
            </td>
            <td>yes</td>
            <td>
              full block; <code>vx</code> zeroed on wall hit, <code>vy</code>{" "}
              zeroed on landing
            </td>
          </tr>
          <tr>
            <td>
              <code>move_platformer</code>
            </td>
            <td>
              <code>input_x</code> in [-1, 1] + <code>jump_pressed</code>
            </td>
            <td>yes</td>
            <td>full block + step-up + one-way platforms</td>
          </tr>
          <tr>
            <td>
              <code>move_platformer_with_slide</code>
            </td>
            <td>same as above</td>
            <td>yes</td>
            <td>
              everything above, plus walkable slopes (gated by{" "}
              <code>max_walk_angle</code>)
            </td>
          </tr>
        </tbody>
      </table>
      <p>
        Rule of thumb: <strong>displacement methods for top-down games</strong>{" "}
        (you do the velocity math, the runner does the geometry),{" "}
        <strong>physics methods for platformers</strong> (the runner owns
        gravity and landing). <code>move_and_slide</code> never reads or writes{" "}
        <code>vx</code>/<code>vy</code>.
      </p>
      <p>
        <strong>Why move_and_slide slides:</strong> it tries the full move first
        (fast path). If that collides, it retries the X-only and Y-only moves.
        Diagonal into a wall → the X-only move collides, so it retracts X and
        keeps Y; you've slid. If <em>neither</em> axis alone collides
        (you clipped a corner dead-on) it picks the dominant axis and slides
        along the other. For slopes, pass <code>slope_slide=True</code> and it
        runs up to 4 projection passes, each stripping the component of motion
        that points into the colliding edge's normal.
      </p>

      <h2 id="velocity-contract">THE VELOCITY CONTRACT</h2>
      <p>
        In the three physics modes, when you pass <code>velocity=(vx, vy)</code>
        :
      </p>
      <ul>
        <li>
          the runner <strong>skips</strong> its own gravity, input and jump; it
          only resolves collision for that velocity;
        </li>
        <li>
          it <strong>adopts</strong> the velocity onto the sprite (
          <code>sprite.vx</code>, <code>sprite.vy</code> are set);
        </li>
        <li>
          you own the velocity; the runner zeroes <code>vx</code> on a wall hit
          and <code>vy</code> on landing.
        </li>
      </ul>
      <CodeBlock
        title="crate falls: you apply gravity"
        code={`crate.vy += 800.0 * dt                      # you apply gravity
result = runner.move_grounded(crate, None, None, dt, velocity=(crate.vx, crate.vy))
if result.hit_wall_x:
    crate.vx = 0.0                          # the runner zeroes vy on landing itself`}
      />
      <Callout kind="warn" title="ONE OWNERSHIP MODEL PER OBJECT">
        Without <code>velocity=</code>, <code>move_grounded</code> and{" "}
        <code>move_platformer</code> apply their own gravity and read the
        velocity off <code>sprite.vx/vy</code>. Double-applying gravity is a
        classic bug; pick one model per object per frame.
      </Callout>

      <h2 id="sliding-box">OBJECTS IN THE PHYSICS WORLD: THE SLIDING BOX</h2>
      <p>
        This is the centerpiece, straight from{" "}
        <code>examples/physics-crate/main.py</code> (tested, correct): a floor,
        a wall column, three crates, a player. Walk into a crate and watch it
        slide; push it into another crate and it stops; jump on top of a crate
        and stand on it.
      </p>

      <h3>Author the world and its bodies</h3>
      <CodeBlock
        title="scene.py"
        code={`world = PhysicsWorld(tile_map=tile_map, tileset_collision=tileset, tile_size=(32, 32))

crates = [
    Body(RectangleShape(width=32, height=32), x=8 * 32, y=floor_y - 32, mode="kinematic"),
    Body(RectangleShape(width=32, height=32), x=10 * 32, y=floor_y - 32, mode="kinematic"),
]
for crate in crates:
    world.add_body(crate)          # <-- nothing collides until this happens`}
      />
      <p>
        <code>mode</code> is a <em>promise</em>, not a physics flag.{" "}
        <code>"static"</code> never moves (scenery);
        <code>"kinematic"</code> is moved explicitly by your code each frame.{" "}
        <strong>Nothing moves a kinematic body except you</strong>: the player
        walking into it does not shove it; that's the push loop below. Bodies
        take primitive shapes only (anything else raises <code>TypeError</code>
        ), and a body never blocks itself.
      </p>
      <Callout kind="danger" title="THE RULE YOU CAN'T SKIP">
        A body participates in movement resolution <em>only because</em> it is
        in <code>world.bodies</code> and a runner is attached to that world. Add
        a body but forget the attach, and the player walks straight through it.
      </Callout>

      <h3>Bodies already block and support: no extra code</h3>
      <p>
        Once the crate is in the world it is <em>already</em> a wall, a landing
        surface and a step. The player's single <code>move_platformer</code>{" "}
        call resolves against tiles <em>and</em> the crates. Jump onto a crate
        and the platformer step-up logic puts you on top; the Y phase checks{" "}
        <code>world.collides_with_body</code> exactly like it checks tiles.
      </p>

      <h3>The push: where the velocity contract earns its keep</h3>
      <CodeBlock title="the push loop" code={PUSH} />
      <p>Walk through what happens:</p>
      <ul>
        <li>
          The player is stopped by the crate's side (it's a solid), so{" "}
          <code>hit_wall_x</code> is true.
        </li>
        <li>
          <code>world.collides_with_body(player)</code> identifies{" "}
          <em>which</em> solid, and we only push it if{" "}
          <code>mode == "kinematic"</code>. Static walls never move.
        </li>
        <li>
          The crate gets <code>vx = axis * 260.0</code>, then step 3 drives it
          with <code>move_grounded(..., velocity=...)</code>: explicit velocity,
          so no gravity, no ledge detection, pure collision resolution.
        </li>
        <li>
          The crate slides. When it presses into the <em>next</em> crate (or the
          tile wall), <code>move_grounded</code> sees a wall, sets{" "}
          <code>hit_wall_x</code>, and we zero <code>vx</code>. Crates block
          each other because step 3 resolves every crate against the world's{" "}
          <em>other</em> crates too.
        </li>
      </ul>
      <p>
        That's the entire loop:{" "}
        <strong>
          read the result, assign velocity, drive bodies through the runner,
          read the result again.
        </strong>{" "}
        The runner never simulates pushing on its own, but give it a velocity
        per frame and it behaves exactly like one.
      </p>

      <h3>The sub-pixel gap: why the probe exists</h3>
      <p>
        The runner stops a sprite a <em>fraction of a pixel</em> short of a body
        (a skin gap so resting contact never jitters into a tunnel).
        Consequence: at the resting position,{" "}
        <code>world.collides_with_body(player)</code> can return{" "}
        <code>None</code>. The demo probes a few pixels into the push direction:
      </p>
      <CodeBlock title="probe.py" code={PROBE} />
      <Callout kind="tip" title="STATIC QUERIES AND RESTING SPRITES">
        Static overlap queries are only reliable away from the surface the
        runner already resolved. If you need to know what's <em>in front of</em>{" "}
        a resting sprite, probe into the movement direction; don't trust the
        exact resting position.
      </Callout>

      <h3>The interaction table</h3>
      <table>
        <thead>
          <tr>
            <th>Pair</th>
            <th>Mechanism</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>sprite ↔ tiles</td>
            <td>
              runner queries (all <code>move_*</code>)
            </td>
            <td>automatic</td>
          </tr>
          <tr>
            <td>sprite ↔ body</td>
            <td>
              runner + <code>world.collides_with_body(sprite)</code>
            </td>
            <td>automatic + hit-testing</td>
          </tr>
          <tr>
            <td>body ↔ body</td>
            <td>
              <code>move_grounded(body, ..., velocity=...)</code>
            </td>
            <td>crates block crates</td>
          </tr>
          <tr>
            <td>sprite ↔ sprite</td>
            <td>
              <strong>not the world</strong>;{" "}
              <code>ObjectCollisionManager</code>
            </td>
            <td>separate lane, spatial grid</td>
          </tr>
        </tbody>
      </table>
      <p>
        The world is not a physics engine. It resolves movement against tiles
        and bodies; it does not simulate sprite-vs-sprite contact. That's{" "}
        <a href="/object-collision">ObjectCollisionManager's lane</a>.
      </p>

      <h2 id="result">READING COLLISIONRESULT</h2>
      <table>
        <thead>
          <tr>
            <th>Flag</th>
            <th>Meaning</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>collided</code>
            </td>
            <td>anything hit at all, including a landing</td>
          </tr>
          <tr>
            <td>
              <code>final_x</code> / <code>final_y</code>
            </td>
            <td>where the runner parked you</td>
          </tr>
          <tr>
            <td>
              <code>hit_wall_x</code>
            </td>
            <td>movement along X was blocked</td>
          </tr>
          <tr>
            <td>
              <code>hit_wall_y</code>
            </td>
            <td>
              movement along Y was blocked (landing or ceiling, displacement
              modes)
            </td>
          </tr>
          <tr>
            <td>
              <code>hit_ceiling</code>
            </td>
            <td>head bonk (physics modes)</td>
          </tr>
          <tr>
            <td>
              <code>on_ground</code>
            </td>
            <td>feet on something solid</td>
          </tr>
          <tr>
            <td>
              <code>slide_vector</code>
            </td>
            <td>
              <code>move_and_slide</code> only: the movement component that
              survived
            </td>
          </tr>
        </tbody>
      </table>
      <p>
        The runner mutates <code>sprite.x/y</code> in place; after the call the
        sprite is wherever it ended up; <code>final_*</code> is for when you
        want to know <em>where</em> without inspecting it. And{" "}
        <code>hit_wall_x</code> vs <code>collided</code>: in the crate loop we
        branch on <code>hit_wall_x</code> precisely so a landing doesn't zero
        the crate's push velocity.
      </p>

      <h2 id="layers">LAYERS & MASKS: BOTH SIDES MUST AGREE</h2>
      <p>
        Filtering is <em>mutual agreement</em>, not either-or. Two objects
        collide only if <strong>both</strong> pass:
      </p>
      <CodeBlock
        title="hit.py: the actual rule"
        code={`(a_mask & b_layer) != 0 and (b_mask & a_layer) != 0`}
      />
      <p>
        Defaults are <code>collision_layer=1</code>,{" "}
        <code>collision_mask=0xFFFFFFFF</code>. This gates{" "}
        <code>world.collides_with_body</code> and therefore every body
        interaction inside every <code>move_*</code>. The AND is deliberate: it
        makes "should these two interact" symmetric, so one object can't
        silently filter a pair the other expected.
      </p>

      <h2 id="coords">COORDINATE SPACE</h2>
      <ul>
        <li>
          <strong>One coordinate system.</strong> Tiles and sprites live in the
          same pixel space. Tile <code>(col, row)</code> occupies{" "}
          <code>(col * tile_w, row * tile_h)</code>.
        </li>
        <li>
          <strong>Rectangles:</strong> <code>(x, y)</code> is the top-left (plus
          the shape's <code>offset</code>). <strong>Circles:</strong>{" "}
          <code>(x, y)</code> is the center. <strong>Capsules:</strong>{" "}
          <code>(x, y)</code> is the <em>top cap's</em> center — the draw box is{" "}
          <code>(x - radius, y - radius)</code> sized{" "}
          <code>2r × (2r + height)</code>, and the capsule is vertical-only
          (there is no horizontal capsule).
        </li>
        <li>
          <strong>Bodies are never one-way.</strong>{" "}
          <code>Body.top_y_at(world_x)</code> samples the top surface, but
          bodies block from every direction. One-way is a tile-polygon feature (
          <code>poly.one_way</code>), and only the platformer family honors it;{" "}
          <code>move_grounded</code> treats one-way polygons as plain solid.
        </li>
      </ul>

      <h2 id="traps">TRAPS, RANKED BY HOW OFTEN THEY FIRE</h2>
      <ol>
        <li>
          <strong>Rectangle top-left vs circle center.</strong> Swap coordinate
          conventions and your sprite teleports half its size into the floor.{" "}
          <Link to="/quick-start#top-left-vs-center">
            The Quick Start warning covers anchoring and width in full
          </Link>
          .
        </li>
        <li>
          <strong>Attach before you move.</strong> A runner without{" "}
          <code>attach</code>/<code>from_world</code> ignores the world
          entirely; bodies become ghosts. <code>from_world</code> does both;
          prefer it.
        </li>
        <li>
          <strong>
            <code>velocity=</code> skips gravity.
          </strong>{" "}
          Every frame you forget to apply it, the crate hovers.
        </li>
        <li>
          <strong>Pushing the wrong mode.</strong> Only{" "}
          <code>mode == "kinematic"</code> bodies should receive velocity.
        </li>
        <li>
          <strong>The skin gap.</strong> A resting sprite can fail a static
          overlap query. Probe into the direction of motion.
        </li>
        <li>
          <strong>Tiles with no collision data.</strong> A <code>tile_map</code>{" "}
          without a matching <code>tileset_collision</code> raises{" "}
          <code>ValueError</code> at world construction, by design, so you can't
          ship an empty world.
        </li>
        <li>
          <strong>One-way layer filtering.</strong> Collision requires both
          objects' masks to allow the pair, so either one excluding the other's
          layer prevents the hit.
        </li>
      </ol>

      <p>
        Next: the <a href="/runner">CollisionRunner guide</a>: presets,
        tunables, and per-mode wiring. Or the full{" "}
        <a href="/pipeline">end-to-end pipeline</a>.
      </p>
    </div>
  );
}
