import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";

export default function Particles() {
  return (
    <div className="content">
      <h1>Particles: visual effects</h1>
      <p>
        One config per effect, one <code>ParticleSystem</code> per emitter. A
        system owns exactly one emitter; for two effects you build two
        systems. Configs come from the tilemap-editor's particle JSON or are
        built by hand with <code>ParticleSystemConfig</code>.
      </p>

      <h2 id="quickstart">QUICK START: ONE EFFECT, FIVE LINES</h2>
      <p>
        A particle effect has three pieces: a <strong>config</strong> (everything the
        effect looks like), a <strong>system</strong> (the runtime object), and a
        <strong>spawn area</strong> (the rect where new particles appear —
        passed to <code>update()</code> every frame). The engine does the rest:
      </p>
      <CodeBlock
        title="one effect, whole game"
        code={`from tilemap_parser import TilemapData
from tilemap_parser.runtime.particles import ParticleSystem

td = TilemapData.load("data/map.json", nodes_dir="data")

# 1. grab the effect's config from the map (emitters placed in the editor)
snow_node = next(n for n in td.particle_emitters if n.name == "snow")

# 2. build the system; maps with render_scale > 1: scale dimensionful
#    fields once, and remember the scale for the area rect (step 3)
rs = td.render_scale
snow_cfg = snow_node.config
snow_cfg.apply_render_scale(rs)
snow = ParticleSystem(snow_cfg)

# 3. every frame: update() spawns inside the area, draw() blits with the camera
r = snow_node.rect
snow.update(dt, r.x * rs, r.y * rs, r.w * rs, r.h * rs)
snow.draw(screen, camera_x, camera_y, 1.0)`}
      />
      <p>
        The emitter's <code>rect</code> is raw editor pixels, not auto-scaled.
        Unlike <code>AreaNode</code> rects (which come pre-scaled), particle
        emitter rects need the same <code>rs</code> multiplier the config got.
        With <code>render_scale = 1</code> the multiplication is a no-op, which
        is why examples that skip it still work.
      </p>
      <p>
        Same shape when you bypass the map:{" "}
        <code>parse_particle_file()</code> returns the configs directly, and
        you supply the area rect yourself.
      </p>

      <h2 id="kinds">TWO WAYS TO SPEND THE AREA RECT</h2>
      <p>
        The area rect is simply the rect where <em>new particles spawn</em>.
        What it should be depends on the effect you want.
      </p>
      <ul>
        <li>
          <strong>Anchored to the map</strong> — an explosion at a fixed spot,
          a torch, a bullet spark. Use the emitter's rect from the editor
          node (a small, static rect in world coordinates), as in the quick
          start.
        </li>
        <li>
          <strong>Following the camera</strong> — full-screen effects like
          snow or mist that should cover the <em>whole visible screen</em>.
          Pass the on-screen rect each frame instead; particles keep spawning
          across the view and the effect follows the camera everywhere.
        </li>
      </ul>
      <CodeBlock
        title="snow: camera-following, screen-wide"
        code={`# the config is stored in the map; the area is the visible screen rect
rs = td.render_scale
snow_cfg = next(n for n in td.particle_emitters if n.name == "snow").config
snow_cfg.apply_render_scale(rs)
snow = ParticleSystem(snow_cfg)

# area = a rect on screen (top quarter of the view), moved with the camera.
# screen rect is already in effective pixels: no rs multiplication here.
snow.update(dt, cam.x, cam.y + HEIGHT // 4, WIDTH, HEIGHT // 2)
snow.draw(screen, cam.x, cam.y, 1.0)`}
      />
      <CodeBlock
        title="spark: map-anchored burst"
        code={`spark_cfg = next(n for n in td.particle_emitters if n.name == "spark").config
spark_cfg.apply_render_scale(rs)
spark_cfg.spawn_rate = 0            # no streaming; fire on demand
spark = ParticleSystem(spark_cfg)

# fire a fixed burst in world pixels: position and spread are yours to
# pick, rs-scaled if the map is scaled. A burst enters the area rect once,
# then dynamics take over.
spark.emit_burst(24, bullet.x, bullet.y, 8 * rs, 8 * rs)

# zero-area update: nothing new spawns, existing particles keep being animated
spark.update(dt, 0, 0, 0, 0)
spark.draw(screen, cam.x, cam.y, 1.0)`}
      />
      <p>
        Same config, same loop — only the rectangle changes. Map rect makes
        the effect stay in place; screen rect makes it travel with the camera;
        a zero rect means "no new particles, just finish the ones alive".
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
        rect where particles spawn — the two patterns above. Config{" "}
        <code>emission_shape</code> decides <em>how</em> the area is used:
        point / rect / circle / line. <code>draw()</code> needs the camera
        offset and zoom. This is the whole per-frame cost:
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
    # node.rect is raw editor coords: multiply by the map's render_scale
    # (same rs the config got), like the quick start above
    ps.update(dt, node.rect.x * rs, node.rect.y * rs, node.rect.w * rs, node.rect.h * rs)
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

      <h2 id="field">ADVANCED: PARTICLE FIELDS — FOG, HAZE, DUST</h2>
      <p>
        The three modes above are for one-off or streaming particles. Fog,
        haze, and dust are different: they should <em>already be there</em> and
        only drift. That's what <code>ParticleField</code> is for — it creates
        the sheets once, then just moves them. Nothing is ever created or
        destroyed, so the fog never flickers and costs almost nothing per
        frame.
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
      <Callout kind="tip" title="FIELDS vs EMITTERS">
        <code>spawn_rate</code> is great for effects that are naturally a{" "}
        <em>stream</em> — rain, embers, smoke puffs — because a stream of
        short-lived particles <em>is</em> the look. It is a bad fit for plain
        atmosphere: fog made of a constant stream means thousands of
        create/destroy events per minute and constant flicker. For atmosphere,
        fill once and wrap. A field of a few hundred sheets costs far less
        than an emitter making the same look.
      </Callout>

      <h3 id="field-options">WHAT EACH <code>ParticleField</code> OPTION DOES</h3>
      <p>
        The quick answer for each option — what it changes, and the values it
        accepts. If an option says <em>profile overrides</em>, it only matters
        when you have not passed a <code>profile</code>.
      </p>
      <table>
        <thead>
          <tr>
            <th>option</th>
            <th>type</th>
            <th>what it does</th>
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
              The world rect where the fog lives. Sheets wrap at the edges, so
              pad it so sheets are off-screen before they wrap. <strong>Required.</strong>
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
              The layered tuning as plain data. Safer and easiest: pass{" "}
              <code>FOG_PROFILE</code>. <code>None</code> builds reasonable
              defaults from the <code>size</code>/<code>speed</code>/<code>alpha</code>{" "}
              options. Profile overrides those.
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
              The sprite each sheet draws. <code>"fog"</code> is a flat,
              soft-edged square that tiles into continuous haze;{" "}
              <code>"smoke"</code> is rounder with a brighter middle. Profile
              overrides.
            </td>
          </tr>
          <tr>
            <td>
              <code>color</code>
            </td>
            <td>
              <code>(r, g, b)</code>
            </td>
            <td>
              Tint for every sheet. The end color is auto-darkened slightly.
            </td>
          </tr>
          <tr>
            <td>
              <code>alpha</code>
            </td>
            <td>
              <code>int</code> 0-255
            </td>
            <td>
              How strong each sheet is. Only used when there is no{" "}
              <code>profile</code>. Profile overrides.
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
              The master strength knob, multiplied into every layer's alpha.
              Assign to fade the whole effect live:{" "}
              <code>field.global_alpha = 0.4</code>.
            </td>
          </tr>
          <tr>
            <td>
              <code>density</code>
            </td>
            <td>
              <code>float</code> &gt; 0
            </td>
            <td>
              How many sheets there are. 1.0 = the default amount; 2.0 = twice
              that — and roughly twice the work. starting low and raising it
              only if the look is too thin.
            </td>
          </tr>
          <tr>
            <td>
              <code>direction</code>
            </td>
            <td>
              <code>float</code> degrees | <code>"random"</code>
            </td>
            <td>
              Where sheets drift: 0 = right, 90 = down, 180 = left, 270 = up.
              Or <code>"random"</code> — every sheet drifts its own way.
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
              How fast sheets drift, as a range — each picks one. Varying speed
              between layers is what stops the fog looking like a grid.
            </td>
          </tr>
          <tr>
            <td>
              <code>size</code>
            </td>
            <td>
              <code>(min, max)</code> px
            </td>
            <td>Sheet size range. Only used when there is no{" "}<code>profile</code>. Profile overrides.</td>
          </tr>
          <tr>
            <td>
              <code>spread</code>
            </td>
            <td>
              <code>float</code> 0-360
            </td>
            <td>
              How much wobble around <code>direction</code>; 0 = one straight
              drift angle.
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
              Depth layers for generic fields (no profile) — more = more depth,
              more work. Profile overrides.
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
              The performance budget: low = fewer sheets (cap 260), medium =
              default (cap 500), high = most (cap 800). It never removes
              layers — layer structure comes from the profile. Turn this down
              on weaker machines.
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
              <code>True</code> keeps the nearest layer in the lower 65% of the
              area, so the fog reads as hugging the ground.
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
              <code>render_scale</code>. Pass <code>map_data.render_scale</code>.
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
                <code>0</code> (default) = normal soft alpha. Overlapping sheets
                just look denser. This is the option for atmosphere: fog, mist,
                haze.
              </p>
              <p>
                Any non-zero flag except <code>pygame.BLEND_PREMULTIPLIED</code>{" "}
                changes how the sheet is drawn onto the screen: the soft
                transparent look is lost and the fog renders <em>solid</em>{" "}
                (opaque). So for realistic fog keep <code>blend=0</code>.
              </p>
              <p>
                Useful non-zero choices:{" "}
                <code>pygame.BLEND_PREMULTIPLIED</code> = premultiplied alpha,
                which preserves soft alpha when used with a{" "}
                <code>premul_alpha()</code> surface;{" "}
                <code>pygame.BLEND_RGBA_ADD</code> = additive glow (sparks,
                fireflies) — start with <code>global_alpha</code> roughly
                halved or it washes out.
              </p>
            </td>
          </tr>
        </tbody>
      </table>
      <p>
        Live tuning: <code>set_color((r, g, b))</code> retints in place (never
        touches alphas), <code>set_density(x)</code>,{" "}
        <code>set_motion(direction=90, speed=(2, 4))</code> and{" "}
        <code>set_area((x, y, w, h))</code> rebuild the field so the change
        applies immediately. Read the result via <code>field.layers</code> —
        each layer has <code>.name</code>, <code>.area</code> and{" "}
        <code>.system</code>.
      </p>

      <h3 id="layered">LAYERED FIELDS: DEPTH FROM PARALLEL FIELDS</h3>
      <p>
        One layer reads flat: same size, same speed, same alpha — a uniform
        haze. Run three stacked layers, each with its own size, speed and
        alpha, and the eye reads depth. The working recipe:
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
        Wrap preserves each sheet's y-offset forever, so sheets that share a
        speed stay aligned as coherent rows or streaks — the giveaway that it
        is particles. Spreading speeds and sizes <em>across</em> layers is what
        dissolves that. The recipe below is a known-good fog; start from it and
        only touch the dials you care about.
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
      <Callout kind="tip" title="FOG_PROFILE IS A STARTING POINT">
        <code>FOG_PROFILE</code> is just data. Copy it, edit the numbers, and
        you have your own mood — dust, ash, underwater shimmer. Starting
        points: light mist — halve <code>global_alpha</code>; heavy fog — raise{" "}
        <code>density</code>; dust — watch the wind and use a generic field.
      </Callout>

      <h3 id="generic-field">GENERIC CONTINUOUS FIELDS</h3>
      <p>
        Fog is only a preset. For dust, pollen, ash, or magic haze, use{" "}
        <code>ParticleField</code> without a profile — it still fills once and
        wraps forever, and you pick the shape, alpha, density, size and motion.
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

      <h3 id="profiles">PROFILES: LAYER TUNING AS PLAIN DATA</h3>
      <p>
        <code>FOG_PROFILE</code> is a <code>FieldProfile(name, presets)</code>:
        a named tuple of <code>FieldLayerSpec</code>s. Each spec is{" "}
        <code>(name, size_min, size_max, speed_min_mul, speed_max_mul, alpha, coverage, ground_layer=False)</code>{" "}
        — <code>coverage</code> is that layer's share of the area (2.0 =
        double the sheet area), <code>speed_*_mul</code> multiplies the
        field's speed range, and <code>ground_layer=True</code> pins the band
        to the lower 65%. Profiles are immutable data — copy them, never mutate
        them. <code>profile.with_alpha(factor, name=None)</code> returns a
        scaled copy (e.g. <code>FOG_PROFILE.with_alpha(0.5, name="mist")</code>)
        without touching the source. Here is the shipped fog, ready to copy:
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

      <h3 id="halfres">HALF-RESOLUTION RENDERING AND SCENE GLOW</h3>
      <p>
        A few hundred big sheets still means per-pixel work every frame. Fog is
        a soft blur anyway, so render it into a half-resolution buffer and
        upscale once — a quarter of the blit area, visually identical. This is
        a rendering recipe, not a <code>ParticleField</code> responsibility:
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
        composite additively. The fog then brightens the scene where it lies
        instead of occluding it.
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
        Alpha particles against black already store their premultiplied color,
        so the additive blit adds exactly the fog's light. Keep the field's own
        <code>blend</code> at <code>0</code> for this — the additive behavior
        comes from the composite, not from the particles.
      </p>

      <h3 id="manual-field">MANUAL FIELDS</h3>
      <p>
        <code>ParticleField</code> is a friendly wrapper around the primitive.
        If you need full control, build the contract yourself:{" "}
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
    </div>
  );
}