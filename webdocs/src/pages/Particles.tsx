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
ox, oy = camera.offset
explosion.draw(screen, ox, oy, zoom)`}
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

      <h2 id="field">PERSISTENT FIELDS: FOG, HAZE, DUST</h2>
      <p>
        Three modes, one system: <strong>burst</strong> (fires once),{" "}
        <strong>emitter</strong> (<code>spawn_rate</code>, particles are born
        and die), and <strong>field</strong> — the atmosphere case. Fog should
        not be a steady stream of newborn particles: every birth is an alpha
        pop and every death is churn. A field is filled once and then{" "}
        <em>only moves</em>: <code>wrap=True</code> makes particles never die —
        exiting the area re-enters on the opposite side, exact offset kept —
        and <code>spawn_rate=0</code> stops new births. Nothing pops, nothing
        churns; the per-frame cost is just moving the same sheets.
      </p>
      <CodeBlock
        title="field.py"
        code={`from tilemap_parser import ParticleField

# padded so sheets leave the screen before they wrap
fog = ParticleField(
    area=(-80, -80, 960, 760),
    color=(200, 205, 215),
    alpha=14,          # per-sheet strength (0-255)
    density=1.0,       # sheet count multiplier
    direction=0,       # drift direction, degrees (0 = right)
    speed=(6, 14),     # drift speed range, px/sec
    quality="medium",  # low / medium / high — budget dial
)

# then the normal loop; no particles are born or die
fog.update(dt)
fog.draw(screen)`}
      />
      <p>
        <code>ParticleField</code> owns the hidden field contract and the
        layered recipe. Tune <code>density</code> for sheet count,{" "}
        <code>alpha</code> for strength, <code>direction</code>/
        <code>speed</code> for motion, and <code>quality</code> for the
        visual/performance budget. For depth, pass{" "}
        <code>profile=FOG_PROFILE</code> (see LAYERED FIELDS) — or check the{" "}
        <a href="#field-params">parameter reference</a> before inventing your
        own look. See <code>examples/particles/src/field.py</code> (LEFT/RIGHT
        change density live).
      </p>
      <Callout kind="tip" title="FIELDS vs EMITTERS">
        <code>spawn_rate</code> is right for discrete continuous effects —
        rain, embers, smoke puffs — where a stream of short-lived particles{" "}
        <em>is</em> the look. It is the wrong tool for a uniform atmosphere:
        fog via <code>spawn_rate</code> means thousands of birth/death events
        per minute and constant alpha flicker. For atmosphere, fill once and
        wrap. A field of a few hundred sheets costs a fraction of an emitter
        producing the same look.
      </Callout>

      <h2 id="layered">LAYERED FIELDS: DEPTH FROM PARALLEL FIELDS</h2>
      <p>
        A single field reads flat: one sheet size, one speed, one alpha — a
        uniform haze. Real atmosphere is layered. Run three fields in
        parallel, each with its own size, speed and alpha, and the eye reads
        depth. The rule that works:
      </p>
      <table>
        <thead>
          <tr>
            <th>layer</th>
            <th>size</th>
            <th>speed</th>
            <th>alpha</th>
            <th>role</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>far</td>
            <td>largest</td>
            <td>slowest</td>
            <td>lowest</td>
            <td>anchors the haze; reads as distance</td>
          </tr>
          <tr>
            <td>mid</td>
            <td>medium</td>
            <td>medium</td>
            <td>medium</td>
            <td>the main volume</td>
          </tr>
          <tr>
            <td>near</td>
            <td>smallest</td>
            <td>fastest</td>
            <td>low</td>
            <td>ground band; reads as proximity</td>
          </tr>
        </tbody>
      </table>
      <p>
        Layering is not just aesthetics. Wrap preserves each sheet's y-offset
        forever, so within one field, sheets that share a speed stay aligned
        as coherent rows or vertical streaks — the classic "I can tell it's
        particles" tell. Spreading speeds and sizes <em>across</em> layers
        makes sheets decorrelate over time, dissolving those structures at
        config level. The recipe below is a known-good fog, so start from it
        and touch only the dials you care about.
      </p>
      <CodeBlock
        title="layered fog"
        code={`from tilemap_parser import FOG_PROFILE, ParticleField

