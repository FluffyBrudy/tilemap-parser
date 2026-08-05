import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";

export default function Particles() {
  return (
    <div className="content">
      <h1>Particles: visual effects</h1>
      <p>
        The particle system is one config per effect, one{" "}
        <code>ParticleSystem</code> per emitter. A system owns exactly one
        emitter; for two effects you build two systems. Configs come from the
        tilemap-editor's particle JSON or are built by hand with{" "}
        <code>ParticleSystemConfig</code>.
      </p>

      <h2 id="setup">LOADING AND BUILDING</h2>
      <p>
        <code>parse_particle_file()</code> returns a list of{" "}
        <code>ParticleSystemConfig</code>s (one per effect in the file). Pick
        one, wrap it in a <code>ParticleSystem</code>, done.
      </p>
      <CodeBlock
        title="setup.py"
        code={`from tilemap_parser import parse_particle_file, ParticleSystem

configs = parse_particle_file("data/particles/explosion.json")
explosion = ParticleSystem(configs[0])

# maps with render_scale > 1: scale dimensionful fields once
configs[0].apply_render_scale(render_scale)`}
      />
      <p>
        Everything about the effect lives in the config: <code>spawn_rate</code>,{" "}
        <code>max_particles</code>, <code>lifetime_min/max</code>,{" "}
        <code>speed_min/max</code>, <code>direction</code> +{" "}
        <code>spread</code>, <code>gravity_x/y</code>, start/end colors,
        <code>start_scale/end_scale</code>, <code>alpha_fade</code>,{" "}
        <code>emission_shape</code> and <code>particle_shape</code>. The valid
        values for the shape/fade fields are the module constants{" "}
        <code>EMISSION_SHAPES</code>, <code>PARTICLE_SHAPES</code> and{" "}
        <code>ALPHA_FADE_MODES</code>.
      </p>

      <h2 id="update-render">UPDATE AND DRAW: THE AREA RECT</h2>
      <p>
        <code>update()</code> needs the emitter's <em>emission area</em>: the
        rect where particles spawn (config <code>emission_shape</code> decides
        how the area is used: point / rect / circle / line).{" "}
        <code>draw()</code> needs the camera offset and zoom. This is the whole
        per-frame cost:
      </p>
      <CodeBlock
        title="game loop"
        code={`# update(dt, area_x, area_y, area_w, area_h)  # spawn rect in world px
explosion.update(dt, 320.0, 240.0, 32.0, 32.0)

# draw(screen, offset_x, offset_y, zoom)  # camera offset, not rect
explosion.draw(screen, camera.offset_x, camera.offset_y, zoom)`}
      />

      <h2 id="burst">BURSTS AND CONTINUOUS EMISSION</h2>
      <p>
        A burst fires a fixed count immediately; that's the explosion pattern.
        Continuous emission comes from the config's <code>spawn_rate</code>{" "}
        (particles per second, capped by <code>max_particles</code>) fed by{" "}
        <code>update()</code>, the torch pattern. Nothing to toggle at
        runtime; the config is the switch.
      </p>
      <CodeBlock
        title="burst.py"
        code={`# explosion: 120 particles at once, anywhere in the 32x32 area
explosion.emit_burst(120, x, y, 32.0, 32.0)

# torch: config.spawn_rate > 0 and update() every frame emits steadily`}
      />

      <h2 id="renderers">RENDERERS</h2>
      <p>
        <code>ParticleSystem.draw()</code> internally calls{" "}
        <code>SpriteBatchRenderer</code>, the concrete renderer that caches
        shape textures, tints, scales and batches blits. The{" "}
        <code>ParticleRenderer</code> base class is abstract; you only meet it
        if you write your own renderer (implement{" "}
        <code>prepare(particles, config)</code> and{" "}
        <code>draw(screen, offset_x, offset_y, zoom)</code>).{" "}
        <code>clear_texture_caches()</code> frees the cached shape textures
        when you're done.
      </p>

      <h2 id="editor">EDITOR-PLACED EMITTERS (NODES)</h2>
      <p>
        Emitters placed in the tilemap-editor come back as parsed nodes. Wrap
        each node in a <code>ParticleEmitterNode</code> to get its config and
        placement rect, then build the system, exactly as{" "}
        <code>examples/particles/src/main.py</code> does:
      </p>
      <CodeBlock
        title="from the map"
        code={`from tilemap_parser import parse_nodes_file
from tilemap_parser.runtime.particles import ParticleEmitterNode

for parsed in parse_nodes_file("data/map.nodes.json"):
    if parsed.node_type != "particle_emitter":
        continue
    node = ParticleEmitterNode(parsed)          # .config + .rect
    ps = ParticleSystem(node.config)
    ps.update(dt, node.rect.x, node.rect.y, node.rect.w, node.rect.h)
    ps.draw(screen, 0, 0, 1)`}
      />
      <p>
        If you already load the map with{" "}
        <code>TilemapData.load(path, nodes_dir=...)</code>, the same emitters
        come pre-wrapped as <code>td.particle_emitters</code>; skip the manual
        wrapping.
      </p>

      <Callout kind="tip" title="PERFORMANCE">
        Batching means the renderer is cheap at reasonable counts, but each
        particle is a Python object, so thousands per frame will cost you. Prefer
        a few bursts or modest <code>spawn_rate</code>s over one system with{" "}
        <code>max_particles</code> in the thousands.
      </Callout>
    </div>
  );
}
