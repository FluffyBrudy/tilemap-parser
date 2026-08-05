import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";

const LOOP = `manager = ObjectCollisionManager(cell_size=128.0)   # uniform spatial grid
manager.add_object(player)
manager.add_object(enemy1)
manager.add_object(enemy2)

# per frame: all-vs-all
for hit in manager.check_all_collisions():
    hit.resolve()          # separate both objects along the normal
    # or: vx, vy = hit.slide_velocity(player.vx, player.vy)  # strip approach

# or one-vs-all (enemy against everything, linear scan)
for hit in manager.check_object(enemy1):
    if hit.involves(player):
        print("enemy touched the player")
        other = hit.other(enemy1)      # -> player`;

export default function ObjectCollision() {
  return (
    <div className="content">
      <h1>Object Collision: the sprite-vs-sprite lane</h1>
      <p>
        The physics world resolves sprites against tiles and bodies. It does{" "}
        <strong>not</strong> resolve sprite against sprite; that's a separate
        lane, on purpose. Two characters touching is{" "}
        <code>ObjectCollisionManager</code>'s job.
      </p>

      <h2 id="why">WHY IT'S SEPARATE</h2>
      <ul>
        <li>
          The world's job is <em>movement resolution</em> (don't let sprites
          walk into solids).
        </li>
        <li>
          The manager's job is <em>contact detection</em> between moving things
          (who touched who, how deep).
        </li>
        <li>
          Different queries, different cadence: the world runs every{" "}
          <code>move_*</code>; the manager runs one{" "}
          <code>check_all_collisions()</code> pass per frame.
        </li>
      </ul>
      <p>
        The manager is a uniform spatial grid (<code>cell_size=128.0</code> by
        default, rebuilt per query): objects only narrowphase against objects
        in their own or adjacent cells. Mixed shapes all work: rect, circle,
        capsule, polygon, and multi-shape objects (via a{" "}
        <code>collision_shapes</code> attribute).
      </p>

      <h2 id="api">THE API</h2>
      <table>
        <thead>
          <tr>
            <th>Method</th>
            <th>Does</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>add_object(obj)</code>
            </td>
            <td>register; duplicates warn and are skipped</td>
          </tr>
          <tr>
            <td>
              <code>remove_object(obj)</code>
            </td>
            <td>unregister; missing objects warn</td>
          </tr>
          <tr>
            <td>
              <code>clear()</code>
            </td>
            <td>remove everything</td>
          </tr>
          <tr>
            <td>
              <code>check_all_collisions()</code>
            </td>
            <td>all-vs-all via the grid; each pair reported once</td>
          </tr>
          <tr>
            <td>
              <code>check_object(obj)</code>
            </td>
            <td>one object vs all others (linear scan; need not be managed)</td>
          </tr>
          <tr>
            <td>
              <code>check_object_first(obj)</code>
            </td>
            <td>first hit only, in insertion order</td>
          </tr>
        </tbody>
      </table>
      <p>
        Each hit is a{" "}
        <code>CollisionHit(object_a, object_b, normal, depth)</code>:
      </p>
      <table>
        <thead>
          <tr>
            <th>Member</th>
            <th>Does</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>normal</code>
            </td>
            <td>direction to separate (from A to B)</td>
          </tr>
          <tr>
            <td>
              <code>depth</code>
            </td>
            <td>penetration depth</td>
          </tr>
          <tr>
            <td>
              <code>resolve()</code>
            </td>
            <td>separates both objects by half the depth along the normal</td>
          </tr>
          <tr>
            <td>
              <code>slide_velocity(vx, vy)</code>
            </td>
            <td>
              projects a velocity onto the surface; approach component stripped
            </td>
          </tr>
          <tr>
            <td>
              <code>involves(obj)</code> / <code>other(obj)</code>
            </td>
            <td>who's in this hit</td>
          </tr>
        </tbody>
      </table>

      <h2 id="wiring">WIRING IT IN</h2>
      <CodeBlock title="the sprite-vs-sprite lane" code={LOOP} />
      <Callout
        kind="warn"
        title="LAYER FILTERING IS MUTUAL: SAME RULE AS THE WORLD"
      >
        <code>should_collide</code> requires both sides to agree:{" "}
        <code>(a_mask &amp; b_layer) != 0 and (b_mask &amp; a_layer) != 0</code>
        . Filter on both objects or not at all.
      </Callout>

      <h2 id="tuning">CELL SIZE TUNING</h2>
      <p>
        <code>cell_size</code> is a cost trade-off. Too small: many empty cells,
        grid rebuild overhead. Too big: every object ends up in the same cell
        and the broadphase is a lie. For 32px tiles, 128 is a sane default; the{" "}
        <a href="/examples">comparison example</a>{" "}
        <code>spatial-cell-size-tuning.py</code> benchmarks this empirically.{" "}
        <code>cell_size</code> must be finite and positive; anything else
        raises <code>ValueError</code>.
      </p>
    </div>
  );
}