fog = ParticleField(
    area=(-160, -90, 1600, 900),
    profile=FOG_PROFILE,        # the shipped fog tuning, as plain data
    color=(200, 50, 80),
    density=1.0,
    global_alpha=1.0,           # 0-1 strength scale
    direction=0,
    speed=(8, 8),
    quality="medium",
    ground_bias=True,   # near layer uses the lower 65% of the area
)

fog.update(dt)
fog.draw(screen, 0, 0, 1)`}
      />
      <p>
        Four dials, everything else shared: <code>density</code> is sheet
        count, <code>global_alpha</code> is strength, <code>direction</code>/
        <code>speed</code> is motion, and <code>quality</code> is budget. The
        layer tuning lives in <code>FOG_PROFILE</code> — copy it and edit the
        numbers to build your own layered moods. Starting points: light mist —
        halve <code>global_alpha</code>; heavy fog — raise <code>density</code>;
        dust haze — reverse the wind and use a generic field.
      </p>

      <h2 id="generic-field">GENERIC CONTINUOUS FIELDS</h2>
      <p>
        Fog is only a preset. For dust, pollen, ash, magic haze, or other
        persistent ambience, use <code>ParticleField</code> directly. It still
        fills once and wraps forever; you choose the shape, alpha, density,
        size and motion.
      </p>
      <CodeBlock
        title="generic field"
        code={`dust = ParticleField(
    area=(-160, -90, 1600, 900),
    shape="smoke",
    color=(180, 150, 100),
    alpha=10,
    density=0.7,
    direction=180,
    speed=(3, 8),
    size=(20, 45),
    spread=45,
    quality="low",
)

