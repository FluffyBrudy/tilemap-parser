import CodeBlock from "../components/CodeBlock";

export default function TechnicalNotes() {
  return (
    <div className="content">
      <h1>Technical Notes</h1>
      <p>
        Edge conventions, scale rules and performance facts that the guides
        assume. All of these are the library's actual behavior, stated
        precisely.
      </p>

      <h2 id="edges">EDGE CONVENTIONS</h2>
      <ul>
        <li>
          <strong>
            Polygon queries are half-open on right and bottom edges.
          </strong>{" "}
          A sprite sitting exactly on a tile's right or bottom boundary does not
          count as colliding; the left and top edges are inclusive. This is what
          lets two solids rest flush without false positives.
        </li>
        <li>
          <strong>Object-manager AABB checks are inclusive</strong>: touching
          bounding boxes in <code>ObjectCollisionManager</code> count as
          overlapping, so <code>resolve()</code> pushes apart with zero overlap.
        </li>
      </ul>

      <h2 id="scale">RENDER_SCALE</h2>
      <ul>
        <li>
          <code>TilemapData.render_scale</code> is adopted by{" "}
          <code>PhysicsWorld</code> and by the runner on attach; rendering and
          collision stay in the same pixel space.
        </li>
        <li>
          Effective tile size is <code>tile_size × render_scale</code>; tile{" "}
          <code>(col, row)</code> occupies{" "}
          <code>(col × eff_w, row × eff_h)</code>. A{" "}
          <code>render_scale ≤ 0</code> raises <code>ValueError</code> in both
          the renderer and the runner.
        </li>
        <li>
          Polygon vertices are scaled by <code>render_scale</code> when
          transformed to world space; author collision in tile-local pixels,
          scale for free.
        </li>
      </ul>

      <h2 id="modes">BODY MODES ARE PROMISES</h2>
      <p>
        <code>"static"</code> and <code>"kinematic"</code> do not imply
        physics-engine dynamics. Velocity is scripted, Godot{" "}
        <code>StaticBody2D</code>/<code>CharacterBody2D</code> style. A
        kinematic body moves only when your loop drives it through a{" "}
        <code>move_*</code> call with explicit velocity.
      </p>

      <h2 id="oneway">ONE-WAY, PRECISELY</h2>
      <ul>
        <li>
          Only <code>move_platformer</code> and{" "}
          <code>move_platformer_with_slide</code> honor <code>one_way</code>{" "}
          polygons (block from above, pass from below).
        </li>
        <li>
          The flag is <strong>authored in the collision JSON</strong>, per
          polygon — never in the map JSON, and never auto-detected. Control is
          authoring-level only: there is no runtime per-sprite "make platforms
          solid" override. Your levers are the JSON flag and the movement
          method you call.
        </li>
        <li>
          Gating is approach-based: a one-way polygon blocks only when the
          sprite is <em>falling</em> (<code>vy &gt; 0</code>) and its previous
          bottom was above the platform top — fast falls can't tunnel, and
          jumping up through always passes.
        </li>
        <li>
          The horizontal phase never sees one-way polygons (they can't wall
          you); the landing snap re-includes them with from-above gating.
        </li>
        <li>
          <code>move_grounded</code> treats one-way polygons as plain solid
          geometry.
        </li>
        <li>Bodies are never one-way; they block from every direction.</li>
        <li>
          The renderer doesn't know the flag exists: one-way tiles draw like
          any other tile. For dashed-edge overlays, query{" "}
          <code>world.tile_map</code> + the collision tileset at runtime (see
          the Map Parsing page).
        </li>
      </ul>

      <h2 id="velocity">VELOCITY CONTRACT, RECAP</h2>
      <p>
        Physics modes with <code>velocity=(vx, vy)</code>: skip
        gravity/input/jump, adopt the velocity onto the sprite, zero{" "}
        <code>vx</code> on wall hit, zero <code>vy</code> on landing.
        Displacement modes (<code>move_and_slide</code> and{" "}
        <code>move_rpg</code>) never read or write <code>vx/vy</code>.
      </p>

      <h2 id="perf">PERFORMANCE NOTES</h2>
      <ul>
        <li>
          <strong>Movement queries are zero-allocation on the hot path.</strong>{" "}
          <code>_collides_at</code> iterates tiles and shapes inline and exits
          on the first hit; <code>get_nearby_tile_shapes</code> (which
          allocates) exists for your own queries, not for movement.
        </li>
        <li>
          <strong>
            The runner reuses one <code>CollisionResult</code>.
          </strong>{" "}
          Fields are reset per call. Read the return value in the same frame.
        </li>
        <li>
          <strong>Rendering is chunk-culled</strong> (32×32-tile chunks), with
          per-layer <code>z_index</code> sorting and a tile-variant cache.{" "}
          <code>warm_cache()</code> pre-bakes variants and frees the source map
          data.
        </li>
        <li>
          <strong>Object collision uses a uniform spatial grid</strong> rebuilt
          per <code>check_all_collisions()</code>; single-object queries are a
          linear scan. <code>cell_size</code> (default 128) is the tuning knob;
          benchmark with{" "}
          <code>examples/comparison/spatial-cell-size-tuning.py</code>.
        </li>
        <li>
          <strong>Circle/capsule bodies are polygon-approximated</strong>{" "}
          (16-edge ngon / stepped capsule) only for slide-mode normal
          computation; the tile resolver works on polygon edges.
        </li>
      </ul>

      <h2 id="camera">CAMERA FACTS</h2>
      <ul>
        <li>
          <code>mode="centered"</code>: target always at viewport center (lerp
          if <code>lerp_speed &gt; 0</code>).
        </li>
        <li>
          <code>mode="deadzone"</code>: camera only moves when the target leaves
          a centered box.
        </li>
        <li>
          <code>shake(duration, intensity)</code> adds a random per-frame offset
          inside <code>offset</code>; it does not move the target.{" "}
          <code>bounds = (min_x, min_y, max_x, max_y)</code> clamps the camera
          position.
        </li>
      </ul>

      <h2 id="grid">THE WORLD OWNS, THE RUNNER RESOLVES</h2>
      <p>
        One space, one runner. Tiles and bodies are solids in the same space;
        the runner resolves movement against the union. The world does not
        simulate sprite-vs-sprite contact; that's{" "}
        <code>ObjectCollisionManager</code>. If you can draw it, you can move
        it; if you can move it, it can be pushed.
      </p>
    </div>
  );
}
