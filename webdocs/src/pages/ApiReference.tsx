import CodeBlock from "../components/CodeBlock";

function Group({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h3>{title}</h3>
      {children}
    </section>
  );
}
function Entry({
  name,
  children,
}: {
  name: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-4">
      <h4>{name}</h4>
      <div className="border-l-2 border-line-2 pl-4">{children}</div>
    </div>
  );
}

export default function ApiReference() {
  return (
    <div className="content">
      <h1>API Reference</h1>
      <p>
        Grouped by purpose, not alphabet soup. Every entry is wired, never just
        signed; the "why" and the "connect it like this" are one sentence. The
        physics pages carry the deep explanations; this is the map.
      </p>

      <h2 id="map-data">MAP DATA & LOADING</h2>
      <Group title="Loading">
        <Entry name="load_map(path) → TilemapData">
          <p>
            Entry point for a tilemap-editor map JSON. Feeds{" "}
            <code>TileLayerRenderer</code> and{" "}
            <code>PhysicsWorld.from_map</code>. Exposes <code>tile_size</code>,{" "}
            <code>render_scale</code>, <code>parsed</code> and{" "}
            <code>build_tile_map()</code>. Full wiring on the{" "}
            <a href="/map-parsing">Map Parsing &amp; Rendering</a> page.
          </p>
        </Entry>
        <Entry name="parse_map_dict / parse_map_file / parse_map_json">
          <p>
            Lower-level parsers behind <code>load_map</code>.{" "}
            <code>parse_map_json</code> handles a JSON string;
          </p>
          <p>
            <code>parse_map_file</code> a path.
          </p>
        </Entry>
        <Entry name="TilemapData.build_tile_map(exclude_layers=None, use_gids=False) → dict">
          <p>
            Collapses the map's tile layers into{" "}
            <code>
              {"{"} (col, row): tile_id {"}"}
            </code>{" "}
            , the layer the runner iterates and <code>PhysicsWorld</code> owns.{" "}
            <code>use_gids=True</code> keys by global tile id.
          </p>
        </Entry>
        <Entry name="TilemapData.get_tile_surface(ttype, variant, copy_surface=True) → Surface | None">
          <p>
            The renderer's bake path: one tile texture from the tileset, scaled
            by <code>render_scale</code>. Handy when you want a tile's art
            outside the renderer (icons, minimaps).
          </p>
        </Entry>
      </Group>
      <Group title="Parsed data classes">
        <Entry name="ParsedMap / ParsedMeta / ParsedLayer / ParsedObject / ParsedObjectArea / ParsedTile / ParsedTileset / ParsedAutotileGroup / ParsedAutotileRule / ParsedProjectState / TilesetAnimation">
          <p>
            Read-only data classes for everything a map JSON contains. You
            usually touch <code>parsed.meta.tile_size</code> and{" "}
            <code>parsed.tilesets</code>; the rest is there when you need to
            query editor data.
          </p>
        </Entry>
      </Group>
      <Group title="Nodes, TMX, objects">
        <Entry name="parse_nodes_dict / parse_nodes_file / ParsedNode / AreaNode">
          <p>
            Parses editor node data (e.g. particle emitters placed in the map).{" "}
            <code>AreaNode</code> wraps a parsed node with its
            <code>rect</code> and <code>properties</code>, scaled by{" "}
            <code>render_scale</code>; see <a href="/json">JSON Formats</a> for
            a real example.
          </p>
        </Entry>
        <Entry name="parse_tmx_file / parse_tsx_file / TmxParseError">
          <p>
            Tiled TMX/TSX converter: bridge maps made in Tiled into the same
            parsed structures.
          </p>
        </Entry>
        <Entry name="load_map_objects / MapObject">
          <p>
            <code>MapObject</code> is the lane for polygon solids: a body with
            owner-local polygon shapes. If <code>Body</code> won't take your
            polygon, this is why it exists.
          </p>
        </Entry>
      </Group>

      <h2 id="shapes">SHAPES & COLLISION DATA</h2>
      <Group title="Primitive shapes">
        <Entry name="RectangleShape(width, height, offset=(0,0))">
          <p>
            Box. <code>(x, y)</code> anchor is top-left plus offset. Only
            primitive shapes are accepted on <code>Body</code>.
          </p>
        </Entry>
        <Entry name="CircleShape(radius, offset=(0,0))">
          <p>
            Disc. <code>(x, y)</code> anchor is the center plus offset.
          </p>
        </Entry>
        <Entry name="CapsuleShape(radius, height, offset=(0,0))">
          <p>
            Vertical capsule: two circles <code>height</code> apart. Full
            collision against every shape type.
          </p>
        </Entry>
        <Entry name="CollisionPolygon(vertices, one_way=False)">
          <p>
            Tile/object polygon. <code>transform(tile_x, tile_y, scale)</code>{" "}
            moves it to world space; <code>is_valid()</code> requires ≥ 3
            vertices. <code>one_way=True</code> = platform pass-through from
            below (honored by the platformer family).
          </p>
        </Entry>
      </Group>
      <Group title="Collision containers">
        <Entry name="TilesetCollision(tileset_name, tile_size, tiles)">
          <p>
            Per-tile-id polygons. <code>has_collision(tile_id)</code>,{" "}
            <code>get_world_shapes(tile_id, x, y, scale)</code>, and{" "}
            <code>merge(collisions, firstgids)</code> for multi-tileset maps.
          </p>
        </Entry>
        <Entry name="TileCollisionData(tile_id, shapes)">
          <p>
            One tile's polygons; <code>has_collision()</code>.
          </p>
        </Entry>
        <Entry name="CharacterCollision(name, shape, properties, collision_layer, collision_mask)">
          <p>
            A sprite's single shape, authored in the editor. Feed it to your
            sprite at spawn.
          </p>
        </Entry>
        <Entry name="ObjectCollisionData / ObjectCollisionRegionData">
          <p>
            Region-based polygon paint. <code>get_region(id)</code>, per-region
            layer/mask.
          </p>
        </Entry>
        <Entry name="CollisionCache">
          <p>
            Loads and caches collision JSON:{" "}
            <code>get_tileset_collision(path)</code>,{" "}
            <code>get_character_collision</code>,{" "}
            <code>get_object_collision</code>;{" "}
            <code>clear_collision_cache()</code> to drop it. Also the
            module-level <code>load_*</code> and <code>parse_*_collision</code>{" "}
            functions.
          </p>
        </Entry>
      </Group>

      <h2 id="movement">MOVEMENT: COLLISIONRUNNER</h2>
      <p>
        Full treatment on the <a href="/runner">CollisionRunner guide</a>.
        Here's the surface:
      </p>
      <Group title="Construction">
        <Entry name="from_game_type(game_type, tile_size=(32,32), strict=False, render_scale=1.0)">
          <p>
            'platformer' | 'topdown' | 'rpg' presets; see the guide's table.
            Unknown names raise <code>ValueError</code>.
          </p>
        </Entry>
        <Entry name="from_world(world, game_type='platformer', strict=False)">
          <p>
            Preset + attach in one call. The world's <code>tile_size</code>/
            <code>render_scale</code> are adopted.
          </p>
        </Entry>
        <Entry name="attach(world) / detach()">
          <p>
            Bind or unbind a <code>PhysicsWorld</code>. Attach once; pass{" "}
            <code>None, None</code> for tile args afterwards.
          </p>
        </Entry>
      </Group>
      <Group title="Movement">
        <Entry name="move_and_slide(sprite, tileset, tiles, delta_x, delta_y, slope_slide=False, world=None)">
          <p>
            Displacement + wall sliding. No gravity, never reads{" "}
            <code>vx/vy</code>. Fast path tries the full move first.
          </p>
        </Entry>
        <Entry name="move_rpg(sprite, tileset, tiles, delta_x, delta_y, world=None)">
          <p>
            Displacement + full blocking. No sliding: a diagonal into a corner
            stops both axes.
          </p>
        </Entry>
        <Entry name="move_grounded(sprite, tileset, tiles, dt, velocity=None, world=None)">
          <p>
            Gravity + landing. <code>velocity=(vx, vy)</code> skips gravity.
            Ledge detection when the sprite was grounded.
          </p>
        </Entry>
        <Entry name="move_platformer(sprite, tileset, tiles, dt, input_x=0.0, jump_pressed=False, velocity=None, world=None)">
          <p>Gravity, jump, step-up, one-way platforms, ground snapping.</p>
        </Entry>
        <Entry name="move_platformer_with_slide(...) → same shape">
          <p>
            Slope-aware: walks polygon floor surfaces within{" "}
            <code>max_walk_angle</code>.
          </p>
        </Entry>
        <Entry name="move(sprite, tileset, tiles, delta_x, delta_y, dt, **kwargs)">
          <p>
            Dispatches on <code>self.mode</code> (SLIDE/PLATFORMER/RPG/GROUNDED),
            handy for one generic call.
          </p>
        </Entry>
      </Group>
      <Group title="Queries & config">
        <Entry name="get_tile_at(world_x, world_y) / get_tile_shapes / get_nearby_tile_shapes">
          <p>World-space queries without moving anything.</p>
        </Entry>
        <Entry name="validate_config(strict=None)">
          <p>
            Range and consistency checks; called by presets. See the guide's
            validation section.
          </p>
        </Entry>
        <Entry name="CollisionResult">
          <p>
            <code>
              collided, final_x, final_y, hit_wall_x, hit_wall_y, hit_ceiling,
              on_ground, slide_vector
            </code>
            .
          </p>
        </Entry>
        <Entry name="MovementMode">
          <p>
            Enum: <code>SLIDE</code>, <code>PLATFORMER</code>, <code>RPG</code>,{" "}
            <code>GROUNDED</code> (moves via <code>move_grounded</code>;
            reachable through the raw{" "}
            <code>CollisionRunner(tile_size, mode=...)</code> constructor, not
            through the <code>from_game_type</code> presets).
          </p>
        </Entry>
      </Group>

      <h2 id="world">PHYSICS WORLD & BODIES</h2>
      <Group title="PhysicsWorld">
        <Entry name="PhysicsWorld(tile_map, tileset_collision, tile_size=(32,32), render_scale=1.0)">
          <p>
            The space. A <code>tile_map</code> without{" "}
            <code>tileset_collision</code> raises <code>ValueError</code>.
          </p>
        </Entry>
        <Entry name="from_map(tilemap_data, tileset_collision, *, exclude_layers=None, use_gids=False)">
          <p>Build from a loaded map; adopts the map's grid geometry.</p>
        </Entry>
        <Entry name="add_body / remove_body / clear_bodies">
          <p>
            Body management. Duplicate <code>add_body</code> is a no-op;
            removing an absent body raises <code>ValueError</code>.
          </p>
        </Entry>
        <Entry name="collides_with_body(sprite) → Body | None">
          <p>
            First overlapping body in insertion order, self excluded, layers
            honored. Bodies are always solid both ways.
          </p>
        </Entry>
        <Entry name="__contains__ / __len__">
          <p>
            <code>body in world</code>, <code>len(world)</code>.
          </p>
        </Entry>
      </Group>
      <Group title="Body">
        <Entry name="Body(collision_shape, x=0, y=0, *, vx=0, vy=0, mode='static', collision_layer=1, collision_mask=0xFFFFFFFF, game_id='')">
          <p>
            A solid. Primitive shapes only (TypeError otherwise);{" "}
            <code>mode</code> in ('static', 'kinematic'): scripted velocity, no
            engine dynamics. <code>top_y_at(world_x)</code> and{" "}
            <code>as_polygon()</code> back the resolver's ground sampling and
            slide normals.
          </p>
        </Entry>
      </Group>
      <Group title="Protocols: the sprite contract">
        <Entry name="ICollidable / ICollidableObject / ICollidableSprite">
          <p>
            The duck-type contracts the runner and world accept.{" "}
            <code>ICollidable</code>: <code>x</code>, <code>y</code>,{" "}
            <code>collision_shape</code>. <code>ICollidableObject</code> adds{" "}
            <code>collision_layer/mask</code>. <code>ICollidableSprite</code>{" "}
            adds <code>vx</code>, <code>vy</code>, <code>on_ground</code> for
            the physics modes. Anything with these attributes works; no
            subclassing required.
          </p>
        </Entry>
      </Group>

      <h2 id="render">RENDERING & CAMERA</h2>
      <Group title="TileLayerRenderer">
        <Entry name="TileLayerRenderer(data, *, include_hidden_layers=False)">
          <p>
            Draws the visible tile layers, chunk-culled (32×32 tiles per chunk).{" "}
            <code>
              render(target, camera_xy=(0,0), viewport_size=None, *,
              extra_objects=None, current_time_ms=None) → LayerRenderStats
            </code>
            . <code>warm_cache()</code> pre-bakes tile variants (then frees the
            source data). Respects layer <code>z_index</code>,{" "}
            <code>y_sort</code> and tileset animations.
          </p>
        </Entry>
        <Entry name="get_layer_dict() → dict">
          <p>
            Raw{" "}
            <code>
              {"{"}layer_id: TileLayer{"}"}
            </code>{" "}
            view of the layers the renderer draws — for debug readouts and
            custom layer iteration.
          </p>
        </Entry>
        <Entry name="LayerRenderStats">
          <p>
            <code>drawn_tiles, skipped_tiles, visible_layers</code>: your
            per-frame culling report.
          </p>
        </Entry>
      </Group>
      <Group title="Camera">
        <Entry name="Camera(viewport_width, viewport_height, mode='centered')">
          <p>
            <code>'centered'</code> keeps the target centered;{" "}
            <code>'deadzone'</code> only moves when the target exits a box.{" "}
            <code>follow(target)</code> (needs x, y, collision_shape),{" "}
            <code>update(dt)</code>, <code>offset</code>,{" "}
            <code>shake(duration, intensity)</code>, <code>lerp_speed</code>,{" "}
            <code>bounds</code>.
          </p>
        </Entry>
      </Group>

      <h2 id="animation">ANIMATION</h2>
      <Group title="AnimationPlayer">
        <Entry name="SpriteAnimationSet.load(json_path, *, spritesheet_path=None, extra_search_base=None)">
          <p>
            Loads an animation JSON + spritesheet into one object.{" "}
            <code>get_image(variant_id)</code>,{" "}
            <code>get_content_bounds(clip_name)</code>.
          </p>
        </Entry>
        <Entry name="AnimationPlayer(animation_set, animation_name)">
          <p>
            Frame clock: <code>update(dt_ms)</code>,{" "}
            <code>get_current_image()</code>, <code>reset()</code>,{" "}
            <code>finished</code>, <code>frame_index</code>. Honors per-frame
            durations and <code>loop</code>.
          </p>
        </Entry>
        <Entry name="AnimationClip / AnimationFrame / AnimationLibrary / AnimationMarker + parse_animation_dict / parse_animation_file / parse_animation_json">
          <p>
            Parsed animation data. <code>AnimationParseError</code> for bad
            files.
          </p>
        </Entry>
      </Group>

      <h2 id="particles">PARTICLES</h2>
      <Group title="ParticleSystem">
        <Entry name="ParticleSystemConfig(particle_shape, spawn_rate, max_particles, lifetime_min/max, speed_min/max, direction, spread, start_color_r/g/b/a, end_color_r/g/b/a, alpha_fade, gravity_x, gravity_y)">
          <p>
            Everything about a particle, in one config. Full wiring on the{" "}
            <a href="/particles">Particles</a> page.
          </p>
        </Entry>
        <Entry name="ParticleSystem(config) + ParticleRenderer / SpriteBatchRenderer / ParticleEmitter / ParticleEmitterNode">
          <p>
            The runtime: emitters spawn, fade, and batch-draw. Node-based
            emitters come from the map's node data (see JSON Formats).{" "}
            <code>clear_texture_caches()</code> frees loaded textures.
          </p>
        </Entry>
        <Entry name="parse_particle_dict / parse_particle_file / PARTICLE_SHAPES / EMISSION_SHAPES / ALPHA_FADE_MODES">
          <p>Parse configs from JSON and the accepted value sets.</p>
        </Entry>
      </Group>

      <h2 id="nav">NAVIGATION</h2>
      <Group title="Pathfinding">
        <Entry name="NavGrid / Pathfinder / PathFollower">
          <p>
            NavGrid builds the walkable grid from a tile layer; Pathfinder
            computes a path; PathFollower moves an entity along it. Full wiring
            on the <a href="/pathfinding">Pathfinding</a> page and in{" "}
            <code>examples/rpg-pathfinding/main.py</code>.
          </p>
        </Entry>
        <Entry name="NavGrid.is_one_way(tx, ty) → bool">
          <p>
            True if the tile at <code>(tx, ty)</code> carries a one-way polygon.
            The pathfinding answer to "can I stand on it" — one-way tiles are
            walkable, solid tiles are walls.
          </p>
        </Entry>
      </Group>

      <h2 id="utils">UTILITIES & QUERIES</h2>
      <Group title="Detection">
        <Entry name="check_collision(a, b) → CollisionHit | None">
          <p>
            Layer filter → AABB broadphase → narrowphase (deepest pair wins).
            Handles multi-shape objects.
          </p>
        </Entry>
        <Entry name="should_collide(a, b)">
          <p>
            The mutual-agreement layer rule:{" "}
            <code>(a_mask &amp; b_layer) and (b_mask &amp; a_layer)</code>.
          </p>
        </Entry>
        <Entry name="aabb_overlap / get_shape_aabb / get_shape_bounds">
          <p>
            Box math. <code>get_shape_bounds</code> backs the runner's tile
            queries.
          </p>
        </Entry>
        <Entry name="circle_vs_circle / rect_vs_rect / rect_vs_circle / polygon_vs_polygon / polygon_vs_rect / polygon_vs_circle / rect_vs_tilemap">
          <p>
            Standalone narrowphase tests, when you want collision without the
            runner.
          </p>
        </Entry>
        <Entry name="CollisionHit">
          <p>
            <code>resolve()</code>, <code>slide_velocity()</code>,{" "}
            <code>involves()</code>, <code>other()</code>: the object-collision
            lane's results.
          </p>
        </Entry>
      </Group>

      <h2 id="errors">ERRORS</h2>
      <Group title="Raised by parsers and validators">
        <Entry name="MapParseError / CollisionParseError / AnimationParseError / TmxParseError">
          <p>
            All subclass <code>ValueError</code>. Parse failures give you the
            offending data plus the reason. The runner raises plain{" "}
            <code>ValueError</code> for config violations and invalid{" "}
            <code>game_type</code>.
          </p>
        </Entry>
      </Group>
    </div>
  );
}