dust.update(dt)
dust.draw(screen)`}
      />

      <h2 id="field-params">PARTICLE FIELD PARAMETER REFERENCE</h2>
      <p>
        Every dial on <code>ParticleField</code>, what it means, and the
        valid values. If a param says "profile overrides", it only drives the
        generic (profile-less) field — the moment you pass{" "}
        <code>profile=FOG_PROFILE</code> the profile's numbers win.
      </p>
      <table>
        <thead>
          <tr>
            <th>param</th>
            <th>type</th>
            <th>meaning</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>area</code>
            </td>
            <td>
              <code>(x, y, w, h)</code>
            </td>
            <td>
              The world-space rect the field lives in. Sheets wrap at the
              edges, so pad it until sheets leave the visible screen before
              they wrap. Required.
            </td>
          </tr>
          <tr>
            <td>
              <code>profile</code>
            </td>
            <td>
              <code>FieldProfile | None</code>
            </td>
            <td>
              Layer tuning as plain data (see below). <code>None</code> builds
              generic layers from the size/speed/alpha dials. Ship with{" "}
              <code>FOG_PROFILE</code>.
            </td>
          </tr>
          <tr>
            <td>
              <code>shape</code>
            </td>
            <td>
              <code>"circle" | "square" | "diamond" | "star" | "sparkle" | "smoke" | "heart" | "line" | "fog"</code>
            </td>
            <td>
              Particle sprite. <code>"fog"</code> is a flat soft-edged square
              that tiles into continuous haze (no bright core, unlike{" "}
              <code>"smoke"</code>). Profile overrides.
            </td>
          </tr>
          <tr>
            <td>
              <code>color</code>
            </td>
            <td>
              <code>(r, g, b)</code>
            </td>
            <td>Tint for every layer; end color auto-darkens by 10.</td>
          </tr>
          <tr>
            <td>
              <code>alpha</code>
            </td>
            <td>
              <code>int</code> 0-255
            </td>
            <td>
              Per-sheet strength used by generic fields. Profile overrides.
            </td>
          </tr>
          <tr>
            <td>
              <code>global_alpha</code>
            </td>
            <td>
              <code>float</code> 0.0-1.0
            </td>
            <td>
              Master strength scale, multiplied into every layer's alpha.
              Hot-tunable: assigning refills the field, so{" "}
              <code>field.global_alpha = 0.4</code> live is how you fade the
              whole effect.
            </td>
          </tr>
          <tr>
            <td>
              <code>density</code>
            </td>
            <td>
              <code>float</code> &gt; 0
            </td>
            <td>Sheet count multiplier. 1.0 = the recipe's reference count.</td>
          </tr>
          <tr>
            <td>
              <code>direction</code>
            </td>
            <td>
              <code>float</code> degrees | <code>"random"</code>
            </td>
            <td>
              Drift direction: 0 = right, 90 = down, 180 = left, 270 = up
              (plain trig on screen coords). Or <code>"random"</code> for
              omnidirectional drift — every sheet picks a random angle on
              refill, the same as a generic field set loose.
            </td>
          </tr>
          <tr>
            <td>
              <code>speed</code>
            </td>
            <td>
              <code>(min, max)</code> px/sec
            </td>
            <td>
              Drift speed range; each sheet picks one. Spreading speeds{" "}
              <em>across layers</em> is what dissolves "I can tell it's
              particles" alignment.
            </td>
          </tr>
          <tr>
            <td>
              <code>size</code>
            </td>
            <td>
              <code>(min, max)</code> px
            </td>
            <td>Sheet size range for generic fields. Profile overrides.</td>
          </tr>
          <tr>
            <td>
              <code>spread</code>
            </td>
            <td>
              <code>float</code> 0-360
            </td>
            <td>
              Random jitter around <code>direction</code>; 0 = a single drift
              direction.
            </td>
          </tr>
          <tr>
            <td>
              <code>layers</code>
            </td>
            <td>
              <code>int</code> &ge; 1
            </td>
            <td>
              How many generic layers to split into when no profile is given.
              Profile overrides.
            </td>
          </tr>
          <tr>
            <td>
              <code>quality</code>
            </td>
            <td>
              <code>"low" | "medium" | "high"</code>
            </td>
            <td>
              Budget dial only: scales density and caps total particles (low
              0.72x/260, medium 1.0x/500, high 1.25x/800). It never trims
              layers — layer structure belongs to the profile.
            </td>
          </tr>
          <tr>
            <td>
              <code>ground_bias</code>
            </td>
            <td>
              <code>bool</code>
            </td>
            <td>
              True keeps the last (nearest) layer in the lower 65% of the
              area, so it reads as proximity to the ground.
            </td>
          </tr>
          <tr>
            <td>
              <code>render_scale</code>
            </td>
            <td>
              <code>float</code> &gt; 0
            </td>
            <td>
              Scales sizes and speeds to match the map's{" "}
              <code>render_scale</code> (pass <code>map_data.render_scale</code>).
            </td>
          </tr>
          <tr>
            <td>
              <code>blend</code>
            </td>
            <td>
              <code>int</code> (pygame flag)
            </td>
            <td>
              <p>
                Passed to every particle blit. <code>0</code> (default) =
                plain alpha — the right choice for natural atmosphere: fog,
                mist, haze. Overlapping sheets just look denser.
              </p>
              <p>
                <code>pygame.BLEND_PREMULTIPLIED</code> = premultiplied
                tints; slightly cleaner overlap compositing when many soft
                sheets stack (same visual style, more correct math). Also
                the cheapest per-pixel blit.
              </p>
              <p>
                <code>pygame.BLEND_RGBA_ADD</code> = additive, glowing
                particles. Reserved for glow/magic effects: RGB <em>and</em>{" "}
                alpha accumulate, so start with{" "}
                <code>global_alpha</code> roughly halved or the field washes
                out to white. Prefer it for sparks, fireflies, magic haze —
                not for natural fog.
              </p>
            </td>
          </tr>
        </tbody>
      </table>
      <p>
        Live tuning beyond <code>global_alpha</code>:{" "}
        <code>set_color((r, g, b))</code> retints (never touches alphas),{" "}
        <code>set_density(x)</code>, <code>set_motion(direction=90, speed=(2, 4))</code>{" "}
        and <code>set_area((x, y, w, h))</code> all refill the field so the
        change applies immediately. Read the result via{" "}
        <code>field.layers</code>: each has <code>.name</code>,{" "}
        <code>.area</code> and <code>.system</code> (the underlying{" "}
        <code>ParticleSystem</code>).
      </p>

      <h2 id="halfres">HALF-RESOLUTION RENDERING AND SCENE GLOW</h2>
      <p>
        A few hundred big sheets still means per-pixel work every frame.
        Fog is a soft blur anyway, so render it into a half-resolution
        buffer and upscale once — a quarter of the blit area, visually
        identical. This is a rendering recipe, not a{" "}
        <code>ParticleField</code> responsibility:
      </p>
      <CodeBlock
        title="natural atmosphere"
        code={`mist_buffer = pygame.Surface((W // 2, H // 2), pygame.SRCALPHA)
mist_buffer.fill((0, 0, 0, 0))
mist.draw(mist_buffer, 0, 0, 0.5)   # zoom = 1/2

# Two-step scale+blit: the dest-form smoothscale(src, size, dest)
# corrupts display surface pixels, so scale to a fresh surface first.
scaled = pygame.transform.smoothscale(mist_buffer, (W, H))
screen.blit(scaled, (0, 0))         # plain alpha composite`}
      />
      <p>
        If you want the fog to <em>add light</em> instead of just tint —
        glowing haze in a dark scene — swap the buffer to plain RGB and
        composite additively. That's the additive-composite trick: fog
        brightens the scene where it lies instead of occluding it.
      </p>
      <CodeBlock
        title="scene glow (additive composite)"
        code={`glow_buffer = pygame.Surface((W // 2, H // 2))   # no alpha channel
glow_buffer.fill((0, 0, 0))
mist.draw(glow_buffer, 0, 0, 0.5)

scaled = pygame.transform.smoothscale(glow_buffer, (W, H))
screen.blit(scaled, (0, 0), special_flags=pygame.BLEND_RGB_ADD)`}
      />
      <p>
        Alpha particles against black already store their premultiplied
        color, so the additive blit adds exactly the fog's light. Keep the
        field's own <code>blend</code> at <code>0</code> for this; the
        additive behavior comes from the composite, not the particles.
      </p>

      <h3 id="profiles">PROFILES: LAYER TUNING AS PLAIN DATA</h3>
      <p>
        <code>FOG_PROFILE</code> is a <code>FieldProfile(name, presets)</code>:
        a named tuple of <code>FieldLayerSpec</code>s. Each spec is{" "}
        <code>(name, size_min, size_max, speed_min_mul, speed_max_mul, alpha, coverage, ground_layer=False)</code>{" "}
        — <code>coverage</code> is that layer's share of the area (2.0 =
        double the sheet area), <code>speed_*_mul</code> multiplies the
        field's speed range, and <code>ground_layer=True</code> pins the band
        to the lower 65%. Profiles are immutable data — copy them, don't
        mutate them. <code>profile.with_alpha(factor, name=None)</code>{" "}
        returns a scaled copy (e.g. <code>FOG_PROFILE.with_alpha(0.5, name="mist")</code>)
        for authoring named variants; the source profile is never touched.
        Copy and edit the numbers for your own moods:
      </p>
      <table>
        <thead>
          <tr>
            <th>layer</th>
            <th>size (px)</th>
            <th>speed × base</th>
            <th>alpha</th>
            <th>coverage</th>
            <th>band</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>far</td>
            <td>90-140</td>
            <td>0.38-0.75</td>
            <td>10</td>
            <td>4.4</td>
            <td>full</td>
          </tr>
          <tr>
            <td>mid</td>
            <td>60-95</td>
            <td>0.62-1.12</td>
            <td>16</td>
            <td>2.67</td>
            <td>full</td>
          </tr>
          <tr>
            <td>near</td>
            <td>40-65</td>
            <td>1.00-1.75</td>
            <td>10</td>
            <td>1.85</td>
            <td>ground (lower 65%)</td>
          </tr>
        </tbody>
      </table>

      <h2 id="manual-field">ADVANCED: MANUAL FIELDS</h2>
      <p>
        <code>ParticleField</code> is just a friendly wrapper around the
        primitive. If you need full control, build the contract yourself:{" "}
        <code>wrap=True</code>, <code>spawn_rate=0</code>, fill once with{" "}
        <code>emit_field()</code>, then update and draw normally.
      </p>
      <CodeBlock
        title="manual field"
        code={`cfg = ParticleSystemConfig(
    name="mist", particle_shape="fog", emission_shape="rect",
    wrap=True, spawn_rate=0,
    particle_size_min=90, particle_size_max=140,
    speed_min=6.0, speed_max=14.0,
    start_color_a=14, end_color_a=14,
    alpha_fade="none", max_particles=400)

ps = ParticleSystem(cfg)
ps.emit_field(0.6, -80, -80, 960, 760)
ps.update(dt, -80, -80, 960, 760)
ps.draw(screen, 0, 0, 1)`}
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
        particle is a Python object, so thousands per frame will cost you. For
        bursts and emitters prefer a few bursts or modest{" "}
        <code>spawn_rate</code>s over one system with{" "}
        <code>max_particles</code> in the thousands. Fields are the exception:
        a field is paid for once at <code>emit_field</code> time and then only
        moved, so large persistent effects should be fields, not fast
        spawners.
      </Callout>
    </div>
  );
}
